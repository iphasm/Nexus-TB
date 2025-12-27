from typing import Dict, Any
from .base import IStrategy, Signal

class SharkStrategy(IStrategy):
    """
    Shark Mode: Aggressive Short-Only Strategy for Sangría Markets.
    
    Target: Altcoins dropping faster than BTC.
    Logic:
    - STRONG DOWNTREND: Price < EMA50 < EMA200
    - MOMENTUM: ADX > 25 (Strong Trend)
    - RSI: < 50 (Bearish control) but > 20 (Not bottomed yet)
    """

    @property
    def name(self) -> str:
        return "Shark Mode"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Analyze logic for SHARK entry.
        """
        df = market_data.get('dataframe')
        if df is None or df.empty or len(df) < 200:
            return None

        current = df.iloc[-1]
        
        # 1. Indicators
        price = current['close']
        ema_50 = current.get('ema_50', 0)
        ema_200 = current.get('ema_200', 0)
        adx = current.get('adx', 0)
        rsi = current.get('rsi', 50)
        atr = current.get('atr', 0)

        # 2. Shark Logic (Strict Bearish)
        # Structure: Price below EMAs, and shorter EMA below longer EMA (Death Cross alignment)
        is_bear_structure = price < ema_50 < ema_200
        
        # Momentum: Trend is strong (ADX) and Bears in control (RSI < 50)
        # Avoid oversold bottoms (RSI > 20)
        is_valid_momentum = (adx > 25) and (20 < rsi < 50)
        
        signal_type = "HOLD"
        confidence = 0.0

        if is_bear_structure and is_valid_momentum:
            signal_type = "SELL"
            # Confidence scales with ADX (strength of crash)
            confidence = min(0.7 + (adx / 100), 0.95)
            
        if signal_type == "HOLD":
            return None

        return Signal(
            symbol=market_data.get('symbol', "UNKNOWN"),
            action=signal_type,
            confidence=confidence,
            price=price,
            metadata={
                "strategy": "SHARK",
                "adx": adx,
                "rsi": rsi,
                "ema_structure": "BEARISH",
                "atr": atr
            }
        )

    def calculate_entry_params(self, signal: Signal, wallet_balance: float) -> Dict[str, Any]:
        """
        Shark Parameters: High Leverage, Aggressive Stops.
        """
        price = signal.price
        atr = signal.metadata.get('atr', price * 0.02)
        
        return {
            "leverage": 7,  # Higher leverage for high conviction crash
            "size_pct": 0.08, # 8% per trade
            "stop_loss_price": price + (atr * 2.0), # Trailing style room
            "take_profit_price": price - (atr * 4.0) # Target deeper flush
        }
