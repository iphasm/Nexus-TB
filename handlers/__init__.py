# NEXUS TRADING BOT - Async Handlers Package
# This package contains modular routers for aiogram 3.x

from .commands import router as commands_router
from .trading import router as trading_router
from .config import router as config_router
from .callbacks import router as callbacks_router
from .admin import router as admin_router

__all__ = [
    'commands_router',
    'trading_router', 
    'config_router',
    'callbacks_router',
    'admin_router'
]

