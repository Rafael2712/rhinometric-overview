#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# RHINOMETRIC TRIAL - INSTALADOR SIMPLE PARA MAC
# Copia este archivo completo y pégalo en la Mac
# ═══════════════════════════════════════════════════════════════

set -e

clear
echo "════════════════════════════════════════════════════════"
echo "  🦏 RHINOMETRIC TRIAL - INSTALADOR AUTOMÁTICO"
echo "════════════════════════════════════════════════════════"
echo ""

# Verificar Docker
echo "✓ Verificando Docker..."
if ! command -v docker &> /dev/null || ! docker info &> /dev/null 2>&1; then
    echo "❌ Docker no está instalado o no está corriendo"
    echo ""
    echo "Instala Docker Desktop desde:"
    echo "https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Crear directorio
INSTALL_DIR="$HOME/rhinometric-trial"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "✓ Docker OK"
echo "✓ Instalando en: $INSTALL_DIR"
echo ""

# Crear docker-compose.yml
echo "✓ Creando configuración..."
cat > docker-compose.yml << 'EOFCOMPOSE'
services:
  postgres:
    image: postgres:15-alpine
    container_name: rhino-postgres
    environment:
      POSTGRES_DB: rhinometric
      POSTGRES_USER: rhino
      POSTGRES_PASSWORD: rhino123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - rhino
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: rhino-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=7d'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - rhino
    ports:
      - "9090:9090"
    restart: unless-stopped

  loki:
    image: grafana/loki:2.9.3
    container_name: rhino-loki
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - ./loki.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    networks:
      - rhino
    ports:
      - "3100:3100"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.2.3
    container_name: rhino-grafana
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin123
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_AUTH_ANONYMOUS_ENABLED: "false"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
    networks:
      - rhino
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - prometheus
      - loki

networks:
  rhino:
    driver: bridge

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
  loki_data:
EOFCOMPOSE

# Crear prometheus.yml
cat > prometheus.yml << 'EOFPROM'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
EOFPROM

# Crear loki.yml
cat > loki.yml << 'EOFLOKI'
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 1h
  max_chunk_age: 1h
  chunk_target_size: 1048576
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  retention_period: 168h
  reject_old_samples: true
  reject_old_samples_max_age: 168h

compactor:
  working_directory: /loki/compactor
  shared_store: filesystem
  retention_enabled: true
  retention_delete_delay: 2h
EOFLOKI

# Crear datasources.yml
cat > datasources.yml << 'EOFDS'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
EOFDS

echo "✓ Configuración creada"
echo ""

# Descargar imágenes
echo "⏳ Descargando componentes (esto tarda 2-5 minutos)..."
docker compose pull

echo ""
echo "✓ Descarga completa"
echo ""

# Iniciar servicios
echo "🚀 Iniciando Rhinometric..."
docker compose up -d

echo ""
echo "⏳ Esperando que los servicios estén listos (30 segundos)..."
sleep 30

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ RHINOMETRIC INSTALADO CORRECTAMENTE"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🎨 GRAFANA:"
echo "   URL:      http://localhost:3000"
echo "   Usuario:  admin"
echo "   Password: admin123"
echo ""
echo "📈 PROMETHEUS:"
echo "   URL:      http://localhost:9090"
echo ""
echo "📝 LOKI:"
echo "   URL:      http://localhost:3100"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""
echo "Comandos útiles:"
echo "  Ver estado:    docker compose ps"
echo "  Ver logs:      docker compose logs -f"
echo "  Reiniciar:     docker compose restart"
echo "  Detener:       docker compose stop"
echo "  Eliminar todo: docker compose down -v"
echo ""
echo "Ubicación: $INSTALL_DIR"
echo ""
echo "🎉 ¡Listo! Abre http://localhost:3000 en tu navegador"
echo ""
