import os
import sys
from dotenv import load_dotenv, find_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus

# Load environment variables
dotenv_path = find_dotenv()
print(f"📂 Dotenv found at: {dotenv_path}")
load_dotenv(dotenv_path)

api_key = os.getenv('APCA_API_KEY_ID')
secret_key = os.getenv('APCA_API_SECRET_KEY')

print(f"🔑 Key found: {'YES' if api_key else 'NO'}")
print(f"🔑 Secret found: {'YES' if secret_key else 'NO'}")

if not api_key or not secret_key:
    # Try alternate names just in case
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    print(f"🔑 Alt Key found: {'YES' if api_key else 'NO'}")

if not api_key:
    print("❌ Error: Alpaca API keys not found in environment.")
    print("   Please ensure .env contains APCA_API_KEY_ID and APCA_API_SECRET_KEY")
    sys.exit(1)

try:
    trading_client = TradingClient(api_key, secret_key, paper=True)

    # Search for active US Equities
    search_params = GetAssetsRequest(
        status=AssetStatus.ACTIVE,
        asset_class=AssetClass.US_EQUITY
    )

    print("🔄 Fetching Alpaca assets...")
    assets = trading_client.get_all_assets(search_params)

    print(f"✅ Total Active US Equity Assets: {len(assets)}")
    print("\n📝 All US Equity Assets:")
    for asset in assets:
        print(f"{asset.symbol}|{asset.name}|ETB:{asset.easy_to_borrow}")
        
    # Search for Crypto on Alpaca if available
    search_params_crypto = GetAssetsRequest(
        status=AssetStatus.ACTIVE,
        asset_class=AssetClass.CRYPTO
    )
    crypto_assets = trading_client.get_all_assets(search_params_crypto)
    print(f"\n✅ Total Active Crypto Assets: {len(crypto_assets)}")
    print(f"\n✅ Total Active Crypto Assets: {len(crypto_assets)}")
    if crypto_assets:
        print("📝 All Crypto Assets:")
        for asset in crypto_assets:
             print(f"{asset.symbol}|{asset.name}")

except Exception as e:
    print(f"❌ Error fetching assets: {e}")
