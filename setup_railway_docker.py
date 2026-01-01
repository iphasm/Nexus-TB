#!/usr/bin/env python3
"""
Railway Docker ML Training Setup Script
Complete setup for ML training service on Railway using Docker
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
import time

def run_command(cmd, cwd=None, shell=True):
    """Run shell command with proper error handling"""
    try:
        print(f"🔧 Ejecutando: {cmd}")
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd,
            shell=shell,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando comando: {e}")
        print(f"   STDOUT: {e.stdout}")
        print(f"   STDERR: {e.stderr}")
        return False, e.stdout, e.stderr

def check_prerequisites():
    """Check all prerequisites for Railway Docker deployment"""
    print("🔍 Verificando prerrequisitos...")

    checks = [
        ("Railway CLI", "railway --version"),
        ("Docker", "docker --version"),
        ("Git", "git --version"),
        ("Python", "python --version"),
    ]

    for name, cmd in checks:
        success, stdout, stderr = run_command(cmd)
        if success:
            print(f"✅ {name}: {stdout.split()[0] if stdout else 'OK'}")
        else:
            print(f"❌ {name}: NO INSTALADO")
            return False

    # Check required files
    required_files = [
        "Dockerfile.railway",
        "railway_ml_train.py",
        "requirements-railway.txt",
        "system_directive.py"
    ]

    for file in required_files:
        if os.path.exists(file):
            print(f"✅ Archivo: {file}")
        else:
            print(f"❌ Archivo faltante: {file}")
            return False

    print("✅ Todos los prerrequisitos verificados")
    return True

def setup_railway_project():
    """Setup Railway project for ML training"""
    print("\n🚀 Configurando proyecto Railway...")

    # Login to Railway (if not already logged in)
    success, _, _ = run_command("railway whoami")
    if not success:
        print("🔑 Necesitas hacer login en Railway primero:")
        print("   railway login")
        print("   Luego ejecuta este script nuevamente.")
        return False

    # Initialize Railway project
    print("📁 Inicializando proyecto Railway...")
    success, _, stderr = run_command("railway init --name nexus-ml-training-docker --yes")
    if success:
        print("✅ Proyecto Railway inicializado")
    elif "already linked" in stderr:
        print("✅ Proyecto Railway ya existe y está linkeado")
    else:
        print(f"❌ Error inicializando Railway: {stderr}")
        return False

    # Link to project if needed
    success, _, _ = run_command("railway link --yes")
    if success:
        print("✅ Proyecto Railway linkeado correctamente")
    else:
        print("⚠️ No se pudo linkear automáticamente. Asegúrate de estar en el directorio correcto.")

    return True

def configure_environment_variables():
    """Configure required environment variables in Railway"""
    print("\n🔧 Configurando variables de entorno...")

    # Required environment variables
    env_vars = {
        "PYTHONUNBUFFERED": "1",
        "LOG_LEVEL": "INFO",
        "TRAINING_ENV": "railway",
        "PORT": "8000"
    }

    # API Keys (these need to be provided by user)
    api_keys = {
        "BINANCE_API_KEY": "Tu API key de Binance",
        "BINANCE_API_SECRET": "Tu API secret de Binance",
        "ALPHA_VANTAGE_API_KEY": "Tu API key de Alpha Vantage (opcional)"
    }

    print("📝 Variables de entorno básicas:")
    for key, value in env_vars.items():
        success, _, _ = run_command(f"railway variables set {key}=\"{value}\"")
        if success:
            print(f"✅ {key} = {value}")
        else:
            print(f"❌ Error configurando {key}")

    print("\n🔑 Variables de API (requieren configuración manual):")
    for key, description in api_keys.items():
        print(f"   railway variables set {key}=\"tu_valor_aqui\"  # {description}")

    print("\n💡 IMPORTANTE: Configura las API keys manualmente antes de continuar:")
    print("   1. Ve a https://railway.app/dashboard")
    print("   2. Selecciona tu proyecto 'nexus-ml-training-docker'")
    print("   3. Ve a Variables en el menú lateral")
    print("   4. Agrega las API keys listadas arriba")

    return True

def build_and_deploy():
    """Build and deploy the Docker container"""
    print("\n🏗️ Construyendo y desplegando contenedor Docker...")

    # Build Docker image locally first (optional, for testing)
    print("🐳 Construyendo imagen Docker localmente...")
    success, _, stderr = run_command("docker build -f Dockerfile.railway -t railway-ml-training:test .")
    if success:
        print("✅ Imagen Docker construida localmente")
    else:
        print(f"⚠️ Error construyendo imagen local: {stderr}")
        print("   Continuando con deployment en Railway...")

    # Deploy to Railway
    print("🚀 Desplegando en Railway...")
    success, _, stderr = run_command("railway up --service railway-ml")

    if success:
        print("✅ Deployment iniciado exitosamente")
    else:
        print(f"❌ Error en deployment: {stderr}")
        print("💡 Posibles soluciones:")
        print("   - Verifica que railway.json esté configurado correctamente")
        print("   - Asegúrate de que las variables de entorno estén configuradas")
        print("   - Revisa los logs: railway logs")
        return False

    # Wait for deployment and get domain
    print("⏳ Esperando a que el servicio esté listo...")
    time.sleep(10)

    success, domain, _ = run_command("railway domain")
    if success and domain:
        service_url = f"https://{domain.strip()}"
        print(f"🌐 Servicio desplegado en: {service_url}")
        print("\n💡 Configura en tu bot principal:")
        print(f"   export RAILWAY_ML_URL={service_url}")
        return service_url
    else:
        print("⚠️ No se pudo obtener automáticamente la URL del servicio")
        print("   Ejecuta 'railway domain' manualmente para obtener la URL")
        return None

def test_deployment(service_url=None):
    """Test the deployed service"""
    print("\n🧪 Probando el servicio desplegado...")

    if not service_url:
        success, domain, _ = run_command("railway domain")
        if success and domain:
            service_url = f"https://{domain.strip()}"
        else:
            print("❌ No se pudo determinar la URL del servicio")
            return False

    # Test health endpoint
    success, _, _ = run_command(f"curl -f {service_url}/health")
    if success:
        print("✅ Health check exitoso")
        print(f"🌐 Servicio operativo en: {service_url}")
        return True
    else:
        print("❌ Health check falló")
        print("💡 Revisa los logs: railway logs")
        print("💡 Puede tomar unos minutos para que el servicio esté completamente listo")
        return False

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Setup Railway Docker ML Training Service")
    parser.add_argument("--skip-checks", action="store_true", help="Skip prerequisite checks")
    parser.add_argument("--only-build", action="store_true", help="Only build Docker image, don't deploy")
    parser.add_argument("--test-only", action="store_true", help="Only test existing deployment")

    args = parser.parse_args()

    print("🚀 Railway Docker ML Training Setup")
    print("=" * 50)

    if args.test_only:
        return test_deployment()

    if not args.skip_checks:
        if not check_prerequisites():
            print("\n❌ Prerrequisitos no cumplidos. Revisa los errores arriba.")
            sys.exit(1)

    if not setup_railway_project():
        print("\n❌ Error configurando proyecto Railway.")
        sys.exit(1)

    configure_environment_variables()

    if args.only_build:
        print("\n🏗️ Construyendo solo imagen Docker...")
        success, _, _ = run_command("docker build -f Dockerfile.railway -t railway-ml-training:test .")
        if success:
            print("✅ Imagen Docker construida exitosamente")
        else:
            print("❌ Error construyendo imagen Docker")
        return

    service_url = build_and_deploy()

    if service_url:
        print("\n" + "=" * 50)
        print("🎉 DEPLOYMENT COMPLETADO!")
        print(f"🌐 Servicio disponible en: {service_url}")
        print("\n📋 Próximos pasos:")
        print("1. Configura las API keys en Railway Dashboard")
        print("2. Espera 2-3 minutos para que el servicio esté listo")
        print("3. Prueba el servicio: /ml_train en Telegram")
        print("4. Configura RAILWAY_ML_URL en tu bot principal")

        # Test the deployment
        print("\n🧪 Probando deployment...")
        test_deployment(service_url)
    else:
        print("\n❌ Deployment falló. Revisa los logs y configuración.")

if __name__ == "__main__":
    main()
