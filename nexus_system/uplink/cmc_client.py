import aiohttp
import asyncio
import time
from typing import Dict, Any, List
from ..utils.logger import get_logger
import system_directive as config

class CMCClient:
    """
    CoinMarketCap Client for Sentinel Macro Analysis.
    Handles rate-limited polling of Global Metrics and Top Assets.
    """
    BASE_URL = "https://pro-api.coinmarketcap.com"
    
    def __init__(self):
        self.logger = get_logger("CMCClient")
        self.api_key = config.CMC_API_KEY
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }
        self.last_poll_time = 0
        self.cache = {}
        self.poll_interval = getattr(config, 'CMC_POLL_INTERVAL', 600)

    async def get_global_metrics(self) -> Dict[str, Any]:
        """
        Fetches BTC Dominance and Global Market Cap.
        Endpoint: /v1/global-metrics/quotes/latest
        """
        # Rate Limit Check
        now = time.time()
        if now - self.last_poll_time < self.poll_interval and self.cache:
            return self.cache
            
        if not self.api_key:
            self.logger.error("CMC API Key missing!")
            return {}

        url = f"{self.BASE_URL}/v1/global-metrics/quotes/latest"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        quote = data['data']['quote']['USD']
                        
                        metrics = {
                            "btc_dominance": data['data']['btc_dominance'],
                            "eth_dominance": data['data']['eth_dominance'],
                            "total_market_cap": quote['total_market_cap'],
                            "total_volume_24h": quote['total_volume_24h'],
                            "timestamp": time.time()
                        }
                        
                        self.cache = metrics
                        self.last_poll_time = time.time()
                        self.logger.info(f"Updated Macro Metrics: BTC.D {metrics['btc_dominance']:.2f}% | Cap ${metrics['total_market_cap']/1e9:.1f}B")
                        return metrics
                    else:
                        error_text = await resp.text()
                        self.logger.error(f"CMC API Error ({resp.status}): {error_text}")
                        return self.cache # Return stale cache on error
                        
        except Exception as e:
            self.logger.error(f"CMC Connection Error: {e}")
            return self.cache

    async def get_top_losers(self, limit=50) -> List[Dict]:
        """
        Fetches Top 50 Cryptos sorted by 24h/1h percent change.
        Useful for identifying Shark Targets.
        Endpoint: /v1/cryptocurrency/listings/latest
        """
        # Separate rate limit check? For now, we sync with global metrics
        # Ideally we only call this when needed or on same interval
        
        # NOTE: This endpoint consumes credits too. Use sparingly.
        return [] # Implement if needed for dynamic target updates
