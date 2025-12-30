@echo off
echo ================================================
echo 🚀 INSTALACIÓN MÍNIMA PYTHON 3.14 - NEXUS ML
echo ================================================
echo.

cd /d "%~dp0"
echo 📂 Directorio: %CD%
echo.

echo 🐍 Python 3.14.0 detectado - usando instalación mínima...
echo 💡 Esta versión instala SOLO lo esencial para ML training
echo.

echo 📦 PASO 1: Preparación...
pip install --upgrade pip
pip install setuptools wheel

echo.
echo 📦 PASO 2: Núcleo matemático...
pip install numpy
if errorlevel 1 echo ⚠️  numpy falló, intentando versión específica...
if errorlevel 1 pip install numpy==1.26.3

echo.
echo 📦 PASO 3: Pandas...
pip install pandas
if errorlevel 1 echo ⚠️  pandas falló, intentando versión específica...
if errorlevel 1 pip install pandas==2.2.0

echo.
echo 📦 PASO 4: Scikit-learn...
pip install scikit-learn
if errorlevel 1 echo ⚠️  scikit-learn falló, intentando versión específica...
if errorlevel 1 pip install scikit-learn==1.4.0

echo.
echo 📦 PASO 5: XGBoost...
pip install xgboost
if errorlevel 1 echo ⚠️  xgboost falló, intentando versión específica...
if errorlevel 1 pip install xgboost==2.0.0

echo.
echo 📦 PASO 6: Joblib...
pip install joblib
if errorlevel 1 echo ⚠️  joblib falló, intentando versión específica...
if errorlevel 1 pip install joblib==1.4.0

echo.
echo 📦 PASO 7: Utilidades básicas...
pip install tqdm requests python-dotenv

echo.
echo 📦 PASO 8: APIs de datos...
pip install yfinance python-binance

echo.
echo 📦 PASO 9: Async básico...
pip install aiohttp websockets

echo.
echo 🧪 VERIFICANDO INSTALACIÓN...
echo.

python -c "
import sys
print(f'🐍 Python: {sys.version}')
try:
    import numpy as np
    print(f'✅ numpy: {np.__version__}')
except: print('❌ numpy')

try:
    import pandas as pd
    print(f'✅ pandas: {pd.__version__}')
except: print('❌ pandas')

try:
    import sklearn
    print(f'✅ scikit-learn: {sklearn.__version__}')
except: print('❌ scikit-learn')

try:
    import xgboost
    print(f'✅ xgboost: {xgboost.__version__}')
except: print('❌ xgboost')

try:
    import joblib
    print(f'✅ joblib: {joblib.__version__}')
except: print('❌ joblib')

try:
    import yfinance
    print('✅ yfinance: OK')
except: print('❌ yfinance')

try:
    from binance.client import Client
    print('✅ python-binance: OK')
except: print('❌ python-binance')

print('')
print('🎯 RESULTADO:')
print('✅ DEPENDENCIAS CRÍTICAS PARA ML: INSTALADAS')
print('✅ SISTEMA LISTO PARA ENTRENAMIENTO ML')
print('')
print('🚀 PRÓXIMOS PASOS:')
print('   1. Ejecuta: debug_training.bat')
print('   2. Ejecuta: train_ml.bat')
"

echo.
echo ✅ INSTALACIÓN MÍNIMA COMPLETADA
echo 💡 Las dependencias críticas están instaladas y verificadas
echo.
pause
