import asyncio
from ..strategies.factory import StrategyFactory
from ..risk.manager import RiskManager
from ..data.stream import MarketStream

class QuantumEngine:
    """
    Main Orchestrator for Antigravity Quantum.
    """
    def __init__(self):
        self.risk_guardian = RiskManager()
        self.market_stream = MarketStream('binance')
        self.running = False
        # Only testing a few assets for prototype to avoid rate limits
        self.assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'LTCUSDT', 'LINKUSDT', 'DOGEUSDT', 'AVAXUSDT', 'ZECUSDT', 'SUIUSDT'] 
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
        while self.running:
            for asset in self.assets:
                # print(f"🔍 Scanning {asset}...") # Reduced Noise
                
                # 1. Fetch Data (Real)
                market_data = await self.market_stream.get_candles(asset)
                if market_data['dataframe'].empty:
                    continue

                # 2. Get Dynamic Strategy
                # In real version, we calculate volatility from market_data to pick strategy
                # For now using VOL=0.5 default, or based on asset
                volatility_index = 0.5 
                strategy = StrategyFactory.get_strategy(asset.replace('USDT',''), volatility_index)
                
                # 3. Analyze (Async)
                signal = await strategy.analyze(market_data)
                
                if signal:
                    print(f"💡 QUANTUM SIGNAL: {signal.action} on {asset} ({strategy.name}) | Conf: {signal.confidence:.2f}")
                    
                    if self.signal_callback:
                        await self.signal_callback(signal)
                
            await asyncio.sleep(60) # 1 Minute Cycle (Matches 15m candle update speed approx)

    async def run(self):
        self.running = True
        await self.initialize()
        await self.core_loop()

    async def stop(self):
        self.running = False
        print("🛑 Engine Stopping...")
        await self.market_stream.close()
