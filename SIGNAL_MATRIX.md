# 📊 SIGNAL MATRIX - RHINOMETRIC v2.5.0

**Fecha de auditoría:** 17 de enero de 2026  
**Versión auditada:** Rhinometric v2.5.0 Enterprise Edition  
**Auditor:** Sistema automatizado de análisis de correlación

---

## RESUMEN EJECUTIVO

De **16 señales críticas** analizadas:
- ✅ **COMPLETO**: 0 señales (0%)
- ⚠️ **PARCIAL**: 11 señales (69%)
- ❌ **PENDIENTE**: 5 señales (31%)

**HALLAZGO CRÍTICO**: Ninguna señal tiene correlación completa entre todas las capas (métrica → IA → alerta → dashboard → logs → traces).

---

## MATRIZ DE SEÑALES

| # | Signal | Metric Source | AI Anomaly | Alert Rule | Dashboards | Logs | Traces | Estado | Prioridad |
|---|--------|---------------|------------|------------|------------|------|--------|--------|-----------|
| 1 | `http_latency_p95` | **NO EXISTE** en Prometheus | ✅ Config | ❌ NO | ✅ AI Dashboard | ❌ NO | ❌ NO | ❌ PENDIENTE | P0 |
| 2 | `http_latency_p99` | **NO EXISTE** en Prometheus | ✅ Config | ❌ NO | ✅ AI Dashboard | ❌ NO | ❌ NO | ❌ PENDIENTE | P0 |
| 3 | `http_error_rate` | **NO EXISTE** en Prometheus | ✅ Config | ❌ NO | ✅ AI Dashboard | ❌ NO | ❌ NO | ❌ PENDIENTE | P0 |
| 4 | `http_request_rate` | **NO EXISTE** en Prometheus | ✅ Config | ❌ NO | ✅ AI Dashboard | ❌ NO | ❌ NO | ❌ PENDIENTE | P0 |
| 5 | `node_cpu_usage` | ✅ node-exporter | ✅ Config + Models | ✅ HighCPUUsage | ✅ System Monitoring | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P0 |
| 6 | `node_memory_usage` | ✅ node-exporter | ✅ Config + Models | ✅ HighMemoryUsage | ✅ System Monitoring | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P0 |
| 7 | `node_disk_usage` | ✅ node-exporter | ✅ Config | ✅ HighDiskUsage | ❌ NO panel dedicado | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P1 |
| 8 | `node_disk_io` | ✅ node-exporter | ✅ Config | ❌ NO | ❌ NO panel dedicado | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P1 |
| 9 | `container_cpu_usage` | ✅ cAdvisor | ✅ Config | ✅ HighContainerMemory | ✅ Docker Containers | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P1 |
| 10 | `container_memory_usage` | ✅ cAdvisor | ✅ Config | ✅ HighContainerMemory | ✅ Docker Containers | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P1 |
| 11 | `node_network_receive` | ✅ node-exporter | ✅ Config | ❌ NO | ❌ NO panel dedicado | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P2 |
| 12 | `node_network_transmit` | ✅ node-exporter | ✅ Config | ❌ NO | ❌ NO panel dedicado | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P2 |
| 13 | `postgres_connections` | **NO EXISTE** pg_exporter | ✅ Config | ❌ NO | ❌ NO | ❌ NO | ❌ NO | ❌ PENDIENTE | P1 |
| 14 | `postgres_query_duration` | **NO EXISTE** pg_exporter | ✅ Config | ✅ SlowPostgreSQLQueries | ❌ NO | ❌ NO | ❌ NO | ⚠️ PARCIAL | P1 |
| 15 | `license_validation_rate` | ⚠️ license-server | ✅ Config | ✅ LicenseValidationFailing | ✅ License Status | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P0 |
| 16 | `license_expired_count` | **NO VERIFICADO** | ✅ Config | ❌ NO | ✅ License Status | ⚠️ PARCIAL | ❌ NO | ⚠️ PARCIAL | P1 |

---

## ANÁLISIS DETALLADO POR SEÑAL

### 🔴 SEÑALES P0 CRÍTICAS

#### 1. `http_latency_p95` - **PENDIENTE**

**Métrica en Prometheus:**
- ❌ **NO EXISTE** - Query configurada: `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`
- ❌ No hay ningún job que exporte esta métrica con histograms
- ❌ No existe en ningún scrape_config de prometheus-v2.2.yml

