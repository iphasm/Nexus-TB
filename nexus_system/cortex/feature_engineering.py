"""
Technical Indicators Module for ML Inference
MUST match the feature set from ML Cloud Trainer NTB/indicators.py
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
        return df


def add_all_new_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add advanced features for ML inference.
    Currently returns df unchanged - implement advanced features as needed.
    """
    # TODO: Implement advanced feature engineering to match training pipeline
    # For now, return unchanged to prevent import errors
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


def calculate_market_regime_advanced(df: pd.DataFrame) -> pd.Series:
    """Calculate advanced market regime based on multiple factors."""
    try:
        # Combine multiple indicators for more sophisticated regime detection
        adx = calculate_adx(df)
        atr_pct = (calculate_atr(df) / df['close']) * 100
        rsi = df['close'].rolling(14).apply(lambda x: 100 - (100 / (1 + ((x[-1] - x.mean()) / x.std() + 1e-10))))

        regime = pd.Series(0, index=df.index)  # Default: consolidation

        # Strong uptrend: High ADX + RSI > 60 + positive momentum
        strong_up = (adx > 30) & (rsi > 60) & (df['close'] > df['close'].shift(10))
        regime[strong_up] = 1

        # Strong downtrend: High ADX + RSI < 40 + negative momentum
        strong_down = (adx > 30) & (rsi < 40) & (df['close'] < df['close'].shift(10))
        regime[strong_down] = -1

        # High volatility breakout
        high_vol_breakout = (atr_pct > atr_pct.rolling(20).mean() * 1.5) & (adx > 20)
        regime[high_vol_breakout] = 2

        # Low volatility ranging
        low_vol_range = (atr_pct < atr_pct.rolling(20).mean() * 0.8) & (adx < 20)
        regime[low_vol_range] = 3

        return regime
    except Exception:
        return pd.Series(0, index=df.index)


