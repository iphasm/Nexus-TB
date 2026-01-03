"""
Yahoo Finance API Client for Nexus Core
Provides stock market data and correlation analysis.
"""

import asyncio
import time
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from ..utils.logger import get_logger

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

class YahooFinanceClient:
    """
    Yahoo Finance client for stock market data and correlation analysis.
    Used for enhanced portfolio optimization and risk management.
    """

    def __init__(self):
        self.logger = get_logger("YahooFinanceClient")
        if not YFINANCE_AVAILABLE:
            self.logger.error("❌ yfinance not installed. Run: pip install yfinance")
            raise ImportError("yfinance library required")

        # Cache for expensive operations
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def get_historical_data(self, symbols: List[str], period: str = "1y",
                                interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols.
        Used for correlation analysis and technical studies.
        """
        cache_key = f"historical_{'_'.join(symbols)}_{period}_{interval}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self._fetch_historical_data_sync, symbols, period, interval)

        self._set_cache(cache_key, data, ttl=1800)  # 30 min cache
        return data

    def _fetch_historical_data_sync(self, symbols: List[str], period: str, interval: str) -> Dict[str, pd.DataFrame]:
        """Synchronous method to fetch historical data."""
        data = {}

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)

                if not df.empty:
                    # Clean and standardize data
                    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                    df.columns = ['open', 'high', 'low', 'close', 'volume']
                    data[symbol] = df

                    self.logger.debug(f"✅ Fetched {len(df)} bars for {symbol}")
                else:
                    self.logger.warning(f"⚠️ No data available for {symbol}")

            except Exception as e:
                self.logger.error(f"❌ Error fetching {symbol}: {e}")
                continue

        return data

    async def get_correlations(self, symbols: List[str], period: str = "6mo") -> Dict[str, Any]:
        """
        Calculate correlation matrix for given symbols.
        Returns correlation coefficients and analysis.
        """
        if len(symbols) < 2:
            return {"error": "Need at least 2 symbols for correlation analysis"}

        cache_key = f"correlations_{'_'.join(sorted(symbols))}_{period}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        # Get historical data
        historical_data = await self.get_historical_data(symbols, period=period, interval="1d")

        if len(historical_data) < 2:
            return {"error": "Insufficient data for correlation analysis"}

        # Calculate correlations
        loop = asyncio.get_event_loop()
        correlations = await loop.run_in_executor(None, self._calculate_correlations_sync, historical_data)

        self._set_cache(cache_key, correlations, ttl=3600)  # 1 hour cache
        return correlations

    def _calculate_correlations_sync(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Synchronous correlation calculation."""
        try:
            # Combine all close prices into a single DataFrame
            close_prices = pd.DataFrame()

            for symbol, df in data_dict.items():
                if 'close' in df.columns and not df.empty:
                    close_prices[symbol] = df['close']

            # Remove NaN values
            close_prices = close_prices.dropna()

            if close_prices.empty or len(close_prices.columns) < 2:
                return {"error": "Insufficient clean data for correlation"}

            # Calculate correlation matrix
            corr_matrix = close_prices.corr()

            # Calculate average correlations for each symbol
            avg_correlations = {}
            for symbol in corr_matrix.columns:
                # Exclude self-correlation
                other_symbols = [s for s in corr_matrix.columns if s != symbol]
                if other_symbols:
                    avg_corr = corr_matrix.loc[symbol, other_symbols].mean()
                    avg_correlations[symbol] = round(avg_corr, 4)

            # Find most correlated pairs
            correlated_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    sym1 = corr_matrix.columns[i]
                    sym2 = corr_matrix.columns[j]
                    corr_value = corr_matrix.iloc[i, j]

                    if abs(corr_value) > 0.5:  # Only significant correlations
                        correlated_pairs.append({
                            'symbol1': sym1,
                            'symbol2': sym2,
                            'correlation': round(corr_value, 4),
                            'strength': 'high' if abs(corr_value) > 0.7 else 'moderate'
                        })

            # Sort by absolute correlation
            correlated_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)

            result = {
                'correlation_matrix': corr_matrix.round(4).to_dict(),
                'average_correlations': avg_correlations,
                'correlated_pairs': correlated_pairs[:10],  # Top 10 pairs
                'analysis_period': f"{len(close_prices)} trading days",
                'symbols_analyzed': list(corr_matrix.columns)
            }

            self.logger.info(f"✅ Calculated correlations for {len(corr_matrix.columns)} symbols")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating correlations: {e}")
            return {"error": str(e)}

    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get broad market overview including major indices.
        """
        major_indices = ['^GSPC', '^IXIC', '^DJI', '^VIX']  # S&P 500, Nasdaq, Dow, VIX

        cache_key = "market_overview"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        # Get recent data
        data = await self.get_historical_data(major_indices, period="5d", interval="1d")

        overview = {}
        for symbol, df in data.items():
            if not df.empty:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest

                overview[symbol] = {
                    'price': round(latest['close'], 2),
                    'change_pct': round(((latest['close'] - prev['close']) / prev['close']) * 100, 2),
                    'volume': int(latest['volume'])
                }

        self._set_cache(cache_key, overview, ttl=600)  # 10 min cache
        return overview

    async def get_sector_performance(self) -> Dict[str, Any]:
        """
        Get performance data for major market sectors.
        """
        sector_etfs = {
            'technology': 'QQQ',
            'healthcare': 'XLV',
            'financials': 'XLF',
            'energy': 'XLE',
            'consumer': 'XLY',
            'materials': 'XLB',
            'industrials': 'XLI',
            'utilities': 'XLU',
            'real_estate': 'XLRE',
            'communication': 'XLC'
        }

        cache_key = "sector_performance"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        symbols = list(sector_etfs.values())
        data = await self.get_historical_data(symbols, period="1mo", interval="1d")

        performance = {}
        for sector, symbol in sector_etfs.items():
            if symbol in data and not data[symbol].empty:
                df = data[symbol]
                start_price = df['close'].iloc[0]
                end_price = df['close'].iloc[-1]

                performance[sector] = {
                    'symbol': symbol,
                    'change_pct': round(((end_price - start_price) / start_price) * 100, 2),
                    'current_price': round(end_price, 2)
                }

        self._set_cache(cache_key, performance, ttl=1800)  # 30 min cache
        return performance

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self.cache:
            return False

        entry = self.cache[key]
        ttl = entry.get('ttl', self.cache_ttl)
        return (time.time() - entry['timestamp']) < ttl

    def _set_cache(self, key: str, data: Any, ttl: int = None):
        """Set cache entry with timestamp."""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl or self.cache_ttl
        }

    async def health_check(self) -> bool:
        """Simple health check."""
        try:
            data = await self.get_market_overview()
            return len(data) > 0
        except Exception:
            return False
