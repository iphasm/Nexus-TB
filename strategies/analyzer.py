import pandas as pd
from strategies.indicators import (
    calculate_rsi,
    calculate_stoch_rsi,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_hma,
    calculate_adx,
    calculate_adx_slope
)

def check_trend_velocity(df: pd.DataFrame) -> tuple[bool, dict]:
    """
    Estrategia de Velocidad de Tendencia BTC (Trend Velocity).
    
    Señal de Compra (Long):
    1. Cierre > HMA(55)
    2. DI+ > DI-
    3. ADX > 20
    4. ADX Creciente
    5. RSI > 50
    """
    try:
        # Calcular Indicadores
        df['hma_55'] = calculate_hma(df['close'], period=55)
        
        adx_df = calculate_adx(df, period=14)
        df['adx'] = adx_df['adx']
        df['plus_di'] = adx_df['plus_di']
        df['minus_di'] = adx_df['minus_di']
        
        df['adx_rising'] = calculate_adx_slope(df['adx'])
        
        # RSI ya se calcula en el analizador principal si se llama desde allí, pero lo calculamos aquí por seguridad
        if 'rsi' not in df.columns:
            df['rsi'] = calculate_rsi(df['close'], period=14)
            
        curr = df.iloc[-1]
        
        # Condiciones
        # 1. Filtro de Tendencia
        c_trend = curr['close'] > curr['hma_55']
        
        # 2. Dirección
        c_direction = curr['plus_di'] > curr['minus_di']
        
        # 3. Fuerza
        c_strength = curr['adx'] > 20
        c_rising = bool(curr['adx_rising'])
        
        # 4. Momento
        c_momentum = curr['rsi'] > 50
        
        # Señal Final
        long_signal = c_trend and c_direction and c_strength and c_rising and c_momentum
        
        debug_info = {
            'tv_trend_hma': bool(c_trend),
            'tv_dir_plus': bool(c_direction),
            'tv_str_adx': bool(c_strength),
            'tv_adx_rise': bool(c_rising),
            'tv_mom_rsi': bool(c_momentum)
        }
        
        return long_signal, debug_info
        
    except Exception as e:
        print(f"Error en Trend Velocity: {e}")
        return False, {"error": str(e)}

def analyze_market(df: pd.DataFrame, enabled_strategies: dict = None) -> tuple[bool, dict]:
    """
    Estrategia Combinada:
    1. Reversión a la Media (Existente)
    O
    2. Velocidad de Tendencia BTC (Nueva)
    
    enabled_strategies: dict con claves 'mean_reversion' y 'trend_velocity'
    """
    # Valores Predeterminados
    if enabled_strategies is None:
        enabled_strategies = {'mean_reversion': True, 'trend_velocity': True}

    # 0. Validación de Datos
    if df.empty or len(df) < 200:
        return False, {"error": "Datos insuficientes (necesita >200 velas)"}

    try:
        # Indicadores requeridos para Reversión a la Media (Conjunto base)
        # Calculamos indicadores comunes primero para evitar redundancia si es posible,
        # pero por ahora los mantendremos agrupados a menos que el rendimiento se vea afectado.
        
        signal_mean_rev = False
        signal_trend_vel = False
        tv_debug = {}
        
        # --- ESTRATEGIA 1: Reversión a la Media ---
        if enabled_strategies.get('mean_reversion', True):
            # A. EMA 200
            df['ema_200'] = calculate_ema(df['close'], period=200)
            
            # B. Bandas de Bollinger (20, 2)
            bb = calculate_bollinger_bands(df['close'], period=20, std_dev=2)
            df['bb_lower'] = bb['lower']
            
            # C. SMA de Volumen 20
            df['vol_sma_20'] = df['volume'].rolling(window=20).mean()
            
            # D. RSI 14
            df['rsi'] = calculate_rsi(df['close'], period=14)
            
            # E. StochRSI (14, 3, 3)
            stoch = calculate_stoch_rsi(df['rsi'], period=14, k_period=3, d_period=3)
            df['stoch_k'] = stoch['k']
            df['stoch_d'] = stoch['d']
            
            # Evaluar Reversión a la Media
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            cond_setup = curr['close'] < curr['bb_lower']
            cond_trend = curr['close'] > curr['ema_200'] # Lógica de reversión prefiere retroceso en tendencia alcista
            vol_avg = curr['vol_sma_20'] if pd.notna(curr['vol_sma_20']) else 0
            cond_volume = curr['volume'] > (vol_avg * 1.5)
            cross_up = (prev['stoch_k'] < prev['stoch_d']) and (curr['stoch_k'] > curr['stoch_d'])
            in_zone = curr['stoch_k'] < 20
            cond_trigger = cross_up and in_zone
            
            signal_mean_rev = cond_setup and cond_trend and cond_volume and cond_trigger
        
        # --- ESTRATEGIA 2: Velocidad de Tendencia (Trend Velocity) ---
        if enabled_strategies.get('trend_velocity', True):
             # RSI también se necesita para TV, verificar si ya se calculó
            if 'rsi' not in df.columns:
                df['rsi'] = calculate_rsi(df['close'], period=14)
                
            sig, tv_debug = check_trend_velocity(df)
            signal_trend_vel = sig
        
        # --- SEÑAL COMBINADA (Lógica OR) ---
        final_buy_signal = signal_mean_rev or signal_trend_vel
        
        # Construcción de Métricas (Manejar columnas faltantes si la estrategia está desactivada)
        curr = df.iloc[-1]
        
        # Obtención Segura (Safe getters)
        vol_avg = df.iloc[-1].get('vol_sma_20', 1) 
        if pd.isna(vol_avg) or vol_avg == 0: vol_avg = 1 # evitar div/0
        
        metrics_dict = {
            'close': float(curr['close']),
            'rsi': float(curr.get('rsi', 0)),
            'stoch_k': float(curr.get('stoch_k', 0)),
            'stoch_d': float(curr.get('stoch_d', 0)),
            'bb_lower': float(curr.get('bb_lower', 0)),
            'ema_200': float(curr.get('ema_200', 0)),
            'hma_55': float(curr.get('hma_55', 0)),
            'adx': float(curr.get('adx', 0)),
            'vol_ratio': round(curr.get('volume', 0) / vol_avg, 2),
            'source': 'TrendVelocity' if signal_trend_vel else ('MeanReversion' if signal_mean_rev else 'Ninguno'),
             'debug': {
                'mr_signal': signal_mean_rev,
                'tv_signal': signal_trend_vel,
                **tv_debug
            }
        }
        
        return final_buy_signal, metrics_dict

    except Exception as e:
        print(f"❌ Error de Análisis: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}
