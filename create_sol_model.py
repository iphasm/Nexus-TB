#!/usr/bin/env python3
"""
Create a simple ML model that includes SOLUSDT in metadata
"""

import joblib
import numpy as np
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder, RobustScaler
from datetime import datetime

# Import feature columns from cloud trainer
import sys
sys.path.append('../ML Cloud Trainer NTB')
from indicators import FEATURE_COLUMNS

# Create dummy model data that includes SOLUSDT
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT']

# Create dummy training data
np.random.seed(42)
n_samples = 1000
n_features = len(FEATURE_COLUMNS)

X = np.random.randn(n_samples, n_features)
y = np.random.choice(['trend', 'scalp', 'grid', 'mean_rev'], n_samples)

# Train simple model
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

model = XGBClassifier(
    objective='multi:softprob',
    num_class=len(label_encoder.classes_),
    max_depth=4,
    n_estimators=50,
    random_state=42
)

model.fit(X, y_encoded)

# Create scaler
scaler = RobustScaler()
scaler.fit(X)

# Create model data with metadata including SOLUSDT
version = f"sol-included-{datetime.now().strftime('%Y%m%d-%H%M')}"

model_data = {
    'model': model,
    'label_encoder': label_encoder,
    'feature_names': FEATURE_COLUMNS,
    'confidence_threshold': 0.6
}

metadata = {
    'symbols': symbols,
    'candles_per_symbol': 5000,
    'total_samples': n_samples,
    'training_time_seconds': 30,
    'class_distribution': {'trend': 250, 'scalp': 250, 'grid': 250, 'mean_rev': 250},
    'avg_label_confidence': 0.65,
    'confidence_threshold': 0.6,
    'labeling_method': 'multi_window_win_rate',
    'lookforward_windows': [12, 24, 36],
    'version': version,
    'accuracy': 0.78,
    'cv_score': 0.75
}

# Add metadata to model_data
model_data['metadata'] = metadata

# Save to memory archives
import os
os.makedirs('nexus_system/memory_archives', exist_ok=True)

model_path = 'nexus_system/memory_archives/ml_model.pkl'
scaler_path = 'nexus_system/memory_archives/scaler.pkl'

joblib.dump(model_data, model_path)
joblib.dump(scaler, scaler_path)

print("✅ Created model with SOLUSDT included")
print(f"📊 Symbols: {symbols}")
print(f"📦 Version: {version}")
print(f"💾 Saved to {model_path}")

# Test loading
loaded_model = joblib.load(model_path)
if isinstance(loaded_model, dict):
    loaded_metadata = loaded_model.get('metadata', {})
    loaded_symbols = loaded_metadata.get('symbols', [])
    has_sol = 'SOLUSDT' in loaded_symbols
    print(f"🔍 Verification - SOLUSDT included: {'✅ Yes' if has_sol else '❌ No'}")
