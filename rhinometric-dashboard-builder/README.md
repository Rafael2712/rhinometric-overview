# RhinoMetric Dashboard Builder v2.2.0

**Herramienta visual para crear dashboards en Grafana sin conocimientos técnicos**

## 🎯 Descripción

Sistema que permite a usuarios no técnicos crear dashboards de monitoreo profesionales mediante:
- **Query Builder Visual**: Construye queries de Prometheus sin conocer PromQL
- **Panel Editor**: Configura paneles (gráficos, stats, gauges) con formularios simples
- **Template Library**: 6 dashboards pre-configurados listos para usar
- **Drag & Drop**: Organiza paneles visualmente con react-grid-layout
- **API REST**: 20+ endpoints para integración programática

## 📊 Características

### Backend (FastAPI + Python)
- **Grafana API Client**: CRUD completo de dashboards
- **Prometheus Query Builder**: 6 tipos de métricas con templates
  - CPU (usage, by_cpu, by_mode)
  - Memory (usage, available, total, used)
  - Disk (usage, io_read, io_write)
  - Network (receive, transmit, errors)
  - HTTP (request_rate, error_rate, latency_p95, latency_p99)
  - Database (connections, active_connections, slow_queries)
- **Panel System**: 6 tipos (Graph, Stat, Gauge, Table, Pie Chart, Heatmap)
- **Templates**: System Overview (9 paneles), Application Performance (7), Database Monitoring (3)
- **Observability**: Métricas Prometheus, logs structlog, health checks

### Frontend (React + Material-UI)
- **Dashboard Editor**: Drag-and-drop con react-grid-layout
- **Panel Editor**: Formularios para configurar paneles
- **Query Builder UI**: Interfaz visual para construir queries
- **Template Gallery**: Vista previa y selección de templates
- **Responsive**: Funciona en móviles y tablets

## 🚀 Instalación

### Requisitos
- Docker 24.0+
- docker-compose 2.20+
- Grafana 10.0+ (puerto 3000)
- Prometheus 2.45+ (puerto 9090)
- Red Docker: `rhinometric_network_v22`

### Despliegue Rápido

```bash
# 1. Clonar repositorio
cd rhinometric-dashboard-builder

# 2. Configurar variables
export GRAFANA_PASSWORD="tu_password_seguro"

# 3. Iniciar servicios
docker-compose up -d

# 4. Verificar estado
docker-compose ps
docker-compose logs -f dashboard-builder-backend
```

### Verificación

```bash
# Backend health check
curl http://localhost:8087/health

# Swagger UI
open http://localhost:8087/docs

# Frontend
open http://localhost:3001
```

## 📚 Uso Rápido

### 1. Crear Dashboard desde Template

```bash
# Sistema Overview (9 paneles)
curl -X POST http://localhost:8087/api/v1/dashboards \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sistema Producción",
    "tags": ["system", "production"],
    "template": "system-overview"
  }'

# Response
{
  "uid": "abc123def",
  "url": "http://grafana:3000/d/abc123def/sistema-produccion",
  "version": 1
}
```

### 2. Construir Query de Prometheus

```bash
# CPU usage promedio últimos 5 minutos
curl -X POST http://localhost:8087/api/v1/query/build \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "cpu",
    "subtype": "usage",
    "filters": {"instance": "server-01"},
    "aggregation": "avg",
    "range": "5m"
  }'

# Response
{
  "query": "avg(rate(node_cpu_seconds_total{instance=\"server-01\",mode!=\"idle\"}[5m])) * 100",
  "description": "Average CPU usage over 5m for instance=server-01"
}
```

### 3. Crear Dashboard Custom

```bash
curl -X POST http://localhost:8087/api/v1/dashboards \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mi Dashboard",
    "tags": ["custom"],
    "panels": [
      {
        "type": "graph",
        "title": "CPU Usage",
        "query": "rate(node_cpu_seconds_total{mode!=\"idle\"}[5m]) * 100",
        "x": 0, "y": 0, "width": 12, "height": 8
      },
      {
        "type": "stat",
        "title": "Memory Used",
        "query": "node_memory_MemAvailable_bytes",
        "x": 12, "y": 0, "width": 6, "height": 4,
        "thresholds": [
          {"value": 0, "color": "green"},
          {"value": 80, "color": "yellow"},
          {"value": 90, "color": "red"}
        ]
      }
    ]
  }'
```

## 🔧 Configuración

### Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host del backend |
| `PORT` | `8087` | Puerto del backend |
| `LOG_LEVEL` | `INFO` | Nivel de logs (DEBUG, INFO, WARNING, ERROR) |
| `GRAFANA_URL` | `http://grafana:3000` | URL de Grafana |
| `GRAFANA_USER` | `admin` | Usuario Grafana |
| `GRAFANA_PASSWORD` | `admin` | Password Grafana |
| `PROMETHEUS_URL` | `http://prometheus:9090` | URL de Prometheus |

