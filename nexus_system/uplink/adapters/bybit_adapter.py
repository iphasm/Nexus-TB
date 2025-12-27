"""
Bybit Futures Adapter.
Implements IExchangeAdapter for Bybit Unified Trading (USDT Perpetuals).
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional, Callable
import ccxt.async_support as ccxt

from .base import IExchangeAdapter


class BybitAdapter(IExchangeAdapter):
    """
    Bybit Implementation (USDT Futures).
    Uses CCXT.
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        self._api_key = api_key or os.getenv('BYBIT_API_KEY', '')
        self._api_secret = api_secret or os.getenv('BYBIT_SECRET', '')
        self._exchange: Optional[ccxt.bybit] = None

    @property
    def name(self) -> str:
        return "bybit"

    async def initialize(self, **kwargs) -> bool:
        """Initialize Bybit connection."""
        try:
            self._exchange = ccxt.bybit({
                'apiKey': self._api_key,
                'secret': self._api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'linear',  # USDT Futures
                    'adjustForTimeDifference': True,
                }
            })
            await self._exchange.load_markets()
            print(f"✅ BybitAdapter: Connected to USDT Futures")
            return True
        except Exception as e:
            print(f"❌ BybitAdapter: Init failed - {e}")
            return False

    async def fetch_candles(
        self, 
        symbol: str, 
        timeframe: str = '15m', 
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Bybit."""
        if not self._exchange:
            return pd.DataFrame()
            
        try:
            # CCXT handles symbol conversion automatically for standard pairs usually
            # But Bybit likes 'BTC/USDT:USDT' notation in ccxt sometimes
            ohlcv = await self._exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
            
        except Exception as e:
            print(f"⚠️ BybitAdapter: fetch_candles error ({symbol}): {e}")
            return pd.DataFrame()

    async def get_account_balance(self) -> Dict[str, float]:
        """Get Bybit account balance."""
        if not self._exchange:
            return {'total': 0, 'available': 0, 'currency': 'USDT'}
            
        try:
            # Bybit structure is complex, fetch_balance usually simplifies it
            balance = await self._exchange.fetch_balance({'type': 'swap', 'coin': 'USDT'})
            
            usdt = balance.get('USDT', {})
            return {
                'total': float(usdt.get('total', 0)),
                'available': float(usdt.get('free', 0)),
                'currency': 'USDT'
            }
        except Exception as e:
            print(f"⚠️ BybitAdapter: get_balance error: {e}")
            return {'total': 0, 'available': 0, 'currency': 'USDT'}

    async def place_order(
        self, 
        symbol: str, 
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Place order on Bybit."""
        if not self._exchange:
            return {'error': 'Not initialized'}
            
        try:
            params = kwargs.copy()
            params['positionIdx'] = 0 # 0 for One-Way Mode, 1/2 for Hedge
            
            if order_type.upper() == 'MARKET':
                result = await self._exchange.create_order(
                    symbol, 'market', side.lower(), quantity, None, params
                )
            elif order_type.upper() == 'LIMIT':
                result = await self._exchange.create_order(
                    symbol, 'limit', side.lower(), quantity, price, params
                )
            else:
                 # Conditional
                params['stopPrice'] = price
                # Bybit uses specific types or params for trigger orders
                # CCXT mapping: 'stop' -> 'market' with stopPrice
                result = await self._exchange.create_order(
                    symbol, order_type.lower(), side.lower(), quantity, price, params
                )
            
            return {
                'orderId': result.get('id'),
                'status': result.get('status'),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': result.get('price') or price
            }
            
        except Exception as e:
            return {'error': str(e)}

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order."""
        if not self._exchange:
            return False
            
        try:
            await self._exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"⚠️ BybitAdapter: cancel_order error: {e}")
            return False

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get active positions."""
        if not self._exchange:
            return []
            
        try:
            # Fetch Bybit positions
            positions = await self._exchange.fetch_positions(params={'settle': 'USDT'})
            active = []
            for p in positions:
                amt = float(p.get('contracts', 0))
                if amt != 0:
                    active.append({
                        'symbol': p.get('symbol', ''),
                        'side': p.get('side', '').upper(),
                        'quantity': abs(amt),
                        'entryPrice': float(p.get('entryPrice', 0)),
                        'unrealizedPnl': float(p.get('unrealizedPnl', 0)),
                        'leverage': int(p.get('leverage', 1))
                    })
            return active
        except Exception as e:
            print(f"⚠️ BybitAdapter: get_positions error: {e}")
            return []

    async def close(self):
        """Close connections."""
        if self._exchange:
            await self._exchange.close()
            self._exchange = None