**IA de Anomalías:**
- ✅ Configurada en `config.yaml` línea 247
- ✅ Modelos: isolation_forest, lof, statistical
- ✅ Thresholds: warning=1.0s, critical=5.0s
- ✅ Sensitivity: medium
- ⚠️ **PROBLEMA**: La IA lee una métrica que NO existe en Prometheus

**Alertas:**
- ❌ **NO EXISTE** regla de alerta
- ❌ No aparece en `infrastructure.yml`, `application.yml`, ni `services.yml`

**Dashboards:**
- ✅ Aparece en `07_ai_anomaly_detection.json` línea 1514
- ✅ Panel: "HTTP Latency P95 Anomalies"
- ⚠️ **PROBLEMA**: Muestra anomalías de métrica inexistente

**Logs:**
- ❌ **NO CONFIGURADO** - Promtail solo captura logs de Docker sin parsing
- ❌ No hay campos estructurados: sin `latency_ms`, sin `status_code`, sin `endpoint`
- ❌ Formato: JSON Docker crudo sin extracción de campos de aplicación

**Traces:**
- ❌ **NO INSTRUMENTADO** - No hay servicios backend enviando traces a Jaeger
- ⚠️ Jaeger corriendo en puerto 16686 pero sin traces de servicios reales
- ❌ No hay atributos `http.route`, `http.status_code`, `duration`

**VEREDICTO**: ❌ **NO FUNCIONAL** - Toda la cadena está rota desde el origen

---

#### 2. `http_error_rate` - **PENDIENTE**

**Métrica en Prometheus:**
- ❌ **NO EXISTE** - Query: `sum(rate(http_requests_total{status=~"5.."}[5m]))`
- ❌ Ningún servicio exporta contador `http_requests_total`

**IA de Anomalías:**
- ✅ Configurada (línea 232 config.yaml)
- ✅ Priority: CRITICAL
- ✅ alert_on_any_anomaly: true
- ⚠️ Lee métrica inexistente

**Alertas:**
- ❌ **NO EXISTE** regla específica para error rate HTTP

**Dashboards:**
- ✅ Panel en AI Anomaly dashboard (línea 1271)
- ⚠️ Muestra datos de métrica inexistente

**Logs/Traces:**
- ❌ Sin logs estructurados con `status_code`
- ❌ Sin traces con `http.status_code`

**VEREDICTO**: ❌ **NO FUNCIONAL**

---

#### 3-4. `http_request_rate` y `http_latency_p99` - **PENDIENTE**

**Mismo problema que señales 1-2:**
- ❌ Métricas NO existen en Prometheus
- ✅ IA configurada pero leyendo vacío
- ❌ Sin alertas
- ✅ Dashboards de IA muestran "vacío"
- ❌ Sin logs/traces correlacionados

---

#### 5. `node_cpu_usage` - ⚠️ **PARCIAL**

**Métrica en Prometheus:**
- ✅ **EXISTE** - Job: `node-exporter`
- ✅ Query real: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- ✅ Scrapeando correctamente cada 30s

**IA de Anomalías:**
- ✅ Configurada (línea 126 config.yaml)
- ✅ Modelos: isolation_forest, lof, statistical
- ✅ Thresholds: warning=70%, critical=90%
- ✅ Sensitivity: low (reducida para evitar falsos positivos)

**Alertas:**
- ✅ **EXISTE** - `HighCPUUsage` (infrastructure.yml línea 10)
- ✅ Expr: `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80`
- ✅ For: 5m
- ✅ Severity: warning
- ✅ **EXISTE** - `CriticalCPUUsage` (línea 21)
- ✅ Threshold: >95% por 2m, severity: critical

**Dashboards:**
- ✅ Panel en `06_system_metrics.json` (System Monitoring)
- ✅ Panel en AI Anomaly dashboard

**Logs:**
- ⚠️ **PARCIAL** - Promtail captura logs de contenedores
- ⚠️ Formato: JSON Docker con campos `container_id`, `stream`, `output`
- ❌ No hay campos específicos de CPU en logs (esto es normal para métricas de sistema)
- ✅ Logs generales disponibles para contexto temporal

**Traces:**
- ❌ **NO APLICA** - CPU es métrica de infraestructura, no genera traces

