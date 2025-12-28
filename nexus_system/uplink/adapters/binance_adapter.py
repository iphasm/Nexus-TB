"""
Binance Futures Adapter.
Implements IExchangeAdapter for Binance USD-M Futures.
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional, Callable
import ccxt.async_support as ccxt

from .base import IExchangeAdapter


class BinanceAdapter(IExchangeAdapter):
    """
    Binance USD-M Futures implementation.
    Uses CCXT for REST and custom WebSocket for streaming.
    """

    def __init__(self, api_key: str = None, api_secret: str = None, **kwargs):
        self._api_key = api_key or os.getenv('BINANCE_API_KEY', '')
        self._api_secret = api_secret or os.getenv('BINANCE_SECRET', '')
        self._exchange: Optional[ccxt.binanceusdm] = None
        self._ws_manager = None
        self._price_cache = None
        
        # Debug: Show credential presence
        key_preview = f"{self._api_key[:4]}...{self._api_key[-4:]}" if len(self._api_key) > 8 else "(empty/short)"
        print(f"🔐 BinanceAdapter: Credentials loaded - Key: {key_preview}")

    @property
    def name(self) -> str:
        return "binance"

    async def initialize(self, **kwargs) -> bool:
        """Initialize Binance connection."""
        try:
            # Validate credentials
            if not self._api_key or not self._api_secret:
                print(f"❌ BinanceAdapter: Missing API credentials!")
                return False
            
            config = {
                'apiKey': self._api_key,
                'secret': self._api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            }
            
            # Proxy Config
            http_proxy = kwargs.get('http_proxy') or os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
            https_proxy = kwargs.get('https_proxy') or os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
            
            if http_proxy:
                config['httpProxy'] = http_proxy
                # config['httpsProxy'] = https_proxy or http_proxy # REMOVED to avoid conflict
                print(f"🌍 BinanceAdapter: Using Proxy -> {http_proxy}")

            self._exchange = ccxt.binanceusdm(config)
            await self._exchange.load_markets()
            print(f"✅ BinanceAdapter: Connected to USD-M Futures")
            return True
        except Exception as e:
            print(f"❌ BinanceAdapter: Init failed - {e}")
            return False

    async def fetch_candles(
        self, 
        symbol: str, 
        timeframe: str = '15m', 
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Binance Futures."""
        if not self._exchange:
            return pd.DataFrame()
            
        try:
            # Format symbol for CCXT (BTC/USDT:USDT for futures)
            formatted = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and ':' not in symbol else symbol
            ohlcv = await self._exchange.fetch_ohlcv(formatted, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
            
        except Exception as e:
            print(f"⚠️ BinanceAdapter: fetch_candles error ({symbol}): {e}")
            return pd.DataFrame()

    async def get_account_balance(self) -> Dict[str, float]:
        """Get Binance Futures account balance."""
        if not self._exchange:
            return {'total': 0, 'available': 0, 'currency': 'USDT'}
            
        try:
            balance = await self._exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            return {
                'total': float(usdt.get('total', 0)),
                'available': float(usdt.get('free', 0)),
                'currency': 'USDT'
            }
        except Exception as e:
            print(f"⚠️ BinanceAdapter: get_balance error: {e}")
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
        """Place order on Binance Futures."""
        if not self._exchange:
            return {'error': 'Not initialized'}
            
        try:
            params = kwargs.copy()
            
            if order_type.upper() == 'MARKET':
                result = await self._exchange.create_order(
                    symbol, 'market', side.lower(), quantity, None, params
                )
            elif order_type.upper() == 'LIMIT':
                result = await self._exchange.create_order(
                    symbol, 'limit', side.lower(), quantity, price, params
                )
            else:
                # For conditional orders, use raw exchange API
                params['type'] = order_type
                params['side'] = side.upper()
                params['symbol'] = symbol
                params['quantity'] = quantity
                
                # Determine limit price vs trigger price
                # If order type implies MARKET, limit_price must be None
                limit_price = price
                if 'MARKET' in order_type.upper():
                    limit_price = None
                    if price:
                        params['stopPrice'] = price
                else:
                    # STOP (Limit) or TAKE_PROFIT (Limit)
                    # If it's a Limit conditional, we normally need 2 prices:
                    # 1. Trigger (stopPrice)
                    # 2. Limit (price)
                    # The 'price' arg here is ambiguously used as Trigger in trading_manager.
                    # We assume 'price' arg is TRIGGER. limit_price must come from params or be same?
                    # STANDARD NEXUS CONVENTION: price arg = TRIGGER PRICE for conditional.
                    # Limit Price should be in params['price'] if needed, or we assume Trigger=Limit (risky).
                    # For now, let's fix the MARKET case which is the immediate crash.
                    if price:
                        params['stopPrice'] = price
                        # If params has 'price', use it as limit, else use None (which might fail for Limit orders)
                        if 'price' in params:
                            limit_price = params.pop('price') # Move to argument
                        else:
                            # If no separate limit price provided, use trigger as limit?
                            limit_price = price 
                
                result = await self._exchange.create_order(
                    symbol, order_type.lower(), side.lower(), quantity, limit_price, params
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
            # Try to extract detailed error message from ccxt exception
            error_msg = str(e)
            try:
                # CCXT errors often wrap JSON in the message
                if hasattr(e, 'args') and len(e.args) > 0:
                     # e.args[0] might be the raw message
                     pass
                
                # If it's a specific CCXT error, it might have 'code' and 'msg' attributes
                # But generic handling: try to parse json from string if present
                import json
                import re
                
                # Look for JSON part: {"code":...}
                match = re.search(r'\{.*"code":.*\}', error_msg)
                if match:
                    json_str = match.group(0)
                    data = json.loads(json_str)
                    clean_msg = f"Binance Error {data.get('code')}: {data.get('msg')}"
                    return {'error': clean_msg}
            except:
                pass
                
            return {'error': error_msg}

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order."""
        if not self._exchange:
            return False
            
        try:
            await self._exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"⚠️ BinanceAdapter: cancel_order error: {e}")
            return False

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get active positions."""
        if not self._exchange:
            return []
            
        try:
            positions = await self._exchange.fetch_positions()
            active = []
            for p in positions:
                amt = float(p.get('contracts') or 0)
                if amt != 0:
                    active.append({
                        'symbol': p.get('symbol', '').replace('/USDT:USDT', 'USDT'),
                        'side': 'LONG' if amt > 0 else 'SHORT',
                        'quantity': abs(amt),
                        'entryPrice': float(p.get('entryPrice') or 0),
                        'unrealizedPnl': float(p.get('unrealizedPnl') or 0),
                        'leverage': int(p.get('leverage') or 1),
                        'exchange': 'BINANCE'
                    })
            return active
        except Exception as e:
            print(f"⚠️ BinanceAdapter: get_positions error: {e}")
            return []

    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol precision and limits."""
        if not self._exchange:
            return {}
        try:
            formatted = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and ':' not in symbol and '/' not in symbol else symbol
            market = self._exchange.market(formatted)
            return {
                'qty_precision': int(market['precision']['amount']),
                'price_precision': int(market['precision']['price']),
                'min_notional': float(market['limits']['cost']['min'])
            }
        except Exception as e:
            # print(f"⚠️ BinanceAdapter Info Error: {e}")
            return {}

    async def cancel_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol."""
        if not self._exchange: return False
        try:
            formatted = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and '/' not in symbol else symbol
            await self._exchange.cancel_all_orders(formatted)
            return True
        except Exception as e:
            print(f"⚠️ BinanceAdapter Cancel Error ({symbol}): {e}")
            return False

    async def close_position(self, symbol: str) -> bool:
        """Close specific position (Market)."""
        if not self._exchange: return False
        try:
            # 1. Get Position
            positions = await self.get_positions()
            target_pos = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not target_pos: return True # Already closed
            
            qty = target_pos['quantity']
            side = target_pos['side']
            
            if qty == 0: return True
            
            # 2. Execute Close (Opposite Side)
            close_side = 'SELL' if side == 'LONG' else 'BUY'
            
            formatted = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and '/' not in symbol else symbol
            
            # Use param 'reduceOnly': True explicitly
            await self._exchange.create_order(
                formatted, 'market', close_side, qty, params={'reduceOnly': True}
            )
            return True
        except Exception as e:
            print(f"⚠️ BinanceAdapter Close Error ({symbol}): {e}")
            return False

    async def close(self):
        """Close connections."""
        if self._exchange:
            await self._exchange.close()
            self._exchange = None

    def supports_websocket(self) -> bool:
        return True

    async def stream_candles(
        self, 
        symbols: List[str], 
        callback: Callable[[str, dict], None]
    ):
        """Stream real-time candle updates via WebSocket."""
        from ..ws_manager import BinanceWSManager
        from ..price_cache import get_price_cache
        
        self._price_cache = get_price_cache()
        self._ws_manager = BinanceWSManager(symbols, timeframe='15m')
        
        async def on_candle(symbol: str, candle: dict):
            self._price_cache.update_candle(symbol, candle)
            await callback(symbol, candle)
        
        self._ws_manager.add_callback(on_candle)
        
        if await self._ws_manager.connect():
            await self._ws_manager.listen()
