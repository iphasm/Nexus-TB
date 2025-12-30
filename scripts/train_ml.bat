@echo off
echo ================================================
echo 🧠 NEXUS CORTEX ML TRAINING - Windows Launcher
echo ================================================
echo.

cd /d "%~dp0"
echo 📂 Directorio de trabajo: %CD%
echo.

echo 📊 CONFIGURACIÓN DEL ENTRENAMIENTO:
echo.
echo 💡 Intervalo temporal: 15 minutos
echo 💡 Recomendaciones:
echo    • 5000 velas = ~5.2 días de datos
echo    • 15000 velas = ~15.6 días de datos
echo    • 35000 velas = ~36.5 días de datos
echo.

set /p candles="⚡ Cantidad de velas a analizar (ej: 15000): "

if "%candles%"=="" (
    echo ⚠️ No se especificó cantidad. Usando default: 15000
    set candles=15000
)

echo.
echo 🚀 Iniciando entrenamiento ML...
echo 📊 Velas configuradas: %candles%
echo 💻 Ejecutando: python train_cortex.py --candles %candles%
echo 💡 Presiona Ctrl+C para cancelar en cualquier momento
echo.

python train_cortex.py --candles %candles%

set exitcode=%errorlevel%
echo.
if %exitcode% equ 0 (
    echo ✅ Proceso finalizado exitosamente
) else (
    echo ❌ Proceso terminó con código de error: %exitcode%
)

echo.
echo 📋 RESUMEN:
echo    • Velas procesadas: %candles%
echo    • Modelo guardado en: ml_model.pkl
echo    • Scaler guardado en: scaler.pkl
echo.
echo 👉 Para activar ML en el bot: restart bot or run: /ml_mode on
echo.
pause
