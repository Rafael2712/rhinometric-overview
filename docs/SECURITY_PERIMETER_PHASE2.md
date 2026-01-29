# FASE 2: Security Perimeter with Nginx Reverse Proxy

**Autor:** Rafael Canelón  
**Fecha:** 29 de enero de 2026  
**Fase:** FASE 2 - Nginx Reverse Proxy como perímetro único  
**Estado:** 🚧 EN PROGRESO

---

## 📋 Objetivo

Implementar Nginx como reverse proxy único punto de entrada a la plataforma Rhinometric, cerrando el perímetro de seguridad y eliminando la exposición directa de servicios internos.

**Características clave:**
- ✅ Agnóstico: Sin dominios hardcodeados (funciona con IP o hostname)
- ✅ On-prem ready: Lista para empaquetar como licencia
- ✅ Sin romper funcionalidad existente
- ✅ Base sólida para futuras mejoras (SSL, RBAC, etc.)

---

## 🔍 PASO 1: Análisis del Estado Actual

### Snapshot Base

**VM:** 89.167.15.73 (rhinometric-core-restore)  
**Snapshot activo:** GOLD-CORE-V2.7.0-NOTIFICATIONS-OK  
**Servicios:** 19/19 UP  
**Branch Git:** feature/use-direct-grafana-links  
**Último commit:** 40b22fd (docs: FASE 5 validada)

### Fases Completadas (Pre-requisitos)

| Fase | Estado | Descripción |
|------|--------|-------------|
| FASE 1 | ✅ | Grafana Security (anonymous disabled, admin secured) |
| FASE 4.A | ✅ | Kiosk Mode (UI chrome oculto) |
| FASE 5 | ✅ | Notificaciones Slack + Email (100% operacionales) |

---

## 🌐 Estado Inicial de Exposición de Puertos

### Servicios Expuestos a Internet (0.0.0.0)

**CRÍTICOS - Deben cerrarse:**

| Servicio | Contenedor | Puerto Externo | Puerto Interno | Función |
|----------|------------|----------------|----------------|---------|
| **Console Frontend** | `rhinometric-console-frontend` | `3002` | `3002` | UI principal de la plataforma |
| **Console Backend** | `rhinometric-console-backend` | `8105` | `8105` | API Gateway de la consola |
| **Grafana** | `rhinometric-grafana` | `3000` | `3000` | Dashboards y visualización |
| **Prometheus** | `rhinometric-prometheus` | `9090` | `9090` | Métricas y consultas PromQL |
| **Alertmanager** | `rhinometric-alertmanager` | `9093` | `9093` | Gestión de alertas |
| **Jaeger UI** | `rhinometric-jaeger` | `16686` | `16686` | Tracing distribuido |
| **Loki** | `rhinometric-loki` | `3100` | `3100` | Logs agregados |

**EXPORTERS - Deben cerrarse:**

| Servicio | Contenedor | Puerto | Función |
|----------|------------|--------|---------|
| Node Exporter | `rhinometric-node-exporter` | `9100` | Métricas del host |
| cAdvisor | `rhinometric-cadvisor` | `8080` | Métricas de contenedores |
| Postgres Exporter | `rhinometric-postgres-exporter` | `9187` | Métricas de base de datos |
| Blackbox Exporter | `rhinometric-blackbox-exporter` | `9115` | Pruebas de conectividad |

**SERVICIOS AUXILIARES - Deben cerrarse:**

| Servicio | Contenedor | Puerto | Función |
|----------|------------|--------|---------|
| License Server | `rhinometric-license-server-v2` | `5000` | Gestión de licencias |
| License UI | `rhinometric-license-ui` | `8093` | UI de administración de licencias |
| License Validator | `rhinometric-license-validator` | `8099` | Validación de licencias |
| AI Anomaly | `rhinometric-ai-anomaly` | `8085`, `9091` | Detección de anomalías con ML |
| API Connector | `rhinometric-api-connector` | `8000` | Conector de APIs externas |
| Dashboard Builder | `rhinometric-dashboard-builder` | `8001` | Constructor de dashboards |
| Report Generator | `rhinometric-report-generator` | `8086` | Generación de reportes |

