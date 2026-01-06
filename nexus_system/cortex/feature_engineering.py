"""
Feature Engineering Module for ML Classifier
Contains only the feature extraction functions needed for inference,
separated from training code.
"""

import pandas as pd
import numpy as np
from ta.trend import ADXIndicator, EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator, WilliamsRIndicator, UltimateOscillator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import MFIIndicator, ChaikinMoneyFlowIndicator, EaseOfMovementIndicator


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ADX using ta library."""
    try:
        adx = ADXIndicator(df['high'], df['low'], df['close'], window=period)
        return adx.adx().fillna(0).clip(0, 100)
    except Exception:
        return pd.Series(0, index=df.index)


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate MFI using ta library."""
    try:
        mfi = MFIIndicator(df['high'], df['low'], df['close'], df['volume'], window=period)
        return mfi.money_flow_index().fillna(50).clip(0, 100)
    except Exception:
        return pd.Series(50, index=df.index)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate ALL technical indicators for inference.
    EXTENDED FEATURE SET for v3.1
    """
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    # === BASIC INDICATORS ===
    # RSI (14)
    try:
        rsi_indicator = RSIIndicator(close, window=14)
        df['rsi'] = rsi_indicator.rsi().fillna(50)
    except Exception:
        df['rsi'] = 50

    # ADX (14)
    try:
        adx_indicator = ADXIndicator(high, low, close, window=14)
        df['adx'] = adx_indicator.adx().fillna(0)
        df['adx_pos'] = adx_indicator.adx_pos().fillna(0)
        df['adx_neg'] = adx_indicator.adx_neg().fillna(0)
    except Exception:
        df['adx'] = 0
        df['adx_pos'] = 0
        df['adx_neg'] = 0

    # MACD
    try:
        macd_indicator = MACD(close)
        df['macd'] = macd_indicator.macd().fillna(0)
        df['macd_signal'] = macd_indicator.macd_signal().fillna(0)
        df['macd_diff'] = macd_indicator.macd_diff().fillna(0)
    except Exception:
        df['macd'] = 0
        df['macd_signal'] = 0
        df['macd_diff'] = 0

    # Bollinger Bands
    try:
        bb_indicator = BollingerBands(close, window=20)
        df['bb_upper'] = bb_indicator.bollinger_hband().fillna(close)
        df['bb_lower'] = bb_indicator.bollinger_lband().fillna(close)
        df['bb_middle'] = bb_indicator.bollinger_mavg().fillna(close)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_position'] = df['bb_position'].fillna(0.5).clip(0, 1)
    except Exception:
        df['bb_upper'] = close
        df['bb_lower'] = close
        df['bb_middle'] = close
        df['bb_width'] = 0
        df['bb_position'] = 0.5

    # ATR (14)
    try:
        atr_indicator = AverageTrueRange(high, low, close, window=14)
        df['atr'] = atr_indicator.average_true_range().fillna(0)
    except Exception:
        df['atr'] = 0

    # === MOMENTUM INDICATORS ===
    # Williams %R (14)
    try:
        williams_indicator = WilliamsRIndicator(high, low, close, lbp=14)
        df['williams_r'] = williams_indicator.williams_r().fillna(-50)
    except Exception:
        df['williams_r'] = -50

    # Ultimate Oscillator
    try:
        uo_indicator = UltimateOscillator(high, low, close)
        df['uo'] = uo_indicator.ultimate_oscillator().fillna(50)
    except Exception:
        df['uo'] = 50

    # === VOLUME INDICATORS ===
    # MFI (14)
    df['mfi'] = calculate_mfi(df, 14)

    # Chaikin Money Flow
    try:
        cmf_indicator = ChaikinMoneyFlowIndicator(high, low, close, volume)
        df['cmf'] = cmf_indicator.chaikin_money_flow().fillna(0)
    except Exception:
        df['cmf'] = 0

    # Ease of Movement
    try:
        eom_indicator = EaseOfMovementIndicator(high, low, volume)
        df['eom'] = eom_indicator.ease_of_movement().fillna(0)
        df['eom_sma'] = eom_indicator.sma_ease_of_movement().fillna(0)
    except Exception:
        df['eom'] = 0
        df['eom_sma'] = 0

    # === TREND INDICATORS ===
    # EMA 9, 21, 50
    try:
        ema9 = EMAIndicator(close, window=9)
        df['ema9'] = ema9.ema_indicator().fillna(close)

        ema21 = EMAIndicator(close, window=21)
        df['ema21'] = ema21.ema_indicator().fillna(close)

        ema50 = EMAIndicator(close, window=50)
        df['ema50'] = ema50.ema_indicator().fillna(close)
    except Exception:
        df['ema9'] = close
        df['ema21'] = close
        df['ema50'] = close

    # SMA 20, 50
    try:
        sma20 = SMAIndicator(close, window=20)
        df['sma20'] = sma20.sma_indicator().fillna(close)

        sma50 = SMAIndicator(close, window=50)
        df['sma50'] = sma50.sma_indicator().fillna(close)
    except Exception:
        df['sma20'] = close
        df['sma50'] = close

    # === PRICE DERIVATIVES ===
    # Returns
    df['returns'] = close.pct_change().fillna(0)
    df['log_returns'] = np.log(close / close.shift(1)).fillna(0)

    # Volatility
    df['volatility'] = df['returns'].rolling(window=20).std().fillna(0)

    # Volume changes
    if 'volume' in df.columns:
        df['volume_change'] = volume.pct_change().fillna(0)
        df['volume_ma'] = volume.rolling(window=20).mean().fillna(volume)
    else:
        df['volume_change'] = 0
        df['volume_ma'] = 0

    # === TIME FEATURES ===
    # Hour of day (assuming UTC timestamps)
    if isinstance(df.index, pd.DatetimeIndex):
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
    else:
        df['hour'] = 12
        df['day_of_week'] = 0
        df['month'] = 1

    # === TREND FEATURES ===
    # Trend strength
    df['ema9_trend'] = np.where(df['close'] > df['ema9'], 1, -1)
    df['ema21_trend'] = np.where(df['close'] > df['ema21'], 1, -1)
    df['sma_trend'] = np.where(df['close'] > df['sma20'], 1, -1)

    # Momentum
    df['momentum'] = (close - close.shift(10)) / close.shift(10)
    df['momentum'] = df['momentum'].fillna(0)

    # Distance from moving averages
    df['dist_ema9'] = (close - df['ema9']) / close
    df['dist_ema21'] = (close - df['ema21']) / close
    df['dist_sma20'] = (close - df['sma20']) / close

    # Fill any remaining NaN values
    df = df.fillna(0)

    return df


def add_all_new_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all new features to the dataframe.
    This is a simplified version for inference only.
    """
    # For inference, we just return the dataframe with basic indicators
    # The full feature engineering is done during training in the cloud trainer
    return add_indicators(df)
