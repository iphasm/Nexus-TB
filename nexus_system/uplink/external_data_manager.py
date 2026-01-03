"""
External Data Manager - Unified API Client for Nexus Core
Integrates multiple external data sources for enhanced trading decisions.
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, List, Optional
from ..utils.logger import get_logger
import os

class ExternalDataManager:
    """
    Unified manager for external data sources.
    Coordinates data collection from multiple APIs for enhanced trading signals.
    """

    def __init__(self):
        self.logger = get_logger("ExternalDataManager")
        self.clients = {}
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes default

        # Initialize clients
        self._init_clients()

    def _init_clients(self):
        """Initialize all available API clients."""
        try:
            from .yahoo_client import YahooFinanceClient
            self.clients['yahoo'] = YahooFinanceClient()
            self.logger.info("✅ Yahoo Finance client initialized")
        except ImportError:
            self.logger.warning("⚠️ Yahoo Finance client not available")

        try:
            from .coingecko_client import CoinGeckoClient
            self.clients['coingecko'] = CoinGeckoClient()
            self.logger.info("✅ CoinGecko client initialized")
        except ImportError:
            self.logger.warning("⚠️ CoinGecko client not available")

        try:
            from .fred_client import FREDClient
            self.clients['fred'] = FREDClient()
            self.logger.info("✅ FRED client initialized")
        except ImportError:
            self.logger.warning("⚠️ FRED client not available")

        try:
            from .cryptopanic_client import CryptoPanicClient
            self.clients['cryptopanic'] = CryptoPanicClient()
            self.logger.info("✅ CryptoPanic client initialized")
        except ImportError:
            self.logger.warning("⚠️ CryptoPanic client not available")

        try:
            from .reddit_client import RedditClient
            self.clients['reddit'] = RedditClient()
            self.logger.info("✅ Reddit client initialized")
        except ImportError:
            self.logger.warning("⚠️ Reddit client not available")

        try:
            from .defillama_client import DefiLlamaClient
            self.clients['defillama'] = DefiLlamaClient()
            self.logger.info("✅ DefiLlama client initialized")
        except ImportError:
            self.logger.warning("⚠️ DefiLlama client not available")

    async def get_market_correlations(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get correlations between assets using Yahoo Finance data.
        Used for enhanced portfolio optimization and risk management.
        """
        if 'yahoo' not in self.clients:
            return {}

        cache_key = f"correlations_{'_'.join(sorted(symbols))}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            correlations = await self.clients['yahoo'].get_correlations(symbols)
            self._set_cache(cache_key, correlations)
            return correlations
        except Exception as e:
            self.logger.error(f"Error fetching correlations: {e}")
            return {}

    async def get_crypto_market_data(self, limit: int = 100) -> List[Dict]:
        """
        Get comprehensive crypto market data from CoinGecko.
        Used for filtering tradable assets and market cap analysis.
        """
        if 'coingecko' not in self.clients:
            return []

        cache_key = f"crypto_market_{limit}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            market_data = await self.clients['coingecko'].get_market_data(limit=limit)
            self._set_cache(cache_key, market_data)
            return market_data
        except Exception as e:
            self.logger.error(f"Error fetching crypto market data: {e}")
            return []

    async def get_macro_indicators(self) -> Dict[str, Any]:
        """
        Get macroeconomic indicators from FRED.
        Provides context for risk assessment and market regime detection.
        """
        if 'fred' not in self.clients:
            return {}

        cache_key = "macro_indicators"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            macro_data = await self.clients['fred'].get_economic_indicators()
            self._set_cache(cache_key, macro_data, ttl=3600)  # 1 hour cache for macro data
            return macro_data
        except Exception as e:
            self.logger.error(f"Error fetching macro indicators: {e}")
            return {}

    async def get_crypto_news_sentiment(self, symbol: str = None, limit: int = 20) -> List[Dict]:
        """
        Get crypto news and sentiment analysis from CryptoPanic.
        Provides input for AI-powered market analysis and signal confirmation.
        """
        if 'cryptopanic' not in self.clients:
            return []

        cache_key = f"news_sentiment_{symbol or 'all'}_{limit}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            news_data = await self.clients['cryptopanic'].get_news(
                currencies=[symbol] if symbol else None,
                limit=limit
            )
            self._set_cache(cache_key, news_data, ttl=600)  # 10 minutes cache for news
            return news_data
        except Exception as e:
            self.logger.error(f"Error fetching news sentiment: {e}")
            return []

    async def get_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Get retail sentiment from Reddit.
        Measures market psychology and potential reversal signals.
        """
        if 'reddit' not in self.clients:
            return {}

        cache_key = f"social_sentiment_{symbol}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            sentiment_data = await self.clients['reddit'].get_sentiment(symbol)
            self._set_cache(cache_key, sentiment_data, ttl=1800)  # 30 minutes cache
            return sentiment_data
        except Exception as e:
            self.logger.error(f"Error fetching social sentiment: {e}")
            return {}

    async def get_defi_metrics(self) -> Dict[str, Any]:
        """
        Get DeFi ecosystem metrics from DefiLlama.
        Provides insights into DeFi market trends and TVL changes.
        """
        if 'defillama' not in self.clients:
            return {}

        cache_key = "defi_metrics"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            defi_data = await self.clients['defillama'].get_protocol_metrics()
            self._set_cache(cache_key, defi_data, ttl=1800)  # 30 minutes cache
            return defi_data
        except Exception as e:
            self.logger.error(f"Error fetching DeFi metrics: {e}")
            return {}

    async def get_enhanced_market_context(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive market context for a symbol.
        Combines multiple data sources for enriched analysis.
        """
        context = {
            'symbol': symbol,
            'timestamp': time.time(),
            'market_data': {},
            'correlations': {},
            'sentiment': {},
            'news': [],
            'macro_context': {},
            'defi_trends': {}
        }

        # Parallel data fetching
        tasks = [
            self.get_crypto_market_data(limit=50),
            self.get_crypto_news_sentiment(symbol, limit=10),
            self.get_social_sentiment(symbol),
            self.get_macro_indicators(),
            self.get_defi_metrics()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        if not isinstance(results[0], Exception):
            context['market_data'] = next((item for item in results[0] if item.get('symbol') == symbol), {})

        if not isinstance(results[1], Exception):
            context['news'] = results[1]

        if not isinstance(results[2], Exception):
            context['sentiment'] = results[2]

        if not isinstance(results[3], Exception):
            context['macro_context'] = results[3]

        if not isinstance(results[4], Exception):
            context['defi_trends'] = results[4]

        # Calculate correlations if we have market data
        if context['market_data']:
            related_symbols = [symbol] + self._get_related_symbols(symbol)
            correlations = await self.get_market_correlations(related_symbols)
            context['correlations'] = correlations

        return context

    def _get_related_symbols(self, symbol: str) -> List[str]:
        """Get related symbols for correlation analysis."""
        # This could be expanded with more sophisticated logic
        related_map = {
            'BTCUSDT': ['ETHUSDT', 'BNBUSDT', 'ADAUSDT'],
            'ETHUSDT': ['BTCUSDT', 'BNBUSDT', 'SOLUSDT'],
            'SOLUSDT': ['ETHUSDT', 'AVAXUSDT', 'MATICUSDT'],
            # Add more mappings as needed
        }
        return related_map.get(symbol, [])

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

    async def health_check(self) -> Dict[str, bool]:
        """Check health status of all API clients."""
        health_status = {}
        for name, client in self.clients.items():
            try:
                # Simple health check - could be more sophisticated
                health_status[name] = await client.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for {name}: {e}")
                health_status[name] = False

        return health_status
