@echo off
echo ================================================
echo 📦 INSTALACIÓN DE DEPENDENCIAS - NEXUS ML
echo ================================================
echo.

cd /d "%~dp0"
echo 📂 Directorio de trabajo: %CD%
echo.

echo 🔍 Verificando Python...
python --version
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo 💡 Instala Python desde: https://python.org
    pause
    exit /b 1
)
echo ✅ Python encontrado
echo.

echo 🔍 Verificando pip...
python -m pip --version
if errorlevel 1 (
    echo ❌ ERROR: pip no está disponible
    pause
    exit /b 1
)
echo ✅ pip encontrado
echo.

echo 📦 Actualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ⚠️  Advertencia: No se pudo actualizar pip, continuando...
)
echo.

echo 📦 Detectando versión de Python para elegir estrategia de instalación...

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i

echo 🔍 Versión detectada: %python_version%

echo %python_version% | findstr "3.14" >nul
if %errorlevel% equ 0 (
    echo 🐍 Python 3.14.0 detectado - usando instalación especializada...
    echo 📦 Instalando desde requirements_py314.txt...
    python -m pip install -r requirements_py314.txt
) else (
    echo 🐍 Versión estándar detectada - instalación normal...
    echo 📦 Instalando desde requirements.txt...
    python -m pip install -r requirements.txt
)

if errorlevel 1 (
    echo.
    echo ❌ ERROR: Falló la instalación de algunas dependencias
    echo.
    echo 💡 SOLUCIONES POR VERSIÓN DE PYTHON:
    echo.
    echo 📌 Para Python 3.14.0:
    echo    • Ejecuta: install_py314.bat (instalación paso a paso)
    echo.
    echo 📌 Para otras versiones:
    echo    • pip install --upgrade pip setuptools wheel
    echo    • pip install pandas numpy scikit-learn xgboost joblib
    echo    • Instala Visual Studio Build Tools si faltan compiladores
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Todas las dependencias instaladas exitosamente!
echo.
echo 🧪 Probando instalación...
python -c "import pandas, numpy, sklearn, xgboost, joblib, tqdm; print('✅ Todas las importaciones exitosas')"
if errorlevel 1 (
    echo ❌ ERROR: Algunas importaciones fallan
) else (
    echo ✅ Todas las importaciones funcionan correctamente
)

echo.
echo 🎯 PRÓXIMOS PASOS:
echo    1. Ejecuta: debug_training.bat (para verificar funcionamiento)
echo    2. Ejecuta: train_ml.bat (para entrenar el modelo)
echo.
pause
