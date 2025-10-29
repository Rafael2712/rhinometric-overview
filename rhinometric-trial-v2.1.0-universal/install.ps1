# ============================================================================
# Rhinometric v2.1.0 - Quick Start Installer (Windows PowerShell)
# ============================================================================
# Description: One-command installer for Windows
# Checks prerequisites, creates .env, deploys full observability stack
# ============================================================================

$ErrorActionPreference = "Stop"

# Configuration
$RhinometricVersion = "2.1.0"
$ComposeFile = "docker-compose-v2.1.0.yml"
$EnvFile = ".env"
$EnvExample = ".env.example"
$MinDockerVersion = [version]"20.10.0"
$MinComposeVersion = [version]"2.0.0"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Header {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Rhinometric v$RhinometricVersion - Observability Platform           ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] " -NoNewline -ForegroundColor White
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ " -NoNewline -ForegroundColor Green
    Write-Host $Message
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ ERROR: " -NoNewline -ForegroundColor Red
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  WARNING: " -NoNewline -ForegroundColor Yellow
    Write-Host $Message
}

function Generate-SecurePassword {
    $bytes = New-Object byte[] 16
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes).Substring(0, 20) -replace '[/+=]', ''
}

# ============================================================================
# Prerequisite Checks
# ============================================================================

function Test-Docker {
    Write-Step "Checking Docker installation..."
    
    try {
        $dockerVersion = docker --version
        if ($dockerVersion -match '(\d+\.\d+\.\d+)') {
            $version = [version]$matches[1]
            Write-Success "Docker $version found"
            
            if ($version -lt $MinDockerVersion) {
                Write-Warning "Docker version $version is below recommended $MinDockerVersion"
            }
        }
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    # Check if Docker daemon is running
    try {
        docker info | Out-Null
        Write-Success "Docker daemon is running"
    }
    catch {
        Write-Error "Docker daemon is not running"
        Write-Host "Please start Docker Desktop and try again"
        exit 1
    }
}

function Test-DockerCompose {
    Write-Step "Checking Docker Compose..."
    
    try {
        $composeVersion = docker compose version --short
        Write-Success "Docker Compose $composeVersion found"
    }
    catch {
        Write-Error "Docker Compose v2 is not available"
        Write-Host "Please update Docker Desktop to get Compose v2"
        exit 1
    }
}

function Test-Ports {
    Write-Step "Checking port availability..."
    
    $RequiredPorts = @(3000, 5000, 5432, 6379, 8090, 8091, 8092, 9090, 9093)
    $PortsInUse = @()
    
    foreach ($Port in $RequiredPorts) {
        $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connection) {
            $PortsInUse += $Port
        }
    }
    
    if ($PortsInUse.Count -gt 0) {
        Write-Warning "The following ports are already in use: $($PortsInUse -join ', ')"
        $continue = Read-Host "These services may fail to start. Continue anyway? (y/N)"
        if ($continue -ne 'y' -and $continue -ne 'Y') {
            exit 1
        }
    }
    else {
        Write-Success "All required ports are available"
    }
}

function Test-DiskSpace {
    Write-Step "Checking disk space..."
    
    $drive = (Get-Location).Drive
    $freeSpace = (Get-PSDrive $drive.Name).Free / 1GB
    
    if ($freeSpace -lt 5) {
        Write-Warning "Less than 5GB available. Rhinometric requires ~3-5GB for images."
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne 'y' -and $continue -ne 'Y') {
            exit 1
        }
    }
    else {
        Write-Success "$([math]::Round($freeSpace, 1))GB available"
    }
}

# ============================================================================
# Environment Configuration
# ============================================================================

