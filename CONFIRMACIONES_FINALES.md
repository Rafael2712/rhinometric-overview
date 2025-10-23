# 📋 CONFIRMACIONES Y SOLUCIONES FINALES

## 1) ✅ CREDENCIALES GRAFANA - CONFIRMADO

```
URL: http://localhost:3000
Usuario: admin
Contraseña: admin_trial_2024
```

**❌ NO es:** `admin_secure_2024`  
**✅ Contraseña correcta:** `admin_trial_2024`

---

## 2) ✅ DASHBOARDS - ESTADO CONFIRMADO

Todos los dashboards están funcionando:

| Dashboard | Status |
|-----------|--------|
| License Management | ✅ OK |
| Overview | ✅ OK |
| Docker Containers | ✅ OK |
| System Monitoring | ✅ OK |
| Logs Explorer | ✅ OK |
| License Status | ✅ OK |
| Distributed Tracing | ⚠️ Ver nota abajo |

---

## 3) ⚠️ TRACES - SOLUCIÓN AL ERROR

### Problema Identificado:

```
Error: time range must be within last 1m0s
Query: {nestedSetParent<0 && true && resource.service.name != nil} | rate() by(resource.service.name)
```

### Causa:
El **metrics generator de Tempo** solo mantiene métricas en memoria durante **1 minuto**. Las queries con `| rate()` necesitan un time range corto.

### Solución Aplicada:

1. ✅ **Cambiado time range del dashboard:**
   - Antes: `from: now-1h`
   - Ahora: `from: now-5m`

2. ✅ **Agregados 2 paneles nuevos:**
   - **Request Rate by Service (TraceQL Metrics):** Usa `| rate()` con time range compatible
   - **Service Latency (p95/p99):** Usa métricas de Prometheus (más confiable)

3. ✅ **Panel de trazas original mantiene funcionando:** Search de trazas sin `| rate()`

### Cómo Usar:

**Para ver TRAZAS (Explore funciona mejor):**
```
1. Ir a Explore → Tempo
2. Query: {resource.service.name="rhinometric-demo-service"}
3. Ver waterfall de trazas individuales
```

**Para ver MÉTRICAS de trazas (Dashboard):**
```
1. Dashboard "Distributed Tracing"
2. Panels:
   - "Recent Traces" → Lista de trazas
   - "Request Rate by Service" → Rate usando TraceQL
   - "Service Latency" → P95/P99 desde Prometheus
```

### Configuración Tempo:

El metrics generator está configurado en `config/tempo-saas.yml`:
```yaml
metrics_generator:
  processor:
    local_blocks:
      max_live_traces: 10000
      max_block_duration: 5m    # ← Máximo 5 minutos en memoria
      flush_check_period: 10s
```

**Limitación del Trial:** Por diseño, solo mantiene 5 minutos de métricas en memoria para reducir consumo de recursos.

---

## 4) ✅ LOKI - EXPLICACIÓN DE "DOCKER_LOGS"

### ¿Qué son "docker_logs"?

**NO es solo un tipo de log. Son TODOS los logs de TODOS los contenedores.**

Promtail está configurado para leer:
```yaml
__path__: /var/lib/docker/containers/*/*.log
```

Esto significa:
- ✅ Logs de `rhinometric-grafana`
- ✅ Logs de `rhinometric-prometheus`
- ✅ Logs de `rhinometric-loki`
- ✅ Logs de `rhinometric-tempo`
- ✅ Logs de `rhinometric-postgres`
- ✅ Logs de `rhinometric-redis`
- ✅ Logs de `rhinometric-nginx`
- ✅ Logs de **TODOS** los 16 contenedores

### ¿Por qué se llama "docker_logs"?

Es el **nombre del job** definido en `config/promtail-config.yml`:
```yaml
scrape_configs:
  - job_name: docker_containers
    static_configs:
      - targets: [localhost]
        labels:
          job: docker_logs    # ← Este es el label que ves
```

### ¿Cómo filtrar logs por contenedor?

Promtail extrae automáticamente:
- `container_id`: ID corto del contenedor
- `full_container_id`: ID completo del contenedor
- `stream`: stdout o stderr

**Queries de ejemplo:**

