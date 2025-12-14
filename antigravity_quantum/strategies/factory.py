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
        Priority: Grid > Scalping > Trend > Mean Reversion
        
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
        
        # 4. MEAN REVERSION (Default if enabled)
        if qconfig.ENABLED_STRATEGIES.get('MEAN_REVERSION', True):
            # If MEAN_REV_ASSETS is empty, apply to all non-matched assets
            # If it has content, only apply to those specific assets
            if len(qconfig.MEAN_REV_ASSETS) == 0 or symbol in qconfig.MEAN_REV_ASSETS:
                return MeanReversionStrategy()
            
        # 5. FALLBACK: Mean Reversion (always available)
        return MeanReversionStrategy()