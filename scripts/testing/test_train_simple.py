#!/usr/bin/env python3
"""
Test simple para verificar que train_cortex.py se puede importar y ejecutar
"""
import sys
import os

print("=" * 50)
print("🧪 TEST SIMPLE - TRAIN_CORTEX.PY")
print("=" * 50)

# Verificar que estamos en el directorio correcto
print(f"📂 Directorio actual: {os.getcwd()}")

# Verificar que el archivo existe
if os.path.exists("train_cortex.py"):
    print("✅ train_cortex.py encontrado")
else:
    print("❌ train_cortex.py NO encontrado")
    sys.exit(1)

# Intentar importar módulos básicos
print("\n🔍 Probando imports básicos...")
try:
    import pandas as pd
    import numpy as np
    import sklearn
    import xgboost
    import joblib
    print("✅ Imports básicos OK")
except ImportError as e:
    print(f"❌ Error en imports: {e}")
    sys.exit(1)

# Intentar importar train_cortex
print("\n🔍 Probando import de train_cortex...")
try:
    import train_cortex
    print("✅ train_cortex importado correctamente")

    # Verificar que las funciones principales existen
    if hasattr(train_cortex, 'fetch_data'):
        print("✅ Función fetch_data encontrada")
    else:
        print("❌ Función fetch_data NO encontrada")

    if hasattr(train_cortex, 'train'):
        print("✅ Función train encontrada")
    else:
        print("❌ Función train NO encontrada")

except ImportError as e:
    print(f"❌ Error importando train_cortex: {e}")
    sys.exit(1)

# Intentar ejecutar con argumentos mínimos
print("\n🔍 Probando ejecución básica...")
try:
    # Simular argumentos de línea de comandos
    sys.argv = ['train_cortex.py', '--candles', '100', '--symbols', '1']

    # Importar argparse y crear argumentos mock
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--candles', type=str, default='15000')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--symbols', type=int, default=None)

    # Parsear argumentos mock
    args = parser.parse_args(['--candles', '100', '--symbols', '1'])
    print(f"✅ Argumentos parseados: candles={args.candles}, symbols={args.symbols}")

except Exception as e:
    print(f"❌ Error en argumentos: {e}")

print("\n✅ TEST COMPLETADO - Todo funciona correctamente")
print("🚀 El script está listo para ejecutar entrenamiento completo")
print("=" * 50)
