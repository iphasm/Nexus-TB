import ccxt.async_support as ccxt
import pandas as pd
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo

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
    Currently uses REST Polling via CCXT (Async).
    Uses Binance USD-M Futures for crypto.
    """
    def __init__(self, exchange_id='binanceusdm'):  # Changed to USD-M Futures
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)()
        self.tf_map = {
            'BTC': '15m',  # Fast trend
            'ETH': '15m',
            'SOL': '5m',   # Scalping
            'ADA': '1h',   # Grid/Swing
            'default': '15m'
        }

    async def initialize(self):
        """Load markets"""
        try:
            print(f"🔌 Connecting to {self.exchange_id}...")
            await self.exchange.load_markets()
            print(f"✅ Connected to {self.exchange_id} (Async).")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Technical Indicators (Standard + Premium Volume)"""
        # EMAs
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        df['ema_200'] = df['close'].ewm(span=200).mean()
        
        # RSI (14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands (20, 2)
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        df['upper_bb'] = sma_20 + (std_20 * 2)
        df['lower_bb'] = sma_20 - (std_20 * 2)
        
        # ATR (Average True Range)
        prev_close = df['close'].shift(1)
        high_low = df['high'] - df['low']
        high_close = (df['high'] - prev_close).abs()
        low_close = (df['low'] - prev_close).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Synthetic ADX (Trend Strength)
        div = (df['ema_20'] - df['ema_50']).abs()
        df['adx'] = (div / df['close']) * 2500
        
        # --- PREMIUM INDICATORS (Volume) ---
        # Volume SMA (20)
        df['vol_sma'] = df['volume'].rolling(window=20).mean()
        
        # OBV (On-Balance Volume)
        obv_change = pd.Series(0.0, index=df.index, dtype=float)
        obv_change[df['close'] > df['close'].shift(1)] = df['volume']
        obv_change[df['close'] < df['close'].shift(1)] = -df['volume']
        df['obv'] = obv_change.cumsum()
        
        # Fill NaN
        df.bfill(inplace=True)
        df.fillna(0, inplace=True)
        return df

    def _is_alpaca_symbol(self, symbol: str) -> bool:
        """Check if symbol should be routed to Alpaca (stocks/commodities)."""
        try:
            from config import ASSET_GROUPS
            return symbol in ASSET_GROUPS.get('STOCKS', []) or symbol in ASSET_GROUPS.get('COMMODITY', [])
        except Exception:
            return False

    async def get_candles(self, symbol: str, limit: int = 100, timeframe: str = None) -> Dict[str, Any]:
        """
        Fetches OHLCV data. Support override timeframe.
        """
        # ROUTING: Non-crypto symbols go to Alpaca
        try:
            from config import ASSET_GROUPS
            import os
            if symbol in ASSET_GROUPS.get('STOCKS', []) or symbol in ASSET_GROUPS.get('COMMODITY', []):
                # Skip if US market is closed (avoid unnecessary API calls)
                if not is_us_market_open():
                    # Return empty data silently (market closed is expected, not an error)
                    return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A", "market_closed": True}
                
                # Delegate to AlpacaStream
                from .alpaca_stream import AlpacaStream
                alpaca_key = os.getenv('APCA_API_KEY_ID', '').strip("'\" ")
                alpaca_secret = os.getenv('APCA_API_SECRET_KEY', '').strip("'\" ")
                
                if not alpaca_key or not alpaca_secret:
                    print(f"⚠️ Alpaca keys missing - cannot fetch {symbol}")
                    return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A"}
                
                alpaca = AlpacaStream(api_key=alpaca_key, api_secret=alpaca_secret)
                await alpaca.initialize()
                return await alpaca.get_candles(symbol, limit) # alpaca get_candles might not support timeframe override yet, keeping simple
        except Exception as e:
            print(f"⚠️ Alpaca routing error for {symbol}: {e}")
            return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A"}
        
        # Only process crypto
        if not ('USDT' in symbol or 'BUSD' in symbol):
            return {"dataframe": pd.DataFrame()}
        
        # 1. Resolve Timeframe
        if not timeframe:
            timeframe = self.tf_map.get(symbol.split('USDT')[0], self.tf_map['default'])
        
        try:
            # 2. Fetch (Async)
            formatted_symbol = symbol.replace('USDT', '/USDT') if 'USDT' in symbol and '/' not in symbol else symbol
            ohlcv = await self.exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=limit)
            
            # 3. Parse to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 4. Add Indicators (Unified)
            df = self._add_indicators(df)
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "dataframe": df
            }
            
        except Exception as e:
            print(f"⚠️ Data Fetch Error ({symbol}): {e}")
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
        
        # Optimization: If main IS macro (unlikely but possible), skip double fetch
        if tf_main == tf_macro:
             data = await self.get_candles(symbol, limit, timeframe=tf_main)
             return {'main': data, 'macro': data}

        # 2. Fetch Concurrently
        try:
            task_main = self.get_candles(symbol, limit, timeframe=tf_main)
            task_macro = self.get_candles(symbol, limit, timeframe=tf_macro)
            
            # Run parallel
            res_main, res_macro = await asyncio.gather(task_main, task_macro)
            
            # Check for errors (empty frames)
            if res_main['dataframe'].empty:
                 print(f"⚠️ MTF Fetch Failed for Main ({symbol})")
            if res_macro['dataframe'].empty:
                 print(f"⚠️ MTF Fetch Failed for Macro ({symbol})")
                 
            return {
                'main': res_main,
                'macro': res_macro
            }
            
        except Exception as e:
            print(f"❌ MTF Execution Error: {e}")
            return {'main': {"dataframe": pd.DataFrame()}, 'macro': {"dataframe": pd.DataFrame()}}


    async def get_historical_candles(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Fetches a large dataset for backtesting using pagination.
        """
        timeframe = self.tf_map.get(symbol.split('USDT')[0], '15m')
        formatted_symbol = symbol.replace('USDT', '/USDT') if 'USDT' in symbol and '/' not in symbol else symbol
        
        # Calculate start time
        now = pd.Timestamp.now()
        start_time = now - pd.Timedelta(days=days)
        start_ts = int(start_time.timestamp() * 1000)
        
        all_ohlcv = []
        current_since = start_ts
        
        print(f"⏳ Fetching history for {symbol} ({days} days)...")
        
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
                print(f"⚠️ History Fetch Error: {e}")
                break
                
        if not all_ohlcv:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # 4. Add Basic Indicators (Native Pandas Implementation)
        close = df['close']

        # EMAs
        df['ema_20'] = close.ewm(span=20, adjust=False).mean()
        df['ema_50'] = close.ewm(span=50, adjust=False).mean()
        df['ema_200'] = close.ewm(span=200, adjust=False).mean()
        
        # RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands (20, 2)
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        df['upper_bb'] = sma_20 + (std_20 * 2)
        df['lower_bb'] = sma_20 - (std_20 * 2)
        
        # Approximate ADX (Simplified TR/DX for prototype speed)
        # Real ADX requires recursion, approximating with Volatility/Trend strength
        # Using ATR-like measure relative to price
        tr = df[['high', 'low', 'close']].max(axis=1) - df[['high', 'low', 'close']].min(axis=1)
        atr_14 = tr.rolling(14).mean()
        df['atr'] = atr_14
        
        # Synthetic ADX-like filter (same scale as get_candles: 2500)
        # Measures EMA divergence relative to price
        df['adx'] = (abs(df['ema_20'] - df['ema_50']) / close) * 2500
        
        return df

    async def close(self):
        await self.exchange.close()
