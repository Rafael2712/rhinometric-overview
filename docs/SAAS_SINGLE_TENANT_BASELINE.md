# RHINOMETRIC - SaaS Single-Tenant Baseline

## Guia para Crear una Nueva Instancia de Cliente

**Fecha:** 2026-02-13T13:02:21Z
**Version plataforma:** v2.5.1-hardened
**Modelo:** 1 VM por cliente (snapshot clonable de Hetzner)
**Operador:** Rhinometric gestiona la VM, el cliente paga licencia anual

---

## Prerequisitos

- Acceso al panel de Hetzner Cloud (cloud.hetzner.com)
- Snapshot base: `rhinometric-prod-base-v2.5.1` (crear desde la VM actual)
- Datos del nuevo cliente:
  - Nombre de la empresa
  - Dominio deseado (ej: `console.acme-corp.com`)
  - Contacto tecnico (email para alertas)
  - Credenciales SMTP (si el cliente proporciona las suyas)
  - Webhook Slack (si aplica)
  - Tier de licencia contratado (essentials / growth / enterprise)

---

## Paso 1: Crear Snapshot Base (una vez)

> **Este paso solo se hace una vez.** Despues se clona el snapshot para cada cliente.

1. Ir a Hetzner Cloud > Servers > `rhinometric-prod`
2. Detener los contenedores antes del snapshot limpio:

```
cd /opt/rhinometric
docker-compose stop
```

3. Crear snapshot: Hetzner > Server > Snapshots > "Create Snapshot"
   - Nombre: `rhinometric-base-v2.5.1-hardened-YYYYMMDD`
4. Reiniciar la VM original:

```
docker-compose up -d
```

5. Verificar que la instancia original sigue OK:

```
docker-compose ps
curl -s http://localhost/api/health
```

---

## Paso 2: Clonar Snapshot para Nuevo Cliente

1. Ir a Hetzner Cloud > Snapshots
2. Seleccionar `rhinometric-base-v2.5.1-hardened-YYYYMMDD`
3. Click "Create Server from Snapshot"
4. Configurar:
   - **Nombre:** `rhinometric-<CUSTOMER_ID>` (ej: `rhinometric-acme-corp`)
   - **Location:** Elegir segun preferencia del cliente (Helsinki, Falkenstein, etc.)
   - **Type:** CX21 minimo (2 vCPU, 4 GB RAM, 40 GB disco) para essentials
   - **SSH Key:** Anadir tu clave SSH de operacion
5. Crear el servidor
6. Anotar la **IP publica** asignada (ej: `95.216.XX.YY`)

---

## Paso 3: Acceder y Cambiar Hostname

```
ssh root@<NUEVA_IP>

# Cambiar hostname
hostnamectl set-hostname rhinometric-<CUSTOMER_ID>

# Verificar
hostname
```

---

## Paso 4: Configurar DNS

En el panel DNS del dominio del cliente (o en Hetzner DNS si gestionamos nosotros):

1. Crear registro A:
   - `console.<dominio-cliente>.com` -> `<NUEVA_IP>`
2. Si el cliente quiere HTTPS (recomendado), tambien:
   - Verificar que el registro A propaga (puede tardar 5-30 min)
   - Los certificados se configuran en el Paso 6

---

## Paso 5: Editar Configuracion del Cliente

### 5.1 Crear/Editar `customer.env`

```
cd /opt/rhinometric
nano config/customer.env
```

Contenido (rellenar con datos del cliente):

```
# RHINOMETRIC - Configuracion de Cliente
CUSTOMER_NAME=Acme Corp
CUSTOMER_ID=acme-corp
CUSTOMER_DOMAIN=console.acme-corp.com
CUSTOMER_PUBLIC_IP=95.216.XX.YY
CUSTOMER_TIMEZONE=Europe/Madrid
CUSTOMER_DEFAULT_LANGUAGE=es
CUSTOMER_LICENSE_TIER=essentials
CUSTOMER_SMTP_HOST=smtp.zoho.eu
CUSTOMER_SMTP_PORT=587
CUSTOMER_SMTP_USER=alerts@rhinometric.com
CUSTOMER_SMTP_PASSWORD=<password>
CUSTOMER_SMTP_FROM=alerts@rhinometric.com
CUSTOMER_ALERT_EMAIL=ops@acme-corp.com
CUSTOMER_SLACK_WEBHOOK=https://hooks.slack.com/services/...
CUSTOMER_SLACK_CHANNEL_ALERTS=#acme-monitoring
CUSTOMER_SLACK_CHANNEL_CRITICAL=#acme-critical
CUSTOMER_SLACK_CHANNEL_INFO=#acme-info
CUSTOMER_SSL_ENABLED=false
CUSTOMER_WEBSITE_URL=https://www.acme-corp.com/
CUSTOMER_WEBSITE_MONITORING=false
```

### 5.2 Actualizar `.env` (passwords de infraestructura)

Generar passwords unicos para esta instancia:

