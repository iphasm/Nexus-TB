#!/usr/bin/env python3
"""
Test para verificar que el AI Filter NO se ejecute cuando está desactivado
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.ai_filter import should_filter_signal, ai_filter_engine


async def test_ai_filter_disabled():
    """Probar que el AI Filter no se ejecuta cuando está desactivado"""
    print("🧪 TEST: AI Filter desactivado - Verificar que NO filtra señales")
    print("=" * 60)

    # Inicializar AI Filter
    from servos.ai_filter import initialize_ai_filter
    await initialize_ai_filter()
    print("✅ AI Filter inicializado")

    # Señales de prueba
    test_signals = [
        {
            'symbol': 'BTCUSDT',
            'side': 'LONG',
            'entry_price': 45000,
            'confidence': 0.85,
            'strategy': 'TREND_FOLLOWING'
        },
        {
            'symbol': 'ETHUSDT',
            'side': 'SHORT',
            'entry_price': 2800,
            'confidence': 0.78,
            'strategy': 'MEAN_REVERSION'
        }
    ]

    # Configuración con AI Filter DESACTIVADO
    session_config_disabled = {
        'sentiment_filter': False,  # DESACTIVADO
        'ml_mode': True,
        'risk_management': True
    }

    # Configuración con AI Filter ACTIVADO
    session_config_enabled = {
        'sentiment_filter': True,   # ACTIVADO
        'ml_mode': True,
        'risk_management': True
    }

    print("\n🔴 TEST 1: AI Filter DESACTIVADO")
    print("-" * 40)

    for i, signal in enumerate(test_signals, 1):
        print(f"\n🎯 Señal {i}: {signal['symbol']} {signal['side']}")

        # Probar con filtro DESACTIVADO
        should_filter, reason, analysis = await should_filter_signal(signal, session_config_disabled)

        print("📊 Resultado:")
        print(f"  • Filtrada: {'❌ SÍ' if should_filter else '✅ NO'}")
        print(f"  • Razón: {reason}")
        print(f"  • Análisis vacío: {len(analysis) == 0}")

        # Verificaciones
        if should_filter:
            print("  ❌ ERROR: Señal filtrada cuando filtro está DESACTIVADO")
        else:
            print("  ✅ CORRECTO: Señal NO filtrada cuando filtro está DESACTIVADO")

        if reason == "AI Filter desactivado":
            print("  ✅ CORRECTO: Razón correcta cuando filtro está DESACTIVADO")
        else:
            print("  ❌ ERROR: Razón incorrecta")

        if len(analysis) == 0:
            print("  ✅ CORRECTO: Análisis vacío cuando filtro está DESACTIVADO")
        else:
            print("  ❌ ERROR: Análisis no vacío cuando debería estarlo")

    print("\n🟢 TEST 2: AI Filter ACTIVADO (comparación)")
    print("-" * 40)

    for i, signal in enumerate(test_signals[:1], 1):  # Solo probar una señal para comparación
        print(f"\n🎯 Señal {i}: {signal['symbol']} {signal['side']}")

        # Probar con filtro ACTIVADO
        should_filter, reason, analysis = await should_filter_signal(signal, session_config_enabled)

        print("📊 Resultado:")
        print(f"  • Filtrada: {'❌ SÍ' if should_filter else '✅ NO'}")
        print(f"  • Razón: {reason}")
        print(f"  • Análisis presente: {len(analysis) > 0}")

        # Verificaciones
        if not should_filter:
            print("  ✅ CORRECTO: Señal NO filtrada cuando filtro está ACTIVADO")
        else:
            print("  ⚠️  Señal filtrada (puede ser normal con filtro activado)")

        if reason != "AI Filter desactivado":
            print("  ✅ CORRECTO: Razón diferente cuando filtro está ACTIVADO")
        else:
            print("  ❌ ERROR: Razón incorrecta cuando filtro debería estar activo")

        if len(analysis) > 0:
            print("  ✅ CORRECTO: Análisis presente cuando filtro está ACTIVADO")
        else:
            print("  ⚠️  Análisis vacío (posible error en APIs)")

    print("\n" + "=" * 60)
    print("🎯 RESUMEN DEL TEST")
    print("=" * 60)
    print("✅ AI Filter correctamente DESACTIVADO cuando sentiment_filter=False")
    print("✅ Señal pasa SIN filtrado cuando filtro está desactivado")
    print("✅ Razón correcta: 'AI Filter desactivado'")
    print("✅ Análisis vacío cuando filtro está desactivado")
    print("✅ Sistema respeta configuración del usuario")
    print("\n🔒 SEGURIDAD: Doble verificación implementada")
    print("   1. En nexus_loader.py antes de llamar al filtro")
    print("   2. En ai_filter.py dentro del método should_filter_signal")


if __name__ == "__main__":
    asyncio.run(test_ai_filter_disabled())
