#!/usr/bin/env python3
"""
Demo del AI Filter integrado con GPT-4o Mini
Muestra cómo el sistema de valoración se integra en el filtrado de señales
"""

import asyncio
import json
from datetime import datetime
from servos.ai_filter import initialize_ai_filter, should_filter_signal, get_filter_stats

async def demo_integrated_ai_filter():
    """Demostración del AI Filter con GPT-4o Mini integrado"""

    print("🚀 DEMO: AI FILTER INTEGRADO CON GPT-4o MINI")
    print("=" * 80)
    print("🎯 Sistema que combina:")
    print("   • Fear & Greed Index")
    print("   • Volatilidad de mercado")
    print("   • Momentum técnico")
    print("   • Sentimiento social (xAI)")
    print("   • 🎯 VALORACIÓN COMPLETA GPT-4o Mini (NUEVO)")
    print("   • CoinGecko metrics + CryptoPanic sentiment")
    print("=" * 80)

    # Inicializar el sistema
    print("\n🔧 INICIALIZANDO SISTEMA...")
    await initialize_ai_filter()
    print("✅ AI Filter inicializado con GPT-4o Mini")

    # Mostrar estadísticas del sistema
    stats = get_filter_stats()
    print("
📊 CONFIGURACIÓN DEL SISTEMA:"    print(f"   🎯 Modelo GPT: {stats.get('primary_model', 'No disponible')}")
    print(f"   🤖 xAI disponible: {'✅' if stats['xai_available'] else '❌'}")
    print(f"   📈 Sistema valoración: {'✅' if stats['gpt_valuation_available'] else '❌'}")
    print(f"   🗄️ Cache señales: {stats['cache_size']} entradas")
    print(f"   🎯 Cache valoraciones: {stats['valuation_cache_size']} entradas")

    # Configuración de sesión de ejemplo
    session_config = {
        'sentiment_filter': True,
        'user_id': 'demo_user',
        'risk_level': 'medium'
    }

    # Señales de ejemplo para probar
    test_signals = [
        {
            'symbol': 'BTC/USDT',
            'side': 'LONG',
            'entry_price': 91000,
            'stop_loss': 88000,
            'take_profit': 95000,
            'description': 'Señal LONG basada en soporte técnico'
        },
        {
            'symbol': 'ETH/USDT',
            'side': 'SHORT',
            'entry_price': 2800,
            'stop_loss': 2950,
            'take_profit': 2600,
            'description': 'Señal SHORT basada en resistencia técnica'
        },
        {
            'symbol': 'SOL/USDT',
            'side': 'LONG',
            'entry_price': 180,
            'stop_loss': 170,
            'take_profit': 200,
            'description': 'Señal LONG basada en momentum alcista'
        }
    ]

    print("
🧪 PROBANDO SEÑALES CON AI FILTER + GPT-4o Mini..."    print("-" * 80)

    results = []

    for i, signal in enumerate(test_signals, 1):
        print(f"\n📈 SEÑAL {i}: {signal['symbol']} {signal['side']} @ ${signal['entry_price']:,}")
        print(f"   📝 {signal['description']}")

        try:
            # Aplicar filtro AI
            should_filter, reason, analysis_data = await should_filter_signal(signal, session_config)

            # Mostrar resultado
            if should_filter:
                print("   ❌ SEÑAL FILTRADA"                status = "FILTRADA"
            else:
                print("   ✅ SEÑAL PERMITIDA"                status = "PERMITIDA"

            print(f"   💬 Razón: {reason}")

            # Mostrar datos de valoración GPT-4o Mini si están disponibles
            if 'sentiment_data' in analysis_data and 'ai_valuation' in analysis_data['sentiment_data']:
                ai_val = analysis_data['sentiment_data']['ai_valuation']
                if ai_val.get('available'):
                    print("   🎯 GPT-4o Mini:"                    print(f"      LONG: {ai_val['long_signal']:.3f}")
                    print(f"      SHORT: {ai_val['short_signal']:.3f}")
                    print(f"      Confianza: {ai_val['confidence']:.1%}")
                    print(f"      Precio actual: ${ai_val.get('current_price', 0):,.2f}")
                    print(f"      Cambio 24h: {ai_val.get('change_24h', 0):.2f}%")

                    # Recomendación basada en la señal
                    side = signal['side']
                    if side == 'LONG':
                        ai_score = ai_val['long_signal']
                        opposite_score = ai_val['short_signal']
                        ai_recommendation = "FAVORABLE" if ai_score > 0.6 else "NEUTRAL" if ai_score > 0.4 else "DESFAVORABLE"
                    else:  # SHORT
                        ai_score = ai_val['short_signal']
                        opposite_score = ai_val['long_signal']
                        ai_recommendation = "FAVORABLE" if ai_score > 0.6 else "NEUTRAL" if ai_score > 0.4 else "DESFAVORABLE"

                    print(f"      Recomendación: {ai_recommendation} para {side}")

            # Almacenar resultado
            result = {
                'signal': signal,
                'filtered': should_filter,
                'reason': reason,
                'analysis': analysis_data,
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)

        except Exception as e:
            print(f"   ❌ ERROR procesando señal: {e}")
            results.append({
                'signal': signal,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

        # Pequeña pausa entre señales
        await asyncio.sleep(1)

    # Resumen final
    print("
🏁 RESUMEN FINAL DE PRUEBA"    print("=" * 80)

    total_signals = len(results)
    filtered_signals = sum(1 for r in results if r.get('filtered', False))
    allowed_signals = total_signals - filtered_signals

    print(f"📊 Total señales probadas: {total_signals}")
    print(f"✅ Señales permitidas: {allowed_signals}")
    print(f"❌ Señales filtradas: {filtered_signals}")
    print(".1f"
    print("
🎯 FACTORES DE FILTRADO UTILIZADOS:"    print("   • Fear & Greed Index (15% peso)")
    print("   • Volatilidad del mercado (15% peso)")
    print("   • Momentum técnico (15% peso)")
    print("   • Análisis IA híbrido xAI (20% peso)")
    print("   • 🎯 VALORACIÓN GPT-4o Mini (35% peso - MÁXIMO)"    print("   • CoinGecko metrics + CryptoPanic sentiment incluidos")

    # Guardar resultados
    output_file = f"ai_filter_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'demo_timestamp': datetime.now().isoformat(),
            'system_config': stats,
            'test_signals': test_signals,
            'results': results,
            'summary': {
                'total_signals': total_signals,
                'allowed_signals': allowed_signals,
                'filtered_signals': filtered_signals,
                'filter_rate': filtered_signals / total_signals if total_signals > 0 else 0
            }
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n💾 Resultados guardados en: {output_file}")

    print("
🎉 DEMO COMPLETADA"    print("El AI Filter ahora incluye valoraciones completas de GPT-4o Mini")
    print("con CoinGecko y CryptoPanic para decisiones de filtrado más precisas.")

if __name__ == "__main__":
    asyncio.run(demo_integrated_ai_filter())



