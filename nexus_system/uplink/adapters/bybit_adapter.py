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

    # Class-level cache for balance (persists across instances)
    _balance_cache: Dict[str, Any] = {'total': 0, 'available': 0, 'currency': 'USDT', 'timestamp': 0}
    _balance_cache_ttl: float = 30.0  # Cache TTL in seconds
    _last_balance_call: float = 0
    _balance_rate_limit: float = 10.0  # Minimum seconds between balance API calls
    
    # Rate limiting for fetch_candles (prevents API rate limit errors)
    _candles_rate_limiter: Dict[str, float] = {}  # Per-symbol last call time
    _candles_global_last_call: float = 0
    _candles_min_interval: float = 1.0  # Minimum 1 second between ANY candle calls
    _candles_per_symbol_interval: float = 30.0  # Minimum 30 seconds between calls for SAME symbol

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

            # DIRECT TIMESTAMP PATCHING FOR BYBIT - BEFORE ANY API CALLS
            # Bybit has extremely strict timestamp validation that can't be fixed with standard CCXT methods
            # We patch the milliseconds() method to always return timestamps 2 seconds in the past
            import time

            if not self._testnet:  # Only apply to live trading
                # Store original method
                original_milliseconds = self._exchange.milliseconds

                # Create patched method that returns time - 2 seconds
                def patched_milliseconds():
                    return int(time.time() * 1000) - 2000  # 2 seconds ago (tested and working)

                # Apply the patch BEFORE any API calls
                self._exchange.milliseconds = patched_milliseconds

                if verbose:
                    print(f"✅ BybitAdapter: Direct timestamp patching applied")
                    print(f"   ⏰ All timestamps will be generated 2 seconds in the past")
                    print(f"   🛡️ This ensures compatibility with Bybit's recv_window")

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
        """Fetch OHLCV data from Bybit with rate limiting."""
        import time
        
        if not self._exchange:
            return pd.DataFrame()

        # Check if symbol is available using smart verification
        if not await self.check_symbol_availability(symbol):
            return pd.DataFrame()  # Silently skip unavailable symbols

        # === RATE LIMITING ===
        current_time = time.time()
        
        # Global rate limit: minimum 1 second between ANY candle calls
        time_since_global = current_time - BybitAdapter._candles_global_last_call
        if time_since_global < self._candles_min_interval:
            # Too fast - silently skip (will retry next cycle)
            return pd.DataFrame()
        
        # Per-symbol rate limit: minimum 30 seconds between calls for SAME symbol
        cache_key = f"{symbol}:{timeframe}"
        last_call = BybitAdapter._candles_rate_limiter.get(cache_key, 0)
        if current_time - last_call < self._candles_per_symbol_interval:
            # Too soon for this symbol/timeframe - silently skip
            return pd.DataFrame()

        try:
            # Format symbol for CCXT (BTC/USDT:USDT for linear)
            formatted = self._format_symbol(symbol)
            ohlcv = await self._exchange.fetch_ohlcv(formatted, timeframe, limit=limit)
            
            # Update rate limiters on SUCCESS
            BybitAdapter._candles_global_last_call = time.time()
            BybitAdapter._candles_rate_limiter[cache_key] = time.time()

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df

        except Exception as e:
            error_str = str(e).lower()
            
            # Detect rate limiting errors and back off
            if '429' in error_str or 'rate limit' in error_str or 'too many' in error_str:
                # Rate limited - set a longer backoff for this symbol
                BybitAdapter._candles_rate_limiter[cache_key] = time.time() + 60  # 1 min extra backoff
                print(f"⏳ BybitAdapter: Rate limited on {symbol}, backing off 60s")
                return pd.DataFrame()
            
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
        """Get Bybit UTA (Unified Trading Account) balance with rate limiting and caching."""
        import time

        # 1. Return cached balance if within TTL (prevent excessive API calls)
        current_time = time.time()
        cache_age = current_time - BybitAdapter._balance_cache.get('timestamp', 0)

        if cache_age < self._balance_cache_ttl and BybitAdapter._balance_cache.get('available', 0) > 0:
            # Cache is fresh and has valid data
            return {
                'total': BybitAdapter._balance_cache.get('total', 0),
                'available': BybitAdapter._balance_cache.get('available', 0),
                'currency': 'USDT'
            }

        # 2. Rate limit: Minimum 10 seconds between API calls
        time_since_last_call = current_time - BybitAdapter._last_balance_call
        if time_since_last_call < self._balance_rate_limit:
            # Too soon - return cached balance (even if stale)
            cached = BybitAdapter._balance_cache
            if cached.get('available', 0) > 0:
                return {
                    'total': cached.get('total', 0),
                    'available': cached.get('available', 0),
                    'currency': 'USDT'
                }
            # No valid cache, return zeros (rare edge case)
            return {'total': 0, 'available': 0, 'currency': 'USDT'}

        if not self._exchange:
            return {'total': 0, 'available': 0, 'currency': 'USDT'}

        # 3. Attempt API call with rate limiting
        BybitAdapter._last_balance_call = current_time

        try:
            # CCXT's fetch_balance for Bybit V5 can vary by account type / permissions.
            # Try UNIFIED first, then fall back to default only (reduce API calls)
            balance = None

            candidates = [
                None,  # default (most common)
                {'accountType': 'UNIFIED'},
            ]

            for params in candidates:
                try:
                    if params is None:
                        balance = await self._exchange.fetch_balance()
                    else:
                        balance = await self._exchange.fetch_balance(params)
                    break
                except Exception:
                    continue

            if balance is None:
                # All attempts failed - return cached balance if available
                cached = BybitAdapter._balance_cache
                if cached.get('available', 0) > 0:
                    return {
                        'total': cached.get('total', 0),
                        'available': cached.get('available', 0),
                        'currency': 'USDT'
                    }
                return {'total': 0, 'available': 0, 'currency': 'USDT'}

            # 4. Parse balance
            usdt = balance.get('USDT', {})
            total = float(usdt.get('total', 0))
            available = float(usdt.get('free', 0))

            # UTA Fallback: If standard mapping is empty, check 'info' for UTA fields
            if total <= 0 and 'info' in balance:
                try:
                    infoList = balance['info'].get('result', {}).get('list', [])
                    if infoList:
                        uta = infoList[0]
                        total = float(uta.get('totalEquity', 0))
                        available = float(uta.get('totalAvailableBalance', 0))
                except Exception:
                    pass

            # Last Resort: Check CCXT total dict
            if total <= 0:
                total = float(balance.get('total', {}).get('USDT', 0))
                available = float(balance.get('free', {}).get('USDT', 0))

            # 5. Update cache with fresh data
            BybitAdapter._balance_cache = {
                'total': total,
                'available': available,
                'currency': 'USDT',
                'timestamp': current_time
            }

            return {
                'total': total,
                'available': available,
                'currency': 'USDT'
            }
        except Exception as e:
            # On error, return cached balance if available (never return 0 if we have valid cache)
            cached = BybitAdapter._balance_cache
            if cached.get('available', 0) > 0:
                return {
                    'total': cached.get('total', 0),
                    'available': cached.get('available', 0),
                    'currency': 'USDT'
                }

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
                # Conditional orders (STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET)
                # Bybit V5 CCXT: Use 'market' type with triggerPrice in params
                # triggerDirection: 1 = triggers when price rises ABOVE triggerPrice
                #                   2 = triggers when price falls BELOW triggerPrice

                stop_price = kwargs.get('stopPrice') or price
                order_type_upper = order_type.upper()
                
                # Determine trigger direction based on order type and side
                # For LONG position closing (SELL side):
                #   - SL triggers when price FALLS below stop price -> direction 2
                #   - TP triggers when price RISES above take profit -> direction 1
                # For SHORT position closing (BUY side):
                #   - SL triggers when price RISES above stop price -> direction 1
                #   - TP triggers when price FALLS below take profit -> direction 2

                if 'STOP' in order_type_upper and 'TAKE_PROFIT' not in order_type_upper:
                    # STOP_MARKET - Stop Loss
                    params['triggerDirection'] = 2 if side.upper() == 'SELL' else 1
                    order_label = 'StopLoss'
                elif 'TAKE_PROFIT' in order_type_upper:
                    # TAKE_PROFIT_MARKET - Take Profit
                    # Para cerrar LONG position (SELL side): activar cuando price > TP (rises above) -> direction 1
                    # Para cerrar SHORT position (BUY side): activar cuando price < TP (falls below) -> direction 2
                    params['triggerDirection'] = 1 if side.upper() == 'SELL' else 2
                    order_label = 'TakeProfit'
                elif 'TRAILING' in order_type_upper:
                    # TRAILING_STOP_MARKET - Trailing Stop
                    params['triggerDirection'] = 2 if side.upper() == 'SELL' else 1
                    # Bybit trailing uses 'trailingStop' parameter
                    callback_rate = kwargs.get('callbackRate', 1.0)
                    params['trailingStop'] = str(callback_rate)
                    order_label = 'TrailingStop'
                else:
                    params['triggerDirection'] = 2 if side.upper() == 'SELL' else 1
                    order_label = 'Conditional'

                # Set trigger price and ensure reduceOnly for closing orders
                params['triggerPrice'] = str(stop_price)
                params['reduceOnly'] = True
                
                # Remove stopPrice from params if present (we use triggerPrice)
                params.pop('stopPrice', None)

                print(f"🔧 BybitAdapter: Placing {order_label} order for {symbol} - Side: {side}, Qty: {quantity}, Trigger: {stop_price}")
                
                # CCXT Bybit V5: Use 'market' type with trigger params for conditional orders
                result = await self._exchange.create_order(
                    formatted, 'market', side.lower(), quantity, None, params
                )
                print(f"✅ BybitAdapter: {order_label} order placed successfully - ID: {result.get('id')}")
            
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
            print(f"❌ BybitAdapter: place_order error for {symbol}: {e}")
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

    def _get_current_position_stops(self, symbol: str, positions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get current TP/SL values for a symbol from positions data."""
        for position in positions:
            if position.get('symbol') == symbol:
                return {
                    'take_profit': float(position.get('takeProfitPrice') or 0),
                    'stop_loss': float(position.get('stopLossPrice') or 0)
                }
        return {'take_profit': 0, 'stop_loss': 0}

    async def set_trading_stop(
        self,
        symbol: str,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
        trailing_stop: Optional[float] = None,
        active_price: Optional[float] = None  # Para trailing stop
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
            # Get current position stops to avoid unnecessary API calls
            positions = await self.get_positions()
            current_stops = self._get_current_position_stops(symbol, positions)

            # Check if values are actually different (avoid "not modified" error)
            needs_update = False

            if take_profit is not None and abs(current_stops['take_profit'] - take_profit) > 0.01:
                needs_update = True
            if stop_loss is not None and abs(current_stops['stop_loss'] - stop_loss) > 0.01:
                needs_update = True
            if trailing_stop is not None:
                needs_update = True  # Always update trailing stop if specified

            # If no changes needed, return success (same as "not modified")
            if not needs_update:
                print(f"ℹ️ BybitAdapter: Trading stop unchanged for {symbol} (values already set)")
                return {'success': True, 'message': 'Trading stop unchanged (already set)', 'result': {'code': 34040}}

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
            if active_price is not None:
                params['activePrice'] = str(active_price)  # Para activar trailing

            # Use private API endpoint directly
            result = await self._exchange.private_post_v5_position_trading_stop(params)

            action = "set" if (take_profit or stop_loss or trailing_stop) else "cancelled"
            print(f"✅ BybitAdapter: Trading stop {action} for {symbol}")

            return {'success': True, 'message': f'Trading stop {action}', 'result': result}

        except Exception as e:
            error_str = str(e)
            # Handle "not modified" error as success
            if '34040' in error_str or 'not modified' in error_str.lower():
                print(f"ℹ️ BybitAdapter: Trading stop unchanged for {symbol} (not modified)")
                return {'success': True, 'message': 'Trading stop unchanged (not modified)', 'result': {'code': 34040}}
            else:
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
            callback_rate: Trailing DISTANCE (not percentage) - e.g., 0.01 for $0.01 distance
            activation_price: Price at which trailing activates
        """
        if not self._exchange:
            return {'success': False, 'message': 'Not initialized'}

        try:
            formatted = self._format_symbol(symbol)

            params = {
                'positionIdx': 0,
                'reduceOnly': True,
                'trailingStop': str(callback_rate)  # DISTANCIA, no porcentaje
            }

            if activation_price:
                params['activePrice'] = str(activation_price)

            result = await self._exchange.create_order(
                formatted, 'trailing_stop_market', side.lower(), quantity, None, params
            )

            print(f"✅ BybitAdapter: Trailing stop placed for {symbol} @ distance {callback_rate}")
            return {
                'success': True,
                'orderId': result.get('id'),
                'message': f'Trailing stop @ distance {callback_rate}'
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
                try:
                    # Safe extraction with None handling
                    contracts = p.get('contracts')
                    amt = float(contracts) if contracts is not None else 0.0

                    if amt != 0:
                        # Safe field extraction
                        symbol = self._unformat_symbol(p.get('symbol') or '')
                        side = p.get('side', '').lower()
                        position_side = 'LONG' if side == 'long' else 'SHORT'

                        # Safe numeric conversions
                        entry_price = float(p.get('entryPrice') or 0)
                        unrealized_pnl = float(p.get('unrealizedPnl') or 0)
                        leverage = int(p.get('leverage') or 1)
                        take_profit = float(p.get('takeProfitPrice') or 0)
                        stop_loss = float(p.get('stopLossPrice') or 0)

                        active.append({
                            'symbol': symbol,
                            'side': position_side,
                            'quantity': abs(amt),
                            'entryPrice': entry_price,
                            'unrealizedPnl': unrealized_pnl,
                            'leverage': leverage,
                            'takeProfit': take_profit,
                            'stopLoss': stop_loss,
                            'exchange': 'BYBIT'
                        })
                except (ValueError, TypeError) as field_error:
                    # Log individual position parsing errors but continue
                    symbol = p.get('symbol', 'UNKNOWN')
                    print(f"⚠️ BybitAdapter: Error parsing position {symbol}: {field_error}")
                    print(f"   Position data: {p}")
                    continue

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
                 except Exception as json_err:
                     print(f"⚠️ BybitAdapter: Failed to parse error JSON: {json_err}")
                     err_msg = f"Bybit Error (unparseable): {match.group(0)[:100]}"

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
                # Try to get tick size from filters (similar to Binance)
                info = market.get('info', {})

                # Look for price filter in Bybit format
                tick_size = None
                if 'priceFilter' in info:
                    price_filter = info['priceFilter']
                    tick_size = float(price_filter.get('tickSize', 0))
                elif 'filters' in info:
                    # Alternative: look in filters array
                    filters = info['filters']
                    for f in filters:
                        if f.get('filterType') == 'PRICE_FILTER':
                            tick_size = float(f.get('tickSize', 0))
                            break

                # If still no tick_size, try precision-based calculation
                if tick_size is None or tick_size <= 0:
                    price_precision = market.get('precision', {}).get('price', 0)
                    if price_precision and price_precision > 0:
                        if price_precision < 1:  # Already a tick size
                            tick_size = float(price_precision)
                        else:  # Decimal places, convert to tick size
                            tick_size = 10 ** (-int(price_precision))

                # Get min price for additional validation
                limits = market.get('limits', {})
                price_limits = limits.get('price', {})
                min_price = price_limits.get('min')

                # Validate and adjust tick_size if needed
                if tick_size is None or tick_size <= 0:
                    # Fallback: estimate tick size based on min price
                    if min_price and min_price > 0:
                        if min_price >= 1000:
                            tick_size = 1.0
                        elif min_price >= 100:
                            tick_size = 0.1
                        elif min_price >= 10:
                            tick_size = 0.01
                        elif min_price >= 1:
                            tick_size = 0.001
                        elif min_price >= 0.1:
                            tick_size = 0.0001
                        elif min_price >= 0.01:
                            tick_size = 0.00001
                        else:
                            tick_size = 0.000001
                    else:
                        # Generic crypto fallback
                        tick_size = 0.0001

                # Additional validation: tick_size shouldn't be too large
                if tick_size >= 1 and min_price and min_price < 1:
                    print(f"⚠️ BybitAdapter: Tick size {tick_size} too large for min_price {min_price}, adjusting")
                    tick_size = 0.0001  # Conservative fallback for crypto

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
