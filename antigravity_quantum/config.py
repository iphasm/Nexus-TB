
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
# When OFF: Bypasses AI sentiment check, trades execute without IA validation
AI_FILTER_ENABLED = True

# --- PREMIUM SIGNALS (MTF & Volume) ---
# When ON: Strategies use Multi-Timeframe + Volume validation (stricter but better)
PREMIUM_SIGNALS_ENABLED = False

# --- RISK MANAGEMENT CONFIG ---
# Percentage of account equity to risk per trade (e.g., 0.01 = 1% risk)
# Used when ATR-based sizing is active.
RISK_PER_TRADE_PCT = 0.01 

# --- MODULE-SPECIFIC ASSET LISTS ---
# Intelligent classification based on market logic

# NOTE: TREND, SCALPING, GRID, MEAN_REV lists have been deprecated
# in favor of Dynamic Market Classifier (strategies/classifier.py).

# SHARK MODE (Crash/Sniper Targets)
# Specific targets for Black Swan Defense (SharkSentinel)
SHARK_TARGETS = [
    '1000PEPEUSDT', 'WIFUSDT', 'SOLUSDT', 'SUIUSDT', 
    'BONKUSDT', 'FLOKIUSDT', 'DOGEUSDT'
]

# Runtime Blacklist (Global - applies to main scanner)
DISABLED_ASSETS = set()

# Global Settings
USE_QUANTUM_ENGINE = True
