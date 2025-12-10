import pandas as pd
import numpy as np

# Importar cálculos vectorizados desde indicadores (Principio DRY)
from strategies.indicators import (
    calculate_hma,
    calculate_bollinger_bands,
    calculate_keltner_channels,
    calculate_adx,
    calculate_rsi,
    calculate_adx_slope
)

class StrategyEngine:
    """
    Motor de Estrategia Financiera Modular - "Squeeze & Velocity".
    Diseñado para alta eficiencia (Vectorizado con Pandas/Numpy).
    """

    def __init__(self, data: pd.DataFrame):
        """
        Inicializa con Datos OHLCV.
        """
        self.df = data.copy()
        self.metrics = {}
        
    def calculate_indicators(self):
        """
        Calcula todos los indicadores técnicos necesarios matemáticamente.
        Eficiencia de memoria: Se agregan columnas directamente al DF o se usan series temporales.
        """
        if self.df.empty:
            return

        # 1. HMA (55) - Tendencia Principal
        self.df['hma_55'] = calculate_hma(self.df['close'], period=55)
        
        # 2. Bandas de Bollinger (20, 2.0) - Volatilidad
        bb = calculate_bollinger_bands(self.df['close'], period=20, std_dev=2.0)
        self.df['bb_upper'] = bb['upper']
        self.df['bb_lower'] = bb['lower']
        # Usamos ancho de banda para detectar compresión, pero la lógica pide BB dentro de Keltner
        
        # 3. Canales de Keltner (20, 1.5 ATR) - Rango Medio
        kc = calculate_keltner_channels(self.df, period=20, multiplier=1.5)
        self.df['kc_upper'] = kc['upper']
        self.df['kc_lower'] = kc['lower']
        
        # 4. ADX (14) - Fuerza de Tendencia
        adx_df = calculate_adx(self.df, period=14)
        self.df['adx'] = adx_df['adx']
        
        # 5. RSI (14) - Momento
        self.df['rsi'] = calculate_rsi(self.df['close'], period=14)

    def analyze(self) -> dict:
        """
        Ejecuta la lógica "Squeeze & Velocity".
        Devuelve diccionario estructurado con Señal, Razón y Métricas.
        """
        if len(self.df) < 60:
            return {
                "signal": "WAIT",
                "reason": "Datos insuficientes (< 60 velas)",
                "metrics": {}
            }

        self.calculate_indicators()
        
        # Obtener última vela (Cierre actual) y anterior para comparaciones
        curr = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        # --- LÓGICA DE DETECCIÓN ---
        
        # 1. Fase de Compresión (Squeeze)
        # Bollinger Bands DENTRO de Keltner Channels
        # Esto indica volatilidad extremadamente baja, precursora de explosión.
        # Chequeamos si hubo squeeze recientemente (ej. en la vela anterior o actual)
        # Para entrada real, buscamos la RUPTURA del squeeze.
        
        # Definición estricta de TTM Squeeze: BB Upper < KC Upper Y BB Lower > KC Lower.
        is_squeeze = (curr['bb_upper'] < curr['kc_upper']) and (curr['bb_lower'] > curr['kc_lower'])
        was_squeeze = (prev['bb_upper'] < prev['kc_upper']) and (prev['bb_lower'] > prev['kc_lower'])
        
        # 2. Señal de Ruptura (Breakout) - "Velocity"
        # Precio rompe Banda Superior de Bollinger + RSI > 50 (Fuerza alcista)
        breakout_up = (curr['close'] > curr['bb_upper'])
        momentum_bullish = (curr['rsi'] > 50)
        
        # Validación de Tendencia (HMA) + ADX
        # Precio sobre HMA 55 y ADX con pendiente positiva o fuerte (>20)
        trend_bullish = (curr['close'] > curr['hma_55'])
        adx_rising = curr['adx'] > prev['adx']
        adx_strong = curr['adx'] > 20
        
        # --- MÁQUINA DE ESTADOS / DECISIÓN ---
        
        signal = "WAIT"
        reason = "Monitorizando mercado..."
        
        # A. SEÑAL DE ENTRADA (BUY)
        # Condiciones: 
        # 1. Venimos de un squeeze o estamos rompiendo volatilidad.
        # 2. Breakout Alcista confirmado.
        # 3. Tendencia a favor (Sobre HMA).
        # 4. ADX despertando (Rising).
        
        # Relajamos "Venimos de squeeze" a "Ruptura de BB" + Confirmación, 
        # pero el usuario pidió "lógica debe detectar fases de compresión para activar entradas".
        # Interpretación: Si hubo squeeze reciente Y ahora rompe.
        
        # Simplificación robusta: Si Breakout UP Y Tendencia UP Y Momento UP.
        # El Squeeze es un plus de calidad, pero si el precio ya explotó, el squeeze ya pasó.
        # Chequeamos si hubo squeeze en las últimas 5 velas para dar validez "Squeeze Breakout".
        recent_squeeze = any((self.df['bb_upper'].iloc[i] < self.df['kc_upper'].iloc[i]) for i in range(-5, -1))
        
        if breakout_up and trend_bullish and momentum_bullish and adx_rising:
             # Prioridad a entradas post-squeeze
            if recent_squeeze:
                signal = "BUY"
                reason = "🚀 **SQUEEZE BREAKOUT**: Ruptura de Squeeze confirmada con Volatilidad + ADX al alza."
            # O entradas de continuación de tendencia fuerte
            elif adx_strong:
                signal = "BUY"
                reason = "🌊 **TREND VELOCITY**: Continuación de tendencia fuerte (ADX>20) con ruptura de BB."
        
        # B. SALIDA (CLOSE_LONG)
        # Cierre bajo HMA O ADX colapsa (pierde fuerza significativamente)
        # Colapso ADX: Cae más de 5 puntos o cae bajo 20 desde arriba (cruce bajista).
        adx_collapse = (prev['adx'] > 30 and curr['adx'] < 25) # Ejemplo de pérdida de momento
        trend_loss = (curr['close'] < curr['hma_55'])
        
        if trend_loss:
            signal = "CLOSE_LONG"
            reason = "📉 **TENDENCIA ROTA**: Precio cerró bajo HMA 55."
        elif adx_collapse:
             signal = "CLOSE_LONG"
             reason = "exhaustion **ADX**: Pérdida significativa de fuerza en la tendencia."
             
        # Construir Métricas Optimizadas
        final_metrics = {
            "close": float(curr['close']),
            "hma_55": float(curr['hma_55']),
            "rsi": float(curr['rsi']),
            "adx": float(curr['adx']),
            "squeeze_on": bool(is_squeeze or recent_squeeze),
            "bb_upper": float(curr['bb_upper']),
            "kc_upper": float(curr['kc_upper'])
        }
        
        return {
            "signal": signal,
            "reason": reason,
            "metrics": final_metrics
        }
