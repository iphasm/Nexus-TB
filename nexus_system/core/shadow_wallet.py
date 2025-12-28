"""
Shadow Wallet - Real-time Local State Manager
Maintains an in-memory mirror of account balances and positions to reduce API latency.
"""

from typing import Dict, Any, Optional
import time

class ShadowWallet:
    def __init__(self):
        # Structure: {'BINANCE': {'total': 100.0, 'available': 50.0}, 'BYBIT': ...}
        self.balances: Dict[str, Dict[str, float]] = {
            'BINANCE': {'total': 0.0, 'available': 0.0},
            'BYBIT': {'total': 0.0, 'available': 0.0},
            'ALPACA': {'total': 0.0, 'available': 0.0}
        }
        
        # Structure: {'BTCUSDT': {'side': 'LONG', 'quantity': 0.1, ...}}
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        self.last_update: float = 0
        self._listeners = []

    def update_balance(self, exchange: str, balance_data: Dict[str, float]):
        """Update balance for a specific exchange."""
        exchange = exchange.upper()
        if exchange in self.balances:
            self.balances[exchange].update(balance_data)
            self.last_update = time.time()
            self._notify_listeners('balance', exchange)

    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """Update a specific position."""
        if position_data.get('quantity', 0) == 0:
            if symbol in self.positions:
                del self.positions[symbol]
        else:
            self.positions[symbol] = position_data
        
        self.last_update = time.time()
        self._notify_listeners('position', symbol)

    def get_unified_equity(self) -> float:
        """Get total equity across all exchanges in USD."""
        total = 0.0
        for b in self.balances.values():
            total += b.get('total', 0.0)
        return total

    def get_available_balance(self, exchange: str) -> float:
        """Get available balance for a specific exchange."""
        return self.balances.get(exchange.upper(), {}).get('available', 0.0)

    def add_listener(self, callback):
        """Add a listener for updates."""
        self._listeners.append(callback)

    def _notify_listeners(self, update_type: str, key: str):
        for callback in self._listeners:
            try:
                callback(update_type, key)
            except Exception as e:
                print(f"ShadowWallet Listener Error: {e}")
