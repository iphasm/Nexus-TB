#!/usr/bin/env python3
"""
Verificar información de símbolos en Bybit para diagnosticar problemas SL/TP
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter


async def check_bybit_symbols():
    """Verificar información de símbolos problemáticos en Bybit"""
    print("🔍 VERIFICACIÓN DE SÍMBOLOS BYBIT")
    print("=" * 50)

    # Símbolos problemáticos
    problem_symbols = ['ALGOUSDT', 'VETUSDT', 'CRVUSDT']

    # Inicializar adapter
    adapter = BybitAdapter()
    await adapter.initialize()

    print("📊 Información de símbolos problemáticos:")
    print("-" * 40)

    for symbol in problem_symbols:
        try:
            # Obtener información del símbolo
            symbol_info = await adapter.get_symbol_info(symbol)

            if symbol_info:
                tick_size = symbol_info.get('tick_size', 'N/A')
                price_precision = symbol_info.get('price_precision', 'N/A')
                min_qty = symbol_info.get('min_qty', 'N/A')
                min_notional = symbol_info.get('min_notional', 'N/A')

                print(f"\n🎯 {symbol}:")
                print(f"  📏 Tick Size: {tick_size}")
                print(f"  🎯 Price Precision: {price_precision}")
                print(f"  📦 Min Qty: {min_qty}")
                print(f"  💰 Min Notional: {min_notional}")

                # Verificar si tick_size es problemático
                if isinstance(tick_size, (int, float)):
                    if tick_size <= 0:
                        print("  ❌ ERROR: Tick size inválido (≤ 0)")
                    elif tick_size >= 1:
                        print("  ⚠️ ALERTA: Tick size muy grande (≥ 1)")
                    else:
                        print("  ✅ Tick size parece válido")
                else:
                    print("  ❌ ERROR: Tick size no es numérico")

                # Verificar precios de ejemplo
                test_price = 0.15 if symbol == 'ALGOUSDT' else 0.025 if symbol == 'VETUSDT' else 0.35
                print(f"  🧮 Precio de prueba: ${test_price}")

                if isinstance(tick_size, (int, float)) and tick_size > 0:
                    # Calcular separación mínima
                    min_separation = max(tick_size * 2, test_price * 0.0001)
                    print(f"  📏 Separación mínima: ${min_separation:.6f}")

                    # Calcular SL/TP de ejemplo
                    sl_price = test_price * 0.95  # 5% stop loss
                    tp_price = test_price * 1.10  # 10% take profit

                    print(f"  📊 SL calculado: ${sl_price:.6f}")
                    print(f"  📊 TP calculado: ${tp_price:.6f}")

                    # Verificar si están dentro de límites razonables
                    if sl_price <= 0 or tp_price <= 0:
                        print("  ❌ ERROR: Precios calculados inválidos")
                    elif sl_price >= test_price or tp_price <= test_price:
                        print("  ❌ ERROR: SL/TP en dirección incorrecta")
                    else:
                        print("  ✅ Precios calculados parecen válidos")

            else:
                print(f"\n❌ {symbol}: Información no disponible")

        except Exception as e:
            print(f"\n❌ {symbol}: Error obteniendo información - {e}")

    print("\n" + "="*50)
    print("🔍 ANÁLISIS DE POSIBLES CAUSAS")
    print("="*50)

    print("💡 POSIBLES PROBLEMAS IDENTIFICADOS:")
    print("  1. Tick size demasiado grande para precios bajos")
    print("  2. Separación mínima mayor que el movimiento esperado")
    print("  3. round_to_tick_size resultando en cero")
    print("  4. Precios de entrada muy cerca de cero")

    print("\n🛠️ SOLUCIONES PROPUESTAS:")
    print("  1. Validar tick_size antes de usar ensure_price_separation")
    print("  2. Ajustar lógica de separación para precios bajos")
    print("  3. Agregar fallbacks más robustos")
    print("  4. Mejorar logging de debug")

    # Limpiar
    await adapter.close()


if __name__ == "__main__":
    asyncio.run(check_bybit_symbols())
