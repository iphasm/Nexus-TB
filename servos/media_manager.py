import os
from typing import Optional

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ICONS_DIR = os.path.join(BASE_DIR, "assets", "icons")
PERSISTENT_ICONS_DIR = os.path.join(BASE_DIR, "data", "icons")
DEFAULT_ICON = os.path.join(PROJECT_ICONS_DIR, "nexus_default.png")

class MediaManager:
    """
    Manages access to asset visual media (Icons/Logos).
    """
    
    @staticmethod
    def get_icon_path(symbol: str) -> Optional[str]:
        """
        Finds the local icon path for a given symbol.
        Checks both project assets and persistent data directories.
        
        Example: BTCUSDT -> assets/icons/btc.png
        """
        # 1. Normalize Symbol (BTCUSDT -> btc)
        clean_symbol = symbol.replace("USDT", "").lower()
        
        # Possible extensions
        extensions = [".png", ".jpg", ".jpeg", ".webp"]
        
        # 2. Check Directories
        search_dirs = [PERSISTENT_ICONS_DIR, PROJECT_ICONS_DIR]
        
        for directory in search_dirs:
            if not os.path.exists(directory):
                continue
                
            for ext in extensions:
                path = os.path.join(directory, f"{clean_symbol}{ext}")
                if os.path.exists(path):
                    return path
                    
        # 3. Fallback to default if exists
        if os.path.exists(DEFAULT_ICON):
            return DEFAULT_ICON
            
        return None

    @staticmethod
    def list_missing_icons(symbols: list) -> list:
        """Helper to identify which assets lack a custom icon."""
        missing = []
        for s in symbols:
            if not MediaManager.get_icon_path(s):
                missing.append(s)
        return missing
