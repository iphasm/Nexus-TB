class RiskManager:
    """
    The Guardian: Centralized Risk System.
    """
    def __init__(self, max_portfolio_exposure: float = 0.5):
        self.max_exposure = max_portfolio_exposure
        self.active_positions = {}
        self.portfolio_correlation = 0.0

    async def check_trade_approval(self, signal, current_exposure: float) -> bool:
        """
        Gatekeeper for new trades.
        """
        # 1. Global Exposure Limit
        if current_exposure >= self.max_exposure:
            print(f"🚫 Trade Rejected: Max Exposure ({self.max_exposure}) Reached.")
            return False
            
        # 2. Correlation Guard (Stub)
        if self.portfolio_correlation > 0.8 and signal.action == 'BUY':
             print(f"🚫 Trade Rejected: Portfolio too correlated ({self.portfolio_correlation}).")
             return False
             
        return True

    def calculate_real_breakeven(self, entry_price: float, fee_rate: float = 0.001, slippage: float = 0.0005) -> float:
        """
        Calculates the TRUE price to exit without loss.
        Includes Entry Fee + Exit Fee + Slippage Estimate.
        """
        # Fee is paid on Notional (Price * Size). Roughly 2x fee rate for roundtrip.
        total_friction = (fee_rate * 2) + slippage
        breakeven_price = entry_price * (1 + total_friction)
        return breakeven_price

    def check_market_health(self, market_data: dict) -> str:
        """
        Sentinel Core Logic: Determines Global Market State.
        Returns: 'NORMAL', 'BLACK_SWAN', or 'SHARK_CONTEXT'
        """
        # We need BTC context. If this asset IS BTC, we check it.
        # If not, we should ideally have global context passed in.
        # For now, we assume this is called for every asset, but the Engine 
        # should pass BTC data or we check if symbol='BTCUSDT'.
        
        symbol = market_data.get('symbol', '')
        if 'BTC' not in symbol:
            # If we are analyzing an Altcoin, we rely on cached global state 
            # or we skip (Engine handles global checks)
            return 'NORMAL'
            
        df = market_data.get('dataframe')
        if df is None or df.empty: return 'NORMAL'
        
        last = df.iloc[-1]
        open_price = last.get('open', 0)
        close_price = last.get('close', 0)
        
        if open_price == 0: return 'NORMAL'
        
        pct_change = (close_price - open_price) / open_price
        
        # 1. BLACK SWAN CHECK (Crash > 4% in current candle)
        # This is a panic triggers
        if pct_change < -0.04:
            return 'BLACK_SWAN'
            
        # 2. SHARK CONTEXT CHECK
        # BTC Dominance logic usually requires external data (BTC.D chart).
        # Proxy: If BTC is stable/down small (-1% to -3%) but Alts are bleeding?
        # For now, we define Shark Context as "BTC Bearish but not Crash"
        if -0.04 < pct_change < -0.01:
            return 'SHARK_CONTEXT'
            
        return 'NORMAL'

    async def get_override_action(self, symbol: str, market_data: dict) -> str:
        """
        Returns authoritative override command:
        - 'BLACK_SWAN': Force Exit Longs, Pause Buying.
        - 'SHARK_MODE': Force Shark Strategy (Shorts).
        - None: Normal Operation.
        """
        # 1. Check Global Health (if symbol is BTC)
        # In a real system, we'd have a 'GlobalState' singleton.
        # Here we check per-asset if it is BTC to set the flag, 
        # but for Alts we need to know that flag.
        # Limitation: We need the Engine to pass Global State or we estimate.
        
        # IMPROVEMENT: The Engine should call check_market_health on BTC 
        # and pass the result to Alts.
        # For now, we implement the logic assuming the Engine orchestrates it.
        
        # Local Check (Self-contained for this asset)
        df = market_data.get('dataframe')
        if df is None or df.empty: return None
        
        last = df.iloc[-1]
        pct = (last['close'] - last['open']) / last['open'] if last['open'] > 0 else 0
        
        # Individual Black Swan (Flash Crash on generic asset)
        if pct < -0.05: # 5% flash crash on any asset
            return 'BLACK_SWAN'
            
        return None

