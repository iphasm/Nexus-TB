#!/usr/bin/env python3
"""
Local ML Model Training Script - Saves model locally instead of to PostgreSQL
Based on the ML Cloud Trainer but adapted for local use
"""

import os
import sys
import time
import argparse
from datetime import datetime

import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import classification_report

# Add the ML Cloud Trainer path to import indicators
sys.path.append('../ML Cloud Trainer NTB')
from indicators import add_indicators, FEATURE_COLUMNS

# Default symbols including SOLUSDT
DEFAULT_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT',
    'DOGEUSDT', 'WIFUSDT', 'AAVEUSDT', 'CRVUSDT'
]

INTERVAL = '15m'

# Strategy SL/TP configurations
STRATEGY_PARAMS = {
    'trend': {'sl_pct': 0.02, 'tp_pct': 0.04, 'min_adx': 25},
    'scalp': {'sl_pct': 0.008, 'tp_pct': 0.012, 'min_atr_pct': 1.5},
    'grid': {'sl_pct': 0.015, 'tp_pct': 0.015, 'max_atr_pct': 0.8},
    'mean_rev': {'sl_pct': 0.018, 'tp_pct': 0.025, 'rsi_low': 30, 'rsi_high': 70},
}

def fetch_crypto_data(symbol: str, max_candles: int = 15000) -> pd.DataFrame:
    """Fetch crypto data from yfinance (fallback method)"""
    try:
        import yfinance as yf

        # Convert symbol to yfinance format
        yf_conversions = {
            'BTCUSDT': 'BTC-USD', 'ETHUSDT': 'ETH-USD', 'BNBUSDT': 'BNB-USD',
            'ADAUSDT': 'ADA-USD', 'SOLUSDT': 'SOL-USD', 'DOTUSDT': 'DOT-USD',
            'DOGEUSDT': 'DOGE-USD', 'AVAXUSDT': 'AVAX-USD', 'LINKUSDT': 'LINK-USD',
            'XRPUSDT': 'XRP-USD', 'AAVEUSDT': 'AAVE-USD', 'CRVUSDT': 'CRV-USD',
            'WIFUSDT': 'WIF-USD'
        }

        yf_symbol = yf_conversions.get(symbol, f"{symbol[:-4]}-USD")

        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period="60d", interval="15m")

        if df.empty:
            print(f"⚠️ No data for {symbol}")
            return None

        # Rename columns to match expected format
        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]

        if 'datetime' in df.columns:
            df = df.rename(columns={'datetime': 'timestamp'})
        elif 'date' in df.columns:
            df = df.rename(columns={'date': 'timestamp'})

        required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required):
            print(f"⚠️ Missing columns for {symbol}")
            return None

        df = df[required].copy()
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Limit to max_candles
        if len(df) > max_candles:
            df = df.tail(max_candles).reset_index(drop=True)

        return df

    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

def simulate_trade(df: pd.DataFrame, idx: int, strategy: str, lookforward: int = 24) -> bool:
    """Simulate trade and return True if profitable"""
    params = STRATEGY_PARAMS.get(strategy, STRATEGY_PARAMS['mean_rev'])
    entry_price = df.iloc[idx]['close']
    sl_pct = params['sl_pct']
    tp_pct = params['tp_pct']

    rsi = df.iloc[idx]['rsi']
    trend = df.iloc[idx]['trend_str']

    if strategy == 'trend':
        is_long = trend > 0
    elif strategy == 'mean_rev':
        is_long = rsi < 50
    else:
        is_long = rsi < 50

    if is_long:
        sl_price = entry_price * (1 - sl_pct)
        tp_price = entry_price * (1 + tp_pct)
    else:
        sl_price = entry_price * (1 + sl_pct)
        tp_price = entry_price * (1 - tp_pct)

    max_idx = min(idx + lookforward, len(df) - 1)

    for i in range(idx + 1, max_idx + 1):
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']

        if is_long:
            if low <= sl_price:
                return False
            if high >= tp_price:
                return True
        else:
            if high >= sl_price:
                return False
            if low <= tp_price:
                return True

    final_price = df.iloc[max_idx]['close']
    return (final_price > entry_price) if is_long else (final_price < entry_price)

