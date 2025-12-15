import pandas as pd

def calculate_rsi(prices: list, period: int = 14) -> float:
    """
    Calculate the latest RSI value from a list of closing prices.
    Returns: RSI (0-100) or 50.0 if insufficient data.
    """
    if len(prices) < period + 1:
        return 50.0
        
    series = pd.Series(prices)
    delta = series.diff()
    
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    # Use standard smoothing (Wilder's) ideally, but simple rolling is close enough for a quick report
    # For closer accuracy to TradingView, we can use ewm:
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(float(rsi.iloc[-1]), 1)
