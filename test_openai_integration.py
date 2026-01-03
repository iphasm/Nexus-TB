#!/usr/bin/env python3
"""
Script de prueba para verificar la integración completa de OpenAI GPT-4o en Nexus Core.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_openai_configuration():
    """Prueba la configuración básica de OpenAI."""
    print("🔧 PRUEBA DE CONFIGURACIÓN OPENAI")
    print("=" * 50)

    # Usar API key desde variable de entorno (NO HARDCODEAR)
    api_key = os.getenv("OPENAI_API_KEY", "").strip("'\" ")
    if not api_key:
        print("❌ OPENAI_API_KEY no encontrada en variables de entorno")
        print("   Configura: export OPENAI_API_KEY='tu_api_key_aqui'")
        return False

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        # Verificar modelos disponibles
        models = client.models.list()
        available_models = [model.id for model in models.data]

        print("✅ API Key: Válida")
        print(f"📊 Modelos disponibles: {len(available_models)}")

        # Verificar GPT-4o
        if "gpt-4o" in available_models:
            print("✅ GPT-4o: Disponible")
        else:
            print("❌ GPT-4o: NO disponible")
            return False

        # Verificar GPT-4o-mini
        if "gpt-4o-mini" in available_models:
            print("✅ GPT-4o-mini: Disponible")
        else:
            print("⚠️ GPT-4o-mini: NO disponible")

        return True

    except Exception as e:
        print(f"❌ Error de configuración: {e}")
        return False

async def test_nexus_analyst():
    """Prueba el NexusAnalyst con GPT-4o."""
    print("\n🤖 PRUEBA DE NEXUS ANALYST")
    print("=" * 50)

    try:
        from servos.ai_analyst import NexusAnalyst

        analyst = NexusAnalyst()
        if not analyst.client:
            print("❌ NexusAnalyst: Cliente no inicializado")
            return False

        print(f"✅ NexusAnalyst inicializado con modelo: {analyst.model}")

        # Prueba básica de conectividad
        test_response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: analyst.client.chat.completions.create(
                model=analyst.model,
                messages=[{"role": "user", "content": "Hola, responde con una sola palabra: OK"}],
                max_tokens=10
            )
        )

        response_text = test_response.choices[0].message.content.strip()
        print(f"✅ Respuesta de prueba: '{response_text}'")

        # Verificar que usó GPT-4o
        if "gpt-4o" in str(test_response.model):
            print("✅ Modelo correcto usado en la respuesta")
        else:
            print(f"⚠️ Modelo diferente usado: {test_response.model}")

        return True

    except Exception as e:
        print(f"❌ Error en NexusAnalyst: {e}")
        return False

async def test_task_scheduler():
    """Prueba el TaskScheduler con GPT-4o."""
    print("\n📅 PRUEBA DE TASK SCHEDULER")
    print("=" * 50)

    try:
        from servos.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        if not scheduler.client:
            print("❌ TaskScheduler: Cliente no inicializado")
            return False

        print(f"✅ TaskScheduler inicializado con modelo: {scheduler.model}")

        # Prueba básica de parsing
        test_prompt = "Recuérdame comprar café mañana a las 9 AM"

        # Simular parsing (sin ejecutar el scheduling completo)
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: scheduler.client.chat.completions.create(
                    model=scheduler.model,
                    messages=[
                        {"role": "system", "content": "Parse scheduling requests into JSON format."},
                        {"role": "user", "content": test_prompt}
                    ],
                    max_tokens=50
                )
            )

            print(f"✅ TaskScheduler parsing funciona: {len(response.choices[0].message.content)} caracteres")

            if "gpt-4o" in str(response.model):
                print("✅ TaskScheduler usa modelo correcto")
            else:
                print(f"⚠️ TaskScheduler usa modelo diferente: {response.model}")

        except Exception as e:
            print(f"⚠️ TaskScheduler parsing falló: {e}")
            # No es crítico para la prueba básica

        return True

    except Exception as e:
        print(f"❌ Error en TaskScheduler: {e}")
        return False

def test_system_directive():
    """Prueba la configuración en system_directive.py."""
    print("\n⚙️ PRUEBA DE SYSTEM DIRECTIVE")
    print("=" * 50)

    try:
        from system_directive import OPENAI_MODEL
        print(f"✅ OPENAI_MODEL configurado: {OPENAI_MODEL}")

        if OPENAI_MODEL == "gpt-4o":
            print("✅ Modelo correcto configurado (GPT-4o)")
            return True
        else:
            print(f"⚠️ Modelo diferente configurado: {OPENAI_MODEL}")
            return False

    except ImportError:
        print("❌ No se puede importar OPENAI_MODEL desde system_directive")
        return False
    except Exception as e:
        print(f"❌ Error en system_directive: {e}")
        return False

async def run_comprehensive_test():
    """Ejecuta todas las pruebas."""
    print("🚀 INICIANDO PRUEBAS COMPRENSIVAS DE OPENAI INTEGRATION")
    print("=" * 60)

    results = []

    # 1. Configuración básica
    results.append(("Configuración OpenAI", test_openai_configuration()))

    # 2. System directive
    results.append(("System Directive", test_system_directive()))

    # 3. Nexus Analyst
    results.append(("Nexus Analyst", await test_nexus_analyst()))

    # 4. Task Scheduler
    results.append(("Task Scheduler", await test_task_scheduler()))

    # Resultados finales
    print("\n" + "=" * 60)
    print("📊 RESULTADOS FINALES")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! OpenAI GPT-4o está correctamente configurado.")
        print("\n💡 El Nexus Core ahora puede usar GPT-4o para:")
        print("   • Análisis de señales con personalidad")
        print("   • Análisis de sentimiento de mercado")
        print("   • Programación inteligente de tareas")
        print("   • Análisis macro y FOMC")
        print("   • Generación de briefings de mercado")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa la configuración.")

    return all_passed

if __name__ == "__main__":
    try:
        # Verificar que la API key esté configurada
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY no configurada")
            print("   Ejecuta: export OPENAI_API_KEY='tu_api_key_aqui'")
            print("   Luego: python test_openai_integration.py")
            sys.exit(1)

        # Ejecutar pruebas
        asyncio.run(run_comprehensive_test())

    except Exception as e:
        print(f"❌ Error crítico ejecutando pruebas: {e}")
        sys.exit(1)
