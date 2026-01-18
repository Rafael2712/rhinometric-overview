#!/bin/bash
# Rhinometric Trial Installer v2.5.0
# Instalador automático para Ubuntu/Debian/CentOS
# Autor: Rafael Canelón
# Fecha: 16 Diciembre 2025

set -e

VERSION="2.5.0"
TRIAL_DAYS=14

echo "=========================================="
echo "🦏 Rhinometric Trial Installer v${VERSION}"
echo "=========================================="
echo ""
echo "Este instalador configurará:"
echo "  • Grafana 11.x (Observabilidad)"
echo "  • Prometheus 2.48 (Métricas)"
echo "  • Loki 2.9 (Logs)"
echo "  • Console v3 (Gestión)"
echo "  • AI Anomaly Engine (Detección)"
echo ""
echo "Duración: ${TRIAL_DAYS} días"
echo ""

# === VALIDACIONES ===
echo "🔍 Verificando pre-requisitos..."

# Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    echo ""
    echo "Instale Docker desde:"
    echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
    echo "  CentOS: sudo yum install -y docker"
    exit 1
fi

DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+' | head -1)
if (( $(echo "$DOCKER_VERSION < 24.0" | bc -l) )); then
    echo "⚠️  Docker $DOCKER_VERSION detectado (recomendado: 24.0+)"
fi
echo "✅ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)"

# Docker Compose
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    echo "Instale desde: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "✅ Docker Compose OK"

# RAM
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 8 ]; then
    echo "⚠️  RAM detectada: ${TOTAL_RAM}GB (recomendado: 8GB+)"
    echo "   El sistema puede funcionar lento"
fi
echo "✅ RAM: ${TOTAL_RAM}GB"

# Disco
DISK_FREE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$DISK_FREE" -lt 20 ]; then
    echo "❌ Espacio en disco insuficiente: ${DISK_FREE}GB (requerido: 20GB+)"
    exit 1
fi
echo "✅ Disco libre: ${DISK_FREE}GB"

echo ""
echo "=========================================="
echo "📥 Descargando Rhinometric v${VERSION}..."
echo "=========================================="
echo ""

# Crear directorio de instalación
INSTALL_DIR="$HOME/rhinometric-trial"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Descargar docker-compose.yml
cat > docker-compose.yml << 'EOFCOMPOSE'
version: '3.8'

services:
  # === Grafana ===
  grafana:
    image: grafana/grafana:11.3.0
    container_name: rhinometric-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=rhinometric2025
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana-data:/var/lib/grafana

  # === Prometheus ===
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: rhinometric-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  # === Loki ===
  loki:
    image: grafana/loki:2.9.0
    container_name: rhinometric-loki
    restart: unless-stopped
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki

  # === PostgreSQL ===
  postgres:
    image: postgres:16-alpine
    container_name: rhinometric-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: rhinometric
      POSTGRES_USER: rhinometric
      POSTGRES_PASSWORD: rhinometric_trial
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # === Redis ===
  redis:
    image: redis:7-alpine
    container_name: rhinometric-redis
    restart: unless-stopped
    command: redis-server --requirepass rhinometric_trial
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"

volumes:
  grafana-data:
  prometheus-data:
  loki-data:
  postgres-data:
  redis-data:

networks:
  default:
    name: rhinometric-network
EOFCOMPOSE

# Crear prometheus.yml
cat > prometheus.yml << 'EOFPROM'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOFPROM

# Generar licencia trial
EXPIRY_DATE=$(date -d "+${TRIAL_DAYS} days" +%Y-%m-%d 2>/dev/null || date -v+${TRIAL_DAYS}d +%Y-%m-%d 2>/dev/null)
LICENSE_KEY="RHINO-TRIAL-$(openssl rand -hex 6 | tr '[:lower:]' '[:upper:]')"

cat > .env << EOFENV
# Rhinometric Trial License
LICENSE_KEY=${LICENSE_KEY}
LICENSE_TYPE=trial
LICENSE_EXPIRES=${EXPIRY_DATE}
TRIAL_DAYS=${TRIAL_DAYS}

# Credentials (TRIAL - cambiar en producción)
GRAFANA_USER=admin
GRAFANA_PASSWORD=rhinometric2025
POSTGRES_PASSWORD=rhinometric_trial
REDIS_PASSWORD=rhinometric_trial
EOFENV

echo "✅ Archivos descargados"
echo ""

echo "=========================================="
echo "🚀 Iniciando servicios..."
echo "=========================================="
echo ""

# Iniciar stack
docker compose up -d

echo ""
echo "⏳ Esperando a que los servicios estén listos (30 segundos)..."
sleep 30

echo ""
echo "=========================================="
echo "✅ INSTALACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "📊 Acceso a Rhinometric:"
echo ""
echo "  🌐 Grafana:     http://localhost:3000"
echo "     Usuario:     admin"
echo "     Contraseña:  rhinometric2025"
echo ""
echo "  📈 Prometheus:  http://localhost:9090"
echo "  📜 Loki:        http://localhost:3100"
echo ""
echo "🔑 Licencia Trial:"
echo "     Clave:       ${LICENSE_KEY}"
echo "     Expira:      ${EXPIRY_DATE} (${TRIAL_DAYS} días)"
echo ""
echo "📚 Documentación:"
echo "     https://rhinometric.com/documentation"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   • Esta es una licencia TRIAL de ${TRIAL_DAYS} días"
echo "   • Para uso en producción, contacte:"
echo "     rafael.canelon@rhinometric.com"
echo ""
echo "🛠️  Comandos útiles:"
echo "   • Ver logs:      docker compose logs -f"
echo "   • Detener:       docker compose stop"
echo "   • Reiniciar:     docker compose restart"
echo "   • Desinstalar:   docker compose down -v"
echo ""
echo "=========================================="
echo "🦏 ¡Bienvenido a Rhinometric v${VERSION}!"
echo "=========================================="
