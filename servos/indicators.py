"""
Nexus Trading Bot - Technical Indicators Module
Implementation using pandas_ta (OpenBB fork).
"""
import pandas as pd
import pandas_ta as ta
import numpy as np


def calculate_rsi(prices, period: int = 14):
    """Calculate RSI."""
    if isinstance(prices, list):
        prices = pd.Series(prices)
    
    # ta.rsi returns a Series
    rsi = ta.rsi(prices, length=period)
    if rsi is None: return pd.Series([50.0] * len(prices))
    return rsi.fillna(50.0) # Handle NaN at start


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate EMA."""
    ema = ta.ema(series, length=period)
    if ema is None: return pd.Series(series) # Fallback
    return ema


def calculate_hma(series: pd.Series, period: int = 55) -> pd.Series:
    """Calculate HMA."""
    hma = ta.hma(series, length=period)
    if hma is None: return series
    return hma


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR."""
    atr = ta.atr(df['high'], df['low'], df['close'], length=period)
    if atr is None: return pd.Series(0, index=df.index)
    return atr


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> dict:
    """Calculate Bollinger Bands."""
    # ta.bbands returns BBL, BBM, BBU, BBB, BBP
    bb = ta.bbands(series, length=period, std=std_dev)
    if bb is None: 
        return {'middle': series, 'upper': series, 'lower': series}
    
    # Column naming convention in pandas_ta: BBL_length_std, ...
    # We can access by position or wildcard column name logic, 
    # but pandas_ta returns specific names.
    # Safe way: iloc based on standard output order [Lower, Mid, Upper, Bandwidth, Percent]
    # Actually order matches standard? Verify.
    # Usually: BBL, BBM, BBU, ...
    
    # Let's map dynamically
    return {
        'lower': bb.iloc[:, 0],
        'middle': bb.iloc[:, 1],
        'upper': bb.iloc[:, 2]
    }


def calculate_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 1.5) -> dict:
    """Calculate Keltner Channels."""
    # KC returns KCL, KCB, KCU
    kc = ta.kc(df['high'], df['low'], df['close'], length=period, scalar=multiplier)
    if kc is None:
        return {'middle': df['close'], 'upper': df['close'], 'lower': df['close']}
        
    return {
        'lower': kc.iloc[:, 0], # KCL
        'middle': kc.iloc[:, 1], # KCB (Basis/Middle)
        'upper': kc.iloc[:, 2]   # KCU
    }


