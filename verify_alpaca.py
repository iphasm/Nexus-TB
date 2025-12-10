
import os
import sys
from dotenv import load_dotenv

# Load Env
load_dotenv()

ak = os.getenv('APCA_API_KEY_ID')
ask = os.getenv('APCA_API_SECRET_KEY')
base_url = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')

print(f"🔑 Checking Keys...")
print(f"Key: {'*' * 4 + ak[-4:] if ak else 'MISSING'}")
print(f"Secret: {'*' * 4 + ask[-4:] if ask else 'MISSING'}")
print(f"URL: {base_url}")

if not ak or not ask:
    print("❌ Keys Missing in Environment.")
    sys.exit(1)

try:
    print("\n📡 Connecting to Alpaca Trading API...")
    from alpaca.trading.client import TradingClient
    
    paper = 'paper' in base_url
    client = TradingClient(ak, ask, paper=paper)
    
    acct = client.get_account()
    print(f"✅ Connection Success!")
    print(f"   Status: {acct.status}")
    print(f"   Equity: ${float(acct.equity):,.2f}")
    print(f"   Buying Power: ${float(acct.buying_power):,.2f}")
    
except Exception as e:
    print(f"❌ Trading API Connection Failed: {e}")

try:
    print("\n📈 Testing Data API (Alpaca Data)...")
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from datetime import datetime, timedelta

    data_client = StockHistoricalDataClient(ak, ask)
    
    req = StockBarsRequest(
        symbol_or_symbols='GLD', # Gold ETF
        timeframe=TimeFrame.Day,
        start=datetime.utcnow() - timedelta(days=5),
        limit=5
    )
    
    bars = data_client.get_stock_bars(req)
    if not bars.df.empty:
        print(f"✅ Data Fetch Success (GLD): {len(bars.df)} bars")
        print(bars.df.tail(2))
    else:
        print("⚠️ Data Fetch returned empty.")

except Exception as e:
    print(f"❌ Data API Error: {e}")
