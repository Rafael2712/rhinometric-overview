# FASE 2.A - Inventario de Configuracion: CORE vs CLIENTE

**Fecha:** 2026-02-13T12:58:33Z
**Servidor:** rhinometric-prod (89.167.22.228)
**Objetivo:** Clasificar cada variable/config como CORE (producto) o CLIENTE (instancia)

---

## 1. Archivo: `.env` (raiz)

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `POSTGRES_USER` | rhinometric | CORE | Usuario DB siempre igual |
| `POSTGRES_PASSWORD` | (hash) | CORE | Password generado por instancia, pero no es dato del cliente |
| `REDIS_PASSWORD` | (hash) | CORE | Password generado automaticamente |
| `GRAFANA_USER` | admin | CORE | Siempre admin |
| `GRAFANA_PASSWORD` | (hash) | CORE | Password generado por instancia |
| `SECRET_KEY` | (hash) | CORE | JWT secret, generado por instancia |
| `ADMIN_USERNAME` | admin | CORE | Admin inicial del sistema |
| `ADMIN_PASSWORD` | 271211Rc | CORE | Cambiar en cada instancia, no es dato cliente |
| `HOME` | /root | CORE | Path del sistema |
| `SLACK_WEBHOOK_URL` | hooks.slack.com/... | **CLIENTE** | Webhook Slack del cliente |
| `SMTP_PASSWORD` | (password) | **CLIENTE** | Password SMTP del remitente |
| `SMTP_HOST` | smtp.zoho.eu | **CLIENTE** | Servidor SMTP (puede cambiar por cliente) |
| `SMTP_PORT` | 587 | **CLIENTE** | Puerto SMTP |
| `SMTP_USER` | rafael.canelon@rhinometric.com | **CLIENTE** | Cuenta de correo del remitente |

---

## 2. Archivo: `.env.alertmanager`

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `SLACK_WEBHOOK_URL` | hooks.slack.com/... | **CLIENTE** | Duplicado del .env principal |
| `SMTP_PASSWORD` | (password) | **CLIENTE** | Duplicado del .env principal |

---

## 3. Archivo: `.env.license`

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `LICENSE_SECRET` | RHN2024$PROD#KEY!@ | CORE | Secret interno del license server |

---

## 4. Archivo: `.env.production`

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `DOMAIN` | rhinometric.com | **CLIENTE** | Dominio del cliente |
| `EMAIL` | admin@rhinometric.com | **CLIENTE** | Email admin del cliente |
| `ENVIRONMENT` | production | CORE | Siempre production |
| `GRAFANA_PASSWORD` | (placeholder) | CORE | Duplicado |
| `POSTGRES_PASSWORD` | (placeholder) | CORE | Duplicado |
| `PGBOUNCER_PASSWORD` | (vacio) | CORE | No en uso |
| `GRAFANA_ADMIN_PASSWORD` | (vacio) | CORE | Duplicado |
| `RHINO_LICENSE_TIER` | essentials | **CLIENTE** | Tier de licencia del cliente |

---

## 5. Archivo: `docker-compose-v2.5.0-SECURE.yml` - License Server

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `DATABASE_URL` | postgresql://...@postgres:5432/rhinometric_licenses | CORE | Conexion DB interna |
| `REDIS_URL` | redis://...@redis:6379 | CORE | Conexion Redis interna |
| `SMTP_HOST` | smtp.zoho.eu | **CLIENTE** | Servidor SMTP |
| `SMTP_PORT` | 465 | **CLIENTE** | Puerto SMTP |
| `SMTP_USER` | rafael.canelon@rhinometric.com | **CLIENTE** | Cuenta SMTP |
| `SMTP_PASSWORD` | ${SMTP_PASSWORD} | **CLIENTE** | Password SMTP |
| `SMTP_FROM` | rafael.canelon@rhinometric.com | **CLIENTE** | Remitente de correos |

---