def calculate_sentiment_proxy(df: pd.DataFrame) -> pd.Series:
    """Calculate sentiment proxy based on price action patterns."""
    try:
        # Simple sentiment proxy based on candlestick patterns and volume
        bullish = (
            (df['close'] > df['open']) &  # Green candle
            (df['close'] > df['close'].shift(1)) &  # Higher close
            (df['volume'] > df['volume'].rolling(10).mean())  # Above average volume
        )

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
    MUST match the feature set from ML Cloud Trainer NTB/indicators.py
    """
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    # === BASIC INDICATORS ===
    # RSI
    try:
        rsi_indicator = RSIIndicator(close, window=14)
        df['rsi'] = rsi_indicator.rsi().fillna(50).clip(0, 100)
    except Exception:
        df['rsi'] = 50

    # ATR and ATR%
    try:
        atr_indicator = AverageTrueRange(high, low, close, window=14)
        df['atr'] = atr_indicator.average_true_range().fillna(0)
    except Exception:
        df['atr'] = 0
    df['atr_pct'] = (df['atr'] / close) * 100

    # ADX
    df['adx'] = calculate_adx(df, period=14)

    # EMAs
    try:
        ema9 = EMAIndicator(close, window=9)
        df['ema_9'] = ema9.ema_indicator().fillna(close)

        ema20 = EMAIndicator(close, window=20)
        df['ema_20'] = ema20.ema_indicator().fillna(close)

        ema50 = EMAIndicator(close, window=50)
        df['ema_50'] = ema50.ema_indicator().fillna(close)

        ema200 = EMAIndicator(close, window=200)
        df['ema_200'] = ema200.ema_indicator().fillna(close)
    except Exception:
        df['ema_9'] = close
        df['ema_20'] = close
        df['ema_50'] = close
        df['ema_200'] = close

    # Fill NaN in EMAs
    for col in ['ema_9', 'ema_20', 'ema_50', 'ema_200']:
        df[col] = df[col].bfill().fillna(close)

    # Trend Strength (EMA divergence)
    df['trend_str'] = (df['ema_20'] - df['ema_50']) / close * 100

    # Volume Change
    df['vol_ma_5'] = volume.rolling(5).mean()
    df['vol_ma_20'] = volume.rolling(20).mean()
    df['vol_change'] = (df['vol_ma_5'] - df['vol_ma_20']) / (df['vol_ma_20'] + 1e-10)

    # === v3.0 FEATURES ===

    # MACD
    try:
        macd = MACD(close)
        df['macd'] = macd.macd().fillna(0)
        df['macd_signal'] = macd.macd_signal().fillna(0)
        df['macd_hist'] = macd.macd_diff().fillna(0)
    except Exception:
        df['macd'] = 0
        df['macd_signal'] = 0
        df['macd_hist'] = 0
    df['macd_hist_norm'] = df['macd_hist'] / close * 100

    # Bollinger Bands
    try:
        bb = BollingerBands(close, window=20, window_dev=2)
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_std'] = (df['bb_upper'] - df['bb_middle']) / 2
        df['bb_width'] = (df['bb_std'] * 2) / (df['bb_middle'] + 1e-10) * 100
        df['bb_pct'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
    except Exception:
        df['bb_middle'] = close
        df['bb_upper'] = close
        df['bb_lower'] = close
        df['bb_std'] = 0
        df['bb_width'] = 0
        df['bb_pct'] = 0.5

    # Price Momentum (Rate of Change)
    df['roc_5'] = (close - close.shift(5)) / close.shift(5) * 100
    df['roc_10'] = (close - close.shift(10)) / close.shift(10) * 100

    # OBV (On-Balance Volume) - normalized
    obv = (np.sign(close.diff()) * volume).cumsum()
    df['obv_change'] = obv.diff(5) / (obv.rolling(20).mean() + 1e-10)

    # Price position and body percentage
    df['price_position'] = (close - low) / (high - low + 1e-10)
    df['body_pct'] = abs(close - df['open']) / (high - low + 1e-10) * 100

    # EMA signals
    df['above_ema200'] = (close > df['ema_200']).astype(int)
    df['ema_cross'] = ((close > df['ema_20']) & (df['ema_20'] > df['ema_50'])).astype(int)

    # === v3.1 FEATURES ===

    # EMA slope
    df['ema20_slope'] = df['ema_20'].diff(5).fillna(0)

    # MFI
    df['mfi'] = calculate_mfi(df, 14)

    # Distance to 50-period high/low
    df['dist_50_high'] = (close - high.rolling(50).max()) / close * 100
    df['dist_50_low'] = (close - low.rolling(50).min()) / close * 100

    # Time-based features
    df['hour_of_day'] = df.index.hour if hasattr(df.index, 'hour') else 12
    df['day_of_week'] = df.index.dayofweek if hasattr(df.index, 'dayofweek') else 0

    # === v3.2 ADDITIONAL FEATURES ===

    # Extended ROC
    df['roc_21'] = (close - close.shift(21)) / close.shift(21) * 100
    df['roc_50'] = (close - close.shift(50)) / close.shift(50) * 100

    # Williams %R
    try:
        williams = WilliamsRIndicator(high, low, close, lbp=14)
        df['williams_r'] = williams.williams_r().fillna(-50)
    except Exception:
        df['williams_r'] = -50

    # CCI
    df['cci'] = calculate_cci(df, 20)

    # Ultimate Oscillator
    try:
        uo = UltimateOscillator(high, low, close)
        df['ultimate_osc'] = uo.ultimate_oscillator().fillna(50)
    except Exception:
        df['ultimate_osc'] = 50

    # Volume features
    df['volume_roc_5'] = (volume - volume.shift(5)) / (volume.shift(5) + 1e-10) * 100
    df['volume_roc_21'] = (volume - volume.shift(21)) / (volume.shift(21) + 1e-10) * 100

    # Chaikin Money Flow
    try:
        cmf = ChaikinMoneyFlowIndicator(high, low, close, volume, window=20)
        df['chaikin_mf'] = cmf.chaikin_money_flow().fillna(0)
    except Exception:
        df['chaikin_mf'] = 0

    # Force Index
    df['force_index'] = calculate_force_index(df, 13)

    # Ease of Movement
    try:
        eom = EaseOfMovementIndicator(high, low, volume)
        df['ease_movement'] = eom.ease_of_movement().fillna(0)
    except Exception:
        df['ease_movement'] = 0

    # Distance to SMAs
    df['dist_sma20'] = (close - close.rolling(20).mean()) / close * 100
    df['dist_sma50'] = (close - close.rolling(50).mean()) / close * 100

    # Pivot points and Fibonacci
    pivot = (high + low + close) / 3
    df['pivot_dist'] = (close - pivot) / close * 100

    recent_high = high.rolling(20).max()
    recent_low = low.rolling(20).min()
    fib_382 = recent_low + (recent_high - recent_low) * 0.382
    df['fib_dist'] = (close - fib_382) / close * 100

    # Volatility by session
    df['morning_volatility'] = df['atr_pct'].rolling(8).mean()  # ~2 hours
    df['afternoon_volatility'] = df['atr_pct'].rolling(16).mean()  # ~4 hours

    # Gap detection
    df['gap_up'] = ((df['open'] - close.shift(1)) / close.shift(1) * 100).clip(lower=0)
    df['gap_down'] = ((df['open'] - close.shift(1)) / close.shift(1) * 100).clip(upper=0).abs()

    # Range change
    df['range_change'] = ((high - low) - (high - low).shift(1)) / (high - low).shift(1) * 100

    # Elder Ray (Bull/Bear Power)
    df['bull_power'] = high - df['ema_20']
    df['bear_power'] = low - df['ema_20']

    # Momentum divergence
    df['momentum_div'] = df['rsi'].diff(5).fillna(0)

    # Volume Price Trend
    df['vpt'] = (close.pct_change() * volume).cumsum()

    # Intraday momentum
    df['intraday_momentum'] = (close - df['open']) / df['open'] * 100

    # === v3.3 FEATURES ===

    # Market regime
    df['market_regime'] = calculate_market_regime(df)

    # === v3.4 ADVANCED FEATURES ===

    # Stochastic RSI
    df['stoch_rsi'] = calculate_stoch_rsi(df, 14)

    # KST Oscillator
    df['kst'] = calculate_kst(df)

    # Detrended Price Oscillator
    df['dpo'] = calculate_dpo(df, 20)

    # Ulcer Index
    df['ulcer_index'] = calculate_ulcer_index(df, 14)

    # VWAP
    df['vwap'] = calculate_vwap(df)

    # Advanced market regime
    df['market_regime_advanced'] = calculate_market_regime_advanced(df)

    # Sentiment proxy
    df['sentiment_proxy'] = calculate_sentiment_proxy(df)

    # Feature interactions
    df['rsi_stoch_rsi'] = df['rsi'] * df['stoch_rsi']
    df['cci_kst'] = df['cci'] * df['kst']
    df['vol_price_change'] = df['atr_pct'] * df['roc_5'].abs()
    df['regime_volatility'] = df['market_regime'] * df['atr_pct']

    # Statistical features
    df['returns_skew'] = close.pct_change().rolling(20).skew().fillna(0)
    df['returns_kurtosis'] = close.pct_change().rolling(20).kurt().fillna(0)

    # Cyclical time features
    df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

    # Fill any remaining NaN values
    df = df.fillna(0)

    return df
