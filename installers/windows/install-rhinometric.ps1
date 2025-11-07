# ============================================
# Rhinometric v2.5.0 - Windows PowerShell Installer
# Requires: Windows 10/11, PowerShell 5.1+, Docker Desktop
# © 2025 Rhinometric. All rights reserved.
# ============================================

#Requires -RunAsAdministrator

$VERSION = "2.5.0"
$REPO_URL = "https://github.com/Rafael2712/mi-proyecto"
$INSTALL_DIR = "C:\Program Files\Rhinometric"
$DATA_DIR = "C:\ProgramData\Rhinometric"
$LOG_FILE = "C:\ProgramData\Rhinometric\install.log"

# Funciones de log
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host "[INFO] $Message" -ForegroundColor Green
    Add-Content -Path $LOG_FILE -Value $logMessage
}

function Write-Error-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [ERROR] $Message"
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    Add-Content -Path $LOG_FILE -Value $logMessage
}

function Write-Warning-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [WARNING] $Message"
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
    Add-Content -Path $LOG_FILE -Value $logMessage
}

# Inicializar log
New-Item -ItemType Directory -Force -Path (Split-Path $LOG_FILE) | Out-Null

# Banner
Clear-Host
Write-Host @"
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🦏 RHINOMETRIC INSTALLER v$VERSION                   ║
    ║        Observability Platform - Windows Edition          ║
    ║        © 2025 Rhinometric. All rights reserved.          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Blue

Write-Log "Starting Rhinometric v$VERSION installation on Windows"

# Verificar Docker Desktop
Write-Log "Checking Docker Desktop..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error-Log "Docker Desktop not installed"
    Write-Host ""
    Write-Host "Please install Docker Desktop first:" -ForegroundColor Yellow
    Write-Host "https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

try {
    $dockerVersion = docker --version
    Write-Log "Docker found: $dockerVersion"
} catch {
    Write-Error-Log "Docker is not running"
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Verificar Docker Compose
Write-Log "Checking Docker Compose..."
try {
    $composeVersion = docker compose version
    Write-Log "Docker Compose found: $composeVersion"
} catch {
    Write-Error-Log "Docker Compose not found"
    exit 1
}

# Verificar Git
Write-Log "Checking Git..."
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warning-Log "Git not found, installing..."
    winget install --id Git.Git -e --source winget --silent
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Verificar requisitos del sistema
Write-Log "Checking system requirements..."

# RAM: 8GB mínimo
$totalRAM = [Math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
if ($totalRAM -lt 8) {
    Write-Error-Log "Insufficient RAM: ${totalRAM}GB (minimum 8GB required)"
    exit 1
}
Write-Log "RAM: ${totalRAM}GB ✓"

# Disco: 50GB mínimo
$freeDisk = [Math]::Round((Get-PSDrive C).Free / 1GB, 2)
if ($freeDisk -lt 50) {
    Write-Error-Log "Insufficient disk space: ${freeDisk}GB (minimum 50GB required)"
    exit 1
}
Write-Log "Free disk space: ${freeDisk}GB ✓"

# Crear directorios
Write-Log "Creating directories..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\postgres" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\grafana" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\prometheus" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\loki" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\licenses" | Out-Null
New-Item -ItemType Directory -Force -Path "$DATA_DIR\backups" | Out-Null
Write-Log "Directories created ✓"

# Descargar configuración
Write-Log "Downloading Rhinometric from GitHub..."
Set-Location $INSTALL_DIR

if (Test-Path ".git") {
    Write-Log "Existing repository found, updating..."
    git fetch origin main --quiet
    git reset --hard origin/main --quiet
} else {
    Write-Log "Cloning repository..."
    git clone --depth 1 --branch main "$REPO_URL.git" . --quiet 2>&1 | Out-File -Append $LOG_FILE
}

Set-Location "infrastructure\mi-proyecto"
Write-Log "Files downloaded ✓"

# Generar .env con valores seguros
Write-Log "Generating secure configuration..."

# Función para generar password aleatorio
function New-RandomPassword {
    $bytes = New-Object Byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes).Substring(0, 25) -replace '[+/=]', ''
}

$postgresPassword = New-RandomPassword
$redisPassword = New-RandomPassword
$jwtSecret = New-RandomPassword + (New-RandomPassword).Substring(0, 15)

$envContent = @"
# Rhinometric v$VERSION - Generated Configuration
# Generated: $(Get-Date)

# SMTP Configuration (COMPLETE AFTER INSTALLATION)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=licenses@rhinometric.io

# Database (AUTO-GENERATED)
POSTGRES_PASSWORD=$postgresPassword
REDIS_PASSWORD=$redisPassword
JWT_SECRET=$jwtSecret

# License
LICENSE_DURATION_DAYS=180

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin

# Retention Policies
PROMETHEUS_RETENTION_DAYS=15d
PROMETHEUS_RETENTION_SIZE=10GB
LOKI_RETENTION_DAYS=168h
TEMPO_RETENTION_DAYS=72h
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8 -NoNewline
Write-Log "Configuration generated ✓"
Write-Warning-Log "Passwords saved in: $INSTALL_DIR\infrastructure\mi-proyecto\.env"

# Construir imágenes
Write-Log "Building Docker images..."
Write-Log "⏳ This may take 5-10 minutes depending on your connection..."
docker compose -f docker-compose.yml -f docker-compose.override.yml build 2>&1 | Out-File -Append $LOG_FILE

# Iniciar servicios
Write-Log "Starting Rhinometric services..."
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d 2>&1 | Out-File -Append $LOG_FILE

# Esperar servicios
Write-Log "⏳ Waiting for services to be ready (60 seconds)..."
for ($i = 1; $i -le 6; $i++) {
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 10
}
Write-Host ""

# Verificar servicios
Write-Log "Verifying service health..."
$services = @(
    @{Port=3000; Name="Grafana"},
    @{Port=9090; Name="Prometheus"},
    @{Port=3100; Name="Loki"},
    @{Port=3200; Name="Tempo"},
    @{Port=8090; Name="License Server"},
    @{Port=8001; Name="Dashboard Builder"},
    @{Port=5432; Name="PostgreSQL"},
    @{Port=6379; Name="Redis"}
)

$failed = 0
foreach ($service in $services) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $service.Port -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($connection) {
            Write-Log "$($service.Name) (port $($service.Port)) ✓"
        } else {
            Write-Warning-Log "$($service.Name) (port $($service.Port)) not responding"
            $failed++
        }
    } catch {
        Write-Warning-Log "$($service.Name) (port $($service.Port)) not responding"
        $failed++
    }
}

