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

echo 📦 Instalando dependencias (esto puede tomar varios minutos)...
echo.

pip install pyinstaller xgboost scikit-learn pandas joblib yfinance pandas-ta requests --quiet

if errorlevel 1 (
    echo ❌ ERROR: Fallo instalando dependencias
    echo.
    echo Intente manualmente: pip install pyinstaller xgboost scikit-learn pandas joblib yfinance pandas-ta requests
    echo.
    pause
    exit /b 1
)

echo ✅ Dependencias instaladas
echo.

echo 🏗️ Creando ejecutable...
echo Esto puede tomar 10-20 minutos...
echo.

python scripts/setup_ml_trainer.py

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
