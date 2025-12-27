"""
Icon Fetcher Tool.
Downloads transparent icons for all configured assets.
Sources:
- Crypto: assets.coincap.io (High quality transparent PNGs)
- Stocks: parqet.com / clearbit.com
"""

import os
import requests
import sys

# Add parent dir to path to import system_directive
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from system_directive import ASSET_GROUPS
except ImportError:
    # Fallback if run standalone without path setup
    print("Could not import system_directive. Using hardcoded lists.")
    ASSET_GROUPS = {
        'CRYPTO': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT', 'SHIBUSDT', 'DOTUSDT', 'LINKUSDT'],
        'STOCKS': ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD'],
        'ETFS': ['SPY', 'QQQ', 'IWM', 'TLT', 'GLD']
    }

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

# Mappings for tricky symbols
CRYPTO_SLUG_MAP = {
    '1000PEPE': 'pepe',
    '1000SHIB': 'shib',
    '1000BONK': 'bonk',
    '1000FLOKI': 'floki',
    'MATIC': 'polygon',
    'POL': 'polygon',
    'RNDR': 'render-token', # Render might be different
    'RENDER': 'render-token',
    'FET': 'fetch',
    'WIF': 'dogwifhat',
    'LDO': 'lido-dao',
}

def download_file(url, filepath):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return False

def fetch_crypto_icon(symbol):
    clean = symbol.replace('USDT', '')
    filename = f"{clean.lower()}.png"
    filepath = os.path.join(ICONS_DIR, filename)
    
    # Try CoinCap (Usually very good quality)
    # They use lower case symbols usually: btc, eth
    # Special cases handling
    search_symbol = CRYPTO_SLUG_MAP.get(clean, clean.lower())
    
    # URLs to try in order
    urls = [
        f"https://assets.coincap.io/assets/icons/{search_symbol}@2x.png", # Best quality usually
        f"https://cryptologos.cc/logos/{search_symbol}-{clean.lower()}-logo.png", # Backup
    ]
    
    # Try CoinGecko style if direct fails? (Too complex URL structure)
    
    print(f"Downloading {clean}...", end=" ")
    for url in urls:
        if download_file(url, filepath):
            print(f"✅ ({url})")
            return
            
    print("❌ Failed")

def fetch_stock_icon(symbol):
    filename = f"{symbol.lower()}.png"
    filepath = os.path.join(ICONS_DIR, filename)
    
    # URLs for stocks
    # 1. Parqet (Good for US stocks)
    # 2. Clearbit (Needs domain, guessing domain)
    # 3. EODHD (Sometimes works)
    
    urls = [
        f"https://assets.parqet.com/logos/symbol/{symbol}?format=png",
        f"https://eodhd.com/img/logos/US/{symbol}.png",
        f"https://logo.clearbit.com/{symbol}.com" # Naive guess
    ]
    
    print(f"Downloading {symbol}...", end=" ")
    for url in urls:
        if download_file(url, filepath):
            # Check if valid image (some store generic placeholder)
            if os.path.getsize(filepath) > 100: # minimal check
                print(f"✅ ({url})")
                return
    
    print("❌ Failed")


def main():
    print(f"Fetching icons into {ICONS_DIR}")
    
    # Process Crypto
    for symbol in ASSET_GROUPS.get('CRYPTO', []):
        fetch_crypto_icon(symbol)
        
    # Process Stocks
    for symbol in ASSET_GROUPS.get('STOCKS', []):
        fetch_stock_icon(symbol)
        
    # Process ETFs
    for symbol in ASSET_GROUPS.get('ETFS', []):
        fetch_stock_icon(symbol) # ETFs usually work with stock sources

if __name__ == "__main__":
    main()
