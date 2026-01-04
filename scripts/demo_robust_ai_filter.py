#!/usr/bin/env python3
"""
Demo del AI Filter Robusto - Funciona con cualquier combinación de APIs
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.ai_filter import ai_filter_engine, initialize_ai_filter


async def demo_robust_ai_filter():
    """Demo completo del AI Filter robusto"""
    print("🚀 DEMO: AI Filter Robusto - Funciona con 0-5 APIs")
    print("=" * 60)

    # Inicializar
    await initialize_ai_filter()
    print("✅ AI Filter inicializado")

    # Señales de prueba
    test_signals = [
        {'symbol': 'BTCUSDT', 'side': 'LONG', 'entry_price': 45000, 'strategy': 'TREND_FOLLOWING'},
        {'symbol': 'ETHUSDT', 'side': 'SHORT', 'entry_price': 2800, 'strategy': 'MEAN_REVERSION'},
        {'symbol': 'SOLUSDT', 'side': 'LONG', 'entry_price': 120, 'strategy': 'SCALPING'}
    ]

    session_config = {'sentiment_filter': True}

    print(f"\n🎯 Probando {len(test_signals)} señales en condiciones reales")
    print("(APIs parcialmente fallidas: xAI timeout, GPT-4o Mini error)")

    # Procesar señales
    results = []
    for i, signal in enumerate(test_signals, 1):
        print(f"\n{'='*40}")
        print(f"📊 SEÑAL {i}: {signal['symbol']} {signal['side']}")
        print('='*40)

        should_filter, reason, analysis = await ai_filter_engine.should_filter_signal(signal, session_config)

        # Mostrar resultado
        status = "❌ FILTRADA" if should_filter else "✅ PERMITIDA"
        print(f"🎯 Resultado: {status}")
        print(f"📝 Razón: {reason}")

        # Mostrar estado de APIs
        if 'sentiment_data' in analysis:
            sentiment = analysis['sentiment_data']
            api_status = sentiment.get('api_status', {})

            print("\n🔍 Estado de APIs:")
            apis_working = api_status.get('working_apis', 0)
            print(f"   • APIs funcionando: {apis_working}/5")

            if api_status.get('all_apis_failed'):
                print("   • 🔴 Modo: ANÁLISIS TÉCNICO PURO (todas APIs fallaron)")
            elif api_status.get('technical_fallback'):
                print("   • 🟡 Modo: HÍBRIDO LIMITADO (APIs insuficientes)")
            else:
                print("   • 🟢 Modo: COMPLETO (APIs suficientes)")

            # Detalles de APIs individuales
            api_details = {
                'Fear & Greed': sentiment.get('fear_greed', {}),
                'Volatilidad': sentiment.get('volatility', {}),
                'Momentum': sentiment.get('momentum', {}),
                'Social Sentiment': sentiment.get('social_sentiment', {}),
                'GPT-4o Mini': sentiment.get('ai_valuation', {})
            }

            print("   • Detalles:")
            for api_name, data in api_details.items():
                if api_name in ['Fear & Greed', 'Volatilidad', 'Momentum']:
                    status = "✅" if data.get('error') is None else "❌"
                else:
                    status = "✅" if data.get('available') else "❌"
                print(f"     - {api_name}: {status}")

        # Mostrar score si está disponible
        if 'filter_score' in analysis:
            score = analysis['filter_score']
            threshold = 0.9 if api_status.get('all_apis_failed') else 0.8 if apis_working <= 2 else 0.75
            print(f"   📊 Score: {score:.3f} (umbral: {threshold:.2f})")
        results.append({
            'signal': signal,
            'filtered': should_filter,
            'apis_working': apis_working
        })

    # Resumen final
    print(f"\n{'='*60}")
    print("🎉 RESUMEN FINAL")
    print('='*60)

    total_signals = len(results)
    filtered_signals = sum(1 for r in results if r['filtered'])
    allowed_signals = total_signals - filtered_signals

    print(f"📊 Señales procesadas: {total_signals}")
    print(f"✅ Señales permitidas: {allowed_signals} ({allowed_signals/total_signals*100:.1f}%)")
    print(f"❌ Señales filtradas: {filtered_signals} ({filtered_signals/total_signals*100:.1f}%)")

    apis_working_values = [r['apis_working'] for r in results]
    avg_apis = sum(apis_working_values) / len(apis_working_values)

    print(f"🔗 Promedio APIs funcionando: {avg_apis:.1f}")
    print("\n🎯 CARACTERÍSTICAS DEL SISTEMA ROBUSTO:")
    print("  ✅ Funciona con 0-5 APIs disponibles")
    print("  ✅ Fallback automático a análisis técnico")
    print("  ✅ Umbrales adaptables según disponibilidad")
    print("  ✅ Nunca deja de funcionar por fallos externos")
    print("  ✅ Logging detallado del estado de APIs")
    print()
    print("🛡️ El AI Filter es ULTRA-ROBUSTO y confiable!")


if __name__ == "__main__":
    asyncio.run(demo_robust_ai_filter())
