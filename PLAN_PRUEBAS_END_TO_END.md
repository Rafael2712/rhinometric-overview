# 🧪 PLAN DE PRUEBAS END-TO-END - RHINOMETRIC v2.5.0

**Fecha:** 2025-12-05  
**Propósito:** Validación funcional completa antes de pasar a License Module  
**Metodología:** "Cliente gruñón" - verificar TODO funciona sin mentiras

---

## 📋 CHECKLIST DE PRUEBAS

| **Módulo** | **Pruebas** | **Status** | **Evidencia** |
|-----------|-------------|------------|---------------|
| **Home** | 4 tests | ⏳ Pendiente | - |
| **AI Anomalies** | 3 tests | ⏳ Pendiente | - |
| **Alerts** | 3 tests | ⏳ Pendiente | - |
| **Logs** | 2 tests | ⏳ Pendiente | - |
| **Traces** | 2 tests | ⏳ Pendiente | - |
| **Dashboards** | 2 tests | ⏳ Pendiente | - |
| **Coherencia** | 1 test | ⏳ Pendiente | - |

**TOTAL:** 17 pruebas funcionales

---

## 🏠 MÓDULO 1: HOME

### **Test 1.1: Verificar "Monitored Services" cuadra con Prometheus**

**Objetivo:** Confirmar que el número mostrado coincide con servicios reales.

**Pasos:**
1. Abrir Console: http://localhost:3002
2. Ver card "Monitored Services" → debe mostrar **4**
3. Ver texto debajo → debe decir "Client services (Total: 12 incl. platform)"
4. Abrir Prometheus: http://localhost:9090
5. Query: `up{rhinometric_scope="demo"}`
6. Contar resultados → debe ser **4**
7. Query: `up`
8. Contar resultados → debe ser **12**

**Criterio de Éxito:**
- ✅ Console muestra 4 servicios DEMO
- ✅ Console menciona 12 totales
- ✅ Prometheus confirma 4 con label demo
- ✅ Prometheus confirma 12 totales
- ✅ NO hay texto "In Development"

**Comandos de Verificación:**
```bash
# Verificar servicios DEMO
curl "http://localhost:9090/api/v1/query?query=up{rhinometric_scope=\"demo\"}" | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object -ExpandProperty result | Measure-Object

# Verificar servicios TOTALES
curl "http://localhost:9090/api/v1/query?query=up" | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object -ExpandProperty result | Measure-Object
```

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 1.2: Gráficos históricos cambian coherentemente**

**Objetivo:** Confirmar que los gráficos NO usan random.randint() y reflejan datos reales.

**Pasos:**
1. Abrir Console Home
2. Ver gráfico "Active Anomalies" (sparkline)
3. Anotar valores actuales
4. **FORZAR ANOMALÍA:**
   ```bash
   # Generar carga CPU para forzar anomalía
   docker exec rhinometric-console-backend sh -c "dd if=/dev/zero of=/dev/null & sleep 60; kill %1"
   ```
5. Esperar 10 minutos (ciclo de detección AI)
6. Recargar Console Home
7. Ver si gráfico cambió

**Criterio de Éxito:**
- ✅ Gráfico NO cambia aleatoriamente al recargar (sin forzar anomalía)
- ✅ Gráfico SÍ cambia después de forzar anomalía
- ✅ Cambio es coherente con AI Anomaly module

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 1.3: Badge "Backend API: Connected"**

**Objetivo:** Confirmar que ya NO dice "In Development".

**Pasos:**
1. Abrir Console Home
2. Scroll down hasta "Real-time Metrics Integration"
3. Ver badges

**Criterio de Éxito:**
- ✅ Badge verde: "✓ Backend API: Connected"
- ✅ Badge verde: "✓ Frontend: Ready"
- ❌ NO debe decir "In Development"

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 1.4: Service Status coherente**

**Objetivo:** Verificar que "Service Status" refleja uptime real.

**Pasos:**
1. Ver card "Service Status" en Home
2. Anotar valor (ej: "Operational" o "Degraded")
3. Anotar porcentaje (ej: "95.2% Uptime")
4. Ir a Prometheus
5. Query: `up`
6. Contar cuántos tienen value=1 vs value=0

