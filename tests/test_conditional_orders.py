"""
Test Script: Verify Binance Conditional Orders
Tests the connection and fetches open conditional orders.
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

async def test_binance_conditional_orders():
    """Test Binance connection and fetch conditional orders."""
    import ccxt.async_support as ccxt
    
    api_key = os.getenv('BINANCE_API_KEY', '').strip().strip("'\"")
    api_secret = os.getenv('BINANCE_SECRET', '').strip().strip("'\"")
    proxy = os.getenv('PROXY_URL', '')
    
    if not api_key or not api_secret:
        print("❌ Missing BINANCE_API_KEY or BINANCE_SECRET in .env")
        return
    
    print(f"🔑 Using key: {api_key[:4]}...{api_key[-4:]}")
    print(f"🔄 Proxy: {'Yes' if proxy else 'No'}")
    
    # Create exchange
    exchange = ccxt.binanceusdm({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    # Set proxy for async
    if proxy:
        exchange.aiohttp_proxy = proxy
    
    try:
        # 1. Test Connection
        print("\n--- Step 1: Load Markets ---")
        await exchange.load_markets()
        print("✅ Markets loaded OK")
        
        # 2. Test Auth (Fetch Balance)
        print("\n--- Step 2: Fetch Balance ---")
        balance = await exchange.fetch_balance()
        usdt = balance.get('USDT', {})
        print(f"✅ Balance: {usdt.get('total', 0):.2f} USDT (Available: {usdt.get('free', 0):.2f})")
        
        # 3. Fetch Open Positions
        print("\n--- Step 3: Fetch Positions ---")
        positions = await exchange.fetch_positions()
        active = [p for p in positions if abs(float(p.get('contracts', 0))) > 0]
        if active:
            for p in active:
                print(f"📊 Position: {p['symbol']} | Side: {p['side']} | Size: {p['contracts']} | Entry: {p['entryPrice']}")
        else:
            print("📭 No active positions")
        
        # 4. Fetch Open Orders (includes conditional since Dec 2024)
        print("\n--- Step 4: Fetch Open Orders ---")
        # For each active position, check orders
        symbols_to_check = [p['symbol'] for p in active] if active else ['BTC/USDT:USDT', 'ETH/USDT:USDT']
        
        for symbol in symbols_to_check:
            orders = await exchange.fetch_open_orders(symbol)
            if orders:
                print(f"\n📋 Orders for {symbol}:")
                for o in orders:
                    order_type = o.get('type', 'UNKNOWN')
                    stop_price = o.get('stopPrice') or o.get('info', {}).get('stopPrice', 'N/A')
                    print(f"   • {order_type.upper()} | Side: {o['side']} | Qty: {o['amount']} | Trigger: {stop_price}")
            else:
                print(f"📭 No open orders for {symbol}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await exchange.close()

if __name__ == '__main__':
    asyncio.run(test_binance_conditional_orders())
