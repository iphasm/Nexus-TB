#!/usr/bin/env python3
"""
Script to check all saved models
"""

import joblib
import os
import glob

# Check all model files
model_files = glob.glob('nexus_system/memory_archives/ml_model*.pkl')
print(f'Encontrados {len(model_files)} archivos de modelo:')

for model_file in sorted(model_files):
    try:
        model_data = joblib.load(model_file)
        if isinstance(model_data, dict):
            metadata = model_data.get('metadata', {})
            symbols = metadata.get('symbols', [])
            version = metadata.get('version', 'desconocida')
            accuracy = metadata.get('accuracy', 'N/A')
            has_sol = 'SOLUSDT' in symbols
            print(f'📊 {os.path.basename(model_file)}: v{version}, {len(symbols)} símbolos, SOLUSDT: {"✅" if has_sol else "❌"}, acc: {accuracy}')
        else:
            print(f'⚠️ {os.path.basename(model_file)}: formato legacy')
    except Exception as e:
        print(f'❌ {os.path.basename(model_file)}: error - {e}')
