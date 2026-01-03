#!/usr/bin/env python3
"""
Prueba específica para verificar si xAI API puede consultar información de X/Twitter.
Análisis de capacidades de Grok para acceder a datos de X en tiempo real.
"""

import os
import sys
import json
import time

def test_xai_twitter_access():
    """Prueba si xAI puede acceder a información de X/Twitter."""
    print("🐦 PRUEBA DE ACCESO A X/TWITTER - XAI API")
    print("=" * 60)

    # Usar la API key desde variable de entorno
    xai_api_key = os.getenv("XAI_API_KEY", "").strip()

    if not xai_api_key:
        print("❌ No se encontró XAI_API_KEY")
        print("ℹ️ xAI API no está configurada en el sistema")
        print("\n🔍 INFORMACIÓN BASADA EN DOCUMENTACIÓN PÚBLICA:")
        print_xai_twitter_capabilities()
        return

    try:
        import requests

        print("✅ API key de xAI encontrada")
        print("🔄 Probando acceso a datos de X/Twitter...")

        # URL de la API de xAI (basado en documentación)
        xai_base_url = "https://api.x.ai/v1"

        # Pruebas específicas de acceso a X
        test_queries = [
            {
                "query": "¿Cuál es el tweet más reciente de @elonmusk sobre xAI?",
                "description": "Acceso directo a tweets de usuarios específicos"
            },
            {
                "query": "¿Qué se está discutiendo actualmente sobre criptomonedas en X?",
                "description": "Acceso a tendencias y conversaciones en tiempo real"
            },
            {
                "query": "¿Puedes resumir las menciones recientes a #Bitcoin en Twitter?",
                "description": "Acceso a hashtags y trending topics"
            },
            {
                "query": "¿Cuál es el sentimiento general sobre Dogecoin en X hoy?",
                "description": "Análisis de sentimiento en tiempo real"
            }
        ]

        results = {}
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n🔍 Prueba {i}: {test_case['description']}")
            print(f"   Query: {test_case['query']}")

            try:
                # Hacer la consulta usando requests (API REST)
                start_time = time.time()

                headers = {
                    "Authorization": f"Bearer {xai_api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "grok-3",  # Usar modelo disponible
                    "messages": [
                        {"role": "user", "content": test_case['query']}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }

                response = requests.post(
                    f"{xai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                end_time = time.time()
                processing_time = end_time - start_time

                if response.status_code == 200:
                    response_data = response.json()
                    answer = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    print(".2f"                    print(f"   Respuesta: {answer[:200]}..." if len(answer) > 200 else f"   Respuesta: {answer}")

                    results[f"test_{i}"] = {
                        "query": test_case['query'],
                        "success": True,
                        "response_length": len(answer),
                        "processing_time": processing_time,
                        "has_twitter_data": check_if_twitter_data(answer),
                        "status_code": response.status_code
                    }
                else:
                    print(f"❌ Error HTTP {response.status_code}: {response.text}")
                    results[f"test_{i}"] = {
                        "query": test_case['query'],
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }

            except requests.exceptions.RequestException as e:
                print(f"❌ Error de conexión: {e}")
                results[f"test_{i}"] = {
                    "query": test_case['query'],
                    "success": False,
                    "error": f"Connection error: {str(e)}"
                }
            except Exception as e:
                print(f"❌ Error general: {e}")
                results[f"test_{i}"] = {
                    "query": test_case['query'],
                    "success": False,
                    "error": str(e)
                }

        # Análisis de resultados
        analyze_results(results)

    except Exception as e:
        print(f"❌ Error general al inicializar xAI: {e}")
        print("\n🔍 INFORMACIÓN BASADA EN DOCUMENTACIÓN PÚBLICA:")
        print_xai_twitter_capabilities()

def print_xai_twitter_capabilities():
    """Imprimir información sobre capacidades de xAI con X/Twitter."""
    print("\n" + "=" * 60)
    print("📋 CAPACIDADES DE XAI CON X/TWITTER (DOCUMENTACIÓN)")
    print("=" * 60)

    capabilities = {
        "acceso_tiempo_real": {
            "descripcion": "Grok tiene acceso a información en tiempo real de X",
            "fuente": "Documentación oficial de xAI",
            "nivel_confianza": "Alto"
        },
        "datos_x_integrados": {
            "descripcion": "xAI entrena sus modelos con datos de X/Twitter",
            "fuente": "Anuncios de Elon Musk y documentación xAI",
            "nivel_confianza": "Alto"
        },
        "menciones_twitter": {
            "descripcion": "Puede consultar tweets específicos, usuarios y tendencias",
            "fuente": "Demostraciones públicas de Grok",
            "nivel_confianza": "Medio-Alto"
        },
        "sentimiento_tiempo_real": {
            "descripcion": "Análisis de sentimiento en redes sociales",
            "fuente": "Funcionalidades promocionadas",
            "nivel_confianza": "Medio"
        },
        "tendencias_cripto": {
            "descripcion": "Acceso directo a conversaciones sobre criptomonedas",
            "fuente": "Casos de uso mencionados por xAI",
            "nivel_confianza": "Medio-Alto"
        }
    }

    for feature, details in capabilities.items():
        print(f"\n🔹 {feature.replace('_', ' ').title()}:")
        print(f"   📝 {details['descripcion']}")
        print(f"   🔍 Fuente: {details['fuente']}")
        print(f"   📊 Confianza: {details['nivel_confianza']}")

    print("\n" + "=" * 40)
    print("⚠️ LIMITACIONES CONOCIDAS:")
    print("=" * 40)
    print("• No hay API pública completa aún")
    print("• Acceso limitado a datos históricos profundos")
    print("• Dependiente de la infraestructura de X")
    print("• Posibles restricciones de rate limiting")
    print("• No acceso a datos privados o eliminados")

def check_if_twitter_data(response):
    """Verificar si la respuesta contiene datos de Twitter."""
    twitter_indicators = [
        "@",  # menciones de usuario
        "#",  # hashtags
        "tweet", "tweets", "twitter", "x.com",
        "posted", "posted on", "according to",
        "recently", "today", "just now",
        "trending", "viral", "discussion",
        "conversation", "thread"
    ]

    response_lower = response.lower()
    matches = [indicator for indicator in twitter_indicators if indicator in response_lower]

    return len(matches) > 0, matches

def analyze_results(results):
    """Analizar los resultados de las pruebas."""
    print("\n" + "=" * 60)
    print("📊 ANÁLISIS DE RESULTADOS")
    print("=" * 60)

    successful_tests = sum(1 for result in results.values() if result.get("success", False))
    total_tests = len(results)

    print(f"✅ Tests exitosos: {successful_tests}/{total_tests}")

    if successful_tests > 0:
        print("\n🎯 DETALLE DE TESTS EXITOSOS:")
        for test_id, result in results.items():
            if result.get("success"):
                has_twitter, indicators = result.get("has_twitter", (False, []))
                print(f"\n🔍 {test_id}:")
                print(f"   ⏱️ Tiempo de respuesta: {result.get('processing_time', 0):.2f}s")
                print(f"   📏 Longitud respuesta: {result.get('response_length', 0)} caracteres")
                print(f"   🐦 Datos de X detectados: {'✅' if has_twitter else '❌'}")
                if has_twitter:
                    print(f"   📊 Indicadores encontrados: {', '.join(indicators[:5])}")

        # Conclusión
        twitter_data_tests = sum(1 for result in results.values()
                               if result.get("success") and result.get("has_twitter", (False, []))[0])

        if twitter_data_tests > 0:
            print(f"\n🎉 CONCLUSIÓN: ✅ xAI PUEDE acceder a información de X/Twitter")
            print(f"   {twitter_data_tests}/{successful_tests} respuestas contenían datos de X")
        else:
            print(f"\n⚠️ CONCLUSIÓN: ❓ xAI puede responder pero no se detectaron datos específicos de X")
            print("   Posiblemente limita el acceso o las respuestas son generales")

    else:
        print("\n❌ CONCLUSIÓN: No se pudieron realizar pruebas exitosas")
        print("   Verifica la configuración de la API de xAI")

def check_xai_api_availability():
    """Verificar disponibilidad general de xAI API."""
    print("\n" + "=" * 50)
    print("🔍 VERIFICACIÓN DE DISPONIBILIDAD XAI API")
    print("=" * 50)

    # Usar la API key desde variable de entorno
    xai_key = os.getenv("XAI_API_KEY")
    xai_base_url = "https://api.x.ai/v1"

    print(f"🔑 XAI API Key: {'✅ Configurada' if xai_key else '❌ No configurada'}")
    print(f"🌐 XAI Base URL: {xai_base_url}")

    # Intentar verificar conectividad básica
    try:
        import requests
        headers = {"Authorization": f"Bearer {xai_key}"} if xai_key else {}
        response = requests.get(f"{xai_base_url}/models", timeout=10, headers=headers)
        if response.status_code == 200:
            print("✅ API xAI accesible")
            try:
                models = response.json()
                print(f"📊 Modelos disponibles: {len(models.get('data', []))}")
            except:
                print("📊 Modelos: Respuesta recibida (formato desconocido)")
        else:
            print(f"⚠️ API responde con código: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        print("ℹ️ xAI API puede requerir configuración específica")

def main():
    """Función principal."""
    print("🚀 VERIFICACIÓN DE ACCESO XAI A X/TWITTER")
    print("Para integración potencial en Nexus Core")
    print()

    # Verificar disponibilidad
    check_xai_api_availability()

    # Ejecutar pruebas
    test_xai_twitter_access()

    print("\n" + "=" * 80)
    print("📋 RECOMENDACIONES PARA NEXUS CORE:")
    print("=" * 80)
    print("1. 🧪 **Testing**: Configurar API de xAI para pruebas limitadas")
    print("2. 🔄 **Híbrido**: Usar OpenAI + xAI para diferentes tipos de análisis")
    print("3. 📊 **Sentimiento**: xAI podría ser excelente para análisis de redes sociales")
    print("4. ⚡ **Velocidad**: xAI podría complementar análisis rápidos de mercado")
    print("5. 👀 **Monitoreo**: Seguir evolución de xAI en próximos meses")

if __name__ == "__main__":
    main()