**Criterio de Éxito:**
- ✅ Si todos up=1 → debe decir "Operational"
- ✅ Si alguno up=0 → debe decir "Degraded"
- ✅ Porcentaje cuadra con (up_count/total_count)*100

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

## 🤖 MÓDULO 2: AI ANOMALIES

### **Test 2.1: Forzar anomalía y verificar detección**

**Objetivo:** Confirmar que AI detecta anomalías REALES.

**Pasos:**
1. Ir a Console → AI Anomalies
2. Ver tabla actual (anotar cantidad)
3. **FORZAR ANOMALÍA (Opción A - CPU spike):**
   ```bash
   docker exec rhinometric-console-backend sh -c "stress-ng --cpu 4 --timeout 120s"
   ```
4. **FORZAR ANOMALÍA (Opción B - Matar servicio temporalmente):**
   ```bash
   docker stop rhinometric-redis
   sleep 30
   docker start rhinometric-redis
   ```
5. Esperar 10-15 minutos (ciclo de detección)
6. Recargar página AI Anomalies
7. Ver si apareció nueva anomalía

**Criterio de Éxito:**
- ✅ Anomalía aparece en tabla
- ✅ Timestamp es reciente
- ✅ Métrica afectada es correcta (node_cpu_usage o up)
- ✅ Severity asignado (low/medium/high)

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 2.2: Métricas del detalle cuadran con Grafana**

**Objetivo:** Verificar coherencia entre Console y Grafana.

**Pasos:**
1. En AI Anomalies, click en una anomalía
2. Ver detalles:
   - Current Value
   - Expected Value
   - Anomaly Score
3. Ir a Grafana Dashboard "04-rhinometric-overview"
4. Buscar la misma métrica en el mismo timestamp
5. Comparar valores

**Criterio de Éxito:**
- ✅ Current Value coincide con valor en Grafana ±5%
- ✅ Timestamp es el mismo
- ✅ Métrica es la correcta

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 2.3: Notificaciones NO spam**

**Objetivo:** Confirmar que alertas AI no generan spam.

**Pasos:**
1. Ir a Settings
2. Habilitar "AI Anomaly Alerting" (toggle ON)
3. Esperar 1 hora
4. Revisar Alertmanager: http://localhost:9093
5. Contar alertas de tipo "AnomalyDetected"

**Criterio de Éxito:**
- ✅ Si hay anomalías reales → 1 alerta por anomalía (no duplicados)
- ✅ Si NO hay anomalías → 0 alertas
- ❌ NO debe haber 40+ alertas duplicadas

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

## 🚨 MÓDULO 3: ALERTS

### **Test 3.1: Tirar servicio y verificar alerta**

**Objetivo:** Confirmar que Alertmanager detecta servicios down.

**Pasos:**
1. Ver estado actual en Console → Alerts (debe estar vacío o con pocas alertas)
2. **TIRAR SERVICIO NO CRÍTICO:**
   ```bash
   docker stop rhinometric-redis
   ```
3. Esperar 2-3 minutos (for: 2m en alert rule)
4. Ir a Alertmanager: http://localhost:9093
5. Buscar alerta "RedisDown" o "DatabaseDown"
6. Ir a Console → Alerts
7. Ver si aparece la misma alerta
8. **RESTAURAR SERVICIO:**
   ```bash
   docker start rhinometric-redis
   ```

**Criterio de Éxito:**
- ✅ Alerta aparece en Alertmanager después de 2-3 min
- ✅ Alerta aparece en Console Alerts
- ✅ Detalles coinciden (nombre, severity, timestamp)
- ✅ Alerta desaparece al restaurar servicio

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 3.2: Alerta JaegerDown funciona (NO TempoDown)**

**Objetivo:** Confirmar que corregimos la alerta Tempo→Jaeger.

**Pasos:**
1. Ver config: `config/rules/alerts.yml`
2. Buscar "JaegerDown" (debe existir)
3. Buscar "TempoDown" (NO debe existir)
4. **TIRAR JAEGER:**
   ```bash
   docker stop rhinometric-jaeger
   ```
5. Esperar 2-3 minutos
6. Ver Alertmanager
7. Buscar alerta "JaegerDown"
8. **RESTAURAR:**
   ```bash
   docker start rhinometric-jaeger
   ```