**BASES DE DATOS - Deben cerrarse:**

| Servicio | Contenedor | Puerto | Función |
|----------|------------|--------|---------|
| PostgreSQL | `rhinometric-postgres` | `5432` | Base de datos principal |
| Redis | `rhinometric-redis` | `6379` | Cache y cola de mensajes |

**INFRAESTRUCTURA - Pueden mantenerse:**

| Servicio | Contenedor | Puerto | Función |
|----------|------------|--------|---------|
| OTEL Collector | `rhinometric-otel-collector` | `4317`, `4318` | Recolección de telemetría (gRPC/HTTP) |
| API Proxy | `rhinometric-api-proxy` | `8081` | Proxy de APIs (legacy) |

**YA EXISTE (No funcional actualmente):**

| Servicio | Contenedor | Puerto | Estado |
|----------|------------|--------|--------|
| **Nginx** | `rhinometric-nginx` | `80`, `443` | ⚠️ Presente pero no configurado correctamente |

---

## 🚨 Análisis de Riesgo Actual

### Exposición Crítica

**Total de puertos expuestos:** ~30+ puertos abiertos a 0.0.0.0

**Servicios con datos sensibles expuestos:**
- ✅ PostgreSQL (5432) → Base de datos con usuarios, licencias, configuración
- ✅ Redis (6379) → Cache con sesiones y datos temporales
- ✅ Prometheus (9090) → Todas las métricas del sistema (CPU, memoria, red)
- ✅ Grafana (3000) → Aunque con auth, exponer el puerto es innecesario
- ✅ Console Backend (8105) → API principal con endpoints de administración

**Vectores de ataque:**
1. **Ataque directo a bases de datos:** PostgreSQL y Redis sin autenticación obligatoria
2. **Scraping de métricas:** Prometheus expuesto permite recolectar información del sistema
3. **Surface attack amplia:** Cada puerto es un vector de ataque potencial
4. **DoS fácil:** Múltiples servicios expuestos facilitan ataques de denegación de servicio

### Configuración Actual de Grafana

```yaml
environment:
  GF_SERVER_ROOT_URL: https://app.rhinometric.com
  GF_SERVER_DOMAIN: app.rhinometric.com
  GF_SERVER_ENFORCE_DOMAIN: 'false'
  GF_AUTH_ANONYMOUS_ENABLED: 'false'  # ✅ Ya securizado en FASE 1
```

**Problema:** 
- `GF_SERVER_ROOT_URL` tiene dominio hardcodeado
- No está configurado para servir desde subpath `/grafana/`
- Esto **deberá ajustarse** en PASO 4

---

## 🎯 Estado Objetivo (Post-FASE 2)

### Exposición Externa

**Un solo puerto expuesto:**
```
0.0.0.0:80 → Nginx Reverse Proxy
```

**Servicios accesibles vía Nginx:**
```
http://IP_O_HOSTNAME/              → Console Frontend (3002)
http://IP_O_HOSTNAME/api/          → Console Backend (8105)
http://IP_O_HOSTNAME/grafana/      → Grafana (3000) [con Basic Auth]
```

**Servicios internos (Docker network only):**
- Prometheus, Alertmanager, Loki, Jaeger
- PostgreSQL, Redis
- Exporters (node, cadvisor, postgres, blackbox)
- Servicios auxiliares (AI, License, Reports)

### Configuración de Red Prevista

```yaml
# Nginx (único expuesto)
ports:
  - "80:80"

# Console Frontend (solo Docker network)
expose:
  - "3002"
# Sin ports: eliminado

# Console Backend (solo Docker network)
expose:
  - "8105"
# Sin ports: eliminado

# Grafana (solo Docker network)
expose:
  - "3000"
# Sin ports: eliminado

# Resto de servicios: NINGÚN port expuesto a host
```

---

## 📝 Servicios a Modificar (Resumen)

### Cambios en `docker-compose-v2.5.0.yml`

