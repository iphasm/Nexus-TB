"""
Unit tests for Strategy Registry.
"""
import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nexus_system.cortex.registry import StrategyRegistry
from nexus_system.cortex.base import IStrategy


class TestStrategyRegistry(unittest.TestCase):
    
    def test_discovery(self):
        """Test that registry discovers strategies."""
        strategies = StrategyRegistry.get_all()
        
        print(f"Discovered strategies: {list(strategies.keys())}")
        
        # Should find at least some strategies
        self.assertGreater(len(strategies), 0, "Should discover at least one strategy")
        
        # Check known strategies are found
        known = ['TrendFollowingStrategy', 'GridTradingStrategy', 'MeanReversionStrategy']  # ScalpingStrategy disabled
        for name in known:
            self.assertIn(name, strategies, f"Should find {name}")

    def test_get_by_name(self):
        """Test getting strategy by name."""
        strategy_cls = StrategyRegistry.get('TrendFollowingStrategy')
        
        self.assertIsNotNone(strategy_cls, "Should find TrendFollowingStrategy")
        self.assertTrue(issubclass(strategy_cls, IStrategy), "Should be IStrategy subclass")

    def test_instantiate(self):
        """Test instantiating a strategy."""
        strategy = StrategyRegistry.instantiate('TrendFollowingStrategy')
        
        self.assertIsNotNone(strategy, "Should instantiate TrendFollowingStrategy")
        self.assertIsInstance(strategy, IStrategy, "Should be IStrategy instance")
        self.assertTrue(hasattr(strategy, 'name'), "Should have name property")

    def test_list_names(self):
        """Test listing strategy names."""
        names = StrategyRegistry.list_names()
        
        print(f"Strategy names: {names}")
        
        self.assertIsInstance(names, list)
        self.assertGreater(len(names), 0)


if __name__ == '__main__':
    unittest.main()
