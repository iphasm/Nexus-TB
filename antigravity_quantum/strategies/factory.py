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
        # 1. GRID STRATEGY (Sideways/Accumulation)
        if qconfig.ENABLED_STRATEGIES.get('GRID', False):
            if symbol in qconfig.GRID_ASSETS:
                return GridTradingStrategy()
        
        # 2. SCALPING STRATEGY (High Volatility)
        if qconfig.ENABLED_STRATEGIES.get('SCALPING', False):
            if symbol in qconfig.SCALPING_ASSETS:
                return ScalpingStrategy()
        
        # 3. TREND FOLLOWING (Only BTC/Major dominance)
        if symbol == 'BTC' or symbol == 'BTCUSDT':
            return TrendFollowingStrategy()
        
        # 4. MEAN REVERSION (Enabled by default, applies to ALL non-matched assets)
        # CHANGED: Now applies to ALL assets NOT in Grid or Scalping lists
        # This ensures EVERY asset gets a strategy
        if qconfig.ENABLED_STRATEGIES.get('MEAN_REVERSION', True):
            return MeanReversionStrategy()
            
        # 5. ABSOLUTE FALLBACK (if mean reversion disabled): Still use it as safety
        return MeanReversionStrategy()
