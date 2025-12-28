"""
Exchange Adapter Interface.
Defines the contract for all exchange implementations.
"""

import abc
from typing import Dict, Any, List, Optional, Callable
import pandas as pd


class IExchangeAdapter(abc.ABC):
    """
    Abstract Base Class for Exchange Adapters.
    All exchange implementations (Binance, Alpaca, etc.) must implement this interface.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Exchange name identifier."""
        pass

    @abc.abstractmethod
    async def initialize(self, **kwargs) -> bool:
        """
        Initialize connection to the exchange.
        Returns True if successful.
        """
        pass

    @abc.abstractmethod
    async def fetch_candles(
        self, 
        symbol: str, 
        timeframe: str = '15m', 
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch OHLCV candle data.
        Returns DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass

    @abc.abstractmethod
    async def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance.
        Returns dict like {'total': 1000.0, 'available': 800.0, 'currency': 'USDT'}
        """
        pass

    @abc.abstractmethod
    async def place_order(
        self, 
        symbol: str, 
        side: str,  # 'BUY' or 'SELL'
        order_type: str,  # 'MARKET', 'LIMIT', 'STOP_MARKET', etc.
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Place an order.
        Returns order result with at least {'orderId': str, 'status': str}
        """
        pass

    @abc.abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an order.
        Returns True if successful.
        """
        pass

    @abc.abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get active positions.
        Returns list of position dicts.
        """
        pass

    @abc.abstractmethod
    async def close(self):
        """
        Close connection and cleanup resources.
        """
        pass

    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get symbol rules (precision, filters).
        Default returns empty dict. Override if supported.
        """
        return {}

    async def cancel_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol."""
        return False

    async def close_position(self, symbol: str) -> bool:
        """Close specific position."""
        return False

    # Optional: WebSocket streaming
    def supports_websocket(self) -> bool:
        """Override to return True if adapter supports real-time streaming."""
        return False

    async def stream_candles(
        self, 
        symbols: List[str], 
        callback: Callable[[str, dict], None]
    ):
        """
        Stream real-time candle updates.
        Override if supports_websocket() returns True.
        """
        raise NotImplementedError("WebSocket streaming not supported")
