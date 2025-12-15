from typing import Dict, Any
from .base import IStrategy, Signal

class MeanReversionStrategy(IStrategy):
    @property
    def name(self) -> str:
        return "MeanReversion"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Mean Reversion - BIDIRECTIONAL Strategy.
        
        Logic:
        - BUY (Long): Price < Lower BB AND RSI < 30 (Oversold bounce)
        - SELL (Short): Price > Upper BB AND RSI > 70 (Overbought reversal)
        
        EMA200 is used for CONFIDENCE adjustment only, NOT as a hard filter.
        This allows:
        - Buying oversold dips even in downtrends (contrarian)
        - Shorting overbought pumps even in uptrends (contrarian)
        """
        df = market_data.get('dataframe')
        if df is None or df.empty:
            return None
            
        last_row = df.iloc[-1]
        
        price = last_row.get('close', 0)
        rsi = last_row.get('rsi', 50)
        lower_bb = last_row.get('lower_bb', 0)
        upper_bb = last_row.get('upper_bb', 0)
        ema_200 = last_row.get('ema_200', price)
        
        signal_type = "HOLD"
        confidence = 0.0
        
        # Trend context for confidence adjustment
        is_uptrend = price > ema_200
        is_downtrend = price < ema_200
        
        # SELL SIGNAL (Short / Close Long)
        # Priority: Check overbought first (take profits or enter short)
        if price > upper_bb and rsi > 70:
            signal_type = "SELL"
            # Base confidence from RSI extremity
            base_conf = 0.7 + min((rsi - 70) / 30, 0.2)
            # Higher confidence if in downtrend (trend-aligned short)
            confidence = base_conf + 0.1 if is_downtrend else base_conf
            
        # BUY SIGNAL (Long)
        # Oversold bounce - works in uptrends AND as contrarian in downtrends
        elif price < lower_bb and rsi < 30:
            signal_type = "BUY"
            # Base confidence from RSI extremity  
            base_conf = 0.7 + min((30 - rsi) / 30, 0.2)
            # Higher confidence if in uptrend (trend-aligned long)
            # But still allow trades in downtrend with lower confidence
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
                "bb_width": upper_bb - lower_bb,
                "trend": "UP" if is_uptrend else "DOWN"
            }
        )

    def calculate_entry_params(self, signal: Signal, wallet_balance: float) -> Dict[str, Any]:
        """
        Mean Reversion targets quick scalps with tight risk.
        """
        return {
            "leverage": 10, 
            "size_pct": 0.10,  # 10% per trade
            "stop_loss_price": signal.price * 0.98 if signal.action == "BUY" else signal.price * 1.02,
            "take_profit_price": signal.price * 1.03 if signal.action == "BUY" else signal.price * 0.97
        }

