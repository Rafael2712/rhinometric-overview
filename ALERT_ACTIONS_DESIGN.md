# ALERT_ACTIONS_DESIGN.md — Rhinometric Console v2.5.2-alerts

## 1. Resumen Ejecutivo

Se implementaron dos acciones operativas sobre alertas activas en Rhinometric Console:

| Acción | Descripción | Persistencia |
|--------|------------|-------------|
| **Silence Alert** | Crea un silence en Alertmanager (API v2) por duración configurable | Alertmanager (ephemeral) |
| **Acknowledge** | Registra reconocimiento humano en PostgreSQL con auditoría | PostgreSQL (permanente) |

**Contexto**: La sesión anterior (Fase 1 Hardening) añadió `Depends(get_current_user)` a los routers `logs.py` y `traces.py`, pero el frontend no enviaba el header `Authorization: Bearer`. Esto se corrigió simultáneamente.

---

## 2. Problema Resuelto

### 2.1 Regresión /api/logs y /api/traces (Fase 1)

**Causa raíz**: Los endpoints del backend ahora requieren JWT, pero las páginas `Logs.tsx` y `Traces.tsx` no incluían el header de autorización en sus `fetch()`.

**Corrección**:
- `Logs.tsx`: Añadido `{ headers: { Authorization: \`Bearer ${token}\` } }` al fetch de `/api/logs`
- `Traces.tsx`: Añadido header a **ambos** fetch: `/api/traces/services` y `/api/traces?...`

### 2.2 Botones Silence/Acknowledge inexistentes

**Antes**: La página de alertas solo mostraba una tabla read-only sin acciones.

**Después**: Cada alerta tiene botones "Silence" y "Acknowledge" funcionales.

---

## 3. Arquitectura

```
┌─────────────────────────┐
│   Frontend (React)      │
│   Alerts.tsx             │
│   - handleSilence()     │──POST /api/alerts/{fp}/silence──┐
│   - handleAcknowledge() │──POST /api/alerts/{fp}/ack──┐   │
│   - useQuery polls      │                             │   │
└─────────┬───────────────┘                             │   │
          │ GET /api/alerts                             │   │
          │ GET /api/alerts/ack-status                  │   │
          │ GET /api/alerts/silences                    │   │
          ▼                                             ▼   ▼
┌─────────────────────────┐       ┌──────────────────────────┐
│   Backend (FastAPI)     │       │  routers/alerts.py       │
│   main.py               │       │  6 endpoints             │
│   JWT auth on all       │       │  httpx → Alertmanager    │
│   routes                │       │  SQLAlchemy → PostgreSQL │
└─────────┬───────────────┘       └──────────┬───────────────┘
          │                                  │
          ▼                                  ▼
┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐
│ Alertmanager│  │  PostgreSQL  │  │  Loki / Jaeger      │
│ :9093       │  │  :5432       │  │  (logs / traces)    │
│ silences API│  │  alert_ack   │  │                     │
└─────────────┘  └──────────────┘  └─────────────────────┘
```

---

## 4. API Endpoints

### 4.1 GET /api/alerts
Proxy a Alertmanager v2 API. Filtra por estado (active/suppressed/unprocessed) y severidad.

**Response**: `{ alerts: Alert[], total: int }`

### 4.2 POST /api/alerts/{fingerprint}/silence
Crea un silence en Alertmanager para la alerta identificada por fingerprint.

**Request Body**:
```json
{
  "duration": "1h",       // "30m" | "1h" | "4h" | "24h"
  "comment": "Maintenance window"  // opcional
}
```

**Lógica**:
1. Busca la alerta en Alertmanager por fingerprint
2. Extrae labels: `alertname`, `instance`, `job`
3. Construye matchers con `isEqual: true`
4. Calcula `startsAt` (ahora) y `endsAt` (ahora + duración) en ISO 8601
5. POST a `/api/v2/silences` de Alertmanager
6. Retorna `{ silenceID, status, message }`

### 4.3 GET /api/alerts/silences
Lista silences activos desde Alertmanager.

### 4.4 POST /api/alerts/{fingerprint}/ack
Registra acknowledgement en PostgreSQL.

**Request Body**:
```json
{
  "note": "Investigating the issue"  // opcional
}
```

**Lógica**:
1. Busca alerta en AM para obtener `alertname`
2. Upsert en tabla `alert_acknowledgements` (fingerprint + status=ACKNOWLEDGED)
3. Registra usuario (JWT `sub`), timestamp, nota

### 4.5 GET /api/alerts/ack-status?fingerprints=fp1,fp2,...
Batch query de estado de acknowledgement. Retorna mapa fingerprint → {acknowledged, ack_by, ack_at, status, note}.

