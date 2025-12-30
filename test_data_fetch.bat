@echo off
echo ================================================
echo 🧪 TEST - DESCARGA DE DATOS CON PROGRESO
echo ================================================
echo.

cd /d "%~dp0"

echo 🔍 Probando descarga de datos con progreso detallado...
echo.

python -c "
from debug_training import test_data_fetch
try:
    test_data_fetch()
    print('✅ Test completado exitosamente')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo.
echo 📋 Test finalizado
pause
