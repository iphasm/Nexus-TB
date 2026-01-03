@echo off
REM Nexus ML Trainer - Instalador Automatizado
REM ==========================================
echo.
echo ============================================
echo     Nexus ML Trainer v2.0 - Instalador
echo ============================================
echo.
echo Este instalador creara un ejecutable con
echo interfaz grafica para entrenar modelos ML
echo.
echo Requisitos:
echo - Python 3.8+
echo - Conexion a internet
echo - 500MB espacio libre
echo.
echo Presione cualquier tecla para continuar...
pause >nul

echo.
echo 🔍 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no encontrado
    echo.
    echo Instale Python desde: https://python.org
    echo Asegurese de marcar "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

echo 🔍 Verificando compatibilidad de versión...
python scripts/check_python_compatibility.py
if errorlevel 1 (
    echo ❌ Versión de Python no compatible
    echo.
    echo 💡 Instale Python 3.13 desde: https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Versión de Python compatible
echo.

REM Detectar versión de Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 📋 Versión de Python detectada: %PYTHON_VERSION%

REM Verificar compatibilidad de versiones
echo %PYTHON_VERSION% | findstr "3.8" >nul
if %errorlevel% == 0 goto :python_compatible
echo %PYTHON_VERSION% | findstr "3.9" >nul
if %errorlevel% == 0 goto :python_compatible
echo %PYTHON_VERSION% | findstr "3.10" >nul
if %errorlevel% == 0 goto :python_compatible
echo %PYTHON_VERSION% | findstr "3.11" >nul
if %errorlevel% == 0 goto :python_compatible
echo %PYTHON_VERSION% | findstr "3.12" >nul
if %errorlevel% == 0 goto :python_compatible
echo %PYTHON_VERSION% | findstr "3.13" >nul
if %errorlevel% == 0 goto :python_compatible

REM Verificar si es Python 3.14 (versión especial)
echo %PYTHON_VERSION% | findstr "3.14" >nul
if %errorlevel% == 0 (
    echo 🎯 Python 3.14 detectado - Usando instalador especial
    echo ✅ pandas-ta-openbb incluido para indicadores técnicos avanzados
    echo.
    echo 📦 Instalando dependencias compatibles con Python 3.14...
    echo.

    python scripts/setup_ml_trainer_py314.py
    goto :end_install
)

REM Versión no soportada
echo ❌ ERROR: Versión de Python no compatible
echo.
echo Versiones soportadas:
echo ✅ Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 - Features completas
echo ✅ Python 3.14 - Features completas (pandas-ta-openbb)
echo ❌ Python < 3.8 - No soportado
echo.
echo Instale Python 3.8-3.13 desde: https://python.org
pause
exit /b 1

:python_compatible
echo ✅ Python %PYTHON_VERSION% compatible - Features completas disponibles
echo 🎉 pandas-ta incluido para indicadores técnicos avanzados
echo.
echo 📦 Instalando dependencias completas (esto puede tomar varios minutos)...
echo.

pip install pyinstaller xgboost scikit-learn pandas joblib yfinance pandas-ta requests --quiet

if errorlevel 1 (
    echo ❌ ERROR: Fallo instalando dependencias
    echo.
    echo Posibles soluciones:
    echo 1. Verificar conexión a internet
    echo 2. Ejecutar como administrador
    echo 3. Instalar manualmente:
    echo    pip install pyinstaller xgboost scikit-learn pandas joblib yfinance pandas-ta requests
    echo 4. Si el error persiste, usar Python 3.13 alternativo
    echo.
    pause
    exit /b 1
)

echo ✅ Todas las dependencias instaladas correctamente
echo.

echo 🏗️ Creando ejecutable con features completas...
echo ℹ️  Esto puede tomar 10-20 minutos...
echo.

python scripts/setup_ml_trainer.py

:end_install

if errorlevel 1 (
    echo ❌ ERROR: Fallo creando ejecutable
    echo.
    echo Revise los mensajes de error arriba
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo         ¡INSTALACIÓN COMPLETADA!
echo ============================================
echo.
echo ✅ Ejecutable creado exitosamente
echo.
echo 📁 Ubicacion: dist\Nexus_ML_Trainer\
echo 📦 Paquete: Nexus_ML_Trainer_Portable_*.zip
echo.
echo 🚀 Para usar:
echo    1. Extraiga el ZIP
echo    2. Ejecute Nexus_ML_Trainer.exe
echo    3. ¡Disfrute la interfaz grafica!
echo.
echo 📖 Documentacion: ML_TRAINER_README.md
echo.
echo Presione cualquier tecla para finalizar...
pause >nul

echo.
echo ¡Gracias por usar Nexus ML Trainer!
echo.
