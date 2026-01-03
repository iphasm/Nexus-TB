#!/usr/bin/env python3
"""
Debug del error de SL/TP inválido para SEIUSDT
"""
import os
import sys
import asyncio

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar las variables de entorno
os.environ['PROXY_URL'] = 'http://zqiocknu:cejjpesqaead@96.62.194.97:6299'
os.environ['BYBIT_API_KEY'] = 'S7OMynWEyMysJ8MuHd'
os.environ['BYBIT_API_SECRET'] = 'Q4fvuGFUeE2qE8GtM8Tp5sdPlr33Yt4JGV0e'

async def debug_seiusdt_sl_tp():
    """Debug del cálculo de SL/TP para SEIUSDT"""
    print("🔍 DEBUG: SL/TP Calculation for SEIUSDT")
    print("=" * 50)

    from nexus_system.core.nexus_bridge import NexusBridge
    from nexus_system.core.shadow_wallet import ShadowWallet

    # Inicializar bridge
    shadow_wallet = ShadowWallet()
    bridge = NexusBridge(shadow_wallet)

    exchange_kwargs = {
        'http_proxy': os.getenv('PROXY_URL'),
        'https_proxy': os.getenv('PROXY_URL')
    }

    # Conectar a Bybit (donde probablemente irá SEIUSDT)
    print("🔧 Conectando a Bybit...")
    success = await bridge.connect_exchange(
        'BYBIT',
        api_key=os.getenv('BYBIT_API_KEY'),
        api_secret=os.getenv('BYBIT_API_SECRET'),
        **exchange_kwargs
    )

    if not success:
        print("❌ No se pudo conectar a Bybit")
        return

    print("✅ Bybit conectado")

    # Determinar a qué exchange irá SEIUSDT
    symbol = 'SEIUSDT'
    target_exchange = bridge._route_symbol(symbol)
    print(f"📍 {symbol} será enrutado a: {target_exchange}")

    # Obtener precio actual
    try:
        current_price = await bridge.get_last_price(symbol)
        if current_price <= 0:
            print(f"❌ No se pudo obtener precio para {symbol}")
            return
        print(f"💰 Precio actual de {symbol}: ${current_price:.4f}")
    except Exception as e:
        print(f"❌ Error obteniendo precio: {e}")
        return

    # Obtener tick_size
    try:
        qty_prec, price_prec, min_notional, tick_size = await bridge.adapters[target_exchange]._exchange.get_symbol_precision(symbol)
        print(f"📏 Tick size: {tick_size}")
        print(f"💰 Min notional: {min_notional}")
    except Exception as e:
        print(f"❌ Error obteniendo precisión del símbolo: {e}")
        # Valores por defecto
        tick_size = 0.00001  # Para criptos pequeñas
        min_notional = 5.0

    # Simular cálculo de SL/TP como en el código real
    print("\n🧮 SIMULACIÓN DE CÁLCULO SL/TP")
    print("-" * 40)

    # Parámetros de ejemplo (como los que usaría el bot)
    stop_loss_pct = 0.02  # 2%
    tp_ratio = 2.0        # Risk:Reward 1:2

    # Cálculo inicial de SL/TP (sin ATR)
    sl_price = current_price * (1 - stop_loss_pct)
    tp_price = current_price * (1 + (stop_loss_pct * tp_ratio))

    print(f"   SL calculado: {sl_price:.6f}")
    print(f"   TP calculado: {tp_price:.6f}")
    # Aplicar round_to_tick_size inicial
    from servos.trading_manager import round_to_tick_size
    sl_price = round_to_tick_size(sl_price, tick_size)
    tp_price = round_to_tick_size(tp_price, tick_size)

    print(f"   SL después de round_to_tick_size: {sl_price:.6f}")
    print(f"   TP después de round_to_tick_size: {tp_price:.6f}")
    # Aplicar ensure_price_separation
    from servos.trading_manager import ensure_price_separation

    print("\n🔧 Aplicando ensure_price_separation...")
    entry_price = current_price  # Para LONG, entry = current

    sl_price_adjusted = ensure_price_separation(sl_price, entry_price, tick_size, 'LONG', is_sl=True)
    tp_price_adjusted = ensure_price_separation(tp_price, entry_price, tick_size, 'LONG', is_sl=False)

    print(f"   SL después de ensure_price_separation: {sl_price_adjusted}")
    print(f"   TP después de ensure_price_separation: {tp_price_adjusted}")

    # Validación final
    print("\n✅ VALIDACIÓN FINAL:")
    if sl_price_adjusted is None or tp_price_adjusted is None:
        print("❌ ERROR: ensure_price_separation devolvió None")
        return

    if sl_price_adjusted <= 0 or tp_price_adjusted <= 0:
        print(f"❌ ERROR: Precios <= 0 (SL: {sl_price_adjusted}, TP: {tp_price_adjusted})")
        return

    print("✅ SL/TP válidos después del ajuste")
    print(f"   SL final: {sl_price_adjusted:.6f}")
    print(f"   TP final: {tp_price_adjusted:.6f}")
    # Verificar separación mínima
    sl_distance = entry_price - sl_price_adjusted
    tp_distance = tp_price_adjusted - entry_price

    print("\n📊 ANÁLISIS DE SEPARACIÓN:")
    print(f"   Distancia SL: {sl_distance:.6f}")
    print(f"   Distancia TP: {tp_distance:.6f}")
    print(f"   Ratio Risk:Reward: 1:{tp_distance/sl_distance:.2f}")
    min_separation_required = max(tick_size * 2, entry_price * 0.0001)
    print(f"   Separación mínima requerida: {min_separation_required:.6f}")
    if sl_distance >= min_separation_required and tp_distance >= min_separation_required:
        print("✅ Separación suficiente")
    else:
        print("❌ Separación insuficiente")

if __name__ == "__main__":
    asyncio.run(debug_seiusdt_sl_tp())
