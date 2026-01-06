"""
Feature engineering module for ML Cloud Trainer
Separates feature calculation logic from training code
"""

import pandas as pd
import numpy as np
from ta.trend import ADXIndicator, EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator, WilliamsRIndicator, UltimateOscillator
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import MFIIndicator, ChaikinMoneyFlowIndicator, EaseOfMovementIndicator
from typing import List, Set
from config.settings import get_config
from .logging_config import get_logger

logger = get_logger('feature_engineering')
config = get_config()

# Feature columns that will be generated
FEATURE_COLUMNS = [
    # Price-based features
    'close', 'returns', 'log_returns',

    # Trend indicators
    'sma_20', 'sma_50', 'ema_12', 'ema_26',
    'macd', 'macd_signal', 'macd_hist',

    # Momentum indicators
    'rsi', 'williams_r', 'ultimate_oscillator',

    # Volatility indicators
    'atr', 'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
    'bb_position',

    # Volume indicators
    'mfi', 'cmf', 'eom',

    # Trend strength
    'adx', 'plus_di', 'minus_di',

    # Price action
    'high_low_ratio', 'close_open_ratio',

    # Statistical features
    'volatility_20', 'volume_sma_20',

    # Lagged features
    'close_lag_1', 'close_lag_2', 'close_lag_3',
    'returns_lag_1', 'returns_lag_2', 'returns_lag_3',
    'rsi_lag_1', 'rsi_lag_2', 'rsi_lag_3'
]


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate ALL technical indicators for training.
    EXTENDED FEATURE SET for enhanced ML model performance.
    """
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    open_price = df['open']

    # === BASIC PRICE FEATURES ===
    try:
        # Returns and log returns
        df['returns'] = close.pct_change()
        df['log_returns'] = np.log(close / close.shift(1))

        # Price ratios
        df['high_low_ratio'] = high / low
        df['close_open_ratio'] = close / open_price

        logger.debug("Basic price features calculated")
    except Exception as e:
        logger.error(f"Error calculating basic price features: {e}")
        df['returns'] = 0
        df['log_returns'] = 0
        df['high_low_ratio'] = 1
        df['close_open_ratio'] = 1

    # === TREND INDICATORS ===
    try:
        # Moving averages
        df['sma_20'] = close.rolling(window=20).mean()
        df['sma_50'] = close.rolling(window=50).mean()

        # Exponential moving averages
        ema_12 = EMAIndicator(close, window=12)
        df['ema_12'] = ema_12.ema_indicator()

        ema_26 = EMAIndicator(close, window=26)
        df['ema_26'] = ema_26.ema_indicator()

        # MACD
        macd_indicator = MACD(close, window_slow=26, window_fast=12, window_sign=9)
        df['macd'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()
        df['macd_hist'] = macd_indicator.macd_diff()

        logger.debug("Trend indicators calculated")
    except Exception as e:
        logger.error(f"Error calculating trend indicators: {e}")
        # Set defaults
        for col in ['sma_20', 'sma_50', 'ema_12', 'ema_26', 'macd', 'macd_signal', 'macd_hist']:
            df[col] = close

    # === MOMENTUM INDICATORS ===
    try:
        # RSI
        rsi_indicator = RSIIndicator(close, window=14)
        df['rsi'] = rsi_indicator.rsi()

        # Williams %R
        williams_indicator = WilliamsRIndicator(high, low, close, window=14)
        df['williams_r'] = williams_indicator.williams_r()

        # Ultimate Oscillator
        ultimate_indicator = UltimateOscillator(high, low, close, window1=7, window2=14, window3=28)
        df['ultimate_oscillator'] = ultimate_indicator.ultimate_oscillator()

        logger.debug("Momentum indicators calculated")
    except Exception as e:
        logger.error(f"Error calculating momentum indicators: {e}")
        df['rsi'] = 50
        df['williams_r'] = -50
        df['ultimate_oscillator'] = 50

    # === VOLATILITY INDICATORS ===
    try:
        # ATR
        atr_indicator = AverageTrueRange(high, low, close, window=14)
        df['atr'] = atr_indicator.average_true_range()

        # Bollinger Bands
        bb_indicator = BollingerBands(close, window=20, window_dev=2)
        df['bb_upper'] = bb_indicator.bollinger_hband()
        df['bb_middle'] = bb_indicator.bollinger_mavg()
        df['bb_lower'] = bb_indicator.bollinger_lband()
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Rolling volatility
        df['volatility_20'] = close.rolling(window=20).std()

        logger.debug("Volatility indicators calculated")
    except Exception as e:
        logger.error(f"Error calculating volatility indicators: {e}")
        df['atr'] = close * 0.02  # Default 2% ATR
        df['bb_upper'] = close * 1.02
        df['bb_middle'] = close
        df['bb_lower'] = close * 0.98
        df['bb_width'] = 0.04
        df['bb_position'] = 0.5
        df['volatility_20'] = close * 0.02

    # === VOLUME INDICATORS ===
    try:
        # MFI (Money Flow Index)
        mfi_indicator = MFIIndicator(high, low, close, volume, window=14)
        df['mfi'] = mfi_indicator.money_flow_index()

        # Chaikin Money Flow
        cmf_indicator = ChaikinMoneyFlowIndicator(high, low, close, volume, window=20)
        df['cmf'] = cmf_indicator.chaikin_money_flow()

        # Ease of Movement
        eom_indicator = EaseOfMovementIndicator(high, low, volume, window=14)
        df['eom'] = eom_indicator.ease_of_movement()

        # Volume SMA
        df['volume_sma_20'] = volume.rolling(window=20).mean()

        logger.debug("Volume indicators calculated")
    except Exception as e:
        logger.error(f"Error calculating volume indicators: {e}")
        df['mfi'] = 50
        df['cmf'] = 0
        df['eom'] = 0
        df['volume_sma_20'] = volume

    # === TREND STRENGTH INDICATORS ===
    try:
        # ADX
        adx_indicator = ADXIndicator(high, low, close, window=14)
        df['adx'] = adx_indicator.adx()
        df['plus_di'] = adx_indicator.adx_pos()
        df['minus_di'] = adx_indicator.adx_neg()

        logger.debug("Trend strength indicators calculated")
    except Exception as e:
        logger.error(f"Error calculating trend strength indicators: {e}")
        df['adx'] = 25
        df['plus_di'] = 20
        df['minus_di'] = 20

    # === LAGGED FEATURES ===
    try:
        # Price lags
        df['close_lag_1'] = close.shift(1)
        df['close_lag_2'] = close.shift(2)
        df['close_lag_3'] = close.shift(3)

        # Returns lags
        df['returns_lag_1'] = df['returns'].shift(1)
        df['returns_lag_2'] = df['returns'].shift(2)
        df['returns_lag_3'] = df['returns'].shift(3)

        # RSI lags
        df['rsi_lag_1'] = df['rsi'].shift(1)
        df['rsi_lag_2'] = df['rsi'].shift(2)
        df['rsi_lag_3'] = df['rsi'].shift(3)

        logger.debug("Lagged features calculated")
    except Exception as e:
        logger.error(f"Error calculating lagged features: {e}")
        # Set defaults for lagged features
        for lag in ['1', '2', '3']:
            df[f'close_lag_{lag}'] = close
            df[f'returns_lag_{lag}'] = 0
            df[f'rsi_lag_{lag}'] = 50

    # Fill NaN values with forward/backward fill, then 0
    df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

    # Ensure all expected columns exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            logger.warning(f"Missing expected column: {col}")
            if col in ['close', 'returns', 'log_returns', 'high_low_ratio', 'close_open_ratio']:
                df[col] = 0 if col != 'close' else close
            else:
                df[col] = 0

    logger.info(f"Feature engineering completed, shape: {df.shape}")
    return df


def validate_features(df: pd.DataFrame) -> bool:
    """Validate that all required features are present and valid"""
    missing_features = []
    invalid_features = []

    for feature in FEATURE_COLUMNS:
        if feature not in df.columns:
            missing_features.append(feature)
        elif df[feature].isnull().all():
            invalid_features.append(feature)

    if missing_features:
        logger.error(f"Missing features: {missing_features}")
        return False

    if invalid_features:
        logger.error(f"All-NaN features: {invalid_features}")
        return False

    logger.info(f"Feature validation passed: {len(FEATURE_COLUMNS)} features present")
    return True


def get_feature_importance_ranking() -> List[str]:
    """Get features ranked by typical importance for model training"""
    # This is a heuristic ranking based on common ML practice
    # Could be made dynamic based on actual feature importance from trained models
    return [
        # Most important features
        'rsi', 'macd', 'macd_signal', 'bb_position', 'adx',
        'returns', 'log_returns', 'close_lag_1', 'rsi_lag_1',

        # High importance
        'atr', 'volatility_20', 'mfi', 'sma_20', 'ema_12',
        'returns_lag_1', 'close_lag_2', 'rsi_lag_2',

        # Medium importance
        'bb_width', 'cmf', 'eom', 'plus_di', 'minus_di',
        'williams_r', 'ultimate_oscillator', 'high_low_ratio',
        'close_open_ratio', 'volume_sma_20',

        # Lower importance (but still useful)
        'sma_50', 'ema_26', 'macd_hist', 'returns_lag_2',
        'returns_lag_3', 'rsi_lag_3', 'close_lag_3'
    ]


def select_top_features(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    """Select top N most important features"""
    ranking = get_feature_importance_ranking()
    selected_features = ranking[:top_n]

    available_features = [f for f in selected_features if f in df.columns]

    if len(available_features) < top_n:
        logger.warning(f"Only {len(available_features)} of {top_n} requested features available")

    logger.info(f"Selected {len(available_features)} features for training")
    return df[available_features].copy()
