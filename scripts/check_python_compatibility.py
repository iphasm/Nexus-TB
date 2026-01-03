#!/usr/bin/env python3
"""
VERIFICACIÓN DE COMPATIBILIDAD: Python para Nexus ML Trainer
===========================================================

Verifica si la versión de Python instalada es compatible
con el Nexus ML Trainer y qué features estarán disponibles.
"""

import sys

def check_python_compatibility():
    """Verifica compatibilidad de Python con Nexus ML Trainer."""

    print("🐍 VERIFICACIÓN DE COMPATIBILIDAD PYTHON")
    print("=" * 50)

    # Obtener versión de Python
    version = sys.version_info
    python_version = f"{version.major}.{version.minor}.{version.micro}"
    python_short = f"{version.major}.{version.minor}"

    print(f"Versión actual: Python {python_version}")
    print(f"Versión corta: {python_short}")
    print()

    # Definir compatibilidad
    compatibility_matrix = {
        "3.8": {"status": "✅ COMPATIBLE", "pandas_ta": True, "recommended": False},
        "3.9": {"status": "✅ COMPATIBLE", "pandas_ta": True, "recommended": False},
        "3.10": {"status": "✅ COMPATIBLE", "pandas_ta": True, "recommended": False},
        "3.11": {"status": "✅ COMPATIBLE", "pandas_ta": True, "recommended": False},
        "3.12": {"status": "✅ COMPATIBLE", "pandas_ta": True, "recommended": False},
        "3.13": {"status": "🏆 RECOMENDADO", "pandas_ta": True, "recommended": True},
        "3.14": {"status": "⚠️ LIMITADO", "pandas_ta": False, "recommended": False}
    }

    if python_short in compatibility_matrix:
        info = compatibility_matrix[python_short]

        print(f"Estado: {info['status']}")
        print(f"pandas-ta disponible: {'✅ SÍ' if info['pandas_ta'] else '❌ NO'}")
        print(f"Instalador recomendado: {'Normal' if info['pandas_ta'] else 'Python 3.14'}")
        print()

        if info['pandas_ta']:
            print("🎯 FEATURES DISPONIBLES:")
            print("   ✅ XGBoost - Entrenamiento ML completo")
            print("   ✅ Scikit-learn - Preprocesamiento")
            print("   ✅ pandas-ta - Indicadores técnicos avanzados")
            print("   ✅ YFinance - Descarga de datos de mercado")
            print("   ✅ Interfaz gráfica completa")
            print("   ✅ Backup automático")
            print()
            print("🚀 Comando recomendado:")
            print("   Install_ML_Trainer.bat")
        else:
            print("⚠️  FEATURES LIMITADAS:")
            print("   ✅ XGBoost - Entrenamiento ML completo")
            print("   ✅ Scikit-learn - Preprocesamiento")
            print("   ❌ pandas-ta - Indicadores técnicos avanzados")
            print("   ⚠️  Solo indicadores técnicos básicos")
            print("   ✅ YFinance - Descarga de datos de mercado")
            print("   ✅ Interfaz gráfica completa")
            print("   ✅ Backup automático")
            print()
            print("🚀 Comando recomendado:")
            print("   python scripts/setup_ml_trainer_py314.py")

        if info['recommended']:
            print("⭐ ESTA ES LA VERSIÓN RECOMENDADA PARA NEXUS ML TRAINER ⭐")

        print()
        print("=" * 50)
        return True

    else:
        print("❌ VERSIÓN NO SOPORTADA")
        print()
        print("Versiones soportadas:")
        for ver, info in compatibility_matrix.items():
            status = "⭐" if info['recommended'] else "✅" if info['pandas_ta'] else "⚠️"
            print(f"   {status} Python {ver} - {info['status']}")

        print()
        print("💡 Recomendación: Instalar Python 3.13")
        print("   Descargar desde: https://python.org")
        print()
        print("=" * 50)
        return False

def main():
    """Función principal."""
    try:
        compatible = check_python_compatibility()

        if compatible:
            print("✅ Python compatible - Puede proceder con la instalación")
            sys.exit(0)
        else:
            print("❌ Python no compatible - Actualice la versión")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
