#!/usr/bin/env python3
"""
Diagnóstico paso a paso para identificar exactamente dónde se cuelga el script
"""
import time
import signal
import sys

# Global flag for interruption
interrupted = False

def signal_handler(signum, frame):
    """Handle Ctrl+C"""
    global interrupted
    interrupted = True
    print("\n⚠️  DEBUG interrumpido por el usuario", flush=True)

def test_step(step_name, test_func, timeout=30):
    """Ejecuta un paso con timeout y manejo de interrupciones"""
    if interrupted:
        print(f"⚠️  Paso '{step_name}' saltado - interrupción previa", flush=True)
        return False

    print(f"\n🔍 PASO: {step_name}", flush=True)
    print(f"⏱️  Timeout: {timeout}s", flush=True)

    start_time = time.time()

    try:
        result = test_func()
        elapsed = time.time() - start_time
        print(".2f")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        print(".2f")
        return False

def step_imports():
    """Test basic imports"""
    print("  Testing imports...", end=" ", flush=True)
    import pandas as pd
    import numpy as np
    import sklearn
    import xgboost
    import joblib
    print("✅ Imports OK", flush=True)
    return True

def step_system_config():
    """Test system configuration loading"""
    print("  Loading system config...", end=" ", flush=True)
    from system_directive import get_all_assets, is_crypto
    symbols = get_all_assets()
    crypto_test = is_crypto("BTCUSDT")
    stock_test = is_crypto("AAPL")
    print(f"✅ {len(symbols)} symbols, BTCUSDT={crypto_test}, AAPL={stock_test}", flush=True)
    return True

def step_single_fetch():
    """Test single data fetch"""
    print("  Testing single data fetch...", end=" ", flush=True)
    from src.ml.train_cortex import fetch_data
    df = fetch_data("BTCUSDT", max_candles=100, verbose=True)
    if df is not None and not df.empty:
        print(f"✅ {len(df)} rows fetched", flush=True)
        return True
    else:
        print("❌ Fetch failed", flush=True)
        return False

def step_multiple_fetch():
    """Test multiple data fetch"""
    print("  Testing multiple data fetch (2 symbols)...", end=" ", flush=True)
    from src.ml.train_cortex import fetch_data
    symbols = ["BTCUSDT", "ETHUSDT"]

    for symbol in symbols:
        if interrupted:
            print("⏹️  Multiple fetch interrupted", flush=True)
            return False

        print(f"    Fetching {symbol}...", end=" ", flush=True)
        df = fetch_data(symbol, max_candles=50, verbose=False)
        if df is None or df.empty:
            print(f"❌ Failed for {symbol}", flush=True)
            return False
        print(f"✅ {len(df)} rows", flush=True)

    print("✅ Multiple fetch OK", flush=True)
    return True

def step_indicators():
    """Test indicator calculation"""
    print("  Testing indicator calculation...", end=" ", flush=True)
    from src.ml.train_cortex import fetch_data, add_indicators

    df = fetch_data("BTCUSDT", max_candles=200, verbose=False)
    if df is None or df.empty:
        print("❌ No data for indicators", flush=True)
        return False

    initial_cols = len(df.columns)
    df = add_indicators(df)
    final_cols = len(df.columns)

    print(f"✅ Indicators OK: {initial_cols} → {final_cols} columns", flush=True)
    return True

def step_new_features():
    """Test new feature addition"""
    print("  Testing new features addition...", end=" ", flush=True)
    from src.ml.train_cortex import fetch_data, add_indicators
    from src.ml.add_new_features import add_all_new_features

    df = fetch_data("BTCUSDT", max_candles=200, verbose=False)
    if df is None or df.empty:
        print("❌ No data for new features", flush=True)
        return False

    df = add_indicators(df)
    initial_cols = len(df.columns)

    df = add_all_new_features(df)
    final_cols = len(df.columns)
    new_features = final_cols - initial_cols

    print(f"✅ New features OK: +{new_features} features ({final_cols} total)", flush=True)
    return True

def step_data_processing():
    """Test data processing pipeline"""
    print("  Testing data processing pipeline...", end=" ", flush=True)
    from src.ml.train_cortex import fetch_data, add_indicators
    from src.ml.add_new_features import add_all_new_features

    symbols = ["BTCUSDT", "ETHUSDT"]
    all_data = []

    for symbol in symbols:
        if interrupted:
            print("⏹️  Data processing interrupted", flush=True)
            return False

        print(f"    Processing {symbol}...", end=" ", flush=True)

        df = fetch_data(symbol, max_candles=100, verbose=False)
        if df is None or df.empty:
            print(f"❌ No data for {symbol}", flush=True)
            return False

        df = add_indicators(df)
        df = add_all_new_features(df)

        if len(df) > 10:  # Check if we have meaningful data
            all_data.append(df)
            print(f"✅ {len(df)} rows", flush=True)
        else:
            print(f"❌ Insufficient data for {symbol}", flush=True)
            return False

    print(f"✅ Data processing OK: {len(all_data)} symbols processed", flush=True)
    return True

def main():
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 60)
    print("🐛 DIAGNÓSTICO PASO A PASO - IDENTIFICACIÓN DE CUELGUES")
    print("=" * 60)
    print("💡 Presiona Ctrl+C en cualquier momento para detener")
    print("📊 Cada paso tiene timeout de 30 segundos")
    print()

    # Lista de tests ordenados por complejidad
    tests = [
        ("Imports básicos", step_imports, 10),
        ("Configuración del sistema", step_system_config, 5),
        ("Fetch de datos único", step_single_fetch, 30),
        ("Fetch de datos múltiple", step_multiple_fetch, 60),
        ("Cálculo de indicadores", step_indicators, 30),
        ("Adición de nuevas features", step_new_features, 45),
        ("Pipeline completo de datos", step_data_processing, 120)
    ]

    results = []
    for test_name, test_func, timeout in tests:
        if interrupted:
            print("\n⚠️  Diagnóstico interrumpido por el usuario")
            break

        success = test_step(test_name, test_func, timeout)
        results.append((test_name, success))

        if not success:
            print(f"❌ FALLO en '{test_name}' - posible causa del cuelgue")
            break

    # Summary
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL DIAGNÓSTICO:")

    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)

    print(f"   • Tests completados: {successful_tests}/{total_tests}")

    if successful_tests == total_tests:
        print("   ✅ TODOS los tests pasaron - el cuelgue debe estar en training/cv")
    else:
        failed_test = next(test for test, success in results if not success)
        print(f"   ❌ El cuelgue está en: {failed_test}")

    if interrupted:
        print("   ⚠️  Diagnóstico interrumpido por el usuario")

    print("\n💡 RECOMENDACIONES:")
    if successful_tests >= 5:
        print("   • El problema está en el entrenamiento XGBoost o cross-validation")
        print("   • Verifica que tengas suficiente RAM (>4GB)")
        print("   • Intenta con --symbols 1 --candles 500")
    elif successful_tests >= 3:
        print("   • El problema está en el procesamiento de features")
        print("   • Verifica add_new_features.py")
    else:
        print("   • El problema está en la carga inicial")
        print("   • Verifica dependencias y conectividad")

    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Diagnóstico cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
