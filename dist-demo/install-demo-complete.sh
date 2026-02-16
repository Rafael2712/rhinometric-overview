#!/bin/bash
echo "╔══════════════════════════════════════════════╗"
echo "║   RHINOMETRIC DEMO - Instalador Completo     ║"
echo "╚══════════════════════════════════════════════╝"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no instalado"
    exit 1
fi

# Crear estructura
mkdir -p rhinometric-demo
cd rhinometric-demo

# Generar licencia demo 15 días
cat > license.lic << 'LICENSE'
eyJpZCI6ICJkZW1vLTIwMjQiLCAiY3VzdG9tZXIiOiAiRGVtb0NsaWVudCIsICJ0eXBlIjogInRyaWFsIiwgImlzc3VlZCI6ICIyMDI0LTAxLTE3IiwgImV4cGlyZXMiOiAiMjAyNC0wMi0wMSIsICJmZWF0dXJlcyI6IHsibWF4X25vZGVzIjogNSwgImFsZXJ0aW5nIjogdHJ1ZSwgImRhc2hib2FyZHMiOiAxMCwgInJldGVudGlvbl9kYXlzIjogN319
LICENSE

# Docker Compose simplificado para demo
cat > docker-compose.yml << 'COMPOSE'
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=demo2024
      - GF_AUTH_ANONYMOUS_ENABLED=false
    volumes:
      - ./license.lic:/var/lib/grafana/license.lic:ro
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    restart: unless-stopped
COMPOSE

# Configuración Prometheus
cat > prometheus.yml << 'PROM'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'demo'
    static_configs:
      - targets: ['localhost:9090']
PROM

# Iniciar
docker-compose up -d

echo ""
echo "✅ DEMO INSTALADA"
echo "══════════════════════════════"
echo "Grafana: http://localhost:3000"
echo "Usuario: admin"
echo "Contraseña: demo2024"
echo "Validez: 15 días"
echo "══════════════════════════════"
