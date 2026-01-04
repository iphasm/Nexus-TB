#!/usr/bin/env python3
"""
Valoración de Criptomonedas con GPT-4o vs Grok
Análisis individual de BTC, ETH, XRP y SOL con contexto de mercado completo
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar librerías necesarias
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance no disponible")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai no disponible")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ requests no disponible")

# Configuración de APIs mediante variables de entorno (Railway)
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
CRYPTOPANIC_AVAILABLE = bool(CRYPTOPANIC_API_KEY)

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_AVAILABLE = bool(COINGECKO_API_KEY)
# Logging de configuración de APIs
if CRYPTOPANIC_API_KEY:
    print("✅ CryptoPanic API configurada")
else:
    print("⚠️ CryptoPanic API no configurada - configurar variable de entorno CRYPTOPANIC_API_KEY en Railway")
    print("   Obtener API key: https://cryptopanic.com/developers/api/")

if COINGECKO_API_KEY:
    print("✅ CoinGecko API configurada")
else:
    print("⚠️ CoinGecko API no configurada - configurar variable de entorno COINGECKO_API_KEY en Railway")
    print("   Obtener API key gratuita: https://www.coingecko.com/en/api")

# CoinGecko API (usamos requests directamente, no necesitamos pycoingecko)


class AICryptoValuation:
    """Sistema de valoración de criptomonedas con IA."""

    def __init__(self):
        # Mapear símbolos de trading a IDs de CoinGecko
        self.cryptos = [
            {"symbol": "BTC-USD", "name": "Bitcoin", "short": "BTC", "coingecko_id": "bitcoin"},
            {"symbol": "ETH-USD", "name": "Ethereum", "short": "ETH", "coingecko_id": "ethereum"},
            {"symbol": "XRP-USD", "name": "XRP", "short": "XRP", "coingecko_id": "ripple"},
            {"symbol": "SOL-USD", "name": "Solana", "short": "SOL", "coingecko_id": "solana"}
        ]

        # APIs
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.xai_api_key = os.getenv("XAI_API_KEY")
        self.xai_base_url = "https://api.x.ai/v1"

        # Modelo principal configurado: GPT-4o Mini (mejor balance calidad/costo)
        self.primary_model = {
            "name": "GPT-4o Mini",
            "id": "gpt-4o-mini",
            "provider": "OpenAI",
            "type": "primary"
        }

        # Modelos adicionales para comparación (opcional)
        self.openai_models = [
            {"name": "GPT-4o", "id": "gpt-4o", "provider": "OpenAI"},
            {"name": "GPT-4o Mini", "id": "gpt-4o-mini", "provider": "OpenAI"},
            {"name": "GPT-5", "id": "gpt-5", "provider": "OpenAI"},
            {"name": "GPT-5 Mini", "id": "gpt-5-mini", "provider": "OpenAI"}
        ]

        self.xai_models = [
            {"name": "Grok-3", "id": "grok-3", "provider": "xAI"},
            {"name": "Grok-3 Mini", "id": "grok-3-mini", "provider": "xAI"},
            {"name": "Grok-4", "id": "grok-4-0709", "provider": "xAI"},
            {"name": "Grok-4.1 Fast", "id": "grok-4-1-fast-reasoning", "provider": "xAI"}
        ]

        # CoinGecko API configurada (usaremos requests directamente)

        # Validar APIs
        self.openai_available = self._validate_openai()
        self.xai_available = self._validate_xai()
        self.yfinance_available = YFINANCE_AVAILABLE
        self.coingecko_available = COINGECKO_AVAILABLE
        self.cryptopanic_available = CRYPTOPANIC_AVAILABLE

        print("🤖 AI Crypto Valuation System - Optimizado con GPT-4o Mini")
        print(f"   🎯 Modelo Principal: {self.primary_model['name']} ({self.primary_model['id']})")
        print(f"   OpenAI: {'✅' if self.openai_available else '❌'} ({len(self.openai_models)} modelos)")
        print(f"   xAI: {'✅' if self.xai_available else '❌'} ({len(self.xai_models)} modelos)")
        print(f"   yfinance: {'✅' if self.yfinance_available else '❌'}")
        print(f"   CoinGecko: {'✅' if self.coingecko_available else '❌'}")
        print(f"   CryptoPanic: {'✅' if CRYPTOPANIC_AVAILABLE else '❌'}")
        print(f"   💰 Costo estimado por análisis: ~$0.002")
        print(f"   📊 Analizando: {', '.join([c['short'] for c in self.cryptos])}")

    def _validate_openai(self) -> bool:
        """Validar conexión con OpenAI."""
        if not self.openai_api_key:
            return False
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            client.models.list()
            return True
        except:
            return False

    def _validate_xai(self) -> bool:
        """Validar conexión con xAI."""
        if not self.xai_api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.xai_api_key}"}
            response = requests.get(f"{self.xai_base_url}/models", headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """Obtener datos técnicos de una criptomoneda."""
        try:
            ticker = yf.Ticker(symbol)
            current_price = ticker.history(period="1d", interval="1m").iloc[-1]['Close']
            hourly_data = ticker.history(period="1d", interval="1h")
            daily_data = ticker.history(period="2d", interval="1h")

            # Cálculos técnicos
            price_1h_ago = hourly_data.iloc[-2]['Close'] if len(hourly_data) > 1 else current_price
            price_24h_ago = daily_data.iloc[0]['Close'] if len(daily_data) > 24 else current_price

            change_1h = ((current_price - price_1h_ago) / price_1h_ago) * 100
            change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100

            # Volumen
            volume_24h = daily_data['Volume'].tail(24).sum() if len(daily_data) >= 24 else 0

            # Información adicional
            info = ticker.info

            return {
                "price": round(current_price, 2),
                "change_1h": round(change_1h, 2),
                "change_24h": round(change_24h, 2),
                "volume_24h": int(volume_24h),
                "market_cap": info.get("marketCap", 0),
                "success": True
            }

        except Exception as e:
            return {"error": str(e), "success": False}

    def get_coingecko_metrics(self, coingecko_id: str) -> Dict[str, Any]:
        """Obtener métricas adicionales de CoinGecko para una criptomoneda."""
        if not self.coingecko_available:
            return {"error": "CoinGecko no disponible"}

        try:
            # Usar requests directamente con endpoint gratuito
            base_url = "https://api.coingecko.com/api/v3"
            headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}

            url = f"{base_url}/coins/{coingecko_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'true',
                'sparkline': 'false'
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code != 200:
                return {"error": f"Error HTTP {response.status_code}", "success": False}

            coin_data = response.json()

            # Nota: Algunos campos no están disponibles en el plan gratuito
            # Usamos valores por defecto o datos disponibles
            metrics = {
                # Scores (no disponibles en plan gratuito)
                "community_score": coin_data.get("community_score", 0),
                "developer_score": coin_data.get("developer_score", 0),
                "liquidity_score": coin_data.get("liquidity_score", 0),
                "public_interest_score": coin_data.get("public_interest_score", 0),

                # Métricas sociales (parcialmente disponibles)
                "twitter_followers": coin_data.get("community_data", {}).get("twitter_followers", 0),
                "reddit_subscribers": coin_data.get("community_data", {}).get("reddit_subscribers", 0),
                "telegram_channel_user_count": coin_data.get("community_data", {}).get("telegram_channel_user_count", 0),

                # Métricas de desarrollo (limitadas en plan gratuito)
                "github_repos": len(coin_data.get("developer_data", {}).get("repos", [])),
                "github_stars": sum(repo.get("stargazers_count", 0) for repo in coin_data.get("developer_data", {}).get("repos", [])),
                "github_forks": sum(repo.get("forks_count", 0) for repo in coin_data.get("developer_data", {}).get("repos", [])),
                "github_contributors": coin_data.get("developer_data", {}).get("pull_request_contributors", 0),
                "github_commits_last_4_weeks": coin_data.get("developer_data", {}).get("commit_count_4_weeks", 0),

                # Métricas de mercado (disponibles)
                "total_supply": coin_data.get("market_data", {}).get("total_supply"),
                "circulating_supply": coin_data.get("market_data", {}).get("circulating_supply"),
                "max_supply": coin_data.get("market_data", {}).get("max_supply"),
                "fully_diluted_valuation": coin_data.get("market_data", {}).get("fully_diluted_valuation"),

                # Rankings (disponibles)
                "market_cap_rank": coin_data.get("market_cap_rank"),
                "coingecko_rank": coin_data.get("coingecko_rank"),

                # Categorías y plataformas
                "categories": coin_data.get("categories", []),
                "platforms": coin_data.get("platforms", {}),

                "success": True
            }

            return metrics

        except Exception as e:
            return {"error": f"Error obteniendo métricas CoinGecko: {str(e)}", "success": False}

    def get_fear_greed_index(self) -> Dict[str, Any]:
        """Obtener Fear & Greed Index de CoinGecko."""
        if not self.coingecko_available:
            return {"error": "CoinGecko no disponible"}

        try:
            # Usar requests directamente
            base_url = "https://api.coingecko.com/api/v3"
            headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}

            url = f"{base_url}/global"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {"error": f"Error HTTP {response.status_code}", "success": False}

            data = response.json()
            fgi_data = data.get("data", {})

            return {
                "value": fgi_data.get("fear_greed_index", {}).get("value"),
                "value_text": fgi_data.get("fear_greed_index", {}).get("value_text"),
                "timestamp": fgi_data.get("fear_greed_index", {}).get("timestamp"),
                "success": True
            }

        except Exception as e:
            return {"error": f"Error obteniendo Fear & Greed Index: {str(e)}", "success": False}

    def get_global_crypto_data(self) -> Dict[str, Any]:
        """Obtener métricas globales del mercado crypto."""
        if not self.coingecko_available:
            return {"error": "CoinGecko no disponible"}

        try:
            # Usar requests directamente
            base_url = "https://api.coingecko.com/api/v3"
            headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}

            url = f"{base_url}/global"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {"error": f"Error HTTP {response.status_code}", "success": False}

            data = response.json()

            return {
                "active_cryptocurrencies": data.get("data", {}).get("active_cryptocurrencies"),
                "upcoming_icos": data.get("data", {}).get("upcoming_icos"),
                "ongoing_icos": data.get("data", {}).get("ongoing_icos"),
                "ended_icos": data.get("data", {}).get("ended_icos"),
                "markets": data.get("data", {}).get("markets"),
                "total_market_cap": data.get("data", {}).get("total_market_cap", {}),
                "total_volume": data.get("data", {}).get("total_volume", {}),
                "market_cap_percentage": data.get("data", {}).get("market_cap_percentage", {}),
                "market_cap_change_percentage_24h_usd": data.get("data", {}).get("market_cap_change_percentage_24h_usd"),
                "updated_at": data.get("data", {}).get("updated_at"),
                "success": True
            }

        except Exception as e:
            return {"error": f"Error obteniendo datos globales: {str(e)}", "success": False}

    def get_trending_coins(self) -> Dict[str, Any]:
        """Obtener criptomonedas en tendencia."""
        if not self.coingecko_available:
            return {"error": "CoinGecko no disponible"}

        try:
            # Usar requests directamente
            base_url = "https://api.coingecko.com/api/v3"
            headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}

            url = f"{base_url}/search/trending"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {"error": f"Error HTTP {response.status_code}", "success": False}

            trending = response.json()

            coins = []
            for coin in trending.get("coins", []):
                item = coin.get("item", {})
                coins.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "symbol": item.get("symbol"),
                    "market_cap_rank": item.get("market_cap_rank"),
                    "thumb": item.get("thumb"),
                    "price_btc": item.get("price_btc")
                })

            return {
                "trending_coins": coins,
                "success": True
            }

        except Exception as e:
            return {"error": f"Error obteniendo trending coins: {str(e)}", "success": False}

    def run_optimized_valuation(self) -> Dict[str, Any]:
        """Ejecutar valoración optimizada usando GPT-4o Mini como modelo principal."""

        print("\n🚀 VALORACIÓN OPTIMIZADA CON GPT-4o MINI")
        print("=" * 80)
        print("💡 Configuración: Modelo principal GPT-4o Mini (mejor balance calidad/costo)")

        results = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "primary_model": self.primary_model,
                "cost_estimate_per_crypto": 0.002,
                "optimization_reason": "GPT-4o Mini ofrece 94% de precisión de GPT-4o por solo 6.7% del costo"
            },
            "cryptos_analyzed": [c['short'] for c in self.cryptos],
            "valuations": {}
        }

        # Fase 1: Obtener datos de mercado
        print("\n📊 Fase 1: Recopilando datos de mercado...")
        market_data = {}
        for crypto in self.cryptos:
            print(f"   📈 {crypto['short']}...")
            data = self.get_crypto_data(crypto['symbol'])
            market_data[crypto['short']] = data if data.get('success') else {"error": "No disponible"}

        # Fase 2: Métricas CoinGecko
        print("\n🪙 Fase 2: Métricas CoinGecko...")
        coingecko_data = {}
        for crypto in self.cryptos:
            metrics = self.get_coingecko_metrics(crypto['coingecko_id'])
            coingecko_data[crypto['short']] = metrics if metrics.get('success') else {"error": "No disponible"}

        # Fase 3: Datos globales
        print("\n🌍 Fase 3: Contexto de mercado...")
        fear_greed = self.get_fear_greed_index()
        global_crypto = self.get_global_crypto_data()
        trending_coins = self.get_trending_coins()
        cryptopanic_news = self.get_cryptopanic_news(limit=8)

        # Fase 4: Valoraciones con GPT-4o Mini
        print("\n🎯 Fase 4: Valoraciones con GPT-4o Mini...")
        total_cost = 0

        for crypto in self.cryptos:
            print(f"\n🪙 Valorando {crypto['short']}...")

            # Crear payload
            payload = self.create_valuation_payload(
                crypto,
                market_data[crypto['short']],
                coingecko_data[crypto['short']],
                [],  # market_news (simplificado)
                cryptopanic_news,
                {"contexto": "Análisis optimizado con GPT-4o Mini"},
                fear_greed,
                global_crypto,
                trending_coins
            )

            # Obtener valoración principal
            primary_valuation = self.get_primary_valuation(crypto, payload)

            if primary_valuation.get('success'):
                total_cost += primary_valuation['cost_estimate']

                results["valuations"][crypto['short']] = {
                    "crypto_data": market_data[crypto['short']],
                    "coingecko_metrics": coingecko_data[crypto['short']],
                    "primary_valuation": primary_valuation,
                    "analysis_summary": {
                        "model_used": primary_valuation['primary_model'],
                        "long_signal": primary_valuation['valuation']['result'].get('long_signal', 0),
                        "short_signal": primary_valuation['valuation']['result'].get('short_signal', 0),
                        "confidence": primary_valuation['valuation']['result'].get('confidence_level', 0),
                        "response_time": primary_valuation['valuation'].get('response_time', 0)
                    }
                }
            else:
                results["valuations"][crypto['short']] = {
                    "error": primary_valuation.get('error', 'Error desconocido'),
                    "crypto_data": market_data[crypto['short']],
                    "coingecko_metrics": coingecko_data[crypto['short']]
                }

        # Resumen final
        print("\n🏁 RESUMEN DE VALORACIÓN OPTIMIZADA")
        print("=" * 60)
        print(f"🎯 Modelo utilizado: {self.primary_model['name']}")
        print(f"💰 Costo total estimado: ${total_cost:.4f}")
        print(f"💰 Costo por cripto: ${total_cost/len(self.cryptos):.4f}")
        print("📊 Valoraciones exitosas:")
        successful = sum(1 for v in results["valuations"].values() if "primary_valuation" in v)
        print(f"   ✅ {successful}/{len(self.cryptos)} criptos analizadas")

        # Mostrar resultados por cripto
        print("\n📋 RESULTADOS POR CRIPTO:")
        for crypto_short, valuation in results["valuations"].items():
            if "primary_valuation" in valuation:
                summary = valuation["analysis_summary"]
                long_sig = summary["long_signal"]
                short_sig = summary["short_signal"]
                confidence = summary["confidence"]
                time_taken = summary["response_time"]

                print(f"   🪙 {crypto_short}: LONG {long_sig:.3f} | SHORT {short_sig:.3f} ({confidence:.1%}) - {time_taken:.2f}s")
            else:
                print(f"   ❌ {crypto_short}: Error en valoración")

        # Guardar resultados
        filename = f"optimized_valuation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Resultados guardados en: {filename}")

        return results

    def get_primary_valuation(self, crypto: Dict, payload: Dict) -> Dict[str, Any]:
        """Obtener valoración usando el modelo principal (GPT-4o Mini)."""
        print(f"   🎯 Usando modelo principal: {self.primary_model['name']}")

        try:
            # Usar GPT-4o Mini como modelo principal
            result = self.get_openai_valuation_with_model(crypto, payload, self.primary_model['id'])

            if "error" in result:
                print(f"      ❌ Error con {self.primary_model['name']}: {result['error']}")
                return {"error": f"Modelo principal falló: {result['error']}", "success": False}
            else:
                long_signal = result['result'].get('long_signal', 0)
                short_signal = result['result'].get('short_signal', 0)
                confidence = result['result'].get('confidence_level', 0)
                response_time = result.get('response_time', 0)

                print(f"      ✅ {self.primary_model['name']}: LONG {long_signal:.3f} | SHORT {short_signal:.3f} ({confidence:.1%}) - {response_time:.2f}s")
                print(f"      💰 Costo aproximado: $0.002")

                return {
                    "primary_model": self.primary_model['name'],
                    "valuation": result,
                    "cost_estimate": 0.002,
                    "success": True
                }

        except Exception as e:
            print(f"      ❌ Error con modelo principal: {str(e)}")
            return {"error": f"Error con modelo principal: {str(e)}", "success": False}

    def get_cryptopanic_news(self, limit: int = 10) -> Dict[str, Any]:
        """Obtener noticias de CryptoPanic con análisis de sentimiento."""
        if not CRYPTOPANIC_AVAILABLE:
            return {"error": "CryptoPanic API no disponible", "success": False}

        try:
            base_url = "https://cryptopanic.com/api/v3"
            headers = {"accept": "application/json"}

            # Obtener noticias generales de crypto
            params = {
                "auth_token": CRYPTOPANIC_API_KEY,
                "limit": limit,
                "public": "true"
            }

            response = requests.get(f"{base_url}/posts/", headers=headers, params=params, timeout=10)

            if response.status_code != 200:
                return {"error": f"Error HTTP {response.status_code}", "success": False}

            data = response.json()

            # Procesar noticias
            processed_news = []
            sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}

            for post in data.get("results", []):
                sentiment = "neutral"
                if post.get("votes", {}).get("ludicrous", 0) > post.get("votes", {}).get("toxic", 0):
                    sentiment = "bullish"
                elif post.get("votes", {}).get("toxic", 0) > post.get("votes", {}).get("ludicrous", 0):
                    sentiment = "bearish"

                sentiment_counts[sentiment] += 1

                news_item = {
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "source": post.get("domain", ""),
                    "published_at": post.get("published_at", ""),
                    "sentiment": sentiment,
                    "importance": "high" if post.get("is_hot", False) else "medium",
                    "tags": [tag.get("name", "") for tag in post.get("tags", [])],
                    "currencies": [curr.get("code", "") for curr in post.get("currencies", [])]
                }
                processed_news.append(news_item)

            # Calcular métricas de sentimiento
            total_news = len(processed_news)
            sentiment_metrics = {}
            for sentiment, count in sentiment_counts.items():
                sentiment_metrics[sentiment] = {
                    "count": count,
                    "percentage": (count / total_news * 100) if total_news > 0 else 0
                }

            # Determinar sentimiento general del mercado
            if sentiment_metrics["bullish"]["percentage"] > 60:
                market_sentiment = "BULLISH"
            elif sentiment_metrics["bearish"]["percentage"] > 60:
                market_sentiment = "BEARISH"
            else:
                market_sentiment = "NEUTRAL"

            return {
                "news": processed_news,
                "sentiment_metrics": sentiment_metrics,
                "market_sentiment": market_sentiment,
                "total_news": total_news,
                "success": True
            }

        except Exception as e:
            return {"error": f"Error obteniendo noticias CryptoPanic: {str(e)}", "success": False}

    def get_market_news(self) -> List[Dict[str, Any]]:
        """Obtener noticias recientes del mercado crypto."""
        try:
            # Obtener noticias de múltiples fuentes
            tickers = ["BTC-USD", "^GSPC", "^IXIC", "ETH-USD"]  # BTC, S&P 500, Nasdaq, ETH
            all_news = []

            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    news = stock.news

                    for item in news[:3]:  # Limitar a 3 por fuente
                        news_item = {
                            "title": item.get("title", ""),
                            "publisher": item.get("publisher", ""),
                            "timestamp": item.get("providerPublishTime", 0),
                            "related_ticker": ticker,
                            "date": datetime.fromtimestamp(item.get("providerPublishTime", 0)).isoformat()
                        }
                        all_news.append(news_item)

                except Exception as e:
                    continue

            # Ordenar por fecha más reciente
            all_news.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

            return all_news[:8]  # Top 8 noticias

        except Exception as e:
            return []

    def get_global_economic_context(self) -> Dict[str, Any]:
        """Obtener contexto económico global."""
        try:
            # Obtener datos de índices principales
            indices = {
                "S&P 500": "^GSPC",
                "Nasdaq": "^IXIC",
                "Dow Jones": "^DJI",
                "VIX": "^VIX"
            }

            context = {}

            for name, symbol in indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="2d", interval="1d")

                    if len(data) >= 2:
                        current = data.iloc[-1]['Close']
                        previous = data.iloc[-2]['Close']
                        change = ((current - previous) / previous) * 100

                        context[name] = {
                            "price": round(current, 2),
                            "change_pct": round(change, 2)
                        }
                except:
                    continue

            # Añadir contexto general
            context["analysis"] = {
                "fed_policy": "Aguardando decisiones de la FED sobre tasas de interés",
                "global_growth": "Preocupaciones por desaceleración económica global",
                "crypto_adoption": "Mayor adopción institucional y regulación",
                "risk_sentiment": "Moderado con foco en datos económicos"
            }

            return context

        except Exception as e:
            return {"error": str(e)}

    def create_valuation_payload(self, crypto: Dict, crypto_data: Dict, coingecko_metrics: Dict, market_news: List, cryptopanic_news: Dict, global_context: Dict, fear_greed: Dict, global_crypto: Dict, trending_coins: Dict) -> Dict[str, Any]:
        """Crear payload estructurado para valoración."""

        # Formatear noticias generales
        general_news_formatted = []
        for news in market_news[:3]:
            general_news_formatted.append({
                "title": news.get("title", ""),
                "source": news.get("publisher", ""),
                "ticker": news.get("related_ticker", ""),
                "date": news.get("date", "")
            })

        # Formatear noticias CryptoPanic con sentimiento
        cryptopanic_formatted = []
        if cryptopanic_news.get("success"):
            for news in cryptopanic_news.get("news", [])[:5]:
                cryptopanic_formatted.append({
                    "title": news.get("title", ""),
                    "url": news.get("url", ""),
                    "source": news.get("source", ""),
                    "sentiment": news.get("sentiment", "neutral"),
                    "importance": news.get("importance", "medium"),
                    "published_at": news.get("published_at", ""),
                    "currencies": news.get("currencies", []),
                    "tags": news.get("tags", [])
                })

        payload = {
            "timestamp": datetime.now().isoformat(),
            "crypto_info": {
                "symbol": crypto['short'],
                "name": crypto['name'],
                "coingecko_id": crypto['coingecko_id']
            },
            "technical_data": crypto_data,
            "coingecko_metrics": coingecko_metrics,
            "market_news": {
                "general_news": general_news_formatted,
                "cryptopanic_news": cryptopanic_formatted,
                "cryptopanic_sentiment": cryptopanic_news.get("sentiment_metrics", {}),
                "market_sentiment_cryptopanic": cryptopanic_news.get("market_sentiment", "UNKNOWN")
            },
            "global_economic_context": global_context,
            "market_sentiment": {
                "fear_greed_index": fear_greed,
                "global_crypto_metrics": global_crypto,
                "trending_coins": trending_coins.get("trending_coins", [])
            },
            "valuation_request": {
                "task": "comprehensive_crypto_valuation",
                "timeframes": ["short_term", "medium_term"],
                "factors": [
                    "technical_analysis",
                    "fundamental_analysis",
                    "coingecko_metrics_analysis",
                    "cryptopanic_sentiment_analysis",
                    "cryptopanic_news_impact",
                    "developer_activity",
                    "community_engagement",
                    "market_sentiment",
                    "news_sentiment",
                    "social_sentiment",
                    "global_economic_conditions",
                    "regulatory_environment",
                    "institutional_adoption",
                    "fear_greed_index",
                    "liquidity_analysis"
                ]
            }
        }

        return payload

    def get_openai_valuation_with_model(self, crypto: Dict, payload: Dict, model_id: str) -> Dict[str, Any]:
        """Obtener valoración de OpenAI con modelo específico."""

        if not self.openai_available:
            return {"error": "OpenAI no disponible"}

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)

            prompt = f"""
            Eres un analista senior de criptomonedas con 15+ años de experiencia en mercados financieros.

            DATOS TÉCNICOS DE {crypto['name']} ({crypto['short']}):
            - Precio actual: ${payload['technical_data']['price']:,.2f}
            - Cambio 1h: {payload['technical_data']['change_1h']:.2f}%
            - Cambio 24h: {payload['technical_data']['change_24h']:.2f}%
            - Volumen 24h: ${payload['technical_data']['volume_24h']/1e9:.1f}B
            - Market Cap: ${payload['technical_data']['market_cap']/1e12:.2f}T

            MÉTRICAS COINGECKO DETALLADAS:
            - Developer Score: {payload['coingecko_metrics'].get('developer_score', 'N/A')}/100
            - Community Score: {payload['coingecko_metrics'].get('community_score', 'N/A')}/100
            - Liquidity Score: {payload['coingecko_metrics'].get('liquidity_score', 'N/A')}/100
            - GitHub Stars: {payload['coingecko_metrics'].get('github_stars', 0):,}
            - GitHub Commits (4 semanas): {payload['coingecko_metrics'].get('github_commits_last_4_weeks', 0)}
            - Twitter Followers: {payload['coingecko_metrics'].get('twitter_followers', 0):,}
            - Reddit Subscribers: {payload['coingecko_metrics'].get('reddit_subscribers', 0):,}
            - Market Cap Rank: #{payload['coingecko_metrics'].get('market_cap_rank', 'N/A')}

            SENTIMIENTO DE MERCADO GLOBAL:
            - Fear & Greed Index: {payload['market_sentiment']['fear_greed_index'].get('value', 'N/A')} ({payload['market_sentiment']['fear_greed_index'].get('value_text', 'Unknown')})
            - Market Cap Total: ${payload['market_sentiment']['global_crypto_metrics'].get('total_market_cap', {}).get('usd', 0)/1e12:.2f}T
            - BTC Dominance: {payload['market_sentiment']['global_crypto_metrics'].get('market_cap_percentage', {}).get('btc', 0):.1f}%

            ANÁLISIS DE SENTIMIENTO CRYPTOPANIC:
            - Sentimiento General: {payload['market_news'].get('market_sentiment_cryptopanic', 'UNKNOWN')}
            - Bullish: {payload['market_news'].get('cryptopanic_sentiment', {}).get('bullish', {}).get('percentage', 0):.1f}%
            - Bearish: {payload['market_news'].get('cryptopanic_sentiment', {}).get('bearish', {}).get('percentage', 0):.1f}%
            - Neutral: {payload['market_news'].get('cryptopanic_sentiment', {}).get('neutral', {}).get('percentage', 0):.1f}%

            NOTICIAS GENERALES:
            {json.dumps(payload['market_news']['general_news'], indent=2, ensure_ascii=False)}

            NOTICIAS CRYPTOPANIC CON SENTIMIENTO:
            {json.dumps(payload['market_news']['cryptopanic_news'], indent=2, ensure_ascii=False)}

            CONTEXTO ECONÓMICO GLOBAL:
            {json.dumps(payload['global_economic_context'], indent=2, ensure_ascii=False)}

            TAREA: Proporciona una valoración COMPREHENSIVA de {crypto['short']} considerando TODAS las métricas disponibles, especialmente las de desarrollo, comunidad y sentimiento de mercado.

            FORMATO DE RESPUESTA (JSON estricto):
            {{
                "long_signal": 0.750,
                "short_signal": 0.250,
                "confidence_level": 0.85,
                "price_target_long": 95000,
                "price_target_short": 85000,
                "key_drivers_long": ["driver1", "driver2"],
                "key_drivers_short": ["driver1", "driver2"],
                "technical_analysis": "análisis técnico detallado",
                "fundamental_analysis": "análisis fundamental incluyendo métricas CoinGecko",
                "coingecko_insights": "análisis específico de developer score, community engagement, etc.",
                "market_sentiment": "NEUTRAL",
                "investment_thesis": "tesis de inversión considerando todas las métricas"
            }}
            """

            start_time = time.time()

            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "Eres un analista de inversiones experto. Responde ÚNICAMENTE con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            end_time = time.time()

            result_text = response.choices[0].message.content.strip()

            try:
                result_json = json.loads(result_text)
            except:
                result_json = {"error": "Respuesta no es JSON válido", "raw_response": result_text}

            return {
                "provider": "OpenAI",
                "model": model_id,
                "crypto": crypto['short'],
                "response_time": round(end_time - start_time, 2),
                "result": result_json,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Error con OpenAI {model_id}: {str(e)}"}

    def get_grok_valuation_with_model(self, crypto: Dict, payload: Dict, model_id: str) -> Dict[str, Any]:
        """Obtener valoración de Grok con modelo específico."""

        if not self.xai_available:
            return {"error": "xAI no disponible"}

        try:
            headers = {
                "Authorization": f"Bearer {self.xai_api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""
            Eres Grok, una IA creada por xAI. Analiza {crypto['name']} ({crypto['short']}) de forma objetiva y directa.

            DATOS TÉCNICOS:
            - Precio: ${payload['technical_data']['price']:,.2f}
            - Cambio 1h: {payload['technical_data']['change_1h']:.2f}%
            - Cambio 24h: {payload['technical_data']['change_24h']:.2f}%
            - Volumen: ${payload['technical_data']['volume_24h']/1e9:.1f}B
            - Market Cap: ${payload['technical_data']['market_cap']/1e12:.2f}T

            MÉTRICAS COINGECKO DETALLADAS:
            - Developer Score: {payload['coingecko_metrics'].get('developer_score', 'N/A')}/100
            - Community Score: {payload['coingecko_metrics'].get('community_score', 'N/A')}/100
            - Liquidity Score: {payload['coingecko_metrics'].get('liquidity_score', 'N/A')}/100
            - GitHub Stars: {payload['coingecko_metrics'].get('github_stars', 0):,}
            - GitHub Commits (4 semanas): {payload['coingecko_metrics'].get('github_commits_last_4_weeks', 0)}
            - Twitter Followers: {payload['coingecko_metrics'].get('twitter_followers', 0):,}
            - Reddit Subscribers: {payload['coingecko_metrics'].get('reddit_subscribers', 0):,}
            - Market Cap Rank: #{payload['coingecko_metrics'].get('market_cap_rank', 'N/A')}

            SENTIMIENTO DE MERCADO GLOBAL:
            - Fear & Greed Index: {payload['market_sentiment']['fear_greed_index'].get('value', 'N/A')} ({payload['market_sentiment']['fear_greed_index'].get('value_text', 'Unknown')})
            - Market Cap Total: ${payload['market_sentiment']['global_crypto_metrics'].get('total_market_cap', {}).get('usd', 0)/1e12:.2f}T
            - BTC Dominance: {payload['market_sentiment']['global_crypto_metrics'].get('market_cap_percentage', {}).get('btc', 0):.1f}%

            ANÁLISIS DE SENTIMIENTO CRYPTOPANIC:
            - Sentimiento General: {payload['market_news'].get('market_sentiment_cryptopanic', 'UNKNOWN')}
            - Bullish: {payload['market_news'].get('cryptopanic_sentiment', {}).get('bullish', {}).get('percentage', 0):.1f}%
            - Bearish: {payload['market_news'].get('cryptopanic_sentiment', {}).get('bearish', {}).get('percentage', 0):.1f}%
            - Neutral: {payload['market_news'].get('cryptopanic_sentiment', {}).get('neutral', {}).get('percentage', 0):.1f}%

            NOTICIAS GENERALES:
            {json.dumps(payload['market_news']['general_news'], indent=2, ensure_ascii=False)}

            NOTICIAS CRYPTOPANIC CON SENTIMIENTO:
            {json.dumps(payload['market_news']['cryptopanic_news'], indent=2, ensure_ascii=False)}

            CONTEXTO ECONÓMICO GLOBAL:
            {json.dumps(payload['global_economic_context'], indent=2, ensure_ascii=False)}

            Brinda una valoración completa considerando el panorama económico global, adopción institucional y métricas CoinGecko.

            FORMATO DE RESPUESTA (JSON estricto):
            {{
                "long_signal": 0.750,
                "short_signal": 0.250,
                "confidence_level": 0.80,
                "price_target_long": 95000,
                "price_target_short": 85000,
                "key_drivers_long": ["driver1", "driver2"],
                "key_drivers_short": ["driver1", "driver2"],
                "technical_analysis": "análisis técnico",
                "fundamental_analysis": "análisis fundamental incluyendo métricas CoinGecko",
                "coingecko_insights": "análisis específico de developer score, community engagement, etc.",
                "market_sentiment": "BULLISH|BEARISH|NEUTRAL",
                "investment_thesis": "tesis de inversión concisa considerando todas las métricas"
            }}
            """

            data = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": "Responde ÚNICAMENTE con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }

            start_time = time.time()

            response = requests.post(
                f"{self.xai_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=20
            )

            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                result_text = result["choices"][0]["message"]["content"].strip()

                try:
                    result_json = json.loads(result_text)
                except:
                    result_json = {"error": "Respuesta no es JSON válido", "raw_response": result_text}

                return {
                    "provider": "xAI",
                    "model": model_id,
                    "crypto": crypto['short'],
                    "response_time": round(end_time - start_time, 2),
                    "result": result_json,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"xAI API Error: {response.status_code}"}

        except Exception as e:
            return {"error": f"Error con xAI {model_id}: {str(e)}"}

    def get_openai_valuation(self, crypto: Dict, payload: Dict) -> Dict[str, Any]:
        """Obtener valoración de GPT-4o."""

        if not self.openai_available:
            return {"error": "OpenAI no disponible"}

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)

            prompt = f"""
            Eres un analista senior de criptomonedas con 15+ años de experiencia en mercados financieros.

            DATOS TÉCNICOS DE {crypto['name']} ({crypto['short']}):
            - Precio actual: ${payload['technical_data']['price']:,.2f}
            - Cambio 1h: {payload['technical_data']['change_1h']:.2f}%
            - Cambio 24h: {payload['technical_data']['change_24h']:.2f}%
            - Volumen 24h: ${payload['technical_data']['volume_24h']/1e9:.1f}B
            - Market Cap: ${payload['technical_data']['market_cap']/1e12:.2f}T

            MÉTRICAS COINGECKO DETALLADAS:
            - Developer Score: {payload['coingecko_metrics'].get('developer_score', 'N/A')}/100
            - Community Score: {payload['coingecko_metrics'].get('community_score', 'N/A')}/100
            - Liquidity Score: {payload['coingecko_metrics'].get('liquidity_score', 'N/A')}/100
            - GitHub Stars: {payload['coingecko_metrics'].get('github_stars', 0):,}
            - GitHub Commits (4 semanas): {payload['coingecko_metrics'].get('github_commits_last_4_weeks', 0)}
            - Twitter Followers: {payload['coingecko_metrics'].get('twitter_followers', 0):,}
            - Reddit Subscribers: {payload['coingecko_metrics'].get('reddit_subscribers', 0):,}
            - Market Cap Rank: #{payload['coingecko_metrics'].get('market_cap_rank', 'N/A')}

            SENTIMIENTO DE MERCADO GLOBAL:
            - Fear & Greed Index: {payload['market_sentiment']['fear_greed_index'].get('value', 'N/A')} ({payload['market_sentiment']['fear_greed_index'].get('value_text', 'Unknown')})
            - Market Cap Total: ${payload['market_sentiment']['global_crypto_metrics'].get('total_market_cap', {}).get('usd', 0)/1e12:.2f}T
            - BTC Dominance: {payload['market_sentiment']['global_crypto_metrics'].get('market_cap_percentage', {}).get('btc', 0):.1f}%

            ANÁLISIS DE SENTIMIENTO CRYPTOPANIC:
            - Sentimiento General: {payload['market_news'].get('market_sentiment_cryptopanic', 'UNKNOWN')}
            - Bullish: {payload['market_news'].get('cryptopanic_sentiment', {}).get('bullish', {}).get('percentage', 0):.1f}%
            - Bearish: {payload['market_news'].get('cryptopanic_sentiment', {}).get('bearish', {}).get('percentage', 0):.1f}%
            - Neutral: {payload['market_news'].get('cryptopanic_sentiment', {}).get('neutral', {}).get('percentage', 0):.1f}%

            NOTICIAS GENERALES:
            {json.dumps(payload['market_news']['general_news'], indent=2, ensure_ascii=False)}

            NOTICIAS CRYPTOPANIC CON SENTIMIENTO:
            {json.dumps(payload['market_news']['cryptopanic_news'], indent=2, ensure_ascii=False)}

            CONTEXTO ECONÓMICO GLOBAL:
            {json.dumps(payload['global_economic_context'], indent=2, ensure_ascii=False)}

            TAREA: Proporciona una valoración COMPREHENSIVA de {crypto['short']} considerando TODAS las métricas disponibles, especialmente las de desarrollo, comunidad y sentimiento de mercado.

            FORMATO DE RESPUESTA (JSON estricto):
            {{
                "long_signal": 0.750,
                "short_signal": 0.250,
                "confidence_level": 0.85,
                "price_target_long": 95000,
                "price_target_short": 85000,
                "key_drivers_long": ["driver1", "driver2"],
                "key_drivers_short": ["driver1", "driver2"],
                "technical_analysis": "análisis técnico detallado",
                "fundamental_analysis": "análisis fundamental incluyendo métricas CoinGecko",
                "coingecko_insights": "análisis específico de developer score, community engagement, etc.",
                "market_sentiment": "NEUTRAL",
                "investment_thesis": "tesis de inversión considerando todas las métricas"
            }}
            """

            start_time = time.time()

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un analista de inversiones experto. Responde ÚNICAMENTE con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            end_time = time.time()

            result_text = response.choices[0].message.content.strip()

            try:
                result_json = json.loads(result_text)
            except:
                result_json = {"error": "Respuesta no es JSON válido", "raw_response": result_text}

            return {
                "provider": "OpenAI",
                "model": "GPT-4o",
                "crypto": crypto['short'],
                "response_time": round(end_time - start_time, 2),
                "result": result_json,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Error con OpenAI: {str(e)}"}

    def get_grok_valuation(self, crypto: Dict, payload: Dict) -> Dict[str, Any]:
        """Obtener valoración de Grok (xAI)."""

        if not self.xai_available:
            return {"error": "xAI no disponible"}

        try:
            headers = {
                "Authorization": f"Bearer {self.xai_api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""
            Eres Grok, una IA creada por xAI. Analiza {crypto['name']} ({crypto['short']}) de forma objetiva y directa.

            DATOS TÉCNICOS:
            - Precio: ${payload['technical_data']['price']:,.2f}
            - Cambio 1h: {payload['technical_data']['change_1h']:.2f}%
            - Cambio 24h: {payload['technical_data']['change_24h']:.2f}%
            - Volumen: ${payload['technical_data']['volume_24h']/1e9:.1f}B
            - Market Cap: ${payload['technical_data']['market_cap']/1e12:.2f}T

            MÉTRICAS COINGECKO DETALLADAS:
            - Developer Score: {payload['coingecko_metrics'].get('developer_score', 'N/A')}/100
            - Community Score: {payload['coingecko_metrics'].get('community_score', 'N/A')}/100
            - Liquidity Score: {payload['coingecko_metrics'].get('liquidity_score', 'N/A')}/100
            - GitHub Stars: {payload['coingecko_metrics'].get('github_stars', 0):,}
            - GitHub Commits (4 semanas): {payload['coingecko_metrics'].get('github_commits_last_4_weeks', 0)}
            - Twitter Followers: {payload['coingecko_metrics'].get('twitter_followers', 0):,}
            - Reddit Subscribers: {payload['coingecko_metrics'].get('reddit_subscribers', 0):,}
            - Market Cap Rank: #{payload['coingecko_metrics'].get('market_cap_rank', 'N/A')}

            SENTIMIENTO DE MERCADO GLOBAL:
            - Fear & Greed Index: {payload['market_sentiment']['fear_greed_index'].get('value', 'N/A')} ({payload['market_sentiment']['fear_greed_index'].get('value_text', 'Unknown')})
            - Market Cap Total: ${payload['market_sentiment']['global_crypto_metrics'].get('total_market_cap', {}).get('usd', 0)/1e12:.2f}T
            - BTC Dominance: {payload['market_sentiment']['global_crypto_metrics'].get('market_cap_percentage', {}).get('btc', 0):.1f}%

            ANÁLISIS DE SENTIMIENTO CRYPTOPANIC:
            - Sentimiento General: {payload['market_news'].get('market_sentiment_cryptopanic', 'UNKNOWN')}
            - Bullish: {payload['market_news'].get('cryptopanic_sentiment', {}).get('bullish', {}).get('percentage', 0):.1f}%
            - Bearish: {payload['market_news'].get('cryptopanic_sentiment', {}).get('bearish', {}).get('percentage', 0):.1f}%
            - Neutral: {payload['market_news'].get('cryptopanic_sentiment', {}).get('neutral', {}).get('percentage', 0):.1f}%

            NOTICIAS GENERALES:
            {json.dumps(payload['market_news']['general_news'], indent=2, ensure_ascii=False)}

            NOTICIAS CRYPTOPANIC CON SENTIMIENTO:
            {json.dumps(payload['market_news']['cryptopanic_news'], indent=2, ensure_ascii=False)}

            CONTEXTO ECONÓMICO GLOBAL:
            {json.dumps(payload['global_economic_context'], indent=2, ensure_ascii=False)}

            Brinda una valoración completa considerando el panorama económico global, adopción institucional y métricas CoinGecko.

            FORMATO DE RESPUESTA (JSON estricto):
            {{
                "long_signal": 0.750,
                "short_signal": 0.250,
                "confidence_level": 0.80,
                "price_target_long": 95000,
                "price_target_short": 85000,
                "key_drivers_long": ["driver1", "driver2"],
                "key_drivers_short": ["driver1", "driver2"],
                "technical_analysis": "análisis técnico",
                "fundamental_analysis": "análisis fundamental incluyendo métricas CoinGecko",
                "coingecko_insights": "análisis específico de developer score, community engagement, etc.",
                "market_sentiment": "BULLISH|BEARISH|NEUTRAL",
                "investment_thesis": "tesis de inversión concisa considerando todas las métricas"
            }}
            """

            data = {
                "model": "grok-3",
                "messages": [
                    {"role": "system", "content": "Responde ÚNICAMENTE con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }

            start_time = time.time()

            response = requests.post(
                f"{self.xai_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=20
            )

            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                result_text = result["choices"][0]["message"]["content"].strip()

                try:
                    result_json = json.loads(result_text)
                except:
                    result_json = {"error": "Respuesta no es JSON válido", "raw_response": result_text}

                return {
                    "provider": "xAI",
                    "model": "Grok",
                    "crypto": crypto['short'],
                    "response_time": round(end_time - start_time, 2),
                    "result": result_json,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"xAI API Error: {response.status_code}"}

        except Exception as e:
            return {"error": f"Error con xAI: {str(e)}"}

    def run_comprehensive_valuation(self) -> Dict[str, Any]:
        """Ejecutar valoración completa de todas las criptos."""

        print("\n🚀 INICIANDO VALORACIÓN COMPREHENSIVA CON IA")
        print("=" * 80)

        results = {
            "timestamp": datetime.now().isoformat(),
            "cryptos_analyzed": [c['short'] for c in self.cryptos],
            "valuations": {}
        }

        # Fase 1: Obtener datos de mercado
        print("\n📊 Fase 1: Obteniendo datos técnicos...")
        market_data = {}
        for crypto in self.cryptos:
            print(f"   🔍 {crypto['short']}...")
            data = self.get_crypto_data(crypto['symbol'])
            market_data[crypto['short']] = data
            if data.get('success'):
                print(f"      ✅ ${data['price']:,.2f} ({data['change_24h']:.2f}%)")
            else:
                print(f"      ❌ Error: {data.get('error', 'Desconocido')}")

        # Fase 2: Obtener métricas adicionales de CoinGecko
        print("\n🪙 Fase 2: Obteniendo métricas CoinGecko...")
        coingecko_data = {}
        for crypto in self.cryptos:
            print(f"   📈 {crypto['short']} métricas...")
            metrics = self.get_coingecko_metrics(crypto['coingecko_id'])
            coingecko_data[crypto['short']] = metrics
            if metrics.get('success'):
                dev_score = metrics.get('developer_score', 0)
                comm_score = metrics.get('community_score', 0)
                print(f"      ✅ Dev: {dev_score:.1f}, Community: {comm_score:.1f}")
            else:
                print(f"      ⚠️ Sin métricas adicionales")

        # Fase 3: Obtener datos globales y trending
        print("\n🌍 Fase 3: Obteniendo datos globales...")
        fear_greed = self.get_fear_greed_index()
        global_crypto = self.get_global_crypto_data()
        trending_coins = self.get_trending_coins()

        if fear_greed.get('success'):
            fgi_value = fear_greed.get('value', 0)
            fgi_text = fear_greed.get('value_text', 'Unknown')
            print(f"   ✅ Fear & Greed Index: {fgi_value} ({fgi_text})")
        else:
            print("   ⚠️ Fear & Greed Index no disponible")

        if global_crypto.get('success'):
            total_mcap = global_crypto.get('total_market_cap', {}).get('usd', 0)
            print(f"   ✅ Market Cap Total: ${total_mcap/1e12:.2f}T")
        else:
            print("   ⚠️ Datos globales no disponibles")

        # Fase 4: Obtener noticias y contexto económico
        print("\n📰 Fase 4: Obteniendo contexto de mercado...")
        market_news = self.get_market_news()
        cryptopanic_news = self.get_cryptopanic_news(limit=8)
        global_context = self.get_global_economic_context()

        print(f"   ✅ {len(market_news)} noticias tradicionales recopiladas")

        if cryptopanic_news.get("success"):
            sentiment = cryptopanic_news.get("market_sentiment", "UNKNOWN")
            total_cp_news = cryptopanic_news.get("total_news", 0)
            print(f"   ✅ {total_cp_news} noticias CryptoPanic ({sentiment})")
        else:
            print(f"   ⚠️ CryptoPanic no disponible: {cryptopanic_news.get('error', 'Unknown error')}")

        print(f"   ✅ Contexto económico global obtenido")

        # Fase 5: Valoraciones con múltiples modelos
        for crypto in self.cryptos:
            print(f"\n🤖 Fase 5: Valoración Multi-Modelo de {crypto['short']}")
            print("=" * 60)

            # Crear payload específico para esta cripto
            payload = self.create_valuation_payload(
                crypto,
                market_data[crypto['short']],
                coingecko_data[crypto['short']],
                market_news,
                cryptopanic_news,
                global_context,
                fear_greed,
                global_crypto,
                trending_coins
            )

            # Valoraciones con todos los modelos OpenAI
            openai_valuations = {}
            print("   📘 MODELOS OPENAI:")
            for model_info in self.openai_models:
                print(f"      🔄 {model_info['name']} analizando {crypto['short']}...")
                try:
                    result = self.get_openai_valuation_with_model(crypto, payload, model_info['id'])
                    if "error" in result:
                        print(f"         ❌ {model_info['name']}: {result['error']}")
                        openai_valuations[model_info['name']] = None
                    else:
                        long_signal = result['result'].get('long_signal', 0)
                        short_signal = result['result'].get('short_signal', 0)
                        confidence = result['result'].get('confidence_level', 0)
                        print(f"         ✅ {model_info['name']}: LONG {long_signal:.3f} | SHORT {short_signal:.3f} ({confidence:.1%}) - {result['response_time']}s")
                        openai_valuations[model_info['name']] = result
                except Exception as e:
                    print(f"         ❌ {model_info['name']}: Error - {str(e)}")
                    openai_valuations[model_info['name']] = None

            # Valoraciones con todos los modelos xAI
            xai_valuations = {}
            print("   🧠 MODELOS XAI:")
            for model_info in self.xai_models:
                print(f"      🔄 {model_info['name']} analizando {crypto['short']}...")
                try:
                    result = self.get_grok_valuation_with_model(crypto, payload, model_info['id'])
                    if "error" in result:
                        print(f"         ❌ {model_info['name']}: {result['error']}")
                        xai_valuations[model_info['name']] = None
                    else:
                        long_signal = result['result'].get('long_signal', 0)
                        short_signal = result['result'].get('short_signal', 0)
                        confidence = result['result'].get('confidence_level', 0)
                        print(f"         ✅ {model_info['name']}: LONG {long_signal:.3f} | SHORT {short_signal:.3f} ({confidence:.1%}) - {result['response_time']}s")
                        xai_valuations[model_info['name']] = result
                except Exception as e:
                    print(f"         ❌ {model_info['name']}: Error - {str(e)}")
                    xai_valuations[model_info['name']] = None

            # Almacenar resultados
            results["valuations"][crypto['short']] = {
                "crypto_data": market_data[crypto['short']],
                "coingecko_metrics": coingecko_data[crypto['short']],
                "openai_valuations": openai_valuations,
                "xai_valuations": xai_valuations,
                "multi_model_comparison": self._compare_all_models(openai_valuations, xai_valuations)
            }

        # Fase 6: Análisis comparativo final
        print("\n📊 Fase 6: Análisis comparativo final...")
        final_analysis = self._generate_final_analysis(results, fear_greed, global_crypto, trending_coins, cryptopanic_news)
        results["final_analysis"] = final_analysis
        results["market_sentiment"] = {
            "fear_greed_index": fear_greed,
            "global_crypto_metrics": global_crypto,
            "trending_coins": trending_coins,
            "cryptopanic_sentiment": cryptopanic_news
        }

        # Exportar resultados
        filename = self._export_results(results)

        # Mostrar resumen
        self._print_precision_table(results)
        self._print_summary(results)

        return results

    def _compare_all_models(self, openai_valuations: Dict, xai_valuations: Dict) -> Dict[str, Any]:
        """Comparar valoraciones de todos los modelos."""

        all_models = {}

        # Agregar modelos OpenAI
        for model_name, valuation in openai_valuations.items():
            if valuation and 'result' in valuation:
                long_signal = valuation['result'].get('long_signal', 0)
                short_signal = valuation['result'].get('short_signal', 0)
                confidence = valuation['result'].get('confidence_level', 0)
                response_time = valuation.get('response_time', 0)

                all_models[model_name] = {
                    "long_signal": long_signal,
                    "short_signal": short_signal,
                    "confidence": confidence,
                    "response_time": response_time,
                    "precision": abs(long_signal - short_signal),
                    "direction": "LONG" if long_signal > short_signal else "SHORT"
                }

        # Agregar modelos xAI
        for model_name, valuation in xai_valuations.items():
            if valuation and 'result' in valuation:
                long_signal = valuation['result'].get('long_signal', 0)
                short_signal = valuation['result'].get('short_signal', 0)
                confidence = valuation['result'].get('confidence_level', 0)
                response_time = valuation.get('response_time', 0)

                all_models[model_name] = {
                    "long_signal": long_signal,
                    "short_signal": short_signal,
                    "confidence": confidence,
                    "response_time": response_time,
                    "precision": abs(long_signal - short_signal),
                    "direction": "LONG" if long_signal > short_signal else "SHORT"
                }

        # Estadísticas generales
        if all_models:
            long_signals = [m['long_signal'] for m in all_models.values()]
            short_signals = [m['short_signal'] for m in all_models.values()]
            precisions = [m['precision'] for m in all_models.values()]
            confidences = [m['confidence'] for m in all_models.values()]
            response_times = [m['response_time'] for m in all_models.values()]

            # Modelo más preciso
            most_precise = max(all_models.items(), key=lambda x: x[1]['precision'])

            # Modelo más rápido
            fastest = min(all_models.items(), key=lambda x: x[1]['response_time'])

            # Modelo más confiado
            most_confident = max(all_models.items(), key=lambda x: x[1]['confidence'])

            # Consenso general
            avg_long = sum(long_signals) / len(long_signals)
            avg_short = sum(short_signals) / len(short_signals)
            consensus_direction = "LONG" if avg_long > avg_short else "SHORT"

            return {
                "models_count": len(all_models),
                "models_data": all_models,
                "statistics": {
                    "avg_long_signal": round(avg_long, 3),
                    "avg_short_signal": round(avg_short, 3),
                    "avg_precision": round(sum(precisions) / len(precisions), 3),
                    "avg_confidence": round(sum(confidences) / len(confidences), 3),
                    "avg_response_time": round(sum(response_times) / len(response_times), 2)
                },
                "best_models": {
                    "most_precise": most_precise[0],
                    "fastest": fastest[0],
                    "most_confident": most_confident[0]
                },
                "consensus": {
                    "direction": consensus_direction,
                    "strength": round(abs(avg_long - avg_short), 3)
                }
            }

        return {"error": "No hay modelos para comparar"}

    def _compare_valuations(self, openai: Dict, grok: Dict) -> Dict[str, Any]:
        """Comparar valoraciones de ambas AIs."""

        try:
            # Obtener scores de long y short
            openai_long = openai['result'].get('long_signal', 0)
            openai_short = openai['result'].get('short_signal', 0)
            grok_long = grok['result'].get('long_signal', 0)
            grok_short = grok['result'].get('short_signal', 0)

            # Calcular precisión (qué tan extremos son los scores)
            openai_precision = abs(openai_long - openai_short)
            grok_precision = abs(grok_long - grok_short)

            # Acuerdo en dirección (si ambos ven más long que short o viceversa)
            openai_direction = "LONG" if openai_long > openai_short else "SHORT"
            grok_direction = "LONG" if grok_long > grok_short else "SHORT"
            direction_agreement = openai_direction == grok_direction

            # Diferencias absolutas
            long_diff = abs(openai_long - grok_long)
            short_diff = abs(openai_short - grok_short)
            avg_diff = (long_diff + short_diff) / 2

            # Diferencia en targets de precio
            openai_target_long = openai['result'].get('price_target_long', 0)
            grok_target_long = grok['result'].get('price_target_long', 0)

            target_diff_pct = 0
            if openai_target_long > 0 and grok_target_long > 0:
                target_diff_pct = ((grok_target_long - openai_target_long) / openai_target_long) * 100

            # Score de consenso (promedio de long signals)
            consensus_long = (openai_long + grok_long) / 2
            consensus_short = (openai_short + grok_short) / 2

            return {
                "direction_agreement": direction_agreement,
                "openai_direction": openai_direction,
                "grok_direction": grok_direction,
                "long_signal_diff": round(long_diff, 3),
                "short_signal_diff": round(short_diff, 3),
                "avg_signal_diff": round(avg_diff, 3),
                "openai_precision": round(openai_precision, 3),
                "grok_precision": round(grok_precision, 3),
                "consensus_long": round(consensus_long, 3),
                "consensus_short": round(consensus_short, 3),
                "confidence_avg": round((openai['result'].get('confidence_level', 0) + grok['result'].get('confidence_level', 0)) / 2, 3),
                "target_price_difference_pct": round(target_diff_pct, 2),
                "precision_comparison": "GPT-4o más preciso" if openai_precision > grok_precision else "Grok más preciso" if grok_precision > openai_precision else "Precisión similar"
            }

        except Exception as e:
            return {"error": str(e)}

    def _generate_final_analysis(self, results: Dict, fear_greed: Dict, global_crypto: Dict, trending_coins: Dict, cryptopanic_news: Dict) -> Dict[str, Any]:
        """Generar análisis final del mercado con múltiples modelos."""

        valuations = results.get("valuations", {})

        # Análisis global de todos los modelos
        all_long_signals = []
        all_short_signals = []
        model_performance = {}

        for crypto, data in valuations.items():
            multi_comp = data.get('multi_model_comparison', {})
            if multi_comp and 'models_data' in multi_comp:
                models_data = multi_comp['models_data']
                for model_name, model_data in models_data.items():
                    all_long_signals.append(model_data['long_signal'])
                    all_short_signals.append(model_data['short_signal'])

                    if model_name not in model_performance:
                        model_performance[model_name] = {
                            'long_signals': [],
                            'short_signals': [],
                            'precisions': [],
                            'response_times': []
                        }

                    model_performance[model_name]['long_signals'].append(model_data['long_signal'])
                    model_performance[model_name]['short_signals'].append(model_data['short_signal'])
                    model_performance[model_name]['precisions'].append(model_data['precision'])
                    model_performance[model_name]['response_times'].append(model_data['response_time'])

        # Calcular estadísticas globales
        if all_long_signals and all_short_signals:
            avg_long = sum(all_long_signals) / len(all_long_signals)
            avg_short = sum(all_short_signals) / len(all_short_signals)
            long_ratio = sum(1 for l, s in zip(all_long_signals, all_short_signals) if l > s) / len(all_long_signals)

            market_sentiment = "BULLISH" if long_ratio > 0.6 else "BEARISH" if long_ratio < 0.4 else "NEUTRAL"
        else:
            avg_long = avg_short = long_ratio = 0
            market_sentiment = "NEUTRAL"

        # Rankings de modelos
        model_stats = {}
        for model_name, perf in model_performance.items():
            if perf['precisions']:
                model_stats[model_name] = {
                    'avg_precision': sum(perf['precisions']) / len(perf['precisions']),
                    'avg_response_time': sum(perf['response_times']) / len(perf['response_times']),
                    'avg_long_signal': sum(perf['long_signals']) / len(perf['long_signals'])
                }

        # Modelos top
        if model_stats:
            most_precise_model = max(model_stats.items(), key=lambda x: x[1]['avg_precision'])[0]
            fastest_model = min(model_stats.items(), key=lambda x: x[1]['avg_response_time'])[0]
            most_bullish_model = max(model_stats.items(), key=lambda x: x[1]['avg_long_signal'])[0]
        else:
            most_precise_model = fastest_model = most_bullish_model = "N/A"

        # Análisis del Fear & Greed Index
        fgi_value = fear_greed.get('value', 50)
        fgi_sentiment = "FEAR" if fgi_value < 25 else "GREED" if fgi_value > 75 else "NEUTRAL"

        # Análisis de sentimiento CryptoPanic
        cp_sentiment = "NEUTRAL"
        if cryptopanic_news.get('success'):
            cp_sentiment = cryptopanic_news.get('market_sentiment', 'NEUTRAL')
            cp_bullish_pct = cryptopanic_news.get('sentiment_metrics', {}).get('bullish', {}).get('percentage', 0)
            cp_bearish_pct = cryptopanic_news.get('sentiment_metrics', {}).get('bearish', {}).get('percentage', 0)
        else:
            cp_bullish_pct = cp_bearish_pct = 0

        # Análisis de métricas de desarrollo
        dev_scores = {}
        for crypto, data in valuations.items():
            if data.get('coingecko_metrics', {}).get('success'):
                dev_scores[crypto] = data['coingecko_metrics'].get('developer_score', 0)

        best_developer = max(dev_scores, key=dev_scores.get) if dev_scores else "N/A"

        return {
            "market_sentiment": market_sentiment,
            "long_signals_ratio": round(long_ratio, 3),
            "avg_long_signal": round(avg_long, 3),
            "avg_short_signal": round(avg_short, 3),
            "most_recommended_crypto": self._find_most_recommended(valuations),
            "model_performance": model_stats,
            "top_models": {
                "most_precise": most_precise_model,
                "fastest": fastest_model,
                "most_bullish": most_bullish_model
            },
            "fear_greed_analysis": {
                "value": fgi_value,
                "sentiment": fgi_sentiment,
                "interpretation": f"Fear & Greed Index en {fgi_value} indica {fgi_sentiment.lower()}"
            },
            "cryptopanic_sentiment_analysis": {
                "market_sentiment": cp_sentiment,
                "bullish_percentage": cp_bullish_pct,
                "bearish_percentage": cp_bearish_pct,
                "interpretation": f"CryptoPanic indica sentimiento {cp_sentiment.lower()} con {cp_bullish_pct:.1f}% bullish y {cp_bearish_pct:.1f}% bearish"
            },
            "developer_activity": {
                "best_developer": best_developer,
                "scores": dev_scores
            },
            "key_insights": [
                f"Mercado general: {market_sentiment}",
                f"Señales LONG promedio: {avg_long:.3f} | SHORT promedio: {avg_short:.3f}",
                f"Ratio señales LONG: {long_ratio:.1%}",
                f"Modelo más preciso: {most_precise_model}",
                f"Modelo más rápido: {fastest_model}",
                f"Fear & Greed Index: {fgi_value} ({fgi_sentiment})",
                f"CryptoPanic sentimiento: {cp_sentiment} ({cp_bullish_pct:.1f}% bullish)",
                f"Mejor actividad de desarrollo: {best_developer}",
                "Análisis de sentimiento CryptoPanic proporciona señal adicional",
                "Múltiples modelos AIs proporcionan análisis diversificado",
                "Contexto económico global y sentimiento de mercado influyen en todas las valoraciones"
            ]
        }

    def _find_most_recommended(self, valuations: Dict) -> str:
        """Encontrar la cripto más recomendada basada en scores LONG de múltiples modelos."""

        recommendations = {}

        for crypto, data in valuations.items():
            total_long_score = 0
            model_count = 0

            # Modelos OpenAI
            openai_vals = data.get('openai_valuations', {})
            for model_name, valuation in openai_vals.items():
                if valuation and 'result' in valuation:
                    long_signal = valuation['result'].get('long_signal', 0)
                    total_long_score += long_signal
                    model_count += 1

            # Modelos xAI
            xai_vals = data.get('xai_valuations', {})
            for model_name, valuation in xai_vals.items():
                if valuation and 'result' in valuation:
                    long_signal = valuation['result'].get('long_signal', 0)
                    total_long_score += long_signal
                    model_count += 1

            # Calcular score promedio de LONG
            avg_long_score = total_long_score / model_count if model_count > 0 else 0
            recommendations[crypto] = avg_long_score

        return max(recommendations, key=recommendations.get) if recommendations else "N/A"

    def _export_results(self, results: Dict) -> str:
        """Exportar resultados a JSON."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_crypto_valuation_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Resultados exportados a: {filename}")
        return filename

    def _print_precision_table(self, results: Dict):
        """Mostrar tabla comparativa de precisión de múltiples modelos IA."""

        valuations = results.get("valuations", {})

        print("\n" + "=" * 140)
        print("📊 TABLA COMPARATIVA DE PRECISIÓN: MÚLTIPLES MODELOS IA")
        print("=" * 140)

        # Recopilar estadísticas de todos los modelos
        model_stats = {}

        for crypto, data in valuations.items():
            multi_comp = data.get('multi_model_comparison', {})
            if multi_comp and 'models_data' in multi_comp:
                models_data = multi_comp['models_data']
                for model_name, model_data in models_data.items():
                    if model_name not in model_stats:
                        model_stats[model_name] = {
                            'cryptos': [],
                            'precisions': [],
                            'long_signals': [],
                            'response_times': []
                        }

                    model_stats[model_name]['cryptos'].append(crypto)
                    model_stats[model_name]['precisions'].append(model_data['precision'])
                    model_stats[model_name]['long_signals'].append(model_data['long_signal'])
                    model_stats[model_name]['response_times'].append(model_data['response_time'])

        # Mostrar estadísticas por modelo
        print("<12")
        print("-" * 140)

        for model_name, stats in sorted(model_stats.items()):
            if stats['precisions']:
                avg_precision = sum(stats['precisions']) / len(stats['precisions'])
                avg_long = sum(stats['long_signals']) / len(stats['long_signals'])
                avg_time = sum(stats['response_times']) / len(stats['response_times'])
                total_evals = len(stats['precisions'])

                print("<12")

        print("-" * 140)

        # Rankings finales
        if model_stats:
            # Modelo más preciso
            most_precise = max(model_stats.items(),
                             key=lambda x: sum(x[1]['precisions']) / len(x[1]['precisions']) if x[1]['precisions'] else 0)
            most_precise_name = most_precise[0]
            most_precise_score = sum(most_precise[1]['precisions']) / len(most_precise[1]['precisions'])

            # Modelo más rápido
            fastest = min(model_stats.items(),
                         key=lambda x: sum(x[1]['response_times']) / len(x[1]['response_times']) if x[1]['response_times'] else float('inf'))
            fastest_name = fastest[0]
            fastest_time = sum(fastest[1]['response_times']) / len(fastest[1]['response_times'])

            # Modelo más bullish
            most_bullish = max(model_stats.items(),
                              key=lambda x: sum(x[1]['long_signals']) / len(x[1]['long_signals']) if x[1]['long_signals'] else 0)
            most_bullish_name = most_bullish[0]
            most_bullish_score = sum(most_bullish[1]['long_signals']) / len(most_bullish[1]['long_signals'])

            print("🏆 RANKINGS FINALES:")
            print(f"   🏹 Más preciso: {most_precise_name} (precisión: {most_precise_score:.3f})")
            print(f"   ⚡ Más rápido: {fastest_name} (tiempo: {fastest_time:.2f}s)")
            print(f"   🚀 Más bullish: {most_bullish_name} (LONG avg: {most_bullish_score:.3f})")

        print("\n" + "=" * 140)

    def _print_summary(self, results: Dict):
        """Mostrar resumen final."""

        print("\n" + "=" * 80)
        print("📊 RESUMEN FINAL - VALORACIONES IA")
        print("=" * 80)

        valuations = results.get("valuations", {})

        for crypto, data in valuations.items():
            print(f"\n🪙 {crypto}")
            print("-" * 40)

            # Modelos OpenAI
            print("   🤖 OPENAI MODELS:")
            openai_vals = data.get('openai_valuations', {})
            for model_name, valuation in openai_vals.items():
                if valuation and 'result' in valuation:
                    long_signal = valuation['result'].get('long_signal', 0)
                    short_signal = valuation['result'].get('short_signal', 0)
                    confidence = valuation['result'].get('confidence_level', 0)
                    print(f"      {model_name}: LONG {long_signal:.3f} | SHORT {short_signal:.3f} ({confidence:.1%})")
                else:
                    print(f"      {model_name}: ❌ No disponible")

            # Modelos xAI
            print("   🧠 XAI MODELS:")
            xai_vals = data.get('xai_valuations', {})
            for model_name, valuation in xai_vals.items():
                if valuation and 'result' in valuation:
                    long_signal = valuation['result'].get('long_signal', 0)
                    short_signal = valuation['result'].get('short_signal', 0)
                    confidence = valuation['result'].get('confidence_level', 0)
                    print(f"      {model_name}: LONG {long_signal:.3f} | SHORT {short_signal:.3f} ({confidence:.1%})")
                else:
                    print(f"      {model_name}: ❌ No disponible")

            # Métricas de CoinGecko
            cg_metrics = data.get('coingecko_metrics', {})
            if cg_metrics.get('success'):
                print(f"   🛠️  Developer Score: {cg_metrics.get('developer_score', 0):.1f}/100")
                print(f"   👥 Community Score: {cg_metrics.get('community_score', 0):.1f}/100")
                if cg_metrics.get('github_stars', 0) > 0:
                    print(f"   ⭐ GitHub Stars: {cg_metrics.get('github_stars', 0):,}")
                if cg_metrics.get('twitter_followers', 0) > 0:
                    print(f"   🐦 Twitter: {cg_metrics.get('twitter_followers', 0):,}")

            # Comparación multi-modelo
            multi_comp = data.get('multi_model_comparison', {})
            if multi_comp and 'statistics' in multi_comp:
                stats = multi_comp['statistics']
                consensus = multi_comp.get('consensus', {})
                best = multi_comp.get('best_models', {})
                print(f"   📊 Estadísticas: Avg LONG {stats['avg_long_signal']:.3f} | SHORT {stats['avg_short_signal']:.3f}")
                print(f"   🎯 Consenso: {consensus.get('direction', 'N/A')} (fuerza: {consensus.get('strength', 0):.3f})")
                print(f"   🏆 Más preciso: {best.get('most_precise', 'N/A')} | Más rápido: {best.get('fastest', 'N/A')}")

        # Tabla comparativa de precisión
        self._print_precision_table(results)

        # Análisis final
        final = results.get("final_analysis", {})
        if final:
            print(f"\n🎯 ANÁLISIS DE MERCADO:")
            print(f"   📈 Sentimiento general: {final.get('market_sentiment', 'N/A')}")
            print(f"   🏆 Más recomendado: {final.get('most_recommended_crypto', 'N/A')}")

            # Información del Fear & Greed Index
            fgi = final.get('fear_greed_analysis', {})
            if fgi:
                print(f"   😨 Fear & Greed Index: {fgi.get('value', 'N/A')} ({fgi.get('sentiment', 'N/A')})")

            # Información de CryptoPanic
            cp = final.get('cryptopanic_sentiment_analysis', {})
            if cp:
                print(f"   📰 CryptoPanic: {cp.get('market_sentiment', 'N/A')} ({cp.get('bullish_percentage', 0):.1f}% bullish)")

            # Información de desarrollo
            dev = final.get('developer_activity', {})
            if dev and dev.get('best_developer') != 'N/A':
                print(f"   🛠️  Mejor desarrollo: {dev.get('best_developer', 'N/A')}")

            print(f"\n💡 INSIGHTS CLAVE:")
            for insight in final.get('key_insights', []):
                print(f"   • {insight}")


def main():
    """Función principal."""

    print("🚀 VALORACIÓN DE CRIPTOMONEDAS CON IA")
    print("GPT-4o vs Grok - Análisis comprehensivo")
    print("=" * 60)

    try:
        # Crear sistema de valoración
        valuer = AICryptoValuation()

        # Verificar que tengamos al menos una API
        if not valuer.openai_available and not valuer.xai_available:
            print("❌ Error: Necesitas al menos una API (OpenAI o xAI)")
            return

        if not valuer.yfinance_available:
            print("❌ Error: yfinance es requerido para datos de mercado")
            return

        # Ejecutar valoración completa
        results = valuer.run_comprehensive_valuation()

        print("\n✅ Valoración completada exitosamente!")
        print("\n💡 Las valoraciones consideran:")
        print("   • Datos técnicos en tiempo real")
        print("   • Noticias recientes del mercado")
        print("   • Análisis de sentimiento CryptoPanic")
        print("   • Contexto económico global")
        print("   • Factores fundamentales y regulatorios")
        print("   • Métricas sociales y de desarrollo")

    except Exception as e:
        print(f"❌ Error en la valoración: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
