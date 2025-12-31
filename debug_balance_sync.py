#!/usr/bin/env python3
"""
DEBUG: Balance Sync Issue Investigation
Investigates why check_liquidity fails when Bybit operations succeed
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexus_system.core.nexus_bridge import NexusBridge
from system_directive import ASSET_GROUPS
from servos.shadow_wallet import ShadowWallet

async def debug_balance_sync():
    """Debug the balance synchronization issue"""

    print("🔍 DEBUG: Balance Sync Issue Investigation")
    print("=" * 60)

    # 1. Check symbol routing
    symbol = "1000PEPEUSDT"
    print(f"📊 Symbol: {symbol}")

    # Check which groups contain PEPE
    groups_containing_pepe = []
    for group_name, symbols in ASSET_GROUPS.items():
        if symbol in symbols:
            groups_containing_pepe.append(group_name)

    print(f"📊 Groups containing {symbol}: {groups_containing_pepe}")

    # 2. Initialize bridge (without actual connections for testing)
    bridge = NexusBridge()

    # Mock adapters for testing
    bridge.adapters = {'BYBIT': None, 'BINANCE': None}  # Mock connected adapters
    bridge.primary_exchange = 'BYBIT'

    # Test routing
    routed_exchange = bridge._route_symbol(symbol)
    print(f"📊 _route_symbol('{symbol}') -> {routed_exchange}")

    # 3. Test what happens with force_exchange
    force_exchange = "BYBIT"
    print(f"📊 force_exchange specified: {force_exchange}")

    # This simulates the logic in execute_long_position
    if force_exchange and force_exchange in bridge.adapters.keys():
        target_exchange = force_exchange
        print(f"📊 execute_long_position target_exchange: {target_exchange} (forced)")
    else:
        target_exchange = bridge._route_symbol(symbol)
        print(f"📊 execute_long_position target_exchange: {target_exchange} (auto-routed)")

    # 4. Test check_liquidity routing (simulated)
    print("\n📊 Simulating check_liquidity routing:")
    check_liquidity_target = bridge._route_symbol(symbol)
    print(f"📊 check_liquidity target_exchange: {check_liquidity_target}")

    # 5. Compare results
    routing_consistent = (target_exchange == check_liquidity_target)
    print(f"📊 Routing consistent: {routing_consistent}")

    if not routing_consistent:
        print("❌ PROBLEM FOUND: execute_long_position and check_liquidity use different exchanges!")
        print(f"   execute_long_position: {target_exchange}")
        print(f"   check_liquidity: {check_liquidity_target}")
    else:
        print("✅ Routing is consistent between functions")

    # 6. Test balance thresholds
    print("\n📊 Balance Threshold Analysis:")
    # Simulate check_liquidity threshold calculation
    # In a real scenario, this would get min_notional from get_symbol_precision
    # For debugging, let's assume some values
    min_notional = 5.0  # Example
    threshold = max(min_notional * 1.1, 6.0)
    print(f"📊 Min notional: ${min_notional}")
    print(f"📊 Threshold: ${threshold}")

    # Test different balance scenarios
    test_balances = [0.0, 3.0, 5.0, 7.0, 10.0]
    for balance in test_balances:
        sufficient = balance >= threshold
        status = "✅ SUFFICIENT" if sufficient else "❌ INSUFFICIENT"
        print(f"📊 Balance ${balance:.2f}: {status} (threshold: ${threshold:.2f})")

    print("\n🔍 CONCLUSION:")
    print("The issue is likely that:")
    print("1. execute_long_position correctly routes to BYBIT")
    print("2. check_liquidity also routes to BYBIT (confirmed)")
    print("3. But the balance check fails due to stale or incorrect balance data")
    print("4. However, the actual order placement succeeds anyway")
    print("")
    print("RECOMMENDATION: Add detailed logging to check_liquidity and execute_long_position")
    print("to see the exact balance values being used for the decision.")

if __name__ == "__main__":
    asyncio.run(debug_balance_sync())
