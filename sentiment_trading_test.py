#!/usr/bin/env python3
"""
Prueba de Análisis de Sentimiento de Mercado con OpenAI y xAI
Valoración de oportunidades de trading para BTC/USDT

Este script obtiene:
1. Datos de noticias de yfinance
2. Precio actual de BTC
3. Envía análisis estructurado a OpenAI y xAI para valoración numérica
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar librerías necesarias
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance no disponible. Instala con: pip install yfinance")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai no disponible. Instala con: pip install openai")


class SentimentTradingTest:
    """Clase para pruebas de análisis de sentimiento y valoración de trading."""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.xai_api_key = os.getenv("XAI_API_KEY", "").strip()
        self.xai_base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")

        # Configuración de modelos
        self.openai_model = "gpt-4o"  # Modelo principal para análisis complejo
        self.xai_model = "grok-3"

        # Validar conexiones
        self.openai_available = self._validate_openai()
        self.xai_available = self._validate_xai()
        self.yfinance_available = YFINANCE_AVAILABLE

        print("🚀 Sentiment Trading Test Inicializado")
        print(f"   OpenAI: {'✅' if self.openai_available else '❌'}")
        print(f"   xAI: {'✅' if self.xai_available else '❌'}")
        print(f"   yfinance: {'✅' if self.yfinance_available else '❌'}")

    def _validate_openai(self) -> bool:
        """Validar conexión con OpenAI."""
        if not self.openai_api_key:
            print("❌ OPENAI_API_KEY no encontrada")
            return False

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            # Prueba simple de conexión
            client.models.list()
            return True
        except Exception as e:
            print(f"❌ Error conectando con OpenAI: {e}")
            return False

    def _validate_xai(self) -> bool:
        """Validar conexión con xAI."""
        if not self.xai_api_key:
            print("❌ XAI_API_KEY no encontrada")
            return False

        try:
            headers = {"Authorization": f"Bearer {self.xai_api_key}"}
            response = requests.get(f"{self.xai_base_url}/models", headers=headers, timeout=10)

            if response.status_code == 200:
                return True
            else:
                print(f"❌ Error xAI API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error conectando con xAI: {e}")
            return False

    def get_btc_price_data(self) -> Dict[str, Any]:
        """
        Obtener precio actual de BTC y datos técnicos recientes.

        Returns:
            Dict con precio actual, cambios, y datos técnicos
        """
        if not self.yfinance_available:
            return {"error": "yfinance no disponible"}

        try:
            # Obtener datos de BTC-USD
            btc = yf.Ticker("BTC-USD")

            # Precio actual
            current_price = btc.history(period="1d", interval="1m").iloc[-1]['Close']

            # Datos de las últimas 24 horas
            daily_data = btc.history(period="1d", interval="1h")

            # Cambios porcentuales
            price_24h_ago = daily_data.iloc[0]['Close']
            price_1h_ago = daily_data.iloc[-2]['Close'] if len(daily_data) > 1 else current_price

            change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
            change_1h = ((current_price - price_1h_ago) / price_1h_ago) * 100

            # Volumen
            volume_24h = daily_data['Volume'].sum()

            # Datos técnicos básicos
            high_24h = daily_data['High'].max()
            low_24h = daily_data['Low'].min()

            return {
                "current_price": round(current_price, 2),
                "change_24h_pct": round(change_24h, 2),
                "change_1h_pct": round(change_1h, 2),
                "high_24h": round(high_24h, 2),
                "low_24h": round(low_24h, 2),
                "volume_24h": int(volume_24h),
                "timestamp": datetime.now().isoformat(),
                "symbol": "BTC-USD"
            }

        except Exception as e:
            return {"error": f"Error obteniendo precio BTC: {str(e)}"}

    def get_market_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtener noticias recientes de mercado usando yfinance.

        Args:
            limit: Número máximo de noticias a obtener

        Returns:
            Lista de noticias con título, fecha, y fuente
        """
        if not self.yfinance_available:
            return [{"error": "yfinance no disponible"}]

        try:
            # Obtener noticias de BTC y mercados crypto
            tickers = ["BTC-USD", "^GSPC", "^IXIC"]  # BTC, S&P 500, Nasdaq

            all_news = []

            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    news = stock.news

                    for item in news[:limit//len(tickers)]:
                        news_item = {
                            "title": item.get("title", ""),
                            "publisher": item.get("publisher", ""),
                            "link": item.get("link", ""),
                            "timestamp": item.get("providerPublishTime", 0),
                            "related_ticker": ticker,
                            "date": datetime.fromtimestamp(item.get("providerPublishTime", 0)).isoformat()
                        }
                        all_news.append(news_item)

                except Exception as e:
                    print(f"⚠️ Error obteniendo noticias de {ticker}: {e}")
                    continue

            # Ordenar por fecha más reciente
            all_news.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

            return all_news[:limit]

        except Exception as e:
            return [{"error": f"Error obteniendo noticias: {str(e)}"}]

    def create_analysis_payload(self, btc_data: Dict, news_data: List) -> Dict[str, Any]:
        """
        Crear payload JSON estructurado para enviar a las APIs.

        Args:
            btc_data: Datos de precio y técnico de BTC
            news_data: Lista de noticias recientes

        Returns:
            Dict estructurado con toda la información necesaria
        """
        # Limpiar datos de error si existen
        if "error" in btc_data:
            btc_data = {"current_price": 0, "change_24h_pct": 0, "error": btc_data["error"]}

        # Filtrar noticias válidas
        valid_news = [n for n in news_data if "error" not in n]

        payload = {
            "timestamp": datetime.now().isoformat(),
            "market_data": {
                "btc_usd": btc_data
            },
            "news": {
                "count": len(valid_news),
                "items": valid_news[:5],  # Limitar a 5 noticias más recientes
                "sources": list(set([n.get("publisher", "") for n in valid_news if n.get("publisher")]))
            },
            "analysis_request": {
                "task": "market_sentiment_analysis",
                "objective": "Evaluar condiciones actuales para operación LONG en BTC",
                "requirements": [
                    "Analizar sentimiento de mercado basado en noticias",
                    "Evaluar momentum técnico actual",
                    "Proporcionar valoración numérica: -1 (muy negativo) a +1 (muy positivo)",
                    "Recomendar si es buena oportunidad para compra LONG",
                    "Explicar factores principales que influyen en la decisión"
                ]
            }
        }

        return payload

    def analyze_with_openai(self, payload: Dict) -> Dict[str, Any]:
        """
        Analizar datos con OpenAI GPT-4o.

        Args:
            payload: Datos estructurados del mercado

        Returns:
            Dict con análisis, valoración y metadata
        """
        if not self.openai_available:
            return {"error": "OpenAI no disponible", "valuation": 0}

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)

            prompt = f"""
            Eres un analista senior de criptomonedas con 10+ años de experiencia.

            DATOS DE MERCADO:
            - BTC Precio actual: ${payload['market_data']['btc_usd'].get('current_price', 'N/A')}
            - Cambio 24h: {payload['market_data']['btc_usd'].get('change_24h_pct', 'N/A')}%
            - Cambio 1h: {payload['market_data']['btc_usd'].get('change_1h_pct', 'N/A')}%

            NOTICIAS RECIENTES:
            {json.dumps(payload['news']['items'], indent=2, ensure_ascii=False)}

            TAREA:
            1. Analiza el sentimiento general del mercado basado en las noticias
            2. Evalúa el momentum técnico actual
            3. Proporciona una valoración numérica entre -1 (muy negativo) y +1 (muy positivo)
            4. Recomienda si es buena oportunidad para COMPRA LONG en BTC
            5. Explica brevemente los 3 factores principales

            FORMATO DE RESPUESTA (JSON estricto):
            {{
                "sentiment_score": float,
                "technical_momentum": "bullish|bearish|neutral",
                "recommendation": "BUY_LONG|AVOID|HOLD",
                "confidence_level": float,
                "key_factors": ["factor1", "factor2", "factor3"],
                "analysis": "breve explicación en español"
            }}
            """

            start_time = time.time()

            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "Eres un analista de mercados experto. Responde ÚNICAMENTE con JSON válido, sin texto adicional."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            end_time = time.time()

            result_text = response.choices[0].message.content.strip()

            try:
                result_json = json.loads(result_text)
            except json.JSONDecodeError:
                result_json = {"error": "Respuesta no es JSON válido", "raw_response": result_text}

            return {
                "provider": "OpenAI",
                "model": self.openai_model,
                "response_time": round(end_time - start_time, 2),
                "result": result_json,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Error con OpenAI: {str(e)}", "valuation": 0}

    def analyze_with_xai(self, payload: Dict) -> Dict[str, Any]:
        """
        Analizar datos con xAI Grok.

        Args:
            payload: Datos estructurados del mercado

        Returns:
            Dict con análisis, valoración y metadata
        """
        if not self.xai_available:
            return {"error": "xAI no disponible", "valuation": 0}

        try:
            headers = {
                "Authorization": f"Bearer {self.xai_api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""
            Eres Grok, una IA creada por xAI. Analiza el mercado crypto de forma objetiva y directa.

            DATOS DE MERCADO:
            - BTC Precio actual: ${payload['market_data']['btc_usd'].get('current_price', 'N/A')}
            - Cambio 24h: {payload['market_data']['btc_usd'].get('change_24h_pct', 'N/A')}%
            - Cambio 1h: {payload['market_data']['btc_usd'].get('change_1h_pct', 'N/A')}%

            NOTICIAS RECIENTES:
            {json.dumps(payload['news']['items'], indent=2, ensure_ascii=False)}

            TAREA:
            Analiza si es buen momento para COMPRA LONG en BTC. Sé directo y usa lógica clara.

            FORMATO DE RESPUESTA (JSON estricto):
            {{
                "sentiment_score": float,
                "technical_momentum": "bullish|bearish|neutral",
                "recommendation": "BUY_LONG|AVOID|HOLD",
                "confidence_level": float,
                "key_factors": ["factor1", "factor2", "factor3"],
                "analysis": "análisis conciso en español"
            }}
            """

            data = {
                "model": self.xai_model,
                "messages": [
                    {"role": "system", "content": "Responde ÚNICAMENTE con JSON válido, sin texto adicional."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }

            start_time = time.time()

            response = requests.post(
                f"{self.xai_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=15
            )

            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                result_text = result["choices"][0]["message"]["content"].strip()

                try:
                    result_json = json.loads(result_text)
                except json.JSONDecodeError:
                    result_json = {"error": "Respuesta no es JSON válido", "raw_response": result_text}

                return {
                    "provider": "xAI",
                    "model": self.xai_model,
                    "response_time": round(end_time - start_time, 2),
                    "result": result_json,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"xAI API Error: {response.status_code}", "valuation": 0}

        except Exception as e:
            return {"error": f"Error con xAI: {str(e)}", "valuation": 0}

    def run_complete_test(self) -> Dict[str, Any]:
        """
        Ejecutar prueba completa: obtener datos + análisis con ambas APIs.

        Returns:
            Dict con resultados completos de la prueba
        """
        print("\n🔍 INICIANDO PRUEBA COMPLETA DE ANÁLISIS DE SENTIMIENTO")
        print("=" * 60)

        results = {
            "test_timestamp": datetime.now().isoformat(),
            "phases": {}
        }

        # Fase 1: Obtener datos de BTC
        print("\n📊 Fase 1: Obteniendo datos de BTC...")
        btc_data = self.get_btc_price_data()

        if "error" in btc_data:
            print(f"❌ Error obteniendo BTC: {btc_data['error']}")
            results["phases"]["btc_data"] = {"error": btc_data["error"]}
        else:
            print(f"✅ BTC: ${btc_data['current_price']} ({btc_data['change_24h_pct']}% 24h)")
            results["phases"]["btc_data"] = {"success": True, "data": btc_data}

        # Fase 2: Obtener noticias
        print("\n📰 Fase 2: Obteniendo noticias de mercado...")
        news_data = self.get_market_news(limit=10)

        valid_news = [n for n in news_data if "error" not in n]
        print(f"✅ {len(valid_news)} noticias obtenidas")

        results["phases"]["news_data"] = {
            "success": len(valid_news) > 0,
            "count": len(valid_news),
            "data": valid_news
        }

        # Fase 3: Crear payload estructurado
        print("\n📋 Fase 3: Creando payload estructurado...")
        payload = self.create_analysis_payload(btc_data, news_data)
        results["phases"]["payload_creation"] = {"success": True, "payload": payload}

        # Fase 4: Análisis con OpenAI
        print("\n🤖 Fase 4: Análisis con OpenAI GPT-4o...")
        openai_result = self.analyze_with_openai(payload)

        if "error" in openai_result:
            print(f"❌ Error OpenAI: {openai_result['error']}")
            results["phases"]["openai_analysis"] = {"error": openai_result["error"]}
        else:
            sentiment = openai_result["result"].get("sentiment_score", 0)
            recommendation = openai_result["result"].get("recommendation", "UNKNOWN")
            print(f"✅ OpenAI: Score {sentiment}, {recommendation} ({openai_result['response_time']}s)")
            results["phases"]["openai_analysis"] = openai_result

        # Fase 5: Análisis con xAI
        print("\n🧠 Fase 5: Análisis con xAI Grok...")
        xai_result = self.analyze_with_xai(payload)

        if "error" in xai_result:
            print(f"❌ Error xAI: {xai_result['error']}")
            results["phases"]["xai_analysis"] = {"error": xai_result["error"]}
        else:
            sentiment = xai_result["result"].get("sentiment_score", 0)
            recommendation = xai_result["result"].get("recommendation", "UNKNOWN")
            print(f"✅ xAI: Score {sentiment}, {recommendation} ({xai_result['response_time']}s)")
            results["phases"]["xai_analysis"] = xai_result

        # Fase 6: Comparación final
        print("\n⚖️ Fase 6: Comparación de resultados...")

        comparison = self._generate_comparison(results)
        results["phases"]["comparison"] = comparison

        print("\n" + "=" * 60)
        print("📊 RESULTADOS FINALES:")
        print("=" * 60)

        self._print_final_results(comparison)

        return results

    def _generate_comparison(self, results: Dict) -> Dict[str, Any]:
        """Generar comparación entre resultados de ambas APIs."""

        comparison = {
            "openai": {},
            "xai": {},
            "agreement": {},
            "consensus": {}
        }

        # Extraer resultados de OpenAI
        openai_phase = results["phases"].get("openai_analysis", {})
        if "result" in openai_phase:
            comparison["openai"] = {
                "sentiment_score": openai_phase["result"].get("sentiment_score", 0),
                "recommendation": openai_phase["result"].get("recommendation", "UNKNOWN"),
                "confidence": openai_phase["result"].get("confidence_level", 0),
                "response_time": openai_phase.get("response_time", 0),
                "key_factors": openai_phase["result"].get("key_factors", [])
            }

        # Extraer resultados de xAI
        xai_phase = results["phases"].get("xai_analysis", {})
        if "result" in xai_phase:
            comparison["xai"] = {
                "sentiment_score": xai_phase["result"].get("sentiment_score", 0),
                "recommendation": xai_phase["result"].get("recommendation", "UNKNOWN"),
                "confidence": xai_phase["result"].get("confidence_level", 0),
                "response_time": xai_phase.get("response_time", 0),
                "key_factors": xai_phase["result"].get("key_factors", [])
            }

        # Calcular acuerdo
        if comparison["openai"] and comparison["xai"]:
            openai_score = comparison["openai"]["sentiment_score"]
            xai_score = comparison["xai"]["sentiment_score"]

            # Acuerdo en dirección (positivo/negativo)
            agreement_direction = (openai_score * xai_score) > 0

            # Diferencia absoluta
            score_diff = abs(openai_score - xai_score)

            # Acuerdo en recomendación
            openai_rec = comparison["openai"]["recommendation"]
            xai_rec = comparison["xai"]["recommendation"]
            agreement_recommendation = openai_rec == xai_rec

            comparison["agreement"] = {
                "direction_match": agreement_direction,
                "recommendation_match": agreement_recommendation,
                "score_difference": round(score_diff, 3),
                "average_score": round((openai_score + xai_score) / 2, 3)
            }

            # Consenso
            avg_score = comparison["agreement"]["average_score"]
            if avg_score > 0.3:
                consensus_signal = "BULLISH"
            elif avg_score < -0.3:
                consensus_signal = "BEARISH"
            else:
                consensus_signal = "NEUTRAL"

            comparison["consensus"] = {
                "signal": consensus_signal,
                "strength": "STRONG" if abs(avg_score) > 0.5 else "MODERATE" if abs(avg_score) > 0.2 else "WEAK",
                "confidence": min(comparison["openai"]["confidence"], comparison["xai"]["confidence"])
            }

        return comparison

    def _print_final_results(self, comparison: Dict):
        """Imprimir resultados finales de forma clara."""

        if not comparison["openai"] or not comparison["xai"]:
            print("❌ No hay suficientes datos para comparar")
            return

        print(f"🤖 OpenAI GPT-4o:")
        print(f"   Score: {comparison['openai']['sentiment_score']}")
        print(f"   Recomendación: {comparison['openai']['recommendation']}")
        print(f"   Confianza: {comparison['openai']['confidence']}")
        print(f"   Tiempo: {comparison['openai']['response_time']}s")

        print(f"\n🧠 xAI Grok:")
        print(f"   Score: {comparison['xai']['sentiment_score']}")
        print(f"   Recomendación: {comparison['xai']['recommendation']}")
        print(f"   Confianza: {comparison['xai']['confidence']}")
        print(f"   Tiempo: {comparison['xai']['response_time']}s")

        if "agreement" in comparison:
            print(f"\n⚖️ Acuerdo entre APIs:")
            print(f"   Dirección: {'✅' if comparison['agreement']['direction_match'] else '❌'}")
            print(f"   Recomendación: {'✅' if comparison['agreement']['recommendation_match'] else '❌'}")
            print(f"   Diferencia score: {comparison['agreement']['score_difference']}")
            print(f"   Score promedio: {comparison['agreement']['average_score']}")

        if "consensus" in comparison:
            print(f"\n🎯 Consenso Final:")
            print(f"   Señal: {comparison['consensus']['signal']}")
            print(f"   Fuerza: {comparison['consensus']['strength']}")
            print(f"   Confianza: {comparison['consensus']['confidence']}")


def main():
    """Función principal para ejecutar la prueba."""

    print("🚀 PRUEBA DE ANÁLISIS DE SENTIMIENTO DE MERCADO")
    print("Comparación OpenAI vs xAI para valoración de trading BTC")
    print("=" * 60)

    # Crear instancia del tester
    tester = SentimentTradingTest()

    # Verificar que tengamos las APIs necesarias
    if not tester.openai_available and not tester.xai_available:
        print("❌ Error: Necesitas al menos una API key (OpenAI o xAI)")
        return

    if not tester.yfinance_available:
        print("❌ Error: yfinance es necesario para obtener datos de mercado")
        return

    # Ejecutar prueba completa
    results = tester.run_complete_test()

    # Guardar resultados en archivo
    output_file = f"sentiment_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Resultados guardados en: {output_file}")

    print("\n✅ Prueba completada exitosamente!")


if __name__ == "__main__":
    main()

