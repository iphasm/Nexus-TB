"""
Nexus System - Binance WebSocket Manager
Real-time kline streaming for Binance USD-M Futures.
"""

import asyncio
import json
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime

# WebSocket state constants (websockets v15+)
WS_STATE_OPEN = 1



from ..utils.logger import get_logger

class BinanceWSManager:
    """
    Manages WebSocket connections to Binance Futures for real-time kline updates.
    Supports multi-stream subscriptions and automatic reconnection.
    """
    
    BASE_URL = "wss://fstream.binance.com/stream"
    MAX_STREAMS_PER_CONNECTION = 200  # Binance limit
    PING_INTERVAL = 180  # 3 minutes (Binance disconnects after 5 min of silence)
    
    def __init__(self, symbols: List[str], timeframe: str = '15m'):
        """
        Initialize WebSocket manager.
        
        Args:
            symbols: List of symbols to subscribe (e.g., ['BTCUSDT', 'ETHUSDT'])
            timeframe: Kline interval (e.g., '1m', '5m', '15m', '1h')
        """
        self.logger = get_logger("BinanceWS")
        self.symbols = [s.lower() for s in symbols]
        self.timeframe = timeframe
        self.ws = None
        self.running = False
        self.callbacks: List[Callable] = []
        self.last_update: Dict[str, datetime] = {}
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 25  # Increased for stability
        self._ping_task = None
        
        # Proxy support
        import os
        self.proxy = os.getenv('PROXY_URL') or os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
        
    def add_callback(self, callback: Callable):
        """
        Register a callback for kline updates.
        Callback signature: async def callback(symbol: str, candle: dict)
        """
        self.callbacks.append(callback)
        
    def build_stream_url(self) -> str:
        """Build combined stream URL for all symbols."""
        streams = [f"{s}@kline_{self.timeframe}" for s in self.symbols]
        
        # Split into chunks if too many symbols
        if len(streams) > self.MAX_STREAMS_PER_CONNECTION:
            streams = streams[:self.MAX_STREAMS_PER_CONNECTION]
            self.logger.warning(f"Truncated to {self.MAX_STREAMS_PER_CONNECTION} streams")
            
        return f"{self.BASE_URL}?streams={'/'.join(streams)}"
    
    async def connect(self) -> bool:
        """Establish WebSocket connection with proxy support."""
        try:
            import websockets
            import os
            
            url = self.build_stream_url()
            self.logger.info(f"Connecting to {len(self.symbols)} streams...")
            
            # Use Proxy if configured
            # websockets library doesn't support HTTP proxies natively in 'connect' 
            # without additional wrappers, but removing the bypass allows 
            # system-level/environment-level routing to take over if supported by the OS.
            # For robust proxying, normally a socks wrapper or aiohttp is needed.
            
            connect_kwargs = {
                'ping_interval': 20,
                'ping_timeout': 10,
                'close_timeout': 5
            }
            
            # If a SOCKS proxy is detected, we could use it here if PySocks is available
            # However, for now, we simply STOP the explicit bypass which was causing the issue.
            
            self.ws = await websockets.connect(url, **connect_kwargs)
            
            self.running = True
            self._reconnect_attempts = 0
            self.logger.info(f"Connected ({len(self.symbols)} kline streams @ {self.timeframe})")
            
            # Start ping task to keep connection alive
            if self._ping_task:
                self._ping_task.cancel()
            self._ping_task = asyncio.create_task(self._ping_loop())
            
            return True
            
        except ImportError:
            self.logger.error("'websockets' package not installed. Run: pip install websockets")
            return False
        except Exception as e:
            self.logger.error(f"Connection failed - {e}")
            return False
    
    async def _ping_loop(self):
        """Send periodic pings to keep connection alive."""
        while self.running:
            try:
                await asyncio.sleep(self.PING_INTERVAL)
                if self.ws and self._is_connected():
                    await self.ws.ping()
            except Exception:
                pass  # Connection will be handled by listen loop
    
    def _is_connected(self) -> bool:
        """Check if WebSocket is connected (compatible with websockets v15+)."""
        if not self.ws:
            return False
        # websockets v15+ uses state property (1 = OPEN)
        if hasattr(self.ws, 'state'):
            return self.ws.state == WS_STATE_OPEN
        # Fallback for older versions
        return getattr(self.ws, 'open', False)
    
    async def listen(self):
        """Main listening loop with automatic reconnection."""
        while self.running:
            try:
                if not self._is_connected():
                    if not await self._reconnect():
                        self.logger.error("Max reconnection attempts reached")
                        break
                    continue
                
                msg = await asyncio.wait_for(self.ws.recv(), timeout=30)
                await self._process_message(msg)
                
            except asyncio.TimeoutError:
                # No message in 30s, send ping
                try:
                    if self._is_connected():
                        await self.ws.ping()
                except Exception:
                    pass
                    
            except Exception as e:
                error_str = str(e).lower()
                if "closed" in error_str or "connection" in error_str:
                    self.logger.warning(f"Disconnected - {e}")
                    await self._reconnect()
                else:
                    self.logger.warning_debounced(f"Error - {e}", interval=60)
                    await asyncio.sleep(1)
    
    async def _reconnect(self) -> bool:
        """Attempt to reconnect with exponential backoff."""
        self._reconnect_attempts += 1
        
        if self._reconnect_attempts > self._max_reconnect_attempts:
            return False
            
        wait_time = min(2 ** self._reconnect_attempts, 60)
        self.logger.warning(f"Reconnecting in {wait_time}s (attempt {self._reconnect_attempts})")
        await asyncio.sleep(wait_time)
        
        return await self.connect()
    
    async def _process_message(self, raw_msg: str):
        """Parse and emit kline updates."""
        try:
            data = json.loads(raw_msg)
            
            # Combined stream format: {"stream": "btcusdt@kline_15m", "data": {...}}
            stream = data.get('stream', '')
            kline_data = data.get('data', {}).get('k', {})
            
            if not kline_data:
                return
                
            symbol = kline_data.get('s', '').upper()  # e.g., "BTCUSDT"
            
            candle = {
                'timestamp': kline_data.get('t'),  # Kline start time (ms)
                'open': float(kline_data.get('o', 0)),
                'high': float(kline_data.get('h', 0)),
                'low': float(kline_data.get('l', 0)),
                'close': float(kline_data.get('c', 0)),
                'volume': float(kline_data.get('v', 0)),
                'close_time': kline_data.get('T'),  # Kline close time (ms)
                'is_closed': kline_data.get('x', False),  # True when candle finalized
                'trades': kline_data.get('n', 0)  # Number of trades
            }
            
            self.last_update[symbol] = datetime.now()
            
            # Emit to all callbacks
            for callback in self.callbacks:
                try:
                    await callback(symbol, candle)
                except Exception as e:
                    self.logger.error_debounced(f"Callback error for {symbol} - {e}", interval=300)
                    
        except json.JSONDecodeError:
            pass
        except Exception as e:
            self.logger.warning_debounced(f"Parse error - {e}", interval=300)
    
    async def close(self):
        """Close WebSocket connection."""
        self.running = False
        
        if self._ping_task:
            self._ping_task.cancel()
            
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
                
        self.logger.info("Disconnected")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        return {
            'connected': self._is_connected(),
            'symbols': len(self.symbols),
            'timeframe': self.timeframe,
            'last_updates': {k: v.isoformat() for k, v in self.last_update.items()},
            'reconnect_attempts': self._reconnect_attempts
        }


async def test_ws():
    """Quick test of WebSocket connection."""
    manager = BinanceWSManager(['BTCUSDT', 'ETHUSDT'], '1m')
    
    received = []
    
    async def on_candle(symbol, candle):
        received.append((symbol, candle['close']))
        print(f"📊 {symbol}: ${candle['close']:,.2f} (closed={candle['is_closed']})")
        if len(received) >= 5:
            manager.running = False
    
    manager.add_callback(on_candle)
    
    if await manager.connect():
        await manager.listen()
        
    await manager.close()
    print(f"\n✅ Received {len(received)} updates")


if __name__ == "__main__":
    asyncio.run(test_ws())
