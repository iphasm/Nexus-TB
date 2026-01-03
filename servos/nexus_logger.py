"""
NEXUS LOGGER - LEGACY COMPATIBILITY LAYER
========================================

⚠️  DEPRECATED: This module has been replaced by Voight-Kampff.
   All logging functionality has been migrated to servos/voight_kampff.py

   For new code, use: from servos.voight_kampff import voight_kampff as logger
   This file is kept for backward compatibility only.
"""

# Import everything from the new Voight-Kampff system
from servos.voight_kampff import voight_kampff as nexus_logger

# Legacy compatibility - expose the same interface
__all__ = ['nexus_logger', 'NexusLogger']

# Create alias for backward compatibility
NexusLogger = type(nexus_logger)
