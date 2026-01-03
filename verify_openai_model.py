#!/usr/bin/env python3
"""
Script para verificar la configuración del modelo OpenAI en Nexus Core.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def verify_openai_configuration():
    """Verifica la configuración completa de OpenAI."""
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN OPENAI")
    print("=" * 50)

    # 1. Verificar API Key
    api_key = os.getenv("OPENAI_API_KEY", "").strip("'\" ")
    if api_key:
        print(f"✅ API Key: Configurada (últimos 4 dígitos: ...{api_key[-4:]})")
    else:
        print("❌ API Key: NO CONFIGURADA")
        return False

    # 2. Verificar modelo configurado
    try:
        from system_directive import OPENAI_MODEL
        configured_model = OPENAI_MODEL
        print(f"✅ Modelo configurado en system_directive.py: {configured_model}")
    except ImportError:
        configured_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        print(f"⚠️ Modelo por defecto (variable de entorno): {configured_model}")

    # 3. Verificar que las clases usan la configuración correcta
    try:
        from servos.ai_analyst import NexusAnalyst
        analyst = NexusAnalyst()
        if hasattr(analyst, 'model'):
            analyst_model = analyst.model
            print(f"✅ NexusAnalyst model: {analyst_model}")
            if analyst_model == configured_model:
                print("✅ NexusAnalyst: Modelo correcto")
            else:
                print(f"⚠️ NexusAnalyst: Modelo diferente ({analyst_model} vs {configured_model})")
        else:
            print("❌ NexusAnalyst: No tiene atributo model")
    except Exception as e:
        print(f"❌ Error verificando NexusAnalyst: {e}")

    try:
        from servos.task_scheduler import TaskScheduler
        scheduler = TaskScheduler()
        if hasattr(scheduler, 'model'):
            scheduler_model = scheduler.model
            print(f"✅ TaskScheduler model: {scheduler_model}")
            if scheduler_model == configured_model:
                print("✅ TaskScheduler: Modelo correcto")
            else:
                print(f"⚠️ TaskScheduler: Modelo diferente ({scheduler_model} vs {configured_model})")
        else:
            print("❌ TaskScheduler: No tiene atributo model")
    except Exception as e:
        print(f"❌ Error verificando TaskScheduler: {e}")

    # 4. Verificar compatibilidad del modelo
    valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    if configured_model in valid_models:
        print(f"✅ Modelo válido: {configured_model} está en la lista de modelos soportados")
    else:
        print(f"⚠️ Modelo potencialmente inválido: {configured_model}")

    # 5. Recomendaciones
    print("\n📋 RECOMENDACIONES:")
    if configured_model == "gpt-4o":
        print("✅ Configuración óptima: Usando GPT-4o (modelo más avanzado)")
    elif configured_model == "gpt-4o-mini":
        print("⚠️ Usando GPT-4o-mini: Considera actualizar a GPT-4o para mejor calidad")
        print("   Para cambiar: export OPENAI_MODEL=gpt-4o")
    else:
        print(f"ℹ️ Usando modelo personalizado: {configured_model}")

    print("\n🔧 PARA CAMBIAR EL MODELO:")
    print("1. Variable de entorno: export OPENAI_MODEL=gpt-4o")
    print("2. O directamente en system_directive.py: OPENAI_MODEL = 'gpt-4o'")
    print("3. Reiniciar el bot después del cambio")

    return True

if __name__ == "__main__":
    try:
        verify_openai_configuration()
    except Exception as e:
        print(f"❌ Error ejecutando verificación: {e}")
        sys.exit(1)
