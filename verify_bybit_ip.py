#!/usr/bin/env python3
"""
Verificar exactamente qué IP llega a Bybit usando las mismas credenciales y configuración
"""
import os
import sys
import asyncio
import aiohttp
import hmac
import hashlib

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar las variables de entorno exactas
os.environ['PROXY_URL'] = 'http://zqiocknu:cejjpesqaead@96.62.194.97:6299'
os.environ['BYBIT_API_KEY'] = 'S7OMynWEyMysJ8MuHd'
os.environ['BYBIT_API_SECRET'] = 'Q4fvuGFUeE2qE8GtM8Tp5sdPlr33Yt4JGV0e'

async def test_ip_detection():
    """Verificar qué IP detecta Bybit usando las mismas credenciales"""
    print("🌍 VERIFICACIÓN DE IP QUE LLEGA A BYBIT")
    print("=" * 50)

    proxy_url = os.getenv('PROXY_URL')
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')

    print(f"🔑 API Key: {api_key[:8]}...")
    print(f"🌐 Proxy configurado: {proxy_url}")

    # Test 1: Verificar IP del proxy con servicio público
    print("\n🌐 Test 1: IP detectada por servicios públicos")
    print("-" * 40)

    try:
        async with aiohttp.ClientSession() as session:
            # Test con ipify.org
            async with session.get('https://api.ipify.org', proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    public_ip = await resp.text()
                    print(f"✅ IP pública (ipify.org): {public_ip.strip()}")

                    if public_ip.strip() == '96.62.194.97':
                        print("✅ La IP del proxy coincide con la esperada")
                    else:
                        print("⚠️ La IP del proxy NO coincide con la esperada")

            # Test con httpbin.org
            async with session.get('https://httpbin.org/ip', proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    httpbin_ip = data.get('origin', 'Unknown')
                    print(f"✅ IP pública (httpbin.org): {httpbin_ip}")

    except Exception as e:
        print(f"❌ Error verificando IP pública: {e}")

    # Test 2: Verificar qué IP ve Bybit (sin autenticación)
    print("\n🔍 Test 2: Verificación con Bybit (sin auth)")
    print("-" * 40)

    try:
        async with aiohttp.ClientSession() as session:
            # Endpoint público de Bybit
            url = "https://api.bybit.com/v5/market/instruments-info?category=linear&symbol=ETHUSDT"
            async with session.get(url, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                print(f"✅ Bybit responde: HTTP {resp.status}")

                if resp.status == 200:
                    print("✅ Comunicación con Bybit funciona")
                else:
                    print("❌ Problema de comunicación básica con Bybit")

    except Exception as e:
        print(f"❌ Error conectando a Bybit: {e}")

    # Test 3: Simular exactamente la petición que hace CCXT a Bybit
    print("\n🔐 Test 3: Simulación de petición autenticada")
    print("-" * 40)

    try:
        # Crear la misma petición que hace CCXT para obtener balance
        import time

        timestamp = str(int(time.time() * 1000))
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')

        # Crear payload como lo hace CCXT
        payload = f"accountType=UNIFIED&timestamp={timestamp}"
        signature = hmac.new(
            api_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': '10000'
        }

        print("📤 Enviando petición autenticada a Bybit...")
        print(f"   Timestamp: {timestamp}")
        print(f"   Headers: X-BAPI-API-KEY, X-BAPI-SIGN, X-BAPI-TIMESTAMP, X-BAPI-RECV-WINDOW")
        print(f"   Proxy: {proxy_url}")

        async with aiohttp.ClientSession() as session:
            url = "https://api.bybit.com/v5/account/wallet-balance?accountType=UNIFIED"
            async with session.get(url, headers=headers, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                print(f"📥 Respuesta de Bybit: HTTP {resp.status}")

                if resp.status == 200:
                    data = await resp.json()
                    ret_code = data.get('retCode')
                    ret_msg = data.get('retMsg')

                    print(f"   Código de retorno: {ret_code}")
                    print(f"   Mensaje: {ret_msg}")

                    if ret_code == 0:
                        print("🎉 ¡PETICIÓN AUTENTICADA EXITOSA!")
                        print("   ✅ La IP está autorizada en Bybit")
                        balance = data.get('result', {}).get('list', [{}])[0].get('coin', [])
                        usdt_balance = next((coin for coin in balance if coin.get('coin') == 'USDT'), {})
                        if usdt_balance:
                            print(f"   💰 Balance USDT: {usdt_balance.get('walletBalance', 0)}")
                        return True
                    else:
                        print(f"❌ Error de Bybit: {ret_msg}")

                        # Analizar el error específico
                        if 'invalid request' in ret_msg.lower():
                            if 'timestamp' in ret_msg.lower():
                                print("   ⏰ Error de timestamp (resuelto con -2000ms)")
                            elif 'ip' in ret_msg.lower():
                                print("   🌐 Error de IP no autorizada")
                                print("   💡 La IP que llega a Bybit NO está en la lista autorizada")
                            else:
                                print("   ❓ Error de validación desconocido")
                        elif 'permission' in ret_msg.lower():
                            print("   🚫 Error de permisos insuficientes")
                        else:
                            print(f"   ❓ Error desconocido: {ret_msg}")

                        return False
                else:
                    print(f"❌ Error HTTP: {resp.status}")
                    try:
                        error_text = await resp.text()
                        print(f"   Detalles: {error_text[:200]}...")
                    except:
                        pass
                    return False

    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ip_detection())
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡BYBIT FUNCIONANDO! La IP está autorizada.")
    else:
        print("❌ Problema de IP: La dirección que llega a Bybit no está autorizada.")
        print("💡 Solución: Agregar la IP correcta a la lista autorizada en Bybit")
        print("   - IP del proxy: 96.62.194.97 (¿está autorizada?)")
        print("   - O usar un VPS con IP fija autorizada")

