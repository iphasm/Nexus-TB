#!/usr/bin/env python3
"""
Debug script para probar el entrenamiento ML paso a paso
"""
import sys
import time

print("=" * 50, flush=True)
print("🐛 DEBUG - NEXUS CORTEX ML TRAINING", flush=True)
print("=" * 50, flush=True)
print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
print(f"🐍 Python: {sys.version.split()[0]}", flush=True)
print("", flush=True)

def test_step(step_name, test_func):
    print(f"🔍 Testing: {step_name}...", flush=True)
    try:
        result = test_func()
        print(f"✅ {step_name}: OK", flush=True)
        return True
    except Exception as e:
        print(f"❌ {step_name}: FAILED - {e}", flush=True)
        return False

def test_imports():
    print("  Testing pandas...", flush=True)
    import pandas as pd
    print(f"  pandas version: {pd.__version__}", flush=True)

    print("  Testing numpy...", flush=True)
    import numpy as np
    print(f"  numpy version: {np.__version__}", flush=True)

    print("  Testing xgboost...", flush=True)
    import xgboost
    print(f"  xgboost version: {xgboost.__version__}", flush=True)

    print("  Testing binance...", flush=True)
    from binance.client import Client

    print("  Testing system_directive...", flush=True)
    from system_directive import get_all_assets, is_crypto

def test_config():
    from system_directive import get_all_assets, is_crypto
    symbols = get_all_assets()
    print(f"  Total symbols: {len(symbols)}", flush=True)
    print(f"  First 5 symbols: {symbols[:5]}", flush=True)

    # Test crypto detection
    test_symbol = "BTCUSDT"
    is_crypto_result = is_crypto(test_symbol)
    print(f"  {test_symbol} is crypto: {is_crypto_result}", flush=True)

def test_data_fetch():
    from src.ml.train_cortex import fetch_data
    from system_directive import is_crypto
    import time

    # Test symbols from different sources
    test_symbols = [
        ("BTCUSDT", "Binance Crypto"),
        ("ETHUSDT", "Binance Crypto"),
        ("AAPL", "Yahoo Finance Stock"),
        ("SPY", "Yahoo Finance ETF")
    ]

    print(f"  Testing data fetch for {len(test_symbols)} symbols (50 candles each)...", flush=True)
    print("", flush=True)

    successful_fetches = 0

    for symbol, source in test_symbols:
        start_time = time.time()
        print(f"  📊 Testing {symbol} ({source})...", flush=True)

        try:
            df = fetch_data(symbol, max_candles=50, verbose=True)

            if df is not None and not df.empty:
                fetch_time = time.time() - start_time
                print(f"    ✅ {symbol}: {len(df)} filas en {fetch_time:.2f}s", flush=True)

                # Show date range
                if 'timestamp' in df.columns:
                    try:
                        min_date = df['timestamp'].min()
                        max_date = df['timestamp'].max()
                        print(f"       📅 Rango: {min_date} → {max_date}", flush=True)
                    except:
                        print("       ⚠️  Error mostrando rango de fechas", flush=True)

                # Show basic stats
                if 'close' in df.columns:
                    try:
                        last_price = df['close'].iloc[-1]
                        print(f"       💰 Último precio: {last_price:.4f}", flush=True)
                    except:
                        print("       ⚠️  Error obteniendo precio", flush=True)

                successful_fetches += 1
            else:
                print(f"    ❌ {symbol}: Sin datos retornados", flush=True)
                print("       💡 Posibles causas: Símbolo inválido, sin datos históricos, error de API", flush=True)

        except Exception as e:
            fetch_time = time.time() - start_time
            print(f"    ❌ {symbol}: Error después de {fetch_time:.2f}s - {str(e)}", flush=True)

            # Specific error guidance
            if "API" in str(e).upper() or "RATE" in str(e).upper():
                print("       💡 Posible rate limiting o problema de conectividad API", flush=True)
            elif "TIMEOUT" in str(e).upper():
                print("       💡 Timeout de conexión - verificar internet", flush=True)
            elif "CERTIFICATE" in str(e).upper():
                print("       💡 Problema de certificado SSL", flush=True)

        print("", flush=True)

    # Summary
    success_rate = successful_fetches / len(test_symbols) * 100
    print(f"  📈 Resultado: {successful_fetches}/{len(test_symbols)} símbolos exitosos ({success_rate:.0f}%)", flush=True)

    if successful_fetches == 0:
        raise Exception("❌ Todos los fetches fallaron - problema crítico de conectividad")
    elif successful_fetches < len(test_symbols):
        print("  ⚠️  Algunos símbolos fallaron - posible problema parcial de conectividad", flush=True)
    else:
        print("  ✅ Todos los fetches exitosos - conectividad OK", flush=True)

# Run all tests
print("🚀 Iniciando pruebas de diagnóstico...", flush=True)
print("", flush=True)

all_passed = True

all_passed &= test_step("Importaciones de librerías", test_imports)
print("", flush=True)

all_passed &= test_step("Configuración del sistema", test_config)
print("", flush=True)

all_passed &= test_step("Descarga de datos de prueba", test_data_fetch)
print("", flush=True)

if all_passed:
    print("🎉 Todas las pruebas pasaron exitosamente!", flush=True)
    print("✅ El sistema está listo para entrenamiento completo", flush=True)
else:
    print("❌ Algunas pruebas fallaron. Revisa los errores arriba.", flush=True)

print("", flush=True)
print("=" * 50, flush=True)
input("Presiona Enter para salir...")
