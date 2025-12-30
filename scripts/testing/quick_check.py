#!/usr/bin/env python3
"""
Check rápido de dependencias - versión simplificada
"""
import sys

def test_import(module_name):
    """Prueba una importación individual"""
    try:
        print(f"Probando {module_name}...", end=" ", flush=True)
        __import__(module_name)
        print("✅ OK")
        return True
    except ImportError as e:
        print(f"❌ FALLÓ: {e}")
        return False

print("=" * 40)
print("CHECK RÁPIDO DE DEPENDENCIAS")
print("=" * 40)
print(f"Python: {sys.version.split()[0]}")
print()

# Lista de dependencias críticas
deps = [
    "numpy",
    "pandas",
    "sklearn",
    "xgboost",
    "joblib",
    "yfinance",
    "tqdm"
]

success_count = 0
for dep in deps:
    if test_import(dep):
        success_count += 1

print()
print(f"Resultado: {success_count}/{len(deps)} dependencias OK")

if success_count == len(deps):
    print("🎉 ¡Todas las dependencias críticas funcionan!")
else:
    print("❌ Algunas dependencias faltan")

print("=" * 40)
