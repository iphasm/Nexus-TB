from typing import Dict, Any
from .base import IStrategy, Signal

class ScalpingStrategy(IStrategy):
    @property
    def name(self) -> str:
        return "Scalping"

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
        
        # ACTUALLY: The user wants "Nexus" power. 
        # The best way is to treat the incoming 'dataframe' as the TRIGGER timeframe.
        # If the WS is streaming 15m bars, we are triggering at 15m close.
        # If we want 1m triggers, we need to subscribe to 1m bars.
        
        # Current Setup: BinanceWSManager is streaming 15m bars (timeframe='15m' in stream.py).
        # To get 1m triggers, we need to change subscription to '1m' OR '5m'.
        # Assuming we stick to 15m for now as per stream.py config, this update optimizes the logic
        # to be ready for faster updates and cleaner signal generation.
        
        # Prefer 1m data for Trigger, Fallback to 15m if missing
        trigger_df = df_1m if df_1m is not None and not df_1m.empty and len(df_1m) > 10 else df_15m
        trend_df = df_15m
        
        last = trigger_df.iloc[-1]
        prev = trigger_df.iloc[-2] if len(trigger_df) > 1 else last
        
        # 1. Trend Filter (Always use 15m or higher)
        trend_last = trend_df.iloc[-1]
        trend_close = trend_last['close']
        ema_200 = trend_last.get('ema_200', trend_close)
        
        # Trend Logic
        is_uptrend = trend_close > ema_200
        is_downtrend = trend_close < ema_200
        
        # 2. Trigger Logic (Uses Trigger TF - 1m ideal)
        # We use RSI and Momentum from the Trigger TF (1m)
        rsi = last.get('rsi', 50)
        rsi_prev = prev.get('rsi', 50)
        adx = last.get('adx', 0) # ADX of 1m indicates micro-trend strength
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

    def calculate_entry_params(self, signal: Signal, wallet_balance: float, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scalping: High Leverage, ATR-based Stops, Quick TP.
        Now uses ATR for dynamic SL/TP calculation instead of fixed percentages.
        """
        # Safe Config Get
        cfg = config or {}
        lev = cfg.get('leverage', 10)
        size_pct = cfg.get('max_capital_pct', 0.05)  # Default 5% for scalping

        # Get ATR from signal metadata (passed from trading_manager)
        atr = signal.metadata.get('atr', 0)
        current_price = signal.price

        # Base SL/TP calculations using ATR (much more realistic)
        if atr > 0:
            # Scalping: SL = 1.5 * ATR, TP = 2.5 * ATR (RR ratio ~1.7:1)
            sl_distance = 1.5 * atr
            tp_distance = 2.5 * atr
        else:
            # Fallback if no ATR available (shouldn't happen in normal operation)
            # Use 2% SL and 3.5% TP as reasonable defaults
            sl_distance = current_price * 0.02
            tp_distance = current_price * 0.035

        # Apply Risk Scaling if available
        try:
            from nexus_system.core.risk_scaler import RiskScaler
            scaler = RiskScaler()

            # Get scaling multipliers (requires confidence, strategy, and market data)
            # For now, use defaults since we don't have full context
            confidence = signal.confidence if hasattr(signal, 'confidence') else 0.7
            multipliers = scaler.calculate_risk_multipliers(
                confidence=confidence,
                strategy="Scalping",
                market_data=None  # Could be enhanced to pass market regime
            )

            # Apply scaling to SL/TP distances
            sl_distance *= multipliers.stop_loss_multiplier
            tp_distance *= multipliers.take_profit_multiplier

        except Exception as e:
            # If risk scaling fails, use base ATR calculations
            print(f"⚠️ Risk scaling unavailable for scalping: {e}")

        # Calculate actual SL/TP prices
        if signal.action == "BUY":
            stop_loss_price = current_price - sl_distance
            take_profit_price = current_price + tp_distance
        else:  # SHORT
            stop_loss_price = current_price + sl_distance
            take_profit_price = current_price - tp_distance

        # Ensure minimum distance to avoid instant closes
        min_distance_pct = 0.005  # 0.5% minimum
        min_distance = current_price * min_distance_pct

        if abs(stop_loss_price - current_price) < min_distance:
            if signal.action == "BUY":
                stop_loss_price = current_price - min_distance
            else:
                stop_loss_price = current_price + min_distance

        if abs(take_profit_price - current_price) < min_distance:
            if signal.action == "BUY":
                take_profit_price = current_price + min_distance
            else:
                take_profit_price = current_price - min_distance

        return {
            "leverage": lev,
            "size_pct": size_pct,
            "stop_loss_price": stop_loss_price,
            "take_profit_price": take_profit_price
        }


