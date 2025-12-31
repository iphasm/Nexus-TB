"""
NEXUS TRADING BOT - Async Trading Manager
Async version of TradingSession using python-binance AsyncClient

NOTE: This is a wrapper that provides async interfaces while maintaining 
backward compatibility with the sync TradingSession for gradual migration.
"""

import os
import json
import time
import aiohttp
import asyncio
from typing import Optional, Dict, Any, Tuple, List
from nexus_system.utils.logger import get_logger

# Nexus Core
from nexus_system.core.nexus_bridge import NexusBridge
from nexus_system.core.shadow_wallet import ShadowWallet

# AI Analyst
from servos.ai_analyst import NexusAnalyst

# Shield 2.0
from nexus_system.shield.correlation import CorrelationManager

# Personalities
from servos.personalities import PersonalityManager

import pandas as pd

# Cortex / Strategy System
from nexus_system.cortex.base import Signal
from nexus_system.cortex.registry import StrategyRegistry


# Helper function to round price to tick size
def round_to_tick_size(price: float, tick_size: float) -> float:
    """
    Redondea un precio al múltiplo más cercano del tick size de Binance.
    
    Args:
        price: Precio a redondear
        tick_size: Tick size del símbolo (ej: 0.001, 0.01, 0.1)
    
    Returns:
        Precio redondeado al múltiplo más cercano del tick size
    """
    if price <= 0:
        return price
    
    # Si tick_size es inválido o muy grande, usar estimación basada en el precio
    if tick_size <= 0 or tick_size >= price:
        # Estimar tick_size basado en el precio (fallback)
        if price >= 1000:
            tick_size = 0.1
        elif price >= 1:
            tick_size = 0.01
        elif price >= 0.1:
            tick_size = 0.001
        elif price >= 0.01:
            tick_size = 0.0001
        else:
            tick_size = 0.00001
    
    # Redondear al múltiplo más cercano: round(price / tick_size) * tick_size
    rounded = round(price / tick_size) * tick_size
    
    # Asegurar que el resultado no sea 0 si el precio original no era 0
    if rounded <= 0 and price > 0:
        # Si el redondeo resultó en 0, usar el precio original
        # Esto puede pasar si tick_size es muy grande comparado con el precio
        return price
    
    # Evitar errores de punto flotante usando formato y parse
    # Esto asegura que 0.001 * 100 = 0.1 exactamente
    decimals = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0
    result = float(f"{rounded:.{decimals}f}")
    
    # Validación final: si el resultado es 0 pero el precio original no, devolver el precio original
    if result <= 0 and price > 0:
        return price
    
    return result


def format_price_smart(price: float, max_decimals: int = 12) -> str:
    """
    Formatea un precio mostrando solo las cifras significativas.
    Muestra 3 cifras después del último cero antes de los dígitos significativos.
    
    Ejemplos:
        - 0.0073094399999999995 -> 0.007309 (3 cifras después del último cero)
        - 0.00793152 -> 0.007931 (3 cifras después del último cero)
        - 0.007776 -> 0.007776 (3 cifras después del último cero)
        - 1.523 -> 1.523 (sin ceros iniciales, mostrar 3 decimales)
    
    Args:
        price: Precio a formatear
        max_decimals: Máximo de decimales a considerar
    
    Returns:
        String formateado del precio
    """
    if price <= 0:
        return "0.0"
    
    # Convertir a string con suficientes decimales SIN eliminar trailing zeros todavía
    price_str_full = f"{price:.{max_decimals}f}"
    
    # Si tiene punto decimal
    if '.' in price_str_full:
        parts = price_str_full.split('.')
        integer_part = parts[0]
        decimal_part = parts[1] if len(parts) > 1 else ""
        
        # Si la parte entera es 0 o vacía
        if integer_part == '0' or integer_part == '':
            # Para números pequeños, mostrar hasta 6 dígitos después del punto
            # Esto captura "00" + "7309" = "007309" para 0.0073094399999999995
            result_decimal = decimal_part[:6]
            # Eliminar solo trailing zeros al final
            result_decimal = result_decimal.rstrip('0')
            if result_decimal:
                return f"0.{result_decimal}"
            else:
                return "0.0"
        else:
            # Parte entera no es 0, mostrar normalmente con hasta 3 decimales
            return f"{integer_part}.{decimal_part[:3]}".rstrip('0').rstrip('.')
    else:
        return price_str_full


def ensure_price_separation(price: float, entry_price: float, tick_size: float, side: str, is_sl: bool) -> float:
    """
    Asegura que SL/TP tengan una separación mínima del precio de entrada.
    
    Args:
        price: Precio calculado (SL o TP)
        entry_price: Precio de entrada
        tick_size: Tick size del símbolo
        side: 'LONG' o 'SHORT'
        is_sl: True si es SL, False si es TP
    
    Returns:
        Precio ajustado con separación mínima garantizada
    """
    if price <= 0 or entry_price <= 0:
        return price
    
    # Calcular separación mínima (al menos 2 ticks para evitar problemas de redondeo)
    min_separation = max(tick_size * 2, entry_price * 0.0001)  # Al menos 0.01% o 2 ticks
    
    if side == 'LONG':
        if is_sl:
            # SL debe ser < entry, asegurar al menos min_separation de diferencia
            if price >= entry_price:
                price = entry_price - min_separation
            elif (entry_price - price) < min_separation:
                price = entry_price - min_separation
        else:
            # TP debe ser > entry, asegurar al menos min_separation de diferencia
            if price <= entry_price:
                price = entry_price + min_separation
            elif (price - entry_price) < min_separation:
                price = entry_price + min_separation
    else:  # SHORT
        if is_sl:
            # SL debe ser > entry, asegurar al menos min_separation de diferencia
            if price <= entry_price:
                price = entry_price + min_separation
            elif (price - entry_price) < min_separation:
                price = entry_price + min_separation
        else:
            # TP debe ser < entry, asegurar al menos min_separation de diferencia
            if price >= entry_price:
                price = entry_price - min_separation
            elif (entry_price - price) < min_separation:
                price = entry_price - min_separation
    
    # Re-redondear después del ajuste
    return round_to_tick_size(price, tick_size)


def format_position_message(
    symbol: str,
    side: str,
    quantity: float,
    entry_price: float,
    sl_price: float,
    tp_price: float,
    leverage: int,
    total_equity: float,
    margin_used: float,
    target_exchange: str,
    atr_value: float = None,
    strategy: str = "Manual",
    personality: str = "STANDARD_ES"
) -> str:
    """
    Genera mensaje enriquecido de ejecución de posición con frase de personalidad.

    Args:
        symbol: Símbolo del activo
        side: 'LONG' o 'SHORT'
        quantity: Cantidad ejecutada
        entry_price: Precio de entrada
        sl_price: Precio de Stop Loss
        tp_price: Precio de Take Profit
        leverage: Leverage aplicado
        total_equity: Equity total disponible
        margin_used: Margen utilizado
        target_exchange: Exchange destino
        atr_value: Valor de ATR usado (opcional)
        strategy: Estrategia utilizada
        personality: Personalidad activa

    Returns:
        Mensaje formateado con información completa y frase de personalidad
    """
    # Cálculos adicionales
    notional = quantity * entry_price
    risk_amount = abs(entry_price - sl_price) * quantity
    risk_pct = (risk_amount / total_equity) * 100 if total_equity > 0 else 0
    rr_ratio = abs(tp_price - entry_price) / abs(sl_price - entry_price) if sl_price != entry_price else 1.0

    # Determinar emoji y dirección
    direction_emoji = "📈" if side == "LONG" else "📉"
    main_emoji = "🚀" if side == "LONG" else "🐻"

    # Obtener frase de personalidad
    personality_manager = PersonalityManager()
    personality_phrase = personality_manager.get_message(personality, 'POSITION_EXECUTED')

    return f"""
{main_emoji} {side.upper()} EJECUTADO: {symbol}
═══════════════════════════════════════════

💰 CAPITAL ASIGNADO
├─ Exchange: {target_exchange} ({'Crypto' if 'USDT' in symbol else 'Stocks'})
├─ Equity Total: ${total_equity:,.2f}
├─ Margen Usado: ${margin_used:,.2f} ({margin_used/total_equity*100:.1f}%)
└─ Leverage: {leverage}x

📊 POSICIÓN
├─ Cantidad: {quantity:.4f} {symbol.replace('USDT', '').replace('USD', '')}
├─ Precio Entrada: ${entry_price:,.2f}
├─ Valor Notional: ${notional:,.2f}
└─ Dirección: {side.upper()} {direction_emoji}

🎯 OBJETIVOS DE RIESGO
├─ Stop Loss: ${sl_price:,.2f} ({((sl_price-entry_price)/entry_price*100):+.1f}%)
├─ Take Profit: ${tp_price:,.2f} ({((tp_price-entry_price)/entry_price*100):+.1f}%)
├─ Ratio Riesgo/Recompensa: 1:{rr_ratio:.1f}
└─ Riesgo Máximo: ${risk_amount:.2f} ({risk_pct:.2f}% del capital)

⚡ EJECUCIÓN
├─ Órdenes SL/TP: ✅ Configuradas
├─ ATR Usado: {atr_value:.4f if atr_value else 'N/A'} ({'2x multiplicador' if atr_value else 'Porcentaje fijo'})
└─ Risk-Based Sizing: ✅ Aplicado

💡 ESTRATEGIA: {strategy}{' con ATR Dinámico' if atr_value else ''}

💬 {personality_phrase}
""".strip()


