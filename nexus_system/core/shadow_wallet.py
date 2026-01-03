"""
Shadow Wallet - Real-time Local State Manager
Maintains an in-memory mirror of account balances and positions to reduce API latency.
PER-USER ISOLATION: Each chat_id has its own wallet state.
"""

from typing import Dict, Any, Optional
import time

class ShadowWallet:
    """
    Per-user isolated wallet state manager.
    Structure: {chat_id: {'balances': {...}, 'positions': {...}}}
    """
    def __init__(self, chat_id: str = None):
        # Per-user isolation: each chat_id has its own wallet state
        self.chat_id = chat_id
        self.user_wallets: Dict[str, Dict[str, Any]] = {}

        # Global listeners (shared across all users)
        self._listeners = []

    def _get_user_wallet(self, chat_id: str) -> Dict[str, Any]:
        """Get or create wallet state for a specific user."""
        if chat_id not in self.user_wallets:
            self.user_wallets[chat_id] = {
                'balances': {
                    'BINANCE': {'total': 0.0, 'available': 0.0},
                    'BYBIT': {'total': 0.0, 'available': 0.0},
                    'ALPACA': {'total': 0.0, 'available': 0.0}
                },
                'positions': {},
                'last_update': 0
            }
        return self.user_wallets[chat_id]

    # LEGACY METHODS - Kept for backward compatibility but now per-user
    @property
    def balances(self) -> Dict[str, Dict[str, float]]:
        """Legacy: Get balances for current user (if set) or raise error."""
        if not self.chat_id:
            raise ValueError("ShadowWallet: chat_id not set. Use update_balance(chat_id, exchange, balance_data)")
        return self._get_user_wallet(self.chat_id)['balances']

    @property
    def positions(self) -> Dict[str, Dict[str, Any]]:
        """Legacy: Get positions for current user (if set) or raise error."""
        if not self.chat_id:
            raise ValueError("ShadowWallet: chat_id not set. Use update_position(chat_id, symbol, position_data)")
        return self._get_user_wallet(self.chat_id)['positions']

    @property
    def last_update(self) -> float:
        """Legacy: Get last update for current user."""
        if not self.chat_id:
            return 0
        return self._get_user_wallet(self.chat_id)['last_update']

    def update_balance(self, chat_id: str, exchange: str, balance_data: Dict[str, float]):
        """Update balance for a specific user and exchange."""
        user_wallet = self._get_user_wallet(chat_id)
        exchange = exchange.upper()

        if exchange in user_wallet['balances']:
            user_wallet['balances'][exchange].update(balance_data)
            user_wallet['last_update'] = time.time()
            self._notify_listeners('balance', f"{chat_id}:{exchange}")

    def update_position(self, chat_id: str, symbol: str, position_data: Dict[str, Any]):
        """Update a specific position for a user."""
        user_wallet = self._get_user_wallet(chat_id)

        if position_data.get('quantity', 0) == 0:
            if symbol in user_wallet['positions']:
                del user_wallet['positions'][symbol]
        else:
            user_wallet['positions'][symbol] = position_data

        user_wallet['last_update'] = time.time()
        self._notify_listeners('position', f"{chat_id}:{symbol}")

    # LEGACY METHODS - For backward compatibility during migration
    def update_balance_legacy(self, exchange: str, balance_data: Dict[str, float]):
        """Legacy method - requires chat_id to be set."""
        if not self.chat_id:
            raise ValueError("ShadowWallet: chat_id not set for legacy method")
        self.update_balance(self.chat_id, exchange, balance_data)

    def update_position_legacy(self, symbol: str, position_data: Dict[str, Any]):
        """Legacy method - requires chat_id to be set."""
        if not self.chat_id:
            raise ValueError("ShadowWallet: chat_id not set for legacy method")
        self.update_position(self.chat_id, symbol, position_data)

    def get_unified_equity(self, chat_id: str) -> float:
        """Get total equity across all exchanges for a specific user."""
        user_wallet = self._get_user_wallet(chat_id)
        total = 0.0
        for b in user_wallet['balances'].values():
            total += b.get('total', 0.0)
        return total

    def get_available_balance(self, chat_id: str, exchange: str) -> float:
        """Get available balance for a specific user and exchange."""
        user_wallet = self._get_user_wallet(chat_id)
        return user_wallet['balances'].get(exchange.upper(), {}).get('available', 0.0)

    # LEGACY METHODS - For backward compatibility
    def get_unified_equity_legacy(self) -> float:
        """Legacy method - requires chat_id to be set."""
        if not self.chat_id:
            return 0.0
        return self.get_unified_equity(self.chat_id)

    def get_available_balance_legacy(self, exchange: str) -> float:
        """Legacy method - requires chat_id to be set."""
        if not self.chat_id:
            return 0.0
        return self.get_available_balance(self.chat_id, exchange)

    def add_listener(self, callback):
        """Add a listener for updates."""
        self._listeners.append(callback)

    def _notify_listeners(self, update_type: str, key: str):
        for callback in self._listeners:
            try:
                callback(update_type, key)
            except Exception as e:
                print(f"ShadowWallet Listener Error: {e}")