def calculate_adx(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate ADX."""
    # ta.adx returns ADX, DMP, DMN
    adx_df = ta.adx(df['high'], df['low'], df['close'], length=period)
    if adx_df is None:
        z = pd.Series(0, index=df.index)
        return {'adx': z, 'plus_di': z, 'minus_di': z}
        
    return {
        'adx': adx_df.iloc[:, 0],      # ADX
        'plus_di': adx_df.iloc[:, 1],  # DMP
        'minus_di': adx_df.iloc[:, 2]  # DMN
    }


def calculate_adx_slope(adx_series: pd.Series, lookback: int = 5) -> pd.Series:
    """Calculate slope of ADX (Manual diff)."""
    return adx_series.diff(lookback)


def calculate_stoch_rsi(rsi_series: pd.Series, period: int = 14, k_period: int = 3, d_period: int = 3) -> dict:
    """Calculate Stochastic RSI."""
    # ta.stochrsi returns K, D
    stoch = ta.stochrsi(rsi_series, length=period, rsi_length=period, k=k_period, d=d_period)
    if stoch is None:
        z = pd.Series(0, index=rsi_series.index)
        return {'k': z, 'd': z}
        
    return {
        'k': stoch.iloc[:, 0],
        'd': stoch.iloc[:, 1]
    }


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price."""
    try:
        # ta.vwap requires a DatetimeIndex and it MUST be ordered
        if not df.index.is_monotonic_increasing:
             df.sort_index(inplace=True)
             
        vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
        if vwap is None or vwap.isna().all():
            raise ValueError("VWAP returned None or all NaN")
        return vwap
    except Exception:
        # Fallback: Manual VWAP calculation (cumulative)
        # VWAP = cumsum(typical_price * volume) / cumsum(volume)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        cum_vol = df['volume'].cumsum()
        cum_tp_vol = (typical_price * df['volume']).cumsum()
        vwap_manual = cum_tp_vol / cum_vol.replace(0, np.nan)
        return vwap_manual.fillna(df['close'])


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> dict:
    """Calculates Supertrend."""
    # ta.supertrend returns Trend, Direction, Long, Short
    st = ta.supertrend(df['high'], df['low'], df['close'], length=period, multiplier=multiplier)
    if st is None:
         z = pd.Series(0, index=df.index)
         return {'line': z, 'direction': z}
         
    # output: SUPERT_..., SUPERTd_..., SUPERTl_..., SUPERTs_...
    # column 0 is Trend Line
    # column 1 is Direction (1, -1)
    
    return {
        'line': st.iloc[:, 0],
        'direction': st.iloc[:, 1]
    }


# =============================================================================
# ADVANCED INDICATORS (New)
# =============================================================================

def calculate_ichimoku(df: pd.DataFrame, tenkan: int = 9, kijun: int = 26, senkou: int = 52) -> dict:
    """
    Ichimoku Cloud.
    Returns: tenkan, kijun, senkou_a, senkou_b, chikou
    """
    ich = ta.ichimoku(df['high'], df['low'], df['close'], tenkan=tenkan, kijun=kijun, senkou=senkou)
    if ich is None or len(ich) < 2:
        z = pd.Series(0, index=df.index)
        return {'tenkan': z, 'kijun': z, 'senkou_a': z, 'senkou_b': z, 'chikou': z}
    
    # ich returns tuple: (ichimoku_df, span_df)
    # ichimoku_df has: ISA (Senkou A), ISB (Senkou B), ITS (Tenkan), IKS (Kijun), ICS (Chikou)
    ich_df = ich[0]
    
    return {
        'tenkan': ich_df.iloc[:, 2] if ich_df.shape[1] > 2 else pd.Series(0, index=df.index),
        'kijun': ich_df.iloc[:, 3] if ich_df.shape[1] > 3 else pd.Series(0, index=df.index),
        'senkou_a': ich_df.iloc[:, 0] if ich_df.shape[1] > 0 else pd.Series(0, index=df.index),
        'senkou_b': ich_df.iloc[:, 1] if ich_df.shape[1] > 1 else pd.Series(0, index=df.index),
        'chikou': ich_df.iloc[:, 4] if ich_df.shape[1] > 4 else pd.Series(0, index=df.index)
    }


def calculate_squeeze_pro(df: pd.DataFrame, bb_length: int = 20, kc_length: int = 20, 
                          mom_length: int = 12, use_tr: bool = True) -> dict:
    """
    Squeeze Pro (Advanced Squeeze with Momentum).
    Returns: squeeze_on, squeeze_off, no_squeeze, momentum
    """
    sqz = ta.squeeze_pro(df['high'], df['low'], df['close'], 
                         bb_length=bb_length, kc_length=kc_length, 
                         mom_length=mom_length, use_tr=use_tr)
    if sqz is None:
        z = pd.Series(0, index=df.index)
        return {'squeeze_on': z, 'squeeze_off': z, 'no_squeeze': z, 'momentum': z}
    
    # Returns: SQZ_ON, SQZ_OFF, SQZ_NO, SQZ
    return {
        'squeeze_on': sqz.iloc[:, 0],
        'squeeze_off': sqz.iloc[:, 1],
        'no_squeeze': sqz.iloc[:, 2],
        'momentum': sqz.iloc[:, 3] if sqz.shape[1] > 3 else pd.Series(0, index=df.index)
    }


def calculate_psar(df: pd.DataFrame, af0: float = 0.02, af: float = 0.02, max_af: float = 0.2) -> dict:
    """
    Parabolic SAR.
    Returns: long (bullish stops), short (bearish stops), af, reversal
    """
    psar = ta.psar(df['high'], df['low'], df['close'], af0=af0, af=af, max_af=max_af)
    if psar is None:
        z = pd.Series(0, index=df.index)
        return {'long': z, 'short': z, 'af': z, 'reversal': z}
    
    # Returns: PSARl, PSARs, PSARaf, PSARr
    return {
        'long': psar.iloc[:, 0],   # Bullish stop line
        'short': psar.iloc[:, 1],  # Bearish stop line
        'af': psar.iloc[:, 2],     # Acceleration Factor
        'reversal': psar.iloc[:, 3] if psar.shape[1] > 3 else pd.Series(0, index=df.index)
    }


def calculate_choppiness(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    Choppiness Index.
    High values (>61.8) = Choppy/Ranging market.
    Low values (<38.2) = Trending market.
    """
    chop = ta.chop(df['high'], df['low'], df['close'], length=length)
    if chop is None:
        return pd.Series(50, index=df.index)  # Neutral
    return chop


def calculate_volume_profile(df: pd.DataFrame, width: int = 10) -> dict:
    """
    Volume Profile (Price by Volume).
    Note: This returns aggregated data, not a time-series.
    Returns: price_levels, volumes, poc (Point of Control)
    """
    # ta.vp returns a DataFrame with price levels and volumes
    try:
        vp = ta.vp(df['close'], df['volume'], width=width)
        if vp is None or vp.empty:
            return {'price_levels': [], 'volumes': [], 'poc': 0}
        
        # Find Point of Control (price level with max volume)
        poc_idx = vp['Volume'].idxmax() if 'Volume' in vp.columns else 0
        poc = vp.loc[poc_idx, 'Price'] if 'Price' in vp.columns else 0
        
        return {
            'price_levels': vp['Price'].tolist() if 'Price' in vp.columns else [],
            'volumes': vp['Volume'].tolist() if 'Volume' in vp.columns else [],
            'poc': poc
        }
    except Exception:
        return {'price_levels': [], 'volumes': [], 'poc': 0}

