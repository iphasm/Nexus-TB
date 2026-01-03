#!/usr/bin/env python3
"""
INSTALADOR ESPECÍFICO PARA PYTHON 3.14
=====================================

Instalador optimizado para Python 3.14 que evita dependencias
problemáticas como pandas-ta (que requiere numba).
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

def check_python_314():
    """Verifica que estamos usando Python 3.14."""
    version = sys.version_info
    if not (version.major == 3 and version.minor == 14):
        print(f"⚠️  Este script es específico para Python 3.14")
        print(f"   Versión actual: {version.major}.{version.minor}.{version.micro}")
        print(f"   Continuando de todos modos...")
        return False
    return True

def install_dependencies_py314():
    """Instala dependencias compatibles con Python 3.14."""
    print("📦 Instalando dependencias compatibles con Python 3.14...")

    # Dependencias críticas compatibles con Python 3.14
    dependencies = [
        # Core ML libraries
        'xgboost>=2.0.0',
        'scikit-learn>=1.4.0',
        'pandas>=2.1.0',
        'numpy>=1.24.0',
        'joblib>=1.3.0',

        # Web/data libraries
        'requests>=2.31.0',
        'yfinance>=0.2.40',

        # PyInstaller
        'pyinstaller>=6.0.0',

            # PyInstaller
        'pyinstaller>=6.0.0',

        # pandas-ta parchado compatible con Python 3.14
        'pandas-ta-openbb>=0.4.22'  # Desde carpeta local del proyecto
    ]

    print("🔧 Instalando dependencias una por una (más seguro)...")

    failed_deps = []
    for dep in dependencies:
        print(f"📦 Instalando {dep}...")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', dep, '--quiet'
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✅ {dep} instalado correctamente")
            else:
                print(f"❌ Error instalando {dep}")
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
                failed_deps.append(dep)

        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout instalando {dep}")
            failed_deps.append(dep)
        except Exception as e:
            print(f"💥 Error inesperado instalando {dep}: {e}")
            failed_deps.append(dep)

    if failed_deps:
        print(f"\n❌ DEPENDENCIAS FALLIDAS: {', '.join(failed_deps)}")
        print("💡 Intente instalar manualmente:")
        for dep in failed_deps:
            print(f"   pip install {dep}")
        return False

    # Instalar pandas-ta parchado compatible con Python 3.14
    print("\n🔧 Instalando pandas-ta parchado (compatible con Python 3.14)...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'pandas-ta-openbb>=0.4.22', '--quiet'
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("✅ pandas-ta-openbb instalado correctamente desde PyPI")
            print("   📦 Versión: 0.4.22 (compatible con Python 3.14)")
            print("   🎯 API: Compatible con pandas-ta original")
        else:
            print("❌ Error instalando pandas-ta-openbb")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return False
    except Exception as e:
        print(f"💥 Error instalando pandas-ta-openbb: {e}")
        return False

    print("✅ Todas las dependencias críticas instaladas")
    return True

def create_simplified_spec():
    """Crea especificaciones simplificadas con pandas-ta-openbb (PyPI)."""
    print("📝 Creando especificaciones simplificadas para Python 3.14...")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

a = Analysis(
    ['scripts/ml_trainer_gui.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'system_directive.py'), '.'),
        (os.path.join(project_root, 'nexus_system'), 'nexus_system'),
        (os.path.join(project_root, 'src'), 'src'),
        (os.path.join(project_root, 'servos'), 'servos'),
    ],
    hiddenimports=[
        'tkinter', 'tkinter.ttk', 'tkinter.scrolledtext',
        'tkinter.messagebox', 'tkinter.filedialog',
        'system_directive', 'servos.voight_kampff',
        'nexus_system.cortex.ml_classifier',
        'pandas.plotting._matplotlib', 'pandas.plotting._core',
        'sklearn.utils._weight_vector', 'sklearn.utils._cython_blas',
        'xgboost.core', 'xgboost.sklearn',
        'joblib.numpy_pickle_utils', 'joblib.compression',
        'yfinance.utils', 'yfinance.ticker',
        # pandas-ta-openbb compatible con Python 3.14 (instalado desde PyPI)
        'pandas_ta', 'pandas_ta.momentum', 'pandas_ta.trend', 'pandas_ta.volatility',
        'pandas_ta.overlap', 'pandas_ta.volume', 'pandas_ta.statistics',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test', 'test', 'unittest', 'pdb', 'pydoc',
        'doctest', 'sqlite3', 'dbm', 'gdbm', 'readline', 'rlcompleter',
        # Excluir dependencias problemáticas (pandas-ta-openbb ya incluido)
        'numba', 'llvmlite',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Nexus_ML_Trainer_PY314',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nexus_ML_Trainer_PY314'
)
'''

    spec_file = "ml_trainer_py314.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"✅ Especificaciones creadas: {spec_file}")
    return spec_file

def build_executable_py314(spec_file):
    """Construye ejecutable optimizado para Python 3.14."""
    print("🏗️ Construyendo ejecutable para Python 3.14...")

    # Configurar variables de entorno para mejor compatibilidad
    env = os.environ.copy()
    env['PYTHONOPTIMIZE'] = '1'  # Optimización de Python

    cmd = [
        sys.executable, '-m', 'pyinstaller',
        '--clean',
        '--noconfirm',
        '--onedir',
        spec_file
    ]

    print(f"🔧 Comando: {' '.join(cmd)}")

    try:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            bufsize=1, universal_newlines=True,
                            env=env) as process:

            for line in process.stdout:
                print(line, end='', flush=True)

        if process.returncode == 0:
            print("\n✅ Ejecutable construido exitosamente para Python 3.14!")

            # Verificar archivos generados
            exe_dir = "dist/Nexus_ML_Trainer_PY314"
            exe_file = os.path.join(exe_dir, "Nexus_ML_Trainer_PY314.exe")

            if os.path.exists(exe_file):
                exe_size = os.path.getsize(exe_file) / (1024 * 1024)
                print(f"   Tamaño: {exe_size:.2f} MB")
                print(f"📁 Ubicación: {os.path.abspath(exe_dir)}")
                return True
            else:
                print("❌ Ejecutable no encontrado")
                return False
        else:
            print(f"\n❌ Construcción falló (código: {process.returncode})")
            return False

    except Exception as e:
        print(f"\n❌ Error durante construcción: {e}")
        return False

def create_py314_readme():
    """Crea documentación específica para Python 3.14."""
    readme_content = """# Nexus ML Trainer - Python 3.14 Edition