# Crear script de uninstall
$uninstallScript = @'
# Rhinometric Uninstaller for Windows
#Requires -RunAsAdministrator

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║              🗑️  RHINOMETRIC UNINSTALLER                  ║" -ForegroundColor Red
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

$confirm = Read-Host "This will remove all Rhinometric data and containers. Type 'YES' to continue"

if ($confirm -ne "YES") {
    Write-Host "Uninstall cancelled."
    exit 0
}

Write-Host "[1/4] Stopping services..." -ForegroundColor Green
Set-Location "C:\Program Files\Rhinometric\infrastructure\mi-proyecto"
docker compose down -v 2>$null

Write-Host "[2/4] Removing images..." -ForegroundColor Green
docker images | Select-String "rhinometric" | ForEach-Object { 
    $imageId = ($_ -split '\s+')[2]
    docker rmi -f $imageId 2>$null
}

Write-Host "[3/4] Removing data..." -ForegroundColor Green
Remove-Item -Path "C:\ProgramData\Rhinometric" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[4/4] Removing installation..." -ForegroundColor Green
Set-Location C:\
Remove-Item -Path "C:\Program Files\Rhinometric" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ Rhinometric has been completely uninstalled" -ForegroundColor Green
'@

$uninstallScript | Out-File -FilePath "$INSTALL_DIR\uninstall.ps1" -Encoding UTF8

# Resumen
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
if ($failed -eq 0) {
    Write-Host "║              ✅ INSTALLATION COMPLETED                     ║" -ForegroundColor Green
} else {
    Write-Host "║         ⚠️  INSTALLATION WITH WARNINGS ($failed services)    ║" -ForegroundColor Yellow
}
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Log "Rhinometric v$VERSION installed in: $INSTALL_DIR"
Write-Log "Data in: $DATA_DIR"
Write-Host ""
Write-Host "📊 ACCESS TO PLATFORM:" -ForegroundColor Blue
Write-Host "  • Grafana:          http://localhost:3000"
Write-Host "  • Prometheus:       http://localhost:9090"
Write-Host "  • License Server:   http://localhost:8090"
Write-Host "  • Dashboard Builder: http://localhost:8001"
Write-Host ""
Write-Host "🔐 INITIAL CREDENTIALS:" -ForegroundColor Blue
Write-Host "  • Username: " -NoNewline
Write-Host "admin" -ForegroundColor Green
Write-Host "  • Password: " -NoNewline
Write-Host "admin " -ForegroundColor Green -NoNewline
Write-Host "(⚠️  CHANGE ON FIRST LOGIN)" -ForegroundColor Yellow
Write-Host ""
Write-Host "📧 CONFIGURE SMTP (OPTIONAL):" -ForegroundColor Blue
Write-Host "  Edit: " -NoNewline
Write-Host "$INSTALL_DIR\infrastructure\mi-proyecto\.env" -ForegroundColor Green
Write-Host "  Variables: SMTP_USER, SMTP_PASSWORD"
Write-Host "  Then restart: docker compose restart rhinometric-license-server-v2"
Write-Host ""
Write-Host "📚 NEXT STEPS:" -ForegroundColor Blue
Write-Host "  1. Access Grafana in your browser"
Write-Host "  2. Generate a license in License Server"
Write-Host "  3. Read documentation: https://github.com/Rafael2712/mi-proyecto/wiki"
Write-Host ""
Write-Host "🛠️  USEFUL COMMANDS:" -ForegroundColor Blue
Write-Host "  • View logs:     docker compose logs -f"
Write-Host "  • Restart:       docker compose restart"
Write-Host "  • Stop:          docker compose down"
Write-Host "  • View status:   docker compose ps"
Write-Host "  • Uninstall:     PowerShell -File '$INSTALL_DIR\uninstall.ps1'"
Write-Host ""

if ($failed -gt 0) {
    Write-Host "⚠️  $failed service(s) did not respond" -ForegroundColor Yellow
    Write-Host "   Check logs: docker compose logs" -ForegroundColor Yellow
    Write-Host ""
}

Write-Log "Installation completed. Log saved in: $LOG_FILE"
Write-Log "Enjoy Rhinometric! 🦏"

exit 0