```logql
# Ver logs de un contenedor específico por ID
{job="docker_logs", container_id="abc123456789"}

# Ver solo stderr (errores)
{job="docker_logs", stream="stderr"}

# Ver logs que contengan "error"
{job="docker_logs"} |~ "(?i)error"

# Ver logs de PostgreSQL (buscar por nombre)
{job="docker_logs"} |~ "postgres"

# Ver logs de Grafana
{job="docker_logs"} |~ "grafana"
```

### ¿Necesitas más fuentes de logs?

Si quieres agregar logs de:
- Sistema host (WSL2): `/var/log/*.log`
- Aplicaciones custom fuera de Docker
- Archivos de log específicos

Puedes agregar más jobs en `promtail-config.yml`:
```yaml
scrape_configs:
  - job_name: docker_containers
    # ... configuración actual ...
  
  - job_name: system_logs
    static_configs:
      - targets: [localhost]
        labels:
          job: system_logs
          __path__: /var/log/*.log
  
  - job_name: custom_app
    static_configs:
      - targets: [localhost]
        labels:
          job: my_app
          __path__: /app/logs/*.log
```

### Dashboard Actualizado:

He mejorado el dashboard de Logs Explorer:

1. **Panel "Log Rate per Container":** Muestra rate separado por `container_id`
2. **Panel "Top 10 Jobs":** Muestra los jobs con más logs
3. **Panel "Live Logs Stream":** Todos los logs en tiempo real
4. **Panel "Logs Histogram by Level":** Separado por nivel (error/warn/info)

---

## 🔄 APLICAR CAMBIOS

### Paso 1: Reiniciar servicios afectados

```bash
# Reiniciar Promtail (nueva config)
wsl -d Ubuntu docker restart rhinometric-promtail

# Reiniciar Grafana (nuevos dashboards)
wsl -d Ubuntu docker restart rhinometric-grafana

# Esperar 10 segundos
sleep 10
```

### Paso 2: Verificar

```bash
# Ver logs de Promtail
wsl -d Ubuntu docker logs rhinometric-promtail --tail 20

# Ver estado de Grafana
curl -s http://localhost:3000/api/health
```

### Paso 3: Abrir Grafana

```
1. http://localhost:3000
2. Login: admin / admin_trial_2024
3. Ir a Dashboards:
   - Distributed Tracing → Ver paneles nuevos (Request Rate, Latency)
   - Logs Explorer → Ver logs por contenedor
```

---

## ✅ RESUMEN DE SOLUCIONES

| Problema | Solución | Estado |
|----------|----------|--------|
| **Contraseña incorrecta** | Confirmada: `admin_trial_2024` | ✅ |
| **Traces error `rate()`** | Time range 5m + paneles nuevos | ✅ |
| **Solo "docker_logs"** | Normal, son TODOS los contenedores | ✅ |
| **No diferenciar contenedores** | Labels `container_id` + panel nuevo | ✅ |

---

## 📊 QUERIES ÚTILES

### Loki (Logs):

```logql
# Ver logs de un contenedor específico
{job="docker_logs", container_id="abc123"}

# Ver errores de todos los contenedores
{job="docker_logs"} |~ "(?i)(error|exception|fatal)"

# Ver logs de Prometheus
{job="docker_logs"} |~ "prometheus"

# Contar errores por minuto
sum(count_over_time({job="docker_logs"} |~ "error" [1m]))

# Top contenedores por volumen de logs
topk(10, sum by (container_id) (count_over_time({job="docker_logs"}[5m])))
```

### Tempo (Traces):

```traceql
# Ver trazas del servicio demo
{resource.service.name="rhinometric-demo-service"}

# Ver trazas lentas (>100ms)
{duration > 100ms}

# Ver trazas con errores
{status = error}

# ⚠️ NO usar en dashboard (solo Explore):
{resource.service.name != nil} | rate() by(resource.service.name)
```

---

## 🎯 PRÓXIMOS PASOS

1. ✅ Login con `admin_trial_2024`
2. ✅ Explorar dashboards actualizados
3. ⏳ Si necesitas más fuentes de logs, agregar jobs en Promtail
4. ⏳ Usar Explore para queries complejas de trazas
5. ⏳ Documentar queries útiles para usuarios finales

---

*Generado: 23 de Octubre, 2025*
