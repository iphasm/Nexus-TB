#!/usr/bin/env python3
"""
Test script to verify SOLUSDT no longer triggers ML bypass
"""

import pandas as pd
import numpy as np
from nexus_system.cortex.ml_classifier import MLClassifier

# Create dummy market data for SOLUSDT
np.random.seed(42)
timestamps = pd.date_range('2024-01-01', periods=100, freq='15min')
data = {
    'timestamp': timestamps,
    'open': np.random.uniform(90, 110, 100),
    'high': np.random.uniform(95, 115, 100),
    'low': np.random.uniform(85, 105, 100),
    'close': np.random.uniform(90, 110, 100),
    'volume': np.random.uniform(1000, 10000, 100),
    'rsi': np.random.uniform(30, 70, 100),
    'adx': np.random.uniform(20, 40, 100),
    'atr_pct': np.random.uniform(0.5, 2.0, 100),
    'trend_str': np.random.uniform(-1, 1, 100),
    'vol_change': np.random.uniform(-0.5, 0.5, 100)
}

df = pd.DataFrame(data)

market_data = {
    'symbol': 'SOLUSDT',
    'dataframe': df
}

print("🧪 Testing SOLUSDT ML classification...")
print(f"📊 Symbol: {market_data['symbol']}")
print(f"📈 Data points: {len(df)}")

# Test classification
result = MLClassifier.classify(market_data)

if result is None:
    print("🔄 ML Bypass: SOLUSDT still triggering bypass (fallback to rule-based)")
    print("❌ TEST FAILED: SOLUSDT should be classified by ML")
else:
    print("✅ ML Classification: SOLUSDT successfully classified")
    print(f"🎯 Regime: {result.regime}")
    print(f"📈 Strategy: {result.suggested_strategy}")
    print(f"🎪 Confidence: {result.confidence:.1%}")
    print("✅ TEST PASSED: SOLUSDT bypass fixed")
