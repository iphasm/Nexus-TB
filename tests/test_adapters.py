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
from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter
from nexus_system.uplink.adapters.exchange_factory import get_exchange_driver, CRYPTO_EXCHANGES


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


class TestBybitAdapter(unittest.TestCase):
    """Test BybitAdapter - Enhanced order management."""
    
    def test_name(self):
        """Test adapter name."""
        adapter = BybitAdapter()
        self.assertEqual(adapter.name, "bybit")
    
    def test_supports_websocket(self):
        """Test WebSocket support flag."""
        adapter = BybitAdapter()
        self.assertTrue(adapter.supports_websocket())
    
    def test_has_cancel_all_orders(self):
        """Test BybitAdapter has cancel_all_orders method (key improvement)."""
        adapter = BybitAdapter()
        self.assertTrue(hasattr(adapter, 'cancel_all_orders'))
    
    def test_has_set_trading_stop(self):
        """Test BybitAdapter has set_trading_stop method."""
        adapter = BybitAdapter()
        self.assertTrue(hasattr(adapter, 'set_trading_stop'))
    
    def test_has_amend_order(self):
        """Test BybitAdapter has amend_order method."""
        adapter = BybitAdapter()
        self.assertTrue(hasattr(adapter, 'amend_order'))
    
    def test_symbol_formatting(self):
        """Test symbol formatting utilities."""
        adapter = BybitAdapter()
        self.assertEqual(adapter._format_symbol('BTCUSDT'), 'BTC/USDT:USDT')
        self.assertEqual(adapter._unformat_symbol('BTC/USDT:USDT'), 'BTCUSDT')


class TestExchangeFactory(unittest.TestCase):
    """Test exchange factory pattern."""
    
    def test_get_binance_driver(self):
        """Factory should return BinanceAdapter for BINANCE."""
        adapter = get_exchange_driver('BINANCE')
        self.assertIsInstance(adapter, BinanceAdapter)
    
    def test_get_bybit_driver(self):
        """Factory should return BybitAdapter for BYBIT."""
        adapter = get_exchange_driver('BYBIT')
        self.assertIsInstance(adapter, BybitAdapter)
    
    def test_get_alpaca_driver(self):
        """Factory should return AlpacaAdapter for ALPACA."""
        adapter = get_exchange_driver('ALPACA')
        self.assertIsInstance(adapter, AlpacaAdapter)
    
    def test_invalid_exchange_raises(self):
        """Factory should raise ValueError for unknown exchange."""
        with self.assertRaises(ValueError):
            get_exchange_driver('INVALID_EXCHANGE')
    
    def test_crypto_exchanges_constant(self):
        """CRYPTO_EXCHANGES should contain both Binance and Bybit."""
        self.assertIn('BINANCE', CRYPTO_EXCHANGES)
        self.assertIn('BYBIT', CRYPTO_EXCHANGES)


if __name__ == '__main__':
    unittest.main()
