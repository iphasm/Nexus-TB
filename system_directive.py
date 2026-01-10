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
# EXCHANGE EXCLUSIONS - Activos NO disponibles en cada exchange
# =================================================================
# Evita intentar obtener datos de activos que no existen en un exchange
BINANCE_EXCLUSIONS = set()  # Binance tiene casi todo

BYBIT_EXCLUSIONS = {
    # === Binance Ecosystem Tokens (NO disponibles en Bybit) ===
    "BNBUSDT",      # Token nativo de Binance - NO en Bybit
    "BAKEUSDT",     # Binance ecosystem token
    "ALPACAUSDT",   # Binance-specific
    "BIFIUSDT",     # Binance-specific
    "CAKEUSDT",     # PancakeSwap (BSC) - NO en Bybit futures
    "XVSUSDT",      # Venus (BSC) - NO en Bybit futures
    "SFPUSDT",      # SafePal (BSC) - verificar
    "TRUUSDT",      # TrueFi (BSC) - verificar

    # === Meme Coins NO en Bybit futures ===
    "BOMEUSDT",     # Book of Meme - NO en Bybit perpetuos
    "BRETTUSDT",    # Brett - NO en Bybit
    "MEWUSDT",      # Cat in a Dogs World - NO en Bybit

    # === AI/Tech tokens limitados ===
    "TRBUSDT",      # Tellor - NO en Bybit
    "ARKMUSDT",     # Arkham - verificar

    # === Gaming tokens limitados ===
    "ILVUSDT",      # Illuvium - puede no estar
    "ENJUSDT",      # Enjin - verificar

    # === Stablecoins/Otros ===
    "BTTCUSDT",     # BitTorrent en formato Binance
    "TUSDUSDT",     # TrueUSD puede no estar en Bybit
    "USDCUSDT",     # Stablecoin pair - verificar
    "PAXGUSDT",     # Pax Gold - verificar

    # === DeFi limitados ===
    "COMPUSDT",     # Compound - verificar
    "SNXUSDT",      # Synthetix - verificar
}

def is_symbol_available_on_exchange(symbol: str, exchange: str) -> bool:
    """Verifica si un símbolo está disponible en un exchange específico"""
    if exchange.upper() == 'BINANCE':
        return symbol not in BINANCE_EXCLUSIONS
    elif exchange.upper() == 'BYBIT':
        return symbol not in BYBIT_EXCLUSIONS
    return True  # Por defecto, asumir disponible

# =================================================================
# CRYPTO SUBGROUPS - OPTIMIZED LIST (2025) - Correlation Analysis
# =================================================================
# Optimized based on correlation analysis to reduce overexposure
# Removed assets with >85% correlation to keep portfolio diversified
CRYPTO_SUBGROUPS = {
    'MAJOR_CAPS': [
        # Core positions - user preferences preserved
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT"
    ],
    'MEME_COINS': [
        # Low-correlation meme representatives
        "DOGEUSDT", "WIFUSDT", "1000PEPEUSDT", "PONKEUSDT"
    ],
    'DEFI': [
        # Low-correlation DeFi picks
        "AAVEUSDT", "CRVUSDT", "SNXUSDT", "LDOUSDT", "DYDXUSDT"
    ],
    'AI_TECH': [
        # AI/Tech tokens
        "WLDUSDT", "INJUSDT"
    ],
    'LAYER1_INFRA': [
        # Low-correlation L1/Infrastructure
        "NEARUSDT", "ARBUSDT", "LTCUSDT", "BCHUSDT", "ETCUSDT", "ALGOUSDT"
    ],
    'BYBIT_EXCLUSIVE': [
        # Bybit-specific tokens for coverage
        'FLOWUSDT', 'PENDLEUSDT', 'XAIUSDT'
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
    'LAYER1_INFRA': True,      # Layer 1 and infrastructure tokens
    'BYBIT_EXCLUSIVE': False   # Bybit-specific tokens (disabled by default)
}

# --- STRATEGY CONFIG ---
ENABLED_STRATEGIES = {
    'SCALPING': False,  # DESHABILITADO: Nunca se activa y causa conflictos de cálculo
    'GRID': True,
    'MEAN_REVERSION': True,
    'BLACK_SWAN': True,
    'SHARK': True,  # ACTIVADO: Capitaliza oportunidades bajistas
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
# PREMIUM_SIGNALS_ENABLED = False  # REMOVED: Redundant with AI Filter

# --- MTF (Multi-Timeframe) Confluence Filter ---
MTF_FILTER_ENABLED = True           # Enable/disable MTF filter
MTF_MIN_CONFLUENCE_SCORE = 6.0      # Minimum score (0-10) to pass signal (higher = fewer trades, better quality)
MTF_TIMEFRAMES = ['1m', '15m', '4h'] # Timeframes used for analysis


# OpenAI Configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # Default to gpt-4o
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
SHARK_CRASH_THRESHOLD_PCT = 3.0  # Percentage drop to trigger Black Swan
SHARK_WINDOW_SECONDS = 60  # Rolling window size
SHARK_MAX_WORKERS = 10  # Thread pool workers (legacy, will be removed)
SHARK_HEARTBEAT_SECONDS = 1  # Price check interval
SHARK_COOLDOWN_SECONDS = 300  # Cooldown after trigger (5 minutes)

# --- SHARK INDEPENDENT MODE CONFIG ---
SHARK_INDEPENDENT_MODE = True  # Allow Shark to activate without Black Swan
SHARK_MOMENTUM_THRESHOLD = 2.0  # 2% drop for independent Shark activation
SHARK_MIN_VOLUME_MULTIPLIER = 1.2  # Minimum volume spike for activation

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
    "bybit_api_secret": None,

    # --- PROTECTION CONFIGURATION ---
    "trailing_enabled": True,
    "trailing_callback_rate_binance_pct": 1.0,   # 0.1–5.0
    "trailing_pct_bybit": 1.0,                   # convertiremos a distancia
    "protection_trigger_by": "MARK_PRICE",       # MARK_PRICE / LAST_PRICE (Binance)
    "protection_retry_attempts": 2,
    "protection_retry_delay_sec": 0.6,
    "protection_tolerance_pct": 0.01,            # 1% tolerancia en verificación
    
    # --- DYNAMIC TP PROGRESSION ---
    "dynamic_tp_enabled": True,                  # Enable progressive TP raising
    "tp_progression_thresholds": [               # (progress%, tp_boost%)
        (0.50, 0.25),  # At 50% → +25% TP
        (0.70, 0.50),  # At 70% → +50% TP
        (0.85, 0.75),  # At 85% → +75% TP
    ],
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