```
cd /opt/rhinometric

# Generar passwords aleatorios
PG_PASS=$(openssl rand -base64 32 | tr -d '=/+' | head -c 32)
REDIS_PASS=$(openssl rand -base64 32 | tr -d '=/+' | head -c 32)
GRAFANA_PASS=$(openssl rand -base64 32 | tr -d '=/+' | head -c 32)
SECRET=$(openssl rand -base64 48 | tr -d '=/+' | head -c 48)
ADMIN_PASS=$(openssl rand -base64 16 | tr -d '=/+' | head -c 16)
```

Editar `.env` con los valores generados:

```
nano .env
```

Campos a cambiar:
- `POSTGRES_PASSWORD=<PG_PASS>`
- `REDIS_PASSWORD=<REDIS_PASS>`
- `GRAFANA_PASSWORD=<GRAFANA_PASS>`
- `SECRET_KEY=<SECRET>`
- `ADMIN_PASSWORD=<ADMIN_PASS>`
- `SMTP_*` -> copiar de customer.env
- `SLACK_WEBHOOK_URL` -> copiar de customer.env

### 5.3 Actualizar Nginx

```
nano nginx/nginx.conf
```

Cambiar:
- `server_name console.rhinometric.com;` -> `server_name <CUSTOMER_DOMAIN>;`

### 5.4 Actualizar Docker Compose

```
nano docker-compose-v2.5.0-SECURE.yml
```

Cambiar en servicio `rhinometric-console-backend`:
- `CORS_ORIGINS`: reemplazar IPs y dominios con los del cliente
- `SECRET_KEY`: usar el nuevo SECRET generado

Cambiar en servicio `rhinometric-grafana`:
- `GF_SERVER_ROOT_URL`: `http://<NUEVA_IP>/grafana`
- `GF_SERVER_DOMAIN`: `<CUSTOMER_DOMAIN>`

Cambiar en servicio `rhinometric-ai-anomaly`:
- `GRAFANA_URL`: `http://<NUEVA_IP>/grafana` (o https si SSL activado)

Cambiar en servicio `license-server-v2`:
- `SMTP_*`: copiar de customer.env

### 5.5 Actualizar Alertmanager

```
nano alertmanager/alertmanager.yml
```

Cambiar todos los campos SMTP:
- `smtp_from`: email del remitente
- `smtp_smarthost`: host:puerto SMTP
- `smtp_auth_username`: usuario SMTP
- `smtp_auth_password`: password SMTP
- `slack_api_url`: webhook Slack del cliente

Cambiar en TODOS los receivers:
- `to:` -> email del cliente para alertas
- `channel:` -> canales Slack del cliente

### 5.6 Actualizar AI Anomaly Config

```
nano rhinometric-ai-anomaly/config.yaml
```

Cambiar en `server.cors_origins`:
- Anadir dominio del cliente

Si `CUSTOMER_WEBSITE_MONITORING=true`:
- Reemplazar URLs `rhinometric.com` por URL del sitio web del cliente
Si no, comentar/deshabilitar las 4 metricas de website monitoring.

### 5.7 Actualizar Frontend (Grafana URL)

```
nano rhinometric-console/frontend/src/utils/grafana.ts
```

Cambiar el fallback:
- `"http://89.167.22.228/grafana"` -> `"http://<NUEVA_IP>/grafana"`

Luego reconstruir el frontend:

```
cd rhinometric-console/frontend
docker build -t rhinometric-console-frontend:v2.5.1-<CUSTOMER_ID> .
cd /opt/rhinometric
```

---

## Paso 6: SSL/HTTPS (Recomendado)

Si el dominio ya apunta a la nueva IP:

```
# Instalar certbot si no esta
apt install -y certbot

# Parar nginx temporalmente
docker-compose stop nginx

# Obtener certificado
certbot certonly --standalone -d <CUSTOMER_DOMAIN> --non-interactive --agree-tos -m ops@rhinometric.com

# Copiar certificados
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/<CUSTOMER_DOMAIN>/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/<CUSTOMER_DOMAIN>/privkey.pem nginx/ssl/

# Descomentar bloque HTTPS en nginx.conf
# Descomentar "443:443" en docker-compose
# Descomentar volume de SSL en docker-compose
# Anadir redirect HTTP->HTTPS en bloque port 80
```

---

## Paso 7: Desplegar

```
cd /opt/rhinometric

# Parar todo
docker-compose down

# Levantar con nueva configuracion
docker-compose up -d

# Esperar 30 segundos a que todos los servicios arranquen
sleep 30

# Verificar
docker-compose ps
```

---

## Paso 8: Checklist de Verificacion

Ejecutar manualmente cada check y marcar con [x] cuando pase:

### 8.1 Servicios Basicos

```
# Todos los contenedores healthy
docker-compose ps | grep -c "healthy"
# Esperado: 15

# Frontend responde
curl -s -o /dev/null -w "%{http_code}" http://localhost/
# Esperado: 200

# Backend health
curl -s http://localhost/api/health
# Esperado: JSON con status ok
```

### 8.2 Autenticacion

```
# Endpoints protegidos devuelven 401 sin token
curl -s -o /dev/null -w "%{http_code}" http://localhost/api/logs
# Esperado: 401

curl -s -o /dev/null -w "%{http_code}" http://localhost/api/traces
# Esperado: 401
```

