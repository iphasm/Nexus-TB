"""
Dynamic Cooldown Manager for NEXUS TRADING BOT
Intelligently adjusts signal cooldown based on frequency and market volatility
"""

import time
from typing import Dict, Tuple
from collections import deque
import asyncio


class DynamicCooldownManager:
    """
    Manages per-symbol cooldowns with dynamic adjustment based on:
    1. Signal frequency (signals per hour)
    2. Market volatility (ATR changes)
    """
    
    def __init__(self, default_cooldown: int = 300):
        """
        Args:
            default_cooldown: Default cooldown in seconds (5 minutes)
        """
        self.default_cooldown = default_cooldown
        
        # Track last alert time per symbol
        self._last_alert: Dict[str, float] = {}
        
        # Track signal history: symbol -> deque of timestamps (last hour)
        self._signal_history: Dict[str, deque] = {}
        
        # Track ATR history for volatility detection
        self._atr_history: Dict[str, deque] = {}
        
        # Current cooldown per symbol
        self._cooldowns: Dict[str, int] = {}
        
    def _build_key(self, symbol: str, exchange: str = None, strategy: str = None, regime: str = None) -> str:
        """Build a cooldown key. Supports symbol, exchange, strategy, and regime."""
        key_parts = [symbol]
        if exchange:
            key_parts.append(exchange)
        if strategy:
            key_parts.append(strategy)
        if regime:
            key_parts.append(regime)
        return ":".join(key_parts)

    def is_on_cooldown(self, symbol: str, exchange: str = None, strategy: str = None, regime: str = None) -> bool:
        """Check if symbol (scoped by exchange/strategy/regime) is still on cooldown."""
        # Check multiple levels: specific first, then fallback to broader scopes
        keys_to_check = [
            self._build_key(symbol, exchange, strategy, regime),  # Most specific
            self._build_key(symbol, exchange, strategy),          # Strategy level
            self._build_key(symbol, exchange),                     # Exchange level
            self._build_key(symbol)                                # Symbol level only
        ]

        for key in keys_to_check:
            if key in self._last_alert:
                cooldown = self._get_cooldown(key)
                elapsed = time.time() - self._last_alert[key]
                if elapsed < cooldown:
                    return True

        return False
    
    def set_cooldown(self, symbol: str, atr: float = None, exchange: str = None, strategy: str = None, regime: str = None, seconds: int = None):
        """Mark symbol as alerted and record signal. Scoped per exchange/strategy/regime."""
        key = self._build_key(symbol, exchange, strategy, regime)
        current_time = time.time()
        self._last_alert[key] = current_time
        
        # Record signal timestamp
        if key not in self._signal_history:
            self._signal_history[key] = deque(maxlen=20)  # Keep last 20 signals
        self._signal_history[key].append(current_time)
        
        # Record ATR if provided
        if atr is not None:
            if key not in self._atr_history:
                self._atr_history[key] = deque(maxlen=10)  # Keep last 10 ATR values
            self._atr_history[key].append(atr)
        
        # Recalculate cooldown for this symbol
        self._update_cooldown(key, override_seconds=seconds)
    
    def _get_cooldown(self, key: str) -> int:
        """Get current cooldown for symbol/exchange key."""
        return self._cooldowns.get(key, self.default_cooldown)
    
    def _update_cooldown(self, key: str, override_seconds: int = None):
        """
        Dynamically adjust cooldown based on signal frequency and volatility.
        
        Rules:
        - High frequency (>4 signals/hr) → Increase to 15 min (900s)
        - Normal frequency (1-4/hr) → Keep default 5 min (300s)
        - Low frequency (<1/hr) → Reduce to 3 min (180s)
        - High volatility → Reduce by 20% (faster reaction)
        - Low volatility → Increase by 50% (filter noise)
        """
        # Calculate signal frequency
        frequency = self._calculate_frequency(key)
        
        # Calculate volatility factor
        volatility_factor = self._calculate_volatility_factor(key)
        
        # Base cooldown based on frequency
        if frequency > 4.0:
            # High frequency - increase cooldown to reduce spam
            base_cooldown = 900  # 15 minutes
        elif frequency >= 1.0:
            # Normal frequency
            base_cooldown = 300  # 5 minutes
        else:
            # Low frequency - reduce cooldown to catch signals faster
            base_cooldown = 180  # 3 minutes
        
        # Adjust for volatility
        if volatility_factor > 1.5:
            # High volatility - reduce cooldown for faster reaction
            adjusted_cooldown = int(base_cooldown * 0.8)
        elif volatility_factor < 0.7:
            # Low volatility - increase cooldown to filter noise
            adjusted_cooldown = int(base_cooldown * 1.5)
        else:
            # Normal volatility
            adjusted_cooldown = base_cooldown
        
        # Override if explicit seconds provided (e.g., freeze asset)
        if override_seconds is not None:
            adjusted_cooldown = override_seconds
        
        # Store calculated cooldown
        self._cooldowns[key] = adjusted_cooldown
        
        # Log adjustment for debugging
        print(f"📊 Cooldown adjusted for {key}: {adjusted_cooldown}s "
              f"(freq: {frequency:.1f}/hr, vol: {volatility_factor:.2f}x)")
    
    def _calculate_frequency(self, key: str) -> float:
        """
        Calculate signals per hour for the symbol.
        
        Returns:
            float: Signals per hour (0.0 if no history)
        """
        if key not in self._signal_history:
            return 0.0
        
        history = self._signal_history[key]
        if len(history) < 2:
            return 0.0
        
        # Get signals from last hour
        current_time = time.time()
        one_hour_ago = current_time - 3600
        
        recent_signals = [ts for ts in history if ts > one_hour_ago]
        
        if len(recent_signals) < 2:
            return 0.0
        
        # Calculate rate
        time_span = current_time - recent_signals[0]
        if time_span == 0:
            return 0.0
        
        # Extrapolate to per-hour rate
        signals_per_hour = (len(recent_signals) / time_span) * 3600
        
        return signals_per_hour
    
    def _calculate_volatility_factor(self, key: str) -> float:
        """
        Calculate volatility factor based on ATR changes.
        
        Returns:
            float: Volatility factor (1.0 = normal, >1.5 = high, <0.7 = low)
        """
        if key not in self._atr_history or len(self._atr_history[key]) < 3:
            return 1.0  # Normal volatility if no data
        
        atr_values = list(self._atr_history[key])
        
        # Calculate average ATR
        avg_atr = sum(atr_values) / len(atr_values)
        
        if avg_atr == 0:
            return 1.0
        
        # Compare latest ATR to average
        latest_atr = atr_values[-1]
        volatility_factor = latest_atr / avg_atr
        
        return volatility_factor
    
    def get_status(self, symbol: str, exchange: str = None) -> Dict:
        """Get cooldown status for a symbol (optionally scoped to an exchange)."""
        key = self._build_key(symbol, exchange)
        cooldown = self._get_cooldown(key)
        frequency = self._calculate_frequency(key)
        volatility = self._calculate_volatility_factor(key)
        
        if key in self._last_alert:
            elapsed = time.time() - self._last_alert[key]
            remaining = max(0, cooldown - elapsed)
        else:
            elapsed = 0
            remaining = 0
        
        return {
            'symbol': symbol,
            'exchange': exchange,
            'cooldown_seconds': cooldown,
            'remaining_seconds': remaining,
            'signals_per_hour': frequency,
            'volatility_factor': volatility,
            'on_cooldown': self.is_on_cooldown(symbol, exchange)
        }
    
    def reset(self, symbol: str, exchange: str = None):
        """Reset cooldown for a symbol (optionally per exchange)."""
        key = self._build_key(symbol, exchange)
        if key in self._last_alert:
            del self._last_alert[key]
        if key in self._cooldowns:
            del self._cooldowns[key]
    
    def reset_all(self):
        """Reset all cooldowns."""
        self._last_alert.clear()
        self._signal_history.clear()
        self._atr_history.clear()
        self._cooldowns.clear()

