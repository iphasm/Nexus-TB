"""
TA-Lib Compatibility Layer for Nexus ML Training
Replaces pandas-ta with direct TA-Lib usage for better compatibility and performance
"""

import talib
import numpy as np
import pandas as pd
from typing import Union, Optional

class TACompat:
    """Compatibility layer that mimics pandas-ta API using TA-Lib directly"""

    @staticmethod
    def adx(high: Union[pd.Series, np.ndarray],
            low: Union[pd.Series, np.ndarray],
            close: Union[pd.Series, np.ndarray],
            length: int = 14) -> pd.Series:
        """Calculate ADX using TA-Lib"""
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)

        adx_values = talib.ADX(high, low, close, timeperiod=length)
        return pd.Series(adx_values, index=range(len(adx_values)))

    @staticmethod
    def mfi(high: Union[pd.Series, np.ndarray],
            low: Union[pd.Series, np.ndarray],
            close: Union[pd.Series, np.ndarray],
            volume: Union[pd.Series, np.ndarray],
            length: int = 14) -> pd.Series:
        """Calculate MFI using TA-Lib"""
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)
        volume = np.array(volume)

        mfi_values = talib.MFI(high, low, close, volume, timeperiod=length)
        return pd.Series(mfi_values, index=range(len(mfi_values)))

    @staticmethod
    def ema(close: Union[pd.Series, np.ndarray], length: int = 10) -> pd.Series:
        """Calculate EMA using TA-Lib"""
        close = np.array(close)
        ema_values = talib.EMA(close, timeperiod=length)
        return pd.Series(ema_values, index=range(len(ema_values)))

    @staticmethod
    def sma(close: Union[pd.Series, np.ndarray], length: int = 10) -> pd.Series:
        """Calculate SMA using TA-Lib"""
        close = np.array(close)
        sma_values = talib.SMA(close, timeperiod=length)
        return pd.Series(sma_values, index=range(len(sma_values)))

    @staticmethod
    def rsi(close: Union[pd.Series, np.ndarray], length: int = 14) -> pd.Series:
        """Calculate RSI using TA-Lib"""
        close = np.array(close)
        rsi_values = talib.RSI(close, timeperiod=length)
        return pd.Series(rsi_values, index=range(len(rsi_values)))

    @staticmethod
    def macd(close: Union[pd.Series, np.ndarray],
             fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD using TA-Lib"""
        close = np.array(close)
        macd_line, macd_signal, macd_hist = talib.MACD(close,
                                                      fastperiod=fast,
                                                      slowperiod=slow,
                                                      signalperiod=signal)
        return {
            'MACD': pd.Series(macd_line, index=range(len(macd_line))),
            'MACDh': pd.Series(macd_hist, index=range(len(macd_hist))),
            'MACDs': pd.Series(macd_signal, index=range(len(macd_signal)))
        }

    @staticmethod
    def bbands(close: Union[pd.Series, np.ndarray],
               length: int = 20, std: float = 2.0):
        """Calculate Bollinger Bands using TA-Lib"""
        close = np.array(close)
        upper, middle, lower = talib.BBANDS(close,
                                           timeperiod=length,
                                           nbdevup=std,
                                           nbdevdn=std,
                                           matype=talib.MA_Type.SMA)
        return {
            'BBL': pd.Series(lower, index=range(len(lower))),
            'BBM': pd.Series(middle, index=range(len(middle))),
            'BBU': pd.Series(upper, index=range(len(upper)))
        }

    @staticmethod
    def stoch(high: Union[pd.Series, np.ndarray],
              low: Union[pd.Series, np.ndarray],
              close: Union[pd.Series, np.ndarray],
              fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3):
        """Calculate Stochastic Oscillator using TA-Lib"""
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)

        slowk, slowd = talib.STOCH(high, low, close,
                                  fastk_period=fastk_period,
                                  slowk_period=slowk_period,
                                  slowd_period=slowd_period)
        return {
            'STOCHk': pd.Series(slowk, index=range(len(slowk))),
            'STOCHd': pd.Series(slowd, index=range(len(slowd)))
        }

    @staticmethod
    def cci(high: Union[pd.Series, np.ndarray],
            low: Union[pd.Series, np.ndarray],
            close: Union[pd.Series, np.ndarray],
            length: int = 14) -> pd.Series:
        """Calculate CCI using TA-Lib"""
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)

        cci_values = talib.CCI(high, low, close, timeperiod=length)
        return pd.Series(cci_values, index=range(len(cci_values)))

    @staticmethod
    def willr(high: Union[pd.Series, np.ndarray],
              low: Union[pd.Series, np.ndarray],
              close: Union[pd.Series, np.ndarray],
              length: int = 14) -> pd.Series:
        """Calculate Williams %R using TA-Lib"""
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)

        willr_values = talib.WILLR(high, low, close, timeperiod=length)
        return pd.Series(willr_values, index=range(len(willr_values)))

    @staticmethod
    def obv(close: Union[pd.Series, np.ndarray],
            volume: Union[pd.Series, np.ndarray]) -> pd.Series:
        """Calculate OBV using TA-Lib"""
        close = np.array(close)
        volume = np.array(volume)

        obv_values = talib.OBV(close, volume)
        return pd.Series(obv_values, index=range(len(obv_values)))

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
