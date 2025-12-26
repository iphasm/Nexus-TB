import logging
import os
import sys
import time
from typing import Dict

# Environment Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure Root Logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Silence Noisy Libraries
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("yfinance").setLevel(logging.WARNING)

class NexusLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        self._last_log: Dict[str, float] = {}

    def info(self, msg: str):
        self.logger.info(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
        
    def error(self, msg: str):
        self.logger.error(msg)
        
    def info_debounced(self, msg: str, interval: float = 60.0):
        """Log info only if 'interval' seconds have passed since last identical log."""
        self._log_debounced(logging.INFO, msg, interval)
        
    def warning_debounced(self, msg: str, interval: float = 60.0):
        """Log warning only if 'interval' seconds have passed since last identical log."""
        self._log_debounced(logging.WARNING, msg, interval)
        
    def error_debounced(self, msg: str, interval: float = 60.0):
        """Log error only if 'interval' seconds have passed since last identical log."""
        self._log_debounced(logging.ERROR, msg, interval)

    def _log_debounced(self, level: int, msg: str, interval: float):
        now = time.time()
        last_time = self._last_log.get(msg, 0)
        
        if now - last_time > interval:
            self.logger.log(level, msg)
            self._last_log[msg] = now

def get_logger(name: str) -> NexusLogger:
    return NexusLogger(name)
