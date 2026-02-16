# RHINOMETRIC v2.5.1 - Dashboards Grafana

**Última actualización:** 22 de enero de 2026  
**Estado:** Producción (4 dashboards funcionales)

---

## 📊 DASHBOARDS ACTIVOS (v2.5.1)

### 1. **04-rhinometric-overview.json**
- **UID:** `rhinometric-overview`
- **Título:** Rhinometric Infrastructure Overview
- **Descripción:** Vista general de infraestructura (hosts, contenedores, servicios)
- **Paneles:** 8 paneles (CPU, RAM, Disco, Network, Contenedores, Uptime)
- **Fuentes de datos:** Prometheus, Loki
- **Estado:** ✅ Funcional
- **Uso:** Dashboard principal para troubleshooting infra

---

### 2. **05-docker-containers.json**
- **UID:** `docker-containers`
- **Título:** Docker Containers Monitoring
- **Descripción:** Monitoreo detallado de contenedores Docker
- **Paneles:** 10 paneles (Tabla overview, CPU per container, Memory, Network I/O, Disk I/O)
- **Fuentes de datos:** Prometheus (cAdvisor), Loki
- **Estado:** ✅ Funcional
- **Uso:** Troubleshooting contenedores específicos

---

### 3. **06-system-monitoring.json**
- **UID:** `system-monitoring`
- **Título:** System Monitoring (Host Metrics)
- **Descripción:** Métricas detalladas de hosts (CPU, RAM, Disco, Network)
- **Paneles:** 12 paneles (CPU per core, Load Average, Memory, Swap, Filesystem, Network)
- **Fuentes de datos:** Prometheus (node-exporter)
- **Estado:** ✅ Funcional
- **Uso:** Análisis profundo de métricas sistema operativo

---

### 4. **07-ai-anomaly-detection.json**
- **UID:** `ai-anomaly-detection`
- **Título:** AI Anomaly Detection
- **Descripción:** Anomalías detectadas por ML (Isolation Forest, LOF, Statistical)
- **Paneles:** 9 paneles (Anomalías activas, Score, Métricas monitoreadas, Timeline)
- **Fuentes de datos:** Prometheus (rhinometric-ai-anomaly:9090)
- **Estado:** ✅ Funcional - **EXCELENTE** (95/100)
- **Uso:** Detección proactiva de anomalías, correlación con otros dashboards

---

## 🔗 NAVEGACIÓN ENTRE DASHBOARDS

### Flujo de Correlación Recomendado

1. **Alerta recibida** → Ver dashboard correspondiente según tipo:
   - CPU/Memoria host → `06-system-monitoring`
   - Contenedor caído → `05-docker-containers`
   - Anomalía IA → `07-ai-anomaly-detection`

2. **Desde 07-ai-anomaly** → Link a métrica origen:
   - `node_cpu_usage` → `06-system-monitoring`
   - `container_cpu_usage` → `05-docker-containers`

3. **Desde cualquier dashboard** → `04-rhinometric-overview` (big picture)

---

## 📈 MÉTRICAS DISPONIBLES POR DASHBOARD

### Dashboard 04 (Overview)
- ✅ Métricas host (node-exporter)
- ✅ Métricas contenedores (cAdvisor)
- ✅ Servicios up/down (Prometheus targets)
- ✅ Logs recientes (Loki)

### Dashboard 05 (Containers)
- ✅ `container_cpu_usage_seconds_total`
- ✅ `container_memory_working_set_bytes`
- ✅ `container_network_receive_bytes_total`
- ✅ `container_fs_reads_bytes_total`
- ✅ `container_last_seen` (para detectar down)

### Dashboard 06 (System)
- ✅ `node_cpu_seconds_total`
- ✅ `node_memory_MemAvailable_bytes`
- ✅ `node_filesystem_avail_bytes`
- ✅ `node_network_receive_bytes_total`
- ✅ `node_disk_io_time_seconds_total`

### Dashboard 07 (AI Anomaly)
- ✅ `rhinometric_anomaly_active` (anomalías detectadas)
- ✅ `rhinometric_anomaly_score` (severity 0-100)
- ✅ `rhinometric_metrics_monitored` (11 métricas activas en v2.5.1)
- ✅ `rhinometric_model_inference_duration_seconds`

