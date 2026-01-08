#!/usr/bin/env python3
"""
Test script to verify Bybit leverage limits handling
"""

import asyncio
from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter

async def test_leverage_limits():
    """Test leverage limits functionality"""
    adapter = BybitAdapter()

    # Test symbols with different expected leverage limits
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'PONKEUSDT']

    print("🧪 Testing Bybit leverage limits...")

    for symbol in test_symbols:
        try:
            limits = await adapter.get_leverage_limits(symbol)
            print(f"📊 {symbol}: Min={limits['min']}x, Max={limits['max']}x")
        except Exception as e:
            print(f"❌ Error getting limits for {symbol}: {e}")

if __name__ == "__main__":
    asyncio.run(test_leverage_limits())
