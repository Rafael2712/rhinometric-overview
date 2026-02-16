#!/usr/bin/env bash
set -euo pipefail

# Rhinometric Trial (macOS) — Full stack + exporters + PgBouncer (6 months)
# This script prepares a customer-ready folder at ~/rhinometric-trial and starts the stack.

echo "════════════════════════════════════════════════════════"
echo "  🦏 RHINOMETRIC TRIAL — Instalador macOS (6 meses)"
echo "════════════════════════════════════════════════════════"

# Preflight checks
if ! command -v docker &>/dev/null; then
  echo "❌ Docker no está instalado. Instala Docker Desktop y vuelve a ejecutar."; exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker Desktop no está corriendo. Ábrelo y vuelve a intentar."; exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_TRIAL="$SCRIPT_DIR/trial-package"
DEST="$HOME/rhinometric-trial"

echo "📁 Preparando carpeta de trabajo en: $DEST"
rm -rf "$DEST"
mkdir -p "$DEST"
cp -R "$SRC_TRIAL/"* "$DEST/"

# Required environment for trial-package services (license-server, postgres, grafana)
cat > "$DEST/.env" <<'ENV'
POSTGRES_DB=rhinometric
POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=rhino123
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin123
# Randomize in production
JWT_SECRET=replace_me_with_a_random_secret
ENV

# Dashboards: copy existing JSON dashboards into provisioning path
DASH_SRC_ROOT="$SCRIPT_DIR/grafana/dashboards"
DASH_DEST="$DEST/grafana/provisioning/dashboards"
mkdir -p "$DASH_DEST"
mkdir -p "$DEST/grafana/provisioning/dashboards/conf"

# Provider de dashboards para Grafana
cat > "$DEST/grafana/provisioning/dashboards/provider.yml" <<'GF'
apiVersion: 1
providers:
  - name: 'rhinometric-dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: true
GF