def label_data(df: pd.DataFrame) -> pd.DataFrame:
    """Label data with best strategy"""
    n = len(df)
    labels = ['mean_rev'] * n
    confidences = [0.5] * n

    adx = df['adx'].values
    atr_pct = df['atr_pct'].values
    rsi = df['rsi'].values

    strategies = ['trend', 'scalp', 'grid', 'mean_rev']

    for idx in range(n - 25):
        strategy_scores = {}

        for strat in strategies:
            eligible = False
            if strat == 'trend' and adx[idx] > 25:
                eligible = True
            elif strat == 'scalp' and atr_pct[idx] > 1.5:
                eligible = True
            elif strat == 'grid' and atr_pct[idx] < 0.8:
                eligible = True
            elif strat == 'mean_rev' and (rsi[idx] < 35 or rsi[idx] > 65):
                eligible = True

            if not eligible:
                strategy_scores[strat] = 0.0
                continue

            wins = 0
            tests = 0
            for lookforward in [12, 24, 36]:
                if idx + lookforward < n:
                    if simulate_trade(df, idx, strat, lookforward):
                        wins += 1
                    tests += 1

            win_rate = wins / tests if tests > 0 else 0
            strategy_scores[strat] = win_rate

        if strategy_scores:
            best_strategy = max(strategy_scores, key=strategy_scores.get)
            best_score = strategy_scores[best_strategy]

            if best_score > 0:
                labels[idx] = best_strategy
                confidences[idx] = best_score

    df['target'] = labels
    df['label_confidence'] = confidences
    df = df.iloc[:-25].copy()
    df.dropna(inplace=True)

    return df

def main():
    print("=" * 60)
    print("🧠 LOCAL ML TRAINER - NEXUS CORTEX")
    print("=" * 60)

    symbols = DEFAULT_SYMBOLS[:10]  # First 10 symbols
    max_candles = 5000  # Reduced for faster training

    print(f"📊 Training on {len(symbols)} symbols: {symbols}")
    print(f"🕯️ Candles per symbol: {max_candles}")

    # Collect data
    all_data = []
    print("\n📥 Fetching data...")

    for symbol in symbols:
        print(f"  📊 {symbol}...", end=" ", flush=True)
        df = fetch_crypto_data(symbol, max_candles)

        if df is not None and len(df) > 100:
            df = add_indicators(df)
            df = label_data(df)

            if len(df) > 50:
                all_data.append(df)
                print(f"✅ {len(df)} samples")
            else:
                print("⚠️ Too few samples")
        else:
            print("❌ Failed")

    if not all_data:
        print("❌ No data collected!")
        return

    # Prepare training data
    full_df = pd.concat(all_data, ignore_index=True)
    print(f"\n📊 Total samples: {len(full_df)}")

    X = full_df[FEATURE_COLUMNS]
    y = full_df['target']

    # Filter rare classes
    class_counts = y.value_counts()
    min_samples = int(len(y) * 0.01)
    valid_classes = class_counts[class_counts >= min_samples].index.tolist()

    if len(valid_classes) < len(class_counts):
        removed = [c for c in class_counts.index if c not in valid_classes]
        print(f"⚠️ Removing rare classes: {removed}")

        mask = y.isin(valid_classes)
        X = X[mask]
        y = y[mask]
        full_df = full_df[mask]

    # Encode labels
    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    print(f"🎯 Classes: {list(label_encoder.classes_)}")
    print("📈 Class distribution:")
    for label, count in y.value_counts().items():
        pct = count / len(y) * 100
        print(".1f")

    # Scale features
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    # Sample weights
    sample_weights = compute_sample_weight('balanced', y_encoded)

    # Train model
    print("\n🏋️ Training model...")
    model = XGBClassifier(
        objective='multi:softprob',
        num_class=len(label_encoder.classes_),
        max_depth=6,
        n_estimators=100,  # Reduced for speed
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_scaled, y_encoded, sample_weight=sample_weights)

    # Quick evaluation
    split_idx = int(len(X_scaled) * 0.8)
    X_test = X_scaled[split_idx:]
    y_test = y_encoded[split_idx:]

    preds = model.predict(X_test)
    accuracy = (preds == y_test).mean()
    print(".3f")

    # Save model locally
    version = f"local-v3.3-{datetime.now().strftime('%Y%m%d-%H%M')}"

    model_data = {
        'model': model,
        'label_encoder': label_encoder,
        'feature_names': FEATURE_COLUMNS,
        'confidence_threshold': 0.6
    }

    metadata = {
        'symbols': symbols,
        'candles_per_symbol': max_candles,
        'total_samples': len(full_df),
        'training_time_seconds': 0,
        'class_distribution': {str(k): int(v) for k, v in y.value_counts().items()},
        'avg_label_confidence': float(full_df['label_confidence'].mean()),
        'confidence_threshold': 0.6,
        'labeling_method': 'multi_window_win_rate',
        'lookforward_windows': [12, 24, 36]
    }

    # Save to memory archives
    os.makedirs('nexus_system/memory_archives', exist_ok=True)

    model_path = 'nexus_system/memory_archives/ml_model.pkl'
    scaler_path = 'nexus_system/memory_archives/scaler.pkl'

    joblib.dump(model_data, model_path)
    joblib.dump(scaler, scaler_path)

    print(f"\n💾 Model saved to {model_path}")
    print(f"📊 Includes SOLUSDT: {'✅ Yes' if 'SOLUSDT' in symbols else '❌ No'}")
    print(f"🎯 Test Accuracy: {accuracy:.3f}")
    print(f"📦 Version: {version}")

if __name__ == "__main__":
    main()
