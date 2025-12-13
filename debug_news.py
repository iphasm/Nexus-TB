import yfinance as yf

tickers = ["^GSPC", "^TNX", "DX-Y.NYB", "BTC-USD", "DJT"]

print("--- TESTING NEWS FETCHING ---")
for t in tickers:
    try:
        obj = yf.Ticker(t)
        news = obj.news
        print(f"\nTicker: {t}")
        if not news:
            print("❌ No news found (Empty list)")
        else:
            print(f"✅ News found: {len(news)} items")
            first_item = news[0]
            # Check nested
            if 'content' in first_item and isinstance(first_item['content'], dict):
                 print(f"   Headlines (FIXED): {[n['content'].get('title') for n in news[:2] if 'content' in n]}")
            else:
                 print(f"   Headlines: {[n.get('title', 'NO_TITLE') for n in news[:2]]}")
    except Exception as e:
        print(f"❌ Error fetching {t}: {e}")
