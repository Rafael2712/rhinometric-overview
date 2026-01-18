# 📊 RHINOMETRIC Dashboards - Guía de Uso

## 🎯 Dashboards Disponibles

### 1. 🎛️ RHINOMETRIC Control Center
**Archivo**: `rhinometric-control-center.json`  
**Puerto**: Dashboards embebidos vía iframe

**Características**:
- Interfaz embebida de **API Connector** (puerto 8000)
- Interfaz embebida de **Dashboard Builder** (puerto 8001)
- Métricas en tiempo real de ambos servicios
- Monitoreo de estado, latencia y tasa de error
- Vista unificada de todos los recursos del sistema

**Paneles**:
- 🔗 API Connector (iframe + métricas)
- 📊 Dashboard Builder (iframe + métricas)
- 📈 System Metrics (CPU, Memory, Health)

**Casos de uso**:
- Gestión centralizada de la plataforma
- Crear conexiones a datasources sin salir de Grafana
- Diseñar dashboards visualmente desde Grafana
- Monitoreo unificado de servicios

---

### 2. 🎯 RHINOMETRIC Observability Cockpit
**Archivo**: `observability-cockpit.json`  
**Enfoque**: Monitoreo del stack de observabilidad

**Características**:
- Métricas de **Prometheus** (samples/s, TSDB size, query rate)
- Logs de **Loki** (ingestion rate, streams, query latency)
- Traces de **Tempo** (spans/s, trace count, storage)
- Métricas de **cAdvisor** (containers, CPU, memory)
- Vista en tiempo real de logs de la plataforma

**Paneles**:
- 🔥 Prometheus: Ingestion, storage, queries
- 🔍 Loki: Log aggregation, streams, queries
- 🔗 Tempo: Distributed tracing metrics
- 📈 cAdvisor: Container resource usage
- 📋 Recent Platform Logs (filterable)

**Casos de uso**:
- Verificar salud del stack de observabilidad
- Detectar problemas de ingesta de métricas/logs
- Analizar rendimiento de consultas
- Monitorear consumo de recursos de contenedores

---

### 3. ⚡ RHINOMETRIC API Performance
**Archivo**: `api-performance.json`  
**Enfoque**: Rendimiento de APIs REST

**Características**:
- Métricas de **API Connector** (requests/s, latency, error rate)
- Métricas de **Dashboard Builder** (dashboards creados, usuarios activos)
- Métricas de **License Server** (validaciones, licencias activas)
- Métricas de **Landing Page** (page views, response time)
- Top endpoints por tráfico

**Paneles**:
- 🔗 API Connector: Status, throughput, latency (p50/p95/p99)
- 📊 Dashboard Builder: Creation rate, active users
- 🔐 License Server: Validations, failures
- 🌐 Landing Page: Traffic, visitors
- 📋 Top Endpoints (tables)

**Casos de uso**:
- Identificar endpoints lentos
- Detectar picos de tráfico
- Analizar tasas de error
- Optimizar rendimiento de APIs

---

## 🚀 Instalación

### Método 1: Script Automático (Recomendado)

```bash
# 1. Obtener Grafana API Token (ver HOW_TO_GET_GRAFANA_TOKEN.md)
export GRAFANA_API_TOKEN="tu-token-aqui"

# 2. Ejecutar script de importación
./import-dashboards.sh
```

**Salida esperada**:
```
🚀 RHINOMETRIC Dashboard Import Script

📡 Verificando conexión a Grafana...
✅ Grafana está corriendo

📂 Importando dashboards desde: ./grafana-dashboards

📊 Importando: rhinometric-control-center
✅ Dashboard importado: rhinometric-control-center
   UID: rhinometric-control
   URL: http://localhost:80/d/rhinometric-control

📊 Importando: observability-cockpit
✅ Dashboard importado: observability-cockpit
   UID: observability-cockpit
   URL: http://localhost:80/d/observability-cockpit

📊 Importando: api-performance
✅ Dashboard importado: api-performance
   UID: api-performance
   URL: http://localhost:80/d/api-performance

✅ 3 dashboard(s) importado(s) exitosamente

🎉 Proceso completado!
```

---

### Método 2: Importación Manual

1. **Abrir Grafana**: http://localhost:80
2. **Login**: admin / admin
3. **Ir a Dashboards** → Click en "Import"
4. **Upload JSON**:
   - Seleccionar archivo desde `grafana-dashboards/`
   - Click "Import"
5. **Repetir** para cada dashboard

---

## 📋 Verificación

### 1. Verificar importación exitosa

```bash
# Listar dashboards
curl -H "Authorization: Bearer $GRAFANA_API_TOKEN" \
  http://localhost:80/api/search?type=dash-db | jq
```

**Salida esperada**:
```json
[
  {
    "id": 1,
    "uid": "rhinometric-control",
    "title": "🎛️ RHINOMETRIC Control Center",
    "uri": "db/rhinometric-control-center",
    "url": "/d/rhinometric-control/rhinometric-control-center",
    "type": "dash-db",
    "tags": ["rhinometric", "control", "admin"]
  },
  {
    "id": 2,
    "uid": "observability-cockpit",
    "title": "🎯 RHINOMETRIC Observability Cockpit",
    ...
  },
  {
    "id": 3,
    "uid": "api-performance",
    "title": "⚡ RHINOMETRIC API Performance",
    ...
  }
]
```

