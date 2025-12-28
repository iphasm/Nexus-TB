from typing import Dict, Any
from .base import IStrategy, Signal

class MeanReversionStrategy(IStrategy):
    @property
    def name(self) -> str:
        return "MeanReversion"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Mean Reversion - BIDIRECTIONAL Strategy with ANTI-FALLING-KNIFE protection.
        
        Logic:
        - BUY (Long): Price < Lower BB AND RSI < 30 AND RSI is RISING (momentum confirm)
        - SELL (Short): Price > Upper BB AND RSI > 70 AND RSI is FALLING
        
        Additional Filters:
        - Volatility Filter: Skip if ATR > 2x average (extreme volatility)
        - RSI Momentum: Must confirm direction before entry
        """
        df = market_data.get('dataframe')
        if df is None or df.empty or len(df) < 3:
            return None
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        price = last_row.get('close', 0)
        rsi = last_row.get('rsi', 50)
        rsi_prev = prev_row.get('rsi', 50)
        lower_bb = last_row.get('lower_bb', 0)
        upper_bb = last_row.get('upper_bb', 0)
        ema_200 = last_row.get('ema_200', price)
        atr = last_row.get('atr', 0)
        
        # VOLATILITY FILTER: Skip if extreme volatility (ATR > 2x average)
        atr_avg = df['atr'].rolling(20).mean().iloc[-1] if 'atr' in df.columns else atr
        if atr > atr_avg * 2.0 and atr_avg > 0:
            # Extreme volatility - skip signal
            return None
        
        signal_type = "HOLD"
        confidence = 0.0
        
        # Trend context for confidence adjustment
        adx = last_row.get('adx', 0)
        is_ranging = adx < 20
        
        # If Ranging (Low ADX), we ignore EMA trend and trade both sides
        if is_ranging:
            is_uptrend = True
            is_downtrend = True
        else:
            is_uptrend = price > ema_200
            is_downtrend = price < ema_200
        
        # RSI MOMENTUM CHECKS (Anti-Falling-Knife)
        rsi_rising = rsi > rsi_prev
        rsi_falling = rsi < rsi_prev
        
        # SELL SIGNAL (Short / Close Long)
        # Overbought + RSI turning down = reversal confirmation
        if price > upper_bb and rsi > 70 and rsi_falling:
            signal_type = "SELL"
            base_conf = 0.7 + min((rsi - 70) / 30, 0.2)
            confidence = base_conf + 0.1 if is_downtrend else base_conf
            
        # BUY SIGNAL (Long)
        # Oversold + RSI turning UP = bounce confirmation (NOT falling knife)
        elif price < lower_bb and rsi < 30 and rsi_rising:
            signal_type = "BUY"
            base_conf = 0.7 + min((30 - rsi) / 30, 0.2)
            confidence = base_conf + 0.1 if is_uptrend else base_conf
            
        if signal_type == "HOLD":
            return None
            
        return Signal(
            symbol=market_data.get('symbol', "UNKNOWN"), 
            action=signal_type,
            confidence=min(confidence, 1.0),
            price=price,
            metadata={
                "rsi": rsi, 
                "rsi_momentum": "UP" if rsi_rising else "DOWN",
                "bb_width": upper_bb - lower_bb,
                "trend": "UP" if is_uptrend else "DOWN",
                "atr": atr,
                "volatility_filter": "PASS"
            }
        )

    def calculate_entry_params(self, signal: Signal, wallet_balance: float, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Mean Reversion targets quick scalps with tight risk.
        Now uses ATR for dynamic stops (Consistency fix).
        """
        # Safe Config Get
        cfg = config or {}
        lev = cfg.get('leverage', 10)
        size_pct = cfg.get('max_capital_pct', 0.10)
        
        price = signal.price
        atr = signal.metadata.get('atr', price * 0.01) # Fallback 1%
        
        # SL = 2 * ATR (Tight but dynamic)
        # TP = 3 * ATR
        sl_dist = atr * 2.0
        tp_dist = atr * 3.0
        
        if signal.action == "BUY":
            sl_price = price - sl_dist
            tp_price = price + tp_dist
        else:
            sl_price = price + sl_dist
            tp_price = price - tp_dist
        
        return {
            "leverage": lev, 
            "size_pct": size_pct,
            "stop_loss_price": sl_price,
            "take_profit_price": tp_price
        }


