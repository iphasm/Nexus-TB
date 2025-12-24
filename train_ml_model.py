"""
ML Model Training Script v2.0 - Enhanced Version
- Better ADX calculation
- Improved labeling with multiple classes
- Cross-validation
- More robust feature engineering
"""

import asyncio
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from binance.client import Client
import warnings
warnings.filterwarnings('ignore')

import yfinance as yf
from config import get_all_assets, is_crypto

# Configuration
SYMBOLS = get_all_assets()
INTERVAL = '15m'
MODEL_OUTPUT = os.path.join('antigravity_quantum', 'data', 'ml_model.pkl')


def fetch_data(symbol, max_candles=4500):
    """
    Fetches historical data from Binance (Crypto) or YFinance (Stocks).
    For Binance, uses pagination to get more data (up to max_candles).
    """
    print(f"📥 Fetching data for {symbol}...")
    
    if is_crypto(symbol):
        # BINANCE - with pagination for more data
        try:
            client = Client()
            all_klines = []
            
            # Fetch in chunks of 1500 (Binance limit)
            limit_per_request = 1500
            end_time = None
            
            while len(all_klines) < max_candles:
                if end_time:
                    klines = client.futures_klines(
                        symbol=symbol, 
                        interval=INTERVAL, 
                        limit=limit_per_request,
                        endTime=end_time
                    )
                else:
                    klines = client.futures_klines(
                        symbol=symbol, 
                        interval=INTERVAL, 
                        limit=limit_per_request
                    )
                
                if not klines:
                    break
                    
                all_klines = klines + all_klines  # Prepend older data
                end_time = klines[0][0] - 1  # Get data before first candle
                
                if len(klines) < limit_per_request:
                    break  # No more data available
            
            df = pd.DataFrame(all_klines[:max_candles], columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 
                'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            df = df.astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp').reset_index(drop=True)
            return df
        except Exception as e:
            print(f"   ⚠️ Binance error for {symbol}: {e}")
            return None
    else:
        # STOCKS / COMMODITIES (YFinance)
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="59d", interval="15m")
            
            if df.empty:
                print(f"   ⚠️ No data from YF for {symbol}")
                return None
                
            df.reset_index(inplace=True)
            df.rename(columns={
                'Date': 'timestamp', 'Datetime': 'timestamp',
                'Open': 'open', 'High': 'high', 'Low': 'low', 
                'Close': 'close', 'Volume': 'volume'
            }, inplace=True)
            
            if df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                
            return df
        except Exception as e:
            print(f"   ⚠️ YFinance error for {symbol}: {e}")
            return None


