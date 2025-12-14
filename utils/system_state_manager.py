
import json
import os
import logging
from typing import Dict, Any

STATE_FILE = "bot_state.json"

class SystemStateManager:
    def __init__(self, state_file=STATE_FILE):
        self.state_file = state_file
        self.default_state = {
            "enabled_strategies": {
                "SCALPING": False,
                "GRID": False,
                "MEAN_REVERSION": True,
                "BLACK_SWAN": True,
                "SHARK": False
            },
            "group_config": {
                "CRYPTO": True,
                "STOCKS": False,
                "COMMODITY": False
            },
            "disabled_assets": [],
            "module_assets": {
                "SHARK_TARGETS": [],
                "SCALPING_ASSETS": [],
                "GRID_ASSETS": [],
                "MEAN_REV_ASSETS": []
            },
            "session_config": {
                "leverage": 5,
                "max_capital_pct": 0.1,
                "personality": "STANDARD_ES",
                "mode": "WATCHER"
            }
        }

    def load_state(self) -> Dict[str, Any]:
        """Loads state from PostgreSQL first, then JSON fallback."""
        # Try PostgreSQL first
        try:
            from utils.db import load_bot_state
            db_state = load_bot_state()
            if db_state is not None:
                merged = self.default_state.copy()
                for key, val in db_state.items():
                    if isinstance(val, dict) and key in merged:
                        merged[key].update(val)
                    else:
                        merged[key] = val
                return merged
        except Exception as e:
            print(f"⚠️ PostgreSQL state load failed: {e}")
        
        # JSON Fallback
        if not os.path.exists(self.state_file):
            print(f"⚠️ State file '{self.state_file}' not found. Using defaults.")
            return self.default_state.copy()

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                merged_state = self.default_state.copy()
                
                for key, val in state.items():
                    if isinstance(val, dict) and key in merged_state:
                         merged_state[key].update(val)
                    else:
                        merged_state[key] = val
                
                print(f"✅ State loaded from '{self.state_file}'")
                
                # Apply module assets to config.py
                self._apply_module_assets(merged_state)
                
                return merged_state
        except Exception as e:
            print(f"❌ Error loading state: {e}. Using defaults.")
            return self.default_state.copy()
    
    def _apply_module_assets(self, state: Dict):
        """Applies saved module asset lists back to config.py"""
        if "module_assets" not in state:
            return
            
        try:
            import antigravity_quantum.config as cfg
            ma = state["module_assets"]
            
            # Clear and update each list
            if "SHARK_TARGETS" in ma:
                cfg.SHARK_TARGETS.clear()
                cfg.SHARK_TARGETS.extend(ma["SHARK_TARGETS"])
                
            if "SCALPING_ASSETS" in ma:
                cfg.SCALPING_ASSETS.clear()
                cfg.SCALPING_ASSETS.extend(ma["SCALPING_ASSETS"])
                
            if "GRID_ASSETS" in ma:
                cfg.GRID_ASSETS.clear()
                cfg.GRID_ASSETS.extend(ma["GRID_ASSETS"])
                
            if "MEAN_REV_ASSETS" in ma:
                cfg.MEAN_REV_ASSETS.clear()
                cfg.MEAN_REV_ASSETS.extend(ma["MEAN_REV_ASSETS"])
                
            print(f"✅ Module assets restored from state")
        except Exception as e:
            print(f"⚠️ Failed to apply module assets: {e}")

    def save_state(self, enabled_strategies: Dict, group_config: Dict, disabled_assets: set, session: Any = None):
        """Saves current runtime state to PostgreSQL first, then JSON fallback."""
        
        session_cfg = self.default_state["session_config"]
        if session and session.config:
            session_cfg = session.config.copy()
            if 'mode' not in session_cfg:
                session_cfg['mode'] = 'WATCHER'

        # Try PostgreSQL first
        try:
            from utils.db import save_bot_state
            if save_bot_state(enabled_strategies, group_config, disabled_assets):
                return  # Success
        except Exception as e:
            print(f"⚠️ PostgreSQL state save failed: {e}")

        # Collect module assets from config.py
        module_assets = {}
        try:
            import antigravity_quantum.config as cfg
            module_assets = {
                "SHARK_TARGETS": list(cfg.SHARK_TARGETS),
                "SCALPING_ASSETS": list(cfg.SCALPING_ASSETS),
                "GRID_ASSETS": list(cfg.GRID_ASSETS),
                "MEAN_REV_ASSETS": list(cfg.MEAN_REV_ASSETS)
            }
        except Exception as e:
            print(f"⚠️ Failed to collect module assets: {e}")

        # JSON Fallback
        state = {
            "enabled_strategies": enabled_strategies,
            "group_config": group_config,
            "disabled_assets": list(disabled_assets),
            "module_assets": module_assets,
            "session_config": session_cfg
        }

        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4)
            print(f"💾 State saved (incl. module assets)")
        except Exception as e:
            print(f"❌ Error saving state: {e}")