**Criterio de Éxito:**
- ✅ Alerta "JaegerDown" existe en config
- ✅ Alerta "TempoDown" NO existe
- ✅ Alerta se dispara al tirar Jaeger
- ✅ Query es: `up{job="jaeger"} == 0`

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 3.3: Coherencia Console vs Alertmanager**

**Objetivo:** Verificar que Console muestra LAS MISMAS alertas que Alertmanager.

**Pasos:**
1. Ir a Alertmanager: http://localhost:9093
2. Contar alertas activas (firing)
3. Ir a Console → Alerts
4. Contar alertas en tabla
5. Comparar nombres y timestamps

**Criterio de Éxito:**
- ✅ Misma cantidad de alertas
- ✅ Mismos nombres
- ✅ Mismos timestamps ±1min

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

## 📝 MÓDULO 4: LOGS

### **Test 4.1: Generar log reconocible y buscarlo**

**Objetivo:** Confirmar que logs llegan a Loki y se pueden buscar.

**Pasos:**
1. **GENERAR LOG ÚNICO:**
   ```bash
   docker exec rhinometric-console-backend python -c "print('TEST-RHINO-LOG-12345-UNIQUE')"
   ```
2. Esperar 30 segundos (Promtail shipping)
3. Ir a Grafana: http://localhost:3000
4. Explore → Loki
5. Query: `{container_name="rhinometric-console-backend"} |= "TEST-RHINO-LOG-12345"`
6. Ver si aparece
7. Ir a Console → Logs
8. Buscar "TEST-RHINO-LOG-12345"

**Criterio de Éxito:**
- ✅ Log aparece en Grafana Loki
- ✅ Log aparece en Console Logs module
- ✅ Timestamp es correcto (últimos 5 min)
- ✅ Container name es correcto

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 4.2: Filtros funcionan correctamente**

**Objetivo:** Verificar que filtros por container/severity funcionan.

**Pasos:**
1. Ir a Console → Logs
2. Aplicar filtro: Container = "rhinometric-ai-anomaly"
3. Ver que SOLO aparecen logs de ese container
4. Cambiar filtro: Level = "ERROR"
5. Ver que solo aparecen logs de error

**Criterio de Éxito:**
- ✅ Filtro por container funciona
- ✅ Filtro por level funciona
- ✅ Resultados cuadran con Grafana

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

## 🔍 MÓDULO 5: TRACES

### **Test 5.1: Generar trace y verla en Jaeger**

**Objetivo:** Confirmar que traces llegan a Jaeger.

**Pasos:**
1. **GENERAR REQUEST con trace:**
   ```bash
   curl http://localhost:8105/api/kpis -H "traceparent: 00-12345678901234567890123456789012-1234567890123456-01"
   ```
2. Esperar 10 segundos
3. Ir a Jaeger UI: http://localhost:16686
4. Service: "rhinometric-console-backend"
5. Buscar traces recientes
6. Ver si aparece

**Criterio de Éxito:**
- ✅ Trace aparece en Jaeger
- ✅ Spans son correctos (request → query prometheus → response)
- ✅ Latencia es razonable (<500ms)

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 5.2: Console Traces muestra Jaeger**

**Objetivo:** Verificar que módulo Traces funciona.

**Pasos:**
1. Ir a Console → Traces
2. Ver si carga interfaz
3. Ver si muestra traces recientes

**Criterio de Éxito:**
- ✅ Página carga sin errores
- ✅ Muestra traces (si hay)
- ✅ Coincide con Jaeger UI

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

## 📊 MÓDULO 6: DASHBOARDS

### **Test 6.1: Dashboards se abren sin errores**

**Objetivo:** Confirmar que los 8 dashboards funcionan.

**Pasos:**
1. Ir a Console → Dashboards
2. Click en cada dashboard:
   - 01 Logs Explorer
   - 02 Applications APIs
   - 03 GitHub Webhooks
   - 04 Rhinometric Overview
   - 05 Docker Containers
   - 06 System Monitoring
   - 07 License Status
   - 08 Stack Health
3. Verificar que:
   - Se abre en Grafana
   - Paneles cargan datos
   - NO hay errores "Plugin not found"

