# Script para generar trafico agresivo y disparar alertas
# Uso: .\trigger-alerts.ps1

Write-Host "=== GENERADOR DE ALERTAS RHINOMETRIC ===" -ForegroundColor Cyan
Write-Host "Este script generara carga para disparar alertas...`n" -ForegroundColor Yellow

$backendUrl = "http://localhost:8105"
$iterations = 500
$concurrency = 5

# Funcion para hacer requests concurrentes
function Invoke-LoadTest {
    param([int]$Count, [string]$Url)
    
    $jobs = @()
    for ($i = 1; $i -le $Count; $i++) {
        $jobs += Start-Job -ScriptBlock {
            param($Url)
            try {
                Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue | Out-Null
            } catch {}
        } -ArgumentList $Url
        
        if ($i % $concurrency -eq 0) {
            $jobs | Wait-Job | Remove-Job
            $jobs = @()
            Write-Host "." -NoNewline -ForegroundColor Green
        }
    }
    $jobs | Wait-Job | Remove-Job
}

# 1. Generar carga HTTP
Write-Host "1. Generando carga HTTP alta (500 requests)..." -ForegroundColor Cyan
Write-Host "   Progress: " -NoNewline
Invoke-LoadTest -Count $iterations -Url "$backendUrl/api/traces"
Write-Host "`n   Completado`n" -ForegroundColor Green

# 2. Generar queries a diferentes endpoints
Write-Host "2. Generando queries a multiples endpoints..." -ForegroundColor Cyan
$endpoints = @("/api/logs", "/api/anomalies", "/api/alerts", "/health")
foreach ($endpoint in $endpoints) {
    Write-Host "   - $endpoint... " -NoNewline
    Invoke-LoadTest -Count 100 -Url "$backendUrl$endpoint"
    Write-Host "OK" -ForegroundColor Green
}

# 3. Esperar procesamiento
Write-Host "`n3. Esperando procesamiento de metricas (30 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 4. Verificar alertas
Write-Host "`n4. Verificando alertas disparadas:" -ForegroundColor Cyan
try {
    $alerts = Invoke-WebRequest -Uri "http://localhost:9093/api/v2/alerts" -UseBasicParsing | 
              Select-Object -ExpandProperty Content | ConvertFrom-Json
    
    if ($alerts.Count -gt 0) {
        Write-Host "   Alertas encontradas: $($alerts.Count)" -ForegroundColor Red
        $alerts | ForEach-Object {
            Write-Host "   - $($_.labels.alertname): $($_.labels.severity)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   Aun no hay alertas disparadas (normal en sistemas estables)" -ForegroundColor Gray
        Write-Host "   Las reglas estan cargadas y monitoreando..." -ForegroundColor Gray
    }
} catch {
    Write-Host "   Error verificando alertas: $_" -ForegroundColor Red
}

# 5. Verificar anomalias
Write-Host "`n5. Verificando anomalias detectadas:" -ForegroundColor Cyan
try {
    $anomalies = Invoke-WebRequest -Uri "http://localhost:8085/anomalies" -UseBasicParsing | 
                 Select-Object -ExpandProperty Content | ConvertFrom-Json
    
    Write-Host "   Total de anomalias: $($anomalies.count)" -ForegroundColor $(if($anomalies.count -gt 0){'Red'}else{'Gray'})
    Write-Host "   Anomalias activas: $($anomalies.active_count)" -ForegroundColor $(if($anomalies.active_count -gt 0){'Red'}else{'Gray'})
    
    if ($anomalies.count -eq 0) {
        Write-Host "   El modelo ML necesita mas datos historicos (24-48h)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Error verificando anomalias: $_" -ForegroundColor Red
}

Write-Host "`n=== RESUMEN ===" -ForegroundColor Cyan
Write-Host "Carga generada: ~$iterations requests HTTP" -ForegroundColor Green
Write-Host "`nPara ver resultados:" -ForegroundColor Yellow
Write-Host "  • Rhinometric Alerts: http://localhost:3002/alerts" -ForegroundColor White
Write-Host "  • Prometheus Alerts:  http://localhost:9090/alerts" -ForegroundColor White
Write-Host "  • AlertManager:       http://localhost:9093" -ForegroundColor White
Write-Host "  • AI Anomalies:       http://localhost:3002/anomalies" -ForegroundColor White
Write-Host ""
