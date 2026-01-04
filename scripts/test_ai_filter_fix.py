#!/usr/bin/env python3
"""
Test del AI Filter corregido para verificar que sea más permisivo cuando las APIs fallan
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.ai_filter import ai_filter_engine, initialize_ai_filter


async def test_ai_filter_fix():
    """Probar el AI Filter corregido"""
    print("🧪 TEST: AI Filter con correcciones de robustez")
    print("=" * 50)

    # Inicializar
    print("🔧 Inicializando AI Filter...")
    await initialize_ai_filter()
    print("✅ AI Filter inicializado")

    # Simular señal de prueba
    test_signal = {
        'symbol': 'BTCUSDT',
        'side': 'LONG',
        'entry_price': 45000,
        'confidence': 0.85,
        'strategy': 'TREND_FOLLOWING'
    }

    # Configuración de sesión
    session_config = {
        'sentiment_filter': True,
        'ml_mode': True,
        'risk_management': True
    }

    print(f"\n🎯 Probando señal: {test_signal['symbol']} {test_signal['side']}")

    # Forzar que la valoración GPT falle (simulando APIs caídas)
    original_get_ai_valuation = ai_filter_engine._get_ai_valuation
    async def mock_failed_valuation(symbol):
        return {
            'available': False,
            'reason': 'APIs simuladamente caídas para test',
            'fallback': True
        }

    ai_filter_engine._get_ai_valuation = mock_failed_valuation

    try:
        # Probar filtrado
        should_filter, reason, analysis = await ai_filter_engine.should_filter_signal(test_signal, session_config)

        print("\n📊 RESULTADO:")
        print(f"  • Filtrada: {'❌ SÍ' if should_filter else '✅ NO'}")
        print(f"  • Razón: {reason}")

        if 'filter_score' in analysis:
            print(f"  • Score final: {analysis['filter_score']:.3f}")
            print(f"  • Umbral: 0.75 (antes 0.7)")

            # Verificar que sea más permisivo
            if analysis['filter_score'] <= 0.75:
                print("  ✅ CORRECTO: Señal permitida cuando APIs fallan")
            else:
                print("  ❌ ERROR: Señal filtrada cuando debería ser permitida")

        # Mostrar pesos usados
        if 'weights' in analysis:
            print("\n📊 PESOS USADOS:")
            for factor, weight in analysis['weights'].items():
                print(f"  • {factor}: {weight:.1%}")

    finally:
        # Restaurar método original
        ai_filter_engine._get_ai_valuation = original_get_ai_valuation

    print("\n🎯 TEST COMPLETADO")
    print("💡 El AI Filter ahora debería ser más permisivo cuando las APIs fallan")


if __name__ == "__main__":
    asyncio.run(test_ai_filter_fix())
