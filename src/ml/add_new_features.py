#!/usr/bin/env python3
"""
Script para agregar nuevas features que reduzcan la dependencia de ATR
"""
import pandas as pd
import numpy as np
from ta_compat import ta

def add_momentum_features(df):
    """Agrega features de momentum avanzadas"""
    print("📊 Agregando features de momentum...")

    # Rate of Change adicional (periodos más largos)
    df['roc_21'] = (df['close'] - df['close'].shift(21)) / df['close'].shift(21) * 100
    df['roc_50'] = (df['close'] - df['close'].shift(50)) / df['close'].shift(50) * 100

    # Williams %R (momentum oscillator)
    williams = ta.willr(df['high'], df['low'], df['close'], length=14)
    df['williams_r'] = williams if williams is not None else -50

    # Commodity Channel Index (CCI)
    cci = ta.cci(df['high'], df['low'], df['close'], length=20)
    df['cci'] = cci if cci is not None else 0

    # Ultimate Oscillator
    uo = ta.uo(df['high'], df['low'], df['close'], length1=7, length2=14, length3=28)
    df['ultimate_osc'] = uo if uo is not None else 50

    print("   ✅ Agregadas: ROC_21, ROC_50, Williams %R, CCI, Ultimate Oscillator")
    return df

def add_volume_features(df):
    """Agrega features de volumen avanzadas"""
    print("📊 Agregando features de volumen...")

    # Volume Rate of Change
    df['volume_roc_5'] = (df['volume'] - df['volume'].shift(5)) / df['volume'].shift(5) * 100
    df['volume_roc_21'] = (df['volume'] - df['volume'].shift(21)) / df['volume'].shift(21) * 100

    # Chaikin Money Flow
    cmf = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=20)
    df['chaikin_mf'] = cmf if cmf is not None else 0

    # Force Index
    df['force_index'] = df['close'].diff() * df['volume']

    # Ease of Movement (eom in pandas_ta)
    eom = ta.eom(df['high'], df['low'], df['close'], df['volume'], length=14)
    df['ease_movement'] = eom if eom is not None else 0

    print("   ✅ Agregadas: Volume ROC, Chaikin MF, Force Index, Ease of Movement")
    return df

def add_structure_features(df):
    """Agrega features de estructura de mercado"""
    print("📊 Agregando features de estructura...")

    # Distance to moving averages
    df['dist_sma20'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'] * 100
    df['dist_sma50'] = (df['close'] - df['close'].rolling(50).mean()) / df['close'] * 100

    # Pivot Points
    df['pivot_point'] = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
    df['pivot_r1'] = 2 * df['pivot_point'] - df['low'].shift(1)
    df['pivot_s1'] = 2 * df['pivot_point'] - df['high'].shift(1)
    df['pivot_dist'] = (df['close'] - df['pivot_point']) / df['close'] * 100

    # Fibonacci retracements (simplified)
    high_21 = df['high'].rolling(21).max()
    low_21 = df['low'].rolling(21).min()
    df['fib_618'] = low_21 + (high_21 - low_21) * 0.618
    df['fib_382'] = low_21 + (high_21 - low_21) * 0.382
    df['fib_dist'] = (df['close'] - df['fib_618']) / df['close'] * 100

    print("   ✅ Agregadas: Distancia SMA, Pivot Points, Fibonacci levels")
    return df

def add_correlation_features(df):
    """Agrega features de correlación (simplified - necesitaría datos multi-asset)"""
    print("📊 Agregando features de correlación...")

    # Intra-day volatility patterns
    df['morning_volatility'] = df['close'].pct_change().rolling(12).std()  # First 3 hours
    df['afternoon_volatility'] = df['close'].pct_change().rolling(12).std()  # Last 3 hours

    # Gap analysis
    df['gap_up'] = ((df['open'] - df['close'].shift(1)) / df['close'].shift(1) * 100).clip(lower=0)
    df['gap_down'] = ((df['open'] - df['close'].shift(1)) / df['close'].shift(1) * 100).clip(upper=0).abs()

    # Range expansion
    df['range_ratio'] = df['high'] - df['low']
    df['range_change'] = df['range_ratio'] / df['range_ratio'].shift(1)

    print("   ✅ Agregadas: Volatilidad intra-day, Gap analysis, Range expansion")
    return df

def add_market_sentiment_features(df):
    """Agrega features de sentimiento de mercado (simplified)"""
    print("📊 Agregando features de sentimiento...")

    # Bull/Bear Ratio (simplified)
    df['bull_power'] = df['close'] - df['ema_20']
    df['bear_power'] = df['ema_20'] - df['close']

    # Momentum divergence
    df['momentum_div'] = df['rsi'] - df['rsi'].shift(10)

    # Volume-Price Trend
    df['vpt'] = (df['close'].pct_change() * df['volume']).cumsum()

    # Intraday momentum
    df['intraday_momentum'] = (df['close'] - df['open']) / df['open'] * 100

    print("   ✅ Agregadas: Bull/Bear power, Momentum divergence, VPT, Intraday momentum")
    return df

def add_all_new_features(df):
    """Agrega todas las nuevas features"""
    print("\n🚀 INICIANDO EXPANSIÓN DE FEATURES")
    print("=" * 50)

    initial_features = len(df.columns)
    print(f"📊 Features iniciales: {initial_features}")

    # Agregar cada categoría de features
    df = add_momentum_features(df)
    df = add_volume_features(df)
    df = add_structure_features(df)
    df = add_correlation_features(df)
    df = add_market_sentiment_features(df)

    # Limpiar NaN
    df = df.dropna()

    final_features = len(df.columns)
    new_features = final_features - initial_features

    print(f"\n✅ EXPANSIÓN COMPLETADA:")
    print(f"   • Features iniciales: {initial_features}")
    print(f"   • Nuevas features: {new_features}")
    print(f"   • Total features: {final_features}")
    print(f"   • Muestras finales: {len(df)}")

    return df

if __name__ == "__main__":
    print("⚠️  Este script debe ser usado desde train_cortex.py")
    print("💡 Las nuevas features se agregan automáticamente durante el entrenamiento")
