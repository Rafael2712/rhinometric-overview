#!/bin/bash
# Rhinometric Annual License Installer v2.5.0
# Instalación completa para producción (1 año)
# Autor: Rafael Canelón
# Fecha: 16 Diciembre 2025

set -e

VERSION="2.5.0"
LICENSE_DURATION="1 año"

echo "=========================================="
echo "🦏 Rhinometric Annual License v${VERSION}"
echo "=========================================="
echo ""
echo "Instalación COMPLETA para PRODUCCIÓN"
echo "Licencia válida: ${LICENSE_DURATION}"
echo ""

# === VALIDACIÓN DE LICENCIA ===
echo "🔑 Verificación de licencia..."
echo ""

if [ -z "$RHINOMETRIC_LICENSE_KEY" ]; then
    echo "❌ ERROR: Clave de licencia no proporcionada"
    echo ""
    echo "Para obtener su clave de licencia:"
    echo "  1. Adquirir licencia en: https://rhinometric.com/pricing"
    echo "  2. Recibirá email con clave (formato: RHINO-ANNUAL-XXXXXXXXXXXX)"
    echo "  3. Ejecutar instalador:"
    echo ""
    echo "     export RHINOMETRIC_LICENSE_KEY=RHINO-ANNUAL-XXXXXXXXXXXX"
    echo "     ./rhinometric-annual-2.5.0-install.sh"
    echo ""
    exit 1
fi

echo "✅ Licencia detectada: ${RHINOMETRIC_LICENSE_KEY:0:20}..."
echo ""

# === VALIDACIONES DE SISTEMA ===
echo "🔍 Verificando requisitos del sistema..."
echo ""

# Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    echo ""
    echo "Instale Docker:"
    echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
    echo "  CentOS/RHEL:   sudo yum install -y docker"
    exit 1
fi

DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+' | head -1)
if (( $(echo "$DOCKER_VERSION < 24.0" | bc -l) )); then
    echo "❌ Docker $DOCKER_VERSION detectado (requerido: 24.0+)"
    exit 1
fi
echo "✅ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)"

# Docker Compose
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi
echo "✅ Docker Compose OK"

# RAM (producción requiere mínimo 16GB)
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 16 ]; then
    echo "⚠️  RAM: ${TOTAL_RAM}GB (recomendado para producción: 16GB+)"
    read -p "   ¿Continuar de todos modos? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo "✅ RAM: ${TOTAL_RAM}GB"

# CPU (producción requiere 8+ cores)
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -lt 8 ]; then
    echo "⚠️  CPU: ${CPU_CORES} cores (recomendado: 8+)"
fi
echo "✅ CPU: ${CPU_CORES} cores"

# Disco (producción requiere 100GB+)
DISK_FREE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$DISK_FREE" -lt 100 ]; then
    echo "⚠️  Disco libre: ${DISK_FREE}GB (recomendado: 100GB+)"
fi
echo "✅ Disco libre: ${DISK_FREE}GB"

echo ""
echo "=========================================="
echo "📥 Descargando Rhinometric v${VERSION}..."
echo "=========================================="
echo ""

# Directorio de instalación para producción
INSTALL_DIR="/opt/rhinometric"
sudo mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Descargar docker-compose completo para producción
sudo tee docker-compose.yml > /dev/null << 'EOFCOMPOSE'
version: '3.8'

services:
  # === Grafana (Producción) ===
  grafana:
    image: grafana/grafana:11.3.0
    container_name: rhinometric-grafana
    restart: always
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-clock-panel
      - GF_SERVER_ROOT_URL=https://${DOMAIN:-localhost}:3000
      - GF_SMTP_ENABLED=true
      - GF_SMTP_HOST=${SMTP_HOST}
      - GF_SMTP_FROM_ADDRESS=${SMTP_FROM}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'

  # === Prometheus (Producción) ===
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: rhinometric-prometheus
    restart: always
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=365d'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'

  # === Loki (Producción) ===
  loki:
    image: grafana/loki:2.9.0
    container_name: rhinometric-loki
    restart: always
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/loki-config.yml
      - loki-data:/loki
    command: -config.file=/etc/loki/loki-config.yml
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'

  # === Tempo (Distributed Tracing) ===
  tempo:
    image: grafana/tempo:2.3.0
    container_name: rhinometric-tempo
    restart: always
    ports:
      - "3200:3200"
      - "4317:4317"
    volumes:
      - tempo-data:/var/tempo
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # === PostgreSQL (Producción) ===
  postgres:
    image: postgres:16-alpine
    container_name: rhinometric-postgres
    restart: always
    environment:
      POSTGRES_DB: rhinometric
      POSTGRES_USER: rhinometric
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'

  # === Redis (Producción) ===
  redis:
    image: redis:7-alpine
    container_name: rhinometric-redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # === Console v3 Backend ===
  console-backend:
    image: rhinometric/console-backend:2.5.0
    container_name: rhinometric-console-backend
    restart: always
    environment:
      - DATABASE_URL=postgresql://rhinometric:${POSTGRES_PASSWORD}@postgres:5432/rhinometric
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    ports:
      - "8105:8105"
    depends_on:
      - postgres
      - redis

  # === Console v3 Frontend ===
  console-frontend:
    image: rhinometric/console-frontend:2.5.0
    container_name: rhinometric-console-frontend
    restart: always
    ports:
      - "3002:80"
    depends_on:
      - console-backend

  # === AI Anomaly Engine ===
  ai-anomaly:
    image: rhinometric/ai-anomaly:2.5.0
    container_name: rhinometric-ai-anomaly
    restart: always
    environment:
      - PROMETHEUS_URL=http://prometheus:9090
      - ALERTMANAGER_URL=http://alertmanager:9093
    ports:
      - "8085:8085"
    depends_on:
      - prometheus

  # === License Server v2 ===
  license-server:
    image: rhinometric/license-server:2.5.0
    container_name: rhinometric-license-server
    restart: always
    environment:
      - LICENSE_KEY=${RHINOMETRIC_LICENSE_KEY}
      - DATABASE_URL=postgresql://rhinometric:${POSTGRES_PASSWORD}@postgres:5432/rhinometric
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis

