from typing import Dict, Any
from .base import IStrategy, Signal

class ScalpingStrategy(IStrategy):
    @property
    def name(self) -> str:
        return "Scalping (High Vol)"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Scalping Strategy for High Volatility - BIDIRECTIONAL with protection.
        
        Logic:
        - LONG: RSI momentum up + ADX trending + RSI rising for 2+ candles
        - SHORT: RSI momentum down + ADX trending + RSI falling for 2+ candles
        
        Filters:
        - Volatility Filter: Skip if ATR > 2x average (extreme crash/pump)
        - Momentum Strength: Require sustained direction, not just single candle
        """
        df = market_data.get('dataframe')
        if df is None or df.empty or len(df) < 4: return None
        
        # Latest Candles
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        # Indicators
        rsi = last.get('rsi', 50)
        rsi_prev = prev.get('rsi', 50)
        rsi_prev2 = prev2.get('rsi', 50)
        adx = last.get('adx', 0)
        close = last['close']
        ema_200 = last.get('ema_200', close)
        atr = last.get('atr', 0)
        
        # VOLATILITY FILTER: Skip extreme volatility
        atr_avg = df['atr'].rolling(20).mean().iloc[-1] if 'atr' in df.columns else atr
        if atr > atr_avg * 2.0 and atr_avg > 0:
            return None  # Skip during crashes/pumps
        
        signal_type = "HOLD"
        confidence = 0.0
        
        # Calculate trend alignment for confidence boost
        is_uptrend = close > ema_200
        is_downtrend = close < ema_200
        
        # MOMENTUM CHECKS - Require 2 consecutive candles in same direction
        rsi_rising_strong = rsi > rsi_prev > rsi_prev2  # 2 candles up
        rsi_falling_strong = rsi < rsi_prev < rsi_prev2  # 2 candles down
        
        # MOMENTUM LONG - Strong upward RSI with trend confirmation
        if rsi > 52 and rsi_rising_strong and adx > 20:
            signal_type = "BUY"
            base_conf = 0.65 + (min(adx, 50)/200)
            confidence = base_conf + 0.1 if is_uptrend else base_conf
            
        # MOMENTUM SHORT - Strong downward RSI with trend confirmation
        elif rsi < 48 and rsi_falling_strong and adx > 20:
            signal_type = "SELL"
            base_conf = 0.65 + (min(adx, 50)/200)
            confidence = base_conf + 0.1 if is_downtrend else base_conf
            
        # --- PREMIUM SIGNALS (RSI Divergence & MTF) ---
        if signal_type != "HOLD":
            # 1. RSI Divergence (Last 10 frames)
            if len(df) >= 15:
                recent = df.iloc[-5:]
                older = df.iloc[-10:-5]
                
                # Bullish Div: Lower Low Price + Higher Low RSI
                if signal_type == "BUY":
                    if recent['low'].min() < older['low'].min() and recent['rsi'].min() > older['rsi'].min():
                        confidence = min(confidence + 0.15, 1.0)
                        
                # Bearish Div: Higher High Price + Lower High RSI
                elif signal_type == "SELL":
                    if recent['high'].max() > older['high'].max() and recent['rsi'].max() < older['rsi'].max():
                         confidence = min(confidence + 0.15, 1.0)
                         
            # 2. MTF Filter (Macro RSI Context)
            macro_df = market_data.get('macro_dataframe')
            if macro_df is not None and not macro_df.empty:
                try:
                    macro_rsi = macro_df.iloc[-1].get('rsi', 50)
                    
                    # Prevent buying into Macro Bear Trend limit? 
                    # Actually for scalping, we just want to avoid fighting massive momentum.
                    if signal_type == "BUY" and macro_rsi < 30: 
                        confidence += 0.1 # Oversold bounce likely
                    elif signal_type == "SELL" and macro_rsi > 70:
                        confidence += 0.1 # Overbought dump likely
                        
                    # Filter: Don't Short if Macro RSI > 60 (Likely strong uptrend)
                    if signal_type == "SELL" and macro_rsi > 60:
                        return None 
                    # Filter: Don't Long if Macro RSI < 40 (Likely strong downtrend)
                    if signal_type == "BUY" and macro_rsi < 40:
                        return None
                        
                except: pass
            
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
                "adx": adx, 
                "trend": "UP" if is_uptrend else "DOWN",
                "momentum_strength": "STRONG",
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


