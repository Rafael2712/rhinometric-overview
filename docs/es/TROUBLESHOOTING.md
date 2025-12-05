# 🔧 Rhinometric - Troubleshooting Guide

**Versión:** 2.5.1  
**Fecha:** Diciembre 2025  
**Propósito:** Resolver problemas comunes de operación

---

## 📋 Índice de Problemas

### **Console y UI**
1. [Console no carga (página en blanco)](#1-console-no-carga-página-en-blanco)
2. [API Error en Home](#2-api-error-en-home)
3. [KPIs muestran 0 o valores incorrectos](#3-kpis-muestran-0-o-valores-incorrectos)
4. [Gráficos históricos vacíos](#4-gráficos-históricos-vacíos)
5. [Dashboards no cargan](#5-dashboards-no-cargan)

### **Logs**
6. [Logs no aparecen en Console](#6-logs-no-aparecen-en-console)
7. [Loki muestra error "too many outstanding requests"](#7-loki-muestra-error-too-many-outstanding-requests)
8. [Promtail no envía logs](#8-promtail-no-envía-logs)

### **Traces**
9. [Jaeger vacío (sin traces)](#9-jaeger-vacío-sin-traces)
10. [Traces incompletas](#10-traces-incompletas)

### **AI Anomalies**
11. [Demasiadas anomalías (falsos positivos)](#11-demasiadas-anomalías-falsos-positivos)
12. [AI Engine caído](#12-ai-engine-caído)
13. [Sin anomalías detectadas (esperadas)](#13-sin-anomalías-detectadas-esperadas)

### **Alerts**
14. [Alertas no disparan](#14-alertas-no-disparan)
15. [Alert fatigue (spam de alertas)](#15-alert-fatigue-spam-de-alertas)
16. [Alertmanager no envía notificaciones](#16-alertmanager-no-envía-notificaciones)

### **Prometheus y Métricas**
17. [Prometheus no scrapea targets](#17-prometheus-no-scrapea-targets)
18. [Targets en estado DOWN](#18-targets-en-estado-down)
19. [Métricas faltantes](#19-métricas-faltantes)

### **Servicios Core**
20. [PostgreSQL no arranca](#20-postgresql-no-arranca)
21. [Redis caído](#21-redis-caído)
22. [Contenedores en restart loop](#22-contenedores-en-restart-loop)

### **Performance**
23. [Rhinometric consume mucha RAM](#23-rhinometric-consume-mucha-ram)
24. [Disco lleno](#24-disco-lleno)
25. [Lentitud general](#25-lentitud-general)

---

## 🖥️ Console y UI

### **1. Console no carga (página en blanco)**

**Síntomas:**
- Browser muestra página blanca
- `http://localhost:3002` no responde
- Console no muestra errores en DevTools

**Diagnóstico:**

```bash
# 1. Verificar frontend está corriendo
docker ps | grep console-frontend

# 2. Ver logs
docker logs rhinometric-console-frontend --tail 50

# 3. Probar acceso directo
curl http://localhost:3002
```

**Causas comunes:**

| **Error en logs** | **Causa** | **Solución** |
|-------------------|-----------|--------------|
| `ECONNREFUSED ::1:3001` | Backend caído | `docker restart rhinometric-console-backend` |
| `Cannot find module` | Build corrupto | `docker-compose up -d --build rhinometric-console-frontend` |
| `Permission denied` | Volumen con permisos incorrectos | `sudo chown -R 1000:1000 volumes/console` |

**Solución rápida:**

```bash
# Reiniciar frontend y backend
docker restart rhinometric-console-frontend rhinometric-console-backend

# Esperar 30 segundos y probar
curl http://localhost:3002
```

---

### **2. API Error en Home**

**Síntomas:**
- Home muestra "Failed to fetch KPIs"
- Console carga pero datos no aparecen
- DevTools muestra error 500 o 503

**Diagnóstico:**

```bash
# 1. Ver logs de backend
docker logs rhinometric-console-backend --tail 100

# 2. Verificar backend responde
curl http://localhost:3001/api/health

# 3. Verificar Prometheus accesible desde backend
docker exec -it rhinometric-console-backend curl http://prometheus:9090/-/healthy
```

**Causas comunes:**

1. **Prometheus caído:**
   ```bash
   docker ps | grep prometheus
   docker restart rhinometric-prometheus
   ```

2. **Network entre containers rota:**
   ```bash
   docker network inspect rhinometric-net
   docker-compose down
   docker-compose up -d
   ```

3. **Backend con cache corrupto:**
   ```bash
   docker restart rhinometric-console-backend
   ```

**Solución rápida:**

```bash
# Reiniciar toda la cadena
docker restart rhinometric-prometheus rhinometric-console-backend rhinometric-console-frontend
```

---

### **3. KPIs muestran 0 o valores incorrectos**

**Síntomas:**
- Service Status = 0%
- Monitored Services = 0/0
- Active Anomalies = 0 (cuando debería haber)

**Diagnóstico:**

```bash
# 1. Verificar Prometheus tiene datos
curl 'http://localhost:9090/api/v1/query?query=up'

# 2. Ver query exacta que falla
docker logs rhinometric-console-backend | grep "KPI"
```

**Causas comunes:**

1. **Prometheus sin targets configurados:**
   - Abrir `http://localhost:9090/targets`
   - Si lista vacía → editar `config/prometheus.yml`

2. **Queries incorrectas en backend:**
   - Ver logs: `docker logs rhinometric-console-backend`
   - Buscar errores de query Prometheus

3. **Time range incorrecto:**
   - Backend consulta últimas 24h
   - Si Prometheus instalado hace <24h → datos parciales son normales

**Solución:**

```bash
# Verificar targets en Prometheus
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health}'

# Si targets vacíos, agregar en config/prometheus.yml
docker-compose restart rhinometric-prometheus
```

---

### **4. Gráficos históricos vacíos**

**Síntomas:**
- Home → Gráficos de 24h no muestran líneas
- Ejes aparecen pero sin datos

**Diagnóstico:**

```bash
# 1. Query manual histórica
curl -G http://localhost:9090/api/v1/query_range \
  --data-urlencode 'query=up' \
  --data-urlencode 'start='$(date -d '24 hours ago' +%s) \
  --data-urlencode 'end='$(date +%s) \
  --data-urlencode 'step=3600'

# 2. Ver logs de backend
docker logs rhinometric-console-backend | grep "Historical"
```

**Causas comunes:**

1. **Prometheus instalado hace <24h:**
   - Normal: solo habrá datos desde instalación
   - Solución: Esperar a acumular histórico

2. **Retention de Prometheus muy baja:**
   - Editar `.env` → `PROMETHEUS_RETENTION=15d`
   - `docker-compose up -d --force-recreate rhinometric-prometheus`

3. **Query range incorrecto:**
   - Ver logs backend: `docker logs rhinometric-console-backend`
   - Buscar error en query_range

**Solución:**

```bash
# Verificar retención actual
docker exec -it rhinometric-prometheus cat /etc/prometheus/prometheus.yml | grep retention

# Ajustar si es necesario
echo "PROMETHEUS_RETENTION=15d" >> .env
docker-compose up -d --force-recreate rhinometric-prometheus
```

---

### **5. Dashboards no cargan**

**Síntomas:**
- Console → Dashboards → iframe vacío
- Error "Failed to load dashboard"

**Diagnóstico:**

```bash
# 1. Verificar Grafana corriendo
docker ps | grep grafana

# 2. Acceder directamente
curl http://localhost:3000/api/health

# 3. Ver logs
docker logs rhinometric-grafana --tail 50
```

**Causas comunes:**

1. **Grafana caído:**
   ```bash
   docker restart rhinometric-grafana
   ```

2. **Dashboards no importados:**
   ```bash
   # Verificar dashboards en Grafana
   curl http://localhost:3000/api/search?query=&type=dash-db

   # Si lista vacía, reimportar
   docker-compose down
   docker-compose up -d
   ```

3. **CORS bloqueado por navegador:**
   - Abrir DevTools → Console
   - Buscar error "Cross-Origin"
   - Solución: Agregar en `config/grafana/grafana.ini`:
     ```ini
     [security]
     allow_embedding = true
     ```

**Solución rápida:**

```bash
docker restart rhinometric-grafana
# Esperar 30 segundos
curl http://localhost:3000/api/search?query=Rhinometric
```

---

## 📜 Logs

### **6. Logs no aparecen en Console**

**Síntomas:**
- Console → Logs → tabla vacía
- Filtros no retornan resultados

**Diagnóstico:**

```bash
# 1. Verificar Loki corriendo
docker ps | grep loki

# 2. Query manual a Loki
curl -G http://localhost:3100/loki/api/v1/query --data-urlencode 'query={job="varlogs"}' | jq

# 3. Verificar Promtail enviando logs
docker logs rhinometric-promtail --tail 50
```

**Causas comunes:**

1. **Loki caído:**
   ```bash
   docker restart rhinometric-loki
   ```

2. **Promtail no configurado:**
   ```bash
   # Verificar config
   docker exec -it rhinometric-promtail cat /etc/promtail/promtail.yaml

   # Debe tener:
   # clients:
   #   - url: http://loki:3100/loki/api/v1/push
   ```

3. **Logs en directorio no monitoreado:**
   - Promtail solo lee `/var/log` y logs de Docker
   - Para agregar path custom: editar `config/promtail.yaml`

**Solución:**

```bash
# Reiniciar cadena completa
docker restart rhinometric-promtail rhinometric-loki

# Esperar 30 segundos y probar query
curl -G http://localhost:3100/loki/api/v1/query --data-urlencode 'query={job="varlogs"}' --data-urlencode 'limit=5'
```

---

### **7. Loki muestra error "too many outstanding requests"**

**Síntomas:**
- Console → Logs → error HTTP 429
- Logs de Loki: `too many outstanding requests`

**Causa:**
- Rate limiting de Loki alcanzado (límite de 500 consultas/seg por defecto)

**Solución:**

```bash
# Editar config/loki-config.yml
limits_config:
  max_query_parallelism: 32  # Aumentar de 16 a 32
  max_outstanding_per_tenant: 2048  # Aumentar de 500 a 2048

# Reiniciar Loki
docker-compose up -d --force-recreate rhinometric-loki
```

---

### **8. Promtail no envía logs**

**Síntomas:**
- Loki vacío (query retorna `[]`)
- Logs de Promtail: `connection refused` o `timeout`

**Diagnóstico:**

```bash
# 1. Ver logs de Promtail
docker logs rhinometric-promtail --tail 100

# 2. Verificar conectividad a Loki
docker exec -it rhinometric-promtail curl http://loki:3100/ready
```

**Causas comunes:**

1. **Loki no accesible:**
   ```bash
   docker network inspect rhinometric-net | grep loki
   docker restart rhinometric-loki
   ```

2. **Configuración incorrecta:**
   ```bash
   # Verificar URL en config
   docker exec -it rhinometric-promtail cat /etc/promtail/promtail.yaml | grep url

   # Debe ser: http://loki:3100/loki/api/v1/push
   ```

**Solución:**

```bash
# Reiniciar ambos
docker restart rhinometric-loki rhinometric-promtail

# Verificar logs de Promtail tras 1 minuto
docker logs rhinometric-promtail --tail 20 | grep "POST /loki/api/v1/push"
```

---

## 🔍 Traces

### **9. Jaeger vacío (sin traces)**

**Síntomas:**
- Jaeger UI (`http://localhost:16686`) sin servicios en dropdown
- "No traces found"

**Causa:**
- **Servicios NO instrumentados con OpenTelemetry**

**Solución:**

1. **Verificar si servicio exporta traces:**
   ```bash
   # Ejemplo con servicio Python
   docker logs <NOMBRE_SERVICIO> | grep -i "trace\|opentelemetry"
   ```

2. **Instrumentar servicio (ejemplo Python):**
   ```python
   # Instalar dependencias
   pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

   # Código
   from opentelemetry import trace
   from opentelemetry.sdk.trace import TracerProvider
   from opentelemetry.sdk.trace.export import BatchSpanProcessor
   from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

   trace.set_tracer_provider(TracerProvider())
   otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
   trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
   ```

3. **Reiniciar servicio:**
   ```bash
   docker restart <NOMBRE_SERVICIO>
   ```

**Verificación:**

```bash
# Tras 5 minutos, verificar en Jaeger
curl http://localhost:16686/api/services
# Debe retornar lista con nombre de servicio
```

---

### **10. Traces incompletas**

**Síntomas:**
- Traces aparecen pero faltan spans
- Trace muestra solo 1-2 operaciones (debería tener más)

**Causas:**

1. **Servicios intermedios no instrumentados:**
   - Ejemplo: Frontend → API Gateway → Backend
   - Si API Gateway no propaga context → trace se corta

2. **Sampling muy agresivo:**
   - OpenTelemetry descarta traces aleatoriamente
   - Ajustar sampling ratio: `tracer = trace.get_tracer(__name__, sampler=AlwaysOnSampler())`

**Solución:**

- Instrumentar TODOS los servicios en cadena
- Verificar propagación de headers (`traceparent`, `tracestate`)

---

## 🤖 AI Anomalies

### **11. Demasiadas anomalías (falsos positivos)**

**Síntomas:**
- Console → AI Anomalies → >50 anomalías activas
- Muchas con severity "Low" o "Medium"

**Causa:**
- Umbral de desviación muy sensible

**Solución:**

```bash
# Editar config/ai-anomaly-config.yml
anomaly_detection:
  deviation_threshold: 30  # Aumentar de 20 a 30 (%)
  severity_thresholds:
    low: 30
    medium: 50
    high: 80
    critical: 120

# Reiniciar AI Engine
docker restart rhinometric-ai-anomaly
```

**Alternativa:** Excluir métricas ruidosas

```yaml
# config/ai-anomaly-config.yml
excluded_metrics:
  - node_network_transmit_bytes_total  # Muy ruidosa
  - node_disk_io_time_seconds_total    # Picos normales
```

---

### **12. AI Engine caído**

**Síntomas:**
- Home → AI Anomaly Engine = DOWN
- Sin anomalías nuevas (tabla vacía)

**Diagnóstico:**

```bash
# 1. Verificar container
docker ps -a | grep ai-anomaly

# 2. Ver logs
docker logs rhinometric-ai-anomaly --tail 100

# 3. Ver errores
docker logs rhinometric-ai-anomaly 2>&1 | grep -i "error\|exception"
```

**Causas comunes:**

| **Error en logs** | **Causa** | **Solución** |
|-------------------|-----------|--------------|
| `ModuleNotFoundError` | Dependencias faltantes | `docker-compose up -d --build rhinometric-ai-anomaly` |
| `Connection refused` (Prometheus) | Prometheus caído | `docker restart rhinometric-prometheus` |
| `OOM killed` | Sin RAM | Aumentar límite en `docker-compose.yml` |

**Solución rápida:**

```bash
docker restart rhinometric-ai-anomaly

# Esperar 2 minutos
docker logs rhinometric-ai-anomaly --tail 20
```

---

### **13. Sin anomalías detectadas (esperadas)**

**Síntomas:**
- Console → AI Anomalies → tabla vacía
- Sabes que hay comportamiento anómalo (ej: CPU al 100%)

**Causas:**

1. **Baseline aún no calculado:**
   - AI Engine necesita 7 días de histórico
   - Si instalación reciente → esperar

2. **Umbral muy alto:**
   - Reducir `deviation_threshold` en config

3. **Métrica no monitoreada:**
   - Verificar en Prometheus: `curl 'http://localhost:9090/api/v1/query?query=<METRIC_NAME>'`

**Solución:**

```bash
# Reducir umbral temporalmente
# Editar config/ai-anomaly-config.yml
deviation_threshold: 10  # Reducir de 20 a 10

docker restart rhinometric-ai-anomaly
```

---

## 🚨 Alerts

### **14. Alertas no disparan**

**Síntomas:**
- Console → Alerts → tabla vacía
- Prometheus muestra targets DOWN pero sin alertas

**Diagnóstico:**

```bash
# 1. Verificar reglas cargadas en Prometheus
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {alert, state}'

# 2. Ver estado de alertas
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alertname, state}'
```

**Causas comunes:**

1. **Reglas no cargadas:**
   ```bash
   # Verificar archivo existe
   ls -lh config/rules/alerts.yml

   # Verificar sintaxis
   docker exec -it rhinometric-prometheus promtool check rules /etc/prometheus/rules/alerts.yml
   ```

2. **Expresión incorrecta:**
   ```yaml
   # Ejemplo de regla que NUNCA dispara (mal)
   - alert: RedisDown
     expr: up{job="redis"} > 0  # INCORRECTO (debería ser == 0)
   ```

3. **Periodo `for` muy largo:**
   ```yaml
   # Alerta que requiere 1 hora para disparar
   - alert: HighCPU
     expr: node_cpu_usage > 80
     for: 1h  # Demasiado tiempo
   ```

**Solución:**

```bash
# Reload reglas sin reiniciar Prometheus
curl -X POST http://localhost:9090/-/reload

# Verificar reglas activas
curl http://localhost:9090/api/v1/rules
```

---

### **15. Alert fatigue (spam de alertas)**

**Síntomas:**
- Console → Alerts → >20 alertas activas
- Alertas duplicadas o ruidosas

**Solución:**

1. **Agregar periodo `for`:**
   ```yaml
   - alert: RedisDown
     expr: up{job="redis"} == 0
     for: 2m  # Esperar 2 minutos antes de alertar
   ```

2. **Silenciar temporalmente en Alertmanager:**
   - Abrir `http://localhost:9093`
   - Click en alerta → "Silence"
   - Duración: 1h, 24h, etc.

3. **Agrupar alertas:**
   ```yaml
   # config/alertmanager.yml
   route:
     group_by: ['alertname', 'cluster']
     group_wait: 30s
     group_interval: 5m
   ```

---

### **16. Alertmanager no envía notificaciones**

**Síntomas:**
- Alertas aparecen en Console
- NO llegan a Slack/Email

**Causa:**
- **Versión v2.5.1 NO tiene integración Slack/Email configurada por defecto**

**Solución temporal:**

```yaml
# Editar config/alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

route:
  receiver: 'slack'
```

```bash
docker restart rhinometric-alertmanager
```

---

## 📊 Prometheus y Métricas

### **17. Prometheus no scrapea targets**

**Síntomas:**
- `http://localhost:9090/targets` → lista vacía
- Console Home → Monitored Services = 0/0

**Diagnóstico:**

```bash
# 1. Ver config de Prometheus
docker exec -it rhinometric-prometheus cat /etc/prometheus/prometheus.yml

# 2. Verificar sintaxis
docker exec -it rhinometric-prometheus promtool check config /etc/prometheus/prometheus.yml
```

**Causas comunes:**

1. **Config vacío o mal indentado:**
   ```yaml
   # INCORRECTO (mal indentado)
   scrape_configs:
   - job_name: 'prometheus'
   static_configs:
     - targets: ['localhost:9090']  # Falta indentación
   ```

2. **Archivo no montado:**
   ```bash
   # Verificar volumen
   docker inspect rhinometric-prometheus | grep -A 5 "Mounts"
   ```

**Solución:**

```bash
# Corregir config/prometheus.yml
# Reiniciar Prometheus
docker restart rhinometric-prometheus

# Verificar targets tras 30 segundos
curl http://localhost:9090/api/v1/targets
```

---

### **18. Targets en estado DOWN**

**Síntomas:**
- `http://localhost:9090/targets` → algunos targets rojos

**Diagnóstico:**

```bash
# Ver detalles del target
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="down")'
```

**Causas comunes:**

| **Target** | **Causa** | **Solución** |
|------------|-----------|--------------|
| `prometheus:9090` | Prometheus no puede scrapear a sí mismo | Verificar puerto 9090 abierto |
| `node-exporter:9100` | Node Exporter caído | `docker restart node-exporter` |
| `postgres-exporter:9187` | PostgreSQL caído o credenciales mal | Verificar `.env` → `POSTGRES_USER/PASSWORD` |

**Solución rápida:**

```bash
# Reiniciar target problemático
docker restart <NOMBRE_CONTAINER>

# Verificar en Prometheus tras 1 minuto
curl http://localhost:9090/api/v1/targets
```

---

### **19. Métricas faltantes**

**Síntomas:**
- Query en Prometheus retorna vacío
- Dashboard muestra "No Data"

**Diagnóstico:**

```bash
# 1. Verificar métrica existe
curl -G http://localhost:9090/api/v1/label/__name__/values | jq '.data[] | select(. | contains("node_cpu"))'

# 2. Query con time range
curl -G http://localhost:9090/api/v1/query --data-urlencode 'query=node_cpu_seconds_total'
```

**Causas:**

1. **Exporter no instalado:**
   - Métrica `container_*` → requiere cAdvisor
   - Métrica `pg_*` → requiere Postgres Exporter

2. **Retention expiró:**
   - Métrica existió pero se borró (retention 15 días por defecto)

**Solución:**

```bash
# Instalar exporter faltante (ejemplo cAdvisor)
# Ya debería estar en docker-compose.yml
docker-compose up -d cadvisor

# Verificar métrica tras 1 minuto
curl -G http://localhost:9090/api/v1/query --data-urlencode 'query=container_cpu_usage_seconds_total'
```

---

## 🛢️ Servicios Core

### **20. PostgreSQL no arranca**

**Síntomas:**
- Console backend: `connection refused` PostgreSQL
- `docker ps -a` → rhinometric-postgres en estado `Exited`

**Diagnóstico:**

```bash
# Ver logs
docker logs rhinometric-postgres --tail 100

# Errores comunes
docker logs rhinometric-postgres 2>&1 | grep -i "fatal\|error"
```

**Causas:**

| **Error** | **Causa** | **Solución** |
|-----------|-----------|--------------|
| `data directory not empty` | Volumen corrupto | Borrar volumen: `docker volume rm rhinometric_postgres_data` |
| `role "rhinometric" does not exist` | DB no inicializada | Forzar recreación: `docker-compose up -d --force-recreate rhinometric-postgres` |
| `permission denied` | Permisos volumen mal | `sudo chown -R 999:999 volumes/postgres` |

**Solución rápida:**

```bash
# Reiniciar PostgreSQL
docker restart rhinometric-postgres

# Si persiste, recrear con volumen nuevo
docker-compose down
docker volume rm rhinometric_postgres_data
docker-compose up -d rhinometric-postgres
```

---

### **21. Redis caído**

**Síntomas:**
- Console backend: `connection refused` Redis
- Alerta `RedisDown` activa

**Diagnóstico:**

```bash
# Ver estado
docker ps -a | grep redis

# Ver logs
docker logs rhinometric-redis --tail 50
```

**Solución:**

```bash
# Reiniciar
docker restart rhinometric-redis

# Verificar
docker exec -it rhinometric-redis redis-cli ping
# Debe retornar: PONG
```

---

### **22. Contenedores en restart loop**

**Síntomas:**
- `docker ps` → container con "Restarting (1) X seconds ago"
- Container no se mantiene UP

**Diagnóstico:**

```bash
# Ver logs completos
docker logs <CONTAINER_NAME> --tail 200

# Ver exit code
docker inspect <CONTAINER_NAME> | grep ExitCode
```

**Causas:**

- **Exit code 137:** OOM Killed (sin RAM)
- **Exit code 1:** Error de aplicación
- **Exit code 139:** Segmentation fault

**Solución:**

```bash
# Si OOM (código 137), aumentar límite
# Editar docker-compose.yml
services:
  <SERVICIO>:
    mem_limit: 2g  # Aumentar de 1g a 2g

docker-compose up -d --force-recreate <SERVICIO>
```

---

## ⚡ Performance

### **23. Rhinometric consume mucha RAM**

**Síntomas:**
- Host con RAM >80% usada
- Containers siendo OOM killed

**Diagnóstico:**

```bash
# Ver consumo por container
docker stats --no-stream

# Identificar culpable
docker stats --no-stream | sort -k 4 -h
```

**Soluciones:**

1. **Reducir retención:**
   ```bash
   # Editar .env
   PROMETHEUS_RETENTION=7d  # Reducir de 15d a 7d
   LOKI_RETENTION=3d       # Reducir de 7d a 3d

   docker-compose up -d --force-recreate rhinometric-prometheus rhinometric-loki
   ```

2. **Limitar RAM por container:**
   ```yaml
   # docker-compose.yml
   services:
     prometheus:
       mem_limit: 2g
     loki:
       mem_limit: 1g
   ```

---

### **24. Disco lleno**

**Síntomas:**
- `df -h` → 95%+ usado
- Containers fallan con "no space left on device"

**Diagnóstico:**

```bash
# Ver uso de volúmenes Docker
docker system df

# Ver tamaño por volumen
docker volume ls -q | xargs -I {} sh -c 'echo -n "{} "; docker volume inspect {} | grep Mountpoint | cut -d '"' -f 4 | xargs du -sh'
```

**Soluciones:**

1. **Limpiar logs de Docker:**
   ```bash
   docker system prune -a --volumes -f
   ```

2. **Reducir retención Prometheus:**
   ```bash
   # Ver espacio usado
   du -sh volumes/prometheus

   # Reducir retención a 7 días
   echo "PROMETHEUS_RETENTION=7d" >> .env
   docker-compose up -d --force-recreate rhinometric-prometheus
   ```

3. **Configurar log rotation:**
   ```bash
   # Editar /etc/docker/daemon.json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }

   sudo systemctl restart docker
   ```

---

### **25. Lentitud general**

**Síntomas:**
- Console tarda >10 segundos en cargar
- Queries a Prometheus lentas

**Diagnóstico:**

```bash
# Ver carga del host
uptime

# Ver I/O de disco
iostat -x 1 5

# Ver procesos pesados
top -o %CPU
```

**Soluciones:**

1. **Reducir scrape interval:**
   ```yaml
   # config/prometheus.yml
   global:
     scrape_interval: 30s  # Aumentar de 15s a 30s
   ```

2. **Limitar cardinality:**
   - Revisar métricas con alta cardinality
   - Ejemplo: `node_network_transmit_bytes_total` con muchas interfaces
   - Solución: Excluir métricas innecesarias en `prometheus.yml`

3. **Usar SSD en vez de HDD:**
   - Prometheus/Loki son I/O intensivos
   - SSD mejora performance 5-10x

---

## 🆘 Soporte

Si problema persiste:

1. **Recopilar información:**
   ```bash
   # Logs de todos los containers
   docker-compose logs > rhinometric-logs.txt

   # Estado de containers
   docker ps -a > docker-ps.txt

   # Uso de recursos
   docker stats --no-stream > docker-stats.txt
   ```

2. **Enviar a soporte:**
   - Email: soporte@rhinometric.com
   - Asunto: `[Troubleshooting] <BREVE_DESCRIPCIÓN>`
   - Adjuntar: `rhinometric-logs.txt`, `docker-ps.txt`, `docker-stats.txt`

---

**© 2025 Rhinometric - Troubleshooting Guide Completo**
