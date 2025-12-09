import pandas as pd
import numpy as np
import json
import os
from data.fetcher import get_market_data
from strategies.indicators import (
    calculate_rsi, calculate_hma, calculate_adx, calculate_adx_slope
)

def generate_chart():
    print("⏳ Fetching data for Visualization...")
    try:
        df = get_market_data('BTCUSDT', timeframe='15m', limit=1000)
    except Exception as e:
        print(f"Fallback to dummy data: {e}")
        dates = pd.date_range(end=pd.Timestamp.now(), periods=1000, freq='15min')
        df = pd.DataFrame({
             'time': dates,
             'open': np.linspace(90000, 95000, 1000),
             'high': np.linspace(90100, 95100, 1000),
             'low': np.linspace(89900, 94900, 1000),
             'close': np.linspace(90050, 95050, 1000),
             'volume': np.random.normal(100, 10, 1000)
        }, index=dates)

    if df.empty: return

    # Indicators
    df['hma_55'] = calculate_hma(df['close'], period=55)
    adx_df = calculate_adx(df, period=14)
    df['adx'] = adx_df['adx']
    df['plus_di'] = adx_df['plus_di']
    df['minus_di'] = adx_df['minus_di']
    df['adx_rising'] = calculate_adx_slope(df['adx'])
    df['rsi'] = calculate_rsi(df['close'], period=14)

    # Logic
    markers = []
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms') if 'timestamp' in df.columns else pd.to_datetime(df.index)
        df.set_index('datetime', inplace=True)

    # We loop to find signals
    for i in range(200, len(df)):
        curr = df.iloc[i]
        
        # TV Logic
        tv_trend = curr['close'] > curr['hma_55']
        tv_dir = curr['plus_di'] > curr['minus_di']
        tv_str = curr['adx'] > 20
        tv_rise = bool(curr['adx_rising'])
        tv_mom = curr['rsi'] > 50
        
        if tv_trend and tv_dir and tv_str and tv_rise and tv_mom:
            # Timestamp to Unix Timestamp (seconds)
            ts = int(df.index[i].timestamp())
            markers.append({
                'time': ts,
                'position': 'belowBar',
                'color': '#2196F3',
                'shape': 'arrowUp',
                'text': 'TV Buy'
            })

    # Prepare specific lists for chart
    ohlc_data = []
    hma_data = []
    
    for i in range(len(df)):
        ts = int(df.index[i].timestamp())
        ohlc_data.append({
            'time': ts,
            'open': float(df.iloc[i]['open']),
            'high': float(df.iloc[i]['high']),
            'low': float(df.iloc[i]['low']),
            'close': float(df.iloc[i]['close']),
        })
        
        val = df.iloc[i]['hma_55']
        if not pd.isna(val):
            hma_data.append({
                'time': ts,
                'value': float(val)
            })

    # HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BTC TV Strategy Signals</title>
        <meta charset="utf-8" />
        <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: #1e1e1e; font-family: 'Segoe UI', sans-serif; color: #ddd; }}
            #chart {{ width: 100%; height: 100vh; }}
            #legend {{ 
                position: absolute; top: 12px; left: 12px; z-index: 2; 
                background: rgba(30, 30, 30, 0.8); padding: 10px 15px; 
                border-radius: 6px; border: 1px solid #444; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }}
            h2 {{ margin: 0 0 5px 0; font-size: 16px; color: #fff; }}
            p {{ margin: 3px 0; font-size: 12px; opacity: 0.8; }}
            .error {{ position: absolute; top: 50%; width: 100%; text-align: center; color: red; }}
        </style>
    </head>
    <body>
        <div id="legend">
            <h2>BTCUSDT Trend Velocity</h2>
            <p>🔵 Arrow: Buy Signal</p>
            <p>🟠 Line: HMA 55 Trend</p>
        </div>
        <div id="chart"></div>
        <div id="error-msg" class="error" style="display:none;">Error: Chart library failed to load. Check internet connection.</div>

        <script>
            if (typeof LightweightCharts === 'undefined') {{
                document.getElementById('error-msg').style.display = 'block';
                document.getElementById('legend').style.display = 'none';
            }} else {{
                const chartOptions = {{ 
                    layout: {{ textColor: '#d1d4dc', background: {{ type: 'solid', color: '#1e1e1e' }} }},
                    grid: {{ vertLines: {{ color: '#2B2B43' }}, horzLines: {{ color: '#2B2B43' }} }},
                    crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
                    timeScale: {{ borderColor: '#485c7b', timeVisible: true }}
                }};
                
                const chart = LightweightCharts.createChart(document.getElementById('chart'), chartOptions);
                
                const candlestickSeries = chart.addCandlestickSeries({{
                    upColor: '#26a69a', downColor: '#ef5350', 
                    borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350'
                }});
                
                const data = {json.dumps(ohlc_data)};
                candlestickSeries.setData(data);
                
                const markers = {json.dumps(markers)};
                candlestickSeries.setMarkers(markers);
                
                const hmaSeries = chart.addLineSeries({{ 
                    color: '#FF9800', 
                    lineWidth: 2,
                    priceLineVisible: false 
                }});
                hmaSeries.setData({json.dumps(hma_data)});
                
                chart.timeScale().fitContent();
                
                // Add resize listener
                window.addEventListener('resize', () => {{
                    chart.applyOptions({{ width: document.body.clientWidth, height: document.body.clientHeight }});
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    # Save to user root directly
    output_path = r"c:\Users\iphas\OneDrive\Documents\GitHub\Antigravity-Bot\btc_tv_signals.html"
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"✅ Chart generated at: {output_path}") 

if __name__ == "__main__":
    generate_chart()
