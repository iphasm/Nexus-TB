"""
Unit Tests for Kelly Criterion Position Sizing.
"""
import unittest
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from servos.trading_manager import AsyncTradingSession

class TestKellyCriterion(unittest.TestCase):
    
    def setUp(self):
        # Mock session with dummy credentials
        self.session = AsyncTradingSession("123", "key", "secret")
        # Mock config with Kelly Disabled initially
        self.session.config = {
            'use_kelly_criterion': False,
            'max_capital_pct': 0.10,
            'kelly_fraction': 0.5,
            'win_rate_est': 0.55,
            'risk_reward_est': 1.5
        }
    
    def test_base_sizing(self):
        """Test standard 1% risk sizing (Kelly Disabled)."""
        # Allow enough capital for this test
        self.session.config['max_capital_pct'] = 0.60
        
        equity = 10000
        price = 100
        sl_price = 98  # $2 risk per unit
        leverage = 1
        min_notional = 5
        
        # Expected: Risk 1% = $100. Dist=$2. Qty = 50.
        # Position Value = 50 * 100 = 5000 (50% of equity).
        # Requires max_capital_pct >= 0.50.
        qty = self.session.calculate_dynamic_size(equity, price, sl_price, leverage, min_notional)
        self.assertAlmostEqual(qty, 50.0, places=1)

    def test_kelly_sizing(self):
        """
        Test Kelly Sizing.
        p = 0.55, b = 1.5, f = 0.5 (Half)
        Kelly* = 0.55 - (0.45 / 1.5) = 0.55 - 0.3 = 0.25 (25%)
        Half-Kelly = 12.5%
        
        So risk should be 12.5% of Equity ($1250).
        Dist = $2. Qty = 625.
        
        HOWEVER, we have a MAX CAP check (max_capital_pct=0.10 -> $1000 value).
        Value of 625 units @ $100 = $62,500. This is huge.
        Let's adjust leverage/cap for the test to see raw kelly vs capped.
        """
        self.session.config['use_kelly_criterion'] = True
        self.session.config['max_capital_pct'] = 1.0 # Allow full equity for this test logic
        
        equity = 10000
        price = 100
        sl_price = 98
        leverage = 1
        min_notional = 5
        
        # Expected Risk = 12.5% of 10k = 1250.
        # Qty = 1250 / 2 = 625.
        qty = self.session.calculate_dynamic_size(equity, price, sl_price, leverage, min_notional)
        
        # Check if capped by max_capital logic?
        # max_cap_val = 10000 * 1.0 * 1 = 10000. 
        # max_qty = 10000 / 100 = 100.
        
        # So it SHOULD be capped at 100 units.
        self.assertAlmostEqual(qty, 100.0, places=1, msg="Should be capped by max allocation")

    def test_kelly_small_cap(self):
        """Test Kelly with strict cap."""
        self.session.config['use_kelly_criterion'] = True
        self.session.config['max_capital_pct'] = 0.10 # 10% Cap ($1000)
        
        equity = 10000
        price = 100
        sl_price = 98
        leverage = 5
        
        # Kelly says risk 12.5% ($1250) -> 625 units.
        # Cap says: 10% of equity ($1000) * 5x Lev = $5000 notional.
        # Max Qty = 5000 / 100 = 50 units.
        
        qty = self.session.calculate_dynamic_size(equity, price, sl_price, leverage, 5)
        self.assertAlmostEqual(qty, 50.0, places=1, msg="Should be strictly capped at 10% margin")


if __name__ == '__main__':
    unittest.main()