def calculate_adx(df, period=14):
    """
    Calculate proper ADX (Average Directional Index)
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    # Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / atr
    
    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = dx.rolling(period).mean()
    
    return adx.fillna(0).clip(0, 100)


def add_indicators(df):
    """
    Calculate all technical indicators for training.
    Must match MLClassifier._extract_features logic.
    """
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    # RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # ATR (14)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    df['atr_pct'] = (df['atr'] / close) * 100
    
    # ADX (Proper calculation)
    df['adx'] = calculate_adx(df, period=14)
    
    # EMAs
    df['ema_20'] = close.ewm(span=20, adjust=False).mean()
    df['ema_50'] = close.ewm(span=50, adjust=False).mean()
    df['ema_200'] = close.ewm(span=200, adjust=False).mean()
    
    # Trend Strength (EMA divergence)
    df['trend_str'] = (df['ema_20'] - df['ema_50']) / close * 100
    
    # Volume Change (5 period vs 20 period average)
    df['vol_ma_5'] = volume.rolling(5).mean()
    df['vol_ma_20'] = volume.rolling(20).mean()
    df['vol_change'] = (df['vol_ma_5'] - df['vol_ma_20']) / (df['vol_ma_20'] + 1e-10)
    
    # Bollinger Bands Width (volatility measure)
    df['bb_middle'] = close.rolling(20).mean()
    df['bb_std'] = close.rolling(20).std()
    df['bb_width'] = (df['bb_std'] * 2) / (df['bb_middle'] + 1e-10) * 100
    
    # Price position in range (0-1)
    df['price_position'] = (close - low.rolling(20).min()) / (high.rolling(20).max() - low.rolling(20).min() + 1e-10)
    
    df.dropna(inplace=True)
    return df


def label_data(df):
    """
    Improved labeling based on FUTURE price action and volatility.
    Looking 12 periods ahead (3 hours on 15m).
    """
    future_close = df['close'].shift(-12)
    future_high = df['high'].rolling(12).max().shift(-12)
    future_low = df['low'].rolling(12).min().shift(-12)
    
    change_pct = (future_close - df['close']) / df['close']
    range_pct = (future_high - future_low) / df['close']
    
    # Initialize
    df['target'] = 'mean_rev'
    
    # 1. TREND: Clear directional movement > 1.2%
    trend_up = change_pct > 0.012
    trend_down = change_pct < -0.012
    df.loc[trend_up | trend_down, 'target'] = 'trend'
    
    # 2. SCALP: High volatility (range > 2%) but low net change
    high_vol = range_pct > 0.02
    low_change = change_pct.abs() < 0.008
    df.loc[high_vol & low_change, 'target'] = 'scalp'
    
    # 3. GRID: Low volatility, price stayed in tight range
    low_vol = range_pct < 0.012
    tight_range = change_pct.abs() < 0.005
    df.loc[low_vol & tight_range, 'target'] = 'grid'
    
    # 4. MEAN_REV: RSI extreme + reversal pattern
    oversold = df['rsi'] < 30
    overbought = df['rsi'] > 70
    reversal_up = change_pct > 0.008
    reversal_down = change_pct < -0.008
    df.loc[oversold & reversal_up, 'target'] = 'mean_rev'
    df.loc[overbought & reversal_down, 'target'] = 'mean_rev'
    
    df.dropna(inplace=True)
    return df


def train():
    all_data = []
    
    print("=" * 60)
    print("🧠 ML MODEL TRAINING v2.0")
    print("=" * 60)
    print(f"📊 Symbols: {len(SYMBOLS)}")
    print(f"⏰ Interval: {INTERVAL}")
    print()
    
    for symbol in SYMBOLS:
        try:
            df = fetch_data(symbol)
            if df is None or df.empty:
                continue
            df = add_indicators(df)
            df = label_data(df)
            if len(df) > 100:  # Only use if enough data
                all_data.append(df)
                print(f"   ✓ {symbol}: {len(df)} samples")
        except Exception as e:
            print(f"   ✗ {symbol}: {e}")
            
    if not all_data:
        print("❌ No data collected.")
        return

    full_df = pd.concat(all_data, ignore_index=True)
    
    # Feature Columns (Must match MLClassifier._extract_features)
    # [RSI, ADX, ATR_PCT, TREND_STR, VOL_CHANGE]
    X_cols = ['rsi', 'adx', 'atr_pct', 'trend_str', 'vol_change']
    X = full_df[X_cols]
    y = full_df['target']
    
    print()
    print("=" * 60)
    print(f"📊 Total samples: {len(X)}")
    print(f"📈 Class distribution:")
    for label, count in y.value_counts().items():
        pct = count / len(y) * 100
        print(f"   • {label}: {count} ({pct:.1f}%)")
    print()
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train with tuned hyperparameters
    print("🔧 Training RandomForest...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced',  # Handle imbalanced classes
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Cross-validation
    print("🔄 Cross-Validation (5-fold)...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"   CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    # Evaluate
    print()
    print("📈 Test Set Evaluation:")
    print("-" * 60)
    preds = model.predict(X_test)
    print(classification_report(y_test, preds))
    
    # Feature Importance
    print("🔑 Feature Importance:")
    for feat, imp in sorted(zip(X_cols, model.feature_importances_), key=lambda x: -x[1]):
        bar = "█" * int(imp * 50)
        print(f"   {feat:12} {imp:.3f} {bar}")
    
    # Save
    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT)
    print()
    print("=" * 60)
    print(f"✅ Model saved to: {MODEL_OUTPUT}")
    print("👉 To enable, restart bot and run: /ml_mode on")
    print("=" * 60)


if __name__ == "__main__":
    train()
