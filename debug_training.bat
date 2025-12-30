@echo off
echo ================================================
echo 🐛 DEBUG - NEXUS CORTEX ML TRAINING
echo ================================================
echo.

cd /d "%~dp0"

echo 🔍 Ejecutando pruebas de diagnóstico...
echo 📍 Directorio: %CD%
echo 🐍 Python: %PYTHONPATH%
echo.

echo 🧪 Verificando Python disponible...
python --version
if errorlevel 1 (
    echo ❌ ERROR: Python no encontrado en PATH
    echo 💡 Asegúrate de que Python esté instalado y en el PATH
    pause
    exit /b 1
)

echo.
echo 🔍 Ejecutando pruebas de diagnóstico...
echo 🐍 Usando: %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe
"%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" debug_training.py

if errorlevel 1 (
    echo.
    echo ⚠️  Falló con Python del sistema, intentando con C:\Python314\
    "C:\Python314\python.exe" debug_training.py
)

if errorlevel 1 (
    echo.
    echo ❌ Error ejecutando el script
    echo 💡 Verifica que todas las dependencias estén instaladas
) else (
    echo.
    echo ✅ Script ejecutado correctamente
)

echo.
pause