**FLUJO DE CORRELACIÓN:**
```
1. Prometheus detecta CPU > 80% → ✅
2. IA detecta anomalía en CPU → ✅
3. Alerta "HighCPUUsage" se dispara → ✅
4. Dashboard muestra spike de CPU → ✅
5. Logs disponibles para contexto → ⚠️ (sin campos específicos)
6. Traces → N/A
```

**VEREDICTO**: ⚠️ **FUNCIONAL PERO CORRELACIÓN MANUAL** - Puedes ver anomalía + alerta + dashboard, pero debes ir manualmente a logs filtrando por tiempo + instancia

---

#### 6. `node_memory_usage` - ⚠️ **PARCIAL**

**Similar a CPU:**
- ✅ Métrica existe en Prometheus
- ✅ IA configurada correctamente
- ✅ Alertas: `HighMemoryUsage` (>85% por 5m), `CriticalMemoryUsage` (>95% por 2m)
- ✅ Dashboards en System Monitoring y AI
- ⚠️ Logs disponibles pero no específicos
- ❌ Traces N/A

**VEREDICTO**: ⚠️ **FUNCIONAL PERO CORRELACIÓN MANUAL**

---

#### 15. `license_validation_rate` - ⚠️ **PARCIAL**

**Métrica en Prometheus:**
- ⚠️ **PROBABLEMENTE EXISTE** - License-server exporta en `/api/metrics`
- ✅ Job configurado: `license-server-v2` en prometheus-v2.2.yml línea 96
- ⚠️ **NO VERIFICADO** - No pude leer el código del license-server para confirmar nombre exacto

**IA de Anomalías:**
- ✅ Configurada (línea 380 config.yaml)
- ✅ Models: isolation_forest, statistical
- ✅ Sensitivity: low

**Alertas:**
- ✅ **EXISTE** - `LicenseValidationFailing` (application.yml línea 90)
- ✅ Expr: `rate(rhinometric_license_validation_errors_total[5m]) > 0.1`
- ✅ For: 5m, severity: warning

**Dashboards:**
- ✅ Panel en `07_license_status.json`

**Logs:**
- ⚠️ License-server tiene logging (veo imports en backend/routers/license.py)
- ❌ Promtail NO parsea campos específicos de licencia

**Traces:**
- ❌ License-server NO instrumentado con OTEL

**VEREDICTO**: ⚠️ **FUNCIONAL BÁSICO** - Métrica + alerta + dashboard, pero sin logs estructurados ni traces

---

### ❌ SEÑALES NO FUNCIONALES (PostgreSQL, Redis)

#### 13-14. PostgreSQL Metrics - **PENDIENTE**

**PROBLEMA CRÍTICO:**
```yaml
# En prometheus-v2.2.yml línea 102-108:
# DISABLED: postgres-exporter not configured
# - job_name: 'postgres-exporter'
#   static_configs:
#     - targets: ['postgres-exporter:9187']
```

- ❌ **postgres-exporter NO EXISTE** en docker-compose
- ❌ Métricas `pg_stat_activity_count`, `pg_stat_statements_*` NO disponibles
- ✅ IA configurada para leerlas (pero lee vacío)
- ✅ Alertas configuradas (pero nunca se disparan)
- ❌ No hay dashboards de PostgreSQL
- ❌ No hay logs estructurados de queries
- ❌ No hay traces de queries

**VEREDICTO**: ❌ **COMPLETAMENTE NO FUNCIONAL** - Stack PostgreSQL sin observabilidad

---

## 🔴 PROBLEMAS CRÍTICOS IDENTIFICADOS

### PROBLEMA #1: Métricas HTTP Fantasma (P0)

**Severidad**: 🔴 CRÍTICO  
**Impacto**: La UI muestra métricas de IA que NO EXISTEN

**Detalle:**
- La IA está configurada para leer `http_latency_p95`, `http_error_rate`, `http_request_rate`
- **NINGUNA** de estas métricas existe en Prometheus
- No hay ningún servicio HTTP instrumentado exportando estas métricas
- Los dashboards de AI Anomaly muestran paneles vacíos o con NaN

**Causa Raíz:**
- La configuración de la IA asume que hay una aplicación HTTP instrumentada
- El stack actual NO tiene ningún backend HTTP real con métricas
- Solo hay servicios de infraestructura (Prometheus, Grafana, Loki)