## 6. Archivo: `docker-compose-v2.5.0-SECURE.yml` - Console Backend

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `API_TITLE` | Rhinometric Console API Gateway | CORE | Nombre del API |
| `API_VERSION` | 2.5.0 | CORE | Version del producto |
| `API_PREFIX` | /api | CORE | Prefijo de rutas |
| `SECRET_KEY` | k3y_f1x3d_rh1n0m3tr1c_s3cur3_2026 | CORE | JWT secret (generar por instancia) |
| `ALGORITHM` | HS256 | CORE | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 | CORE | Expiracion token |
| `CORS_ORIGINS` | [...89.167.22.228, console.rhinometric.com...] | **CLIENTE** | Dominios permitidos (incluye IP y dominio del cliente) |
| `PROMETHEUS_URL` | http://prometheus:9090 | CORE | URL interna Prometheus |
| `AI_ANOMALY_URL` | http://rhinometric-ai-anomaly:8085 | CORE | URL interna AI |
| `LICENSE_VALIDATOR_URL` | http://license-server-v2:5000 | CORE | URL interna License |
| `ALERTMANAGER_URL` | http://alertmanager:9093 | CORE | URL interna Alertmanager |
| `GRAFANA_URL` | http://grafana:3000 | CORE | URL interna Grafana |
| `GRAFANA_USER` | admin | CORE | Usuario Grafana |
| `GRAFANA_PASSWORD` | ${GRAFANA_PASSWORD} | CORE | Password Grafana |
| `LOKI_URL` | http://loki:3100 | CORE | URL interna Loki |
| `JAEGER_URL` | http://jaeger:16686 | CORE | URL interna Jaeger |
| `DATABASE_URL` | postgresql://...@postgres:5432/rhinometric | CORE | Conexion DB |
| `ADMIN_USERNAME` | admin | CORE | Admin inicial |
| `ADMIN_PASSWORD` | admin | CORE | Password admin inicial |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | http://otel-collector:4317 | CORE | URL interna OTEL |
| `OTEL_SERVICE_NAME` | rhinometric-console-backend | CORE | Nombre servicio OTEL |

---

## 7. Archivo: `docker-compose-v2.5.0-SECURE.yml` - Grafana

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `GF_SECURITY_ADMIN_USER` | admin | CORE | Admin Grafana |
| `GF_SECURITY_ADMIN_PASSWORD` | ${GRAFANA_PASSWORD} | CORE | Password Grafana |
| `GF_SERVER_ROOT_URL` | http://89.167.22.228/grafana | **CLIENTE** | URL publica de Grafana (contiene IP del cliente) |
| `GF_SERVER_SERVE_FROM_SUB_PATH` | true | CORE | Siempre subpath |
| `GF_SERVER_DOMAIN` | app.rhinometric.com | **CLIENTE** | Dominio del cliente |
| `GF_SERVER_NAME` | Rhinometric Observability Platform | CORE | Nombre producto |
| `GF_BRANDING_TITLE` | Rhinometric | CORE | Branding producto |
| `GF_BRANDING_FOOTER` | Powered by Rhinometric v2.5.0 | CORE | Footer producto |

---

## 8. Archivo: `docker-compose-v2.5.0-SECURE.yml` - AI Anomaly

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `GRAFANA_URL` | https://grafana.rhinometric.com | **CLIENTE** | URL publica Grafana del cliente |
| `CHECK_INTERVAL_SECONDS` | 600 | CORE | Intervalo de deteccion |
| `LOOKBACK_HOURS` | 24 | CORE | Ventana de analisis |

---

## 9. Archivo: `nginx/nginx.conf`

| Directiva | Valor actual | Tipo | Descripcion |
|-----------|-------------|------|-------------|
| `server_name` | console.rhinometric.com | **CLIENTE** | Dominio publico de la consola |
| `ssl_certificate` | (comentado) /etc/nginx/ssl/fullchain.pem | **CLIENTE** | Certificado SSL del dominio |
| `ssl_certificate_key` | (comentado) /etc/nginx/ssl/privkey.pem | **CLIENTE** | Clave privada SSL |
| Rate limits (api_limit, auth_limit) | 30r/s, 5r/m | CORE | Limites de tasa |
| Upstream servers | nombres Docker internos | CORE | Nombres de contenedores |

---

## 10. Archivo: `alertmanager/alertmanager.yml`

| Campo | Valor actual | Tipo | Descripcion |
|-------|-------------|------|-------------|
| `smtp_from` | rafael.canelon@rhinometric.com | **CLIENTE** | Remitente de alertas email |
| `smtp_smarthost` | smtp.zoho.eu:587 | **CLIENTE** | Servidor SMTP |
| `smtp_auth_username` | rafael.canelon@rhinometric.com | **CLIENTE** | Usuario SMTP |
| `smtp_auth_password` | (password) | **CLIENTE** | Password SMTP |
| `slack_api_url` | hooks.slack.com/... | **CLIENTE** | Webhook Slack global |
| Receivers `to:` | rafael.canelon@rhinometric.com | **CLIENTE** | Destinatarios de alertas |
| Slack channels | #rhinometric-alerts, #rhinometric-critical, #rhinometric-info | **CLIENTE** | Canales Slack del cliente |

---

## 11. Archivo: `rhinometric-console/frontend/src/utils/grafana.ts`

| Variable | Valor actual | Tipo | Descripcion |
|----------|-------------|------|-------------|
| `GRAFANA_PUBLIC_URL` (fallback) | http://89.167.22.228/grafana | **CLIENTE** | URL publica de Grafana hardcodeada como fallback |
| `VITE_GRAFANA_PUBLIC_URL` | (env var, no seteada) | **CLIENTE** | URL publica Grafana via env build |

