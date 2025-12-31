import pandas as pd
from typing import Dict, Any
from .base import IStrategy, Signal

class TrendFollowingStrategy(IStrategy):
    """
    Classic Trend Following for Dominant Assets (BTC).
    
    BIDIRECTIONAL:
    - BUY: EMA20 > EMA50 (uptrend) + ADX confirms trend strength
    - SELL: EMA20 < EMA50 (downtrend) + ADX confirms trend strength
    """
    
    @property
    def name(self) -> str:
        return "TrendFollowing"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Trend Following Strategy - BIDIRECTIONAL with protection.
        
        Logic:
        - LONG: EMA20 crosses above EMA50 with ADX > 20
        - SHORT: EMA20 crosses below EMA50 with ADX > 20
        
        Filters:
        - Volatility Filter: Skip if ATR > 2x average (extreme conditions)
        """
        df = market_data.get('dataframe')
        if df is None or df.empty or len(df) < 3:
            return None

        last_row = df.iloc[-1]
        
        ema_short = last_row.get('ema_20', 0)
        ema_long = last_row.get('ema_50', 0)
        ema_200 = last_row.get('ema_200', 0)
        adx = last_row.get('adx', 0)
        price = last_row.get('close', 0)
        atr = last_row.get('atr', 0)
        
        # VOLATILITY FILTER: Skip extreme volatility
        atr_avg = df['atr'].rolling(20).mean().iloc[-1] if 'atr' in df.columns else atr
        if atr > atr_avg * 2.0 and atr_avg > 0:
            return None  # Skip during extreme conditions
        
        signal_type = "HOLD"
        confidence = 0.0
        
        # Macro trend context
        is_macro_uptrend = price > ema_200 if ema_200 > 0 else True
        
        # UPTREND - EMA20 > EMA50
        if ema_short > ema_long and adx > 20:
            signal_type = "BUY"
            base_conf = min(adx / 50, 0.8)
            # Boost if aligned with macro trend
            confidence = base_conf + 0.15 if is_macro_uptrend else base_conf
            
        # DOWNTREND - EMA20 < EMA50
        elif ema_short < ema_long and adx > 20:
            signal_type = "SELL"
            base_conf = min(adx / 50, 0.8)
            # Boost if aligned with macro trend (bearish = price < EMA200)
            confidence = base_conf + 0.15 if not is_macro_uptrend else base_conf
        
        # --- PREMIUM SIGNALS (MTF & Volume) ---
        # Stricter filtering if MTF data is available
        macro_df = market_data.get('macro_dataframe')
        if macro_df is not None and not macro_df.empty and signal_type != "HOLD":
            try:
                macro_last = macro_df.iloc[-1]
                macro_close = macro_last['close']
                # Use EMA200 if available, else EMA50
                macro_ema = macro_last.get('ema_200', macro_last.get('ema_50', 0))
                
                # 1. MTF Confirmation (Must align with Macro Trend)
                if signal_type == "BUY" and macro_close < macro_ema:
                    return None # Filter out: Macro is Bearish
                if signal_type == "SELL" and macro_close > macro_ema:
                    return None # Filter out: Macro is Bullish
                
                # 2. Volume Validation
                vol_sma = last_row.get('vol_sma', 0)
                volume = last_row.get('volume', 0)
                if volume > vol_sma:
                    confidence += 0.1 # Volume Breakout Boost
                else:
                    confidence -= 0.05 # Low Volume Penalty
                    
                # 3. OBV Alignment (Optional for now, keeping simple)
                
            except Exception as e:
                print(f"⚠️ Premium Logic Error: {e}")
                pass # Fallback to standard logic if error
        
        # Return None for HOLD to avoid processing non-actionable signals
        if signal_type == "HOLD":
            return None
            
        return Signal(
            symbol=market_data.get('symbol', "BTC"),
            action=signal_type,
            confidence=min(confidence, 1.0),
            price=price,
            metadata={
                "adx": adx, 
                "ema_diff": ema_short - ema_long,
                "trend": "UP" if ema_short > ema_long else "DOWN",
                "atr": atr
            }
        )

    def calculate_entry_params(self, signal: Signal, wallet_balance: float, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trend strategies use wider stops (ATR * 2) and try to ride the wave.
        RESPETA LÍMITES DE PERFILES DE RIESGO
        """
        atr = signal.metadata.get('atr', 100) # Fallback

        # Safe Config Get - RESPETAR LÍMITES DE PERFIL
        cfg = config or {}
        base_leverage = cfg.get('leverage', 5)
        max_allowed_leverage = cfg.get('max_leverage_allowed', base_leverage)
        lev = min(base_leverage, max_allowed_leverage)  # RESPETAR TOPE DE PERFIL

        # Use risk % if available, else default size
        risk_pct = cfg.get('risk_per_trade_pct', 0.01)

        # RESPETAR LÍMITE DE CAPITAL DEL PERFIL
        base_size_pct = cfg.get('max_capital_pct', 0.10)
        max_allowed_capital = cfg.get('max_capital_pct_allowed', base_size_pct)
        size_pct = min(base_size_pct, max_allowed_capital)  # RESPETAR TOPE DE PERFIL
        
        # Calculate dynamic prices
        # Trend: Wide stops (2 ATR)
        sl_price = signal.price - (atr * 2) if signal.action == "BUY" else signal.price + (atr * 2)
        tp_price = signal.price + (atr * 4) if signal.action == "BUY" else signal.price - (atr * 4)
        
        return {
            "leverage": lev,
            "size_pct": size_pct,
            "stop_loss_price": sl_price,
            "take_profit_price": tp_price
        }


