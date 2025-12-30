@echo off
echo ================================================
echo 🧪 TEST - NEXUS CORTEX ML TRAINING
echo ================================================
echo.

cd /d "%~dp0"

echo 🧪 Ejecutando test con configuración mínima...
echo 📊 Configuración: 3 símbolos, 1000 velas (rápido)
echo.

python train_cortex.py --candles 1000 --symbols 3

echo.
echo ✅ Test completado
echo.
pause
