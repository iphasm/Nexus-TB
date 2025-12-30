@echo off
echo ================================================
echo 🐛 DEBUG - NEXUS CORTEX ML TRAINING (Python 3.14)
echo ================================================
echo.

cd /d "%~dp0"

echo 🔍 Usando Python 3.14 específicamente...
echo 📍 Directorio: %CD%
echo.

echo 🧪 Verificando Python 3.14...
"C:\Python314\python.exe" --version
if errorlevel 1 (
    echo ❌ ERROR: Python 3.14 no encontrado en C:\Python314\
    echo 💡 Verifica la instalación de Python 3.14
    pause
    exit /b 1
)

echo.
echo 🔍 Ejecutando pruebas de diagnóstico con Python 3.14...
"C:\Python314\python.exe" debug_training.py

if errorlevel 1 (
    echo.
    echo ❌ Error ejecutando el script
    echo 💡 Posibles causas:
    echo    • Dependencias no instaladas en Python 3.14
    echo    • Conflicto de versiones
    echo    • Problema con el script
) else (
    echo.
    echo ✅ Script ejecutado correctamente con Python 3.14
)

echo.
pause
