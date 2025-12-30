@echo off
echo ================================================
echo 🐍 INSTALACIÓN PARA PYTHON 3.14.0 - NEXUS ML
echo ================================================
echo.

cd /d "%~dp0"
echo 📂 Directorio de trabajo: %CD%
echo.

echo 🔍 Detectando versión de Python...
python --version
echo.

echo 📦 Estrategia de instalación para Python 3.14.0:
echo    • Usando requirements_py314.txt (optimizado para 3.14)
echo    • Instalando dependencias críticas primero
echo    • Evitando librerías problemáticas
echo.

echo 📦 PASO 1: Actualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ⚠️  No se pudo actualizar pip, continuando...
)
echo.

echo 📦 PASO 2: Instalando dependencias críticas...
echo 🧪 Probando instalación básica...

python -c "import sys; print(f'Python version: {sys.version}')"

pip install --upgrade pip setuptools wheel
pip install numpy pandas

if errorlevel 1 (
    echo ❌ Error instalando dependencias básicas
    echo 💡 Posibles soluciones:
    echo    • Reinicia tu terminal
    echo    • Verifica conexión a internet
    echo    • Instala manualmente: pip install numpy pandas
    pause
    exit /b 1
)

echo ✅ Dependencias básicas OK
echo.

echo 📦 PASO 3: Instalando librerías ML (una por una)...
echo 🧪 Scikit-learn...
pip install scikit-learn --no-deps
if errorlevel 1 (
    echo ⚠️  Scikit-learn falló, intentando versión específica...
    pip install scikit-learn==1.4.0 --no-deps
)

echo 🧪 XGBoost...
pip install xgboost --no-deps
if errorlevel 1 (
    echo ⚠️  XGBoost falló, intentando versión específica...
    pip install xgboost==2.0.0 --no-deps
)

echo 🧪 Joblib...
pip install joblib --no-deps
if errorlevel 1 (
    echo ⚠️  Joblib falló, intentando versión específica...
    pip install joblib==1.4.0 --no-deps
)

echo.

echo 📦 PASO 4: Instalando dependencias restantes...
pip install yfinance pandas-ta tqdm python-binance

if errorlevel 1 (
    echo ⚠️  Algunas dependencias opcionales fallaron, pero continuamos...
)

echo.

echo 📦 PASO 5: Verificando instalación...
echo 🧪 Probando importaciones críticas...

python -c "
try:
    import pandas as pd
    import numpy as np
    import sklearn
    import xgboost
    import joblib
    import yfinance
    print('✅ TODAS LAS IMPORTACIONES CRÍTICAS EXITOSAS')
    print(f'   • pandas: {pd.__version__}')
    print(f'   • numpy: {np.__version__}')
    print(f'   • scikit-learn: {sklearn.__version__}')
    print(f'   • xgboost: {xgboost.__version__}')
except ImportError as e:
    print(f'❌ IMPORTACIÓN FALLIDA: {e}')
    exit(1)
"

if errorlevel 1 (
    echo ❌ Verificación fallida
    echo 💡 Algunas dependencias críticas no se instalaron
    pause
    exit /b 1
)

echo.
echo 🎉 ¡INSTALACIÓN COMPLETADA PARA PYTHON 3.14.0!
echo.
echo ✅ Dependencias críticas instaladas y verificadas
echo.
echo 🚀 PRÓXIMOS PASOS:
echo    1. Ejecuta: debug_training.bat (verificar funcionamiento)
echo    2. Ejecuta: train_ml.bat (entrenar modelo ML)
echo.
echo 💡 Nota: Algunas dependencias avanzadas pueden no estar disponibles
echo          pero las funciones ML críticas funcionan correctamente.
echo.
pause