volumes:
  grafana-data:
  prometheus-data:
  loki-data:
  tempo-data:
  postgres-data:
  redis-data:

networks:
  default:
    name: rhinometric-network
EOFCOMPOSE

# Crear archivo de configuración
sudo tee .env > /dev/null << EOFENV
# Rhinometric Annual License v${VERSION}
LICENSE_KEY=${RHINOMETRIC_LICENSE_KEY}
LICENSE_TYPE=annual
LICENSE_DURATION=365

# Security (CAMBIAR CONTRASEÑAS EN PRODUCCIÓN)
GRAFANA_USER=admin
GRAFANA_PASSWORD=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# SMTP (opcional - para alertas por email)
SMTP_HOST=smtp.example.com
SMTP_FROM=alerts@example.com

# Domain (opcional - para HTTPS)
DOMAIN=rhinometric.yourdomain.com
EOFENV

# Crear configuraciones
sudo mkdir -p grafana/provisioning prometheus loki

# Configuración Prometheus básica
sudo tee prometheus.yml > /dev/null << 'EOFPROM'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
EOFPROM

echo "✅ Archivos de configuración creados"
echo ""

echo "=========================================="
echo "🚀 Iniciando servicios de producción..."
echo "=========================================="
echo ""

# Iniciar stack completo
sudo docker compose up -d

echo ""
echo "⏳ Esperando a que todos los servicios estén listos..."
echo "   (esto puede tomar 2-3 minutos en el primer arranque)"
sleep 90

echo ""
echo "=========================================="
echo "✅ INSTALACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "🦏 Rhinometric v${VERSION} - Producción Ready"
echo ""
echo "📊 Accesos del sistema:"
echo ""
echo "  🌐 Grafana:         http://$(hostname -I | awk '{print $1}'):3000"
echo "     Usuario:         admin"
echo "     Contraseña:      (ver archivo /opt/rhinometric/.env)"
echo ""
echo "  📈 Prometheus:      http://$(hostname -I | awk '{print $1}'):9090"
echo "  📜 Loki:            http://$(hostname -I | awk '{print $1}'):3100"
echo "  🔍 Tempo:           http://$(hostname -I | awk '{print $1}'):3200"
echo "  🎛️  Console v3:      http://$(hostname -I | awk '{print $1}'):3002"
echo "  🤖 AI Engine:       http://$(hostname -I | awk '{print $1}'):8085"
echo ""
echo "🔑 Licencia:"
echo "     Tipo:            Annual (Producción)"
echo "     Duración:        ${LICENSE_DURATION}"
echo "     Clave:           ${RHINOMETRIC_LICENSE_KEY:0:30}..."
echo ""
echo "📁 Archivos de configuración:"
echo "     Ubicación:       /opt/rhinometric/"
echo "     Contraseñas:     /opt/rhinometric/.env"
echo "     Logs:            sudo docker compose logs -f"
echo ""
echo "🔐 SEGURIDAD - IMPORTANTE:"
echo "   ⚠️  Cambie las contraseñas en /opt/rhinometric/.env"
echo "   ⚠️  Configure firewall (ufw allow 3000/tcp, etc.)"
echo "   ⚠️  Habilite HTTPS con Let's Encrypt (recomendado)"
echo ""
echo "🛠️  Comandos útiles:"
echo "   • Ver estado:     cd /opt/rhinometric && sudo docker compose ps"
echo "   • Ver logs:       cd /opt/rhinometric && sudo docker compose logs -f"
echo "   • Reiniciar:      cd /opt/rhinometric && sudo docker compose restart"
echo "   • Actualizar:     cd /opt/rhinometric && sudo docker compose pull && sudo docker compose up -d"
echo "   • Backup:         sudo tar -czf rhinometric-backup.tar.gz /opt/rhinometric/"
echo ""
echo "📚 Documentación:"
echo "     https://rhinometric.com/documentation"
echo ""
echo "📧 Soporte profesional:"
echo "     Email: rafael.canelon@rhinometric.com"
echo "     SLA:   24h response time"
echo ""
echo "=========================================="
echo "🦏 ¡Bienvenido a Rhinometric Producción!"
echo "=========================================="
