# Notificaciones AI Anomaly — Slack y Email

**Ultima actualizacion:** 16 Febrero 2026
**Version:** v2.5.2-alerts
**Servidor:** 89.167.22.228 (rhinometric-core-production)
**Estado:** Produccion

---

## Indice

1. [Vision general](#1-vision-general)
2. [Arquitectura del flujo de notificaciones](#2-arquitectura-del-flujo-de-notificaciones)
3. [Reglas de alerta (Prometheus)](#3-reglas-de-alerta-prometheus)
4. [Plantilla Slack](#4-plantilla-slack)
5. [Plantilla Email (HTML)](#5-plantilla-email-html)
6. [Catalogo de alertas y troubleshooting](#6-catalogo-de-alertas-y-troubleshooting)
7. [Roles y enlaces — RBAC](#7-roles-y-enlaces--rbac)
8. [Verificacion y testing](#8-verificacion-y-testing)
9. [Archivos modificados](#9-archivos-modificados)

---

## 1. Vision general

Las notificaciones de anomalia AI de Rhinometric informan al equipo cuando el motor de inteligencia artificial detecta comportamientos atipicos en las metricas de infraestructura o de la plataforma web.

### Antes (v2.5.1)
- Mensajes genericos tipo "Anomalia detectada en node_cpu_usage"
- Sin contexto de troubleshooting
- Link a "View in Prometheus" (obsoleto — las metricas viven en VictoriaMetrics)
- Formato identico al resto de alertas (infra, licensing, etc.)

### Despues (v2.5.2-alerts)
- Mensajes con descripcion en lenguaje humano por tipo de metrica
- Mini-runbook de troubleshooting (2-3 pasos) incluido en cada notificacion
- Botones de accion:
  - "Abrir en consola Rhinometric" (para todos los roles)
  - "Ver metricas en Grafana" (admin/owner, datasource VictoriaMetrics)
- Formato dedicado para AI anomaly (separado del formato generico)
- Plantillas especificas: `ai_anomaly_slack.tmpl` y `ai_anomaly_email.tmpl`

---

## 2. Arquitectura del flujo de notificaciones

```
AI Engine (:8085)
    │
    │ Exporta: rhinometric_anomaly_active{metric_name, severity}
    │          rhinometric_anomaly_score
    │          rhinometric_anomaly_deviation_percent
    │          rhinometric_anomaly_current_value
    │          rhinometric_anomaly_expected_value
    │
    ▼
Prometheus (:9090)
    │
    │ Evalua reglas: CriticalAnomalyDetected, HighAnomalyDetected,
    │                MediumAnomalyDetected, AIAnomalyServiceDown
    │ Labels: component=ai-anomaly, severity, metric_name
    │
    ▼
Alertmanager (:9093)
    │
    │ Route: match component=ai-anomaly → receiver "ai-anomaly-alerts"
    │
    ├──► Slack (#rhinometric-alerts)
    │    Template: ai_anomaly_slack.tmpl
    │    - Titulo con emoji de severidad
    │    - Descripcion en lenguaje humano
    │    - Contexto (componente, metrica, instancia)
    │    - Troubleshooting inline
    │    - Botones: Consola + Grafana
    │
    └──► Email (Zoho → rafael.canelon@rhinometric.com)
         Template: ai_anomaly_email.tmpl
         - Header con color por severidad
         - Seccion "Que ha detectado Rhinometric"
         - Tabla de contexto
         - Botones de accion
         - Guia rapida de troubleshooting
         - Links a documentacion
```

---

## 3. Reglas de alerta (Prometheus)

**Archivo:** `config/rules/alerts.yml` — grupo `ai_anomaly_alerts`

| Alerta | Expresion | For | Severidad | Descripcion |
|---|---|---|---|---|
| `CriticalAnomalyDetected` | `rhinometric_anomaly_active{severity="critical"} == 1` | 2m | critical | Anomalia critica detectada por el modelo AI |
| `HighAnomalyDetected` | `rhinometric_anomaly_active{severity="high"} == 1` | 5m | warning | Anomalia alta sostenida |
| `MediumAnomalyDetected` | `rhinometric_anomaly_active{severity="medium"} == 1` | 10m | warning | Anomalia moderada sostenida |
| `AIAnomalyServiceDown` | `up{job="rhinometric-ai-anomaly"} == 0` | 2m | critical | Servicio AI caido |

Todas las reglas de anomalia incluyen `component: ai-anomaly` en sus labels, lo que permite el routing dedicado en Alertmanager.

---

## 4. Plantilla Slack

**Archivo:** `alertmanager/templates/ai_anomaly_slack.tmpl`

### Estructura del mensaje

```
🔴 [CRITICAL] AI Anomaly: node_cpu_usage (rhinometric-ai-anomaly:8085)

Uso de CPU del nodo fuera del rango normal aprendido por el modelo AI.

Contexto:
• Componente: ai-anomaly
• Metrica: node_cpu_usage
• Severidad: CRITICAL
• Estado: firing
• Instancia: rhinometric-ai-anomaly:8085
• Detectado: 2026-02-16 14:15:00 UTC

Troubleshooting:
1. Revisar grafica de CPU en los ultimos 30 minutos en Grafana.
2. Cruzar con logs de procesos principales en el nodo.
3. Comprobar si coincide con despliegues, backups o jobs pesados.

[Abrir en consola Rhinometric]  [Ver metricas en Grafana (admin)]
```

### Emojis de severidad
| Severidad | Emoji |
|---|---|
| CRITICAL | 🔴 |
| HIGH | 🟠 |
| WARNING / MEDIUM | 🟡 |
| LOW / INFO | 🔵 |

---

## 5. Plantilla Email (HTML)

**Archivo:** `alertmanager/templates/ai_anomaly_email.tmpl`

### Secciones del correo

1. **Header** — Color gradient por severidad (rojo=critical, naranja=high, amarillo=warning, azul=low)
   - Badges: severidad + "AI ANOMALY" + estado
   - Metrica + instancia + timestamp

2. **Que ha detectado Rhinometric** — Descripcion en lenguaje humano segun `metric_name`
   - Si hay datos de desviacion: porcentaje + valor actual vs baseline

3. **Contexto** — Tabla con tipo, alerta, metrica, severidad, estado, componente, instancia, job, timestamps

4. **Acciones rapidas** — Dos botones:
   - "Abrir en consola Rhinometric" → `https://console.rhinometric.com/anomalies`
   - "Ver metricas en Grafana" → Grafana Explore con datasource `victoriametrics`
   - Nota: "Grafana requiere permisos de ADMIN/OWNER"

5. **Guia rapida de troubleshooting** — 3 pasos especificos por tipo de metrica

6. **Mas informacion** — Links a documentacion en GitHub:
   - `AI_ANOMALIES_CORRELATION_MODULE.md`
   - `ALERTING_NOTIFICATIONS_AI_ANOMALY.md`

7. **Footer** — Version, servidor, nota de suscripcion

---

## 6. Catalogo de alertas y troubleshooting

### node_cpu_usage
**Significado:** Uso de CPU del nodo fuera del rango normal aprendido (picos anomalos o caida brusca).

**Primeros pasos:**
1. Revisar grafica de CPU en los ultimos 30 minutos en Grafana.
2. Cruzar con logs de procesos principales en el nodo.
3. Comprobar si coincide con despliegues, backups o jobs pesados.

---

### node_memory_usage
**Significado:** Uso de memoria del nodo fuera del rango normal aprendido.

**Primeros pasos:**
1. Revisar uso de RAM total y por proceso en Grafana.
2. Buscar OOM kills en logs del sistema.
3. Verificar si hay fugas de memoria en servicios recientes.

---

### node_disk_usage
**Significado:** Uso de disco fuera del rango esperado por el baseline.

**Primeros pasos:**
1. Verificar espacio en disco con `df -h` en el nodo.
2. Identificar directorios que crecen rapido (logs, datos).
3. Revisar politicas de retencion y limpieza automatica.

---

### node_disk_io
**Significado:** Latencia o throughput de disco anomalos (mas lentos o mucho mas rapidos de lo esperado).

**Primeros pasos:**
1. Revisar metricas de IOPS, read/write bytes y latencia.
2. Comprobar si hay procesos con acceso intensivo a disco (DB, backup).
3. Ver espacio libre y errores en logs de sistema.

---

### node_network_receive
**Significado:** Trafico de red entrante inusual en el nodo.

**Primeros pasos:**
1. Mirar metricas de rx_bytes, rx_packets y drops.
2. Revisar logs de firewall / reverse-proxy.
3. Verificar si coincide con campanas, pruebas de carga o escaneos.

---

### node_network_transmit
**Significado:** Trafico de red saliente anomalo (posible fuga de datos, picos de respuestas, etc.).

**Primeros pasos:**
1. Ver metricas de tx_bytes, tx_packets, errores/drops.
2. Revisar que servicios generan mas trafico (logs de apps / proxy).
3. Validar si hay jobs de sincronizacion, backups externos, etc.

---

### rhinometric_website_availability
**Significado:** Disponibilidad de la web mas baja de lo esperado (caidas o errores).

**Primeros pasos:**
1. Revisar HTTP status (5xx/4xx), uptime y health checks.
2. Mirar logs de Nginx/ingress y de la aplicacion web.
3. Comprobar despliegues recientes en frontend/backend.

---

### rhinometric_website_response_time
**Significado:** Tiempos de respuesta de la web mas altos de lo normal.

**Primeros pasos:**
1. Ver metricas de latencia (p95/p99) en Grafana.
2. Revisar CPU, memoria y GC en los servicios web.
3. Consultar logs de consultas lentas (DB / APIs internas).

---

### rhinometric_website_ssl_expiry
**Significado:** Certificado SSL con vencimiento anomalo detectado.

**Primeros pasos:**
1. Verificar fecha de vencimiento del certificado SSL.
2. Comprobar renovacion automatica (Let's Encrypt / proveedor).
3. Revisar configuracion de HTTPS en Nginx.

---

### rhinometric_website_dns_time
**Significado:** La resolucion DNS de la web esta tardando mas de lo esperado.

**Primeros pasos:**
1. Ver metricas de DNS lookup time.
2. Comprobar estado del proveedor DNS / registros.
3. Revisar cambios recientes en records (A/CNAME) o TTL.

---

## 7. Roles y enlaces — RBAC

### Principio de diseno

Las notificaciones son **universales** — todos los roles las reciben. La seguridad se delega a cada destino:

| Accion | Todos los roles | Solo ADMIN/OWNER |
|---|---|---|
| Recibir alerta Slack/email | Si | Si |
| Boton "Abrir en consola Rhinometric" | Funcional para todos | Funcional para todos |
| Boton "Ver metricas en Grafana" | Visible para todos | Solo admin/owner tiene acceso real |
| Grafana Explore (datasource victoriametrics) | Bloqueado por RBAC de Grafana | Acceso completo |

### Como funciona

1. **Consola Rhinometric** — Al hacer clic, el usuario entra a `/anomalies`. La consola ya aplica su propio RBAC:
   - ADMIN/OWNER: ven los botones de Grafana en el modal de anomalia
   - OPERATOR/VIEWER: ven la informacion pero sin acceso a herramientas externas

2. **Grafana** — Si un viewer hace clic en el boton de Grafana, Grafana/SSO se encargan de bloquear o mostrar solo lo permitido. No inventamos otra capa de seguridad en Alertmanager.

---

## 8. Verificacion y testing

### Verificar config de Alertmanager
```bash
# Health check
docker exec rhinometric-alertmanager wget -qO- http://localhost:9093/-/healthy

# Verificar que el receiver ai-anomaly-alerts existe
docker exec rhinometric-alertmanager wget -qO- http://localhost:9093/api/v2/status | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('ai-anomaly' in d['config']['original'])
"
```

### Verificar reglas en Prometheus
```bash
# Reload rules
docker exec rhinometric-prometheus kill -HUP 1

# Verificar grupo ai_anomaly_alerts
docker exec rhinometric-prometheus wget -qO- http://localhost:9090/api/v1/rules | python3 -c "
import json,sys
d=json.load(sys.stdin)
for g in d['data']['groups']:
    if 'ai_anomaly' in g['name']:
        print(f'Rules: {len(g[\"rules\"])}')
        for r in g['rules']: print(f'  {r[\"name\"]}')
"
```

### Verificar alertas activas
```bash
docker exec rhinometric-prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=ALERTS{component="ai-anomaly"}' | python3 -c "
import json,sys
d=json.load(sys.stdin)
results=d['data']['result']
print(f'AI anomaly alerts firing: {len(results)}')
for r in results[:3]:
    print(f'  {r[\"metric\"][\"alertname\"]} - {r[\"metric\"][\"metric_name\"]} [{r[\"metric\"][\"severity\"]}]')
"
```

---

## 9. Archivos modificados

| Archivo | Accion | Descripcion |
|---|---|---|
| `alertmanager/alertmanager.yml` | Modificado | Anadida ruta `component: ai-anomaly` → receiver `ai-anomaly-alerts` con templates dedicados |
| `alertmanager/templates/ai_anomaly_slack.tmpl` | Nuevo | Plantilla Slack con titulo, descripcion, contexto, troubleshooting y botones |
| `alertmanager/templates/ai_anomaly_email.tmpl` | Nuevo | Plantilla email HTML con header, contexto, acciones, troubleshooting y footer |
| `alertmanager/templates/email.tmpl` | Sin cambios | Plantilla generica para alertas no-AI (no modificada) |
| `config/rules/alerts.yml` | Modificado | Anadida regla `MediumAnomalyDetected`, enriquecidas annotations con descripciones human-friendly |

### Archivos NO modificados (confirmacion)
- Ningun archivo `.tsx`, `.ts`, `.css` del frontend
- Ningun archivo de backend Python
- Ninguna configuracion de docker-compose
- Ninguna regla de alerta fuera del grupo `ai_anomaly_alerts`

---

**Documento generado:** 16 Feb 2026 — Rhinometric DevOps Team
**Clasificacion:** Interno — Equipo de Desarrollo
