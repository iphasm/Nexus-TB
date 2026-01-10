"""
Multi-Timeframe (MTF) Confluence Filter
Filters signals by requiring alignment across 3 timeframes: Micro (1m), Main (15m), Macro (4h).
Only signals with high confluence score pass the filter.
"""
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class TrendDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class MTFAnalysis:
    """Result of multi-timeframe analysis for a symbol."""
    symbol: str
    
    # Trend per timeframe
    micro_trend: TrendDirection  # 1m
    main_trend: TrendDirection   # 15m
    macro_trend: TrendDirection  # 4h
    
    # Individual scores (0-10)
    trend_alignment_score: float
    momentum_score: float
    volume_score: float
    structure_score: float
    
    # Overall confluence (0-10)
    confluence_score: float
    
    # Filter decision
    passed: bool
    reason: str
    
    @property
    def direction(self) -> TrendDirection:
        """Overall direction based on macro trend."""
        return self.macro_trend


class MTFConfluenceFilter:
    """
    Multi-Timeframe Confluence Filter.
    
    Scoring System (0-10):
    - Trend Alignment: All 3 TFs must agree on direction
    - Momentum: RSI levels and MACD alignment
    - Volume: Volume confirmation
    - Structure: EMA stack alignment
    
    Minimum score to pass: Configurable (default 6.0)
    """
    
    # Default thresholds
    DEFAULT_MIN_SCORE = 6.0
    PERFECT_ALIGNMENT_BONUS = 2.0
    
    def __init__(self, min_score: float = None):
        """
        Initialize MTF filter.
        
        Args:
            min_score: Minimum confluence score to pass (0-10). Default: 6.0
        """
        self.min_score = min_score or self.DEFAULT_MIN_SCORE
    
    def _get_trend(self, df: pd.DataFrame) -> TrendDirection:
        """
        Determine trend direction from a dataframe.
        Uses EMA20 vs EMA50 crossover.
        """
        if df.empty or len(df) < 50:
            return TrendDirection.NEUTRAL
        
        try:
            ema20 = df['ema20'].iloc[-1] if 'ema20' in df.columns else None
            ema50 = df['ema50'].iloc[-1] if 'ema50' in df.columns else None
            
            if ema20 is None or ema50 is None:
                return TrendDirection.NEUTRAL
            
            # Trend determination
            if ema20 > ema50 * 1.002:  # 0.2% buffer
                return TrendDirection.BULLISH
            elif ema50 > ema20 * 1.002:
                return TrendDirection.BEARISH
            else:
                return TrendDirection.NEUTRAL
        except Exception:
            return TrendDirection.NEUTRAL
    
    def _score_trend_alignment(self, micro: TrendDirection, main: TrendDirection, 
                               macro: TrendDirection) -> Tuple[float, str]:
        """
        Score trend alignment across timeframes.
        Perfect alignment = 10, partial = 5-7, conflict = 0-3
        """
        trends = [micro, main, macro]
        
        # Count bullish and bearish
        bullish_count = sum(1 for t in trends if t == TrendDirection.BULLISH)
        bearish_count = sum(1 for t in trends if t == TrendDirection.BEARISH)
        neutral_count = sum(1 for t in trends if t == TrendDirection.NEUTRAL)
        
        # Perfect alignment (all same direction, not neutral)
        if bullish_count == 3:
            return 10.0, "✅ Perfect bullish alignment"
        if bearish_count == 3:
            return 10.0, "✅ Perfect bearish alignment"
        
        # Strong alignment (2/3 agree, macro not conflicting)
        if bullish_count == 2 and macro == TrendDirection.BULLISH:
            return 8.0, "📈 Strong bullish (2/3 + macro)"
        if bearish_count == 2 and macro == TrendDirection.BEARISH:
            return 8.0, "📉 Strong bearish (2/3 + macro)"
        
        # Moderate alignment (2/3 agree)
        if bullish_count == 2:
            return 6.0, "Moderate bullish (2/3)"
        if bearish_count == 2:
            return 6.0, "Moderate bearish (2/3)"
        
        # Weak/conflicting
        if neutral_count >= 2:
            return 4.0, "⚠️ No clear trend (neutral)"
        
        # Conflict (1 bullish, 1 bearish, 1 neutral or similar)
        return 2.0, "❌ Conflicting trends"
    
    def _score_momentum(self, df_main: pd.DataFrame, df_macro: pd.DataFrame) -> float:
        """
        Score momentum alignment using RSI and MACD.
        """
        score = 5.0  # Start neutral
        
        try:
            # Main timeframe RSI
            if 'rsi' in df_main.columns and not df_main['rsi'].empty:
                rsi_main = df_main['rsi'].iloc[-1]
                
                # Avoid extremes (overbought/oversold)
                if 30 < rsi_main < 70:
                    score += 1.5
                elif 40 < rsi_main < 60:
                    score += 0.5  # Extra for mid-range
                elif rsi_main <= 30 or rsi_main >= 70:
                    score -= 1.0  # Extreme RSI penalty
            
            # MACD alignment
            if 'macd' in df_main.columns and 'macd_signal' in df_main.columns:
                macd = df_main['macd'].iloc[-1]
                signal = df_main['macd_signal'].iloc[-1]
                
                # MACD above signal = bullish momentum
                if macd > signal:
                    score += 1.0
                
                # Macro MACD confirmation
                if 'macd' in df_macro.columns and 'macd_signal' in df_macro.columns:
                    macd_macro = df_macro['macd'].iloc[-1]
                    signal_macro = df_macro['macd_signal'].iloc[-1]
                    
                    # Aligned momentum
                    if (macd > signal and macd_macro > signal_macro) or \
                       (macd < signal and macd_macro < signal_macro):
                        score += 1.5
        except Exception:
            pass
        
        return min(10.0, max(0.0, score))
    
    def _score_volume(self, df_main: pd.DataFrame) -> float:
        """
        Score volume confirmation.
        """
        score = 5.0
        
        try:
            if 'volume' not in df_main.columns or df_main['volume'].empty:
                return score
            
            current_vol = df_main['volume'].iloc[-1]
            avg_vol = df_main['volume'].rolling(20).mean().iloc[-1]
            
            if avg_vol > 0:
                vol_ratio = current_vol / avg_vol
                
                # Good volume (1.0-2.0x average)
                if 1.0 <= vol_ratio <= 2.0:
                    score += 2.0
                # Exceptional volume
                elif vol_ratio > 2.0:
                    score += 3.0
                # Low volume (weak signal)
                elif vol_ratio < 0.5:
                    score -= 2.0
        except Exception:
            pass
        
        return min(10.0, max(0.0, score))
    
    def _score_structure(self, df_main: pd.DataFrame) -> float:
        """
        Score price structure (EMA stack alignment).
        """
        score = 5.0
        
        try:
            if not all(col in df_main.columns for col in ['ema20', 'ema50', 'ema100']):
                # Try with ema200 if ema100 not available
                if not all(col in df_main.columns for col in ['ema20', 'ema50', 'ema200']):
                    return score
                ema_long = df_main['ema200'].iloc[-1]
            else:
                ema_long = df_main['ema100'].iloc[-1]
            
            ema20 = df_main['ema20'].iloc[-1]
            ema50 = df_main['ema50'].iloc[-1]
            close = df_main['close'].iloc[-1]
            
            # Bullish stack: Price > EMA20 > EMA50 > EMA100/200
            if close > ema20 > ema50 > ema_long:
                score = 9.0
            # Bearish stack: Price < EMA20 < EMA50 < EMA100/200
            elif close < ema20 < ema50 < ema_long:
                score = 9.0
            # Partial alignment
            elif (close > ema20 > ema50) or (close < ema20 < ema50):
                score = 7.0
            # Price respecting EMA20
            elif (close > ema20 and ema20 > ema50) or (close < ema20 and ema20 < ema50):
                score = 6.0
        except Exception:
            pass
        
        return min(10.0, max(0.0, score))
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> MTFAnalysis:
        """
        Perform full MTF confluence analysis.
        
        Args:
            symbol: Trading symbol
            data: Dict with 'main', 'macro', 'micro' keys from get_multiframe_candles
            
        Returns:
            MTFAnalysis with scores and filter decision
        """
        # Extract dataframes
        df_micro = data.get('micro', {}).get('dataframe', pd.DataFrame())
        df_main = data.get('main', {}).get('dataframe', pd.DataFrame())
        df_macro = data.get('macro', {}).get('dataframe', pd.DataFrame())
        
        # Determine trends
        micro_trend = self._get_trend(df_micro)
        main_trend = self._get_trend(df_main)
        macro_trend = self._get_trend(df_macro)
        
        # Calculate individual scores
        trend_score, trend_reason = self._score_trend_alignment(micro_trend, main_trend, macro_trend)
        momentum_score = self._score_momentum(df_main, df_macro)
        volume_score = self._score_volume(df_main)
        structure_score = self._score_structure(df_main)
        
        # Weighted confluence score
        # Trend alignment is most important (40%), then structure (25%), momentum (20%), volume (15%)
        confluence = (
            trend_score * 0.40 +
            structure_score * 0.25 +
            momentum_score * 0.20 +
            volume_score * 0.15
        )
        
        # Perfect alignment bonus
        if trend_score >= 9.5:
            confluence = min(10.0, confluence + self.PERFECT_ALIGNMENT_BONUS)
        
        # Determine if passed
        passed = confluence >= self.min_score
        
        # Generate reason
        if passed:
            reason = f"✅ Confluence {confluence:.1f}/10 (min: {self.min_score})"
        else:
            reason = f"❌ Low confluence {confluence:.1f}/10 (need {self.min_score}). {trend_reason}"
        
        return MTFAnalysis(
            symbol=symbol,
            micro_trend=micro_trend,
            main_trend=main_trend,
            macro_trend=macro_trend,
            trend_alignment_score=trend_score,
            momentum_score=momentum_score,
            volume_score=volume_score,
            structure_score=structure_score,
            confluence_score=round(confluence, 2),
            passed=passed,
            reason=reason
        )
    
    def should_trade(self, symbol: str, data: Dict[str, Any], 
                     signal_direction: str) -> Tuple[bool, MTFAnalysis]:
        """
        Check if a signal should be executed based on MTF confluence.
        
        Args:
            symbol: Trading symbol
            data: Multi-timeframe data from get_multiframe_candles
            signal_direction: 'BUY' or 'SELL' from strategy
            
        Returns:
            (should_execute: bool, analysis: MTFAnalysis)
        """
        analysis = self.analyze(symbol, data)
        
        # First check: Confluence score
        if not analysis.passed:
            return False, analysis
        
        # Second check: Direction alignment
        expected_trend = TrendDirection.BULLISH if signal_direction.upper() == 'BUY' else TrendDirection.BEARISH
        
        # Macro trend must align with signal direction
        if analysis.macro_trend != expected_trend and analysis.macro_trend != TrendDirection.NEUTRAL:
            analysis.passed = False
            analysis.reason = f"❌ Signal {signal_direction} conflicts with macro trend ({analysis.macro_trend.value})"
            return False, analysis
        
        return True, analysis


# Singleton instance
_mtf_filter: Optional[MTFConfluenceFilter] = None

def get_mtf_filter(min_score: float = None) -> MTFConfluenceFilter:
    """Get singleton MTF filter instance."""
    global _mtf_filter
    if _mtf_filter is None:
        _mtf_filter = MTFConfluenceFilter(min_score)
    return _mtf_filter


def check_mtf_confluence(symbol: str, data: Dict[str, Any], 
                         signal_direction: str, min_score: float = 6.0) -> Tuple[bool, str, float]:
    """
    Convenience function to check MTF confluence.
    
    Returns:
        (passed: bool, reason: str, score: float)
    """
    filter_instance = MTFConfluenceFilter(min_score)
    should_trade, analysis = filter_instance.should_trade(symbol, data, signal_direction)
    return should_trade, analysis.reason, analysis.confluence_score
