#!/usr/bin/env python3
"""
Demo del sistema de análisis de sentimiento de mercado.
Muestra cómo funciona sin requerir APIs reales.
"""

import json
from datetime import datetime
from sentiment_trading_test import SentimentTradingTest

def create_mock_data():
    """Crear datos simulados para la demo."""

    # Datos simulados de BTC
    mock_btc_data = {
        "current_price": 45230.75,
        "change_24h_pct": 2.45,
        "change_1h_pct": -0.12,
        "high_24h": 45890.00,
        "low_24h": 44120.50,
        "volume_24h": 28500000000,
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC-USD"
    }

    # Noticias simuladas
    mock_news = [
        {
            "title": "Bitcoin rompe resistencia clave de $45,000 con volumen alto",
            "publisher": "CoinDesk",
            "link": "https://coindesk.com/bitcoin-breakout",
            "timestamp": int(datetime.now().timestamp()) - 3600,
            "related_ticker": "BTC-USD",
            "date": datetime.now().isoformat()
        },
        {
            "title": "FED mantiene tasas de interés sin cambios, cripto celebra",
            "publisher": "Bloomberg",
            "link": "https://bloomberg.com/fed-holds-rates",
            "timestamp": int(datetime.now().timestamp()) - 7200,
            "related_ticker": "^GSPC",
            "date": datetime.now().isoformat()
        },
        {
            "title": "Tesla aumenta holdings de Bitcoin en $500M",
            "publisher": "Reuters",
            "link": "https://reuters.com/tesla-bitcoin",
            "timestamp": int(datetime.now().timestamp()) - 10800,
            "related_ticker": "TSLA",
            "date": datetime.now().isoformat()
        },
        {
            "title": "Nasdaq cierra en máximos históricos",
            "publisher": "Financial Times",
            "link": "https://ft.com/nasdaq-highs",
            "timestamp": int(datetime.now().timestamp()) - 14400,
            "related_ticker": "^IXIC",
            "date": datetime.now().isoformat()
        },
        {
            "title": "Ethereum supera los $3,000 por primera vez en 2024",
            "publisher": "Cointelegraph",
            "link": "https://cointelegraph.com/eth-3000",
            "timestamp": int(datetime.now().timestamp()) - 18000,
            "related_ticker": "ETH-USD",
            "date": datetime.now().isoformat()
        }
    ]

    return mock_btc_data, mock_news

def simulate_openai_response():
    """Simular respuesta de OpenAI."""
    return {
        "sentiment_score": 0.75,
        "technical_momentum": "bullish",
        "recommendation": "BUY_LONG",
        "confidence_level": 0.82,
        "key_factors": [
            "Ruptura de resistencia de $45,000 con alto volumen",
            "Noticias positivas de FED y Tesla",
            "Momentum técnico alcista en BTC"
        ],
        "analysis": "El mercado muestra fuerte momentum alcista con ruptura técnica clave y noticias positivas fundamentales. Recomiendo entrada LONG con stop loss en $43,500."
    }

def simulate_xai_response():
    """Simular respuesta de xAI."""
    return {
        "sentiment_score": 0.68,
        "technical_momentum": "bullish",
        "recommendation": "BUY_LONG",
        "confidence_level": 0.79,
        "key_factors": [
            "Breakout técnico confirmado",
            "Aumento de posiciones institucionales",
            "Sentimiento positivo en noticias"
        ],
        "analysis": "Datos técnicos y fundamentales apuntan a continuación del rally alcista. El volumen en la ruptura es un indicador positivo fuerte."
    }

def run_demo():
    """Ejecutar demo completa con datos simulados."""

    print("🎭 DEMO: ANÁLISIS DE SENTIMIENTO DE MERCADO")
    print("Simulación con datos ficticios")
    print("=" * 60)

    # Crear datos simulados
    btc_data, news_data = create_mock_data()

    # Crear payload
    tester = SentimentTradingTest()
    payload = tester.create_analysis_payload(btc_data, news_data)

    print("\n📊 DATOS DE MERCADO SIMULADOS:")
    print(f"   BTC Precio: ${btc_data['current_price']:,}")
    print(f"   Cambio 24h: {btc_data['change_24h_pct']}%")
    print(f"   Volumen 24h: ${btc_data['volume_24h']/1e9:.1f}B")

    print(f"\n📰 NOTICIAS RECIENTES ({len(news_data)}):")
    for i, news in enumerate(news_data[:3], 1):
        print(f"   {i}. {news['title'][:60]}...")
        print(f"      Fuente: {news['publisher']}")

    print("\n🤖 SIMULACIÓN OPENAI GPT-4o:")
    openai_result = simulate_openai_response()
    print(f"   Score de sentimiento: {openai_result['sentiment_score']}")
    print(f"   Momentum técnico: {openai_result['technical_momentum']}")
    print(f"   Recomendación: {openai_result['recommendation']}")
    print(f"   Confianza: {openai_result['confidence_level']}")
    print(f"   Factores clave: {', '.join(openai_result['key_factors'][:2])}")
    print(f"   Análisis: {openai_result['analysis']}")

    print("\n🧠 SIMULACIÓN XAI GROK:")
    xai_result = simulate_xai_response()
    print(f"   Score de sentimiento: {xai_result['sentiment_score']}")
    print(f"   Momentum técnico: {xai_result['technical_momentum']}")
    print(f"   Recomendación: {xai_result['recommendation']}")
    print(f"   Confianza: {xai_result['confidence_level']}")
    print(f"   Factores clave: {', '.join(xai_result['key_factors'][:2])}")
    print(f"   Análisis: {xai_result['analysis']}")

    # Simular comparación
    print("\n⚖️ COMPARACIÓN Y CONSENSO:")
    avg_score = (openai_result['sentiment_score'] + xai_result['sentiment_score']) / 2
    score_diff = abs(openai_result['sentiment_score'] - xai_result['sentiment_score'])

    print(f"   Score promedio: {avg_score:.3f}")
    print(f"   Diferencia entre APIs: {score_diff:.3f}")
    print(f"   Acuerdo dirección: ✅ (Ambas positivas)")
    print(f"   Acuerdo recomendación: ✅ (Ambas BUY_LONG)")

    if avg_score > 0.5:
        signal = "🚀 BULLISH (Compra LONG recomendada)"
    elif avg_score > 0.2:
        signal = "⚠️ MODERATE BULLISH"
    elif avg_score > -0.2:
        signal = "⏸️ NEUTRAL"
    elif avg_score > -0.5:
        signal = "⚠️ MODERATE BEARISH"
    else:
        signal = "📉 BEARISH (Evitar LONG)"

    print(f"   Señal consenso: {signal}")

    print("\n💡 INTERPRETACIÓN:")
    print("   Ambas APIs coinciden en momentum alcista fuerte.")
    print("   Factores técnicos y fundamentales alineados positivamente.")
    print("   Alta confianza en la recomendación de compra LONG.")

    # Mostrar estructura JSON
    print("\n📋 ESTRUCTURA JSON ENVIADA A APIs:")
    print(json.dumps(payload, indent=2, ensure_ascii=False)[:500] + "...")

    print("\n✅ Demo completada exitosamente!")
    print("\nPara usar con datos reales:")
    print("1. Configura OPENAI_API_KEY en variables de entorno")
    print("2. Opcionalmente configura XAI_API_KEY")
    print("3. Ejecuta: python sentiment_trading_test.py")

if __name__ == "__main__":
    run_demo()