**Criterio de Éxito:**
- ✅ 8/8 dashboards abren correctamente
- ✅ Paneles muestran datos reales
- ✅ NO hay plugins rotos
- ✅ NO hay paneles con "No data" (excepto métricas que no existen)

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

### **Test 6.2: Dashboards reflejan datos reales**

**Objetivo:** Verificar coherencia entre dashboards y Prometheus.

**Pasos:**
1. Abrir Dashboard "04-rhinometric-overview"
2. Ver panel "Node CPU Usage"
3. Anotar valor actual (ej: 45%)
4. Ir a Prometheus
5. Query: `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
6. Comparar valores

**Criterio de Éxito:**
- ✅ Valores coinciden ±5%
- ✅ Gráficos tienen forma similar
- ✅ NO hay datos aleatorios

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

## 🔄 TEST 7: COHERENCIA GLOBAL

### **Test 7.1: TODO cuadra entre sistemas**

**Objetivo:** Verificación final de que NO hay contradicciones.

**Escenario:**
1. Tirar servicio Redis
2. Esperar 3 minutos
3. Verificar que TODOS estos sistemas muestran lo mismo:
   - Prometheus: `up{job="redis"} == 0`
   - Alertmanager: Alerta "RedisDown" activa
   - Console Home: Service Status = "Degraded"
   - Console Alerts: Alerta visible
   - Grafana Dashboard: Panel Redis = Down
   - Logs: ERROR logs de conexión a Redis

**Criterio de Éxito:**
- ✅ TODOS los sistemas coinciden
- ✅ Timestamps son coherentes (±2min)
- ✅ NO hay sistema mostrando Redis UP cuando está DOWN

**Status:** ⏳ Pendiente  
**Evidencia:** -

---

## 📋 CHECKLIST DE TEXTO "IN DEVELOPMENT"

Verificar que NO aparece en:

| **Ubicación** | **Estado** | **Texto Correcto** |
|---------------|------------|-------------------|
| Home - Badge Backend API | ⏳ Pendiente | "✓ Backend API: Connected" |
| Settings - Additional Settings | ⏳ Pendiente | "Additional Settings: In Development" (OK - es placeholder) |
| Dashboard Builder | ⏳ Pendiente | NO debe existir aún (roadmap) |
| Integrations Module | ⏳ Pendiente | NO debe existir aún (roadmap) |

---

## 🎯 CRITERIOS DE ÉXITO GLOBAL

Para considerar la plataforma **PRODUCTION READY**:

### ✅ **OBLIGATORIOS (Bloqueantes):**
1. ✅ Todos los servicios HEALTHY (excepto cloudflare - no crítico)
2. ✅ Console NO muestra datos fake/random
3. ✅ Coherencia entre Prometheus/Grafana/Console
4. ✅ Alertas funcionan (se disparan y resuelven)
5. ✅ AI Anomalies detecta eventos REALES
6. ✅ Logs llegan a Loki y son buscables
7. ✅ Traces llegan a Jaeger
8. ✅ Dashboards funcionan sin errores

### ⚠️ **DESEABLES (No bloqueantes):**
1. ⚠️ Notificaciones AI no hacen spam
2. ⚠️ Todos los healthchecks pasan en <30s
3. ⚠️ Performance aceptable (dashboards cargan <3s)

### 📌 **PENDIENTES ACEPTABLES (Roadmap):**
1. 📌 Dashboard Builder (próximamente)
2. 📌 Integrations UI (próximamente)
3. 📌 Reportes automáticos (próximamente)
4. 📌 RBAC avanzado (próximamente)

---

## 🚀 PRÓXIMOS PASOS

**Una vez completadas estas pruebas:**

1. ✅ Marcar cada test como PASSED/FAILED
2. ✅ Documentar evidencias (screenshots, logs)
3. ✅ Corregir SOLO los FAILED críticos
4. ✅ Pasar a módulo License

**¿LISTO PARA EMPEZAR LAS PRUEBAS?**

Avísame y ejecuto cada test uno por uno, documentando resultados en tiempo real.

---

**Generado:** 2025-12-05  
**Status:** Plan creado - Esperando inicio de pruebas