**Solución Requerida:**
1. **Opción A (Rápida)**: Desactivar estas métricas en `config.yaml`
   ```yaml
   - name: "http_latency_p95"
     enabled: false  # ← Cambiar a false
   ```

2. **Opción B (Correcta)**: Instrumentar rhinometric-console-backend con Prometheus client
   - Añadir `prometheus_client` a requirements.txt
   - Crear middleware en FastAPI para métricas HTTP
   - Exportar `http_request_duration_seconds_bucket` (histogram)
   - Exportar `http_requests_total` (counter con label `status`)

**Tiempo Estimado:**
- Opción A: 5 minutos
- Opción B: 2-3 horas

---

### PROBLEMA #2: PostgreSQL Sin Observabilidad (P0)

**Severidad**: 🔴 CRÍTICO  
**Impacto**: Base de datos crítica sin monitoring

**Detalle:**
- PostgreSQL es dependency de license-server y console-backend
- **NO HAY** postgres-exporter instalado
- **NO HAY** métricas de conexiones, queries, locks, cache hit rate
- La IA está configurada para monitorear PostgreSQL pero lee vacío
- Hay alertas de PostgreSQL que NUNCA se dispararán

**Solución Requerida:**
```yaml
# Añadir a docker-compose-trial.yml:
postgres-exporter:
  image: prometheuscommunity/postgres-exporter:latest
  container_name: rhinometric-postgres-exporter
  environment:
    DATA_SOURCE_NAME: "postgresql://postgres:trial_rhinometric_2024@postgres:5432/rhinometric_trial?sslmode=disable"
  networks:
    - rhinometric_network
  depends_on:
    - postgres
```

**Tiempo Estimado:** 1 hora

---

### PROBLEMA #3: Logs Sin Estructura (P0)

**Severidad**: 🔴 CRÍTICO  
**Impacto**: Imposible correlacionar anomalías con logs

**Detalle Actual:**
```yaml
# promtail-config.yml captura logs pero sin parsing:
- json:
    expressions:
      output: log  # Solo texto crudo
      stream: stream
```

**Lo que tienes:**
- Logs de contenedores en formato JSON Docker
- Campo `output` con texto plano sin estructura

**Lo que necesitas para correlación:**
```json
{
  "timestamp": "2026-01-17T10:30:45Z",
  "service": "console-backend",
  "level": "ERROR",
  "method": "GET",
  "path": "/api/users",
  "status_code": 500,
  "latency_ms": 1245,
  "error": "Database connection timeout",
  "trace_id": "abc123",
  "request_id": "xyz789"
}
```

**Solución Requerida:**
1. **Backend**: Usar logging estructurado
   ```python
   import structlog
   logger = structlog.get_logger()
   logger.info("request_completed", 
               method="GET", 
               path="/api/users",
               status_code=200,
               latency_ms=45)
   ```

2. **Promtail**: Parsear JSON de aplicación
   ```yaml
   - json:
       expressions:
         level:
         service:
         method:
         path:
         status_code:
         latency_ms:
         error:
         trace_id:
   - labels:
       level:
       service:
       status_code:
   ```

**Tiempo Estimado:** 4-6 horas

---

### PROBLEMA #4: Zero Tracing (P1)

**Severidad**: 🟡 IMPORTANTE  
**Impacto**: No se puede rastrear latencias end-to-end

**Detalle:**
- Jaeger está corriendo en puerto 16686 (UI) y recibiendo en puertos 14268 (HTTP), 14250 (gRPC), 4317/4318 (OTLP)
- **NINGÚN** servicio real está instrumentado con OpenTelemetry
- No hay traces de:
  - rhinometric-console-backend (FastAPI)
  - license-server (Flask)
  - ai-anomaly (FastAPI)

**Solución Requerida:**
```python
# En cada servicio FastAPI:
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="jaeger:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Instrumentar app
FastAPIInstrumentor.instrument_app(app)
```

**Tiempo Estimado:** 6-8 horas (para los 3 servicios)

---

## 📋 ROADMAP DE CORRECCIÓN

### SPRINT 1: PARIDAD MÉTRICA-ALERTA-DASHBOARD (Semana 1-2)

**Objetivo**: Que cada señal crítica tenga métrica + alerta + panel

#### Tareas P0 (CRÍTICAS - 3 días):

