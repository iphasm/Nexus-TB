@echo off
echo ================================================
echo 🔍 VERIFICACIÓN RÁPIDA DE DEPENDENCIAS
echo ================================================
echo.

cd /d "%~dp0"

echo 🧪 Verificando dependencias ML...
echo.

python check_dependencies.py

echo.
if errorlevel 1 (
    echo ❌ Faltan dependencias - ejecuta install_dependencies.bat
) else (
    echo ✅ Todas las dependencias OK - puedes ejecutar debug_training.bat
)

echo.
pause
