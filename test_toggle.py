import pandas as pd
import numpy as np
from strategies.analyzer import analyze_market

def generate_test_data(length=300):
    """
    Generates data that should trigger BOTH strategies if configured correctly.
    """
    index = pd.date_range(start='2023-01-01', periods=length, freq='15min')
    
    # Rising Trend for Trend Velocity
    close = np.linspace(100, 200, length)
    
    # Volatility for ADX
    ranges = np.linspace(1.0, 5.0, length) 
    high = close + (ranges / 2)
    low = close - (ranges / 2)
    
    # Mean Reversion trigger adjustments
    # We need a dip below BB lower at the end? 
    # Or just ensure TV triggers. 
    # Let's focus on checking if 'source' changes when we disable logic.
    
    # Creating a guaranteed TV signal
    # TV needs: Close > HMA(55), DI+ > DI-, ADX > 20, ADX Rising, RSI > 50
    # Our synthetic data should satisfy this.
    
    df = pd.DataFrame({
        'open': close,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.normal(100, 10, length)
    }, index=index)
    
    return df

def test_toggles():
    print("Generating data...")
    df = generate_test_data()
    
    print("\n--- TEST 1: All Enabled ---")
    sig, metrics = analyze_market(df, {'mean_reversion': True, 'trend_velocity': True})
    print(f"Signal: {sig}")
    print(f"Source: {metrics.get('source')}")
    print(f"Debug: {metrics.get('debug')}")
    
    if not sig:
        print("⚠️ Data didn't trigger any strategy, test key verification might be weak.")
    
    print("\n--- TEST 2: Disable Trend Velocity ---")
    sig, metrics = analyze_market(df, {'mean_reversion': True, 'trend_velocity': False})
    print(f"Signal: {sig}")
    print(f"Source: {metrics.get('source')}")
    print(f"Debug TV Signal (should be False): {metrics['debug']['tv_signal']}")
    
    if metrics['debug']['tv_signal'] is False and metrics.get('source') != 'TrendVelocity':
        print("✅ Trend Velocity successfully disabled.")
    else:
        print("❌ Failed to disable Trend Velocity.")

    print("\n--- TEST 3: Disable All ---")
    sig, metrics = analyze_market(df, {'mean_reversion': False, 'trend_velocity': False})
    print(f"Signal: {sig}")
    if not sig and metrics.get('source') == 'None':
        print("✅ All strategies disabled successfully.")
    else:
        print("❌ Disable all failed.")

if __name__ == "__main__":
    test_toggles()
