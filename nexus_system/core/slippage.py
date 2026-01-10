"""
Dynamic Slippage Model - Realistic Trade Execution Simulation
Accounts for order size, liquidity, volatility, and exchange-specific behavior.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Exchange(Enum):
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    ALPACA = "ALPACA"


@dataclass
class SlippageResult:
    """Result of slippage calculation."""
    base_slippage_pct: float
    size_impact_pct: float
    volatility_impact_pct: float
    total_slippage_pct: float
    expected_fill_price: float
    worst_case_price: float
    
    @property
    def total_cost(self) -> float:
        """Total slippage as a percentage."""
        return self.total_slippage_pct


class DynamicSlippage:
    """
    Dynamic Slippage Calculator.
    
    Factors considered:
    1. Exchange base slippage (maker/taker fees proxy)
    2. Order size relative to average volume (market impact)
    3. Current volatility (ATR-based)
    4. Order type (market vs limit)
    5. Time of day (optional: lower liquidity during off-hours)
    """
    
    # Base slippage per exchange (includes typical spread + partial fills)
    EXCHANGE_BASE_SLIPPAGE = {
        Exchange.BINANCE: 0.0005,   # 0.05% - Very liquid
        Exchange.BYBIT: 0.0006,     # 0.06% - Slightly less liquid
        Exchange.ALPACA: 0.0008,    # 0.08% - Stock markets, wider spreads
    }
    
    # Impact multipliers for order size
    SIZE_IMPACT_BRACKETS = [
        # (max_size_pct_of_volume, impact_multiplier)
        (0.001, 0.0),      # < 0.1% of volume: negligible impact
        (0.005, 0.0002),   # 0.1-0.5%: small impact
        (0.01, 0.0005),    # 0.5-1%: moderate impact
        (0.02, 0.001),     # 1-2%: noticeable impact
        (0.05, 0.003),     # 2-5%: significant impact
        (float('inf'), 0.01)  # >5%: severe impact
    ]
    
    def __init__(self, default_volume_24h: float = 1_000_000):
        """
        Initialize with default 24h volume assumption.
        
        Args:
            default_volume_24h: Default 24h volume in USD for symbols without data
        """
        self.default_volume_24h = default_volume_24h
        self.volume_cache: Dict[str, float] = {}
    
    def set_volume(self, symbol: str, volume_24h: float):
        """Cache 24h volume for a symbol."""
        self.volume_cache[symbol] = volume_24h
    
    def get_volume(self, symbol: str) -> float:
        """Get cached volume or return default."""
        return self.volume_cache.get(symbol, self.default_volume_24h)
    
    def calculate_size_impact(self, order_size_usd: float, volume_24h: float) -> float:
        """
        Calculate market impact based on order size.
        
        Larger orders relative to volume cause more slippage.
        """
        if volume_24h <= 0:
            volume_24h = self.default_volume_24h
        
        size_ratio = order_size_usd / volume_24h
        
        for max_ratio, impact in self.SIZE_IMPACT_BRACKETS:
            if size_ratio <= max_ratio:
                return impact
        
        # Fallback for very large orders
        return 0.01
    
    def calculate_volatility_impact(self, atr: float, price: float) -> float:
        """
        Calculate volatility impact.
        
        Higher ATR relative to price = more potential slippage.
        """
        if price <= 0:
            return 0.0
        
        atr_pct = atr / price
        
        # Normalized volatility impact
        # Low vol (< 1%): minimal impact
        # Medium vol (1-3%): moderate impact
        # High vol (> 3%): significant impact
        
        if atr_pct < 0.01:
            return 0.0001
        elif atr_pct < 0.02:
            return 0.0003
        elif atr_pct < 0.03:
            return 0.0005
        elif atr_pct < 0.05:
            return 0.001
        else:
            return 0.002
    
    def calculate(
        self,
        symbol: str,
        price: float,
        order_size_usd: float,
        side: str,  # 'BUY' or 'SELL'
        exchange: str = "BINANCE",
        atr: float = None,
        volume_24h: float = None,
        is_market_order: bool = True
    ) -> SlippageResult:
        """
        Calculate expected slippage for an order.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            price: Current market price
            order_size_usd: Order size in USD
            side: 'BUY' or 'SELL'
            exchange: Exchange name
            atr: Average True Range (volatility indicator)
            volume_24h: 24h trading volume in USD
            is_market_order: True for market orders, False for limit
            
        Returns:
            SlippageResult with detailed breakdown
        """
        # Resolve exchange enum
        try:
            exchange_enum = Exchange[exchange.upper()]
        except KeyError:
            exchange_enum = Exchange.BINANCE
        
        # 1. Base slippage
        base_slippage = self.EXCHANGE_BASE_SLIPPAGE.get(exchange_enum, 0.0005)
        
        # Limit orders have less slippage (assuming fill)
        if not is_market_order:
            base_slippage *= 0.3
        
        # 2. Size impact
        vol = volume_24h if volume_24h else self.get_volume(symbol)
        size_impact = self.calculate_size_impact(order_size_usd, vol)
        
        # 3. Volatility impact
        if atr and price > 0:
            vol_impact = self.calculate_volatility_impact(atr, price)
        else:
            vol_impact = 0.0002  # Default small volatility impact
        
        # 4. Total slippage
        total_slippage = base_slippage + size_impact + vol_impact
        
        # 5. Calculate expected fill prices
        if side.upper() == 'BUY':
            expected_fill = price * (1 + total_slippage)
            worst_case = price * (1 + total_slippage * 2)  # 2x slippage worst case
        else:  # SELL
            expected_fill = price * (1 - total_slippage)
            worst_case = price * (1 - total_slippage * 2)
        
        return SlippageResult(
            base_slippage_pct=round(base_slippage * 100, 4),
            size_impact_pct=round(size_impact * 100, 4),
            volatility_impact_pct=round(vol_impact * 100, 4),
            total_slippage_pct=round(total_slippage * 100, 4),
            expected_fill_price=round(expected_fill, 8),
            worst_case_price=round(worst_case, 8)
        )
    
    def estimate_execution_cost(
        self,
        symbol: str,
        price: float,
        quantity: float,
        side: str,
        exchange: str = "BINANCE",
        atr: float = None,
        volume_24h: float = None,
        fee_rate: float = 0.001  # 0.1% maker/taker fee
    ) -> Dict[str, float]:
        """
        Estimate total execution cost including fees and slippage.
        
        Returns dict with:
        - slippage_cost: Expected slippage in USD
        - fee_cost: Exchange fee in USD
        - total_cost: Combined cost in USD
        - total_cost_pct: Combined cost as percentage
        """
        order_size_usd = price * quantity
        
        slippage = self.calculate(
            symbol=symbol,
            price=price,
            order_size_usd=order_size_usd,
            side=side,
            exchange=exchange,
            atr=atr,
            volume_24h=volume_24h
        )
        
        slippage_cost = order_size_usd * (slippage.total_slippage_pct / 100)
        fee_cost = order_size_usd * fee_rate
        total_cost = slippage_cost + fee_cost
        
        return {
            'slippage_cost': round(slippage_cost, 4),
            'fee_cost': round(fee_cost, 4),
            'total_cost': round(total_cost, 4),
            'total_cost_pct': round((total_cost / order_size_usd) * 100, 4) if order_size_usd > 0 else 0,
            'slippage_pct': slippage.total_slippage_pct,
            'expected_fill': slippage.expected_fill_price
        }


# Singleton instance
_slippage_model: Optional[DynamicSlippage] = None

def get_slippage_model() -> DynamicSlippage:
    """Get singleton DynamicSlippage instance."""
    global _slippage_model
    if _slippage_model is None:
        _slippage_model = DynamicSlippage()
    return _slippage_model


# Convenience function for trading_manager integration
def estimate_slippage(
    symbol: str,
    price: float,
    order_size_usd: float,
    side: str,
    exchange: str = "BINANCE",
    atr: float = None
) -> float:
    """
    Quick slippage estimate.
    Returns expected slippage as a decimal (0.001 = 0.1%).
    """
    model = get_slippage_model()
    result = model.calculate(
        symbol=symbol,
        price=price,
        order_size_usd=order_size_usd,
        side=side,
        exchange=exchange,
        atr=atr
    )
    return result.total_slippage_pct / 100
