# Rhinometric Console Backend Observability (v2.6.0)

## Overview

La versión 2.6.0 "Application Edition" transforma el backend de Rhinometric en un componente **completamente observable**, cerrando la brecha entre infraestructura y aplicación.

## Métricas Implementadas

### HTTP Metrics (Prometheus)

**Endpoint**: `http://rhinometric-console-backend:8100/metrics`

#### Request Metrics
- `http_requests_total{method, endpoint, status_code}` - Counter de requests totales
- `http_request_duration_seconds{method, endpoint}` - Histogram de latencias (buckets: 5ms a 10s)
- `http_requests_in_progress{method, endpoint}` - Gauge de requests activas
- `http_request_size_bytes{method, endpoint}` - Histogram de tamaño de request
- `http_response_size_bytes{method, endpoint}` - Histogram de tamaño de response

#### Error Metrics
- `http_errors_total{method, endpoint, status_code, error_type}` - Counter de errores
  - `error_type`: `client_error` (4xx), `server_error` (5xx), `exception`

#### Business Metrics
- `api_auth_attempts_total{result}` - Intentos de autenticación (`success`, `failed`, `expired`)
- `api_license_validations_total{status}` - Validaciones de licencia (`valid`, `invalid`, `expired`, `error`)
- `api_anomaly_queries_total{endpoint}` - Queries a AI Anomaly service
- `api_alert_operations_total{operation}` - Operaciones de alertas (`list`, `acknowledge`, `silence`, `create`)

#### Database Pool Metrics
- `db_connections_active` - Conexiones DB activas
- `db_connections_idle` - Conexiones DB idle en pool
- `db_query_duration_seconds{query_type}` - Duración de queries (`select`, `insert`, `update`, `delete`)

### OpenTelemetry Traces

**Export**: OTLP gRPC → `localhost:4317` → Jaeger

Cada HTTP request genera una traza con:
- **Service name**: `rhinometric-console-backend`
- **Span attributes**:
  - `http.method`
  - `http.target` (endpoint)
  - `http.status_code`
  - `http.user_agent`
- **Automatic instrumentation**:
  - FastAPI requests/responses
  - httpx outgoing calls (a Prometheus, Loki, AI Anomaly, etc.)

### Database Metrics (Postgres Exporter)

**Port**: `9187` (scraped by Prometheus)

Métricas clave exportadas por `postgres-exporter`:
- `pg_stat_database_numbackends` - Conexiones activas por database
- `pg_stat_database_xact_commit` - Rate de commits
- `pg_stat_database_xact_rollback` - Rate de rollbacks
- `pg_stat_database_tup_returned` - Rows leídas
- `pg_stat_database_tup_inserted` - Rows insertadas
- `pg_stat_database_tup_updated` - Rows actualizadas
- `pg_stat_database_tup_deleted` - Rows eliminadas
- `pg_stat_database_blks_read` - Disk blocks leídos
- `pg_stat_database_blks_hit` - Cache hits
- `pg_database_size_bytes` - Tamaño de database

### Redis Metrics (Redis Exporter)

**Port**: `9121` (scraped by Prometheus)

Métricas clave:
- `redis_connected_clients` - Clientes conectados
- `redis_commands_processed_total` - Comandos procesados
- `redis_keyspace_hits_total` - Cache hits
- `redis_keyspace_misses_total` - Cache misses
- `redis_memory_used_bytes` - Memoria usada
- `redis_evicted_keys_total` - Keys evicted

## Configuración

### Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: 'console-backend'
    static_configs:
      - targets: ['rhinometric-console-backend:8100']
    scrape_interval: 10s
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['rhinometric-postgres-exporter:9187']
    scrape_interval: 15s

  - job_name: 'redis'
    static_configs:
      - targets: ['rhinometric-redis-exporter:9121']
    scrape_interval: 15s
