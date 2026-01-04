#!/usr/bin/env python3
"""
Diagnóstico de precios SL/TP inválidos en Bybit
Investiga por qué ALGOUSDT, VETUSDT, CRVUSDT fallan
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.trading_manager import ensure_price_separation, round_to_tick_size


async def diagnose_sl_tp_prices():
    """Diagnóstico de precios SL/TP inválidos"""
    print("🔍 DIAGNÓSTICO: Precios SL/TP Inválidos en Bybit")
    print("=" * 60)

    # Símbolos problemáticos
    problem_symbols = ['ALGOUSDT', 'VETUSDT', 'CRVUSDT']

    print("🎯 Símbolos problemáticos:")
    for symbol in problem_symbols:
        print(f"  • {symbol}")

    print("\n🧪 PRUEBA: Simulando cálculos de SL/TP")
    print("-" * 40)

    # Parámetros típicos de una operación
    test_cases = [
        {
            'symbol': 'ALGOUSDT',
            'entry_price': 0.15,  # Precio típico
            'sl_pct': 0.05,       # 5% stop loss
            'tp_pct': 0.10,       # 10% take profit
            'tick_size': 0.0001   # Tick size típico
        },
        {
            'symbol': 'VETUSDT',
            'entry_price': 0.025,
            'sl_pct': 0.05,
            'tp_pct': 0.10,
            'tick_size': 0.00001
        },
        {
            'symbol': 'CRVUSDT',
            'entry_price': 0.35,
            'sl_pct': 0.05,
            'tp_pct': 0.10,
            'tick_size': 0.001
        }
    ]

    for test in test_cases:
        symbol = test['symbol']
        entry_price = test['entry_price']
        sl_pct = test['sl_pct']
        tp_pct = test['tp_pct']
        tick_size = test['tick_size']

        print(f"\n🎯 Probando {symbol} (Entry: ${entry_price})")

        # Calcular precios originales
        sl_price_original = entry_price * (1 - sl_pct)  # LONG: SL < entry
        tp_price_original = entry_price * (1 + tp_pct)  # LONG: TP > entry

        print(f"  📊 Precios originales:")
        print(f"    SL: ${sl_price_original:.6f}")
        print(f"    TP: ${tp_price_original:.6f}")
        print(f"  📏 Tick Size: {tick_size}")

        # Aplicar ensure_price_separation
        try:
            sl_price_adjusted = ensure_price_separation(sl_price_original, entry_price, tick_size, 'LONG', is_sl=True)
            tp_price_adjusted = ensure_price_separation(tp_price_original, entry_price, tick_size, 'LONG', is_sl=False)

            print("\n  🔧 Después de ensure_price_separation:")
            print(f"  SL ajustado: {sl_price_adjusted}")
            print(f"  TP ajustado: {tp_price_adjusted}")

            # Validación final
            sl_valid = sl_price_adjusted is not None and sl_price_adjusted > 0
            tp_valid = tp_price_adjusted is not None and tp_price_adjusted > 0

            print("\n  ✅ Validación final:")
            print(f"  SL válido: {sl_valid}")
            print(f"  TP válido: {tp_valid}")

            if not sl_valid or not tp_valid:
                print("  ❌ ERROR: Precios inválidos después del ajuste!")
                print(f"     SL is None: {sl_price_adjusted is None}")
                print(f"     SL <= 0: {sl_price_adjusted <= 0 if sl_price_adjusted else 'N/A'}")
                print(f"     TP is None: {tp_price_adjusted is None}")
                print(f"     TP <= 0: {tp_price_adjusted <= 0 if tp_price_adjusted else 'N/A'}")
            else:
                print("  ✅ ÉXITO: Precios válidos")

        except Exception as e:
            print(f"  ❌ ERROR en ensure_price_separation: {e}")

    print("\n" + "="*60)
    print("🔍 ANÁLISIS DEL PROBLEMA")
    print("="*60)

    print("💡 POSIBLES CAUSAS:")
    print("  1. Tick size demasiado grande comparado con el precio")
    print("  2. Separación mínima calculada incorrectamente")
    print("  3. round_to_tick_size retornando valores inválidos")
    print("  4. Precios de entrada demasiado bajos")

    print("\n🛠️ SOLUCIONES PROPUESTAS:")
    print("  1. Validar tick_size antes de usar round_to_tick_size")
    print("  2. Ajustar cálculo de separación mínima para precios bajos")
    print("  3. Agregar validación adicional en ensure_price_separation")
    print("  4. Fallback cuando tick_size es problemático")

    print("\n🎯 PRÓXIMOS PASOS:")
    print("  1. Revisar tick_size real de Bybit para estos símbolos")
    print("  2. Modificar ensure_price_separation para manejar casos extremos")
    print("  3. Agregar logs detallados de debug")


if __name__ == "__main__":
    asyncio.run(diagnose_sl_tp_prices())