**Eliminar `ports:` y agregar `expose:` en:**

1. `rhinometric-console-frontend` (3002)
2. `rhinometric-console-backend` (8105)
3. `rhinometric-grafana` (3000)
4. `rhinometric-prometheus` (9090)
5. `rhinometric-alertmanager` (9093)
6. `rhinometric-jaeger` (16686, 14317)
7. `rhinometric-loki` (3100)
8. `rhinometric-node-exporter` (9100)
9. `rhinometric-cadvisor` (8080)
10. `rhinometric-postgres-exporter` (9187)
11. `rhinometric-blackbox-exporter` (9115)
12. `rhinometric-postgres` (5432)
13. `rhinometric-redis` (6379)
14. `rhinometric-license-server-v2` (5000)
15. `rhinometric-license-ui` (8093)
16. `rhinometric-license-validator` (8099)
17. `rhinometric-ai-anomaly` (8085, 9091)
18. `rhinometric-api-connector` (8000)
19. `rhinometric-dashboard-builder` (8001)
20. `rhinometric-report-generator` (8086)

**Excepción (mantener por ahora):**
- `rhinometric-otel-collector` (4317, 4318) - Para instrumentación externa
- `rhinometric-api-proxy` (8081) - Legacy, evaluar después

**Configurar correctamente:**
- `rhinometric-nginx` (80, 443) - Actualizar con config correcta

---

## 🔐 Configuración de Seguridad Prevista

### Basic Auth en Nginx

**Rutas protegidas con Basic Auth:**
- `/grafana/` → Usuario: `proxy-admin` / Password: (generada fuerte)

**Rutas sin Basic Auth (login propio de la app):**
- `/` → Console Frontend (tiene su propio login cuando se implemente RBAC)
- `/api/` → Console Backend (protegido por JWT tokens)

**Justificación:**
- Grafana ya tiene su propio login (admin/Rhino2026SecureAdmin)
- Basic Auth añade una capa adicional antes de llegar al login de Grafana
- Console no necesita doble auth (solo su propio sistema de usuarios)

### Credenciales de Basic Auth

**Ubicación:** `/opt/rhinometric/nginx/.htpasswd`  
**Usuario:** `proxy-admin`  
**Password:** (Se generará en PASO 3 con `htpasswd`)  
**Permisos:** `chmod 600`, `chown root:root`  
**Git:** ✅ **Añadido a .gitignore** (no commitear)

---

## 📊 Verificación del Estado Actual en VM

### Comando ejecutado en VM:

```bash
ssh rhinometric-restore "ss -tulpn | grep LISTEN"
```

**Resultado esperado:**
- Múltiples servicios escuchando en 0.0.0.0:PUERTO
- Confirmar que realmente todos los puertos están expuestos

### Docker Compose actual:

**Archivo:** `/opt/rhinometric/docker-compose-v2.5.0.yml`  
**Versión actual:** 2.5.0  
**Total de servicios:** 39 servicios definidos  
**Network:** `rhinometric_network_v22` (bridge, 172.22.0.0/16)

---

## 📦 Archivos a Crear/Modificar

### Archivos Nuevos

1. **nginx/nginx.conf**
   - Configuración principal de Nginx
   - Upstreams por nombre de servicio Docker
   - Location blocks para /, /api/, /grafana/
   - Headers correctos (X-Real-IP, X-Forwarded-For, etc.)
   - Configuración de websockets si es necesario

2. **nginx/.htpasswd**
   - Credenciales de Basic Auth
   - ⚠️ NO COMMITEAR (añadir a .gitignore)

3. **nginx/Dockerfile** (opcional)
   - Si necesitamos customizar la imagen de Nginx
   - Por ahora: usar `nginx:alpine` oficial

### Archivos a Modificar

1. **docker-compose-v2.5.0.yml**
   - Actualizar servicio `rhinometric-nginx`
   - Eliminar `ports:` de ~20 servicios
   - Agregar `expose:` donde sea necesario
   - Ajustar variables de Grafana (GF_SERVER_ROOT_URL, GF_SERVER_SERVE_FROM_SUB_PATH)

