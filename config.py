"""
Antigravity Bot - Centralized Configuration
Single source of truth for asset groups and ticker mappings.
"""

# =================================================================
# ASSET GROUPS - Define which exchanges handle which assets
# =================================================================

ASSET_GROUPS = {
    'CRYPTO': [
        # Major Caps
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT',
        'AVAXUSDT', 'LTCUSDT', 'DOTUSDT', 'MATICUSDT', 'LINKUSDT',
        'NEARUSDT', 'ATOMUSDT', 'ICPUSDT', 'BCHUSDT',
        # Memes & AI
        'WIFUSDT', '1000PEPEUSDT', 'DOGEUSDT', 'SHIBUSDT', 'SUIUSDT',
        'RENDERUSDT', 'FETUSDT', 'INJUSDT', 'FTMUSDT', 'SEIUSDT',
        'BONKUSDT', 'FLOKIUSDT', 'TRBUSDT', 'ZECUSDT', 'EOSUSDT',
        # DeFi
        'UNIUSDT', 'AAVEUSDT', 'XLMUSDT', 'CRVUSDT'
    ],
    'STOCKS': ['TSLA', 'NVDA', 'MSFT', 'AAPL', 'AMD'],
    'COMMODITY': ['GLD', 'USO', 'SLV', 'CPER', 'UNG']
}

# Toggle groups on/off
GROUP_CONFIG = {
    'CRYPTO': True,
    'STOCKS': True,
    'COMMODITY': True
}

# =================================================================
# TICKER MAP - Human-readable names for all assets
# =================================================================

TICKER_MAP = {
    # === CRYPTO (Binance Futures) ===
    'BTCUSDT': '₿ Bitcoin',
    'ETHUSDT': 'Ξ Ethereum',
    'BNBUSDT': '🔶 Binance Coin',
    'SOLUSDT': '◎ Solana',
    'ADAUSDT': '🔵 Cardano',
    'XRPUSDT': '💧 Ripple',
    'AVAXUSDT': '🔺 Avalanche',
    'LTCUSDT': '🥈 Litecoin',
    'DOTUSDT': '⚫ Polkadot',
    'MATICUSDT': '🟣 Polygon',
    'LINKUSDT': '🔗 Chainlink',
    'NEARUSDT': '🌐 NEAR Protocol',
    'ATOMUSDT': '⚛️ Cosmos',
    'ICPUSDT': '∞ Internet Computer',
    'BCHUSDT': '💚 Bitcoin Cash',
    # Memes
    'WIFUSDT': '🐕 Dogwifhat',
    '1000PEPEUSDT': '🐸 Pepe',
    'DOGEUSDT': '🐶 Dogecoin',
    'SHIBUSDT': '🐕‍🦺 Shiba Inu',
    'SUIUSDT': '💧 Sui',
    'BONKUSDT': '🦴 Bonk',
    'FLOKIUSDT': '🐕 Floki',
    # AI & Tech
    'RENDERUSDT': '🖼️ Render',
    'FETUSDT': '🤖 Fetch.ai',
    'INJUSDT': '💉 Injective',
    'FTMUSDT': '👻 Fantom',
    'SEIUSDT': '🌊 Sei',
    'TRBUSDT': '🔮 Tellor',
    'ZECUSDT': '🔐 Zcash',
    'EOSUSDT': '🟣 EOS',
    # DeFi
    'UNIUSDT': '🦄 Uniswap',
    'AAVEUSDT': '👻 Aave',
    'XLMUSDT': '✨ Stellar',
    'CRVUSDT': '🔄 Curve',
    
    # === STOCKS (Alpaca) ===
    'TSLA': '🚗 Tesla',
    'NVDA': '🎮 NVIDIA',
    'MSFT': '🪟 Microsoft',
    'AAPL': '🍎 Apple',
    'AMD': '🔴 AMD',
    
    # === COMMODITIES (Alpaca ETFs) ===
    'GLD': '🥇 ORO',
    'USO': '🛢️ PETRÓLEO',
    'SLV': '🥈 PLATA',
    'CPER': '🟤 COBRE',
    'UNG': '🔥 GAS NATURAL'
}


# =================================================================
# HELPER FUNCTIONS
# =================================================================

def get_all_assets():
    """Get flat list of all tradeable assets."""
    assets = []
    for group in ASSET_GROUPS.values():
        assets.extend(group)
    return list(set(assets))


def get_display_name(symbol: str) -> str:
    """Get human-readable name for a symbol."""
    return TICKER_MAP.get(symbol, symbol)


def is_crypto(symbol: str) -> bool:
    """Check if symbol is a crypto asset (routed to Binance)."""
    return 'USDT' in symbol


def get_broker(symbol: str) -> str:
    """Determine which broker handles the symbol."""
    if is_crypto(symbol):
        return 'BINANCE'
    return 'ALPACA'


def resolve_symbol(text: str) -> str:
    """Clean and standardize symbol input."""
    s = text.strip().upper().replace('/', '').replace('-', '').replace('_', '')
    
    # 1. Exact Match Check
    known_assets = get_all_assets()
    if s in known_assets or s in TICKER_MAP:
        return s
    
    # 2. Reverse Lookup (by name)
    for ticker, name in TICKER_MAP.items():
        # Strip emoji and check
        clean_name = ''.join(c for c in name if not c in '₿Ξ🔶◎🔵💧🔺🥈⚫🟣🔗🌐⚛️∞💚🐕🐸🐶🐕‍🦺💧🦴🖼️🤖💉👻🌊🔮🔐🦄✨🔄🚗🎮🪟🍎🔴🥇🛢️🟤🔥').strip()
        if s == clean_name.upper():
            return ticker
    
    # 3. Try Appending USDT (for crypto)
    s_usdt = s + "USDT"
    if s_usdt in ASSET_GROUPS.get('CRYPTO', []):
        return s_usdt
    
    return s
