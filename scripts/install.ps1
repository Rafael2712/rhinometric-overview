# ═══════════════════════════════════════════════════════════════════════════
#  RHINOMETRIC v2.1.0 - ONE-COMMAND INSTALLER (Windows PowerShell)
# ═══════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " 🦏 RHINOMETRIC v2.1.0 - Enterprise Observability Platform" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ───────────────────────────────────────────────────────────────────────────
# 1. VALIDATE PREREQUISITES
# ───────────────────────────────────────────────────────────────────────────
Write-Host "📋 [1/5] Validando prerequisitos..." -ForegroundColor Yellow

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ERROR: Docker no está instalado" -ForegroundColor Red
    Write-Host "   Instala Docker Desktop desde: https://docker.com/get-started" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command "docker compose" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ERROR: Docker Compose no está disponible" -ForegroundColor Red
    Write-Host "   Actualiza Docker a versión 24.0+ que incluye Compose v2" -ForegroundColor Red
    exit 1
}

$dockerVersion = (docker --version) -replace '.*Docker version (\d+\.\d+).*','$1'
Write-Host "   ✅ Docker $dockerVersion detectado" -ForegroundColor Green

# ───────────────────────────────────────────────────────────────────────────
# 2. SETUP ENVIRONMENT
# ───────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "⚙️  [2/5] Configurando entorno..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "   ✅ Archivo .env creado desde .env.example" -ForegroundColor Green
        Write-Host "   ⚠️  IMPORTANTE: Edita .env y configura tus credenciales" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "   Presiona Enter para continuar con valores por defecto o Ctrl+C para editar primero"
    } else {
        Write-Host "   ❌ ERROR: No se encontró .env.example" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ Archivo .env existente (no se sobrescribe)" -ForegroundColor Green
}

# ───────────────────────────────────────────────────────────────────────────
# 3. CREATE DATA DIRECTORIES
# ───────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "📁 [3/5] Creando directorios de datos..." -ForegroundColor Yellow

$dataDir = "$env:USERPROFILE\rhinometric_data_v2.1"
$dirs = @("grafana", "prometheus", "loki", "tempo", "postgres", "redis", "license-server")

foreach ($dir in $dirs) {
    $fullPath = Join-Path $dataDir $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}

Write-Host "   ✅ Directorios creados en: $dataDir" -ForegroundColor Green

# ───────────────────────────────────────────────────────────────────────────
# 4. START SERVICES
# ───────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "🚀 [4/5] Iniciando servicios Docker..." -ForegroundColor Yellow

Set-Location deploy
docker compose -f docker-compose.yml up -d

Write-Host "   ✅ Contenedores iniciados" -ForegroundColor Green

# ───────────────────────────────────────────────────────────────────────────
# 5. VERIFY INSTALLATION
# ───────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "🔍 [5/5] Verificando instalación..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$runningContainers = (docker ps --format '{{.Names}}' | Select-String "rhinometric" | Measure-Object).Count
Write-Host "   ✅ Contenedores activos: $runningContainers" -ForegroundColor Green

# ───────────────────────────────────────────────────────────────────────────
# SUCCESS
# ───────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host " ✅ INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📍 ACCESOS:" -ForegroundColor Cyan
Write-Host "   • Grafana:        http://localhost:3000"
Write-Host "   • Prometheus:     http://localhost:9090"
Write-Host "   • Loki:           http://localhost:3100"
Write-Host "   • License Server: http://localhost:5000"
Write-Host "   • License UI:     http://localhost:8092"
Write-Host ""
Write-Host "🔐 CREDENCIALES GRAFANA:" -ForegroundColor Cyan
Write-Host "   Usuario:    admin (ver .env para cambiar)"
Write-Host "   Contraseña: Ver archivo .env"
Write-Host ""
Write-Host "📚 DOCUMENTACIÓN: https://github.com/Rafael2712/rhinometric-overview"
Write-Host "💬 SOPORTE: rafael.canelon@rhinometric.com"
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
