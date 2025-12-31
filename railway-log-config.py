#!/usr/bin/env python3
"""
Railway Log Configuration Script
Configura las variables de entorno para optimizar logging en Railway
"""

import os
import sys

def setup_railway_logging():
    """Configura logging optimizado para Railway"""

    # Configuración recomendada para Railway
    env_vars = {
        # Nivel de logging principal
        "LOG_LEVEL": "INFO",  # INFO para producción, DEBUG para troubleshooting

        # Configuración de agrupación de logs
        "LOG_GROUP_INTERVAL": "10.0",  # Agrupar logs cada 10 segundos
        "LOG_MAX_GROUP_SIZE": "15",    # Máximo 15 mensajes por grupo

        # Modo silencioso (reduce ruido en producción)
        "QUIET_MODE": "true",  # Activar para reducir logs innecesarios

        # Configuración específica de Railway
        "RAILWAY_LOG_FORMAT": "compact",  # Formato compacto para Railway
    }

    print("🔧 Configuración de Logging para Railway")
    print("=" * 50)

    for key, value in env_vars.items():
        current = os.getenv(key, "NOT_SET")
        print("30")

        # Solo sobrescribir si no está configurado
        if current == "NOT_SET":
            os.environ[key] = value
            print(f"  ✅ Configurado: {key}={value}")
        else:
            print(f"  ⚠️  Ya configurado: {key}={current}")

    print("\n📋 Resumen de Configuración:")
    print(f"  • Nivel de log: {os.getenv('LOG_LEVEL', 'INFO')}")
    print(f"  • Modo silencioso: {os.getenv('QUIET_MODE', 'false')}")
    print(f"  • Intervalo de agrupación: {os.getenv('LOG_GROUP_INTERVAL', '5.0')}s")
    print(f"  • Tamaño máximo de grupo: {os.getenv('LOG_MAX_GROUP_SIZE', '10')}")

    print("\n🎯 Recomendaciones para Railway:")
    print("  • LOG_LEVEL=INFO para producción normal")
    print("  • LOG_LEVEL=DEBUG solo para troubleshooting")
    print("  • QUIET_MODE=true para reducir ruido")
    print("  • Reinicia el bot después de cambiar variables")

if __name__ == "__main__":
    setup_railway_logging()
