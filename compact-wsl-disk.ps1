# ============================================
# Script para compactar disco virtual WSL2
# Recupera espacio en Windows después de limpiar datos en WSL2
# ============================================

Write-Host "`n╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔧 COMPACTADOR DE DISCO VIRTUAL WSL2              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. Verificar que WSL está apagado
Write-Host "⏸️  Deteniendo WSL2..." -ForegroundColor Yellow
wsl --shutdown
Start-Sleep -Seconds 3

# 2. Encontrar el disco virtual
Write-Host "`n🔍 Buscando disco virtual de Ubuntu 22.04..." -ForegroundColor Yellow
$vhdxPath = (Get-ChildItem -Path "C:\Users\canel\AppData\Local\Packages\" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 10GB } | Select-Object -First 1).FullName

if (-not $vhdxPath) {
    Write-Host "❌ No se encontró el disco virtual" -ForegroundColor Red
    exit 1
}

Write-Host "📍 Disco encontrado: $vhdxPath" -ForegroundColor Cyan

# 3. Obtener tamaño antes
$sizeBefore = [math]::Round((Get-Item $vhdxPath).Length / 1GB, 2)
Write-Host "📊 Tamaño actual: $sizeBefore GB" -ForegroundColor Yellow

# 4. Crear script temporal para diskpart
$diskpartScript = @"
select vdisk file="$vhdxPath"
attach vdisk readonly
compact vdisk
detach vdisk
exit
"@

$scriptPath = "$env:TEMP\diskpart_compact.txt"
$diskpartScript | Out-File -FilePath $scriptPath -Encoding ASCII

# 5. Ejecutar diskpart
Write-Host "`n🔧 Compactando disco virtual (esto puede tardar varios minutos)..." -ForegroundColor Green
diskpart /s $scriptPath

# 6. Verificar resultado
Start-Sleep -Seconds 2
$sizeAfter = [math]::Round((Get-Item $vhdxPath).Length / 1GB, 2)
$recovered = [math]::Round($sizeBefore - $sizeAfter, 2)

Write-Host "`n╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ COMPACTACIÓN COMPLETADA                        ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`n📊 Tamaño antes:      $sizeBefore GB" -ForegroundColor Cyan
Write-Host "📊 Tamaño después:    $sizeAfter GB" -ForegroundColor Cyan
Write-Host "💾 Espacio recuperado: $recovered GB" -ForegroundColor Green

# 7. Limpiar script temporal
Remove-Item $scriptPath -ErrorAction SilentlyContinue

Write-Host "`n✅ Ahora puedes iniciar WSL2 con: wsl -d Ubuntu-22.04" -ForegroundColor Yellow
Write-Host ""
