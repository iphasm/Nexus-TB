class RiskManager:
    """
    The Guardian: Centralized Risk System.
    """
    def __init__(self, max_portfolio_exposure: float = 0.5):
        self.max_exposure = max_portfolio_exposure
        self.active_positions = {}
        self.portfolio_correlation = 0.0
        # Global State (Driven by BTC)
        self.global_state = 'NORMAL'
        self.last_btc_price = 0.0
        
        # Macro Data (CMC)
        from ..uplink.cmc_client import CMCClient
        self.cmc_client = CMCClient()
        self.btc_dominance = 0.0
        self.total_cap = 0.0

    async def update_macro_health(self):
        """
        Polls CMC for Macro Data (Dominance/Cap).
        Called periodically by NexusCore background task.
        """
        metrics = await self.cmc_client.get_global_metrics()
        if metrics:
            self.btc_dominance = metrics.get('btc_dominance', 0)
            self.total_cap = metrics.get('total_market_cap', 0)
            
            # Smart Logic: If BTC Dominance is skyrocketing (>55% and rising)
            # It validates Shark Context even if BTC price drop is mild.
            if self.btc_dominance > 55.0 and self.global_state == 'NORMAL':
                # Weak Shark Context (Warning)
                pass

    async def check_trade_approval(self, signal, current_exposure: float) -> bool:
        """
        Gatekeeper for new trades.
        """
        # 0. Global State Check
        if self.global_state == 'BLACK_SWAN' and signal.action == 'BUY':
             print(f"🚫 Trade Rejected: BLACK SWAN Protocol Active.")
             return False
             
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
        """
        total_friction = (fee_rate * 2) + slippage
        breakeven_price = entry_price * (1 + total_friction)
        return breakeven_price

    def update_market_health(self, symbol: str, market_data: dict):
        """
        Updates Global Market Health based on BTC data ONLY.
        This runs 24/7 on every BTC tick/candle via NexusCore.
        """
        if 'BTC' not in symbol:
            return

        df = market_data.get('dataframe')
        if df is None or df.empty: return
        
        last = df.iloc[-1]
        open_price = last.get('open', 0)
        close_price = last.get('close', 0)
        
        if open_price == 0: return

        pct_change = (close_price - open_price) / open_price
        
        # 1. BLACK SWAN CHECK (Crash > 4% in current candle)
        if pct_change < -0.04:
            if self.global_state != 'BLACK_SWAN':
                print("🚨 BLACK SWAN DETECTED (BTC CRASH). SYSTEM LOCKDOWN.")
            self.global_state = 'BLACK_SWAN'
            return
            
        # 2. SHARK CONTEXT CHECK (Bearish but not crash: -1.5% to -4%)
        if -0.04 < pct_change < -0.015:
            self.global_state = 'SHARK_CONTEXT'
            return
            
        # 3. NORMAL
        self.global_state = 'NORMAL'

    async def get_override_action(self, symbol: str, market_data: dict) -> str:
        """
        Returns authoritative override command based on GLOBAL state + Local checks.
        """
        # 1. Update Global State (If this tick is BTC)
        # Efficient: Updates state in-place
        self.update_market_health(symbol, market_data)
        
        # 2. Return Logic based on Global State
        if self.global_state == 'BLACK_SWAN':
            return 'BLACK_SWAN'
            
        if self.global_state == 'SHARK_CONTEXT':
            # Check if this asset is a SHARK TARGET
            from system_directive import SHARK_TARGETS
            if symbol in SHARK_TARGETS:
                return 'SHARK_MODE'

        return None

