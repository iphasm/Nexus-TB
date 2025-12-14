from .base import IStrategy
from .trend import TrendFollowingStrategy
from .grid import GridTradingStrategy
from .mean_reversion import MeanReversionStrategy
from .scalping import ScalpingStrategy

# Import all module asset lists
from ..config import ENABLED_STRATEGIES, GRID_ASSETS, SCALPING_ASSETS, MEAN_REV_ASSETS

class StrategyFactory:
    """
    Dynamic Factory to assign strategies based on asset profile and Global Config.
    Respects per-module asset lists configured via /assets menu.
    """
    
    @staticmethod
    def get_strategy(symbol: str, volatility_index: float) -> IStrategy:
        """
        Assigns the optimal strategy based on flags and whitelist.
        Priority: Grid > Scalping > Trend > Mean Reversion
        """
        # 1. GRID STRATEGY (Sideways/Accumulation)
        if ENABLED_STRATEGIES.get('GRID', False):
            if symbol in GRID_ASSETS:
                return GridTradingStrategy()
        
        # 2. SCALPING STRATEGY (High Volatility)
        if ENABLED_STRATEGIES.get('SCALPING', False):
            if symbol in SCALPING_ASSETS:
                return ScalpingStrategy()
        
        # 3. TREND FOLLOWING (Only BTC/Major dominance)
        if symbol == 'BTC' or symbol == 'BTCUSDT':
            return TrendFollowingStrategy()
        
        # 4. MEAN REVERSION (Default if enabled)
        if ENABLED_STRATEGIES.get('MEAN_REVERSION', True):
            # If MEAN_REV_ASSETS is empty, apply to all non-matched assets
            # If it has content, only apply to those specific assets
            if len(MEAN_REV_ASSETS) == 0 or symbol in MEAN_REV_ASSETS:
                return MeanReversionStrategy()
            
        # 5. FALLBACK: Mean Reversion (always available)
        return MeanReversionStrategy()