if compgen -G "$DASH_SRC_ROOT/*.json" > /dev/null; then
  echo "🖼️  Copiando dashboards a $DASH_DEST"
  cp -f "$DASH_SRC_ROOT"/*.json "$DASH_DEST/"
else
  echo "ℹ️  No se encontraron dashboards JSON en $DASH_SRC_ROOT; añadiendo dashboard básico de logs."
  # Dashboard mínimo de Logs por si no hay nada en el repo
  cat > "$DASH_DEST/Logs-Basico-Loki.json" <<'DASH'
{
  "id": null,
  "uid": "logs-basico",
  "title": "Logs Basico (Loki)",
  "timezone": "browser",
  "schemaVersion": 39,
  "version": 1,
  "panels": [
    {
      "type": "logs",
      "title": "Logs de contenedores",
      "datasource": { "type": "loki", "uid": "loki" },
      "gridPos": { "h": 18, "w": 24, "x": 0, "y": 0 },
      "options": {
        "showTime": true,
        "sortOrder": "Descending",
        "wrapLogMessage": true,
        "dedupStrategy": "none"
      },
      "targets": [
        {
          "expr": "{project=\"rhinometric\"} |~ \".*\"",
          "refId": "A"
        }
      ]
    }
  ]
}
DASH
fi

# Datasources de Grafana para Prometheus, Loki y Tempo
mkdir -p "$DEST/grafana/provisioning/datasources"
cat > "$DEST/grafana/provisioning/datasources/datasources.yml" <<'DS'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    uid: loki
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
DS

# Promtail config (docker_sd + push a Loki) y Blackbox (fallback por defecto)
mkdir -p "$DEST/config"
# Promtail: generamos una config conocida que funciona con Docker Desktop
cat > "$DEST/config/promtail.yml" <<'PROMTAIL'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    labels:
      project: rhinometric
      environment: trial
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_compose_service']
        target_label: 'service'
      - source_labels: ['__meta_docker_compose_project']
        target_label: 'project'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
PROMTAIL

# Blackbox: usar el del repo si existe, si no generar uno mínimo
if [ -f "$SCRIPT_DIR/config/blackbox.yml" ]; then
  cp -f "$SCRIPT_DIR/config/blackbox.yml" "$DEST/config/blackbox.yml"
else
  cat > "$DEST/config/blackbox.yml" <<'BBX'
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      method: GET
BBX
fi

# PgBouncer config (trial-friendly: trust auth inside the docker network)
mkdir -p "$DEST/pgbouncer"
cat > "$DEST/pgbouncer/pgbouncer.ini" <<'PGB'
[databases]
appdb   = host=postgres port=5432 dbname=rhinometric pool_mode=transaction
postgres= host=postgres port=5432 dbname=postgres

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = trust
ignore_startup_parameters = extra_float_digits
admin_users = postgres
pool_mode = transaction
default_pool_size = 20
max_client_conn = 200
PGB
echo '"postgres" "md50000000000000000000000000000000"' > "$DEST/pgbouncer/userlist.txt"

# Build local PgBouncer exporter image (uses repo Dockerfile and scripts)
echo "🔧 Construyendo imagen local: rhinometric/pgbouncer-exporter:local"
EXTRA_DIR="$DEST/extras"
mkdir -p "$EXTRA_DIR"
cp -f "$SCRIPT_DIR/Dockerfile.pgbouncer-exporter" "$EXTRA_DIR/"
cp -f "$SCRIPT_DIR/pgbouncer_exporter.py" "$EXTRA_DIR/"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
  cp -f "$SCRIPT_DIR/requirements.txt" "$EXTRA_DIR/"
else
  # Minimal requirements to run the exporter
  cat > "$EXTRA_DIR/requirements.txt" <<'REQ'
psycopg2-binary==2.9.9
prometheus_client==0.17.1
REQ
fi
(
  cd "$EXTRA_DIR"
  docker build -t rhinometric/pgbouncer-exporter:local -f Dockerfile.pgbouncer-exporter .
)

# Override compose to add exporters and PgBouncer
cat > "$DEST/docker-compose.override.addons.yml" <<'EOF'
services:
  pgbouncer:
    image: edoburu/pgbouncer:latest
    container_name: rhinometric-pgbouncer
    environment:
      DB_USER: postgres
      DB_PASSWORD: rhino123
    volumes:
      - ./pgbouncer/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini:ro
      - ./pgbouncer/userlist.txt:/etc/pgbouncer/userlist.txt:ro
    depends_on:
      - postgres
    networks: [rhinometric]
    restart: unless-stopped

  pgbouncer-exporter:
    image: rhinometric/pgbouncer-exporter:local
    container_name: rhinometric-pgbouncer-exporter
    environment:
      PGBOUNCER_HOST: pgbouncer
      PGBOUNCER_PORT: 6432
      PGBOUNCER_USER: postgres
      PGBOUNCER_PASSWORD: ''
      EXPORTER_PORT: 9127
      COLLECTION_INTERVAL: 15
    ports: ["9127:9127"]
    depends_on: [pgbouncer]
    networks: [rhinometric]
    restart: unless-stopped

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: rhinometric-postgres-exporter
    environment:
      DATA_SOURCE_NAME: postgresql://rhinometric:rhino123@postgres:5432/rhinometric?sslmode=disable
    networks: [rhinometric]
    restart: unless-stopped

  blackbox-exporter:
    image: prom/blackbox-exporter:latest
    container_name: rhinometric-blackbox-exporter
    command: ["--config.file=/etc/blackbox/blackbox.yml"]
    volumes:
      - ./config/blackbox.yml:/etc/blackbox/blackbox.yml:ro
    networks: [rhinometric]
    restart: unless-stopped

  promtail:
    image: grafana/promtail:2.9.0
    container_name: rhinometric-promtail
    command: -config.file=/etc/promtail/config.yml
    volumes:
      - ./config/promtail.yml:/etc/promtail/config.yml:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    networks: [rhinometric]
    restart: unless-stopped
    ports:
      - "9080:9080"
EOF

# Replace Prometheus config with one that includes the extra jobs
cat > "$DEST/config/prometheus.yml" <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'rhinometric-trial'
    environment: 'trial'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['prometheus:9090']

  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']

  - job_name: 'alertmanager'
    static_configs:
      - targets: ['alertmanager:9093']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'pgbouncer-exporter'
    static_configs:
      - targets: ['pgbouncer-exporter:9127']

  - job_name: 'promtail'
    static_configs:
      - targets: ['promtail:9080']

  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - http://grafana:3000
          - http://prometheus:9090
          - http://alertmanager:9093
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
EOF

(
  cd "$DEST"
  echo "\n📥 Descargando imágenes (puede tardar unos minutos)…"
  docker compose pull || true
  echo "\n🚀 Iniciando servicios…"
  docker compose -f docker-compose.yml -f docker-compose.override.addons.yml up -d
)

sleep 5
echo "\n════════════════════════════════════════════════════════"
echo "  ✅ Rhinometric Trial desplegado (6 meses)"
echo "════════════════════════════════════════════════════════"
echo "URLs:"
echo "  • Grafana:       http://localhost:3000   (admin / defínelo en $DEST/.env si procede)"
echo "  • Prometheus:    http://localhost:9090"
echo "  • Alertmanager:  http://localhost:9093"
echo "  • Loki:          http://localhost:3100"
echo "  • Tempo:         http://localhost:3200"
echo "\nCarpeta de despliegue: $DEST"
echo "Comandos útiles:"
echo "  cd $DEST"
echo "  docker compose ps"
echo "  docker compose logs -f"
echo "  docker compose -f docker-compose.yml -f docker-compose.override.addons.yml restart"
echo "  docker compose -f docker-compose.yml -f docker-compose.override.addons.yml down -v"

echo "\nℹ️  Nota: Esta versión Trial expira a los 180 días vía el servicio de licencias."
echo "      Retención de datos: 7 días."

exit 0