2. **.gitignore**
   - Añadir `nginx/.htpasswd`

---

## ⏭️ Próximos Pasos

**PASO 2:** Diseño detallado de la configuración de Nginx ✅ **COMPLETADO**  
**PASO 3:** Implementar cambios en docker-compose-v2.5.0.yml (EN CURSO)  
**PASO 4:** Ajustar configuración de Grafana para subpath `/grafana/`  
**PASO 5:** Despliegue controlado y pruebas  
**PASO 6:** Validación de seguridad y documentación final  

---

## 🎨 PASO 2: Diseño de Nginx (COMPLETADO)

### Arquitectura Implementada

**Nginx como Reverse Proxy:**
```
                    Internet
                       |
                    [:80] Nginx
                       |
        +--------------+---------------+
        |              |               |
    [3002]         [8105]           [3000]
  Frontend        Backend          Grafana
   Console         API              (Basic Auth)
```

### Configuración de Nginx

**Archivo creado:** `nginx/nginx.conf` (227 líneas)

#### Upstreams Definidos

```nginx
upstream console_frontend {
    server rhinometric-console-frontend:3002;
    keepalive 32;
}

upstream console_backend {
    server rhinometric-console-backend:8105;
    keepalive 32;
}

upstream grafana {
    server rhinometric-grafana:3000;
    keepalive 16;
}
```

**Nota clave:** Los upstreams usan nombres de servicio Docker, no IPs fijas. Esto hace la configuración:
- ✅ Agnóstica (funciona en cualquier entorno)
- ✅ Auto-resolvible por Docker DNS interno
- ✅ Resiliente a recreación de contenedores

#### Location Blocks

1. **`location /` - Console Frontend**
   - Sin autenticación (tendrá login propio con RBAC)
   - Websocket support habilitado
   - Timeouts: 60s
   - Buffering: ON

2. **`location /api/` - Console Backend**
   - Sin autenticación (protegido por JWT tokens)
   - Websocket support para SSE
   - Timeouts: 90s (APIs pueden tardar más)
   - Buffering: OFF (streaming)
   - **IMPORTANTE:** Path `/api/` se mantiene en el proxy_pass

3. **`location /grafana/` - Grafana con Basic Auth**
   - ✅ Basic Auth: `proxy-admin` / `aJtImXAwtoiGGGZan/CKfmalSl9wtNsQ`
   - Rewrite: `^/grafana/(.*) → /$1` (Grafana espera rutas desde /)
   - Header especial: `X-Forwarded-Prefix: /grafana`
   - Websocket support para live features
   - Timeouts: 120s (dashboards complejos)

4. **`location /grafana` - Redirect**
   - Redirect 301 a `/grafana/` (con trailing slash)
   - Necesario para que JS de Grafana funcione correctamente

5. **`location /nginx-health` - Health Check**
   - Endpoint simple para monitoring
   - Retorna HTTP 200 "healthy"

### Características de Seguridad

#### Headers HTTP

```nginx
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
X-Real-IP, X-Forwarded-For, X-Forwarded-Proto, etc.
```

#### Gzip Compression

- Habilitado para todos los tipos de contenido relevantes
- Nivel de compresión: 6 (balance performance/compresión)
- Reduce ancho de banda ~60-70%

#### Performance

- `sendfile on` - Transfer eficiente de archivos
- `tcp_nopush on` - Optimización de paquetes TCP
- `keepalive` connections en upstreams
- `worker_processes auto` - Usa todos los cores disponibles

### Basic Auth Implementation

**Archivos creados:**

1. **`nginx/.htpasswd`**
   ```
   proxy-admin:$apr1$sIOJfb7j$a9Xjf3VxEuyBeTJu/NRTs/
   ```
   - Hash: APR1 MD5 (compatible con Apache/Nginx)
   - ⚠️ **NO COMMITEADO** (añadido a .gitignore)

