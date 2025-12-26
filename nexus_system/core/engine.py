import asyncio
from ..cortex.factory import StrategyFactory
from ..shield.manager import RiskManager
from ..uplink.stream import MarketStream
from ..directive import DISABLED_ASSETS


from ..utils.logger import get_logger

class NexusCore:
    """
    Main Orchestrator for Nexus System.
    """
    def __init__(self, assets=None, alpaca_keys: dict = None):
        self.logger = get_logger("NexusCore")
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
        Triggered immediately when a candle closes (or updates).
        """
        # Only analyze on candle CLOSE (signals are based on confirmed candles)
        if not candle.get('is_closed', False):
            return

        # Rate Limiting: Max 1 analysis per symbol per second (prevent double triggers)
        now = asyncio.get_running_loop().time()
        if now - self.last_analysis_time.get(symbol, 0) < 1.0:
            return
        self.last_analysis_time[symbol] = now
        
        # Check if asset is disabled
        from ..directive import DISABLED_ASSETS
        if symbol in DISABLED_ASSETS:
            return

        # Run Analysis Task (Fire and Forget)
        asyncio.create_task(self._process_symbol_event(symbol))

    async def _process_symbol_event(self, asset: str):
        """Execute strategy analysis for a single symbol."""
        try:
            # 1. Fetch Market Data (From Cache - instantaneous)
            # Use get_candles which checks cache first
            # Ideally we pass different params for event driven? 
            # For now, standard flow works as it hits cache.
            
            from ..directive import PREMIUM_SIGNALS_ENABLED
            
            if PREMIUM_SIGNALS_ENABLED:
                mtf_data = await self.market_stream.get_multiframe_candles(asset)
                market_data = mtf_data['main']
                if not mtf_data['macro']['dataframe'].empty:
                    market_data['macro_dataframe'] = mtf_data['macro']['dataframe']
            else:
                market_data = await self.market_stream.get_candles(asset)
            
            if market_data.get('dataframe') is None or market_data['dataframe'].empty:
                return

            # 2. Get Strategy via Factory
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
            
            # If no WebSockets are active (fallback mode), we might want to poll manually?
            # For now, we assume WS is primary. If WS fails, we might need a fallback poller.
            # But MarketStream handles WS reconnection.
            
            await asyncio.sleep(60)  # Sleep long, just keep process alive

    async def run(self):
        self.running = True
        await self.initialize()
        await self.core_loop()

    async def stop(self):
        self.running = False
        print("🛑 Engine Stopping...")
        await self.market_stream.close()


