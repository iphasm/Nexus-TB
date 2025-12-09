import pandas as pd
import numpy as np
from data.fetcher import get_market_data
from strategies.indicators import (
    calculate_rsi, calculate_stoch_rsi, calculate_bollinger_bands,
    calculate_ema, calculate_hma, calculate_adx, calculate_adx_slope
)

def run_analysis():
    print("⏳ Fetching 1000 candles of BTCUSDT (15m)...")
    try:
        # Fetch data
        df = get_market_data('BTCUSDT', timeframe='15m', limit=1000)
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        # Build dummy data if fetch fails (fallback for offline dev)
        print("⚠️ switching to dummy data for testing...")
        dates = pd.date_range(start='2024-01-01', periods=1000, freq='15min')
        df = pd.DataFrame({
            'open': np.linspace(40000, 60000, 1000),
            'high': np.linspace(40100, 60100, 1000),
            'low': np.linspace(39900, 59900, 1000),
            'close': np.linspace(40050, 60050, 1000) + np.random.normal(0, 100, 1000),
            'volume': np.random.normal(1000, 100, 1000)
        }, index=dates)

    if df.empty:
        print("❌ Dataframe empty.")
        return

    print(f"✅ Loaded {len(df)} candles.")

    # --- 1. Calculate Indicators (Vectorized) ---
    print("📊 Calculating Indicators...")
    
    # Common
    df['ema_200'] = calculate_ema(df['close'], period=200)
    df['rsi'] = calculate_rsi(df['close'], period=14)
    
    # MR Specific
    bb = calculate_bollinger_bands(df['close'], period=20, std_dev=2)
    df['bb_lower'] = bb['lower']
    df['vol_sma_20'] = df['volume'].rolling(window=20).mean()
    stoch = calculate_stoch_rsi(df['rsi'], period=14, k_period=3, d_period=3)
    df['stoch_k'] = stoch['k']
    df['stoch_d'] = stoch['d']
    
    # TV Specific
    df['hma_55'] = calculate_hma(df['close'], period=55)
    adx_df = calculate_adx(df, period=14)
    df['adx'] = adx_df['adx']
    df['plus_di'] = adx_df['plus_di']
    df['minus_di'] = adx_df['minus_di']
    df['adx_rising'] = calculate_adx_slope(df['adx'])

    # --- 2. Logic Simulation (Vectorized-ish iteration) ---
    print("🧠 Simulating Strategy Logic...")
    
    results = {
        'timestamp': [],
        'price': [],
        'mr_signal': [],
        'tv_signal': [],
        'combined_signal': []
    }
    
    # We iterate from 200 to end to ensure indicators have warmed up
    for i in range(200, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        # --- Mean Reversion Logic ---
        # 1. Setup: Close < BB_Lower
        mr_setup = curr['close'] < curr['bb_lower']
        # 2. Trend: Close > EMA_200
        mr_trend = curr['close'] > curr['ema_200']
        # 3. Volume: Vol > 1.5 * Avg
        vol_avg = curr['vol_sma_20'] if pd.notna(curr['vol_sma_20']) else 1
        mr_vol = curr['volume'] > (vol_avg * 1.5)
        # 4. Trigger: Stoch Cross Up in Oversold
        mr_cross = (prev['stoch_k'] < prev['stoch_d']) and (curr['stoch_k'] > curr['stoch_d'])
        mr_zone = curr['stoch_k'] < 20
        mr_trigger = mr_cross and mr_zone
        
        mr_signal = mr_setup and mr_trend and mr_vol and mr_trigger
        
        # --- Trend Velocity Logic ---
        # 1. Trend: Close > HMA 55
        tv_trend = curr['close'] > curr['hma_55']
        # 2. Direction: DI+ > DI-
        tv_dir = curr['plus_di'] > curr['minus_di']
        # 3. Strength: ADX > 20 and Rising
        tv_str = curr['adx'] > 20
        tv_rise = bool(curr['adx_rising'])
        # 4. Mom: RSI > 50
        tv_mom = curr['rsi'] > 50
        
        tv_signal = tv_trend and tv_dir and tv_str and tv_rise and tv_mom
        
        results['timestamp'].append(df.index[i])
        results['price'].append(curr['close'])
        results['mr_signal'].append(mr_signal)
        results['tv_signal'].append(tv_signal)
        results['combined_signal'].append(mr_signal or tv_signal)

    res_df = pd.DataFrame(results)
    
    # --- 3. Analysis ---
    total_candles = len(res_df)
    count_mr = res_df['mr_signal'].sum()
    count_tv = res_df['tv_signal'].sum()
    count_both = ((res_df['mr_signal']) & (res_df['tv_signal'])).sum()
    count_combined = res_df['combined_signal'].sum()
    
    print("\n" + "="*40)
    print("📈 STRATEGY UTILIZATION REPORT (BTCUSDT 15m)")
    print("="*40)
    print(f"Candles Analyzed: {total_candles} (~{total_candles/4/24:.1f} days)")
    
    print(f"\n1️⃣ Mean Reversion (MR)")
    print(f"   - Signals: {count_mr}")
    print(f"   - Frequency: Every ~{total_candles/count_mr:.1f} candles ({total_candles/count_mr/4:.1f} hours)" if count_mr else "   - Frequency: Never")
    
    print(f"\n2️⃣ Trend Velocity (TV)")
    print(f"   - Signals: {count_tv}")
    print(f"   - Frequency: Every ~{total_candles/count_tv:.1f} candles ({total_candles/count_tv/4:.1f} hours)" if count_tv else "   - Frequency: Never")

    print(f"\n3️⃣ Overlap & Confluence")
    print(f"   - Overlap (Both True): {count_both}")
    print(f"   - Correlation: Are they firing together? {count_both}/{count_combined} times.")
    
    print(f"\n4️⃣ Total Active Signals (OR Logic)")
    print(f"   - Total Triggers: {count_combined}")
    print(f"   - Utilization Increases: +{(count_combined - max(count_mr, count_tv))} signals vs best single strategy")

    # Sample signals
    if count_combined > 0:
        print("\n🔍 Recent 5 Signals:")
        last_sig = res_df[res_df['combined_signal']].tail(5)
        for _, row in last_sig.iterrows():
            source = []
            if row['mr_signal']: source.append("MR")
            if row['tv_signal']: source.append("TV")
            print(f"   - {row['timestamp']} @ ${row['price']:.2f} | Type: {'+'.join(source)}")

if __name__ == "__main__":
    run_analysis()
