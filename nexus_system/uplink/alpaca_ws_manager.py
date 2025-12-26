"""
Nexus System - Alpaca WebSocket Manager
Real-time bar streaming for Stocks/ETFs via Alpaca Data API.
Uses IEX feed (free tier) with 1-minute bars aggregated to 15m.
"""

import asyncio
import os
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict


def is_us_market_open() -> bool:
    """Check if US stock market is currently open (9:30 AM - 4:00 PM ET, Mon-Fri)."""
    et = ZoneInfo("America/New_York")
    now = datetime.now(et)
    
    # Weekday check (Monday=0, Friday=4)
    if now.weekday() > 4:  # Saturday or Sunday
        return False
    
    # Time check: 9:30 AM to 4:00 PM ET
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now <= market_close


class AlpacaWSManager:
    """
    Manages WebSocket connection to Alpaca for real-time bar updates.
    Aggregates 1-minute bars into 15-minute candles for strategy compatibility.
    """
    
    def __init__(self, symbols: List[str], api_key: str = None, api_secret: str = None):
        """
        Initialize WebSocket manager.
        
        Args:
            symbols: List of stock/ETF symbols (e.g., ['TSLA', 'NVDA'])
            api_key: Alpaca API key (or from env APCA_API_KEY_ID)
            api_secret: Alpaca API secret (or from env APCA_API_SECRET_KEY)
        """
        self.symbols = [s.upper() for s in symbols]
        self.api_key = api_key or os.getenv('APCA_API_KEY_ID', '').strip("'\" ")
        self.api_secret = api_secret or os.getenv('APCA_API_SECRET_KEY', '').strip("'\" ")
        
        self.stream = None
        self.running = False
        self.callbacks: List[Callable] = []
        self.last_update: Dict[str, datetime] = {}
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        
        # Aggregation: store 1m bars and aggregate to 15m
        self._minute_bars: Dict[str, List[dict]] = defaultdict(list)
        self._current_15m_start: Dict[str, datetime] = {}
        
    def add_callback(self, callback: Callable):
        """
        Register a callback for candle updates.
        Callback signature: async def callback(symbol: str, candle: dict)
        """
        self.callbacks.append(callback)
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to Alpaca."""
        if not self.api_key or not self.api_secret:
            print("❌ AlpacaWS: No API keys provided")
            return False
        
        if not is_us_market_open():
            print("⚠️ AlpacaWS: US market is closed. WS will activate during market hours.")
            return False
            
        try:
            from alpaca.data.live import StockDataStream
            
            print(f"🔌 AlpacaWS: Connecting to {len(self.symbols)} symbols...")
            
            # Try to use DataFeed enum (newer alpaca-py versions)
            try:
                from alpaca.data.enums import DataFeed
                feed_param = DataFeed.IEX
            except ImportError:
                # Fallback to string for older versions
                feed_param = "iex"
            
            # Create stream with IEX feed (free tier)
            self.stream = StockDataStream(
                self.api_key,
                self.api_secret,
                feed=feed_param
            )
            
            # Register bar handler for each symbol
            async def on_bar_handler(bar):
                await self._process_bar(bar)
            
            self.stream.subscribe_bars(on_bar_handler, *self.symbols)
            
            self.running = True
            self._reconnect_attempts = 0
            print(f"✅ AlpacaWS: Connected ({len(self.symbols)} symbols @ IEX feed)")
            
            return True
            
        except ImportError:
            print("❌ AlpacaWS: 'alpaca-py' package not installed. Run: pip install alpaca-py")
            return False
        except Exception as e:
            print(f"❌ AlpacaWS: Connection failed - {e}")
            return False
    
    async def _process_bar(self, bar):
        """Process incoming 1-minute bar and aggregate to 15m."""
        try:
            symbol = bar.symbol
            
            # Create candle dict from bar
            candle_1m = {
                'timestamp': int(bar.timestamp.timestamp() * 1000),
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': float(bar.volume),
                'is_closed': True
            }
            
            # Aggregate to 15m
            candle_15m = self._aggregate_to_15m(symbol, candle_1m, bar.timestamp)
            
            if candle_15m:
                self.last_update[symbol] = datetime.now()
                
                # Emit to all callbacks
                for callback in self.callbacks:
                    try:
                        await callback(symbol, candle_15m)
                    except Exception as e:
                        print(f"⚠️ AlpacaWS: Callback error for {symbol} - {e}")
                        
        except Exception as e:
            print(f"⚠️ AlpacaWS: Bar processing error - {e}")
    
    def _aggregate_to_15m(self, symbol: str, candle_1m: dict, timestamp: datetime) -> Optional[dict]:
        """
        Aggregate 1-minute bars into 15-minute candles.
        Returns the 15m candle when complete, or updates in-progress candle.
        """
        # Calculate 15m period start
        minute = timestamp.minute
        period_start_minute = (minute // 15) * 15
        period_start = timestamp.replace(minute=period_start_minute, second=0, microsecond=0)
        period_start_ms = int(period_start.timestamp() * 1000)
        
        # Check if this is a new 15m period
        current_start = self._current_15m_start.get(symbol)
        
        if current_start != period_start:
            # New period - emit the previous complete candle if exists
            if symbol in self._minute_bars and self._minute_bars[symbol]:
                # Build complete 15m candle from accumulated 1m bars
                bars = self._minute_bars[symbol]
                complete_candle = {
                    'timestamp': int(current_start.timestamp() * 1000) if current_start else period_start_ms,
                    'open': bars[0]['open'],
                    'high': max(b['high'] for b in bars),
                    'low': min(b['low'] for b in bars),
                    'close': bars[-1]['close'],
                    'volume': sum(b['volume'] for b in bars),
                    'is_closed': True
                }
                
                # Reset for new period
                self._minute_bars[symbol] = [candle_1m]
                self._current_15m_start[symbol] = period_start
                
                return complete_candle
            else:
                # First bar of first period
                self._minute_bars[symbol] = [candle_1m]
                self._current_15m_start[symbol] = period_start
                return None
        else:
            # Same period - accumulate
            self._minute_bars[symbol].append(candle_1m)
            
            # Return in-progress candle (not closed)
            bars = self._minute_bars[symbol]
            return {
                'timestamp': period_start_ms,
                'open': bars[0]['open'],
                'high': max(b['high'] for b in bars),
                'low': min(b['low'] for b in bars),
                'close': bars[-1]['close'],
                'volume': sum(b['volume'] for b in bars),
                'is_closed': False
            }
    
    async def listen(self):
        """Main listening loop - runs the Alpaca stream."""
        if not self.stream:
            print("❌ AlpacaWS: Stream not initialized")
            return
            
        while self.running:
            try:
                # Check market hours
                if not is_us_market_open():
                    print("⏸️ AlpacaWS: Market closed, pausing stream...")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Run stream (blocking)
                print("📡 AlpacaWS: Listening for bars...")
                await self.stream._run_forever()
                
            except Exception as e:
                error_str = str(e).lower()
                if "closed" in error_str or "connection" in error_str:
                    print(f"⚠️ AlpacaWS: Disconnected - {e}")
                    await self._reconnect()
                else:
                    print(f"⚠️ AlpacaWS: Error - {e}")
                    await asyncio.sleep(5)
    
    async def _reconnect(self) -> bool:
        """Attempt to reconnect with exponential backoff."""
        self._reconnect_attempts += 1
        
        if self._reconnect_attempts > self._max_reconnect_attempts:
            print("❌ AlpacaWS: Max reconnection attempts reached")
            return False
            
        wait_time = min(2 ** self._reconnect_attempts, 60)
        print(f"🔄 AlpacaWS: Reconnecting in {wait_time}s (attempt {self._reconnect_attempts})")
        await asyncio.sleep(wait_time)
        
        return await self.connect()
    
    async def close(self):
        """Close WebSocket connection."""
        self.running = False
        
        if self.stream:
            try:
                await self.stream.close()
            except Exception:
                pass
                
        print("🔌 AlpacaWS: Disconnected")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        return {
            'connected': self.running and is_us_market_open(),
            'symbols': len(self.symbols),
            'feed': 'IEX (free)',
            'market_open': is_us_market_open(),
            'last_updates': {k: v.isoformat() for k, v in self.last_update.items()},
            'reconnect_attempts': self._reconnect_attempts
        }


async def test_alpaca_ws():
    """Quick test of Alpaca WebSocket connection."""
    manager = AlpacaWSManager(['TSLA', 'AAPL'])
    
    received = []
    
    async def on_candle(symbol, candle):
        received.append((symbol, candle['close']))
        print(f"📊 {symbol}: ${candle['close']:.2f} (closed={candle['is_closed']})")
        if len(received) >= 5:
            manager.running = False
    
    manager.add_callback(on_candle)
    
    if await manager.connect():
        try:
            await asyncio.wait_for(manager.listen(), timeout=120)
        except asyncio.TimeoutError:
            print("⏱️ Test timeout")
        
    await manager.close()
    print(f"\n✅ Received {len(received)} updates")


if __name__ == "__main__":
    asyncio.run(test_alpaca_ws())
