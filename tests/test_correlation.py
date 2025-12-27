
import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from nexus_system.shield.correlation import CorrelationManager

class TestCorrelationManager(unittest.TestCase):
    def setUp(self):
        self.manager = CorrelationManager(max_correlation=0.85, window_size=50)

    def test_high_correlation(self):
        """Test rejection of highly correlated assets (e.g. BTC vs WBTC)."""
        # Create synthetic BTC data
        btc_prices = pd.Series(np.linspace(100, 200, 60))
        
        # Create WBTC data (almost identical)
        wbtc_prices = btc_prices * 1.001
        
        # 1. Update history for BTC (Active Position)
        self.manager.update_price_history('BTCUSDT', btc_prices)
        
        # 2. Check WBTC (Candidate)
        # Should be REJECTED (Unsafe)
        is_safe = self.manager.check_correlation('WBTCUSDT', wbtc_prices, ['BTCUSDT'])
        
        print(f"Test High Correlation: Safe? {is_safe}")
        self.assertFalse(is_safe, "Should reject highly correlated asset")

    def test_low_correlation(self):
        """Test acceptance of low correlated assets (e.g. BTC vs Stablecoin/inverse)."""
        # BTC Uptrend
        btc_prices = pd.Series(np.linspace(100, 200, 60))
        
        # Inverse/Random asset
        rand_prices = pd.Series(np.linspace(200, 100, 60)) # Distinct downtrend (-1 correlation)
        
        # 1. Update history for BTC
        self.manager.update_price_history('BTCUSDT', btc_prices)
        
        # 2. Check Random
        is_safe = self.manager.check_correlation('RANDUSDT', rand_prices, ['BTCUSDT'])
        
        print(f"Test Low Correlation: Safe? {is_safe}")
        self.assertTrue(is_safe, "Should accept low/negative correlated asset")

    def test_empty_history(self):
        """Test behavior when history is missing."""
        prices = pd.Series(np.linspace(100, 200, 60))
        
        # Check against an active position that has NO history stored
        # check_correlation iterates active_positions. If 'BTCUSDT' is active but logic didn't update it, it usually skips or fails safe.
        # In current implementation: "if existing_series is None: continue" -> So it returns True (Safe)
        is_safe = self.manager.check_correlation('ETHUSDT', prices, ['BTCUSDT'])
        
        self.assertTrue(is_safe, "Should fail safe if history missing")

if __name__ == '__main__':
    unittest.main()
