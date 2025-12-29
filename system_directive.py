"""
NEXUS TRADING BOT - Centralized Configuration
Single source of truth for asset groups and ticker mappings.
"""
import os

# =================================================================
# ASSET GROUPS - Define which exchanges handle which assets
# =================================================================

ASSET_GROUPS = {
    'CRYPTO': [
        # Major Caps (Binance Futures)
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT',
        'NEARUSDT', 'ATOMUSDT', 'ICPUSDT', 'BCHUSDT',
        # Memes & AI
        'WIFUSDT', '1000PEPEUSDT', 'DOGEUSDT', '1000SHIBUSDT', 'SUIUSDT',
        'RENDERUSDT', 'FETUSDT', 'INJUSDT', 'SEIUSDT',
        '1000BONKUSDT', '1000FLOKIUSDT', 'TRBUSDT', 'ZECUSDT',
        'PONKEUSDT', 'BRETTUSDT',
        # DeFi
        'UNIUSDT', 'AAVEUSDT', 'XLMUSDT', 'CRVUSDT', 'POLUSDT', 'LDOUSDT',
        # AI / Tech
        'TAOUSDT'
    ],
    'BYBIT': [
        # Bybit Perpetuals (cross-listed on Binance until Bybit fetcher is ready)
        'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT',
        'FLOWUSDT', 'TAOUSDT', 'RENDERUSDT', '1000PEPEUSDT', 'DOGEUSDT'
        # Bybit-exclusive (disabled - need Bybit data fetcher):
        # 'NIGHTUSDT', 'MNTUSDT', 'ZKPUSDT', 'RAVEUSDT', 'FOLKSUSDT'
    ],
    'STOCKS': [
        # High Liquidity Day Trading Workhorses (Alpaca)
        'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN',
        'META', 'GOOGL', 'AMD', 'JPM', 'BAC'
    ],
    'ETFS': [
        # Core ETFs for Market Operations (Alpaca)
        'SPY',   # S&P 500
        'QQQ',   # Nasdaq 100
        'IWM',   # Russell 2000
        'TLT',   # Long-Term Bonds
        'GLD'    # Gold
    ]
}

# Toggle groups on/off (Global Defaults)
GROUP_CONFIG = {
    'CRYPTO': True,
    'BYBIT': True,
    'STOCKS': True,
    'ETFS': True
}

# --- STRATEGY CONFIG ---
ENABLED_STRATEGIES = {
    'SCALPING': True,
    'GRID': True,
    'MEAN_REVERSION': True,
    'BLACK_SWAN': True,
    'SHARK': False,
    'TREND': True
}

# --- STRATEGY CONFIG MAPPING (Centralized) ---
# Maps Strategy Name to Config Key (Duplicate in nexus_loader/factory fixed)
STRATEGY_CONFIG_MAP = {
    'TrendFollowing': 'TREND',
    'Trend': 'TREND',
    'TREND': 'TREND',
    'Scalping': 'SCALPING',
    'Scalping (High Vol)': 'SCALPING',
    'SCALPING': 'SCALPING',
    'MeanReversion': 'MEAN_REVERSION',
    'Mean Reversion': 'MEAN_REVERSION',
    'MEAN_REVERSION': 'MEAN_REVERSION',
    'Grid': 'GRID',
    'GridTrading': 'GRID',
    'GRID': 'GRID',
    'BlackSwan': 'SENTINEL',
    'BLACK_SWAN': 'SENTINEL',
    'Shark': 'SENTINEL',
    'SHARK': 'SENTINEL',
    'Sentinel': 'SENTINEL',
}

# Maps Strategy Name to Class Name (for Factory)
STRATEGY_CLASS_MAP = {
    'TrendFollowing': 'TrendFollowingStrategy',
    'Trend': 'TrendFollowingStrategy',
    'Scalping': 'ScalpingStrategy',
    'Grid': 'GridTradingStrategy',
    'MeanReversion': 'MeanReversionStrategy',
    'Shark': 'SentinelStrategy',
    'BlackSwan': 'SentinelStrategy',
    'Sentinel': 'SentinelStrategy',
}

# Runtime Blacklist (Global)
DISABLED_ASSETS = set()

# --- SHARK TARGETS (High Volatility Assets) ---
SHARK_TARGETS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'WIFUSDT', '1000PEPEUSDT',
    'DOGEUSDT', 'SUIUSDT', 'SEIUSDT', 'INJUSDT', 'TAOUSDT'
]

# --- AI & ML MODULES ---
# Defaults - DB persisted values will override on startup
AI_FILTER_ENABLED = True
ML_CLASSIFIER_ENABLED = True
# --- RISK & MANAGEMENT ---
RISK_PER_TRADE_PCT = 0.01
ALLOW_SLTP_UPDATE = True
SLTP_UPDATE_COOLDOWN = 1800  # 30 minutes
COOLDOWN_SECONDS = 180  # Default signal cooldown (3 minutes)
PREMIUM_SIGNALS_ENABLED = True  # Enable multi-timeframe analysis


# --- COINMARKETCAP SENTINEL CONFIG ---
CMC_API_KEY = os.getenv("CMC_API_KEY", "")
CMC_POLL_INTERVAL = 600  # 10 Minutes (Preserve API Credits)

# --- NETWORK & HTTP CONFIG ---
# Timeouts (seconds)
HTTP_TIMEOUT = 10
HTTP_TIMEOUT_SHORT = 5
HTTP_TIMEOUT_LONG = 30

