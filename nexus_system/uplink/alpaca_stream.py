"""
Nexus System - Alpaca Market Data Stream
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
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
            
            # Calculate date range (last ~7 days for 15m bars)
            end = datetime.now()
            start = end - timedelta(days=7)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame(15, TimeFrameUnit.Minute),  # 15-minute bars
                start=start,
                end=end,
                limit=limit,
                feed="iex"  # Use IEX feed (free tier) instead of SIP (paid)
            )
            
            print(f"📡 AlpacaStream: Requesting bars for {symbol}...")
            import asyncio
            loop = asyncio.get_event_loop()
            bars = await loop.run_in_executor(None, self.client.get_stock_bars, request)
            
            # BarSet can be accessed like bars[symbol] or bars.data[symbol]
            # Handle both dict-like and object-like access patterns
            symbol_bars = None
            try:
                # Try direct index access (newer alpaca-py versions)
                if hasattr(bars, 'data') and symbol in bars.data:
                    symbol_bars = bars.data[symbol]
                elif symbol in bars:
                    symbol_bars = bars[symbol]
            except (TypeError, KeyError):
                pass
            
            if not symbol_bars or len(symbol_bars) == 0:
                print(f"⚠️ AlpacaStream: No bars returned for {symbol}")
                return {"dataframe": pd.DataFrame(), "symbol": symbol, "timeframe": "15m"}
            
            print(f"✅ AlpacaStream: Received {len(symbol_bars)} bars for {symbol}")
            
            # Convert to DataFrame
            data = []
            for bar in symbol_bars:
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
            
            # Add indicators using pandas-ta wrappers
            from servos.indicators import (
                calculate_ema, calculate_rsi, calculate_bollinger_bands,
                calculate_atr, calculate_adx
            )
            
            df['ema_20'] = calculate_ema(df['close'], period=20)
            df['ema_50'] = calculate_ema(df['close'], period=50)
            df['ema_200'] = calculate_ema(df['close'], period=200)
            
            # RSI (14)
            df['rsi'] = calculate_rsi(df['close'], period=14)
            
            # Bollinger Bands (20, 2)
            bb = calculate_bollinger_bands(df['close'], period=20, std_dev=2.0)
            df['upper_bb'] = bb['upper']
            df['lower_bb'] = bb['lower']
            
            # ATR (14)
            df['atr'] = calculate_atr(df, period=14)
            
            # ADX (14)
            adx_data = calculate_adx(df, period=14)
            df['adx'] = adx_data['adx']
            
            # Volume SMA (20)
            df['vol_sma'] = df['volume'].rolling(window=20).mean()
            
            # Fill NaN values
            df.bfill(inplace=True)
            df.fillna(0, inplace=True)
            
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