function Initialize-Environment {
    Write-Step "Setting up environment configuration..."
    
    if (Test-Path $EnvFile) {
        Write-Warning ".env file already exists"
        $overwrite = Read-Host "Overwrite with new configuration? (y/N)"
        if ($overwrite -ne 'y' -and $overwrite -ne 'Y') {
            Write-Success "Using existing .env file"
            return
        }
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        Copy-Item $EnvFile "$EnvFile.backup.$timestamp"
        Write-Success "Backed up existing .env file"
    }
    
    if (-not (Test-Path $EnvExample)) {
        Write-Error ".env.example not found"
        exit 1
    }
    
    Copy-Item $EnvExample $EnvFile
    
    # Generate secure passwords
    $postgresPass = Generate-SecurePassword
    $redisPass = Generate-SecurePassword
    $grafanaPass = Generate-SecurePassword
    
    # Update .env with generated passwords
    (Get-Content $EnvFile) -replace 'POSTGRES_PASSWORD=.*', "POSTGRES_PASSWORD=$postgresPass" `
                           -replace 'REDIS_PASSWORD=.*', "REDIS_PASSWORD=$redisPass" `
                           -replace 'GRAFANA_PASSWORD=.*', "GRAFANA_PASSWORD=$grafanaPass" `
        | Set-Content $EnvFile
    
    Write-Success "Environment configured with secure passwords"
    
    # Save credentials to file
    $credsFile = "credentials.txt"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    @"
# ============================================================================
# Rhinometric v$RhinometricVersion - Generated Credentials
# ============================================================================
# IMPORTANT: Store this file securely and delete after saving elsewhere
# Generated: $timestamp
# ============================================================================

GRAFANA (http://localhost:3000):
  Username: admin
  Password: $grafanaPass

POSTGRES (localhost:5432):
  Database: rhinometric_trial
  Username: rhinometric
  Password: $postgresPass

REDIS (localhost:6379):
  Password: $redisPass

# ============================================================================
# Other Services (no authentication required):
# ============================================================================
# Prometheus: http://localhost:9090
# License Server API: http://localhost:5000/api/docs
# API Connector UI: http://localhost:8091
# License Management UI: http://localhost:8092
# Alertmanager: http://localhost:9093
# ============================================================================
"@ | Out-File -FilePath $credsFile -Encoding UTF8
    
    Write-Success "Credentials saved to $credsFile"
}

# ============================================================================
# Deployment
# ============================================================================

function Deploy-Stack {
    Write-Step "Deploying Rhinometric stack..."
    
    if (-not (Test-Path $ComposeFile)) {
        Write-Error "docker-compose file not found: $ComposeFile"
        exit 1
    }
    
    Write-Host "Pulling Docker images (this may take 5-10 minutes on first run)..."
    docker compose -f $ComposeFile pull
    
    Write-Host "Starting services..."
    docker compose -f $ComposeFile up -d
    
    Write-Success "All services started"
}

function Wait-ForServices {
    Write-Step "Waiting for services to become healthy..."
    
    Write-Host "This may take 30-60 seconds..."
    Start-Sleep -Seconds 15
    
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            $containers = docker compose -f $ComposeFile ps --format json | ConvertFrom-Json
            $healthyCount = ($containers | Where-Object { $_.Health -eq "healthy" }).Count
            $totalCount = $containers.Count
            
            Write-Host "`rHealthy containers: $healthyCount/$totalCount  " -NoNewline
            
            if ($healthyCount -ge 10) {
                Write-Host ""
                Write-Success "Core services are healthy"
                return
            }
        }
        catch {
            # Fallback if JSON parsing fails
            $output = docker compose -f $ComposeFile ps
            $healthyCount = ($output | Select-String "healthy").Count
            $totalCount = ($output | Select-String "Up").Count
            
            Write-Host "`rHealthy containers: $healthyCount/$totalCount  " -NoNewline
            
            if ($healthyCount -ge 10) {
                Write-Host ""
                Write-Success "Core services are healthy"
                return
            }
        }
        
        Start-Sleep -Seconds 2
        $attempt++
    }
    
    Write-Host ""
    Write-Warning "Some services may still be starting. Check with: docker compose -f $ComposeFile ps"
}

# ============================================================================
# Post-Install
# ============================================================================

function Show-AccessInfo {
    Write-Header
    
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  Installation Complete!                                      ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor White
    Write-Host ""
    Write-Host "  Grafana:              " -NoNewline -ForegroundColor Cyan
    Write-Host "http://localhost:3000"
    Write-Host "  Prometheus:           " -NoNewline -ForegroundColor Cyan
    Write-Host "http://localhost:9090"
    Write-Host "  License Server:       " -NoNewline -ForegroundColor Cyan
    Write-Host "http://localhost:5000/api/docs"
    Write-Host "  API Connector UI:     " -NoNewline -ForegroundColor Cyan
    Write-Host "http://localhost:8091"
    Write-Host "  License Management:   " -NoNewline -ForegroundColor Cyan
    Write-Host "http://localhost:8092"
    Write-Host ""
    Write-Host "🔐 Credentials:" -ForegroundColor White
    Write-Host ""
    Write-Host "  Saved in: " -NoNewline
    Write-Host "credentials.txt" -ForegroundColor Yellow
    Write-Host "  Grafana username: " -NoNewline
    Write-Host "admin" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 Quick Commands:" -ForegroundColor White
    Write-Host ""
    Write-Host "  View logs:        " -NoNewline
    Write-Host "docker compose -f $ComposeFile logs -f" -ForegroundColor Yellow
    Write-Host "  Check status:     " -NoNewline
    Write-Host "docker compose -f $ComposeFile ps" -ForegroundColor Yellow
    Write-Host "  Stop services:    " -NoNewline
    Write-Host "docker compose -f $ComposeFile down" -ForegroundColor Yellow
    Write-Host "  Restart:          " -NoNewline
    Write-Host "docker compose -f $ComposeFile restart" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📚 Documentation:" -ForegroundColor White
    Write-Host ""
    Write-Host "  README.md - Full documentation"
    Write-Host "  CONFIGURAR_EMAIL_ZOHO.md - Email configuration guide"
    Write-Host ""
    Write-Host "⚠️  Remember to:" -ForegroundColor Yellow
    Write-Host "  1. Store credentials.txt securely"
    Write-Host "  2. Change Grafana password on first login"
    Write-Host "  3. Configure SMTP in .env for email functionality"
    Write-Host ""
}

# ============================================================================
# Main Execution
# ============================================================================

function Main {
    Write-Header
    
    # Prerequisites
    Test-Docker
    Test-DockerCompose
    Test-Ports
    Test-DiskSpace
    
    Write-Host ""
    
    # Configuration
    Initialize-Environment
    
    Write-Host ""
    
    # Deployment
    Deploy-Stack
    Wait-ForServices
    
    Write-Host ""
    
    # Success
    Show-AccessInfo
}

# Run main function
try {
    Main
}
catch {
    Write-Host ""
    Write-Error "Installation failed: $($_.Exception.Message)"
    exit 1
}