- [ ] **HTTP-01**: Instrumentar console-backend con Prometheus client
  - Añadir middleware de métricas HTTP
  - Exportar histograms de latencia
  - Exportar counters de requests/errors
  - **Tiempo**: 3 horas
  - **Validación**: `curl localhost:8105/metrics` muestra `http_request_duration_seconds_bucket`

- [ ] **HTTP-02**: Crear alertas HTTP faltantes
  ```yaml
  # Añadir a config/rules/alerts/application.yml:
  - alert: HighHttpLatencyP95
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High HTTP P95 latency"
  
  - alert: HighHttpErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High HTTP error rate (5xx)"
  ```
  - **Tiempo**: 1 hora

- [ ] **PG-01**: Desplegar postgres-exporter
  - Añadir servicio a docker-compose
  - Habilitar job en prometheus-v2.2.yml
  - **Tiempo**: 1 hora

- [ ] **PG-02**: Crear dashboards PostgreSQL
  - Panel de conexiones activas
  - Panel de query duration p95
  - Panel de cache hit rate
  - **Tiempo**: 2 horas

#### Tareas P1 (IMPORTANTES - 2 días):

- [ ] **DISK-01**: Añadir panel de disk I/O a System Monitoring dashboard
- [ ] **NET-01**: Añadir paneles de network rate a System Monitoring
- [ ] **AI-01**: Desactivar métricas fantasma en config.yaml hasta que existan
  ```yaml
  # En rhinometric-ai-anomaly/config.yaml:
  - name: "http_latency_p95"
    enabled: false  # ← DESACTIVAR hasta que exista la métrica
  ```

---

### SPRINT 2: CORRELACIÓN LOGS/TRACES (Semana 3-4)

**Objetivo**: Poder saltar de anomalía → logs → traces

#### Tareas P0 (CRÍTICAS - 5 días):

- [ ] **LOG-01**: Implementar logging estructurado en console-backend
  ```python
  import structlog
  structlog.configure(
      processors=[
          structlog.stdlib.add_log_level,
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.JSONRenderer()
      ]
  )
  ```
  - **Tiempo**: 4 horas

- [ ] **LOG-02**: Añadir campos de correlación
  - `trace_id` (de OpenTelemetry)
  - `request_id` (UUID por request)
  - `method`, `path`, `status_code`, `latency_ms`
  - **Tiempo**: 2 horas

- [ ] **LOG-03**: Configurar Promtail para parsear JSON estructurado
  ```yaml
  pipeline_stages:
    - json:
        expressions:
          timestamp:
          level:
          service:
          method:
          path:
          status_code:
          latency_ms:
          trace_id:
          error:
    - labels:
        level:
        service:
        status_code:
    - timestamp:
        source: timestamp
        format: RFC3339
  ```
  - **Tiempo**: 2 horas

- [ ] **TRACE-01**: Instrumentar console-backend con OpenTelemetry
  - FastAPIInstrumentor
  - Exportar a tempo:4317
  - **Tiempo**: 3 horas

- [ ] **TRACE-02**: Instrumentar license-server con OTEL
  - FlaskInstrumentor
  - **Tiempo**: 2 horas

- [ ] **TRACE-03**: Instrumentar ai-anomaly con OTEL
  - FastAPIInstrumentor
  - **Tiempo**: 2 horas

#### Tareas P1 (IMPORTANTES - 3 días):

- [ ] **UI-01**: Añadir botón "View Logs" desde página de Anomalies
  ```typescript
  const viewLogsForAnomaly = (anomaly: Anomaly) => {
    const from = anomaly.timestamp - 300000; // 5 min antes
    const to = anomaly.timestamp + 300000;   // 5 min después
    const url = `http://localhost:3000/explore?orgId=1&left=${encodeURIComponent(JSON.stringify({
      datasource: 'loki',
      queries: [{ 
        refId: 'A', 
        expr: `{service="${anomaly.service}"} | json | latency_ms > 1000`,
        range: { from, to }
      }]
    }))}`;
    window.open(url, '_blank');
  };
  ```
  - **Tiempo**: 2 horas

- [ ] **UI-02**: Añadir botón "View Traces" desde página de Anomalies
  - Similar pero apuntando a Tempo
  - **Tiempo**: 2 horas

---

### SPRINT 3: AUTOMATIZACIÓN Y PULIDO (Semana 5-6)

**Objetivo**: Correlación con 1-2 clicks

#### Tareas P0:

