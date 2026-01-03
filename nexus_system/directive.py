
# Dynamic configuration for the Nexus Core
# This file is imported by both the Engine (background) and Main (foreground).

from system_directive import (
    ENABLED_STRATEGIES, 
    GROUP_CONFIG, 
    RISK_PER_TRADE_PCT, 
    ALLOW_SLTP_UPDATE,
    SLTP_UPDATE_COOLDOWN,
    AI_FILTER_ENABLED,
    ML_CLASSIFIER_ENABLED,
    SHARK_TARGETS,
    DISABLED_ASSETS
)

# Global Settings
USE_NEXUS_ENGINE = True

# Per-symbol last update timestamp (in-memory, persists during bot session)
SLTP_LAST_UPDATE = {}  # {symbol: timestamp}
