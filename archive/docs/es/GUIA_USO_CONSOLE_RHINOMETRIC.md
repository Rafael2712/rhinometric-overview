# 📱 Rhinometric Console - Guía de Uso

**Versión:** 2.5.1  
**Fecha:** Diciembre 2025  
**Audiencia:** Usuarios finales (DevOps, SRE, Observability Engineers)

---

## 🔐 1. Login y Configuración Inicial

### **Acceso a la Console**

1. Abrir navegador: `http://<IP_HOST>:3002`
2. Pantalla de login:
   - **Usuario:** `admin` (por defecto)
   - **Contraseña:** `admin` (por defecto)
3. Click en **"Login"**

### **Cambio de Contraseña Obligatorio (Primer Login)**

En el primer acceso, el sistema solicita cambio de contraseña:

- **Nueva contraseña:** Mínimo 8 caracteres, debe incluir:
  - Mayúsculas y minúsculas
  - Números
  - Símbolos (@, #, $, etc.)
- Click en **"Cambiar contraseña"**

### **Interfaz Principal**

Tras login exitoso, verás:
- **Sidebar izquierdo:** Menú de navegación
- **Header superior:** Usuario actual + botón logout
- **Área central:** Contenido de cada sección

---

## 🏠 2. Home (Dashboard Ejecutivo)

**URL:** `http://<IP_HOST>:3002/`

### **2.1. KPIs en Tiempo Real** (Parte superior)

#### **Service Status**
- **Indicador:** `●` Verde (Operational) / Rojo (Degraded) / Gris (Unknown)
- **Significado:**
  - **Operational:** Todos los servicios críticos UP
  - **Degraded:** 1+ servicios caídos
  - **Unknown:** No se puede determinar estado
- **Cálculo:** `100 * (servicios UP / total servicios)`

#### **Monitored Services**
- **Formato:** `11/13` (servicios UP / total servicios)
- **Qué cuenta como servicio:**
  - Prometheus, Grafana, Loki, Jaeger, Alertmanager
  - PostgreSQL, Redis
  - Console Backend, AI Anomaly Engine
  - Node Exporter, Postgres Exporter, etc.
- **Color:**
  - Verde: Todos UP
  - Amarillo: 1-2 servicios DOWN
  - Rojo: 3+ servicios DOWN

#### **Active Anomalies**
- **Número:** Anomalías activas detectadas por IA
- **Fuente:** AI Anomaly Engine (modelos ML)
- **Severidad:** Click para ver detalles en página "AI Anomalies"
- **Rango normal:** 0-15 (depende de la infraestructura)
- **⚠️ Atención:** >20 anomalías = revisar urgentemente

#### **Alerts (24h)**
- **Número:** Alertas activas en últimas 24 horas
- **Fuente:** Alertmanager
- **Tipos:** Warning (amarillo) / Critical (rojo)
- **Rango normal:** 0-5
- **⚠️ Atención:** >10 alertas = posible incidente o alert fatigue

### **2.2. Gráficos Históricos** (24 horas)

Debajo de los KPIs, 4 mini gráficos de línea:

#### **Service Uptime (%)**
- **Eje Y:** Porcentaje (0-100%)
- **Eje X:** Últimas 24 horas (1 punto por hora = 24 puntos)
- **Interpretación:**
  - **100%:** Todo perfecto
  - **95-99%:** Normal (algunos reinicios)
  - **<90%:** Problema grave

#### **Monitored Hosts**
- **Eje Y:** Número de hosts monitorizados
- **Interpretación:**
  - Línea plana: Infraestructura estable
  - Caídas: Hosts desconectados o exporters caídos
  - Subidas: Nuevos hosts agregados

#### **Anomalies Detected**
- **Eje Y:** Número de anomalías por hora
- **Interpretación:**
  - Picos: Momentos de comportamiento anómalo
  - Línea baja (0-5): Normal
  - Línea alta (>10): Revisar patrones

#### **Alerts Fired**
- **Eje Y:** Número de alertas disparadas por hora
- **Interpretación:**
  - 0: Sin problemas
  - Picos aislados: Incidente puntual
  - Picos continuos: Problema sistémico

**⚠️ IMPORTANTE:** Estos gráficos NO se actualizan automáticamente. Refrescar (F5) para ver datos recientes.

---

## 📊 3. Dashboards (Grafana Integrado)

**URL:** `http://<IP_HOST>:3002/dashboards`

### **3.1. Lista de Dashboards Disponibles**

La Console muestra 8 dashboards embebidos de Grafana:

1. **01 - Logs Explorer**
   - **Función:** Búsqueda y filtrado de logs en tiempo real
   - **Uso:** Investigar errores, warnings, eventos específicos

2. **02 - Applications & APIs**
   - **Función:** Métricas de aplicaciones custom
   - **Uso:** Monitorizar APIs propias, webhooks, microservicios

3. **03 - GitHub Webhooks**
   - **Función:** Logs de webhook-collector (si está configurado)
   - **Uso:** Debugging de integraciones GitHub

4. **04 - Rhinometric Overview**
   - **Función:** Vista global del stack de observabilidad
   - **Métricas:** CPU, RAM, red de Prometheus, Loki, Grafana, Jaeger

5. **05 - Docker Containers**
   - **Función:** Métricas de todos los contenedores (vía cAdvisor)
   - **Métricas:** CPU, RAM, red, disco por contenedor

6. **06 - System Monitoring**
   - **Función:** Métricas del host físico (vía node-exporter)
   - **Métricas:** CPU total, RAM total, disco, red, procesos

7. **07 - License Status**
   - **Función:** Estado de licencias (Coming Soon en v2.5.1)
   - **Estado actual:** Placeholder

8. **08 - Stack Health**
   - **Función:** Salud del stack completo (Prometheus + Loki)
   - **Métricas:** Uptime, errores, latencias

### **3.2. Cómo Usar un Dashboard**

1. Click en dashboard deseado
2. Se abre en iframe embebido (dentro de Console)
3. **Limitaciones actuales:**
   - No se puede editar desde Console
   - Para editar: Click en "Open in Grafana" → editar en Grafana nativo
4. **Interacción:**
   - Zoom: Click y arrastrar en gráfico
   - Time range: Selector superior derecho
   - Variables: Dropdowns en parte superior (si existen)

### **3.3. Abrir en Grafana Nativo**

Si necesitas funcionalidad avanzada:
1. Click en **"Open in Grafana"** (botón superior derecho)
2. Se abre en nueva pestaña: `http://<IP_HOST>:3000`
3. Login con credenciales de Grafana (admin/admin por defecto)

---

## 🤖 4. AI Anomalies (Detección Inteligente)

**URL:** `http://<IP_HOST>:3002/anomalies`

### **4.1. Tabla de Anomalías**

Columnas de la tabla:

#### **Metric Name**
- **Formato:** `node_cpu_usage`, `node_memory_usage`, etc.
- **Significado:** Métrica monitorizadaque presentó comportamiento anómalo

#### **Current Value**
- **Formato:** Número decimal (ej: `87.5`)
- **Unidad:** Depende de la métrica
  - CPU: % (0-100)
  - RAM: GB
  - Red: MB/s

#### **Baseline**
- **Formato:** Número decimal (ej: `45.2`)
- **Significado:** Valor "normal" esperado según histórico
- **Cálculo:** Media de misma hora en días anteriores

#### **Deviation**
- **Formato:** Porcentaje (ej: `+93.5%`)
- **Significado:** Qué tan lejos está el valor actual del baseline
- **Fórmula:** `((current - baseline) / baseline) * 100`

#### **Severity**
- **Valores:**
  - 🟢 **Low:** deviation < 20%
  - 🟡 **Medium:** 20% ≤ deviation < 50%
  - 🟠 **High:** 50% ≤ deviation < 100%
  - 🔴 **Critical:** deviation ≥ 100%

#### **Timestamp**
- **Formato:** `2025-12-05 14:30:00`
- **Significado:** Cuándo se detectó la anomalía

### **4.2. Cómo Investigar una Anomalía**

**Ejemplo:** Anomalía en `node_cpu_usage` con deviation +95% (Critical)

1. **Ver contexto temporal:**
   - ¿Hay otras anomalías en el mismo momento?
   - ¿Hay alertas correlacionadas?

2. **Ir a Logs:**
   - Click en botón **"View Logs"** (próxima versión)
   - O manualmente: Dashboards → Logs Explorer
   - Filtrar por timestamp cercano a la anomalía
   - Buscar errores: `{container_name=~".*"} |= "error"`

3. **Ir a Traces:**
   - Click en botón **"View Traces"** (próxima versión)
   - O manualmente: Abrir Jaeger (`http://<IP_HOST>:16686`)
   - Buscar traces en mismo timestamp
   - Ver si hay latencias anómalas

4. **Revisar Dashboards:**
   - System Monitoring → ver CPU/RAM/Red en detalle
   - Docker Containers → identificar contenedor problemático

5. **Correlacionar con despliegues:**
   - ¿Se hizo deploy reciente?
   - ¿Se cambió configuración?

### **4.3. Limitaciones Actuales**

- ❌ No hay botón "Acknowledge" o "Dismiss" (próxima versión)
- ❌ No se pueden crear reglas custom de IA desde UI
- ❌ Anomalías históricas no se guardan >24h
- ✅ Anomalías son REALES (no inventadas por IA)

---

## 🚨 5. Alerts (Gestión de Alertas)

**URL:** `http://<IP_HOST>:3002/alerts`

### **5.1. Tabla de Alertas Activas**

Columnas:

#### **Alert Name**
- Ejemplos: `RedisDown`, `PrometheusDown`, `APIHighErrorRate`
- Definidas en: `config/rules/alerts.yml`

#### **Severity**
- **warning:** Amarillo (requiere atención, no urgente)
- **critical:** Rojo (requiere acción inmediata)

#### **Status**
- **firing:** Alerta activa
- **resolved:** Alerta resuelta (desaparece de la tabla)

#### **Labels**
- Metadatos adicionales (ej: `job=redis`, `instance=rhinometric-redis:6379`)

#### **Annotations**
- **summary:** Descripción corta
- **description:** Detalles completos + acciones recomendadas

#### **Started At**
- Timestamp de cuándo se disparó

### **5.2. Diferencia entre Anomalías y Alertas**

| **Criterio** | **Anomalías (AI)** | **Alertas (Rules)** |
|--------------|-------------------|---------------------|
| **Origen** | Machine Learning | Reglas manuales en YAML |
| **Detección** | Automática (desviación estadística) | Condición booleana (`up == 0`) |
| **Falsos positivos** | Posibles (IA puede confundirse) | Raros (si regla bien definida) |
| **Uso** | Investigación proactiva | Reacción reactiva |
| **Ejemplo** | CPU 20% más alto que baseline | Redis caído completamente |

### **5.3. Cómo Investigar una Alerta**

**Ejemplo:** Alerta `RedisDown` (critical)

1. **Ver descripción:**
   - Annotations → description: "Redis ha estado caído por más de 2 minutos"

2. **Verificar servicio:**
   ```bash
   docker ps | grep redis
   docker logs rhinometric-redis --tail 50
   ```

3. **Reiniciar si es necesario:**
   ```bash
   docker restart rhinometric-redis
   ```

4. **Verificar en Prometheus:**
   - `http://<IP_HOST>:9090`
   - Query: `up{job="redis"}`
   - Si retorna 1 → resuelto

5. **Esperar resolución:**
   - Alerta desaparece automáticamente cuando `up{job="redis"} == 1`

### **5.4. Configurar Notificaciones (Coming Soon)**

En versión actual (v2.5.1):
- ❌ No hay integración Slack/Email desde UI
- ⚠️ Configuración manual en `config/alertmanager.yml`

En próxima versión:
- ✅ UI para configurar webhooks
- ✅ Templates de Slack, Email, PagerDuty

---

## 📜 6. Logs (Búsqueda Centralizada)

**URL:** `http://<IP_HOST>:3002/logs`

### **6.1. Filtros Disponibles**

#### **Service / Container**
- Dropdown con todos los contenedores monitorizados
- Ejemplos: `rhinometric-console-backend`, `prometheus`, `loki`

#### **Log Level**
- error, warn, info, debug
- Filtrado por patrón en texto del log

#### **Time Range**
- Last 5 minutes
- Last 15 minutes
- Last 1 hour
- Last 6 hours
- Last 24 hours
- Custom (date picker)

### **6.2. Resultados**

Cada línea de log muestra:
- **Timestamp:** `2025-12-05 14:35:12`
- **Container:** `rhinometric-ai-anomaly`
- **Log Level:** 🔴 ERROR / 🟡 WARN / 🔵 INFO
- **Message:** Texto completo del log

### **6.3. Limitaciones Actuales**

- ❌ No hay botón "Tail" (streaming en tiempo real)
- ❌ No se puede exportar a CSV
- ✅ Búsqueda es rápida (indexado por Loki)

---

## 🔍 7. Traces (Trazabilidad Distribuida)

**URL:** `http://<IP_HOST>:3002/traces`

### **7.1. Qué Muestra**

- Botón **"Open Jaeger UI"** → Abre Jaeger en `http://<IP_HOST>:16686`
- Actualmente, Console solo redirige a Jaeger
- En próxima versión: Traces embebidas en Console

### **7.2. Cómo Usar Jaeger**

1. **Seleccionar servicio:**
   - Dropdown "Service": Elegir servicio instrumentado
   - Ejemplo: `rhinometric-console-backend`

2. **Buscar traces:**
   - Click en **"Find Traces"**
   - Filtra por operación, tags, duración, etc.

3. **Analizar trace:**
   - Click en trace específico
   - Ver timeline de spans (llamadas entre servicios)
   - Identificar latencias, errores, dependencias

### **7.3. Requisitos**

- ⚠️ Servicios deben estar instrumentados con OpenTelemetry
- ⚠️ Si servicio no exporta traces → no aparecerá en Jaeger

---

## ⚙️ 8. Settings (Configuración)

**URL:** `http://<IP_HOST>:3002/settings`

### **8.1. Opciones Disponibles**

#### **UI Theme**
- Light / Dark
- Se guarda en localStorage del navegador

#### **AI Alerts Enabled**
- ON: AI Engine genera alertas automáticas cuando detecta anomalías críticas
- OFF: AI solo reporta, no genera alertas
- (Coming Soon - aún no implementado)

### **8.2. Opciones "Coming Soon" (No Disponibles)**

- **Integrations:** Slack, Email, Webhook, PagerDuty
- **Reports:** Configurar reportes PDF automáticos
- **Users:** Gestión de usuarios (multi-user)
- **License:** Ver/renovar licencia (próxima versión)

---

## 🔄 9. Actualización Automática de Datos

### **Frecuencias de Refresco**

| **Pantalla** | **Auto-Refresh** | **Frecuencia** |
|--------------|-----------------|---------------|
| Home (KPIs) | ✅ Sí | 30 segundos |
| Home (Gráficos) | ❌ No | Manual (F5) |
| AI Anomalies | ✅ Sí | 30 segundos |
| Alerts | ✅ Sí | 15 segundos |
| Logs | ❌ No | Manual |
| Traces | ❌ No | Manual |

---

## 🎯 10. Workflow de Diagnóstico Típico

### **Escenario: "La aplicación está lenta"**

1. **Home:** Revisar KPIs
   - ¿Service Status = Degraded?
   - ¿Alertas activas?

2. **AI Anomalies:** Buscar anomalías recientes
   - ¿CPU/RAM/Red anómalos?
   - ¿Qué servicio tiene el problema?

3. **Dashboards:** Profundizar
   - Docker Containers → identificar contenedor con alta CPU
   - System Monitoring → ver si es problema del host

4. **Logs:** Buscar errores
   - Filtrar por contenedor problemático
   - Buscar "error", "exception", "timeout"

5. **Traces:** Ver latencias
   - Jaeger → buscar traces lentas (>1s)
   - Identificar operación problemática

6. **Acción:** Reiniciar servicio, escalar recursos, etc.

---

## 📞 Soporte

- **FAQ:** [FAQ_RHINOMETRIC.md](./FAQ_RHINOMETRIC.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Email:** soporte@rhinometric.com

---

**© 2025 Rhinometric - Guía de Uso Completa**
