"""
Nexus Trading Bot - Technical Indicators Module
Implementation using pandas_ta (OpenBB fork).
"""
import pandas as pd
import pandas_ta as ta
import numpy as np


def calculate_rsi(prices, period: int = 14):
    """Calculate RSI."""
    if isinstance(prices, list):
        prices = pd.Series(prices)
    
    # ta.rsi returns a Series
    rsi = ta.rsi(prices, length=period)
    if rsi is None: return pd.Series([50.0] * len(prices))
    return rsi.fillna(50.0) # Handle NaN at start


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate EMA."""
    ema = ta.ema(series, length=period)
    if ema is None: return pd.Series(series) # Fallback
    return ema


def calculate_hma(series: pd.Series, period: int = 55) -> pd.Series:
    """Calculate HMA."""
    hma = ta.hma(series, length=period)
    if hma is None: return series
    return hma


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR."""
    atr = ta.atr(df['high'], df['low'], df['close'], length=period)
    if atr is None: return pd.Series(0, index=df.index)
    return atr


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> dict:
    """Calculate Bollinger Bands."""
    # ta.bbands returns BBL, BBM, BBU, BBB, BBP
    bb = ta.bbands(series, length=period, std=std_dev)
    if bb is None: 
        return {'middle': series, 'upper': series, 'lower': series}
    
    # Column naming convention in pandas_ta: BBL_length_std, ...
    # We can access by position or wildcard column name logic, 
    # but pandas_ta returns specific names.
    # Safe way: iloc based on standard output order [Lower, Mid, Upper, Bandwidth, Percent]
    # Actually order matches standard? Verify.
    # Usually: BBL, BBM, BBU, ...
    
    # Let's map dynamically
    return {
        'lower': bb.iloc[:, 0],
        'middle': bb.iloc[:, 1],
        'upper': bb.iloc[:, 2]
    }


def calculate_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 1.5) -> dict:
    """Calculate Keltner Channels."""
    # KC returns KCL, KCB, KCU
    kc = ta.kc(df['high'], df['low'], df['close'], length=period, scalar=multiplier)
    if kc is None:
        return {'middle': df['close'], 'upper': df['close'], 'lower': df['close']}
        
    return {
        'lower': kc.iloc[:, 0], # KCL
        'middle': kc.iloc[:, 1], # KCB (Basis/Middle)
        'upper': kc.iloc[:, 2]   # KCU
    }


def calculate_adx(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate ADX."""
    # ta.adx returns ADX, DMP, DMN
    adx_df = ta.adx(df['high'], df['low'], df['close'], length=period)
    if adx_df is None:
        z = pd.Series(0, index=df.index)
        return {'adx': z, 'plus_di': z, 'minus_di': z}
        
    return {
        'adx': adx_df.iloc[:, 0],      # ADX
        'plus_di': adx_df.iloc[:, 1],  # DMP
        'minus_di': adx_df.iloc[:, 2]  # DMN
    }


def calculate_adx_slope(adx_series: pd.Series, lookback: int = 5) -> pd.Series:
    """Calculate slope of ADX (Manual diff)."""
    return adx_series.diff(lookback)


def calculate_stoch_rsi(rsi_series: pd.Series, period: int = 14, k_period: int = 3, d_period: int = 3) -> dict:
    """Calculate Stochastic RSI."""
    # ta.stochrsi returns K, D
    stoch = ta.stochrsi(rsi_series, length=period, rsi_length=period, k=k_period, d=d_period)
    if stoch is None:
        z = pd.Series(0, index=rsi_series.index)
        return {'k': z, 'd': z}
        
    return {
        'k': stoch.iloc[:, 0],
        'd': stoch.iloc[:, 1]
    }


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price."""
    # ta.vwap returns Series
    vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
    if vwap is None: return df['close']
    return vwap


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> dict:
    """Calculates Supertrend."""
    # ta.supertrend returns Trend, Direction, Long, Short
    st = ta.supertrend(df['high'], df['low'], df['close'], length=period, multiplier=multiplier)
    if st is None:
         z = pd.Series(0, index=df.index)
         return {'line': z, 'direction': z}
         
    # output: SUPERT_..., SUPERTd_..., SUPERTl_..., SUPERTs_...
    # column 0 is Trend Line
    # column 1 is Direction (1, -1)
    
    return {
        'line': st.iloc[:, 0],
        'direction': st.iloc[:, 1]
    }
