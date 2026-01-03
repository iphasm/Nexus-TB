#!/usr/bin/env python3
"""
Test script for user data isolation in ShadowWallet
Ensures balances and positions don't leak between users
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from nexus_system.core.shadow_wallet import ShadowWallet

async def test_user_isolation():
    """Test that user data is properly isolated."""

    print("🧪 Testing User Data Isolation")
    print("=" * 50)

    # Create ShadowWallet instance
    wallet = ShadowWallet()

    # Test data for different users
    user1_id = "123456789"
    user2_id = "987654321"

    print("👤 Testing User 1 data...")

    # User 1 updates
    wallet.update_balance(user1_id, 'BINANCE', {'total': 1000.0, 'available': 800.0})
    wallet.update_balance(user1_id, 'BYBIT', {'total': 500.0, 'available': 400.0})
    wallet.update_position(user1_id, 'BTCUSDT', {
        'symbol': 'BTCUSDT',
        'side': 'LONG',
        'quantity': 1.0,
        'entryPrice': 50000.0,
        'unrealizedPnl': 100.0,
        'leverage': 5,
        'exchange': 'BINANCE'
    })

    print("👤 Testing User 2 data...")

    # User 2 updates (different data)
    wallet.update_balance(user2_id, 'BINANCE', {'total': 2000.0, 'available': 1500.0})
    wallet.update_balance(user2_id, 'ALPACA', {'total': 3000.0, 'available': 2500.0})
    wallet.update_position(user2_id, 'ETHUSDT', {
        'symbol': 'ETHUSDT',
        'side': 'SHORT',
        'quantity': 2.0,
        'entryPrice': 3000.0,
        'unrealizedPnl': -50.0,
        'leverage': 3,
        'exchange': 'BYBIT'
    })

    # Verify isolation
    print("\n🔍 Verification Results:")
    print("-" * 30)

    # Check User 1 data
    user1_wallet = wallet._get_user_wallet(user1_id)
    user1_binance_bal = user1_wallet['balances']['BINANCE']
    user1_bybit_bal = user1_wallet['balances']['BYBIT']
    user1_positions = user1_wallet['positions']

    print(f"👤 User 1 ({user1_id}):")
    print(f"   BINANCE: ${user1_binance_bal['total']:.0f} total, ${user1_binance_bal['available']:.0f} available")
    print(f"   BYBIT: ${user1_bybit_bal['total']:.0f} total, ${user1_bybit_bal['available']:.0f} available")
    print(f"   Positions: {list(user1_positions.keys())}")

    # Check User 2 data
    user2_wallet = wallet._get_user_wallet(user2_id)
    user2_binance_bal = user2_wallet['balances']['BINANCE']
    user2_alpaca_bal = user2_wallet['balances']['ALPACA']
    user2_positions = user2_wallet['positions']

    print(f"👤 User 2 ({user2_id}):")
    print(f"   BINANCE: ${user2_binance_bal['total']:.0f} total, ${user2_binance_bal['available']:.0f} available")
    print(f"   ALPACA: ${user2_alpaca_bal['total']:.0f} total, ${user2_alpaca_bal['available']:.0f} available")
    print(f"   Positions: {list(user2_positions.keys())}")

    # Verify no cross-contamination
    checks = [
        ("User 1 BINANCE total", user1_binance_bal['total'], 1000.0),
        ("User 1 BYBIT total", user1_bybit_bal['total'], 500.0),
        ("User 1 positions", len(user1_positions), 1),
        ("User 1 BTC position", 'BTCUSDT' in user1_positions, True),

        ("User 2 BINANCE total", user2_binance_bal['total'], 2000.0),
        ("User 2 ALPACA total", user2_alpaca_bal['total'], 3000.0),
        ("User 2 positions", len(user2_positions), 1),
        ("User 2 ETH position", 'ETHUSDT' in user2_positions, True),

        # Cross-contamination checks (check if balance is still zero)
        ("User 1 has no ALPACA balance", user1_wallet['balances'].get('ALPACA', {}).get('total', 0), 0.0),
        ("User 2 has no BYBIT balance", user2_wallet['balances'].get('BYBIT', {}).get('total', 0), 0.0),
        ("User 1 has no ETH position", 'ETHUSDT' not in user1_positions, True),
        ("User 2 has no BTC position", 'BTCUSDT' not in user2_positions, True),
    ]

    print("\n✅ Validation Checks:")
    all_passed = True

    for description, actual, expected in checks:
        status = "✅" if actual == expected else "❌"
        print(f"   {status} {description}: {actual}")
        if actual != expected:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 USER ISOLATION TEST PASSED!")
        print("✅ No data leakage between users")
        print("✅ Balances properly isolated")
        print("✅ Positions properly isolated")
        print("✅ Dashboard data integrity maintained")
    else:
        print("❌ USER ISOLATION TEST FAILED!")
        print("🔍 Data contamination detected")
        print("🚨 Critical security issue - fix immediately!")

    print("=" * 50)

    # Test unified equity calculation
    user1_equity = wallet.get_unified_equity(user1_id)
    user2_equity = wallet.get_unified_equity(user2_id)

    print("\n💰 Equity Calculations:")
    print(".2f")
    print(".2f")
    expected_user1 = 1000.0 + 500.0  # BINANCE + BYBIT
    expected_user2 = 2000.0 + 3000.0  # BINANCE + ALPACA

    equity_checks = [
        ("User 1 equity", user1_equity, expected_user1),
        ("User 2 equity", user2_equity, expected_user2),
    ]

    for description, actual, expected in equity_checks:
        status = "✅" if abs(actual - expected) < 0.01 else "❌"
        print(f"   {status} {description}: ${actual:.2f} (expected: ${expected:.2f})")

    return all_passed

async def main():
    """Main test function."""
    await test_user_isolation()

if __name__ == "__main__":
    asyncio.run(main())
