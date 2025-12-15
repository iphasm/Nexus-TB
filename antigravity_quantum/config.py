
# Dynamic configuration for the Quantum Engine
# This file is imported by both the Engine (background) and Main (foreground).

# --- STRATEGY CONFIG ---
ENABLED_STRATEGIES = {
    'SCALPING': True,      # High Risk, High Reward
    'GRID': True,          # Grid Trading for sideways
    'MEAN_REVERSION': True, # Default safe strategy
    'BLACK_SWAN': True,    # Defense: Cancel longs during crashes
    'SHARK': False,        # Attack: Open shorts during crashes (OFF by default)
    'TREND': True          # Trend Following (BTC)
}

# --- GROUP CONFIG ---
# Controls which market sectors are scanned
GROUP_CONFIG = {
    'CRYPTO': True,
    'STOCKS': True,
    'COMMODITY': True
}

# SL/TP Update Flag
ALLOW_SLTP_UPDATE = True

# Cooldown for SLTP updates (seconds) - prevents spam on open positions
SLTP_UPDATE_COOLDOWN = 1800  # 30 minutes minimum between updates per asset

# Per-symbol last update timestamp (in-memory, persists during bot session)
SLTP_LAST_UPDATE = {}  # {symbol: timestamp}

# --- MODULE-SPECIFIC ASSET LISTS ---
# These can be toggled via /assets menu

# 1. SHARK MODE (Crash/Sniper Targets)
# High beta assets that crash hard when market dumps
SHARK_TARGETS = [
    '1000PEPEUSDT', 'WIFUSDT', 'SOLUSDT', 'SUIUSDT', 
    'BONKUSDT', 'FLOKIUSDT', 'TRBUSDT', 'DOGEUSDT'
]

# 2. SCALPING (High Volatility & Momentum)
# Assets with clean impulse moves
SCALPING_ASSETS = [
    'SOLUSDT', 'WIFUSDT', '1000PEPEUSDT', 'SUIUSDT', 'AVAXUSDT',
    'DOGEUSDT', 'RENDERUSDT', 'NEARUSDT', 'FTMUSDT', 'INJUSDT', 'SEIUSDT'
]

# 3. GRID TRADING (Sideways/Range)
# Stable assets that respect support/resistance
GRID_ASSETS = [
    'ADAUSDT', 'XRPUSDT', 'LTCUSDT', 'LINKUSDT', 
    'DOTUSDT', 'MATICUSDT', 'XLMUSDT', 'EOSUSDT'
]

# 4. MEAN REVERSION (Solid/Bluechip)
# Assets that reliably return to EMA
MEAN_REV_ASSETS = [
    'BNBUSDT', 'ETHUSDT', 'ZECUSDT', 
    'UNIUSDT', 'AAVEUSDT', 'ATOMUSDT'
]

# Runtime Blacklist (Global - applies to main scanner)
DISABLED_ASSETS = set()

# Global Settings
USE_QUANTUM_ENGINE = True
