# 🦏 RHINOMETRIC TRIAL - START TRIAL (POWERSHELL)
# Script de instalación principal para Windows
# © 2025 Rhinometric

param(
    [Parameter(Mandatory=$false)]
    [string]$CustomerName = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$AutoInstall
)

$ErrorActionPreference = "Stop"

# Banner
function Print-Banner {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                           ║" -ForegroundColor Cyan
    Write-Host "║        🦏 RHINOMETRIC - PLATAFORMA DE OBSERVABILIDAD     ║" -ForegroundColor Cyan
    Write-Host "║        Versión Trial: 180 días (6 meses)                 ║" -ForegroundColor Cyan
    Write-Host "║        Unificando Métricas, Logs y Trazas Distribuidas   ║" -ForegroundColor Cyan
    Write-Host "║        © 2025 Rhinometric                                 ║" -ForegroundColor Cyan
    Write-Host "║                                                           ║" -ForegroundColor Cyan
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host ""
}

Print-Banner

# Verificar Docker
Write-Host "[1/6] Verificando Docker Desktop..." -ForegroundColor Yellow

try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker no está instalado" -ForegroundColor Red
        Write-Host "   Por favor, instala Docker Desktop y vuelve a ejecutar este script" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Docker detectado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error verificando Docker" -ForegroundColor Red
    exit 1
}

# Verificar que Docker está corriendo
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker no está corriendo" -ForegroundColor Red
        Write-Host "   Por favor, inicia Docker Desktop y vuelve a ejecutar este script" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Docker está corriendo" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está corriendo" -ForegroundColor Red
    exit 1
}

# Pedir nombre de cliente si no está especificado
if (-not $CustomerName -and -not $AutoInstall) {
    Write-Host ""
    Write-Host "[2/6] Configuración de licencia" -ForegroundColor Yellow
    $CustomerName = Read-Host "Nombre de tu empresa u organización"
    
    if (-not $CustomerName) {
        Write-Host "❌ El nombre del cliente es requerido" -ForegroundColor Red
        exit 1
    }
}

Write-Host "   Cliente: $CustomerName" -ForegroundColor Cyan

# Generar contraseñas seguras
Write-Host ""
Write-Host "[3/6] Generando configuración segura..." -ForegroundColor Yellow

$GRAFANA_PASSWORD = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
$POSTGRES_PASSWORD = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 20 | ForEach-Object {[char]$_})
$JWT_SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Crear archivo .env
$envContent = @"
# 🦏 RHINOMETRIC TRIAL - ENVIRONMENT VARIABLES
# Generado: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Grafana
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD

# PostgreSQL
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# License Server
JWT_SECRET=$JWT_SECRET

# Trial Configuration
LICENSE_DURATION_DAYS=180
CUSTOMER_NAME=$CustomerName
"@

Set-Content -Path ".env" -Value $envContent
Write-Host "✅ Configuración generada" -ForegroundColor Green

# Crear directorios necesarios
Write-Host ""
Write-Host "[4/6] Creando estructura de directorios..." -ForegroundColor Yellow

