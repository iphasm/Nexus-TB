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
        Trend Following Strategy - BIDIRECTIONAL.
        
        Logic:
        - LONG: EMA20 crosses above EMA50 with ADX > 20
        - SHORT: EMA20 crosses below EMA50 with ADX > 20
        """
        df = market_data.get('dataframe')
        if df is None or df.empty:
            return None

        last_row = df.iloc[-1]
        
        ema_short = last_row.get('ema_20', 0)
        ema_long = last_row.get('ema_50', 0)
        ema_200 = last_row.get('ema_200', 0)
        adx = last_row.get('adx', 0)
        price = last_row.get('close', 0)
        
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
                "trend": "UP" if ema_short > ema_long else "DOWN"
            }
        )

    def calculate_entry_params(self, signal: Signal, wallet_balance: float) -> Dict[str, Any]:
        """
        Trend strategies use wider stops (ATR * 2) and try to ride the wave.
        """
        atr = signal.metadata.get('atr', 100) # Fallback
        
        return {
            "leverage": 5,
            "size_pct": 0.10,
            "stop_loss_price": signal.price - (atr * 2) if signal.action == "BUY" else signal.price + (atr * 2),
            "take_profit_price": signal.price + (atr * 4) if signal.action == "BUY" else signal.price - (atr * 4)
        }

