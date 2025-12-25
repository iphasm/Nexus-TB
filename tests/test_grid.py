import pytest
import pandas as pd
import asyncio
from nexus_system.cortex.grid import GridTradingStrategy

@pytest.mark.asyncio
async def test_grid_logic():
    # Fix: Use small period for testing so we don't need 200 rows
    strategy = GridTradingStrategy(ema_period=5)
    
    # 1. Create Data (Trend UP then Revert)
    # EMA 5 is used. We need at least 5 rows.
    # We will manually set columns so strategy just reads them.
    # The strategy checks len(df) < ema_period, so we need >5 rows.
    # EMA 200 = 100
    # ATR = 1.0
    # Upper Band = 102.0
    # Lower Band = 98.0
    
    data = {
        'close': [100, 100, 100, 97.5, 102.5, 100],  # Close params
        'ema_5': [100, 100, 100, 100, 100, 100],  # Use ema_5 to match period
        'atr': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    }
    df = pd.DataFrame(data)
    
    # Test Case A: Price < Lower Band (97.5 < 98.0) -> BUY
    market_data_buy = {
        'symbol': 'BTCUSDT',
        'dataframe': df.iloc[0:4] # Ends at 97.5
    }
    
    signal_buy = await strategy.analyze(market_data_buy)
    assert signal_buy is not None
    assert signal_buy.action == "BUY"
    assert signal_buy.confidence >= 0.6
    
    # Test Case B: Price > Upper Band (102.5 > 102.0) -> SELL
    market_data_sell = {
        'symbol': 'BTCUSDT',
        'dataframe': df.iloc[0:5] # Ends at 102.5
    }
    
    signal_sell = await strategy.analyze(market_data_sell)
    assert signal_sell is not None
    assert signal_sell.action == "SELL"
    
    # Test Case C: Price Inside Bands (100) -> HOLD (None)
    market_data_hold = {
        'symbol': 'BTCUSDT',
        'dataframe': df.iloc[0:6] # Ends at 100
    }
    
    signal_hold = await strategy.analyze(market_data_hold)
    assert signal_hold is None

@pytest.mark.asyncio
async def test_grid_params():
    strategy = GridTradingStrategy(ema_period=5)
    
    # Mock Signal
    from nexus_system.cortex.base import Signal
    
    sig = Signal(
        symbol='BTC', action='BUY', confidence=0.8, price=100.0,
        metadata={'atr': 2.0}
    )
    
    params = strategy.calculate_entry_params(sig, 1000.0)
    
    # SL = Price - 4*ATR = 100 - 8 = 92
    assert params['stop_loss_price'] == 92.0
    assert params['leverage'] == 3
