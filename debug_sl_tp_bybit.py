#!/usr/bin/env python3
"""
DEBUG: SL/TP Orders in Bybit
Diagnose why Stop Loss and Take Profit orders are failing in Bybit
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexus_system.core.nexus_bridge import NexusBridge

async def debug_sl_tp_bybit():
    """Debug SL/TP order placement issues in Bybit"""

    print("🔍 DEBUG: SL/TP Orders in Bybit")
    print("=" * 60)

    # Initialize bridge
    bridge = NexusBridge()

    # Check if Bybit adapter is available
    if 'BYBIT' not in bridge.adapters:
        print("❌ Bybit adapter not initialized")
        return

    bybit_adapter = bridge.adapters['BYBIT']
    print("✅ Bybit adapter found")

    # Test parameters - using PEPE as example
    symbol = "1000PEPEUSDT"
    side = "SELL"  # For closing LONG position
    quantity = 100.0  # Small test quantity
    entry_price = 0.0100  # Example entry price
    sl_price = 0.0095  # Example SL price (below entry for LONG)
    tp_price = 0.0110  # Example TP price (above entry for LONG)

    print(f"📊 Test Parameters:")
    print(f"   Symbol: {symbol}")
    print(f"   Entry Price: ${entry_price}")
    print(f"   SL Price: ${sl_price}")
    print(f"   TP Price: ${tp_price}")
    print(f"   Quantity: {quantity}")

    # Test 1: SL Order
    print("\n🛑 Testing SL Order (STOP_MARKET):")
    try:
        sl_result = await bridge.place_order(
            symbol, side, 'STOP_MARKET',
            quantity=quantity, price=sl_price, reduceOnly=True
        )
        if sl_result.get('error'):
            print(f"❌ SL Order Failed: {sl_result['error']}")
        else:
            print(f"✅ SL Order Placed: {sl_result}")
    except Exception as e:
        print(f"❌ SL Order Exception: {e}")

    # Test 2: TP Order
    print("\n🎯 Testing TP Order (TAKE_PROFIT_MARKET):")
    try:
        tp_result = await bridge.place_order(
            symbol, side, 'TAKE_PROFIT_MARKET',
            quantity=quantity, price=tp_price, reduceOnly=True
        )
        if tp_result.get('error'):
            print(f"❌ TP Order Failed: {tp_result['error']}")
        else:
            print(f"✅ TP Order Placed: {tp_result}")
    except Exception as e:
        print(f"❌ TP Order Exception: {e}")

    # Test 3: Check symbol info
    print("\n📊 Checking Symbol Info:")
    try:
        symbol_info = await bridge.get_symbol_info(symbol)
        if symbol_info:
            print(f"✅ Symbol Info: {symbol_info}")
        else:
            print(f"❌ No symbol info available")
    except Exception as e:
        print(f"❌ Symbol Info Error: {e}")

    # Test 4: Check current price
    print("\n💰 Checking Current Price:")
    try:
        current_price = await bridge.get_last_price(symbol)
        print(f"✅ Current Price: ${current_price}")
    except Exception as e:
        print(f"❌ Price Fetch Error: {e}")

    print("\n🔍 POSSIBLE ISSUES:")
    print("1. Invalid trigger prices (too close to current price)")
    print("2. reduceOnly=True not supported for conditional orders")
    print("3. Incorrect order type mapping for Bybit")
    print("4. Missing required parameters for Bybit API")
    print("5. Position not open yet when placing conditional orders")

if __name__ == "__main__":
    asyncio.run(debug_sl_tp_bybit())
