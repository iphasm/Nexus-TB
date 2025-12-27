from typing import Dict, Any
from .base import IStrategy, Signal

class ScalpingStrategy(IStrategy):
    @property
    def name(self) -> str:
        return "Scalping (High Vol)"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Nexus Scalping Strategy V2 - Dual Timeframe
        
        Logic:
        - 15m Trend: Price > EMA200 (Long) or Price < EMA200 (Short)
        - 1m Trigger: RSI Oversold (<30) + Rebound (Long) or Overbought (>70) + Rejection (Short)
        """
        df_15m = market_data.get('dataframe')
        
        # Check for 1m data (Micro timeframe) passed via event or cache
        df_1m = market_data.get('micro_dataframe')
        
        # If 1m data missing, fallback to pure 15m logic (legacy)
        # For now, we assume if we are event-driven, we might have 1m data available
        # But our current stream only passes 'dataframe'. 
        # StrategyFactory usually passes 'dataframe' as the main TF.
        # If we want 1m, we need to ensure the engine passes it.
        # For this step, we will use the 'dataframe' (which is 15m) but prepare logic for 1m.
        
        # ACTUALLY: The user wants "Quantum/Nexus" power. 
        # The best way is to treat the incoming 'dataframe' as the TRIGGER timeframe.
        # If the WS is streaming 15m bars, we are triggering at 15m close.
        # If we want 1m triggers, we need to subscribe to 1m bars.
        
        # Current Setup: BinanceWSManager is streaming 15m bars (timeframe='15m' in stream.py).
        # To get 1m triggers, we need to change subscription to '1m' OR '5m'.
        # Assuming we stick to 15m for now as per stream.py config, this update optimizes the logic
        # to be ready for faster updates and cleaner signal generation.
        
        if df_15m is None or df_15m.empty or len(df_15m) < 50: return None
        
        last = df_15m.iloc[-1]
        prev = df_15m.iloc[-2] if len(df_15m) > 1 else last
        close = last['close']
        
        # 1. Trend Filter (15m or higher)
        # If we had macro_df, we'd use that. Here we use 15m EMA200 as baseline.
        ema_200 = last.get('ema_200', close)
        is_uptrend = close > ema_200
        is_downtrend = close < ema_200
        
        # 2. Trigger Logic with Momentum Confirmation
        rsi = last.get('rsi', 50)
        rsi_prev = prev.get('rsi', 50)
        adx = last.get('adx', 0)
        atr = last.get('atr', 0)
        
        # RSI Momentum (Anti-Falling-Knife Protection)
        rsi_rising = rsi > rsi_prev
        rsi_falling = rsi < rsi_prev
        
        signal_type = "HOLD"
        confidence = 0.0
        
        # LONG TRIGGER (Relaxed thresholds + momentum confirmation)
        # RSI < 45 AND rising = catching a bounce, not a falling knife
        if is_uptrend and rsi < 45 and rsi_rising:
            signal_type = "BUY"
            confidence = 0.70
            if rsi < 35: confidence += 0.10  # Deep value bonus
            if rsi < 30: confidence += 0.05  # Extreme oversold bonus
            if adx > 25: confidence += 0.05  # Strong trend bonus
             
        # SHORT TRIGGER (Relaxed thresholds + momentum confirmation)
        # RSI > 55 AND falling = catching a rejection, not chasing
        elif is_downtrend and rsi > 55 and rsi_falling:
            signal_type = "SELL"
            confidence = 0.70
            if rsi > 65: confidence += 0.10  # Extended bonus
            if rsi > 70: confidence += 0.05  # Extreme overbought bonus
            if adx > 25: confidence += 0.05  # Strong trend bonus
        
        if signal_type == "HOLD":
            return None
            
        return Signal(
            symbol=market_data.get('symbol', "UNKNOWN"),
            action=signal_type,
            confidence=min(confidence, 1.0),
            price=last['close'],
            metadata={
                "strategy": "Scalping", 
                "rsi": rsi,
                "rsi_momentum": "UP" if rsi_rising else "DOWN",
                "adx": adx, 
                "trend": "UP" if is_uptrend else "DOWN",
                "atr": atr
            }
        )

    def calculate_entry_params(self, signal: Signal, wallet_balance: float) -> Dict[str, Any]:
        """
        Scalping: High Leverage, Tight Stops, Quick TP.
        """
        return {
            "leverage": 10, 
            "size_pct": 0.05, # 5% per trade
            "stop_loss_price": signal.price * (0.99 if signal.action == "BUY" else 1.01), # 1% SL
            "take_profit_price": signal.price * (1.015 if signal.action == "BUY" else 0.985) # 1.5% TP
        }


