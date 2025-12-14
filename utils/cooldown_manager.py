"""
Dynamic Cooldown Manager for Antigravity Bot
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
        
    def is_on_cooldown(self, symbol: str) -> bool:
        """Check if symbol is still on cooldown."""
        if symbol not in self._last_alert:
            return False
        
        cooldown = self._get_cooldown(symbol)
        elapsed = time.time() - self._last_alert[symbol]
        
        return elapsed < cooldown
    
    def set_cooldown(self, symbol: str, atr: float = None):
        """Mark symbol as alerted and record signal."""
        current_time = time.time()
        self._last_alert[symbol] = current_time
        
        # Record signal timestamp
        if symbol not in self._signal_history:
            self._signal_history[symbol] = deque(maxlen=20)  # Keep last 20 signals
        self._signal_history[symbol].append(current_time)
        
        # Record ATR if provided
        if atr is not None:
            if symbol not in self._atr_history:
                self._atr_history[symbol] = deque(maxlen=10)  # Keep last 10 ATR values
            self._atr_history[symbol].append(atr)
        
        # Recalculate cooldown for this symbol
        self._update_cooldown(symbol)
    
    def _get_cooldown(self, symbol: str) -> int:
        """Get current cooldown for symbol."""
        return self._cooldowns.get(symbol, self.default_cooldown)
    
    def _update_cooldown(self, symbol: str):
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
        frequency = self._calculate_frequency(symbol)
        
        # Calculate volatility factor
        volatility_factor = self._calculate_volatility_factor(symbol)
        
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
        
        # Store calculated cooldown
        self._cooldowns[symbol] = adjusted_cooldown
        
        # Log adjustment for debugging
        print(f"📊 Cooldown adjusted for {symbol}: {adjusted_cooldown}s "
              f"(freq: {frequency:.1f}/hr, vol: {volatility_factor:.2f}x)")
    
    def _calculate_frequency(self, symbol: str) -> float:
        """
        Calculate signals per hour for the symbol.
        
        Returns:
            float: Signals per hour (0.0 if no history)
        """
        if symbol not in self._signal_history:
            return 0.0
        
        history = self._signal_history[symbol]
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
    
    def _calculate_volatility_factor(self, symbol: str) -> float:
        """
        Calculate volatility factor based on ATR changes.
        
        Returns:
            float: Volatility factor (1.0 = normal, >1.5 = high, <0.7 = low)
        """
        if symbol not in self._atr_history or len(self._atr_history[symbol]) < 3:
            return 1.0  # Normal volatility if no data
        
        atr_values = list(self._atr_history[symbol])
        
        # Calculate average ATR
        avg_atr = sum(atr_values) / len(atr_values)
        
        if avg_atr == 0:
            return 1.0
        
        # Compare latest ATR to average
        latest_atr = atr_values[-1]
        volatility_factor = latest_atr / avg_atr
        
        return volatility_factor
    
    def get_status(self, symbol: str) -> Dict:
        """Get cooldown status for a symbol."""
        cooldown = self._get_cooldown(symbol)
        frequency = self._calculate_frequency(symbol)
        volatility = self._calculate_volatility_factor(symbol)
        
        if symbol in self._last_alert:
            elapsed = time.time() - self._last_alert[symbol]
            remaining = max(0, cooldown - elapsed)
        else:
            elapsed = 0
            remaining = 0
        
        return {
            'symbol': symbol,
            'cooldown_seconds': cooldown,
            'remaining_seconds': remaining,
            'signals_per_hour': frequency,
            'volatility_factor': volatility,
            'on_cooldown': self.is_on_cooldown(symbol)
        }
    
    def reset(self, symbol: str):
        """Reset cooldown for a symbol."""
        if symbol in self._last_alert:
            del self._last_alert[symbol]
        if symbol in self._cooldowns:
            del self._cooldowns[symbol]
    
    def reset_all(self):
        """Reset all cooldowns."""
        self._last_alert.clear()
        self._signal_history.clear()
        self._atr_history.clear()
        self._cooldowns.clear()
