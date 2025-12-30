#!/usr/bin/env python3
"""
Script rápido para verificar que todas las dependencias ML estén instaladas
"""
import sys
import importlib

def check_module(module_name, description=""):
    """Verifica si un módulo se puede importar"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description or module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description or module_name}: {e}")
        return False

def main():
    print("=" * 50)
    print("🔍 VERIFICACIÓN DE DEPENDENCIAS ML")
    print("=" * 50)
    print(f"🐍 Python: {sys.version.split()[0]}")
    print()

    # Lista de dependencias críticas para ML (ordenadas por importancia)
    critical_deps = [
        ("pandas", "pandas - Manipulación de datos"),
        ("numpy", "numpy - Computación numérica"),
        ("sklearn", "scikit-learn - Machine Learning"),
        ("xgboost", "xgboost - Modelo XGBoost"),
        ("joblib", "joblib - Serialización de modelos"),
    ]

    optional_deps = [
        ("tqdm", "tqdm - Barras de progreso"),
        ("yfinance", "yfinance - Datos de Yahoo Finance"),
        ("pandas_ta", "pandas-ta - Indicadores técnicos"),
        ("binance.client", "python-binance - API de Binance"),
    ]

    dependencies = critical_deps + optional_deps

    print("📦 Verificando dependencias críticas...\n")

    critical_good = True
    for module, description in critical_deps:
        success = check_module(module, description)
        critical_good = critical_good and success

    print("\n📦 Verificando dependencias opcionales...\n")

    optional_good = True
    for module, description in optional_deps:
        success = check_module(module, description)
        optional_good = optional_good and success

    print()
    if critical_good:
        print("🎉 ¡Dependencias críticas instaladas correctamente!")
        if optional_good:
            print("✅ Todas las dependencias (incluyendo opcionales) están OK")
            print("✅ El sistema está completamente listo para entrenamiento ML")
        else:
            print("⚠️  Algunas dependencias opcionales faltan, pero puedes continuar")
            print("✅ El sistema básico está listo para entrenamiento ML")
    else:
        print("❌ Faltan dependencias críticas")
        print("💡 Ejecuta: install_dependencies.bat o install_py314.bat")

    print()
    print("=" * 50)

if __name__ == "__main__":
    main()
