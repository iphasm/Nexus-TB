"""
Nexus Bridge - Interfaz Unificada de Exchanges

Este módulo proporciona una interfaz unificada para interactuar con múltiples exchanges
(Binance, Bybit, Alpaca) a través de un único punto de control. Se integra con Shadow
Wallet para mantener el estado en tiempo real de balances y posiciones.

Arquitectura:
- NexusBridge: Router principal que delega a adapters específicos
- IExchangeAdapter: Interfaz común para todos los adapters
- ShadowWallet: Estado en memoria sincronizado con exchanges

Flujo:
1. Cliente llama a NexusBridge.place_order()
2. Bridge determina exchange mediante _route_symbol()
3. Bridge delega al adapter correspondiente
4. Adapter ejecuta orden usando CCXT async
5. ShadowWallet se actualiza vía WebSocket o sync explícito
"""

from typing import Dict, Any, Optional
from nexus_system.uplink.adapters.base import IExchangeAdapter
from nexus_system.uplink.adapters.binance_adapter import BinanceAdapter
from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter
from nexus_system.uplink.adapters.alpaca_adapter import AlpacaAdapter
from nexus_system.core.shadow_wallet import ShadowWallet

# Lazy import to avoid circular dependencies
try:
    from system_directive import ASSET_GROUPS
except ImportError:
    ASSET_GROUPS = {}

