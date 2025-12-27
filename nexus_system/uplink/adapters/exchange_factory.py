"""
Exchange Factory.
Factory pattern for instantiating exchange adapters.
"""

import os
from typing import Optional
from .base import IExchangeAdapter
from .binance_adapter import BinanceAdapter
from .bybit_adapter import BybitAdapter
from .alpaca_adapter import AlpacaAdapter


# Supported exchange types
CRYPTO_EXCHANGES = ['BINANCE', 'BYBIT']
STOCK_EXCHANGES = ['ALPACA']


def get_exchange_driver(
    exchange_name: str,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None
) -> IExchangeAdapter:
    """
    Factory function to get the appropriate exchange adapter.
    
    Args:
        exchange_name: "BINANCE", "BYBIT", or "ALPACA"
        api_key: Optional API key (falls back to env vars)
        api_secret: Optional API secret (falls back to env vars)
    
    Returns:
        Initialized IExchangeAdapter instance
        
    Raises:
        ValueError: If exchange_name is not supported
    """
    name = exchange_name.upper().strip()
    
    if name == 'BINANCE':
        return BinanceAdapter(
            api_key=api_key or os.getenv('BINANCE_API_KEY'),
            api_secret=api_secret or os.getenv('BINANCE_SECRET')
        )
    
    elif name == 'BYBIT':
        return BybitAdapter(
            api_key=api_key or os.getenv('BYBIT_API_KEY'),
            api_secret=api_secret or os.getenv('BYBIT_SECRET')
        )
    
    elif name == 'ALPACA':
        return AlpacaAdapter(
            api_key=api_key or os.getenv('APCA_API_KEY_ID'),
            api_secret=api_secret or os.getenv('APCA_API_SECRET_KEY')
        )
    
    else:
        raise ValueError(f"Unsupported exchange: {exchange_name}. Supported: {CRYPTO_EXCHANGES + STOCK_EXCHANGES}")


def get_crypto_driver(config: dict) -> IExchangeAdapter:
    """
    Get the user's preferred crypto exchange adapter based on config.
    
    Args:
        config: User session config dict containing 'crypto_exchange'
        
    Returns:
        IExchangeAdapter for crypto trading (Binance or Bybit)
    """
    exchange = config.get('crypto_exchange', 'BINANCE').upper()
    
    if exchange not in CRYPTO_EXCHANGES:
        print(f"⚠️ Unknown crypto exchange '{exchange}', defaulting to BINANCE")
        exchange = 'BINANCE'
    
    # Get credentials from config or env
    if exchange == 'BYBIT':
        return get_exchange_driver(
            'BYBIT',
            api_key=config.get('bybit_key'),
            api_secret=config.get('bybit_secret')
        )
    else:
        return get_exchange_driver(
            'BINANCE',
            api_key=config.get('binance_key'),
            api_secret=config.get('binance_secret')
        )
