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
        Sentinel Parameters:
        - Black Swan: N/A (Exits don't use this).
        - Shark: Aggressive Shorting.
        """
        cfg = config or {}
        lev = cfg.get('leverage', 7)
        size_pct = cfg.get('max_capital_pct', 0.08)
        
        price = signal.price
        atr = signal.metadata.get('atr', price * 0.02)
        
        return {
            "leverage": lev, 
            "size_pct": size_pct,
            "stop_loss_price": price + (atr * 2.0), # Trailing style room
            "take_profit_price": price - (atr * 4.0) # Target deeper flush
        }
