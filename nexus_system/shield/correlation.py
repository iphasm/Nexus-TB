import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class CorrelationManager:
    """
    Shield 2.0: Portfolio Correlation Guard.
    Prevents over-concentration in highly correlated assets.
    """
    def __init__(self, max_correlation: float = 0.85, window_size: int = 50):
        self.max_correlation = max_correlation
        self.window_size = window_size
        # Cache of price history for active references: {symbol: pd.Series(prices)}
        self.price_history: Dict[str, pd.Series] = {}

    def update_price_history(self, symbol: str, prices: pd.Series):
        """
        Updates the price history for a symbol. 
        Should be called periodically or when a position is opened.
        Efficiently stores only the necessary window size.
        """
        if prices.empty: return
        # Store only the last N closing prices
        self.price_history[symbol] = prices.iloc[-self.window_size:].copy()

    def check_correlation(self, candidate_symbol: str, candidate_prices: pd.Series, active_positions: List[str]) -> bool:
        """
        Checks if the candidate symbol is too correlated with any CURRENTLY ACTIVE position.
        Returns:
            True if Safe (Correlation < Threshold)
            False if Unsafe (Correlation > Threshold)
        """
        # If no active positions, it's always safe (unless we check against a benchmark, but here strict portfolio risk)
        if not active_positions:
            return True
            
        # Ensure we have the candidate's history
        self.update_price_history(candidate_symbol, candidate_prices)
        candidate_series = self.price_history.get(candidate_symbol)
        
        if candidate_series is None or len(candidate_series) < self.window_size * 0.8:
            # Not enough data to judge correlation, defaulting to Safe (or Strict? Defaulting Safe for availability)
            return True

        for position_symbol in active_positions:
            # Skip self if checking re-entry? (Assuming distinct symbols)
            if position_symbol == candidate_symbol: continue
            
            existing_series = self.price_history.get(position_symbol)
            if existing_series is None:
                # We might miss data if not initialized. 
                # Ideally, RiskManager calls update_price_history for all active positions regularly.
                continue
                
            # Align indices and compute returns (log-returns for better correlation)
            # In a live stream, sizes might differ slightly.
            # We align by taking the common length from the end.
            min_len = min(len(candidate_series), len(existing_series))
            s1_prices = candidate_series.iloc[-min_len:]
            s2_prices = existing_series.iloc[-min_len:]

            # Compute log-returns for better correlation analysis
            s1_returns = np.log(s1_prices / s1_prices.shift(1)).dropna()
            s2_returns = np.log(s2_prices / s2_prices.shift(1)).dropna()

            # Ensure we have enough data points
            if len(s1_returns) < 10 or len(s2_returns) < 10:
                continue  # Skip if insufficient return data

            # Compute Correlation on returns
            corr = s1_returns.corr(s2_returns)
            
            if corr > self.max_correlation:
                print(f"🚫 Shield Alert: {candidate_symbol} is {corr:.2f} correlated with active position {position_symbol}.")
                return False # UNSAFE
                
        return True # SAFE
