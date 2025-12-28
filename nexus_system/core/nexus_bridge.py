"""
Nexus Bridge - Unified Exchange Interface
Abstracts multiple exchanges into a single control plane.
Integrates with Shadow Wallet for real-time state.
"""

from typing import Dict, Any, Optional
import asyncio
from nexus_system.uplink.adapters.base import IExchangeAdapter
from nexus_system.uplink.adapters.binance_adapter import BinanceAdapter
from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter
from nexus_system.uplink.adapters.alpaca_adapter import AlpacaAdapter
from nexus_system.core.shadow_wallet import ShadowWallet

class NexusBridge:
    def __init__(self, shadow_wallet: ShadowWallet):
        self.shadow_wallet = shadow_wallet
        self.adapters: Dict[str, IExchangeAdapter] = {}
        self.primary_exchange = 'BINANCE'

    async def connect_exchange(self, name: str, **credentials) -> bool:
        """Initialize and register an exchange adapter."""
        name = name.upper()
        adapter = None
        
        if name == 'BINANCE':
            adapter = BinanceAdapter(**credentials)
        elif name == 'BYBIT':
            adapter = BybitAdapter(**credentials)
        elif name == 'ALPACA':
            adapter = AlpacaAdapter(**credentials)
        
        if adapter:
            if await adapter.initialize(**credentials):
                self.adapters[name] = adapter
                
                # Initial sync to Shadow Wallet (Balance & Positions)
                print(f"🔄 Bridge: Syncing {name} state...")
                balance = await adapter.get_account_balance()
                self.shadow_wallet.update_balance(name, balance)
                
                positions = await adapter.get_positions()
                for pos in positions:
                    self.shadow_wallet.update_position(pos['symbol'], pos)
                    
                return True
            else:
                print(f"❌ NexusBridge: Failed to connect {name}")
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
        
        # Execute Order
        result = await adapter.place_order(
            symbol, side, order_type, quantity, price, **kwargs
        )
        
        # Immediate Shadow update if successful (optimistic)
        # Real confirmation comes via WebSocket usually, but this helps responsiveness
        return result

    def _route_symbol(self, symbol: str) -> str:
        """Smart routing logic."""
        if 'USDT' not in symbol and 'USD' not in symbol: # Rough check for stocks
            return 'ALPACA'
        if 'BTC' in symbol or 'ETH' in symbol:
             # Could check spread here in future
             return self.primary_exchange
        return self.primary_exchange

    async def close_all(self):
        """Shutdown all connections."""
        for name, adapter in self.adapters.items():
            print(f"🔌 Bridge: Disconnecting {name}...")
            await adapter.close()