### 4.6 POST /api/alerts/{fingerprint}/resolve
Marca un acknowledgement como RESOLVED con timestamp.

---

## 5. Modelo de Datos

### Tabla: alert_acknowledgements

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL PK | Auto-increment |
| fingerprint | VARCHAR(64) | Fingerprint de alerta (indexed) |
| alertname | VARCHAR(255) | Nombre de la alerta (indexed) |
| status | VARCHAR(20) | ACKNOWLEDGED / RESOLVED |
| ack_by | VARCHAR(100) | Usuario que reconoció |
| ack_at | TIMESTAMPTZ | Momento del acknowledgement |
| resolved_at | TIMESTAMPTZ | Momento de resolución (nullable) |
| note | TEXT | Nota libre (nullable) |
| created_at | TIMESTAMPTZ | Creación del registro |
| updated_at | TIMESTAMPTZ | Última actualización |

**Auto-creación**: La tabla se crea automáticamente en `startup_event()` con `checkfirst=True`.

---

## 6. Frontend

### Alerts.tsx (457 líneas → reescrito completo)

**Funcionalidades**:
- Polling de alertas cada 30s via `useQuery`
- Polling de ack-status cada 60s
- Polling de silences cada 60s
- Botón **Silence** con selector de duración (30m/1h/4h/24h)
- Botón **Acknowledge** (deshabilitado si ya está ACK)
- Badge "ACK" visible en cada fila con alerta reconocida
- Feedback visual (success/error) con auto-dismiss 5s
- Colores por severidad: critical=red, warning=amber, info=blue
- Export CSV de alertas

### Correcciones TypeScript:
- Removido import no usado: `useMutation` (error TS6133)
- Corregidos 5 unions de tipo: `string || undefined` → `string | undefined`

---

## 7. Archivos Modificados

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `frontend/src/pages/Logs.tsx` | + Authorization header | ~3 |
| `frontend/src/pages/Traces.tsx` | + 2× Authorization header | ~6 |
| `frontend/src/pages/Alerts.tsx` | Reescritura completa | 457 |
| `backend/routers/alerts.py` | Reescritura completa (6 endpoints) | ~200 |
| `backend/models/alert_acknowledgement.py` | **NUEVO** — SQLAlchemy model | ~40 |
| `backend/models/__init__.py` | + import AlertAcknowledgement | 2 |
| `backend/main.py` | + import + auto-create table | ~8 |
| `docker-compose-v2.5.0-SECURE.yml` | image tag → v2.5.2-alerts | 1 |

---

## 8. Docker Images

| Imagen | Tag | Build |
|--------|-----|-------|
| rhinometric-console-backend | v2.5.2-alerts | `--no-cache` rebuild |
| rhinometric-console-frontend | v2.5.2-alerts | `--no-cache` rebuild |

---

## 9. Validación

### Tests ejecutados (2026-02-13):

| Test | Resultado |
|------|-----------|
| `POST /api/auth/login` | ✅ 200 — JWT obtenido |
| `GET /api/logs` (1h range) | ✅ 200 — Loki responde |
| `GET /api/traces/services` | ✅ 200 — 2 servicios |
| `GET /api/traces` | ✅ 200 — Spans con detalle completo |
| `GET /api/alerts` | ✅ 200 — Lista alertas |
| `GET /api/alerts/ack-status` | ✅ 200 — Estado ack por fingerprint |
| `GET /api/alerts/silences` | ✅ 200 — Lista silences |
| PostgreSQL `alert_acknowledgements` | ✅ Tabla auto-creada |
| Backend health check | ✅ Healthy |
| Frontend container | ✅ Healthy |

---

## 10. Decisiones de Diseño

1. **Silence vía Alertmanager API v2** (no v1): Permite matchers estructurados y respuesta con silenceID
2. **Acknowledge en PostgreSQL** (no en Alertmanager): Los silences de AM son efímeros; el ack necesita auditoría permanente
3. **Batch ack-status**: Un solo GET para N fingerprints reduce roundtrips del frontend
4. **Auto-create table**: `checkfirst=True` hace la migración idempotente sin herramientas externas
5. **No useMutation**: Se usa `fetch()` directo con `queryClient.invalidateQueries()` para simplicidad
6. **Ticketing/Jira**: Diferido a Fase 3 — Integraciones Externas

---

## 11. Fase 3 — Pendiente

- [ ] Integración con ticketing (Jira/ServiceNow) vía webhook en el acknowledge
- [ ] Escalation automática si alerta no ack en N minutos
- [ ] Historial de silences por alerta
- [ ] Dashboard Grafana con métricas de MTTA (Mean Time To Acknowledge)