---

## 12. Archivo: `rhinometric-console/frontend/src/pages/*.tsx` (hardcoded)

| Referencia | Valor | Tipo | Descripcion |
|------------|-------|------|-------------|
| `support@rhinometric.com` | email soporte | CORE | Email de soporte del producto Rhinometric |
| `sales@rhinometric.com` | email ventas | CORE | Email de ventas del producto |

---

## 13. Archivo: `rhinometric-ai-anomaly/config.yaml`

| Campo | Valor actual | Tipo | Descripcion |
|-------|-------------|------|-------------|
| `server.cors_origins` | localhost, grafana.rhinometric.com | **CLIENTE** | Origenes CORS (dominio del cliente) |
| `alertmanager.labels.team` | platform | CORE | Label de equipo |
| `models.*` | (configuracion ML) | CORE | Parametros de modelos ML |
| `metrics.*` | (queries Prometheus) | CORE | Metricas a monitorizar |
| `rhinometric.com` website checks | URLs rhinometric.com | **CLIENTE** | URLs del sitio web a monitorizar (si el cliente tiene web) |

---

## 14. Archivo: `loki/config.yml`

| Campo | Valor actual | Tipo | Descripcion |
|-------|-------------|------|-------------|
| `limits_config.retention_period` | 168h (7 dias) | **CLIENTE** | Retencion segun tier de licencia |
| Resto de config | (parametros Loki) | CORE | Config tecnica del motor |

---

## 15. Archivo: `prometheus/prometheus.yml`

| Campo | Valor actual | Tipo | Descripcion |
|-------|-------------|------|-------------|
| `scrape_interval` | 15s | CORE | Intervalo de scrape |
| Todos los targets internos | nombres Docker | CORE | Targets del stack propio |
| blackbox-http targets | URLs internas | CORE | Health checks internos |

---

## 16. Archivos NO client-specific (100% CORE)

| Archivo | Motivo |
|---------|--------|
| `config/otel-collector-config.yml` | Config tecnica del collector |
| `grafana/provisioning/datasources/*` | Datasources apuntan a servicios internos |
| `grafana/provisioning/dashboards/*` | Dashboards del producto |
| `prometheus/rules/alerts.yml` | Reglas de alerta del stack |
| `blackbox/blackbox.yml` | Config del exporter |
| `config/promtail-config.yml` | Config de recoleccion de logs |

---

## Resumen: Variables tipo CLIENTE

| # | Variable / Campo | Archivo(s) donde aparece | Valor actual |
|---|-----------------|--------------------------|-------------|
| 1 | **Dominio publico** | nginx.conf, compose (CORS_ORIGINS, GF_SERVER_DOMAIN, GF_SERVER_ROOT_URL), .env.production, AI anomaly CORS | console.rhinometric.com / app.rhinometric.com |
| 2 | **IP publica** | compose (CORS_ORIGINS, GF_SERVER_ROOT_URL), frontend grafana.ts | 89.167.22.228 |
| 3 | **SMTP host** | .env, compose (license-server, alertmanager), alertmanager.yml | smtp.zoho.eu |
| 4 | **SMTP port** | .env, compose | 587 / 465 |
| 5 | **SMTP user** | .env, compose, alertmanager.yml | rafael.canelon@rhinometric.com |
| 6 | **SMTP password** | .env, .env.alertmanager, compose | (password) |
| 7 | **SMTP from** | compose (license-server), alertmanager.yml | rafael.canelon@rhinometric.com |
| 8 | **Slack webhook URL** | .env, .env.alertmanager, alertmanager.yml | hooks.slack.com/... |
| 9 | **Slack channels** | alertmanager.yml | #rhinometric-alerts, -critical, -info |
| 10 | **Email destinatario alertas** | alertmanager.yml (4 receivers) | rafael.canelon@rhinometric.com |
| 11 | **Tier de licencia** | .env.production | essentials |
| 12 | **Retencion Loki** | loki/config.yml | 168h |
| 13 | **URL Grafana publica** | compose AI anomaly, frontend grafana.ts | https://grafana.rhinometric.com / http://89.167.22.228/grafana |
| 14 | **Certificados SSL** | nginx.conf (comentado) | No configurado aun |
| 15 | **Website monitoring URLs** | AI anomaly config.yaml | https://www.rhinometric.com/ |
| 16 | **Timezone** | No configurado explicitamente | UTC por defecto |

> **Nota:** Muchas variables CLIENTE estan duplicadas en 2-3 archivos. La Fase 2.A propone centralizar en un unico `customer.env`.
