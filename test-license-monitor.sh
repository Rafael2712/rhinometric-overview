#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "  RHINOMETRIC v2.3.0 - LICENSE MONITOR TEST"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ============================================================================
# TEST 1: Verificar archivos del license-monitor
# ============================================================================

echo "TEST 1: Verificando archivos de license-monitor..."

if [ -f "license-monitor/license_monitor.py" ]; then
    echo "✅ license_monitor.py encontrado"
    size=$(du -h license-monitor/license_monitor.py | cut -f1)
    echo "   Tamaño: $size"
    lines=$(wc -l < license-monitor/license_monitor.py)
    echo "   Líneas: $lines LOC"
else
    echo "❌ license_monitor.py NO encontrado"
    exit 1
fi

if [ -f "license-monitor/Dockerfile" ]; then
    echo "✅ Dockerfile encontrado"
else
    echo "❌ Dockerfile NO encontrado"
    exit 1
fi

echo ""

# ============================================================================
# TEST 2: Verificar configuración docker-compose
# ============================================================================

echo "TEST 2: Verificando configuración docker-compose..."

if docker compose -f docker-compose-v2.2.0.yml config > /dev/null 2>&1; then
    echo "✅ Configuración de docker-compose válida"
else
    echo "❌ ERROR: Configuración de docker-compose inválida"
    exit 1
fi

# Verificar que existe el servicio license-monitor
if docker compose -f docker-compose-v2.2.0.yml config | grep -q "license-monitor:"; then
    echo "✅ Servicio license-monitor configurado"
else
    echo "❌ Servicio license-monitor NO encontrado en docker-compose"
    exit 1
fi

echo ""

# ============================================================================
# TEST 3: Verificar variables de entorno necesarias
# ============================================================================

echo "TEST 3: Verificando variables de entorno..."

# Exportar variables por defecto para test
export SMTP_HOST=${SMTP_HOST:-smtp.zoho.eu}
export SMTP_PORT=${SMTP_PORT:-587}
export SMTP_USER=${SMTP_USER:-rafael.canelon@rhinometric.com}
export SMTP_PASSWORD=${SMTP_PASSWORD:-271211Rc$}
export ALERT_EMAIL_TO=${ALERT_EMAIL_TO:-rafael.canelon@rhinometric.com}

echo "✅ SMTP_HOST: $SMTP_HOST"
echo "✅ SMTP_PORT: $SMTP_PORT"
echo "✅ SMTP_USER: $SMTP_USER"
echo "✅ SMTP_PASSWORD: [CONFIGURADO]"
echo "✅ ALERT_EMAIL_TO: $ALERT_EMAIL_TO"

echo ""

# ============================================================================
# TEST 4: Test de sintaxis Python
# ============================================================================

echo "TEST 4: Validando sintaxis Python..."

python3 -m py_compile license-monitor/license_monitor.py 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Sintaxis Python válida"
else
    echo "❌ ERROR: Sintaxis Python inválida"
    exit 1
fi

echo ""

# ============================================================================
# TEST 5: Test de importaciones
# ============================================================================

echo "TEST 5: Verificando importaciones Python..."

python3 -c "
import sys
import json
import time
import smtplib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
print('✅ Todas las importaciones OK')
" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Todas las librerías disponibles"
else
    echo "❌ ERROR: Faltan librerías Python"
    exit 1
fi

echo ""

# ============================================================================
# TEST 6: Test de funciones clave
# ============================================================================

echo "TEST 6: Validando funciones del monitor..."

# Crear script de test
cat > /tmp/test_monitor_functions.py << 'EOTEST'
import sys
sys.path.insert(0, 'license-monitor')

# Importar módulo
from license_monitor import (
    find_license_file,
    load_license,
    get_days_until_expiration,
    load_alert_state,
    save_alert_state,
    get_email_template
)

print("✅ find_license_file importado")
print("✅ load_license importado")
print("✅ get_days_until_expiration importado")
print("✅ load_alert_state importado")
print("✅ save_alert_state importado")
print("✅ get_email_template importado")

# Test básico de funciones
license_path = find_license_file()
if license_path:
    print(f"✅ Licencia encontrada: {license_path}")
    
    license_data = load_license(license_path)
    if license_data:
        print(f"✅ Licencia cargada: {license_data.get('customer')}")
        
        days = get_days_until_expiration(license_data)
        if days is not None:
            print(f"✅ Días hasta expiración: {days}")
        else:
            print("⚠️  No se pudo calcular expiración")
    else:
        print("⚠️  No se pudo cargar licencia")
