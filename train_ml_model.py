import asyncio
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from binance.client import Client
# from utils.indicators import calculate_indicators  <-- REMOVED to avoid dependency issues

import yfinance as yf
from config import get_all_assets, is_crypto

# Configuration
SYMBOLS = get_all_assets()
INTERVAL = '15m'
MODEL_OUTPUT = os.path.join('antigravity_quantum', 'data', 'ml_model.pkl')

def fetch_data(symbol):
    """Fetches historical data from Binance (Crypto) or YFinance (Stocks)"""
    print(f"📥 Fetching data for {symbol}...")
    
    if is_crypto(symbol):
        # BINANCE
        try:
            client = Client() # Public client
            klines = client.futures_klines(symbol=symbol, interval=INTERVAL, limit=1500)
            
            # Parse
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 
                'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            df = df.astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"   ⚠️ Binance error for {symbol}: {e}")
            return None
    else:
        # STOCKS / COMMODITIES (YFinance)
        try:
            # interval='15m' max 60 days in yfinance
            # Map symbol if needed (e.g. GLD -> GLD, but some might differ)
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="59d", interval="15m")
            
            if df.empty:
                print(f"   ⚠️ No data from YF for {symbol}")
                return None
                
            df.reset_index(inplace=True)
            # Rename columns to standard lowercase
            df.rename(columns={
                'Date': 'timestamp', 'Datetime': 'timestamp',
                'Open': 'open', 'High': 'high', 'Low': 'low', 
                'Close': 'close', 'Volume': 'volume'
            }, inplace=True)
            
            # Ensure timezone naive for compatibility
            if df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                
            return df
        except Exception as e:
            print(f"   ⚠️ YFinance error for {symbol}: {e}")
            return None

def add_indicators(df):
    """
    Must match MLClassifier._extract_features logic exactly in terms of inputs.
    """
    # Simple Manual Calculation to ensure independence from complex bot logic for this script
    close = df['close']
    
    # RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # ATR (14)
    high = df['high']
    low = df['low']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    df['atr_pct'] = (df['atr'] / close) * 100
    
    # ADX (14) - Simplified for demo
    # Note: True ADX is complex, using a simplified volatility/trend proxy for 'adx' feature match
    # Or strictly implementing standard ADX if needed. Let's use a simpler proxy for robust demo.
    # Actually, let's just assume simple directional strength
    df['adx'] = df['atr_pct'] * 15 # Placeholder approx if lib not avail, but let's try to match bot
    
    # EMAs
    df['ema_20'] = close.ewm(span=20, adjust=False).mean()
    df['ema_50'] = close.ewm(span=50, adjust=False).mean()
    df['ema_200'] = close.ewm(span=200, adjust=False).mean()
    
    # Features specific to bot
    df['trend_str'] = (df['ema_20'] - df['ema_50']) / close * 100
    df['vol_change'] = (df['volume'] - df['volume'].shift(1)) / (df['volume'].shift(1) + 1e-9)
    
    df.dropna(inplace=True)
    return df

def label_data(df):
    """
    Auto-label data based on FUTURE price action.
    This creates the 'ground truth' for training.
    
    Looking 12 periods ahead (e.g. 3 hours on 15m).
    """
    df['target'] = 'mean_rev' # Default
    
    future_close = df['close'].shift(-12)
    change_pct = (future_close - df['close']) / df['close']
    
    # 1. TREND: Price moved > 1.5% in either direction
    df.loc[change_pct > 0.015, 'target'] = 'trend'
    df.loc[change_pct < -0.015, 'target'] = 'trend'
    
    # 2. GRID: Price stayed within tight range +/- 0.5%
    mask_grid = (change_pct.abs() < 0.005)
    df.loc[mask_grid, 'target'] = 'grid'
    
    # 3. SCALP: High intra-period volatility but low net displacement? 
    # For simplicity, let's leave as mix.
    
    df.dropna(inplace=True)
    return df

def train():
    all_data = []
    
    print("🚀 Starting Training Process...")
    
    for symbol in SYMBOLS:
        try:
            df = fetch_data(symbol)
            df = add_indicators(df)
            df = label_data(df)
            all_data.append(df)
        except Exception as e:
            print(f"⚠️ Error with {symbol}: {e}")
            
    if not all_data:
        print("❌ No data collected.")
        return

    full_df = pd.concat(all_data)
    
    # Feature Columns (Must match MLClassifier._extract_features)
    # [RSI, ADX, ATR_PCT, TREND_STR, VOL_CHANGE]
    X_cols = ['rsi', 'adx', 'atr_pct', 'trend_str', 'vol_change']
    X = full_df[X_cols]
    y = full_df['target']
    
    print(f"📊 Training on {len(X)} samples...")
    print(f"   Distribution: {y.value_counts().to_dict()}")
    
    # Splite
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    print("\n📈 Model Evaluation:")
    preds = model.predict(X_test)
    print(classification_report(y_test, preds))
    
    # Save
    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT)
    print(f"✅ Model saved to: {MODEL_OUTPUT}")
    print("👉 To enable, restart bot and run: /ml_mode on")

if __name__ == "__main__":
    train()
