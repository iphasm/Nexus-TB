import os
from binance.client import Client

def test_fetch():
    print("--- DEBUG BINANCE FETCH [INTERNATIONAL API] ---")
    
    # Try Public Client with International API
    print("# Attempting Public Client Init (International)...")
    try:
        client = Client(tld='com')
        print("✅ Client init successful (Public - api.binance.com)")
        
        symbol = "BTCUSDT"
        print(f"# Fetching klines for {symbol}...")
        klines = client.get_klines(symbol=symbol, interval='15m', limit=5)
        
        if klines:
            print(f"✅ Success! Received {len(klines)} candles.")
            print(f"Sample candle data: {klines[0]}")
            print(f"\nFirst candle close price: {klines[0][4]}")
        else:
            print("❌ Success response but EMPTY list returned.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Verify Binance API is accessible from your region")
        print("3. Check if firewall is blocking api.binance.com")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch()
