from typing import Dict, Any
from .base import IStrategy, Signal

class GridTradingStrategy(IStrategy):
    """
    Dynamic Grid Strategy (v0.0)
    
    Logic:
    - Uses EMA 200 as the "Mean" (Center of Grid).
    - Uses ATR to define dynamic Grid Levels (Volatility Bands).
    - ENTRY: Price deviates significantly from Mean (> 2 * ATR).
        - Buy Low (Below Lower Band)
        - Sell High (Above Upper Band)
    - EXIT: Price returns towards Mean (or slight overshoot).
    
    This is a Stateless "Grid" that adapts to market volatility and trend.
    """
    
    def __init__(self, ema_period=200, atr_multiplier_entry=2.0, atr_multiplier_exit=0.5):
        self.ema_period = ema_period
        self.entry_mult = atr_multiplier_entry
        self.exit_mult = atr_multiplier_exit

    @property
    def name(self) -> str:
        return "Grid Trading"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Analyze market for Grid Entry signals based on Mean Reversion.
        """
        df = market_data.get('dataframe')
        if df is None or df.empty: return None
        
        # Ensure sufficient data
        if len(df) < self.ema_period:
            return None
            
        current = df.iloc[-1]
        
        # 1. Get Indicators
        price = current['close']
        ema_mean = current.get(f'ema_{self.ema_period}')
        atr = current.get('atr')
        
        # Safety: Indicators must exist
        if not ema_mean or not atr:
            return None
            
        # 2. Calculate Dynamic Grid Levels
        upper_band = ema_mean + (self.entry_mult * atr)
        lower_band = ema_mean - (self.entry_mult * atr)
        
        # 3. Logic: Fade the Move (Counter-Trend Entry)
        signal_type = "HOLD"
        confidence = 0.0
        meta = {}
        
        # BUY Logic: Price is "Too Low" (Below Lower Band)
        if price < lower_band:
            signal_type = "BUY"
            # Higher confidence if further away
            dist_sigma = (lower_band - price) / atr
            confidence = min(0.6 + (dist_sigma * 0.1), 0.95)
            meta = {
                "grid_dist": f"{dist_sigma:.2f}σ", 
                "band": lower_band
            }
            
        # SELL Logic: Price is "Too High" (Above Upper Band)
        elif price > upper_band:
            signal_type = "SELL"
            dist_sigma = (price - upper_band) / atr
            confidence = min(0.6 + (dist_sigma * 0.1), 0.95)
            meta = {
                "grid_dist": f"{dist_sigma:.2f}σ", 
                "band": upper_band
            }
        
        # Return None for HOLD
        if signal_type == "HOLD":
            return None
            
        # Attach ATR for risk calc
        meta['atr'] = atr
            
        return Signal(
            symbol=market_data.get('symbol', "UNKNOWN"),
            action=signal_type,
            confidence=confidence,
            price=price,
            metadata=meta
        )

    def calculate_entry_params(self, signal: Signal, wallet_balance: float, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Grid Risk Management:
        - Conservatively sized (High probability of mean reversion, but "catching a knife" risk).
        - Wide Stop Loss to allow for noise.
        """
        # Safe Config Get
        cfg = config or {}
        lev = cfg.get('leverage', 3)
        size_pct = cfg.get('max_capital_pct', 0.05)
        
        price = signal.price
        atr = signal.metadata.get('atr', price * 0.01)
        
        # Wide Stop Loss (4x ATR)
        sl_dist = atr * 4.0
        
        if signal.action == "BUY":
            sl_price = price - sl_dist
            # TP Target: Return to Mean (EMA) or slightly past it.
            # Ideally TP is dynamic, but for entry params we set a fixed target based on risk/reward
            # Here we target the Mean. Since we don't have Mean here, we guess approx 2x ATR back?
            # Better: Target 2x ATR profit (Risk 1:0.5 or 1:1 depending on entry quality)
            tp_price = price + (atr * 2.5) 
        else:
            sl_price = price + sl_dist
            tp_price = price - (atr * 2.5)
            
        return {
            "leverage": lev, # Conservative leverage for Mean Reversion
            "size_pct": size_pct, # 5% per grid trade
            "stop_loss_price": sl_price,
            "take_profit_price": tp_price
        }

