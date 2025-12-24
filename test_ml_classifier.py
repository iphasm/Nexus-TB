"""
ML Classifier Test Script v2.0
Tests the trained model with REAL market data from Binance
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from binance.client import Client


def fetch_real_data(symbol: str, interval: str = '15m', limit: int = 100):
    """Fetch real market data from Binance"""
    print(f"📥 Fetching real data for {symbol}...")
    
    try:
        client = Client()
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
        
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None


def add_indicators(df):
    """Calculate all indicators needed by the ML classifier"""
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
    
    # ADX (proper calculation)
    period = 14
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    atr = df['atr']
    plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / (atr + 1e-10)
    minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / (atr + 1e-10)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    df['adx'] = dx.rolling(period).mean().fillna(25).clip(0, 100)
    
    # EMAs
    df['ema_20'] = close.ewm(span=20, adjust=False).mean()
    df['ema_50'] = close.ewm(span=50, adjust=False).mean()
    
    # Fill NaN
    df = df.ffill().bfill()
    
    return df


def get_market_context(df):
    """Analyze the current market context based on indicators"""
    last = df.iloc[-1]
    
    rsi = last['rsi']
    adx = last['adx']
    close = last['close']
    ema_20 = last['ema_20']
    ema_50 = last['ema_50']
    atr = last['atr']
    
    # Trend direction
    if close > ema_20 > ema_50:
        trend = "📈 Uptrend"
    elif close < ema_20 < ema_50:
        trend = "📉 Downtrend"
    else:
        trend = "↔️ Mixed"
    
    # RSI condition
    if rsi > 70:
        rsi_status = "🔥 Overbought"
    elif rsi < 30:
        rsi_status = "🧊 Oversold"
    else:
        rsi_status = "⚖️ Neutral"
    
    # ADX strength
    if adx > 40:
        adx_status = "💪 Strong Trend"
    elif adx > 25:
        adx_status = "📊 Moderate Trend"
    else:
        adx_status = "😴 Weak/Range"
    
    # Volatility
    atr_pct = (atr / close) * 100
    if atr_pct > 3:
        vol_status = "🌀 High Volatility"
    elif atr_pct > 1.5:
        vol_status = "📊 Normal Volatility"
    else:
        vol_status = "😴 Low Volatility"
    
    return {
        'trend': trend,
        'rsi': f"{rsi:.1f} {rsi_status}",
        'adx': f"{adx:.1f} {adx_status}",
        'volatility': vol_status,
        'atr_pct': atr_pct
    }


def main():
    print("=" * 60)
    print("🧠 ML CLASSIFIER LIVE TEST")
    print("=" * 60)
    
    # Load classifier
    try:
        from antigravity_quantum.strategies.ml_classifier import MLClassifier
        MLClassifier.load_model()
        
        if MLClassifier._model is None:
            print("❌ ERROR: Model not loaded!")
            print("   Run: python train_ml_model.py")
            return
            
        print("✅ Model loaded successfully!")
        print(f"   Type: {type(MLClassifier._model).__name__}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to load MLClassifier: {e}")
        return
    
    # Test with real symbols
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
    
    print("-" * 60)
    print("LIVE MARKET PREDICTIONS")
    print("-" * 60)
    
    for symbol in test_symbols:
        df = fetch_real_data(symbol)
        if df is None:
            continue
            
        df = add_indicators(df)
        
        # Get market context
        context = get_market_context(df)
        
        # Prepare for classifier
        market_data = {'dataframe': df}
        
        # Get ML prediction
        result = MLClassifier.classify(market_data)
        
        # Display
        print(f"\n{'='*50}")
        print(f"🪙 {symbol}")
        print(f"{'='*50}")
        print(f"💰 Price: ${df['close'].iloc[-1]:,.2f}")
        print(f"📊 RSI: {context['rsi']}")
        print(f"📈 ADX: {context['adx']}")
        print(f"🔄 Trend: {context['trend']}")
        print(f"🌀 Vol: {context['volatility']} (ATR: {context['atr_pct']:.2f}%)")
        print()
        
        if result:
            print(f"🎯 ML PREDICTION: {result.suggested_strategy}")
            print(f"   Confidence: {result.confidence:.1%}")
            print(f"   Reason: {result.reason}")
        else:
            print("⚠️ ML returned None (would fallback to rules)")
    
    print("\n" + "=" * 60)
    print("✅ LIVE TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
