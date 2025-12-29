"""
Nexus Trading Bot - Async Shark Mode Sentinel
Migrated from threading.Thread to asyncio.Task for full async support.
Uses aiohttp for HTTP requests and asyncio for concurrent operations.
"""
import asyncio
import aiohttp
import logging
from collections import deque
from typing import Callable, Optional, Dict, Any
import random

# Configure Logger
logger = logging.getLogger("SharkMode")

# Import config constants
try:
    from system_directive import (
        SHARK_TARGETS,
        SHARK_CRASH_THRESHOLD_PCT,
        SHARK_WINDOW_SECONDS,
        SHARK_HEARTBEAT_SECONDS,
        SHARK_COOLDOWN_SECONDS,
        BINANCE_PUBLIC_API,
        HTTP_TIMEOUT_SHORT,
        ENABLED_STRATEGIES
    )
except ImportError:
    # Fallback if system_directive not available
    SHARK_TARGETS = ['1000PEPEUSDT', 'SOLUSDT', 'WIFUSDT', 'RENDERUSDT', 'SUIUSDT']
    SHARK_CRASH_THRESHOLD_PCT = 3.0
    SHARK_WINDOW_SECONDS = 60
    SHARK_HEARTBEAT_SECONDS = 1
    SHARK_COOLDOWN_SECONDS = 300
    BINANCE_PUBLIC_API = "https://api.binance.com/api/v3"
    HTTP_TIMEOUT_SHORT = 5
    ENABLED_STRATEGIES = {}


