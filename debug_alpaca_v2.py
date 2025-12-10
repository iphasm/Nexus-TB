
import os
from alpaca.trading.client import TradingClient
from alpaca.common.exceptions import APIError

# Simulate User's potentially problematic config
# We will use the keys from env, but FORCE the URL to have /v2 as they requested
ak = os.getenv('APCA_API_KEY_ID')
ask = os.getenv('APCA_API_SECRET_KEY')
base_url_bad = "https://paper-api.alpaca.markets/v2"

print(f"🛠️ Testing with Base URL: {base_url_bad}")

if not ak or not ask:
    print("❌ Keys missing.")
    exit()

try:
    print("1. Init Client with /v2...")
    client = TradingClient(ak, ask, url_override=base_url_bad)
    
    print("2. Attempting get_account()...")
    acct = client.get_account()
    print("✅ get_account result:", acct.status)
    
    print("3. Attempting get_asset('AAPL')...")
    asset = client.get_asset('AAPL')
    print("✅ get_asset result:", asset.symbol)

except APIError as e:
    print(f"❌ API Error: {e}")
    print(f"   Code: {e.code}")
    print(f"   Status: {e.status_code}")
except Exception as e:
    print(f"❌ General Error: {e}")
