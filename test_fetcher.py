from data.fetcher import get_market_data

print("=== Testing Data Fetcher ===\n")

# Test 1: Crypto with USDT
print("Test 1: Fetching BTCUSDT...")
df = get_market_data('BTCUSDT', timeframe='15m', limit=5)
if not df.empty:
    print(f"✅ Success! Got {len(df)} rows")
    print(f"Latest close price: ${df.iloc[-1]['close']:.2f}")
    print(f"Columns: {list(df.columns)}\n")
else:
    print("❌ Failed: Empty DataFrame\n")

# Test 2: Another crypto (Ethereum)
print("Test 2: Fetching ETHUSDT...")
df2 = get_market_data('ETHUSDT', timeframe='15m', limit=3)
if not df2.empty:
    print(f"✅ Success! Got {len(df2)} rows")
    print(f"Latest close price: ${df2.iloc[-1]['close']:.2f}\n")
else:
    print("❌ Failed: Empty DataFrame\n")

print("=== All Tests Complete ===")
