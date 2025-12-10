import pandas as pd
import numpy as np

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcula el Índice de Fuerza Relativa (RSI).
    Usa el suavizado de Wilder (alpha = 1/periodo) vía ewm(com=periodo-1).
    """
    delta = series.diff()
    
    # Separar ganancias y pérdidas
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0) # Almacenar como valores positivos

    # Suavizado de Wilder
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    # Calcular RS
    rs = avg_gain / avg_loss
    
    # Calcular RSI: 100 - (100 / (1 + RS))
    rsi = 100 - (100 / (1 + rs))
    
    # Manejar división por cero (avg_loss == 0 significa que RSI es 100)
    rsi = rsi.replace([np.inf], 100)
    
    # Manejar NaN al inicio
    rsi = rsi.fillna(0)
    
    return rsi

def calculate_stoch_rsi(rsi_series: pd.Series, period: int = 14, k_period: int = 3, d_period: int = 3) -> pd.DataFrame:
    """
    Calcula el RSI Estocástico.
    Entrada: Serie RSI (no precio).
    Fórmula: (rsi - min_rsi) / (max_rsi - min_rsi)
    Devuelve valores en rango 0-100 (multiplicado por 100).
    Devuelve DataFrame con 'k' (StochRSI suavizado) y 'd' (SMA de k).
    """
    # Calcular Min/Max RSI en ventana
    min_rsi = rsi_series.rolling(window=period).min()
    max_rsi = rsi_series.rolling(window=period).max()
    
    # Calcular Stoch RSI (Fast %K)
    # Evitar división por cero
    denominator = max_rsi - min_rsi
    stoch_rsi = (rsi_series - min_rsi) / denominator
    
    # Manejar NaNs del cálculo (0/0 etc)
    stoch_rsi = stoch_rsi.fillna(0)
    
    # Escalar a 0-100 según osciladores comunes para consistencia
    stoch_rsi_100 = stoch_rsi * 100
    
    # Suavizar %K
    k_line = stoch_rsi_100.rolling(window=k_period).mean()
    
    # Calcular %D (SMA de %K)
    d_line = k_line.rolling(window=d_period).mean()
    
    # Manejar NaNs
    k_line = k_line.fillna(0)
    d_line = d_line.fillna(0)
    
    return pd.DataFrame({'k': k_line, 'd': d_line})

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    Calcula MACD, Línea de Señal e Histograma.
    """
    # EMA Rápida
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    
    # EMA Lenta
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    
    # Línea MACD
    macd_line = ema_fast - ema_slow
    
    # Línea de Señal
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # Histograma
    histogram = macd_line - signal_line
    
    # Manejar NaNs
    macd_line = macd_line.fillna(0)
    signal_line = signal_line.fillna(0)
    histogram = histogram.fillna(0)
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    })

def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """
    Calcula Bandas de Bollinger (Superior, Media, Inferior).
    """
    # Banda Media: SMA
    middle = series.rolling(window=period).mean()
    
    # Desviación Estándar
    std = series.rolling(window=period).std()
    
    # Bandas Superior/Inferior
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    # Manejar NaNs (ej. ventana inicial)
    middle = middle.bfill().fillna(0)
    upper = upper.bfill().fillna(0)
    lower = lower.bfill().fillna(0)
    
    return pd.DataFrame({
        'upper': upper,
        'middle': middle,
        'lower': lower
    })

def calculate_ema(series: pd.Series, period: int = 200) -> pd.Series:
    """
    Calcula Media Móvil Exponencial (EMA).
    """
    return series.ewm(span=period, adjust=False).mean()

def calculate_wma(series: pd.Series, period: int) -> pd.Series:
    """
    Calcula Media Móvil Ponderada (WMA).
    weights: [1, 2, ..., period]
    """
    return series.rolling(period).apply(lambda x: ((x * np.arange(1, period + 1)).sum()) / (np.arange(1, period + 1).sum()), raw=True)

def calculate_hma(series: pd.Series, period: int = 55) -> pd.Series:
    """
    Calcula Media Móvil de Hull (HMA).
    Fórmula: WMA(2 * WMA(n/2) - WMA(n), sqrt(n))
    """
    half_period = int(period / 2)
    sqrt_period = int(np.sqrt(period))
    
    wma_half = calculate_wma(series, half_period)
    wma_full = calculate_wma(series, period)
    
    raw_hma = (2 * wma_half) - wma_full
    hma = calculate_wma(raw_hma, sqrt_period)
    return hma

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calcula ADX, DI+, DI-.
    Devuelve DataFrame con columnas: ['adx', 'plus_di', 'minus_di']
    """
    # 1. Rango Verdadero (True Range)
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # 2. Movimiento Direccional
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    # 3. TR y DM Suavizados (Suavizado de Wilder)
    # Nota: ewm(alpha=1/periodo) es equivalente a Wilder
    alpha = 1 / period
    
    tr_smooth = tr.ewm(alpha=alpha, adjust=False).mean()
    plus_dm_smooth = pd.Series(plus_dm, index=df.index).ewm(alpha=alpha, adjust=False).mean()
    minus_dm_smooth = pd.Series(minus_dm, index=df.index).ewm(alpha=alpha, adjust=False).mean()
    
    # 4. DI+ y DI-
    plus_di = 100 * (plus_dm_smooth / tr_smooth)
    minus_di = 100 * (minus_dm_smooth / tr_smooth)
    
    # 5. DX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    
    # 6. ADX (DX Suavizado)
    # ADX estándar usa el mismo suavizado en DX
    adx = dx.ewm(alpha=alpha, adjust=False).mean()
    
    return pd.DataFrame({
        'adx': adx,
        'plus_di': plus_di,
        'minus_di': minus_di
    }).fillna(0)

def calculate_adx_slope(adx_series: pd.Series) -> pd.Series:
    """
    Devuelve serie booleana: True si ADX está subiendo (actual > anterior).
    """
    return adx_series > adx_series.shift(1)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calcula el Rango Verdadero Promedio (ATR).
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # 1. True Range (TR)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # 2. ATR (Suavizado similar a Wilder)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    
    return atr

def calculate_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 1.5) -> pd.DataFrame:
    """
    Calcula Canales de Keltner.
    Línea Central: EMA(20)
    Banda Superior: EMA + (ATR * multiplicador)
    Banda Inferior: EMA - (ATR * multiplicador)
    """
    # Usar EMA para línea central
    central = calculate_ema(df['close'], period)
    
    # Calcular ATR
    atr = calculate_atr(df, period=10) # El periodo de ATR en Keltner suele ser 10, o igual al EMA (20). Usaremos 20 por consistencia si no se especifica.
    # Ajuste: El usuario pidió Keltner (20, 1.5 ATR). Asumiremos ATR(20) si no se especifica otro, pero el estándar suele ser ATR(10). 
    # Siguiendo la petición estricta "Canales de Keltner (20, 1.5 ATR)", usaremos ATR(20) para el rango o ATR(10)? 
    # Usaremos el mismo periodo que el canal (20) para simplificar a menos que se requiera otro.
    # Corrección: El ATR estándar para Keltner suele ser 10, pero usaremos 'period' para todo para ser "Keltner (20, 1.5)".
    
    atr = calculate_atr(df, period=period)
    
    upper = central + (atr * multiplier)
    lower = central - (atr * multiplier)
    
    return pd.DataFrame({
        'upper': upper,
        'central': central,
        'lower': lower
    })
