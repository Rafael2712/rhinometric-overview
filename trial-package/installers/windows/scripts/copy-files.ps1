# 🦏 RHINOMETRIC TRIAL - COPIAR ARCHIVOS
# Script para copiar archivos del trial package
# © 2025 Rhinometric

param(
    [Parameter(Mandatory=$true)]
    [string]$Source,
    
    [Parameter(Mandatory=$true)]
    [string]$Destination
)

Write-Host "Copiando archivos de Rhinometric Trial..." -ForegroundColor Cyan
Write-Host "Origen: $Source" -ForegroundColor Gray
Write-Host "Destino: $Destination" -ForegroundColor Gray

try {
    # Crear directorio destino si no existe
    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    
    # Copiar todos los archivos
    Copy-Item -Path "$Source\*" -Destination $Destination -Recurse -Force
    
    Write-Host "✅ Archivos copiados exitosamente" -ForegroundColor Green
    exit 0
    
} catch {
    Write-Host "❌ Error copiando archivos: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
