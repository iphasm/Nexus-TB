import ccxt.async_support as ccxt
import pandas as pd
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

# Adapter Pattern Support
from .adapters.base import IExchangeAdapter

from ..utils.logger import get_logger

def is_us_market_open() -> bool:
    """Check if US stock market is currently open (9:30 AM - 4:00 PM ET, Mon-Fri)."""
    et = ZoneInfo("America/New_York")
    now = datetime.now(et)
    
    # Weekday check (Monday=0, Friday=4)
    if now.weekday() > 4:  # Saturday or Sunday
        return False
    
    # Time check: 9:30 AM to 4:00 PM ET
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now <= market_close

class MarketStream:
    """
    Async Market Data Provider.
    Hybrid mode: WebSocket for real-time updates, REST for fallback.
    Supports adapter injection for exchange abstraction.
    """
    def __init__(self, exchange_id='binanceusdm', use_websocket: bool = True, 
                 adapters: Optional[Dict[str, IExchangeAdapter]] = None):
        self.logger = get_logger("MarketStream")
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)()
        self.tf_map = {
            'BTC': '15m',  # Fast trend
            'ETH': '15m',
            'SOL': '5m',   # Scalping
            'ADA': '1h',   # Grid/Swing
            'default': '15m'
        }
        self.alpaca = None
        
        # Adapter Pattern: Optional injected adapters
        # Keys: 'binance', 'alpaca', etc.
        self._adapters: Dict[str, IExchangeAdapter] = adapters or {}
        
        # WebSocket Integration
        self.use_websocket = use_websocket
        self.ws_manager = None
        self.price_cache = None
        self._ws_task = None
        
        # Alpaca WebSocket
        self.alpaca_ws_manager = None
        self.alpaca_price_cache = None
        self._alpaca_ws_task = None
        
        # Unified Callbacks
        self._callbacks = []

    def add_callback(self, callback):
        """Register callback for price updates (async def callback(symbol, candle))."""
        self._callbacks.append(callback)
        # Add to existing managers if already running
        if self.ws_manager:
            self.ws_manager.add_callback(callback)
        if self.alpaca_ws_manager:
            self.alpaca_ws_manager.add_callback(callback)

    def register_adapter(self, name: str, adapter: IExchangeAdapter):
        """Register an exchange adapter at runtime."""
        self._adapters[name] = adapter
        self.logger.info(f"🔌 Registered adapter: {name}")

    def _get_adapter(self, symbol: str) -> Optional[IExchangeAdapter]:
        """Get the appropriate adapter for a symbol using intelligent routing."""
        from system_directive import ASSET_GROUPS

        # Normalize symbol first
        normalized_symbol = symbol
        if 'USDT' in symbol and not symbol.endswith('USDT'):
            normalized_symbol = symbol.replace('/', '').replace(':USDT', 'USDT')

        # Helper function to check if exchange adapter is available
        def is_exchange_available(exchange: str) -> bool:
            return exchange.lower() in self._adapters

        # CRYPTO EXCHANGE ROUTING LOGIC (intelligent fallback):
        # For symbols in CRYPTO group, prefer Bybit over Binance
        # If Bybit fails, the calling code will fallback to Binance
        if normalized_symbol in ASSET_GROUPS.get('CRYPTO', []):
            # Prefer Bybit for crypto symbols (will fallback if not available)
            if is_exchange_available('bybit'):
                return self._adapters.get('bybit')
            elif is_exchange_available('binance'):
                return self._adapters.get('binance')

        # Stocks and ETFs - Alpaca only
        if (normalized_symbol in ASSET_GROUPS.get('STOCKS', []) or
            normalized_symbol in ASSET_GROUPS.get('ETFS', [])):
            if is_exchange_available('alpaca'):
                return self._adapters.get('alpaca')

        # BYBIT exclusive group
        if normalized_symbol in ASSET_GROUPS.get('BYBIT', []):
            if is_exchange_available('bybit'):
                return self._adapters.get('bybit')

        # Fallback patterns for crypto symbols
        if 'USDT' in normalized_symbol:
            if is_exchange_available('bybit'):
                return self._adapters.get('bybit')  # Prefer Bybit for crypto
            elif is_exchange_available('binance'):
                return self._adapters.get('binance')

        # Ultimate fallback for stocks (symbols without USDT/USD)
        if ('USDT' not in normalized_symbol and 'USD' not in normalized_symbol and
            '/' not in normalized_symbol):
            if is_exchange_available('alpaca'):
                return self._adapters.get('alpaca')

        return None

    async def initialize(self, alpaca_key: str = None, alpaca_secret: str = None, crypto_symbols: list = None):
        """Load markets and optionally start WebSocket streams."""
        try:
            self.logger.info(f"Connecting to {self.exchange_id}...")
            await self.exchange.load_markets()
            self.logger.info(f"Connected to {self.exchange_id} (Async).")
            
            # Initialize Alpaca Stream (Single Instance)
            import os
            # Prioritize passed keys, fallback to ENV
            key = alpaca_key or os.getenv('APCA_API_KEY_ID', '').strip("'\" ")
            secret = alpaca_secret or os.getenv('APCA_API_SECRET_KEY', '').strip("'\" ")
            
            if key and secret:
                try:
                    from .alpaca_stream import AlpacaStream
                    self.alpaca = AlpacaStream(api_key=key, api_secret=secret)
                    await self.alpaca.initialize()
                    # Message printed by AlpacaStream.initialize()
                    
                    # Initialize Alpaca WebSocket (if enabled)
                    if self.use_websocket:
                        from system_directive import ASSET_GROUPS
                        stock_symbols = ASSET_GROUPS.get('STOCKS', []) + ASSET_GROUPS.get('ETFS', [])
                        if stock_symbols:
                            await self._init_alpaca_websocket(stock_symbols, key, secret)
                except Exception as ex:
                    self.logger.warning(f"Alpaca Stream Init Failed: {ex}")
            else:
                self.logger.warning("No Alpaca Keys found (Env or Passed). Stocks disabled.")
                self.alpaca = None
            
            # Initialize WebSocket for crypto (if enabled)
            if self.use_websocket and crypto_symbols:
                await self._init_websocket(crypto_symbols)
                
        except Exception as e:
            self.logger.error(f"Connection Failed: {e}")
    
    async def _init_websocket(self, symbols: list):
        """Initialize WebSocket connection for crypto symbols."""
        try:
            from .ws_manager import BinanceWSManager
            from .price_cache import get_price_cache  # Use global singleton
            
            # Filter crypto symbols only
            crypto_symbols = [s for s in symbols if 'USDT' in s]
            
            if not crypto_symbols:
                self.logger.info("WebSocket: No crypto symbols to subscribe")
                return
            
            self.price_cache = get_price_cache()  # Use singleton for shared access
            self.ws_manager = BinanceWSManager(crypto_symbols, timeframe='15m')
            
            # Register callback to update cache
            async def on_candle(symbol: str, candle: dict):
                self.price_cache.update_candle(symbol, candle)
            
            self.ws_manager.add_callback(on_candle)
            
            # Register user callbacks
            for cb in self._callbacks:
                self.ws_manager.add_callback(cb)
            
            # Connect and start listening in background
            if await self.ws_manager.connect():
                self._ws_task = asyncio.create_task(self.ws_manager.listen())
                self.logger.info(f"WebSocket: Streaming {len(crypto_symbols)} crypto symbols")
            else:
                self.logger.warning("WebSocket: Failed to connect, using REST fallback")
                self.use_websocket = False
                
        except ImportError as e:
            self.logger.warning(f"WebSocket: Module not available ({e}), using REST")
            self.use_websocket = False
        except Exception as e:
            self.logger.warning(f"WebSocket: Init failed ({e}), using REST fallback")
            self.use_websocket = False
    
    async def _init_alpaca_websocket(self, symbols: list, api_key: str, api_secret: str):
        """Initialize WebSocket connection for Alpaca stocks/ETFs."""
        try:
            from .alpaca_ws_manager import AlpacaWSManager
            from .price_cache import get_alpaca_price_cache
            
            if not symbols:
                self.logger.info("AlpacaWS: No stock symbols to subscribe")
                return
            
            self.alpaca_price_cache = get_alpaca_price_cache()
            self.alpaca_ws_manager = AlpacaWSManager(symbols, api_key, api_secret)
            
            # Register callback to update cache
            async def on_alpaca_candle(symbol: str, candle: dict):
                self.alpaca_price_cache.update_candle(symbol, candle)
            
            self.alpaca_ws_manager.add_callback(on_alpaca_candle)
            
            # Register user callbacks
            for cb in self._callbacks:
                self.alpaca_ws_manager.add_callback(cb)
            
            # Connect and start listening in background
            if await self.alpaca_ws_manager.connect():
                self._alpaca_ws_task = asyncio.create_task(self.alpaca_ws_manager.listen())
                self.logger.info(f"AlpacaWS: Streaming {len(symbols)} stock/ETF symbols")
            else:
                self.logger.warning("AlpacaWS: Not connected (market may be closed), using REST fallback")
                
        except ImportError as e:
            self.logger.warning(f"AlpacaWS: Module not available ({e}), using REST")
        except Exception as e:
            self.logger.warning(f"AlpacaWS: Init failed ({e}), using REST fallback")

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Technical Indicators (Standard + Premium Volume) using Centralized Utility"""
        from ..utils.indicators import TechnicalIndicators
        return TechnicalIndicators.add_all_indicators(df)

    def _is_alpaca_symbol(self, symbol: str) -> bool:
        """Check if symbol should be routed to Alpaca (stocks/commodities)."""
        try:
            from system_directive import ASSET_GROUPS
            return symbol in ASSET_GROUPS.get('STOCKS', []) or symbol in ASSET_GROUPS.get('ETFS', [])
        except Exception:
            return False

    async def get_candles(self, symbol: str, limit: int = 100, timeframe: str = None) -> Dict[str, Any]:
        """
        Fetches OHLCV data. Uses WebSocket cache when available, REST fallback otherwise.
        """
        # ROUTING: Non-crypto symbols go to Alpaca
        try:
            from system_directive import ASSET_GROUPS
            import os
            if symbol in ASSET_GROUPS.get('STOCKS', []) or symbol in ASSET_GROUPS.get('ETFS', []):
                # Skip if US market is closed (avoid unnecessary API calls)
                if not is_us_market_open():
                    return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A", "market_closed": True}
                
                # Try Alpaca WebSocket cache first
                if self.alpaca_price_cache and not self.alpaca_price_cache.is_stale(symbol, max_age_seconds=90):
                    cached_df = self.alpaca_price_cache.get_dataframe(symbol)
                    if not cached_df.empty and len(cached_df) >= 50:
                        df = self._add_indicators(cached_df)
                        return {
                            "symbol": symbol,
                            "timeframe": "15m",
                            "dataframe": df,
                            "source": "websocket"
                        }
                
                # Fallback to REST API
                if not self.alpaca:
                    # Silent fail if no keys (logged at init)
                    return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A"}
                
                result = await self.alpaca.get_candles(symbol, limit)
                
                # Backfill WS cache with REST data
                if self.alpaca_price_cache and not result['dataframe'].empty:
                    candles = result['dataframe'].to_dict('records')
                    for c in candles:
                        c['is_closed'] = True
                    self.alpaca_price_cache.backfill(symbol, candles)
                
                return result
        except Exception as e:
            self.logger.warning_debounced(f"Alpaca routing error for {symbol}: {e}", interval=300)
            return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A"}
        
        # Only process crypto
        if not ('USDT' in symbol or 'BUSD' in symbol):
            return {"dataframe": pd.DataFrame()}
        
        # 1. Resolve Timeframe
        if not timeframe:
            timeframe = self.tf_map.get(symbol.split('USDT')[0], self.tf_map['default'])
        
        # 2. Try WebSocket cache first (if enabled and fresh)
        if self.use_websocket and self.price_cache and not self.price_cache.is_stale(symbol, max_age_seconds=90):
            cached_df = self.price_cache.get_dataframe(symbol)
            if not cached_df.empty and len(cached_df) >= 50:  # Need enough for indicators
                # Add indicators to cached data
                df = self._add_indicators(cached_df)
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "dataframe": df,
                    "source": "websocket"
                }
        
        # 3. REST Fallback
        try:
            adapter = self._get_adapter(symbol)
            if adapter:
                df = await adapter.fetch_candles(symbol, timeframe=timeframe, limit=limit)
                if not df.empty:
                    # Add Indicators (Unified)
                    df = self._add_indicators(df)
                    
                    # Backfill WebSocket cache with REST data
                    if self.price_cache:
                        candles = df.to_dict('records')
                        for c in candles:
                            c['is_closed'] = True
                        self.price_cache.backfill(symbol, candles)
                        
                    return {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "dataframe": df,
                        "source": f"adapter:{adapter.name}"
                    }
                else:
                    # Adapter returned empty data, try fallback for crypto symbols
                    if 'USDT' in symbol and adapter.name.lower() == 'bybit':
                        # Try Binance as fallback for crypto symbols
                        binance_adapter = self._adapters.get('binance')
                        if binance_adapter:
                            self.logger.info(f"Bybit returned no data for {symbol}, trying Binance fallback")
                            df = await binance_adapter.fetch_candles(symbol, timeframe=timeframe, limit=limit)
                            if not df.empty:
                                # Add Indicators (Unified)
                                df = self._add_indicators(df)

                                # Backfill WebSocket cache with REST data
                                if self.price_cache:
                                    candles = df.to_dict('records')
                                    for c in candles:
                                        c['is_closed'] = True
                                    self.price_cache.backfill(symbol, candles)

                                return {
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                    "dataframe": df,
                                    "source": "adapter:binance (fallback)"
                                }
            except Exception as adapter_error:
                # Adapter failed, try fallback for crypto symbols
                if 'USDT' in symbol and adapter and adapter.name.lower() == 'bybit':
                    binance_adapter = self._adapters.get('binance')
                    if binance_adapter:
                        self.logger.info(f"Bybit failed for {symbol} ({adapter_error}), trying Binance fallback")
                        try:
                            df = await binance_adapter.fetch_candles(symbol, timeframe=timeframe, limit=limit)
                            if not df.empty:
                                # Add Indicators (Unified)
                                df = self._add_indicators(df)

                                # Backfill WebSocket cache with REST data
                                if self.price_cache:
                                    candles = df.to_dict('records')
                                    for c in candles:
                                        c['is_closed'] = True
                                    self.price_cache.backfill(symbol, candles)

                                return {
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                    "dataframe": df,
                                    "source": "adapter:binance (fallback)"
                                }
                        except Exception as binance_error:
                            self.logger.warning(f"Binance fallback also failed for {symbol}: {binance_error}")
                else:
                    # Re-raise the original error if not a crypto symbol or not Bybit
                    raise adapter_error

            # Original fallback to self.exchange (Binance) if no adapter found
            # NOTE: Binance USDM Futures uses 'BASE/QUOTE:QUOTE' format (e.g. BTC/USDT:USDT)
            formatted_symbol = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and ':' not in symbol else symbol
            ohlcv = await self.exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=limit)
            
            # Parse to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Add Indicators (Unified)
            df = self._add_indicators(df)
            
            # Backfill WebSocket cache with REST data
            if self.price_cache:
                candles = df.to_dict('records')
                for c in candles:
                    c['is_closed'] = True
                self.price_cache.backfill(symbol, candles)
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "dataframe": df,
                "source": "rest"
            }
            
        except Exception as e:
            self.logger.warning_debounced(f"Data Fetch Error ({symbol}): {e}", interval=300)
            return {"dataframe": pd.DataFrame()}

    async def get_multiframe_candles(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Fetches both Lower Timeframe (Strategy TF) and Higher Timeframe (4h) candles.
        Returns: {'main': dict, 'macro': dict}
        """
        # ROUTING: Non-crypto symbols go to Alpaca (no MTF needed for stocks)
        if self._is_alpaca_symbol(symbol):
            data = await self.get_candles(symbol, limit)
            # Use same data for both main and macro (stocks don't need MTF analysis)
            return {'main': data, 'macro': data}
        
        # 1. Identify Timeframes (crypto only from here)
        tf_main = self.tf_map.get(symbol.split('USDT')[0], self.tf_map['default'])
        tf_macro = '4h'
        
        # Micro TF Logic (1m for Scalping)
        # If main is small (5m), micro is 1m. If main is 15m, micro is 1m.
        tf_micro = '1m'
        
        # Optimization: If main IS macro (unlikely but possible), skip double fetch
        if tf_main == tf_macro:
             data = await self.get_candles(symbol, limit, timeframe=tf_main)
             return {'main': data, 'macro': data, 'micro': {"dataframe": pd.DataFrame()}}

        # 2. Fetch Concurrently (Main + Macro + Micro)
        try:
            task_main = self.get_candles(symbol, limit, timeframe=tf_main)
            task_macro = self.get_candles(symbol, limit, timeframe=tf_macro)
            task_micro = self.get_candles(symbol, 50, timeframe=tf_micro) # Smaller limit for micro is fine
            
            # Run parallel
            res_main, res_macro, res_micro = await asyncio.gather(task_main, task_macro, task_micro)
            
            # Check for errors (empty frames)
            if res_main['dataframe'].empty:
                 self.logger.debug(f"MTF Fetch Failed for Main ({symbol})")
            if res_macro['dataframe'].empty:
                 self.logger.debug(f"MTF Fetch Failed for Macro ({symbol})")
                 
            return {
                'main': res_main,
                'macro': res_macro,
                'micro': res_micro
            }
            
        except Exception as e:
            self.logger.error(f"MTF Execution Error: {e}")
            return {
                'main': {"dataframe": pd.DataFrame()}, 
                'macro': {"dataframe": pd.DataFrame()},
                'micro': {"dataframe": pd.DataFrame()}
            }


    async def get_historical_candles(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Fetches a large dataset for backtesting using pagination.
        """
        # SKIP NON-CRYPTO (Alpaca history not supported yet in this method)
        if self._is_alpaca_symbol(symbol):
            return pd.DataFrame()

        timeframe = self.tf_map.get(symbol.split('USDT')[0], '15m')
        # NOTE: Binance USDM Futures uses 'BASE/QUOTE:QUOTE' format (e.g. BTC/USDT:USDT)
        formatted_symbol = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and ':' not in symbol else symbol
        
        # Calculate start time
        now = pd.Timestamp.now()
        start_time = now - pd.Timedelta(days=days)
        start_ts = int(start_time.timestamp() * 1000)
        
        all_ohlcv = []
        current_since = start_ts
        
        self.logger.info(f"Fetching history for {symbol} ({days} days)...")
        
        for _ in range(10): # Safety limit 10 pages
            try:
                ohlcv = await self.exchange.fetch_ohlcv(formatted_symbol, timeframe, since=current_since, limit=1000)
                if not ohlcv:
                    break
                
                all_ohlcv.extend(ohlcv)
                current_since = ohlcv[-1][0] + 1 # Next ms
                
                # Check if we reached recent time
                if len(ohlcv) < 1000:
                    break
                    
                await asyncio.sleep(0.2) # Rate limit protection
                
            except Exception as e:
                self.logger.warning(f"History Fetch Error: {e}")
                break
                
        if not all_ohlcv:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # 4. Add Indicators (Standardized)
        df = self._add_indicators(df)
        
        return df

    async def close(self):
        """Close all connections (REST + WebSocket)."""
        # Close Binance WebSocket
        if self._ws_task:
            self._ws_task.cancel()
        if self.ws_manager:
            await self.ws_manager.close()
        
        # Close Alpaca WebSocket
        if self._alpaca_ws_task:
            self._alpaca_ws_task.cancel()
        if self.alpaca_ws_manager:
            await self.alpaca_ws_manager.close()
        
        # Close REST
        await self.exchange.close()