### Estructura de Proyecto

```
rhinometric-dashboard-builder/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # v2.2.0
│   │   ├── config.py            # Configuración (60 líneas)
│   │   ├── grafana_api.py       # Cliente Grafana (110 líneas)
│   │   ├── prometheus_api.py    # Query Builder (180 líneas)
│   │   ├── panels.py            # Panel System (200 líneas)
│   │   ├── templates.py         # Dashboard Templates (280 líneas)
│   │   └── main.py              # FastAPI App (410 líneas)
│   ├── requirements.txt         # Dependencias Python
│   └── Dockerfile               # Imagen backend
├── frontend/
│   ├── src/
│   │   ├── components/          # Componentes React (pendiente)
│   │   └── utils/               # Utilities (pendiente)
│   ├── package.json             # Dependencias Node
│   ├── Dockerfile               # Imagen frontend
│   └── nginx.conf               # Config nginx
├── docker-compose.yml           # Orquestación
└── README.md                    # Este archivo
```

## 📖 API Reference

### Dashboards

- **POST /api/v1/dashboards** - Crear dashboard
- **GET /api/v1/dashboards** - Listar dashboards
- **GET /api/v1/dashboards/{uid}** - Obtener dashboard
- **DELETE /api/v1/dashboards/{uid}** - Eliminar dashboard

### Templates

- **GET /api/v1/templates** - Listar templates disponibles
- **GET /api/v1/templates/{template_type}** - Obtener template específico

Tipos: `system-overview`, `application-performance`, `database-monitoring`, `network-traffic`, `container-monitoring`, `anomaly-detection`

### Query Builder

- **POST /api/v1/query/build** - Construir query Prometheus
- **POST /api/v1/query/validate** - Validar query
- **GET /api/v1/query/metrics** - Listar tipos de métricas

### Panels

- **GET /api/v1/panels/types** - Tipos de paneles disponibles

Tipos: `graph`, `stat`, `gauge`, `table`, `pie_chart`, `heatmap`

### System

- **GET /health** - Health check (Grafana + Prometheus)
- **GET /metrics** - Métricas Prometheus
- **GET /docs** - Swagger UI

## 🧪 Testing

```bash
# Health check completo
curl http://localhost:8087/health

# Listar templates
curl http://localhost:8087/api/v1/templates

# Listar tipos de paneles
curl http://localhost:8087/api/v1/panels/types

# Ver métricas Prometheus
curl http://localhost:8087/metrics
```

## 🔍 Troubleshooting

### Backend no arranca

```bash
# Ver logs
docker-compose logs dashboard-builder-backend

# Verificar conectividad Grafana
docker exec -it rhinometric-dashboard-builder-backend curl http://grafana:3000/api/health

# Verificar conectividad Prometheus
docker exec -it rhinometric-dashboard-builder-backend curl http://prometheus:9090/-/healthy
```

### Frontend no carga

```bash
# Ver logs nginx
docker-compose logs dashboard-builder-frontend

# Verificar proxy backend
docker exec -it rhinometric-dashboard-builder-frontend cat /etc/nginx/nginx.conf
```

### Dashboards no se crean

```bash
# Verificar credenciales Grafana
curl -u admin:$GRAFANA_PASSWORD http://localhost:3000/api/datasources

# Ver logs detallados
docker-compose logs -f dashboard-builder-backend | grep ERROR
```

## 📈 Roadmap

- [x] Backend completo (v2.2.0)
- [x] Frontend infrastructure
- [ ] Frontend React components (en desarrollo)
- [ ] Tests E2E con Playwright
- [ ] Dashboard templates adicionales (Network, Container, Anomaly)
- [ ] Export/Import dashboards JSON
- [ ] Versionado de dashboards
- [ ] Colaboración multi-usuario

## 🤝 Integración

### Añadir a docker-compose.yml principal

```yaml
# docker-compose-v2.2.0.yml
services:
  dashboard-builder-backend:
    image: rhinometric-dashboard-builder-backend:latest
    environment:
      GRAFANA_URL: http://grafana:3000
      PROMETHEUS_URL: http://prometheus:9090
    networks:
      - rhinometric_network_v22
    
  dashboard-builder-frontend:
    image: rhinometric-dashboard-builder-frontend:latest
    ports:
      - "3001:80"
    networks:
      - rhinometric_network_v22
```

## 📄 Licencia

Propietaria - RhinoMetric Enterprise Observability Platform

## 🆘 Soporte

- **Swagger UI**: http://localhost:8087/docs
- **Health Check**: http://localhost:8087/health
- **Logs**: `docker-compose logs -f`
- **Repositorio**: Internal GitLab

---

**Estado**: Backend 100% completo ✅ | Frontend en desarrollo 🚧

**Versión**: 2.2.0 | **Fecha**: Enero 2025