2. **`nginx/.htpasswd-password-temp.txt`**
   ```
   aJtImXAwtoiGGGZan/CKfmalSl9wtNsQ
   ```
   - Password en claro para referencia
   - ⚠️ **NO COMMITEADO** (añadido a .gitignore)
   - **Ubicación en VM:** `/opt/rhinometric/nginx/.htpasswd-password-temp.txt`

### Gestión de Contraseñas

**Usuario:** `proxy-admin`  
**Password:** `aJtImXAwtoiGGGZan/CKfmalSl9wtNsQ`  
**Uso:** Basic Auth para acceso a `/grafana/`

**Protección:**
- Archivo `.htpasswd` con permisos 600 en VM
- Password almacenada en archivo temporal local (no commitear)
- Hash irreversible en `.htpasswd`

### Websocket Support

Todas las rutas tienen configurado:

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

**Justificación:**
- Console Frontend: Puede usar websockets para updates en tiempo real
- Console Backend: SSE (Server-Sent Events) para streaming de alertas
- Grafana: Live features (dashboards auto-refresh, alertas en vivo)

### Logging

**Access log:** `/var/log/nginx/access.log`
- Formato: IP, user, timestamp, request, status, size, referer, user-agent
- Útil para debugging y auditoría

**Error log:** `/var/log/nginx/error.log`
- Nivel: `warn`
- Captura errores de proxy, timeouts, upstreams down

### Archivos Respaldados

- `nginx/nginx.conf.backup-20260129` - Configuración anterior (trial version)
- `nginx/ssl.conf` - SSL config (no se usa aún, futuro)
- `nginx/nginx.simple.conf` - Config simplificada (legacy)

### Validación Local

**Config correcta (sintaxis):**
```bash
# Se validará en VM al cargar el servicio
docker run --rm -v $(pwd)/nginx:/etc/nginx:ro nginx:alpine nginx -t
```

**Output esperado:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Decisiones de Diseño

**¿Por qué NO exponemos Prometheus/Alertmanager/Loki?**
- No son servicios de cara al usuario final
- Solo se acceden vía Grafana (con datasources internos)
- Reducir surface attack
- Si un admin los necesita, puede hacer SSH tunnel

**¿Por qué Basic Auth SOLO en Grafana?**
- Grafana ya tiene su propio login
- Basic Auth añade capa adicional sin molestar mucho
- Console tendrá su propio sistema de auth con RBAC (FASE 3)
- Backend API está protegido por JWT tokens

