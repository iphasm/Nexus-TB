#!/usr/bin/env python3
"""
AUDITORÍA RÁPIDA: ML Classifier
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('🔬 AUDITORÍA RÁPIDA ML CLASSIFIER')
print('=' * 50)

# Verificar archivos
model_path = 'nexus_system/memory_archives/ml_model.pkl'
scaler_path = 'nexus_system/memory_archives/scaler.pkl'

model_exists = os.path.exists(model_path)
scaler_exists = os.path.exists(scaler_path)

print(f'Modelo: {"✅" if model_exists else "❌"} {model_path}')
print(f'Scaler: {"✅" if scaler_exists else "❌"} {scaler_path}')

if model_exists:
    try:
        import joblib
        model_data = joblib.load(model_path)
        if isinstance(model_data, dict):
            model = model_data.get('model')
            feature_names = model_data.get('feature_names')
            print(f'✅ Modelo cargado - Features: {len(feature_names) if feature_names else "N/A"}')
        else:
            print('⚠️  Modelo en formato legacy')
    except Exception as e:
        print(f'❌ Error cargando modelo: {e}')
else:
    print('❌ Modelo no encontrado')

# Verificar activos
try:
    from system_directive import get_all_assets, ASSET_GROUPS, GROUP_CONFIG
    all_assets = get_all_assets()
    enabled_assets = []

    for group, assets in ASSET_GROUPS.items():
        if GROUP_CONFIG.get(group, True):
            enabled_assets.extend(assets)

    enabled_assets = list(set(enabled_assets))

    print(f'📊 Total activos configurados: {len(all_assets)}')
    print(f'🎯 Activos habilitados: {len(enabled_assets)}')

    print('\n📂 GRUPOS DE ACTIVOS:')
    for group, assets in ASSET_GROUPS.items():
        status = '✅' if GROUP_CONFIG.get(group, True) else '❌'
        print(f'   {status} {group}: {len(assets)} activos')

    # Verificar algunos activos clave
    key_assets = ['BTCUSDT', 'ETHUSDT', 'TAOUSDT', 'SOLUSDT']
    print(f'\n🔑 ACTIVOS CLAVE:')
    for asset in key_assets:
        in_config = asset in all_assets
        enabled = asset in enabled_assets
        status = '✅' if enabled else ('⚠️ ' if in_config else '❌')
        print(f'   {status} {asset}')

except Exception as e:
    print(f'❌ Error cargando configuración: {e}')

print('\n✅ Auditoría completada')
print('\n📋 RECOMENDACIONES:')
if not model_exists:
    print('❌ Reentrenar modelo - archivo faltante')
else:
    print('✅ Modelo existe - verificar si necesita actualización con nuevos activos')
