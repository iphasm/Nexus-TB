from typing import Dict, Any
from .base import IStrategy, Signal

class ScalpingStrategy(IStrategy):
    @property
    def name(self) -> str:
        return "Scalping (High Vol)"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Scalping Strategy for High Volatility - BIDIRECTIONAL.
        
        Logic:
        - LONG: RSI momentum up + ADX trending
        - SHORT: RSI momentum down + ADX trending
        
        EMA200 is used for CONFIDENCE boost, not as a hard filter.
        This allows trading in both directions during volatile markets.
        """
        df = market_data.get('dataframe')
        if df is None or df.empty: return None
        
        # Latest Candles
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Indicators
        rsi = last.get('rsi', 50)
        adx = last.get('adx', 0)
        close = last['close']
        ema_200 = last.get('ema_200', close)
        
        signal_type = "HOLD"
        confidence = 0.0
        
        # Calculate trend alignment for confidence boost
        is_uptrend = close > ema_200
        is_downtrend = close < ema_200
        
        # MOMENTUM LONG
        # RSI crossing up with momentum, ADX confirms trend
        if rsi > 52 and last['rsi'] > prev['rsi'] and adx > 20:
            signal_type = "BUY"
            base_conf = 0.65 + (min(adx, 50)/200)
            # Boost confidence if aligned with macro trend
            confidence = base_conf + 0.1 if is_uptrend else base_conf
            
        # MOMENTUM SHORT
        # RSI crossing down with momentum, ADX confirms trend
        elif rsi < 48 and last['rsi'] < prev['rsi'] and adx > 20:
            signal_type = "SELL"
            base_conf = 0.65 + (min(adx, 50)/200)
            # Boost confidence if aligned with macro trend
            confidence = base_conf + 0.1 if is_downtrend else base_conf
            
        if signal_type == "HOLD":
            return None
            
        return Signal(
            symbol=market_data.get('symbol', "UNKNOWN"),
            action=signal_type,
            confidence=min(confidence, 1.0),
            price=last['close'],
            metadata={"strategy": "Scalping", "rsi": rsi, "adx": adx, "trend": "UP" if is_uptrend else "DOWN"}
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

