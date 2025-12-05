# Script para verificar trazas en Tempo agrupadas por servicio

Write-Host "🔍 Consultando trazas de los últimos 3 minutos..." -ForegroundColor Cyan

$start = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - 180
$end = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()

$url = "http://localhost:3200/api/search?q=%7B%7D`&limit=100`&start=$start`&end=$end"

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "📊 Trazas encontradas: $($data.traces.Count)" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 Trazas por servicio:" -ForegroundColor Yellow
    Write-Host ""
    
    $grouped = $data.traces | Group-Object rootServiceName | Sort-Object Count -Descending
    
    foreach ($group in $grouped) {
        Write-Host "   $($group.Name): $($group.Count) trazas" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "🔢 Total de servicios únicos: $($grouped.Count)" -ForegroundColor Magenta
    
} catch {
    Write-Host "❌ Error al consultar Tempo: $_" -ForegroundColor Red
}
