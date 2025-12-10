import pandas as pd
from strategies.indicators import (
    calculate_rsi,
    calculate_stoch_rsi,
    calculate_bollinger_bands,
    calculate_ema
)

def analyze_mean_reversion(df: pd.DataFrame) -> tuple[bool, dict]:
    """
    Estrategia SPOT: Reversión a la Media.
    
    Señal de Compra (SPOT ACCUMULATION):
    1. Precio < Banda Inferior de Bollinger (Oversold extreme).
    2. RSI < 30 (Oversold).
    3. Stoch RSI cruce alcista en zona baja.
    4. Confirmación de volumen.
    """
    # 0. Validación de Datos
    if df.empty or len(df) < 200:
        return False, {"error": "Datos insuficientes"}

    try:
        # A. Cálculos de Indicadores
        # EMA 200 (Tendencia General)
        df['ema_200'] = calculate_ema(df['close'], period=200)
        
        # Bandas de Bollinger (20, 2)
        bb = calculate_bollinger_bands(df['close'], period=20, std_dev=2)
        df['bb_lower'] = bb['lower']
        
        # RSI 14
        df['rsi'] = calculate_rsi(df['close'], period=14)
        
        # StochRSI
        stoch = calculate_stoch_rsi(df['rsi'], period=14, k_period=3, d_period=3)
        df['stoch_k'] = stoch['k']
        df['stoch_d'] = stoch['d']
        
        # Volumen SMA
        vol_sma = df['volume'].rolling(20).mean()
        
        # B. Evaluación Lógica (Última vela)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Condiciones
        # 1. Configuración: Precio debajo de la banda inferior (Sobreventa estadística)
        cond_bb = curr['close'] < curr['bb_lower']
        
        # 2. RSI bajo
        cond_rsi = curr['rsi'] < 40 # Relajado un poco de 30 para más frecuencia en Spot
        
        # 3. Disparador: Cruce StochRSI
        cond_stoch = (prev['stoch_k'] < prev['stoch_d']) and (curr['stoch_k'] > curr['stoch_d']) and (curr['stoch_k'] < 20)
        
        # 4. Volumen (Opcional, pero bueno para confirmar soporte)
        vol_threshold = vol_sma.iloc[-1] * 1.2 if pd.notna(vol_sma.iloc[-1]) else 0
        cond_vol = curr['volume'] > vol_threshold
        
        # Señal Final
        signal = cond_bb and cond_rsi and cond_stoch
        
        reason = ""
        if signal:
            reason = "💎 **MEAN REVERSION (SPOT)**: Precio bajo BB + Cruce StochRSI."
            
        metrics = {
            'close': float(curr['close']),
            'rsi': float(curr['rsi']),
            'stoch_k': float(curr['stoch_k']),
            'bb_lower': float(curr['bb_lower']),
            'source': 'MeanReversion' if signal else 'None',
            'reason': reason
        }
        
        return signal, metrics

    except Exception as e:
        print(f"❌ Error Mean Reversion: {e}")
        return False, {"error": str(e)}
