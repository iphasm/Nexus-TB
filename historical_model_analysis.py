#!/usr/bin/env python3
"""
Análisis de Modelos basado en Datos Históricos
Análisis comparativo usando resultados anteriores
"""

import json
from datetime import datetime
from collections import defaultdict

def analyze_historical_data():
    """Análisis basado en datos históricos de valoraciones"""

    print("📊 ANÁLISIS HISTÓRICO DE MODELOS IA")
    print("=" * 60)

    # Cargar datos históricos
    try:
        with open('ai_crypto_valuation_20260104_022817.json', 'r', encoding='utf-8') as f:
            historical_data = json.load(f)
    except FileNotFoundError:
        print("❌ No se encontraron datos históricos")
        return

    print(f"📅 Datos analizados: {historical_data['timestamp'][:19]}")
    print(f"🪙 Criptomonedas: {', '.join(historical_data['cryptos_analyzed'])}")

    # Extraer datos de valoraciones
    model_stats = defaultdict(lambda: {
        'valuations': 0,
        'successful': 0,
        'response_times': [],
        'long_signals': [],
        'short_signals': [],
        'confidence_levels': [],
        'price_targets_long': [],
        'price_targets_short': []
    })

    # Procesar cada criptomoneda
    for crypto in historical_data['cryptos_analyzed']:
        crypto_data = historical_data['valuations'][crypto]

        # OpenAI valuations
        if 'openai_valuations' in crypto_data:
            for model_name, valuation in crypto_data['openai_valuations'].items():
                if isinstance(valuation, dict) and 'result' in valuation:
                    model_stats[model_name]['valuations'] += 1

                    result = valuation['result']
                    if all(key in result for key in ['long_signal', 'short_signal', 'confidence_level']):
                        model_stats[model_name]['successful'] += 1

                        # Recopilar métricas
                        model_stats[model_name]['response_times'].append(valuation.get('response_time', 0))
                        model_stats[model_name]['long_signals'].append(result['long_signal'])
                        model_stats[model_name]['short_signals'].append(result['short_signal'])
                        model_stats[model_name]['confidence_levels'].append(result['confidence_level'])

                        # Price targets si existen
                        if 'price_target_long' in result:
                            model_stats[model_name]['price_targets_long'].append(result['price_target_long'])
                        if 'price_target_short' in result:
                            model_stats[model_name]['price_targets_short'].append(result['price_target_short'])

        # xAI valuations
        if 'xai_valuations' in crypto_data:
            for model_name, valuation in crypto_data['xai_valuations'].items():
                if isinstance(valuation, dict) and 'result' in valuation:
                    model_stats[model_name]['valuations'] += 1

                    result = valuation['result']
                    if all(key in result for key in ['long_signal', 'short_signal', 'confidence_level']):
                        model_stats[model_name]['successful'] += 1

                        # Recopilar métricas
                        model_stats[model_name]['response_times'].append(valuation.get('response_time', 0))
                        model_stats[model_name]['long_signals'].append(result['long_signal'])
                        model_stats[model_name]['short_signals'].append(result['short_signal'])
                        model_stats[model_name]['confidence_levels'].append(result['confidence_level'])

                        # Price targets si existen
                        if 'price_target_long' in result:
                            model_stats[model_name]['price_targets_long'].append(result['price_target_long'])
                        if 'price_target_short' in result:
                            model_stats[model_name]['price_targets_short'].append(result['price_target_short'])

    # Calcular estadísticas finales
    final_stats = {}

    for model_name, stats in model_stats.items():
        if stats['successful'] > 0:
            final_stats[model_name] = {
                'total_valuations': stats['valuations'],
                'successful_valuations': stats['successful'],
                'success_rate': stats['successful'] / stats['valuations'],
                'avg_response_time': sum(stats['response_times']) / len(stats['response_times']),
                'avg_long_signal': sum(stats['long_signals']) / len(stats['long_signals']),
                'avg_short_signal': sum(stats['short_signals']) / len(stats['short_signals']),
                'avg_confidence': sum(stats['confidence_levels']) / len(stats['confidence_levels']),
                'consistency_long': calculate_consistency(stats['long_signals']),
                'consistency_short': calculate_consistency(stats['short_signals'])
            }

    # Rankings
    print("\n📊 RESULTADOS DEL ANÁLISIS HISTÓRICO")    print("=" * 60)

    if not final_stats:
        print("❌ No hay datos suficientes para análisis")
        return

    # Ranking por tasa de éxito
    print("🏆 RANKING POR TASA DE ÉXITO:")
    success_ranking = sorted(final_stats.items(),
                           key=lambda x: x[1]['success_rate'], reverse=True)
    for i, (model, stats) in enumerate(success_ranking, 1):
        success_rate = stats['success_rate']
        successful = stats['successful_valuations']
        total = stats['total_valuations']
        print("2d"
    # Ranking por velocidad
    print("
⚡ RANKING POR VELOCIDAD:"    speed_ranking = sorted(final_stats.items(),
                        key=lambda x: x[1]['avg_response_time'])
    for i, (model, stats) in enumerate(speed_ranking, 1):
        speed = stats['avg_response_time']
        print("2d"
    # Ranking por confianza
    print("
🎯 RANKING POR CONFIANZA PROMEDIO:"    confidence_ranking = sorted(final_stats.items(),
                            key=lambda x: x[1]['avg_confidence'], reverse=True)
    for i, (model, stats) in enumerate(confidence_ranking, 1):
        confidence = stats['avg_confidence']
        print("2d"
    # Ranking por optimismo
    print("
🚀 RANKING POR OPTIMISMO (LONG AVG):"    bullish_ranking = sorted(final_stats.items(),
                          key=lambda x: x[1]['avg_long_signal'], reverse=True)
    for i, (model, stats) in enumerate(bullish_ranking, 1):
        long_avg = stats['avg_long_signal']
        print("2d"
    # Ranking por consistencia
    print("
🎲 RANKING POR CONSISTENCIA (LONG):"    consistency_ranking = sorted(final_stats.items(),
                              key=lambda x: x[1]['consistency_long'], reverse=True)
    for i, (model, stats) in enumerate(consistency_ranking, 1):
        consistency = stats['consistency_long']
        print("2d"
    # Análisis detallado por modelo
    print("
📈 ANÁLISIS DETALLADO POR MODELO"    print("-" * 60)

    for model_name, stats in sorted(final_stats.items()):
        print(f"\n🧠 {model_name}:")
        print(".1f"        print(".2f"        print(".1%"        print(".3f"        print(".3f"        print(".3f"        print(".3f"
        if stats['consistency_long'] > 0:
            print(".3f"        if stats['consistency_short'] > 0:
            print(".3f"
    # Conclusiones
    print("
🏁 CONCLUSIONES DEL ANÁLISIS HISTÓRICO"    print("-" * 60)

    if success_ranking:
        best_model = success_ranking[0][0]
        best_success_rate = success_ranking[0][1]['success_rate']
        print(f"🏆 MODELO MÁS CONFIABLE: {best_model} ({best_success_rate:.1%} éxito)")

    if speed_ranking:
        fastest_model = speed_ranking[0][0]
        fastest_time = speed_ranking[0][1]['avg_response_time']
        print(f"⚡ MODELO MÁS RÁPIDO: {fastest_model} ({fastest_time:.2f}s promedio)")

    if confidence_ranking:
        most_confident = confidence_ranking[0][0]
        highest_confidence = confidence_ranking[0][1]['avg_confidence']
        print(f"🎯 MODELO MÁS CONFIADO: {most_confident} ({highest_confidence:.1%} confianza)")

    if bullish_ranking:
        most_bullish = bullish_ranking[0][0]
        bullish_level = bullish_ranking[0][1]['avg_long_signal']
        print(f"🚀 MODELO MÁS OPTIMISTA: {most_bullish} (LONG {bullish_level:.3f})")

    # Recomendaciones
    print("
💡 RECOMENDACIONES:"    print("   • Para trading profesional: Usa modelos con alta tasa de éxito y confianza")
    print("   • Para análisis rápido: Prioriza velocidad sobre precisión")
    print("   • Para decisiones críticas: Combina múltiples modelos")
    print("   • Para aprendizaje: Experimenta con todos los modelos disponibles")

    # Guardar análisis
    analysis_result = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": "historical_model_comparison",
        "data_source": "ai_crypto_valuation_20260104_022817.json",
        "models_analyzed": list(final_stats.keys()),
        "final_stats": final_stats,
        "rankings": {
            "success": [m[0] for m in success_ranking],
            "speed": [m[0] for m in speed_ranking],
            "confidence": [m[0] for m in confidence_ranking],
            "bullish": [m[0] for m in bullish_ranking],
            "consistency": [m[0] for m in consistency_ranking]
        }
    }

    filename = f"historical_model_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Análisis guardado en: {filename}")

    return analysis_result

def calculate_consistency(values):
    """Calcula la consistencia de una serie de valores (menor varianza = mayor consistencia)"""
    if len(values) < 2:
        return 0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    # Convertir varianza a consistencia (0-1, donde 1 es máxima consistencia)
    consistency = 1 / (1 + variance)
    return consistency

if __name__ == "__main__":
    analyze_historical_data()
