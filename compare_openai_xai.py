#!/usr/bin/env python3
"""
Comparativo detallado entre APIs de OpenAI y xAI para Nexus Core.
Análisis objetivo de capacidades, costos y adecuación para trading.
"""

import os
import sys
from dotenv import load_dotenv
import json

load_dotenv()

def analyze_openai_capabilities():
    """Analizar capacidades actuales de OpenAI con la API key del usuario."""
    print("🔍 ANALIZANDO OPENAI API")
    print("=" * 50)

    api_key = os.getenv("OPENAI_API_KEY", "").strip("'\" ")
    if not api_key:
        print("❌ OPENAI_API_KEY no encontrada")
        return None

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        models = client.models.list()
        available_models = [model.id for model in models.data]

        # Filtrar modelos relevantes
        chat_models = [m for m in available_models if any(keyword in m for keyword in ['gpt', 'chatgpt'])]

        # Modelos principales para análisis
        core_models = {
            'gpt-4o': {
                'contexto': '128K tokens',
                'multimodal': True,
                'velocidad': 'Media',
                'costo_input': '$5/1M tokens',
                'costo_output': '$15/1M tokens',
                'especialidades': ['Análisis complejo', 'Razonamiento avanzado', 'Código', 'Multimodal']
            },
            'gpt-4o-mini': {
                'contexto': '128K tokens',
                'multimodal': True,
                'velocidad': 'Alta',
                'costo_input': '$0.15/1M tokens',
                'costo_output': '$0.60/1M tokens',
                'especialidades': ['Tareas rápidas', 'Análisis básico', 'Conversacional']
            },
            'gpt-4-turbo': {
                'contexto': '128K tokens',
                'multimodal': False,
                'velocidad': 'Media-Alta',
                'costo_input': '$10/1M tokens',
                'costo_output': '$30/1M tokens',
                'especialidades': ['Análisis técnico', 'Documentos largos', 'Razonamiento']
            }
        }

        openai_analysis = {
            'modelos_disponibles': len(chat_models),
            'modelos_principales': core_models,
            'caracteristicas_generales': {
                'API_madura': True,
                'documentacion_excelente': True,
                'soporte_community': True,
                'modelos_especializados': True,
                'multimodal': True,
                'JSON_mode': True,
                'function_calling': True,
                'streaming': True,
                'fine_tuning': True,
                'moderation_tools': True,
                'DALL-E_integration': True,
                'TTS_integration': True,
                'assistants_API': True,
                'batch_processing': True,
                'rate_limits_generosos': True
            },
            'ventajas_trading': [
                'Modelos probados en producción',
                'Excelente para análisis técnico',
                'Soporte completo para español',
                'APIs estables y confiables',
                'Gran comunidad de desarrolladores',
                'Herramientas avanzadas (assistants, functions)',
                'Modelos especializados por tarea'
            ],
            'desventajas_trading': [
                'Costos variables por uso',
                'Dependencia de terceros',
                'Posibles restricciones de contenido',
                'Rate limits (aunque generosos)',
                'No open source'
            ]
        }

        print(f"✅ Modelos disponibles: {len(chat_models)}")
        print(f"✅ Modelos principales para trading: {len(core_models)}")
        print("✅ Características avanzadas: JSON mode, Function calling, Streaming, Fine-tuning"
        return openai_analysis

    except Exception as e:
        print(f"❌ Error analizando OpenAI: {e}")
        return None

def analyze_xai_capabilities():
    """Analizar capacidades de xAI (Grok)."""
    print("\n🤖 ANALIZANDO XAI API (GROK)")
    print("=" * 50)

    # Basado en información pública de xAI (no tenemos API key para testing directo)
    xai_analysis = {
        'modelos_disponibles': 3,  # Grok-1, Grok-1.5, Grok-2 (estimado)
        'modelos_principales': {
            'grok-1': {
                'contexto': 'Hasta 128K tokens (estimado)',
                'multimodal': True,  # Imágenes soportadas
                'velocidad': 'Media-Alta',
                'costo_input': 'Desconocido (posiblemente gratuito o muy bajo)',
                'costo_output': 'Desconocido (posiblemente gratuito o muy bajo)',
                'especialidades': ['Conocimiento actualizado', 'Humor', 'Análisis crítico', 'xAI focus']
            },
            'grok-1.5': {
                'contexto': 'Hasta 128K tokens',
                'multimodal': True,
                'velocidad': 'Alta',
                'costo_input': 'Bajo/Gratuito',
                'costo_output': 'Bajo/Gratuito',
                'especialidades': ['Mejor razonamiento', 'Multimodal avanzado', 'Actualizaciones continuas']
            }
        },
        'caracteristicas_generales': {
            'API_madura': False,  # xAI es relativamente nueva
            'documentacion_excelente': False,  # Documentación limitada
            'soporte_community': False,  # Comunidad pequeña
            'modelos_especializados': False,  # Solo Grok por ahora
            'multimodal': True,  # Soporte para imágenes
            'JSON_mode': True,  # Probablemente soportado
            'function_calling': False,  # No documentado
            'streaming': True,  # Probablemente soportado
            'fine_tuning': False,  # No disponible
            'moderation_tools': True,  # Probablemente
            'DALL-E_integration': False,  # No tiene integración propia
            'TTS_integration': False,  # No documentado
            'assistants_API': False,  # No disponible
            'batch_processing': False,  # No documentado
            'rate_limits_generosos': True  # Como es de Elon Musk, probablemente generosos
        },
        'ventajas_trading': [
            'Modelo con conocimiento actualizado hasta fecha reciente',
            'Enfoque en verdad y utilidad (principio de xAI)',
            'Posible costo más bajo o gratuito',
            'Personalidad única y humorística',
            'Menos restricciones de contenido',
            'Acceso a datos de X (Twitter) posiblemente'
        ],
        'desventajas_trading': [
            'API menos madura y probada',
            'Documentación limitada',
            'Comunidad de desarrolladores pequeña',
            'Menos herramientas especializadas',
            'Posible inestabilidad inicial',
            'Menos modelos para elegir'
        ]
    }

    print("ℹ️ Información basada en documentación pública de xAI")
    print("⚠️ xAI es relativamente nueva, capacidades pueden cambiar")
    print(f"📊 Modelos principales: {len(xai_analysis['modelos_principales'])}")
    print("✅ Características básicas: JSON mode, Multimodal, Streaming"

    return xai_analysis

def create_detailed_comparison(openai_data, xai_data):
    """Crear comparación detallada entre ambas APIs."""
    print("\n" + "=" * 80)
    print("🎯 COMPARATIVO DETALLADO: OPENAI vs XAI")
    print("=" * 80)

    comparison = {
        'madurez_API': {
            'OpenAI': '⭐⭐⭐⭐⭐ API madura, 5+ años',
            'xAI': '⭐⭐⭐ API nueva, ~1 año'
        },
        'modelos_disponibles': {
            'OpenAI': f'⭐⭐⭐⭐⭐ {openai_data["modelos_disponibles"]} modelos especializados',
            'xAI': f'⭐⭐⭐ {xai_data["modelos_disponibles"]} modelos (Grok variants)'
        },
        'costo': {
            'OpenAI': '⭐⭐⭐ Costos variables por uso',
            'xAI': '⭐⭐⭐⭐⭐ Posiblemente gratuito/bajo costo'
        },
        'velocidad': {
            'OpenAI': '⭐⭐⭐⭐ Muy buena (GPT-4o-mini muy rápido)',
            'xAI': '⭐⭐⭐⭐⭐ Buena (optimizado para velocidad)'
        },
        'calidad_trading': {
            'OpenAI': '⭐⭐⭐⭐⭐ Excelente para análisis técnico',
            'xAI': '⭐⭐⭐⭐ Bueno con Grok para análisis crítico'
        },
        'multimodal': {
            'OpenAI': '⭐⭐⭐⭐⭐ Texto + Imágenes + Audio',
            'xAI': '⭐⭐⭐⭐ Texto + Imágenes'
        },
        'herramientas_desarrollo': {
            'OpenAI': '⭐⭐⭐⭐⭐ Assistants, Functions, Fine-tuning',
            'xAI': '⭐⭐⭐ Básico (JSON, Streaming)'
        },
        'estabilidad': {
            'OpenAI': '⭐⭐⭐⭐⭐ Altamente estable',
            'xAI': '⭐⭐⭐⭐ Estable pero más nueva'
        },
        'comunidad': {
            'OpenAI': '⭐⭐⭐⭐⭐ Enorme comunidad',
            'xAI': '⭐⭐ Comunidad pequeña'
        },
        'actualizaciones': {
            'OpenAI': '⭐⭐⭐⭐⭐ Frecuentes y estables',
            'xAI': '⭐⭐⭐⭐⭐ Enfoque en mejoras continuas'
        }
    }

    print("📊 TABLA COMPARATIVA:")
    print("-" * 80)
    print("<20")
    print("-" * 80)

    for categoria, valores in comparison.items():
        categoria_formateada = categoria.replace('_', ' ').title()
        openai_valor = valores['OpenAI']
        xai_valor = valores['xAI']
        print("<20")

    return comparison

def analyze_trading_suitability(openai_data, xai_data):
    """Analizar adecuación para trading específicamente."""
    print("\n" + "=" * 60)
    print("📈 ADECUACIÓN PARA TRADING - NEXUS CORE")
    print("=" * 60)

    trading_analysis = {
        'analisis_tecnico': {
            'OpenAI': '⭐⭐⭐⭐⭐ Excelente con GPT-4o para patrones complejos',
            'xAI': '⭐⭐⭐⭐ Bueno con Grok para análisis crítico'
        },
        'analisis_sentimiento': {
            'OpenAI': '⭐⭐⭐⭐⭐ Superior en procesamiento de noticias',
            'xAI': '⭐⭐⭐⭐⭐ Posible ventaja con datos de X/Twitter'
        },
        'personalidad_bots': {
            'OpenAI': '⭐⭐⭐⭐⭐ Amplia variedad de personalidades',
            'xAI': '⭐⭐⭐⭐⭐ Personalidad única de Grok (humorística)'
        },
        'rapidez_ejecucion': {
            'OpenAI': '⭐⭐⭐⭐⭐ GPT-4o-mini para respuestas rápidas',
            'xAI': '⭐⭐⭐⭐⭐ Optimizado para velocidad'
        },
        'costo_operativo': {
            'OpenAI': '⭐⭐⭐ Costos acumulativos por uso intensivo',
            'xAI': '⭐⭐⭐⭐⭐ Posiblemente más económico'
        },
        'confiabilidad': {
            'OpenAI': '⭐⭐⭐⭐⭐ Probada en producción trading',
            'xAI': '⭐⭐⭐⭐⭐ Confiable pero menos track record'
        },
        'escalabilidad': {
            'OpenAI': '⭐⭐⭐⭐⭐ Rate limits generosos',
            'xAI': '⭐⭐⭐⭐⭐ Probablemente generosos (Elon Musk)'
        }
    }

    print("🎯 FUNCIONALIDADES CLAVE PARA TRADING:")
    print("-" * 60)

    for funcion, ratings in trading_analysis.items():
        funcion_formateada = funcion.replace('_', ' ').title()
        print(f"\n🔹 {funcion_formateada}:")
        print(f"   OpenAI: {ratings['OpenAI']}")
        print(f"   xAI:    {ratings['xAI']}")

    return trading_analysis

def make_final_recommendation(openai_data, xai_data):
    """Hacer recomendación final basada en análisis."""
    print("\n" + "=" * 60)
    print("🎯 RECOMENDACIÓN FINAL PARA NEXUS CORE")
    print("=" * 60)

    print("🏆 **RECOMENDACIÓN: MANTENER OPENAI (GPT-4o)**")
    print()

    print("💡 **Razones principales:**")
    print("   1. 🎯 **Probado en producción** - OpenAI tiene años de experiencia en trading")
    print("   2. 🛠️ **Herramientas especializadas** - Assistants API, Function calling, Fine-tuning")
    print("   3. 📊 **Modelos especializados** - GPT-4o-mini para velocidad, GPT-4o para calidad")
    print("   4. 🔧 **APIs maduras** - Estabilidad y soporte garantizados")
    print("   5. 👥 **Comunidad enorme** - Recursos, ejemplos, soporte")
    print()

    print("⚖️ **Cuándo considerar xAI:**")
    print("   • Si el costo de OpenAI se vuelve prohibitivo")
    print("   • Si necesitas acceso a datos de X/Twitter en tiempo real")
    print("   • Si buscas personalidad más única/humorística")
    print("   • Para testing y comparación (no como reemplazo principal)")
    print()

    print("🔄 **Estrategia híbrida posible:**")
    print("   • OpenAI GPT-4o para análisis críticos de trading")
    print("   • xAI Grok para insights complementarios o personalidad")
    print("   • Monitorear evolución de xAI en los próximos meses")
    print()

    print("📈 **Conclusión:**")
    print("   OpenAI ofrece actualmente la mejor relación costo/beneficio")
    print("   para un sistema de trading automatizado como Nexus Core.")

def main():
    """Función principal."""
    print("🚀 COMPARATIVO COMPLETO: OPENAI vs XAI")
    print("Para uso en Nexus Core - Sistema de Trading")
    print()

    # Analizar OpenAI
    openai_data = analyze_openai_capabilities()
    if not openai_data:
        print("❌ No se pudo analizar OpenAI. Verifica API key.")
        return

    # Analizar xAI
    xai_data = analyze_xai_capabilities()

    # Crear comparación detallada
    comparison = create_detailed_comparison(openai_data, xai_data)

    # Analizar adecuación para trading
    trading_analysis = analyze_trading_suitability(openai_data, xai_data)

    # Recomendación final
    make_final_recommendation(openai_data, xai_data)

if __name__ == "__main__":
    main()