class AsyncTradingSession:
    """
    Async Trading Session using Nexus Bridge.
    Unified interface for Binance, Bybit, and Alpaca.
    """
    
    def __init__(self, chat_id: str, api_key: str, api_secret: str, config: Optional[Dict] = None, manager=None):
        self.chat_id = chat_id
        self.config_api_key = api_key
        self.config_api_secret = api_secret
        
        # Nexus Core
        self.shadow_wallet = ShadowWallet()
        self.bridge = NexusBridge(self.shadow_wallet)
        self.logger = get_logger("AsyncTradingSession")
        
        self.manager = manager
        
        from system_directive import DEFAULT_SESSION_CONFIG
        
        # Initialize with centralized defaults
        self.config = dict(DEFAULT_SESSION_CONFIG)
        
        if config:
            self.config.update(config)
        
        self.mode = self.config.get('mode', 'WATCHER')
        
        # Circuit Breaker State (Can be disabled via config)
        self.cb_ignore_until = 0  
        
        # AI Analyst
        self.ai_analyst = NexusAnalyst()

        # Shield 2.0: Portfolio Correlation Guard
        self.correlation_manager = CorrelationManager()
        
        # Operation Lock: Prevent concurrent/spam operations per symbol
        self._operation_locks = {}  # {symbol: timestamp}
        self._lock_duration = 30  # seconds
        
        # Algo Order Tracking: Track algoIds for selective cancellation
        self.active_algo_orders = {}  # {symbol: {'sl_id': str, 'tp_id': str}}
        
        # Proxy Setup
        self._proxy = os.getenv('PROXY_URL') or os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')

    
    @property
    def client(self):
        """
        Backward compatibility property.
        Returns the underlying CCXT exchange from Binance adapter.
        NOTE: This returns a CCXT exchange (binanceusdm), not python-binance AsyncClient.
        Some method names differ. For futures operations, use CCXT equivalents.
        """
        if self.bridge and 'BINANCE' in self.bridge.adapters:
            adapter = self.bridge.adapters['BINANCE']
            return adapter._exchange  # CCXT binanceusdm instance
        return None
    
    @property
    def bybit_client(self):
        """Returns the Bybit adapter instance if connected."""
        if self.bridge and 'BYBIT' in self.bridge.adapters:
            return self.bridge.adapters['BYBIT']
        return None
    
    @property
    def alpaca_adapter(self):
        """Returns the Alpaca adapter instance if connected."""
        if self.bridge and 'ALPACA' in self.bridge.adapters:
            return self.bridge.adapters['ALPACA']
        return None
    


    async def initialize(self, verbose: bool = True) -> bool:
        """Async initialization via Nexus Bridge."""
        if verbose:
            print("🧠 Nexus Analyst: CONNECTED.")
        
        # Proxy Settings (Config > Env > self._proxy)
        # Fix: Check PROXY_URL and self._proxy which were being ignored
        http_proxy = (self.config.get('http_proxy') or 
                     os.getenv('PROXY_URL') or 
                     os.getenv('HTTP_PROXY') or 
                     os.getenv('http_proxy') or 
                     self._proxy)
                     
        https_proxy = (self.config.get('https_proxy') or 
                      os.getenv('PROXY_URL') or 
                      os.getenv('HTTPS_PROXY') or 
                      os.getenv('https_proxy') or
                      self._proxy)
        
        exchange_kwargs = {}
        if http_proxy:
            exchange_kwargs['http_proxy'] = http_proxy
            if https_proxy:
                 exchange_kwargs['https_proxy'] = https_proxy

        # 1. Binance Futures
        if self.config_api_key and self.config_api_secret:
            await self.bridge.connect_exchange(
                'BINANCE', 
                api_key=self.config_api_key, 
                api_secret=self.config_api_secret,
                **exchange_kwargs
            )
            if verbose: print(f"✅ Bridge: Connected to Binance")

        # 2. Bybit
        bybit_key = self.config.get('bybit_api_key') or os.getenv('BYBIT_API_KEY')
        bybit_secret = self.config.get('bybit_api_secret') or os.getenv('BYBIT_API_SECRET')
        if bybit_key and bybit_secret:
            await self.bridge.connect_exchange(
                'BYBIT',
                api_key=bybit_key,
                api_secret=bybit_secret,
                **exchange_kwargs
            )
            if verbose: print(f"✅ Bridge: Connected to Bybit")
            
        # 3. Alpaca
        alp_key = (self.config.get('alpaca_key') or 
                   os.getenv('ALPACA_API_KEY') or 
                   os.getenv('APCA_API_KEY_ID'))
        alp_sec = (self.config.get('alpaca_secret') or 
                   os.getenv('ALPACA_API_SECRET') or 
                   os.getenv('ALPACA_SECRET_KEY') or 
                   os.getenv('APCA_API_SECRET_KEY'))
        
        if alp_key and alp_sec:
             # Smart Mode Detection:
             # 1. Respect PAPER_MODE env if strictly set
             # 2. Otherwise detect from Key Prefix (AK = Live, PK = Paper)
             # 3. Default to True (Paper) for safety
             
             env_paper = os.getenv('PAPER_MODE')
             if env_paper is not None:
                 paper_mode = env_paper.lower() == 'true'
             elif alp_key.startswith('AK'):
                 paper_mode = False
             else:
                 paper_mode = True
                 
             # URL-based override (legacy compatibility)
             base_url = os.getenv('APCA_API_BASE_URL', '').lower()
             if base_url and 'paper' not in base_url and 'api.alpaca' in base_url:
                 paper_mode = False
                 
             await self.bridge.connect_exchange(
                'ALPACA',
                api_key=alp_key.strip(),
                api_secret=alp_sec.strip(),
                paper=paper_mode,
                url_override=os.getenv('APCA_API_BASE_URL'),
                **exchange_kwargs
            )
             if verbose: print(f"✅ Bridge: Connected to Alpaca")
             
        return True
    


    def calculate_dynamic_size(self, equity: float, price: float, sl_price: float, leverage: int, min_notional: float) -> float:
        """
        Calculates position size based on Risk Per Trade (e.g. 1% of Equity).
        Formula: Risk Amount / Distance to SL
        """
        from system_directive import RISK_PER_TRADE_PCT
        
        # 1. Determine Risk Percentage
        risk_pct = RISK_PER_TRADE_PCT
        
        # --- KELLY CRITERION LOGIC ---
        if self.config.get('use_kelly_criterion', False):
            try:
                p = self.config.get('win_rate_est', 0.55)
                b = self.config.get('risk_reward_est', 1.5)
                fraction = self.config.get('kelly_fraction', 0.5)
                
                # Kelly Formula: f = p - (q / b)
                q = 1 - p
                kelly_optimal = p - (q / b)
                
                # Apply Fraction (Safety)
                kelly_risk = kelly_optimal * fraction
                
                if kelly_risk > 0:
                    # Log the difference if significant
                    if abs(kelly_risk - risk_pct) > 0.01:
                         print(f"🧠 Kelly Sizing: {kelly_risk:.2%} risk (vs Base {risk_pct:.2%})")
                    risk_pct = kelly_risk
                else:
                    print("⚠️ Kelly suggests 0% or negative allocation. Reverting to base risk.")
            except Exception as e:
                print(f"⚠️ Kelly Calculation Error: {e}")
                
        # 2. Calculate Risk Amount ($)
        risk_amount = equity * risk_pct
        
        # 3. Calculate Distance to SL
        dist_to_sl = abs(price - sl_price)
        if dist_to_sl <= 0: return 0.0
        
        # 4. Raw Quantity (Units)
        raw_qty = risk_amount / dist_to_sl
        
        # 5. Cap at Max Capital Allocation (Safety Net)
        max_cap_val = equity * self.config.get('max_capital_pct', 0.10) * leverage
        max_qty_cap = max_cap_val / price
        
        # 6. Check Available Margin (Smart Sizing)
        # Fetch real-time available balance from ShadowWallet
        try:
             # Wait for wallet details (async call not allowed here if sync, but this method is sync?)
             # Wait, calculate_dynamic_size is NOT async in definition but get_wallet_details IS async.
             # We should make calculate_dynamic_size async or use synchronous shadow wallet access.
             # ShadowWallet access is synchronous (dict lookup).
             
             # Direct ShadowWallet Access for speed
             bin_bal = self.shadow_wallet.balances.get('BINANCE', {})
             available = bin_bal.get('available', 0.0)
             
             # Buffer: Leave 5% margin free
             usable_margin = available * 0.95
             
             if usable_margin > 0:
                 max_affordable_qty = (usable_margin * leverage) / price
                 
                 if raw_qty > max_affordable_qty:
                     print(f"⚠️ Sizing Reduced: Margin {usable_margin:.2f} limits qty to {max_affordable_qty:.4f}")
                     raw_qty = max_affordable_qty
        except Exception:
             pass # Fallback to equity-based calculation
        
        final_qty = min(raw_qty, max_qty_cap)
        
        # 7. Min Notional Check
        if (final_qty * price) < min_notional:
             # If risk-based size is too small, check if we can bump to min_notional 
             # without exceeding 2x risk. If so, allowed. Else, skip.
             min_qty = (min_notional * 1.05) / price
             implied_risk = min_qty * dist_to_sl
             if implied_risk <= (risk_amount * 2): # Allow slight risk stretch
                 return min_qty
             else:
                 return 0.0 # Too risky
                 
        return final_qty
    

    async def initialize_alpaca(self, verbose: bool = True):
        """Initialize Alpaca client from per-user config, with ENV fallback for admins only."""
        # Check if this user is an admin (allow ENV fallback for owners)
        admin_ids = os.getenv('TELEGRAM_ADMIN_ID', '').replace(' ', '').split(',')
        is_admin = str(self.chat_id) in admin_ids
        
        # Get credentials: per-user config first, ENV fallback only for admins
        ak = self.config.get('alpaca_key', '').strip() if self.config.get('alpaca_key') else ''
        ask = self.config.get('alpaca_secret', '').strip() if self.config.get('alpaca_secret') else ''
        
        # ENV fallback ONLY for admins
        if not ak and is_admin:
            ak = os.getenv('APCA_API_KEY_ID', '').strip().strip("'\"")
        if not ask and is_admin:
            ask = os.getenv('APCA_API_SECRET_KEY', '').strip().strip("'\"")
        
        base_url = os.getenv('APCA_API_BASE_URL', '').strip().strip("'\"")
        
        if ak and ask:
            try:
                # Determine paper mode
                paper = True
                if base_url:
                    if base_url.endswith('/v2'):
                        base_url = base_url[:-3]
                    if 'paper' not in base_url and 'api.alpaca' in base_url:
                        paper = False
                
                self.alpaca_client = TradingClient(ak, ask, paper=paper, url_override=base_url)
                
                if verbose:
                    print(f"✅ [Chat {self.chat_id}] Alpaca Client Initialized (Paper: {paper})")
            except Exception as e:
                if verbose:
                    print(f"❌ [Chat {self.chat_id}] Alpaca Init Error: {e}")
    
    async def close(self):
        """Cleanup all resources including NexusBridge adapters."""
        try:
            # Close NexusBridge (handles all adapters: Binance, Bybit, Alpaca)
            if self.bridge:
                await self.bridge.close_all()
        except Exception as e:
            print(f"⚠️ Error closing bridge for session {self.chat_id}: {e}")
    
    # --- CONFIG METHODS ---
    
    def set_mode(self, mode: str) -> bool:
        """Set operation mode."""
        if mode in ['WATCHER', 'COPILOT', 'PILOT']:
            self.mode = mode
            self.config['mode'] = mode
            return True
        return False
    
    async def update_config(self, key: str, value: Any) -> bool:
        """Update a config value."""
        self.config[key] = value
        return True
    
    def get_configuration(self) -> Dict:
        """Get current configuration."""
        return {
            "mode": self.mode,
            "leverage": self.config['leverage'],
            "max_capital_pct": self.config['max_capital_pct'],
            "stop_loss_pct": self.config['stop_loss_pct'],
            "has_keys": bool(self.client),
            "strategies": self.config.get('strategies', {}),
            "groups": self.config.get('groups', {}),
            "disabled_assets": self.config.get('disabled_assets', [])
        }
        
    def toggle_strategy(self, strategy: str) -> bool:
        """Toggle a specific strategy on/off."""
        strategies = self.config.get('strategies', {})
        current = strategies.get(strategy, False)
        strategies[strategy] = not current
        self.config['strategies'] = strategies
        return strategies[strategy]

    def is_strategy_enabled(self, strategy: str) -> bool:
        """Check if strategy is enabled. Default TRUE for most strategies."""
        # Default to True for most strategies (except SHARK which is aggressive)
        default = False if strategy == 'SHARK' else True
        return self.config.get('strategies', {}).get(strategy, default)

    def toggle_group(self, group: str) -> bool:
        """Toggle a specific asset group on/off."""
        groups = self.config.get('groups', {})
        current = groups.get(group, False)
        groups[group] = not current
        self.config['groups'] = groups
        return groups[group]

    def is_group_enabled(self, group: str) -> bool:
        """
        Check if group is enabled FOR THIS USER.
        Fetches from DB (per-user preferences) first, falls back to session config.
        """
        # Try DB first (per-user preferences)
        from servos.db import get_user_enabled_groups
        user_groups = get_user_enabled_groups(self.chat_id)
        if user_groups:
            return user_groups.get(group, True)
        # Fallback to session config (legacy)
        return self.config.get('groups', {}).get(group, True)

    def toggle_asset_blacklist(self, symbol: str) -> bool:
        """Toggle asset in blacklist. Returns True if now DISABLED (in list)."""
        disabled = self.config.get('disabled_assets', [])
        if symbol in disabled:
            disabled.remove(symbol)
            result = False
        else:
            disabled.append(symbol)
            result = True
        self.config['disabled_assets'] = disabled
        return result

    def is_asset_disabled(self, symbol: str) -> bool:
        """Check if asset is in blacklist."""
        return symbol in self.config.get('disabled_assets', [])
    
    # --- HELPER METHODS ---
    
    async def get_symbol_precision(self, symbol: str) -> Tuple[int, int, float, float]:
        """
        Returns (quantityPrecision, pricePrecision, minNotional, tickSize)
        tickSize es el tamaño de tick real de Binance para redondeo correcto.
        """
        # Default Fallback High Precision (6) to avoid 0.0 on PEPE/SHIB
        default_q, default_p, default_n, default_tick = 2, 6, 5.0, 0.01
        
        if not self.bridge: 
            return default_q, default_p, default_n, default_tick
        
        try:
            info = await self.bridge.get_symbol_info(symbol)
            if info:
                q = info.get('quantity_precision', default_q)
                p = info.get('price_precision', default_p)
                n = info.get('min_notional', default_n)
                tick_size = info.get('tick_size', default_tick)  # NEW: Get real tick size
                
                # Validar tick_size
                if tick_size <= 0:
                    tick_size = default_tick
                
                # Log de precisión ajustada (solo en modo debug)
                self.logger.debug(f"Precisión {symbol}: Q={q}, P={p}, N={n}, TickSize={tick_size}")
                return (q, p, n, tick_size)
            else:
                print(f"⚠️ No Info for {symbol}, using calculated defaults (P={default_p}, TickSize={default_tick})", flush=True)
                
        except Exception as e:
            print(f"⚠️ Precision Error (Bridge) {symbol}: {e}", flush=True)
            
        return default_q, default_p, default_n, default_tick
    
    async def _fetch_ohlcv_for_chart(self, symbol: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch historical klines for chart generation."""
        try:
            klines = await self.client.futures_klines(symbol=symbol, interval='15m', limit=limit)
            data = []
            for k in klines:
                data.append({
                    'timestamp': int(k[0]),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            return pd.DataFrame(data)
        except Exception as e:
            print(f"⚠️ Chart Data Fetch Error: {e}")
            return None

    # --- RISK HELPER: CORRELATION GUARD (Shield 2.0) ---
    async def _check_correlation_safeguard(self, candidate_symbol: str) -> Tuple[bool, str]:
        """
        Checks if adding candidate_symbol violates portfolio correlation limits.
        Uses cached market data from NexusCore engine via SessionManager.
        """
        if not self.manager or not self.manager.engine:
            # Fallback: If no engine (standalone mode), skip check or be strict?
            # Defaulting to Safe to not block trading if engine is offline, but logging warning.
            return True, ""
            
        try:
            # 1. Get Active Positions
            active_pos = await self.get_active_positions()
            active_symbols = [p['symbol'] for p in active_pos if 'USDT' in p['symbol']] # Crypto only
            
            # Filter out self (if re-entering/adding to same pos)
            active_symbols = [s for s in active_symbols if s != candidate_symbol]
            
            if not active_symbols:
                return True, ""
            
            # 2. Update History for Active Positions
            # Fetch from Engine's MarketStream (Memory Cache)
            stream = self.manager.engine.market_stream
            
            # Prepare Candidate Data first
            cand_data = await stream.get_candles(candidate_symbol, limit=60)
            if cand_data['dataframe'].empty:
                return True, "" # Not enough data to correlation check
                
            cand_prices = cand_data['dataframe']['close']
            
            # Check against each active position
            # We pass the active_symbols list to manager, but manager needs their history updated first
            for pos_sym in active_symbols:
                pos_data = await stream.get_candles(pos_sym, limit=60)
                if not pos_data['dataframe'].empty:
                    self.correlation_manager.update_price_history(pos_sym, pos_data['dataframe']['close'])
            
            # 3. Perform Check
            is_safe = self.correlation_manager.check_correlation(
                candidate_symbol, 
                cand_prices, 
                active_symbols
            )
            
            if not is_safe:
                return False, f"🚫 **Shield Protocol**: Alta correlación detectada."
                
            return True, ""
            
        except Exception as e:
            print(f"⚠️ Correlation Check Error: {e}")
            return True, "" # Fail Safe (Allow trade)

    # --- TRADING METHODS ---
    
    async def _ensure_client(self) -> Tuple[bool, str]:
        """Ensure Binance client is initialized."""
        if self.client:
            return True, ""
        
        # Try to re-initialize lazy
        print(f"🔄 [Chat {self.chat_id}] Attempting lazy re-initialization...")
        await self.initialize()
        err = getattr(self, '_init_error', 'Unknown Error')
        return False, f"Client Connection Failed: {err}"

    async def _place_order_with_retry(self, func, **kwargs):
        """Helper: Place order with retries for -1007/Timeout"""
        for attempt in range(1, 4):
            try:
                return await func(**kwargs)
            except Exception as e:
                if "timeout" in str(e).lower() or "network" in str(e).lower() or "-1007" in str(e):
                    if attempt < 3:
                        await asyncio.sleep(attempt)
                        continue
                raise e
        raise Exception("Max retries exceeded")

    async def get_open_algo_orders(self, symbol: str) -> list:
        """
        Fetch open algo orders (conditional orders like SL/TP/Trailing).
        Uses NexusBridge for CCXT compatibility.
        """
        try:
            if not self.bridge:
                return []
            
            # Use Bridge to get open orders
            orders = await self.bridge.get_open_orders(symbol)
            
            # Filter for algo-type orders (conditional orders)
            algo_types = ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET', 
                         'STOP', 'TAKE_PROFIT', 'TRAILING_STOP',
                         'stop_market', 'take_profit_market', 'trailing_stop_market']
            algo_orders = [o for o in orders if o.get('type', '').upper() in [t.upper() for t in algo_types]]
            
            return algo_orders
        except Exception as e:
            print(f"⚠️ Error fetching algo orders for {symbol}: {e}")
            return []

    async def smart_breakeven_check(self, breakeven_roi_threshold: float = 0.10) -> str:
        """Check positions and move SL to Beakeven if ROI > threshold."""
        report = []
        try:
            positions = await self.bridge.get_positions()
            for pos in positions:
                symbol = pos['symbol']
                qty = float(pos['quantity'])
                if qty == 0: continue
                
                entry = float(pos['entry_price'])
                if entry <= 0: continue
                
                curr = await self.bridge.get_last_price(symbol)
                side = pos['side']
                
                # Check current price validity
                if curr <= 0: continue

                pnl_pct = (curr - entry)/entry if side == 'LONG' else (entry - curr)/entry
                
                if pnl_pct >= breakeven_roi_threshold:
                    # Cancel existing SL
                    await self.bridge.cancel_orders(symbol)
                    
                    # Place New SL at Entry
                    qty_prec, price_prec, _, tick_size = await self.get_symbol_precision(symbol)
                    sl_price = round_to_tick_size(entry, tick_size)
                    
                    sl_side = 'SELL' if side == 'LONG' else 'BUY'
                    # Place conditional order - price arg is stopPrice for conditional orders
                    result = await self.bridge.place_order(
                        symbol, sl_side, 'STOP_MARKET', 
                        quantity=qty, price=sl_price,
                        reduceOnly=True
                    )
                    if result.get('error'):
                        report.append(f"⚠️ {symbol}: SL Error - {result['error']}")
                        continue
                    report.append(f"✅ {symbol}: Reset SL to Entry (ROI {pnl_pct:.1%})")
                    
        except Exception as e:
            report.append(f"❌ Breakeven Check Error: {str(e)}")
            
        return "\n".join(report) if report else "No changes."

    async def execute_refresh_all_orders(self) -> str:
        """Ensure all open positions have SL/TP attached."""
        report = []
        try:
            positions = await self.bridge.get_positions()
            for pos in positions:
                symbol = pos['symbol']
                qty = float(pos['quantity'])
                if qty == 0: continue
                
                # Check existing orders
                orders = await self.get_open_algo_orders(symbol)
                has_sl = any(o.get('type') in ['STOP_MARKET', 'STOP'] for o in orders)
                has_tp = any(o.get('type') in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT'] for o in orders)
                
                if not has_sl or not has_tp:
                    # Recalculate and Place
                    entry = float(pos['entry_price'])
                    curr = await self.bridge.get_last_price(symbol)
                    
                    stop_loss_pct = self.config.get('stop_loss_pct', 0.02)
                    tp_ratio = self.config.get('tp_ratio', 1.5)
                    qty_prec, price_prec, _, tick_size = await self.get_symbol_precision(symbol)
                    
                    sl_dist = entry * stop_loss_pct
                    side = pos['side']
                    
                    if side == 'LONG':
                        sl_price = round_to_tick_size(entry - sl_dist, tick_size)
                        tp_price = round_to_tick_size(entry + (sl_dist * tp_ratio), tick_size)
                        order_side = 'SELL'
                    else: # SHORT
                        sl_price = round_to_tick_size(entry + sl_dist, tick_size)
                        tp_price = round_to_tick_size(entry - (sl_dist * tp_ratio), tick_size)
                        order_side = 'BUY'
                        
                    # Log de cálculos de SL (solo en modo debug)
                    raw_sl = entry - sl_dist if side == 'LONG' else entry + sl_dist
                    self.logger.debug(f"Cálculo SL {symbol}: Entry={entry}, SL%={stop_loss_pct:.2%}, Prec={price_prec}, RawSL={raw_sl:.4f} -> Final={sl_price:.4f}")
                    
                    # SAFETY: Re-apply tick size rounding if prices are invalid
                    # Esto asegura que los precios sean válidos después del redondeo
                    if sl_price <= 0 and entry > 0:
                        raw_sl = entry - sl_dist if side=='LONG' else entry + sl_dist
                        sl_price = round_to_tick_size(raw_sl, tick_size)
                    
                    if tp_price <= 0 and entry > 0:
                        raw_tp = entry + (sl_dist * tp_ratio) if side=='LONG' else entry - (sl_dist * tp_ratio)
                        tp_price = round_to_tick_size(raw_tp, tick_size)
                    
                    # Validación final: Si aún son 0 después del redondeo, recalcular con tick_size más pequeño
                    if sl_price <= 0 and entry > 0:
                        raw_sl = entry - sl_dist if side=='LONG' else entry + sl_dist
                        # Intentar con tick_size más pequeño si el actual causó 0
                        smaller_tick = tick_size / 10 if tick_size > 0.00001 else 0.00001
                        sl_price = round_to_tick_size(raw_sl, smaller_tick)
                        if sl_price <= 0:
                            sl_price = raw_sl  # Último recurso: usar valor sin redondeo
                    
                    if tp_price <= 0 and entry > 0:
                        raw_tp = entry + (sl_dist * tp_ratio) if side=='LONG' else entry - (sl_dist * tp_ratio)
                        # Intentar con tick_size más pequeño si el actual causó 0
                        smaller_tick = tick_size / 10 if tick_size > 0.00001 else 0.00001
                        tp_price = round_to_tick_size(raw_tp, smaller_tick)
                        if tp_price <= 0:
                            tp_price = raw_tp  # Último recurso: usar valor sin redondeo

                        
                    # Place missing orders with validation
                    if not has_sl:
                        # Validate SL won't trigger immediately
                        sl_valid = True
                        if side == 'LONG' and curr <= sl_price:
                            sl_valid = False
                            report.append(f"⚠️ {symbol}: SL Skipped (Price {curr} at/below SL {sl_price})")
                        elif side == 'SHORT' and curr >= sl_price:
                            sl_valid = False
                            report.append(f"⚠️ {symbol}: SL Skipped (Price {curr} at/above SL {sl_price})")
                        
                        if sl_valid:
                            result = await self.bridge.place_order(
                                symbol, order_side, 'STOP_MARKET', 
                                quantity=qty, price=sl_price, reduceOnly=True
                            )
                            if result.get('error'):
                                report.append(f"⚠️ {symbol}: SL Error - {result['error']}")
                            
                    if not has_tp:
                        # Validate TP won't trigger immediately
                        tp_valid = True
                        if side == 'LONG' and curr >= tp_price:
                            tp_valid = False
                            report.append(f"⚠️ {symbol}: TP Skipped (Price {curr} at/above TP {tp_price})")
                        elif side == 'SHORT' and curr <= tp_price:
                            tp_valid = False
                            report.append(f"⚠️ {symbol}: TP Skipped (Price {curr} at/below TP {tp_price})")
                        
                        if tp_valid:
                            result = await self.bridge.place_order(
                                symbol, order_side, 'TAKE_PROFIT_MARKET', 
                                quantity=qty, price=tp_price, reduceOnly=True
                            )
                            if result.get('error'):
                                report.append(f"⚠️ {symbol}: TP Error - {result['error']}")
                            else:
                                report.append(f"✅ {symbol}: Refreshed SL/TP (SL: {sl_price}, TP: {tp_price})")

                    
        except Exception as e:
            report.append(f"❌ Sync Error: {str(e)}")
            
        return "\n".join(report) if report else "All positions synced."

    async def _cancel_all_robust(self, symbol: str, verify: bool = True) -> bool:
        """
        Cancela todas las órdenes abiertas (estándar + condicionales) de forma robusta.
        
        Problema conocido con Binance:
        - cancel_all_orders() puede no cancelar órdenes condicionales correctamente
        - Requiere cancelación individual de órdenes condicionales
        
        Lógica:
        1. Obtener todas las órdenes abiertas (incluyendo condicionales)
        2. Cancelar todas las órdenes vía bridge (que maneja cancelación individual)
        3. Verificar que no queden órdenes (opcional, con retry)
        4. Limpiar tracking de órdenes algo
        
        Returns: True si todas las órdenes fueron canceladas, False si algunas permanecen
        """
        if not self.bridge:
            return True  # No bridge significa no hay órdenes
            
        try:
            # 1. Obtener todas las órdenes abiertas vía bridge
            all_orders = await self.bridge.get_open_orders(symbol)
            
            if not all_orders:
                # Limpiar tracking dict
                if symbol in self.active_algo_orders:
                    del self.active_algo_orders[symbol]
                self.logger.info(f"🧹 {symbol}: No open orders to cancel", group=False)
                return True
                
            self.logger.info(f"🧹 {symbol}: Cancelling {len(all_orders)} existing orders (bridge)", group=False)
            
            # 2. Cancelar todas las órdenes vía bridge
            # BinanceAdapter ahora cancela órdenes condicionales individualmente
            success = await self.bridge.cancel_orders(symbol)
            
            if not success:
                self.logger.warning(f"⚠️ {symbol}: Cancel command failed", group=False)
                return False
            
            # 3. Limpiar tracking de órdenes algo
            if symbol in self.active_algo_orders:
                del self.active_algo_orders[symbol]
            
            # 4. Verificar con retry (opcional, agrega latencia pero asegura cancelación)
            if verify:
                # Binance puede tardar hasta 1 segundo en actualizar el estado
                for attempt in range(3):
                    await asyncio.sleep(0.5 + (attempt * 0.3))  # 0.5s, 0.8s, 1.1s
                    remaining = await self.bridge.get_open_orders(symbol)
                    if not remaining:
                        self.logger.info(f"✅ {symbol}: All orders cancelled and verified", group=False)
                        return True
                    
                    # Si aún quedan órdenes, intentar cancelar nuevamente
                    if attempt < 2:
                        self.logger.warning(f"🔄 {symbol}: {len(remaining)} orders still remain, retrying cancellation...", group=False)
                        await self.bridge.cancel_orders(symbol)
                
                # Si después de 3 intentos aún quedan órdenes
                remaining = await self.bridge.get_open_orders(symbol)
                if remaining:
                    self.logger.warning(f"⚠️ {symbol}: {len(remaining)} orders still remain after {3} attempts", group=False)
                    for order in remaining:
                        self.logger.warning(f"   - Remaining: {order.get('type')} {order.get('orderId')}", group=False)
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"❌ _cancel_all_robust error for {symbol}: {e}", group=False)
            return False


    async def _place_conditional_with_tracking(
        self, symbol: str, order_type: str, side: str, 
        quantity: float, stop_price: float, **kwargs
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Place conditional order and track algoId for later cancellation.
        Uses NexusBridge for proper CCXT compatibility.
        
        Args:
            symbol: Trading pair
            order_type: STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
            side: BUY or SELL
            quantity: Order quantity
            stop_price: Trigger price (or activation for trailing)
            **kwargs: Additional params (callbackRate for trailing, etc)
            
        Returns: (success, message, algoId)
        """
        try:
            # Build params for conditional order
            params = {
                'stopPrice': stop_price,
                'reduceOnly': True,
                **kwargs
            }
            
            # Use Bridge for CCXT-compatible order placement with retry
            result = None
            for attempt in range(1, 4):
                try:
                    result = await self.bridge.place_order(
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        quantity=quantity,
                        price=stop_price,
                        **params
                    )
                    if 'error' in result:
                        raise Exception(result['error'])
                    break
                except Exception as e:
                    if "timeout" in str(e).lower() or "network" in str(e).lower() or "-1007" in str(e):
                        if attempt < 3:
                            await asyncio.sleep(attempt)
                            continue
                    raise e
            
            if not result:
                raise Exception("Max retries exceeded")
            
            # Extract algoId (or orderId for standard)
            algo_id = str(result.get('orderId', ''))
            
            # Store in tracking dict
            if symbol not in self.active_algo_orders:
                self.active_algo_orders[symbol] = {}
            
            # Determine key based on order type
            if 'STOP' in order_type and 'TRAILING' not in order_type and 'TAKE_PROFIT' not in order_type:
                type_key = 'sl_id'
            elif 'TAKE_PROFIT' in order_type:
                type_key = 'tp_id'
            else:
                type_key = 'trail_id'
                
            self.active_algo_orders[symbol][type_key] = algo_id
            print(f"✅ {symbol}: Placed {order_type} @ {stop_price} (ID: {algo_id})")
            
            return True, f"{order_type} @ {stop_price}", algo_id
            
        except Exception as e:
            print(f"⚠️ {symbol}: Failed to place {order_type}: {e}")
            return False, str(e), None

    async def synchronize_sl_tp_safe(
        self, 
        symbol: str, 
        quantity: float, 
        sl_price: float, 
        tp_price: float, 
        side: str, 
        min_notional: float, 
        qty_precision: int, 
        entry_price: float = 0.0, 
        current_price: float = 0.0
    ) -> Tuple[bool, str]:
        """
        Sincronización quirúrgica de SL/TP (V2 - Anti-Spam).
        
        Este método sincroniza stop loss y take profit de forma inteligente:
        1. Verifica si ya existe SL/TP válido (omite si está dentro de 1% de tolerancia)
        2. Cancela órdenes existentes (STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET)
        3. Verifica que la cancelación fue exitosa antes de continuar
        4. Coloca nuevos SL/TP con reduceOnly=True
        5. Valida triggers contra precio actual para evitar error -2021
        
        Args:
            symbol: Símbolo del activo
            quantity: Cantidad de la posición
            sl_price: Precio de stop loss
            tp_price: Precio de take profit
            side: Lado de la posición ('LONG' o 'SHORT')
            min_notional: Valor mínimo de orden
            qty_precision: Precisión de cantidad
            entry_price: Precio de entrada (para validación)
            current_price: Precio actual del mercado (para validación)
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        try:
            # Validación inicial: Precios deben ser válidos
            if sl_price <= 0:
                return False, f"⚠️ {symbol}: SL inválido (precio: {sl_price})"
            if tp_price <= 0:
                return False, f"⚠️ {symbol}: TP inválido (precio: {tp_price})"
            
            # Validación: Entry price debe ser válido para cálculos
            if entry_price <= 0:
                entry_price = current_price if current_price > 0 else sl_price
            
            # Validación: Current price debe ser válido
            if current_price <= 0:
                current_price = entry_price
            # 1. Fetch existing orders via bridge
            orders = await self.bridge.get_open_orders(symbol)
            
            existing_sl = None
            existing_tp_count = 0
            
            for o in orders:
                # Handle both standard and algo order formats
                order_type = o.get('type', '') or o.get('algoType', '')
                if order_type in ['STOP_MARKET', 'STOP']:
                    existing_sl = float(o.get('stopPrice', 0) or o.get('triggerPrice', 0))
                elif order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'TRAILING_STOP_MARKET', 'TRAILING_STOP']:
                    existing_tp_count += 1
            
            # 2. Check if existing SL is within 1% tolerance - SKIP UPDATE
            if existing_sl and sl_price > 0:
                tolerance = abs(existing_sl - sl_price) / sl_price
                if tolerance < 0.01 and existing_tp_count >= 1:
                    return True, f"✅ SL/TP ya configurados (SL: {existing_sl:.2f}, TP count: {existing_tp_count}). Sin cambios."
            
            # 3. Cancel existing SL/TP orders - FORCE CLEANUP (Standard + Algo)
            # Uses _cancel_all_robust which now includes verification
            # 3. Cancel existing SL/TP orders - FORCE CLEANUP (Standard + Algo)
            # Uses _cancel_all_robust which now includes verification
            try:
                # Retry loop for cancellation
                cleared = False
                for _ in range(2):
                    cleared = await self._cancel_all_robust(symbol, verify=True)
                    if cleared:
                        break
                    await asyncio.sleep(0.5)
                
                if not cleared:
                    print(f"⚠️ {symbol}: Cancellation failed (orders remain). Aborting Sync to avoid duplicates.")
                    return False, "⚠️ Sync Aborted: Could not clear existing orders."
                    
            except Exception as e:
                print(f"⚠️ Error cancelling orders for {symbol}: {e}")
                return False, f"Sync Error (Cancel): {e}"
            
            # 5. Place new SL (reduceOnly) with -2021 check
            sl_msg = ""
            abs_qty = abs(quantity)
            sl_side = 'SELL' if side == 'LONG' else 'BUY'
            
            # Validation SL - FIX: Correct direction check
            valid_sl = True
            if current_price > 0:
                if side == 'LONG' and current_price <= sl_price:
                    sl_msg = f"⚠️ SL Skipped: Price ({current_price}) at/below Stop ({sl_price})"
                    valid_sl = False
                elif side == 'SHORT' and current_price >= sl_price:
                    sl_msg = f"⚠️ SL Skipped: Price ({current_price}) at/above Stop ({sl_price})"
                    valid_sl = False
            
            if sl_price > 0 and valid_sl:
                result = await self.bridge.place_order(
                    symbol=symbol, side=sl_side, order_type='STOP_MARKET',
                    quantity=abs_qty, price=sl_price
                    # NOTE: reduceOnly=True removed for conditional orders - not supported by Bybit
                )
                if result.get('error'):
                    error_code = result.get('code')
                    if error_code == -2021:
                        sl_msg = f"⚠️ SL Error: Precio de activación ya alcanzado. Ajusta el stopPrice."
                    else:
                        sl_msg = f"⚠️ SL Error: {result['error']}"
                else:
                    sl_msg = f"SL: {sl_price}"
                
            # 6. Place TP (split or single trailing) with -2021 check
            tp_msg = ""
            
            qty_tp1 = float(round(abs_qty / 2, qty_precision))
            qty_trail = float(round(abs_qty - qty_tp1, qty_precision))
            
            # Check split feasibility
            ref_price = current_price if current_price > 0 else (sl_price if sl_price > 0 else tp_price)
            is_split = ref_price > 0 and (qty_tp1 * ref_price) > min_notional and (qty_trail * ref_price) > min_notional
            
            if not is_split:
                print(f"ℹ️ {symbol}: Skipping TP1 split (Position value < 2x MinNotional). Using Full Trailing.")
            
            if is_split:
                # Validation TP1 - FIX: Correct direction check
                valid_tp = True
                if current_price > 0:
                    if side == 'LONG' and current_price >= tp_price:
                        tp_msg = f"⚠️ TP Skipped: Price ({current_price}) at/above TP ({tp_price})"
                        valid_tp = False
                    elif side == 'SHORT' and current_price <= tp_price:
                        tp_msg = f"⚠️ TP Skipped: Price ({current_price}) at/below TP ({tp_price})"
                        valid_tp = False

                # TP1 (fixed) - Validar que tp_price es válido
                if valid_tp and tp_price > 0:
                    tp1_result = await self.bridge.place_order(
                        symbol=symbol, side=sl_side, order_type='TAKE_PROFIT_MARKET',
                        quantity=qty_tp1, price=tp_price
                        # NOTE: reduceOnly=True removed for conditional orders - not supported by Bybit
                    )
                    if tp1_result.get('error'):
                        print(f"⚠️ {symbol}: TP1 Error - {tp1_result['error']}")
                elif not valid_tp:
                    print(f"⚠️ {symbol}: TP1 omitido - {tp_msg}")
                
                # Trailing for rest - Validar que activation es válido
                activation = tp_price if tp_price > 0 else entry_price  # Activate at TP1 o entry
                if activation > 0:
                    trail_result = await self.bridge.place_order(
                        symbol=symbol, side=sl_side, order_type='TRAILING_STOP_MARKET',
                        quantity=qty_trail, price=activation, callbackRate=1.0
                        # NOTE: reduceOnly=True removed for conditional orders - not supported by Bybit
                    )
                    if trail_result.get('error'):
                        print(f"⚠️ {symbol}: Trailing Stop Error - {trail_result['error']}")
                else:
                    print(f"⚠️ {symbol}: Trailing Stop omitido - activation price inválido")
                tp_msg = f"TP1: {tp_price} | Trail: 1.0% (Act: {activation})"
            else:
                # Full trailing
                # Fix: Use tp_price as activation. entry_price can be invalid if currently in profit
                # (e.g. SHORT Entry 100, Current 90. Activation cannot be 100 for BUY Trailing)
                activation = tp_price if tp_price > 0 else entry_price
                if activation > 0:
                    trail_result = await self.bridge.place_order(
                        symbol=symbol, side=sl_side, order_type='TRAILING_STOP_MARKET',
                        quantity=abs_qty, price=activation, callbackRate=1.0
                        # NOTE: reduceOnly=True removed for conditional orders - not supported by Bybit
                    )
                    if trail_result.get('error'):
                        print(f"⚠️ {symbol}: Trailing Stop Error - {trail_result['error']}")
                    tp_msg = f"Trail: {activation} (1.0%)"
                else:
                    tp_msg = f"⚠️ Trailing Stop omitido - activation price inválido"
            
            return True, f"{sl_msg}\n{tp_msg}"
            
        except Exception as e:
            return False, f"Sync Error: {e}"


    async def check_liquidity(self, symbol: str) -> Tuple[bool, float, str]:
        """
        Check if we have enough 'dry powder' to open a new position.
        Returns: (is_sufficient, available_balance, message)
        """
        # 1. Get Min Notional (Minimum trade size allowed by exchange)
        qty_prec, price_prec, min_notional, tick_size = await self.get_symbol_precision(symbol)
        
        # 2. Get Available Balance (Unified via ShadowWallet/Bridge)
        # Note: We need 'available' balance, not total equity
        if not self.shadow_wallet:
             return False, 0.0, "Wallet not initialized"
             
        # Determine target exchange using NexusBridge routing (matches trade execution)
        target_exchange = 'BINANCE'  # Default
        if self.bridge:
            target_exchange = self.bridge._route_symbol(symbol)

        # Force-sync balance for target exchange BEFORE checking (avoid stale ShadowWallet data)
        if self.bridge and target_exchange in self.bridge.adapters:
            try:
                fresh_balance = await self.bridge.adapters[target_exchange].get_account_balance()
                self.shadow_wallet.update_balance(target_exchange, fresh_balance)
                print(f"✅ Balance synced for {target_exchange}: ${fresh_balance.get('available', 0):.2f}")
            except Exception as sync_err:
                print(f"⚠️ Balance Sync Error ({target_exchange}): {sync_err}")

        # Fetch balance from the CORRECT exchange (now fresh)
        balance = self.shadow_wallet.balances.get(target_exchange, {}).get('available', 0)

        # Debug: Log which exchange we're checking
        self.logger.debug(f"Liquidity Check: {symbol} -> {target_exchange} (Balance: ${balance:.2f})")
             
        # 3. Define Threshold (Min Notional + 10% buffer)
        threshold = max(min_notional * 1.1, 6.0) # Ensure at least $6 for safety
        
        if balance < threshold:
             return False, balance, f"⚠️ **Low Budget Mode:** Balance (${balance:.2f}) on {target_exchange} < Min Req (${threshold:.2f}). Pausing entries."
             
        return True, balance, "OK"

    async def execute_long_position(self, symbol: str, atr: Optional[float] = None, strategy: str = "Manual", force_exchange: str = None) -> Tuple[bool, str]:
        """Execute a LONG position asynchronously via Nexus Bridge (Refactored)."""
        
        # Log de inicio de ejecución de posición LONG
        self.logger.debug(f"Ejecutando posición LONG: {symbol}, ATR={atr}")

        # Determine target exchange using NexusBridge routing (respects BYBIT asset group)
        is_crypto = 'USDT' in symbol or 'BTC' in symbol
        if force_exchange and force_exchange in (self.bridge.adapters.keys() if self.bridge else []):
            target_exchange = force_exchange
            self.logger.debug(f"Forced routing {symbol} -> {target_exchange}")
        else:
            target_exchange = self.bridge._route_symbol(symbol) if self.bridge else ('BINANCE' if is_crypto else 'ALPACA')
            self.logger.debug(f"Auto routing {symbol} -> {target_exchange}")
        
        # Force-sync balance for target exchange (avoid stale ShadowWallet data)
        if self.bridge and target_exchange in self.bridge.adapters:
            try:
                fresh_balance = await self.bridge.adapters[target_exchange].get_account_balance()
                self.shadow_wallet.update_balance(target_exchange, fresh_balance)
            except Exception as sync_err:
                print(f"⚠️ Balance Sync Error ({target_exchange}): {sync_err}")

        
        # 1. Check existing position via Shadow Wallet
        current_pos = await self.bridge.get_position(symbol)
        net_qty = current_pos.get('quantity', 0)
        current_side = current_pos.get('side', '')
        
        if net_qty > 0:
            if current_side == 'LONG':
                 return await self.execute_update_sltp(symbol, 'LONG', atr)
            elif current_side == 'SHORT':
                 print(f"🔄 Auto-Flip Triggered: Long requested for {symbol} (Current: Short)")
                 return await self.execute_flip_position(symbol, 'LONG', atr)

        # Low Budget Check
        has_liquidity, bal, msg = await self.check_liquidity(symbol)
        if not has_liquidity:
            return False, msg

        try:
            # 2. Get Data via Bridge
            current_price = await self.bridge.get_last_price(symbol)
            if current_price <= 0: return False, f"❌ Failed to fetch price for {symbol}"
            
            # Use exchange-specific equity (BINANCE for crypto, ALPACA for stocks)
            exchange_bal = self.shadow_wallet.balances.get(target_exchange, {})
            total_equity = exchange_bal.get('total', 0)
            if total_equity == 0:
                 total_equity = self.shadow_wallet.get_unified_equity()
            
            qty_precision, price_precision, min_notional, tick_size = await self.get_symbol_precision(symbol)

            # 3. Calculate Sizing & Risk Parameters (RESPETANDO PERFILES DE RIESGO)
            base_leverage = self.config.get('leverage', 5)
            max_allowed_leverage = self.config.get('max_leverage_allowed', base_leverage)
            leverage = min(base_leverage, max_allowed_leverage) if is_crypto else 1  # No leverage for stocks

            stop_loss_pct = self.config['stop_loss_pct']
            tp_ratio = self.config.get('tp_ratio', 1.5)
            max_capital_allowed = self.config.get('max_capital_pct_allowed', self.config.get('max_capital_pct', 0.25))
            size_pct = min(self.config['max_capital_pct'], max_capital_allowed)  # RESPETAR TOPE DE PERFIL

            # --- STRATEGY OVERRIDE ---
            if strategy and strategy not in ["Manual", "Legacy"]:
                strat_instance = StrategyRegistry.instantiate(strategy)
                if strat_instance:
                    # Create stub signal for parameter calculation
                    stub_signal = Signal(
                        symbol=symbol, action='BUY', confidence=1.0, 
                        price=current_price, metadata={'atr': atr or 0}
                    )
                    try:
                        params = strat_instance.calculate_entry_params(stub_signal, total_equity, self.config)
                        # Override defaults BUT RESPETAR LÍMITES DE PERFIL
                        strategy_leverage = params.get('leverage', leverage)
                        max_allowed_leverage = self.config.get('max_leverage_allowed', strategy_leverage)
                        leverage = min(strategy_leverage, max_allowed_leverage)  # RESPETAR TOPE DE PERFIL

                        strategy_size_pct = params.get('size_pct', size_pct)
                        max_allowed_capital = self.config.get('max_capital_pct_allowed', strategy_size_pct)
                        size_pct = min(strategy_size_pct, max_allowed_capital)  # RESPETAR TOPE DE PERFIL

                        sl_price = params.get('stop_loss_price')
                        tp_price = params.get('take_profit_price')
                        
                        # Set custom prices if provided
                        if sl_price and tp_price:
                            # Strategy handled price calc
                             # Set dummy vars to skip default calc below if we use a flag?
                             # Better: Put default logic in 'else' or verify params.
                             pass
                    except Exception as e:
                        print(f"⚠️ Strategy Param Error ({strategy}): {e}")

            # Calculate Final Prices/Qty
            # Note: If strategy provided SL/TP, use them. Else use defaults.
            if 'sl_price' not in locals():
                if atr and atr > 0:
                    mult = self.config.get('atr_multiplier', 2.0)
                    sl_dist = mult * atr
                    sl_price = round_to_tick_size(current_price - sl_dist, tick_size)
                    tp_price = round_to_tick_size(current_price + (tp_ratio * sl_dist), tick_size)
                else:
                    sl_price = round_to_tick_size(current_price * (1 - stop_loss_pct), tick_size)
                    tp_price = round_to_tick_size(current_price * (1 + (stop_loss_pct * tp_ratio)), tick_size)
            
            # --- MAX SL SHIELD (Emergency Clamp) ---
            max_sl_allowed = self.config.get('max_stop_loss_pct', 0.05)
            min_allowed_sl = current_price * (1 - max_sl_allowed)
            
            if sl_price < min_allowed_sl:
                actual_pct = (current_price - sl_price) / current_price
                self.logger.warning(f"🛡️ Max SL Shield Triggered ({symbol}): Strategy requested {actual_pct:.1%} Stop. Clamped to {max_sl_allowed:.1%}")
                sl_price = round_to_tick_size(min_allowed_sl, tick_size)

            # Assign Margin & Calculate Qty (Safety Clamp)
            margin_assignment = total_equity * size_pct
            
            # Clamp to Available Balance (Buffer 5%)
            available_balance = exchange_bal.get('available', 0)
            if margin_assignment > available_balance * 0.95:
                new_margin = available_balance * size_pct
                print(f"⚠️ Sizing Clamp (Long): Requested ${margin_assignment:.2f} > Avail ${available_balance:.2f}. Reducing to {size_pct:.1%} of Avail (${new_margin:.2f}).")
                margin_assignment = new_margin

            raw_quantity = (margin_assignment * leverage) / current_price
            
            # --- USE RISK-BASED SIZING WHEN ATR IS AVAILABLE ---
            if atr and sl_price > 0:
                risk_based_qty = self.calculate_dynamic_size(
                    equity=total_equity, 
                    price=current_price, 
                    sl_price=sl_price, 
                    leverage=leverage, 
                    min_notional=min_notional
                )
                if risk_based_qty > 0:
                    # Use the more conservative of the two approaches
                    if risk_based_qty < raw_quantity:
                        print(f"📊 Risk-Based Sizing: {risk_based_qty:.4f} < Capital-Based: {raw_quantity:.4f}")
                    raw_quantity = min(raw_quantity, risk_based_qty)
            
            quantity = float(round(raw_quantity, qty_precision))
            if (quantity * current_price) < min_notional:

                 return False, f"❌ {symbol}: Insufficient capital."

            # Diagnostic logging
            notional = quantity * current_price
            margin_required = notional / leverage
            print(f"📊 {symbol} Order Details: Qty={quantity}, Price=${current_price:.4f}, Notional=${notional:.2f}")
            print(f"📊 {symbol} Risk Params: Leverage={leverage}x, Margin Required=${margin_required:.2f}, Equity=${total_equity:.2f}")

            # 4. Set Leverage BEFORE placing order (critical for margin calculation)
            lev_result = await self.bridge.set_leverage(symbol, leverage)
            print(f"📊 {symbol} Set Leverage Result: {lev_result}")
            
            # 5. Execute Market Buy
            res = await self.bridge.place_order(symbol, 'BUY', 'MARKET', quantity=quantity)
            if 'error' in res:
                print(f"❌ {symbol} Order Failed: {res}")
                return False, f"Bridge Error: {res['error']}"

            entry_price = float(res.get('price', current_price) or current_price)

            # Ensure SL/TP have minimum separation from entry price after rounding
            sl_price = ensure_price_separation(sl_price, entry_price, tick_size, 'LONG', is_sl=True)
            tp_price = ensure_price_separation(tp_price, entry_price, tick_size, 'LONG', is_sl=False)

            # 6. Place SL/TP (Separate to ensure logic holds) - NON-BLOCKING
            # For conditional orders, price arg = stopPrice (trigger price)
            # Validate prices before placing orders to avoid -2021 error
            sl_placed = False
            tp_placed = False

            try:
                sl_valid = True
                if entry_price <= sl_price:
                    print(f"⚠️ {symbol}: SL Skipped - Entry ({entry_price}) <= SL ({sl_price})")
                    sl_valid = False

                if sl_valid:
                    sl_result = await self.bridge.place_order(
                        symbol, 'SELL', 'STOP_MARKET',
                        quantity=quantity, price=sl_price
                        # NOTE: reduceOnly=True removed for conditional orders - not supported by Bybit
                    )
                    if sl_result.get('error'):
                        print(f"⚠️ {symbol}: SL Order Error - {sl_result['error']}")
                    else:
                        sl_placed = True
                        print(f"✅ {symbol}: SL Order Placed at {sl_price}")
            except Exception as sl_error:
                print(f"⚠️ {symbol}: SL Order Exception - {sl_error}")

            try:
                # Validate TP: For LONG, TP should be above entry
                tp_valid = True
                if entry_price >= tp_price:
                    print(f"⚠️ {symbol}: TP Skipped - Entry ({entry_price}) >= TP ({tp_price})")
                    tp_valid = False

                if tp_valid:
                    tp_result = await self.bridge.place_order(
                        symbol, 'SELL', 'TAKE_PROFIT_MARKET',
                        quantity=quantity, price=tp_price
                        # NOTE: reduceOnly=True removed for conditional orders - not supported by Bybit
                    )
                    if tp_result.get('error'):
                        print(f"⚠️ {symbol}: TP Order Error - {tp_result['error']}")
                    else:
                        tp_placed = True
                        print(f"✅ {symbol}: TP Order Placed at {tp_price}")
            except Exception as tp_error:
                print(f"⚠️ {symbol}: TP Order Exception - {tp_error}")

            # Generar mensaje enriquecido con personalidad
            personality = self.config.get('personality', 'STANDARD_ES')
            margin_used = notional / leverage

            message = format_position_message(
                symbol=symbol,
                side='LONG',
                quantity=quantity,
                entry_price=entry_price,
                sl_price=sl_price if sl_placed else None,
                tp_price=tp_price if tp_placed else None,
                leverage=leverage,
                total_equity=total_equity,
                margin_used=margin_used,
                target_exchange=target_exchange,
                atr_value=atr,
                strategy=strategy,
                personality=personality
            )

            # Add warning if SL/TP failed to place
            if not sl_placed or not tp_placed:
                warning_msg = ""
                if not sl_placed:
                    warning_msg += "⚠️ SL no colocado. "
                if not tp_placed:
                    warning_msg += "⚠️ TP no colocado. "
                message = f"{warning_msg}\n\n{message}"

            return True, message

        except Exception as e:
            return False, f"Execution Error: {e}"


    async def execute_short_position(self, symbol: str, atr: Optional[float] = None, strategy: str = "Manual", force_exchange: str = None) -> Tuple[bool, str]:
        """
        Ejecuta una posición SHORT de forma asíncrona mediante Nexus Bridge.
        
        Este método maneja todo el flujo de ejecución de una posición SHORT:
        1. Sincroniza balance para evitar datos obsoletos
        2. Verifica límites de capital y posición existente
        3. Calcula tamaño de posición (capital-based y risk-based)
        4. Calcula SL/TP basado en ATR o porcentaje fijo
        5. Coloca orden de entrada y órdenes condicionales (SL/TP)
        
        Args:
            symbol: Símbolo del activo (ej: 'BTCUSDT')
            atr: Valor de ATR para cálculo de riesgo (opcional)
            strategy: Nombre de la estrategia para parámetros personalizados
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        # Log de inicio de ejecución de posición SHORT
        self.logger.debug(f"Ejecutando posición SHORT: {symbol}, ATR={atr}")

        # Determine target exchange using NexusBridge routing (respects BYBIT asset group)
        is_crypto = 'USDT' in symbol or 'BTC' in symbol
        if force_exchange and force_exchange in (self.bridge.adapters.keys() if self.bridge else []):
            target_exchange = force_exchange
            self.logger.debug(f"Forced routing {symbol} -> {target_exchange}")
        else:
            target_exchange = self.bridge._route_symbol(symbol) if self.bridge else ('BINANCE' if is_crypto else 'ALPACA')
            self.logger.debug(f"Auto routing {symbol} -> {target_exchange}")
        
        # Sincronizar balance antes de verificar límites (evita datos obsoletos en ShadowWallet)
        if self.bridge and target_exchange in self.bridge.adapters:
            try:
                fresh_balance = await self.bridge.adapters[target_exchange].get_account_balance()
                self.shadow_wallet.update_balance(target_exchange, fresh_balance)
            except Exception as sync_err:
                print(f"⚠️ Balance Sync Error ({target_exchange}): {sync_err}")

        
        # 1. Check existing position via Shadow Wallet
        current_pos = await self.bridge.get_position(symbol)
        net_qty = current_pos.get('quantity', 0)
        current_side = current_pos.get('side', '')
        
        if net_qty > 0:
            if current_side == 'SHORT':
                 return await self.execute_update_sltp(symbol, 'SHORT', atr)
            elif current_side == 'LONG':
                 print(f"🔄 Auto-Flip Triggered: Short requested for {symbol} (Current: Long)")
                 return await self.execute_flip_position(symbol, 'SHORT', atr)

        # Low Budget Check
        has_liquidity, bal, msg = await self.check_liquidity(symbol)
        if not has_liquidity:
            return False, msg

        try:
            # 2. Get Data via Bridge
            current_price = await self.bridge.get_last_price(symbol)
            if current_price <= 0: return False, f"❌ Failed to fetch price for {symbol}"
            
            # Use exchange-specific equity (BINANCE for crypto, ALPACA for stocks)
            exchange_bal = self.shadow_wallet.balances.get(target_exchange, {})
            total_equity = exchange_bal.get('total', 0)
            if total_equity == 0:
                 total_equity = self.shadow_wallet.get_unified_equity()
            
            qty_precision, price_precision, min_notional, tick_size = await self.get_symbol_precision(symbol)

            # 3. Calculate Sizing & Risk Parameters (RESPETANDO PERFILES DE RIESGO)
            base_leverage = self.config.get('leverage', 5)
            max_allowed_leverage = self.config.get('max_leverage_allowed', base_leverage)
            leverage = min(base_leverage, max_allowed_leverage) if is_crypto else 1  # No leverage for stocks

            stop_loss_pct = self.config['stop_loss_pct']
            tp_ratio = self.config.get('tp_ratio', 1.5)
            max_capital_allowed = self.config.get('max_capital_pct_allowed', self.config.get('max_capital_pct', 0.25))
            size_pct = min(self.config['max_capital_pct'], max_capital_allowed)  # RESPETAR TOPE DE PERFIL

            # --- STRATEGY OVERRIDE ---
            if strategy and strategy not in ["Manual", "Legacy"]:
                strat_instance = StrategyRegistry.instantiate(strategy)
                if strat_instance:
                    stub_signal = Signal(
                        symbol=symbol, action='SELL', confidence=1.0, 
                        price=current_price, metadata={'atr': atr or 0}
                    )
                    try:
                        params = strat_instance.calculate_entry_params(stub_signal, total_equity, self.config)
                        leverage = params.get('leverage', leverage)
                        size_pct = params.get('size_pct', size_pct)
                        sl_price = params.get('stop_loss_price')
                        tp_price = params.get('take_profit_price')
                    except Exception as e:
                        print(f"⚠️ Strategy Param Error ({strategy}): {e}")

            # Calculate Final Prices/Qty
            if 'sl_price' not in locals():
                if atr and atr > 0:
                    mult = self.config.get('atr_multiplier', 2.0)
                    sl_dist = mult * atr
                    sl_price = round_to_tick_size(current_price + sl_dist, tick_size)
                    tp_price = round_to_tick_size(current_price - (tp_ratio * sl_dist), tick_size)
                else:
                    sl_price = round_to_tick_size(current_price * (1 + stop_loss_pct), tick_size)
                    tp_price = round_to_tick_size(current_price * (1 - (stop_loss_pct * tp_ratio)), tick_size)
            
            # --- MAX SL SHIELD (Emergency Clamp) ---
            max_sl_allowed = self.config.get('max_stop_loss_pct', 0.05)
            max_allowed_sl = current_price * (1 + max_sl_allowed)
            
            if sl_price > max_allowed_sl:
                actual_pct = (sl_price - current_price) / current_price
                self.logger.warning(f"🛡️ Max SL Shield Triggered ({symbol}): Strategy requested {actual_pct:.1%} Stop. Clamped to {max_sl_allowed:.1%}")
                sl_price = round_to_tick_size(max_allowed_sl, tick_size)
            
            # Assign Margin & Calculate Qty (Safety Clamp)
            margin_assignment = total_equity * size_pct

            # Clamp to Available Balance (Buffer 5%)
            available_balance = exchange_bal.get('available', 0)
            if margin_assignment > available_balance * 0.95:
                new_margin = available_balance * size_pct
                print(f"⚠️ Sizing Clamp (Short): Requested ${margin_assignment:.2f} > Avail ${available_balance:.2f}. Reducing to {size_pct:.1%} of Avail (${new_margin:.2f}).")
                margin_assignment = new_margin

            raw_quantity = (margin_assignment * leverage) / current_price
            
            # --- USE RISK-BASED SIZING WHEN ATR IS AVAILABLE ---
            if atr and sl_price > 0:
                risk_based_qty = self.calculate_dynamic_size(
                    equity=total_equity, 
                    price=current_price, 
                    sl_price=sl_price, 
                    leverage=leverage, 
                    min_notional=min_notional
                )
                if risk_based_qty > 0:
                    # Use the more conservative of the two approaches
                    if risk_based_qty < raw_quantity:
                        print(f"📊 Risk-Based Sizing (Short): {risk_based_qty:.4f} < Capital-Based: {raw_quantity:.4f}")
                    raw_quantity = min(raw_quantity, risk_based_qty)
            
            quantity = float(round(raw_quantity, qty_precision))
            if (quantity * current_price) < min_notional:
                 return False, f"❌ {symbol}: Insufficient capital."


            # 4. Set Leverage BEFORE placing order (critical for margin calculation)
            await self.bridge.set_leverage(symbol, leverage)
            
            # 5. Execute Market Sell (SHORT)
            res = await self.bridge.place_order(symbol, 'SELL', 'MARKET', quantity=quantity)
            if 'error' in res:
                return False, f"Bridge Error: {res['error']}"

            entry_price = float(res.get('price', current_price) or current_price)

            # Ensure SL/TP have minimum separation from entry price after rounding
            sl_price = ensure_price_separation(sl_price, entry_price, tick_size, 'SHORT', is_sl=True)
            tp_price = ensure_price_separation(tp_price, entry_price, tick_size, 'SHORT', is_sl=False)

            # 6. Place SL/TP (Buy Orders) - NON-BLOCKING
            # SL (Buy Stop) - For SHORT, SL is above entry
            # For conditional orders, price arg = stopPrice (trigger price)
            # Validate prices before placing orders to avoid -2021 error
            sl_placed = False
            tp_placed = False

            try:
                sl_valid = True
                if entry_price >= sl_price:
                    print(f"⚠️ {symbol}: SL Skipped - Entry ({entry_price}) >= SL ({sl_price})")
                    sl_valid = False

                if sl_valid:
                    sl_result = await self.bridge.place_order(
                        symbol, 'BUY', 'STOP_MARKET',
                        quantity=quantity, price=sl_price
                        # NOTE: reduceOnly=True removed for conditional orders - not supported by Bybit
                    )
                    if sl_result.get('error'):
                        print(f"⚠️ {symbol}: SL Order Error - {sl_result['error']}")
                    else:
                        sl_placed = True
                        print(f"✅ {symbol}: SL Order Placed at {sl_price}")
            except Exception as sl_error:
                print(f"⚠️ {symbol}: SL Order Exception - {sl_error}")

            try:
                # Validate TP: For SHORT, TP should be below entry
                tp_valid = True
                if entry_price <= tp_price:
                    print(f"⚠️ {symbol}: TP Skipped - Entry ({entry_price}) <= TP ({tp_price})")
                    tp_valid = False

                if tp_valid:
                    tp_result = await self.bridge.place_order(
                        symbol, 'BUY', 'TAKE_PROFIT_MARKET',
                        quantity=quantity, price=tp_price
                        # NOTE: reduceOnly=True removed for conditional orders - not supported by Bybit
                    )
                    if tp_result.get('error'):
                        print(f"⚠️ {symbol}: TP Order Error - {tp_result['error']}")
                    else:
                        tp_placed = True
                        print(f"✅ {symbol}: TP Order Placed at {tp_price}")
            except Exception as tp_error:
                print(f"⚠️ {symbol}: TP Order Exception - {tp_error}")

            # Generar mensaje enriquecido con personalidad
            personality = self.config.get('personality', 'STANDARD_ES')
            margin_used = notional / leverage

            message = format_position_message(
                symbol=symbol,
                side='SHORT',
                quantity=quantity,
                entry_price=entry_price,
                sl_price=sl_price if sl_placed else None,
                tp_price=tp_price if tp_placed else None,
                leverage=leverage,
                total_equity=total_equity,
                margin_used=margin_used,
                target_exchange=target_exchange,
                atr_value=atr,
                strategy=strategy,
                personality=personality
            )

            # Add warning if SL/TP failed to place
            if not sl_placed or not tp_placed:
                warning_msg = ""
                if not sl_placed:
                    warning_msg += "⚠️ SL no colocado. "
                if not tp_placed:
                    warning_msg += "⚠️ TP no colocado. "
                message = f"{warning_msg}\n\n{message}"

            return True, message

                
        except Exception as e:
            print(f"⚠️ Execution Error (Short {symbol}): {e}")
            return False, f"Execution Error: {e}"

    async def get_open_algo_orders(self, symbol: str = None) -> List[Dict]:
        """
        Get open ALGO orders (conditional orders) for a symbol.
        
        NOTE: The Algo Service endpoint may not be available for all accounts.
        After Dec 2024, conditional orders (STOP_MARKET, TAKE_PROFIT_MARKET, 
        TRAILING_STOP_MARKET) should appear in regular futures_get_open_orders.
        
        This function checks both the Algo Service AND filters standard orders
        for conditional types.
        """
        if not self.client: return []
        
        conditional_orders = []
        
        # 1. Use Bridge to get open orders (consistent format)
        try:
            standard_orders = await self.bridge.get_open_orders(symbol)
            conditional_types = ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET', 
                                'STOP', 'TAKE_PROFIT', 'TRAILING_STOP',
                                'stop_market', 'take_profit_market', 'trailing_stop_market']
            
            for order in standard_orders:
                order_type = order.get('type', '')
                if order_type.upper() in [t.upper() for t in conditional_types]:
                    conditional_orders.append(order)
        except Exception as e:
            print(f"⚠️ Standard order check error ({symbol}): {e}")
        
        # 2. Try Algo Service endpoint (may not be available for all accounts)
        # Silently fail if not available - the standard orders check above is the fallback
        try:
            params = {'symbol': symbol} if symbol else {}
            
            # Try the algo endpoint - this may return 404 or error for some accounts
            result = await self.client._request(
                'get', 'algo/openOrders', signed=True, data=params
            )
            
            if isinstance(result, dict) and 'orders' in result:
                conditional_orders.extend(result['orders'])
            elif isinstance(result, list):
                conditional_orders.extend(result)
                
        except Exception:
            # Algo endpoint not available - that's OK, standard orders fallback works
            pass
        
        return conditional_orders

    async def _cancel_all_robust(self, symbol: str, verify: bool = True) -> bool:
        """
        Robust cancellation of ALL orders (Standard + Algo) via Bridge.
        """
        # Since standardizing on Nexus Bridge, we delegate to cancel_orders
        # found in cancel_algo_orders (which we updated to use Bridge too).
        
        # We can just call the bridge directly here for clarity.
        if not self.bridge: return False
        
        try:
             await self.bridge.cancel_orders(symbol)
             return True
        except Exception as e:
             print(f"⚠️ Cancel robustness warning ({symbol}): {e}")
             return False



    async def execute_close_position(self, symbol: str, only_side: str = None) -> Tuple[bool, str]:
        """Close position for a symbol via Nexus Bridge."""
        try:
            # 1. Cancel Open Orders
            await self.bridge.cancel_orders(symbol)
            
            # 2. Check Side if requested
            if only_side:
                pos = await self.bridge.get_position(symbol)
                qty = pos.get('quantity', 0)
                side = pos.get('side', '')
                if qty == 0:
                     return True, f"⚠️ No position found for {symbol}."
                if side != only_side:
                     return True, f"ℹ️ Skipped Close: {symbol} is {side}, target was {only_side}"

            # 3. Close Position
            closed = await self.bridge.close_position(symbol)
            
            # 4. Final Cleanup
            await self.bridge.cancel_orders(symbol)
            
            if closed:
                return True, f"✅ Closed {symbol}."
            else:
                return False, f"Bridge reported failure closing {symbol}."
            
        except Exception as e:
            return False, f"Close Error: {e}"

    async def execute_close_all(self) -> Tuple[bool, str]:
        """
        NUCLEAR CLOSE: Close ALL open positions and cancel ALL open orders for ALL symbols.
        Ensures no orphaned orders (standard or algo) remain anywhere in the account.
        """
        if not self.bridge:
            return False, "No valid session."
        
        try:
            # 1. Get symbols with active positions via Bridge/ShadowWallet
            # This is the most reliable source for "what am I trading?"
            active = await self.get_active_positions()
            param_symbols = {p['symbol'] for p in active}
            
            # Note: Checking for symbols with ONLY open orders (but no position) is harder
            # without a "get_all_open_orders" across all exchanges in the Bridge.
            # For now, we focus on clearing active positions which also clears their orders.
            
            all_symbols = param_symbols
            
            if not all_symbols:
                return True, "✅ No hay posiciones activas."
            
            print(f"☢️ NUCLEAR CLOSE: Cleansing {len(all_symbols)} symbols: {all_symbols}")
            
            results = []
            for sym in sorted(list(all_symbols)):
                # execute_close_position robustly cancels (pre & post) and closes position
                success, msg = await self.execute_close_position(sym)
                results.append(f"{sym}: {'✅' if success else '❌'}")
            
            return True, "🔥 Limpieza Total:\n" + "\n".join(results)
            
        except Exception as e:
            print(f"❌ Error in execute_close_all: {e}")
            return False, f"Error en Limpieza Total: {e}"

    async def execute_refresh_all_orders(self) -> str:
        """
        Refresh SL/TP/Trailing for ALL active positions.
        Forces update based on CURRENT price (Trailing) and Config (SL/TP %).
        """
        if not self.bridge:
            return "❌ No invalid session."

        try:
            active_pos = await self.get_active_positions()
            if not active_pos:
                return "ℹ️ No hay posiciones activas para sincronizar."

            # Filter: Binance & Bybit (Crypto) vs Alpaca (Stocks)
            crypto_pos = [p for p in active_pos if p.get('source') in ['BINANCE', 'BYBIT']]
            alpaca_count = len([p for p in active_pos if p.get('source') == 'ALPACA'])
            
            if not crypto_pos:
                if alpaca_count > 0:
                    return f"ℹ️ {alpaca_count} posiciones Alpaca activas (no requieren sync de SL/TP)."
                return "ℹ️ No hay posiciones activas para sincronizar."

            report = ["🔄 **Reporte de Sincronización:**", ""]
            
            # Count details for the report
            binance_count = len([p for p in crypto_pos if p.get('source') == 'BINANCE'])
            bybit_count = len([p for p in crypto_pos if p.get('source') == 'BYBIT'])
            
            if binance_count > 0: report.append(f"🔌 Binance: {binance_count} posiciones")
            if bybit_count > 0: report.append(f"🔌 Bybit: {bybit_count} posiciones")
            if alpaca_count > 0:
                report.append(f"ℹ️ {alpaca_count} posiciones Alpaca omitidas (Binance/Bybit sync only)")
            report.append("")
            
            for p in crypto_pos:
                symbol = p['symbol']
                qty = float(p['amt'])
                if qty == 0: continue

                side = 'LONG' if qty > 0 else 'SHORT'
                entry_price = float(p['entry'])
                
                # Get current price via Bridge (CCXT-compatible)
                current_price = await self.bridge.get_last_price(symbol)
                
                # Get precision
                qty_prec, price_prec, min_notional, tick_size = await self.get_symbol_precision(symbol)

                # Standard SL/TP logic:
                stop_loss_pct = self.config.get('stop_loss_pct', 0.02)
                
                # BREAKEVEN LOGIC: If profit > 1%, Move SL to Entry
                pnl_pct = (current_price - entry_price) / entry_price if side == 'LONG' else (entry_price - current_price) / entry_price
                is_in_profit_1pct = pnl_pct >= 0.01
                
                if side == 'LONG':
                    # If in 1% profit, SL = Entry. Else, SL = Entry - Default %
                    if is_in_profit_1pct:
                        sl_price = round_to_tick_size(entry_price, tick_size)
                        sl_label = "Breakeven"
                    else:
                        sl_price = round_to_tick_size(entry_price * (1 - stop_loss_pct), tick_size)
                        sl_label = f"{stop_loss_pct*100}%"
                    
                    tp_price = round_to_tick_size(entry_price * (1 + (stop_loss_pct * 3)), tick_size)
                else:
                    # Short: If in 1% profit, SL = Entry. Else, SL = Entry + Default %
                    if is_in_profit_1pct:
                        sl_price = round_to_tick_size(entry_price, tick_size)
                        sl_label = "Breakeven"
                    else:
                        sl_price = round_to_tick_size(entry_price * (1 + stop_loss_pct), tick_size)
                        sl_label = f"{stop_loss_pct*100}%"
                        
                    tp_price = round_to_tick_size(entry_price * (1 - (stop_loss_pct * 3)), tick_size)
                
                # --- MAX SL SHIELD (Emergency Clamp) ---
                max_sl_allowed = self.config.get('max_stop_loss_pct', 0.05)
                if side == 'LONG':
                    min_allowed_sl = entry_price * (1 - max_sl_allowed)
                    if sl_price < min_allowed_sl:
                        sl_price = round_to_tick_size(min_allowed_sl, tick_size)
                        sl_label = f"SHIELD ({max_sl_allowed:.1%})"
                else:
                    max_allowed_sl = entry_price * (1 + max_sl_allowed)
                    if sl_price > max_allowed_sl:
                        sl_price = round_to_tick_size(max_allowed_sl, tick_size)
                        sl_label = f"SHIELD ({max_sl_allowed:.1%})"

                # Execute Sync
                success, msg = await self.synchronize_sl_tp_safe(
                    symbol, qty, sl_price, tp_price, side, min_notional, qty_prec, entry_price=entry_price, current_price=current_price
                )
                
                status_icon = "✅" if success else "⚠️"
                report.append(f"**{symbol}** ({side}) {status_icon}")
                if success:
                    # Formatear precios de forma inteligente (3 cifras después del último cero)
                    sl_formatted = format_price_smart(sl_price)
                    tp_formatted = format_price_smart(tp_price)
                    entry_formatted = format_price_smart(entry_price)
                    report.append(f"   SL: {sl_formatted} ({sl_label}) | TP: {tp_formatted}")
                    report.append(f"   TS Act: {entry_formatted} (Entry)")
                else:
                    report.append(f"   Err: {msg}")
                report.append("")

            return "\n".join(report)

        except Exception as e:
            return f"❌ Error Critical en Sync: {e}"
    
    async def execute_update_sltp(self, symbol: str, side: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """Update SL/TP for existing position. Includes spam protection."""
        if not self.client:
            return False, "No session."
        
        # PERSISTENT COOLDOWN: Check global per-symbol cooldown
        from system_directive import SLTP_UPDATE_COOLDOWN
        from nexus_system.directive import SLTP_LAST_UPDATE
        now = time.time()
        last_update = SLTP_LAST_UPDATE.get(symbol, 0)
        
        if now - last_update < SLTP_UPDATE_COOLDOWN:
            remaining = int(SLTP_UPDATE_COOLDOWN - (now - last_update))
            return False, f"⏳ {symbol} SL/TP updated recently. Wait {remaining//60}m {remaining%60}s."
        
        # OPERATION LOCK: Short-term lock to prevent concurrent updates
        if symbol in self._operation_locks:
            elapsed = now - self._operation_locks[symbol]
            if elapsed < self._lock_duration:
                remaining = int(self._lock_duration - elapsed)
                return False, f"⏳ {symbol} update in progress. Wait {remaining}s."
        
        # Lock this symbol
        self._operation_locks[symbol] = now
        
        try:
            # Get position via Bridge
            pos = await self.bridge.get_position(symbol)
            qty = float(pos.get('quantity', 0))
            
            if qty == 0:
                return False, "No position found to update."
            
            curr_side = 'LONG' if qty > 0 else 'SHORT'
            if curr_side != side:
                return False, f"Side mismatch (Req: {side}, Has: {curr_side})."
            
            # Get new price info via Bridge
            current_price = await self.bridge.get_last_price(symbol)
            if current_price <= 0: return False, f"Failed to fetch price for {symbol}"
            
            # Get precision via Bridge function already defined
            # (No change needed here, just verifying logic flow)
            qty_precision, price_precision, min_notional, tick_size = await self.get_symbol_precision(symbol)
            
            stop_loss_pct = self.config['stop_loss_pct']
            
            # Calculate updated SL/TP
            # Use consistent tp_ratio from config (same as execute_long/short_position)
            tp_ratio = self.config.get('tp_ratio', 1.5)
            
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                if side == 'LONG':
                    sl_price = round_to_tick_size(current_price - sl_dist, tick_size)
                    tp_price = round_to_tick_size(current_price + (tp_ratio * sl_dist), tick_size)
                else:
                    sl_price = round_to_tick_size(current_price + sl_dist, tick_size)
                    tp_price = round_to_tick_size(current_price - (tp_ratio * sl_dist), tick_size)
            else:
                if side == 'LONG':
                    sl_price = round_to_tick_size(current_price * (1 - stop_loss_pct), tick_size)
                    tp_price = round_to_tick_size(current_price * (1 + (stop_loss_pct * tp_ratio)), tick_size)
                else:
                    sl_price = round_to_tick_size(current_price * (1 + stop_loss_pct), tick_size)
                    tp_price = round_to_tick_size(current_price * (1 - (stop_loss_pct * tp_ratio)), tick_size)
            
            # --- MAX SL SHIELD (Emergency Clamp) ---
            max_sl_allowed = self.config.get('max_stop_loss_pct', 0.05)
            if side == 'LONG':
                min_allowed_sl = current_price * (1 - max_sl_allowed)
                if sl_price < min_allowed_sl:
                    self.logger.warning(f"🛡️ Max SL Shield Triggered (Update {symbol}): Clamped to {max_sl_allowed:.1%}")
                    sl_price = round_to_tick_size(min_allowed_sl, tick_size)
            else:
                max_allowed_sl = current_price * (1 + max_sl_allowed)
                if sl_price > max_allowed_sl:
                    self.logger.warning(f"🛡️ Max SL Shield Triggered (Update {symbol}): Clamped to {max_sl_allowed:.1%}")
                    sl_price = round_to_tick_size(max_allowed_sl, tick_size)
            
            # Get actual entry price from position (not current market price)
            entry_price = float(pos.get('entryPrice', 0) or pos.get('entry_price', 0) or current_price)
            if entry_price <= 0:
                entry_price = current_price  # Fallback to current if entry not available
            
            # Delegate to Surgical Sync
            success, sync_msg = await self.synchronize_sl_tp_safe(
                symbol, abs(qty), sl_price, tp_price, side, min_notional, qty_precision, 
                entry_price=entry_price, current_price=current_price
            )
            
            if success:
                # Update persistent cooldown timestamp
                SLTP_LAST_UPDATE[symbol] = time.time()
                return True, (
                    f"🔄 SL/TP Updated (Surgical) for {symbol}\n"
                    f"{sync_msg}"
                )
            else:
                return False, sync_msg
            
        except Exception as e:
            return False, f"Update Error: {e}"
        finally:
            self._operation_locks.pop(symbol, None)
    
    async def execute_move_to_breakeven(self, symbol: str) -> Tuple[bool, str]:
        """
        Surgical Breakeven: Moves SL to entry price + buffer for a specific symbol.
        Used by the real-time Sniper Profit Safeguard (SPS).
        """
        try:
            # 1. Get position details from Shadow Wallet
            pos = self.shadow_wallet.positions.get(symbol)
            if not pos:
                return False, "No active position."
            
            qty = abs(float(pos.get('quantity', 0) or pos.get('amt', 0)))
            entry_price = float(pos.get('entryPrice', 0))
            side = str(pos.get('side', 'LONG')).upper()
            
            if qty <= 0 or entry_price <= 0:
                return False, "Invalid position data."
            
            # 2. Get symbol info
            qty_prec, price_prec, min_notional, tick_size = await self.get_symbol_precision(symbol)
            current_price = await self.bridge.get_last_price(symbol)
            
            # 3. Calculate Breakeven SL
            # Buffer: 0.1% to cover trading fees
            buffer = 0.001 
            if side == 'LONG':
                new_sl = round_to_tick_size(entry_price * (1 + buffer), tick_size)
                # Keep TP where it was or adjust if too close
                tp_pct = self.config.get('take_profit_pct', 0.05)
                new_tp = round_to_tick_size(entry_price * (1 + tp_pct), tick_size)
            else:
                new_sl = round_to_tick_size(entry_price * (1 - buffer), tick_size)
                tp_pct = self.config.get('take_profit_pct', 0.05)
                new_tp = round_to_tick_size(entry_price * (1 - tp_pct), tick_size)
                
            # 4. Apply via Bridge
            success, msg = await self.synchronize_sl_tp_safe(
                symbol, qty, new_sl, new_tp, side, min_notional, qty_prec, 
                entry_price=entry_price, current_price=current_price
            )
            
            if success:
                # Send alert to Telegram
                try:
                    await self.manager.bot.send_message(
                        self.chat_id, 
                        f"🛡️ **SPS: POSITION SECURED**\n"
                        f"Asset: `{symbol}`\n"
                        f"Status: SL moved to Break-Even ({new_sl})\n"
                        f"Reason: 50% TP Progress reached.",
                        parse_mode="Markdown"
                    )
                except:
                    pass
            
            return success, msg
            
        except Exception as e:
            return False, f"Breakeven Error: {e}"


    async def cleanup_orphaned_orders(self) -> Tuple[bool, str]:
        """
        Cancel orders for symbols without positions (Standard + Algo).
        Also detects 'messy' active positions (too many orders) and advises sync.
        """
        if not self.client:
            return False, "No valid session."
        
        try:
            # Get BOTH standard AND algo orders
            all_orders = await self.client.futures_get_open_orders()
            algo_orders = await self.get_open_algo_orders()
            
            active_pos = await self.get_active_positions()
            active_symbols = set(p['symbol'] for p in active_pos)
            
            orphaned = set()
            messy_active = []
            
            # Logic: Group orders by symbol
            orders_by_symbol = {s: 0 for s in active_symbols}
            
            # Check standard orders
            for order in all_orders:
                sym = order['symbol']
                if sym not in active_symbols:
                    orphaned.add(sym)
                else:
                    orders_by_symbol[sym] += 1
            
            # Check algo orders (SL/TP/Trailing)
            for order in algo_orders:
                sym = order.get('symbol', '')
                if sym and sym not in active_symbols:
                    orphaned.add(sym)
                elif sym in active_symbols:
                    orders_by_symbol[sym] += 1
            
            # Identify Messy Active Positions (> 4 orders is suspicious for single position)
            for sym, count in orders_by_symbol.items():
                if count > 4:
                    messy_active.append(f"{sym} ({count})")
            
            total_orders = len(all_orders) + len(algo_orders)
            
            # 1. Cancel Orphans
            probs = []
            if orphaned:
                canceled = 0
                for sym in orphaned:
                    try:
                        await self._cancel_all_robust(sym)
                        canceled += 1
                    except Exception as e:
                        print(f"Error canceling {sym}: {e}")
                probs.append(f"🧹 Cleaned {canceled} orphaned symbols ({', '.join(orphaned)})")
            
            # 2. Report Messy Active
            if messy_active:
                probs.append(f"⚠️ Messy positions: {', '.join(messy_active)}. Run /sync to fix.")
            
            if not probs:
                return True, f"✅ No orphaned orders. ({total_orders} orders total, {len(active_symbols)} positions)"
            
            return True, "\n".join(probs)
            
        except Exception as e:
            return False, f"Cleanup Error: {e}"
    
    async def smart_breakeven_check(self, breakeven_roi_threshold: float = 0.10) -> str:
        """
        Smart Breakeven Manager - Protects profits by moving SL to breakeven.
        
        Rules:
        - If ROI >= 10% (threshold): Move SL to entry price + small buffer
        - This locks in breakeven and prevents winning trades from going negative
        
        Called periodically or after position opens.
        """
        if not self.client:
            return "❌ No session."
        
        try:
            active_pos = await self.get_active_positions()
            if not active_pos:
                return "ℹ️ No positions to check."
            
            report = ["📊 **Breakeven Check Report:**", ""]
            modified = 0
            
            for p in active_pos:
                symbol = p['symbol']
                qty = float(p['amt'])
                entry_price = float(p['entry'])
                unrealized_pnl = float(p.get('pnl', 0))
                leverage = int(p.get('leverage', self.config.get('leverage', 5)))
                
                if qty == 0 or entry_price == 0:
                    continue
                
                side = 'LONG' if qty > 0 else 'SHORT'
                
                # Get current price via bridge
                current_price = await self.bridge.get_last_price(symbol)
                
                # Use unrealized PnL from API (confirmed correct by user)
                pnl = unrealized_pnl
                
                # Calculate ROI using Binance formula:
                # ROI = PnL / Initial_Margin
                # Initial_Margin = Notional / Leverage = (qty * entry_price) / leverage
                notional = abs(qty) * entry_price
                initial_margin = notional / leverage if leverage > 0 else notional
                
                # ROI = PnL / Initial_Margin
                if initial_margin > 0:
                    roi = pnl / initial_margin
                else:
                    roi = 0
                
                roi_pct = roi * 100
                
                # Check if ROI >= threshold (10%)
                if roi >= breakeven_roi_threshold:
                    # Time to move SL to breakeven!
                    qty_prec, price_prec, min_notional, tick_size = await self.get_symbol_precision(symbol)
                    
                    # Breakeven SL with small buffer (0.1% above entry for LONG, below for SHORT)
                    buffer = 0.001  # 0.1% buffer to cover fees
                    if side == 'LONG':
                        new_sl = round_to_tick_size(entry_price * (1 + buffer), tick_size)
                        new_tp = round_to_tick_size(current_price * 1.15, tick_size)  # Keep TP at +15% from current
                    else:
                        new_sl = round_to_tick_size(entry_price * (1 - buffer), tick_size)
                        new_tp = round_to_tick_size(current_price * 0.85, tick_size)  # Keep TP at -15% from current
                    
                    # Apply the new SL
                    try:
                        success, msg = await self.synchronize_sl_tp_safe(
                            symbol, qty, new_sl, new_tp, side, min_notional, qty_prec, 
                            entry_price=entry_price, current_price=current_price
                        )
                        if success:
                            modified += 1
                            report.append(f"✅ **{symbol}** - ROI: {roi_pct:.1f}% (PnL: ${pnl:.2f}) → SL moved to breakeven ({new_sl})")
                        else:
                            report.append(f"⚠️ **{symbol}** - ROI: {roi_pct:.1f}% → Failed: {msg}")
                    except Exception as e:
                        report.append(f"❌ **{symbol}** - Error: {e}")
                else:
                    report.append(f"⏳ **{symbol}** ({leverage}x) - ROI: {roi_pct:.1f}% (PnL: ${pnl:.2f}, Margin: ${initial_margin:.2f}) < {breakeven_roi_threshold*100:.0f}%")
            
            if modified > 0:
                report.append("")
                report.append(f"📈 **{modified} positions moved to breakeven!**")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"❌ Breakeven Check Error: {e}"

    
    async def execute_spot_buy(self, symbol: str) -> Tuple[bool, str]:
        """Execute SPOT market buy."""
        if not self.client:
            return False, "No valid session."
        
        try:
            # Get account
            acc = await self.client.get_account()
            usdt_balance = 0.0
            for asset in acc['balances']:
                if asset['asset'] == 'USDT':
                    usdt_balance = float(asset['free'])
                    break
            
            alloc_pct = self.config.get('spot_allocation_pct', 0.20)
            buy_amount = usdt_balance * alloc_pct
            
            if buy_amount < 10:
                return False, f"❌ Insufficient USDT ({usdt_balance:.2f} * {alloc_pct*100}% = {buy_amount:.2f})"
            
            # Get price
            ticker = await self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            # Calculate quantity
            raw_qty = buy_amount / price
            info = await self.client.get_symbol_info(symbol)
            step_size = 0.001
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    break
            
            precision = len(str(step_size).rstrip('0').split('.')[-1])
            quantity = round(raw_qty - (raw_qty % step_size), precision)
            
            if quantity <= 0:
                return False, "Quantity too small."
            
            # Execute
            order = await self.client.order_market_buy(symbol=symbol, quantity=quantity)
            
            fill_price = float(order.get('fills', [{}])[0].get('price', price))
            return True, f"Bought {quantity} {symbol} @ {fill_price}"
            
        except Exception as e:
            return False, f"Spot Buy Error: {e}"
    
    async def get_active_positions(self) -> List[Dict]:
        """Get list of active positions (Unified via NexusBridge)."""
        active = []
        
        # 1. Force Sync via Bridge (ensure fresh data)
        if self.bridge:
            # Track all symbols currently on exchange
            exchange_symbols = set()
            
            for name, adapter in self.bridge.adapters.items():
                try:
                    # Sync Positions
                    positions = await adapter.get_positions()
                    for pos in positions:
                        symbol = pos['symbol']
                        exchange_symbols.add(symbol)
                        self.shadow_wallet.update_position(symbol, pos)
                        
                    # Sync Balance (fast enough to do here)
                    balance = await adapter.get_account_balance()
                    self.shadow_wallet.update_balance(name, balance)
                except Exception as e:
                    print(f"⚠️ Dashboard Sync Error ({name}): {e}")
            
            # Remove closed positions (symbols in cache but not on exchange)
            stale_symbols = [s for s in self.shadow_wallet.positions.keys() if s not in exchange_symbols]
            for stale in stale_symbols:
                del self.shadow_wallet.positions[stale]
                print(f"🧹 ShadowWallet: Removed stale position {stale}")

        # 2. Read from Shadow Wallet
        for symbol, p in self.shadow_wallet.positions.items():
            try:
                raw_qty = float(p.get('quantity', 0))
                if raw_qty == 0: continue
                
                # Determine signed amount for dashboard display
                side = p.get('side', 'LONG')
                signed_amt = abs(raw_qty) if side == 'LONG' else -abs(raw_qty)
                
                # Source detection (from exchange field or fallback)
                source = p.get('exchange', 'BINANCE')
                if 'ALPACA' in str(symbol): source = 'ALPACA' # Fallback
                
                active.append({
                    'symbol': symbol,
                    'amt': signed_amt,
                    'entry': float(p.get('entryPrice', 0)),
                    'pnl': float(p.get('unrealizedPnl', 0)),
                    'leverage': int(p.get('leverage', 1)),
                    'source': source
                })
            except Exception as e:
                print(f"⚠️ Position Format Error ({symbol}): {e}")
            
        return active
    
    async def get_wallet_details(self) -> Dict:
        """Get wallet balances from Shadow Wallet (Real-time)."""
        try:
            # 1. Binance Futures
            bin_bal = self.shadow_wallet.balances.get('BINANCE', {})
            futures_balance = bin_bal.get('total', 0.0)
            futures_available = bin_bal.get('available', 0.0)
            futures_pnl = 0.0 # ShadowWallet simple balance doesn't track UnrealizedPnL yet strictly
            # We could fetch PnL from caching positions if needed
            
            # 2. Bybit
            bybit_bal = self.shadow_wallet.balances.get('BYBIT', {})
            bybit_total = bybit_bal.get('total', 0.0)
            
            # 3. Alpaca (only show if user has their OWN credentials)
            alpaca_equity = 0.0
            user_has_alpaca = self.config.get('alpaca_key') and self.config.get('alpaca_secret')
            if user_has_alpaca:
                alp_bal = self.shadow_wallet.balances.get('ALPACA', {})
                alpaca_equity = alp_bal.get('total', 0.0)
            
            # Legacy Spot support (Mocked for now as we focus on Futures)
            spot_usdt = 0.0 
            
            total = futures_balance + bybit_total + alpaca_equity + spot_usdt
            
            return {
                "spot_usdt": spot_usdt,
                "earn_usdt": 0.0,
                "futures_balance": futures_balance,
                "bybit_balance": bybit_total, # Added Bybit
                "futures_pnl": 0.0,  # PnL agregado (se calcula desde posiciones activas)
                "alpaca_equity": alpaca_equity,
                "total": total
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def get_dashboard_summary(self) -> Dict:
        """
        Aggregates all data for the Unified Dashboard.
        - Wallet (Binance/Alpaca)
        - Active Positions (Count/PnL)
        - Mode/Risk Status
        """
        # 1. Active Positions (Triggers Sync)
        positions = await self.get_active_positions()
        
        # 2. Wallet Data (Now Fresh)
        wallet = await self.get_wallet_details()
        if 'error' in wallet:
            wallet = {k: 0.0 for k in ['spot_usdt','earn_usdt','futures_balance','futures_pnl','alpaca_equity','total']}
            wallet['error'] = True
        pos_count = len(positions)
        longs = len([p for p in positions if p['amt'] > 0])
        shorts = len([p for p in positions if p['amt'] < 0])
        
        # Split by Exchange
        bin_pos = [p for p in positions if p.get('source') == 'BINANCE']
        bybit_pos = [p for p in positions if p.get('source') == 'BYBIT']
        
        # Only include Alpaca positions if user has their OWN credentials
        user_has_alpaca = self.config.get('alpaca_key') and self.config.get('alpaca_secret')
        alp_pos = [p for p in positions if p.get('source') == 'ALPACA'] if user_has_alpaca else []
        
        bin_longs = len([p for p in bin_pos if p['amt'] > 0])
        bin_shorts = len([p for p in bin_pos if p['amt'] < 0])
        
        bybit_longs = len([p for p in bybit_pos if p['amt'] > 0])
        bybit_shorts = len([p for p in bybit_pos if p['amt'] < 0])
        
        alp_longs = len([p for p in alp_pos if p['amt'] > 0])
        alp_shorts = len([p for p in alp_pos if p['amt'] < 0])

        # 3. Aggregated PnL
        calc_pnl = sum(p['pnl'] for p in positions)
        bin_pnl = sum(p['pnl'] for p in bin_pos)
        bybit_pnl = sum(p['pnl'] for p in bybit_pos)
        alp_pnl = sum(p['pnl'] for p in alp_pos)
        
        # 4. Allocations
        total_equity = wallet['total']
        if total_equity > 0:
            alloc_binance_fut = (wallet['futures_balance'] / total_equity) * 100
            alloc_binance_spot = ((wallet['spot_usdt'] + wallet['earn_usdt']) / total_equity) * 100
            alloc_bybit = (wallet['bybit_balance'] / total_equity) * 100
            alloc_alpaca = (wallet['alpaca_equity'] / total_equity) * 100
        else:
            alloc_binance_fut = alloc_binance_spot = alloc_bybit = alloc_alpaca = 0

        # 5. Macro Stats
        macro = {"btc_dominance": 0.0, "global_state": "N/A"}
        if self.manager and hasattr(self.manager, 'get_macro_stats'):
             macro = self.manager.get_macro_stats()

        return {
            "wallet": wallet,
            "positions": {
                "count": pos_count,
                "longs": longs,
                "shorts": shorts,
                "total_pnl": calc_pnl,
                # Detailed breakdown
                "binance": {
                    "count": len(bin_pos),
                    "longs": bin_longs,
                    "shorts": bin_shorts,
                    "pnl": bin_pnl
                },
                "bybit": {
                    "count": len(bybit_pos),
                    "longs": bybit_longs,
                    "shorts": bybit_shorts,
                    "pnl": bybit_pnl
                },
                "alpaca": {
                    "count": len(alp_pos),
                    "longs": alp_longs,
                    "shorts": alp_shorts,
                    "pnl": alp_pnl
                }
            },
            "allocation": {
                "binance_futures": alloc_binance_fut,
                "binance_spot": alloc_binance_spot,
                "alpaca": alloc_alpaca
            },
            "macro": macro,
            "config": self.config
        }
    
    async def _execute_alpaca_order(self, symbol: str, side: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """Execute order via Alpaca (runs sync code in executor)."""
        if not self.alpaca_client:
            return False, "⚠️ Alpaca Client not initialized."
        
        # Run sync Alpaca code in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._alpaca_order_sync, 
            symbol, side, atr
        )

    async def _execute_bybit_order(self, symbol: str, side: str, strategy: str = "Manual", atr: Optional[float] = None) -> Tuple[bool, str]:
        """Execute order via Bybit Adapter."""
        if not self.bybit_client:
            return False, "⚠️ Bybit Client not initialized."
            
        try:
            # 1. Get Account Info
            bal = await self.bybit_client.get_account_balance()
            total_equity = bal['total']
            
            # 2. Get Price
            current_price = await self.bybit_client.get_market_price(symbol)
            if current_price <= 0:
                return False, f"❌ Failed to fetch price for {symbol}"
                
            # 3. Leverage
            leverage = self.config['leverage']
            await self.bybit_client.set_leverage(symbol, leverage)
            
            # 4. Sizing & SL/TP
            tp_ratio = self.config.get('tp_ratio', 1.5)
            stop_loss_pct = self.config['stop_loss_pct']
            
            if atr and atr > 0:
                 mult = self.config.get('atr_multiplier', 2.0)
                 sl_dist = mult * atr
                 if side == 'LONG':
                     sl_price = round(current_price - sl_dist, 2)
                     tp_price = round(current_price + (tp_ratio * sl_dist), 2)
                 else:
                     sl_price = round(current_price + sl_dist, 2)
                     tp_price = round(current_price - (tp_ratio * sl_dist), 2)
                 
                 # Dynamic Sizing (Approx)
                 risk_amt = total_equity * 0.01 
                 dist_to_sl = sl_dist
                 raw_quantity = risk_amt / dist_to_sl if dist_to_sl > 0 else 0
            else:
                 margin_assignment = total_equity * self.config['max_capital_pct']
                 raw_quantity = (margin_assignment * leverage) / current_price
                 
                 if side == 'LONG':
                     sl_price = round(current_price * (1 - stop_loss_pct), 2)
                     tp_price = round(current_price * (1 + (stop_loss_pct * 3)), 2)
                 else:
                     sl_price = round(current_price * (1 + stop_loss_pct), 2)
                     tp_price = round(current_price * (1 - (stop_loss_pct * 3)), 2)

            quantity = round(raw_quantity, 4) 
            
            if quantity <= 0: return False, "Quantity too small."
            
            # 5. Execute
            res = await self.bybit_client.place_order(
                symbol, side, 'MARKET', quantity, 
                takeProfit=str(tp_price), stopLoss=str(sl_price)
            )
            
            if 'error' in res:
                return False, f"Bybit Error: {res['error']}"
                
            return True, (
                f"✅ Bybit {side} {symbol}\n"
                f"Qty: {quantity}\n"
                f"Entry: {current_price}\n"
                f"SL: {sl_price}\n"
                f"TP: {tp_price}"
            )

        except Exception as e:
            return False, f"Bybit Execution Error: {e}"
    
    def _alpaca_order_sync(self, symbol: str, side: str, atr: Optional[float]) -> Tuple[bool, str]:
        """Sync Alpaca order execution (called via run_in_executor)."""
        try:
            import yfinance as yf
            
            # Check existing position
            try:
                pos = self.alpaca_client.get_open_position(symbol)
                if pos:
                    return False, f"⚠️ Position already open for {symbol}."
            except:
                pass
            
            # Get account
            acct = self.alpaca_client.get_account()
            equity = float(acct.equity)
            buying_power = float(acct.buying_power)
            
            # Get price
            ticker = yf.Ticker(symbol)
            try:
                current_price = ticker.fast_info['last_price']
            except:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    return False, f"❌ Failed to fetch price for {symbol}"
            
            if not current_price:
                return False, "❌ Price is zero/null."
            
            # Calculate SL/TP
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                if side == 'LONG':
                    sl_price = current_price - sl_dist
                    tp_price = current_price + (1.5 * sl_dist)
                else:
                    sl_price = current_price + sl_dist
                    tp_price = current_price - (1.5 * sl_dist)
            else:
                sl_pct = 0.02
                if side == 'LONG':
                    sl_price = current_price * (1 - sl_pct)
                    tp_price = current_price * (1 + (sl_pct * 3))
                else:
                    sl_price = current_price * (1 + sl_pct)
                    tp_price = current_price * (1 - (sl_pct * 3))
            
            # Size calculation
            dist_to_stop = abs(current_price - sl_price) or 0.01
            risk_amt = equity * 0.02
            qty = risk_amt / dist_to_stop
            
            max_alloc = equity * 0.20
            
            # Cap at Buying Power (leave 2% buffer for fees/fluctuation)
            if max_alloc > (buying_power * 0.98):
                max_alloc = buying_power * 0.98
                
            if (qty * current_price) > max_alloc:
                qty = max_alloc / current_price
            
            qty = round(qty, 2)
            if side == 'SHORT':
                qty = int(qty)
            
            if qty < 0.01:
                return False, f"Quantity too small ({qty})."
            
            # Submit order
            side_enum = OrderSide.BUY if side == 'LONG' else OrderSide.SELL
            
            req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side_enum,
                time_in_force=TimeInForce.DAY,
                take_profit=TakeProfitRequest(limit_price=round(tp_price, 2)),
                stop_loss=StopLossRequest(stop_price=round(sl_price, 2))
            )
            
            res = self.alpaca_client.submit_order(req)
            
            status_str = str(res.status).replace('OrderStatus.', '').replace('_', ' ').title()
            
            return True, (
                f"✅ Alpaca {side} {symbol}\n"
                f"Qty: {qty}\n"
                f"SL: {sl_price:.2f}\n"
                f"TP: {tp_price:.2f}\n"
                f"Status: {status_str}"
            )
            
        except Exception as e:
            error_str = str(e)
            if "insufficient buying power" in error_str:
                return False, f"❌ Alpaca: Insufficient Buying Power (BP: {getattr(acct, 'buying_power', 'N/A')})"
            return False, f"Alpaca Error: {e}"

    # --- RESTORED METHODS FROM SYNC ---
    
    def get_trade_preview(self, symbol: str, side: str, current_price: float, atr: Optional[float] = None) -> Tuple[float, float, float]:
        """
        Calculates TP, SL, and TS (Trailing Stop Activation) prices without executing the trade.
        Returns: (sl_price, tp_price, ts_price)
        """
        try:
            # Estimación de tick_size basada en el precio (fallback para función síncrona)
            if current_price >= 1000:
                tick_size = 0.1
            elif current_price >= 1:
                tick_size = 0.01
            elif current_price >= 0.1:
                tick_size = 0.001
            else:
                tick_size = 0.0001
            
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                
                if side == 'LONG':
                    sl_price = round_to_tick_size(current_price - sl_dist, tick_size)
                    tp_price = round_to_tick_size(current_price + (1.5 * sl_dist), tick_size)
                else:
                    sl_price = round_to_tick_size(current_price + sl_dist, tick_size)
                    tp_price = round_to_tick_size(current_price - (1.5 * sl_dist), tick_size)
            else:
                sl_pct = self.config.get('stop_loss_pct', 0.02)
                tp_pct = sl_pct * 1.5
                
                if side == 'LONG':
                    sl_price = round_to_tick_size(current_price * (1 - sl_pct), tick_size)
                    tp_price = round_to_tick_size(current_price * (1 + tp_pct), tick_size)
                else:
                    sl_price = round_to_tick_size(current_price * (1 + sl_pct), tick_size)
                    tp_price = round_to_tick_size(current_price * (1 - tp_pct), tick_size)
            
            # TS Activation is usually set to TP1 price in our logic
            ts_price = tp_price
            
            return sl_price, tp_price, ts_price
        except Exception as e:
            print(f"Preview Error: {e}")
            return 0.0, 0.0, 0.0

    async def execute_flip_position(self, symbol: str, new_side: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """
        FLIP LOGIC:
        1. Cancel Open Orders.
        2. Close Current Position.
        3. Wait 3s for stability.
        4. Verify position is closed
        5. Open New Position (Reverse).
        """
        if not self.bridge:
            return False, "No valid session."
        
        # 1. Cancel Open Orders (Safety)
        await self.bridge.cancel_orders(symbol)
        
        # 2. Close Current
        success_close, msg_close = await self.execute_close_position(symbol)
        
        if not success_close and "No open position" not in msg_close:
            return False, f"Flip Aborted: Failed to close ({msg_close})"
        
        # 2. Safety Wait & Robust Verification
        # We try up to 3 times to verify closure, with a small delay between each.
        try:
            verified = False
            qty_now = 0
            for attempt in range(3):
                await asyncio.sleep(2.0 if attempt == 0 else 1.0) # Total up to 4s
                pos = await self.bridge.get_position(symbol)
                qty_now = abs(float(pos.get('quantity', 0) or pos.get('amt', 0)))
                
                if qty_now == 0:
                    verified = True
                    break
                else:
                    self.logger.warning(f"🔄 Flip Verification (Attempt {attempt+1}/3): {symbol} still has {qty_now} contracts. Waiting...")

            if not verified:
                return False, f"Flip Aborted: Position failed to close after 3 attempts ({qty_now} remaining)"
        except Exception as e:
            self.logger.warning(f"⚠️ Verification Error ({symbol}): {e}")
        
        # 4. Open New
        if new_side == 'LONG':
            return await self.execute_long_position(symbol, atr)
        elif new_side == 'SHORT':
            return await self.execute_short_position(symbol, atr)
        else:
            return False, f"Invalid Side: {new_side}"

    def reset_circuit_breaker(self) -> None:
        """
        Resets the circuit breaker logic by updating the 'ignore_until' timestamp.
        Any losses recorded before this timestamp will not count towards the streak.
        """
        self.cb_ignore_until = int(time.time() * 1000)
        print(f"✅ [Chat {self.chat_id}] Circuit Breaker Reset. Ignoring history before {self.cb_ignore_until}")

    async def check_circuit_breaker(self) -> Tuple[bool, str]:
        """
        Circuit Breaker / Safety Switch
        If detects 5 consecutive losses (Realized PnL < 0) in PILOT mode,
        automatically downgrades to COPILOT to stop the bleeding.
        Returns: (Triggered: bool, Message: str)
        """
        if self.mode != 'PILOT':
            return False, ""
        
        # Check if enabled in config
        if not self.config.get('circuit_breaker_enabled', True):
            return False, ""
        
        if not self.bridge:
            return False, ""
        
        try:
            # NOTE: CCXT doesn't have futures_income_history equivalent
            # This feature requires python-binance or direct API call
            # For now, skip circuit breaker check when using CCXT
            binance_adapter = self.bridge.adapters.get('BINANCE')
            if not binance_adapter or not hasattr(binance_adapter._exchange, 'fapiPrivateGetIncome'):
                return False, ""  # Skip if method not available
            
            # Fetch last 20 Income entries (REALIZED_PNL only)
            income = await binance_adapter._exchange.fapiPrivateGetIncome({
                'incomeType': 'REALIZED_PNL',
                'limit': 20
            })
            
            # Sort descending by time (Newest first)
            income.sort(key=lambda x: x['time'], reverse=True)
            
            consecutive_losses = 0
            for trade in income:
                pnl = float(trade['income'])
                trade_time = int(trade['time'])  # Ensure it's an int for comparison
                if pnl < 0:
                    # CHECK: Ignore if before reset time
                    if trade_time < self.cb_ignore_until:
                        break
                    consecutive_losses += 1
                else:
                    break

            
            # Threshold Check
            if consecutive_losses >= 5:
                old_mode = self.mode
                self.set_mode('COPILOT')
                
                msg = (
                    f"⚠️ **CIRCUIT BREAKER ACTIVADO** ⚠️\n"
                    f"Se han detectado {consecutive_losses} pérdidas consecutivas en modo PILOT.\n"
                    f"🛡️ El sistema ha cambiado automáticamente a **COPILOT** para proteger tu capital.\n"
                    f"Revisa el mercado manualmente antes de reactivar."
                )
                return True, msg
        
        except Exception as e:
            print(f"Error checking circuit breaker: {e}")
        
        return False, ""

    async def get_pnl_history(self, days: int = 1) -> Tuple[float, List[Dict]]:
        """Fetches Realized PnL from Binance for the last N days"""
        if not self.bridge:
            return 0.0, []
        
        try:
            # Get Binance adapter from bridge
            binance_adapter = self.bridge.adapters.get('BINANCE')
            if not binance_adapter or not binance_adapter._exchange:
                return 0.0, []
                
            exchange = binance_adapter._exchange
            start_time = int((time.time() - (days * 86400)) * 1000)
            
            # Fetch Realized PnL using CCXT's direct API call
            income = await exchange.fapiPrivateGetIncome({
                'incomeType': 'REALIZED_PNL',
                'startTime': start_time,
                'limit': 100
            })
            # Fetch Commission (to subtract for Net PnL)
            commission = await exchange.fapiPrivateGetIncome({
                'incomeType': 'COMMISSION',
                'startTime': start_time,
                'limit': 100
            })
            
            total_pnl = 0.0
            details = []
            
            for item in income:
                amt = float(item['income'])
                total_pnl += amt
                details.append({'symbol': item['symbol'], 'amount': amt, 'time': item['time'], 'type': 'PNL'})
            
            for item in commission:
                amt = float(item['income'])
                total_pnl += amt  # Commission is negative
            
            return total_pnl, details
        
        except Exception as e:
            print(f"Error fetching PnL: {e}")
            return 0.0, []

    def _log_trade(self, symbol: str, entry: float, qty: float, sl: float, tp: float, side: str = 'LONG') -> None:
        """Logs trade to local JSON file for history"""
        try:
            log_file = 'data/trades.json'
            entry_data = {
                "timestamp": time.time(),
                "date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "chat_id": self.chat_id,
                "symbol": symbol,
                "side": side,
                "entry_price": entry,
                "quantity": qty,
                "sl": sl,
                "tp": tp
            }
            
            data = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    try:
                        data = json.load(f)
                    except:
                        pass
            
            data.append(entry_data)
            
            with open(log_file, 'w') as f:
                json.dump(data, f, indent=4)
        
        except Exception as e:
            print(f"⚠️ Failed to log trade: {e}")


class AsyncSessionManager:
    """
    Manages multiple AsyncTradingSessions.
    Provides persistence and lookup by chat_id.
    """
    
    def __init__(self, data_file: str = 'data/sessions.json'):
        self.data_file = data_file
        self.sessions: Dict[str, AsyncTradingSession] = {}
        self._lock = asyncio.Lock()
        self.engine = None
        
    def set_nexus_engine(self, engine):
        """Inject NexusCore engine reference."""
        self.engine = engine
        
    def get_macro_stats(self) -> Dict:
        """Retrieve Global Macro Stats from Engine (RiskGuardian)."""
        if self.engine and self.engine.risk_guardian:
             rg = self.engine.risk_guardian
             return {
                 "btc_dominance": getattr(rg, 'btc_dominance', 0.0),
                 "global_state": getattr(rg, 'global_state', 'NORMAL'),
                 "total_cap": getattr(rg, 'total_cap', 0.0)
             }
        return {"btc_dominance": 0.0, "global_state": "N/A", "total_cap": 0.0}
    

    async def load_sessions(self):
        """Load sessions from PostgreSQL (with JSON fallback)."""
        async with self._lock:
            loaded_source = "NONE"
            
            # Try PostgreSQL first
            postgresql_success = False
            try:
                from servos.db import load_all_sessions
                db_sessions = load_all_sessions()
                
                if db_sessions is not None:
                    for chat_id, info in db_sessions.items():
                        # SANITIZE: Check authorization
                        from servos.db import get_user_role
                        allowed, role = get_user_role(str(chat_id))
                        
                        config = info.get('config', {})
                        
                        # FORCE DEFAULTS if unauthorized (Fixes persistent old config issue)
                        api_key = info.get('api_key', '')
                        api_secret = info.get('api_secret', '')
                        
                        if not allowed:
                            print(f"🔒 Locking down Unauthorized session: {chat_id}")
                            config.update({
                                "mode": "WATCHER",
                                "strategies": {},
                                "groups": {},
                                "sentiment_filter": False,
                                "personality": "STANDARD_ES"
                            })
                            # Force Clear Keys
                            api_key = ""
                            api_secret = ""
                        
                        session = AsyncTradingSession(
                            chat_id=chat_id,
                            api_key=api_key,
                            api_secret=api_secret,
                            config=config,
                            manager=self
                        )
                        await session.initialize(verbose=False)
                        self.sessions[chat_id] = session
                    
                    print(f"🐘 Loaded {len(self.sessions)} sessions from PostgreSQL")
                    postgresql_success = True
                    loaded_source = "POSTGRESQL"
            except Exception as e:
                print(f"⚠️ PostgreSQL load failed, using JSON fallback: {e}")
            
            # Fallback to JSON if PostgreSQL failed
            if not postgresql_success:
                if not os.path.exists(self.data_file):
                    pass # Will ensure admin below
                else:
                    try:
                        with open(self.data_file, 'r') as f:
                            data = json.load(f)
                        
                        for chat_id, info in data.items():
                            # SANITIZE: Check authorization
                            from servos.db import get_user_role
                            allowed, role = get_user_role(str(chat_id))
                            
                            config = info.get('config', {})
                            
                            if not allowed:
                                print(f"🔒 Locking down Unauthorized session (JSON): {chat_id}")
                                config.update({
                                    "mode": "WATCHER",
                                    "strategies": {},
                                    "groups": {},
                                    "sentiment_filter": False,
                                    "personality": "STANDARD_ES"
                                })
                                # Force Clear Keys in Info dict (for init below)
                                info['api_key'] = ""
                                info['api_secret'] = ""

                            session = AsyncTradingSession(
                                chat_id=chat_id,
                                api_key=info.get('api_key', ''),
                                api_secret=info.get('api_secret', ''),
                                config=config,
                                manager=self
                            )
                            await session.initialize(verbose=False)
                            self.sessions[chat_id] = session
                        
                        print(f"📁 Loaded {len(self.sessions)} sessions from {self.data_file}")
                        loaded_source = "JSON"
                        
                    except Exception as e:
                        print(f"❌ Session Load Error: {e}")
        
        # Ensure Admin Session (Silent)
        await self._ensure_admin_session(verbose=False)
        
        # --- AGGREGATED STARTUP LOG ---
        print("🧠 Nexus Analyst: CONNECTED.")
        
        proxied_users = []
        binance_users = []
        alpaca_users = []
        
        # Extract proxy URL from first available session for display
        proxy_url_display = ""
        
        for s in self.sessions.values():
            if s._proxy:
                proxied_users.append(s.chat_id)
                if not proxy_url_display:
                    proxy_url_display = s._proxy
            
            # Check adapters via bridge (refactored from deprecated s.client)
            if 'BINANCE' in s.bridge.adapters:
                binance_users.append(s.chat_id)
            
            if 'ALPACA' in s.bridge.adapters:
                alpaca_users.append(s.chat_id)
        
        if proxied_users:
            print(f"🔄 Proxy configured: [{len(proxied_users):02d} Users]")
        
        if binance_users:
            print(f"✅ Binance Client Init (✅ Proxy): [{len(binance_users):02d} Users]")
            
        if alpaca_users:
            print(f"✅ Alpaca Client Initialized (Paper: Mixed): [{len(alpaca_users):02d} Users]")
    

    async def _ensure_admin_session(self, verbose: bool = True):
        """Create or REPLACE admin sessions from env vars (supports comma-separated IDs).
        
        IMPORTANT: Admin sessions ALWAYS use ENV credentials, overriding any DB values.
        This ensures the admin can always connect even if DB has stale/different keys.
        """
        # Sanitize inputs
        raw_admin_ids = os.getenv('TELEGRAM_ADMIN_ID', '').strip().strip("'\"")
        
        # Binance
        bin_key = os.getenv('BINANCE_API_KEY', '').strip().strip("'\"")
        bin_sec = os.getenv('BINANCE_SECRET', '').strip().strip("'\"")
        
        # Alpaca
        alp_key = os.getenv('APCA_API_KEY_ID', '').strip().strip("'\"")
        alp_sec = os.getenv('APCA_API_SECRET_KEY', '').strip().strip("'\"")
        
        if not raw_admin_ids or not bin_key or not bin_sec:
            return

        # Split multiple IDs (e.g. "123,456,789")
        admin_ids = [aid.strip() for aid in raw_admin_ids.split(',') if aid.strip()]

        for admin_id in admin_ids:
            # Check if session exists and has DIFFERENT keys
            existing = self.sessions.get(admin_id)
            needs_recreation = False
            
            # Check if config needs update (Alpaca)
            alpaca_needs_update = False
            if existing:
                cfg = existing.config
                if cfg.get('alpaca_key') != alp_key or cfg.get('alpaca_secret') != alp_sec:
                    alpaca_needs_update = True

            if existing:
                # Always recreate if keys differ (ENV takes priority)
                # Check Binance params + Alpaca Params
                if (existing.config_api_key != bin_key or 
                    existing.config_api_secret != bin_sec or 
                    alpaca_needs_update):
                    
                    needs_recreation = True
                    # Close old session's adapters
                    await existing.bridge.close_all()
                    if verbose:
                        print(f"🔄 Admin {admin_id}: ENV credentials differ from DB - recreating session")
            else:
                needs_recreation = True
            
            if needs_recreation:
                # Create fresh session with ENV credentials
                
                # PRESERVE EXISTING CONFIG
                new_config = {}
                if existing and existing.config:
                    new_config = existing.config.copy()
                
                # Update with MANDATORY credentials
                new_config.update({'alpaca_key': alp_key, 'alpaca_secret': alp_sec})
                
                session = AsyncTradingSession(admin_id, bin_key, bin_sec, config=new_config, manager=self)
                await session.initialize(verbose=verbose)
                self.sessions[admin_id] = session
                if verbose:
                    print(f"🔑 Admin session {'updated' if existing else 'created'} for {admin_id} (Env Vars)")
    
    async def save_sessions(self):
        """Persist sessions to PostgreSQL and JSON (redundancy)."""
        async with self._lock:
            data = {}
            for chat_id, session in self.sessions.items():
                data[chat_id] = {
                    'api_key': session.config_api_key,
                    'api_secret': session.config_api_secret,
                    'config': session.config
                }
            
            # 1. Save to PostgreSQL
            try:
                from servos.db import save_all_sessions
                if save_all_sessions(data):
                    print(f"🐘 Saved {len(data)} sessions to PostgreSQL")
            except Exception as e:
                print(f"⚠️ PostgreSQL save failed: {e}")
            
            # 2. Save to JSON (backup)
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def get_session(self, chat_id: str) -> Optional[AsyncTradingSession]:
        """Get session by chat_id."""
        return self.sessions.get(chat_id)
    
    async def create_or_update_session(
        self, chat_id: str, api_key: str, api_secret: str
    ) -> AsyncTradingSession:
        """Create or update a session."""
        
        existing = self.sessions.get(chat_id)
        config = existing.config if existing else None
        
        session = AsyncTradingSession(chat_id, api_key, api_secret, config, manager=self)
        await session.initialize()
        
        self.sessions[chat_id] = session
        await self.save_sessions()
        
        return session
    
    async def delete_session(self, chat_id: str) -> bool:
        """Delete a session."""
        if chat_id in self.sessions:
            session = self.sessions.pop(chat_id)
            await session.close()
            await self.save_sessions()
            return True
        return False
    
    def get_all_sessions(self) -> List[AsyncTradingSession]:
        """Get all active sessions."""
        return list(self.sessions.values())
    
    async def close_all(self):
        """Cleanup all sessions."""
        for session_id, session in self.sessions.items():
            try:
                await session.close()
                print(f"✅ Session {session_id} closed successfully")
            except Exception as e:
                print(f"⚠️ Error closing session {session_id}: {e}")
        self.sessions.clear()

