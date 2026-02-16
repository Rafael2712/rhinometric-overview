# FASE 2.A - Propuesta de Configuracion Centralizada por Cliente

**Fecha:** 2026-02-13T12:59:51Z
**Servidor:** rhinometric-prod (89.167.22.228)
**Objetivo:** Definir un archivo unico `customer.env` que centralice todas las variables de tipo CLIENTE

---

## 1. Problema Actual

Las variables especificas del cliente estan dispersas en **8 archivos diferentes**:

- `.env` (raiz)
- `.env.alertmanager`
- `.env.production`
- `docker-compose-v2.5.0-SECURE.yml` (inline en 3 servicios)
- `nginx/nginx.conf`
- `alertmanager/alertmanager.yml`
- `rhinometric-ai-anomaly/config.yaml`
- `rhinometric-console/frontend/src/utils/grafana.ts` (hardcoded)

Esto significa que para configurar un nuevo cliente hay que editar 8 archivos, con riesgo de olvidar alguno o crear inconsistencias.

---

## 2. Archivo Propuesto: `/opt/rhinometric/config/customer.env`

### Estructura

```
# ============================================================
# RHINOMETRIC - Configuracion de Cliente (Instancia)
# ============================================================
# Este archivo contiene TODAS las variables especificas de esta
# instancia de cliente. Es el UNICO archivo que debe editarse
# al provisionar una nueva instancia SaaS.
# ============================================================

# --- IDENTIDAD DEL CLIENTE ---
CUSTOMER_NAME=Acme Corp
CUSTOMER_ID=acme-corp
CUSTOMER_DOMAIN=console.acme-corp.com
CUSTOMER_PUBLIC_IP=89.167.22.228
CUSTOMER_TIMEZONE=Europe/Madrid
CUSTOMER_DEFAULT_LANGUAGE=es

# --- LICENCIA ---
CUSTOMER_LICENSE_TIER=essentials
# Valores: essentials (1-20 hosts) | growth (21-70) | enterprise (71+)

# --- NOTIFICACIONES: EMAIL ---
CUSTOMER_SMTP_HOST=smtp.zoho.eu
CUSTOMER_SMTP_PORT=587
CUSTOMER_SMTP_USER=alerts@acme-corp.com
CUSTOMER_SMTP_PASSWORD=<smtp_password_here>
CUSTOMER_SMTP_FROM=alerts@acme-corp.com
CUSTOMER_ALERT_EMAIL=ops-team@acme-corp.com

# --- NOTIFICACIONES: SLACK (opcional) ---
CUSTOMER_SLACK_WEBHOOK=https://hooks.slack.com/services/XXXXX/YYYYY/ZZZZZ
CUSTOMER_SLACK_CHANNEL_ALERTS=#monitoring-alerts
CUSTOMER_SLACK_CHANNEL_CRITICAL=#monitoring-critical
CUSTOMER_SLACK_CHANNEL_INFO=#monitoring-info

# --- SSL/TLS (rutas relativas a /opt/rhinometric) ---
CUSTOMER_SSL_ENABLED=false
CUSTOMER_SSL_CERT_PATH=./nginx/ssl/fullchain.pem
CUSTOMER_SSL_KEY_PATH=./nginx/ssl/privkey.pem

# --- WEBSITE MONITORING (opcional, si el cliente tiene web) ---
CUSTOMER_WEBSITE_URL=https://www.acme-corp.com/
CUSTOMER_WEBSITE_MONITORING=false
```

---

## 3. Mapeo: customer.env -> Archivos Actuales

Cada variable del `customer.env` se mapea a uno o mas archivos existentes que deben actualizarse:

### 3.1 Identidad y Red

| Variable customer.env | Archivo destino | Campo/Variable destino |
|----------------------|-----------------|----------------------|
| `CUSTOMER_DOMAIN` | `nginx/nginx.conf` | `server_name` |
| `CUSTOMER_DOMAIN` | `docker-compose*.yml` (backend) | `CORS_ORIGINS` (construir array) |
| `CUSTOMER_DOMAIN` | `docker-compose*.yml` (grafana) | `GF_SERVER_DOMAIN` |
| `CUSTOMER_PUBLIC_IP` | `docker-compose*.yml` (backend) | `CORS_ORIGINS` (construir array) |
| `CUSTOMER_PUBLIC_IP` | `docker-compose*.yml` (grafana) | `GF_SERVER_ROOT_URL` |
| `CUSTOMER_PUBLIC_IP` | `frontend grafana.ts` | `GRAFANA_PUBLIC_URL` fallback (o `VITE_GRAFANA_PUBLIC_URL` en build) |

### 3.2 Licencia y Retencion

| Variable customer.env | Archivo destino | Campo/Variable destino |
|----------------------|-----------------|----------------------|
| `CUSTOMER_LICENSE_TIER` | `.env.production` | `RHINO_LICENSE_TIER` |
| `CUSTOMER_LICENSE_TIER` | `loki/config.yml` | `retention_period` (derivado: essentials=168h, growth=120h, enterprise=72h) |

### 3.3 Email / SMTP