## ⚠️ Versión Especial para Python 3.14

Esta versión está optimizada específicamente para Python 3.14 y excluye algunas dependencias que aún no son compatibles.

## 🔧 Limitaciones

### ❌ Dependencias Excluidas
- **pandas-ta**: No compatible con Python 3.14 (requiere numba)
- **numba**: No soporta Python 3.14 aún

### ✅ Funcionalidades Disponibles
- ✅ XGBoost para ML training
- ✅ Scikit-learn para preprocessing
- ✅ Pandas para data handling
- ✅ YFinance para descarga de datos
- ✅ Interfaz gráfica completa

### ⚠️ Funcionalidades Afectadas
- **Análisis técnico avanzado**: Limitado sin pandas-ta
- **Indicadores técnicos**: Usará implementación básica
- **Performance**: Sin optimizaciones de numba

## 🚀 Instalación

### Opción 1: Instalador Automatizado
```bash
python scripts/setup_ml_trainer_py314.py
```

### Opción 2: Manual
```bash
# Instalar dependencias compatibles
pip install xgboost>=2.0.0 scikit-learn>=1.4.0 pandas>=2.1.0
pip install yfinance>=0.2.40 pyinstaller>=6.0.0

# Crear ejecutable
python scripts/create_ml_trainer_exe.py
```

## 📊 Comparación de Features

| Feature | Python 3.11-3.13 | Python 3.14 |
|---------|------------------|-------------|
| pandas-ta | ✅ Completo | ❌ Excluido |
| Indicadores técnicos | ✅ Avanzados | ⚠️ Básicos |
| Performance | ✅ Optimizada | ⚠️ Estándar |
| Compatibilidad | ✅ Completa | ✅ Funcional |

## 🔄 Actualización Futura

Cuando pandas-ta y numba sean compatibles con Python 3.14, esta versión especial será actualizada automáticamente.

## 📞 Soporte

Para problemas específicos de Python 3.14:
1. Verificar que todas las dependencias están instaladas
2. Comprobar logs de error detallados
3. Considerar usar Python 3.11-3.13 para features completas

---
*Versión especial para Python 3.14 - Generado automáticamente*
"""

    readme_path = "README_PY314.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"✅ README Python 3.14 creado: {readme_path}")

def main():
    """Función principal del instalador Python 3.14."""
    print("🐍 INSTALADOR PYTHON 3.14: Nexus ML Trainer")
    print("=" * 60)
    print("Versión optimizada para Python 3.14")
    print("Excluye pandas-ta por compatibilidad")
    print()

    # Verificar Python
    check_python_314()

    print()

    # Instalar dependencias
    if not install_dependencies_py314():
        print("❌ Falló instalación de dependencias")
        return

    print()

    # Crear especificaciones
    spec_file = create_simplified_spec()

    print()

    # Construir ejecutable
    if build_executable_py314(spec_file):
        print()

        # Crear documentación
        create_py314_readme()

        print()
        print("🎉 ¡INSTALACIÓN COMPLETA PARA PYTHON 3.14!")
        print()
        print("📦 RESULTADOS:")
        print("   ✅ Dependencias compatibles instaladas")
        print("   ✅ Ejecutable optimizado creado")
        print("   ✅ Documentación específica generada")
        print()
        print("🚀 EJECUTABLE DISPONIBLE:")
        print("   📁 dist/Nexus_ML_Trainer_PY314/")
        print("   📄 README_PY314.md")
        print()
        print("⚠️  NOTA: Sin pandas-ta (limitaciones en indicadores técnicos)")
        print("🔄 Se actualizará cuando sea compatible con Python 3.14")

    else:
        print("❌ Error en construcción del ejecutable")

if __name__ == "__main__":
    main()
