# Rhinometric Dashboard Builder

**UI sin YAML** para crear dashboards de Grafana desde templates preconfigurados.

## ÌæØ Caracter√≠sticas

- **Wizard visual** - No requiere conocer PromQL ni YAML
- **Templates listos** - AI Anomaly, System Overview, App Performance
- **Integraci√≥n directa** - Crea en Grafana y abre autom√°ticamente
- **Backend API RESTful** - Express + Axios + Prometheus metrics
- **Frontend React** - Standalone con CDN (sin build)

## Ì≥¶ Componentes

### Backend API (:8001)
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /templates` - Lista de templates disponibles
- `POST /create` - Crear dashboard en Grafana

**Tecnolog√≠as:** Node.js, Express, Axios, prom-client

### Frontend UI (:3001)
- Wizard de 2 pasos: Selecci√≥n de template ‚Üí T√≠tulo personalizado ‚Üí Crear
- React standalone (CDN) sin compilaci√≥n
- CORS configurado para API en :8001

## Ì∫Ä Quick Start

### Backend
```bash
cd backend
npm install
npm start
# API running en http://localhost:8001
```

### Frontend
```bash
cd frontend
npm start
# UI running en http://localhost:3001
```

## Ì¥ß Configuraci√≥n

### Variables de Entorno (Backend)
```bash
PORT=8001
GRAFANA_URL=http://localhost:3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

### Templates Disponibles

#### 1. AI Anomaly Detection
- **Panels:** Detecciones 24h, Anomal√≠as activas, Modelos entrenados, Gr√°fico tiempo real
- **Queries:** 
  - `increase(rhinometric_anomaly_detections_total[24h])`
  - `rhinometric_anomaly_active_count`
  - `rate(rhinometric_anomaly_detections_total[5m])`

#### 2. System Overview
- **Panels:** CPU, Memory, Disk, Network
- **Queries:** node_exporter m√©tricas

#### 3. App Performance
- **Panels:** Req/sec, Error Rate, Avg Latency, Percentiles
- **Queries:** HTTP metrics

## Ì∞≥ Docker

```dockerfile
# Backend
FROM node:18-alpine
WORKDIR /app
COPY backend/package*.json ./
RUN npm ci --production
COPY backend/ .
EXPOSE 8001
CMD ["node", "server.js"]

# Frontend
FROM node:18-alpine
WORKDIR /app
COPY frontend/ .
RUN npm install -g serve
EXPOSE 3001
CMD ["serve", "-p", "3001", "-s", "."]
```

## Ì¥ó Integraci√≥n con Deploy/Demo

El Dashboard Builder est√° incluido en `docker-compose-demo.yml`:

```yaml
rhinometric-dashboard-builder:
  image: rhinometric/dashboard-builder:v2.5.0
  ports:
    - "8001:8001"
  environment:
    - GRAFANA_URL=http://grafana:3000
    - GRAFANA_USER=admin
    - GRAFANA_PASSWORD=rhinometric_demo
```

Acceso v√≠a Traefik: `https://demo.rhinometric.local/builder`

## Ì≥ä M√©tricas

El backend expone m√©tricas en `/metrics`:
- `dashboard_builder_requests_total` - Total de requests (method, route, status)
- `dashboard_builder_request_duration_seconds` - Duraci√≥n de requests (histogram)

Prometheus scrape config:
```yaml
- job_name: 'rhinometric-dashboard-builder'
  static_configs:
    - targets: ['rhinometric-dashboard-builder:8001']
  metrics_path: /metrics
```

## Ì∑™ Testing

```bash
# Health check
curl http://localhost:8001/health

# Listar templates
curl http://localhost:8001/templates

# Crear dashboard
curl -X POST http://localhost:8001/create \
  -H "Content-Type: application/json" \
  -d '{"template":"ai-anomaly","title":"Mi Dashboard AI"}'

# Response:
# {
#   "success": true,
#   "url": "http://localhost:3000/d/abc123/mi-dashboard-ai",
#   "uid": "abc123"
# }
```

## Ì∞õ Troubleshooting

### "Failed to create dashboard"
- Verificar credenciales Grafana (`GRAFANA_USER`/`GRAFANA_PASSWORD`)
- Confirmar que Grafana est√° accesible en `GRAFANA_URL`
- Revisar logs: `docker logs rhinometric-dashboard-builder-demo`

### "Error de conexi√≥n" en Frontend
- Verificar que backend est√© corriendo en :8001
- Comprobar CORS: `curl -I http://localhost:8001/health`
- Abrir DevTools ‚Üí Network ‚Üí buscar error de preflight

### Dashboard con "No data"
- Ejecutar `bash deploy/demo/scripts/anomaly-seed.sh` para generar m√©tricas
- Verificar datasource Prometheus UID: debe ser "prometheus"
- Comprobar targets en Prometheus: http://localhost:9090/targets

## Ì≥ö Referencias

- **API Grafana:** https://grafana.com/docs/grafana/latest/developers/http_api/dashboard/
- **Datasource UIDs:** Cr√≠tico para provisioning autom√°tico
- **Templates:** Basados en dashboards oficiales de Grafana
