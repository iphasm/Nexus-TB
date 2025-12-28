"""
Strategy Factory - Dynamic Assignment via Registry.
Uses StrategyRegistry for plugin-based strategy discovery.
"""

from typing import Dict, Any
from .base import IStrategy
from .registry import StrategyRegistry
from .classifier import MarketClassifier

# Import the system directive for runtime config access
import system_directive as qconfig


# Import maps from system_directive
from system_directive import STRATEGY_CLASS_MAP as STRATEGY_MAP, STRATEGY_CONFIG_MAP as CONFIG_KEY_MAP


class StrategyFactory:
    """
    Dynamic Factory to assign strategies based on asset profile and Global Config.
    Now uses StrategyRegistry for plugin-based strategy discovery.
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
            except Exception as e:
                print(f"⚠️ ML Classifier Failed: {e}")
        
        # B. Fallback to Rule-Based if ML disabled or failed
        if regime_result is None:
            regime_result = MarketClassifier.classify(market_data)
        
        # 2. Get suggested strategy name from classifier
        suggested = regime_result.suggested_strategy
        
        # 3. Check if strategy is enabled in config
        config_key = CONFIG_KEY_MAP.get(suggested, suggested.upper())
        default_enabled = False if suggested == 'Shark' else True
        
        if not qconfig.ENABLED_STRATEGIES.get(config_key, default_enabled):
            # Strategy disabled, fall through to fallback
            suggested = None
        
        # 4. Try to instantiate via Registry
        strategy = None
        
        if suggested:
            class_name = STRATEGY_MAP.get(suggested, f"{suggested}Strategy")
            strategy = StrategyRegistry.instantiate(class_name)
            
            if strategy:
                print(f"📦 Registry: Loaded {class_name} for {symbol}")
        
        # 5. Fallback: Mean Reversion (Safe default)
        if strategy is None:
            if qconfig.ENABLED_STRATEGIES.get('MEAN_REVERSION', True):
                strategy = StrategyRegistry.instantiate('MeanReversionStrategy')
            
            # Ultimate fallback if registry fails
            if strategy is None:
                from .mean_reversion import MeanReversionStrategy
                strategy = MeanReversionStrategy()
                print(f"⚠️ Registry fallback: Using direct import for MeanReversion")
        
        # 6. Attach regime metadata to strategy for logging
        if strategy and regime_result:
            strategy.regime_meta = regime_result
        
        return strategy
