# Nexus Trading Bot - Auto Deploy Script (PowerShell)
# Automatiza: git add, commit, push a GitHub
# Railway detecta automáticamente el push y despliega

param(
    [string]$Message = "",
    [switch]$All = $false,
    [switch]$Status = $false,
    [switch]$SkipTests = $false,
    [switch]$SkipLint = $false,
    [switch]$Notify = $false
)

# Colores para output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "🌌 NEXUS TRADING BOT - Auto Deploy"
Write-ColorOutput Cyan "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if git is available
try {
    $gitVersion = git --version
    Write-ColorOutput Green "✅ Git encontrado: $gitVersion"
} catch {
    Write-ColorOutput Red "❌ Git no está instalado o no está en PATH"
    exit 1
}

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-ColorOutput Red "❌ No estás en un repositorio Git"
    exit 1
}

# Show status if requested
if ($Status) {
    Write-ColorOutput Yellow "`n📊 Estado del repositorio:"
    git status --short
    exit 0
}

# Get current branch
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-ColorOutput Cyan "`n🌿 Rama actual: $currentBranch"

# Check for changes
$changes = git status --porcelain
if (-not $changes) {
    Write-ColorOutput Yellow "⚠️ No hay cambios para commitear"
    exit 0
}

# Show changes
Write-ColorOutput Yellow "`n📝 Cambios detectados:"
git status --short

# Get commit message
if (-not $Message) {
    Write-ColorOutput Cyan "`n💬 Ingresa el mensaje de commit (o presiona Enter para auto-generar):"
    $Message = Read-Host
}

if (-not $Message) {
    # Auto-generate message based on changes
    $changedFiles = git diff --name-only HEAD
    $fileCount = ($changedFiles | Measure-Object).Count
    
    $Message = "🔧 Update: $fileCount archivo(s) modificado(s)"
    
    # Try to detect what was changed
    if ($changedFiles -match "nexus_bridge|adapter") {
        $Message += " [Bridge/Adapters]"
    }
    if ($changedFiles -match "trading_manager") {
        $Message += " [Trading]"
    }
    if ($changedFiles -match "cortex|strategy") {
        $Message += " [Strategies]"
    }
    if ($changedFiles -match "handler|command") {
        $Message += " [Handlers]"
    }
    
    Write-ColorOutput Yellow "📝 Mensaje auto-generado: $Message"
}

# Pre-deploy validations
Write-ColorOutput Cyan "`n🔍 Ejecutando validaciones pre-deploy..."

# 0. Backup Critical Files
Write-ColorOutput Yellow "  0️⃣ Creando backup de archivos críticos..."
$backupDir = "backups"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = Join-Path $backupDir "backup_$timestamp"

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

# Files to backup
$criticalFiles = @(
    "system_directive.py",
    "nexus_loader.py",
    ".env.example",
    "railway.json",
    "requirements.txt"
)

# Directories to backup
$criticalDirs = @(
    "nexus_system\core",
    "nexus_system\cortex",
    "servos"
)

$backedUp = 0
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        $dest = Join-Path $backupPath $file
        $destDir = Split-Path $dest -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item $file $dest -Force
        $backedUp++
    }
}

foreach ($dir in $criticalDirs) {
    if (Test-Path $dir) {
        $dest = Join-Path $backupPath $dir
        Copy-Item $dir $dest -Recurse -Force
        $backedUp++
    }
}

if ($backedUp -gt 0) {
    Write-ColorOutput Green "    ✅ Backup creado: $backupPath ($backedUp items)"
    # Keep only last 5 backups
    Get-ChildItem $backupDir -Directory | Sort-Object CreationTime -Descending | Select-Object -Skip 5 | Remove-Item -Recurse -Force
    Write-ColorOutput Yellow "    🧹 Limpieza: Manteniendo últimos 5 backups"
} else {
    Write-ColorOutput Yellow "    ⚠️ No se encontraron archivos para backup"
}

# 1. Dependency Check
Write-ColorOutput Yellow "  1️⃣ Verificando dependencias..."
if (Test-Path "requirements.txt") {
    $missingDeps = @()
    $requiredDeps = Get-Content "requirements.txt" | Where-Object { $_ -notmatch '^#' -and $_ -notmatch '^\s*$' } | ForEach-Object {
        ($_ -split '>=')[0].Trim().ToLower()
    }
    
    foreach ($dep in $requiredDeps) {
        if ($dep) {
            $result = python -m pip show $dep 2>&1
            if ($LASTEXITCODE -ne 0) {
                $missingDeps += $dep
            }
        }
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-ColorOutput Red "    ❌ Dependencias faltantes:"
        foreach ($dep in $missingDeps) {
            Write-ColorOutput Red "       - $dep"
        }
        Write-ColorOutput Yellow "    💡 Ejecuta: pip install -r requirements.txt"
        $continue = Read-Host "¿Continuar de todas formas? (s/N)"
        if ($continue -ne "s" -and $continue -ne "S") {
            exit 1
        }
    } else {
        Write-ColorOutput Green "    ✅ Todas las dependencias instaladas"
    }
} else {
    Write-ColorOutput Yellow "    ⏭️ requirements.txt no encontrado"
}

