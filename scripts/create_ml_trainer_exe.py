#!/usr/bin/env python3
"""
CREADOR DE EJECUTABLE: Nexus ML Trainer GUI
==========================================

Crea un ejecutable .exe independiente para Windows con la interfaz gráfica
del entrenador ML de Nexus.

REQUISITOS:
- Python 3.8+
- PyInstaller
- Todas las dependencias del proyecto

INSTALACIÓN DE DEPENDENCIAS:
pip install pyinstaller
pip install -r requirements.txt
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas."""
    print("🔍 Verificando dependencias...")

    required_packages = [
        'pyinstaller',
        'tkinter',  # Viene con Python estándar
        'xgboost',
        'scikit-learn',
        'pandas',
        'joblib',
        'yfinance',
        'pandas-ta',
        'requests'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'scikit-learn':
                import sklearn
            else:
                __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")

    if missing_packages:
        print(f"\n⚠️  Paquetes faltantes: {', '.join(missing_packages)}")
        print("💡 Instalar con: pip install " + " ".join(missing_packages))
        return False

    print("✅ Todas las dependencias están instaladas")
    return True

def create_spec_file():
    """Crea el archivo de especificaciones para PyInstaller."""
    print("📝 Creando archivo de especificaciones...")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Añadir el directorio del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

# Configuración del análisis
a = Analysis(
    ['scripts/ml_trainer_gui.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # Incluir archivos necesarios
        (os.path.join(project_root, 'system_directive.py'), '.'),
        (os.path.join(project_root, 'nexus_system'), 'nexus_system'),
        (os.path.join(project_root, 'src'), 'src'),
        (os.path.join(project_root, 'servos'), 'servos'),
    ],
    hiddenimports=[
        # Dependencias críticas
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'system_directive',
        'servos.voight_kampff',
        'nexus_system.cortex.ml_classifier',
        'pandas.plotting._matplotlib',
        'pandas.plotting._core',
        'sklearn.utils._weight_vector',
        'sklearn.utils._cython_blas',
        'xgboost.core',
        'xgboost.sklearn',
        'joblib.numpy_pickle_utils',
        'joblib.compression',
        'yfinance.utils',
        'yfinance.ticker',
        'pandas_ta',
        'pandas_ta.utils',
        'pandas_ta.overlap',
        'pandas_ta.momentum',
        'pandas_ta.volume',
        'pandas_ta.volatility',
        'pandas_ta.trend',
        'pandas_ta.Overlap',
        'pandas_ta.Momentum',
        'pandas_ta.Volume',
        'pandas_ta.Volatility',
        'pandas_ta.Trend',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir módulos innecesarios para reducir tamaño
        'tkinter.test',
        'test',
        'unittest',
        'pdb',
        'pydoc',
        'doctest',
        'argparse',
        'optparse',
        'getopt',
        'readline',
        'rlcompleter',
        'sqlite3',
        'dbm',
        'gdbm',
        'pickle',
        'copyreg',
        'copy',
        'pprint',
        'reprlib',
        'enum',
        'numbers',
        'math',
        'cmath',
        'decimal',
        'fractions',
        'random',
        'statistics',
        'datetime',  # Mantener datetime
        'calendar',
        'time',
        'zoneinfo',
        'locale',
        'gettext',
        'argparse',  # Necesario para el script
        'optparse',
        'getopt',
        'readline',
        'rlcompleter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Configuración del PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Configuración del EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Nexus_ML_Trainer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False = sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Añadir icono si existe
)

# Configuración del directorio de distribución (opcional)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='Nexus_ML_Trainer'
# )
'''

    spec_file = "ml_trainer.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"✅ Archivo de especificaciones creado: {spec_file}")
    return spec_file

def create_exe(spec_file):
    """Crea el ejecutable usando PyInstaller."""
    print("🏗️ Creando ejecutable...")

    cmd = [
        sys.executable, "-m", "pyinstaller",
        "--clean",  # Limpiar cache
        "--noconfirm",  # No pedir confirmación
        spec_file
    ]

    print(f"🔧 Ejecutando: {' '.join(cmd)}")

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutos timeout
        )

        print("STDOUT:")
        print(process.stdout)

        if process.stderr:
            print("STDERR:")
            print(process.stderr)

        if process.returncode == 0:
            print("✅ Ejecutable creado exitosamente")

            # Verificar que el exe existe
            exe_path = "dist/Nexus_ML_Trainer.exe"
            if os.path.exists(exe_path):
                exe_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(".2f"                print(f"📁 Ubicación: {os.path.abspath(exe_path)}")

                return True
            else:
                print("❌ Ejecutable no encontrado después de la compilación")
                return False
        else:
            print(f"❌ PyInstaller falló con código: {process.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Timeout: La creación del ejecutable tomó más de 30 minutos")
        return False
    except Exception as e:
        print(f"❌ Error durante la creación: {e}")
        return False

def create_installer_package():
    """Crea un paquete de instalación con el ejecutable y archivos auxiliares."""
    print("📦 Creando paquete de instalación...")

    try:
        # Crear directorio de distribución
        dist_dir = "Nexus_ML_Trainer_Package"
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        os.makedirs(dist_dir)

        # Copiar ejecutable
        exe_source = "dist/Nexus_ML_Trainer.exe"
        exe_dest = os.path.join(dist_dir, "Nexus_ML_Trainer.exe")

        if os.path.exists(exe_source):
            shutil.copy2(exe_source, exe_dest)
            print(f"✅ Ejecutable copiado: {exe_dest}")
        else:
            print(f"⚠️  Ejecutable no encontrado: {exe_source}")
            return False

        # Crear archivos auxiliares
        create_readme(dist_dir)
        create_config_template(dist_dir)
        create_launcher_script(dist_dir)

        # Crear archivo ZIP
        zip_name = f"Nexus_ML_Trainer_v2.0_{os.name}"
        shutil.make_archive(zip_name, 'zip', dist_dir)

        print(f"✅ Paquete creado: {zip_name}.zip")
        print(f"📁 Contenido en: {dist_dir}/")

        return True

    except Exception as e:
        print(f"❌ Error creando paquete: {e}")
        return False

def create_readme(dist_dir):
    """Crea archivo README para el paquete."""
    readme_content = """# Nexus ML Trainer v2.0

## 🚀 Interfaz Gráfica para Entrenamiento ML

Esta aplicación permite entrenar el modelo de Machine Learning de Nexus de manera sencilla mediante una interfaz gráfica intuitiva.

## 📋 Requisitos del Sistema

- Windows 10/11 (64-bit)
- 8GB RAM mínimo (16GB recomendado)
- 4GB espacio libre en disco
- Conexión a internet para descargar datos de mercado

## 🛠️ Instalación

1. Extraer todos los archivos del ZIP
2. Ejecutar `Nexus_ML_Trainer.exe`
3. La aplicación se abrirá automáticamente

## 📖 Uso

### Configuración Básica
- **Velas de entrenamiento**: Número de velas históricas (recomendado: 5000)
- **Límite de símbolos**: Dejar vacío para usar todos los activos habilitados

### Opciones Avanzadas
- **Verbose**: Mostrar logs detallados durante el entrenamiento
- **Backup automático**: Crear copia del modelo anterior

### Proceso de Entrenamiento
1. Configurar parámetros
2. Hacer clic en "🚀 Iniciar Entrenamiento"
3. Observar progreso en la barra y logs en tiempo real
4. El entrenamiento puede tomar 10-30 minutos
5. Al finalizar, el modelo estará actualizado

## 📊 Resultados

Los archivos generados se guardarán en:
- Modelo: `nexus_system/memory_archives/ml_model.pkl`
- Scaler: `nexus_system/memory_archives/scaler.pkl`
- Backup: `*_backup_*.pkl` (automático)

## 🔧 Solución de Problemas

### Error de conexión
- Verificar conexión a internet
- Los datos se descargan de Yahoo Finance y Binance

### Error de memoria
- Reducir número de velas o símbolos
- Cerrar otras aplicaciones

### Error de permisos
- Ejecutar como administrador
- Verificar permisos de escritura en la carpeta

## 📞 Soporte

Para soporte técnico o reportar errores:
- Revisar los logs de la aplicación
- Verificar que todas las dependencias estén incluidas

## 📄 Licencia

Esta aplicación es parte del sistema Nexus Trading Bot.
Consulte la documentación principal para términos de uso.

---
Generado automáticamente - Nexus ML Trainer Package
"""

    readme_path = os.path.join(dist_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"✅ README creado: {readme_path}")

def create_config_template(dist_dir):
    """Crea archivo de configuración de ejemplo."""
    config = {
        "candles": 5000,
        "symbols": None,
        "verbose": True,
        "backup": True,
        "last_training": None
    }

    config_path = os.path.join(dist_dir, "ml_trainer_config_template.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    print(f"✅ Configuración de ejemplo creada: {config_path}")

def create_launcher_script(dist_dir):
    """Crea script batch para Windows."""
    batch_content = '''@echo off
echo ============================================
echo     Nexus ML Trainer v2.0
echo ============================================
echo.

REM Verificar si el ejecutable existe
if not exist "Nexus_ML_Trainer.exe" (
    echo ERROR: Nexus_ML_Trainer.exe no encontrado
    echo.
    echo Asegurese de que todos los archivos esten en el mismo directorio
    pause
    exit /b 1
)

echo Iniciando Nexus ML Trainer...
echo.

REM Ejecutar la aplicación
start "" "Nexus_ML_Trainer.exe"

echo Aplicacion iniciada. Puede cerrar esta ventana.
echo.
pause
'''

    batch_path = os.path.join(dist_dir, "Ejecutar_ML_Trainer.bat")
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)

    print(f"✅ Script launcher creado: {batch_path}")

def main():
    """Función principal."""
    print("🚀 CREACIÓN DE EJECUTABLE: Nexus ML Trainer GUI")
    print("=" * 60)

    # Verificar que estamos en Windows
    if os.name != 'nt':
        print("⚠️  Este script está diseñado para Windows")
        print("💡 Para otros sistemas operativos, modificar el script manualmente")
        if not input("¿Continuar de todos modos? (y/N): ").lower().startswith('y'):
            return

    # Paso 1: Verificar dependencias
    if not check_dependencies():
        print("❌ Faltan dependencias. Instalar con: pip install pyinstaller [dependencias faltantes]")
        return

    print()

    # Paso 2: Crear archivo de especificaciones
    spec_file = create_spec_file()

    print()

    # Paso 3: Crear ejecutable
    if create_exe(spec_file):
        print()

        # Paso 4: Crear paquete de instalación
        if create_installer_package():
            print()
            print("🎉 ¡PAQUETE COMPLETO CREADO EXITOSAMENTE!")
            print()
            print("📦 Archivos generados:")
            print("   • Nexus_ML_Trainer.exe - Ejecutable principal")
            print("   • Nexus_ML_Trainer_Package/ - Directorio con todos los archivos")
            print("   • Nexus_ML_Trainer_v2.0_nt.zip - Archivo comprimido")
            print()
            print("📋 Para usar:")
            print("   1. Extraer el ZIP")
            print("   2. Ejecutar Nexus_ML_Trainer.exe")
            print("   3. ¡Disfrutar de la interfaz gráfica!")
            print()
            print("⚡ Atajos de teclado en la aplicación:")
            print("   • F5: Iniciar entrenamiento")
            print("   • Escape: Detener entrenamiento")
            print("   • Ctrl+S: Guardar logs")
            print("   • Ctrl+L: Limpiar logs")

        else:
            print("⚠️  Ejecutable creado pero error en el paquete")
    else:
        print("❌ Error creando el ejecutable")

if __name__ == "__main__":
    main()