class SharkSentinel:
    """
    Async Shark Mode Sentinel - Monitors BTC price for crash detection.
    Replaces threading.Thread with asyncio.Task for full async integration.
    """
    
    def __init__(
        self, 
        session_manager, 
        notify_callback: Callable[[str], None],
        enabled_check_callback: Optional[Callable[[], bool]] = None,
        crash_threshold_pct: float = None,
        window_seconds: int = None
    ):
        """
        Initialize async Shark Sentinel.
        
        :param session_manager: Instance of SessionManager to access all active sessions.
        :param notify_callback: Async function(msg) to send Telegram alerts.
        :param enabled_check_callback: Function() -> bool. If False, sentinel is dormant.
        :param crash_threshold_pct: Percentage drop (positive float) to trigger Shark Mode.
        :param window_seconds: Rolling window size in seconds.
        """
        self.session_manager = session_manager
        self.notify_callback = notify_callback
        self.enabled_check_callback = enabled_check_callback
        self.threshold = crash_threshold_pct or SHARK_CRASH_THRESHOLD_PCT
        self.window_seconds = window_seconds or SHARK_WINDOW_SECONDS
        
        # Deque: Stores (timestamp, price)
        self.price_window = deque(maxlen=self.window_seconds + 10)
        self.running = False
        self.triggered = False  # Cooldown flag
        self._task: Optional[asyncio.Task] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
        
        # Panic Targets (Loaded from config)
        try:
            from system_directive import SHARK_TARGETS
            self.sniper_targets = SHARK_TARGETS
        except ImportError:
            self.sniper_targets = SHARK_TARGETS  # Use fallback from above

    async def _exponential_backoff(self, coro_func, *args, max_retries: int = 3, **kwargs):
        """
        Executes async function with exponential backoff on failure.
        Handling 502/504/System Busy errors.
        """
        delay = 1.0
        for i in range(max_retries):
            try:
                return await coro_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Try {i+1}/{max_retries} failed: {e}")
                if i == max_retries - 1:
                    raise e
                await asyncio.sleep(delay + random.uniform(0, 0.5))  # Jitter
                delay *= 2

    async def fetch_btc_price_raw(self) -> Optional[float]:
        """
        Ultra-lightweight async price fetch using aiohttp.
        Uses WebSocket-ready approach (can be upgraded to use MarketStream later).
        """
        if not self._http_session:
            self._http_session = aiohttp.ClientSession()
        
        url = f"{BINANCE_PUBLIC_API}/ticker/price?symbol=BTCUSDT"
        
        for attempt in range(2):  # 2 attempts total
            try:
                async with self._http_session.get(
                    url, 
                    timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SHORT)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return float(data['price'])
                    else:
                        logger.warning(f"Price fetch failed: HTTP {resp.status}")
            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(0.5)  # Brief pause before retry
                    continue
                logger.warning(f"Price fetch failed after retry: {e}")
                return None
        
        return None

    async def execute_defense_sequence(self):
        """
        Async parallel execution:
        1. Panic Close ALL Longs (All Sessions)
        2. Sniper Short Targets (All Sessions)
        """
        logger.warning("⚔️ EXECUTING DEFENSE SEQUENCE ⚔️")
        
        sessions = self.session_manager.get_all_sessions()
        if not sessions:
            return

        tasks = []

        # 1. PANIC CLOSE LONGS (BLACK SWAN - The Shield)
        # Import here to avoid circular dependency
        try:
            from system_directive import ENABLED_STRATEGIES
            enabled_strategies = ENABLED_STRATEGIES
        except ImportError:
            enabled_strategies = ENABLED_STRATEGIES  # Use fallback
        
        if enabled_strategies.get('BLACK_SWAN', True):
            for session_id, session in sessions.items():
                tasks.append(self._panic_close_session(session))

        # 2. SNIPER SHORTS (SHARK MODE - The Sword)
        if enabled_strategies.get('SHARK', False):
            for session_id, session in sessions.items():
                for target in self.sniper_targets:
                    tasks.append(self._sniper_short_session(session, target))

        # Wait for all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Defense task failed: {result}")

    async def _panic_close_session(self, session):
        """Async task: Close all longs for a specific session."""
        try:
            # Get active positions (async method)
            positions = await session.get_active_positions()
            
            for p in positions:
                # Check if position is LONG (positive quantity)
                qty = float(p.get('quantity', 0) or p.get('positionAmt', 0) or p.get('amt', 0))
                if qty > 0:  # Long position
                    symbol = p.get('symbol', '')
                    logger.info(f"Closing LONG {symbol} for {session.chat_id}")
                    # Execute close (async method)
                    await session.execute_close_position(symbol)
            
        except Exception as e:
            logger.error(f"Panic Close Error (Session {session.chat_id}): {e}")

    async def _sniper_short_session(self, session, symbol: str):
        """Async task: Open Short for a target."""
        try:
            # Check if already short to avoid double entry
            # execute_short_position has internal check
            await session.execute_short_position(symbol, atr=0)  # ATR=0 implies market/default params
        except Exception as e:
            logger.error(f"Sniper Short Error ({symbol}): {e}")

    async def _monitor_loop(self):
        """Main async monitoring loop."""
        logger.info("🦈 SHARK MODE SENTINEL ACTIVE (Async Task)")
        
        while self.running:
            try:
                # 0. Check Toggle
                if self.enabled_check_callback and not self.enabled_check_callback():
                    await asyncio.sleep(5)
                    continue

                now = asyncio.get_event_loop().time()
                price = await self.fetch_btc_price_raw()
                
                if price:
                    self.price_window.append((now, price))
                    
                    # Sliding Window Logic
                    # 1. Pop old entries
                    while self.price_window and self.price_window[0][0] < now - self.window_seconds:
                        self.price_window.popleft()
                    
                    if len(self.price_window) > 1:
                        start_price = self.price_window[0][1]
                        # Calculate drop percentage
                        drop_pct = ((price - start_price) / start_price) * 100
                        
                        # LOGIC CHECK
                        if drop_pct <= -self.threshold and not self.triggered:
                            self.triggered = True
                            
                            msg = (
                                f"⚠️⚠️ **BLACK SWAN DETECTED** ⚠️⚠️\n"
                                f"BTC Crash: {drop_pct:.2f}% en {self.window_seconds}s."
                            )
                            logger.critical(msg)
                            
                            # Notify (async callback)
                            if asyncio.iscoroutinefunction(self.notify_callback):
                                await self.notify_callback(msg)
                            else:
                                # Fallback for sync callback (shouldn't happen but safe)
                                self.notify_callback(msg)
                            
                            # Execute defense sequence
                            await self.execute_defense_sequence()
                            
                            # Cooldown to avoid spam loop
                            await asyncio.sleep(SHARK_COOLDOWN_SECONDS)
                            self.triggered = False
                            self.price_window.clear()  # Reset window
                
                # Heartbeat
                await asyncio.sleep(SHARK_HEARTBEAT_SECONDS)
                
            except Exception as e:
                logger.error(f"Sentinel Loop Error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Prevent CPU spin on hard crash

    async def start(self):
        """Start the async monitoring task."""
        if self.running:
            logger.warning("Shark Sentinel already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("🦈 Shark Sentinel task started")

    async def stop(self):
        """Stop the async monitoring task."""
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._http_session:
            await self._http_session.close()
            self._http_session = None
        
        logger.info("🦈 Shark Sentinel stopped")

    def __del__(self):
        """Cleanup on deletion."""
        if self._http_session and not self._http_session.closed:
            # Note: Can't await in __del__, but session will be closed by event loop cleanup
            pass
