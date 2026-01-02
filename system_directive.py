"""
NEXUS TRADING BOT - Centralized Configuration
Single source of truth for asset groups and ticker mappings.
"""
import os

# =================================================================
# ASSET GROUPS - Define which assets belong to which category
# =================================================================
#
# JERARQUÍA DE GRUPOS EXPANDIDA:
# ├── CRYPTO: TODOS los activos de criptomonedas
# │   ├── Assets disponibles en BINANCE y BYBIT (expanded)
# │   └── El usuario elige qué exchanges usar dentro de CRYPTO
# │   └── SUBGRUPOS TEMÁTICOS: DeFi, Meme, AI, Gaming, etc.
# ├── STOCKS: Activos de acciones (Alpaca)
# └── ETFS: Activos de ETFs (Alpaca)
#
# Dentro de CRYPTO, los exchanges (Binance/Bybit) son elecciones equivalentes
# del usuario, no grupos separados.

# =================================================================
# ASSET GROUPS - OPTIMIZED (2025)
# =================================================================
# Grupos principales de activos - CRYPTO se genera dinámicamente desde CRYPTO_SUBGROUPS

# Initialize ASSET_GROUPS with static groups
ASSET_GROUPS = {
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

# CRYPTO group will be generated after function definitions

# =================================================================
# CRYPTO SUBGROUPS - Thematic categorization within CRYPTO
# =================================================================

# =================================================================
# BYBIT TICKER MAPPING - CORRECTIONS
# =================================================================
# Mapping específico para Bybit cuando los tickers difieren de Binance
# Nexus Bot debe consultar esto antes de enviar orden a Bybit
BYBIT_TICKER_MAPPING = {
    "1000SHIBUSDT": "SHIBUSDT",     # Bybit no usa el 1000 en algunos casos
    "1000PEPEUSDT": "PEPEUSDT",     # Corrección para PEPE
    "1000BONKUSDT": "BONKUSDT",     # Corrección para BONK
    "1000FLOKIUSDT": "FLOKIUSDT",   # Corrección para FLOKI
    "MATICUSDT": "POLUSDT",         # Si Bybit ya migró completo a POL
    "RENDERUSDT": "RNDRUSDT",       # Ticker legacy para Render
    # Agregar más correcciones según sean necesarias
}

# =================================================================
# CRYPTO SUBGROUPS - OPTIMIZED LIST (2025)
# =================================================================
# Lista optimizada y actualizada con los activos más relevantes y líquidos
CRYPTO_SUBGROUPS = {
    'MAJOR_CAPS': [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT",
        "AVAXUSDT", "DOTUSDT", "LINKUSDT", "TRXUSDT"
    ],
    'MEME_COINS': [
        "DOGEUSDT", "WIFUSDT", "BRETTUSDT", "MEWUSDT", "BOMEUSDT"
    ],
    'DEFI': [
        "UNIUSDT", "AAVEUSDT", "CRVUSDT", "COMPUSDT", "SNXUSDT",
        "LDOUSDT", "ENAUSDT", "DYDXUSDT", "INJUSDT"
    ],
    'AI_TECH': [
        "TAOUSDT", "WLDUSDT", "GRTUSDT", "ARKMUSDT", "TRBUSDT", "TIAUSDT"
    ],
    'GAMING_METAVERSE': [
        "AXSUSDT", "SANDUSDT", "MANAUSDT", "IMXUSDT", "GALAUSDT", "ENJUSDT",
        "ILVUSDT", "PIXELUSDT"
    ],
    'LAYER1_INFRA': [
        "SUIUSDT", "SEIUSDT", "NEARUSDT", "MATICUSDT", "APTUSDT",
        "OPUSDT", "ARBUSDT", "ATOMUSDT", "ETCUSDT", "LTCUSDT", "BCHUSDT",
        "ALGOUSDT", "VETUSDT"
    ],
    'BYBIT_EXCLUSIVE': [
        'FLOWUSDT', 'LPTUSDT', 'PENDLEUSDT', 'ASTRUSDT', 'CFGUSDT', 'ACEUSDT',
        'NFPUSDT', 'MAVIAUSDT', 'PIXELUSDT', 'BEAMUSDT', 'NIGHTUSDT', 'MNTUSDT',
        'ZKPUSDT', 'RAVEUSDT', 'FOLKSUSDT', 'AIUSDT', 'XAIUSDT', 'FOXYUSDT',
        'SANTOSUSDT', 'PORTOUSDT', 'CITYUSDT', 'INTERUSDT', 'BARUSDT', 'PSGUSDT', 'JUVUSDT'
    ]
}

# Toggle groups on/off (Global Defaults) - Updated for new hierarchical structure
GROUP_CONFIG = {
    # Main asset groups
    'CRYPTO': True,
    'STOCKS': True,
    'ETFS': True,

    # Crypto thematic subgroups (all enabled by default when CRYPTO is enabled)
    'MAJOR_CAPS': True,        # Major market cap cryptocurrencies
    'MEME_COINS': True,        # Meme coins and viral tokens
    'DEFI': True,              # Decentralized Finance tokens
    'AI_TECH': True,           # AI, Tech, and utility tokens
    'GAMING_METAVERSE': True,  # Gaming and metaverse tokens
    'LAYER1_INFRA': True,      # Layer 1 and infrastructure tokens
    'BYBIT_EXCLUSIVE': False   # Bybit-specific tokens (disabled by default)
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
    'Grid Trading': 'GRID',  # Legacy name with space
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
    "bybit_api_key": None,
    "bybit_api_secret": None
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

def get_crypto_assets() -> list:
    """
    Generate CRYPTO group dynamically from enabled subgroups.
    Excludes BYBIT_EXCLUSIVE if disabled in GROUP_CONFIG.
    """
    crypto_assets = []

    for subgroup_name, assets in CRYPTO_SUBGROUPS.items():
        # Skip BYBIT_EXCLUSIVE if disabled
        if subgroup_name == 'BYBIT_EXCLUSIVE' and not GROUP_CONFIG.get('BYBIT_EXCLUSIVE', False):
            continue
        crypto_assets.extend(assets)

    return sorted(list(set(crypto_assets)))

def get_bybit_corrected_ticker(ticker: str) -> str:
    """
    Get Bybit-corrected ticker if available, otherwise return original.
    """
    return BYBIT_TICKER_MAPPING.get(ticker, ticker)


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

# =================================================================
# DYNAMIC CRYPTO GROUP GENERATION
# =================================================================
# Generate CRYPTO group dynamically after all functions are defined
ASSET_GROUPS['CRYPTO'] = get_crypto_assets()