$directories = @(
    "data\grafana",
    "data\prometheus",
    "data\loki",
    "data\tempo",
    "data\postgres",
    "data\redis",
    "licenses"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "✅ Directorios creados" -ForegroundColor Green

# Generar licencia
Write-Host ""
Write-Host "[5/6] Generando licencia trial..." -ForegroundColor Yellow

$licenseFile = "licenses\license_${CustomerName}_trial.lic"
$expiryDate = (Get-Date).AddDays(180).ToString("yyyy-MM-dd")

$licenseContent = @"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🦏 RHINOMETRIC TRIAL LICENSE                      ║
║        Observability Platform                             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

CLIENTE: $CustomerName
TIPO: Trial
DURACIÓN: 180 días (6 meses)
FECHA EMISIÓN: $(Get-Date -Format "yyyy-MM-dd")
FECHA EXPIRACIÓN: $expiryDate
VERSIÓN: 1.0.0

CARACTERÍSTICAS INCLUIDAS:
  ✅ Grafana - Visualización y dashboards
  ✅ Prometheus - Recolección de métricas
  ✅ Loki - Agregación de logs
  ✅ Tempo - Trazas distribuidas
  ✅ Alertmanager - Gestión de alertas
  ✅ Exportadores de sistema (Node, cAdvisor)
  ✅ Dashboard de licencias
  ✅ Proxy unificado (Nginx)
  ✅ Base de datos PostgreSQL
  ✅ Cache Redis

LIMITACIONES TRIAL:
  ⚠️  Solo para evaluación y testing
  ⚠️  NO para uso en producción
  ⚠️  Retención de datos: 7 días
  ⚠️  Máximo 5 usuarios en Grafana
  ⚠️  Sin alta disponibilidad (HA)
  ⚠️  Sin backups automáticos
  ⚠️  Sin soporte 24/7
  ⚠️  Expira en 180 días

TÉRMINOS DE USO:
  ✅ Permitido: Evaluación, testing, POC, demos
  ❌ Prohibido: Producción, redistribución, modificación

COMPONENTES OPEN SOURCE:
  - Grafana 10.2.3 (Apache 2.0)
  - Prometheus 2.48.0 (Apache 2.0)
  - Loki 2.9.3 (Apache 2.0)
  - Tempo 2.3.1 (Apache 2.0)
  - PostgreSQL 15 (PostgreSQL License)
  - Redis 7 (BSD 3-Clause)

  Para detalles: Ver THIRD_PARTY_LICENSES.txt

SOPORTE:
  📧 Email: soporte@rhinometric.com
  ⏱️  Respuesta: 24-48 horas hábiles

CONVERSIÓN A VERSIÓN COMERCIAL:
  💼 Ventas: ventas@rhinometric.com
  🌐 Web: https://rhinometric.com/pricing
  📞 Teléfono: +34 XXX XXX XXX

AVISO LEGAL:
  Este software se proporciona "tal cual", sin garantías de ningún
  tipo. El uso es bajo tu propio riesgo. Rhinometric no se hace
  responsable de pérdidas de datos o daños derivados del uso.

═══════════════════════════════════════════════════════════
© 2025 Rhinometric. Todos los derechos reservados.
═══════════════════════════════════════════════════════════
"@

Set-Content -Path $licenseFile -Value $licenseContent
Write-Host "✅ Licencia generada: $licenseFile" -ForegroundColor Green

# Iniciar servicios
Write-Host ""
Write-Host "[6/6] Iniciando servicios Rhinometric..." -ForegroundColor Yellow
Write-Host "   (Esto puede tardar 10-15 minutos en la primera ejecución)" -ForegroundColor Cyan

try {
    docker-compose -f docker-compose-trial.yml up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Servicios iniciados correctamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error iniciando servicios" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error ejecutando docker-compose" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Guardar credenciales
$credentialsFile = "credentials.txt"
$credentialsContent = @"
═══════════════════════════════════════════════════════════
🦏 RHINOMETRIC - CREDENCIALES DE ACCESO
═══════════════════════════════════════════════════════════

GRAFANA (Dashboard Principal):
  URL:      http://localhost:3000
  Usuario:  admin
  Password: $GRAFANA_PASSWORD

PROMETHEUS (Métricas):
  URL: http://localhost:9090

LOKI (Logs):
  URL: http://localhost:3100

TEMPO (Trazas Distribuidas):
  URL: http://localhost:3200

ALERTMANAGER (Alertas):
  URL: http://localhost:9093

LICENSE DASHBOARD (Monitor de Licencias):
  URL: http://localhost:8080

NGINX (Proxy Unificado):
  URL: http://localhost

═══════════════════════════════════════════════════════════
IMPORTANTE - GUARDA ESTE ARCHIVO EN UN LUGAR SEGURO
═══════════════════════════════════════════════════════════

Cliente: $CustomerName
Licencia válida hasta: $expiryDate
Generado: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Para soporte: soporte@rhinometric.com
═══════════════════════════════════════════════════════════
"@

Set-Content -Path $credentialsFile -Value $credentialsContent

# Resumen final
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "║        🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE             ║" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   1. Abre Grafana en tu navegador:" -ForegroundColor White
Write-Host "      → http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "   2. Inicia sesión con:" -ForegroundColor White
Write-Host "      Usuario:  admin" -ForegroundColor Yellow
Write-Host "      Password: $GRAFANA_PASSWORD" -ForegroundColor Yellow
Write-Host ""
Write-Host "   3. Explora los dashboards precargados" -ForegroundColor White
Write-Host ""
Write-Host "   4. Consulta la documentación:" -ForegroundColor White
Write-Host "      → README.md en esta carpeta" -ForegroundColor Yellow
Write-Host ""
Write-Host "📄 Credenciales guardadas en: $credentialsFile" -ForegroundColor Cyan
Write-Host "📄 Licencia guardada en: $licenseFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "📧 Soporte: soporte@rhinometric.com" -ForegroundColor Cyan
Write-Host "💼 Ventas: ventas@rhinometric.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "© 2025 Rhinometric. Todos los derechos reservados." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Abrir Grafana en navegador si no es auto-install
if (-not $AutoInstall) {
    $openBrowser = Read-Host "¿Deseas abrir Grafana en el navegador ahora? (S/n)"
    if ($openBrowser -eq "" -or $openBrowser -eq "S" -or $openBrowser -eq "s") {
        Start-Process "http://localhost:3000"
    }
}

exit 0
