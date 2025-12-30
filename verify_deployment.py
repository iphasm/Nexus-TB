#!/usr/bin/env python3
"""
Script de verificación para Railway deployment
Verifica que todos los componentes estén funcionando correctamente
"""
import sys
import os
from pathlib import Path

def log(message, status="INFO"):
    """Logging simple"""
    print(f"[{status}] {message}")

def check_file_exists(filepath, description):
    """Verifica que un archivo existe"""
    if os.path.exists(filepath):
        log(f"✅ {description}: {filepath}")
        return True
    else:
        log(f"❌ {description}: {filepath} NO ENCONTRADO", "ERROR")
        return False

def check_import(module_name, description):
    """Verifica que un módulo se puede importar"""
    try:
        __import__(module_name)
        log(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        log(f"❌ {description}: {module_name} - {e}", "ERROR")
        return False

def check_ml_models():
    """Verifica que los modelos ML estén disponibles"""
    models_ok = True

    # Verificar modelos en ambas ubicaciones para compatibilidad
    model_paths = [
        "models/ml_model.pkl",
        "models/scaler.pkl",
        "nexus_system/memory_archives/ml_model.pkl",
        "nexus_system/memory_archives/scaler.pkl"
    ]

    for path in model_paths:
        if not check_file_exists(path, f"Modelo ML"):
            models_ok = False

    return models_ok

def check_src_modules():
    """Verifica que los módulos en src/ se pueden importar"""
    src_ok = True

    modules_to_check = [
        ("src.ml.train_cortex", "Módulo ML principal"),
        ("src.ml.add_new_features", "Módulo de features"),
        ("src.ml.analyze_features", "Módulo de análisis"),
        ("compatibility_imports", "Compatibilidad backward")
    ]

    for module, description in modules_to_check:
        if not check_import(module, description):
            src_ok = False

    return src_ok

def check_critical_imports():
    """Verifica imports críticos del sistema"""
    critical_ok = True

    critical_modules = [
        ("nexus_loader", "Loader principal"),
        ("servos.indicators", "Indicadores técnicos"),
        ("nexus_system.cortex.ml_classifier", "Clasificador ML"),
        ("handlers.trading", "Handler de trading"),
        ("pandas_ta", "pandas-ta (técnico)")
    ]

    for module, description in critical_modules:
        if not check_import(module, description):
            critical_ok = False

    return critical_ok

def main():
    """Función principal de verificación"""
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE DEPLOYMENT - NEXUS-TB")
    print("=" * 60)

    all_ok = True

    # Verificar archivos críticos
    print("\n📁 VERIFICANDO ARCHIVOS CRÍTICOS:")
    critical_files = [
        ("nexus_loader.py", "Script principal"),
        ("requirements.txt", "Dependencias"),
        ("Dockerfile", "Configuración Docker"),
        ("Procfile", "Configuración Railway"),
        ("railway.json", "Configuración Railway"),
        ("compatibility_imports.py", "Compatibilidad")
    ]

    for filepath, description in critical_files:
        if not check_file_exists(filepath, description):
            all_ok = False

    # Verificar modelos ML
    print("\n🤖 VERIFICANDO MODELOS ML:")
    if not check_ml_models():
        all_ok = False

    # Verificar módulos src/
    print("\n📦 VERIFICANDO MÓDULOS SRC/:")
    if not check_src_modules():
        all_ok = False

    # Verificar imports críticos
    print("\n🔧 VERIFICANDO IMPORTS CRÍTICOS:")
    if not check_critical_imports():
        all_ok = False

    # Verificar estructura de directorios
    print("\n📂 VERIFICANDO ESTRUCTURA:")
    directories = [
        ("src/ml", "Módulos ML"),
        ("models", "Modelos entrenados"),
        ("scripts/setup", "Scripts de instalación"),
        ("scripts/testing", "Scripts de testing"),
        ("docs/analysis", "Documentación")
    ]

    for dirname, description in directories:
        if os.path.exists(dirname):
            log(f"✅ {description}: {dirname}")
        else:
            log(f"❌ {description}: {dirname} NO ENCONTRADO", "ERROR")
            all_ok = False

    # Resultado final
    print("\n" + "=" * 60)
    if all_ok:
        print("🎉 DEPLOYMENT VERIFICATION: SUCCESS")
        print("✅ Todos los componentes verificados correctamente")
        print("🚀 Railway deployment listo para producción")
        return 0
    else:
        print("❌ DEPLOYMENT VERIFICATION: FAILED")
        print("⚠️  Revisar errores arriba antes del deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())
