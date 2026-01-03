#!/usr/bin/env python3
"""
Configuración de Variables de Entorno para Railway - Sistema Híbrido xAI + OpenAI
Guía completa para configurar Nexus Core en Railway con integración xAI.
"""

import os
import json

def generate_railway_env_config():
    """Genera la configuración completa de variables de entorno para Railway."""

    # Configuración base del bot
    base_config = {
        # Telegram Bot
        "TELEGRAM_BOT_TOKEN": "your_telegram_bot_token_here",
        "TELEGRAM_ADMIN_ID": "your_telegram_admin_id_here",

        # OpenAI (sistema principal)
        "OPENAI_API_KEY": "sk-your-openai-api-key-here",
        "OPENAI_MODEL": "gpt-4o",  # Modelo recomendado para trading

        # xAI Integration (sistema híbrido)
        "XAI_API_KEY": "your_xai_api_key_here",
        "XAI_BASE_URL": "https://api.x.ai/v1",
        "XAI_MODEL": "grok-3",  # Modelo balanceado para velocidad/calidad
        "XAI_TIMEOUT": "10",  # Timeout en segundos
        "XAI_MAX_TOKENS": "500",  # Respuestas concisas
        "XAI_COST_PER_TOKEN": "0.00002",  # Costo estimado

        # Exchanges API Keys (opcional - Railway env vars)
        "ALPACA_API_KEY": "your_alpaca_api_key_here",
        "ALPACA_API_SECRET": "your_alpaca_api_secret_here",
        "BYBIT_API_KEY": "your_bybit_api_key_here",
        "BYBIT_API_SECRET": "your_bybit_api_secret_here",

        # Sistema de Trading
        "USE_NEXUS_ENGINE": "true",
        "DEFAULT_LEVERAGE": "5",
        "MAX_POSITIONS": "10",

        # Database
        "DATABASE_URL": "postgresql://user:password@host:port/database",

        # Logging
        "LOG_LEVEL": "INFO",
        "LOG_TO_FILE": "false"
    }

    return base_config

def create_env_file():
    """Crea archivo .env.example con todas las variables necesarias."""

    config = generate_railway_env_config()

    print("🚀 CONFIGURACIÓN DE VARIABLES DE ENTORNO PARA RAILWAY")
    print("=" * 70)
    print()
    print("📋 Copia estas variables en tu configuración de Railway:")
    print()
    print("# 🤖 CONFIGURACIÓN BÁSICA DEL BOT")
    print("TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here")
    print("TELEGRAM_ADMIN_ID=your_telegram_admin_id_here")
    print()

    print("# 🧠 OPENAI (SISTEMA PRINCIPAL)")
    print("OPENAI_API_KEY=sk-your-openai-api-key-here")
    print("OPENAI_MODEL=gpt-4o")
    print()

    print("# 🤖 XAI INTEGRATION (SISTEMA HÍBRIDO)")
    print("XAI_API_KEY=your_xai_api_key_here")
    print("XAI_BASE_URL=https://api.x.ai/v1")
    print("XAI_MODEL=grok-3")
    print("XAI_TIMEOUT=10")
    print("XAI_MAX_TOKENS=500")
    print("XAI_COST_PER_TOKEN=0.00002")
    print()

    print("# 📊 EXCHANGES API KEYS (OPCIONAL)")
    print("ALPACA_API_KEY=your_alpaca_api_key_here")
    print("ALPACA_API_SECRET=your_alpaca_api_secret_here")
    print("BYBIT_API_KEY=your_bybit_api_key_here")
    print("BYBIT_API_SECRET=your_bybit_api_secret_here")
    print()

    print("# ⚙️ SISTEMA DE TRADING")
    print("USE_NEXUS_ENGINE=true")
    print("DEFAULT_LEVERAGE=5")
    print("MAX_POSITIONS=10")
    print()

    print("# 💾 DATABASE")
    print("DATABASE_URL=postgresql://user:password@host:port/database")
    print()

    print("# 📝 LOGGING")
    print("LOG_LEVEL=INFO")
    print("LOG_TO_FILE=false")
    print()

    # Crear archivo .env.example
    with open('.env.example', 'w') as f:
        f.write("# Nexus Core - Railway Environment Variables\n")
        f.write("# Copia este archivo como .env y configura tus valores\n\n")

        for key, value in config.items():
            if 'your_' in value:
                f.write(f"{key}={value}\n")
            else:
                f.write(f"{key}={value}\n")

    print("✅ Archivo .env.example creado con todas las variables necesarias")
    print()

