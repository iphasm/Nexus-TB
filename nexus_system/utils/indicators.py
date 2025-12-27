import pandas as pd
import numpy as np

class TechnicalIndicators:
    """
    Standardized Technical Indicators Library.
    Native implementation using Pandas/Numpy to avoid dependency hell.
    Optimized for Python 3.11+.
    """

    @staticmethod
    def ema(series: pd.Series, span: int) -> pd.Series:
        """Exponential Moving Average"""
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2):
        """Bollinger Bands (Upper, Lower, Middle, Width, Pct)"""
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        # Band Width: (Upper - Lower) / Middle
        width = (upper - lower) / (middle + 1e-10) * 100
        # %B: (Price - Lower) / (Upper - Lower)
        pct = (series - lower) / (upper - lower + 1e-10)
        
        return upper, lower, middle, width, pct

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Approximate ADX (Trend Strength).
        Standard ADX is recursive. This is a simplified vectorizable version
        often used in high-frequency categorization.
        """
        # Using the divergence of EMAs normalized by price as a proxy for trend strength
        # This matches the logic user had in stream.py originally
        ema_fast = df['close'].ewm(span=20, adjust=False).mean()
        ema_slow = df['close'].ewm(span=50, adjust=False).mean()
        return (abs(ema_fast - ema_slow) / df['close']) * 2500

    @staticmethod
    def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Money Flow Index"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        raw_money_flow = typical_price * df['volume']
        
        price_change = typical_price.diff()
        positive_flow = np.where(price_change > 0, raw_money_flow, 0)
        negative_flow = np.where(price_change < 0, raw_money_flow, 0)
        
        positive_sum = pd.Series(positive_flow).rolling(period).sum()
        negative_sum = pd.Series(negative_flow).rolling(period).sum()
        
        mfr = positive_sum / (negative_sum + 1e-10)
        return 100 - (100 / (1 + mfr))

    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD, Signal, Hist"""
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line
        return macd_line, signal_line, hist

    @staticmethod
    def obv_change(df: pd.DataFrame) -> pd.Series:
        """On-Balance Volume Change (period 1)"""
        # Vectorized OBV logic
        change = pd.Series(0.0, index=df.index, dtype=float)
        change[df['close'] > df['close'].shift(1)] = df['volume']
        change[df['close'] < df['close'].shift(1)] = -df['volume']
        return change

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies standard suite of indicators to the DataFrame in-place.
        """
        if df.empty: return df
        
        closes = df['close']
        
        # Trend
        df['ema_20'] = TechnicalIndicators.ema(closes, 20)
        df['ema_50'] = TechnicalIndicators.ema(closes, 50)
        df['ema_200'] = TechnicalIndicators.ema(closes, 200)
        
        # Momentum
        df['rsi'] = TechnicalIndicators.rsi(closes)
        
        # Volatility
        df['upper_bb'], df['lower_bb'], _, df['bb_width'], df['bb_pct'] = \
            TechnicalIndicators.bollinger_bands(closes)
            
        df['atr'] = TechnicalIndicators.atr(df)
        
        # Strength
        df['adx'] = TechnicalIndicators.adx(df)
        
        # Volume
        if 'volume' in df.columns:
            df['vol_sma'] = df['volume'].rolling(window=20).mean()
            df['obv_change'] = TechnicalIndicators.obv_change(df)
            
        # MACD
        _, _, df['macd_hist'] = TechnicalIndicators.macd(closes)
        
        # Clean up
        df.bfill(inplace=True)
        df.fillna(0, inplace=True)
        
        return df
