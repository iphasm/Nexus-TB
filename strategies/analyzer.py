import pandas as pd
from strategies.indicators import (
    calculate_rsi,
    calculate_stoch_rsi,
    calculate_macd,
    calculate_bollinger_bands
)

def analyze_market(df: pd.DataFrame) -> tuple[bool, dict]:
    """
    Analyzes the market data to generate a buy signal based on specific conditions.
    
    Args:
        df: DataFrame with 'close' column (and others required by indicators).
        
    Returns:
        tuple: (buy_signal (bool), metrics_dict (dict))
    """
    # Ensure we have data
    if df.empty:
        return False, {}

    # Calculate Indicators and store in DataFrame
    # 1. RSI
    df['rsi'] = calculate_rsi(df['close'])
    
    # 2. Stoch RSI
    # Passing RSI series as expected by the updated indicator signature
    stoch_result = calculate_stoch_rsi(df['rsi'])
    df['stoch_rsi'] = stoch_result['k'] # Taking %K as the main StochRSI value
    # df['stoch_d'] = stoch_result['d'] # Not strictly asked for in the return dict, but calculated
    
    # 3. MACD
    macd_result = calculate_macd(df['close'])
    df['macd'] = macd_result['macd']
    df['macd_signal'] = macd_result['signal']
    # df['macd_hist'] = macd_result['histogram']
    
    # 4. Bollinger Bands
    bb_result = calculate_bollinger_bands(df['close'])
    df['bb_upper'] = bb_result['upper']
    df['bb_lower'] = bb_result['lower']
    # df['bb_middle'] = bb_result['middle']
    
    # Evaluate the last candle (most recent)
    last_row = df.iloc[-1]
    
    # Extract metrics
    current_rsi = last_row['rsi']
    current_stoch = last_row['stoch_rsi']
    current_close = last_row['close']
    current_bb_lower = last_row['bb_lower']
    
    # Logic Signal: ALL conditions must be True
    # 1. RSI < 30
    cond_rsi = current_rsi < 30
    
    # 2. Stoch RSI < 20 (Assuming 0-100 scale from indicators.py)
    cond_stoch = current_stoch < 20
    
    # 3. Close < BB Lower
    cond_bb = current_close < current_bb_lower
    
    buy_signal = cond_rsi and cond_stoch and cond_bb
    
    metrics_dict = {
        'close': current_close,
        'rsi': current_rsi,
        'stoch_rsi': current_stoch,
        'bb_lower': current_bb_lower
    }
    
    return buy_signal, metrics_dict