- [ ] **DASH-01**: Crear dashboard unificado "Incident Investigation"
  - Input: timestamp + service + metric_name
  - Paneles:
    1. Métrica con spike marcado
    2. Logs del rango temporal filtrados
    3. Traces del rango temporal
    4. Alertas activas del servicio
  - **Tiempo**: 1 día

- [ ] **ALERT-01**: Añadir enlaces de contexto en annotations de alertas
  ```yaml
  annotations:
    summary: "High CPU usage"
    grafana_url: "http://grafana:3000/d/incident?var-timestamp={{$value}}&var-instance={{$labels.instance}}"
    loki_url: "http://grafana:3000/explore?datasource=loki&range={{$value}}"
  ```
  - **Tiempo**: 3 horas

#### Tareas P1:

- [ ] **DOC-01**: Crear runbooks en Grafana
  - Por cada alerta P0, crear página de runbook con:
    - Causa probable
    - Pasos de investigación
    - Enlaces directos a dashboards/logs/traces
  - **Tiempo**: 2 días

---

## 📊 MÉTRICAS DE ÉXITO

Al completar los 3 sprints, deberás poder:

### Test de Correlación End-to-End:

```
ESCENARIO: Se detecta anomalía de http_latency_p95

1. ✅ IA detecta anomalía
   - Visible en GET /api/anomalies
   - Severity: CRITICAL
   - Deviation: +150%

2. ✅ Alerta se dispara
   - "HighHttpLatencyP95" en estado FIRING
   - Anotaciones con enlaces a contexto

3. ✅ Dashboard muestra spike
   - Panel de latencia P95 con línea subiendo
   - Timestamp correlaciona con anomalía

4. ✅ Logs muestran requests lentos
   - Query en Loki: {service="console-backend"} | json | latency_ms > 1000
   - Filtrado por timestamp de anomalía ± 5 min
   - Logs muestran endpoints afectados

5. ✅ Traces muestran bottleneck
   - Traza en Tempo del request más lento
   - Span breakdown muestra que el 90% del tiempo está en consulta DB
   - Atributos: http.route=/api/users, db.statement=SELECT * FROM users...

6. ✅ Root cause identificado
   - La consulta SELECT * FROM users está haciendo full table scan
   - No hay índice en columna filtrada
   - Acción: Crear índice en users.created_at

TIEMPO TOTAL DE INVESTIGACIÓN: 2-3 minutos
```

**Hoy sin correlación:** 15-30 minutos buscando manualmente

---

## 🎯 RESUMEN EJECUTIVO PARA DEMOS

### ¿Cómo se correlaciona una falla en Rhinometric HOY?

**Ejemplo: Spike de Latencia P95**

**1. Detección (FUNCIONAL)**
- La IA de anomalías detecta desviación estadística en la métrica
- Se muestra en la UI de Console en página "AI Anomalies"
- Severidad, timestamp, valor esperado vs actual

**2. Verificación en Dashboard (MANUAL)**
- Usuario debe ir manualmente a Grafana
- Buscar el dashboard correcto (System Monitoring o AI Anomaly)
- Verificar visualmente el spike en el rango de tiempo

**3. Alertas (LIMITADO)**
- Si hay regla configurada, se dispara alerta
- Visible en página "Alerts" de Console
- ⚠️ **PERO**: Solo 6 de 16 señales tienen alertas configuradas

**4. Investigación en Logs (MANUAL + LIMITADO)**
- Usuario va a página "Logs" o Grafana → Explore → Loki
- Filtra manualmente por timestamp ± 5 min
- Filtra por servicio/contenedor
- ⚠️ **LIMITACIÓN**: Logs no tienen campos estructurados
  - No hay `latency_ms`, `status_code`, `endpoint`
  - Solo texto crudo sin parsing
  - Difícil encontrar la causa raíz

**5. Investigación en Traces (NO FUNCIONAL)**
- ❌ Ningún servicio real está instrumentado
- ❌ No se pueden ver traces de requests lentos
- ❌ No se puede identificar el bottleneck

### Limitaciones Conocidas

**1. Métricas HTTP No Existen (CRÍTICO)**
- La UI muestra métricas de aplicación (`http_latency_p95`, `http_error_rate`) que **NO EXISTEN**
- Ningún backend está instrumentado con Prometheus client
- Paneles de AI Anomaly vacíos o con NaN

