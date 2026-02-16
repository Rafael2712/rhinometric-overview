# 🎯 ACCESO RÁPIDO A DASHBOARDS

**Grafana URL:** http://localhost:3000  
**Credenciales:** `admin` / `admin_trial_2024`

---

## 📊 DASHBOARDS ENTERPRISE (13)

### 1. 🔍 Tempo - Distributed Tracing
**URL:** http://localhost:3000/d/cf1m3xo0up14wd  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- RED Metrics (Rate, Errors, Duration)
- Total Traces Stored: 83,011+ trazas
- Ingestion Rate, Storage Usage
- Tabla de todas las trazas (últimas 1h)
- Trazas con errores
- Traces por servicio
- Query Duration p50/p95/p99

**CORRECCIONES:**
- ✅ Panel "Compaction Progress" → ahora usa `tempodb_compaction_blocks_total`
- ✅ Panel "Query Duration" → ahora usa `tempo_query_frontend_queue_duration_seconds`

---

### 2. 📝 Loki - Logs Analysis
**URL:** http://localhost:3000/d/af1m3xp4gl2ioe  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Log Volume by Service
- Total Log Entries (últimas 1h)
- Error Rate
- Logs recientes por servicio
- Top Error Messages
- Log Pattern Distribution

---

### 3. 🗄️ Postgres - Database Performance
**URL:** http://localhost:3000/d/af1m3xq7xhb7kd  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Database Size
- Active Connections
- Transactions per Second
- Query Duration p95/p99
- Lock Count
- Cache Hit Ratio
- Replication Lag

---

### 4. 🔴 Redis - Cache Performance
**URL:** http://localhost:3000/d/af1m3xrdw9wcgd  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Connected Clients
- Memory Usage
- Commands/sec
- Cache Hit Ratio
- Evicted Keys
- Network I/O
- Commands Over Time

---

### 5. 💻 Node Exporter - System Resources
**URL:** http://localhost:3000/d/ff1m3xsiw3wn4f  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- CPU Usage
- Memory Usage
- Disk Usage
- Network I/O
- Load Average
- Disk I/O
- System Uptime

---

### 6. 🐳 cAdvisor - Container Metrics
**URL:** http://localhost:3000/d/ff1m3xtvb51xcc  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Running Containers
- Total CPU Usage
- Total Memory Usage
- Network Traffic
- CPU Usage by Container
- Memory Usage by Container
- Disk I/O by Container

---

### 7. 📊 Prometheus - Metrics Overview
**URL:** http://localhost:3000/d/ef1m3xuz20w00a  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Total Metrics: 1,267+
- Active Targets: 10
- Scrape Duration
- Samples Ingested
- TSDB Head Chunks
- Storage Size
- Rule Evaluation Duration

---

### 8. 🌐 Nginx - Proxy Dashboard
**URL:** http://localhost:3000/d/ef1m3xw3zczy8b  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Uptime Status
- Response Time
- Probe Success
- SSL Certificate Expiry
- Response Time Over Time
- Success Rate
- HTTP Status Codes
- DNS Lookup Duration

**NOTA:** Usa métricas de Blackbox Exporter (probe_*)

---

### 9. 🔔 Alertmanager - Alerts Dashboard
**URL:** http://localhost:3000/d/cf1m3xx1tzgn4a  
**Estado:** ✅ FUNCIONANDO (CORREGIDO)  
**Contenido:**
- Grafana Alerts activas
- Alertmanager Config Size
- Integrations configuradas
- Receivers configurados
- Alerts Over Time
- Config Hash evolution
- Inhibition Rules

**CORRECCIONES:**
- ✅ Todos los paneles actualizados a usar `grafana_alerting_alertmanager_*` metrics
- ✅ Razón: Este stack usa Grafana Alerting integrado, no Alertmanager standalone

---

### 10. 📡 Promtail - Log Collection
**URL:** http://localhost:3000/d/ef1m3xy08l43kb  
**Estado:** ✅ FUNCIONANDO (CORREGIDO)  
**Contenido:**
- Docker Targets discovered
- Entries Sent rate
- Docker Parse Errors
- Bytes Sent to Loki
- Sent Entries Over Time
- Bytes Sent by job
- Docker Entries timeline

**CORRECCIONES:**
- ✅ Panel "Targets Discovered" → ahora usa `promtail_docker_target_entries_total`
- ✅ Panel "Entries Rate" → ahora usa `promtail_sent_entries_total`
- ✅ Panel "Parse Errors" → ahora usa `promtail_docker_target_parsing_errors_total`
- ✅ Razón: Promtail usa Docker service discovery, no file-based targets

---

### 11. 🔎 Blackbox Exporter - Endpoint Monitoring
**URL:** http://localhost:3000/d/ef1m3xzyppzb4f  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Probe Success Rate
- Probe Duration
- SSL Cert Expiry (días restantes)
- HTTP Status Code
- Probe Success Over Time
- Response Time por endpoint
- DNS Lookup Time
- HTTP Phases (DNS, Connect, TLS, Processing, Transfer)

---

### 12. 🏢 Full Stack - Overview
**URL:** http://localhost:3000/d/df1m3y8m3kb28a  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Vista agregada de todo el stack
- Métricas de todos los servicios
- Vista panorámica de observabilidad

