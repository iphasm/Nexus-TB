#!/usr/bin/env python3
"""
Script para agregar el servicio ML training a un proyecto Railway existente
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, cwd=None, shell=True):
    """Run shell command with proper error handling"""
    try:
        print(f"🔧 Ejecutando: {cmd}")
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd,
            shell=shell, cwd=cwd,
            capture_output=True, text=True, check=True
        )
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando comando: {e}")
        print(f"   STDOUT: {e.stdout}")
        print(f"   STDERR: {e.stderr}")
        return False, e.stdout, e.stderr

def check_prerequisites():
    """Check prerequisites for adding ML service"""
    print("🔍 Verificando prerrequisitos...")

    # Check Railway CLI
    success, _, _ = run_command("railway --version")
    if not success:
        print("❌ Railway CLI no está instalado")
        return False

    # Check login status
    success, _, _ = run_command("railway whoami")
    if not success:
        print("❌ No estás logueado en Railway. Ejecuta: railway login")
        return False

    # Check required files
    required_files = [
        "Dockerfile.railway",
        "railway_ml_train.py",
        "requirements-railway.txt",
        "railway-ml-service.json"
    ]

    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Archivo faltante: {file}")
            return False
        print(f"✅ {file}")

    print("✅ Todos los prerrequisitos verificados")
    return True

def get_current_project():
    """Get current linked Railway project"""
    success, stdout, _ = run_command("railway status")
    if success and "Project:" in stdout:
        # Extract project info from status output
        lines = stdout.split('\n')
        for line in lines:
            if line.startswith('Project:'):
                project_name = line.split(':')[1].strip()
                print(f"📁 Proyecto actual: {project_name}")
                return project_name

    print("⚠️ No se pudo determinar el proyecto actual")
    return None

def create_ml_service():
    """Create ML training service in current Railway project"""
    print("\n🚀 Creando servicio ML training...")

    # Add service using Railway CLI
    print("📦 Agregando servicio ML al proyecto...")

    # Railway doesn't have a direct CLI command to add services, so we'll use up
    # This will create a new service based on the railway-ml-service.json config
    success, _, stderr = run_command("railway up --service ml-training")

    if success:
        print("✅ Servicio ML training agregado exitosamente")
        return True
    else:
        print(f"❌ Error agregando servicio: {stderr}")
        print("\n💡 Alternativas:")
        print("1. Ve a https://railway.app/dashboard")
        print("2. Selecciona tu proyecto")
        print("3. Haz click en 'Add Service'")
        print("4. Selecciona 'Empty Service'")
        print("5. Configura manualmente con Dockerfile.railway")
        return False

def configure_service_variables():
    """Configure environment variables for ML service"""
    print("\n🔧 Configurando variables de entorno del servicio ML...")

    # Service-specific variables
    service_vars = {
        "PYTHONUNBUFFERED": "1",
        "LOG_LEVEL": "INFO",
        "TRAINING_ENV": "railway",
        "PORT": "8000",
        # API Keys (user needs to set these)
        "BINANCE_API_KEY": "tu_api_key_aqui",
        "BINANCE_API_SECRET": "tu_secret_aqui",
        "ALPHA_VANTAGE_API_KEY": "opcional"
    }

    print("📝 Variables que necesitas configurar:")
    for key, value in service_vars.items():
        if "tu_" in value:
            print(f"   railway variables set {key}=\"{value}\"  # ⚠️ CONFIGURAR")
        else:
            success, _, _ = run_command(f"railway variables set {key}=\"{value}\"")
            if success:
                print(f"✅ {key} = {value}")
            else:
                print(f"❌ Error configurando {key}")

    print("\n💡 IMPORTANTE:")
    print("- Configura las API keys de Binance en Railway Dashboard")
    print("- Asegúrate de que sean las claves REALES, no placeholders")

def deploy_and_verify():
    """Deploy the ML service and verify it's working"""
    print("\n🚀 Desplegando servicio ML...")

    # Deploy
    success, _, stderr = run_command("railway up --service ml-training")
    if not success:
        print(f"❌ Error en deployment: {stderr}")
        return None

    print("⏳ Esperando que el servicio esté listo...")
    import time
    time.sleep(15)

    # Get service URL
    success, domain, _ = run_command("railway domain --service ml-training")
    if success and domain:
        service_url = f"https://{domain.strip()}"
        print(f"🌐 Servicio ML desplegado en: {service_url}")

        # Test health check
        print("🧪 Probando health check...")
        test_success, _, _ = run_command(f"curl -f {service_url}/health")
        if test_success:
            print("✅ Health check exitoso - Servicio operativo!")
        else:
            print("⚠️ Health check falló - Puede tomar más tiempo en estar listo")

        return service_url
    else:
        print("⚠️ No se pudo obtener la URL automáticamente")
        print("Ejecuta: railway domain --service ml-training")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Add ML training service to existing Railway project")
    parser.add_argument("--skip-checks", action="store_true", help="Skip prerequisite checks")

    args = parser.parse_args()

    print("🚀 Agregar Servicio ML a Proyecto Railway Existente")
    print("=" * 60)

    if not args.skip_checks:
        if not check_prerequisites():
            print("\n❌ Prerrequisitos no cumplidos")
            sys.exit(1)

    # Get current project info
    project_name = get_current_project()
    if not project_name:
        print("\n❌ No se pudo determinar el proyecto actual")
        print("Asegúrate de estar en el directorio correcto y linkeado al proyecto")
        sys.exit(1)

    print(f"\n📋 Proyecto identificado: {project_name}")

    # Create ML service
    if create_ml_service():
        # Configure variables
        configure_service_variables()

        # Deploy and verify
        service_url = deploy_and_verify()

        if service_url:
            print("\n" + "=" * 60)
            print("🎉 SERVICIO ML AGREGADO EXITOSAMENTE!")
            print(f"🌐 URL del servicio: {service_url}")
            print("\n📋 Próximos pasos:")
            print("1. Configura las API keys en Railway Dashboard")
            print("2. Espera 2-3 minutos para que esté completamente listo")
            print("3. Configura RAILWAY_ML_URL en tu bot principal")
            print("4. Prueba con /ml_train en Telegram")

            print("
🔗 Configuración para bot:"            print(f"   export RAILWAY_ML_URL={service_url}")
        else:
            print("\n⚠️ Servicio creado pero no se pudo verificar completamente")
            print("Revisa Railway Dashboard y logs para más detalles")
    else:
        print("\n❌ Error creando el servicio ML")
        print("Revisa las instrucciones alternativas arriba")

if __name__ == "__main__":
    main()
