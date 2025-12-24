"""
ML Model Training Script v3.0 - Enhanced with Trade Simulation
- Trade-based labeling (simulates actual SL/TP outcomes)
- Extended feature set (MACD, BB%, Momentum, OBV, etc.)
- Proper ADX calculation
- Cross-validation with stratified splits
"""

import asyncio
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
from binance.client import Client
import warnings
warnings.filterwarnings('ignore')

import yfinance as yf
from config import get_all_assets, is_crypto

# Configuration
SYMBOLS = get_all_assets()
INTERVAL = '15m'
MODEL_OUTPUT = os.path.join('antigravity_quantum', 'data', 'ml_model.pkl')

# Strategy SL/TP configurations (matching real trading logic)
STRATEGY_PARAMS = {
    'trend': {'sl_pct': 0.02, 'tp_pct': 0.04, 'min_adx': 25},
    'scalp': {'sl_pct': 0.008, 'tp_pct': 0.012, 'min_atr_pct': 1.5},
    'grid': {'sl_pct': 0.015, 'tp_pct': 0.015, 'max_atr_pct': 0.8},
    'mean_rev': {'sl_pct': 0.018, 'tp_pct': 0.025, 'rsi_low': 30, 'rsi_high': 70},
}


def fetch_data(symbol, max_candles=4500):
    """Fetches historical data from Binance (Crypto) or YFinance (Stocks)."""
    print(f"📥 Fetching data for {symbol}...")
    
    if is_crypto(symbol):
        try:
            client = Client()
            all_klines = []
            limit_per_request = 1500
            end_time = None
            
            while len(all_klines) < max_candles:
                if end_time:
                    klines = client.futures_klines(
                        symbol=symbol, interval=INTERVAL, 
                        limit=limit_per_request, endTime=end_time
                    )
                else:
                    klines = client.futures_klines(
                        symbol=symbol, interval=INTERVAL, limit=limit_per_request
                    )
                
                if not klines:
                    break
                all_klines = klines + all_klines
                end_time = klines[0][0] - 1
                if len(klines) < limit_per_request:
                    break
            
            df = pd.DataFrame(all_klines[:max_candles], columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 
                'close_time', 'quote_asset_volume', 'trades', 
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            df = df.astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp').reset_index(drop=True)
            return df
        except Exception as e:
            print(f"   ⚠️ Binance error for {symbol}: {e}")
            return None
    else:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="59d", interval="15m")
            if df.empty:
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
    """Calculate proper ADX (Average Directional Index)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / atr
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = dx.rolling(period).mean()
    
    return adx.fillna(0).clip(0, 100)


def add_indicators(df):
    """
    Calculate ALL technical indicators for training.
    EXTENDED FEATURE SET for v3.0
    """
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    # === BASIC INDICATORS ===
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
    df['ema_9'] = close.ewm(span=9, adjust=False).mean()
    df['ema_20'] = close.ewm(span=20, adjust=False).mean()
    df['ema_50'] = close.ewm(span=50, adjust=False).mean()
    df['ema_200'] = close.ewm(span=200, adjust=False).mean()
    
    # Trend Strength (EMA divergence)
    df['trend_str'] = (df['ema_20'] - df['ema_50']) / close * 100
    
    # Volume Change
    df['vol_ma_5'] = volume.rolling(5).mean()
    df['vol_ma_20'] = volume.rolling(20).mean()
    df['vol_change'] = (df['vol_ma_5'] - df['vol_ma_20']) / (df['vol_ma_20'] + 1e-10)
    
    # === NEW FEATURES FOR v3.0 ===
    
    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    df['macd_hist_norm'] = df['macd_hist'] / close * 100  # Normalized
    
    # Bollinger Bands
    df['bb_middle'] = close.rolling(20).mean()
    df['bb_std'] = close.rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
    df['bb_width'] = (df['bb_std'] * 2) / (df['bb_middle'] + 1e-10) * 100
    # Bollinger %B (position within bands: 0=lower, 1=upper)
    df['bb_pct'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
    
    # Price Momentum (Rate of Change)
    df['roc_5'] = (close - close.shift(5)) / close.shift(5) * 100
    df['roc_10'] = (close - close.shift(10)) / close.shift(10) * 100
    
    # OBV (On-Balance Volume) - normalized
    obv = (np.sign(close.diff()) * volume).cumsum()
    df['obv_change'] = obv.diff(5) / (obv.rolling(20).mean() + 1e-10)
    
    # Price position in range (0-1)
    df['price_position'] = (close - low.rolling(20).min()) / (
        high.rolling(20).max() - low.rolling(20).min() + 1e-10
    )
    
    # Candle patterns (simple)
    df['body_pct'] = abs(close - df['open']) / (high - low + 1e-10)
    df['upper_wick'] = (high - pd.concat([close, df['open']], axis=1).max(axis=1)) / (high - low + 1e-10)
    df['lower_wick'] = (pd.concat([close, df['open']], axis=1).min(axis=1) - low) / (high - low + 1e-10)
    
    # Trend direction binary
    df['above_ema200'] = (close > df['ema_200']).astype(int)
    df['ema_cross'] = (df['ema_9'] > df['ema_20']).astype(int)
    
    df.dropna(inplace=True)
    return df


def simulate_trade(df, idx, strategy, lookforward=24):
    """
    Simulate a trade starting at index 'idx' using strategy parameters.
    Returns True if TP was hit before SL (profitable), False otherwise.
    
    lookforward: number of candles to simulate (24 = 6 hours on 15m)
    """
    params = STRATEGY_PARAMS.get(strategy, STRATEGY_PARAMS['mean_rev'])
    entry_price = df.iloc[idx]['close']
    sl_pct = params['sl_pct']
    tp_pct = params['tp_pct']
    
    # Determine direction based on indicators
    rsi = df.iloc[idx]['rsi']
    trend = df.iloc[idx]['trend_str']
    
    # Simple direction logic
    if strategy == 'trend':
        is_long = trend > 0
    elif strategy == 'mean_rev':
        is_long = rsi < 50  # Buy oversold, sell overbought
    else:
        is_long = rsi < 50  # Default
    
    # Set SL/TP prices
    if is_long:
        sl_price = entry_price * (1 - sl_pct)
        tp_price = entry_price * (1 + tp_pct)
    else:
        sl_price = entry_price * (1 + sl_pct)
        tp_price = entry_price * (1 - tp_pct)
    
    # Simulate forward
    max_idx = min(idx + lookforward, len(df) - 1)
    
    for i in range(idx + 1, max_idx + 1):
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']
        
        if is_long:
            if low <= sl_price:
                return False  # SL hit first
            if high >= tp_price:
                return True   # TP hit first
        else:
            if high >= sl_price:
                return False  # SL hit first
            if low <= tp_price:
                return True   # TP hit first
    
    # Neither hit - check if in profit at end
    final_price = df.iloc[max_idx]['close']
    if is_long:
        return final_price > entry_price
    else:
        return final_price < entry_price


def label_data_v3(df):
    """
    IMPROVED LABELING v3.0 - Trade Simulation Based
    
    For each row, simulates what would happen if each strategy was used.
    Labels with the strategy that would have been most profitable.
    """
    n = len(df)
    labels = ['mean_rev'] * n  # Default
    
    # Pre-compute conditions for strategy eligibility
    adx = df['adx'].values
    atr_pct = df['atr_pct'].values
    rsi = df['rsi'].values
    
    for idx in range(n - 25):  # Need 24 candles forward
        row = df.iloc[idx]
        
        # Determine which strategies are eligible based on current conditions
        eligible = []
        
        # TREND: ADX > 25 indicates trending market
        if adx[idx] > 25:
            eligible.append('trend')
        
        # SCALP: High volatility (ATR% > 1.5%)
        if atr_pct[idx] > 1.5:
            eligible.append('scalp')
        
        # GRID: Low volatility (ATR% < 0.8%)
        if atr_pct[idx] < 0.8:
            eligible.append('grid')
        
        # MEAN_REV: RSI at extremes
        if rsi[idx] < 35 or rsi[idx] > 65:
            eligible.append('mean_rev')
        
        # If no strategy is eligible, default to mean_rev
        if not eligible:
            eligible = ['mean_rev']
        
        # Simulate each eligible strategy and pick the best
        best_strategy = 'mean_rev'
        for strat in eligible:
            if simulate_trade(df, idx, strat):
                best_strategy = strat
                break  # Take first profitable strategy
        
        labels[idx] = best_strategy
    
    df['target'] = labels
    
    # Remove last 25 rows (no future data)
    df = df.iloc[:-25].copy()
    df.dropna(inplace=True)
    return df


def train():
    all_data = []
    
    print("=" * 60)
    print("🧠 ML MODEL TRAINING v3.0 - Trade Simulation")
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
            df = label_data_v3(df)
            if len(df) > 100:
                all_data.append(df)
                print(f"   ✓ {symbol}: {len(df)} samples")
        except Exception as e:
            print(f"   ✗ {symbol}: {e}")
            
    if not all_data:
        print("❌ No data collected.")
        return

    full_df = pd.concat(all_data, ignore_index=True)
    
    # EXTENDED FEATURE SET for v3.0
    X_cols = [
        # Core (original)
        'rsi', 'adx', 'atr_pct', 'trend_str', 'vol_change',
        # New features
        'macd_hist_norm', 'bb_pct', 'bb_width',
        'roc_5', 'roc_10', 'obv_change',
        'price_position', 'body_pct',
        'above_ema200', 'ema_cross'
    ]
    
    X = full_df[X_cols]
    y = full_df['target']
    
    print()
    print("=" * 60)
    print(f"📊 Total samples: {len(X)}")
    print(f"📈 Features: {len(X_cols)}")
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
    print("🔧 Training RandomForest (15 features)...")
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=18,
        min_samples_split=8,
        min_samples_leaf=4,
        class_weight='balanced',
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
    
    # Feature Importance (top 10)
    print("🔑 Top 10 Feature Importance:")
    importance_pairs = sorted(zip(X_cols, model.feature_importances_), key=lambda x: -x[1])
    for feat, imp in importance_pairs[:10]:
        bar = "█" * int(imp * 50)
        print(f"   {feat:18} {imp:.3f} {bar}")
    
    # Save
    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT)
    print()
    print("=" * 60)
    print(f"✅ Model saved to: {MODEL_OUTPUT}")
    print("👉 To enable, restart bot or run: /ml_mode on")
    print("=" * 60)


if __name__ == "__main__":
    train()
