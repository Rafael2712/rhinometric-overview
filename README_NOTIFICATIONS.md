# 🔔 Sistema de Notificaciones - Rhinometric Platform

## Resumen Ejecutivo

Rhinometric cuenta con un **sistema de notificaciones multicamel** completamente operacional que permite recibir alertas de infraestructura, aplicaciones y anomalías de IA en tiempo real a través de:

- **Slack** (#rhinometric-alerts): Alertas críticas y warnings en tiempo real
- **Email** (Zoho Mail): Alertas críticas e informativas con formato HTML

---

## 🎯 Características Principales

### ✅ Integración Dual
- **Slack + Email** trabajando simultáneamente
- Routing inteligente por severidad
- Latencias < 30 segundos end-to-end

### ✅ Configuración Flexible
- **Critical**: Slack + Email (inmediato)
- **Warning**: Solo Slack (menos spam en correo)
- **Info**: Solo Email (documentación asíncrona)

### ✅ Formato Profesional
- Mensajes Slack con emojis y formato estructurado
- Correos HTML con tablas y links a consola/Grafana
- Información completa: alerta, instancia, componente, descripción

---

## 📊 Estado Actual

| Componente | Estado | Última Verificación |
|------------|--------|---------------------|
| Alertmanager | ✅ Running | 29-ene-2026 15:25 UTC |
| Slack Webhook | ✅ Activo | 29-ene-2026 15:23 UTC |
| Zoho SMTP | ✅ Activo | 29-ene-2026 15:24 UTC |
| Prometheus | ✅ Scraping | 20/20 targets UP |

**Alertas activas procesadas:**
- CriticalAnomalyDetected (5 instancias)
- HighMemoryUsage (warnings)
- AIAnomalyHighActiveAnomalies (warnings)

---

## 🚀 Cómo Usar

### Recibir Alertas en Slack

1. **Únete al workspace Rhinometric**
2. **Accede al canal #rhinometric-alerts**
3. **Recibirás automáticamente:**
   - 🔥 Alertas CRITICAL (rojas)
   - ⚠️ Alertas WARNING (amarillas)

### Recibir Alertas por Email

1. **Asegúrate de tener acceso a:** rafael.canelon@rhinometric.com
2. **Recibirás automáticamente:**
   - 🔥 Alertas CRITICAL (HTML con borde rojo)
   - ℹ️ Alertas INFO (HTML con borde azul)

### Enviar Alerta de Prueba

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
      "summary": "Test de notificación",
      "description": "Verificación del sistema de alertas"
    }
  }]'
```

---

## 📁 Configuración

### Archivos Principales

```
/opt/rhinometric/
├── alertmanager/
│   └── alertmanager.yml          # Configuración activa
├── config/
│   └── alertmanager-notifications.yml  # Template
├── .env.alertmanager             # Credenciales (gitignored)
└── deploy-alertmanager-notifications.sh
```

### Variables de Entorno

```bash
# .env.alertmanager
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T09TSCTA9DM/B0ABQTGBDL2/***
SMTP_PASSWORD=***
```

### Routing Rules

| Severity | Slack | Email | Repeat Interval |
|----------|-------|-------|-----------------|
| critical | ✅ | ✅ | 1 hora |
| warning | ✅ | ❌ | 6 horas |
| info | ❌ | ✅ | 12 horas |

---

## 🔧 Mantenimiento

### Actualizar Configuración

```bash
# 1. Editar template
nano config/alertmanager-notifications.yml

# 2. Desplegar cambios
./deploy-alertmanager-notifications.sh

# 3. Verificar logs
docker logs rhinometric-alertmanager --tail 20
```

### Rotar Credenciales

**Slack Webhook:**
1. https://api.slack.com/apps → Regenerar webhook
2. Actualizar `SLACK_WEBHOOK_URL` en `.env.alertmanager`
3. Ejecutar `./deploy-alertmanager-notifications.sh`

**SMTP Password:**
1. Cambiar en Zoho Mail
2. Actualizar `SMTP_PASSWORD` en `.env.alertmanager`
3. Ejecutar `./deploy-alertmanager-notifications.sh`

---

## 🐛 Troubleshooting

### No llegan alertas a Slack

```bash
# Verificar webhook
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test manual"}'

# Revisar logs
docker logs rhinometric-alertmanager | grep slack
```

### No llegan alertas por Email

```bash
# Verificar puerto SMTP (debe ser 587, no 465)
nc -zv smtp.zoho.eu 587

# Revisar logs
docker logs rhinometric-alertmanager | grep email
```

### Alertas duplicadas

**Esto es normal:** Las alertas se re-envían según `repeat_interval`:
- Critical: Cada 1 hora
- Warning: Cada 6 horas
- Info: Cada 12 horas

---

## 📚 Documentación Completa

Para más detalles técnicos, ver:
- [NOTIFICATIONS_SYSTEM.md](NOTIFICATIONS_SYSTEM.md) - Documentación técnica completa
- [docker-compose-v2.5.0.yml](docker-compose-v2.5.0.yml) - Definición de servicios
- [Alertmanager Docs](https://prometheus.io/docs/alerting/latest/configuration/)

---

## 📞 Soporte

**Administrador:** Rafael Canelón  
**Email:** rafael.canelon@rhinometric.com  
**Slack:** #rhinometric-alerts  
**Documentación:** /opt/rhinometric/NOTIFICATIONS_SYSTEM.md

---

**Implementado:** 29 de enero de 2026  
**Autor:** Rafael Canelón  
**Versión:** 1.0
