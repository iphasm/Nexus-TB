#!/usr/bin/env python3
"""
Railway ML Training Deployment Script
Automated deployment of ML training service to Railway
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_railway_cli():
    """Check if Railway CLI is installed"""
    success, _, _ = run_command("railway --version")
    return success

def create_ml_service():
    """Create Railway ML training service"""
    print("🚀 Creando servicio de ML training en Railway...")

    # Initialize Railway project if not exists
    success, _, stderr = run_command("railway init --name nexus-ml-training --yes")
    if not success and "already linked" not in stderr:
        print(f"❌ Error inicializando Railway: {stderr}")
        return False

    # Link to existing project if needed
    success, _, _ = run_command("railway link --yes")
    if not success:
        print("⚠️ No se pudo linkear a proyecto existente, creando nuevo...")

    print("✅ Servicio Railway inicializado")
    return True

def deploy_ml_service():
    """Deploy ML training service to Railway"""
    print("📦 Desplegando servicio ML training...")

    # Set Railway configuration
    success, _, stderr = run_command("railway up --service railway-ml")
    if not success:
        print(f"❌ Error en deployment: {stderr}")
        return False

    print("✅ Servicio ML training desplegado")

    # Get service URL
    success, stdout, _ = run_command("railway domain")
    if success and stdout:
        service_url = f"https://{stdout.strip()}"
        print(f"🌐 URL del servicio: {service_url}")
        print("💡 Configura en tu bot: RAILWAY_ML_URL={service_url}")
        return service_url

    return True

def setup_environment_variables():
    """Setup required environment variables"""
    print("🔧 Configurando variables de entorno...")

    env_vars = {
        "BINANCE_API_KEY": "Tu API key de Binance",
        "BINANCE_API_SECRET": "Tu API secret de Binance",
        "ALPHA_VANTAGE_API_KEY": "Tu API key de Alpha Vantage (opcional)",
        "PYTHONUNBUFFERED": "1",
        "LOG_LEVEL": "INFO"
    }

    for key, description in env_vars.items():
        if not os.getenv(key):
            print(f"⚠️ Variable de entorno faltante: {key}")
            print(f"   Descripción: {description}")
            print(f"   Comando: railway variables set {key}=TU_VALOR")
        else:
            success, _, _ = run_command(f"railway variables set {key}={os.getenv(key)}")
            if success:
                print(f"✅ {key} configurado")
            else:
                print(f"❌ Error configurando {key}")

def create_deployment_files():
    """Create necessary deployment files"""
    print("📄 Creando archivos de despliegue...")

    # Create railway-ml.json
    railway_config = {
        "$schema": "https://railway.app/railway.schema.json",
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python railway_ml_train.py",
            "healthcheckPath": "/health",
            "healthcheckTimeout": 300,
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 3
        },
        "environments": [
            {
                "name": "ml-training",
                "envVars": [
                    {
                        "name": "PYTHONUNBUFFERED",
                        "value": "1"
                    },
                    {
                        "name": "LOG_LEVEL",
                        "value": "INFO"
                    },
                    {
                        "name": "TRAINING_ENV",
                        "value": "railway"
                    }
                ]
            }
        ]
    }

    with open('railway-ml.json', 'w') as f:
        json.dump(railway_config, f, indent=2)

    print("✅ Archivo railway-ml.json creado")

    # Create requirements-railway.txt if not exists
    if not os.path.exists('requirements-railway.txt'):
        requirements = """# Railway ML Training Requirements
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
xgboost==1.7.6
joblib==1.3.2
pandas-ta==0.3.14b
yfinance==0.2.18
python-binance==1.0.19
requests==2.31.0
flask==2.3.3
werkzeug==2.3.7
tqdm==4.65.0
python-dotenv==1.0.0"""

        with open('requirements-railway.txt', 'w') as f:
            f.write(requirements)

        print("✅ Archivo requirements-railway.txt creado")

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy ML training service to Railway")
    parser.add_argument("--skip-checks", action="store_true", help="Skip environment checks")
    parser.add_argument("--only-files", action="store_true", help="Only create deployment files")

    args = parser.parse_args()

    print("🚀 Railway ML Training Deployment Script")
    print("=" * 50)

    if not args.skip_checks:
        # Check Railway CLI
        if not check_railway_cli():
            print("❌ Railway CLI no está instalado.")
            print("Instálalo desde: https://docs.railway.app/develop/cli")
            sys.exit(1)

        # Check required files
        required_files = ['railway_ml_train.py', 'requirements-railway.txt']
        for file in required_files:
            if not os.path.exists(file):
                print(f"❌ Archivo faltante: {file}")
                sys.exit(1)

    # Create deployment files
    create_deployment_files()

    if args.only_files:
        print("✅ Archivos de despliegue creados. Deployment manual requerido.")
        return

    # Deploy to Railway
    if create_ml_service():
        setup_environment_variables()
        service_url = deploy_ml_service()

        if service_url:
            print("\n" + "=" * 50)
            print("🎉 DEPLOYMENT COMPLETADO!")
            print(f"🌐 Servicio disponible en: {service_url}")
            print("\n📋 Próximos pasos:")
            print("1. Configura RAILWAY_ML_URL en tu bot principal")
            print("2. Prueba con /ml_train en Telegram")
            print("3. Monitorea con /ml_status")
        else:
            print("❌ Deployment falló. Revisa los logs de Railway.")
    else:
        print("❌ Error creando servicio Railway.")

if __name__ == "__main__":
    main()
