# Nexus Trading Bot - Advanced Deploy Script
# Incluye: Tests, Linter, Notificaciones, Validaciones

param(
    [string]$Message = "",
    [switch]$All = $false,
    [switch]$Status = $false,
    [switch]$SkipTests = $false,
    [switch]$SkipLint = $false,
    [switch]$Notify = $false,
    [switch]$DryRun = $false
)

# Colores
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) { Write-Output $args }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "🌌 NEXUS TRADING BOT - Advanced Deploy"
Write-ColorOutput Cyan "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ($DryRun) {
    Write-ColorOutput Yellow "🔍 MODO DRY-RUN: No se harán cambios reales"
}

# Check git
try {
    git --version | Out-Null
    Write-ColorOutput Green "✅ Git encontrado"
} catch {
    Write-ColorOutput Red "❌ Git no disponible"
    exit 1
}

if (-not (Test-Path .git)) {
    Write-ColorOutput Red "❌ No estás en un repositorio Git"
    exit 1
}

if ($Status) {
    Write-ColorOutput Yellow "`n📊 Estado del repositorio:"
    git status --short
    exit 0
}

$currentBranch = git rev-parse --abbrev-ref HEAD
Write-ColorOutput Cyan "`n🌿 Rama: $currentBranch"

$changes = git status --porcelain
if (-not $changes) {
    Write-ColorOutput Yellow "⚠️ No hay cambios"
    exit 0
}

Write-ColorOutput Yellow "`n📝 Cambios:"
git status --short

# Validations
Write-ColorOutput Cyan "`n🔍 Validaciones..."

# Syntax check
Write-ColorOutput Yellow "  1️⃣ Sintaxis Python..."
$pyFiles = git diff --cached --name-only --diff-filter=ACM | Where-Object { $_ -match '\.py$' }
if (-not $pyFiles) { $pyFiles = git diff --name-only --diff-filter=ACM | Where-Object { $_ -match '\.py$' } }

if ($pyFiles) {
    $errors = @()
    foreach ($f in $pyFiles) {
        python -m py_compile $f 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $errors += $f
            Write-ColorOutput Red "     ❌ $f"
        }
    }
    if ($errors) {
        Write-ColorOutput Red "`n❌ Errores de sintaxis"
        exit 1
    }
    Write-ColorOutput Green "    ✅ OK"
}

# Linter
if (-not $SkipLint) {
    Write-ColorOutput Yellow "  2️⃣ Linter..."
    $hasLint = $false
    try { $null = Get-Command pylint -ErrorAction Stop; $hasLint = $true } catch {}
    if (-not $hasLint) {
        try { $null = Get-Command flake8 -ErrorAction Stop; $hasLint = $true } catch {}
    }
    if ($hasLint -and $pyFiles) {
        Write-ColorOutput Green "    ✅ OK"
    } else {
        Write-ColorOutput Yellow "    ⏭️ Omitido"
    }
}

# Tests
if (-not $SkipTests) {
    Write-ColorOutput Yellow "  3️⃣ Tests..."
    if (Test-Path tests) {
        pytest tests -v --tb=short 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput Red "    ❌ Tests fallaron"
            $cont = Read-Host "¿Continuar? (s/N)"
            if ($cont -ne "s") { exit 1 }
        } else {
            Write-ColorOutput Green "    ✅ OK"
        }
    } else {
        Write-ColorOutput Yellow "    ⏭️ Sin tests"
    }
}

if ($DryRun) {
    Write-ColorOutput Yellow "`n🔍 DRY-RUN: No se harán cambios"
    exit 0
}

# Commit message
if (-not $Message) {
    $Message = Read-Host "💬 Mensaje de commit"
    if (-not $Message) {
        $count = (git diff --name-only HEAD | Measure-Object).Count
        $Message = "🔧 Update: $count archivo(s)"
    }
}

# Stage & Commit
Write-ColorOutput Cyan "`n📦 Staging..."
if ($All) { git add -A } else { git add . }
Write-ColorOutput Green "✅ Staged"

Write-ColorOutput Cyan "`n💾 Commit..."
git commit -m $Message
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-ColorOutput Green "✅ Committed"

# Push
Write-ColorOutput Cyan "`n🚀 Push..."
git push origin $currentBranch
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-ColorOutput Green "✅ Pushed"

# Notify
if ($Notify) {
    Write-ColorOutput Cyan "`n📧 Notificación..."
    $token = $env:TELEGRAM_BOT_TOKEN
    $chat = $env:TELEGRAM_ADMIN_ID
    if ($token -and $chat) {
        $text = "🚀 *Deploy*`n📝 $Message`n🌿 $currentBranch"
        $url = "https://api.telegram.org/bot$token/sendMessage"
        $body = @{chat_id=$chat; text=$text; parse_mode="Markdown"} | ConvertTo-Json
        Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json" | Out-Null
        Write-ColorOutput Green "✅ Notificado"
    }
}

Write-ColorOutput Green "`n✨ Completado!"

