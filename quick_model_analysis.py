#!/usr/bin/env python3
"""
Análisis Rápido de Modelos IA para Valoración de Criptos
Comparación eficiente con datos actuales
"""

import os
import json
import time
from datetime import datetime
from ai_crypto_valuation import AICryptoValuation

def quick_model_comparison():
    """Análisis rápido de modelos con menos overhead"""

    print("🚀 ANÁLISIS RÁPIDO DE MODELOS IA")
    print("=" * 60)

    # Crear instancia
    valuer = AICryptoValuation()

    # Datos básicos
    cryptos = ['BTC', 'ETH', 'XRP', 'SOL']

    # Recopilar datos una sola vez
    print("\n📊 RECOPILANDO DATOS BASE...")

    # Datos técnicos
    market_data = {}
    for crypto in cryptos:
        print(f"   📈 Obteniendo datos de {crypto}...")
        data = valuer.get_crypto_data(f"{crypto}-USD")
        market_data[crypto] = data if data.get('success') else {"error": "No disponible"}

    # Datos CoinGecko
    coingecko_data = {}
    for crypto in cryptos:
        print(f"   🪙 Métricas CoinGecko de {crypto}...")
        cg_id = {'BTC': 'bitcoin', 'ETH': 'ethereum', 'XRP': 'ripple', 'SOL': 'solana'}[crypto]
        data = valuer.get_coingecko_metrics(cg_id)
        coingecko_data[crypto] = data if data.get('success') else {"error": "No disponible"}

    # Datos globales
    print("   🌍 Datos globales...")
    global_data = valuer.get_global_crypto_data()
    fear_greed = valuer.get_fear_greed_index()
    trending = valuer.get_trending_coins()

    # CryptoPanic
    print("   📰 Análisis CryptoPanic...")
    cryptopanic_news = valuer.get_cryptopanic_news(limit=8)

    print("✅ Datos recopilados exitosamente")

    # Crear payloads para cada crypto
    payloads = {}
    for crypto in cryptos:
        crypto_info = {
            'BTC': {'short': 'BTC', 'symbol': 'BTC', 'name': 'Bitcoin', 'coingecko_id': 'bitcoin'},
            'ETH': {'short': 'ETH', 'symbol': 'ETH', 'name': 'Ethereum', 'coingecko_id': 'ethereum'},
            'XRP': {'short': 'XRP', 'symbol': 'XRP', 'name': 'XRP', 'coingecko_id': 'ripple'},
            'SOL': {'short': 'SOL', 'symbol': 'SOL', 'name': 'Solana', 'coingecko_id': 'solana'}
        }[crypto]

        payloads[crypto] = valuer.create_valuation_payload(
            crypto_info,
            market_data[crypto],
            coingecko_data[crypto],
            [],  # market_news (simplificado)
            cryptopanic_news,
            {"contexto": "Análisis actualizado del mercado crypto"},
            fear_greed,
            global_data,
            trending
        )

    # Modelos a comparar (solo los principales para velocidad)
    test_models = [
        {"name": "GPT-4o", "type": "openai", "id": "gpt-4o"},
        {"name": "GPT-4o Mini", "type": "openai", "id": "gpt-4o-mini"},
        {"name": "Grok-3", "type": "xai", "id": "grok-3"},
        {"name": "Grok-3 Mini", "type": "xai", "id": "grok-3-mini"}
    ]

    # Ejecutar valoraciones
    results = {}
    total_start = time.time()

    print("\n🤖 EJECUTANDO VALORACIONES...")
    print(f"   📊 Probando {len(test_models)} modelos x {len(cryptos)} cryptos = {len(test_models) * len(cryptos)} análisis")

    for model in test_models:
        model_name = model['name']
        results[model_name] = {}
        model_start = time.time()

        print(f"\n🧠 {model_name}:")

        for crypto in cryptos:
            try:
                if model['type'] == 'openai':
                    valuation = valuer.get_openai_valuation_with_model(
                        {'short': crypto, 'symbol': f"{crypto}-USD", 'name': crypto, 'coingecko_id': ''},
                        payloads[crypto],
                        model['id']
                    )
                else:  # xai
                    valuation = valuer.get_grok_valuation_with_model(
                        {'short': crypto, 'symbol': f"{crypto}-USD", 'name': crypto, 'coingecko_id': ''},
                        payloads[crypto],
                        model['id']
                    )

                if valuation.get('success'):
                    results[model_name][crypto] = valuation
                    long_signal = valuation.get('result', {}).get('long_signal', 0)
                    short_signal = valuation.get('result', {}).get('short_signal', 0)
                    confidence = valuation.get('result', {}).get('confidence_level', 0)
                    print(f"   ✅ {crypto}: LONG {long_signal:.3f} | SHORT {short_signal:.3f} ({confidence:.1%})")
                else:
                    results[model_name][crypto] = {'error': 'Falló'}
                    print(f"   ❌ {crypto}: Error - {valuation.get('error', 'Unknown')}")

            except Exception as e:
                results[model_name][crypto] = {'error': str(e)}
                print(f"   ❌ {crypto}: Exception - {str(e)}")

        model_time = time.time() - model_start
        print(".2f")
    total_time = time.time() - total_start
    print("\n⏱️  Tiempo total:")
    print(".2f")
    # Análisis de resultados
    print("\n📊 ANÁLISIS DE RESULTADOS")
    print("=" * 60)

    # Calcular métricas por modelo
    model_stats = {}

    for model_name, crypto_results in results.items():
        successful = 0
        total_long = 0
        total_short = 0
        total_confidence = 0

        for crypto, result in crypto_results.items():
            if 'error' not in result and result.get('success'):
                successful += 1
                long_sig = result.get('result', {}).get('long_signal', 0)
                short_sig = result.get('result', {}).get('short_signal', 0)
                conf = result.get('result', {}).get('confidence_level', 0)

                total_long += long_sig
                total_short += short_sig
                total_confidence += conf

        if successful > 0:
            avg_long = total_long / successful
            avg_short = total_short / successful
            avg_confidence = total_confidence / successful
        else:
            avg_long = avg_short = avg_confidence = 0

        model_stats[model_name] = {
            'successful_valuations': successful,
            'total_cryptos': len(cryptos),
            'success_rate': successful / len(cryptos),
            'avg_long_signal': avg_long,
            'avg_short_signal': avg_short,
            'avg_confidence': avg_confidence
        }

    # Rankings
    print("🏆 RANKING POR PRECISIÓN (ÉXITO):")
    precision_ranking = sorted(model_stats.items(),
                              key=lambda x: x[1]['success_rate'], reverse=True)
    for i, (model, stats) in enumerate(precision_ranking, 1):
        success_rate = stats['success_rate']
        print("2d")
    print("\n🎯 RANKING POR CONFIANZA PROMEDIO:")
    confidence_ranking = sorted(model_stats.items(),
                              key=lambda x: x[1]['avg_confidence'], reverse=True)
    for i, (model, stats) in enumerate(confidence_ranking, 1):
        confidence = stats['avg_confidence']
        print("2d")
    print("\n🚀 RANKING POR OPTIMISMO (LONG AVG):")
    bullish_ranking = sorted(model_stats.items(),
                           key=lambda x: x[1]['avg_long_signal'], reverse=True)
    for i, (model, stats) in enumerate(bullish_ranking, 1):
        long_avg = stats['avg_long_signal']
        print("2d")
    # Resumen final
    print("\n🏁 RESUMEN FINAL")
    print("-" * 60)

    best_precision = precision_ranking[0][0]
    best_confidence = confidence_ranking[0][0]
    most_bullish = bullish_ranking[0][0]

    print(f"🎖️  Modelo más confiable: {best_precision}")
    print(f"🎯 Modelo más preciso: {best_confidence}")
    print(f"🚀 Modelo más optimista: {most_bullish}")

    if best_precision == best_confidence:
        print(f"🏆 GANADOR GENERAL: {best_precision}")
    else:
        print(f"⚖️  Balance: {best_precision} (confiable) vs {best_confidence} (preciso)")

    # Guardar resultados
    analysis_result = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": "quick_model_comparison",
        "models_tested": list(results.keys()),
        "cryptos_analyzed": cryptos,
        "model_stats": model_stats,
        "rankings": {
            "precision": [m[0] for m in precision_ranking],
            "confidence": [m[0] for m in confidence_ranking],
            "bullish": [m[0] for m in bullish_ranking]
        },
        "total_time": total_time,
        "avg_time_per_model": total_time / len(test_models)
    }

    filename = f"quick_model_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Resultados guardados en: {filename}")

    return analysis_result

if __name__ == "__main__":
    quick_model_comparison()
