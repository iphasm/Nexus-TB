from typing import Dict, Any
from .base import IStrategy
from .trend import TrendFollowingStrategy
from .grid import GridTradingStrategy
from .mean_reversion import MeanReversionStrategy
from .scalping import ScalpingStrategy
from .classifier import MarketClassifier

# Import the config MODULE (not individual vars) for runtime access
# Import the system directive (formerly config)
import system_directive as qconfig

class StrategyFactory:
    """
    Dynamic Factory to assign strategies based on asset profile and Global Config.
    Reads config at RUNTIME to respect changes made via /assets menu.
    Uses MarketClassifier for intelligent selection.
    """
    
    @staticmethod
    def get_strategy(symbol: str, market_data: Dict[str, Any]) -> IStrategy:
        """
        Assigns the optimal strategy based on Market Regime Classification.
        
        Args:
            symbol: Asset symbol (e.g. BTCUSDT)
            market_data: Dictionary containing 'dataframe' with technical indicators
        """
        # 1. Classify Regime Logic
        regime_result = None
        
        # A. ML Classifier (If Enabled)
        if qconfig.ML_CLASSIFIER_ENABLED:
            try:
                from .ml_classifier import MLClassifier
                regime_result = MLClassifier.classify(market_data)
                if regime_result:
                    # Optional: Log usage
                    pass
            except Exception as e:
                print(f"⚠️ ML Classifier Failed: {e}")
        
        # B. Fallback to Rule-Based if ML disabled or failed
        if regime_result is None:
            regime_result = MarketClassifier.classify(market_data)
        
        # 2. Assign Strategy based on Regime
        strategy = None
        
        # TREND
        if regime_result.suggested_strategy == "TrendFollowing":
            if qconfig.ENABLED_STRATEGIES.get('TREND', True):
                strategy = TrendFollowingStrategy()
                
        # SCALPING (Volatile)
        elif regime_result.suggested_strategy == "Scalping":
            if qconfig.ENABLED_STRATEGIES.get('SCALPING', True):
                strategy = ScalpingStrategy()
                
        # GRID (Tight Range)
        elif regime_result.suggested_strategy == "Grid":
            if qconfig.ENABLED_STRATEGIES.get('GRID', True):
                strategy = GridTradingStrategy()
                
        # EXTENSIONS: Add more as needed (e.g. Breakout)
        
        # 3. Fallback: Mean Reversion (Safe default for Range/Uncertain)
        if strategy is None:
            # Default to MeanReversion if the suggested one is disabled or fallback needed
            if qconfig.ENABLED_STRATEGIES.get('MEAN_REVERSION', True):
                strategy = MeanReversionStrategy()
            else:
                # Absolute panic fallback if MeanReversion is disabled too (Unlikely)
                strategy = MeanReversionStrategy()
                
        # Attach regime metdata to strategy for logging
        if strategy and regime_result:
             strategy.regime_meta = regime_result
        
        return strategy