### 8.3 Login

```
# Login funciona con admin y el nuevo password
curl -s -X POST http://localhost/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=<ADMIN_PASS>"
# Esperado: JSON con access_token
```

### 8.4 Dominio Publico

```
# Desde fuera de la VM, verificar que responde en el dominio
curl -s -o /dev/null -w "%{http_code}" http://<CUSTOMER_DOMAIN>/
# Esperado: 200 (o 301 si HTTPS redirect activo)
```

### 8.5 Grafana Embebido

```
curl -s -o /dev/null -w "%{http_code}" http://localhost/grafana/
# Esperado: 200
```

### 8.6 Alertas (Manual)

- [ ] Enviar alerta de prueba via Alertmanager API:

```
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"info"},"annotations":{"summary":"Test alert for new customer setup"}}]'
```

- [ ] Verificar que llega email a `CUSTOMER_ALERT_EMAIL`
- [ ] Verificar que llega mensaje a Slack `CUSTOMER_SLACK_CHANNEL_INFO`

### 8.7 AI Anomaly

```
curl -s http://localhost:8085/health 2>/dev/null ; curl -s http://rhinometric-ai-anomaly:8085/health
# Verificar desde dentro del contenedor si no hay puerto expuesto
docker exec rhinometric-ai-anomaly curl -s http://localhost:8085/health
# Esperado: JSON con status healthy
```

---

## Paso 9: Documentar la Instancia

Crear un registro del cliente:

```
mkdir -p /opt/rhinometric/docs/customers
cat > /opt/rhinometric/docs/customers/<CUSTOMER_ID>.md << EOF
# Cliente: <CUSTOMER_NAME>
- ID: <CUSTOMER_ID>
- Dominio: <CUSTOMER_DOMAIN>
- IP: <NUEVA_IP>
- Tier: <CUSTOMER_LICENSE_TIER>
- Fecha provisionamiento: $(date -u +%Y-%m-%d)
- Servidor Hetzner: rhinometric-<CUSTOMER_ID>
- Contacto: <CUSTOMER_ALERT_EMAIL>
EOF
```

---

## Resumen de Archivos a Editar por Cliente

| # | Archivo | Que cambiar |
|---|---------|-------------|
| 1 | `config/customer.env` | Todos los datos del cliente (fuente de verdad) |
| 2 | `.env` | Passwords generados + SMTP + Slack |
| 3 | `nginx/nginx.conf` | `server_name` |
| 4 | `docker-compose-v2.5.0-SECURE.yml` | CORS, IPs, Grafana URL, SMTP, SECRET_KEY |
| 5 | `alertmanager/alertmanager.yml` | SMTP, Slack, emails destinatario |
| 6 | `rhinometric-ai-anomaly/config.yaml` | CORS origins, website monitoring URLs |
| 7 | `rhinometric-console/frontend/src/utils/grafana.ts` | IP fallback de Grafana |
| 8 | SSL certs (si aplica) | `nginx/ssl/fullchain.pem`, `nginx/ssl/privkey.pem` |

> **Nota:** En Fase 2.B se creara un script `provision-customer.sh` que lea `customer.env` y aplique todos estos cambios automaticamente, reduciendo los 8 ediciones manuales a 1 solo archivo + 1 comando.

---

## Tiempo Estimado por Instancia

| Paso | Tiempo |
|------|--------|
| Clonar snapshot | 2-5 min |
| DNS | 5 min (+ propagacion) |
| Editar configs (7 archivos) | 15-20 min |
| SSL (si aplica) | 5-10 min |
| Deploy + verificacion | 5-10 min |
| **Total** | **30-50 min** |

Con el script de Fase 2.B, el tiempo se reducira a ~10-15 min.

---

## Rollback / Destruir Instancia

Si hay que desmontar una instancia de cliente:

1. Ir a Hetzner Cloud > Servers
2. Seleccionar `rhinometric-<CUSTOMER_ID>`
3. Destroy (o Shutdown si se quiere conservar)
4. Eliminar registro DNS
5. Archivar `docs/customers/<CUSTOMER_ID>.md`

> Los datos del cliente (PostgreSQL, Grafana, logs) se pierden con la VM. Si se necesita backup previo, hacer `pg_dump` antes de destruir.

---

## Diagrama de Flujo

```
[Snapshot Base v2.5.1]
        |
        v
[Clonar VM en Hetzner]
        |
        v
[Asignar IP + DNS]
        |
        v
[Editar customer.env] <-- Unico input del operador
        |
        v
[Aplicar configs (manual o script)]
        |
        +---> .env (passwords)
        +---> nginx.conf (dominio)
        +---> docker-compose (URLs, CORS)
        +---> alertmanager.yml (SMTP, Slack)
        +---> ai-anomaly config (CORS, website)
        +---> frontend grafana.ts (IP)
        |
        v
[docker-compose up -d]
        |
        v
[Checklist de verificacion]
        |
        v
[Instancia LIVE para el cliente]
```
