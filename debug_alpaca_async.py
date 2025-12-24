
import asyncio
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

load_dotenv()

async def test_alpaca_fetch():
    print("🧪 Starting Alpaca Data Fetch Test...")
    
    from antigravity_quantum.data.stream import MarketStream
    stream = MarketStream()
    
    # Inject keys manually or via env
    ak = os.getenv('APCA_API_KEY_ID')
    ask = os.getenv('APCA_API_SECRET_KEY')
    
    if not ak or not ask:
        print("❌ No Alpaca Keys found in ENV.")
        return

    print(f"🔑 Using Keys: {ak[:4]}... / {ask[:4]}...")
    await stream.initialize(alpaca_key=ak, alpaca_secret=ask)
    
    if not stream.alpaca:
        print("❌ Stream failed to initialize Alpaca module.")
        return

    symbol = "TSLA"
    print(f"📡 Fetching {symbol} data...")
    
    try:
        # Test standard get_candles
        data = await stream.get_candles(symbol, limit=50)
        df = data.get('dataframe')
        
        if df is None or df.empty:
            print(f"❌ DataFrame is empty for {symbol}")
        else:
            print(f"✅ Data for {symbol} received!")
            print(f"   Rows: {len(df)}")
            print(f"   Columns: {df.columns.tolist()}")
            print(f"   Last Close: {df.iloc[-1]['close']}")
            print(f"   Timeframe: {data.get('timeframe')}")
            print(f"   Indicators: {'rsi' in df.columns}")

            # Debug timestamps
            print(f"   Timestamp Type: {type(df.iloc[-1]['timestamp'])}")
            print(f"   Sample Timestamp: {df.iloc[-1]['timestamp']}")

    except Exception as e:
        print(f"❌ Exception during fetch: {e}")
        import traceback
        traceback.print_exc()
    
    await stream.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_alpaca_fetch())