| Variable customer.env | Archivo destino | Campo/Variable destino |
|----------------------|-----------------|----------------------|
| `CUSTOMER_SMTP_HOST` | `.env`, compose (license-server, alertmanager) | `SMTP_HOST` |
| `CUSTOMER_SMTP_PORT` | `.env`, compose | `SMTP_PORT` |
| `CUSTOMER_SMTP_USER` | `.env`, compose, `alertmanager.yml` | `SMTP_USER`, `smtp_auth_username` |
| `CUSTOMER_SMTP_PASSWORD` | `.env`, `.env.alertmanager`, compose | `SMTP_PASSWORD`, `smtp_auth_password` |
| `CUSTOMER_SMTP_FROM` | compose (license-server), `alertmanager.yml` | `SMTP_FROM`, `smtp_from` |
| `CUSTOMER_ALERT_EMAIL` | `alertmanager.yml` (4 receivers) | campo `to:` en cada receiver |

### 3.4 Slack

| Variable customer.env | Archivo destino | Campo/Variable destino |
|----------------------|-----------------|----------------------|
| `CUSTOMER_SLACK_WEBHOOK` | `.env`, `.env.alertmanager`, `alertmanager.yml` | `SLACK_WEBHOOK_URL`, `slack_api_url` |
| `CUSTOMER_SLACK_CHANNEL_*` | `alertmanager.yml` | `channel:` en cada receiver |

### 3.5 SSL

| Variable customer.env | Archivo destino | Campo/Variable destino |
|----------------------|-----------------|----------------------|
| `CUSTOMER_SSL_ENABLED` | `nginx/nginx.conf` | Descomentar bloque HTTPS + redirect |
| `CUSTOMER_SSL_CERT_PATH` | `nginx/nginx.conf`, compose (nginx volumes) | `ssl_certificate`, volume mount |
| `CUSTOMER_SSL_KEY_PATH` | `nginx/nginx.conf`, compose (nginx volumes) | `ssl_certificate_key`, volume mount |

### 3.6 Grafana URL Publica

| Variable customer.env | Archivo destino | Campo/Variable destino |
|----------------------|-----------------|----------------------|
| `CUSTOMER_DOMAIN` + `CUSTOMER_SSL_ENABLED` | compose (AI anomaly) | `GRAFANA_URL` = https://DOMAIN/grafana o http://IP/grafana |
| `CUSTOMER_PUBLIC_IP` | compose (grafana) | `GF_SERVER_ROOT_URL` = http://IP/grafana |
| `CUSTOMER_DOMAIN` | `rhinometric-ai-anomaly/config.yaml` | `cors_origins` |

### 3.7 Website Monitoring (opcional)

| Variable customer.env | Archivo destino | Campo/Variable destino |
|----------------------|-----------------|----------------------|
| `CUSTOMER_WEBSITE_URL` | `rhinometric-ai-anomaly/config.yaml` | Reemplazar URLs rhinometric.com en metricas de website |
| `CUSTOMER_WEBSITE_MONITORING` | `rhinometric-ai-anomaly/config.yaml` | Habilitar/deshabilitar 4 metricas de website |

---

## 4. Variables que NO van en customer.env

Estas variables cambian por instancia pero son de infraestructura, no del cliente:

| Variable | Motivo | Donde vive |
|----------|--------|-----------|
| `POSTGRES_PASSWORD` | Generada automaticamente al crear la instancia | `.env` |
| `REDIS_PASSWORD` | Generada automaticamente | `.env` |
| `GRAFANA_PASSWORD` | Generada automaticamente | `.env` |
| `SECRET_KEY` (JWT) | Generada automaticamente | compose inline |
| `ADMIN_PASSWORD` | Generada automaticamente, no es dato del cliente | `.env` |
| `LICENSE_SECRET` | Secret interno del producto | `.env.license` |

Estas se generan una vez al crear la instancia y no se vuelven a tocar.

---

## 5. Flujo Conceptual de Uso

```
1. Clonar snapshot de VM base
2. Editar /opt/rhinometric/config/customer.env con datos del nuevo cliente
3. Ejecutar script de aplicacion (Fase 2.B) que:
   a. Lee customer.env
   b. Genera/actualiza .env, alertmanager.yml, nginx.conf, etc.
   c. Genera passwords aleatorios para POSTGRES, REDIS, GRAFANA, JWT
   d. Reconstruye frontend con VITE_GRAFANA_PUBLIC_URL correcto
   e. docker-compose up -d
4. Validar con checklist
```

> **Nota:** En esta Fase 2.A solo documentamos la propuesta. El script de aplicacion se implementara en Fase 2.B.

---

## 6. Beneficios del Modelo Centralizado

| Antes | Despues |
|-------|---------|
| 8 archivos que editar | 1 archivo (`customer.env`) |
| Riesgo de inconsistencias | Fuente unica de verdad |
| No documentado | Campos claros con comentarios |
| Dificil de validar | Checklist automatizable |
| Error humano probable | Reducido a un solo punto |

---

## 7. Nota sobre el Frontend

El frontend tiene `GRAFANA_PUBLIC_URL` hardcodeado como fallback en `grafana.ts`. Para eliminarlo completamente:

1. Usar `VITE_GRAFANA_PUBLIC_URL` como variable de build-time
2. Al provisionar nuevo cliente, pasar la variable durante `npm run build`
3. Esto requiere rebuild del frontend por cliente (ya contemplado en el Dockerfile multi-stage)

Alternativa: en Fase 2.B, hacer que el frontend lea la URL de Grafana desde el backend via API (ej: `/api/config/public`), eliminando la necesidad de rebuild.

---

## 8. Proximos Pasos

- **Fase 2.A (actual):** Documentar inventario + propuesta (este documento)
- **Fase 2.B:** Implementar script `provision-customer.sh` que lea `customer.env` y aplique cambios
- **Fase 2.C:** Integrar con modelo de licencias
