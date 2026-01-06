"""
Feature Engineering Module for ML Classifier
Contains only the feature extraction functions needed for inference,
separated from training code.
"""

import pandas as pd
import numpy as np
from ta.trend import ADXIndicator, EMAIndicator, SMAIndicator, MACD, CCIIndicator, DPOIndicator, KSTIndicator
from ta.momentum import RSIIndicator, WilliamsRIndicator, UltimateOscillator, StochRSIIndicator
from ta.volatility import AverageTrueRange, BollingerBands, UlcerIndex
from ta.volume import MFIIndicator, ChaikinMoneyFlowIndicator, EaseOfMovementIndicator, ForceIndexIndicator, VolumeWeightedAveragePrice
from ta.others import DailyReturnIndicator, CumulativeReturnIndicator
import math


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


def calculate_stoch_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Stochastic RSI."""
    try:
        stoch_rsi = StochRSIIndicator(df['close'], window=period)
        return stoch_rsi.stochrsi_k().fillna(0.5)
    except Exception:
        return pd.Series(0.5, index=df.index)


def calculate_kst(df: pd.DataFrame) -> pd.Series:
    """Calculate Know Sure Thing (KST) oscillator."""
    try:
        kst = KSTIndicator(df['close'])
        return kst.kst().fillna(0)
    except Exception:
        return pd.Series(0, index=df.index)


def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate Commodity Channel Index."""
    try:
        cci = CCIIndicator(df['high'], df['low'], df['close'], window=period)
        return cci.cci().fillna(0)
    except Exception:
        return pd.Series(0, index=df.index)


def calculate_dpo(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate Detrended Price Oscillator."""
    try:
        dpo = DPOIndicator(df['close'], window=period)
        return dpo.dpo().fillna(0)
    except Exception:
        return pd.Series(0, index=df.index)


def calculate_ulcer_index(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Ulcer Index for volatility measurement."""
    try:
        ulcer = UlcerIndex(df['close'], window=period)
        return ulcer.ulcer_index().fillna(0)
    except Exception:
        return pd.Series(0, index=df.index)


def calculate_force_index(df: pd.DataFrame, period: int = 13) -> pd.Series:
    """Calculate Force Index."""
    try:
        force = ForceIndexIndicator(df['close'], df['volume'], window=period)
        return force.force_index().fillna(0)
    except Exception:
        return pd.Series(0, index=df.index)


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate Volume Weighted Average Price."""
    try:
        vwap = VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume'])
        return vwap.volume_weighted_average_price().fillna(df['close'])
    except Exception:
        return df['close']


def calculate_market_regime(df: pd.DataFrame) -> pd.Series:
    """Calculate market regime based on volatility and trend."""
    try:
        # Combine ADX and ATR for regime classification
        adx = calculate_adx(df)
        atr_pct = (calculate_atr(df) / df['close']) * 100

        # Simple regime logic
        regime = pd.Series(0, index=df.index)  # Default: ranging

        # Trending up: ADX > 25 and positive slope
        trending_up = (adx > 25) & (df['close'] > df['close'].shift(20))
        regime[trending_up] = 1

        # Trending down: ADX > 25 and negative slope
        trending_down = (adx > 25) & (df['close'] < df['close'].shift(20))
        regime[trending_down] = -1

        # High volatility ranging
        high_vol = (atr_pct > atr_pct.rolling(50).mean() * 1.2)
        regime[high_vol] = 2

        return regime
    except Exception:
        return pd.Series(0, index=df.index)


def calculate_sentiment_proxy(df: pd.DataFrame) -> pd.Series:
    """Calculate sentiment proxy based on price action patterns."""
    try:
        # Simple sentiment proxy based on buying vs selling pressure
        returns = df['close'].pct_change()

        # Bullish signals
        bullish = (
            (df['close'] > df['open']) &  # Green candle
            (df['close'] > df['close'].shift(1)) &  # Higher close
            (df['volume'] > df['volume'].rolling(10).mean())  # Above average volume
        )

        # Bearish signals
        bearish = (
            (df['close'] < df['open']) &  # Red candle
            (df['close'] < df['close'].shift(1)) &  # Lower close
            (df['volume'] > df['volume'].rolling(10).mean())  # Above average volume
        )

        sentiment = pd.Series(0, index=df.index)
        sentiment[bullish] = 1
        sentiment[bearish] = -1

        # Smooth with rolling average
        return sentiment.rolling(5).mean().fillna(0)
    except Exception:
        return pd.Series(0, index=df.index)


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
    Add all advanced features to the dataframe for enhanced ML performance.
    Includes technical indicators, sentiment analysis, and market regime features.
    """
    df = add_indicators(df)

    # === ADVANCED MOMENTUM INDICATORS ===
    df['stoch_rsi'] = calculate_stoch_rsi(df, 14)
    df['kst'] = calculate_kst(df)
    df['cci'] = calculate_cci(df, 20)
    df['dpo'] = calculate_dpo(df, 20)

    # === ADVANCED VOLATILITY INDICATORS ===
    df['ulcer_index'] = calculate_ulcer_index(df, 14)

    # === ADVANCED VOLUME INDICATORS ===
    df['force_index'] = calculate_force_index(df, 13)
    df['vwap'] = calculate_vwap(df)

    # === MARKET REGIME FEATURES ===
    df['market_regime'] = calculate_market_regime(df)
    df['sentiment_proxy'] = calculate_sentiment_proxy(df)

    # === INTERACTIONS AND DERIVED FEATURES ===
    # RSI + Momentum interactions
    df['rsi_momentum'] = df['rsi'] * df['momentum']
    df['stoch_rsi_kst'] = df['stoch_rsi'] * df['kst']

    # Volatility + Volume interactions
    df['vol_price_change'] = df['volatility'] * df['returns'].abs()
    df['volume_volatility'] = df['volume_change'] * df['volatility']

    # Trend + Momentum combinations
    df['trend_momentum'] = df['ema9_trend'] * df['momentum']
    df['regime_trend'] = df['market_regime'] * df['adx']

    # === SEASONAL AND TIME-BASED FEATURES ===
    # Market hours (crypto markets are 24/7, but there are patterns)
    df['is_asian_session'] = ((df['hour'] >= 0) & (df['hour'] < 8)).astype(int)
    df['is_european_session'] = ((df['hour'] >= 8) & (df['hour'] < 16)).astype(int)
    df['is_us_session'] = ((df['hour'] >= 16) & (df['hour'] < 24)).astype(int)

    # Weekend effect (Friday-Sunday might have different behavior)
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

    # === STATISTICAL FEATURES ===
    # Higher order moments
    df['skewness'] = df['returns'].rolling(20).skew().fillna(0)
    df['kurtosis'] = df['returns'].rolling(20).kurt().fillna(0)

    # Autocorrelation
    df['autocorr_1'] = df['returns'].rolling(20).corr(df['returns'].shift(1)).fillna(0)
    df['autocorr_5'] = df['returns'].rolling(20).corr(df['returns'].shift(5)).fillna(0)

    # === MARKET MICROSTRUCTURE ===
    # Bid-ask spread proxy (using high-low range)
    df['spread_proxy'] = (df['high'] - df['low']) / df['close']
    df['realized_volatility'] = df['returns'].rolling(20).std() * np.sqrt(252)  # Annualized

    # Fill any remaining NaN values
    df = df.fillna(0)

    return df
