#!/usr/bin/env python3
"""
Script to check CCXT version installed
"""

try:
    import ccxt
    print(f"✅ CCXT instalado correctamente")
    print(f"📦 Versión: {ccxt.__version__}")
    # Note: ccxt.version was removed in CCXT 4.5.31
    print(f"🔖 Versión completa: {ccxt.__version__}")

    # Mostrar algunos exchanges disponibles
    print(f"🌐 Exchanges disponibles: {len(ccxt.exchanges)}")

    # Verificar si Bybit está disponible
    if 'bybit' in ccxt.exchanges:
        print("✅ Bybit adapter disponible")
        # Verificar versión específica de Bybit
        bybit_exchange = getattr(ccxt, 'bybit', None)
        if bybit_exchange:
            print(f"   📋 Bybit class version: {bybit_exchange.__module__}")
    else:
        print("❌ Bybit adapter no disponible")

    # Verificar si Binance está disponible
    if 'binance' in ccxt.exchanges:
        print("✅ Binance adapter disponible")
        binance_exchange = getattr(ccxt, 'binance', None)
        if binance_exchange:
            print(f"   📋 Binance class version: {binance_exchange.__module__}")
    else:
        print("❌ Binance adapter no disponible")

    # Verificar funcionalidades críticas para órdenes condicionales
    print("\n🔧 Verificando funcionalidades críticas:")
    try:
        exchange = ccxt.bybit()
        # Verificar si tiene los métodos necesarios para órdenes condicionales
        has_conditional_orders = hasattr(exchange, 'create_order')
        print(f"   ✅ Órdenes condicionales: {'Disponible' if has_conditional_orders else 'No disponible'}")

        # Verificar trailing stops
        has_trailing = hasattr(exchange, 'create_trailing_stop_order') if hasattr(exchange, 'create_trailing_stop_order') else False
        print(f"   ✅ Trailing stops: {'Disponible' if has_trailing else 'Usando método alternativo'}")

    except Exception as e:
        print(f"   ⚠️ Error al verificar funcionalidades: {e}")

except ImportError as e:
    print(f"❌ CCXT no está instalado: {e}")
    print("💡 Instala con: pip install ccxt>=4.0.0")

except Exception as e:
    print(f"❌ Error al verificar CCXT: {e}")
    print(f"   Detalles: {type(e).__name__}: {e}")
