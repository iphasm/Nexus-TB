#!/usr/bin/env python3
"""
Test script to verify CCXT compatibility for conditional orders and trailing stops
"""

import asyncio
import ccxt.async_support as ccxt_async

async def test_ccxt_compatibility():
    """Test CCXT compatibility with conditional orders and trailing stops"""
    print("🧪 Testing CCXT Compatibility for Conditional Orders")
    print(f"📦 CCXT Version: {ccxt_async.__version__}")
    print("=" * 60)

    # Test Bybit
    print("\n📊 Testing Bybit Adapter:")
    try:
        exchange = ccxt_async.bybit({
            'apiKey': 'test',  # Won't make real calls
            'secret': 'test',
            'test': True,
            'enableRateLimit': True,
        })

        # Check if methods exist
        has_create_order = hasattr(exchange, 'create_order')
        has_trailing_stop = hasattr(exchange, 'create_trailing_stop_order')

        print(f"   ✅ create_order method: {'Available' if has_create_order else 'Missing'}")
        print(f"   ✅ create_trailing_stop_order method: {'Available' if has_trailing_stop else 'Missing'}")

        # Check supported order types
        if hasattr(exchange, 'order_types'):
            order_types = exchange.order_types
            conditional_types = [t for t in order_types if 'stop' in t.lower() or 'take' in t.lower() or 'trailing' in t.lower()]
            print(f"   📋 Conditional order types: {conditional_types}")

        await exchange.close()

    except Exception as e:
        print(f"   ❌ Bybit test failed: {e}")

    # Test Binance
    print("\n📊 Testing Binance Adapter:")
    try:
        exchange = ccxt_async.binance({
            'apiKey': 'test',
            'secret': 'test',
            'test': True,
            'enableRateLimit': True,
        })

        has_create_order = hasattr(exchange, 'create_order')
        has_trailing_stop = hasattr(exchange, 'create_trailing_stop_order')

        print(f"   ✅ create_order method: {'Available' if has_create_order else 'Missing'}")
        print(f"   ✅ create_trailing_stop_order method: {'Available' if has_trailing_stop else 'Missing'}")

        if hasattr(exchange, 'order_types'):
            order_types = exchange.order_types
            conditional_types = [t for t in order_types if 'stop' in t.lower() or 'take' in t.lower() or 'trailing' in t.lower()]
            print(f"   📋 Conditional order types: {conditional_types}")

        await exchange.close()

    except Exception as e:
        print(f"   ❌ Binance test failed: {e}")

    print("\n" + "=" * 60)
    print("✅ CCXT Compatibility Test Complete")
    print("\n💡 Recommendations:")
    print("   - Ensure CCXT >= 4.4.0 for full Bybit V5 support")
    print("   - Test conditional orders in staging before production")
    print("   - Monitor error codes: 110092, 110093, 110043")

if __name__ == "__main__":
    asyncio.run(test_ccxt_compatibility())
