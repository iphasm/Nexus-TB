"""
Nexus Trading Bot - Technical Indicators Module
Vectorized calculations using Pandas/NumPy for high performance.
"""
import pandas as pd
import numpy as np


def calculate_rsi(prices, period: int = 14):
    """Calculate RSI from price series or list."""
    if isinstance(prices, list):
        prices = pd.Series(prices)
    
    if len(prices) < period + 1:
        return pd.Series([50.0] * len(prices)) if isinstance(prices, pd.Series) else 50.0
    
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_hma(series: pd.Series, period: int = 55) -> pd.Series:
    """Calculate Hull Moving Average (HMA)."""
    half_period = int(period / 2)
    sqrt_period = int(np.sqrt(period))
    
    wma_half = series.rolling(window=half_period).mean()
    wma_full = series.rolling(window=period).mean()
    
    raw_hma = 2 * wma_half - wma_full
    hma = raw_hma.rolling(window=sqrt_period).mean()
    
    return hma


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    
    return atr


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> dict:
    """Calculate Bollinger Bands."""
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    return {
        'middle': sma,
        'upper': sma + (std * std_dev),
        'lower': sma - (std * std_dev)
    }


def calculate_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 1.5) -> dict:
    """Calculate Keltner Channels."""
    ema = calculate_ema(df['close'], period)
    atr = calculate_atr(df, period)
    
    return {
        'middle': ema,
        'upper': ema + (atr * multiplier),
        'lower': ema - (atr * multiplier)
    }


def calculate_adx(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate ADX (Average Directional Index)."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smooth
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-10)
    minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-10)
    
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    
    return {
        'adx': adx,
        'plus_di': plus_di,
        'minus_di': minus_di
    }


def calculate_adx_slope(adx_series: pd.Series, lookback: int = 5) -> pd.Series:
    """Calculate slope of ADX."""
    return adx_series.diff(lookback)


def calculate_stoch_rsi(rsi_series: pd.Series, period: int = 14, k_period: int = 3, d_period: int = 3) -> dict:
    """Calculate Stochastic RSI."""
    min_rsi = rsi_series.rolling(window=period).min()
    max_rsi = rsi_series.rolling(window=period).max()
    
    stoch_rsi = (rsi_series - min_rsi) / (max_rsi - min_rsi + 1e-10) * 100
    k = stoch_rsi.rolling(window=k_period).mean()
    d = k.rolling(window=d_period).mean()
    
    return {'k': k, 'd': d}


