"""
Nexus Trading Bot - Market Data Fetcher
Synchronous wrapper for fetching market data from Binance.
"""
import os
import pandas as pd
from binance.client import Client


def get_market_data(symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
    """
    Fetch OHLCV data from Binance Futures.
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        timeframe: Candle interval ('1m', '5m', '15m', '1h', '4h', '1d')
        limit: Number of candles to fetch
        
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    try:
        # Get proxy settings if configured
        proxy_url = os.getenv('PROXY_URL')
        request_params = {'proxies': {'https': proxy_url}} if proxy_url else None
        
        # Create client (no auth needed for public data)
        client = Client(tld='com', requests_params=request_params)
        
        # Fetch klines from Futures API
        klines = client.futures_klines(symbol=symbol, interval=timeframe, limit=limit)
        
        if not klines:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
            'taker_buy_quote', 'ignore'
        ])
        
        # Keep only essential columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Convert types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
        
    except Exception as e:
        print(f"[fetcher] Error fetching {symbol}: {e}")
        return pd.DataFrame()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calculate the current ATR value from OHLCV DataFrame.
    
    Args:
        df: DataFrame with high, low, close columns
        period: ATR period (default 14)
        
    Returns:
        Current ATR value as float
    """
    if df.empty or len(df) < period + 1:
        return 0.0
    
    try:
        from servos.indicators import calculate_atr as atr_series
        atr = atr_series(df, period)
        return float(atr.iloc[-1]) if not atr.empty else 0.0
    except Exception as e:
        print(f"[fetcher] ATR calculation error: {e}")
        return 0.0
