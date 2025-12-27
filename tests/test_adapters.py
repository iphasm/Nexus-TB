"""
Unit tests for Exchange Adapters.
Uses mocks to avoid real API calls.
"""
import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch

from nexus_system.uplink.adapters.base import IExchangeAdapter
from nexus_system.uplink.adapters.binance_adapter import BinanceAdapter
from nexus_system.uplink.adapters.alpaca_adapter import AlpacaAdapter


class TestIExchangeAdapter(unittest.TestCase):
    """Test interface contract."""
    
    def test_interface_methods(self):
        """Verify IExchangeAdapter defines required methods."""
        required_methods = [
            'name', 'initialize', 'fetch_candles', 'get_account_balance',
            'place_order', 'cancel_order', 'get_positions', 'close'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(IExchangeAdapter, method), f"Should have {method}")


class TestBinanceAdapter(unittest.TestCase):
    """Test BinanceAdapter."""
    
    def test_name(self):
        """Test adapter name."""
        adapter = BinanceAdapter()
        self.assertEqual(adapter.name, "binance")
    
    def test_supports_websocket(self):
        """Test WebSocket support flag."""
        adapter = BinanceAdapter()
        self.assertTrue(adapter.supports_websocket())


class TestAlpacaAdapter(unittest.TestCase):
    """Test AlpacaAdapter."""
    
    def test_name(self):
        """Test adapter name."""
        adapter = AlpacaAdapter()
        self.assertEqual(adapter.name, "alpaca")
    
    def test_supports_websocket(self):
        """Test WebSocket support flag."""
        adapter = AlpacaAdapter()
        self.assertTrue(adapter.supports_websocket())


if __name__ == '__main__':
    unittest.main()
