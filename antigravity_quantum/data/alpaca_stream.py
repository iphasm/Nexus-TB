"""
Antigravity Quantum - Alpaca Market Data Stream
Fetches OHLCV data for Stocks and Commodities (ETFs) via Alpaca Data API.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class AlpacaStream:
    """
    Market Data Provider for Stocks/Commodities using Alpaca Data API.
    Requires valid Alpaca API keys in the user's session.
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = None
        
    async def initialize(self, api_key: str = None, api_secret: str = None):
        """Initialize Alpaca client with provided or stored keys."""
        if api_key:
            self.api_key = api_key
        if api_secret:
            self.api_secret = api_secret
            
        if not self.api_key or not self.api_secret:
            print("⚠️ AlpacaStream: No API keys provided.")
            return False
            
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            self.client = StockHistoricalDataClient(self.api_key, self.api_secret)
            print("✅ AlpacaStream: Connected.")
            return True
        except Exception as e:
            print(f"❌ AlpacaStream Init Error: {e}")
            return False
    
    async def get_candles(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Fetches OHLCV data for a stock/ETF symbol.
        Returns same format as MarketStream for strategy compatibility.
        """
        if not self.client:
            return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A"}
        
        try:
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
            
            # Calculate date range (last ~7 days for 15m bars)
            end = datetime.now()
            start = end - timedelta(days=7)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame(15, TimeFrameUnit.Minute),  # 15-minute bars
                start=start,
                end=end,
                limit=limit
            )
            
            bars = self.client.get_stock_bars(request)
            
            if symbol not in bars or len(bars[symbol]) == 0:
                return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "15m"}
            
            # Convert to DataFrame
            data = []
            for bar in bars[symbol]:
                data.append({
                    'timestamp': bar.timestamp,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': float(bar.volume)
                })
            
            df = pd.DataFrame(data)
            
            if df.empty:
                return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "15m"}
            
            # Add indicators (same as MarketStream)
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
            
            # ADX placeholder
            df['adx'] = 25.0
            
            return {
                "symbol": symbol,
                "timeframe": "15m",
                "dataframe": df
            }
            
        except Exception as e:
            print(f"⚠️ AlpacaStream Error ({symbol}): {e}")
            return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "N/A"}
    
    async def close(self):
        """Cleanup (no persistent connection for REST API)."""
        self.client = None
