# 📚 MANUAL DE USUARIO - Rhinometric v2.1.0

**Guía Completa de Uso**  
**Nivel**: Principiante a Avanzado  
**Versión**: 2.1.0 Trial

---

## 📑 ÍNDICE

1. [Introducción](#introducción)
2. [Primeros Pasos](#primeros-pasos)
3. [Interfaz de Grafana](#interfaz-de-grafana)
4. [Dashboards Incluidos](#dashboards-incluidos)
5. [API Connector](#api-connector)
6. [Drilldown: Métricas → Logs → Traces](#drilldown)
7. [Alertas y Notificaciones](#alertas-y-notificaciones)
8. [Uso Avanzado](#uso-avanzado)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## 🎯 INTRODUCCIÓN

### **¿Qué es Rhinometric?**

Rhinometric es una **plataforma de observabilidad completa** que te permite monitorear:

- ✅ **Métricas**: CPU, RAM, disco, latencia, errores
- ✅ **Logs**: Centralizados y correlacionados
- ✅ **Traces**: Seguimiento de requests entre servicios
- ✅ **APIs Externas**: Monitoreo de integraciones (Stripe, AWS, OpenAI, etc.)

**Stack Tecnológico**:
- **Grafana 10.4.0**: Visualización
- **Prometheus**: Métricas
- **Loki**: Logs
- **Tempo**: Traces
- **PostgreSQL + Redis**: Persistencia y cache

---

### **Arquitectura de Alto Nivel**

```
┌─────────────────────────────────────────────────────────┐
│                   TU APLICACIÓN                         │
│         (Web, API, Microservicios, Workers)             │
└──────────────┬──────────────────────────────────────────┘
               │
               │ Instrumentación (OTEL)
               ↓
┌─────────────────────────────────────────────────────────┐
│              RHINOMETRIC v2.1.0 TRIAL                   │
│  ┌────────────┐  ┌─────────┐  ┌──────┐  ┌───────────┐  │
│  │ Prometheus │  │  Loki   │  │Tempo │  │API Proxy  │  │
│  │ (Métricas) │  │ (Logs)  │  │(Tra..)│  │(APIs Ext.)│  │
│  └──────┬─────┘  └────┬────┘  └───┬──┘  └─────┬─────┘  │
│         │             │           │            │         │
│         └─────────────┴───────────┴────────────┘         │
│                       │                                  │
│                  ┌────▼────┐                             │
│                  │ GRAFANA │ ← TÚ ACCEDES AQUÍ          │
│                  └─────────┘                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 PRIMEROS PASOS

### **1. Acceder a Grafana**

**URL**: http://localhost:3000 (o http://SERVER_IP:3000)

**Credenciales** (configuradas en `.env`):
- Usuario: `admin`
- Password: `admin123` (o la que configuraste)

---

### **2. Pantalla Inicial**

Al entrar verás:

```
┌─────────────────────────────────────────────────────────┐
│ [☰] GRAFANA                    🔍 Search   👤 admin  ⚙️  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🏠 Home                                                 │
│                                                          │
│  📊 Dashboards Favoritos:                               │
│     • System Overview (Full Stack)                      │
│     • External APIs Monitoring                          │
│     • Application Performance (RED)                     │
│                                                          │
│  📁 Carpetas:                                            │
│     ► Rhinometric v2.1.0 (15 dashboards)                │
│     ► General                                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### **3. Navegación Rápida**

| Atajo | Acción |
|-------|--------|
| `Ctrl + K` | Buscar dashboard |
| `D` | Abrir último dashboard |
| `Esc` | Cerrar panel/modal |
| `?` | Ver todos los atajos |

---

## 📊 DASHBOARDS INCLUIDOS (15)

### **1. System Overview (Full Stack)** 🌟

**URL**: `/d/system-overview`

**Qué muestra**:
- ✅ Estado de 17 contenedores (UP/DOWN)
- ✅ CPU, RAM, Disco por contenedor
- ✅ Network I/O
- ✅ Alertas activas

**Uso**:
- Panel principal para ver salud general del sistema
- Ideal para: Revisión diaria, troubleshooting inicial

**Paneles**:
1. **Container Status**: Tabla con estado de todos los containers
2. **CPU Usage**: Gráfico de líneas por container
3. **Memory Usage**: % de RAM usada
4. **Disk I/O**: Lectura/escritura por segundo
5. **Network Traffic**: Bytes sent/received

---

### **2. External APIs Monitoring** 🌐

**URL**: `/d/external-apis/f09f8c90-external-apis-monitoring`

**Qué muestra**:
- ✅ Health status de APIs externas (OpenWeather, GitHub, Stripe, etc.)
- ✅ Request rate (requests/sec)
- ✅ Response time p50, p95, p99
- ✅ Cache hit rate
- ✅ Error rate (4xx, 5xx)

**Uso**:
- Monitorea integraciones críticas
- Detecta degradaciones antes de que afecten usuarios

**Paneles importantes**:

| Panel | Descripción | Alertar si... |
|-------|-------------|---------------|
| Health Status | 1 = healthy, 0 = down | < 1 por 5 min |
| Request Rate | requests/sec por API | Caída súbita (>50%) |
| Response Time p95 | Latencia percentil 95 | > 2000 ms |
| Error Rate | % de requests con error | > 5% |
| Cache Hit Rate | % de requests cacheadas | < 80% (si aplica) |

**Demo**:

```bash
# Generar tráfico de prueba
cd ~/rhinometric/rhinometric-trial-v2.1.0-universal
./generate-api-activity.sh

# Verás aumentar métricas en ~30 segundos
```

---

### **3. Application Performance (RED)** 📈

**URL**: `/d/application-red`

**RED Method**:
- **R**ate: Requests por segundo
- **E**rrors: % de errores
- **D**uration: Latencia

**Qué muestra**:
- ✅ Request rate por endpoint
- ✅ Error rate (400, 500)
- ✅ Latencia p50, p90, p99
- ✅ Throughput

**Uso**:
- Detectar endpoints lentos
- Identificar picos de errores
- Comparar performance antes/después de deploys

---

### **4. Database Performance (PostgreSQL)** 🗄️

**URL**: `/d/database-perf`

**Qué muestra**:
- ✅ Connections activas/idle
- ✅ Query duration
- ✅ Slow queries (> 500ms)
- ✅ Cache hit ratio
- ✅ Locks y deadlocks

**Uso**:
- Optimizar queries lentas
- Detectar problemas de concurrencia

**Panel clave**: **Slow Queries**

```sql
-- Queries > 500ms en últimos 5 min
SELECT 
  query, 
  mean_exec_time, 
  calls 
FROM pg_stat_statements 
WHERE mean_exec_time > 500 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

---

### **5. Redis Performance** ⚡

**URL**: `/d/redis-perf`

**Qué muestra**:
- ✅ Hit rate (% de keys encontradas en cache)
- ✅ Commands/sec
- ✅ Memory usage
- ✅ Evicted keys
- ✅ Blocked clients

**Uso**:
- Optimizar estrategia de caching
- Detectar problemas de memoria

**Métricas críticas**:
- **Hit Rate**: Debe ser > 80%
- **Evicted Keys**: Si es alto, aumentar `maxmemory`
- **Blocked Clients**: Debe ser 0

---

### **6. Nginx Performance** 🌍

**URL**: `/d/nginx-perf`

**Qué muestra**:
- ✅ Requests/sec por status code
- ✅ Response time
- ✅ Active connections
- ✅ SSL handshakes

**Uso**:
- Monitorear carga de frontend
- Detectar ataques (4xx elevado)

---

### **7. OTEL Collector Metrics** 📡

**URL**: `/d/otel-collector`

**Qué muestra**:
- ✅ Traces recibidos/exportados
- ✅ Logs procesados
- ✅ Métricas scraped
- ✅ Errores de exportación

**Uso**:
- Verificar que instrumentación funciona
- Detectar pérdida de datos

---

### **8-15. Dashboards Adicionales**

| # | Nombre | Descripción |
|---|--------|-------------|
| 8 | Node Exporter | Métricas del host (CPU, RAM, disk, network) |
| 9 | Docker Containers | Detalle de todos los containers |
| 10 | Logs Explorer | Búsqueda y filtrado de logs centralizados |
| 11 | Traces Explorer | Visualización de traces distribuidos |
| 12 | Alerts Overview | Todas las alertas configuradas |
| 13 | License Server | Uso de licencias (solo admin) |
| 14 | Blackbox Exporter | Monitoreo de endpoints externos |
| 15 | Demo Drilldown | Ejemplo completo Metrics → Logs → Traces |

---

## 🔌 API CONNECTOR

### **¿Qué es?**

Interfaz web para **agregar, configurar y monitorear APIs externas** sin editar código.

**Acceso**: http://localhost:8091

---

### **Agregar API Externa**

1. Abre http://localhost:8091
2. Click en **"+ Add API"**
3. Rellena el formulario:

```
┌────────────────────────────────────────┐
│  Add External API                      │
├────────────────────────────────────────┤
│  API Name: [Stripe_API___________]     │
│  URL: [https://api.stripe.com/____]    │
│  Auth Type: [Bearer Token ▼]           │
│  Token: [sk_live_xxxxxxxxxxxxx____]    │
│  Poll Interval: [60_] seconds          │
│  Timeout: [5000_] ms                   │
│  Cache TTL: [300_] seconds             │
│                                        │
│  [Cancel]  [Save API]                  │
└────────────────────────────────────────┘
```

4. Click **"Save API"**

**Resultado**:
- ✅ API agregada a base de datos (PostgreSQL)
- ✅ API Proxy comienza a monitorearla cada 60s
- ✅ Métricas disponibles en Prometheus en ~30s
- ✅ Dashboard "External APIs" muestra la nueva API

---

### **Tipos de Autenticación Soportados**

| Tipo | Ejemplo | Configuración |
|------|---------|---------------|
| Bearer Token | `Authorization: Bearer sk_live_xxx` | Token en campo "Token" |
| API Key (Header) | `X-API-Key: abc123` | Header name + value |
| Basic Auth | `Authorization: Basic base64(user:pass)` | Username + Password |
| OAuth2 | `Authorization: Bearer <access_token>` | Refresh token + endpoint |
| None | Sin autenticación | - |

---

### **Editar API**

1. En la lista, click en **"✏️ Edit"**
2. Modifica campos (ej: aumentar timeout a 10000ms)
3. Click **"Update API"**

**Cambios aplicados en**: ~30 segundos

---

### **Eliminar API**

1. Click en **"🗑️ Delete"**
2. Confirma en el diálogo
3. API removida de monitoreo

---

### **Ver Logs de API**

1. Click en **"📊 View Logs"**
2. Verás últimas 100 requests:

```
┌────────────────────────────────────────────────────────┐
│ Timestamp          Status  Duration  Response           │
├────────────────────────────────────────────────────────┤
│ 2025-01-15 10:30:05  200    124ms    {"data": "..."}   │
│ 2025-01-15 10:29:05  200    98ms     {"data": "..."}   │
│ 2025-01-15 10:28:05  500    5002ms   {"error": "..."}  │
│ 2025-01-15 10:27:05  200    110ms    (cached)          │
└────────────────────────────────────────────────────────┘
```

---

## 🔍 DRILLDOWN: Métricas → Logs → Traces

### **¿Qué es Drilldown?**

Capacidad de **navegar desde un síntoma (métrica alta) hasta la causa raíz (log/trace específico)**.

**Flujo**:

```
1. MÉTRICA ANÓMALA (Latencia p95 > 2000ms en Grafana)
        ↓
2. CLICK en gráfico → "View Logs"
        ↓
3. LOGS filtrados por timestamp + service
        ↓
4. LOG muestra trace_id
        ↓
5. CLICK en trace_id → Tempo
        ↓
6. TRACE completo con spans + duración
```

---

### **Ejemplo Práctico**

**Escenario**: Dashboard "Application RED" muestra latencia alta en endpoint `/api/checkout`

#### **Paso 1: Detectar métrica anómala**

```
📊 Dashboard: Application RED
   Panel: "Response Time p95 by Endpoint"
   
   /api/checkout: 2,450ms  ← ⚠️ ALTO (normal: 200ms)
   /api/products: 150ms
   /api/users: 180ms
```

#### **Paso 2: Drilldown a logs**

1. Click derecho en barra de `/api/checkout`
2. Select **"View Logs"** (o **"Explore"**)
3. Grafana abre **Loki** con filtros pre-configurados:

```logql
{job="api-server", endpoint="/api/checkout"} 
  | json 
  | duration > 2000
```

#### **Paso 3: Analizar logs**

```
[2025-01-15 10:30:05] ERROR api-server: 
  Checkout failed: Database connection timeout
  endpoint="/api/checkout"
  duration=2450ms
  trace_id=abc123xyz
  error="pq: connection refused"
```

**Identificamos**:
- ❌ Base de datos no responde
- 🔍 `trace_id=abc123xyz` para investigar más

#### **Paso 4: Drilldown a trace**

1. Click en `trace_id=abc123xyz` (es un link)
2. Grafana abre **Tempo** con el trace completo:

```
┌─────────────────────────────────────────────────────┐
│ Trace: abc123xyz (2,450ms total)                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  api-server: POST /api/checkout (2,450ms)          │
│    ├─ validate-cart (20ms) ✅                       │
│    ├─ check-inventory (35ms) ✅                     │
│    ├─ charge-payment (50ms) ✅                      │
│    └─ update-database (2,345ms) ❌ ← PROBLEMA AQUÍ │
│         Error: "connection refused"                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### **Paso 5: Causa raíz identificada**

**Problema**: PostgreSQL container reinició durante el checkout

**Solución**:
```bash
# Ver logs de PostgreSQL
docker logs rhinometric-postgres --tail 100

# Ver si está UP
docker ps | grep postgres

# Si está DOWN, reiniciar
docker restart rhinometric-postgres
```

---

## 🚨 ALERTAS Y NOTIFICACIONES

### **1. Crear Alerta**

#### **Paso 1: Ir a Alerting**

1. Menu lateral: **"Alerting"** (🔔 icono)
2. Click **"Alert Rules"**
3. Click **"+ New Alert Rule"**

#### **Paso 2: Configurar Query**

```
┌────────────────────────────────────────────┐
│  Set Alert Rule                            │
├────────────────────────────────────────────┤
│  Rule name: [High_API_Latency_________]    │
│                                            │
│  Query A: Prometheus                       │
│  ┌──────────────────────────────────────┐  │
│  │ histogram_quantile(0.95,             │  │
│  │   rate(api_response_time_bucket[5m]) │  │
│  │ ) > 2000                             │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  Condition: [A > 2000___]                  │
│  For: [5m__] (espera 5 min antes alertar)  │
│                                            │
└────────────────────────────────────────────┘
```

#### **Paso 3: Configurar Notificaciones**

```
┌────────────────────────────────────────────┐
│  Notifications                             │
├────────────────────────────────────────────┤
│  Contact Point: [Slack #alerts ▼]         │
│  Message:                                  │
│  ┌──────────────────────────────────────┐  │
│  │ 🚨 ALERT: API Latency > 2000ms       │  │
│  │                                       │  │
│  │ Value: {{ $values.A }}ms              │  │
│  │ Dashboard: [View]({{ $link }})        │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  [Cancel]  [Save Rule]                     │
└────────────────────────────────────────────┘
```

---

### **2. Contact Points (Canales)**

**Ir a**: Alerting → Contact Points → **"+ New Contact Point"**

#### **Slack**

```yaml
Name: Slack #alerts
Type: Slack
Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
Channel: #alerts
Username: Rhinometric Bot
Icon Emoji: :warning:
```

#### **Email**

```yaml
Name: DevOps Team
Type: Email
Addresses: devops@example.com, oncall@example.com
Subject: [Rhinometric] {{ .GroupLabels.alertname }}
```

#### **PagerDuty**

```yaml
Name: PagerDuty Oncall
Type: PagerDuty
Integration Key: your-integration-key-here
Severity: critical
```

#### **Webhook (Custom)**

```yaml
Name: Custom Webhook
Type: Webhook
URL: https://your-api.com/alerts
HTTP Method: POST
Content-Type: application/json
Body:
  {
    "alert": "{{ .GroupLabels.alertname }}",
    "value": "{{ $values.A }}",
    "timestamp": "{{ .StartsAt }}"
  }
```

---

### **3. Notification Policies**

**Ir a**: Alerting → Notification Policies

**Ejemplo**:

```
┌────────────────────────────────────────────────┐
│  Root Policy                                   │
│    ├─ [severity=critical] → PagerDuty          │
│    ├─ [severity=warning] → Slack #alerts       │
│    ├─ [severity=info] → Email (DevOps)         │
│    └─ [default] → Slack #monitoring            │
└────────────────────────────────────────────────┘
```

**Configurar**:

1. Click **"+ New Nested Policy"**
2. Label matchers: `severity = critical`
3. Contact Point: `PagerDuty Oncall`
4. Continue matching: `No` (detener aquí)
5. Group by: `alertname, instance`
6. Group wait: `30s`
7. Group interval: `5m`

---

### **4. Alertas Recomendadas (Templates)**

#### **Alta Latencia API**

```yaml
Alert: high_api_latency
Query: histogram_quantile(0.95, rate(api_response_time_bucket[5m])) > 2000
For: 5m
Severity: warning
Message: API p95 latency is {{ $value }}ms (threshold: 2000ms)
```

#### **Error Rate Alto**

```yaml
Alert: high_error_rate
Query: (rate(api_requests_total{status=~"5.."}[5m]) / rate(api_requests_total[5m])) * 100 > 5
For: 5m
Severity: critical
Message: Error rate is {{ $value }}% (threshold: 5%)
```

#### **CPU Alta**

```yaml
Alert: high_cpu_usage
Query: (100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)) > 80
For: 10m
Severity: warning
Message: CPU usage on {{ $labels.instance }} is {{ $value }}%
```

#### **Disco Lleno**

```yaml
Alert: disk_space_low
Query: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 15
For: 5m
Severity: critical
Message: Disk space on {{ $labels.mountpoint }} is only {{ $value }}% free
```

#### **PostgreSQL Down**

```yaml
Alert: postgres_down
Query: up{job="postgres-exporter"} == 0
For: 1m
Severity: critical
Message: PostgreSQL is DOWN
```

---

## 🔧 USO AVANZADO

### **1. Crear Dashboard Personalizado**

#### **Paso 1: Crear Dashboard**

1. Menu: **Dashboards** → **"+ New Dashboard"**
2. Click **"Add Visualization"**
3. Select **Data Source**: `Prometheus`

#### **Paso 2: Configurar Panel**

**Query** (ej: CPU por container):

```promql
rate(container_cpu_usage_seconds_total{name=~"rhinometric.*"}[5m]) * 100
```

**Panel Options**:
- Title: `CPU Usage by Container`
- Description: `CPU % last 5 minutes`
- Unit: `Percent (0-100)`
- Legend: `{{ name }}`

**Visualization**:
- Type: `Time Series`
- Style: `Lines`
- Line interpolation: `Smooth`
- Fill opacity: `10`

#### **Paso 3: Agregar más paneles**

- Click **"Add"** → **"Visualization"**
- Repite para métricas adicionales

#### **Paso 4: Guardar**

- Click **💾** (Save dashboard)
- Name: `My Custom Dashboard`
- Folder: `Rhinometric v2.1.0`

---

### **2. Variables en Dashboards**

**Uso**: Filtrar múltiples paneles por container, namespace, etc.

#### **Crear Variable**

1. Dashboard Settings (⚙️ arriba derecha)
2. **Variables** → **"+ New Variable"**
3. Configurar:

```
Name: container
Type: Query
Data Source: Prometheus
Query: label_values(container_cpu_usage_seconds_total, name)
Regex: /rhinometric-(.*)/
Multi-value: true
Include All: true
```

4. **Apply** y **Save**

#### **Usar Variable**

En queries:

```promql
rate(container_cpu_usage_seconds_total{name=~"$container"}[5m])
```

En títulos:

```
CPU Usage - $container
```

---

### **3. Annotations (Eventos)**

**Uso**: Marcar deploys, incidents, releases en dashboards

#### **Crear Annotation**

1. Dashboard Settings → **Annotations** → **"+ New"**
2. Configurar:

```yaml
Name: Deploys
Data Source: -- Grafana --
Query: tags @> ['deploy']
Color: Green
```

#### **Agregar Evento Manualmente**

1. En dashboard, click derecho en gráfico → **"Add Annotation"**
2. Text: `Deployed v2.1.0`
3. Tags: `deploy, production`
4. **Save**

**Resultado**: Línea vertical verde en todos los paneles del dashboard

---

### **4. Exportar/Importar Dashboards**

#### **Exportar**

1. Abrir dashboard
2. Settings (⚙️) → **JSON Model**
3. Copy JSON
4. Pegar en archivo `my-dashboard.json`

#### **Importar**

1. Dashboards → **"+ Import"**
2. Upload JSON file o pegar JSON
3. Select Prometheus data source
4. **Import**

---

## 🐛 TROUBLESHOOTING

### **❌ Panel muestra "No Data"**

**Posibles causas**:

1. **Query incorrecta**
   ```bash
   # Probar query en Prometheus directamente
   curl 'http://localhost:9090/api/v1/query?query=up'
   ```

2. **Métrica no existe**
   ```bash
   # Ver todas las métricas disponibles
   curl http://localhost:9090/api/v1/label/__name__/values | jq .
   ```

3. **Time range incorrecto**
   - Cambiar a "Last 1 hour" o "Last 24 hours"

4. **Scrape interval alto**
   - Espera 1-2 minutos para que aparezcan datos

---

### **❌ Dashboard muestra errores después de importar**

**Solución**:

1. Dashboard Settings → **Variables**
2. Para cada variable, verifica que:
   - Data Source sea correcto (`Prometheus`)
   - Query devuelva resultados (test con `Preview of Values`)

3. En cada panel, verifica:
   - Data Source sea `Prometheus` (no `-- Mixed --`)

---

### **❌ Alertas no se disparan**

**Checklist**:

1. **Verificar evaluación**:
   ```
   Alerting → Alert Rules → Ver estado
   # Debe estar "Pending" o "Firing", no "Normal"
   ```

2. **Probar query**:
   ```
   Explore → Prometheus → Pegar query de alerta
   # Debe devolver valores > threshold
   ```

3. **Verificar Contact Point**:
   ```
   Alerting → Contact Points → Click "Test"
   # Debe llegar notificación de prueba
   ```

4. **Ver logs de Grafana**:
   ```bash
   docker logs rhinometric-grafana | grep -i alert
   ```

---

### **❌ Drilldown no funciona (link a logs/traces)**

**Solución**:

1. Verificar Data Links en panel:
   ```
   Panel Edit → Data Links
   URL: /explore?left=...&datasource=Loki&...
   ```

2. Verificar que Loki tiene logs:
   ```bash
   curl http://localhost:3100/loki/api/v1/label/__name__/values
   ```

3. Verificar que logs tienen labels correctos:
   ```logql
   {job="api-server"} | json
   ```

---

## ❓ FAQ

### **¿Cuánto retención de datos tiene?**

- **Métricas (Prometheus)**: 15 días (configurable en `prometheus.yml`)
- **Logs (Loki)**: 15 días (configurable en `loki-config.yml`)
- **Traces (Tempo)**: 7 días (configurable en `tempo.yaml`)

**Cambiar retención**:

```yaml
# prometheus.yml
storage:
  tsdb:
    retention.time: 30d  # ← Cambiar a 30 días
```

```bash
docker restart rhinometric-prometheus
```

---

### **¿Puedo agregar mis propias métricas?**

Sí! Instrumenta tu app con:

- **Python**: `prometheus-client`
- **Node.js**: `prom-client`
- **Go**: `prometheus/client_golang`
- **Java**: `micrometer`

Ejemplo (Python):

```python
from prometheus_client import Counter, Histogram, start_http_server

# Métrica custom
requests_total = Counter('my_app_requests_total', 'Total requests', ['endpoint'])

@app.route('/api/hello')
def hello():
    requests_total.labels(endpoint='/api/hello').inc()
    return "Hello World"

# Exponer en puerto 8000
start_http_server(8000)
```

Luego agregar en `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'my-app'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

---

### **¿Cómo escalar Rhinometric?**

**Opción 1: Vertical (más recursos)**

```yaml
# docker-compose-v2.1.0.yml
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '4'       # ← Aumentar de 2 a 4
          memory: 8G      # ← Aumentar de 4G a 8G
```

**Opción 2: Horizontal (múltiples instancias)**

- Prometheus: Usa **federation** o **Thanos**
- Loki: Usa modo **microservices** con S3 backend
- Grafana: Usa **load balancer** + shared database

---

### **¿Puedo usar S3 para almacenamiento?**

Sí! Configura Loki con S3 backend:

```yaml
# loki-config.yml
storage_config:
  aws:
    s3: s3://us-east-1/my-bucket-loki
    s3forcepathstyle: true
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
```

---

### **¿Funciona en Kubernetes?**

Sí! Usa Helm chart:

```bash
helm repo add rhinometric https://charts.rhinometric.io
helm install rhinometric rhinometric/rhinometric-stack \
  --set grafana.adminPassword=yourpassword \
  --set mode=trial
```

---

### **¿Puedo cambiar de trial a full después?**

Sí! Cambia en `.env`:

```env
RHINOMETRIC_MODE=full
RHINOMETRIC_LICENSE_KEY=your-purchased-key
```

```bash
docker compose -f docker-compose-v2.1.0.yml up -d --force-recreate license-server
```

---

### **¿Rhinometric consume muchos recursos?**

**Uso típico** (17 containers):
- CPU: 1.5-2.5 vCPU (idle), hasta 4 vCPU (high load)
- RAM: 4-6 GB
- Disco: 2 GB/día (con retención 15d = ~30 GB)

**Optimizaciones**:
- Reducir retención a 7 días
- Aumentar scrape interval a 30s (en vez de 15s)
- Deshabilitar componentes no usados (Tempo si no usas tracing)

---

## 📚 RECURSOS ADICIONALES

- **Documentación Grafana**: https://grafana.com/docs/
- **PromQL Tutorial**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **LogQL Tutorial**: https://grafana.com/docs/loki/latest/logql/
- **Ejemplos de Dashboards**: https://grafana.com/grafana/dashboards/
- **Community Support**: https://github.com/Rafael2712/mi-proyecto/discussions

---

**✅ ¡Felicidades! Ahora dominas Rhinometric v2.1.0** 🎉

**Próximos pasos**:
1. Explora los 15 dashboards incluidos
2. Agrega tus primeras APIs en API Connector
3. Configura alertas críticas (CPU, disco, latencia)
4. Instrumenta tu aplicación con métricas custom
5. Configura backup automático (`./backup.sh`)

---

**Versión**: 1.0.0 | **Rhinometric**: v2.1.0 Trial | **Fecha**: Enero 2025