### 2. Acceder a dashboards

| Dashboard | URL |
|-----------|-----|
| Control Center | http://localhost:80/d/rhinometric-control |
| Observability Cockpit | http://localhost:80/d/observability-cockpit |
| API Performance | http://localhost:80/d/api-performance |

---

## 🔧 Configuración de Datasources

Los dashboards asumen los siguientes datasources en Grafana:

### Prometheus
- **Name**: `Prometheus`
- **URL**: `http://rhinometric-prometheus:9090`
- **Access**: Server (default)

### Loki
- **Name**: `Loki`
- **URL**: `http://rhinometric-loki:3100`
- **Access**: Server (default)

### Tempo
- **Name**: `Tempo`
- **URL**: `http://rhinometric-tempo:3200`
- **Access**: Server (default)

**Verificar datasources**:
```bash
curl -H "Authorization: Bearer $GRAFANA_API_TOKEN" \
  http://localhost:80/api/datasources | jq
```

**Agregar datasource (si falta)**:
```bash
# Ejemplo: Prometheus
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:80/api/datasources \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://rhinometric-prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

---

## ⚠️ Troubleshooting

### Problema: Iframes vacíos en Control Center

**Causa**: Política de CSP (Content Security Policy) del navegador

**Soluciones**:

1. **Opción A - Acceso directo** (recomendado):
   - API Connector: http://localhost:8000
   - Dashboard Builder: http://localhost:8001

2. **Opción B - Configurar CSP**:
   ```yaml
   # docker-compose-v2.2.0.yml (Grafana service)
   environment:
     - GF_SECURITY_ALLOW_EMBEDDING=true
     - GF_SECURITY_COOKIE_SAMESITE=none
   ```

3. **Opción C - Extensión de navegador**:
   - Chrome/Edge: "Ignore X-Frame headers"
   - Firefox: "Disable Content-Security-Policy"

---

### Problema: Paneles sin datos

**Diagnóstico**:
```bash
# Verificar que Prometheus tenga targets activos
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'

# Verificar que hay métricas
curl http://localhost:9090/api/v1/query?query=up | jq
```

**Solución**:
1. Verificar contenedores corriendo:
   ```bash
   docker ps | grep rhinometric
   ```

2. Verificar scrape configs de Prometheus:
   ```bash
   docker exec rhinometric-prometheus cat /etc/prometheus/prometheus.yml
   ```

3. Regenerar tráfico:
   ```bash
   ./generate-traces-simple.py
   ```

---

### Problema: Script de importación falla

**Error**: `GRAFANA_API_TOKEN not configured`

**Solución**:
1. Crear token (ver HOW_TO_GET_GRAFANA_TOKEN.md)
2. Exportar variable:
   ```bash
   export GRAFANA_API_TOKEN="tu-token-aqui"
   ```

**Error**: `Cannot connect to Grafana`

**Solución**:
1. Verificar Grafana corriendo:
   ```bash
   docker ps | grep grafana
   ```

2. Verificar puerto 80 disponible:
   ```bash
   curl http://localhost:80/api/health
   ```

---

## 📊 Mejores Prácticas

### 1. Configurar Auto-Refresh
- Control Center: **5s** (para UIs responsivas)
- Observability Cockpit: **10s** (para métricas detalladas)
- API Performance: **5s** (para detección rápida de issues)

### 2. Configurar Alertas
```bash
# Ejemplo: Alert para error rate alto
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:80/api/alerts \
  -d '{
    "name": "High Error Rate - API Connector",
    "conditions": [{
      "evaluator": {"type": "gt", "params": [5]},
      "query": {
        "model": {
          "expr": "sum(rate(http_requests_total{job=\"api-connector\",status=~\"5..\"}[5m])) / sum(rate(http_requests_total{job=\"api-connector\"}[5m])) * 100"
        }
      }
    }],
    "notifications": [{"uid": "slack-channel"}]
  }'
```

### 3. Crear Snapshots
```bash
# Para compartir dashboards sin acceso a Grafana
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:80/api/snapshots \
  -d '{"dashboard": {...}, "expires": 86400}'
```

---

## 🔗 Links Útiles

- **Grafana UI**: http://localhost:80
- **API Connector**: http://localhost:8000
- **Dashboard Builder**: http://localhost:8001
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Tempo**: http://localhost:3200

## 📚 Documentación

- [Grafana Dashboard JSON Model](https://grafana.com/docs/grafana/latest/dashboards/json-model/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Loki LogQL](https://grafana.com/docs/loki/latest/logql/)
- [Tempo TraceQL](https://grafana.com/docs/tempo/latest/traceql/)

---

**Versión**: 2.4.0  
**Última actualización**: 2024  
**Autor**: RHINOMETRIC Team
