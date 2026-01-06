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
        SHARK_INDEPENDENT_MODE,
        SHARK_MOMENTUM_THRESHOLD,
        SHARK_MIN_VOLUME_MULTIPLIER,
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
    SHARK_INDEPENDENT_MODE = True
    SHARK_MOMENTUM_THRESHOLD = 2.0
    SHARK_MIN_VOLUME_MULTIPLIER = 1.2
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
            # Create session with proper headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            self._http_session = aiohttp.ClientSession(headers=headers)

        url = f"{BINANCE_PUBLIC_API}/ticker/price?symbol=BTCUSDT"

        for attempt in range(3):  # Increased to 3 attempts
            try:
                async with self._http_session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SHORT)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return float(data['price'])
                    elif resp.status == 418:  # I'm a teapot - Binance blocking
                        delay = (attempt + 1) * 5  # Progressive delay: 5s, 10s, 15s
                        logger.warning(f"Price fetch blocked (HTTP 418). Backing off {delay}s before retry {attempt + 1}/3")
                        if attempt < 2:  # Don't sleep on last attempt
                            await asyncio.sleep(delay)
                        continue
                    elif resp.status == 429:  # Rate limit
                        delay = (attempt + 1) * 10  # Longer delay for rate limits
                        logger.warning(f"Rate limited (HTTP 429). Backing off {delay}s before retry {attempt + 1}/3")
                        if attempt < 2:
                            await asyncio.sleep(delay)
                        continue
                    else:
                        logger.warning(f"Price fetch failed: HTTP {resp.status}")
            except Exception as e:
                if attempt < 2:  # Don't retry on last attempt
                    delay = (attempt + 1) * 2  # Progressive delay: 2s, 4s
                    logger.warning(f"Price fetch error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                logger.warning(f"Price fetch failed after retries: {e}")
                return None

        return None

    async def execute_defense_sequence(self, mode: str = "BLACK_SWAN"):
        """
        Async parallel execution based on activation mode:
        - BLACK_SWAN: Panic Close Longs + Sniper Shorts
        - SHARK_INDEPENDENT: Only Sniper Shorts (no panic close)
        """
        logger.warning(f"⚔️ EXECUTING DEFENSE SEQUENCE ({mode}) ⚔️")

        sessions = self.session_manager.get_all_sessions()
        if not sessions:
            return

        tasks = []

        # Get strategy configuration
        try:
            from system_directive import ENABLED_STRATEGIES
            enabled_strategies = ENABLED_STRATEGIES
        except ImportError:
            enabled_strategies = ENABLED_STRATEGIES  # Use fallback

        # 1. PANIC CLOSE LONGS (Only for BLACK_SWAN mode)
        if mode == "BLACK_SWAN" and enabled_strategies.get('BLACK_SWAN', True):
            logger.warning("🛡️ ACTIVATING BLACK SWAN SHIELD - Closing all longs")
            for session_id, session in sessions.items():
                tasks.append(self._panic_close_session(session))

        # 2. SNIPER SHORTS (For both BLACK_SWAN and SHARK_INDEPENDENT)
        if enabled_strategies.get('SHARK', False):
            logger.warning("🦈 ACTIVATING SHARK MODE - Opening sniper shorts")
            for session_id, session in sessions.items():
                for target in self.sniper_targets:
                    tasks.append(self._sniper_short_session(session, target))

        # Wait for all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for result in results if not isinstance(result, Exception))
            error_count = sum(1 for result in results if isinstance(result, Exception))

            logger.info(f"Defense sequence completed: {success_count} successful, {error_count} errors")
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
        """Async task: Open Short for a target with duplicate prevention."""
        try:
            # VALIDATION 1: Check for existing short positions to avoid duplicates
            positions = await session.get_active_positions()
            existing_short = any(
                p.get('symbol') == symbol and
                float(p.get('quantity', 0) or p.get('positionAmt', 0) or p.get('amt', 0)) < 0
                for p in positions
            )

            if existing_short:
                logger.info(f"Skipping {symbol} - Short position already exists")
                return

            # VALIDATION 2: Check available balance (rough estimate)
            try:
                balance = await session.get_balance()
                if balance < 50:  # Minimum $50 for shorts
                    logger.warning(f"Skipping {symbol} - Insufficient balance (${balance:.2f})")
                    return
            except Exception:
                # Continue if balance check fails
                pass

            # Execute short position with ATR=0 (market/default params)
            await session.execute_short_position(symbol, atr=0)
            logger.info(f"🦈 SHARK SHORT executed: {symbol} for session {session.chat_id}")

        except Exception as e:
            logger.error(f"Sniper Short Error ({symbol}): {e}")

    async def _calculate_dynamic_threshold(self, current_price: float) -> float:
        """
        Calculate dynamic crash threshold based on current market volatility.
        Higher volatility = higher threshold to avoid false positives.
        """
        try:
            # Get recent volatility from Binance API
            volatility_pct = await self._get_btc_volatility()

            # Base threshold adjustment based on volatility
            # High volatility (+3% ATR) = +1% to threshold (less sensitive)
            # Low volatility (-1% ATR) = -0.5% to threshold (more sensitive)
            volatility_adjustment = (volatility_pct - 2.0) * 0.5  # ±0.5% per 1% volatility deviation

            dynamic_threshold = self.threshold + volatility_adjustment

            # Ensure reasonable bounds
            dynamic_threshold = max(1.5, min(dynamic_threshold, 6.0))  # Between 1.5% and 6.0%

            return dynamic_threshold

        except Exception as e:
            logger.warning(f"Error calculating dynamic threshold: {e}")
            return self.threshold  # Fallback to static threshold

    async def _get_btc_volatility(self) -> float:
        """Get current BTC volatility (ATR approximation)."""
        try:
            # Fetch 24h stats from Binance
            url = f"{BINANCE_PUBLIC_API}/ticker/24hr?symbol=BTCUSDT"
            async with self._http_session.get(url, timeout=HTTP_TIMEOUT_SHORT) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price_change_pct = abs(float(data['priceChangePercent']))
                    return price_change_pct  # Use 24h change as volatility proxy
                elif resp.status == 418:  # I'm a teapot - Binance blocking
                    logger.warning("Volatility fetch blocked (HTTP 418)")
                    return 2.0  # Default fallback
                elif resp.status == 429:  # Rate limit
                    logger.warning("Volatility fetch rate limited (HTTP 429)")
                    return 2.0  # Default fallback
                else:
                    logger.warning(f"Volatility fetch failed: HTTP {resp.status}")
                    return 2.0  # Default fallback

        except Exception as e:
            logger.warning(f"Error fetching volatility: {e}")
            return 2.0  # Default volatility fallback

    async def _monitor_loop(self):
        """Main async monitoring loop with dynamic thresholds."""
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

                        # Get dynamic threshold based on current volatility
                        current_threshold = await self._calculate_dynamic_threshold(price)

                        # LOGIC CHECK - Multiple activation modes with dynamic thresholds
                        activated_mode = None

                        # 1. BLACK SWAN: Major crash detection (dynamic threshold)
                        if drop_pct <= -current_threshold and not self.triggered:
                            activated_mode = "BLACK_SWAN"
                            msg = (
                                f"⚠️⚠️ **BLACK SWAN DETECTED** ⚠️⚠️\n"
                                f"BTC Crash: {drop_pct:.2f}% (Threshold: {current_threshold:.1f}%)\n"
                                f"en {self.window_seconds}s.\n"
                                f"🚨 ACTIVANDO PROTOCOLO DE DEFENSA COMPLETO"
                            )

                        # 2. SHARK INDEPENDENT: Moderate momentum detection (if enabled)
                        elif (SHARK_INDEPENDENT_MODE and
                              drop_pct <= -SHARK_MOMENTUM_THRESHOLD and
                              drop_pct > -current_threshold and  # Not extreme enough for Black Swan
                              not self.triggered):
                            activated_mode = "SHARK_INDEPENDENT"
                            msg = (
                                f"🦈 **SHARK MOMENTUM DETECTED** 🦈\n"
                                f"BTC Drop: {drop_pct:.2f}% en {self.window_seconds}s.\n"
                                f"🎯 ACTIVANDO MODO SHARK INDEPENDIENTE"
                            )

                        # Execute if any mode activated
                        if activated_mode:
                            self.triggered = True
                            logger.critical(f"{activated_mode}: {msg}")

                            # Notify (async callback)
                            if asyncio.iscoroutinefunction(self.notify_callback):
                                await self.notify_callback(msg)
                            else:
                                # Fallback for sync callback
                                self.notify_callback(msg)

                            # Execute defense sequence with specific mode
                            await self.execute_defense_sequence(activated_mode)

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
