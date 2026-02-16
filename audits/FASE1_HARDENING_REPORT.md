# Fase 1 -- Hardening Minimo + Empaquetado Single-Tenant
## Rhinometric Platform -- 12 febrero 2026

## 1. Resumen Ejecutivo

Se ha completado el hardening minimo de la plataforma para dejarla en estado seguro
para un piloto pagado. Todos los cambios son controlados y reversibles.

**Estado final: APROBADO para piloto pagado**

## 2. Cambios Aplicados

### 2.1 Auth en endpoints desprotegidos

- GET /api/logs: Auth habilitado (antes comentado for debugging) - logs.py
- GET /api/traces: Auth habilitado (antes comentado for debugging) - traces.py
- GET /api/traces/services: Auth habilitado (nunca tuvo auth) - traces.py
- GET /api/grafana/*: Ya tenia JWT inline, sin cambios

### 2.2 Endpoint debug eliminado

- GET /debug-headers: ELIMINADO de main.py (filtraba headers incluyendo tokens JWT)

### 2.3 Backdoor DISABLE_AUTH eliminado

- Eliminado bloque completo de 13 lineas en routers/auth.py
- Permitia bypass total de autenticacion con DISABLE_AUTH=true

### 2.4 Login hardening

- asyncio.sleep(0.5) en ambos caminos de fallo (user not found + wrong password)
- JWT expiry reducido de 30 dias a 24 horas
- Rate limiting nginx ya existia: 5 req/min en /api/(login|auth|register)

### 2.5 Puertos bloqueados

- Puerto 8428 (Victoria Metrics): 0.0.0.0 -> 127.0.0.1
- Puerto 9115 (Blackbox Exporter): 0.0.0.0 -> 127.0.0.1
- Puerto 80 (Nginx): sin cambios (entry point publico)

### 2.6 Nginx HTTPS-ready

- Backup: nginx/nginx.conf.bak.20260212
- Header HSTS preparado (comentado, se activa con HTTPS)
- Bloque servidor HTTPS completo (comentado con instrucciones)
- server_name console.rhinometric.com ya configurado

### 2.7 Docker Compose consolidado

- Nginx integrado en docker-compose-v2.5.0-SECURE.yml
- 8 compose legacy archivados a archive/compose-legacy/

## 3. Validacion

- Backend /health: 200 OK
- Frontend /: 200 OK
- /api/logs sin token: 401
- /api/traces sin token: 401
- /api/traces/services sin token: 401
- /debug-headers: Eliminado
- DISABLE_AUTH en codigo: 0 ocurrencias
- asyncio.sleep en login: 2 ocurrencias
- JWT expiry: 24 horas
- Puerto 8428 externo: connection refused
- Puerto 9115 externo: connection refused
- Puerto 8428 localhost: 200 OK
- Puerto 9115 localhost: 200 OK
- Containers healthy: 14
- Nginx config test: syntax ok

## 4. Archivos Modificados

- routers/logs.py: Auth habilitado en GET
- routers/traces.py: Auth habilitado en GET y GET /services
- routers/auth.py: DISABLE_AUTH eliminado + asyncio.sleep + import asyncio
- main.py: /debug-headers eliminado
- config.py: JWT 60*24 (24h)
- nginx/nginx.conf: HSTS + HTTPS-ready block
- docker-compose-v2.5.0-SECURE.yml: Ports 127.0.0.1 + nginx service

## 5. Lo que NO se toco (por diseno)

- RBAC (no refactor profundo)
- Esquema de BBDD
- License Server (no rewrite a Rust)
- Features nuevas
- Grafana proxy logica interna

## 6. Proximos pasos recomendados

1. HTTPS: Obtener certificado SSL y activar bloque en nginx.conf
2. Cambiar password admin (sigue siendo admin)
3. SECRET_KEY: Generar key aleatoria real
4. RBAC: Activar role check en PUT /ai-alerts (settings.py)
5. Reconstruir imagen Docker para cambios permanentes
