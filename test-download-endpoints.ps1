###############################################################################
# RHINOMETRIC v2.5.0 - Script de Verificación de Endpoints (PowerShell)
# 
# Este script verifica que todos los endpoints de descarga y documentación
# del License Server v2 estén funcionando correctamente.
#
# Uso:
#   .\test-download-endpoints.ps1 [ServerUrl]
#
# Ejemplo:
#   .\test-download-endpoints.ps1 https://licensing.rhinometric.com:5000
#   .\test-download-endpoints.ps1 http://localhost:5000
###############################################################################

param(
    [string]$ServerUrl = "http://localhost:5000"
)

# Colors
$ColorReset = "`e[0m"
$ColorGreen = "`e[32m"
$ColorRed = "`e[31m"
$ColorYellow = "`e[33m"
$ColorBlue = "`e[34m"

# Counters
$script:Passed = 0
$script:Failed = 0
$script:Total = 0

###############################################################################
# Helper Functions
###############################################################################

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Endpoint,
        [int]$ExpectedStatus = 200
    )
    
    $script:Total++
    
    Write-Host -NoNewline "[$script:Total] Probando: $Name... "
    
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl$Endpoint" -Method Get -UseBasicParsing -ErrorAction SilentlyContinue
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host "${ColorGreen}✓ PASS${ColorReset} (HTTP $statusCode)" -ForegroundColor Green
            $script:Passed++
        } else {
            Write-Host "${ColorRed}✗ FAIL${ColorReset} (Expected $ExpectedStatus, got $statusCode)" -ForegroundColor Red
            $script:Failed++
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 404) {
            Write-Host "${ColorYellow}⚠ SKIP${ColorReset} (Archivo no encontrado - 404)" -ForegroundColor Yellow
            Write-Host "    Esto es normal si aún no has copiado el archivo al servidor" -ForegroundColor Yellow
        } else {
            Write-Host "${ColorRed}✗ FAIL${ColorReset} (Error: $_)" -ForegroundColor Red
            $script:Failed++
        }
    }
}

function Test-EndpointJson {
    param(
        [string]$Name,
        [string]$Endpoint,
        [string]$JsonKey
    )
    
    $script:Total++
    
    Write-Host -NoNewline "[$script:Total] Probando: $Name... "
    
    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl$Endpoint" -Method Get -UseBasicParsing
        
        if ($response.PSObject.Properties.Name -contains $JsonKey) {
            Write-Host "${ColorGreen}✓ PASS${ColorReset} (JSON válido, key '$JsonKey' encontrada)" -ForegroundColor Green
            $script:Passed++
        } else {
            Write-Host "${ColorRed}✗ FAIL${ColorReset} (Key '$JsonKey' no encontrada)" -ForegroundColor Red
            $script:Failed++
        }
    } catch {
        Write-Host "${ColorRed}✗ FAIL${ColorReset} (Error: $_)" -ForegroundColor Red
        $script:Failed++
    }
}

function Test-FileDownload {
    param(
        [string]$Name,
        [string]$Endpoint,
        [string]$ExpectedContentType
    )
    
    $script:Total++
    
    Write-Host -NoNewline "[$script:Total] Probando: $Name... "
    
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl$Endpoint" -Method Head -UseBasicParsing -ErrorAction SilentlyContinue
        $contentType = $response.Headers.'Content-Type'
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq 200 -and $contentType -like "*$ExpectedContentType*") {
            Write-Host "${ColorGreen}✓ PASS${ColorReset} (HTTP 200, Content-Type: $contentType)" -ForegroundColor Green
            $script:Passed++
        } else {
            Write-Host "${ColorRed}✗ FAIL${ColorReset} (HTTP $statusCode, Content-Type: $contentType)" -ForegroundColor Red
            $script:Failed++
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 404) {
            Write-Host "${ColorYellow}⚠ SKIP${ColorReset} (Archivo no encontrado - 404)" -ForegroundColor Yellow
            Write-Host "    Esto es normal si aún no has copiado el archivo al servidor" -ForegroundColor Yellow
        } else {
            Write-Host "${ColorRed}✗ FAIL${ColorReset} (Error: $_)" -ForegroundColor Red
            $script:Failed++
        }
    }
}

###############################################################################
# Main Script
###############################################################################

Clear-Host

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   RHINOMETRIC v2.5.0 - Verificación de Endpoints de Descarga    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 Servidor: $ServerUrl" -ForegroundColor Yellow
Write-Host ""

