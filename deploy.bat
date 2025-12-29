@echo off
REM Nexus Trading Bot - Auto Deploy Script (Batch)
REM Automatiza: git add, commit, push a GitHub
REM Railway detecta automáticamente el push y despliega

setlocal enabledelayedexpansion

echo.
echo 🌌 NEXUS TRADING BOT - Auto Deploy
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git no está instalado o no está en PATH
    exit /b 1
)
echo ✅ Git encontrado

REM Check if we're in a git repository
if not exist .git (
    echo ❌ No estás en un repositorio Git
    exit /b 1
)

REM Get current branch
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i
echo.
echo 🌿 Rama actual: %CURRENT_BRANCH%

REM Check for changes
git status --porcelain >nul 2>&1
if errorlevel 1 (
    echo ⚠️ No hay cambios para commitear
    exit /b 0
)

REM Show changes
echo.
echo 📝 Cambios detectados:
git status --short

REM Get commit message
set /p COMMIT_MSG="💬 Ingresa el mensaje de commit (o presiona Enter para auto-generar): "

if "!COMMIT_MSG!"=="" (
    REM Auto-generate message
    for /f %%i in ('git diff --name-only HEAD ^| find /c /v ""') do set FILE_COUNT=%%i
    set COMMIT_MSG=🔧 Update: !FILE_COUNT! archivo(s) modificado(s)
    echo 📝 Mensaje auto-generado: !COMMIT_MSG!
)

REM Stage changes
echo.
echo 📦 Agregando cambios...
git add .
if errorlevel 1 (
    echo ❌ Error al agregar cambios
    exit /b 1
)
echo ✅ Cambios agregados

REM Commit
echo.
echo 💾 Creando commit...
git commit -m "!COMMIT_MSG!"
if errorlevel 1 (
    echo ❌ Error al crear commit
    exit /b 1
)
echo ✅ Commit creado exitosamente

REM Push
echo.
echo 🚀 Enviando a GitHub...
git push origin %CURRENT_BRANCH%
if errorlevel 1 (
    echo ❌ Error al hacer push
    echo 💡 Intenta manualmente: git push origin %CURRENT_BRANCH%
    exit /b 1
)

echo.
echo ✅ Push exitoso a GitHub!
echo 🔄 Railway detectará el push y desplegará automáticamente
echo 💡 Monitorea el despliegue en: https://railway.app
echo.
echo ✨ Proceso completado exitosamente!
echo.

endlocal

