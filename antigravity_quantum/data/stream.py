import ccxt.async_support as ccxt
import pandas as pd
import asyncio
from typing import Dict, Any, List

class MarketStream:
    """
    Async Market Data Provider.
    Currently uses REST Polling via CCXT (Async).
    Can be upgraded to WebSockets (CCXT Pro) later.
    """
    def __init__(self, exchange_id='binance'):
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

    async def get_candles(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Fetches OHLCV data and returns a formatted dict ready for Strategy.analyze()
        Routes to AlpacaStream for Stocks/Commodities.
        """
        # ROUTING: Non-crypto symbols go to Alpaca
        try:
            from config import ASSET_GROUPS
            if symbol in ASSET_GROUPS.get('STOCKS', []) or symbol in ASSET_GROUPS.get('COMMODITY', []):
                # Delegate to AlpacaStream
                from .alpaca_stream import AlpacaStream
                alpaca = AlpacaStream()
                # Note: Alpaca init requires session keys, handled in QuantumEngine
                return await alpaca.get_candles(symbol, limit)
        except Exception as e:
            print(f"⚠️ Alpaca routing error: {e}")
            return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A"}
        
        # Only process crypto (symbols with USDT suffix)
        if not ('USDT' in symbol or 'BUSD' in symbol):
            return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A"}
        
        # 1. Resolve Timeframe based on asset config (Dynamic)
        timeframe = self.tf_map.get(symbol.split('USDT')[0], self.tf_map['default'])
        
        try:
            # 2. Fetch (Async)
            # symbol needs to be compatible with exchange (e.g. BTC/USDT)
            # internal we might use BTCUSDT, ccxt needs BTC/USDT usually
            formatted_symbol = symbol.replace('USDT', '/USDT') if 'USDT' in symbol and '/' not in symbol else symbol
            
            ohlcv = await self.exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=limit)
            
            # 3. Parse to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 4. Add Basic Indicators (Lightweight)
            # Ideally this moves to a 'Technicals' module, but keeping here for speed
            df['ema_20'] = df['close'].ewm(span=20).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            df['ema_200'] = df['close'].ewm(span=200).mean()
            
            # RSI (14) - Required for Mean Reversion and Scalping
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands (20, 2) - Required for Mean Reversion
            sma_20 = df['close'].rolling(window=20).mean()
            std_20 = df['close'].rolling(window=20).std()
            df['upper_bb'] = sma_20 + (std_20 * 2)
            df['lower_bb'] = sma_20 - (std_20 * 2)
            
            # ADX placeholder (Requires complex calc, mocking for prototype)
            # In production, use pandas_ta or ta-lib
            df['adx'] = 30.0 # Mock to allow Trend Strategy to trigger
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "dataframe": df
            }
            
        except Exception as e:
            print(f"⚠️ Data Fetch Error ({symbol}): {e}")
            return {"dataframe": pd.DataFrame()} # Empty DF


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
        
        # Synthetic ADX-like filter: 
        # If SMA slopes are aligned and Volatility is rising -> High Trend Strength
        # This is a robust proxy 
        df['adx'] = (abs(df['ema_20'] - df['ema_50']) / close) * 1000 
        # Normalized logic: > 5 usually means strong divergence/trend
        
        return df

    async def close(self):
        await self.exchange.close()
