# Instalación de Dependencias - Nexus ML Training
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "📦 INSTALACIÓN DE DEPENDENCIAS - NEXUS ML" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "📂 Directorio de trabajo: $PWD" -ForegroundColor White
Write-Host ""

# Verificar Python
Write-Host "🔍 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "💡 Instala Python desde: https://python.org" -ForegroundColor Cyan
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar pip
Write-Host "🔍 Verificando pip..." -ForegroundColor Yellow
try {
    $pipVersion = python -m pip --version 2>&1
    Write-Host "✅ pip encontrado: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: pip no está disponible" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""

# Actualizar pip
Write-Host "📦 Actualizando pip..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip
    Write-Host "✅ pip actualizado" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Advertencia: No se pudo actualizar pip, continuando..." -ForegroundColor Yellow
}

Write-Host ""

# Instalar dependencias
Write-Host "📦 Instalando dependencias desde requirements.txt..." -ForegroundColor Yellow
Write-Host "💡 Esto puede tomar varios minutos..." -ForegroundColor White
Write-Host ""

try {
    python -m pip install -r requirements.txt
    Write-Host "" -ForegroundColor White
    Write-Host "✅ Todas las dependencias instaladas exitosamente!" -ForegroundColor Green
} catch {
    Write-Host "" -ForegroundColor White
    Write-Host "❌ ERROR: Falló la instalación de algunas dependencias" -ForegroundColor Red
    Write-Host "💡 Posibles soluciones:" -ForegroundColor Cyan
    Write-Host "   • Verifica tu conexión a internet" -ForegroundColor White
    Write-Host "   • Ejecuta como administrador" -ForegroundColor White
    Write-Host "   • Instala Visual Studio Build Tools si faltan compiladores" -ForegroundColor White
    Write-Host "   • O instala manualmente: pip install pandas numpy scikit-learn xgboost" -ForegroundColor White
    Write-Host "" -ForegroundColor White
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""

# Probar instalación
Write-Host "🧪 Probando instalación..." -ForegroundColor Yellow
try {
    python -c "import pandas, numpy, sklearn, xgboost, joblib, tqdm, yfinance, pandas_ta; print('✅ Todas las importaciones exitosas')"
    Write-Host "✅ Todas las importaciones funcionan correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Algunas importaciones fallan" -ForegroundColor Red
    Write-Host "Detalles: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

Write-Host "🎯 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "   1. Ejecuta: debug_training.bat (para verificar funcionamiento)" -ForegroundColor White
Write-Host "   2. Ejecuta: train_ml.bat (para entrenar el modelo)" -ForegroundColor White
Write-Host ""

Read-Host "Presiona Enter para salir"
