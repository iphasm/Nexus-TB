import pandas as pd
import time
from data.fetcher import get_market_data
from strategies.engine import StrategyEngine

def test_strategy_engine():
    print("🧪 Testing StrategyEngine Module...")
    
    # 1. Fetch Real Data (BTCUSDT)
    print("⏳ Fetching BTCUSDT data...")
    df = get_market_data('BTCUSDT', timeframe='15m', limit=500)
    
    if df.empty:
        print("❌ Failed to fetch data.")
        return

    print(f"✅ Data fetched: {len(df)} candles.")

    # 2. Initialize Engine
    engine = StrategyEngine(df)
    
    # 3. Analyze
    t0 = time.time()
    result = engine.analyze()
    t1 = time.time()
    
    print(f"⏱️ Analysis Time: {(t1-t0)*1000:.2f}ms")
    
    # 4. Output Results
    print("\n📊 --- RESULTS ---")
    print(f"Signal: {result['signal']}")
    print(f"Reason: {result['reason']}")
    print("\n📈 Metrics:")
    for k, v in result['metrics'].items():
        print(f"  • {k}: {v}")

    # 5. Sanity Checks
    metrics = result['metrics']
    if metrics['bb_upper'] == 0 or metrics['kc_upper'] == 0:
        print("❌ Error: Indicators are zero.")
    else:
        print("✅ Indicators calculated successfully.")
        
    if 'squeeze_on' in metrics:
        print(f"✅ Squeeze Detection: {'ACTIVE' if metrics['squeeze_on'] else 'INACTIVE'}")

if __name__ == "__main__":
    test_strategy_engine()
