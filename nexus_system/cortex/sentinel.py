from typing import Dict, Any
from .base import IStrategy, Signal

class SentinelStrategy(IStrategy):
    """
    Sentinel: The Guardian & The Hunter.
    
    Modes:
    1. BLACK SWAN (Defensive):
       - Trigger: BTC crashes > 4% in 15m.
       - Action: FORCE EXIT ALL LONGS. Prevent new Longs.
       
    2. SHARK MODE (Offensive):
       - Trigger: Bearish Momentum (Sangria).
       - Action: Aggressive Shorts on vulnerable assets.
    """

    @property
    def name(self) -> str:
        return "Sentinel"

    async def analyze(self, market_data: Dict[str, Any]) -> Signal:
        """
        Sentinel Analysis.
        Reads 'sentinel_mode' from metadata or detects it.
        """
        mode = market_data.get('sentinel_mode', 'NORMAL')
        df = market_data.get('dataframe')
        symbol = market_data.get('symbol', 'UNKNOWN')
        
        # --- MODE 1: BLACK SWAN (Defense) ---
        if mode == 'BLACK_SWAN':
            # Priority 1: Protect Capital
            return Signal(
                symbol=symbol,
                action="EXIT_LONG", # Close Longs immediately
                confidence=1.0,
                price=0,
                metadata={'reason': 'BLACK_SWAN_PROTOCOL', 'strategy': 'Sentinel'}
            )

        # --- MODE 2: SHARK (Offense) ---
        # Only analyze if explicitly in Shark Mode or forced check
        if mode == 'SHARK_MODE':
            if df is None or df.empty or len(df) < 50: return None
            
            current = df.iloc[-1]
            price = current['close']
            ema_50 = current.get('ema_50', 0)
            ema_200 = current.get('ema_200', 0)
            adx = current.get('adx', 0)
            rsi = current.get('rsi', 50)
            atr = current.get('atr', 0)
            
            # Shark Entry Logic (Strict Bearish)
            is_bear_structure = price < ema_50 < ema_200
            is_valid_momentum = (adx > 25) and (20 < rsi < 50)
            
            if is_bear_structure and is_valid_momentum:
                # Confidence scales with ADX
                confidence = min(0.7 + (adx / 100), 0.95)
                
                return Signal(
                    symbol=symbol,
                    action="SELL",
                    confidence=confidence,
                    price=price,
                    metadata={
                        "strategy": "Sentinel (Shark)",
                        "adx": adx,
                        "rsi": rsi,
                        "sub_mode": "SHARK_HUNT",
                        "atr": atr
                    }
                )
                
        return None

    def calculate_entry_params(self, signal: Signal, wallet_balance: float, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Sentinel Parameters with Dynamic Risk Management:
        - Black Swan: N/A (Exits don't use this).
        - Shark: Aggressive Shorting with adaptive TP/SL.
        """
        cfg = config or {}
        lev = cfg.get('leverage', 7)
        size_pct = cfg.get('max_capital_pct', 0.08)

        price = signal.price
        atr = signal.metadata.get('atr', price * 0.02)
        adx = signal.metadata.get('adx', 25)
        rsi = signal.metadata.get('rsi', 50)

        # Dynamic position sizing based on signal strength
        # Higher ADX = stronger trend = larger position
        adx_multiplier = min(max(adx / 25, 0.5), 2.0)  # 0.5x to 2.0x
        dynamic_size_pct = size_pct * adx_multiplier

        # Dynamic leverage based on volatility (ATR)
        # Higher ATR = higher volatility = lower leverage
        volatility_factor = min(max(atr / price, 0.005), 0.05)  # 0.5% to 5%
        volatility_multiplier = 1 / (1 + volatility_factor * 10)  # Reduce leverage with volatility
        dynamic_leverage = max(int(lev * volatility_multiplier), 1)

        # Dynamic Take Profit based on signal strength and market conditions
        base_tp_distance = atr * 3.0  # Base: 3 ATR

        # Adjust TP based on ADX (stronger signal = larger target)
        adx_tp_multiplier = 1 + (adx - 25) / 100  # +1% per ADX point above 25
        tp_distance = base_tp_distance * adx_tp_multiplier

        # Adjust TP based on RSI (oversold = larger potential bounce)
        rsi_tp_multiplier = 1 + (30 - rsi) / 100 if rsi < 30 else 1.0
        final_tp_distance = tp_distance * rsi_tp_multiplier

        # Dynamic Stop Loss (tighter for stronger signals)
        sl_distance = atr * 1.5  # Base: 1.5 ATR
        sl_multiplier = 1 / adx_tp_multiplier  # Tighter SL for stronger signals
        final_sl_distance = sl_distance * sl_multiplier

        return {
            "leverage": dynamic_leverage,
            "size_pct": min(dynamic_size_pct, 0.15),  # Cap at 15%
            "stop_loss_price": price + final_sl_distance,
            "take_profit_price": price - final_tp_distance,
            "metadata": {
                "dynamic_leverage": f"{lev} → {dynamic_leverage}",
                "dynamic_size": f"{size_pct:.1%} → {dynamic_size_pct:.1%}",
                "adx_multiplier": f"{adx_tp_multiplier:.2f}",
                "volatility_factor": f"{volatility_factor:.1%}",
                "tp_distance": f"${final_tp_distance:.2f}",
                "sl_distance": f"${final_sl_distance:.2f}"
            }
        }
