from .base import IStrategy
from .trend import TrendFollowingStrategy
from .grid import GridTradingStrategy
from .mean_reversion import MeanReversionStrategy
from .scalping import ScalpingStrategy

# --- CORRECCIÓN AQUÍ ---
# Antes: from ..config import ENABLED_STRATEGIES, GRID_WHITELIST, SCALPING_WHITELIST
# Ahora (Nombres correctos según tu config.py):
from ..config import ENABLED_STRATEGIES, GRID_ASSETS, SCALPING_ASSETS 

class StrategyFactory:
    """
    Dynamic Factory to assign strategies based on asset profile and Global Config.
    """
    
    @staticmethod
    def get_strategy(symbol: str, volatility_index: float) -> IStrategy:
        """
        Assigns the optimal strategy based on flags and whitelist.
        """
        # 1. GRID STRATEGY (Sideways/Accumulation)
        if ENABLED_STRATEGIES.get('GRID', False):
            # CORRECCIÓN: Usar GRID_ASSETS
            if symbol in GRID_ASSETS:
                return GridTradingStrategy()
        
        # 2. SCALPING STRATEGY (High Volatility)
        if ENABLED_STRATEGIES.get('SCALPING', False):
            # CORRECCIÓN: Usar SCALPING_ASSETS
            if symbol in SCALPING_ASSETS and volatility_index > 0.6:
                return ScalpingStrategy()
        
        # 3. TREND FOLLOWING (Only BTC/Major dominance)
        if symbol == 'BTC' or symbol == 'BTCUSDT': # Aseguramos compatibilidad con ambos formatos
            return TrendFollowingStrategy()
            
        # 4. DEFAULT: Mean Reversion (Safest)
        return MeanReversionStrategy()