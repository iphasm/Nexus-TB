import asyncio
from ..cortex.factory import StrategyFactory
from ..shield.manager import RiskManager
from ..uplink.stream import MarketStream
from ..core.exit_manager import ExitManager
from system_directive import DISABLED_ASSETS


from ..utils.logger import get_logger

class NexusCore:
    """
    Main Orchestrator for Nexus System.
    """
    def __init__(self, assets=None, alpaca_keys: dict = None, bybit_keys: dict = None, session_manager=None):
        self.logger = get_logger("NexusCore")
        self.session_manager = session_manager
        self.risk_guardian = RiskManager()
        self.market_stream = MarketStream()  # Use default (binanceusdm for futures)
        self.exit_manager = ExitManager({})  # Initialize ExitManager with empty config (will be updated)
        self.running = False
        self.alpaca_keys = alpaca_keys or {}
        self.bybit_keys = bybit_keys or {}

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
        
        # Bybit Adapter Registration (candles are public; keys are optional)
        bk = self.bybit_keys.get('key')
        bs = self.bybit_keys.get('secret')
        from ..uplink.adapters.bybit_adapter import BybitAdapter

        # If keys exist, use them; otherwise still register a public Bybit client for candles.
        bybit_adapter = BybitAdapter(api_key=bk, api_secret=bs) if (bk and bs) else BybitAdapter()
        if await bybit_adapter.initialize():
            self.market_stream.register_adapter('bybit', bybit_adapter)
            self.logger.info("🔌 Bybit Adapter registered for Data Engine (public candles)")
        else:
            self.logger.warning("⚠️ Bybit Adapter init failed for Data Engine")
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

        # Strategy Analysis (Only on candle CLOSE)
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

        # Check Exit Conditions for Active Positions (ExitManager)
        asyncio.create_task(self._check_exit_conditions(symbol, current_price))

        # Run Analysis Task (Fire and Forget)
        asyncio.create_task(self._process_symbol_event(symbol))

    async def _check_exit_conditions(self, symbol: str, current_price: float):
        """
        Check exit conditions for all active positions on this symbol across all sessions.
        Execute partial exits, trailing stops, and time stops when triggered.
        """
        if not self.session_manager:
            return

        try:
            # Get all active sessions
            for chat_id, session in self.session_manager.sessions.items():
                if not hasattr(session, 'exit_manager') or not session.exit_manager:
                    continue

                # Check if this session has an active exit plan for this symbol
                if symbol in session.exit_manager.active_exit_plans:
                    exit_plan = session.exit_manager.active_exit_plans[symbol]

                    # Check exit conditions
                    triggered_exits = session.exit_manager.check_exit_conditions(symbol, current_price)

                    # Execute triggered exits
                    for rule, quantity_to_close in triggered_exits:
                        try:
                            # Execute the partial exit via trading session
                            success, msg = await session._execute_partial_exit(symbol, rule, quantity_to_close, exit_plan)

                            if success:
                                self.logger.info(f"🎯 Exit Executed: {symbol} - {rule.description} ({quantity_to_close:.4f} qty)")
                                # Send notification to user
                                if session.manager and hasattr(session.manager, 'bot'):
                                    try:
                                        await session.manager.bot.send_message(
                                            session.chat_id,
                                            f"🎯 **EXIT TRIGGERED**\n{symbol}: {rule.description}\nClosed: {quantity_to_close:.4f} units\n💰 {msg}",
                                            parse_mode="Markdown"
                                        )
                                    except Exception as notify_error:
                                        self.logger.debug(f"Exit notification failed: {notify_error}")
                            else:
                                self.logger.warning(f"Exit Failed: {symbol} - {rule.description} - {msg}")

                        except Exception as exit_error:
                            self.logger.error(f"Exit execution error for {symbol}: {exit_error}")

        except Exception as e:
            self.logger.error(f"Exit condition check error for {symbol}: {e}")

    async def _process_symbol_event(self, asset: str):

        """Execute strategy analysis for a single symbol with MTF filtering."""
        async with self._semaphore:
            try:
                # 1. Fetch Multi-Timeframe Data for confluence analysis
                # Use get_multiframe_candles which fetches 1m, 15m, 4h
                mtf_data = await self.market_stream.get_multiframe_candles(asset)
                
                # Use main timeframe for strategy analysis
                market_data = mtf_data.get('main', {})
                
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
                
                # 5. MTF Confluence Filter (NEW)
                # Skip MTF for Sentinel overrides (emergency actions)
                if override_action not in ['BLACK_SWAN', 'SHARK_MODE']:
                    from ..cortex.mtf_filter import get_mtf_filter
                    from system_directive import MTF_MIN_CONFLUENCE_SCORE
                    
                    mtf_filter = get_mtf_filter(MTF_MIN_CONFLUENCE_SCORE)
                    should_trade, analysis = mtf_filter.should_trade(asset, mtf_data, signal.action)
                    
                    if not should_trade:
                        self.logger.info(f"🔍 MTF FILTER: {asset} signal rejected - {analysis.reason}")
                        return
                    
                    # Add confluence data to signal metadata
                    if not hasattr(signal, 'metadata') or signal.metadata is None:
                        signal.metadata = {}
                    signal.metadata['mtf_score'] = analysis.confluence_score
                    signal.metadata['mtf_trend'] = analysis.macro_trend.value
                    
                    self.logger.info(f"✅ MTF PASSED: {asset} confluence={analysis.confluence_score:.1f}/10")
                
                # 6. Emit Signal
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

            # --- WEBSOCKET RECONNECTION ATTEMPT ---
            # Try to reconnect WebSocket if it failed during initialization
            if not self.market_stream.ws_manager and self.market_stream._ws_retry_count < self.market_stream._ws_max_retries:
                try:
                    await self.market_stream._try_reconnect_websocket(self.assets)
                except Exception as e:
                    self.logger.debug(f"WebSocket reconnection attempt failed: {e}")

            await asyncio.sleep(60)  # Sleep long, just keep process alive

    async def run(self):
        self.running = True
        await self.initialize()
        await self.core_loop()

    async def stop(self):
        self.running = False
        print("🛑 Engine Stopping...")
        await self.market_stream.close()


