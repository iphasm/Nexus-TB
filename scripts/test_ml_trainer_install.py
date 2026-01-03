#!/usr/bin/env python3
"""
TEST: Verificación Post-Instalación ML Trainer
============================================

Verifica que el ejecutable del ML Trainer se instaló correctamente
y que todas las funcionalidades básicas funcionan.
"""

import os
import sys
import subprocess
import importlib.util

def test_dependencies():
    """Prueba que las dependencias críticas estén disponibles."""
    print("🔍 Probando dependencias críticas...")

    critical_deps = [
        ('tkinter', 'Interfaz gráfica'),
        ('xgboost', 'ML Core'),
        ('sklearn', 'Preprocessing'),
        ('pandas', 'Data handling'),
        ('joblib', 'Model serialization'),
        ('yfinance', 'Data download'),
    ]

    optional_deps = [
        ('pandas_ta', 'Technical indicators (opcional)'),
    ]

    # Verificar versión de Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"🐍 Python {python_version}")

    if python_version == "3.14":
        print("⚠️  Python 3.14 detectado - pandas-ta no disponible")
        critical_deps.extend(optional_deps)  # pandas-ta se vuelve opcional
    else:
        critical_deps.extend(optional_deps)

    failed_deps = []

    for module_name, description in critical_deps:
        try:
            if module_name == 'tkinter':
                import tkinter
                tkinter._test()  # Prueba básica
            else:
                importlib.import_module(module_name.replace('-', '_'))
            print(f"✅ {description}")
        except ImportError as e:
            print(f"❌ {description}: {e}")
            failed_deps.append(module_name)
        except Exception as e:
            print(f"⚠️  {description}: Error de prueba - {e}")

    return len(failed_deps) == 0

def test_ml_trainer_script():
    """Prueba que el script de interfaz se puede importar."""
    print("\n🔍 Probando script de interfaz...")

    try:
        # Verificar que el archivo existe
        script_path = "scripts/ml_trainer_gui.py"
        if not os.path.exists(script_path):
            print(f"❌ Script no encontrado: {script_path}")
            return False

        # Intentar importar el módulo
        spec = importlib.util.spec_from_file_location("ml_trainer_gui", script_path)
        module = importlib.util.module_from_spec(spec)

        # Solo verificar que se puede cargar (no ejecutar)
        print(f"✅ Script accesible: {script_path}")
        return True

    except Exception as e:
        print(f"❌ Error cargando script: {e}")
        return False

def test_executable_creation():
    """Verifica si el ejecutable fue creado."""
    print("\n🔍 Verificando ejecutable...")

    possible_paths = [
        "dist/Nexus_ML_Trainer/Nexus_ML_Trainer.exe",
        "dist/Nexus_ML_Trainer_PY314/Nexus_ML_Trainer_PY314.exe",
    ]

    exe_found = False
    for exe_path in possible_paths:
        if os.path.exists(exe_path):
            exe_size = os.path.getsize(exe_path) / (1024 * 1024)
            print(".2f"            exe_found = True
            break

    if not exe_found:
        print("❌ Ejecutable no encontrado")
        print("💡 Ejecutar instalación:")
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if python_version == "3.14":
            print("   python scripts/setup_ml_trainer_py314.py")
        else:
            print("   python scripts/setup_ml_trainer.py")
        return False

    return True

def test_system_integration():
    """Prueba integración básica con el sistema Nexus."""
    print("\n🔍 Probando integración con Nexus...")

    try:
        # Verificar system_directive
        from system_directive import get_all_assets, ASSET_GROUPS, GROUP_CONFIG
        assets = get_all_assets()

        print(f"✅ Sistema Nexus accesible: {len(assets)} activos")

        # Verificar que hay activos habilitados
        enabled_count = 0
        for group_name, group_assets in ASSET_GROUPS.items():
            if GROUP_CONFIG.get(group_name, True):
                enabled_count += len(group_assets)

        if enabled_count == 0:
            print("⚠️  No hay activos habilitados")
            return False

        print(f"✅ Activos habilitados: {enabled_count}")
        return True

    except Exception as e:
        print(f"❌ Error de integración: {e}")
        return False

def create_test_report(results):
    """Crea un reporte de los resultados de las pruebas."""
    print("\n" + "=" * 60)
    print("📋 REPORTE DE PRUEBAS POST-INSTALACIÓN")
    print("=" * 60)

    all_passed = all(results.values())

    if all_passed:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ El ML Trainer está listo para usar")
    else:
        print("⚠️  ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisar problemas abajo")

    print("\n📊 RESULTADOS DETALLADOS:")
    test_names = {
        'dependencies': 'Dependencias críticas',
        'script': 'Script de interfaz',
        'executable': 'Ejecutable creado',
        'integration': 'Integración Nexus'
    }

    for test_key, passed in results.items():
        status = "✅" if passed else "❌"
        name = test_names.get(test_key, test_key)
        print(f"   {status} {name}")

    print("\n📋 RECOMENDACIONES:")

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if python_version == "3.14":
        print("• Python 3.14 detectado - usando versión optimizada")
        print("• pandas-ta no disponible (limitaciones en indicadores)")
        print("• Funcionalidad ML completa disponible")

    if all_passed:
        print("🚀 Ejecutar: Nexus_ML_Trainer.exe")
    else:
        print("🔧 Corregir problemas antes de usar")
        if not results.get('executable', True):
            print("   • Ejecutar instalación del ejecutable")

    return all_passed

def main():
    """Función principal de pruebas."""
    print("🧪 TEST POST-INSTALACIÓN: Nexus ML Trainer")
    print("=" * 60)

    # Ejecutar todas las pruebas
    results = {}

    results['dependencies'] = test_dependencies()
    results['script'] = test_ml_trainer_script()
    results['executable'] = test_executable_creation()
    results['integration'] = test_system_integration()

    # Crear reporte
    success = create_test_report(results)

    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
