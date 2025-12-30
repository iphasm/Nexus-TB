@echo off
echo ================================================
echo 🎯 EVALUACIÓN COMPLETA DEL SISTEMA ML
echo ================================================
echo.
echo Selecciona el tipo de evaluación a ejecutar:
echo.
echo [1] Validación Walk-Forward (Análisis temporal)
echo [2] Evaluación de Rendimiento (Análisis completo)
echo [3] Ambas evaluaciones (Completo)
echo [4] Análisis rápido de modelo actual
echo.

set /p choice="Elige una opción (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Ejecutando Validación Walk-Forward...
    echo 💡 Esta evaluación puede tomar 5-15 minutos
    echo.
    python src/ml/walk_forward_validation.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 🚀 Ejecutando Evaluación de Rendimiento...
    echo 💡 Esta evaluación puede tomar 3-8 minutos
    echo.
    python src/ml/performance_evaluation.py
    goto end
)

if "%choice%"=="3" (
    echo.
    echo 🚀 Ejecutando evaluación COMPLETA...
    echo 💡 Ambas evaluaciones pueden tomar 10-25 minutos
    echo.
    echo Paso 1: Validación Walk-Forward
    python src/ml/walk_forward_validation.py
    echo.
    echo Paso 2: Evaluación de Rendimiento
    python src/ml/performance_evaluation.py
    goto end
)

if "%choice%"=="4" (
    echo.
    echo 🚀 Ejecutando análisis rápido...
    echo 💡 Análisis básico del modelo actual
    echo.
    python src/ml/analyze_features.py
    goto end
)

echo ❌ Opción inválida
goto end

:end
echo.
echo ✅ Evaluación completada
echo 📁 Resultados guardados en carpeta 'results/'
echo.
pause
