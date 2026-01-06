#!/usr/bin/env python3
"""
Script to check what model is currently saved locally
"""

import joblib
import os

model_path = 'nexus_system/memory_archives/ml_model.pkl'
if os.path.exists(model_path):
    model_data = joblib.load(model_path)
    if isinstance(model_data, dict):
        feature_names = model_data.get('feature_names', [])
        metadata = model_data.get('metadata', {})
        symbols = metadata.get('symbols', [])
        print(f'📊 Modelo actual: {metadata.get("version", "desconocida")}')
        print(f'🎯 Símbolos incluidos: {len(symbols)}')
        print(f'📈 Accuracy: {metadata.get("accuracy", "N/A")}')
        print(f'🔄 CV Score: {metadata.get("cv_score", "N/A")}')
        print(f'SOLUSDT incluido: {"✅ Sí" if "SOLUSDT" in symbols else "❌ No"}')
        print(f'Símbolos: {symbols[:10]}...' if len(symbols) > 10 else f'Símbolos: {symbols}')
    else:
        print('⚠️ Modelo en formato legacy')
else:
    print('❌ No hay modelo guardado')
