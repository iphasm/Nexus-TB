import pandas as pd
from typing import Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class MarketRegime:
    regime: str  # TREND, RANGE, VOLATILE, UNCERTAIN
    suggested_strategy: str
    confidence: float
    reason: str

class MarketClassifier:
    """
    Analyzes market data to detect the current regime and suggest the optimal strategy.
    
    Regimes:
    - TREND: High ADX, aligned EMAs. -> TrendFollowing
    - RANGE: Low ADX, High Choppiness (proxy), bounded Price. -> Grid / MeanReversion
    - VOLATILE: High ATR, rapid Price changes. -> Scalping (or WAIT if too risky)
    
    NOTE: ADX values are synthetic (EMA divergence * 2500), calibrated for:
    - Weak trend: < 15
    - Moderate trend: 15-30
    - Strong trend: > 30
    """

    @staticmethod
    def classify(market_data: Dict[str, Any]) -> MarketRegime:
        df = market_data.get('dataframe')
        symbol = market_data.get('symbol', 'UNKNOWN')
        
        # Safe default if data is missing
        if df is None or df.empty or len(df) < 50:
            return MarketRegime("UNCERTAIN", "MeanReversion", 0.0, "Insufficient Data")

        last = df.iloc[-1]
        
        # Technicals
        adx = last.get('adx', 0)
        atr = last.get('atr', 0)
        close = last.get('close', 1.0)
        rsi = last.get('rsi', 50)
        
        ema_20 = last.get('ema_20', 0)
        ema_50 = last.get('ema_50', 0)
        ema_200 = last.get('ema_200', 0)
        
        # Metrics
        atr_pct = (atr / close) * 100 if close > 0 else 0
        trend_strength = abs(ema_20 - ema_50) / close * 1000 if close > 0 else 0  # Proxy for divergence
        
        # --- CLASSIFICATION LOGIC (Reordered for Scalping Priority) ---
        
        # 1. EXTREME VOLATILITY → Force Scalping
        # When ATR% is very high, scalping is the best approach regardless of trend
        if atr_pct > 2.0:
            return MarketRegime(
                regime="VOLATILE",
                suggested_strategy="Scalping",
                confidence=0.85,
                reason=f"Extreme Volatility (ATR: {atr_pct:.2f}%) → Scalping Mode"
            )
        
        # 2. STRONG TREND → TrendFollowing (ADX must be decisive)
        # Only classify as TREND if ADX is clearly strong (> 30)
        if adx > 30 and trend_strength > 5.0:
            aligned_macro = (close > ema_200 and ema_20 > ema_50) or (close < ema_200 and ema_20 < ema_50)
            conf = 0.85 if aligned_macro else 0.70
            
            return MarketRegime(
                regime="TREND",
                suggested_strategy="TrendFollowing",
                confidence=conf,
                reason=f"Strong Trend (ADX: {adx:.1f}, Div: {trend_strength:.1f})"
            )
        
        # 3. MODERATE VOLATILITY + WEAK TREND → Scalping
        # This is the key fix - volatile markets with moderate trend go to Scalping
        if atr_pct > 1.0 and adx < 30:
            return MarketRegime(
                regime="VOLATILE",
                suggested_strategy="Scalping",
                confidence=0.75,
                reason=f"Volatile Market (ATR: {atr_pct:.2f}%, ADX: {adx:.1f}) → Scalping"
            )
        
        # 4. MODERATE TREND (original logic, but with higher threshold)
        if adx > 20 or trend_strength > 4.0:
            aligned_macro = (close > ema_200 and ema_20 > ema_50) or (close < ema_200 and ema_20 < ema_50)
            conf = 0.75 if aligned_macro else 0.60
            
            return MarketRegime(
                regime="TREND",
                suggested_strategy="TrendFollowing",
                confidence=conf,
                reason=f"Moderate Trend (ADX: {adx:.1f}, Div: {trend_strength:.1f})"
            )

        # 5. RANGING / ACCUMULATION REGIME
        # Criteria: Low ADX, EMAs close together
        if adx < 18 and trend_strength < 3.0:
            # Distinguish between Tight Range (Grid) and Wide Range (Mean Rev)
            bb_width_pct = ((last.get('upper_bb', 0) - last.get('lower_bb', 0)) / close) * 100

            if bb_width_pct < 2.5: 
                # Tight range - Grid is good
                return MarketRegime(
                    regime="RANGE_TIGHT",
                    suggested_strategy="Grid",
                    confidence=0.7,
                    reason=f"Tight Range (ADX: {adx:.1f}, BB: {bb_width_pct:.1f}%)"
                )
            else:
                # Wide swinging range - Mean Reversion better
                return MarketRegime(
                    regime="RANGE_WIDE",
                    suggested_strategy="MeanReversion",
                    confidence=0.7,
                    reason=f"Wide Range (ADX: {adx:.1f}, BB: {bb_width_pct:.1f}%)"
                )
        
        # 6. DEFAULT FALLBACK - Use Mean Reversion as safe default
        return MarketRegime(
            regime="NORMAL",
            suggested_strategy="MeanReversion",
            confidence=0.5,
            reason=f"Normal Market (ADX: {adx:.1f})"
        )

