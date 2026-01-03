#!/usr/bin/env python3
"""
INSTALADOR RÁPIDO: Nexus ML Trainer GUI
=====================================

Instalador automatizado que verifica dependencias y crea el ejecutable
con configuración óptima para el sistema actual.
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Verifica la versión de Python."""
    print("🐍 Verificando versión de Python...")

    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} no soportado. Requiere Python 3.8+")
        return False

    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_dependencies():
    """Instala las dependencias necesarias."""
    print("📦 Instalando dependencias...")

    dependencies = [
        'pyinstaller',
        'tkinter',  # Viene con Python
        'xgboost',
        'scikit-learn',
        'pandas',
        'joblib',
        'yfinance',
        'pandas-ta',
        'requests'
    ]

    # Verificar qué está instalado
    to_install = []
    for dep in dependencies:
        try:
            if dep == 'tkinter':
                import tkinter
            elif dep == 'scikit-learn':
                import sklearn
            else:
                importlib.import_module(dep.replace('-', '_'))
            print(f"✅ {dep} - instalado")
        except ImportError:
            to_install.append(dep)
            print(f"❌ {dep} - faltante")

    # Instalar faltantes
    if to_install:
        print(f"\n🔧 Instalando {len(to_install)} paquetes...")
        cmd = [sys.executable, '-m', 'pip', 'install'] + to_install

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("✅ Dependencias instaladas correctamente")
                return True
            else:
                print("❌ Error instalando dependencias:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("❌ Timeout instalando dependencias")
            return False
    else:
        print("✅ Todas las dependencias ya están instaladas")
        return True

def create_optimized_spec():
    """Crea archivo de especificaciones optimizado."""
    print("📝 Creando especificaciones optimizadas...")

    # Detectar arquitectura del sistema
    import platform
    arch = platform.machine().lower()

    # Configuración optimizada
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Configuración optimizada para {platform.system()} {arch}
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
        'pandas_ta', 'pandas_ta.utils', 'pandas_ta.overlap',
        'pandas_ta.momentum', 'pandas_ta.volume',
        'pandas_ta.volatility', 'pandas_ta.trend',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter.test', 'test', 'unittest', 'pdb', 'pydoc',
        'doctest', 'sqlite3', 'dbm', 'gdbm', 'readline', 'rlcompleter',
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
    name='Nexus_ML_Trainer',
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

# Para distribución one-folder (más compatible)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nexus_ML_Trainer'
)
'''

    spec_file = "ml_trainer_optimized.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"✅ Especificaciones optimizadas creadas: {spec_file}")
    return spec_file

def build_executable(spec_file):
    """Construye el ejecutable."""
    print("🏗️ Construyendo ejecutable...")

    cmd = [
        sys.executable, '-m', 'pyinstaller',
        '--clean',
        '--noconfirm',
        '--onedir',  # Crear directorio con todos los archivos
        spec_file
    ]

    print(f"🔧 Comando: {' '.join(cmd)}")

    try:
        # Mostrar progreso en tiempo real
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, universal_newlines=True) as process:

            for line in process.stdout:
                print(line, end='', flush=True)

        if process.returncode == 0:
            print("\n✅ Ejecutable construido exitosamente!")

            # Verificar archivos generados
            exe_dir = "dist/Nexus_ML_Trainer"
            exe_file = os.path.join(exe_dir, "Nexus_ML_Trainer.exe")

            if os.path.exists(exe_file):
                exe_size = os.path.getsize(exe_file) / (1024 * 1024)
                print(".2f"                print(f"📁 Ubicación: {os.path.abspath(exe_dir)}")

                # Crear atajo en el escritorio (opcional)
                create_desktop_shortcut(exe_file)

                return True
            else:
                print("❌ Ejecutable no encontrado")
                return False
        else:
            print(f"\n❌ Error en construcción (código: {process.returncode})")
            return False

    except Exception as e:
        print(f"\n❌ Error durante construcción: {e}")
        return False

def create_desktop_shortcut(exe_path):
    """Crea un acceso directo en el escritorio (Windows)."""
    try:
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "Nexus ML Trainer.lnk")

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()

        print(f"✅ Acceso directo creado: {shortcut_path}")

    except ImportError:
        print("ℹ️  Para crear acceso directo instalar: pip install pywin32 winshell")
    except Exception as e:
        print(f"⚠️  No se pudo crear acceso directo: {e}")

def create_portable_package():
    """Crea un paquete portable listo para distribución."""
    print("📦 Creando paquete portable...")

    try:
        import shutil
        from datetime import datetime

        # Directorio fuente
        source_dir = "dist/Nexus_ML_Trainer"
        if not os.path.exists(source_dir):
            print(f"❌ Directorio fuente no encontrado: {source_dir}")
            return False

        # Crear directorio de paquete
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"Nexus_ML_Trainer_Portable_{timestamp}"
        package_dir = package_name

        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        os.makedirs(package_dir)

        # Copiar archivos
        print("📋 Copiando archivos...")
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(package_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # Crear archivos auxiliares
        create_package_readme(package_dir)
        create_default_config(package_dir)

        # Crear ZIP
        zip_name = f"{package_name}.zip"
        print(f"📦 Comprimiendo en {zip_name}...")
        shutil.make_archive(package_name, 'zip', package_dir)

        # Calcular tamaño
        zip_size = os.path.getsize(zip_name) / (1024 * 1024)

        print("
✅ Paquete portable creado:"        print(f"   📁 Directorio: {package_dir}/")
        print(f"   📦 Archivo ZIP: {zip_name}")
        print(".2f"
        return True

    except Exception as e:
        print(f"❌ Error creando paquete: {e}")
        return False

def create_package_readme(package_dir):
    """Crea README para el paquete portable."""
    readme = f"""# Nexus ML Trainer - Portable Package

Versión: 2.0
Generado: {os.path.basename(package_dir).replace('Nexus_ML_Trainer_Portable_', '')}

## 🚀 Inicio Rápido

1. Extraer todos los archivos del ZIP
2. Ejecutar `Nexus_ML_Trainer.exe`
3. ¡Listo! La interfaz gráfica se abrirá automáticamente

## 📋 Requisitos

- Windows 10/11 (64-bit)
- 8GB RAM mínimo
- No requiere instalación adicional

## 🛠️ Características

- ✅ Interfaz gráfica intuitiva
- ✅ Entrenamiento ML automatizado
- ✅ Backup automático de modelos
- ✅ Logs en tiempo real
- ✅ Configuración persistente
- ✅ Portable (no requiere instalación)

## 📊 Parámetros Recomendados

- Velas: 5000 (balance entre velocidad y calidad)
- Símbolos: Todos habilitados (automático)
- Verbose: Activado (para monitoreo)
- Backup: Activado (seguridad)

## 🔧 Solución de Problemas

### Error de memoria
- Reducir velas a 3000
- Limitar símbolos a 20

### Error de conexión
- Verificar conexión a internet
- Los datos se descargan automáticamente

### Error de permisos
- Ejecutar como administrador
- Verificar que no esté bloqueado por antivirus

## 📞 Soporte

Si encuentra problemas:
1. Revisar los logs de la aplicación
2. Verificar que el antivirus no bloquee el ejecutable
3. Asegurarse de tener permisos de escritura

---
Paquete portable generado automáticamente
Nexus Trading Bot - ML Training Suite
"""

    readme_path = os.path.join(package_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme)

def create_default_config(package_dir):
    """Crea configuración por defecto para el paquete."""
    config = {
        "candles": 5000,
        "symbols": None,
        "verbose": True,
        "backup": True,
        "version": "2.0",
        "created": str(os.path.basename(package_dir))
    }

    config_path = os.path.join(package_dir, "config.json")
    import json
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def main():
    """Función principal del instalador."""
    print("🚀 INSTALADOR AUTOMATIZADO: Nexus ML Trainer GUI")
    print("=" * 70)
    print("Este script creará un ejecutable portable con interfaz gráfica")
    print("para entrenar el modelo ML de Nexus de manera sencilla.")
    print()

    # Paso 1: Verificar Python
    if not check_python_version():
        return

    # Paso 2: Instalar dependencias
    if not install_dependencies():
        return

    print()

    # Paso 3: Crear especificaciones optimizadas
    spec_file = create_optimized_spec()

    print()

    # Paso 4: Construir ejecutable
    if build_executable(spec_file):
        print()

        # Paso 5: Crear paquete portable
        if create_portable_package():
            print()
            print("🎉 ¡INSTALACIÓN COMPLETA!")
            print()
            print("📦 RESUMEN:")
            print("   ✅ Ejecutable creado: dist/Nexus_ML_Trainer/Nexus_ML_Trainer.exe")
            print("   ✅ Paquete portable: Nexus_ML_Trainer_Portable_*.zip")
            print("   ✅ Acceso directo: Creado en escritorio (si pywin32 instalado)")
            print()
            print("🚀 PRÓXIMOS PASOS:")
            print("   1. Extraer el ZIP del paquete portable")
            print("   2. Ejecutar Nexus_ML_Trainer.exe")
            print("   3. ¡Entrenar modelos ML con interfaz gráfica!")
            print()
            print("⚡ RECUERDA:")
            print("   • El entrenamiento puede tomar 10-30 minutos")
            print("   • Se recomienda backup automático (activado por defecto)")
            print("   • Los logs se guardan automáticamente")
            print()
            print("🎯 ¡DISFRUTA TU NUEVA HERRAMIENTA ML!")

        else:
            print("⚠️  Ejecutable creado pero error en paquete portable")
    else:
        print("❌ Error en construcción del ejecutable")
        print("💡 Verificar logs de PyInstaller arriba")

if __name__ == "__main__":
    main()