**¿Por qué no SSL aún?**
- Fase actual: cerrar perímetro primero
- SSL será FASE 2.5 (Let's Encrypt + Traefik o Certbot)
- Por ahora: HTTP en puerto 80 es suficiente para on-prem interno

---

## ⏭️ Próximos Pasos

**PASO 2:** Diseño detallado de la configuración de Nginx ✅ **COMPLETADO**  
**PASO 3:** Implementar cambios en docker-compose-v2.5.0.yml ✅ **COMPLETADO**  
**PASO 4:** Ajustar configuración de Grafana para subpath `/grafana/` ✅ **COMPLETADO**  
**PASO 5:** Despliegue controlado y pruebas (PENDIENTE)  
**PASO 6:** Validación de seguridad y documentación final (PENDIENTE)  

---

## 🔧 PASO 3: Modificación de docker-compose (COMPLETADO)

### Resumen de Cambios

**Total de servicios modificados:** 30+ servicios  
**Único puerto expuesto:** 80 (HTTP)  
**Método:** Cambio de `ports:` → `expose:` para todos los servicios excepto Nginx

### 3.A - Servicio Nginx Actualizado

```yaml
nginx:
  image: nginx:1.27-alpine
  container_name: rhinometric-nginx
  ports:
    - "80:80"  # Solo HTTP - SSL será en fase posterior
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/.htpasswd:/etc/nginx/.htpasswd:ro
    - ${HOME}/rhinometric_data_v2.2/nginx/logs:/var/log/nginx
  networks:
    - rhinometric_network_v22
  depends_on:
    rhinometric-console-frontend:
      condition: service_healthy
    rhinometric-console-backend:
      condition: service_healthy
    grafana:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:80/nginx-health"]
```

**Cambios:**
- ✅ Eliminado port 443 (no SSL en esta fase)
- ✅ Cambiada ruta de nginx.conf: `./nginx/nginx.conf` (antes `./nginx.conf`)
- ✅ Añadido volumen `.htpasswd` para Basic Auth
- ✅ Actualizado healthcheck: `/nginx-health` (endpoint custom)
- ✅ Añadidos depends_on: console-frontend, console-backend, grafana

### 3.B - Servicios Críticos Cerrados

#### PostgreSQL, Redis, Prometheus, Alertmanager, Loki

**Total:** 5 servicios críticos ahora SOLO accesibles internamente

```bash
# Verificación post-cambios:
grep -c "expose:" docker-compose-v2.5.0.yml
# Output: 46 (todos los servicios internos)

grep -c "ports:" docker-compose-v2.5.0.yml  
# Output: 1 (solo nginx puerto 80)
```

### 3.C - Aplicaciones Principales Cerradas

- ✅ **Grafana** (3000): Acceso vía `/grafana/` con Basic Auth
- ✅ **Console Backend** (8105): Acceso vía `/api/`
- ✅ **Console Frontend** (3002): Acceso vía `/`

### 3.D - Servicios Auxiliares Cerrados (30+ servicios)

**Método:** Script Python con regex para reemplazo masivo

```python
# Reemplazo automático de todos los ports: restantes
pattern = r'(\s+)ports:\s*\n((?:\s+[-\"] *\d+:\d+ *[\"]*\n)+)'
# Reemplazado por: expose: con los mismos puertos
```

**Servicios modificados incluyen:**
- License Server, License UI, License Validator
- Jaeger, OTEL Collector
- Node Exporter, cAdvisor, Blackbox, Postgres Exporter
- AI Anomaly, Report Generator
- Dashboard Builder, API Connector
- Todos los webhook collectors (9326-9330)
- Todos los database collectors (9332-9347)

---

## 🔐 PASO 4: Configuración Grafana Subpath (COMPLETADO)

### Cambios en Environment Variables

```yaml
# DESPUÉS (agnóstico + subpath):
GF_SERVER_ROOT_URL: "http://%(domain)s/grafana/"
GF_SERVER_SERVE_FROM_SUB_PATH: "true"
```

**Análisis:**
- `%(domain)s`: Variable de Grafana que se reemplaza con dominio/IP actual
- Funciona con: `http://89.167.15.73/grafana/` O `http://cualquier-hostname/grafana/`
- `SERVE_FROM_SUB_PATH=true`: Grafana ajusta URLs internas para `/grafana/`

**Compatibilidad con Nginx:**
```nginx
location /grafana/ {
    rewrite ^/grafana/(.*) /$1 break;  # Elimina /grafana/ antes de proxy
    proxy_set_header X-Forwarded-Prefix /grafana;  # Grafana sabe su subpath
}
```

---

## ⏭️ Próximos Pasos

**PASO 3:** Implementar cambios en docker-compose-v2.5.0.yml ✅ **COMPLETADO**  
**PASO 4:** Ajustar configuración de Grafana para subpath `/grafana/` ✅ **COMPLETADO**  

---

## 📌 Notas Importantes

### Lo que NO se hará en esta fase:

- ❌ NO se actualizarán URLs en templates de Alertmanager (eso es PASO 3 de FASE 2)
- ❌ NO se implementará SSL/Let's Encrypt (futuro)
- ❌ NO se tocará correlación de trace_id (deuda técnica)
- ❌ NO se implementará RBAC completo (FASE 3)

### Lo que SÍ se hará:

- ✅ Cerrar todos los puertos innecesarios
- ✅ Nginx como único punto de entrada
- ✅ Configuración agnóstica (funciona con IP o hostname)
- ✅ Basic Auth opcional en rutas sensibles
- ✅ Preparar base para futuras mejoras

---

**Documento creado por:** Rafael Canelón  
**Fecha:** 29 de enero de 2026  
**Versión:** 1.0 - Estado Inicial Analizado
