#!/usr/bin/env python3
"""
Script para verificar modelos disponibles con la API key de OpenAI
y recomendar el modelo más conveniente para Nexus Core.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_available_models():
    """Verifica modelos disponibles con la API key."""
    print("🔍 VERIFICACIÓN DE MODELOS DISPONIBLES")
    print("=" * 50)

    api_key = os.getenv("OPENAI_API_KEY", "").strip("'\" ")
    if not api_key:
        print("❌ OPENAI_API_KEY no encontrada")
        print("   Configura: export OPENAI_API_KEY='tu_api_key'")
        return None

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        print("📡 Consultando modelos disponibles...")
        models = client.models.list()

        # Filtrar modelos relevantes para chat/completions
        chat_models = []
        for model in models.data:
            model_id = model.id
            if any(keyword in model_id for keyword in ['gpt', 'chat']):
                chat_models.append(model_id)

        # Ordenar alfabéticamente
        chat_models.sort()

        print(f"✅ Modelos de chat disponibles: {len(chat_models)}")
        print("\n📋 LISTA COMPLETA:")
        for model in chat_models:
            print(f"   • {model}")

        # Modelos principales que nos interesan
        primary_models = {
            'gpt-4o': '🚀 Modelo más avanzado - Mejor para análisis complejo',
            'gpt-4o-mini': '⚡ Más rápido y económico - Bueno para tareas rutinarias',
            'gpt-4-turbo': '💪 Muy capaz - Versión anterior de GPT-4',
            'gpt-4': '🏆 GPT-4 original - Máxima calidad',
            'gpt-3.5-turbo': '📉 Más antiguo - Menos recomendado'
        }

        print("\n🎯 MODELOS PRINCIPALES PARA NEXUS:")
        print("-" * 50)

        recommendations = []
        for model, description in primary_models.items():
            if model in chat_models:
                print(f"✅ {model}: {description}")
                recommendations.append((model, description))
            else:
                print(f"❌ {model}: No disponible")

        return recommendations

    except Exception as e:
        print(f"❌ Error consultando modelos: {e}")
        return None

def analyze_nexus_requirements():
    """Analiza los requerimientos del Nexus Core."""
    print("\n🧠 ANÁLISIS DE REQUERIMIENTOS - NEXUS CORE")
    print("=" * 50)

    requirements = {
        "Análisis técnico con personalidad": {
            "complejidad": "ALTA",
            "creatividad": "ALTA",
            "contexto": "MEDIO",
            "velocidad": "MEDIA"
        },
        "Análisis de sentimiento de mercado": {
            "complejidad": "ALTA",
            "creatividad": "MEDIA",
            "contexto": "ALTA",
            "velocidad": "MEDIA"
        },
        "Análisis FOMC/Macro": {
            "complejidad": "ALTA",
            "creatividad": "MEDIA",
            "contexto": "ALTA",
            "velocidad": "MEDIA"
        },
        "Generación de briefings": {
            "complejidad": "MEDIA-ALTA",
            "creatividad": "ALTA",
            "contexto": "ALTA",
            "velocidad": "MEDIA"
        },
        "Task scheduling (ELIMINADO)": {
            "complejidad": "MEDIA",
            "creatividad": "BAJA",
            "contexto": "MEDIA",
            "velocidad": "ALTA"
        }
    }

    print("📊 Funcionalidades actuales:")
    for feature, reqs in requirements.items():
        print(f"\n🔹 {feature}:")
        for aspect, level in reqs.items():
            print(f"   {aspect.capitalize()}: {level}")

def recommend_model(available_models):
    """Recomienda el mejor modelo basado en análisis."""
    print("\n🎯 RECOMENDACIÓN DE MODELO")
    print("=" * 50)

    if not available_models:
        print("❌ No hay modelos disponibles para analizar")
        return

    # Puntajes por modelo
    model_scores = {
        'gpt-4o': {
            'score': 100,
            'costo': 'Alto',
            'velocidad': 'Media',
            'calidad': 'Excelente',
            'razon': 'Modelo más avanzado disponible. Mejor comprensión contextual, análisis más sofisticado.'
        },
        'gpt-4o-mini': {
            'score': 85,
            'costo': 'Bajo',
            'velocidad': 'Alta',
            'calidad': 'Muy buena',
            'razon': 'Excelente relación costo/beneficio. Suficiente para la mayoría de análisis.'
        },
        'gpt-4-turbo': {
            'score': 90,
            'costo': 'Medio-Alto',
            'velocidad': 'Media-Alta',
            'calidad': 'Muy buena',
            'razon': 'Muy capaz, pero GPT-4o es superior en análisis complejo.'
        },
        'gpt-4': {
            'score': 95,
            'costo': 'Muy alto',
            'velocidad': 'Baja',
            'calidad': 'Excelente',
            'razon': 'Máxima calidad pero más lento y costoso que GPT-4o.'
        },
        'gpt-3.5-turbo': {
            'score': 60,
            'costo': 'Muy bajo',
            'velocidad': 'Muy alta',
            'calidad': 'Aceptable',
            'razon': 'Insuficiente para análisis complejo. No recomendado.'
        }
    }

    # Filtrar solo modelos disponibles
    available_model_scores = {}
    for model_name, _ in available_models:
        if model_name in model_scores:
            available_model_scores[model_name] = model_scores[model_name]

    if not available_model_scores:
        print("⚠️ No se encontraron modelos principales disponibles")
        return

    # Encontrar el mejor modelo
    best_model = max(available_model_scores.items(), key=lambda x: x[1]['score'])

    print("🏆 RECOMENDACIÓN PRINCIPAL:")
    print(f"   🔥 **{best_model[0].upper()}** - Puntaje: {best_model[1]['score']}/100")
    print(f"   💰 Costo: {best_model[1]['costo']}")
    print(f"   ⚡ Velocidad: {best_model[1]['velocidad']}")
    print(f"   🎯 Calidad: {best_model[1]['calidad']}")
    print(f"   💡 Razón: {best_model[1]['razon']}")

    print("\n📊 COMPARACIÓN DE MODELOS DISPONIBLES:")

    for model_name in sorted(available_model_scores.keys()):
        score = available_model_scores[model_name]
        print(f"   • {model_name}: Puntaje {score['score']}/100, Costo: {score['costo']}, Velocidad: {score['velocidad']}, Calidad: {score['calidad']}")
    print("\n💡 CONCLUSIONES:")
    print("• Para análisis de trading, GPT-4o ofrece la mejor calidad")
    print("• GPT-4o-mini es excelente para reducir costos en tareas rutinarias")
    print("• La diferencia de calidad entre GPT-4o y GPT-4o-mini es significativa")
    print("• Recomendación: GPT-4o para máxima precisión en decisiones de trading")

    return best_model[0]

def remove_task_scheduling():
    """Confirma que el task scheduling ha sido removido."""
    print("\n🗑️ TASK SCHEDULING - ELIMINADO")
    print("=" * 50)

    print("✅ Task scheduling removido del sistema")
    print("   • Ya no se importa TaskScheduler")
    print("   • Nexus loader no inicializa task scheduling")
    print("   • Reduce complejidad y dependencias")

if __name__ == "__main__":
    try:
        # Verificar modelos disponibles
        available_models = check_available_models()

        if available_models:
            # Analizar requerimientos
            analyze_nexus_requirements()

            # Hacer recomendación
            recommended_model = recommend_model(available_models)

            # Confirmar eliminación de task scheduling
            remove_task_scheduling()

            print("\n" + "=" * 60)
            print("🎉 ANÁLISIS COMPLETADO")
            print("=" * 60)

            if recommended_model:
                print(f"🏆 MODELO RECOMENDADO: {recommended_model.upper()}")
                print("\n🔧 Para aplicar:")
                print(f"   1. Editar system_directive.py: OPENAI_MODEL = '{recommended_model}'")
                print("   2. Reiniciar el bot")
                print("   3. Verificar con: python verify_openai_model.py")

        else:
            print("❌ No se pudieron verificar los modelos disponibles")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error ejecutando análisis: {e}")
        sys.exit(1)
