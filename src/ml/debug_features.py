#!/usr/bin/env python3
"""
Debug script para verificar por qué las features no se están agregando
"""
import signal
import time
import logging
from train_cortex import fetch_data, add_indicators
from add_new_features import add_all_new_features
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global timeout settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2  # Fewer retries for debug

# Global flag for interruption
interrupted = False

def signal_handler(signum, frame):
    """Handle Ctrl+C interruption"""
    global interrupted
    interrupted = True
    print("\n⚠️  Debug interrumpido por el usuario (Ctrl+C)", flush=True)

def debug_feature_addition():
    """Debug paso a paso de la adición de features"""
    global interrupted

    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 60)
    print("🐛 DEBUG - ADICIÓN DE FEATURES")
    print("=" * 60)

    # Paso 1: Obtener datos básicos
    print("\n📊 PASO 1: Descargando datos...")
    start_time = time.time()

    # Add timeout wrapper
    timeout_reached = False
    df = None

    try:
        df = fetch_data("BTCUSDT", max_candles=200, verbose=True)
    except Exception as e:
        print(f"❌ Error en descarga: {e}")
        return

    if time.time() - start_time > REQUEST_TIMEOUT:
        timeout_reached = True
        print(f"⚠️  Descarga tomó más de {REQUEST_TIMEOUT} segundos")

    if interrupted:
        print("⚠️  Operación cancelada por el usuario")
        return

    if df is None or df.empty:
        print("❌ Error: No se pudieron descargar datos")
        return

    print(f"✅ Datos descargados: {len(df)} filas")

    if interrupted or timeout_reached:
        return

    # Paso 2: Agregar indicadores básicos
    print("\n📊 PASO 2: Agregando indicadores básicos...")
    step_start = time.time()

    try:
        df = add_indicators(df)
        step_time = time.time() - step_start
        print(f"✅ Después de indicadores básicos: {len(df.columns)} columnas ({step_time:.2f}s)")
    except Exception as e:
        print(f"❌ Error en indicadores básicos: {e}")
        return

    # Mostrar algunas columnas para verificar
    print("📋 Columnas disponibles:")
    basic_cols = [col for col in df.columns if not col.startswith(('roc_', 'williams', 'cci', 'volume_', 'chaikin', 'dist_', 'pivot', 'fib', 'morning', 'gap', 'bull', 'bear', 'momentum_div', 'vpt', 'intraday'))]
    print(f"   Básicas: {len(basic_cols)} columnas")
    print(f"   Muestra: {basic_cols[:5]}...")

    if interrupted:
        return

    # Paso 3: Agregar nuevas features
    print("\n📊 PASO 3: Agregando nuevas features...")
    step_start = time.time()

    try:
        initial_cols = len(df.columns)
        df = add_all_new_features(df)
        final_cols = len(df.columns)
        new_cols = final_cols - initial_cols
        step_time = time.time() - step_start

        print(f"✅ Después de nuevas features: {final_cols} columnas (+{new_cols}) ({step_time:.2f}s)")
    except Exception as e:
        print(f"❌ Error en nuevas features: {e}")
        return

    # Verificar qué nuevas features se agregaron
    print("\n🔍 VERIFICACIÓN DE NUEVAS FEATURES:")

    feature_categories = {
        'Momentum': ['roc_21', 'roc_50', 'williams_r', 'cci', 'ultimate_osc'],
        'Volumen': ['volume_roc_5', 'volume_roc_21', 'chaikin_mf', 'force_index', 'ease_movement'],
        'Estructura': ['dist_sma20', 'dist_sma50', 'pivot_dist', 'fib_dist'],
        'Correlación': ['morning_volatility', 'afternoon_volatility', 'gap_up', 'gap_down', 'range_change'],
        'Sentimiento': ['bull_power', 'bear_power', 'momentum_div', 'vpt', 'intraday_momentum']
    }

    for category, features in feature_categories.items():
        present = [f for f in features if f in df.columns]
        missing = [f for f in features if f not in df.columns]
        print(f"   • {category}: {len(present)}/{len(features)} presentes")

        if missing:
            print(f"     ❌ Faltan: {missing}")

        # Verificar NaN en features presentes
        for feature in present:
            nan_count = df[feature].isna().sum()
            if nan_count > 0:
                print(f"     ⚠️  {feature}: {nan_count} valores NaN")

    print(f"\n📊 RESULTADO FINAL:")
    print(f"   • Filas: {len(df)}")
    print(f"   • Columnas totales: {len(df.columns)}")
    print(f"   • Nuevas features agregadas: {new_cols}")

    if new_cols < 10:
        print("   ❌ ¡PROBLEMA! Muy pocas features nuevas se agregaron")
        print("   💡 Revisa las funciones en add_new_features.py")
    else:
        print("   ✅ Features nuevas agregadas correctamente")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    debug_feature_addition()