---

### 13. 🎯 APM - Application Performance Monitoring
**URL:** http://localhost:3000/d/cf1m3y99r3oxsf  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Golden Signals (Latency, Traffic, Errors, Saturation)
- RED Metrics agregados
- Service dependency graph
- Error rate tracking

---

## 🎨 DASHBOARD PRINCIPAL

### 14. Rhinometric - Observability Overview
**URL:** http://localhost:3000/d/ef1m1elql2h34e  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- 🔥 Sistema Health (Prometheus UP, Loki Streams, Tempo Traces)
- 📊 Metrics Panel - Top queries desde Prometheus
- 📝 Logs Panel - Últimos logs desde Loki
- 🔍 Traces Panel - Últimas trazas desde Tempo
- 🔴 Redis Metrics (Memory, Commands, Hit Rate)
- 🗄️ Postgres Metrics (Connections, TPS, Locks)
- 🌐 Nginx/Proxy Metrics (Status, Response Time)

**Dashboard de entrada principal** - Muestra overview de todos los sistemas

---

## 🧭 NAVEGACIÓN

### 15. Navigation - Quick Access
**URL:** http://localhost:3000/d/af1m423nclq80f  
**Estado:** ✅ FUNCIONANDO  
**Contenido:**
- Enlaces directos a Explore → Metrics (Prometheus)
- Enlaces directos a Explore → Logs (Loki)
- Enlaces directos a Explore → Traces (Tempo)
- Accesos rápidos a dashboards principales

**Dashboard de navegación** - Hub central para acceso rápido

---

## 🎯 EXPLORE (Análisis Ad-Hoc)

### Metrics (Prometheus)
**URL:** http://localhost:3000/explore?orgId=1&left=%7B%22datasource%22:%22ff1lws6mz39xcc%22%7D  
Ejecutar queries PromQL directamente

### Logs (Loki)
**URL:** http://localhost:3000/explore?orgId=1&left=%7B%22datasource%22:%22df1lwsdy0ecqof%22%7D  
Ejecutar queries LogQL directamente

### Traces (Tempo)
**URL:** http://localhost:3000/explore?orgId=1&left=%7B%22datasource%22:%22cf1m5g6s0xvy8f%22%7D  
Ejecutar queries TraceQL directamente

---

## 📋 RESUMEN DE ESTADO

| Dashboard | UID | Estado | Paneles | Correcciones |
|-----------|-----|---------|---------|--------------|
| Tempo Tracing | cf1m3xo0up14wd | ✅ | 11 | 2 queries |
| Loki Logs | af1m3xp4gl2ioe | ✅ | 7 | - |
| Postgres | af1m3xq7xhb7kd | ✅ | 8 | - |
| Redis | af1m3xrdw9wcgd | ✅ | 7 | - |
| Node Exporter | ff1m3xsiw3wn4f | ✅ | 7 | - |
| cAdvisor | ff1m3xtvb51xcc | ✅ | 7 | - |
| Prometheus | ef1m3xuz20w00a | ✅ | 8 | - |
| Nginx | ef1m3xw3zczy8b | ✅ | 8 | - |
| Alertmanager | cf1m3xx1tzgn4a | ✅ | 7 | 7 queries |
| Promtail | ef1m3xy08l43kb | ✅ | 7 | 7 queries |
| Blackbox | ef1m3xzyppzb4f | ✅ | 8 | - |
| Full Stack | df1m3y8m3kb28a | ✅ | - | - |
| APM | cf1m3y99r3oxsf | ✅ | - | - |
| Overview | ef1m1elql2h34e | ✅ | 10 | - |
| Navigation | af1m423nclq80f | ✅ | 3 | - |

**TOTAL:** 15 dashboards, **TODOS FUNCIONANDO** ✅

---

## 🔧 TROUBLESHOOTING

### Si no ves datos en un dashboard:

1. **Verifica el time range** (arriba a la derecha en Grafana)
   - Por defecto: Last 6 hours
   - Cambia a "Last 1 hour" o "Last 24 hours"

2. **Verifica el refresh** (arriba a la derecha)
   - Dashboards configurados con refresh 30s

3. **Verifica datasources:**
   ```bash
   curl http://localhost:3000/api/datasources -u admin:admin_trial_2024
   ```

4. **Verifica Prometheus targets:**
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

5. **Verifica logs de servicios:**
   ```bash
   docker logs rhinometric-grafana --tail 50
   docker logs rhinometric-tempo --tail 50
   docker logs rhinometric-loki --tail 50
   ```

### Scripts de validación:

```bash
# Validar todos los dashboards y datasources
bash validate-dashboards.sh

# Ver estado detallado
cat DASHBOARDS_STATUS.md
```

---

## 🎉 ¡TODOS LOS DASHBOARDS ESTÁN FUNCIONANDO!

**Próximos pasos sugeridos:**

1. **Explora los dashboards** - Familiarízate con las vistas
2. **Personaliza queries** - Ajusta time ranges y filtros
3. **Crea alertas** - Configura notificaciones en Grafana
4. **Agrega más servicios** - Expande la observabilidad
5. **Documenta** - Anota queries útiles y casos de uso

---

**Documentación completa:** `DASHBOARDS_STATUS.md`  
**Script de validación:** `validate-dashboards.sh`