# URLs (External APIs)
IPIFY_URL = "https://api.ipify.org?format=json"
IP_GEO_URL = "http://ip-api.com/json/{ip_addr}"
TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"
BINANCE_PUBLIC_API = "https://api.binance.com/api/v3"

# --- SHARK MODE CONFIG ---
SHARK_CRASH_THRESHOLD_PCT = 3.0  # Percentage drop to trigger
SHARK_WINDOW_SECONDS = 60  # Rolling window size
SHARK_MAX_WORKERS = 10  # Thread pool workers (legacy, will be removed)
SHARK_HEARTBEAT_SECONDS = 1  # Price check interval
SHARK_COOLDOWN_SECONDS = 300  # Cooldown after trigger (5 minutes)

# --- DIAGNOSTICS CONFIG ---
DIAG_SYMBOL_CRYPTO = "BTCUSDT"
DIAG_SYMBOL_STOCK = "TSLA"
DIAG_TIMEFRAME = "15m"
DIAG_CANDLE_LIMIT = 250
DIAG_CANDLE_LIMIT_SHORT = 1

# --- TRADING SESSION DEFAULTS ---
DEFAULT_SESSION_CONFIG = {
    "mode": "WATCHER",
    "leverage": 5,
    "max_capital_pct": 0.10,
    "stop_loss_pct": 0.02,
    "max_stop_loss_pct": 0.05, # Emergency Clamp: No SL ever wider than 5%
    "tp_ratio": 1.5,
    "spot_allocation_pct": 0.20,
    "personality": "STANDARD_ES",
    "sentiment_filter": True,
    "atr_multiplier": 2.2,
    "circuit_breaker_enabled": True,
    "alpaca_key": None,
    "alpaca_secret": None,
    "strategies": dict(ENABLED_STRATEGIES),
    "groups": dict(GROUP_CONFIG),
    # --- MONEY MANAGEMENT (Kelly Criterion) ---
    "use_kelly_criterion": False, # Disabled by default
    "kelly_fraction": 0.5,        # Half-Kelly (Conservative)
    "win_rate_est": 0.55,         # 55% Win Rate Estimate
    "risk_reward_est": 1.5,       # 1.5 R:R Ratio
    
    # --- SHIELDS ---
    "correlation_guard_enabled": True, # Shield 2.0
    
    # --- EXCHANGE ROUTING ---
    "crypto_exchange": "BINANCE", # BINANCE or BYBIT
    "bybit_key": None,
    "bybit_secret": None
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
    'POLUSDT': '🟣 Polygon (POL)',
    'LINKUSDT': '🔗 Chainlink',
    'NEARUSDT': '🌐 NEAR Protocol',
    'ATOMUSDT': '⚛️ Cosmos',
    'ICPUSDT': '∞ Internet Computer',
    'BCHUSDT': '💚 Bitcoin Cash',
    # Memes
    'WIFUSDT': '🐕 Dogwifhat',
    '1000PEPEUSDT': '🐸 Pepe',
    'DOGEUSDT': '🐶 Dogecoin',
    '1000SHIBUSDT': '🐕‍🦺 Shiba Inu',
    'SUIUSDT': '💧 Sui',
    '1000BONKUSDT': '🦴 Bonk',
    '1000FLOKIUSDT': '🐕 Floki',
    'PONKEUSDT': '🐵 Ponke',
    'BRETTUSDT': '🔵 Brett',
    # AI & Tech
    'RENDERUSDT': '🖼️ Render',
    'FETUSDT': '🤖 Fetch.ai',
    'INJUSDT': '💉 Injective',
    'SEIUSDT': '🌊 Sei',
    'TRBUSDT': '🔮 Tellor',
    'ZECUSDT': '🔐 Zcash',
    # DeFi
    'UNIUSDT': '🦄 Uniswap',
    'AAVEUSDT': '👻 Aave',
    'XLMUSDT': '✨ Stellar',
    'CRVUSDT': '🔄 Curve',
    'LDOUSDT': '🏝️ Lido DAO',
    # Bybit-specific
    'NIGHTUSDT': '🌙 Night',
    'FLOWUSDT': '🌊 Flow',
    'MNTUSDT': '🏔️ Mantle',
    'TAOUSDT': '🧠 Bittensor',
    'ZKPUSDT': '🔐 ZKP',
    'RAVEUSDT': '🎵 Rave',
    'FOLKSUSDT': '👥 Folks',
    
    # === STOCKS (Alpaca) ===
    'AAPL': '🍎 Apple',
    'MSFT': '🪟 Microsoft',
    'NVDA': '🎮 NVIDIA',
    'TSLA': '🚗 Tesla',
    'AMZN': '📦 Amazon',
    'META': '👤 Meta',
    'GOOGL': '🔍 Google',
    'AMD': '🔴 AMD',
    'JPM': '🏦 JPMorgan',
    'BAC': '🏦 Bank of America',
    
    # === ETFs (Alpaca) ===
    'SPY': '📈 S&P 500',
    'QQQ': '💻 Nasdaq 100',
    'IWM': '🐻 Russell 2000',
    'TLT': '📜 Long Bonds',
    'GLD': '🥇 Gold'
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


def get_asset_group(symbol: str) -> str:
    """
    Determine which asset group a symbol belongs to.
    Returns: 'CRYPTO', 'STOCKS', 'ETFS', or 'UNKNOWN'.
    """
    for group_name, symbols in ASSET_GROUPS.items():
        if symbol in symbols:
            return group_name
    return 'UNKNOWN'


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

