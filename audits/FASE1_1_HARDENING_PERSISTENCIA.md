# FASE 1.1 — Hardening Persistencia

**Fecha:** 2026-02-13T12:36:22Z
**Servidor:** rhinometric-prod (89.167.22.228)
**Ejecutado por:** Copilot (asistido)
**Objetivo:** Hacer permanentes los cambios de hardening de la Fase 1, incorporandolos en el codigo fuente en disco y en las imagenes Docker.

---

## 1. Contexto

La Fase 1 aplico hardening de seguridad via `docker cp`, lo que significaba que un `docker-compose up --force-recreate` o la eliminacion del contenedor revertia todos los cambios. Esta Fase 1.1 convierte esos parches temporales en cambios permanentes horneados en las imagenes Docker.

---

## 2. Archivos Modificados en el Host

| Archivo | Ruta en Host | Cambio Aplicado |
|---------|-------------|-----------------|
| logs.py | `rhinometric-console/backend/routers/logs.py` | Auth habilitada: `Depends(get_current_user)` en endpoint GET |
| traces.py | `rhinometric-console/backend/routers/traces.py` | Auth habilitada en AMBOS endpoints (GET / y GET /services) |
| auth.py | `rhinometric-console/backend/routers/auth.py` | Backdoor `DISABLE_AUTH` eliminado; `asyncio.sleep(0.5)` en fallos de login |
| main.py | `rhinometric-console/backend/main.py` | Endpoint `/debug-headers` eliminado |
| config.py | `rhinometric-console/backend/config.py` | JWT expiry reducido de 30 dias a 24 horas (`60 * 24`) |
| nginx.conf | `nginx/nginx.conf` | HSTS header, bloque HTTPS preparado (comentado), server_name configurado |

---

## 3. Verificacion de Integridad (Host vs Contenedor)

Todos los archivos verificados con MD5 — **identicos** entre host y contenedor:

| Archivo | MD5 |
|---------|-----|
| logs.py | `5431cd70fbb550201e35b172caf3130a` |
| traces.py | `6908ce52a618916d66312c0625a0f0f2` |
| auth.py | `ee5026d1db762036241886ccfc750e75` |
| main.py | `747b4e72fb961b8f0a7803471657b1b0` |
| config.py | `c60a3ec30204c65b4cde00ca66aa3a31` |
| nginx.conf | `dfe6d8affdadf4ef79f1cb808bab69a0` |

---

## 4. Imagenes Docker

### Imagen Anterior (conservada para rollback)
- **Nombre:** `rhinometric-rhinometric-console-backend:latest`
- **ID:** `a156a7223b43`
- **Tamano:** 263MB

### Imagen Nueva (en produccion)
- **Nombre:** `rhinometric-console-backend:v2.5.1-hardened`
- **ID:** `479887f1d312`
- **Build context:** `./rhinometric-console/backend/`
- **Base:** python:3.11-slim

### Nginx
No requiere rebuild — usa bind mount (`./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`).
Los cambios en el host se reflejan directamente en el contenedor.

---

## 5. Docker Compose

- **Archivo activo:** `docker-compose.yml` -> symlink a `docker-compose-v2.5.0-SECURE.yml`
- **Cambio aplicado:** Servicio `rhinometric-console-backend` ahora declara:

```
image: rhinometric-console-backend:v2.5.1-hardened
build:
  context: ./rhinometric-console/backend/
  dockerfile: Dockerfile
```

- **Validacion:** `docker-compose config --quiet` -> exit 0

---

## 6. Validacion Post-Despliegue

### Test 1: Autenticacion (endpoints sin token)
| Endpoint | Codigo HTTP | Resultado |
|----------|-------------|-----------|
| /api/logs | 401 | PASS |
| /api/traces | 401 | PASS |
| /api/traces/services | 401 | PASS |

### Test 2: Codigo Hardened en Imagen
| Verificacion | Esperado | Obtenido | Resultado |
|-------------|----------|----------|-----------|
| DISABLE_AUTH en /app/ | 0 ocurrencias | 0 | PASS |
| debug-headers en /app/ | 0 ocurrencias | 0 | PASS |
| asyncio.sleep en auth.py | 2 ocurrencias | 2 | PASS |
| JWT expiry | 60 * 24 (24h) | 60 * 24 | PASS |

### Test 3: Servicios Funcionales
| Servicio | Resultado |
|----------|-----------|
| Frontend (HTTP 200) | PASS |
| Grafana embedded (HTTP 200) | PASS |
| Contenedores healthy | 15/15 PASS |

### Test 4: Supervivencia a Force-Recreate
- **Comando:** `docker-compose up -d --force-recreate rhinometric-console-backend`
- **Resultado:** Todos los tests anteriores PASAN tras force-recreate
- **Conclusion:** **Ya no dependemos de `docker cp` para mantener el hardening**

---

## 7. Procedimiento de Rollback

Si es necesario revertir al estado pre-hardening:

1. Editar `docker-compose.yml` y cambiar `image:` a `rhinometric-rhinometric-console-backend:latest`
2. Ejecutar: `docker-compose up -d rhinometric-console-backend`
3. Verificar: `docker inspect rhinometric-console-backend | grep Image`

La imagen anterior `a156a7223b43` permanece en disco como respaldo.

---

## 8. Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| Codigo fuente en disco | Hardened permanentemente |
| Imagen Docker backend | `v2.5.1-hardened` (479887f1d312) |
| Compose actualizado | Si, con tag explicito |
| Supervive force-recreate | Si, verificado |
| Rollback disponible | Si, imagen antigua conservada |
| Dependencia de docker cp | **ELIMINADA** |

> **El hardening de la Fase 1 ha dejado de ser "pegado con cinta" y ahora esta horneado en las imagenes y el repositorio.**