# Section 1: Health Check
Write-Header "🔍 SECCIÓN 1: Health Check"
Test-EndpointJson "Health Check" "/api/health" "status"
Write-Host ""

# Section 2: Downloads
Write-Header "📥 SECCIÓN 2: Endpoints de Descarga"
Test-FileDownload "Demo OVA" "/downloads/demo-ova" "application/octet-stream"
Test-FileDownload "Trial Installer" "/downloads/trial-installer" "application/x-sh"
Test-EndpointJson "Downloads Info (Metadata)" "/downloads/info" "downloads"
Write-Host ""

# Section 3: Documentation (Spanish)
Write-Header "📚 SECCIÓN 3: Documentación (Español)"
Test-FileDownload "Guía de Instalación (ES)" "/docs/installation-guide?lang=es" "application/pdf"
Test-FileDownload "Manual de Usuario (ES)" "/docs/user-manual?lang=es" "application/pdf"
Write-Host ""

# Section 4: Documentation (English)
Write-Header "📚 SECCIÓN 4: Documentación (English)"
Test-FileDownload "Installation Guide (EN)" "/docs/installation-guide?lang=en" "application/pdf"
Test-FileDownload "User Manual (EN)" "/docs/user-manual?lang=en" "application/pdf"
Write-Host ""

# Section 5: Metadata
Write-Header "🔍 SECCIÓN 5: Verificación de Metadata"
Write-Host "Obteniendo metadata de archivos..." -ForegroundColor Yellow
Write-Host ""

try {
    $metadata = Invoke-RestMethod -Uri "$ServerUrl/downloads/info" -Method Get
    
    Write-Host "📊 Archivos Disponibles:" -ForegroundColor Cyan
    Write-Host ""
    foreach ($item in $metadata.downloads.PSObject.Properties) {
        $name = $item.Name
        $value = $item.Value
        if ($value.available) {
            Write-Host "  • ${name}: " -NoNewline -ForegroundColor White
            Write-Host "✓ Disponible ($($value.size_mb) MB)" -ForegroundColor Green
        } else {
            Write-Host "  • ${name}: " -NoNewline -ForegroundColor White
            Write-Host "✗ No disponible" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "📄 Documentación Disponible:" -ForegroundColor Cyan
    Write-Host ""
    foreach ($item in $metadata.documentation.PSObject.Properties) {
        $name = $item.Name
        $value = $item.Value
        if ($value.available) {
            Write-Host "  • ${name}: " -NoNewline -ForegroundColor White
            Write-Host "✓ Disponible ($($value.size_mb) MB)" -ForegroundColor Green
        } else {
            Write-Host "  • ${name}: " -NoNewline -ForegroundColor White
            Write-Host "✗ No disponible" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "Error obteniendo metadata: $_" -ForegroundColor Red
}

Write-Host ""

# Summary
Write-Header "📊 RESUMEN DE RESULTADOS"

if ($script:Failed -eq 0) {
    Write-Host "Estado: " -NoNewline
    Write-Host "✓ TODOS LOS TESTS PASARON" -ForegroundColor Green
} else {
    Write-Host "Estado: " -NoNewline
    Write-Host "✗ ALGUNOS TESTS FALLARON" -ForegroundColor Red
}

Write-Host ""
Write-Host "Tests ejecutados: $script:Total"
Write-Host "Exitosos:        " -NoNewline
Write-Host $script:Passed -ForegroundColor Green
Write-Host "Fallidos:        " -NoNewline
Write-Host $script:Failed -ForegroundColor Red
Write-Host ""

if ($script:Failed -gt 0) {
    Write-Host "⚠️  NOTAS:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  • Si ves errores 404, probablemente los archivos aún no están copiados al servidor." -ForegroundColor Yellow
    Write-Host "  • Verifica que los archivos estén en las rutas correctas:" -ForegroundColor Yellow
    Write-Host "    - /app/static/downloads/rhinometric-demo-2.5.0.ova" -ForegroundColor Gray
    Write-Host "    - /app/static/downloads/rhinometric-trial-2.5.0-install.sh" -ForegroundColor Gray
    Write-Host "    - /app/static/docs/es/rhinometric-installation-guide-es.pdf" -ForegroundColor Gray
    Write-Host "    - /app/static/docs/en/rhinometric-user-manual-en.pdf" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  • Consulta docs/v2.5.0/DOWNLOAD_ENDPOINTS.md para instrucciones de deployment." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Exit with appropriate code
if ($script:Failed -eq 0) {
    exit 0
} else {
    exit 1
}
