#!/bin/bash
#
# RHINOMETRIC STORAGE POLICIES INSTALLATION
# Aplica todas las políticas de almacenamiento y retención
#
# Uso:
#   chmod +x scripts/install-storage-policies.sh
#   sudo ./scripts/install-storage-policies.sh
#
# Referencia: STORAGE_POLICY.md, STORAGE_STRATEGY.md
#

set -euo pipefail

echo "========================================"
echo " RHINOMETRIC STORAGE POLICIES INSTALLER"
echo "========================================"
echo ""
echo "Este script configura:"
echo "  1. Docker log rotation (50MB × 3 files)"
echo "  2. Disk Guardian (monitoreo cada 5 min)"
echo "  3. Alertas Prometheus (disk usage)"
echo "  4. Verificaciones de retención"
echo ""

# Verificar permisos root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ ERROR: Este script requiere permisos root"
    echo "Ejecutar: sudo $0"
    exit 1
fi

# Directorio base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "${SCRIPT_DIR}")"

echo "📂 Directorio base: ${BASE_DIR}"
echo ""

# ========================================
# 1. DOCKER LOG ROTATION
# ========================================
echo "1️⃣  Configurando Docker log rotation..."

DAEMON_JSON="/etc/docker/daemon.json"

if [ -f "${DAEMON_JSON}" ]; then
    echo "⚠️  ${DAEMON_JSON} ya existe"
    echo "Contenido actual:"
    cat "${DAEMON_JSON}"
    echo ""
    read -p "¿Sobrescribir con configuración de log rotation? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "⏩ Saltando configuración Docker log rotation"
        SKIP_DOCKER_RESTART=true
    else
        SKIP_DOCKER_RESTART=false
    fi
else
    SKIP_DOCKER_RESTART=false
fi

if [ "${SKIP_DOCKER_RESTART}" = false ]; then
    cat > "${DAEMON_JSON}" <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3",
    "compress": "true"
  }
}
EOF
    echo "✅ ${DAEMON_JSON} configurado"
    echo "   Límite por contenedor: 150 MB (50MB × 3 archivos)"
    
    # Preguntar antes de reiniciar Docker
    echo ""
    echo "⚠️  ADVERTENCIA: Reiniciar Docker daemon requiere ~1 minuto de downtime"
    read -p "¿Reiniciar Docker daemon ahora? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Reiniciando Docker daemon..."
        systemctl restart docker
        echo "✅ Docker daemon reiniciado"
        sleep 5
        echo "✅ Servicios Docker reactivados"
    else
        echo "⏩ Aplicar manualmente: systemctl restart docker"
    fi
else
    echo "✅ Docker log rotation ya configurado"
fi

echo ""

# ========================================
# 2. DISK GUARDIAN
# ========================================
echo "2️⃣  Instalando Disk Guardian..."

DISK_GUARDIAN_SCRIPT="${BASE_DIR}/scripts/disk-guardian.sh"
DISK_GUARDIAN_BIN="/usr/local/bin/disk-guardian"

if [ ! -f "${DISK_GUARDIAN_SCRIPT}" ]; then
    echo "❌ ERROR: ${DISK_GUARDIAN_SCRIPT} no encontrado"
    echo "Ejecutar desde el directorio correcto"
    exit 1
fi

# Copiar a /usr/local/bin
cp "${DISK_GUARDIAN_SCRIPT}" "${DISK_GUARDIAN_BIN}"
chmod +x "${DISK_GUARDIAN_BIN}"
echo "✅ Disk Guardian instalado: ${DISK_GUARDIAN_BIN}"

# Configurar cron
CRON_JOB="*/5 * * * * ${DISK_GUARDIAN_BIN} >> /var/log/disk-guardian.log 2>&1"

if crontab -l 2>/dev/null | grep -q "disk-guardian"; then
    echo "✅ Cron job ya configurado"
else
    (crontab -l 2>/dev/null; echo "${CRON_JOB}") | crontab -
    echo "✅ Cron job añadido (cada 5 minutos)"
fi

# Crear log file
touch /var/log/disk-guardian.log
chmod 644 /var/log/disk-guardian.log
echo "✅ Log file: /var/log/disk-guardian.log"

