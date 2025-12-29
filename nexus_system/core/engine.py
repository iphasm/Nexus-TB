import asyncio
from ..cortex.factory import StrategyFactory
from ..shield.manager import RiskManager
from ..uplink.stream import MarketStream
from system_directive import DISABLED_ASSETS


from ..utils.logger import get_logger

class NexusCore:
    """
    Main Orchestrator for Nexus System.
    """
    def __init__(self, assets=None, alpaca_keys: dict = None, session_manager=None):
        self.logger = get_logger("NexusCore")
        self.session_manager = session_manager
        self.risk_guardian = RiskManager()
        self.market_stream = MarketStream()  # Use default (binanceusdm for futures)
        self.running = False
        self.alpaca_keys = alpaca_keys or {}
        
        # Determine Assets
        if assets:
            self.assets = list(set(assets)) # Remove duplicates
            self.logger.info(f"Loaded {len(self.assets)} assets from Main Configuration.")
        else:
            # Fallback for isolated testing
            self.assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
            self.logger.warning("Using Default Fallback Assets.")

        self.signal_callback = None
        
        # Concurrency Control (Max 10 parallel analysis tasks)
        self._semaphore = asyncio.Semaphore(10)
        
    def set_callback(self, callback):
        """
        Sets the async callback for signal emission.
        Signature: async def callback(signal: Signal)
        """
        self.signal_callback = callback

    async def initialize(self):
        self.logger.info("⚙️ Initializing Subsystems...")
        
        # Pass Alpaca keys and crypto symbols for WebSocket
        ak = self.alpaca_keys.get('key')
        asec = self.alpaca_keys.get('secret')
        
        # Filter crypto symbols for WebSocket subscription
        crypto_symbols = [a for a in self.assets if 'USDT' in a]
        
        # Register Event Listener BEFORE initializing stream
        self.market_stream.add_callback(self._on_price_update)
        
        await self.market_stream.initialize(
            alpaca_key=ak, 
            alpaca_secret=asec,
            crypto_symbols=crypto_symbols
        )
        
        # Simulating Async Config / DB Load
        await asyncio.sleep(0.5)
        self.last_analysis_time = {}
        self.logger.info("Risk Manager: Online")
        self.logger.info("Strategy Factory: Online")
        self.logger.info("⚡ Event-Driven Engine Ready")

    async def _on_price_update(self, symbol: str, candle: dict):
        """
        Real-time Event Handler.
        Triggered immediately when price updates (via WebSocket).
        """
        current_price = candle.get('close', 0)
        if current_price <= 0:
            return

        # 1. Sniper Profit Safeguard (SPS) - REAL TIME MONITORING (Per Tick)
        if self.session_manager:
            # We don't await this to keep the price stream moving fast
            asyncio.create_task(self._sentry_profit_monitor(symbol, current_price))

        # 2. Strategy Analysis (Only on candle CLOSE)
        if not candle.get('is_closed', False):
            return

        # Rate Limiting: Max 1 analysis per symbol per second (prevent double triggers)
        now = asyncio.get_running_loop().time()
        if now - self.last_analysis_time.get(symbol, 0) < 1.0:
            return
        self.last_analysis_time[symbol] = now
        
        # Check if asset is disabled
        from system_directive import DISABLED_ASSETS
        if symbol in DISABLED_ASSETS:
            return

        # Run Analysis Task (Fire and Forget)
        asyncio.create_task(self._process_symbol_event(symbol))

    async def _sentry_profit_monitor(self, symbol: str, current_price: float):
        """
        Sentry Profit Monitor (SPS Core Logic)
        Monitors active positions in real-time to protect profits.
        """
        try:
            sessions = self.session_manager.get_all_sessions()
            for session in sessions:
                # Check if session has an active position in this symbol
                positions = session.shadow_wallet.positions
                if symbol not in positions:
                    continue
                
                pos = positions[symbol]
                qty = abs(float(pos.get('quantity', 0) or pos.get('amt', 0)))
                if qty <= 0:
                    continue

                # Use ACTUAL TP/Entry from SPS metadata if available
                entry = float(pos.get('sps_entry') or pos.get('entryPrice', 0))
                tp_price = float(pos.get('sps_tp', 0))
                side = str(pos.get('side', 'LONG')).upper()
                
                if entry <= 0 or tp_price <= 0:
                    # Fallback to config only if metadata is MIA
                    tp_pct = session.config.get('take_profit_pct', 0.05)
                    tp_price = entry * (1 + tp_pct) if side == 'LONG' else entry * (1 - tp_pct)
                
                if entry <= 0:
                    continue
                
                # SPS Phase 1: Break-Even (Move SL when 50% way to TP)
                # SPS Phase 2: Shadow Close (Reversal near TP)
                
                progress = 0
                if side == 'LONG':
                    if current_price > entry:
                        progress = (current_price - entry) / (tp_price - entry)
                else: 
                    if current_price < entry:
                        progress = (entry - current_price) / (entry - tp_price)

                # --- 1. MOVE TO BREAK-EVEN (50% Progress) ---
                if 0.5 <= progress < 0.8:
                    # Check if already at BE (we don't want to spam bridge)
                    # This logic needs session state for 'is_be_moved'
                    if not pos.get('sps_lock_be'):
                        self.logger.info(f"🛡️ SPS: Moving {symbol} to Break-Even ({progress:.1%} progress)")
                        pos['sps_lock_be'] = True # Temporary in-memory flag
                        await session.execute_move_to_breakeven(symbol)

                # --- 2. SHADOW CLOSE (80% Progress + Reversal) ---
                if progress >= 0.8:
                    # Track Peak Price
                    peak = pos.get('sps_peak_price', current_price)
                    if side == 'LONG':
                        peak = max(peak, current_price)
                        reversal = (peak - current_price) / peak
                    else:
                        peak = min(peak, current_price)
                        reversal = (current_price - peak) / peak
                    
                    pos['sps_peak_price'] = peak
                    
                    # If reversal > 0.3%, close immediately
                    if reversal > 0.003: # 0.3% drop from peak
                        self.logger.warning(f"🎯 SPS SHADOW CLOSE: {symbol} reversal ({reversal:.2%}) detected at {progress:.1%} TP progress. Securing Profits.")
                        await session.execute_close_position(symbol, reason="SPS Profit Safeguard")

        except Exception as e:
            # We don't log every tick error to avoid spam
            pass

    async def _process_symbol_event(self, asset: str):
        """Execute strategy analysis for a single symbol."""
        async with self._semaphore:
            try:
                # 1. Fetch Market Data (From Cache - instantaneous)
                # Use get_candles which checks cache first
                # Ideally we pass different params for event driven? 
                # For now, standard flow works as it hits cache.
                
                from system_directive import PREMIUM_SIGNALS_ENABLED
                
                if PREMIUM_SIGNALS_ENABLED:
                    mtf_data = await self.market_stream.get_multiframe_candles(asset)
                    market_data = mtf_data['main']
                    if not mtf_data['macro']['dataframe'].empty:
                        market_data['macro_dataframe'] = mtf_data['macro']['dataframe']
                    if 'micro' in mtf_data and not mtf_data['micro']['dataframe'].empty:
                        market_data['micro_dataframe'] = mtf_data['micro']['dataframe']
                else:
                    market_data = await self.market_stream.get_candles(asset)
                
                if market_data.get('dataframe') is None or market_data['dataframe'].empty:
                    return
    
                # --- SENTINEL OVERRIDE CHECK (Black Swan / Shark) ---
                override_action = await self.risk_guardian.get_override_action(asset, market_data)
                
                strategy = None
                
                if override_action in ['BLACK_SWAN', 'SHARK_MODE']:
                    from ..cortex.sentinel import SentinelStrategy
                    strategy = SentinelStrategy()
                    # Inject Mode into Context
                    market_data['sentinel_mode'] = override_action
                    
                    if override_action == 'BLACK_SWAN':
                         self.logger.critical(f"🦢 SENTINEL ACTIVATED: {override_action} on {asset}")
                
                else:
                     # Standard Factory Selection (Normal Market)
                     strategy = StrategyFactory.get_strategy(asset, market_data)
                
                # 3. Analyze
                signal = await strategy.analyze(market_data)
                
                # 4. Actionable Filter
                if signal is None or signal.action == 'HOLD':
                    return
                
                # 5. Emit Signal
                signal.strategy = strategy.name
                self.logger.info(f"⚡ EVENT TRIGGER: {signal.action} on {asset} ({strategy.name}) | Conf: {signal.confidence:.2f}")
                
                if self.signal_callback:
                    await self.signal_callback(signal)
    
            except Exception as e:
                self.logger.error_debounced(f"Event Error ({asset}): {e}", interval=300)

    async def core_loop(self):
        """
        Main Loop is now a Maintenance Loop.
        Trading is driven by _on_price_update events.
        """
        self.logger.info("Entering Maintenance Mode (Event-Driven Active).")
        
        while self.running:
            # Periodic cleanup / health check / logging
            timestamp = asyncio.get_running_loop().time()
            
            # TODO: Add periodic cache cleanup or stats logging here
            
            # But MarketStream handles WS reconnection.

            # --- MACRO HEALTH POLLER (CMC) ---
            # Run every minute check, but internal method respects CMC_POLL_INTERVAL
            try:
                await self.risk_guardian.update_macro_health()
            except Exception as e:
                self.logger.error(f"Macro Poll Failed: {e}")
            
            await asyncio.sleep(60)  # Sleep long, just keep process alive

    async def run(self):
        self.running = True
        await self.initialize()
        await self.core_loop()

    async def stop(self):
        self.running = False
        print("🛑 Engine Stopping...")
        await self.market_stream.close()


