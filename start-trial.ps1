# ============================================
# RHINOMETRIC TRIAL - START SCRIPT (Windows)
# Versión Trial 6 Meses (180 días)
# ============================================

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "║         🦏 RHINOMETRIC TRIAL - INSTALADOR                 ║" -ForegroundColor Cyan
Write-Host "║         Plataforma de Observabilidad                      ║" -ForegroundColor Cyan
Write-Host "║         Versión: Trial 6 Meses (180 días)                 ║" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar Docker
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "❌ Docker no está instalado" -ForegroundColor Red
    Write-Host "   Instalar desde: https://docs.docker.com/get-docker/"
    exit 1
}

# Verificar Docker Compose
$dockerComposeInstalled = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerComposeInstalled) {
    Write-Host "❌ Docker Compose no está instalado" -ForegroundColor Red
    Write-Host "   Instalar desde: https://docs.docker.com/compose/install/"
    exit 1
}

Write-Host "✅ Docker y Docker Compose detectados" -ForegroundColor Green
Write-Host ""

# Crear directorios necesarios
Write-Host "📁 Creando directorios..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "certs" | Out-Null
New-Item -ItemType Directory -Force -Path "licenses" | Out-Null
New-Item -ItemType Directory -Force -Path "init-db" | Out-Null

Write-Host "✅ Directorios creados" -ForegroundColor Green
Write-Host ""

# Generar .env si no existe
if (-not (Test-Path .env)) {
    Write-Host "🔐 Generando archivo .env..." -ForegroundColor Yellow
    
    $postgresPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 25 | % {[char]$_})
    $grafanaPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | % {[char]$_})
    $jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
    
    @"
# Rhinometric Trial Configuration
POSTGRES_PASSWORD=$postgresPassword
GRAFANA_PASSWORD=$grafanaPassword
JWT_SECRET=$jwtSecret

# URLs
GRAFANA_URL=http://localhost:3000

# Dashboard
DASHBOARD_PORT=8080
"@ | Out-File -FilePath .env -Encoding UTF8
    
    Write-Host "✅ Archivo .env generado" -ForegroundColor Green
} else {
    Write-Host "✅ Archivo .env encontrado" -ForegroundColor Green
}
Write-Host ""

# Preguntar nombre del cliente
Write-Host "📝 INFORMACIÓN DE LA LICENCIA" -ForegroundColor Cyan
Write-Host "────────────────────────────────────────────────────────────"
$clientName = Read-Host "Nombre del cliente/organización"
$clientEmail = Read-Host "Email de contacto"

if ([string]::IsNullOrWhiteSpace($clientName)) {
    $clientName = "Trial-Demo"
}

Write-Host ""
Write-Host "Generando licencia trial para: $clientName"
Write-Host ""

# Generar licencia trial
Write-Host "🔑 Generando licencia trial (180 días)..." -ForegroundColor Yellow

$licenseData = @{
    customer = $clientName
    type = "trial"
    issued = (Get-Date).ToString("o")
    expires = (Get-Date).AddDays(180).ToString("o")
    product = "Rhinometric Observability Platform"
    version = "1.0.0"
    features = @("monitoring", "alerting", "dashboards", "logs", "traces")
    limits = @{
        max_metrics = 10000
        max_logs_per_day = 1000000
        max_traces_per_day = 50000
        retention_days = 7
        max_users = 5
    }
}

$jsonData = $licenseData | ConvertTo-Json -Compress
$bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonData)
$encoded = [Convert]::ToBase64String($bytes)

$licenseFile = "licenses/trial_$($clientName -replace ' ','_').lic"
$encoded | Out-File -FilePath $licenseFile -Encoding UTF8 -NoNewline

Write-Host "✅ Licencia generada: $licenseFile" -ForegroundColor Green
Write-Host ""

# Mostrar información
$expiryDate = (Get-Date).AddDays(180).ToString("yyyy-MM-dd")

