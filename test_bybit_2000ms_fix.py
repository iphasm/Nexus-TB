#!/usr/bin/env python3
"""
Test del fix de 2000ms para Bybit timestamps
"""
import os
import sys
import asyncio
import ccxt
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar las variables de entorno
os.environ['PROXY_URL'] = 'http://zqiocknu:cejjpesqaead@96.62.194.97:6299'
os.environ['BYBIT_API_KEY'] = 'S7OMynWEyMysJ8MuHd'
os.environ['BYBIT_API_SECRET'] = 'Q4fvuGFUeE2qE8GtM8Tp5sdPlr33Yt4JGV0e'

def get_server_time_corrected(offset_ms=2000):
    """Función que resta un offset configurable del tiempo actual"""
    return int(time.time() * 1000) - offset_ms

async def test_multiple_offsets():
    """Probar múltiples offsets para encontrar el óptimo"""
    print("🔍 TEST: BÚSQUEDA DEL OFFSET ÓPTIMO PARA BYBIT")
    print("=" * 60)

    # Probar diferentes offsets
    offsets_to_test = [2000, 3000, 3500, 4000, 4500, 5000]

    for offset in offsets_to_test:
        print(f"\n🧪 Probando offset: -{offset}ms")
        print("-" * 30)

        # Crear función con el offset específico
        def get_server_time_corrected_custom():
            return int(time.time() * 1000) - offset

        try:
            # Inicializar exchange
            exchange = ccxt.bybit({
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
                'options': {
                    'adjustForTimeDifference': False,
                    'recvWindow': 10000,
                }
            })

            # Configurar proxy
            proxy_url = os.getenv('PROXY_URL')
            if proxy_url:
                exchange.aiohttp_proxy = proxy_url

            # Aplicar corrección
            exchange.milliseconds = get_server_time_corrected_custom

            # Intentar cargar mercados
            await exchange.load_markets()
            print(f"✅ Mercados cargados con offset -{offset}ms")

            # Intentar obtener precio
            ticker = await exchange.fetch_ticker('BTC/USDT:USDT')
            price = ticker.get('last', 0)
            print(f"   ✅ Precio obtenido: ${price:.4f}")
            await exchange.close()

            print(f"🎉 ¡OFFSET -{offset}ms FUNCIONA!")
            return offset

        except Exception as e:
            error_msg = str(e)
            if 'timestamp' in error_msg.lower():
                # Extraer información de timestamp del error
                import re
                ts_match = re.search(r'req_timestamp\[(\d+)\],server_timestamp\[(\d+)\]', error_msg)
                if ts_match:
                    req_ts, server_ts = ts_match.groups()
                    diff = int(req_ts) - int(server_ts)
                    print(f"   📊 Diferencia detectada: {diff}ms")
                    print(f"   💡 Sugerencia: probar offset de -{abs(diff) + 500}ms")
                else:
                    print(f"   ❌ Error de timestamp: {error_msg[:100]}...")
            else:
                print(f"   ❌ Error: {error_msg[:100]}...")

            try:
                await exchange.close()
            except:
                pass

    print("\n❌ Ningún offset funcionó en el rango probado")
    return None

async def test_bybit_2000ms_fix():
    """Test original con 2000ms"""
    optimal_offset = await test_multiple_offsets()

    if optimal_offset:
        print(f"\n🎯 OFFSET ÓPTIMO ENCONTRADO: -{optimal_offset}ms")
        print("💡 Implementar este valor en el código del adapter")
        return True
    else:
        print("\n❌ No se encontró un offset que funcione")
        print("💡 Puede requerir cambios más drásticos o configuración externa")
        return False

    try:
        # Cargar mercados primero
        print("\n📊 Cargando mercados...")
        await exchange.load_markets()
        print(f"✅ Mercados cargados: {len(exchange.markets)} mercados")

        # Probar obtener precio
        print("\n💰 Probando obtener precio de BTC/USDT...")
        ticker = await exchange.fetch_ticker('BTC/USDT:USDT')
        price = ticker.get('last', 0)
        print(f"✅ Precio obtenido: ${price:.4f}")
        # Probar obtener balance
        print("\n💼 Probando obtener balance...")
        balance = await exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('total', 0)
        print(f"✅ Balance USDT: {usdt_balance}")

        print("\n🎉 ¡BYBIT FUNCIONANDO PERFECTAMENTE CON CORRECCIÓN DE 2000ms!")
        return True

    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")

        # Mostrar detalles del error
        if hasattr(e, 'args') and e.args:
            for arg in e.args:
                if 'timestamp' in str(arg).lower():
                    print("   ⏰ Error relacionado con timestamp detectado")
                    # Extraer información de timestamp si está disponible
                    import re
                    ts_match = re.search(r'req_timestamp\[(\d+)\],server_timestamp\[(\d+)\]', str(arg))
                    if ts_match:
                        req_ts, server_ts = ts_match.groups()
                        diff = int(req_ts) - int(server_ts)
                        print(f"   📊 Diferencia calculada: {diff}ms")
                        print(f"   🎯 Corrección aplicada: -2000ms")
                        if abs(diff) < 10000:  # Dentro del recvWindow
                            print("   💡 El error debería resolverse con esta corrección")
                        else:
                            print("   ⚠️ La diferencia es muy grande, puede necesitar más ajuste")
                print(f"   📋 Detalle: {arg}")

        return False

    finally:
        # Cleanup
        try:
            await exchange.close()
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_bybit_2000ms_fix())
    print(f"\n🏁 RESULTADO: {'✅ Éxito - Bybit funciona con 2000ms' if success else '❌ Falló - Problema persiste'}")
    sys.exit(0 if success else 1)