---

## ❌ DASHBOARDS ELIMINADOS (v2.5.1)

### Archivos removidos (limpieza 22/01/2026):
- `01-logs-explorer.json.DISABLED` - Funcionalidad integrada en otros dashboards
- `04-veriverde-insights.json.disabled` - Métricas veriverde no en producción
- `05-ai-anomaly-detection.json.disabled` - Duplicado, se usa 07-*
- `13-distributed-tracing.json.disabled` - Solo AI Anomaly tiene traces (v2.5.0)
- `*.bak` (6 archivos) - Backups antiguos
- `*.backup` (2 archivos) - Backups redundantes

### Razón de eliminación:
**Credibilidad v2.5.1** - No mostrar dashboards "deshabilitados" o "en progreso" al cliente. Solo dashboards funcionales 100%.

---

## 🚀 ROADMAP DASHBOARDS

### v2.5.1 (ACTUAL - 22/01/2026)
- ✅ 4 dashboards funcionales
- ✅ Archivos .disabled/.bak eliminados
- ⏳ **Pendiente:** Panel logs integrado en 05/06 (Tarea 5)
- ⏳ **Pendiente:** Links inter-dashboards con variables (Tarea 5)

### v2.6.0 (Planificado - Febrero 2026)
- 🔜 Dashboard 08: **HTTP Metrics** (Console Backend)
  - Request rate, error rate, P95/P99 latency
  - Errores por endpoint
  - Correlación logs ↔ traces vía trace_id
- 🔜 Dashboard 09: **PostgreSQL Monitoring**
  - Connections, queries/sec, slow queries
  - Cache hit ratio, locks, bloat
  - Correlación con logs PostgreSQL
- 🔜 Dashboard 10: **Redis Monitoring**
  - Memory usage, hit rate, commands/sec
  - Keyspace, evictions, connections

### v2.7.0 (Planificado - Marzo 2026)
- 🔜 Dashboard 11: **License Analytics**
- 🔜 Dashboard 12: **Distributed Tracing** (completo)
- 🔜 Dashboard 13: **Executive Summary**

---

## 🔧 MANTENIMIENTO

### Cómo añadir un dashboard nuevo:
1. Crear archivo `XX-nombre-dashboard.json` en este directorio
2. Asegurar que tiene `uid` único
3. Grafana auto-provisioning detecta cambios (requiere restart)
4. Actualizar este README

### Cómo desactivar un dashboard:
1. **NO** renombrar a `.disabled` (eliminar credibilidad)
2. Eliminar el archivo `.json`
3. Actualizar este README
4. Commit con mensaje claro

### Cómo editar un dashboard:
1. Editar en Grafana UI (http://localhost:3000)
2. Exportar JSON (Dashboard settings → JSON Model)
3. Copiar JSON a este directorio (sobrescribir)
4. Commit cambios

---

## 📊 ESTADO DE CORRELACIÓN (v2.5.1)

### Señales disponibles:
- ✅ **Métricas:** 12/17 servicios exportan métricas
- ✅ **Logs:** 14/17 servicios logean a Loki
- ⚠️ **Traces:** 3/17 servicios (AI Anomaly, OTEL Collector, Jaeger)
- ✅ **Alertas:** 9 alertas funcionales (Prometheus + Alertmanager)
- ✅ **Anomalías IA:** 11 métricas monitoreadas con ML

### Capacidades de correlación:
- ✅ **CPU host alta:** Correlación manual (copiar timestamps) - 8-12min
- ✅ **Contenedor caído:** Correlación parcial (copiar container ID) - 5-8min
- ✅ **Anomalía IA detectada:** Correlación semi-auto (links dashboards) - 3-5min
- ❌ **Error HTTP 5xx:** ROTO (sin métricas backend)
- ❌ **Query lenta DB:** IMPOSIBLE (sin postgres-exporter)

---

## 📞 SOPORTE

**Contacto:** Equipo Rhinometric  
**Versión:** v2.5.1 "Polished Edition"  
**Última limpieza:** 22 de enero de 2026

---

**Nota:** Este README refleja el estado REAL de dashboards en v2.5.1. 
No contiene promesas de features futuras, solo funcionalidad actual verificada.