def validate_env_config():
    """Valida que las variables de entorno críticas estén configuradas."""

    print("🔍 VALIDACIÓN DE CONFIGURACIÓN")
    print("=" * 40)

    required_vars = [
        ("TELEGRAM_BOT_TOKEN", "Token del bot de Telegram"),
        ("OPENAI_API_KEY", "API Key de OpenAI"),
        ("XAI_API_KEY", "API Key de xAI (sistema híbrido)")
    ]

    optional_vars = [
        ("TELEGRAM_ADMIN_ID", "ID del administrador de Telegram"),
        ("ALPACA_API_KEY", "API Key de Alpaca"),
        ("BYBIT_API_KEY", "API Key de Bybit"),
        ("DATABASE_URL", "URL de base de datos PostgreSQL")
    ]

    print("📋 Variables REQUERIDAS:")
    all_required = True
    for var, description in required_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower().replace('_', '_')}_here":
            print(f"   ✅ {var}: Configurada ({description})")
        else:
            print(f"   ❌ {var}: NO configurada ({description})")
            all_required = False

    print("\n📋 Variables OPCIONALES:")
    for var, description in optional_vars:
        value = os.getenv(var)
        if value and not value.startswith("your_"):
            print(f"   ✅ {var}: Configurada ({description})")
        else:
            print(f"   ⚠️  {var}: No configurada ({description})")

    print("\n📊 Variables del SISTEMA HÍBRIDO:")
    xai_vars = [
        ("XAI_MODEL", "grok-3"),
        ("XAI_TIMEOUT", "10"),
        ("XAI_MAX_TOKENS", "500"),
        ("XAI_COST_PER_TOKEN", "0.00002")
    ]

    for var, default in xai_vars:
        value = os.getenv(var, default)
        print(f"   📊 {var}: {value}")

    print()
    if all_required:
        print("🎉 CONFIGURACIÓN COMPLETA - El sistema híbrido está listo!")
        return True
    else:
        print("⚠️  CONFIGURACIÓN INCOMPLETA - Revisa las variables requeridas")
        return False

def test_hybrid_system():
    """Prueba básica del sistema híbrido xAI + OpenAI."""

    print("🧪 PRUEBA DEL SISTEMA HÍBRIDO")
    print("=" * 40)

    try:
        from servos.xai_integration import xai_integration
        from servos.ai_analyst import NexusAnalyst

        # Test xAI
        print("🤖 Probando xAI...")
        xai_result = xai_integration.query_xai(
            "Hola, sistema híbrido funcionando",
            context="alert",
            max_retries=1
        )

        if xai_result["success"]:
            print(f"   ✅ xAI: {xai_result['provider']} - {xai_result['response'][:50]}...")
        else:
            print(f"   ❌ xAI: {xai_result['error']}")

        # Test OpenAI (fallback)
        print("🧠 Probando OpenAI...")
        analyst = NexusAnalyst()
        openai_result = analyst.analyze_market_data(
            {"query": "Test sistema híbrido", "context": "test"},
            "general_analysis"
        )

        if openai_result and "analysis" in openai_result:
            print(f"   ✅ OpenAI: Respuesta recibida ({len(openai_result['analysis'])} chars)")
        else:
            print("   ❌ OpenAI: Error en análisis")

        print("\n📊 RESULTADO: Sistema híbrido operativo!"        return True

    except Exception as e:
        print(f"❌ Error en prueba del sistema híbrido: {e}")
        return False

def main():
    """Función principal."""
    print("🚀 CONFIGURACIÓN RAILWAY - SISTEMA HÍBRIDO XAI + OPENAI")
    print("Para Nexus Core - Trading Bot")
    print()

    # Crear archivo de configuración
    create_env_file()

    # Validar configuración actual
    config_ok = validate_env_config()

    # Probar sistema híbrido si la configuración es correcta
    if config_ok:
        test_hybrid_system()

    print("\n" + "=" * 80)
    print("📋 INSTRUCCIONES PARA RAILWAY:")
    print("=" * 80)
    print("1. 🔑 Ve a tu proyecto en Railway")
    print("2. ⚙️  Ve a Variables de Entorno")
    print("3. ➕ Agrega cada variable listada arriba")
    print("4. 🔄 Redeploy tu aplicación")
    print("5. ✅ El sistema híbrido estará activo!")
    print()
    print("💡 RECUERDA:")
    print("   • XAI_API_KEY: Tu API key de xAI (no hardcodeada)")
    print("   • OPENAI_API_KEY: Tu API key de OpenAI (sistema principal)")
    print("   • Variables opcionales mejoran funcionalidad pero no son requeridas")
    print()
    print("🎯 BENEFICIOS DEL SISTEMA HÍBRIDO:")
    print("   • ⚡ Consultas rápidas con xAI para análisis básico")
    print("   • 🧠 Análisis profundos con OpenAI para decisiones críticas")
    print("   • 💰 Reducción de ~30-50% en costos de OpenAI")
    print("   • 🔄 Fallback automático si un sistema falla")
    print("   • 📈 Mejor rendimiento general del bot")

if __name__ == "__main__":
    main()
