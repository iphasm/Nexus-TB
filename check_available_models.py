#!/usr/bin/env python3
"""
Verificar modelos disponibles en OpenAI y xAI APIs
"""

import os
from dotenv import load_dotenv
import requests

# Cargar variables de entorno
load_dotenv()

def check_openai_models():
    """Verificar modelos disponibles en OpenAI."""
    print("🤖 VERIFICANDO MODELOS OPENAI")
    print("=" * 50)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY no encontrada")
        return

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        models = client.models.list()
        available_models = [model.id for model in models.data]

        print(f"✅ {len(available_models)} modelos disponibles")

        # Categorizar modelos
        gpt_models = [m for m in available_models if m.startswith('gpt')]
        other_models = [m for m in available_models if not m.startswith('gpt')]

        print("\n📋 MODELOS GPT:")
        for model in sorted(gpt_models):
            print(f"   • {model}")

        if other_models:
            print("\n📋 OTROS MODELOS:")
            for model in sorted(other_models):
                print(f"   • {model}")

        # Modelos principales para valoración
        valuation_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
        available_valuation = [m for m in valuation_models if m in available_models]

        print(f"\n🎯 MODELOS RECOMENDADOS PARA VALORACIÓN:")
        for model in available_valuation:
            print(f"   ✅ {model}")
        for model in valuation_models:
            if model not in available_models:
                print(f"   ❌ {model} (no disponible)")

        return available_models

    except Exception as e:
        print(f"❌ Error consultando OpenAI: {e}")
        return []

def check_xai_models():
    """Verificar modelos disponibles en xAI."""
    print("\n🧠 VERIFICANDO MODELOS XAI")
    print("=" * 50)

    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("❌ XAI_API_KEY no encontrada")
        return

    try:
        # Intentar consultar modelos disponibles
        headers = {"Authorization": f"Bearer {api_key}"}
        xai_base_url = "https://api.x.ai/v1"

        # Algunos endpoints posibles para modelos
        endpoints_to_try = [
            f"{xai_base_url}/models",
            f"{xai_base_url}/v1/models"
        ]

        models_found = False

        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Modelos obtenidos de {endpoint}")

                    # Intentar extraer información de modelos
                    if 'data' in data:
                        models = [model.get('id', model.get('model', 'unknown')) for model in data['data']]
                    elif isinstance(data, list):
                        models = [model.get('id', model.get('model', 'unknown')) for model in data]
                    else:
                        models = ['grok-3']  # fallback

                    print(f"📋 MODELOS DISPONIBLES:")
                    for model in models:
                        print(f"   • {model}")

                    models_found = True
                    break

            except:
                continue

        if not models_found:
            # Fallback: modelos conocidos de xAI
            print("⚠️ No se pudo consultar API directamente. Modelos conocidos de xAI:")
            known_xai_models = ['grok-3', 'grok-1.5', 'grok-1']
            for model in known_xai_models:
                print(f"   • {model}")

            print("\n🎯 MODELOS RECOMENDADOS PARA VALORACIÓN:")
            print("   ✅ grok-3 (usado actualmente)")
            print("   • grok-1.5 (posible alternativa)")

        return known_xai_models if not models_found else models

    except Exception as e:
        print(f"❌ Error consultando xAI: {e}")
        return []

def compare_models(openai_models, xai_models):
    """Comparar capacidades de modelos."""
    print("\n⚖️ COMPARACIÓN DE MODELOS")
    print("=" * 50)

    print("🤖 OPENAI GPT SERIES:")
    gpt_4_models = [m for m in openai_models if 'gpt-4' in m]
    gpt_3_models = [m for m in openai_models if 'gpt-3.5' in m]

    if gpt_4_models:
        print("   🚀 GPT-4 Series (Más avanzados):")
        for model in sorted(gpt_4_models):
            print(f"      • {model}")

    if gpt_3_models:
        print("   ⚡ GPT-3.5 Series (Más rápidos):")
        for model in sorted(gpt_3_models):
            print(f"      • {model}")

    print("\n🧠 XAI GROK SERIES:")
    for model in sorted(xai_models):
        print(f"   • {model}")

    print("\n📊 VENTAJAS POR API:")
    print("   🤖 OpenAI:")
    print("      ✅ Mayor variedad de modelos")
    print("      ✅ Modelos especializados (4o, 4-turbo, 3.5-turbo)")
    print("      ✅ Mejor soporte para JSON estructurado")
    print("      ✅ Mayor experiencia en análisis financiero")

    print("   🧠 xAI:")
    print("      ✅ Modelo único altamente optimizado")
    print("      ✅ Enfoque en respuestas directas")
    print("      ✅ Conocimiento actualizado continuo")
    print("      ✅ Filosofía de verdad y utilidad")

def main():
    """Función principal."""
    print("🔍 CONSULTA DE MODELOS DISPONIBLES")
    print("OpenAI vs xAI para valoración de criptomonedas")
    print("=" * 60)

    # Verificar modelos de OpenAI
    openai_models = check_openai_models()

    # Verificar modelos de xAI
    xai_models = check_xai_models()

    # Comparar
    if openai_models and xai_models:
        compare_models(openai_models, xai_models)

    print("\n💡 MODELOS USADOS EN LA VALORACIÓN:")
    print("   🤖 OpenAI: gpt-4o (modelo más avanzado disponible)")
    print("   🧠 xAI: grok-3 (modelo principal de xAI)")
    print("\n💡 RECOMENDACIONES:")
    print("   • Para máxima precisión: GPT-4o")
    print("   • Para velocidad: GPT-4o-mini o GPT-3.5-turbo")
    print("   • Para perspectiva alternativa: Grok-3")

if __name__ == "__main__":
    main()