# Test run
echo "🧪 Ejecutando test..."
bash "${DISK_GUARDIAN_BIN}" || echo "⚠️  Test ejecutado (verificar /var/log/disk-guardian.log)"

echo ""

# ========================================
# 3. ALERTAS PROMETHEUS
# ========================================
echo "3️⃣  Verificando alertas Prometheus..."

ALERTS_FILE="${BASE_DIR}/config/rules/disk-alerts.yml"

if [ -f "${ALERTS_FILE}" ]; then
    echo "✅ Alertas de disco configuradas: ${ALERTS_FILE}"
    echo "   Ver: curl http://localhost:9090/api/v1/rules"
else
    echo "⚠️  ${ALERTS_FILE} no encontrado"
    echo "   Crear manualmente (ver STORAGE_STRATEGY.md)"
fi

echo ""

# ========================================
# 4. VERIFICACIONES DE RETENCIÓN
# ========================================
echo "4️⃣  Verificando configuraciones de retención..."

# Prometheus
echo "📊 Prometheus:"
if docker inspect rhinometric-prometheus 2>/dev/null | grep -q "storage.tsdb.retention"; then
    echo "   ✅ Retención configurada"
    docker inspect rhinometric-prometheus | grep "storage.tsdb.retention" | head -2
else
    echo "   ⚠️  Retención NO configurada"
    echo "   Añadir en docker-compose-v2.5.0-core.yml:"
    echo "     --storage.tsdb.retention.time=30d"
    echo "     --storage.tsdb.retention.size=50GB"
fi

# Loki
echo ""
echo "📝 Loki:"
LOKI_CONFIG="${BASE_DIR}/config/loki-config.yml"
if [ -f "${LOKI_CONFIG}" ]; then
    if grep -q "retention_period" "${LOKI_CONFIG}"; then
        echo "   ✅ Retención configurada"
        grep "retention_period" "${LOKI_CONFIG}" | head -1
    else
        echo "   ⚠️  Retención NO configurada"
        echo "   Añadir en ${LOKI_CONFIG}:"
        echo "     limits_config:"
        echo "       retention_period: 168h  # 7 días"
    fi
else
    echo "   ⚠️  ${LOKI_CONFIG} no encontrado"
fi

# Jaeger
echo ""
echo "🔍 Jaeger:"
if docker inspect rhinometric-jaeger 2>/dev/null | grep -q "BADGER_TTL"; then
    echo "   ✅ TTL configurado"
    docker inspect rhinometric-jaeger | grep "BADGER_TTL"
else
    echo "   ⚠️  TTL NO configurado"
    echo "   Añadir en docker-compose-v2.5.0-core.yml:"
    echo "     environment:"
    echo "       BADGER_TTL: \"72h\"  # 3 días"
fi

echo ""

# ========================================
# 5. RESUMEN FINAL
# ========================================
echo "========================================"
echo " RESUMEN DE INSTALACIÓN"
echo "========================================"
echo ""
echo "✅ Completado:"
echo "   - Docker log rotation: ${DAEMON_JSON}"
echo "   - Disk Guardian: ${DISK_GUARDIAN_BIN}"
echo "   - Cron job: Cada 5 minutos"
echo ""
echo "⚠️  Acción manual requerida:"
echo "   1. Aplicar retenciones en docker-compose-v2.5.0-core.yml"
echo "   2. Configurar retention_period en ${LOKI_CONFIG}"
echo "   3. Crear ${ALERTS_FILE} (ver STORAGE_STRATEGY.md)"
echo "   4. Reiniciar stack: docker compose -f docker-compose-v2.5.0-core.yml up -d --force-recreate"
echo ""
echo "📚 Documentación:"
echo "   - STORAGE_POLICY.md: Política ejecutiva"
echo "   - STORAGE_STRATEGY.md: Implementación técnica"
echo "   - STORAGE_INVENTORY.md: Inventario de volúmenes"
echo "   - STORAGE_IMPLEMENTATION_STATUS.md: Estado implementación"
echo ""
echo "✅ Instalación completada"
echo "========================================"
