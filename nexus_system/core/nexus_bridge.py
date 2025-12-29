"""
Nexus Bridge - Unified Exchange Interface
Abstracts multiple exchanges into a single control plane.
Integrates with Shadow Wallet for real-time state.
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
    def __init__(self, shadow_wallet: ShadowWallet):
        self.shadow_wallet = shadow_wallet
        self.adapters: Dict[str, IExchangeAdapter] = {}
        self.primary_exchange = 'BINANCE'

    async def connect_exchange(self, name: str, **credentials) -> bool:
        """Initialize and register an exchange adapter."""
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
        """Get position from Shadow Wallet (Unified)."""
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
            return await adapter.get_symbol_info(symbol)
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
        """Unified order placement routing."""
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

    def _route_symbol(self, symbol: str) -> str:
        """
        Smart routing logic based on system_directive groups.
        IMPORTANT: Only routes to an exchange if its adapter is connected!
        """
        # 1. Check Bybit Group - BUT only if Bybit adapter is connected
        if symbol in ASSET_GROUPS.get('BYBIT', []):
            if 'BYBIT' in self.adapters:
                return 'BYBIT'
            else:
                # Bybit not connected, fallback to Binance for crypto
                if 'BINANCE' in self.adapters:
                    return 'BINANCE'
            
        # 2. Check Crypto (Binance) Group
        if symbol in ASSET_GROUPS.get('CRYPTO', []):
            if 'BINANCE' in self.adapters:
                return 'BINANCE'
            # Fallback to Bybit if Binance not connected
            if 'BYBIT' in self.adapters:
                return 'BYBIT'
            
        # 3. Check Stocks/ETFs Group
        if symbol in ASSET_GROUPS.get('STOCKS', []) or symbol in ASSET_GROUPS.get('ETFS', []):
            if 'ALPACA' in self.adapters:
                return 'ALPACA'
        
        # 4. Fallback: Rough check for stocks (symbols without USDT/USD)
        if 'USDT' not in symbol and 'USD' not in symbol:
            if 'ALPACA' in self.adapters:
                return 'ALPACA'
            
        # 5. Ultimate Fallback - use primary if connected
        if self.primary_exchange in self.adapters:
            return self.primary_exchange
        
        # 6. Last resort - return first connected adapter
        if self.adapters:
            return next(iter(self.adapters.keys()))
        
        return 'BINANCE'  # Default if nothing connected


    async def close_all(self):
        """Shutdown all connections."""
        for name, adapter in self.adapters.items():
            try:
                print(f"🔌 Bridge: Disconnecting {name}...")
                await adapter.close()
            except Exception as e:
                print(f"⚠️ Bridge: Error disconnecting {name}: {e}")
        
        self.adapters.clear()