**2. PostgreSQL Sin Observabilidad (CRÍTICO)**
- Base de datos crítica sin métricas
- Sin monitoreo de conexiones, queries, locks
- postgres-exporter no instalado

**3. Correlación Manual (IMPORTANTE)**
- No hay botones "View Logs" / "View Traces" desde Anomalías
- Usuario debe navegar manualmente entre herramientas
- Debe recordar timestamp y filtrar manualmente

**4. Logs Sin Estructura (CRÍTICO)**
- Promtail captura logs pero no los parsea
- No hay campos de correlación (trace_id, request_id)
- Búsqueda de causa raíz es "grep" en texto plano

**5. Zero Distributed Tracing (IMPORTANTE)**
- Tempo corriendo pero vacío (solo demo traces)
- No se pueden rastrear requests end-to-end
- No se identifican bottlenecks de latencia

### Roadmap de Correlación

**Próximos 30 días (Sprint 1-2):**

1. **Semanas 1-2**: Paridad Básica
   - Instrumentar backend con métricas HTTP reales
   - Desplegar postgres-exporter
   - Completar alertas faltantes para señales P0
   - Desactivar métricas fantasma en IA

2. **Semanas 3-4**: Correlación Logs/Traces
   - Logging estructurado en todos los servicios
   - Añadir trace_id y request_id
   - Instrumentar con OpenTelemetry (3 servicios)
   - Configurar Promtail para parsear JSON

**En 60 días (Sprint 3):**

3. **Semanas 5-6**: Automatización
   - Dashboard unificado de investigación de incidentes
   - Botones directos desde Anomalías a Logs/Traces
   - Alertas con enlaces de contexto automáticos
   - Runbooks en Grafana

### Discurso de Demo (Versión Honesta)

**Lo que funciona HOY:**
- "Rhinometric v2.5.0 detecta anomalías en métricas de infraestructura (CPU, memoria, disco) usando ML"
- "Las alertas se disparan cuando hay umbrales críticos en servidores"
- "Los dashboards muestran visualmente el estado del stack"
- "Los logs se centralizan en Loki para búsqueda temporal"

**Lo que está en progreso:**
- "Estamos completando la instrumentación de métricas de aplicación (HTTP latency, error rate)"
- "La correlación automática entre anomalías → logs → traces está en desarrollo"
- "Actualmente la investigación requiere navegación manual entre herramientas"

**La visión (2 meses):**
- "El objetivo es que cuando la IA detecte una anomalía de latencia, con 1 click veas los logs exactos del período afectado"
- "Y con otro click, el trace distribuido que muestra qué microservicio o query causó el problema"
- "Reduciendo el tiempo de investigación de incidentes de 30 minutos a 2-3 minutos"

---

## 📌 CONCLUSIONES CRÍTICAS

### ✅ Lo que SÍ funciona bien:

1. **Observabilidad de Infraestructura**
   - CPU, memoria, disco, network del host
   - Contenedores via cAdvisor
   - Alertas básicas configuradas

2. **Motor de IA**
   - Algoritmos funcionando (isolation forest, LOF, statistical)
   - Detección de anomalías operativa
   - API expuesta en puerto 8085

3. **Stack Core**
   - Prometheus, Grafana, Loki, Tempo desplegados
   - Dashboards existentes
   - Alertmanager configurado

### ❌ Lo que NO funciona:

1. **Métricas de Aplicación**
   - HTTP latency/error/request rate NO EXISTEN
   - Console-backend sin instrumentación
   - Dashboards de IA muestran vacío

2. **Observabilidad de BD**
   - PostgreSQL sin postgres-exporter
   - Métricas de DB inexistentes

3. **Correlación**
   - Logs sin estructura
   - Traces inexistentes en servicios reales
   - Navegación manual entre herramientas

4. **Alertas Incompletas**
   - Solo 6 de 16 señales críticas tienen alertas
   - HTTP metrics sin alertas (porque no existen)

### 🎯 Prioridad Absoluta (Esta Semana):

1. Instrumentar console-backend con métricas HTTP
2. Desplegar postgres-exporter
3. Desactivar métricas fantasma en config.yaml de IA
4. Crear alertas HTTP

**Tiempo Total Estimado:** 8-10 horas de trabajo

---

**Fin del Informe de Auditoría**

Generado: 2026-01-17  
Próxima revisión: Después de Sprint 1 (2 semanas)
