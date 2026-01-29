# Sistema de Notificaciones Rhinometric

## Estado: ✅ OPERACIONAL

**Fecha de implementación:** 29 de enero de 2026  
**Fase:** FASE 5 - Sistema de Notificaciones Slack + Email  
**Tiempo de implementación:** 3 horas

---

## 📊 Resumen Ejecutivo

El sistema de notificaciones de Rhinometric está **completamente operacional** con dos canales de comunicación:

1. **Slack** (#rhinometric-alerts): Alertas críticas y warnings en tiempo real
2. **Email** (rafael.canelon@rhinometric.com): Alertas críticas e informativas

### Estado de Canales

| Canal | Estado | Última Verificación | Tipo de Alertas | Latencia |
|-------|--------|---------------------|-----------------|----------|
| Slack | ✅ Activo | 2026-01-29 15:23 UTC | Critical + Warning | < 15s |
| Email | ✅ Activo | 2026-01-29 15:24 UTC | Critical + Info | < 30s |

**Última prueba exitosa:** VerificacionEmail_1523 (29-ene-2026 15:23)  
- ✅ Slack: Mensaje recibido en #rhinometric-alerts  
- ✅ Email: Correo HTML recibido en rafael.canelon@rhinometric.com

---

## 🔧 Configuración Técnica

### Arquitectura del Sistema

```
Prometheus → Alertmanager → [Slack Webhook]
                          └→ [Zoho SMTP]
```

### Alertmanager Configuration

**Archivo:** `/opt/rhinometric/alertmanager/alertmanager.yml`  
**Versión:** 0.27.0  
**Puerto:** 9093

#### Receivers Configurados

1. **critical-alerts** (Slack + Email)
   - Alertas con `severity: critical`
   - Envío a ambos canales simultáneamente
   - Group wait: 10 segundos
   - Repeat interval: 1 hora

2. **warning-alerts** (Solo Slack)
   - Alertas con `severity: warning`
   - Envío solo a Slack para rapidez
   - Group wait: 1 minuto
   - Repeat interval: 6 horas

3. **email-only** (Solo Email)
   - Alertas con `severity: info`
   - Documentación por correo
   - Group wait: 5 minutos
   - Repeat interval: 12 horas

### Configuración SMTP (Zoho Mail)

```yaml
global:
  smtp_smarthost: 'smtp.zoho.eu:587'
  smtp_from: 'rafael.canelon@rhinometric.com'
  smtp_auth_username: 'rafael.canelon@rhinometric.com'
  smtp_auth_password: <REDACTED>
  smtp_require_tls: true
```

**Nota importante:** Se usa el puerto **587 con STARTTLS** (no 465) debido a restricciones del firewall de la VM.

### Configuración Slack

**Webhook URL:** `https://hooks.slack.com/services/T09TSCTA9DM/B0ABQTGBDL2/***`  
**Canal destino:** `#rhinometric-alerts`  
**Workspace:** Rhinometric

#### Formato de Mensajes Slack

```
🔥 CRITICAL: <alertname>
⚠️ WARNING: <alertname>

Instance: <instance>
Component: <component>
Description: <descripción detallada>

Status: <firing/resolved>
Started at: <timestamp>

🔗 View Console | 📊 View Grafana
```

---

## 📧 Formato de Correos HTML

Los correos incluyen:

- **Asunto:** `[SEVERITY] Alert: <alertname>`
- **Cuerpo HTML:** Tabla con detalles completos
- **Links directos:** Consola Rhinometric + Grafana
- **Estilo:** Borde rojo para critical, amarillo para warnings

### Ejemplo de Contenido

```html
<table style="border: 3px solid #dc3545; padding: 20px;">
  <tr><th>Alert:</th><td>CriticalAnomalyDetected</td></tr>
  <tr><th>Instance:</th><td>rhinometric-ai-anomaly:8085</td></tr>
  <tr><th>Component:</th><td>ai-anomaly</td></tr>
  <tr><th>Severity:</th><td style="color: #dc3545;">critical</td></tr>
  <tr><th>Status:</th><td>firing</td></tr>
  <tr><th>Description:</th><td>IA detectó anomalía crítica...</td></tr>
  <tr><th>Summary:</th><td>Anomalía CRÍTICA detectada...</td></tr>
  <tr><th>Started at:</th><td>2026-01-29 12:31:56 UTC</td></tr>
</table>

<div style="margin-top: 20px;">
  <a href="http://89.167.15.73:3002">🔗 View Console</a> |
  <a href="http://89.167.15.73:3000">📊 View Grafana</a>
</div>
```

---

## 🚨 Reglas de Routing

### Matriz de Decisión

| Severity | Slack | Email | Group Wait | Repeat Interval |
|----------|-------|-------|------------|-----------------|
| critical | ✅ | ✅ | 10s | 1h |
| warning | ✅ | ❌ | 1m | 6h |
| info | ❌ | ✅ | 5m | 12h |

### Reglas de Inhibición

```yaml
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance', 'component']
```

**Efecto:** Si hay una alerta crítica activa, se suprimen las warnings del mismo componente para evitar ruido.

---

## 🔍 Alertas Activas Monitoreadas

El sistema de notificaciones procesa automáticamente las siguientes alertas de Prometheus:

### Alertas Críticas (Critical)
- `CriticalAnomalyDetected` - Anomalías detectadas por IA con score > 0.95
- `InstanceDown` - Servicios caídos
- `HighDiskUsage` (>95%) - Espacio en disco crítico
- `HighErrorRate` - Tasa de errores > 10%

### Alertas de Advertencia (Warning)
- `HighMemoryUsage` (>90%) - Uso de memoria elevado
- `HighCPUUsage` (>80%) - CPU sobrecargada
- `HighAnomalyDetected` - Anomalías con score > 0.85
- `SlowResponseTime` - Latencias > 2s

### Alertas Informativas (Info)
- `BackupCompleted` - Respaldo exitoso
- `NewLicenseActivated` - Licencia nueva activada
- `SystemMaintenanceScheduled` - Mantenimiento programado

---

## 📁 Archivos de Configuración

### Estructura de Archivos

```
/opt/rhinometric/
├── alertmanager/
│   └── alertmanager.yml          # Config activa (variables expandidas)
├── config/
│   └── alertmanager-notifications.yml  # Template con ${VARIABLES}
├── .env.alertmanager             # Credenciales (NO COMMITEAR)
└── docker-compose-v2.5.0.yml     # Definición del servicio
```

### Variables de Entorno

**Archivo:** `.env.alertmanager`

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T09TSCTA9DM/B0ABQTGBDL2/***
SMTP_PASSWORD=***
```

⚠️ **CRÍTICO:** Este archivo NO debe incluirse en Git. Está en `.gitignore`.

### Script de Despliegue

**Archivo:** `deploy-alertmanager-notifications.sh`

```bash
#!/bin/bash
# Valida .env, expande variables, reinicia Alertmanager
# Uso: ./deploy-alertmanager-notifications.sh
```

**Funcionalidad:**
1. Valida existencia de `.env.alertmanager`
2. Carga variables de entorno
3. Expande `${SLACK_WEBHOOK_URL}` y `${SMTP_PASSWORD}` en el template
4. Respalda configuración actual
5. Copia nueva configuración a `/opt/rhinometric/alertmanager/alertmanager.yml`
6. Reinicia contenedor `rhinometric-alertmanager`
7. Verifica logs de inicio

---

## ✅ Verificación y Testing

### Verificación Manual

#### 1. Verificar Estado del Servicio

```bash
docker ps | grep alertmanager
# Output esperado: Up X minutes (healthy)

curl -s http://localhost:9093/api/v2/status | jq
# Debe retornar versionInfo y config details
```

#### 2. Ver Alertas Activas

```bash
curl -s http://localhost:9093/api/v2/alerts | python3 -m json.tool
```

#### 3. Enviar Alerta de Prueba

```bash
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestNotification",
      "severity": "critical",
      "instance": "test-server",
      "component": "testing"
    },
    "annotations": {
      "summary": "🔥 Test de notificación crítica",
      "description": "Verificación del sistema de alertas"
    }
  }]'
```

#### 4. Verificar Logs

```bash
docker logs rhinometric-alertmanager --tail 50 | grep -E 'Notify|success|error'
```

**Salida esperada:**
```
level=info msg="Notify success" receiver=critical-alerts integration=slack[0]
level=info msg="Notify success" receiver=critical-alerts integration=email[0]
```

### Checklist de Validación

- [x] Alertmanager escuchando en puerto 9093
- [x] Configuración cargada sin errores
- [x] Webhook de Slack válido y activo
- [x] SMTP conecta exitosamente al puerto 587
- [x] Alertas críticas llegan a Slack < 15 segundos
- [x] Alertas críticas llegan a Email < 30 segundos
- [x] Warnings solo llegan a Slack (no email)
- [x] Formato HTML de emails correcto
- [x] Links en emails funcionan correctamente
- [x] Inhibición de warnings funciona cuando hay critical

---

## 🐛 Troubleshooting

### Problema: No llegan notificaciones a Slack

**Síntomas:**
```bash
docker logs alertmanager | grep slack
# Output: "Post \"<webhook>\": context deadline exceeded"
```

**Solución:**
1. Verificar que el webhook URL sea válido:
   ```bash
   curl -X POST $SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test"}'
   ```
2. Revisar que Alertmanager tenga acceso a internet
3. Verificar que la variable `${SLACK_WEBHOOK_URL}` se expandió correctamente en `alertmanager.yml`

---

### Problema: Timeout al enviar emails (Puerto 465)

**Síntomas:**
```
establish TLS connection to server: dial tcp 185.230.214.164:465: connect: connection timed out
```

**Causa:** El firewall de la VM bloquea el puerto 465 (SMTPS).

**Solución:** ✅ **YA APLICADA**
- Cambiar a puerto **587 con STARTTLS**
- Verificar puerto abierto: `nc -zv smtp.zoho.eu 587`

**Configuración correcta:**
```yaml
smtp_smarthost: 'smtp.zoho.eu:587'  # NO usar :465
smtp_require_tls: true  # STARTTLS habilitado
```

---

### Problema: Variables no expandidas en alertmanager.yml

**Síntomas:**
```yaml
- api_url: ''  # VACÍO
  auth_password: ''  # VACÍO
```

**Causa:** `envsubst` no expandió las variables `${VARIABLE}`.

**Solución:** ✅ **YA APLICADA**
```bash
source .env.alertmanager
sed "s|\${SLACK_WEBHOOK_URL}|$SLACK_WEBHOOK_URL|g; \
     s|\${SMTP_PASSWORD}|$SMTP_PASSWORD|g" \
  config/alertmanager-notifications.yml > alertmanager/alertmanager.yml
```

---

### Problema: Line endings Windows (CRLF) en Linux

**Síntomas:**
```
.env.alertmanager: line 3: $'\r': command not found
```

**Solución:**
```bash
sed -i 's/\r$//' .env.alertmanager deploy-alertmanager-notifications.sh
```

---

## 📊 Métricas y Monitoreo

### Métricas de Alertmanager

Prometheus recolecta automáticamente métricas de Alertmanager:

- `alertmanager_notifications_total` - Total de notificaciones enviadas
- `alertmanager_notifications_failed_total` - Notificaciones fallidas
- `alertmanager_notification_latency_seconds` - Latencia de envío

### Dashboards Recomendados

1. **Alertmanager Overview** (ID: 9578)
   - Estado de receivers
   - Tasa de notificaciones
   - Latencias de envío

2. **Alert Analysis** (Personalizado)
   - Alertas más frecuentes
   - Tiempo de resolución
   - Distribución por severidad

---

## 🔐 Seguridad

### Credenciales Almacenadas

| Credential | Storage | Acceso |
|------------|---------|--------|
| Slack Webhook | `.env.alertmanager` | Root only (chmod 600) |
| SMTP Password | `.env.alertmanager` | Root only (chmod 600) |

### Protección de Secrets

```bash
# En la VM:
chmod 600 /opt/rhinometric/.env.alertmanager
chown root:root /opt/rhinometric/.env.alertmanager

# Verificar:
ls -la /opt/rhinometric/.env.alertmanager
# Output: -rw------- 1 root root 343 Jan 29 12:00 .env.alertmanager
```

### Gitignore

```gitignore
# Ya incluido en .gitignore
.env.alertmanager
.env
*.env
```

---

## 🚀 Despliegue Futuro

### Actualizar Configuración

1. **Modificar template:**
   ```bash
   nano config/alertmanager-notifications.yml
   ```

2. **Ejecutar despliegue:**
   ```bash
   ./deploy-alertmanager-notifications.sh
   ```

3. **Verificar:**
   ```bash
   docker logs rhinometric-alertmanager --tail 20
   ```

### Rotar Credenciales

#### Slack Webhook

1. Ir a https://api.slack.com/apps → Tu App → Incoming Webhooks
2. Regenerar webhook
3. Actualizar `.env.alertmanager`:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/NEW/WEBHOOK/URL
   ```
4. Redesplegar: `./deploy-alertmanager-notifications.sh`

#### SMTP Password

1. Cambiar password en Zoho Mail
2. Actualizar `.env.alertmanager`:
   ```bash
   SMTP_PASSWORD=nuevo_password_aqui
   ```
3. Redesplegar: `./deploy-alertmanager-notifications.sh`

---

## 📈 Próximos Pasos Recomendados

### Mejoras Futuras

1. **Integración con PagerDuty** (opcional)
   - Escalamiento automático para alertas críticas sin resolver
   - Rotación de guardias 24/7

2. **Webhooks Personalizados**
   - Integración con ticketing system (Jira/ServiceNow)
   - Logs centralizados de notificaciones

3. **Templates Avanzados**
   - Gráficos embebidos en emails (PNGs)
   - Contexto histórico de métricas

4. **Notificaciones por Teams** (si se requiere en el futuro)
   ```yaml
   - name: teams-alerts
     webhook_configs:
       - url: '<Teams Webhook URL>'
   ```

---

## 📚 Referencias

### Documentación Oficial

- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Zoho Mail SMTP](https://www.zoho.com/mail/help/adminconsole/smtp-imap-pop-access.html)

### Archivos Relacionados

- [SECURITY_HARDENING.md](SECURITY_HARDENING.md) - FASE 1 y 4.A
- [DASHBOARDS_STATUS.md](DASHBOARDS_STATUS.md) - Estado de dashboards
- [docker-compose-v2.5.0.yml](docker-compose-v2.5.0.yml) - Orquestación

---

## ✅ Estado Final

**Fase 5 completada exitosamente** ✅

- Slack: ✅ Operacional (verificado 15:23 UTC)
- Email: ✅ Operacional (verificado 15:24 UTC)
- Testing: ✅ Validado con alertas reales
- Documentación: ✅ Completa
- Latencias: ✅ < 30 segundos end-to-end

**Pruebas Realizadas:**
1. ✅ TestEmailIntegration - Email recibido
2. ✅ TestSlackIntegration - Slack recibido
3. ✅ VerificacionEmail_1523 - Ambos canales recibidos simultáneamente
4. ✅ CriticalAnomalyDetected (real) - Ambos canales activos

**Listo para Snapshot:** ✅ **SÍ**  
**Snapshot Sugerido:** `GOLD-SECURITY-PHASE5-NOTIFICATIONS-COMPLETE`

---

**Autor:** Rafael Canelón  
**Fecha:** 29 de enero de 2026  
**Versión:** 1.0
