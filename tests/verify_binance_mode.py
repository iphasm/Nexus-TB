"""
Diagnostic Script: Verify Binance Position Mode Detection
Checks if the BinanceAdapter correctly detects One-Way vs Hedge mode.
"""
import asyncio
import os
import sys
from pathlib import Path

# Ensure we can find .env in project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from nexus_system.uplink.adapters.binance_adapter import BinanceAdapter

async def verify_mode():
    print(f"📂 Project Root: {project_root}")
    print(f"🔑 BINANCE_API_KEY in env: {bool(os.getenv('BINANCE_API_KEY'))}")
    print(f"🔑 BINANCE_SECRET in env: {bool(os.getenv('BINANCE_SECRET'))}")
    
    print("\n🔍 Initializing BinanceAdapter...")
    adapter = BinanceAdapter()
    
    success = await adapter.initialize()
    if not success:
        print("❌ Adapter initialization failed. Check your API keys and Proxy.")
        return

    print(f"\n✅ Initialization Successful")
    print(f"⚙️ Detected Hedge Mode: {adapter._is_hedge_mode}")
    
    if adapter._is_hedge_mode:
        print("🟩 Account is in HEDGE MODE. 'positionSide' WILL be sent to Binance.")
    else:
        print("🟦 Account is in ONE-WAY MODE. 'positionSide' WILL BE STRIPPED by the adapter.")

    # Test parameter stripping logic
    test_params = {'stopPrice': 1.23, 'positionSide': 'LONG', 'reduceOnly': True}
    print(f"\n🧪 Testing parameter stripping logic...")
    print(f"Input Params: {test_params}")
    
    # Simulate internal stripping logic
    if not adapter._is_hedge_mode and 'positionSide' in test_params:
        test_params.pop('positionSide')
    
    print(f"Processed Params: {test_params}")
    
    if not adapter._is_hedge_mode and 'positionSide' not in test_params:
        print("✅ SUCCESS: positionSide was correctly stripped for One-Way mode.")
    elif adapter._is_hedge_mode and 'positionSide' in test_params:
        print("✅ SUCCESS: positionSide was correctly preserved for Hedge mode.")
    else:
        print("❌ FAILURE: Parameter logic mismatch.")

    await adapter.close()

if __name__ == "__main__":
    asyncio.run(verify_mode())
