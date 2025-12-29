"""
Alpaca Adapter.
Implements IExchangeAdapter for Alpaca (Stocks/ETFs).
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .base import IExchangeAdapter


def is_us_market_open() -> bool:
    """Check if US stock market is currently open."""
    et = ZoneInfo("America/New_York")
    now = datetime.now(et)
    
    if now.weekday() > 4:  # Weekend
        return False
    
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now <= market_close


class AlpacaAdapter(IExchangeAdapter):
    """
    Alpaca implementation for stocks and ETFs.
    Uses alpaca-py SDK.
    """

    def __init__(self, api_key: str = None, api_secret: str = None, paper: bool = True, **kwargs):
        # Track credential source for debugging
        key_source = 'PARAM'
        if api_key:
            self._api_key = api_key.strip("'\" ")
        elif os.getenv('ALPACA_API_KEY'):
            self._api_key = os.getenv('ALPACA_API_KEY').strip("'\" ")
            key_source = 'ALPACA_API_KEY env'
        elif os.getenv('APCA_API_KEY_ID'):
            self._api_key = os.getenv('APCA_API_KEY_ID').strip("'\" ")
            key_source = 'APCA_API_KEY_ID env'
        else:
            self._api_key = ''
            key_source = 'NONE'
        
        self._api_secret = (api_secret or 
                            os.getenv('ALPACA_API_SECRET') or 
                            os.getenv('ALPACA_SECRET_KEY') or 
                            os.getenv('APCA_API_SECRET_KEY', '')).strip("'\" ")
        self._paper = paper
        self._url_override = kwargs.get('url_override') or os.getenv('APCA_API_BASE_URL')
        self._trading_client = None
        self._data_client = None
        self._proxy_config = kwargs
        self._key_source = key_source  # Store for error messages

    @property
    def name(self) -> str:
        return "alpaca"

    async def initialize(self, verbose: bool = False, **kwargs) -> bool:
        """Initialize Alpaca connection."""
        if not self._api_key or not self._api_secret:
            if verbose: print("⚠️ AlpacaAdapter: No API keys provided")
            return False
            
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.data.historical import StockHistoricalDataClient
            
            self._trading_client = TradingClient(
                self._api_key, 
                self._api_secret, 
                paper=self._paper,
                url_override=self._url_override
            )
            self._data_client = StockHistoricalDataClient(
                self._api_key, 
                self._api_secret
            )
            
            # Test connection
            acct = self._trading_client.get_account()
            return True
            
        except Exception as e:
            mode = 'PAPER' if self._paper else 'LIVE'
            key_preview = self._api_key[:5] + "..." if self._api_key else "None"
            print(f"❌ AlpacaAdapter: Init failed ({mode}) - {e}")
            print(f"   Key Prefix: {key_preview} | Source: {self._key_source}")
            print(f"   Tip: Check your .env file and ensure config matches.")
            return False

    async def fetch_candles(
        self, 
        symbol: str, 
        timeframe: str = '15m', 
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Alpaca."""
        if not self._data_client:
            return pd.DataFrame()
            
        # Skip if market is closed
        if not is_us_market_open():
            return pd.DataFrame()
            
        try:
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
            
            # Map timeframe string to Alpaca TimeFrame
            tf_map = {
                '1m': TimeFrame.Minute,
                '5m': TimeFrame.Minute,
                '15m': TimeFrame.Minute,
                '1h': TimeFrame.Hour,
                '4h': TimeFrame.Hour,
                '1d': TimeFrame.Day,
            }
            
            alpaca_tf = tf_map.get(timeframe, TimeFrame.Minute)
            
            # Calculate start time (last N bars worth of time)
            end = datetime.now(ZoneInfo("America/New_York"))
            start = end - timedelta(days=7)  # Get enough data for limit
            
            from alpaca.data.enums import DataFeed

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=alpaca_tf,
                start=start,
                end=end,
                limit=limit,
                feed=DataFeed.IEX  # Use IEX for free tier compatibility
            )
            
            bars = self._data_client.get_stock_bars(request)
            
            if symbol not in bars.data or not bars.data[symbol]:
                return pd.DataFrame()
            
            records = []
            for bar in bars.data[symbol]:
                records.append({
                    'timestamp': bar.timestamp,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': float(bar.volume)
                })
            
            return pd.DataFrame(records)
            
        except Exception as e:
            print(f"⚠️ AlpacaAdapter: fetch_candles error ({symbol}): {e}")
            return pd.DataFrame()

    async def get_account_balance(self) -> Dict[str, float]:
        """Get Alpaca account balance."""
        if not self._trading_client:
            return {'total': 0, 'available': 0, 'currency': 'USD'}
            
        try:
            account = self._trading_client.get_account()
            return {
                'total': float(account.equity),
                'available': float(account.buying_power),
                'currency': 'USD'
            }
        except Exception as e:
            print(f"⚠️ AlpacaAdapter: get_balance error: {e}")
            return {'total': 0, 'available': 0, 'currency': 'USD'}

    async def place_order(
        self, 
        symbol: str, 
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Place order on Alpaca."""
        if not self._trading_client:
            return {'error': 'Not initialized'}
            
        try:
            from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            
            alpaca_side = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
            
            if order_type.upper() == 'MARKET':
                request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    time_in_force=TimeInForce.DAY
                )
            else:
                request = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=alpaca_side,
                    limit_price=price,
                    time_in_force=TimeInForce.DAY
                )
            
            order = self._trading_client.submit_order(request)
            
            return {
                'orderId': order.id,
                'status': order.status.value,
                'symbol': symbol,
                'side': side,
                'quantity': quantity
            }
            
        except Exception as e:
            return {'error': str(e)}

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order."""
        if not self._trading_client:
            return False
            
        try:
            self._trading_client.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            print(f"⚠️ AlpacaAdapter: cancel_order error: {e}")
            return False

    async def cancel_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol."""
        if not self._trading_client:
            return False
            
        try:
            from alpaca.trading.enums import QueryOrderStatus
            orders = self._trading_client.get_orders(
                status=QueryOrderStatus.OPEN,
                symbols=[symbol]
            )
            for order in orders:
                self._trading_client.cancel_order_by_id(order.id)
            return True
        except Exception as e:
            print(f"⚠️ AlpacaAdapter: cancel_orders error: {e}")
            return False

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get active positions."""
        if not self._trading_client:
            return []
            
        try:
            positions = self._trading_client.get_all_positions()
            result = []
            for p in positions:
                result.append({
                    'symbol': p.symbol,
                    'side': 'LONG' if float(p.qty) > 0 else 'SHORT',
                    'quantity': abs(float(p.qty)),
                    'entryPrice': float(p.avg_entry_price),
                    'unrealizedPnl': float(p.unrealized_pl),
                    'currentPrice': float(p.current_price),
                    'exchange': 'ALPACA'
                })
            return result
        except Exception as e:
            print(f"⚠️ AlpacaAdapter: get_positions error: {e}")
            return []

    async def close_position(self, symbol: str) -> bool:
        """Close specific position (Market)."""
        if not self._trading_client:
            return False
            
        try:
            positions = await self.get_positions()
            target_pos = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not target_pos:
                print(f"ℹ️ AlpacaAdapter: No position found for {symbol} (already closed)")
                return True  # Already closed
            
            qty = target_pos['quantity']
            side = target_pos['side']
            
            if qty == 0:
                return True
            
            # Execute close (opposite side)
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide
            
            close_side = OrderSide.SELL if side == 'LONG' else OrderSide.BUY
            
            from alpaca.trading.enums import TimeInForce

            request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=close_side,
                time_in_force=TimeInForce.DAY
            )
            
            self._trading_client.submit_order(request)
            print(f"🔒 AlpacaAdapter: Closing {symbol} - {close_side.value} {qty}")
            return True
            
        except Exception as e:
            print(f"⚠️ AlpacaAdapter: close_position error ({symbol}): {e}")
            return False

    async def close(self):
        """Close connections."""
        self._trading_client = None
        self._data_client = None

    def supports_websocket(self) -> bool:
        return True  # Alpaca has WebSocket support