class NexusBridge:
    """
    Interfaz unificada para múltiples exchanges.
    
    Proporciona un punto de entrada único para operaciones de trading,
    enrutando automáticamente a los adapters correctos según el símbolo.
    """
    
    def __init__(self, shadow_wallet: ShadowWallet):
        """
        Inicializa Nexus Bridge.
        
        Args:
            shadow_wallet: Instancia de ShadowWallet para mantener estado en memoria
        """
        self.shadow_wallet = shadow_wallet
        self.adapters: Dict[str, IExchangeAdapter] = {}  # Diccionario de adapters conectados
        self.primary_exchange = 'BINANCE'  # Exchange por defecto

    async def connect_exchange(self, name: str, **credentials) -> bool:
        """
        Inicializa y registra un adapter de exchange.
        
        Args:
            name: Nombre del exchange ('BINANCE', 'BYBIT', 'ALPACA')
            **credentials: Credenciales del exchange (api_key, api_secret, etc.)
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        name = name.upper()
        adapter = None
        
        try:
            if name == 'BINANCE':
                adapter = BinanceAdapter(**credentials)
            elif name == 'BYBIT':
                adapter = BybitAdapter(**credentials)
            elif name == 'ALPACA':
                adapter = AlpacaAdapter(**credentials)
            else:
                print(f"❌ NexusBridge: Unknown exchange {name}")
                return False
            
            if adapter:
                # Set bridge reference for centralized symbol formatting
                adapter._bridge = self

                # Pass verbose=False to suppress detailed adapter logs (bridge shows consolidated messages)
                if await adapter.initialize(verbose=False, **credentials):
                    self.adapters[name] = adapter

                    # Initial sync to Shadow Wallet (Balance & Positions) - silent
                    try:
                        balance = await adapter.get_account_balance()
                        self.shadow_wallet.update_balance(name, balance)

                        positions = await adapter.get_positions()
                        for pos in positions:
                            self.shadow_wallet.update_position(pos['symbol'], pos)
                    except Exception as e:
                        print(f"⚠️ NexusBridge: Error syncing {name} to Shadow Wallet: {e}")
                        # Continue anyway - adapter is connected

                    # NOTA: No sincronizar activos automáticamente para mantener lista optimizada
                    # La sincronización manual solo debe hacerse con /sync_crypto si es necesario
                    # if name in ['BINANCE', 'BYBIT']:
                    #     try:
                    #         await self.sync_crypto_assets()
                    #     except Exception as sync_err:
                    #         print(f"⚠️ NexusBridge: Error syncing crypto assets for {name}: {sync_err}")

                    return True
                else:
                    print(f"❌ NexusBridge: Failed to connect {name}")
        except Exception as e:
            print(f"❌ NexusBridge: Error connecting {name}: {e}")
        
        return False

    async def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene la posición de un símbolo desde Shadow Wallet.
        
        Args:
            symbol: Símbolo del activo (ej: 'BTCUSDT')
        
        Returns:
            Dict con información de la posición o dict vacío si no existe
        """
        return self.shadow_wallet.positions.get(symbol, {})

    async def get_positions(self, exchange: Optional[str] = None) -> list:
        """
        Obtener todas las posiciones activas de los adapters conectados.
        Opcionalmente filtrar por exchange específico.
        """
        positions = []
        target_adapters = {}

        if exchange:
            ex_name = exchange.upper()
            if ex_name in self.adapters:
                target_adapters = {ex_name: self.adapters[ex_name]}
        else:
            target_adapters = self.adapters

        for name, adapter in target_adapters.items():
            try:
                adapter_positions = await adapter.get_positions()
                for pos in adapter_positions:
                    normalized = self.normalize_symbol(pos.get('symbol', ''))
                    pos['symbol'] = normalized
                    pos['exchange'] = name
                    self.shadow_wallet.update_position(normalized, pos)
                    positions.append(pos)
            except Exception as e:
                print(f"⚠️ NexusBridge: Error getting positions from {name}: {e}")

        return positions

    async def get_last_price(self, symbol: str, exchange: Optional[str] = None) -> float:
        """Get last price via adapter (using ticker for speed, fallback to candles).

        IMPORTANT: In multi-exchange mode, callers should pass `exchange` explicitly to avoid
        re-routing to a different exchange than where the position/orders exist.
        """
        target = exchange.upper() if exchange else self._route_symbol(symbol)
        adapter = self.adapters.get(target)
        if not adapter:
            return 0.0

        # Format symbol for the adapter
        formatted_symbol = adapter._format_symbol(symbol) if hasattr(adapter, '_format_symbol') else symbol

        # Method 1: Try to use fetch_ticker (faster, no rate limiting issues)
        try:
            if hasattr(adapter, '_exchange') and adapter._exchange:
                ticker = await adapter._exchange.fetch_ticker(formatted_symbol)
                if ticker and 'last' in ticker and ticker['last']:
                    return float(ticker['last'])
        except Exception as ticker_err:
            # Ticker failed, try candles as fallback
            pass

        # Method 2: Fallback to candles (may be rate limited)
        try:
            df = await adapter.fetch_candles(symbol, timeframe='1m', limit=1)
            if not df.empty:
                return float(df['close'].iloc[-1])
        except Exception as e:
            print(f"⚠️ Bridge Price Error ({symbol}): {e}")
        return 0.0

    async def get_symbol_info(self, symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
        """Get symbol precision/limits via adapter.

        IMPORTANT: In multi-exchange mode, callers should pass `exchange` explicitly to avoid
        fetching precision/tick rules from the wrong venue.
        """
        target = exchange.upper() if exchange else self._route_symbol(symbol)
        adapter = self.adapters.get(target)
        if adapter:
            result = await adapter.get_symbol_info(symbol)
            if not result:
                print(f"⚠️ NexusBridge: get_symbol_info({symbol}) via {target} returned empty")
                # Provide fallback defaults for common crypto symbols
                if 'USDT' in symbol:
                    print(f"📊 Using fallback defaults for {symbol} (P=6, TickSize=0.01)")
                    return {
                        'symbol': symbol,
                        'tick_size': 0.01,
                        'price_precision': 2,
                        'quantity_precision': 6,
                        'min_qty': 0.001,
                        'max_qty': 1000,
                        'step_size': 0.001,
                        'exchange': target,
                        'fallback': True
                    }
            return result
        else:
            print(f"⚠️ NexusBridge: No adapter connected for {target} (symbol: {symbol})")
        return {}


    async def get_open_orders(self, symbol: str = None, exchange: Optional[str] = None) -> list:
        """Get open orders via adapter.

        IMPORTANT: In multi-exchange mode, callers should pass `exchange` explicitly.
        """
        if exchange:
            target = exchange.upper()
        else:
            target = self._route_symbol(symbol) if symbol else self.primary_exchange
        adapter = self.adapters.get(target)
        if adapter and hasattr(adapter, 'get_open_orders'):
            return await adapter.get_open_orders(symbol)
        return []

    async def cancel_orders(self, symbol: str, exchange: Optional[str] = None) -> bool:
        """Cancel all open orders via adapter.

        IMPORTANT: In multi-exchange mode, callers should pass `exchange` explicitly.
        """
        target = exchange.upper() if exchange else self._route_symbol(symbol)
        adapter = self.adapters.get(target)
        if adapter:
            return await adapter.cancel_orders(symbol)
        return False

    async def close_position(self, symbol: str, exchange: Optional[str] = None) -> bool:
        """Close specific position via adapter.

        IMPORTANT: In multi-exchange mode, callers should pass `exchange` explicitly.
        """
        target = exchange.upper() if exchange else self._route_symbol(symbol)
        adapter = self.adapters.get(target)
        if adapter:
            return await adapter.close_position(symbol)
        return False

    async def set_leverage(self, symbol: str, leverage: int, exchange: Optional[str] = None) -> bool:
        """Set leverage for a symbol via adapter.

        IMPORTANT: In multi-exchange mode, callers should pass `exchange` explicitly.
        """
        target = exchange.upper() if exchange else self._route_symbol(symbol)
        adapter = self.adapters.get(target)
        if adapter and hasattr(adapter, 'set_leverage'):
            return await adapter.set_leverage(symbol, leverage)
        return True  # Return True if adapter doesn't support leverage (e.g., Alpaca)

    async def place_order(
        self, 
        symbol: str, 
        side: str, 
        order_type: str = 'MARKET', 
        quantity: float = 0, 
        price: Optional[float] = None,
        exchange: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Coloca una orden de forma unificada, enrutando automáticamente al exchange correcto.
        
        Args:
            symbol: Símbolo del activo (ej: 'BTCUSDT')
            side: Lado de la orden ('BUY' o 'SELL')
            order_type: Tipo de orden ('MARKET', 'LIMIT', 'STOP_MARKET', 'TAKE_PROFIT_MARKET', etc.)
            quantity: Cantidad a operar
            price: Precio (requerido para órdenes LIMIT, usado como stopPrice para condicionales)
            exchange: Exchange específico (opcional, se determina automáticamente si no se proporciona)
            **kwargs: Parámetros adicionales (reduceOnly, stopPrice, etc.)
        
        Returns:
            Dict con resultado de la orden o error si falla
        """
        target_exchange = exchange or self._route_symbol(symbol)
        adapter = self.adapters.get(target_exchange)
        
        if not adapter:
            return {'error': f"Exchange {target_exchange} not connected"}
        
        print(f"🌉 Bridge: Routing {side} {symbol} -> {target_exchange}")
        
        try:
            # Execute Order
            result = await adapter.place_order(
                symbol, side, order_type, quantity, price, **kwargs
            )
            
            # Note: Shadow Wallet updates come via WebSocket streams or explicit sync
            # This method returns the order result for immediate feedback
            return result
        except Exception as e:
            print(f"❌ Bridge: Order placement error ({symbol}): {e}")
            return {'error': str(e), 'symbol': symbol, 'side': side}

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normaliza un símbolo a formato estándar BTCUSDT independientemente del formato de entrada.

        Soporta múltiples formatos:
        - BTCUSDT (formato estándar del sistema)
        - BTC/USDT (formato CCXT estándar)
        - BTC/USDT:USDT (formato Bybit futures)
        - BTCUSDT:USDT (variante)
        - btcusdt (minúsculas)
        - BTC_USDT (con guiones bajos)
        - BTC-USDT (con guiones)

        Returns:
            str: Símbolo normalizado (ej: 'BTCUSDT')
        """
        if not symbol or not isinstance(symbol, str):
            return symbol

        # Limpiar y normalizar
        clean_symbol = symbol.strip().upper().replace('_', '').replace('-', '')

        # Si ya está en formato correcto (termina con USDT y no tiene separadores), devolver tal cual
        if clean_symbol.endswith('USDT') and '/' not in clean_symbol and ':' not in clean_symbol:
            return clean_symbol

        # Extraer la base del símbolo eliminando sufijos conocidos
        base = clean_symbol

        # Primero intentar con sufijos que incluyen separadores
        complex_suffixes = ['/USDT:USDT', '/USDT', ':USDT']
        for suffix in complex_suffixes:
            if base.endswith(suffix.upper()):
                base = base[:-len(suffix)]
                break
        else:
            # Si no encontró sufijos complejos, intentar sufijo simple
            if base.endswith('USDT'):
                base = base[:-4]

        # Limpiar separadores restantes de la base
        if '/' in base:
            base = base.split('/')[0]
        if ':' in base:
            base = base.split(':')[0]

        # Asegurar que la base no esté vacía y sea válida
        if base and len(base) >= 2 and base.isalpha():
            return f"{base}USDT"

        # Fallback para casos extremos
        return symbol.upper().replace('/', '').replace(':', '').replace('_', '').replace('-', '')

    def format_symbol_for_exchange(self, symbol: str, exchange: str) -> str:
        """
        Formatea un símbolo normalizado para un exchange específico.
        Incluye correcciones específicas de Bybit.

        Args:
            symbol: Símbolo en formato normalizado (BTCUSDT)
            exchange: Nombre del exchange ('BINANCE', 'BYBIT', 'ALPACA')

        Returns:
            str: Símbolo formateado para el exchange
        """
        normalized = self.normalize_symbol(symbol)

        if exchange.upper() == 'BYBIT':
            # Aplicar correcciones específicas de Bybit primero
            try:
                from system_directive import get_bybit_corrected_ticker
                corrected = get_bybit_corrected_ticker(normalized)
                if corrected != normalized:
                    normalized = corrected
            except ImportError:
                pass  # Si no está disponible, continuar sin corrección

            # Bybit usa BTC/USDT:USDT para futures
            if normalized.endswith('USDT'):
                base = normalized[:-4]  # Remover USDT
                return f"{base}/USDT:USDT"
        elif exchange.upper() == 'BINANCE':
            # Binance usa BTCUSDT para futures
            return normalized
        elif exchange.upper() == 'ALPACA':
            # Alpaca usa símbolos sin USDT (AAPL, MSFT, etc.)
            if normalized.endswith('USDT'):
                return normalized[:-4]  # Remover USDT
            return normalized

        return normalized

    async def validate_symbol(self, symbol: str, exchange: str) -> bool:
        """
        Valida si un símbolo está disponible en un exchange específico.

        Args:
            symbol: Símbolo a validar (en cualquier formato)
            exchange: Nombre del exchange

        Returns:
            bool: True si el símbolo es válido y está disponible
        """
        try:
            normalized = self.normalize_symbol(symbol)
            formatted = self.format_symbol_for_exchange(normalized, exchange)

            adapter = self.adapters.get(exchange.upper())
            if not adapter:
                return False

            # Intentar obtener información del símbolo
            symbol_info = await adapter.get_symbol_info(formatted)
            return symbol_info is not None and 'symbol' in symbol_info

        except Exception as e:
            print(f"⚠️ Symbol validation error for {symbol} on {exchange}: {e}")
            return False

    async def set_position_protection(
        self,
        symbol: str,
        exchange: str,
        side: str,          # "LONG" | "SHORT"
        quantity: float,
        stop_loss: float,
        take_profit: float,
        trailing: dict | None,
        *,
        cancel_existing: bool = True,
    ) -> dict:
        """
        Establece protección completa (SL/TP/Trailing) para una posición de manera unificada.
        Retorna dict: {ok: bool, details: str, applied: {...}, errors:[...]}
        """

        ex = exchange.upper()

        if cancel_existing:
            await self.cancel_protection_orders(symbol, exchange=ex)

        if ex == "BINANCE":
            return await self._set_protection_binance(symbol, side, quantity, stop_loss, take_profit, trailing)

        if ex == "BYBIT":
            return await self._set_protection_bybit(symbol, side, quantity, stop_loss, take_profit, trailing)

        if ex == "ALPACA":
            # Alpaca no soporta "SL/TP server-side" igual que futuros; manejar aparte
            return {"ok": True, "details": "Alpaca: protección automática no soportada en este modo."}

        return {"ok": False, "details": f"Exchange no soportado: {ex}"}


    async def cancel_protection_orders(self, symbol: str, exchange: str) -> bool:
        """
        Cancela órdenes protectoras en el exchange correcto.
        Binance: cancelar open orders condicionales.
        Bybit: cancelar condicionales + reset trading-stop si aplica.
        """
        ex = exchange.upper()
        if ex == "BINANCE":
            return await self.cancel_orders(symbol)
        if ex == "BYBIT":
            # 1) cancel condicionales
            await self.cancel_orders(symbol)
            # 2) reset trading stop (0 cancela)
            bybit = self.adapters.get("BYBIT")
            if bybit:
                await bybit.set_trading_stop(symbol, take_profit=0, stop_loss=0, trailing_stop=0)
            return True
        return True


    async def _set_protection_binance(self, symbol: str, side: str, qty: float, sl: float, tp: float, trailing: dict | None) -> dict:
        """Implementa protección Binance usando órdenes condicionales."""
        close_side = "SELL" if side == "LONG" else "BUY"
        config = self.adapters["BINANCE"]._exchange.options if self.adapters.get("BINANCE") else {}

        applied = {"sl": False, "tp": False, "trailing": False}
        errors = []

        try:
            # SL
            sl_res = await self.place_order(
                symbol=symbol,
                side=close_side,
                order_type="STOP_MARKET",
                quantity=qty,
                price=sl,                    # se mapea a stopPrice
                reduceOnly=True,
                workingType=config.get("protection_trigger_by", "MARK_PRICE"),
            )
            if "error" in sl_res:
                errors.append(f"SL: {sl_res['error']}")
            else:
                applied["sl"] = True
        except Exception as e:
            errors.append(f"SL Exception: {e}")

        try:
            # TP
            tp_res = await self.place_order(
                symbol=symbol,
                side=close_side,
                order_type="TAKE_PROFIT_MARKET",
                quantity=qty,
                price=tp,
                reduceOnly=True,
                workingType=config.get("protection_trigger_by", "MARK_PRICE"),
            )
            if "error" in tp_res:
                errors.append(f"TP: {tp_res['error']}")
            else:
                applied["tp"] = True
        except Exception as e:
            errors.append(f"TP Exception: {e}")

        # TRAILING (corregir binance_adapter: no exigir stopPrice aquí)
        if trailing and config.get("trailing_enabled", True):
            try:
                tr_res = await self.place_order(
                    symbol=symbol,
                    side=close_side,
                    order_type="TRAILING_STOP_MARKET",
                    quantity=trailing.get("qty", qty),
                    price=None,  # NO stopPrice
                    reduceOnly=True,
                    activationPrice=trailing.get("activation_price"),
                    callbackRate=trailing.get("callback_rate_pct", 1.0),
                    workingType=config.get("protection_trigger_by", "MARK_PRICE"),
                )
                if "error" in tr_res:
                    errors.append(f"Trailing: {tr_res['error']}")
                else:
                    applied["trailing"] = True
            except Exception as e:
                errors.append(f"Trailing Exception: {e}")

        ok = applied["sl"] or applied["tp"]  # Al menos SL o TP debe funcionar
        details = f"Binance: SL={applied['sl']}, TP={applied['tp']}, Trailing={applied['trailing']}"
        if errors:
            details += f" | Errors: {errors}"

        return {"ok": ok, "details": details, "applied": applied, "errors": errors}


    async def _set_protection_bybit(self, symbol: str, side: str, qty: float, sl: float, tp: float, trailing: dict | None) -> dict:
        """
        Implementa protección Bybit usando endpoint V5 position/trading-stop (server-side).
        """
        bybit = self.adapters.get("BYBIT")
        if not bybit:
            return {"ok": False, "details": "Bybit adapter not available"}

        # trailing Bybit requiere DISTANCIA (no %). Convertimos:
        # trailing_pct_bybit = 1% => trailing_distance = price * 0.01
        trailing_distance = None
        active_price = None
        if trailing:
            active_price = trailing.get("activation_price")
            pct = trailing.get("pct", 1.0)
            if active_price:
                trailing_distance = active_price * (pct / 100.0)  # Convertir % a distancia

        applied = {"sl": False, "tp": False, "trailing": False}
        errors = []

        try:
            # Intento 1: set_trading_stop con SL+TP+Trailing
            res = await bybit.set_trading_stop(
                symbol=symbol,
                stop_loss=sl,
                take_profit=tp,
                trailing_stop=trailing_distance,
                # activePrice=active_price si se soporta
            )
            if res.get("success", False):
                applied = {"sl": True, "tp": True, "trailing": trailing_distance is not None}
            else:
                # Fallback A: si Bybit rechaza trailing junto con TP/SL
                res2 = await bybit.set_trading_stop(symbol, stop_loss=sl, take_profit=tp, trailing_stop=0)
                if res2.get("success", False):
                    applied["sl"] = True
                    applied["tp"] = True

                    # Trailing por orden nativa si se necesita
                    if trailing_distance and active_price:
                        tr = await bybit.place_trailing_stop(
                            symbol=symbol,
                            side=("SELL" if side == "LONG" else "BUY"),
                            quantity=qty,
                            callback_rate=trailing_distance,     # distancia, NO %
                            activation_price=active_price,
                        )
                        if tr.get("success", False):
                            applied["trailing"] = True
                        else:
                            errors.append(f"Trailing order failed: {tr.get('message', 'Unknown')}")
                else:
                    errors.append(f"Trading stop failed: {res.get('message', 'Unknown')}")
        except Exception as e:
            errors.append(f"Exception: {e}")

        ok = applied["sl"] or applied["tp"]  # Al menos SL o TP debe funcionar
        details = f"Bybit: SL={applied['sl']}, TP={applied['tp']}, Trailing={applied['trailing']}"
        if errors:
            details += f" | Errors: {errors}"

        return {"ok": ok, "details": details, "applied": applied, "errors": errors}


    def _route_symbol(self, symbol: str, user_preferences: Optional[Dict[str, bool]] = None) -> str:
        """
        Lógica de enrutamiento inteligente basada en grupos de activos y preferencias de usuario.

        Determina automáticamente qué exchange usar para un símbolo basándose en:
        1. Disponibilidad del símbolo en cada exchange (usando BYBIT_EXCLUSIONS)
        2. Grupos de activos definidos en system_directive (BYBIT, CRYPTO, STOCKS, ETFS)
        3. Preferencias del usuario (qué exchanges tiene habilitados)
        4. Disponibilidad de adapters conectados
        5. Fallback inteligente al exchange más apropiado

        Args:
            symbol: Símbolo del activo
            user_preferences: Dict con preferencias de usuario {'BYBIT': True, 'ALPACA': False, etc.}

        Returns:
            str: Nombre del exchange ('BINANCE', 'BYBIT', 'ALPACA')
        """
        # Normalizar símbolo primero
        normalized_symbol = self.normalize_symbol(symbol)

        # Import symbol availability check
        try:
            from system_directive import is_symbol_available_on_exchange
        except ImportError:
            def is_symbol_available_on_exchange(s, e): return True

        # Helper function to check if exchange is available for user AND symbol
        def is_exchange_available(exchange: str, check_symbol: bool = True) -> bool:
            if exchange not in self.adapters:
                return False
            if user_preferences and exchange in user_preferences:
                if not user_preferences[exchange]:
                    return False
            # Check if symbol is tradeable on this exchange
            if check_symbol and not is_symbol_available_on_exchange(normalized_symbol, exchange):
                return False
            return True

        # CRYPTO EXCHANGE ROUTING LOGIC (NUEVA JERARQUÍA):
        # CRYPTO group contains ALL cryptocurrency assets
        # User preferences determine which exchanges to use within CRYPTO
        # Both BINANCE and BYBIT are equally important choices

        # Check if this is a crypto symbol
        is_crypto = 'USDT' in normalized_symbol or normalized_symbol in ASSET_GROUPS.get('CRYPTO', [])

        if is_crypto:
            # Get which exchanges are available for this specific symbol
            binance_available = is_exchange_available('BINANCE')
            bybit_available = is_exchange_available('BYBIT')

            # PRIORIDAD: Binance primero (más estable con timestamps)
            # Solo usar Bybit si Binance no está disponible para este símbolo
            if binance_available:
                return 'BINANCE'

            if bybit_available:
                return 'BYBIT'

            # Fallback: Intentar Binance si está conectado (ignorar disponibilidad de símbolo)
            if 'BINANCE' in self.adapters:
                return 'BINANCE'

            # Fallback: Intentar Bybit si está conectado
            if 'BYBIT' in self.adapters:
                return 'BYBIT'

            # Neither available - this symbol may not be tradeable
            # Log and fallback to primary
            print(f"⚠️ NexusBridge: {normalized_symbol} not available on any crypto exchange")

        # 3. Stocks and ETFs - Alpaca ONLY (never route to crypto exchanges)
        stocks_etfs = ASSET_GROUPS.get('STOCKS', []) + ASSET_GROUPS.get('ETFS', [])
        if normalized_symbol in stocks_etfs:
            # Always return ALPACA for stocks/ETFs - don't fallback to crypto exchanges
            if 'ALPACA' in self.adapters:
                return 'ALPACA'
            else:
                # Alpaca not connected - still return ALPACA (will fail gracefully)
                print(f"⚠️ NexusBridge: {normalized_symbol} is a stock/ETF but ALPACA not connected")
                return 'ALPACA'

        # 4. Fallback: Rough check for stocks (symbols without USDT suffix)
        # These are likely stocks/ETFs that should go to Alpaca
        if 'USDT' not in normalized_symbol and not normalized_symbol.endswith('USD'):
            # Check if it looks like a stock symbol (all uppercase, 1-5 chars, no numbers)
            if normalized_symbol.isalpha() and len(normalized_symbol) <= 5:
                if 'ALPACA' in self.adapters:
                    return 'ALPACA'
                else:
                    print(f"⚠️ NexusBridge: {normalized_symbol} looks like a stock but ALPACA not connected")
                    return 'ALPACA'  # Return ALPACA anyway - will fail gracefully

        # 5. Ultimate Fallback for crypto - use primary exchange if available and enabled
        if self.primary_exchange and is_exchange_available(self.primary_exchange, check_symbol=False):
            return self.primary_exchange

        # 6. Last resort for crypto - return first available crypto adapter
        for exchange_name in ['BINANCE', 'BYBIT']:
            if is_exchange_available(exchange_name, check_symbol=False):
                return exchange_name

        return 'BINANCE'  # Default if nothing available


    async def sync_crypto_assets(self) -> Dict[str, list]:
        """
        Sincroniza activos crypto entre exchanges y actualiza ASSET_GROUPS dinámicamente.

        Returns:
            Dict con estadísticas de sincronización
        """
        synced_assets = {
            'BINANCE': [],
            'BYBIT': [],
            'UNIFIED': []
        }

        try:
            # Obtener activos de Binance
            if 'BINANCE' in self.adapters:
                try:
                    binance_markets = await self.adapters['BINANCE']._exchange.load_markets()
                    binance_usdt = [symbol for symbol in binance_markets.keys()
                                  if 'USDT' in symbol and not symbol.endswith(':USDT')]
                    binance_normalized = [self.normalize_symbol(s) for s in binance_usdt]
                    synced_assets['BINANCE'] = binance_normalized
                    print(f"✅ Binance: {len(binance_normalized)} USDT assets")
                except Exception as e:
                    print(f"⚠️ Error syncing Binance assets: {e}")

            # Obtener activos de Bybit
            if 'BYBIT' in self.adapters:
                try:
                    bybit_markets = await self.adapters['BYBIT']._exchange.load_markets()
                    bybit_usdt = [symbol for symbol in bybit_markets.keys()
                                if 'USDT' in symbol and not symbol.endswith(':USDT')]
                    bybit_normalized = [self.normalize_symbol(s) for s in bybit_usdt]
                    synced_assets['BYBIT'] = bybit_normalized
                    print(f"✅ Bybit: {len(bybit_normalized)} USDT assets")
                except Exception as e:
                    print(f"⚠️ Error syncing Bybit assets: {e}")

            # Unificar activos (intersección + específicos de cada exchange)
            unified = list(set(synced_assets['BINANCE'] + synced_assets['BYBIT']))
            synced_assets['UNIFIED'] = sorted(unified)

            # NOTA: No modificar ASSET_GROUPS automáticamente para mantener lista optimizada
            # Solo informar sobre los activos disponibles
            print(f"ℹ️  Información: {len(unified)} activos disponibles en exchanges conectados")
            print(f"ℹ️  Configuración actual: {len(ASSET_GROUPS.get('CRYPTO', []))} activos optimizados")
            print(f"ℹ️  Para modificar la lista optimizada, editar system_directive.py manualmente")

            # Comentar código que modifica ASSET_GROUPS
            # from system_directive import ASSET_GROUPS, CRYPTO_SUBGROUPS
            # existing_crypto = ASSET_GROUPS.get('CRYPTO', [])
            # new_crypto_assets = [asset for asset in unified if asset not in existing_crypto]
            # if new_crypto_assets:
            #     updated_crypto = existing_crypto + new_crypto_assets
            #     ASSET_GROUPS['CRYPTO'] = sorted(list(set(updated_crypto)))
            #     print(f"🔄 Added {len(new_crypto_assets)} new crypto assets to CRYPTO group")

            print(f"📊 Unified crypto assets: {len(unified)} total")

            # Clasificar nuevos activos automáticamente
            # NOTE: new_crypto_assets deshabilitado; mantener bloque comentado para referencia
            # if new_crypto_assets:
            #     categorized = self._categorize_new_assets(new_crypto_assets)
            #     print(f"🏷️ Categorized {len(categorized)} new assets into subgroups")

            return synced_assets

        except Exception as e:
            print(f"❌ Error in sync_crypto_assets: {e}")
            return synced_assets

    async def sync_all_positions(self) -> int:
        """
        Sincroniza todas las posiciones de todos los exchanges al ShadowWallet.
        
        Returns:
            int: Número de posiciones sincronizadas
        """
        synced = 0
        for name, adapter in self.adapters.items():
            try:
                positions = await adapter.get_positions()
                for pos in positions:
                    normalized_symbol = self.normalize_symbol(pos.get('symbol', ''))
                    self.shadow_wallet.update_position(normalized_symbol, {
                        'symbol': normalized_symbol,
                        'quantity': pos.get('quantity', 0),
                        'side': pos.get('side', 'LONG'),
                        'entry_price': pos.get('entryPrice', 0),
                        'unrealized_pnl': pos.get('unrealizedPnl', 0),
                        'exchange': name
                    })
                    synced += 1
            except Exception as e:
                print(f"⚠️ Position sync failed for {name}: {e}")
        return synced

    def _categorize_new_assets(self, new_assets: list) -> Dict[str, list]:
        """
        Clasifica automáticamente nuevos activos crypto en categorías temáticas
        basándose en nombres, símbolos y características conocidas.

        Args:
            new_assets: Lista de nuevos símbolos para clasificar

        Returns:
            Dict con assets clasificados por categoría
        """
        from system_directive import CRYPTO_SUBGROUPS

        categorized = {
            'MAJOR_CAPS': [],
            'MEME_COINS': [],
            'DEFI': [],
            'AI_TECH': [],
            'GAMING_METAVERSE': [],
            'LAYER1_INFRA': [],
            'BYBIT_EXCLUSIVE': []
        }

        # Keywords para clasificación automática
        classification_rules = {
            'MEME_COINS': [
                'pepe', 'doge', 'shib', 'wif', 'bonk', 'floki', 'ponke', 'brett', 'mew', 'turbo',
                'aibot', 'baby', 'hoge', 'kishu', 'slerf', 'bome', 'paws', 'wojak', 'landwolf',
                'mog', 'corgi', 'inu', 'cat', 'frog', 'duck', 'bird', 'fish', 'moon', 'rocket'
            ],
            'DEFI': [
                'uni', 'aave', 'crv', 'sushi', 'comp', 'mkr', 'yfi', 'bal', 'ren', 'knc',
                'zrx', 'bat', 'lrc', 'omg', 'ant', 'storj', 'rep', 'cake', 'pancake', 'joe',
                'trader', 'farm', 'alpha', 'beta', 'gamma', 'theta', 'yield', 'vault', 'stake'
            ],
            'AI_TECH': [
                'fet', 'agix', 'ocean', 'nmr', 'ctxc', 'amb', 'grt', 'skl', 'trb', 'pol',
                'ldo', 'arpa', 'data', 'qsp', 'tao', 'vai', 'synth', 'bot', 'ai', 'gpt',
                'neuron', 'cortex', 'brain', 'mind', 'think', 'learn', 'data', 'oracle'
            ],
            'GAMING_METAVERSE': [
                'axs', 'sand', 'mana', 'enj', 'ilv', 'ygg', 'dar', 'tlm', 'atlas', 'fis',
                'ghst', 'imx', 'gal', 'gmt', 'pixel', 'beam', 'pixel', 'mavia', 'nfp', 'cfg',
                'ace', 'game', 'play', 'meta', 'verse', 'land', 'world', 'space', 'galaxy'
            ],
            'LAYER1_INFRA': [
                'inj', 'sei', 'mina', 'sc', 'ctsi', 'celr', 'one', 'ftm', 'harmony', 'iotx',
                'tia', 'omni', 'zks', 'alt', 'flow', 'lpt', 'pendle', 'astr', 'op', 'arb',
                'matic', 'poly', 'near', 'atom', 'cosmos', 'dot', 'ksm', 'avax', 'sol', 'ada'
            ]
        }

        for asset in new_assets:
            # Remover USDT para análisis
            base_symbol = asset.replace('USDT', '').lower()
            classified = False

            # Verificar reglas de clasificación
            for category, keywords in classification_rules.items():
                if any(keyword in base_symbol for keyword in keywords):
                    categorized[category].append(asset)
                    classified = True
                    break

            # Si no se clasificó, verificar si es exclusivo de Bybit
            if not classified:
                # Los nuevos assets que no están en la lista original probablemente son de Bybit
                categorized['BYBIT_EXCLUSIVE'].append(asset)

        # Actualizar CRYPTO_SUBGROUPS con los nuevos assets
        for category, assets in categorized.items():
            if assets:  # Solo actualizar si hay nuevos assets
                if category not in CRYPTO_SUBGROUPS:
                    CRYPTO_SUBGROUPS[category] = []
                CRYPTO_SUBGROUPS[category].extend(assets)
                CRYPTO_SUBGROUPS[category] = sorted(list(set(CRYPTO_SUBGROUPS[category])))

        return categorized

    async def close_all(self):
        """Shutdown all connections."""
        for name, adapter in self.adapters.items():
            try:
                print(f"🔌 Bridge: Disconnecting {name}...")
                await adapter.close()
            except Exception as e:
                print(f"⚠️ Bridge: Error disconnecting {name}: {e}")

        self.adapters.clear()
