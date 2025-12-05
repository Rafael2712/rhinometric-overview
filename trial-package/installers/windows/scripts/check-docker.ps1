# 🦏 RHINOMETRIC TRIAL - VERIFICAR DOCKER DESKTOP
# Script para verificar instalación y estado de Docker Desktop
# © 2025 Rhinometric

param(
    [switch]$Verbose
)

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🦏 RHINOMETRIC - Verificación de Docker Desktop" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Verificar si Docker está instalado
Write-Host "[1/3] Verificando instalación de Docker..." -ForegroundColor Yellow

try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker instalado: $dockerVersion" -ForegroundColor Green
        $dockerInstalled = $true
    } else {
        Write-Host "❌ Docker no detectado" -ForegroundColor Red
        $dockerInstalled = $false
    }
} catch {
    Write-Host "❌ Docker no detectado" -ForegroundColor Red
    $dockerInstalled = $false
}

# Verificar si Docker está corriendo
Write-Host ""
Write-Host "[2/3] Verificando estado de Docker..." -ForegroundColor Yellow

if ($dockerInstalled) {
    try {
        $dockerPs = docker ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker está corriendo" -ForegroundColor Green
            $dockerRunning = $true
        } else {
            Write-Host "⚠️  Docker instalado pero no está corriendo" -ForegroundColor Yellow
            Write-Host "   Por favor, inicia Docker Desktop y vuelve a intentarlo" -ForegroundColor Yellow
            $dockerRunning = $false
        }
    } catch {
        Write-Host "❌ Error verificando estado de Docker" -ForegroundColor Red
        $dockerRunning = $false
    }
} else {
    $dockerRunning = $false
}

# Verificar recursos disponibles
Write-Host ""
Write-Host "[3/3] Verificando recursos del sistema..." -ForegroundColor Yellow

try {
    $computerInfo = Get-ComputerInfo
    $totalRAM = [math]::Round($computerInfo.CsTotalPhysicalMemory / 1GB, 2)
    
    Write-Host "   RAM total: $totalRAM GB" -ForegroundColor Cyan
    
    if ($totalRAM -ge 8) {
        Write-Host "✅ Memoria RAM suficiente" -ForegroundColor Green
        $ramOK = $true
    } else {
        Write-Host "⚠️  Memoria RAM insuficiente (mínimo 8GB recomendados)" -ForegroundColor Yellow
        $ramOK = $false
    }
} catch {
    Write-Host "⚠️  No se pudo verificar la RAM del sistema" -ForegroundColor Yellow
    $ramOK = $false
}

# Resumen
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  RESUMEN" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($dockerInstalled) {
    Write-Host "Docker Desktop:     ✅ Instalado" -ForegroundColor Green
} else {
    Write-Host "Docker Desktop:     ❌ NO instalado" -ForegroundColor Red
}

if ($dockerRunning) {
    Write-Host "Estado Docker:      ✅ Corriendo" -ForegroundColor Green
} else {
    Write-Host "Estado Docker:      ❌ Detenido" -ForegroundColor Red
}

if ($ramOK) {
    Write-Host "Memoria RAM:        ✅ Suficiente ($totalRAM GB)" -ForegroundColor Green
} else {
    Write-Host "Memoria RAM:        ⚠️  Insuficiente ($totalRAM GB)" -ForegroundColor Yellow
}

Write-Host ""

# Retornar código de salida
if ($dockerInstalled -and $dockerRunning -and $ramOK) {
    Write-Host "🎉 Sistema listo para instalar Rhinometric" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Requisitos no cumplidos. Por favor, revisa los errores arriba." -ForegroundColor Yellow
    exit 1
}
