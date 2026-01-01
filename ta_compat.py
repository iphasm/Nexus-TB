"""
TA Compatibility Layer for Nexus ML Training
Replaces pandas-ta with modern 'ta' library for better compatibility and performance
"""

import ta
import numpy as np
import pandas as pd
from typing import Union, Optional

class TACompat:
    """Compatibility layer that mimics pandas-ta API using 'ta' library"""

    @staticmethod
    def adx(high: Union[pd.Series, np.ndarray],
            low: Union[pd.Series, np.ndarray],
            close: Union[pd.Series, np.ndarray],
            length: int = 14) -> pd.Series:
        """Calculate ADX using ta library"""
        # Convert to pandas Series if needed
        if isinstance(high, np.ndarray):
            high = pd.Series(high)
        if isinstance(low, np.ndarray):
            low = pd.Series(low)
        if isinstance(close, np.ndarray):
            close = pd.Series(close)

        adx_values = ta.trend.adx(high, low, close, window=length)
        return adx_values

    @staticmethod
    def mfi(high: Union[pd.Series, np.ndarray],
            low: Union[pd.Series, np.ndarray],
            close: Union[pd.Series, np.ndarray],
            volume: Union[pd.Series, np.ndarray],
            length: int = 14) -> pd.Series:
        """Calculate MFI using ta library"""
        if isinstance(high, np.ndarray):
            high = pd.Series(high)
        if isinstance(low, np.ndarray):
            low = pd.Series(low)
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        if isinstance(volume, np.ndarray):
            volume = pd.Series(volume)

        mfi_values = ta.volume.money_flow_index(high, low, close, volume, window=length)
        return mfi_values

    @staticmethod
    def ema(close: Union[pd.Series, np.ndarray], length: int = 10) -> pd.Series:
        """Calculate EMA using ta library"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        ema_values = ta.trend.ema_indicator(close, window=length)
        return ema_values

    @staticmethod
    def sma(close: Union[pd.Series, np.ndarray], length: int = 10) -> pd.Series:
        """Calculate SMA using ta library"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        sma_values = ta.trend.sma_indicator(close, window=length)
        return sma_values

    @staticmethod
    def rsi(close: Union[pd.Series, np.ndarray], length: int = 14) -> pd.Series:
        """Calculate RSI using ta library"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        rsi_values = ta.momentum.rsi(close, window=length)
        return rsi_values

    @staticmethod
    def macd(close: Union[pd.Series, np.ndarray],
             fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD using ta library"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        macd_line = ta.trend.macd(close, window_fast=fast, window_slow=slow)
        macd_signal = ta.trend.macd_signal(close, window_fast=fast, window_slow=slow, window_sign=signal)
        macd_hist = ta.trend.macd_diff(close, window_fast=fast, window_slow=slow, window_sign=signal)

        return {
            'MACD': macd_line,
            'MACDh': macd_hist,
            'MACDs': macd_signal
        }

    @staticmethod
    def bbands(close: Union[pd.Series, np.ndarray],
               length: int = 20, std: float = 2.0):
        """Calculate Bollinger Bands using ta library"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        upper = ta.volatility.bollinger_hband(close, window=length, window_dev=std)
        lower = ta.volatility.bollinger_lband(close, window=length, window_dev=std)
        middle = ta.volatility.bollinger_mavg(close, window=length)

        return {
            'BBL': lower,
            'BBM': middle,
            'BBU': upper
        }

    @staticmethod
    def stoch(high: Union[pd.Series, np.ndarray],
              low: Union[pd.Series, np.ndarray],
              close: Union[pd.Series, np.ndarray],
              fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3):
        """Calculate Stochastic Oscillator using ta library"""
        if isinstance(high, np.ndarray):
            high = pd.Series(high)
        if isinstance(low, np.ndarray):
            low = pd.Series(low)
        if isinstance(close, np.ndarray):
            close = pd.Series(close)

        stoch_k = ta.momentum.stoch(high, low, close, window=fastk_period, smooth_window=slowk_period)
        stoch_d = ta.momentum.stoch_signal(high, low, close, window=fastk_period,
                                         smooth_window=slowk_period, smooth_window2=slowd_period)

        return {
            'STOCHk': stoch_k,
            'STOCHd': stoch_d
        }

    @staticmethod
    def cci(high: Union[pd.Series, np.ndarray],
            low: Union[pd.Series, np.ndarray],
            close: Union[pd.Series, np.ndarray],
            length: int = 14) -> pd.Series:
        """Calculate CCI using ta library"""
        if isinstance(high, np.ndarray):
            high = pd.Series(high)
        if isinstance(low, np.ndarray):
            low = pd.Series(low)
        if isinstance(close, np.ndarray):
            close = pd.Series(close)

        cci_values = ta.trend.cci(high, low, close, window=length)
        return cci_values

    @staticmethod
    def willr(high: Union[pd.Series, np.ndarray],
              low: Union[pd.Series, np.ndarray],
              close: Union[pd.Series, np.ndarray],
              length: int = 14) -> pd.Series:
        """Calculate Williams %R using ta library"""
        if isinstance(high, np.ndarray):
            high = pd.Series(high)
        if isinstance(low, np.ndarray):
            low = pd.Series(low)
        if isinstance(close, np.ndarray):
            close = pd.Series(close)

        willr_values = ta.momentum.williams_r(high, low, close, lbp=length)
        return willr_values

    @staticmethod
    def obv(close: Union[pd.Series, np.ndarray],
            volume: Union[pd.Series, np.ndarray]) -> pd.Series:
        """Calculate OBV using ta library"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        if isinstance(volume, np.ndarray):
            volume = pd.Series(volume)

        obv_values = ta.volume.on_balance_volume(close, volume)
        return obv_values

# Create a global instance that mimics pandas-ta API
ta = TACompat()

# Additional utility functions to match pandas-ta patterns
def ema(close, length=10):
    """Direct EMA function for compatibility"""
    return ta.ema(close, length)

def sma(close, length=10):
    """Direct SMA function for compatibility"""
    return ta.sma(close, length)

def rsi(close, length=14):
    """Direct RSI function for compatibility"""
    return ta.rsi(close, length)
