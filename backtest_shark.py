import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import time

# Configuration
START_DATE = "2025-10-09 00:00:00"
END_DATE = "2025-10-11 23:59:59"
CAPITAL = 1000
TARGETS = ['SOL/USDT', 'DOGE/USDT', 'SUI/USDT', 'RENDER/USDT', 'WIF/USDT'] # High beta targets
CRASH_THRESHOLD = 0.03  # 3% drop
WINDOW_MINUTES = 1      # 60 seconds (1 candle for simplicity in backtest, or rolling window)

def fetch_data(symbol, start_str, end_str):
    print(f"📥 Fetching data for {symbol}...")
    exchange = ccxt.binance()
    start_ts = int(datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ts = int(datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp() * 1000)
    
    all_candles = []
    current_ts = start_ts
    
    while current_ts < end_ts:
        try:
            candles = exchange.fetch_ohlcv(symbol, timeframe='1m', since=current_ts, limit=1000)
            if not candles:
                break
            
            all_candles.extend(candles)
            current_ts = candles[-1][0] + 60000
            
            # Rate limit
            time.sleep(0.1)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            break
            
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def run_backtest():
    print("🦈 Initiating Shark Mode Backtest Simulation...")
    print(f"📅 Period: {START_DATE} to {END_DATE}")
    print(f"💰 Capital: ${CAPITAL}")
    
    # 1. Fetch BTC Data (Trigger)
    btc_df = fetch_data('BTC/USDT', START_DATE, END_DATE)
    print(f"✅ BTC Data: {len(btc_df)} candles")
    
    # 2. Fetch Target Data
    target_dfs = {}
    for t in TARGETS:
        target_dfs[t] = fetch_data(t, START_DATE, END_DATE)
        
    # 3. Simulation Loop
    # We will iterate BTC candles. If a candle (or rolling window) shows >3% drop, we trigger shorts.
    
    events = []
    active_positions = [] # List of dicts
    balance = CAPITAL
    
    # Allocation per trade
    allocation = CAPITAL / len(TARGETS)
    
    # Pre-calculate rolling drop for BTC to speed up
    # Calculate % change from high of rolling window to current low? 
    # Or just simpler: Open vs Close of same minute for flash crashes, or 1m rolling.
    # SharkSentinel uses a rolling deque of real-time ticks.
    # Best approximation for 1m OHLCV: Low of current candle vs Open of current (or High of previous).
    # Let's use: (Low - High.rolling(5).max()) / High.rolling(5).max()
    # If that drop > 3% within 5 mins, TRIGGER.
    
    # Sentinel Window is 60s. So we check: (Current Low - Open) / Open < -0.03
    # Or strict 1m candle crash.
    
    btc_df['pct_change'] = (btc_df['low'] - btc_df['open']) / btc_df['open']
    
    triggers = btc_df[btc_df['pct_change'] <= -CRASH_THRESHOLD]
    
    print(f"\n⚡ Detected {len(triggers)} Shark Triggers (BTC > {CRASH_THRESHOLD*100}% drop in 1m)")
    
    total_pnl = 0
    trade_log = []
    
    for ts, row in triggers.iterrows():
        # Cooldown check: Don't trigger if we just triggered?
        # Sentinel has 5 min cooldown.
        last_trigger_ts = events[-1]['ts'] if events else None
        if last_trigger_ts and (ts - last_trigger_ts).total_seconds() < 300:
            continue
            
        events.append({'ts': ts, 'drop': row['pct_change']})
        print(f"🔴 ALERT: {ts} | BTC Crash {row['pct_change']*100:.2f}%")
        
        # Execute Shorts on Targets
        for symbol in TARGETS:
            df = target_dfs.get(symbol)
            if df is None or ts not in df.index:
                continue
                
            # Entry Price = Close of that minute (simulating finding it during the crash)
            # In reality, we enter DURING the crash, so maybe (Open + Close)/2 or Low?
            # Let's be conservative: Close of the crash candle.
            entry_price = df.loc[ts, 'close']
            
            # Exit Strategy: 
            # 1. Take Profit: +6% (Price drops 6%)
            # 2. Stop Loss: -3% (Price rises 3%)
            # 3. Time limit: Exit after 60 mins?
            
            # Look forward 60 mins
            future_slice = df.loc[ts:].iloc[1:61] # Next 60 candles
            
            exit_price = entry_price
            exit_reason = "Time Limit"
            pnl = 0
            
            for f_ts, f_row in future_slice.iterrows():
                # Check TP (Short: Price goes DOWN)
                # If Low < Entry * 0.94
                if f_row['low'] <= entry_price * 0.94:
                    exit_price = entry_price * 0.94
                    exit_reason = "Take Profit (+6%)"
                    break
                    
                # Check SL (Short: Price goes UP)
                # If High > Entry * 1.03
                if f_row['high'] >= entry_price * 1.03:
                    exit_price = entry_price * 1.03
                    exit_reason = "Stop Loss (-3%)"
                    break
            else:
                # Time limit exit
                if not future_slice.empty:
                    exit_price = future_slice.iloc[-1]['close']
            
            # Calc PnL (Short)
            # (Entry - Exit) / Entry * Allocation
            roi = (entry_price - exit_price) / entry_price
            profit = allocation * roi
            
            # Leverage? User asked for "futures account". Assuming 1x for safety unless specified? 
            # Shark mode implies sniper aggression. Let's assume 5x leverage typical for setups.
            # User said "$1000 on futures". Backtest usually raw expected equity delta.
            # Let's stick to 1x to show raw asset performance, maybe note leverage multiplier.
            # ACTUALLY, "Shark Mode" usually implies high leverage. Let's use 5x.
            
            LEVERAGE = 5
            realized_profit = profit * LEVERAGE
            
            total_pnl += realized_profit
            trade_log.append({
                'symbol': symbol,
                'entry_ts': ts,
                'entry': entry_price,
                'exit': exit_price,
                'reason': exit_reason,
                'roi_raw': roi * 100,
                'pnl': realized_profit
            })
            
            print(f"   🔻 SHORT {symbol} @ {entry_price:.4f} -> {exit_reason} @ {exit_price:.4f} | PnL: ${realized_profit:.2f}")

    print("\n" + "="*50)
    print("🐋 BACKTEST RESULTS")
    print("="*50)
    print(f"Initial Capital: ${CAPITAL}")
    print(f"Total Trades: {len(trade_log)}")
    print(f"Gross PnL (5x Lev): ${total_pnl:.2f}")
    print(f"Final Equity: ${CAPITAL + total_pnl:.2f}")
    print(f"ROI: {(total_pnl/CAPITAL)*100:.2f}%")
    print("="*50)

if __name__ == "__main__":
    run_backtest()
