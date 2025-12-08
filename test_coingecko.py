import ccxt

try:
    cg = ccxt.coingecko()
    print("CoinGecko initialized.")
    # cg.load_markets() # Can be heavy
    
    # Try fetching OHLCV for 'BTC/USDT' directly?
    # Coingecko usually expects IDs like 'bitcoin' and vs_currency 'usd'
    # But let's check if ccxt abstracts this.
    try:
        data = cg.fetch_ohlcv('BTC/USDT', '1d', limit=5)
        print(f"Success with BTC/USDT: {len(data)} candles")
    except Exception as e:
        print(f"Failed with BTC/USDT: {e}")
        
    # Try 'bitcoin' vs 'usd'?
    try:
        # ccxt coingecko symbols are usually 'ID/VS' e.g. 'bitcoin/usd'
        data = cg.fetch_ohlcv('bitcoin/usd', '1d', limit=5)
        print(f"Success with bitcoin/usd: {len(data)} candles")
    except Exception as e:
        print(f"Failed with bitcoin/usd: {e}")

except Exception as e:
    print(f"General Error: {e}")
