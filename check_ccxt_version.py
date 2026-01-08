#!/usr/bin/env python3
"""
Script to check CCXT version installed
"""

try:
    import ccxt
    print(f"✅ CCXT instalado correctamente")
    print(f"📦 Versión: {ccxt.__version__}")
    print(f"🔖 Versión completa: {ccxt.version}")

    # Mostrar algunos exchanges disponibles
    print(f"🌐 Exchanges disponibles: {len(ccxt.exchanges)}")

    # Verificar si Bybit está disponible
    if 'bybit' in ccxt.exchanges:
        print("✅ Bybit adapter disponible")
    else:
        print("❌ Bybit adapter no disponible")

    # Verificar si Binance está disponible
    if 'binance' in ccxt.exchanges:
        print("✅ Binance adapter disponible")
    else:
        print("❌ Binance adapter no disponible")

except ImportError as e:
    print(f"❌ CCXT no está instalado: {e}")
    print("💡 Instala con: pip install ccxt>=4.0.0")

except Exception as e:
    print(f"❌ Error al verificar CCXT: {e}")
    print(f"   Detalles: {type(e).__name__}: {e}")
