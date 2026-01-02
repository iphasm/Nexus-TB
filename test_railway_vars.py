#!/usr/bin/env python3
"""
Test script to verify Railway environment variables detection.
"""

import os
import sys

def test_railway_variables():
    """Test Railway environment variable detection."""

    print("🚂 TEST: VERIFICACIÓN DE VARIABLES RAILWAY")
    print("=" * 50)

    # Check all Railway variables
    railway_vars = [
        'RAILWAY_BINANCE_API_KEY',
        'RAILWAY_BINANCE_API_SECRET',
        'RAILWAY_BYBIT_API_KEY',
        'RAILWAY_BYBIT_API_SECRET',
        'RAILWAY_ALPACA_API_KEY',
        'RAILWAY_ALPACA_API_SECRET',
        'TELEGRAM_SUPEROWNER_ID'
    ]

    print("\n🔑 VARIABLES DE ENTORNO RAILWAY:")
    for var in railway_vars:
        value = os.getenv(var)
        exists = bool(value)
        masked_value = f"***{str(value)[-4:]}" if value and len(str(value)) > 4 else str(value) if value else "NOT SET"
        print(f"  {'✅' if exists else '❌'} {var}: {masked_value}")

    # Check standard env vars too
    print("\n🔑 VARIABLES DE ENTORNO ESTÁNDAR:")
    standard_vars = [
        'BINANCE_API_KEY',
        'BINANCE_API_SECRET',
        'BYBIT_API_KEY',
        'BYBIT_API_SECRET',
        'ALPACA_API_KEY',
        'ALPACA_API_SECRET'
    ]

    for var in standard_vars:
        value = os.getenv(var)
        exists = bool(value)
        masked_value = f"***{str(value)[-4:]}" if value and len(str(value)) > 4 else str(value) if value else "NOT SET"
        print(f"  {'✅' if exists else '❌'} {var}: {masked_value}")

    # Test the detection logic (simulate get_configured_exchanges)
    print("\n🏦 SIMULACIÓN DE DETECCIÓN DE EXCHANGES:")
    print("(Esta es la lógica que usa el bot)")

    configured = {}

    # Railway vars
    railway_binance_key = os.getenv('RAILWAY_BINANCE_API_KEY')
    railway_binance_secret = os.getenv('RAILWAY_BINANCE_API_SECRET')
    railway_bybit_key = os.getenv('RAILWAY_BYBIT_API_KEY')
    railway_bybit_secret = os.getenv('RAILWAY_BYBIT_API_SECRET')
    railway_alpaca_key = os.getenv('RAILWAY_ALPACA_API_KEY')
    railway_alpaca_secret = os.getenv('RAILWAY_ALPACA_API_SECRET')

    # Check Binance
    binance_key = (os.getenv('BINANCE_API_KEY') or railway_binance_key)
    binance_secret = (os.getenv('BINANCE_API_SECRET') or railway_binance_secret)
    configured['BINANCE'] = bool(binance_key and binance_secret)

    # Check Bybit
    bybit_key = (os.getenv('BYBIT_API_KEY') or railway_bybit_key)
    bybit_secret = (os.getenv('BYBIT_API_SECRET') or railway_bybit_secret)
    configured['BYBIT'] = bool(bybit_key and bybit_secret)

    # Check Alpaca
    alpaca_key = (os.getenv('ALPACA_API_KEY') or railway_alpaca_key)
    alpaca_secret = (os.getenv('ALPACA_API_SECRET') or railway_alpaca_secret)
    configured['ALPACA'] = bool(alpaca_key and alpaca_secret)

    print(f"  {'✅' if configured['BINANCE'] else '❌'} BINANCE: {'Configurado' if configured['BINANCE'] else 'No configurado'}")
    print(f"  {'✅' if configured['BYBIT'] else '❌'} BYBIT: {'Configurado' if configured['BYBIT'] else 'No configurado'}")
    print(f"  {'✅' if configured['ALPACA'] else '❌'} ALPACA: {'Configurado' if configured['ALPACA'] else 'No configurado'}")

    print("\n💡 CONCLUSIONES:")
    if not configured['BINANCE']:
        print("  ⚠️ BINANCE no está configurado.")
        print("  🔍 Verifica que RAILWAY_BINANCE_API_KEY y RAILWAY_BINANCE_API_SECRET estén configuradas.")
        print("  🔍 O usa BINANCE_API_KEY y BINANCE_API_SECRET como variables estándar.")
    else:
        print("  ✅ BINANCE está correctamente configurado.")

    if not configured['BYBIT']:
        print("  ⚠️ BYBIT no está configurado.")
    else:
        print("  ✅ BYBIT está correctamente configurado.")

    if not configured['ALPACA']:
        print("  ⚠️ ALPACA no está configurado.")
    else:
        print("  ✅ ALPACA está correctamente configurado.")

if __name__ == "__main__":
    test_railway_variables()