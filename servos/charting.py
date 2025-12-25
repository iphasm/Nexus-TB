import os
import pandas as pd
import mplfinance as mpf
from datetime import datetime

# Ensure charts directory exists
CHARTS_DIR = os.path.join(os.getcwd(), "data", "charts")
if not os.path.exists(CHARTS_DIR):
    os.makedirs(CHARTS_DIR, exist_ok=True)

def cleanup_old_charts(max_files=20):
    """Keep only the latest N chart files."""
    try:
        files = [os.path.join(CHARTS_DIR, f) for f in os.listdir(CHARTS_DIR) if f.endswith('.png')]
        files.sort(key=os.path.getmtime)
        
        while len(files) > max_files:
            os.remove(files.pop(0))
    except Exception as e:
        print(f"⚠️ Chart Cleanup Error: {e}")

def generate_trade_chart(symbol: str, df: pd.DataFrame, side: str, entry: float, sl: float, tp: float, timeframe: str = "15m") -> str:
    """
    Generates a candlestick chart with Entry/SL/TP lines.
    Returns the absolute path to the saved image.
    """
    try:
        # 1. Prepare Data
        # Ensure proper columns and index
        # Expected: open, high, low, close, volume (lowercase from Binance) -> Title Case for mpf
        df = df.copy()
        df.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
        }, inplace=True)
        
        if not isinstance(df.index, pd.DatetimeIndex):
            # If timestamp column exists (ensure it's ms)
            if 'timestamp' in df.columns:
                df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('Date', inplace=True)
            elif 'close_time' in df.columns:
                df['Date'] = pd.to_datetime(df['close_time'], unit='ms')
                df.set_index('Date', inplace=True)

        # Slice last 60 candles for clarity
        plot_df = df.tail(60)

        # 2. visual Configuration
        # Determine Title Color based on Side
        title_color = '#00ff00' if side == 'LONG' else '#ff0000'
        title = f"{symbol} - {timeframe} | {side} SIGNAL"
        
        # Output Filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{symbol}_{side}_{timestamp}.png"
        filepath = os.path.join(CHARTS_DIR, filename)
        
        # 3. Custom Night Style
        # Green Up, Red Down
        mc = mpf.make_marketcolors(
            up='#2ebd85', down='#f6465d', 
            edge='inherit', wick='inherit', 
            volume={'up': '#2ebd85', 'down': '#f6465d'}
        )
        s = mpf.make_mpf_style(
            marketcolors=mc, 
            base_mpf_style='nightclouds', 
            gridstyle=':', 
            facecolor='#0b0e11', # Binance Dark BG
            edgecolor='#0b0e11'
        )
        
        # 4. Indicators (Calculate basic MA if not present)
        add_plots = []
        if 'hma_55' in plot_df.columns:
            add_plots.append(mpf.make_addplot(plot_df['hma_55'], color='yellow', width=1.5))
        if 'bb_upper' in plot_df.columns and 'bb_lower' in plot_df.columns:
            add_plots.append(mpf.make_addplot(plot_df['bb_upper'], color='cyan', width=0.5, alpha=0.3))
            add_plots.append(mpf.make_addplot(plot_df['bb_lower'], color='cyan', width=0.5, alpha=0.3))

        # 5. Horizontal Lines (Entry, SL, TP)
        # Entry (Blue), SL (Red), TP (Green)
        hlines = dict(
            hlines=[entry, sl, tp], 
            colors=['#3b82f6', '#ef4444', '#22c55e'], 
            linewidths=[1.5, 1.5, 1.5], 
            alpha=0.9,
            linestyle='--'
        )

        # 6. Generate Plot
        mpf.plot(
            plot_df, 
            type='candle', 
            style=s, 
            volume=False, 
            addplot=add_plots,
            hlines=hlines,
            title=title,
            savefig=dict(fname=filepath, dpi=100, bbox_inches='tight'),
            tight_layout=True,
            warn_too_much_data=1000
        )
        
        # Cleanup old files
        cleanup_old_charts()
        
        return filepath

    except Exception as e:
        print(f"❌ Chart Generation Error: {e}")
        return ""
