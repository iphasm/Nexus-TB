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
                if await adapter.initialize(**credentials):
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

    async def get_last_price(self, symbol: str) -> float:
        """Get last price via adapter (using candles for compatibility)."""
        target = self._route_symbol(symbol)
        adapter = self.adapters.get(target)
        if not adapter:
            return 0.0
            
        try:
            # Efficient check: Use 1m candle, limit 1
            df = await adapter.fetch_candles(symbol, timeframe='1m', limit=1)
            if not df.empty:
                return float(df['close'].iloc[-1])
        except Exception as e:
            print(f"⚠️ Bridge Price Error ({symbol}): {e}")
        return 0.0

    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol precision/limits via adapter."""
        target = self._route_symbol(symbol)
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


    async def get_open_orders(self, symbol: str = None) -> list:
        """Get open orders via adapter."""
        target = self._route_symbol(symbol) if symbol else self.primary_exchange
        adapter = self.adapters.get(target)
        if adapter and hasattr(adapter, 'get_open_orders'):
            return await adapter.get_open_orders(symbol)
        return []

    async def cancel_orders(self, symbol: str) -> bool:
        """Cancel all open orders via adapter."""
        target = self._route_symbol(symbol)
        adapter = self.adapters.get(target)
        if adapter:
            return await adapter.cancel_orders(symbol)
        return False

    async def close_position(self, symbol: str) -> bool:
        """Close specific position via adapter."""
        target = self._route_symbol(symbol)
        adapter = self.adapters.get(target)
        if adapter:
            return await adapter.close_position(symbol)
        return False

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol via adapter."""
        target = self._route_symbol(symbol)
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

    def _route_symbol(self, symbol: str, user_preferences: Optional[Dict[str, bool]] = None) -> str:
        """
        Lógica de enrutamiento inteligente basada en grupos de activos y preferencias de usuario.

        Determina automáticamente qué exchange usar para un símbolo basándose en:
        1. Grupos de activos definidos en system_directive (BYBIT, CRYPTO, STOCKS, ETFS)
        2. Preferencias del usuario (qué exchanges tiene habilitados)
        3. Disponibilidad de adapters conectados
        4. Fallback inteligente al exchange más apropiado

        Args:
            symbol: Símbolo del activo
            user_preferences: Dict con preferencias de usuario {'BYBIT': True, 'ALPACA': False, etc.}

        Returns:
            str: Nombre del exchange ('BINANCE', 'BYBIT', 'ALPACA')
        """
        # Helper function to check if exchange is available for user
        def is_exchange_available(exchange: str) -> bool:
            if exchange not in self.adapters:
                return False
            if user_preferences and exchange in user_preferences:
                return user_preferences[exchange]
            return True  # If no preferences specified, assume available

        # CRYPTO EXCHANGE ROUTING LOGIC:
        # Both CRYPTO and BYBIT groups contain cryptocurrency assets
        # CRYPTO group → BINANCE exchange (primary)
        # BYBIT group → BYBIT exchange (secondary/alternative)

        # 1. Priority routing for BYBIT-specific assets
        # If symbol is in BYBIT group, prefer BYBIT exchange
        if symbol in ASSET_GROUPS.get('BYBIT', []):
            if is_exchange_available('BYBIT'):
                return 'BYBIT'
            # Fallback: if BYBIT not available but symbol is cross-listed on BINANCE
            if is_exchange_available('BINANCE'):
                return 'BINANCE'

        # 2. Enhanced crypto routing with user preferences
        # For symbols in CRYPTO group (primarily BINANCE assets)
        if symbol in ASSET_GROUPS.get('CRYPTO', []):
            # Check user preferences for crypto exchanges
            preferred_crypto_exchange = None

            # If user has BYBIT enabled and symbol is also available there, prefer BYBIT
            if is_exchange_available('BYBIT') and symbol in ASSET_GROUPS.get('BYBIT', []):
                preferred_crypto_exchange = 'BYBIT'
            # Otherwise, use BINANCE if available (primary for CRYPTO group)
            elif is_exchange_available('BINANCE'):
                preferred_crypto_exchange = 'BINANCE'
            # Fallback to BYBIT if BINANCE not available
            elif is_exchange_available('BYBIT'):
                preferred_crypto_exchange = 'BYBIT'

            if preferred_crypto_exchange:
                return preferred_crypto_exchange

        # 3. Stocks and ETFs - Alpaca only
        if symbol in ASSET_GROUPS.get('STOCKS', []) or symbol in ASSET_GROUPS.get('ETFS', []):
            if is_exchange_available('ALPACA'):
                return 'ALPACA'

        # 4. Fallback: Rough check for stocks (symbols without USDT/USD)
        if 'USDT' not in symbol and 'USD' not in symbol:
            if is_exchange_available('ALPACA'):
                return 'ALPACA'

        # 5. Ultimate Fallback - use primary exchange if available and enabled
        if self.primary_exchange and is_exchange_available(self.primary_exchange):
            return self.primary_exchange

        # 6. Last resort - return first available adapter according to user preferences
        for exchange_name in ['BINANCE', 'BYBIT', 'ALPACA']:
            if is_exchange_available(exchange_name):
                return exchange_name

        return 'BINANCE'  # Default if nothing available


    async def close_all(self):
        """Shutdown all connections."""
        for name, adapter in self.adapters.items():
            try:
                print(f"🔌 Bridge: Disconnecting {name}...")
                await adapter.close()
            except Exception as e:
                print(f"⚠️ Bridge: Error disconnecting {name}: {e}")
        
        self.adapters.clear()
