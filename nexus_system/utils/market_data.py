"""
Nexus Trading Bot - Utilidad Async para Obtener Datos de Mercado

Este módulo reemplaza servos/fetcher.py (síncrono) con una versión completamente async
que usa MarketStream. Proporciona funciones helper compatibles con el código existente
pero sin bloquear el event loop.

Funciones:
- get_market_data_async(): Obtiene datos OHLCV de forma async
- calculate_atr_async(): Calcula ATR de forma async

Nota: Este módulo usa MarketStream que soporta WebSocket + REST fallback para
obtener datos de mercado de forma eficiente.
"""
import pandas as pd
from typing import Optional
from ..uplink.stream import MarketStream


async def get_market_data_async(
    symbol: str, 
    timeframe: str = '1h', 
    limit: int = 100,
    market_stream: Optional[MarketStream] = None
) -> pd.DataFrame:
    """
    Obtiene datos OHLCV de forma asíncrona usando MarketStream.
    Compatible con la interfaz de servos/fetcher.py pero completamente async.
    
    Args:
        symbol: Par de trading (ej: 'BTCUSDT', 'TSLA')
        timeframe: Intervalo de velas ('1m', '5m', '15m', '1h', '4h', '1d')
        limit: Número de velas a obtener
        market_stream: Instancia opcional de MarketStream (crea una nueva si no se proporciona)
    
    Returns:
        DataFrame con columnas: timestamp, open, high, low, close, volume
    """
    # Usar instancia proporcionada o crear una temporal
    stream = market_stream
    should_close = False
    
    if stream is None:
        # Crear instancia temporal si no se proporciona
        # Sin WebSocket para requests únicos (más eficiente para llamadas puntuales)
        stream = MarketStream(use_websocket=False)
        should_close = True
        try:
            await stream.initialize()
        except Exception as e:
            print(f"[market_data] Error inicializando MarketStream: {e}")
            return pd.DataFrame()
    
    try:
        # Obtener velas usando MarketStream
        result = await stream.get_candles(symbol, limit=limit, timeframe=timeframe)
        
        # MarketStream devuelve dict con 'dataframe', extraer DataFrame
        df = result.get('dataframe', pd.DataFrame())
        
        if df.empty:
            return pd.DataFrame()
        
        # Asegurar que tenemos las columnas necesarias
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0
        
        # Limitar a las columnas necesarias y al límite solicitado
        df = df[required_cols].tail(limit)
        
        return df
        
    except Exception as e:
        print(f"[market_data] Error obteniendo datos para {symbol}: {e}")
        return pd.DataFrame()
    finally:
        # Cerrar instancia temporal si la creamos
        if should_close and stream:
            try:
                await stream.close()
            except:
                pass


async def calculate_atr_async(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calcula el valor actual de ATR desde un DataFrame OHLCV.
    Versión async que usa servos/indicators.
    
    Args:
        df: DataFrame con columnas high, low, close
        period: Período de ATR (default 14)
    
    Returns:
        Valor actual de ATR como float
    """
    if df.empty or len(df) < period + 1:
        return 0.0
    
    try:
        from servos.indicators import calculate_atr as atr_series
        atr = atr_series(df, period)
        return float(atr.iloc[-1]) if not atr.empty else 0.0
    except Exception as e:
        print(f"[market_data] Error calculando ATR: {e}")
        return 0.0

