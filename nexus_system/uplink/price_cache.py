"""
Nexus System - Price Cache
In-memory storage for real-time candle data from WebSocket streams.
Provides DataFrame interface compatible with existing MarketStream.
"""

import pandas as pd
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading


class PriceCache:
    """
    Thread-safe in-memory cache for candle data.
    Maintains rolling window of candles per symbol.
    """
    
    def __init__(self, max_candles: int = 250):
        """
        Initialize price cache.
        
        Args:
            max_candles: Maximum candles to store per symbol (default 250 for EMA200)
        """
        self.max_candles = max_candles
        self._candles: Dict[str, List[dict]] = defaultdict(list)
        self._last_update: Dict[str, datetime] = {}
        self._lock = threading.Lock()
        
    def update_candle(self, symbol: str, candle: dict):
        """
        Update or append a candle.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            candle: Candle dict with keys: timestamp, open, high, low, close, volume, is_closed
        """
        with self._lock:
            candles = self._candles[symbol]
            
            if candle.get('is_closed', False):
                # Candle is finalized - check if we need to update last or append
                if candles:
                    last = candles[-1]
                    if last.get('timestamp') == candle.get('timestamp'):
                        # Update existing candle (was open, now closed)
                        candles[-1] = candle
                    else:
                        # New candle
                        candles.append(candle)
                else:
                    candles.append(candle)
                    
                # Trim to max size
                if len(candles) > self.max_candles:
                    self._candles[symbol] = candles[-self.max_candles:]
            else:
                # Candle is still open - update or append
                if candles:
                    last = candles[-1]
                    if last.get('timestamp') == candle.get('timestamp'):
                        # Update in-progress candle
                        candles[-1] = candle
                    elif not last.get('is_closed', True):
                        # Replace previous open candle
                        candles[-1] = candle
                    else:
                        # New open candle
                        candles.append(candle)
                else:
                    candles.append(candle)
                    
            self._last_update[symbol] = datetime.now()
    
    def get_candles(self, symbol: str) -> List[dict]:
        """Get raw candle list for a symbol."""
        with self._lock:
            return list(self._candles.get(symbol, []))
    
    def get_dataframe(self, symbol: str) -> pd.DataFrame:
        """
        Get candles as DataFrame (compatible with MarketStream output).
        
        Args:
            symbol: Trading pair
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        candles = self.get_candles(symbol)
        
        if not candles:
            return pd.DataFrame()
            
        df = pd.DataFrame(candles)
        
        # Ensure required columns exist
        required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in df.columns:
                df[col] = 0
        
        # Convert timestamp to datetime if needed
        if 'timestamp' in df.columns and df['timestamp'].dtype in ['int64', 'float64']:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
        return df[required]
    
    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get the most recent close price for a symbol."""
        candles = self.get_candles(symbol)
        if candles:
            return candles[-1].get('close')
        return None
    
    def get_last_update(self, symbol: str) -> Optional[datetime]:
        """Get timestamp of last update for a symbol."""
        return self._last_update.get(symbol)
    
    def is_stale(self, symbol: str, max_age_seconds: int = 120) -> bool:
        """
        Check if cached data is stale.
        
        Args:
            symbol: Trading pair
            max_age_seconds: Maximum age before considered stale
            
        Returns:
            True if data is stale or missing
        """
        last_update = self._last_update.get(symbol)
        if not last_update:
            return True
        age = (datetime.now() - last_update).total_seconds()
        return age > max_age_seconds
    
    def get_symbols(self) -> List[str]:
        """Get list of all cached symbols."""
        with self._lock:
            return list(self._candles.keys())
    
    def clear(self, symbol: str = None):
        """
        Clear cache for a symbol or all symbols.
        
        Args:
            symbol: Symbol to clear, or None to clear all
        """
        with self._lock:
            if symbol:
                self._candles.pop(symbol, None)
                self._last_update.pop(symbol, None)
            else:
                self._candles.clear()
                self._last_update.clear()
    
    def backfill(self, symbol: str, candles: List[dict]):
        """
        Backfill historical candles (e.g., from REST API on reconnect).
        
        Args:
            symbol: Trading pair
            candles: List of candle dicts (oldest first)
        """
        with self._lock:
            # Normalize timestamps to integers for comparison
            def normalize_ts(ts):
                if ts is None:
                    return 0
                if hasattr(ts, 'timestamp'):  # pandas Timestamp
                    return int(ts.timestamp() * 1000)
                if isinstance(ts, (int, float)):
                    return int(ts)
                return 0
            
            # Merge with existing, avoiding duplicates
            existing_timestamps = {normalize_ts(c.get('timestamp')) for c in self._candles[symbol]}
            
            for candle in candles:
                ts = normalize_ts(candle.get('timestamp'))
                if ts not in existing_timestamps:
                    self._candles[symbol].append(candle)
                    existing_timestamps.add(ts)
            
            # Sort by timestamp (normalized) and trim
            self._candles[symbol] = sorted(
                self._candles[symbol], 
                key=lambda x: normalize_ts(x.get('timestamp'))
            )[-self.max_candles:]
            
            self._last_update[symbol] = datetime.now()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'symbols': len(self._candles),
                'total_candles': sum(len(c) for c in self._candles.values()),
                'symbols_detail': {
                    k: {
                        'count': len(v),
                        'last_update': self._last_update.get(k, 'N/A')
                    }
                    for k, v in self._candles.items()
                }
            }


# Global singleton for shared access
_price_cache: Optional[PriceCache] = None
_alpaca_price_cache: Optional[PriceCache] = None


def get_price_cache() -> PriceCache:
    """Get global price cache instance (Binance)."""
    global _price_cache
    if _price_cache is None:
        _price_cache = PriceCache()
    return _price_cache


def get_alpaca_price_cache() -> PriceCache:
    """Get global price cache instance (Alpaca stocks/ETFs)."""
    global _alpaca_price_cache
    if _alpaca_price_cache is None:
        _alpaca_price_cache = PriceCache()
    return _alpaca_price_cache

