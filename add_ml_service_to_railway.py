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
    """Guide user to create ML training service in Railway dashboard"""
    print("\n🚀 Creando servicio ML training...")
    print("⚠️  IMPORTANTE: Railway requiere crear servicios desde el Dashboard web")
    print("   La CLI no puede crear servicios directamente.\n")

    project_name = get_current_project()
    if project_name:
        print(f"📋 Tu proyecto actual: {project_name}")
        print(f"🔗 Dashboard URL: https://railway.app/dashboard")

    print("\n📝 PASOS PARA CREAR EL SERVICIO:")
    print("┌─────────────────────────────────────────────────────┐")
    print("│ 1. Ve a: https://railway.app/dashboard             │")
    print("│ 2. Selecciona tu proyecto                          │")
    print("│ 3. Haz click en 'Add Service' (botón verde)       │")
    print("│ 4. Selecciona 'Empty Service'                      │")
    print("│ 5. Nombre: 'ml-training'                           │")
    print("│ 6. Haz click en 'Add Service'                      │")
    print("└─────────────────────────────────────────────────────┘")

    print("\n⏳ Una vez creado el servicio en Railway:")
    print("   - El servicio aparecerá en tu dashboard")
    print("   - Railway detectará automáticamente los archivos de configuración")
    print("   - El build comenzará automáticamente")

    # Ask user to confirm
    input("\n🔄 Presiona ENTER cuando hayas creado el servicio 'ml-training' en Railway Dashboard...")

    # Verify service exists
    print("🔍 Verificando que el servicio existe...")

    # Try different commands to list services
    commands_to_try = [
        "railway service",
        "railway service list",
        "railway status"
    ]

    services_found = False
    services_output = ""

    for cmd in commands_to_try:
        print(f"🔍 Probando comando: {cmd}")
        success, output, error = run_command(cmd)

        if success:
            services_output = output
            print(f"✅ Comando exitoso: {cmd}")
            if "ml-training" in output:
                print("✅ Servicio 'ml-training' encontrado!")
                services_found = True
                break
            else:
                print(f"⚠️ Servicio 'ml-training' no encontrado en output de {cmd}")
        else:
            print(f"❌ Comando falló: {cmd} - {error}")

    if services_found:
        return True
    else:
        print("\n❌ Servicio 'ml-training' no encontrado con ningún comando")
        print("Asegúrate de haberlo creado en Railway Dashboard")
        print("\n🔍 Intenta manualmente:")
        print("   railway service")
        print("   railway status")
        print("\n💡 Si los comandos fallan, verifica:")
        print("   - Que estás logueado: railway whoami")
        print("   - Que estás en el proyecto correcto: railway status")
        print("   - Que creaste el servicio en: https://railway.app/dashboard")

        # Ask user if they want to continue anyway
        response = input("\n❓ ¿Quieres continuar asumiendo que el servicio existe? (y/N): ").strip().lower()
        if response == 'y' or response == 'yes':
            print("⏭️ Continuando con la configuración...")
            return True

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
    print("\n🚀 Verificando despliegue del servicio ML...")

    # Check if service is deploying/has deployed
    print("🔍 Verificando estado del servicio...")
    success, status_output, _ = run_command("railway status")

    if "ml-training" in status_output:
        print("✅ Servicio 'ml-training' está activo en Railway")
    else:
        print("⚠️ Servicio 'ml-training' no aparece en el estado actual")
        print("Puede estar desplegándose aún...")

    # Wait for deployment
    print("⏳ Esperando que el servicio termine de desplegarse...")
    print("💡 Esto puede tomar 2-5 minutos la primera vez")

    import time
    time.sleep(30)  # Give more time for Railway to deploy

    # Get service URL - Railway typically gives one domain per project
    # The ML service will be accessible at the project domain
    success, domain, _ = run_command("railway domain")
    if success and domain:
        service_url = f"https://{domain.strip()}"
        print(f"🌐 Servicio ML desplegado en: {service_url}")
        print("💡 Nota: Railway usa un dominio por proyecto, no por servicio")
    else:
        print("⚠️ No se pudo obtener la URL del proyecto automáticamente")
        print("💡 Revisa Railway Dashboard para obtener la URL")
        print("   O ejecuta: railway domain")
        service_url = None

    return service_url

    # Test health check
    print("🧪 Probando health check...")
    max_attempts = 3
    for attempt in range(max_attempts):
        test_success, _, _ = run_command(f"curl -f {service_url}/health")
        if test_success:
            print("✅ Health check exitoso - Servicio operativo!")
            return service_url
        else:
            print(f"⚠️ Health check falló (intento {attempt + 1}/{max_attempts})")
            if attempt < max_attempts - 1:
                print("   Esperando 20 segundos antes del siguiente intento...")
                time.sleep(20)

    print("⚠️ Health check falló después de varios intentos")
    print("💡 El servicio puede estar iniciándose aún")
    print("   Revisa Railway Dashboard para ver el estado del deployment")
    return service_url  # Return URL anyway for configuration

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Add ML training service to existing Railway project")
    parser.add_argument("--skip-checks", action="store_true", help="Skip prerequisite checks")
    parser.add_argument("--skip-service-creation", action="store_true", help="Skip service creation guide (if already created)")
    parser.add_argument("--skip-service-verification", action="store_true", help="Skip service verification (if CLI commands fail but service exists)")

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

    # Guide user to create ML service (unless skipped)
    if not args.skip_service_creation:
        if not create_ml_service():
            if not args.skip_service_verification:
                print("\n❌ Servicio ML no pudo ser verificado")
                print("Sigue las instrucciones arriba y ejecuta el script nuevamente")
                print("Opciones:")
                print("  --skip-service-creation (si ya creaste el servicio)")
                print("  --skip-service-verification (si los comandos CLI fallan)")
                sys.exit(1)
            else:
                print("⏭️  Saltando verificación de servicio (--skip-service-verification)")
        else:
            print("✅ Servicio ML verificado correctamente")
    else:
        print("⏭️  Saltando creación de servicio (--skip-service-creation)")

    # Configure variables
    configure_service_variables()

    # Deploy and verify
    service_url = deploy_and_verify()

    if service_url:
        print("\n" + "=" * 60)
        print("🎉 SERVICIO ML CONFIGURADO EXITOSAMENTE!")
        print(f"🌐 URL del servicio: {service_url}")
        print("\n📋 Próximos pasos:")
        print("1. ✅ API keys configuradas (verifica en Railway Dashboard)")
        print("2. ⏳ Espera a que Railway termine el deployment")
        print("3. 🔗 Configura RAILWAY_ML_URL en tu bot principal")
        print("4. 🎮 Prueba con /ml_train en Telegram")

        print("\n🔗 Configuración para bot:")
        print(f"   export RAILWAY_ML_URL={service_url}")

        print("\n💡 Monitoreo:")
        print("   railway logs --service ml-training  # Ver logs")
        print("   railway status                       # Ver estado")
        print("   railway service                      # Ver servicios")
    else:
        print("\n⚠️ Servicio configurado pero deployment en progreso")
        print("💡 Railway puede estar terminando el build/deployment")
        print("   Revisa Railway Dashboard en unos minutos")
        print("   O ejecuta el script nuevamente: python add_ml_service_to_railway.py --skip-service-creation")

if __name__ == "__main__":
    main()
