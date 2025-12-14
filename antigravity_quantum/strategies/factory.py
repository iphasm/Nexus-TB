from .base import IStrategy
from .trend import TrendFollowingStrategy
from .grid import GridTradingStrategy
from .mean_reversion import MeanReversionStrategy
from .scalping import ScalpingStrategy

# Import the config MODULE (not individual vars) for runtime access
import antigravity_quantum.config as qconfig

class StrategyFactory:
    """
    Dynamic Factory to assign strategies based on asset profile and Global Config.
    Reads config at RUNTIME to respect changes made via /assets menu.
    """
    
    @staticmethod
    def get_strategy(symbol: str, volatility_index: float) -> IStrategy:
        """
        Assigns the optimal strategy based on flags and whitelist.
        Priority: Grid > Scalping > Trend > Mean Reversion (Fallback for ALL)
        
        NOTE: All config reads happen HERE (runtime) not at import time.
        """
        strategy = None
        
        # 1. GRID STRATEGY (Sideways/Accumulation)
        if qconfig.ENABLED_STRATEGIES.get('GRID', False):
            if symbol in qconfig.GRID_ASSETS:
                strategy = GridTradingStrategy()
                print(f"🎯 {symbol} → GRID Strategy")
                return strategy
        
        # 2. SCALPING STRATEGY (High Volatility)
        if qconfig.ENABLED_STRATEGIES.get('SCALPING', False):
            if symbol in qconfig.SCALPING_ASSETS:
                strategy = ScalpingStrategy()
                print(f"🎯 {symbol} → SCALPING Strategy")
                return strategy
        
        # 3. TREND FOLLOWING (Only BTC/Major dominance)
        if symbol == 'BTC' or symbol == 'BTCUSDT':
            if qconfig.ENABLED_STRATEGIES.get('TREND', True):
                strategy = TrendFollowingStrategy()
                print(f"🎯 {symbol} → TREND Strategy")
                return strategy
        
        # 4. MEAN REVERSION (Enabled by default, applies to ALL non-matched assets)
        if qconfig.ENABLED_STRATEGIES.get('MEAN_REVERSION', True):
            strategy = MeanReversionStrategy()
            # Only log on first occurrence to reduce noise
            return strategy
            
        # 5. ABSOLUTE FALLBACK (if mean reversion disabled): Still use it as safety
        return MeanReversionStrategy()
