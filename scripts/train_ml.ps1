# Nexus Cortex ML Training Launcher
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🧠 NEXUS CORTEX ML TRAINING - PowerShell Launcher" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "📊 CONFIGURACIÓN DEL ENTRENAMIENTO:" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Intervalo temporal: 15 minutos" -ForegroundColor White
Write-Host "💡 Recomendaciones:" -ForegroundColor White
Write-Host "   • 5000 velas = ~5.2 días de datos" -ForegroundColor Gray
Write-Host "   • 15000 velas = ~15.6 días de datos" -ForegroundColor Gray
Write-Host "   • 35000 velas = ~36.5 días de datos" -ForegroundColor Gray
Write-Host ""

$candles = Read-Host "⚡ Cantidad de velas a analizar (ej: 15000)"

if ([string]::IsNullOrWhiteSpace($candles)) {
    $candles = "15000"
    Write-Host "❌ No se especificó cantidad. Usando default: 15000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Iniciando entrenamiento ML..." -ForegroundColor Green
Write-Host "📊 Velas configuradas: $candles" -ForegroundColor White
Write-Host "💡 Presiona Ctrl+C para cancelar en cualquier momento" -ForegroundColor Yellow
Write-Host ""

try {
    & python train_cortex.py --candles $candles
    Write-Host ""
    Write-Host "✅ Proceso finalizado exitosamente" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ Error ejecutando el script: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "📋 RESUMEN:" -ForegroundColor Cyan
    Write-Host "   • Velas procesadas: $candles" -ForegroundColor White
    Write-Host "   • Modelo guardado en: nexus_system\memory_archives\ml_model.pkl" -ForegroundColor White
    Write-Host "   • Scaler guardado en: nexus_system\memory_archives\scaler.pkl" -ForegroundColor White
    Write-Host ""
    Write-Host "👉 Para activar ML en el bot: restart bot or run: /ml_mode on" -ForegroundColor Green
    Write-Host ""
    Read-Host "Presiona Enter para salir"
}
