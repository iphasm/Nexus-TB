import pandas as pd
import numpy as np

# Import from consolidated indicators module (Nexus Protocol)
from servos.indicators import (
    calculate_hma,
    calculate_bollinger_bands,
    calculate_keltner_channels,
    calculate_adx,
    calculate_rsi,
    calculate_adx_slope,
    calculate_ema,
    calculate_stoch_rsi,
    calculate_atr,
    calculate_supertrend,
    calculate_vwap,
    # NEW: Advanced Indicators
    calculate_ichimoku,
    calculate_squeeze_pro,
    calculate_psar,
    calculate_choppiness
)

class StrategyEngine:
    """
    Motor de Estrategia Financiera Modular - "Squeeze & Velocity" v2.0.
    Optimizado con indicadores avanzados para mayor precisión.
    """

    def __init__(self, data: pd.DataFrame):
        """
        Inicializa con Datos OHLCV.
        """
        self.df = data.copy()
        self.metrics = {}
        
    def calculate_indicators(self):
        """
        Calcula todos los indicadores técnicos necesarios.
        """
        if self.df.empty:
            return

        # --- CORE INDICATORS ---
        # 1. HMA (55)
        self.df['hma_55'] = calculate_hma(self.df['close'], period=55)
        
        # 2. Bollinger Bands (20, 2.0)
        bb = calculate_bollinger_bands(self.df['close'], period=20, std_dev=2.0)
        self.df['bb_upper'] = bb['upper']
        self.df['bb_lower'] = bb['lower']
        
        # 3. Keltner Channels (20, 1.5)
        kc = calculate_keltner_channels(self.df, period=20, multiplier=1.5)
        self.df['kc_upper'] = kc['upper']
        self.df['kc_lower'] = kc['lower']
        
        # 4. ADX (14)
        adx_df = calculate_adx(self.df, period=14)
        self.df['adx'] = adx_df['adx']
        
        # 5. RSI (14)
        self.df['rsi'] = calculate_rsi(self.df['close'], period=14)
        
        # 6. ATR (14)
        self.df['atr'] = calculate_atr(self.df, period=14)

        # 7. EMA (200)
        self.df['ema_200'] = calculate_ema(self.df['close'], period=200)

        # 8. StochRSI (14, 3, 3)
        stoch = calculate_stoch_rsi(self.df['rsi'], period=14, k_period=3, d_period=3)
        self.df['stoch_k'] = stoch['k']
        self.df['stoch_d'] = stoch['d']

        # 9. Volume SMA (20)
        self.df['vol_sma'] = self.df['volume'].rolling(20).mean()

        # 10. Supertrend (10, 3.0)
        st = calculate_supertrend(self.df, period=10, multiplier=3.0)
        self.df['supertrend'] = st['line']
        self.df['supertrend_dir'] = st['direction']

        # 11. VWAP
        if 'volume' in self.df.columns:
            self.df['vwap'] = calculate_vwap(self.df)
        else:
            self.df['vwap'] = self.df['hma_55']

        # --- NEW: ADVANCED INDICATORS ---
        
        # 12. Choppiness Index (14) - Market State Filter
        self.df['choppiness'] = calculate_choppiness(self.df, length=14)
        
        # 13. Squeeze Pro - Enhanced Squeeze Detection
        sqz = calculate_squeeze_pro(self.df)
        self.df['sqz_on'] = sqz['squeeze_on']
        self.df['sqz_off'] = sqz['squeeze_off'] 
        self.df['sqz_mom'] = sqz['momentum']
        
        # 14. Ichimoku Cloud - Support/Resistance
        ich = calculate_ichimoku(self.df)
        self.df['ich_senkou_a'] = ich['senkou_a']
        self.df['ich_senkou_b'] = ich['senkou_b']
        self.df['ich_tenkan'] = ich['tenkan']
        self.df['ich_kijun'] = ich['kijun']
        
        # 15. PSAR - Dynamic Trailing Stops
        psar = calculate_psar(self.df)
        self.df['psar_long'] = psar['long']
        self.df['psar_short'] = psar['short']

    def analyze(self) -> dict:
        """
        Ejecuta el análisis Híbrido v2.0 con filtros avanzados.
        """
        if len(self.df) < 200:
            return {
                "signal_spot": False,
                "signal_futures": "WAIT",
                "reason_spot": "",
                "reason_futures": "Datos insuficientes (< 200 velas)",
                "metrics": {}
            }

        self.calculate_indicators()
        
        curr = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        # =================================================================
        # FILTRO MAESTRO: CHOPPINESS INDEX
        # Si el mercado está "choppy" (>61.8), NO OPERAR.
        # Esto evita falsas señales en mercados laterales.
        # =================================================================
        is_choppy = curr['choppiness'] > 61.8
        is_trending = curr['choppiness'] < 38.2  # Strong trend
        
        # --- 1. ANÁLISIS SPOT (Mean Reversion) ---
        spot_signal = False
        spot_reason = ""
        
        cond_bb_spot = curr['close'] < curr['bb_lower']
        cond_rsi_spot = curr['rsi'] < 40
        cond_stoch_spot = (prev['stoch_k'] < prev['stoch_d']) and (curr['stoch_k'] > curr['stoch_d']) and (curr['stoch_k'] < 20)
        
        # NEW: Ichimoku Cloud Support (Price near cloud base)
        cloud_top = max(curr['ich_senkou_a'], curr['ich_senkou_b'])
        cloud_bottom = min(curr['ich_senkou_a'], curr['ich_senkou_b'])
        near_cloud_support = curr['close'] <= cloud_bottom * 1.02  # Within 2% of cloud
        
        if cond_bb_spot and cond_rsi_spot and cond_stoch_spot and not is_choppy:
            spot_signal = True
            spot_reason = "💎 **MEAN REVERSION**: Precio bajo BB + RSI bajo + StochRSI cruce."
            if near_cloud_support:
                spot_reason += " ☁️ Soporte Ichimoku confirmado."

        # --- 2. ANÁLISIS FUTUROS (Squeeze & Velocity) ---
        fut_signal = "WAIT"
        fut_reason = "Monitorizando..."

        # =================================================================
        # FILTRO ANTI-CHOP: Si el mercado está lateral, NO ENTRAR.
        # =================================================================
        if is_choppy:
            return {
                "signal_spot": spot_signal,
                "signal_futures": "WAIT",
                "reason_spot": spot_reason,
                "reason_futures": "⏸️ **MERCADO LATERAL**: Choppiness >61.8. Esperando tendencia.",
                "metrics": self._build_metrics(curr)
            }

        # NEW: Usar Squeeze Pro en lugar de lógica manual
        squeeze_firing = (curr['sqz_off'] == 1) and (prev['sqz_on'] == 1)  # Squeeze just released
        squeeze_momentum_bullish = curr['sqz_mom'] > 0 and curr['sqz_mom'] > prev['sqz_mom']
        squeeze_momentum_bearish = curr['sqz_mom'] < 0 and curr['sqz_mom'] < prev['sqz_mom']
        
        breakout_up = (curr['close'] > curr['bb_upper'])
        momentum_bullish = (curr['rsi'] > 50)
        
        # TREND FILTER: Supertrend + VWAP + Ichimoku Cloud
        above_cloud = curr['close'] > cloud_top
        trend_bullish = (curr['supertrend_dir'] == 1) and (curr['close'] > curr['vwap']) and above_cloud
        
        adx_rising = curr['adx'] > prev['adx']
        adx_strong = curr['adx'] > 20
        
        # ENTRY LONG
        if trend_bullish and momentum_bullish and adx_rising:
            if squeeze_firing and squeeze_momentum_bullish:
                fut_signal = "BUY"
                fut_reason = "🚀 **SQUEEZE PRO BREAKOUT**: Compresión liberada + Momentum alcista."
            elif breakout_up and adx_strong and is_trending:
                fut_signal = "BUY"
                fut_reason = "🌊 **VELOCITY TREND**: Tendencia fuerte confirmada (Chop <38.2)."

        # ENTRY SHORT
        breakout_down = (curr['close'] < curr['bb_lower'])
        momentum_bearish = (curr['rsi'] < 50)
        below_cloud = curr['close'] < cloud_bottom
        trend_bearish = (curr['supertrend_dir'] == -1) and (curr['close'] < curr['vwap']) and below_cloud
        
        if trend_bearish and momentum_bearish and adx_rising:
            if fut_signal == "WAIT":
                if squeeze_firing and squeeze_momentum_bearish:
                    fut_signal = "SHORT"
                    fut_reason = "🔻 **SQUEEZE PRO SHORT**: Compresión liberada + Momentum bajista."
                elif breakout_down and adx_strong and is_trending:
                    fut_signal = "SHORT"
                    fut_reason = "📉 **BEARISH VELOCITY**: Tendencia bajista confirmada."
        
        # EXIT LOGIC: Supertrend Flip OR PSAR Hit
        adx_collapse = (prev['adx'] > 30 and curr['adx'] < 25)
        
        # NEW: PSAR-based exit (more precise than just Supertrend)
        psar_exit_long = pd.notna(curr['psar_short']) and curr['close'] < curr['psar_short']
        psar_exit_short = pd.notna(curr['psar_long']) and curr['close'] > curr['psar_long']
        
        trend_loss_bull = (curr['supertrend_dir'] == -1) or psar_exit_long
        trend_loss_bear = (curr['supertrend_dir'] == 1) or psar_exit_short
        
        if trend_loss_bull and fut_signal == "WAIT":
            fut_signal = "CLOSE_LONG"
            fut_reason = "📉 **EXIT SIGNAL**: PSAR/Supertrend indica cierre de Long."
            
        elif trend_loss_bear and fut_signal == "WAIT":
            fut_signal = "CLOSE_SHORT"
            fut_reason = "📈 **EXIT SIGNAL**: PSAR/Supertrend indica cierre de Short."
            
        elif adx_collapse and fut_signal == "WAIT":
            fut_signal = "EXIT_ALL"
            fut_reason = "⚠️ **ADX COLLAPSE**: Pérdida de fuerza tendencial."

        return {
            "signal_spot": spot_signal,
            "signal_futures": fut_signal,
            "reason_spot": spot_reason,
            "reason_futures": fut_reason,
            "metrics": self._build_metrics(curr)
        }

    def _build_metrics(self, curr) -> dict:
        """Build metrics dictionary."""
        return {
            "close": float(curr['close']),
            "rsi": float(curr['rsi']),
            "adx": float(curr['adx']),
            "choppiness": float(curr.get('choppiness', 50)),
            "squeeze_momentum": float(curr.get('sqz_mom', 0)),
            "stoch_k": float(curr['stoch_k']),
            "bb_lower": float(curr['bb_lower']),
            "hma_55": float(curr['hma_55']),
            "vwap": float(curr.get('vwap', 0)),
            "supertrend": float(curr['supertrend']),
            "supertrend_dir": int(curr['supertrend_dir']),
            "ich_cloud_top": float(max(curr.get('ich_senkou_a', 0), curr.get('ich_senkou_b', 0))),
            "psar_long": float(curr.get('psar_long', 0)) if pd.notna(curr.get('psar_long')) else 0,
            "psar_short": float(curr.get('psar_short', 0)) if pd.notna(curr.get('psar_short')) else 0,
            "atr": float(curr['atr'])
        }

    def analyze_macro_trend(self, df_macro: pd.DataFrame) -> str:
        """
        Analiza la tendencia MACRO (ej. 1H o 4H) con Ichimoku.
        """
        if df_macro.empty or len(df_macro) < 200:
            return "NEUTRAL"
            
        # Use Ichimoku for macro analysis
        ich = calculate_ichimoku(df_macro)
        last_close = df_macro['close'].iloc[-1]
        cloud_top = max(ich['senkou_a'].iloc[-1], ich['senkou_b'].iloc[-1])
        cloud_bottom = min(ich['senkou_a'].iloc[-1], ich['senkou_b'].iloc[-1])
        
        if last_close > cloud_top:
            return "BULL"
        elif last_close < cloud_bottom:
            return "BEAR"
            
        return "NEUTRAL"