```

### Docker Compose Services

```yaml
services:
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/rhinometric_trial?sslmode=disable"

  redis-exporter:
    image: oliver006/redis_exporter:latest
    environment:
      REDIS_ADDR: "redis:6379"
```

## Dashboards

### 06 - Rhinometric Console Backend
**UID**: `rhinometric-backend`  
**Location**: `grafana/provisioning/dashboards/json/06-backend-observability.json`

**Panels**:
1. **Request Rate** (req/s) - Tráfico general del API
2. **Latency p95** (ms) - Performance perceived por usuarios
3. **Error Rate** (err/s) - Tasa de errores 4xx/5xx
4. **Active Requests** - Requests en progreso
5. **Request Rate by Endpoint** - Tráfico por endpoint
6. **Request Latency Percentiles** (p50, p95, p99) - Distribución de latencias
7. **Postgres Connections** - Conexiones activas a DB
8. **Postgres Transactions** - Commits/s y Rollbacks/s
9. **Redis Activity** - Clientes y comandos/s
10. **Auth Attempts** - Intentos de login (success/failed)
11. **License Validations** - Validaciones por status

## Queries Útiles

### Latencia promedio por endpoint
```promql
rate(http_request_duration_seconds_sum{job="console-backend"}[5m])
/
rate(http_request_duration_seconds_count{job="console-backend"}[5m])
```

### Error rate percentage
```promql
100 * (
  rate(http_errors_total{job="console-backend"}[5m])
  /
  rate(http_requests_total{job="console-backend"}[5m])
)
```

### Endpoints más lentos (p95)
```promql
topk(5, 
  histogram_quantile(0.95, 
    rate(http_request_duration_seconds_bucket{job="console-backend"}[5m])
  )
)
```

### DB connection pool utilization
```promql
db_connections_active / (db_connections_active + db_connections_idle) * 100
```

### Postgres cache hit ratio
```promql
100 * (
  pg_stat_database_blks_hit{datname="rhinometric_trial"}
  /
  (pg_stat_database_blks_hit{datname="rhinometric_trial"} + pg_stat_database_blks_read{datname="rhinometric_trial"})
)
```

### Redis hit rate
```promql
100 * (
  rate(redis_keyspace_hits_total[5m])
  /
  (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
)
```

## Correlación con Traces (Jaeger)

Desde cualquier panel del dashboard, puedes hacer drill-down a trazas:

1. Click en un spike de latencia o error
2. Data link → **View Traces** → Jaeger
3. Filtra por:
   - `service.name=rhinometric-console-backend`
   - `http.status_code=500` (para errores)
   - `http.target=/api/anomalies` (para endpoint específico)

## Alertas Recomendadas

### High Error Rate
```yaml
- alert: BackendHighErrorRate
  expr: rate(http_errors_total{job="console-backend"}[5m]) > 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Backend error rate alto: {{ $value }} errores/s"
```

### High Latency
```yaml
- alert: BackendHighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="console-backend"}[5m])) > 0.5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Backend latency p95 > 500ms"
```

### Postgres Connections High
```yaml
- alert: PostgresConnectionsHigh
  expr: pg_stat_database_numbackends{datname="rhinometric_trial"} > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Postgres connections alto: {{ $value }}"
```

### Redis Memory High
```yaml
- alert: RedisMemoryHigh
  expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Redis memory usage > 90%"
```

## Próximos Pasos (Fase 2)

- [ ] Data links desde dashboards → Loki logs
- [ ] Data links desde dashboards → Jaeger traces
- [ ] Logs estructurados en JSON (FastAPI logging)
- [ ] Correlación request_id entre métricas/logs/traces
- [ ] Alertas integradas con AI Anomaly detection

## Referencias

- **Prometheus Client Python**: https://github.com/prometheus/client_python
- **OpenTelemetry Python**: https://opentelemetry.io/docs/instrumentation/python/
- **Postgres Exporter**: https://github.com/prometheus-community/postgres_exporter
- **Redis Exporter**: https://github.com/oliver006/redis_exporter
