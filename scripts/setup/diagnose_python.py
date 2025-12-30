#!/usr/bin/env python3
"""
Diagnóstico completo del entorno Python
"""
import sys
import os
import subprocess

def run_command(cmd):
    """Ejecuta un comando y retorna la salida"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

print("=" * 60)
print("🔍 DIAGNÓSTICO COMPLETO - ENTORNO PYTHON")
print("=" * 60)

# Información básica de Python
print(f"🐍 Python versión: {sys.version}")
print(f"📁 Ejecutable: {sys.executable}")
print(f"🏠 Directorio: {os.getcwd()}")
print()

# Variables de entorno relevantes
print("🔧 Variables de entorno:")
print(f"  PYTHONPATH: {os.environ.get('PYTHONPATH', 'No definido')}")
print(f"  PYTHONHOME: {os.environ.get('PYTHONHOME', 'No definido')}")
print(f"  PATH incluye Python: {'python' in os.environ.get('PATH', '').lower()}")
print()

# Verificar pip
print("📦 Verificando pip:")
stdout, stderr, code = run_command("python -m pip --version")
if code == 0:
    print(f"  ✅ pip disponible: {stdout}")
else:
    print(f"  ❌ pip no disponible: {stderr}")

# Verificar site-packages
print()
print("📚 Site packages:")
for path in sys.path[:3]:  # Mostrar primeros 3 paths
    print(f"  • {path}")

print()
print("🔍 Verificando dependencias críticas:")

# Lista de dependencias a verificar
deps = [
    ("numpy", "import numpy as np; print(f'v{np.__version__}')"),
    ("pandas", "import pandas as pd; print(f'v{pd.__version__}')"),
    ("sklearn", "import sklearn; print(f'v{sklearn.__version__}')"),
    ("xgboost", "import xgboost; print(f'v{xgboost.__version__}')"),
    ("joblib", "import joblib; print(f'v{joblib.__version__}')"),
    ("yfinance", "import yfinance; print('OK')"),
    ("tqdm", "import tqdm; print('OK')")
]

for dep_name, test_code in deps:
    print(f"  {dep_name}...", end=" ")
    try:
        exec(test_code)
        print("✅")
    except Exception as e:
        print(f"❌ ({str(e)[:30]}...)")

print()
print("🔍 Verificando comandos de pip:")

# Verificar qué muestra pip list
stdout, stderr, code = run_command("python -m pip list | findstr -i pandas")
if stdout:
    print(f"  📦 pandas en pip list: {stdout}")
else:
    print("  ❌ pandas NO encontrado en pip list")

stdout, stderr, code = run_command("python -m pip list | findstr -i joblib")
if stdout:
    print(f"  📦 joblib en pip list: {stdout}")
else:
    print("  ❌ joblib NO encontrado en pip list")

print()
print("💡 RECOMENDACIONES:")
print("  1. Si faltan dependencias: pip install pandas numpy scikit-learn xgboost joblib")
print("  2. Si hay problemas de path: reinstalar Python o usar entorno virtual")
print("  3. Si usas conda: conda install pandas scikit-learn xgboost")

print()
print("=" * 60)
input("Presiona Enter para salir...")
