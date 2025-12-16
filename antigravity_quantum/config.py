
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

# --- AI FILTER MODULE ---
# Master switch for OpenAI sentiment analysis filter
# When OFF: Bypasses AI sentiment check, trades execute without IA validation
AI_FILTER_ENABLED = True

# --- MODULE-SPECIFIC ASSET LISTS ---
# Intelligent classification based on market logic

# 1. TREND FOLLOWING (Major dominance, long-term momentum)
# Only BTC and ETH - these drive market direction
TREND_ASSETS = ['BTCUSDT', 'ETHUSDT']

# 2. SHARK MODE (Crash/Sniper Targets)
# High beta assets that crash hard when market dumps + volatile tech stocks
SHARK_TARGETS = [
    '1000PEPEUSDT', 'WIFUSDT', 'SOLUSDT', 'SUIUSDT', 
    'BONKUSDT', 'FLOKIUSDT', 'DOGEUSDT',
    'TSLA', 'NVDA'  # Tech stocks with high beta
]

# 3. SCALPING (High Volatility & Momentum)
# CRYPTO ONLY - Stocks don't have enough intraday volatility
SCALPING_ASSETS = [
    'SOLUSDT', 'WIFUSDT', '1000PEPEUSDT', 'SUIUSDT', 'AVAXUSDT',
    'DOGEUSDT', 'RENDERUSDT', 'NEARUSDT', 'FTMUSDT', 'INJUSDT', 
    'SEIUSDT', 'BONKUSDT', 'FLOKIUSDT'
]

# 4. GRID TRADING (Sideways/Range)
# CRYPTO ONLY - Blue chips with consistent support/resistance
GRID_ASSETS = [
    'ADAUSDT', 'XRPUSDT', 'LTCUSDT', 'LINKUSDT', 
    'DOTUSDT', 'MATICUSDT', 'XLMUSDT', 'EOSUSDT'
]

# 5. MEAN REVERSION (All asset classes)
# Assets that reliably revert to EMA - includes Stocks & Commodities
MEAN_REV_ASSETS = [
    # Crypto
    'BNBUSDT', 'ETHUSDT', 'ZECUSDT', 'UNIUSDT', 'AAVEUSDT', 'ATOMUSDT',
    # Stocks (Alpaca)
    'TSLA', 'NVDA', 'MSFT', 'AAPL', 'AMD',
    # Commodities (Alpaca ETFs)
    'GLD', 'SLV', 'USO', 'UNG', 'CPER'
]

# Runtime Blacklist (Global - applies to main scanner)
DISABLED_ASSETS = set()

# Global Settings
USE_QUANTUM_ENGINE = True
