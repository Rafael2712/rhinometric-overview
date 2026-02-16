# Módulo de Anomalías AI y Correlación — Rhinometric v2.5.2

**Última actualización:** 16 Febrero 2026  
**Versión de referencia:** v2.5.2-alerts  
**Servidor de producción:** 89.167.22.228 (rhinometric-core-production)  
**Estado:** ✅ Producción  

---

## Índice

1. [Visión General](#1-visión-general)
2. [Flujo Funcional](#2-flujo-funcional)
3. [Integraciones Técnicas](#3-integraciones-técnicas)
4. [Cambios de UX — Unificación Feb 2026](#4-cambios-de-ux--unificación-feb-2026)
5. [Roles y Permisos](#5-roles-y-permisos)
6. [Limitaciones Actuales](#6-limitaciones-actuales)
7. [Roadmap](#7-roadmap)
8. [Changelog Reciente](#8-changelog-reciente)

---

## 1. Visión General

El módulo de **Anomalías AI y Correlación** es el componente de inteligencia analítica de Rhinometric. Permite a los operadores detectar comportamientos atípicos en la infraestructura monitoreada y realizar un análisis de causa raíz automatizado mediante correlación de métricas, logs y anomalías adyacentes.

### Componentes principales

| Componente | Archivo fuente | Descripción |
|---|---|---|
| **Anomalies** | `frontend/src/pages/Anomalies.tsx` | Tabla de anomalías detectadas por el motor AI, con modal de detalle y acciones Grafana |
| **CorrelationView** | `frontend/src/pages/CorrelationView.tsx` | Vista de correlación completa: timeline, cards de métricas/logs, y sección "Análisis Profundo" con enlaces externos |
| **Alerts** | `frontend/src/pages/Alerts.tsx` | Alertas tradicionales de Prometheus/AlertManager, con enlace a Grafana Explore |
| **Correlation Engine** | `backend/services/correlation_engine.py` | Motor de correlación Python (FastAPI) que agrega datos de VictoriaMetrics, Loki, Jaeger y AI Engine |
| **externalLinks** | `frontend/src/utils/externalLinks.ts` | Funciones para generar URLs a Grafana Explore, Loki y Jaeger |
| **grafana** | `frontend/src/utils/grafana.ts` | Funciones de integración con Grafana (dashboard, explore, autenticación) |

### Stack de observabilidad

```
┌──────────────────────────────────────────────────────┐
│            Rhinometric Console (Frontend)             │
│   Anomalies.tsx │ CorrelationView.tsx │ Alerts.tsx    │
└────────┬─────────────────┬────────────────┬──────────┘
         │                 │                │
         ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────┐
│              Console Backend (FastAPI)                    │
│ /api/correlation/correlate  │  /api/anomalies  │ /api/* │
└────────┬──────────┬─────────┬─────────┬─────────────────┘
         │          │         │         │
         ▼          ▼         ▼         ▼
   VictoriaMetrics  Loki    Jaeger   AI Engine
   :8428            :3100   :16686   :8085
   (uid: victoria   (uid:   (uid:
    metrics)        loki)   jaeger)
```

---

## 2. Flujo Funcional

### 2.1 Detección de anomalía

1. El **AI Engine** (puerto 8085) ejecuta modelos ML sobre las métricas recopiladas.
2. Cuando detecta una desviación significativa, genera un evento con:
   - `event_id` — Identificador único
   - `event_timestamp` — Marca de tiempo del evento
   - `event_type` — Tipo (`anomaly`, `metric_spike`, etc.)
   - `metadata` — Diccionario con `host`, `instance`, `metric_name`, `severity`

### 2.2 Listado de anomalías (Anomalies.tsx)

- La página `/anomalies` muestra una tabla con paginación de anomalías detectadas.
- Cada fila incluye: timestamp, tipo, severidad, host afectado, métrica, estado.
- Al pulsar una anomalía se abre un **modal de detalle** con:
  - Información del evento
  - Sección **Grafana** (solo ADMIN/OWNER) con botones:
    - **Métricas** → Abre Grafana Explore con PromQL mapeada contra VictoriaMetrics
    - **Logs** → Deshabilitado ("Próximamente")
    - **Traces** → Deshabilitado ("Próximamente")
  - Botón "Ver Correlación" → Navega a `/correlation/{id}`

### 2.3 Vista de correlación (CorrelationView.tsx)

Al pulsar "Ver Correlación", el frontend ejecuta:

```
POST /api/correlation/correlate
{
  "event_id": "<anomaly_id>",
  "event_timestamp": "<ISO timestamp>",
  "event_type": "anomaly",
  "metadata": { "host": "...", "metric_name": "...", ... }
}
```

El motor de correlación responde con datos agregados. La vista renderiza:

1. **CorrelationTimeline** — Visualización temporal de eventos (anomalía central ± 5 min)
2. **CorrelationCards** — Cards con métricas, logs y anomalías correlacionadas
3. **Análisis Profundo** (RBAC: ADMIN/OWNER) — Tres botones:
   - **Grafana Metrics** → PromQL real contra VictoriaMetrics
   - **Grafana Logs** → LogQL contra Loki
   - **Jaeger Traces** → Deshabilitado ("Próximamente")

### 2.4 Motor de correlación (backend)

**Clase:** `CorrelationEngine` en `backend/services/correlation_engine.py`

**Pipeline de correlación:**

```
correlate_event(event)
  │
  ├─ _fetch_metrics_in_window()     → VictoriaMetrics (:8428)
  │     usa _build_metric_queries() → genera PromQL por query_name
  │
  ├─ _fetch_logs_in_window()        → Loki (:3100)
  │     usa _build_log_query()      → genera LogQL
  │
  ├─ _fetch_anomalies_in_window()   → AI Engine (:8085)
  │     anomalías en misma ventana temporal
  │
  └─ Agrega resultados → JSON response
```

**Ventana temporal:** `event_timestamp ± 300 segundos` (5 minutos)

**TSDB primaria:** VictoriaMetrics (`http://victoria-metrics:8428`)  
**TSDB fallback:** Prometheus (`http://prometheus:9090`)  
**Flag:** `self.use_victoria_metrics = True` (siempre usa VM en producción)

**Query keys devueltas por `_build_metric_queries()`:**

| Clave | PromQL | Condición |
|---|---|---|
| `specific_metric` | `{metric_name}{instance=~"..."}` | Cuando `metadata.metric_name` existe |
| `cpu_usage` | `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` | Cuando NO hay metric_name |
| `memory_usage` | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100` | ídem |
| `disk_usage` | `(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100` | ídem |
| `network_receive` | `rate(node_network_receive_bytes_total[5m])` | ídem |

---

## 3. Integraciones Técnicas

### 3.1 Datasources de Grafana

Grafana accesible en `http://89.167.22.228/grafana` (reverse proxy vía nginx).

| Datasource | UID | URL interna | Uso |
|---|---|---|---|
| **VictoriaMetrics** | `victoriametrics` | `http://victoria-metrics:8428` | Métricas de infraestructura y aplicación |
| **Prometheus** | `prometheus` | `http://prometheus:9090` | Relay / reglas de alertas (NO usado para Explore) |
| **Loki** | `loki` | `http://loki:3100` | Logs centralizados |
| **Jaeger** | `jaeger` | `http://jaeger:16686` | Traces distribuidos (no instrumentados aún) |

> **Decisión crítica (Feb 2026):** Todas las URLs de Grafana Explore generadas por el frontend apuntan al datasource `victoriametrics` (UID), no a `prometheus`. El motivo es que VictoriaMetrics es la TSDB primaria que almacena y sirve las métricas; Prometheus actúa únicamente como relay y evaluador de reglas de alertas.

### 3.2 Generación de URLs — externalLinks.ts

Las funciones `getGrafanaMetricsUrl()` y `getGrafanaLogsUrl()` generan URLs para `/grafana/explore` con el formato:

```
/grafana/explore?orgId=1&left={"datasource":"victoriametrics","queries":[{"refId":"A","expr":"<PromQL>"}],"range":{"from":"<ms>","to":"<ms>"}}
```

Parámetros:
- `datasource` — UID del datasource Grafana (`victoriametrics` para métricas, `loki` para logs)
- `queries[].expr` — Expresión PromQL o LogQL
- `range.from` / `range.to` — Timestamps en milisegundos (epoch)

### 3.3 MetricMap — Traducción de query_name a PromQL

El frontend contiene un diccionario `metricMap` que traduce las claves devueltas por el backend a expresiones PromQL reales. Este mapeo existe en dos lugares:

**CorrelationView.tsx** — usado por el botón "Grafana Metrics" de Análisis Profundo:

| Clave de entrada | PromQL de salida | Origen |
|---|---|---|
| `cpu_usage` | `100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` | Backend correlation engine |
| `memory_usage` | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100` | Backend correlation engine |
| `disk_usage` | `(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100` | Backend correlation engine |
| `network_receive` | `rate(node_network_receive_bytes_total[5m])` | Backend correlation engine |
| `node_cpu_usage` | Misma PromQL que `cpu_usage` | Anomaly AI engine |
| `node_memory_usage` | Misma PromQL que `memory_usage` | Anomaly AI engine |
| `node_disk_io` | `rate(node_disk_io_time_seconds_total[5m])` | Anomaly AI engine |
| `node_network_receive` | `rate(node_network_receive_bytes_total[5m])` | Anomaly AI engine |
| `node_network_transmit` | `rate(node_network_transmit_bytes_total[5m])` | Anomaly AI engine |
| `node_disk_usage` | Misma PromQL que `disk_usage` | Anomaly AI engine |
| `rhinometric_website_*` | Métrica directa (pass-through) | Website monitor |
| `postgres_connections` | `pg_stat_database_numbackends` | Base de datos |
| `response_time_ms` | `http_request_duration_seconds` | Aplicación |
| `error_rate` | `rate(http_requests_total{status=~"5.."}[5m])` | Aplicación |
| `http_request_rate` | `sum(rate(http_requests_total[5m]))` | Aplicación |
| `http_error_rate` | `sum(rate(http_requests_total{status=~"5.."}[5m]))` | Aplicación |
| `http_latency_p95` | `histogram_quantile(0.95, ...)` | Aplicación |
| `http_latency_p99` | `histogram_quantile(0.99, ...)` | Aplicación |

**Anomalies.tsx** — usado por el botón "Métricas" del modal de anomalía (mapeo similar, subconjunto).

**Fallback:** Si una clave no existe en `metricMap`, se usa el valor original como expresión PromQL directa.

### 3.4 Jaeger (Traces) — Estado actual

Jaeger está desplegado como contenedor (`rhinometric-jaeger`, puerto 16686) y configurado como datasource en Grafana (uid: `jaeger`), pero:

- No hay instrumentación OpenTelemetry en el backend.
- No se generan traces automáticos.
- Los botones de Traces en CorrelationView y Anomalies están **deshabilitados** con tooltip "Próximamente".
- La función `getJaegerTracesUrl()` sigue existiendo en `externalLinks.ts` pero no se importa en ninguna vista.

---

## 4. Cambios de UX — Unificación Feb 2026

### 4.1 Resumen de la unificación

En Febrero 2026 se realizó una unificación completa de la experiencia de usuario entre las tres páginas principales del módulo (Alerts, Anomalies, CorrelationView). Los cambios incluyeron:

| Aspecto | Antes | Después |
|---|---|---|
| **Datasource Grafana** | `prometheus` (uid) en todas las URLs | `victoriametrics` (uid) en todas las URLs |
| **MetricMap keys** | Solo claves `node_*` (del AI engine) | Claves duales: `node_*` (AI engine) + backend keys (`cpu_usage`, etc.) |
| **Sección Grafana (Anomalies)** | Visible para todos los roles | Solo visible para ADMIN/OWNER (`isAdmin()`) |
| **Botón Métricas (Anomalies)** | Siempre habilitado | Deshabilitado cuando `metric_name` es falsy o contiene "unknown" |
| **Botón Logs (Anomalies)** | Funcional / enlace directo | Deshabilitado — "Próximamente" |
| **Botón Traces (ambas vistas)** | Enlace a Jaeger directo | Deshabilitado — "Próximamente" |
| **Responsive layout** | Inconsistente entre páginas | Grid unificado: `grid-cols-1 md:grid-cols-3` |
| **Idioma** | Mezcla inglés/español | Todo en español |
| **Dark mode** | Parcial | Consistente: backgrounds `bg-gray-800/900`, texto `text-gray-300/400` |

### 4.2 Archivos modificados

1. **`frontend/src/utils/externalLinks.ts`**
   - `getGrafanaMetricsUrl()`: datasource `'prometheus'` → `'victoriametrics'`

2. **`frontend/src/pages/CorrelationView.tsx`**
   - Añadido `CORRELATION_VIEW_BUILD` para cache-busting del bundle
   - `data-build` attribute en el contenedor principal
   - MetricMap expandido con claves duales (backend + anomaly + rhinometric + generic)
   - Botón Jaeger: siempre deshabilitado, tooltip "Próximamente"
   - Eliminada importación de `getJaegerTracesUrl`

3. **`frontend/src/pages/Anomalies.tsx`**
   - Sección Grafana envuelta en `{isAdmin() && <div>...</div>}`
   - Botón Métricas: disabled cuando no hay métrica válida
   - Datasource: `'prometheus'` → `'victoriametrics'`
   - Botones Logs y Traces: deshabilitados ("Próximamente")
   - MetricMap expandido con claves `rhinometric_website_*`

4. **`frontend/src/pages/Alerts.tsx`**
   - Datasource: `'prometheus'` → `'victoriametrics'`

### 4.3 Cache-busting

El bundle de Vite genera un hash basado en el contenido del fichero. Si un cambio es puramente de datos (strings, valores), el hash puede no cambiar, causando que los navegadores sirvan la versión cacheada.

Solución implementada:
```typescript
const CORRELATION_VIEW_BUILD = '2026-02-16T12';
// ...
<div data-build={CORRELATION_VIEW_BUILD}>
```

Esto fuerza un nuevo content hash en el bundle de producción.

---

## 5. Roles y Permisos

### 5.1 Modelo de roles

| Rol | Nivel | Descripción |
|---|---|---|
| `OWNER` | Máximo | Propietario de la instancia |
| `ADMIN` | Alto | Administrador de la plataforma |
| `OPERATOR` | Medio | Operador de monitoreo |
| `VIEWER` | Bajo | Solo lectura |

### 5.2 Funciones de autorización

```typescript
// frontend/src/utils/externalLinks.ts
export function canAccessExternalTools(userRoles: string[]): boolean {
  return userRoles.some(role =>
    ['OWNER', 'ADMIN'].includes(role.toUpperCase())
  );
}

// frontend/src/lib/auth/store.ts
isAdmin(): boolean  // true si roles incluye OWNER o ADMIN
```

### 5.3 Matriz de acceso

| Funcionalidad | OWNER | ADMIN | OPERATOR | VIEWER |
|---|---|---|---|---|
| Ver lista de anomalías | ✅ | ✅ | ✅ | ✅ |
| Ver detalle de anomalía (modal) | ✅ | ✅ | ✅ | ✅ |
| Ver correlación (timeline + cards) | ✅ | ✅ | ✅ | ✅ |
| Botones Grafana en modal Anomalías | ✅ | ✅ | ❌ | ❌ |
| Sección "Análisis Profundo" en Correlación | ✅ | ✅ | ❌ | ❌ |
| Ver alertas (Alerts) | ✅ | ✅ | ✅ | ✅ |
| Botón "View in Grafana" en Alerts | ✅ | ✅ | ✅ | ✅ |

> **Nota:** El botón de Grafana en Alerts (`Alerts.tsx`) actualmente no tiene gating RBAC. Es accesible por cualquier rol. Esto podría alinearse en una futura iteración.

---

## 6. Limitaciones Actuales

### 6.1 Funcionales

| ID | Limitación | Impacto | Prioridad |
|---|---|---|---|
| L-01 | **Jaeger Traces no instrumentados** — No hay spans generados por el backend | Botones de traces deshabilitados en toda la UI | Media |
| L-02 | **Logs deshabilitados en modal de Anomalías** — Botón de Loki en modal marcado "Próximamente" | El usuario debe usar CorrelationView para acceder a logs correlacionados | Baja |
| L-03 | **MetricMap estático** — Las traducciones de query_name a PromQL están hardcodeadas en el frontend | Nuevas métricas requieren deploy de frontend | Media |
| L-04 | **Sin Grafana RBAC en Alerts** — El botón "View in Grafana" en Alerts no verifica roles | OPERATOR y VIEWER pueden abrir Grafana desde Alerts | Baja |
| L-05 | **Grafana anonymous auth** — Grafana usa `console-viewer` con rol Viewer vía Basic Auth temporal | Seguridad parcial; previsto migrar a backend proxy en v2.7 | Media |

### 6.2 Técnicas

| ID | Limitación | Detalle |
|---|---|---|
| T-01 | **Cache-busting manual** — Se necesita actualizar `CORRELATION_VIEW_BUILD` para forzar invalidación | Workaround para hashes de Vite que no cambian |
| T-02 | **Datasource hardcodeado** — UIDs de datasource (`victoriametrics`, `loki`) están en el código fuente | Idealmente se moverían a variables de entorno |
| T-03 | **Prometheus como relay** — Prometheus sigue corriendo pero no se usa como datasource principal | Consumo de RAM innecesario; evaluar eliminación |

---

## 7. Roadmap

### Corto plazo (Sprint 3 — Q1 2026)

- [ ] **Métricas dinámicas por contexto** — El backend debe devolver PromQL relevante al tipo de anomalía (DB → postgres metrics, red → network metrics) en lugar de métricas genéricas del host.
- [ ] **Habilitar botón de Logs** en modal de Anomalías — Generar LogQL filtrada por host+nivel y abrir en Grafana Explore con datasource `loki`.
- [ ] **Mover UIDs de datasource a env vars** — `VITE_GRAFANA_METRICS_DS`, `VITE_GRAFANA_LOGS_DS`.

### Medio plazo (v2.6.x — Q2 2026)

- [ ] **Instrumentación OpenTelemetry** — Añadir spans al backend FastAPI para habilitar traces.
- [ ] **Habilitar botón de Traces** — Conectar con Jaeger/Grafana Tempo una vez instrumentado.
- [ ] **RBAC en Alerts.tsx** — Aplicar mismo gating `isAdmin()` del modal de Anomalías.
- [ ] **MetricMap dinámico** — Endpoint `/api/metric-mappings` que devuelva las traducciones al frontend.

### Largo plazo (v2.7+ — Q3-Q4 2026)

- [ ] **Backend proxy para Grafana** — Eliminar acceso anónimo/viewer; autenticar mediante token de sesión del backend.
- [ ] **Alertas desde anomalías** — Botón "Crear Alerta" que genere regla en Prometheus/AlertManager automáticamente.
- [ ] **Exportación PDF** — Generar reporte de correlación completo como PDF enviable por email.
- [ ] **Eliminación de Prometheus** — Evaluar reemplazo total por VictoriaMetrics vMAlert para reglas de alertas.

---

## 8. Changelog Reciente

### v2.5.2-alerts — 16 Febrero 2026

#### 🔧 Fixed

- **Datasource incorrecto en Grafana Explore** — Todos los enlaces de Grafana apuntaban al datasource `prometheus` (uid) en lugar de `victoriametrics`. Esto causaba que las métricas no se encontraran o mostraran datos incorrectos al abrir Grafana desde la consola.
  - Corregido en: `externalLinks.ts`, `Anomalies.tsx`, `Alerts.tsx`
  
- **MetricMap keys no coincidían con backend** — El motor de correlación devuelve claves como `cpu_usage`, `memory_usage`, `disk_usage`, `network_receive`, pero el frontend solo tenía las variantes con prefijo `node_*`. La búsqueda en el diccionario fallaba y se pasaba el string crudo (ej: "cpu_usage") como query a Grafana.
  - Corregido en: `CorrelationView.tsx`, `Anomalies.tsx`

- **Cache del navegador servía bundle obsoleto** — El hash del bundle de Vite no cambiaba entre builds cuando solo se modificaban strings literales. Los navegadores servían la versión cacheada.
  - Mitigado con: constante `CORRELATION_VIEW_BUILD` y atributo `data-build` que fuerza nuevo hash.

#### 🔒 Changed

- **Sección Grafana en modal de Anomalías** — Ahora gated por `isAdmin()` (solo ADMIN/OWNER pueden ver los botones de Grafana).
- **Botón Métricas en modal** — Se deshabilita automáticamente cuando `metric_name` es vacío o contiene "unknown".

#### 🚫 Disabled

- **Botón Jaeger Traces** — Deshabilitado en CorrelationView y Anomalies con tooltip "Próximamente" hasta que se instrumente OpenTelemetry.
- **Botón Logs en modal Anomalías** — Deshabilitado con "Próximamente" (disponible en CorrelationView).

#### 📦 Build

- **Bundle:** `index-ksGfZoKC.js` + `index-BwZnT-Vl.css`
- **Imagen Docker:** `rhinometric-console-frontend:v2.5.2-alerts`
- **Verificación post-deploy:**
  ```bash
  # Confirmar datasource correcto en bundle
  docker exec rhinometric-console-frontend \
    sh -c "grep -oE 'datasource:.{1,25}' /usr/share/nginx/html/assets/index-*.js"
  # Esperado: 3x datasource:"victoriametrics", 2x datasource:"loki", 0x datasource:"prometheus"
  ```

---

## Apéndice A: Datasources de Grafana (API)

Obtenidos via `GET /grafana/api/datasources` el 16/02/2026:

```json
[
  {
    "name": "Prometheus",
    "uid": "prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "isDefault": true
  },
  {
    "name": "VictoriaMetrics",
    "uid": "victoriametrics",
    "type": "prometheus",
    "url": "http://victoria-metrics:8428",
    "isDefault": false
  },
  {
    "name": "Loki",
    "uid": "loki",
    "type": "loki",
    "url": "http://loki:3100",
    "isDefault": false
  },
  {
    "name": "Jaeger",
    "uid": "jaeger",
    "type": "jaeger",
    "url": "http://jaeger:16686",
    "isDefault": false
  }
]
```

> **Nota:** Aunque Prometheus está configurado como `isDefault: true`, el frontend explícitamente especifica `datasource: 'victoriametrics'` en todas las URLs de Explore para métricas. Esto garantiza que las queries se ejecuten contra VictoriaMetrics independientemente del default de Grafana.

## Apéndice B: Diagrama de Componentes

```
                    ┌─────────────────────────────────┐
                    │       Usuario (Browser)          │
                    └──────┬──────────────┬────────────┘
                           │              │
                    Anomalies.tsx    CorrelationView.tsx
                           │              │
                           ▼              ▼
                    ┌──────────────────────────────────┐
                    │   grafana.ts / externalLinks.ts   │
                    │                                    │
                    │  openGrafanaExplore(url)           │
                    │  getGrafanaMetricsUrl(query,t1,t2) │
                    │  getGrafanaLogsUrl(query,t1,t2)    │
                    │  canAccessExternalTools(roles)      │
                    └──────┬──────────────┬────────────┘
                           │              │
              ┌────────────┘              └────────────┐
              ▼                                        ▼
    ┌───────────────────┐                   ┌──────────────────┐
    │  Grafana Explore   │                   │ Console Backend  │
    │  /grafana/explore  │                   │ POST /api/       │
    │                    │                   │  correlation/    │
    │  DS: victoria      │                   │  correlate       │
    │      metrics       │                   └────────┬─────────┘
    │  DS: loki          │                            │
    └───────────────────┘              ┌──────────────┼──────────────┐
                                       │              │              │
                                       ▼              ▼              ▼
                                VictoriaMetrics    Loki         AI Engine
                                  :8428           :3100          :8085
```

---

**Documento generado:** 16 Feb 2026 — Rhinometric DevOps Team  
**Clasificación:** Interno — Equipo de Desarrollo
