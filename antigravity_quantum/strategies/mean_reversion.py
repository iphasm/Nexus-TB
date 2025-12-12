from typing import Dict, Any
from .base import IStrategy, Signal

class MeanReversionStrategy(IStrategy):
    @property
    def name(self) -> str:
        return "MeanReversion (ETH)"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Mean Reversion Logic:
        - Buy: Price < Lower BB AND RSI < 30 (Oversold)
        - Sell: Price > Upper BB AND RSI > 70 (Overbought)
        """
        df = market_data.get('dataframe')
        if df is None or df.empty:
            return None
            
        last_row = df.iloc[-1]
        
        price = last_row.get('close', 0)
        rsi = last_row.get('rsi', 50)
        lower_bb = last_row.get('lower_bb', 0)
        upper_bb = last_row.get('upper_bb', 0)
        middle_bb = last_row.get('ema_20', 0) # SMA 20 usually middle band
        ema_200 = last_row.get('ema_200', 0) # Macro Trend Filter
        
        signal_type = "HOLD"
        confidence = 0.0
        
        # BUY SIGNAL (Long)
        # Condition: Price < BB Lower AND RSI < 30 AND Price > EMA 200 (Uptrend)
        if price < lower_bb and rsi < 30 and price > ema_200:
            signal_type = "BUY"
            # Confidence increases as RSI gets lower
            confidence = min((30 - rsi) / 20 + 0.5, 1.0)
            
        # SELL SIGNAL (Short)
        # Condition: Price > BB Upper AND RSI > 70 AND Price < EMA 200 (Downtrend)
        elif price > upper_bb and rsi > 70 and price < ema_200:
            signal_type = "SELL"
            confidence = min((rsi - 70) / 20 + 0.5, 1.0)
            
        # EXIT LOGIC (Reversion to mean)
        # We also want to exit Longs if they hit Upper Band, or Shorts if Lower Band
        # Simplistic exit for now:
        # If LONG and Price > Middle BB -> EXIT ? 
        # For this prototype we keep simplistic "Opposite Signal" or explicit Exit logic. 
        # But wait, original code only exited on "SELL". 
        # Lets add explicit EXIT action if we cross the mean (EMA20) to lock profits.
        
        # NOTE: The Backtest Engine treats 'SELL' as closing a position if one exists.
        # But 'SELL' here basically means Open Short.
        # We need to distinguish Open Short vs Close Long.
        # Current Backtest Engine is simplistic: 
        #   - If BUY and no pos -> Open Long
        #   - If SELL and pos -> Close Long
        # This is a limitation of the engine for bidirectional trading.
        # For Mean Reversion, "SELL" signal usually means "Overbought". 
        # So using it to close a Long is correct.
        
        # However, we won't open a Short unless the trend is bearish (Price < EMA 200).
        # But we SHOULD close a Long regardless of EMA 200 if it's overbought.
        
        # Refined Logic:
        # 1. Check for Exits first
        # (This would require knowing current position, which analyze() doesn't know fully yet)
        # Assuming simplistic engine compliance:
        
        if price > upper_bb and rsi > 70:
             # Just signal SELL. Engine will close Long if exists.
             # If no Long, Engine will try to Open Short -> Checked by EMA 200 below?
             # Wait, engine logic: 
             # if signal.action == "SELL" ... and position is not None: Close.
             # So 'SELL' signal closes meaningful position.
             # But it doesn't open short unless enabled. 
             # My Engine logic ONLY supports Long-only spot for now (BacktestEngine lines 65-85).
             # It does NOT support opening shorts.
             
             # So, 'SELL' just closes.
             signal_type = "SELL"
             confidence = 0.9

        # If no sell condition, check Buy
        elif price < lower_bb and rsi < 30 and price > ema_200:
             signal_type = "BUY"
             confidence = min((30 - rsi) / 20 + 0.5, 1.0)
            
        # EXIT LOGIC (Reversion to mean)
        # If we just hit middle band, it's often a take profit point
        # But simplistic engine handles "SELL" as exit.
            
        if signal_type == "HOLD":
            return None
            
        return Signal(
            symbol=market_data.get('symbol', "ETH"), 
            action=signal_type,
            confidence=confidence,
            price=price,
            metadata={"rsi": rsi, "bb_width": upper_bb - lower_bb}
        )

    def calculate_entry_params(self, signal: Signal, wallet_balance: float) -> Dict[str, Any]:
        """
        Mean Reversion targets quick scalps.
        """
        return {
            "leverage": 10, 
            "size_pct": 0.15,
            "stop_loss_price": signal.price * 0.98 if signal.action == "BUY" else signal.price * 1.02,
            "take_profit_price": signal.price * 1.02 if signal.action == "BUY" else signal.price * 0.98
        }
