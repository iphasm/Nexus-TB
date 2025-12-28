import asyncio
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from nexus_system.uplink.stream import MarketStream

async def verify():
    print("🔹 Initializing MarketStream (REST Only)...")
    stream = MarketStream(use_websocket=False)
    # Initialize implementation might need to load markets
    await stream.initialize() 
    
    symbol = 'BTCUSDT'
    print(f"🔹 Fetching Multiframe candles for {symbol}...")
    
    try:
        # This calls the method I modified
        data = await stream.get_multiframe_candles(symbol, limit=10)
        
        print(f"Keys returned: {list(data.keys())}")
        
        if 'micro' in data:
            df = data['micro']['dataframe']
            print(f"Micro Dataframe Shape: {df.shape}")
            if not df.empty:
                print("First 3 rows:")
                print(df[['timestamp', 'close', 'volume']].head(3))
                
                # Verify 1m diff
                if len(df) > 1:
                    diff = df['timestamp'].iloc[1] - df['timestamp'].iloc[0]
                    print(f"⏱️ Time delta: {diff}")
                    if diff == pd.Timedelta(minutes=1):
                        print("✅ SUCCESS: Interval is exactly 1 minute.")
                    else:
                        print(f"❌ FAILURE: Interval is {diff}, expected 0 days 00:01:00")
            else:
                print("❌ ERROR: Micro dataframe is empty.")
        else:
            print("❌ ERROR: 'micro' key missing in response.")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

    await stream.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())
