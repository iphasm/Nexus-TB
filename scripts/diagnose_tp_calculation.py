#!/usr/bin/env python3
"""
Diagnóstico de cálculo de precios TP para posiciones SHORT
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.trading_manager import ensure_price_separation, round_to_tick_size


async def diagnose_tp_calculation():
    """Diagnóstico simple de cálculo de TP"""
    print("🔍 DIAGNÓSTICO: Cálculo de TP para SHORT positions")
    print("=" * 60)

    # Simular escenario problemático
    scenario = {
        'symbol': 'APTUSDT',
        'current_price': 1.9380,  # Usado por RiskPolicy
        'entry_price': 1.9240,    # Precio real de ejecución
        'tick_size': 0.0001,
        'stop_loss_pct': 0.03,
        'tp_ratio': 2.0
    }

    symbol = scenario['symbol']
    current_price = scenario['current_price']
    entry_price = scenario['entry_price']
    tick_size = scenario['tick_size']
    stop_loss_pct = scenario['stop_loss_pct']
    tp_ratio = scenario['tp_ratio']

    print(f"🎯 {symbol} SHORT Position")
    print(f"  Current Price: ${current_price:.6f}")
    print(f"  Entry Price: ${entry_price:.6f}")
    print(f"  Tick Size: {tick_size}")

    # Cálculo original (RiskPolicy)
    original_tp = current_price * (1 - (stop_loss_pct * tp_ratio))
    print(f"\n🔍 RiskPolicy TP (current_price): ${original_tp:.6f}")

    # Corrección usando entry_price
    corrected_tp = entry_price * (1 - (stop_loss_pct * tp_ratio))
    print(f"🛠️ Corrected TP (entry_price): ${corrected_tp:.6f}")

    # Aplicar round_to_tick_size
    corrected_tp_rounded = round_to_tick_size(corrected_tp, tick_size)
    print(f"🔄 After tick rounding: ${corrected_tp_rounded:.6f}")

    # Aplicar ensure_price_separation
    final_tp = ensure_price_separation(corrected_tp_rounded, entry_price, tick_size, 'SHORT', is_sl=False)
    print(f"✅ Final TP (ensure_separation): ${final_tp}")

    # Validación
    if final_tp and final_tp < entry_price and final_tp > 0:
        print("🎉 SUCCESS: TP is valid and in correct direction (< entry_price)")
        print(f"   Entry: ${entry_price:.6f} > TP: ${final_tp} ✅")
    else:
        print("❌ ERROR: TP is invalid or in wrong direction")
        print(f"   Entry: ${entry_price:.6f}, TP: ${final_tp}")

    print("\n🚀 EXPECTED RESULT: APTUSDT SHORT TP should be around $1.81 (not $2.03)")


if __name__ == "__main__":
    asyncio.run(diagnose_tp_calculation())