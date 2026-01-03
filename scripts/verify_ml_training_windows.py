#!/usr/bin/env python3
"""
VERIFICACIÓN: Integridad del Entrenador ML para Windows
=======================================================

Verifica que el sistema de entrenamiento ML funcione correctamente en Windows:
- Paths compatibles con Windows
- Imports sin problemas
- Dependencias disponibles
- Configuración correcta
- Ejecución de prueba
"""

import os
import sys
import subprocess
import platform
from datetime import datetime

def verify_windows_compatibility():
    """Verifica compatibilidad con Windows."""

    print("🔍 VERIFICACIÓN: Integridad Entrenador ML para Windows")
    print("=" * 70)
    print(f"🖥️  Sistema operativo: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version}")
    print(f"📂 Directorio actual: {os.getcwd()}")
    print()

    issues = []
    warnings = []

    # 1. Verificar estructura de directorios
    print("1️⃣ VERIFICACIÓN DE ESTRUCTURA DE DIRECTORIOS")
    print("-" * 50)

    required_dirs = [
        "src/ml",
        "nexus_system/memory_archives",
        "nexus_system/cortex",
        "scripts"
    ]

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            issues.append(f"Directorio faltante: {dir_path}")
            print(f"❌ {dir_path}")

    # 2. Verificar archivos críticos
    print("\n2️⃣ VERIFICACIÓN DE ARCHIVOS CRÍTICOS")
    print("-" * 50)

    critical_files = [
        "src/ml/train_cortex.py",
        "src/ml/add_new_features.py",
        "nexus_system/cortex/ml_classifier.py",
        "scripts/retrain_ml_model.py",
        "system_directive.py"
    ]

    for file_path in critical_files:
        if os.path.exists(file_path):
            # Verificar que sea legible
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"✅ {file_path} ({len(content)} chars)")
            except Exception as e:
                issues.append(f"Archivo corrupto: {file_path} - {e}")
                print(f"❌ {file_path} - Error: {e}")
        else:
            issues.append(f"Archivo faltante: {file_path}")
            print(f"❌ {file_path}")

    # 3. Verificar imports críticos
    print("\n3️⃣ VERIFICACIÓN DE IMPORTS CRÍTICOS")
    print("-" * 50)

    imports_to_test = [
        ("system_directive", "get_all_assets, ASSET_GROUPS, GROUP_CONFIG"),
        ("xgboost", "XGBClassifier"),
        ("sklearn.preprocessing", "RobustScaler, LabelEncoder"),
        ("sklearn.model_selection", "TimeSeriesSplit, cross_val_score"),
        ("pandas", "DataFrame"),
        ("joblib", "dump, load"),
        ("yfinance", "Ticker"),
        ("pandas_ta", "Strategy")
    ]

    for module, items in imports_to_test:
        try:
            if items:
                # Import específico
                exec(f"from {module} import {items}")
            else:
                # Import general
                exec(f"import {module}")
            print(f"✅ {module}")
        except ImportError as e:
            issues.append(f"Import faltante: {module} - {e}")
            print(f"❌ {module} - {e}")
        except Exception as e:
            warnings.append(f"Import con problemas: {module} - {e}")
            print(f"⚠️  {module} - {e}")

    # 4. Verificar configuración de activos
    print("\n4️⃣ VERIFICACIÓN DE CONFIGURACIÓN DE ACTIVOS")
    print("-" * 50)

    try:
        sys.path.insert(0, os.getcwd())
        from system_directive import ASSET_GROUPS, GROUP_CONFIG

        # Calcular activos habilitados
        enabled_assets = []
        for group_name, assets in ASSET_GROUPS.items():
            if GROUP_CONFIG.get(group_name, True):
                enabled_assets.extend(assets)
        enabled_assets = list(set(enabled_assets))

        print(f"✅ Grupos configurados: {len(ASSET_GROUPS)}")
        print(f"✅ Activos habilitados: {len(enabled_assets)}")

        # Verificar que tenemos suficientes activos
        if len(enabled_assets) < 5:
            issues.append(f"Pocos activos habilitados: {len(enabled_assets)}")
        elif len(enabled_assets) > 100:
            warnings.append(f"Muchos activos habilitados: {len(enabled_assets)} - puede ser lento")

        # Mostrar algunos activos de ejemplo
        sample_assets = enabled_assets[:5]
        print(f"📊 Ejemplos: {', '.join(sample_assets)}")

    except Exception as e:
        issues.append(f"Error en configuración de activos: {e}")
        print(f"❌ Error cargando configuración: {e}")

    # 5. Verificar paths de Windows
    print("\n5️⃣ VERIFICACIÓN DE PATHS PARA WINDOWS")
    print("-" * 50)

    test_paths = [
        "nexus_system/memory_archives/ml_model.pkl",
        "nexus_system/memory_archives/scaler.pkl",
        "src/ml/train_cortex.py"
    ]

    for path in test_paths:
        abs_path = os.path.abspath(path)
        dir_path = os.path.dirname(abs_path)

        # Verificar que el directorio existe o se puede crear
        if os.path.exists(dir_path):
            print(f"✅ {path}")
        else:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ {path} (directorio creado)")
            except Exception as e:
                issues.append(f"No se puede crear directorio: {dir_path} - {e}")
                print(f"❌ {path} - {e}")

    # 6. Verificar ejecución básica del script
    print("\n6️⃣ VERIFICACIÓN DE EJECUCIÓN BÁSICA")
    print("-" * 50)

    try:
        # Probar import del script de entrenamiento
        sys.path.insert(0, 'src')
        import ml.train_cortex as tc

        # Verificar que las constantes principales existan
        required_attrs = ['SYMBOLS', 'INTERVAL', 'MODEL_OUTPUT', 'SCALER_OUTPUT']
        for attr in required_attrs:
            if hasattr(tc, attr):
                value = getattr(tc, attr)
                if attr in ['MODEL_OUTPUT', 'SCALER_OUTPUT']:
                    # Verificar que sea una ruta absoluta o correcta
                    if os.path.isabs(value) or (os.path.dirname(value) and os.path.exists(os.path.dirname(value))):
                        print(f"✅ {attr}: {value}")
                    else:
                        warnings.append(f"Path potencialmente problemático: {attr} = {value}")
                        print(f"⚠️  {attr}: {value}")
                else:
                    print(f"✅ {attr}: {value}")
            else:
                issues.append(f"Atributo faltante en train_cortex: {attr}")
                print(f"❌ {attr} faltante")

        # Verificar que SYMBOLS tenga activos
        if hasattr(tc, 'SYMBOLS') and tc.SYMBOLS:
            print(f"✅ SYMBOLS contiene {len(tc.SYMBOLS)} activos")
        else:
            issues.append("SYMBOLS vacío o no definido")
            print("❌ SYMBOLS vacío")

    except Exception as e:
        issues.append(f"Error importando/cargando train_cortex: {e}")
        print(f"❌ Error en train_cortex: {e}")

    # 7. Verificar compatibilidad de comandos del sistema
    print("\n7️⃣ VERIFICACIÓN DE COMPATIBILIDAD DE SISTEMA")
    print("-" * 50)

    # Verificar que sys.executable existe
    if os.path.exists(sys.executable):
        print(f"✅ Python executable: {sys.executable}")
    else:
        issues.append(f"Python executable no encontrado: {sys.executable}")
        print(f"❌ Python executable faltante")

    # Verificar que podemos ejecutar subprocess
    try:
        result = subprocess.run([sys.executable, '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Subprocess funciona: {result.stdout.strip()}")
        else:
            issues.append("Subprocess no funciona correctamente")
            print("❌ Subprocess con problemas")
    except Exception as e:
        issues.append(f"Error en subprocess: {e}")
        print(f"❌ Error en subprocess: {e}")

    # 8. Resumen final
    print("\n" + "=" * 70)
    print("🎯 RESULTADO DE VERIFICACIÓN PARA WINDOWS")

    if not issues:
        print("✅ SISTEMA COMPLETAMENTE COMPATIBLE CON WINDOWS")
        print("🚀 El entrenador ML está listo para ejecutarse")
        success = True
    else:
        print("❌ PROBLEMAS CRÍTICOS ENCONTRADOS:")
        for issue in issues:
            print(f"   ❌ {issue}")
        success = False

    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for warning in warnings:
            print(f"   ⚠️  {warning}")

    # Recomendaciones
    print("\n📋 RECOMENDACIONES:")
    if success:
        print("✅ Ejecutar: python scripts/retrain_ml_model.py")
        print("✅ Monitorear logs durante el entrenamiento")
        print("✅ Verificar archivos generados en nexus_system/memory_archives/")
    else:
        print("❌ Corregir los problemas listados arriba antes de entrenar")
        print("🔧 Verificar instalación de dependencias: pip install -r requirements.txt")

    return success

if __name__ == "__main__":
    success = verify_windows_compatibility()

    print(f"\n{'='*70}")
    print(f"🕒 Verificación completada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if success:
        print("✅ VERIFICACIÓN EXITOSA - Windows compatible")
        sys.exit(0)
    else:
        print("❌ VERIFICACIÓN FALLIDA - Corregir problemas")
        sys.exit(1)
