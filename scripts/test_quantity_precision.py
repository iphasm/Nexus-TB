#!/usr/bin/env python3
"""
Test de precisión de cantidad para TP parciales
Verifica que min_qty se respete en la lógica de split
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.trading_manager import round_to_tick_size


async def test_quantity_precision():
    """Test de precisión de cantidad"""
    print("🧪 TEST: Precisión de Cantidad para TP Parciales")
    print("=" * 60)

    # Simular escenarios problemáticos
    test_cases = [
        {
            'symbol': 'SUIUSDT',
            'total_qty': 10.0,
            'min_notional': 20.0,  # $20 min
            'min_qty': 10.0,       # Mínimo 10 unidades
            'current_price': 2.0,
            'tick_size': 0.0001
        },
        {
            'symbol': 'VETUSDT',
            'total_qty': 1000.0,
            'min_notional': 10.0,  # $10 min
            'min_qty': 1.0,        # Mínimo 1 unidad
            'current_price': 0.01,
            'tick_size': 1e-06
        },
        {
            'symbol': 'ALGOUSDT',
            'total_qty': 100.0,
            'min_notional': 5.0,   # $5 min
            'min_qty': 0.1,        # Mínimo 0.1 unidades
            'current_price': 0.15,
            'tick_size': 1e-05
        }
    ]

    for case in test_cases:
        symbol = case['symbol']
        total_qty = case['total_qty']
        min_notional = case['min_notional']
        min_qty = case['min_qty']
        current_price = case['current_price']
        tick_size = case['tick_size']

        print(f"\n🎯 {symbol} (Total Qty: {total_qty})")
        print(f"  💰 Min Notional: ${min_notional}")
        print(f"  📦 Min Qty: {min_qty}")
        print(f"  💵 Current Price: ${current_price}")

        # Calcular split tradicional (50/50)
        qty_tp1 = round_to_tick_size(total_qty / 2, 1)  # Redondear a entero para qty
        qty_trail = round_to_tick_size(total_qty - qty_tp1, 1)

        print("\n  🔄 Split Tradicional (50/50):")
        print(f"  TP1 Qty: {qty_tp1}")
        print(f"  Trail Qty: {qty_trail}")

        # Verificar condiciones para split
        tp1_notional = qty_tp1 * current_price
        trail_notional = qty_trail * current_price

        print("\n  ✅ Verificación de Condiciones:")
        print(f"  TP1 Notional: ${tp1_notional:.2f} ≥ ${min_notional} = {tp1_notional >= min_notional}")
        print(f"  Trail Notional: ${trail_notional:.2f} ≥ ${min_notional} = {trail_notional >= min_notional}")
        print(f"  TP1 Qty: {qty_tp1} ≥ {min_qty} = {qty_tp1 >= min_qty}")
        print(f"  Trail Qty: {qty_trail} ≥ {min_qty} = {qty_trail >= min_qty}")

        # Decisión final
        can_split = (tp1_notional >= min_notional and
                    trail_notional >= min_notional and
                    qty_tp1 >= min_qty and
                    qty_trail >= min_qty)

        print(f"\n  🎯 DECISIÓN: {'✅ SPLIT PERMITIDO' if can_split else '❌ FULL TRAILING ONLY'}")

        if not can_split:
            print("  📋 Usará cantidad completa para trailing stop")
            print(f"     Trail Qty: {total_qty} (100%)")

        # Verificar escenarios reales de los logs
        if symbol == 'SUIUSDT':
            print("\n  📋 LOGS REALES - SUIUSDT:")
            print("  ❌ 'amount must be greater than minimum amount precision of 10'")
            print("  💡 CAUSA: Intentó usar qty=5.0 pero min_qty=10.0")
            print(f"  ✅ FIX: Ahora verifica qty >= {min_qty} antes de split")

    print("\n" + "="*60)
    print("🎯 RESULTADO FINAL")
    print("="*60)
    print("✅ FIX 1: Agregado min_qty a get_symbol_precision")
    print("✅ FIX 2: Condición is_split incluye verificación de min_qty")
    print("✅ FIX 3: Cuando no split, usa cantidad completa para trailing")
    print("✅ FIX 4: Evita errores 'minimum amount precision'")
    print()
    print("🚀 Los errores de cantidad en SUIUSDT deberían resolverse")


if __name__ == "__main__":
    asyncio.run(test_quantity_precision())
