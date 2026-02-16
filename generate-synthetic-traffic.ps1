# Script para generar trafico sintetico y disparar alertas en Rhinometric
# Uso: .\generate-synthetic-traffic.ps1

Write-Host "=== RHINOMETRIC TRAFFIC GENERATOR ===" -ForegroundColor Cyan
Write-Host "Generando trafico sintetico para poblar metricas y disparar alertas...`n" -ForegroundColor Yellow

# Configuracion
$baseUrl = "http://localhost:8105"
$grafanaUrl = "http://localhost:3000"
$prometheusUrl = "http://localhost:9090"
$iterations = 100
$delayMs = 500

# Funcion para hacer requests
function Invoke-SyntheticRequest {
    param(
        [string]$Url,
        [string]$Description
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
        Write-Host "+" -ForegroundColor Green -NoNewline
        return $true
    } catch {
        Write-Host "x" -ForegroundColor Red -NoNewline
        return $false
    }
}

# 1. Generar trafico HTTP al backend
$msg = "1. Generando trafico HTTP al backend (" + $iterations + " requests)..."
Write-Host $msg -ForegroundColor Cyan
$msg = "1. Generando trafico HTTP al backend (" + $iterations + " requests)..."
Write-Host $msg -ForegroundColor Cyan
Write-Host "   Progress: " -NoNewline

for ($i = 1; $i -le $iterations; $i++) {
    # Vary endpoints para generar diferentes metricas
    $endpoints = @(
        "/health",
        "/api/traces?service=test-service",
        "/api/logs?limit=10",
        "/api/anomalies",
        "/api/alerts"
    )
    
    $endpoint = $endpoints | Get-Random
    Invoke-SyntheticRequest -Url "${baseUrl}${endpoint}" -Description "Request $i"
    
    Start-Sleep -Milliseconds $delayMs
    
    if ($i % 10 -eq 0) {
        $progress = " $i/" + $iterations
        Write-Host $progress -ForegroundColor Gray
        Write-Host "   Progress: " -NoNewline
    }
}

Write-Host "`n   Completado`n" -ForegroundColor Green

# 2. Generar trafico a Grafana
Write-Host "2. Generando trafico a Grafana (20 requests)..." -ForegroundColor Cyan
Write-Host "   Progress: " -NoNewline

for ($i = 1; $i -le 20; $i++) {
    Invoke-SyntheticRequest -Url "${grafanaUrl}/api/health" -Description "Grafana health"
    Start-Sleep -Milliseconds 300
}

Write-Host "`n   Completado`n" -ForegroundColor Green

# 3. Generar trafico a Prometheus
Write-Host "3. Generando trafico a Prometheus (20 requests)..." -ForegroundColor Cyan
Write-Host "   Progress: " -NoNewline

for ($i = 1; $i -le 20; $i++) {
    Invoke-SyntheticRequest -Url "${prometheusUrl}/api/v1/query?query=up" -Description "Prometheus query"
    Start-Sleep -Milliseconds 300
}

Write-Host "`n   Completado`n" -ForegroundColor Green

# 5. Resumen
Write-Host "`n=== RESUMEN ===" -ForegroundColor Cyan
$msg2 = "Trafico HTTP generado: ~" + $iterations + " requests"
Write-Host $msg2 -ForegroundColor Green
Write-Host "Servicios accedidos: Backend, Grafana, Prometheus" -ForegroundColor Green
Write-Host "`nEspera 2-5 minutos para que:" -ForegroundColor Yellow
Write-Host "  - Prometheus procese las metricas" -ForegroundColor Gray
Write-Host "  - AI Anomaly Detection Engine analice los datos" -ForegroundColor Gray
Write-Host "  - AlertManager evalue las reglas (si se violaron umbrales)" -ForegroundColor Gray
Write-Host "`nVerifica los resultados en:" -ForegroundColor Cyan
Write-Host "  • UI Rhinometric: http://localhost:3002" -ForegroundColor White
Write-Host "  • Grafana: http://localhost:3000" -ForegroundColor White
Write-Host "  • Prometheus Alerts: http://localhost:9090/alerts" -ForegroundColor White
Write-Host "  • AlertManager: http://localhost:9093" -ForegroundColor White
Write-Host ""

