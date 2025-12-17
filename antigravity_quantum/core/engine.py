import asyncio
from ..strategies.factory import StrategyFactory
from ..risk.manager import RiskManager
from ..data.stream import MarketStream
from ..config import DISABLED_ASSETS

class QuantumEngine:
    """
    Main Orchestrator for Antigravity Quantum.
    """
    def __init__(self, assets=None):
        self.risk_guardian = RiskManager()
        self.market_stream = MarketStream('binance')
        self.running = False
        
        # Determine Assets
        if assets:
            self.assets = list(set(assets)) # Remove duplicates
            print(f"🌌 QuantumEngine: Loaded {len(self.assets)} assets from Main Configuration.")
        else:
            # Fallback for isolated testing
            self.assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
            print("⚠️ QuantumEngine: Using Default Fallback Assets.")

        self.signal_callback = None
        
    def set_callback(self, callback):
        """
        Sets the async callback for signal emission.
        Signature: async def callback(signal: Signal)
        """
        self.signal_callback = callback

    async def initialize(self):
        print("🌌 QuantumEngine: Initializing Subsystems...")
        await self.market_stream.initialize()
        
        # Simulating Async Config / DB Load
        await asyncio.sleep(0.5)
        print("✅ Risk Manager: Online")
        print("✅ Strategy Factory: Online")

    async def core_loop(self):
        """Main Decision Loop"""
        print("🚀 Quantum Core Loop Started.")
        cycle_count = 0
        while self.running:
            cycle_count += 1
            # DYNAMIC FILTER: Remove disabled assets each cycle
            active_assets = [a for a in self.assets if a not in DISABLED_ASSETS]
            
            if not active_assets:
                print(f"⚠️ Cycle {cycle_count}: No active assets (all disabled)")
                await asyncio.sleep(60)
                continue
            
            signals_generated = 0
            for asset in active_assets:
                try:
                    # 1. Fetch Market Data
                    market_data = await self.market_stream.get_candles(asset)
                    
                    if market_data.get('dataframe') is None or market_data['dataframe'].empty:
                        continue
                    
                    # 2. Get Strategy via Factory (Dynamic Classification)
                    strategy = StrategyFactory.get_strategy(asset, market_data)
                    
                    # 3. Analyze Market & Generate Signal
                    signal = strategy.analyze(market_data)
                    
                    # 4. Filter: Only actionable signals
                    if signal is None or signal.action == 'HOLD':
                        continue
                    
                    # 5. Risk Check (Optional - basic exposure check)
                    # approved = await self.risk_guardian.check_trade_approval(signal, 0.0)
                    
                    # 6. Emit Signal
                    signal.strategy = strategy.name
                    signals_generated += 1
                    print(f"💡 QUANTUM SIGNAL: {signal.action} on {asset} ({strategy.name}) | Conf: {signal.confidence:.2f}")
                    
                    if self.signal_callback:
                        await self.signal_callback(signal)
                        
                except Exception as e:
                    print(f"⚠️ Error processing {asset}: {e}")
                    continue
            
            # Diagnostic: Log cycle summary every 5 cycles
            if cycle_count % 5 == 0:
                print(f"📊 Cycle {cycle_count}: Scanned {len(active_assets)} assets, {signals_generated} signals generated")
                
            await asyncio.sleep(60)  # 1 Minute Cycle


    async def run(self):
        self.running = True
        await self.initialize()
        await self.core_loop()

    async def stop(self):
        self.running = False
        print("🛑 Engine Stopping...")
        await self.market_stream.close()
