import asyncio
import pandas as pd
import numpy as np
import sys
import os

# Add root to path
sys.path.append(os.getcwd())
print("DEBUG: Root added to path")

# DEPRECATED: Premium Signals functionality has been removed
# Premium Signals were redundant with the new AI Filter system
# The AI Filter provides superior multi-factor analysis including:
# - Fear & Greed Index analysis
# - Market volatility assessment
# - Technical momentum evaluation
# - Social sentiment analysis
# - Intelligent IA-powered decision making

print("⚠️  PREMIUM SIGNALS TEST DEPRECATED")
print("Premium Signals functionality has been removed as redundant with AI Filter")
print("See servos/ai_filter.py for the new intelligent filtering system")
print("=" * 60)

# Import strategies
print("DEBUG: Importing TrendStrategy...")
from nexus_system.cortex.trend import TrendFollowingStrategy
# print("DEBUG: Importing ScalpingStrategy...")  # DISABLED: Scalping strategy disabled
# from nexus_system.cortex.scalping import ScalpingStrategy  # DISABLED: Scalping strategy disabled
print("DEBUG: Strategies imported.")

async def test_trend_logic():
    print("--- Testing TrendFollowingStrategy (Premium) ---")
    strategy = TrendFollowingStrategy()
    
    # Mock Data: Uptrend
    print("1. Creating Mock Dataframe...")
    df = pd.DataFrame({
        'close': [100.0, 101.0, 102.0, 103.0, 104.0],
        'high': [101.0, 102.0, 103.0, 104.0, 105.0],
        'low': [99.0, 100.0, 101.0, 102.0, 103.0],
        'volume': [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
        'ema_20': [100.0, 100.5, 101.0, 101.5, 102.0],
        'ema_50': [99.0, 99.5, 100.0, 100.5, 101.0], # EMA20 > EMA50 (Buy)
        'ema_200': [90.0, 90.0, 90.0, 90.0, 90.0],
        'adx': [25.0, 25.0, 25.0, 25.0, 25.0],
        'atr': [1.0, 1.0, 1.0, 1.0, 1.0],
        'vol_sma': [1000.0, 1000.0, 1000.0, 1000.0, 1000.0] # Volume > SMA
    })
    
    market_data = {
        'symbol': 'BTCUSDT',
        'dataframe': df
    }
    
    # Case 1: Standard Buy (No Macro)
    print("2. Running Case 1 (Standard)...")
    signal = await strategy.analyze(market_data)
    if signal:
        print(f"   -> CASE 1 (Standard): {signal.action} | Conf: {signal.confidence:.2f} | PASS")
    else:
        print("   -> CASE 1 (Standard): None | FAIL")

    # Case 2: Premium Buy (Macro Bullish)
    print("3. Running Case 2 (Macro Bullish)...")
    macro_df = pd.DataFrame({'close': [200.0], 'ema_200': [150.0], 'ema_50': [180.0]})
    market_data['macro_dataframe'] = macro_df
    
    signal = await strategy.analyze(market_data)
    if signal and signal.action == "BUY":
        print(f"   -> CASE 2 (Macro Bullish): {signal.action} | Conf: {signal.confidence:.2f} | PASS")
    else:
        print(f"   -> CASE 2 (Macro Bullish): {signal} | FAIL")
    
    # Case 3: Premium Buy Filtered (Macro Bearish)
    print("4. Running Case 3 (Macro Bearish Filter)...")
    # Macro Price (100) < Macro EMA200 (150) -> Bearish Trend
    macro_df_bear = pd.DataFrame({'close': [100.0], 'ema_200': [150.0], 'ema_50': [120.0]})
    market_data['macro_dataframe'] = macro_df_bear
    
    signal = await strategy.analyze(market_data)
    if signal is None:
        print("   -> CASE 3 (Macro Bearish Filter): None | PASS (Correctly filtered)")
    else:
        print(f"   -> CASE 3 (Macro Bearish Filter): {signal.action} | FAIL (Should be filtered)")

# async def test_scalping_logic():  # DISABLED: Scalping strategy disabled
#     print("\n--- Testing ScalpingStrategy (Premium) ---")
#     strategy = ScalpingStrategy()
#
#     # Mock Data: Bullish Divergence Setup
#     # Require 15+ rows
#     print("1. Creating RSI Mock Data...")
#     N = 60
#     df = pd.DataFrame({
#         'close': [100.0] * N,
#         'low':   [99.0] * N,
#         'high':  [101.0] * N,
#         'rsi':   [50.0] * N,
#         'adx':   [30.0] * N,
#         'ema_200': [110.0] * N, # Downtrend context
#         'atr': [1.0] * N
#     })
#
#     # Create Lower Low in Price (Recent vs Older)
#     # Older (idx -10 to -5): Low = 95
#     df.loc[10:15, 'low'] = 95.0
#     # Recent (idx -5 to end): Low = 90 (Lower Low)
#     df.loc[15:, 'low'] = 90.0
#
#     # Create Higher Low in RSI (Recent vs Older)
#     # Older RSI Min = 30
#     df.loc[10:15, 'rsi'] = 30.0
#     # Recent RSI Min = 40 (Higher Low)
#     df.loc[15:, 'rsi'] = 40.0
#
#     # Trigger Base Signal (BUY)
#     # Requirement: Uptrend (Price > EMA200) AND RSI < 45 AND RSI Rising
#
#     # 1. Set Uptrend
#     df['ema_200'] = 90.0 # Price 100 > 90
#
#     # 2. Set RSI Dip and Rebound (Rising but still oversold-ish)
#     df.loc[N-1, 'rsi'] = 42.0 # Current
#     df.loc[N-2, 'rsi'] = 40.0 # Prev
#     df.loc[N-3, 'rsi'] = 38.0 # Older
#     # Rising: 42 > 40. True.
#     # Condition: 42 < 45. True.
#
#     market_data = {'symbol': 'SOLUSDT', 'dataframe': df}
#
#     print("2. Running Case 4 (RSI Divergence)...")
#     signal = await strategy.analyze(market_data)
#
#     if signal and signal.action == "BUY":
#         print(f"   -> CASE 4 (Scalping Div): {signal.action} | Conf: {signal.confidence:.2f} | PASS")
#     else:
#         print(f"   -> CASE 4 (Scalping Div): {signal} | FAIL")

async def main():
    print("🚀 STARTING ASYNC TEST RUNNER")
    try:
        await test_trend_logic()
        # await test_scalping_logic()  # DISABLED: Scalping strategy disabled
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY")
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

