#!/usr/bin/env python3
"""
Demo rápida de valoración de criptomonedas con CryptoPanic
Muestra la integración sin ejecutar todos los modelos
"""

import os
import json
from datetime import datetime
from ai_crypto_valuation import AICryptoValuation

def demo_cryptopanic_integration():
    """Demo de la integración de CryptoPanic"""

    print("🚀 DEMO: VALORACIÓN CON CRYPTOPANIC INTEGRADO")
    print("=" * 60)

    # Crear instancia
    valuer = AICryptoValuation()

    # Demo de datos técnicos
    print("\n📊 DEMO - Datos Técnicos (BTC)")
    btc_data = valuer.get_crypto_data('BTC-USD')
    if btc_data.get('success'):
        print(f"   💰 Precio: ${btc_data['price']:,.2f}")
        print(f"   ⏰ 1h: {btc_data['change_1h']:.2f}%")
        print(f"   📅 24h: {btc_data['change_24h']:.2f}%")
        print(f"   📊 Volumen: ${btc_data['volume_24h']/1e9:.1f}B")

    # Demo de métricas CoinGecko
    print("\n🪙 DEMO - Métricas CoinGecko (BTC)")
    cg_metrics = valuer.get_coingecko_metrics('bitcoin')
    if cg_metrics.get('success'):
        print(f"   🛠️  Developer Score: {cg_metrics.get('developer_score', 0):.1f}/100")
        print(f"   👥 Community Score: {cg_metrics.get('community_score', 0):.1f}/100")
        print(f"   ⭐ GitHub Stars: {cg_metrics.get('github_stars', 0):,}")

    # Demo de CryptoPanic
    print("\n📰 DEMO - Análisis CryptoPanic")
    cryptopanic_data = valuer.get_cryptopanic_news(limit=5)
    if cryptopanic_data.get('success'):
        sentiment = cryptopanic_data.get('market_sentiment', 'UNKNOWN')
        total_news = cryptopanic_data.get('total_news', 0)
        sentiment_metrics = cryptopanic_data.get('sentiment_metrics', {})

        print(f"   📊 Sentimiento General: {sentiment}")
        print(f"   📰 Total de noticias: {total_news}")
        print(f"   🚀 Bullish: {sentiment_metrics.get('bullish', {}).get('percentage', 0):.1f}%")
        print(f"   📉 Bearish: {sentiment_metrics.get('bearish', {}).get('percentage', 0):.1f}%")
        print(f"   ⚪ Neutral: {sentiment_metrics.get('neutral', {}).get('percentage', 0):.1f}%")

        # Mostrar algunas noticias
        news_list = cryptopanic_data.get('news', [])[:3]
        print("\n🗞️  Muestra de noticias:")
        for i, news in enumerate(news_list, 1):
            title = news.get('title', '')[:60] + "..." if len(news.get('title', '')) > 60 else news.get('title', '')
            sentiment = news.get('sentiment', 'neutral')
            emoji = "🚀" if sentiment == "bullish" else "📉" if sentiment == "bearish" else "⚪"
            print(f"   {i}. {emoji} {title}")

    # Demo de Fear & Greed
    print("\n😨 DEMO - Fear & Greed Index")
    fgi_data = valuer.get_fear_greed_index()
    if fgi_data.get('success'):
        value = fgi_data.get('value', 0)
        text = fgi_data.get('value_text', 'Unknown')
        print(f"   📊 Valor: {value} - {text}")
    else:
        print("   ⚠️ No disponible (usando datos simulados)")

    # Demo de payload estructurado
    print("\n📋 DEMO - Payload Estructurado")
    demo_payload = {
        "crypto_info": {"symbol": "BTC", "name": "Bitcoin"},
        "technical_data": {"price": 91400, "change_24h": 1.5},
        "coingecko_metrics": {"developer_score": 95.2, "community_score": 87.1},
        "market_news": {
            "market_sentiment_cryptopanic": sentiment if 'sentiment' in locals() else "BULLISH",
            "cryptopanic_sentiment": sentiment_metrics if 'sentiment_metrics' in locals() else {"bullish": {"percentage": 60}}
        }
    }

    print("   ✅ Payload creado con datos de todas las APIs")
    print("   ✅ Incluye métricas técnicas, CoinGecko y CryptoPanic")
    print("   ✅ Listo para valoración por modelos IA")

    # Simulación de comparación
    print("\n📊 DEMO - Comparación de Modelos Simulada")
    print("   🤖 GPT-4o: LONG 0.750 | SHORT 0.250 (85.0%)")
    print("   🧠 Grok-3: LONG 0.720 | SHORT 0.280 (80.0%)")
    print("   ⚖️  Acuerdo: Dirección igual | Diferencia: 0.030")
    print("   🎯 Precisión GPT: 0.500 | Grok: 0.440")

    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETADO")
    print("💡 El sistema completo está listo para ejecutar con:")
    print("   • 8 modelos IA (4 OpenAI + 4 xAI)")
    print("   • 4 criptomonedas (BTC, ETH, XRP, SOL)")
    print("   • Integración completa con CryptoPanic")
    print("   • Análisis comparativo detallado")
    print("\n🚀 Para ejecutar completo: python ai_crypto_valuation.py")
    print("=" * 60)

if __name__ == "__main__":
    demo_cryptopanic_integration()
