
# Dynamic configuration for the Quantum Engine
# This file is imported by both the Engine (background) and Main (foreground).

# --- STRATEGY CONFIG ---
ENABLED_STRATEGIES = {
    'SCALPING': True,      # High Risk, High Reward
    'GRID': True,          # Grid Trading for sideways
    'MEAN_REVERSION': True, # Default safe strategy
    'BLACK_SWAN': True,    # Defense: Cancel longs during crashes
    'SHARK': False         # Attack: Open shorts during crashes (OFF by default)
}

# SL/TP Update Flag
ALLOW_SLTP_UPDATE = True

# Cooldown for SLTP updates (seconds) - prevents spam on open positions
SLTP_UPDATE_COOLDOWN = 900  # 15 minutes minimum between updates per asset

# --- MODULE-SPECIFIC ASSET LISTS ---
# These can be toggled via /assets menu

# Shark Mode: Assets to SHORT during market crashes
SHARK_TARGETS = ['1000PEPEUSDT', 'SOLUSDT', 'WIFUSDT', 'RENDERUSDT', 'SUIUSDT']

# Scalping: High volatility assets for quick trades
SCALPING_ASSETS = ['ZECUSDT', 'SUIUSDT', 'SOLUSDT', 'BTCUSDT', 'ETHUSDT']

# Grid Trading: Range-bound assets for grid strategy
GRID_ASSETS = ['ADAUSDT', 'ZECUSDT']

# Mean Reversion: Empty = use all non-blacklisted assets
MEAN_REV_ASSETS = []

# Runtime Blacklist (Global - applies to main scanner)
DISABLED_ASSETS = set()

# Global Settings
USE_QUANTUM_ENGINE = True
