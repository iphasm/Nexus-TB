@echo off
echo ================================================
echo 🔄 INSTALACIÓN LIMPIA PYTHON 3.14 - ÚLTIMO RECURSO
echo ================================================
echo.

cd /d "%~dp0"
echo 📂 Directorio: %CD%
echo.

echo ⚠️  ATENCIÓN: Este script instala desde cero
echo 💡 Crea un entorno virtual limpio para evitar conflictos
echo.

set /p confirm="¿Continuar? (y/N): "
if /i not "%confirm%"=="y" (
    echo ❌ Cancelado por el usuario
    pause
    exit /b 1
)

echo.
echo 🗑️  LIMPIANDO CACHE DE PIP...
pip cache purge
python -m pip install --upgrade pip --force-reinstall

echo.
echo 📦 CREANDO ENTORNO VIRTUAL...
python -m venv nexus_ml_env
if errorlevel 1 (
    echo ❌ Error creando entorno virtual
    echo 💡 Instala virtualenv: pip install virtualenv
    pause
    exit /b 1
)

echo.
echo 🔄 ACTIVANDO ENTORNO VIRTUAL...
call nexus_ml_env\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Error activando entorno virtual
    pause
    exit /b 1
)

echo ✅ Entorno virtual activado
echo.

echo 📦 INSTALANDO DEPENDENCIAS EN ENTORNO LIMPIO...

echo 🧪 Numpy...
pip install numpy==1.26.3
echo 🧪 Pandas...
pip install pandas==2.2.0
echo 🧪 Scikit-learn...
pip install scikit-learn==1.4.0
echo 🧪 XGBoost...
pip install xgboost==2.0.0
echo 🧪 Joblib...
pip install joblib==1.4.0
echo 🧪 Utilidades...
pip install tqdm requests python-dotenv
echo 🧪 APIs...
pip install yfinance python-binance
echo 🧪 Async...
pip install aiohttp websockets

echo.
echo 🧪 VERIFICANDO INSTALACIÓN EN ENTORNO VIRTUAL...

python -c "
import sys
print(f'🐍 Python: {sys.version}')
try:
    import numpy as np
    print(f'✅ numpy: {np.__version__}')
    import pandas as pd
    print(f'✅ pandas: {pd.__version__}')
    import sklearn
    print(f'✅ scikit-learn: {sklearn.__version__}')
    import xgboost
    print(f'✅ xgboost: {xgboost.__version__}')
    import joblib
    print(f'✅ joblib: {joblib.__version__}')
    import yfinance
    print('✅ yfinance: OK')
    from binance.client import Client
    print('✅ python-binance: OK')
    print('')
    print('🎉 ¡TODAS LAS DEPENDENCIAS INSTALADAS EN ENTORNO VIRTUAL!')
    print('💡 Para usar: call nexus_ml_env\Scripts\activate.bat')
except Exception as e:
    print(f'❌ ERROR: {e}')
    sys.exit(1)
"

if errorlevel 1 (
    echo ❌ Verificación fallida en entorno virtual
    pause
    exit /b 1
)

echo.
echo ✅ INSTALACIÓN COMPLETA EN ENTORNO VIRTUAL
echo.
echo 📋 INSTRUCCIONES DE USO:
echo    1. Para activar entorno: call nexus_ml_env\Scripts\activate.bat
echo    2. Para ejecutar scripts: python debug_training.py
echo    3. Para entrenar: python train_cortex.py --candles 5000
echo.
echo 💡 El entorno virtual evita conflictos con otras instalaciones
echo.
pause