Write-Host "📋 CONFIGURACIÓN COMPLETADA" -ForegroundColor Cyan
Write-Host "────────────────────────────────────────────────────────────"
Write-Host "Cliente:          $clientName"
Write-Host "Email:            $clientEmail"
Write-Host "Tipo:             Trial"
Write-Host "Duración:         180 días (6 meses)"
Write-Host "Expira:           $expiryDate"
Write-Host "Licencia:         $licenseFile"
Write-Host ""

# Preguntar si iniciar
$startNow = Read-Host "¿Iniciar Rhinometric ahora? (s/n)"

if ($startNow -match "^[Ss]$") {
    Write-Host ""
    Write-Host "🚀 Iniciando contenedores..." -ForegroundColor Yellow
    Write-Host ""
    
    # Bajar servicios existentes
    docker-compose -f docker-compose-trial.yml down 2>$null
    
    # Construir e iniciar
    docker-compose -f docker-compose-trial.yml up -d --build
    
    Write-Host ""
    Write-Host "⏳ Esperando que los servicios estén listos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # Verificar servicios
    Write-Host ""
    Write-Host "🔍 Verificando servicios..." -ForegroundColor Yellow
    docker-compose -f docker-compose-trial.yml ps
    
    # Leer password de Grafana
    $envContent = Get-Content .env
    $grafanaPass = ($envContent | Select-String "GRAFANA_PASSWORD=").ToString().Split("=")[1]
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                                                            ║" -ForegroundColor Green
    Write-Host "║         ✅ RHINOMETRIC TRIAL INICIADO                      ║" -ForegroundColor Green
    Write-Host "║                                                            ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 ACCESO A LOS SERVICIOS:" -ForegroundColor Cyan
    Write-Host "────────────────────────────────────────────────────────────"
    Write-Host ""
    Write-Host "  🎨 Grafana Dashboard:" -ForegroundColor White
    Write-Host "     URL:      http://localhost:3000" -ForegroundColor Gray
    Write-Host "     Usuario:  admin" -ForegroundColor Gray
    Write-Host "     Password: $grafanaPass" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  📈 Prometheus:" -ForegroundColor White
    Write-Host "     URL:      http://localhost:9090" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  📝 Loki (Logs):" -ForegroundColor White
    Write-Host "     URL:      http://localhost:3100" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  🔍 Tempo (Traces):" -ForegroundColor White
    Write-Host "     URL:      http://localhost:3200" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  🚨 Alertmanager:" -ForegroundColor White
    Write-Host "     URL:      http://localhost:9093" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  🔑 License Dashboard:" -ForegroundColor White
    Write-Host "     URL:      http://localhost:8080" -ForegroundColor Gray
    Write-Host "     URL Alt:  http://localhost/dashboard/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "────────────────────────────────────────────────────────────"
    Write-Host ""
    Write-Host "📚 COMANDOS ÚTILES:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Ver logs:           docker-compose -f docker-compose-trial.yml logs -f"
    Write-Host "  Ver estado:         docker-compose -f docker-compose-trial.yml ps"
    Write-Host "  Reiniciar:          docker-compose -f docker-compose-trial.yml restart"
    Write-Host "  Detener:            docker-compose -f docker-compose-trial.yml stop"
    Write-Host "  Eliminar todo:      docker-compose -f docker-compose-trial.yml down -v"
    Write-Host ""
    Write-Host "────────────────────────────────────────────────────────────"
    Write-Host ""
    Write-Host "⚠️  IMPORTANTE:" -ForegroundColor Yellow
    Write-Host "   - Esta es una versión TRIAL válida por 180 días"
    Write-Host "   - Retención de datos limitada a 7 días"
    Write-Host "   - Máximo 5 usuarios"
    Write-Host "   - Para versión comercial: contacto@rhinometric.com"
    Write-Host ""
    Write-Host "📧 Soporte: soporte@rhinometric.com"
    Write-Host "📖 Docs:    https://docs.rhinometric.com"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "✅ Configuración completada" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para iniciar Rhinometric manualmente:"
    Write-Host "  docker-compose -f docker-compose-trial.yml up -d"
    Write-Host ""
}
