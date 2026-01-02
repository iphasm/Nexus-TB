"""
Bybit Futures Adapter.
Implements IExchangeAdapter for Bybit Unified Trading (USDT Perpetuals).
Focused on improved order management with single-call cancellation.
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional, Callable
import ccxt.async_support as ccxt

from .base import IExchangeAdapter


class BybitAdapter(IExchangeAdapter):
    """
    Bybit V5 Implementation (USDT Linear Perpetuals).
    Uses CCXT async with enhanced order cancellation capabilities.
    
    Key Improvements over Binance:
    - cancel_all_orders(): Single API call to cancel all orders
    - set_trading_stop(): Cancel/modify position-linked TP/SL
    - amend_order(): Hot-edit orders without cancel+replace
    """

    def __init__(self, api_key: str = None, api_secret: str = None, **kwargs):
        self._api_key = api_key or os.getenv('BYBIT_API_KEY', '')
        self._api_secret = api_secret or os.getenv('BYBIT_API_SECRET', '')
        self._exchange: Optional[ccxt.bybit] = None
        self._testnet = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'
        self._proxy_config = kwargs

    @property
    def name(self) -> str:
        return "bybit"

    async def initialize(self, verbose: bool = False, **kwargs) -> bool:
        """Initialize Bybit V5 connection."""
        try:
            # Clean credentials (strip whitespace/quotes)
            self._api_key = self._api_key.strip().strip("'\"") if self._api_key else ''
            self._api_secret = self._api_secret.strip().strip("'\"") if self._api_secret else ''
            
            # Merge init kwargs with method kwargs
            config_options = {**self._proxy_config, **kwargs}
            
            config = {
                'apiKey': self._api_key,
                'secret': self._api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'linear',  # USDT Perpetuals
                    'adjustForTimeDifference': True,
                    'recvWindow': 10000,  # Increase from 5000 to handle clock sync
                }
            }
            
            # Unified Proxy Config (CCXT Async uses aiohttp_proxy, NOT proxies dict)
            http_proxy = config_options.get('http_proxy') or os.getenv('PROXY_URL') or os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
            
            # Testnet support
            if self._testnet:
                config['sandbox'] = True
                
            self._exchange = ccxt.bybit(config)
            
            # For async CCXT, proxy must be set via aiohttp_proxy property AFTER creation
            if http_proxy:
                self._exchange.aiohttp_proxy = http_proxy
            
            await self._exchange.load_markets()

            # Clear cache for known available symbols that might have been incorrectly cached
            known_available = ['SUIUSDT', 'SEIUSDT', 'NEARUSDT', 'MATICUSDT', 'APTUSDT', 'OPUSDT', 'ARBUSDT', 'ATOMUSDT']
            for symbol in known_available:
                self._failed_symbols_cache.discard(symbol)

            return True

        except Exception as e:
            if verbose: print(f"❌ BybitAdapter: Init failed - {e}")
            return False

    # Cache de símbolos que fallaron (auto-aprendizaje)
    _failed_symbols_cache: set = set()

    async def check_symbol_availability(self, symbol: str) -> bool:
        """Check if a symbol is actually available on Bybit by querying the exchange."""
        if not self._exchange:
            return False

        try:
            # First check static exclusions
            from system_directive import is_symbol_available_on_exchange
            if not is_symbol_available_on_exchange(symbol, 'BYBIT'):
                return False

            # Check cache first
            if symbol in self._failed_symbols_cache:
                return False

            # Try to get symbol info (lightweight call)
            formatted = self._format_symbol(symbol)
            markets = self._exchange.markets
            return formatted in markets

        except Exception as e:
            print(f"⚠️ BybitAdapter: Error checking {symbol} availability: {e}")
            return False

    def clear_failed_cache(self, symbol: str = None):
        """Clear the failed symbols cache. If symbol is None, clear all."""
        if symbol:
            self._failed_symbols_cache.discard(symbol)
            print(f"🧹 BybitAdapter: Cleared cache for {symbol}")
        else:
            self._failed_symbols_cache.clear()
            print(f"🧹 BybitAdapter: Cleared all failed symbols cache")

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str = '15m',
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Bybit."""
        if not self._exchange:
            return pd.DataFrame()

        # Check if symbol is available using smart verification
        if not await self.check_symbol_availability(symbol):
            return pd.DataFrame()  # Silently skip unavailable symbols

        try:
            # Format symbol for CCXT (BTC/USDT:USDT for linear)
            formatted = self._format_symbol(symbol)
            ohlcv = await self._exchange.fetch_ohlcv(formatted, timeframe, limit=limit)

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df

        except Exception as e:
            error_str = str(e).lower()
            # Auto-learn: Only cache if clearly a "symbol not found" error
            if ('symbol' in error_str and ('not found' in error_str or 'invalid' in error_str or 'does not exist' in error_str)) or 'market not found' in error_str:
                self._failed_symbols_cache.add(symbol)
                # Only log once per symbol
                print(f"🔇 BybitAdapter: {symbol} not available on Bybit (cached)")
            else:
                # Don't cache temporary errors (rate limits, network issues, etc.)
                print(f"⚠️ BybitAdapter: fetch_candles error ({symbol}): {e}")
            return pd.DataFrame()

    async def get_account_balance(self) -> Dict[str, float]:
        """Get Bybit UTA (Unified Trading Account) balance."""
        if not self._exchange:
            return {'total': 0, 'available': 0, 'currency': 'USDT'}

        try:
            # CCXT's fetch_balance for Bybit V5 can vary by account type / permissions.
            # Try UNIFIED first, then fall back to default / other types.
            balance = None
            last_err = None

            candidates = [
                {'accountType': 'UNIFIED'},
                None,  # default
                {'accountType': 'CONTRACT'},
                {'accountType': 'SPOT'},
            ]

            print(f"🔍 BybitAdapter: Attempting balance fetch...")
            for i, params in enumerate(candidates):
                try:
                    account_type = params.get('accountType', 'default') if params else 'default'
                    print(f"🔍 BybitAdapter: Trying account type: {account_type}")

                    if params is None:
                        balance = await self._exchange.fetch_balance()
                    else:
                        balance = await self._exchange.fetch_balance(params)

                    print(f"✅ BybitAdapter: Balance fetched successfully with {account_type}")
                    # Debug: Show balance structure
                    print(f"📊 BybitAdapter: Raw balance keys: {list(balance.keys())}")
                    if 'USDT' in balance:
                        print(f"📊 BybitAdapter: USDT balance: {balance['USDT']}")
                    if 'info' in balance:
                        print(f"📊 BybitAdapter: Info section present")
                    break
                except Exception as e:
                    print(f"❌ BybitAdapter: Failed with {account_type}: {str(e)[:200]}...")
                    last_err = e
                    continue

            if balance is None:
                print(f"💥 BybitAdapter: All balance fetch attempts failed")
                raise last_err or RuntimeError("Bybit fetch_balance failed (unknown error)")
            
            # 1. Try CCXT standard mapping
            usdt = balance.get('USDT', {})
            print(f"🔍 BybitAdapter: Processing USDT dict: {usdt}")
            total = float(usdt.get('total', 0))
            available = float(usdt.get('free', 0))
            print(f"🔍 BybitAdapter: Parsed total={total}, available={available}")
            
            # 2. UTA Fallback: If standard mapping is empty, check 'info' for UTA fields
            # In Unified Trading Accounts, Bybit reports net worth in USD/USDT via totalEquity
            if total <= 0 and 'info' in balance:
                try:
                    # Bybit V5 structure
                    infoList = balance['info'].get('result', {}).get('list', [])
                    if infoList:
                        uta = infoList[0]
                        # Use totalEquity which represents the whole account value in USD
                        total = float(uta.get('totalEquity', 0))
                        available = float(uta.get('totalAvailableBalance', 0))
                except Exception as e:
                    print(f"⚠️ BybitAdapter: UTA info parsing error: {e}")
            
            # 3. Last Resort: Check CCXT total dict
            if total <= 0:
                total = float(balance.get('total', {}).get('USDT', 0))
                available = float(balance.get('free', {}).get('USDT', 0))

            result = {
                'total': total,
                'available': available,
                'currency': 'USDT'
            }
            print(f"🔍 BybitAdapter: Returning balance: {result}")
            return result
        except Exception as e:
            # Parse error (debounced to avoid log spam)
            err_msg = str(e)
            import re, json, time
            match = re.search(r'\{.*"code":.*\}', err_msg)
            if match:
                 try:
                     data = json.loads(match.group(0))
                     err_msg = f"Bybit Error {data.get('code')}: {data.get('msg')}"
                 except Exception:
                     pass

            now = time.time()
            last_ts = getattr(self, '_last_balance_error_ts', 0)
            if now - last_ts > 300:  # 5 min debounce
                print(f"⚠️ BybitAdapter: get_balance error: {err_msg}")
                self._last_balance_error_ts = now

            return {'total': 0, 'available': 0, 'currency': 'USDT'}

    async def get_market_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        if not self._exchange:
            return 0.0
            
        try:
            formatted = self._format_symbol(symbol)
            ticker = await self._exchange.fetch_ticker(formatted)
            return float(ticker.get('last', 0))
        except Exception as e:
            print(f"⚠️ BybitAdapter: get_market_price error ({symbol}): {e}")
            return 0.0

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol."""
        if not self._exchange:
            return False
            
        try:
            formatted = self._format_symbol(symbol)
            await self._exchange.set_leverage(leverage, formatted)
            print(f"✅ BybitAdapter: Leverage set to {leverage}x for {symbol}")
            return True
        except Exception as e:
            error_str = str(e).lower()
            # 'leverage not modified' means it's already set to the requested value - not an error
            if 'not modified' in error_str or 'no need to change' in error_str or '110043' in str(e):
                print(f"ℹ️ BybitAdapter: Leverage already at {leverage}x for {symbol}")
                return True
            print(f"⚠️ BybitAdapter: set_leverage error: {e}")
            return False


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

        # Check if symbol is available using smart verification
        if not await self.check_symbol_availability(symbol):
            return {'error': f'{symbol} not available on Bybit'}

        try:
            formatted = self._format_symbol(symbol)
            params = kwargs.copy()
            params['positionIdx'] = 0  # One-Way Mode
            
            if order_type.upper() == 'MARKET':
                result = await self._exchange.create_order(
                    formatted, 'market', side.lower(), quantity, None, params
                )
            elif order_type.upper() == 'LIMIT':
                result = await self._exchange.create_order(
                    formatted, 'limit', side.lower(), quantity, price, params
                )
            else:
                # Conditional orders (STOP_MARKET, TAKE_PROFIT_MARKET)
                # Bybit requires specific order types: 'Stop' and 'TakeProfit'
                # Bybit requires 'triggerDirection' for stop/trigger orders
                # 1 = ascending (triggers when price rises above triggerPrice) - used for TP on LONG, SL on SHORT
                # 2 = descending (triggers when price falls below triggerPrice) - used for SL on LONG, TP on SHORT

                stop_price = kwargs.get('stopPrice') or price
                params['triggerPrice'] = stop_price

                # Determine trigger direction based on order type and side
                # For SL: triggers when price moves AGAINST your position
                # For TP: triggers when price moves IN FAVOR of your position
                order_type_upper = order_type.upper()

                if 'STOP' in order_type_upper and 'TAKE_PROFIT' not in order_type_upper:
                    # STOP_MARKET - This is a Stop Loss
                    # Bybit V5 uses 'StopLoss' for stop loss orders
                    # SELL side (closing LONG) = price falling -> descending (2)
                    # BUY side (closing SHORT) = price rising -> ascending (1)
                    bybit_order_type = 'StopLoss'
                    params['triggerDirection'] = 2 if side.upper() == 'SELL' else 1
                elif 'TAKE_PROFIT' in order_type_upper:
                    # TAKE_PROFIT_MARKET - This is a Take Profit
                    # Bybit V5 uses 'TakeProfit' for take profit orders
                    # SELL side (closing LONG) = price rising -> ascending (1)
                    # BUY side (closing SHORT) = price falling -> descending (2)
                    bybit_order_type = 'TakeProfit'
                    params['triggerDirection'] = 1 if side.upper() == 'SELL' else 2
                else:
                    # Fallback for unknown order types
                    bybit_order_type = 'StopLoss'
                    params['triggerDirection'] = 2 if side.upper() == 'SELL' else 1

                result = await self._exchange.create_order(
                    formatted, bybit_order_type, side.lower(), quantity, None, params
                )
            
            return {
                'orderId': result.get('id'),
                'orderLinkId': result.get('clientOrderId'),
                'status': result.get('status'),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': result.get('price') or price
            }
            
        except Exception as e:
            return {'error': str(e)}


    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a single order by ID."""
        if not self._exchange:
            return False
            
        try:
            formatted = self._format_symbol(symbol)
            await self._exchange.cancel_order(order_id, formatted)
            return True
        except Exception as e:
            print(f"⚠️ BybitAdapter: cancel_order error: {e}")
            return False

    async def cancel_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol (required by IExchangeAdapter)."""
        result = await self.cancel_all_orders(symbol)
        return result.get('success', False)

    # =========================================================================
    # ENHANCED ORDER MANAGEMENT (Key Bybit Advantage)
    # =========================================================================

    async def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """
        Cancel ALL orders for a symbol in a SINGLE API call.
        This is the key improvement over Binance's individual cancellation loop.
        
        Returns: {'success': bool, 'cancelled': int, 'message': str}
        """
        if not self._exchange:
            return {'success': False, 'cancelled': 0, 'message': 'Not initialized'}
            
        try:
            formatted = self._format_symbol(symbol)
            
            # Bybit V5: Single call cancels all active + conditional orders
            result = await self._exchange.cancel_all_orders(formatted)
            
            # Result format: list of cancelled order IDs
            cancelled_count = len(result) if isinstance(result, list) else 1
            
            print(f"✅ BybitAdapter: Cancelled {cancelled_count} orders for {symbol} (single call)")
            return {
                'success': True,
                'cancelled': cancelled_count,
                'message': f'Cancelled {cancelled_count} orders'
            }
            
        except Exception as e:
            # No orders to cancel is not an error
            if 'no order' in str(e).lower() or 'not found' in str(e).lower():
                return {'success': True, 'cancelled': 0, 'message': 'No orders to cancel'}
            print(f"⚠️ BybitAdapter: cancel_all_orders error: {e}")
            return {'success': False, 'cancelled': 0, 'message': str(e)}

    async def set_trading_stop(
        self, 
        symbol: str, 
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
        trailing_stop: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Set or cancel TP/SL for a position using Bybit's trading-stop endpoint.
        
        To CANCEL: pass 0 as the value (e.g., stop_loss=0 cancels SL)
        To SET: pass the price value
        
        This is superior to Binance where TP/SL are separate conditional orders.
        """
        if not self._exchange:
            return {'success': False, 'message': 'Not initialized'}
            
        try:
            formatted = self._format_symbol(symbol)
            
            params = {
                'category': 'linear',
                'symbol': formatted.replace('/', '').replace(':USDT', ''),
                'positionIdx': 0  # One-Way Mode
            }
            
            if take_profit is not None:
                params['takeProfit'] = str(take_profit)
            if stop_loss is not None:
                params['stopLoss'] = str(stop_loss)
            if trailing_stop is not None:
                params['trailingStop'] = str(trailing_stop)
            
            # Use private API endpoint directly
            result = await self._exchange.private_post_v5_position_trading_stop(params)
            
            action = "set" if (take_profit or stop_loss or trailing_stop) else "cancelled"
            print(f"✅ BybitAdapter: Trading stop {action} for {symbol}")
            
            return {'success': True, 'message': f'Trading stop {action}', 'result': result}
            
        except Exception as e:
            print(f"⚠️ BybitAdapter: set_trading_stop error: {e}")
            return {'success': False, 'message': str(e)}

    async def amend_order(
        self, 
        symbol: str, 
        order_id: str, 
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Amend (hot-edit) an existing order without cancel+replace.
        Bybit native feature - not available on Binance.
        """
        if not self._exchange:
            return {'success': False, 'message': 'Not initialized'}
            
        try:
            formatted = self._format_symbol(symbol)
            
            params = {
                'category': 'linear',
                'symbol': formatted.replace('/', '').replace(':USDT', ''),
                'orderId': order_id
            }
            
            if quantity is not None:
                params['qty'] = str(quantity)
            if price is not None:
                params['price'] = str(price)
            if trigger_price is not None:
                params['triggerPrice'] = str(trigger_price)
            
            result = await self._exchange.private_post_v5_order_amend(params)
            
            print(f"✅ BybitAdapter: Order {order_id} amended")
            return {'success': True, 'message': 'Order amended', 'result': result}
            
        except Exception as e:
            print(f"⚠️ BybitAdapter: amend_order error: {e}")
            return {'success': False, 'message': str(e)}

    async def place_trailing_stop(
        self,
        symbol: str,
        side: str,
        quantity: float,
        callback_rate: float,
        activation_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place a native server-side trailing stop order.
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL' (to close position)
            quantity: Order quantity
            callback_rate: Trailing percentage (e.g., 1.0 for 1%)
            activation_price: Price at which trailing activates
        """
        if not self._exchange:
            return {'success': False, 'message': 'Not initialized'}
            
        try:
            formatted = self._format_symbol(symbol)
            
            params = {
                'positionIdx': 0,
                'reduceOnly': True,
                'trailingStop': str(callback_rate)
            }
            
            if activation_price:
                params['activePrice'] = activation_price
            
            result = await self._exchange.create_order(
                formatted, 'trailing_stop_market', side.lower(), quantity, None, params
            )
            
            print(f"✅ BybitAdapter: Trailing stop placed for {symbol} @ {callback_rate}%")
            return {
                'success': True,
                'orderId': result.get('id'),
                'message': f'Trailing stop @ {callback_rate}%'
            }
            
        except Exception as e:
            print(f"⚠️ BybitAdapter: place_trailing_stop error: {e}")
            return {'success': False, 'message': str(e)}

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get active positions."""
        if not self._exchange:
            return []
            
        try:
            positions = await self._exchange.fetch_positions(params={'settle': 'USDT'})
            active = []
            for p in positions:
                amt = float(p.get('contracts', 0))
                if amt != 0:
                    active.append({
                        'symbol': self._unformat_symbol(p.get('symbol', '')),
                        'side': 'LONG' if p.get('side') == 'long' else 'SHORT',
                        'quantity': abs(amt),
                        'entryPrice': float(p.get('entryPrice', 0)),
                        'unrealizedPnl': float(p.get('unrealizedPnl', 0)),
                        'leverage': int(p.get('leverage', 1)),
                        'takeProfit': float(p.get('takeProfitPrice', 0) or 0),
                        'stopLoss': float(p.get('stopLossPrice', 0) or 0),
                        'exchange': 'BYBIT'
                    })
            return active
        except Exception as e:
            # Parse error
            err_msg = str(e)
            import re, json
            match = re.search(r'\{.*"code":.*\}', err_msg)
            if match:
                 try:
                     data = json.loads(match.group(0))
                     err_msg = f"Bybit Error {data.get('code')}: {data.get('msg')}"
                 except: pass
                 
            print(f"⚠️ BybitAdapter: get_positions error: {err_msg}")
            return []

    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open orders for a symbol."""
        if not self._exchange:
            return []
            
        try:
            formatted = self._format_symbol(symbol) if symbol else None
            # CCXT fetch_open_orders handles V5 unified logic
            orders = await self._exchange.fetch_open_orders(formatted)
            
            result = []
            for o in orders:
                result.append({
                    'orderId': str(o.get('id', '')),
                    'symbol': self._unformat_symbol(o.get('symbol', '')),
                    'type': (o.get('type') or '').upper(),
                    'side': (o.get('side') or '').upper(),
                    'quantity': float(o.get('amount') or 0),
                    'price': float(o.get('price') or 0),
                    'stopPrice': float(o.get('stopPrice') or o.get('triggerPrice') or 0),
                    'status': o.get('status'),
                    'source': 'ccxt'
                })
                
            # Bybit V5 might classify stop orders separately in some contexts,
            # but usually fetch_open_orders returns conditional ones too if implemented in ccxt.
            # If standard orders are empty, let's verify if we need a specific 'algo' fetch (like Binance).
            # Note: CCXT for Bybit usually merges them or has 'fetchOpenOrders' cover standard.
            
            return result
        except Exception as e:
            print(f"⚠️ BybitAdapter: get_open_orders error: {e}")
            return []

    async def close_position(self, symbol: str) -> bool:
        """Close specific position (Market)."""
        if not self._exchange:
            return False
            
        try:
            # 1. Get positions
            positions = await self.get_positions()
            
            # Normalize symbol
            # Bybit 'symbol' in our get_positions is unformatted (BTCUSDT). 
            target_pos = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not target_pos:
                # If quantity 0 is returned in get_positions, it's filtered out usually.
                # But if simply not found, return True (already closed).
                return True
            
            qty = target_pos['quantity']
            side = target_pos['side']  # LONG or SHORT
            
            if qty <= 0:
                return True
                
            # 2. Place opposing order
            close_side = 'sell' if side == 'LONG' else 'buy'
            formatted = self._format_symbol(symbol)
            
            print(f"🔒 BybitAdapter: Closing {symbol} - {close_side} {qty}")
            
            # Bybit V5 requires reduceOnly for closing
            await self._exchange.create_order(
                formatted, 'market', close_side, qty, params={'reduceOnly': True}
            )
            return True
            
        except Exception as e:
            print(f"⚠️ BybitAdapter: close_position error: {e}")
            return False

    async def close(self):
        """Close connections."""
        if self._exchange:
            await self._exchange.close()
            self._exchange = None

    def supports_websocket(self) -> bool:
        return True

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol precision, tick size, and limits."""
        if not self._exchange:
            print(f"⚠️ BybitAdapter.get_symbol_info: No exchange instance for {symbol}")
            return {}

        try:
            formatted = self._format_symbol(symbol)

            # Check if markets are loaded
            if not self._exchange.markets:
                print(f"🔄 BybitAdapter: Loading markets for symbol info...")
                await self._exchange.load_markets()

            # Try to get market info
            try:
                market = self._exchange.market(formatted)
            except Exception as market_err:
                print(f"⚠️ BybitAdapter: Market '{formatted}' not found, reloading markets...")
                await self._exchange.load_markets()
                try:
                    market = self._exchange.market(formatted)
                except Exception as reload_err:
                    print(f"❌ BybitAdapter: Symbol '{formatted}' still not found after reload: {reload_err}")
                    return {}

            # Extract tick size and precision from market info
            tick_size = None
            price_precision = None

            try:
                # Bybit uses different structure than Binance
                # Try to get precision from market object
                price_precision = market.get('precision', {}).get('price', 0)

                # Try to get tick size from limits or calculate from precision
                limits = market.get('limits', {})
                price_limits = limits.get('price', {})
                min_price = price_limits.get('min')

                if min_price and min_price > 0:
                    # For crypto, tick size is often 0.1 or similar
                    # Use precision to calculate tick size
                    if price_precision and price_precision > 0:
                        tick_size = 10 ** (-price_precision)
                    else:
                        # Fallback: estimate tick size based on min price
                        if min_price >= 1:
                            tick_size = 0.1  # Common for prices >= $1
                        elif min_price >= 0.1:
                            tick_size = 0.01
                        else:
                            tick_size = 0.0001  # Very small for volatile assets

                # Fallback to precision-based calculation
                if tick_size is None and price_precision:
                    if price_precision < 1:  # Already a tick size
                        tick_size = float(price_precision)
                    else:  # Decimal places, convert to tick size
                        tick_size = 10 ** (-int(price_precision))

                # Final fallback
                if tick_size is None:
                    tick_size = 0.01  # Default for most crypto

            except Exception as e:
                print(f"⚠️ BybitAdapter: Error extracting tick_size: {e}")
                tick_size = 0.01  # Default fallback

            # Extract precision (price decimal places)
            if price_precision is None:
                try:
                    # Try to infer from tick size
                    if tick_size >= 1:
                        price_precision = 0
                    else:
                        price_precision = abs(int(np.log10(tick_size)))
                except:
                    price_precision = 2  # Default for most crypto

            # Create result dictionary similar to Binance format
            result = {
                'symbol': symbol,
                'formatted_symbol': formatted,
                'tick_size': tick_size,
                'price_precision': price_precision,
                'quantity_precision': int(market.get('precision', {}).get('amount', 0)),
                'min_qty': market.get('limits', {}).get('amount', {}).get('min', 0),
                'max_qty': market.get('limits', {}).get('amount', {}).get('max', 0),
                'step_size': market.get('limits', {}).get('amount', {}).get('min', 0.001),
                'exchange': 'BYBIT'
            }

            print(f"✅ BybitAdapter: Symbol info retrieved for {symbol}")
            return result

        except Exception as e:
            print(f"❌ BybitAdapter: Error getting symbol info for {symbol}: {e}")
            return {}

    # =========================================================================
    # HELPER METHODS

    def _format_symbol(self, symbol: str) -> str:
        """Convert BTCUSDT to BTC/USDT:USDT for CCXT linear futures, applying Bybit corrections."""
        # Use centralized bridge formatting if available
        if hasattr(self, '_bridge') and self._bridge:
            return self._bridge.format_symbol_for_exchange(symbol, 'BYBIT')

        # Fallback to local implementation
        # 1) Apply Bybit ticker corrections (e.g., 1000PEPEUSDT -> PEPEUSDT)
        try:
            from system_directive import get_bybit_corrected_ticker
            symbol = get_bybit_corrected_ticker(symbol)
        except Exception:
            pass

        if ':' in symbol:
            return symbol
        if '/' in symbol:
            return f"{symbol}:USDT"
        # BTCUSDT -> BTC/USDT:USDT
        base = symbol.replace('USDT', '')
        return f"{base}/USDT:USDT"

    def _unformat_symbol(self, symbol: str) -> str:
        """Convert BTC/USDT:USDT back to BTCUSDT."""
        # Use centralized bridge normalization if available
        if hasattr(self, '_bridge') and self._bridge:
            return self._bridge.normalize_symbol(symbol)

        # Fallback to local implementation
        return symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