else:
    print("ℹ️  Licencia no encontrada (OK en test)")

# Test de template
test_license = {
    'customer': 'TestCompany',
    'type': 'trial',
    'expires': '2025-12-31'
}
subject, body = get_email_template(10, test_license)
if subject and body and len(body) > 1000:
    print(f"✅ Template de email generado: {len(body)} bytes")
else:
    print("❌ Template de email inválido")
    sys.exit(1)

print("\n✅ TODAS LAS FUNCIONES OK")
EOTEST

python3 /tmp/test_monitor_functions.py 2>&1
TEST_RESULT=$?

rm -f /tmp/test_monitor_functions.py

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Funciones del monitor validadas"
else
    echo "❌ ERROR: Funciones del monitor fallan"
    exit 1
fi

echo ""

# ============================================================================
# TEST 7: Test de construcción de imagen Docker
# ============================================================================

echo "TEST 7: Verificando construcción de imagen Docker..."

echo "ℹ️  Construyendo imagen (esto puede tardar 1-2 minutos)..."

docker build -t rhinometric-license-monitor:test -f license-monitor/Dockerfile license-monitor/ > /tmp/docker_build.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Imagen Docker construida exitosamente"
    
    # Verificar tamaño de imagen
    size=$(docker images rhinometric-license-monitor:test --format "{{.Size}}")
    echo "   Tamaño: $size"
    
    # Limpiar imagen de test
    docker rmi rhinometric-license-monitor:test > /dev/null 2>&1
else
    echo "❌ ERROR: Fallo en construcción de imagen"
    echo ""
    echo "Log de construcción:"
    tail -20 /tmp/docker_build.log
    exit 1
fi

rm -f /tmp/docker_build.log

echo ""

# ============================================================================
# TEST 8: Verificar volúmenes necesarios
# ============================================================================

echo "TEST 8: Verificando volúmenes necesarios..."

# Verificar licencia
if [ -f "licenses/cliente.lic" ]; then
    echo "✅ Licencia disponible: licenses/cliente.lic"
else
    echo "⚠️  Licencia no encontrada (necesaria para test real)"
fi

# Verificar clave pública
if [ -f "security/rhinometric_public.pem" ]; then
    echo "✅ Clave pública disponible: security/rhinometric_public.pem"
else
    echo "❌ Clave pública no encontrada"
    exit 1
fi

# Verificar directorio de logs
mkdir -p "${HOME}/rhinometric_data_v2.2/license-monitor/logs"
if [ -d "${HOME}/rhinometric_data_v2.2/license-monitor/logs" ]; then
    echo "✅ Directorio de logs creado"
else
    echo "❌ No se pudo crear directorio de logs"
    exit 1
fi

echo ""

# ============================================================================
# RESUMEN
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "✅ TODOS LOS TESTS DEL LICENSE MONITOR PASARON"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Próximos pasos para test real:"
echo ""
echo "  1. Iniciar solo el monitor:"
echo "     docker compose -f docker-compose-v2.2.0.yml up -d license-monitor"
echo ""
echo "  2. Ver logs en tiempo real:"
echo "     docker logs rhinometric-license-monitor -f"
echo ""
echo "  3. Ver estado de alertas:"
echo "     cat \${HOME}/rhinometric_data_v2.2/license-monitor/rhinometric_alerts_sent.json"
echo ""
echo "  4. Test manual de alerta (modificar días en licencia):"
echo "     # Editar licenses/cliente.lic y cambiar 'expires' a fecha próxima"
echo "     # Reiniciar monitor: docker compose -f docker-compose-v2.2.0.yml restart license-monitor"
echo ""
echo "  5. Verificar email de prueba:"
echo "     # Monitor enviará email si días <= 10/3/1"
echo "     # Revisar logs del monitor para ver si email fue enviado"
echo ""
echo "Configuración SMTP actual:"
echo "  Host: $SMTP_HOST"
echo "  Port: $SMTP_PORT"
echo "  User: $SMTP_USER"
echo "  To: $ALERT_EMAIL_TO"
echo ""
