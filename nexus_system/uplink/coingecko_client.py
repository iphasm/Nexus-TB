"""
CoinGecko API Client for Nexus Core
Provides comprehensive crypto market data for asset filtering and analysis.
"""

import aiohttp
import asyncio
import time
from typing import Dict, Any, List, Optional
from ..utils.logger import get_logger
import os

class CoinGeckoClient:
    """
    CoinGecko API Client for enhanced crypto market intelligence.
    Used for filtering tradable assets and market analysis.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.logger = get_logger("CoinGeckoClient")
        self.api_key = os.getenv("COINGECKO_API_KEY", "")
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.min_request_interval = 1.2  # Rate limiting: ~50 requests/minute

        # Cache for expensive operations
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def __aenter__(self):
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_session()

    async def _init_session(self):
        """Initialize HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _rate_limit_wait(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to CoinGecko API."""
        await self._rate_limit_wait()

        if not self.session:
            await self._init_session()

        url = f"{self.BASE_URL}{endpoint}"
        request_params = params or {}

        # Add API key if available (for Pro endpoints)
        if self.api_key:
            request_params['x_cg_demo_api_key'] = self.api_key

        try:
            async with self.session.get(url, params=request_params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    self.logger.warning("CoinGecko rate limit hit, waiting 60s...")
                    await asyncio.sleep(60)
                    return await self._make_request(endpoint, params)  # Retry
                else:
                    error_text = await response.text()
                    self.logger.error(f"CoinGecko API error {response.status}: {error_text}")
                    return {}
        except Exception as e:
            self.logger.error(f"CoinGecko request error: {e}")
            return {}

    async def get_market_data(self, limit: int = 100, currency: str = 'usd') -> List[Dict[str, Any]]:
        """
        Get comprehensive market data for top cryptocurrencies.
        Used for asset filtering and market intelligence.

        Returns:
            List of crypto data with market cap, volume, price change, etc.
        """
        cache_key = f"market_data_{limit}_{currency}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        params = {
            'vs_currency': currency,
            'order': 'market_cap_desc',
            'per_page': min(limit, 250),  # CoinGecko limit
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '1h,24h,7d,30d'
        }

        data = await self._make_request('/coins/markets', params)

        if not data:
            return []

        # Process and standardize data
        processed_data = []
        for coin in data:
            processed_coin = {
                'id': coin.get('id'),
                'symbol': coin.get('symbol', '').upper(),
                'name': coin.get('name'),
                'current_price': coin.get('current_price', 0),
                'market_cap': coin.get('market_cap', 0),
                'market_cap_rank': coin.get('market_cap_rank'),
                'total_volume': coin.get('total_volume', 0),
                'price_change_1h': coin.get('price_change_percentage_1h_in_currency'),
                'price_change_24h': coin.get('price_change_percentage_24h_in_currency'),
                'price_change_7d': coin.get('price_change_percentage_7d_in_currency'),
                'price_change_30d': coin.get('price_change_percentage_30d_in_currency'),
                'circulating_supply': coin.get('circulating_supply'),
                'total_supply': coin.get('total_supply'),
                'max_supply': coin.get('max_supply'),
                'ath': coin.get('ath'),
                'ath_change_percentage': coin.get('ath_change_percentage'),
                'last_updated': coin.get('last_updated'),
                # Filtering criteria
                'is_eligible': self._is_asset_eligible(coin),
                'liquidity_score': self._calculate_liquidity_score(coin),
                'volatility_score': self._calculate_volatility_score(coin)
            }
            processed_data.append(processed_coin)

        self._set_cache(cache_key, processed_data)
        self.logger.info(f"✅ Fetched {len(processed_data)} crypto market data points")
        return processed_data

    async def get_coin_details(self, coin_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific coin.
        Used for deep analysis of selected assets.
        """
        cache_key = f"coin_details_{coin_id}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        data = await self._make_request(f'/coins/{coin_id}')

        if not data:
            return {}

        # Extract relevant details
        details = {
            'id': data.get('id'),
            'symbol': data.get('symbol', '').upper(),
            'name': data.get('name'),
            'description': data.get('description', {}).get('en', ''),
            'homepage': data.get('links', {}).get('homepage', []),
            'blockchain_site': data.get('links', {}).get('blockchain_site', []),
            'categories': data.get('categories', []),
            'market_cap_rank': data.get('market_cap_rank'),
            'coingecko_rank': data.get('coingecko_rank'),
            'coingecko_score': data.get('coingecko_score'),
            'developer_score': data.get('developer_score'),
            'community_score': data.get('community_score'),
            'liquidity_score': data.get('liquidity_score'),
            'public_interest_score': data.get('public_interest_score'),
            'market_data': {
                'current_price': data.get('market_data', {}).get('current_price', {}).get('usd'),
                'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd'),
                'total_volume': data.get('market_data', {}).get('total_volume', {}).get('usd'),
                'price_change_24h': data.get('market_data', {}).get('price_change_24h'),
                'price_change_percentage_24h': data.get('market_data', {}).get('price_change_percentage_24h')
            },
            'community_data': {
                'twitter_followers': data.get('community_data', {}).get('twitter_followers'),
                'telegram_channel_user_count': data.get('community_data', {}).get('telegram_channel_user_count'),
                'reddit_subscribers': data.get('community_data', {}).get('reddit_subscribers')
            }
        }

        self._set_cache(cache_key, details, ttl=1800)  # 30 min cache for details
        return details

    async def get_trending_coins(self) -> List[Dict[str, Any]]:
        """
        Get trending coins from CoinGecko.
        Useful for identifying emerging opportunities.
        """
        cache_key = "trending_coins"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        data = await self._make_request('/search/trending')

        if not data or 'coins' not in data:
            return []

        trending = []
        for item in data['coins']:
            coin_data = item.get('item', {})
            trending.append({
                'id': coin_data.get('id'),
                'symbol': coin_data.get('symbol'),
                'name': coin_data.get('name'),
                'thumb': coin_data.get('thumb'),
                'market_cap_rank': coin_data.get('market_cap_rank'),
                'price_btc': coin_data.get('price_btc')
            })

        self._set_cache(cache_key, trending, ttl=600)  # 10 min cache
        return trending

    def _is_asset_eligible(self, coin_data: Dict[str, Any]) -> bool:
        """
        Determine if an asset meets Nexus trading criteria.
        """
        market_cap = coin_data.get('market_cap', 0)
        total_volume = coin_data.get('total_volume', 0)
        price = coin_data.get('current_price', 0)

        # Minimum criteria for trading
        min_market_cap = 50_000_000  # $50M
        min_volume_24h = 1_000_000   # $1M daily volume
        min_price = 0.000001       # Avoid extremely low-priced tokens

        return (
            market_cap >= min_market_cap and
            total_volume >= min_volume_24h and
            price >= min_price
        )

    def _calculate_liquidity_score(self, coin_data: Dict[str, Any]) -> float:
        """
        Calculate liquidity score (0-100) based on volume and market cap.
        """
        market_cap = coin_data.get('market_cap', 0)
        volume_24h = coin_data.get('total_volume', 0)

        if market_cap == 0:
            return 0.0

        # Volume to market cap ratio (higher = more liquid)
        volume_ratio = volume_24h / market_cap

        # Normalize to 0-100 scale
        # 1% daily volume = 100 points, 0.1% = 10 points, etc.
        score = min(volume_ratio * 10000, 100)

        return round(score, 2)

    def _calculate_volatility_score(self, coin_data: Dict[str, Any]) -> float:
        """
        Calculate volatility score (0-100) based on price changes.
        """
        changes = [
            abs(coin_data.get('price_change_percentage_1h_in_currency', 0) or 0),
            abs(coin_data.get('price_change_percentage_24h_in_currency', 0) or 0),
            abs(coin_data.get('price_change_percentage_7d_in_currency', 0) or 0),
            abs(coin_data.get('price_change_percentage_30d_in_currency', 0) or 0)
        ]

        # Average absolute change
        avg_change = sum(changes) / len(changes) if changes else 0

        # Normalize: 10% avg change = 100 points, 1% = 10 points, etc.
        score = min(avg_change * 10, 100)

        return round(score, 2)

    async def filter_eligible_assets(self, raw_symbols: List[str]) -> List[str]:
        """
        Filter a list of symbols to only include eligible ones based on CoinGecko data.
        """
        market_data = await self.get_market_data(limit=500)  # Get more data for filtering

        # Create lookup dict
        eligible_symbols = {coin['symbol'] for coin in market_data if coin['is_eligible']}

        # Filter original list
        filtered = [symbol for symbol in raw_symbols if symbol in eligible_symbols]

        self.logger.info(f"✅ Filtered {len(raw_symbols)} symbols to {len(filtered)} eligible assets")
        return filtered

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
        """Simple health check for the API."""
        try:
            data = await self.get_market_data(limit=5)
            return len(data) > 0
        except Exception:
            return False
