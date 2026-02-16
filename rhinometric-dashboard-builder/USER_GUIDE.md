# Dashboard Builder v2.2.0 - Guía de Usuario

## 📖 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Acceso al Sistema](#acceso-al-sistema)
3. [Templates Pre-configurados](#templates-pre-configurados)
4. [Query Builder Visual](#query-builder-visual)
5. [Panel Editor](#panel-editor)
6. [Dashboard Personalizado](#dashboard-personalizado)
7. [Casos de Uso](#casos-de-uso)
8. [Tips y Buenas Prácticas](#tips-y-buenas-prácticas)

---

## Introducción

Dashboard Builder es una herramienta visual que permite crear dashboards profesionales en Grafana **sin conocimientos de PromQL ni JSON**. Diseñado para:

- 👨‍💼 **Managers**: Crear reportes ejecutivos con un clic
- 🔧 **Operaciones**: Monitorear infraestructura sin scripts
- 📊 **Analistas**: Visualizar métricas sin programar
- 🚀 **DevOps**: Acelerar creación de dashboards

---

## Acceso al Sistema

### Interfaz Web

1. **Frontend**: http://localhost:3001
2. **API Swagger**: http://localhost:8087/docs
3. **Grafana**: http://localhost:3000

### Credenciales Default

```
Grafana:
  Usuario: admin
  Password: admin (cambiar en producción)
```

---

## Templates Pre-configurados

### 1. System Overview (9 paneles)

**¿Para qué?** Monitoreo completo de servidores Linux

**Métricas incluidas:**
- CPU Usage (stat + timeseries)
- Memory Usage (stat + graph)
- Disk Usage (stat)
- Disk I/O (graph)
- Network Traffic (graph)
- System Uptime (stat)
- CPU by Core (graph)

**Uso via API:**

```bash
curl -X POST http://localhost:8087/api/v1/dashboards \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Servidor Producción - Web01",
    "tags": ["production", "web-server"],
    "template": "system-overview",
    "folder": "Production"
  }'
```

**Uso via Frontend:**

1. Ir a "Templates"
2. Seleccionar "System Overview"
3. Configurar:
   - **Title**: Nombre descriptivo
   - **Tags**: production, web-server
   - **Folder**: Production
4. Click "Create Dashboard"

**Vista previa:**

```
┌─────────────────────────────────────────────┐
│  CPU: 45%  │  Memory: 2.3GB  │  Uptime: 30d │
├─────────────────────────────────────────────┤
│           CPU Usage Over Time               │
│  ╱╲    ╱╲                                   │
│ ╱  ╲  ╱  ╲  ╱╲                              │
│      ╲╱    ╲╱  ╲                            │
├─────────────────────────────────────────────┤
│  CPU by Core     │  Disk I/O     │ Network  │
│  [Graph]         │  [Graph]      │ [Graph]  │
└─────────────────────────────────────────────┘
```

### 2. Application Performance (7 paneles)

**¿Para qué?** Monitoreo de aplicaciones web y APIs

**Métricas incluidas:**
- Request Rate (stat)
- Error Rate (stat)
- Avg Response Time (stat)
- Active Users (stat)
- Request Rate Over Time (graph)
- Response Time Percentiles (P50, P95, P99)
- Error Rate by Status Code

**Uso:**

```bash
curl -X POST http://localhost:8087/api/v1/dashboards \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Gateway Performance",
    "tags": ["api", "production"],
    "template": "application-performance"
  }'
```

**Casos de uso:**
- Monitorear SLA (P95 < 200ms)
- Detectar picos de tráfico
- Alertar sobre error rates > 1%

### 3. Database Monitoring (3 paneles)

**¿Para qué?** Monitoreo de PostgreSQL, MySQL, MongoDB

**Métricas incluidas:**
- Active Connections (stat)
- Total Connections (graph)
- Connection Pool by State (table)

**Uso:**

```bash
curl -X POST http://localhost:8087/api/v1/dashboards \
  -H "Content-Type: application/json" \
  -d '{
    "title": "PostgreSQL - DB01",
    "tags": ["database", "postgres"],
    "template": "database-monitoring"
  }'
```

### Templates Disponibles

| Template | Paneles | Uso Típico | Nivel |
|----------|---------|------------|-------|
| `system-overview` | 9 | Servidores Linux | Básico |
| `application-performance` | 7 | APIs, Web Apps | Intermedio |
| `database-monitoring` | 3 | PostgreSQL, MySQL | Básico |
| `network-traffic` | - | Switches, routers | Avanzado |
| `container-monitoring` | - | Docker, Kubernetes | Intermedio |
| `anomaly-detection` | - | ML-based alerts | Avanzado |

---

## Query Builder Visual

### ¿Qué hace?

Convierte formularios simples en queries de Prometheus complejas.

### Tipos de Métricas

#### 1. CPU

**Subtypes:**
- `usage`: Uso total de CPU (%)
- `usage_by_cpu`: Uso por core individual
- `usage_by_mode`: Uso por modo (user, system, iowait)

**Ejemplo - CPU usage promedio:**

```bash
curl -X POST http://localhost:8087/api/v1/query/build \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "cpu",
    "subtype": "usage",
    "filters": {"instance": "web-server-01"},
    "aggregation": "avg",
    "range": "5m"
  }'

# Response
{
  "query": "avg(rate(node_cpu_seconds_total{instance=\"web-server-01\",mode!=\"idle\"}[5m])) * 100"
}
```

**Frontend UI:**

```
┌───────────────────────────────────────┐
│ Query Builder                         │
├───────────────────────────────────────┤
│ Metric Type:  [CPU ▼]                 │
│ Subtype:      [usage ▼]               │
│ Instance:     [web-server-01]         │
│ Aggregation:  [avg ▼]                 │
│ Range:        [5m ▼]                  │
│                                       │
│ Preview:                              │
│ avg(rate(node_cpu_seconds_total{...  │
│                                       │
│ [Build Query]                         │
└───────────────────────────────────────┘
```

#### 2. Memory

**Subtypes:**
- `usage`: Memoria usada (%)
- `available`: Memoria disponible (bytes)
- `total`: Memoria total (bytes)
- `used`: Memoria usada (bytes)

**Ejemplo - Memory usage con alerta:**

```bash
curl -X POST http://localhost:8087/api/v1/query/build \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "memory",
    "subtype": "usage",
    "filters": {},
    "aggregation": "avg"
  }'

# Query generada
avg((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)
```

#### 3. Disk

**Subtypes:**
- `usage`: Uso de disco (%)
- `io_read`: Read I/O (bytes/s)
- `io_write`: Write I/O (bytes/s)

**Ejemplo - Disk I/O read:**

```bash
{
  "metric_type": "disk",
  "subtype": "io_read",
  "filters": {"device": "sda"},
  "aggregation": "rate",
  "range": "1m"
}

# Query
rate(node_disk_read_bytes_total{device="sda"}[1m])
```

#### 4. Network

**Subtypes:**
- `receive`: Tráfico entrante (bytes/s)
- `transmit`: Tráfico saliente (bytes/s)
- `errors`: Errores de red

**Ejemplo - Network receive total:**

```bash
{
  "metric_type": "network",
  "subtype": "receive",
  "aggregation": "sum"
}

# Query
sum(rate(node_network_receive_bytes_total[5m]))
```

#### 5. HTTP

**Subtypes:**
- `request_rate`: Requests por segundo
- `error_rate`: % de errores
- `latency_p95`: Latencia P95
- `latency_p99`: Latencia P99

**Ejemplo - Error rate por endpoint:**

```bash
{
  "metric_type": "http",
  "subtype": "error_rate",
  "filters": {"endpoint": "/api/users"},
  "aggregation": "rate",
  "group_by": ["status_code"]
}

# Query
rate(http_requests_total{endpoint="/api/users",status_code=~"5.."}[5m])
/ rate(http_requests_total{endpoint="/api/users"}[5m]) * 100
```

#### 6. Database

**Subtypes:**
- `connections`: Conexiones totales
- `active_connections`: Conexiones activas
- `slow_queries`: Queries lentas

**Ejemplo - Database active connections:**

```bash
{
  "metric_type": "database",
  "subtype": "active_connections",
  "filters": {"database": "users_db"}
}

# Query
pg_stat_activity_count{database="users_db",state="active"}
```

### Aggregations

| Agregación | Descripción | Uso |
|------------|-------------|-----|
| `avg` | Promedio | CPU/Memory usage |
| `sum` | Suma total | Request count, bytes |
| `min` | Mínimo | Latency best case |
| `max` | Máximo | Latency worst case |
| `count` | Conteo | Número de instancias |
| `rate` | Tasa de cambio/s | HTTP requests/s |
| `increase` | Incremento total | Counter metrics |

### Filters

```json
{
  "filters": {
    "instance": "web-01",
    "job": "prometheus",
    "environment": "production",
    "region": "us-east-1"
  }
}
```

Genera: `{instance="web-01",job="prometheus",environment="production",region="us-east-1"}`

### Group By

```json
{
  "group_by": ["instance", "job"]
}
```

Genera: `by (instance, job)`

---

## Panel Editor

### Tipos de Paneles

#### 1. Graph (Timeseries)

**¿Cuándo usar?** Métricas que cambian en el tiempo (CPU, memory, network)

**Configuración:**

```json
{
  "type": "graph",
  "title": "CPU Usage Over Time",
  "query": "rate(node_cpu_seconds_total{mode!=\"idle\"}[5m]) * 100",
  "x": 0, "y": 0, "width": 12, "height": 8,
  "legend_show": true,
  "line_width": 2,
  "fill_opacity": 10
}
```

**Opciones:**
- `legend_show`: Mostrar leyenda
- `line_width`: Grosor línea (1-5)
- `fill_opacity`: Transparencia (0-100)

#### 2. Stat (Número grande)

**¿Cuándo usar?** Valor actual (uptime, active users, error count)

**Configuración:**

```json
{
  "type": "stat",
  "title": "Active Users",
  "query": "sum(active_sessions)",
  "x": 0, "y": 0, "width": 6, "height": 4,
  "thresholds": [
    {"value": 0, "color": "green"},
    {"value": 1000, "color": "yellow"},
    {"value": 5000, "color": "red"}
  ],
  "color_mode": "background"
}
```

**Color Modes:**
- `value`: Color del número
- `background`: Color de fondo

#### 3. Gauge (Medidor)

**¿Cuándo usar?** Métricas con min/max (CPU %, disk usage, progress)

**Configuración:**

```json
{
  "type": "gauge",
  "title": "Memory Usage",
  "query": "(1 - node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes) * 100",
  "x": 6, "y": 0, "width": 6, "height": 4,
  "min": 0,
  "max": 100,
  "thresholds": [
    {"value": 0, "color": "green"},
    {"value": 80, "color": "yellow"},
    {"value": 90, "color": "red"}
  ]
}
```

#### 4. Table

**¿Cuándo usar?** Comparar múltiples valores (top 10 servers, connection pool)

**Configuración:**

```json
{
  "type": "table",
  "title": "Top 10 Servers by CPU",
  "query": "topk(10, rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])) * 100",
  "x": 0, "y": 8, "width": 12, "height": 6,
  "format": "table"
}
```

#### 5. Pie Chart

**¿Cuándo usar?** Distribución (error types, traffic by endpoint)

**Configuración:**

```json
{
  "type": "pie_chart",
  "title": "Requests by Endpoint",
  "query": "sum by (endpoint) (rate(http_requests_total[5m]))",
  "x": 12, "y": 0, "width": 6, "height": 8,
  "legend_placement": "right"
}
```

#### 6. Heatmap

**¿Cuándo usar?** Latency distributions, histogramas

**Configuración:**

```json
{
  "type": "heatmap",
  "title": "Response Time Distribution",
  "query": "rate(http_request_duration_seconds_bucket[5m])",
  "x": 0, "y": 16, "width": 12, "height": 8
}
```

### Grid Layout

Sistema de 24 columnas:

```
┌──────────────────────────────────────────────┐
│ width=12          │ width=12                 │  ← Row 1
├──────────────────────────────────────────────┤
│ width=8           │ width=8    │ width=8     │  ← Row 2
├──────────────────────────────────────────────┤
│ width=24 (full width)                        │  ← Row 3
└──────────────────────────────────────────────┘

x: Columna inicial (0-23)
y: Fila inicial (0-∞)
width: Ancho en columnas (1-24)
height: Alto en unidades (1-∞)
```

**Layouts comunes:**

```python
# Layout 3 columnas (stats)
[
  {"x": 0, "y": 0, "width": 8, "height": 4},   # Stat 1
  {"x": 8, "y": 0, "width": 8, "height": 4},   # Stat 2
  {"x": 16, "y": 0, "width": 8, "height": 4}   # Stat 3
]

# Layout 2 columnas (graphs)
[
  {"x": 0, "y": 4, "width": 12, "height": 8},  # Graph 1
  {"x": 12, "y": 4, "width": 12, "height": 8}  # Graph 2
]

# Layout sidebar
[
  {"x": 0, "y": 12, "width": 6, "height": 12},  # Sidebar (gauges)
  {"x": 6, "y": 12, "width": 18, "height": 12}  # Main (graph)
]
```

---

## Dashboard Personalizado

### Ejemplo Completo: E-commerce Monitoring

**Objetivo:** Monitorear tienda online con métricas de negocio

**Paneles:**

```bash
curl -X POST http://localhost:8087/api/v1/dashboards \
  -H "Content-Type: application/json" \
  -d '{
    "title": "E-commerce - Black Friday",
    "tags": ["ecommerce", "sales", "production"],
    "refresh": "30s",
    "panels": [
      {
        "type": "stat",
        "title": "Orders/min",
        "query": "rate(orders_total[1m]) * 60",
        "x": 0, "y": 0, "width": 6, "height": 4,
        "thresholds": [
          {"value": 0, "color": "red"},
          {"value": 10, "color": "yellow"},
          {"value": 50, "color": "green"}
        ],
        "color_mode": "background"
      },
      {
        "type": "stat",
        "title": "Revenue/min ($)",
        "query": "rate(revenue_total[1m]) * 60",
        "x": 6, "y": 0, "width": 6, "height": 4,
        "thresholds": [
          {"value": 0, "color": "red"},
          {"value": 1000, "color": "yellow"},
          {"value": 5000, "color": "green"}
        ]
      },
      {
        "type": "gauge",
        "title": "Checkout Success Rate",
        "query": "(sum(rate(checkout_success[5m])) / sum(rate(checkout_attempts[5m]))) * 100",
        "x": 12, "y": 0, "width": 6, "height": 4,
        "min": 0, "max": 100,
        "thresholds": [
          {"value": 0, "color": "red"},
          {"value": 85, "color": "yellow"},
          {"value": 95, "color": "green"}
        ]
      },
      {
        "type": "stat",
        "title": "Active Users",
        "query": "sum(active_sessions)",
        "x": 18, "y": 0, "width": 6, "height": 4
      },
      {
        "type": "graph",
        "title": "Orders Over Time",
        "query": "rate(orders_total[5m]) * 60",
        "x": 0, "y": 4, "width": 12, "height": 8
      },
      {
        "type": "graph",
        "title": "API Response Time (P95)",
        "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"api\"}[5m]))",
        "x": 12, "y": 4, "width": 12, "height": 8
      },
      {
        "type": "pie_chart",
        "title": "Traffic by Page",
        "query": "sum by (page) (rate(page_views_total[5m]))",
        "x": 0, "y": 12, "width": 8, "height": 8
      },
      {
        "type": "table",
        "title": "Top 10 Products",
        "query": "topk(10, sum by (product) (rate(product_views_total[5m])))",
        "x": 8, "y": 12, "width": 16, "height": 8
      }
    ]
  }'
```

**Dashboard generado:**

```
┌────────────────────────────────────────────────────────────────┐
│ Orders/min │ Revenue/min │ Checkout  │ Active Users            │
│     45     │    $3,250   │  Success  │     1,234               │
│   (green)  │   (green)   │   [97%]   │                         │
├────────────────────────────────────────────────────────────────┤
│        Orders Over Time       │  API Response Time (P95)       │
│  ╱╲      ╱╲                  │  ─────                         │
│ ╱  ╲    ╱  ╲  ╱╲             │        ╱╲                      │
│      ╲  ╱    ╲╱  ╲            │       ╱  ╲                     │
│       ╲╱                      │      ╱    ╲                    │
├────────────────────────────────────────────────────────────────┤
│ Traffic by Page │ Top 10 Products (Table)                      │
│  [Pie Chart]    │ Product       │ Views/min                    │
│                 │ iPhone 15     │ 342                          │
│                 │ AirPods Pro   │ 278                          │
│                 │ MacBook Air   │ 156                          │
└────────────────────────────────────────────────────────────────┘
```

---

## Casos de Uso

### 1. SRE: SLA Monitoring

**Objetivo:** Monitorear SLA de 99.9% uptime y latency P95 < 200ms

```bash
{
  "title": "SLA Dashboard - API Gateway",
  "panels": [
    {
      "type": "stat",
      "title": "Availability (Target: 99.9%)",
      "query": "(1 - (sum(rate(http_requests_total{status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])))) * 100",
      "thresholds": [
        {"value": 0, "color": "red"},
        {"value": 99, "color": "yellow"},
        {"value": 99.9, "color": "green"}
      ]
    },
    {
      "type": "stat",
      "title": "P95 Latency (Target: <200ms)",
      "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) * 1000",
      "thresholds": [
        {"value": 0, "color": "green"},
        {"value": 200, "color": "yellow"},
        {"value": 500, "color": "red"}
      ]
    }
  ]
}
```

### 2. DevOps: Deployment Tracking

**Objetivo:** Monitorear despliegue en producción

```bash
{
  "title": "Deployment - v2.1.0 to Production",
  "panels": [
    {
      "type": "graph",
      "title": "Error Rate Before/After",
      "query": "rate(http_requests_total{status_code=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
      "annotations": [
        {"time": "2025-01-15T14:30:00Z", "text": "Deployment started"}
      ]
    },
    {
      "type": "graph",
      "title": "Response Time P95",
      "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
    },
    {
      "type": "graph",
      "title": "Pod Restarts",
      "query": "sum(kube_pod_container_status_restarts_total) by (pod)"
    }
  ]
}
```

### 3. Business: Executive Dashboard

**Objetivo:** Métricas de negocio para ejecutivos

```bash
{
  "title": "Executive Dashboard - Weekly Review",
  "panels": [
    {
      "type": "stat",
      "title": "Total Revenue (7d)",
      "query": "sum(increase(revenue_total[7d]))",
      "color_mode": "background"
    },
    {
      "type": "stat",
      "title": "New Users (7d)",
      "query": "sum(increase(user_registrations_total[7d]))"
    },
    {
      "type": "graph",
      "title": "Daily Active Users",
      "query": "sum(active_users_daily)"
    },
    {
      "type": "pie_chart",
      "title": "Revenue by Product Category",
      "query": "sum by (category) (revenue_total)"
    }
  ]
}
```

### 4. Security: Intrusion Detection

**Objetivo:** Detectar ataques y anomalías

```bash
{
  "title": "Security - Intrusion Detection",
  "panels": [
    {
      "type": "stat",
      "title": "Failed Login Attempts/min",
      "query": "rate(login_failures_total[1m]) * 60",
      "thresholds": [
        {"value": 0, "color": "green"},
        {"value": 10, "color": "yellow"},
        {"value": 50, "color": "red"}
      ]
    },
    {
      "type": "table",
      "title": "Top IPs by Failed Logins",
      "query": "topk(10, sum by (ip) (rate(login_failures_total[5m])))"
    },
    {
      "type": "graph",
      "title": "403 Forbidden Requests",
      "query": "rate(http_requests_total{status_code=\"403\"}[5m])"
    }
  ]
}
```

---

## Tips y Buenas Prácticas

### Nomenclatura de Dashboards

```
✅ BUENO:
- "Production - API Gateway"
- "Database - PostgreSQL Main"
- "E-commerce - Checkout Flow"

❌ MALO:
- "Dashboard 1"
- "Test"
- "Untitled"
```

### Tags Efectivos

```json
{
  "tags": [
    "production",           // Environment
    "api-gateway",          // Component
    "sre",                  // Team
    "critical"              // Priority
  ]
}
```

### Thresholds Realistas

```json
// CPU Usage
{"value": 0, "color": "green"},   // 0-70%: Normal
{"value": 70, "color": "yellow"}, // 70-90%: Warning
{"value": 90, "color": "red"}     // >90%: Critical

// Error Rate
{"value": 0, "color": "green"},   // <0.1%: Excellent
{"value": 0.1, "color": "yellow"}, // 0.1-1%: Warning
{"value": 1, "color": "red"}       // >1%: Critical

// Latency P95
{"value": 0, "color": "green"},   // <100ms: Excellent
{"value": 100, "color": "yellow"}, // 100-500ms: Acceptable
{"value": 500, "color": "red"}     // >500ms: Slow
```

### Query Performance

```bash
# ✅ Optimizado (rate con range corto)
rate(http_requests_total[5m])

# ❌ Lento (irate solo usa 2 puntos)
irate(http_requests_total[5m])

# ✅ Agregado primero, luego filtrado
sum(rate(http_requests_total[5m])) by (endpoint)

# ❌ Filtrado sin agregación
rate(http_requests_total{endpoint="/api/users"}[5m])
```

### Refresh Intervals

```yaml
Real-time monitoring:    10s-30s
Production dashboards:   1m-5m
Executive dashboards:    1h
Historical analysis:     1d
```

### Panel Layout

```
Prioridad visual (top-to-bottom):
1. Stats críticos (row 1) ← Lo primero que se ve
2. Graphs principales (row 2-3)
3. Tables detalladas (row 4+)
4. Logs/debug info (bottom)

Left-to-right:
- Más importante a la izquierda
- Contexto adicional a la derecha
```

### Validación Pre-Deploy

```bash
# 1. Test connectivity
curl http://localhost:8087/health

# 2. Validate query
curl -X POST http://localhost:8087/api/v1/query/validate \
  -d '{"query": "rate(http_requests_total[5m])"}'

# 3. Test template
curl http://localhost:8087/api/v1/templates/system-overview

# 4. Create in test folder
curl -X POST http://localhost:8087/api/v1/dashboards \
  -d '{"title": "TEST - My Dashboard", "folder": "Testing", ...}'
```

---

## Atajos y Comandos Útiles

### CLI Quick Commands

```bash
# Listar todos los dashboards
curl http://localhost:8087/api/v1/dashboards | jq '.[] | {title, uid, url}'

# Obtener dashboard específico
curl http://localhost:8087/api/v1/dashboards/abc123def | jq

# Eliminar dashboard
curl -X DELETE http://localhost:8087/api/v1/dashboards/abc123def

# Ver métricas disponibles
curl http://localhost:8087/api/v1/query/metrics | jq

# Probar query
curl -X POST http://localhost:8087/api/v1/query/build \
  -d '{"metric_type": "cpu", "subtype": "usage"}' | jq '.query'
```

### Environment Variables

```bash
# Development
export LOG_LEVEL=DEBUG
export GRAFANA_URL=http://localhost:3000
export PROMETHEUS_URL=http://localhost:9090

# Production
export LOG_LEVEL=INFO
export GRAFANA_URL=http://grafana.prod.company.com
export GRAFANA_PASSWORD=$(cat /run/secrets/grafana_password)
```

---

**¿Necesitas ayuda?**

- Swagger UI: http://localhost:8087/docs
- Logs: `docker-compose logs -f dashboard-builder-backend`
- Health: http://localhost:8087/health
- Soporte: Equipo SRE interno

---

**Versión**: 2.2.0 | **Actualizado**: Enero 2025
