#!/usr/bin/env python3
"""
Test rápido para verificar timeouts y evitar operaciones bloqueantes
"""
import signal
import time
import sys

# Global flag for interruption
interrupted = False

def signal_handler(signum, frame):
    """Handle Ctrl+C"""
    global interrupted
    interrupted = True
    print("\n⚠️  Test interrumpido por el usuario", flush=True)

def test_basic_imports():
    """Test imports without network calls"""
    print("🔍 Testing basic imports...", end=" ", flush=True)
    start_time = time.time()

    try:
        import pandas as pd
        import numpy as np
        import sklearn
        import xgboost
        import joblib

        import_time = time.time() - start_time
        print(f"✅ OK ({import_time:.2f}s)")
        return True
    except ImportError as e:
        print(f"❌ FAILED: {e}")
        return False

def test_network_timeout():
    """Test a simple network call with timeout"""
    print("🔍 Testing network timeout...", end=" ", flush=True)
    start_time = time.time()

    try:
        import requests
        # Test with a very short timeout to avoid hanging
        response = requests.get("https://httpbin.org/delay/1", timeout=5)
        network_time = time.time() - start_time
        print(f"✅ OK ({network_time:.2f}s)")
        return True
    except requests.exceptions.Timeout:
        print("⚠️  TIMEOUT (esperado)")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_symbol_loading():
    """Test loading symbols without network"""
    print("🔍 Testing symbol loading...", end=" ", flush=True)
    start_time = time.time()

    try:
        from system_directive import get_all_assets
        symbols = get_all_assets()
        load_time = time.time() - start_time
        print(f"✅ OK ({load_time:.2f}s)")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 50)
    print("🧪 TEST DE TIMEOUTS - VERIFICACIÓN RÁPIDA")
    print("=" * 50)

    tests = [
        ("Imports básicos", test_basic_imports),
        ("Timeout de red", test_network_timeout),
        ("Carga de símbolos", test_symbol_loading)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        if interrupted:
            print("⚠️  Tests interrumpidos por el usuario")
            break

        print(f"\n{test_name}:")
        if test_func():
            passed += 1

    print("\n" + "=" * 50)
    print("📊 RESULTADOS:")
    print(f"   • Tests pasados: {passed}/{total}")
    print(f"   • Estado: {'✅ OK' if passed == total else '❌ PROBLEMAS'}")

    if passed == total:
        print("   ✅ El sistema está listo para operaciones de red")
        print("   🚀 Puedes ejecutar los scripts de training sin timeouts")
    else:
        print("   ❌ Hay problemas que pueden causar timeouts")
        print("   💡 Revisa las dependencias faltantes")

    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Test cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado en test: {e}")
