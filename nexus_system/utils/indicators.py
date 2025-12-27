"""
Nexus System - Technical Indicators (Legacy Wrapper).
This module wraps servos.indicators which uses pandas-ta.
Kept for backward compatibility with existing code.
"""
import pandas as pd
import numpy as np
from servos.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_adx,
    calculate_vwap,
    calculate_supertrend,
    calculate_stoch_rsi,
    calculate_psar,
    calculate_ichimoku,
    calculate_choppiness
)
import pandas_ta as ta


class TechnicalIndicators:
    """
    Standardized Technical Indicators Library.
    Now using pandas-ta backend via servos.indicators.
    """

    @staticmethod
    def ema(series: pd.Series, span: int) -> pd.Series:
        """Exponential Moving Average"""
        return calculate_ema(series, period=span)

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        return calculate_rsi(series, period=period)

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2):
        """Bollinger Bands (Upper, Lower, Middle, Width, Pct)"""
        bb = calculate_bollinger_bands(series, period=period, std_dev=float(std_dev))
        upper = bb['upper']
        lower = bb['lower']
        middle = bb['middle']
        
        # Calculate Width and %B
        width = (upper - lower) / (middle + 1e-10) * 100
        pct = (series - lower) / (upper - lower + 1e-10)
        
        return upper, lower, middle, width, pct

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        return calculate_atr(df, period=period)

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """ADX (Full calculation via pandas-ta)"""
        adx_data = calculate_adx(df, period=period)
        return adx_data['adx']

    @staticmethod
    def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Money Flow Index"""
        result = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=period)
        if result is None:
            return pd.Series(50, index=df.index)
        return result.fillna(50)

    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD, Signal, Hist"""
        macd_df = ta.macd(series, fast=fast, slow=slow, signal=signal)
        if macd_df is None:
            z = pd.Series(0, index=series.index)
            return z, z, z
        return macd_df.iloc[:, 0], macd_df.iloc[:, 2], macd_df.iloc[:, 1]

    @staticmethod
    def obv_change(df: pd.DataFrame) -> pd.Series:
        """On-Balance Volume"""
        obv = ta.obv(df['close'], df['volume'])
        if obv is None:
            return pd.Series(0, index=df.index)
        return obv.diff()

    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        """Volume Weighted Average Price"""
        return calculate_vwap(df)

    @staticmethod
    def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
        """Supertrend Indicator"""
        st = calculate_supertrend(df, period=period, multiplier=multiplier)
        return st['line'], st['direction']

    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3):
        """Stochastic Oscillator"""
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)
        if stoch is None:
            z = pd.Series(0, index=df.index)
            return z, z
        return stoch.iloc[:, 0], stoch.iloc[:, 1]

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Applies standard suite of indicators to the DataFrame."""
        if df.empty:
            return df
        
        closes = df['close']
        
        # Trend
        df['ema_20'] = TechnicalIndicators.ema(closes, 20)
        df['ema_50'] = TechnicalIndicators.ema(closes, 50)
        df['ema_200'] = TechnicalIndicators.ema(closes, 200)
        
        # Momentum
        df['rsi'] = TechnicalIndicators.rsi(closes)
        
        # Volatility
        df['upper_bb'], df['lower_bb'], _, df['bb_width'], df['bb_pct'] = \
            TechnicalIndicators.bollinger_bands(closes)
            
        df['atr'] = TechnicalIndicators.atr(df)
        
        # Strength
        df['adx'] = TechnicalIndicators.adx(df)
        
        # Volume
        if 'volume' in df.columns:
            df['vol_sma'] = df['volume'].rolling(window=20).mean()
            df['obv_change'] = TechnicalIndicators.obv_change(df)
            
        # MACD
        _, _, df['macd_hist'] = TechnicalIndicators.macd(closes)

        # Stochastic
        df['stoch_k'], df['stoch_d'] = TechnicalIndicators.stochastic(df)
        
        # VWAP
        if 'volume' in df.columns:
            df['vwap'] = TechnicalIndicators.vwap(df)
            
        # Supertrend
        df['supertrend'], df['supertrend_dir'] = TechnicalIndicators.supertrend(df)
        
        # Clean up
        df.bfill(inplace=True)
        df.fillna(0, inplace=True)
        
        return df