# 2. Python Syntax Check
Write-ColorOutput Yellow "  1️⃣ Verificando sintaxis Python..."
$pythonFiles = git diff --cached --name-only --diff-filter=ACM | Where-Object { $_ -match '\.py$' }
if ($pythonFiles) {
    $syntaxErrors = @()
    foreach ($file in $pythonFiles) {
        $result = python -m py_compile $file 2>&1
        if ($LASTEXITCODE -ne 0) {
            $syntaxErrors += $file
            Write-ColorOutput Red "     ❌ Error de sintaxis en: $file"
        }
    }
    if ($syntaxErrors.Count -gt 0) {
        Write-ColorOutput Red "`n❌ Errores de sintaxis detectados. Corrige antes de deployar."
        exit 1
    }
    Write-ColorOutput Green "    ✅ Sintaxis Python OK"
} else {
    Write-ColorOutput Yellow "    ⏭️ No hay archivos Python modificados"
}

# 3. Linter Check (optional)
if (-not $SkipLint) {
    Write-ColorOutput Yellow "  2️⃣ Verificando linter (opcional)..."
    # Check if pylint/flake8 is available
    $hasLinter = $false
    try {
        $null = Get-Command pylint -ErrorAction Stop
        $hasLinter = $true
    } catch {
        try {
            $null = Get-Command flake8 -ErrorAction Stop
            $hasLinter = $true
        } catch {
            Write-ColorOutput Yellow "    ⏭️ Linter no disponible (pylint/flake8)"
        }
    }
    
    if ($hasLinter -and $pythonFiles) {
        $lintErrors = 0
        foreach ($file in $pythonFiles) {
            $result = pylint --errors-only $file 2>&1
            if ($LASTEXITCODE -ne 0) {
                $lintErrors++
            }
        }
        if ($lintErrors -gt 0) {
            Write-ColorOutput Yellow "    ⚠️ Advertencias de linter encontradas (continuando...)"
        } else {
            Write-ColorOutput Green "    ✅ Linter OK"
        }
    }
}

# 4. Run Tests (optional)
if (-not $SkipTests) {
    Write-ColorOutput Yellow "  3️⃣ Ejecutando tests..."
    if (Test-Path "tests") {
        try {
            $testResult = pytest tests -v --tb=short 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput Red "`n❌ Tests fallaron. Revisa los errores arriba."
                Write-ColorOutput Yellow "💡 Usa -SkipTests para omitir tests"
                $continue = Read-Host "¿Continuar de todas formas? (s/N)"
                if ($continue -ne "s" -and $continue -ne "S") {
                    exit 1
                }
            } else {
                Write-ColorOutput Green "    ✅ Tests pasaron"
            }
        } catch {
            Write-ColorOutput Yellow "    ⚠️ pytest no disponible o tests fallaron (continuando...)"
        }
    } else {
        Write-ColorOutput Yellow "    ⏭️ Carpeta tests no encontrada"
    }
}

Write-ColorOutput Green "`n✅ Validaciones completadas"

# Stage changes
Write-ColorOutput Cyan "`n📦 Agregando cambios..."
if ($All) {
    git add -A
    Write-ColorOutput Green "✅ Todos los cambios agregados (incluyendo eliminados)"
} else {
    git add .
    Write-ColorOutput Green "✅ Cambios agregados"
}

# Commit
Write-ColorOutput Cyan "`n💾 Creando commit..."
try {
    git commit -m $Message
    Write-ColorOutput Green "✅ Commit creado exitosamente"
} catch {
    Write-ColorOutput Red "❌ Error al crear commit: $_"
    exit 1
}

# Push
Write-ColorOutput Cyan "`n🚀 Enviando a GitHub..."
try {
    git push origin $currentBranch
    Write-ColorOutput Green "`n✅ Push exitoso a GitHub!"
    Write-ColorOutput Cyan "🔄 Railway detectará el push y desplegará automáticamente"
    Write-ColorOutput Yellow "`n💡 Monitorea el despliegue en: https://railway.app"
    
    # Send notification if requested
    if ($Notify) {
        Write-ColorOutput Cyan "`n📧 Enviando notificación..."
        try {
            $telegramBotToken = $env:TELEGRAM_BOT_TOKEN
            $telegramChatId = $env:TELEGRAM_ADMIN_ID
            
            if ($telegramBotToken -and $telegramChatId) {
                $notificationText = "🚀 *Deploy Exitoso*`n`n" +
                                   "📝 Commit: $Message`n" +
                                   "🌿 Branch: $currentBranch`n" +
                                   "⏰ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" +
                                   "🔄 Railway desplegando automáticamente..."
                
                $url = "https://api.telegram.org/bot$telegramBotToken/sendMessage"
                $body = @{
                    chat_id = $telegramChatId
                    text = $notificationText
                    parse_mode = "Markdown"
                } | ConvertTo-Json
                
                Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json" | Out-Null
                Write-ColorOutput Green "✅ Notificación enviada a Telegram"
            } else {
                Write-ColorOutput Yellow "⚠️ Variables TELEGRAM_BOT_TOKEN o TELEGRAM_ADMIN_ID no configuradas"
            }
        } catch {
            Write-ColorOutput Yellow "⚠️ Error enviando notificación: $_"
        }
    }
} catch {
    Write-ColorOutput Red "`n❌ Error al hacer push: $_"
    Write-ColorOutput Yellow "💡 Intenta manualmente: git push origin $currentBranch"
    exit 1
}

Write-ColorOutput Green "`n✨ Proceso completado exitosamente!"

