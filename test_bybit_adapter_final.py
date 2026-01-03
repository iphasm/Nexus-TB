#!/usr/bin/env python3
"""
Test final usando exactamente la configuración del adapter BybitAdapter
"""
import os
import sys
import asyncio

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar las variables de entorno exactas
os.environ['PROXY_URL'] = 'http://zqiocknu:cejjpesqaead@96.62.194.97:6299'
os.environ['BYBIT_API_KEY'] = 'S7OMynWEyMysJ8MuHd'
os.environ['BYBIT_API_SECRET'] = 'Q4fvuGFUeE2qE8GtM8Tp5sdPlr33Yt4JGV0e'

async def test_bybit_adapter_config():
    """Test usando exactamente la configuración del BybitAdapter"""
    print("🎯 TEST FINAL: CONFIGURACIÓN EXACTA DEL BYBIT ADAPTER")
    print("=" * 60)

    from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter

    # Crear adapter exactamente como lo hace el código
    print("🔧 Creando BybitAdapter con configuración real...")

    adapter = BybitAdapter(
        api_key=os.getenv('BYBIT_API_KEY'),
        api_secret=os.getenv('BYBIT_API_SECRET'),
        http_proxy=os.getenv('PROXY_URL'),
        https_proxy=os.getenv('PROXY_URL')
    )

    print("✅ Adapter creado")

    # Inicializar (esto aplica la corrección de timestamp)
    print("\n🚀 Inicializando adapter...")
    success = await adapter.initialize(verbose=True)

    if success:
        print("✅ Adapter inicializado correctamente")

        # Verificar configuración de timestamp
        if hasattr(adapter, '_exchange') and adapter._exchange:
            exchange = adapter._exchange

            # Verificar que el patching está aplicado
            test_timestamp = exchange.milliseconds()
            real_time = int(asyncio.get_event_loop().time() * 1000)
            diff = real_time - test_timestamp

            print(f"\n⏰ Verificación de timestamp:")
            print(f"   Timestamp generado: {test_timestamp}")
            print(f"   Timestamp real: {real_time}")
            print(f"   Diferencia: {diff}ms")

            if diff >= 1900 and diff <= 2100:  # ~2000ms ±100ms
                print("   ✅ Corrección de timestamp aplicada correctamente")
            else:
                print("   ⚠️ Corrección de timestamp puede no estar funcionando")

        # Test de precio
        print("\n💰 Test de obtención de precio...")
        try:
            price = await adapter._exchange.fetch_ticker('BTC/USDT:USDT')
            if price and 'last' in price:
                print(f"   ✅ Precio obtenido: ${price['last']:.4f}")
                print("✅ ¡BYBIT FUNCIONANDO PERFECTAMENTE!")
                return True
            else:
                print("❌ Precio no obtenido")
                return False

        except Exception as e:
            print(f"❌ Error obteniendo precio: {e}")
            return False

    else:
        print("❌ Falló la inicialización del adapter")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bybit_adapter_config())
    print(f"\n🏁 RESULTADO FINAL: {'✅ Éxito - Bybit funciona con adapter real' if success else '❌ Falló - Problema persiste'}")
    sys.exit(0 if success else 1)
