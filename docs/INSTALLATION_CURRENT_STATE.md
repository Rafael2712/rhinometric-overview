# INSTALLATION CURRENT STATE
## Rhinometric On-Premise — Inventario real al 25 Feb 2026

---

## A. What Exists (Artefactos de instalación)

### Instaladores encontrados (6 variantes, ninguno canónico)

| Archivo | Líneas | Estado | Notas |
|---------|--------|--------|-------|
| `/install-rhinometric.sh` | 401 | **Más completo** | Checks OS/RAM/disk/docker/ports, genera .env, copia compose, levanta stack, smoke test básico. Referencia `docker-compose-v2.5.0-core.yml` (no el SECURE activo). NO idempotente. |
| `/dist/install.sh` | 67 | Minimalista | Single-container approach (`docker run`), NO compose. Solo Grafana. Obsoleto. |
| `/dist/install-secure.sh` | ~30 | Stub | Wrapper mínimo. |
| `/dist/install-client.sh` | ~20 | Stub | Wrapper mínimo. |
| `/rhinometric-v2.5.0-release/scripts/install-rhinometric.sh` | 401 | **Copia idéntica** de `/install-rhinometric.sh` | Duplicado. |
| `/installers/install.sh` | ? | Otro variante | No inspeccionado en detalle. |

### Control CLI

| Archivo | Tipo | Estado |
|---------|------|--------|
| `/scripts/rmetricctl` | Python 3 | Backup/management CLI v2.2.0. Funcional pero apunta a `rhinometric_data_v2.2` (path obsoleto, producción usa `v2.5`). |

### Docker Compose files activos

| Archivo | Estado |
|---------|--------|
| `docker-compose-v2.5.0-SECURE.yml` | **ACTIVO** — symlinked desde `docker-compose.yml`. 21 servicios definidos. |
| `docker-compose-v2.5.0-PRODUCTION.yml` | Alternativo |
| `docker-compose-v2.5.0-LICENSE-SERVER.yml` | Solo license server |

Hay **30+ compose files** adicionales en `/archive/`, `/infrastructure/docker/`, `/config/`, etc. Todos legacy o experimentales.

### Env files

| Archivo | Propósito |
|---------|-----------|
| `.env` | **Activo** — 17 variables (POSTGRES, REDIS, GRAFANA, SECRET_KEY, ADMIN, SMTP, PUBLIC_IP, CUSTOMER_DOMAIN). Valores reales presentes. `chmod 600`. |
| `.env.template` | Template v2.6.0 con comentarios. **Bueno.** Variables documentadas con instrucciones de generación. |
| `.env.example` | Template legacy — solo 3 vars (POSTGRES, PGBOUNCER, GRAFANA) + tier config. Incompleto. |
| `.env.production` | 3 líneas. Stub. |
| `.env.license` | 1 línea. |
| `.env.alertmanager` | Alertmanager específico (MAIL_FROM, SLACK_WEBHOOK). |
| `.env.alertmanager.template` | Template para alertmanager. |
| `backend/.env.example` | Backend específico. |

### Fingerprint / License

| Archivo | Propósito |
|---------|-----------|
| `rhinometric-licensing/scripts/get-hwid.sh` | **Script funcional** — genera HWID basado en CPU+MAC+hostname → SHA256 truncado a 16 chars. Cross-platform (Linux/macOS/Windows). |
| `license.key` | JSON payload con `tenant_id`, `version`, `signature`. Activo en producción. |
| `licenses/license.key` | Copia/alternativa. |
| `rust-licenses/src/fingerprint.rs` | Rust implementation del fingerprint (usado por license-admin en Lightsail). |

### Docs existentes

| Archivo | Líneas | Relevancia |
|---------|--------|-----------|
| `docs/RHINOMETRIC_V26_INSTALLATION_AND_LICENSE_DESIGN.md` | ~1300 | Diseño detallado del sistema de instalación+licencia. **Referencia clave.** |
| `docs/PROVISIONING_GUIDE.md` | ~250 | Guía de provisioning. |
| `docs/DEPLOYMENT_TRIAL_SELFSERVICE.md` | ~300 | Trial self-service flow. |
| `rhinometric-v2.5.0-release/docs/INSTALLATION_GUIDE.md` | ? | Guía v2.5.0 release. |
| `dashboard-studio/QUICKSTART.md` | ~50 | Solo para dashboard-studio. |

### Health check scripts

| Archivo | Propósito |
|---------|-----------|
| `check-health.sh` | Curl a 6 endpoints (Grafana, Prometheus, Loki, Tempo, Alertmanager, License Dashboard). Referencia puertos obsoletos. |
| `check_status.sh` | Similar. |
| `quick-health-check.sh` | Similar. |
| `verify-all-services.sh` | Similar. |
| `validate-stack.sh` | Similar. |

---

## B. Current Steps (Proceso manual de instalación HOY)

### Flujo real observado en producción (89.167.22.228):

1. **Provision VM** — Ubuntu 22/24, SSH access, min 8GB RAM, 150GB+ disk.
2. **Install Docker** — `curl -fsSL https://get.docker.com | sh`
3. **Clone repo** — `git clone` del repo `mi-proyecto` a `/opt/rhinometric`
4. **Create `.env`** — Copia manual de `.env.template`, relleno de passwords con `openssl rand -base64 24`
5. **Select compose file** — Symlink `docker-compose.yml → docker-compose-v2.5.0-SECURE.yml`
6. **Build images** — `docker-compose build` (console-backend, console-frontend, license-server-v2, ai-anomaly se compilan localmente)
7. **Start stack** — `docker-compose up -d` (o `docker-compose up -d --scale license-ui=0` porque license-ui falla el build)
8. **Wait + verify** — Esperar ~2 minutos, `docker ps` para verificar containers healthy
9. **Generate fingerprint** — `bash rhinometric-licensing/scripts/get-hwid.sh` → obtener HWID
10. **Request license** — Enviar HWID por email a licenses@rhinometric.com
11. **Apply license** — Copiar archivo `.lic`/`.key` recibido a `/opt/rhinometric/license.key`
12. **Restart** — `docker-compose restart console-backend`

### Pasos NO documentados (se hacen ad-hoc):
- Configurar nginx (reverse proxy) — se hace manualmente
- Setup Cloudflare/DNS — manual
- Configurar alertmanager notifications — manual
- Import Grafana dashboards — manual con scripts separados
- Setup cron backups — manual

---

## C. Known Failure Points (Puntos frágiles)

### 1. Build failures (CRÍTICO)
- `license-ui` **no compila** — falta imagen o Dockerfile roto. Producción usa `--scale license-ui=0`.
- Builds locales dependen de `npm install`/`pip install` con acceso a internet. Si la red falla, la instalación falla.
- No hay imágenes pre-built en ningún registry.

### 2. Compose file confusion (ALTO)
- 30+ compose files. No hay uno canónico claro.
- El activo (`docker-compose-v2.5.0-SECURE.yml`) está symlinked manualmente.
- El instalador `install-rhinometric.sh` referencia `docker-compose-v2.5.0-core.yml` (diferente al activo).

### 3. Idempotencia inexistente (ALTO)
- Correr el instalador 2 veces SOBREESCRIBE `.env` (pierde passwords generadas).
- No detecta instalación previa ni containers running.
- `check_ports` falla si los propios containers ya están corriendo.

### 4. ENV inconsistency (MEDIO)
- `.env.template` tiene 17 vars, `.env.example` tiene 3, el instalador genera solo 5.
- `SECRET_KEY`, `PUBLIC_IP`, `CUSTOMER_DOMAIN`, `ADMIN_USERNAME` no se generan en el instalador.
- La app necesita todas las vars de `.env.template` para funcionar correctamente.

### 5. Data path hardcoded (MEDIO)
- Compose usa `${HOME}/rhinometric_data_v2.5/` para volúmenes.
- Si `HOME` no está en `.env`, Docker Compose expande a la home del usuario que ejecuta.
- `rmetricctl` apunta a `rhinometric_data_v2.2` (path stale).

### 6. Health checks insuficientes (MENOR)
- El instalador espera 60s con `sleep 60` en lugar de polling real.
- `check-health.sh` referencia Tempo (no está activo) y puertos obsoletos.
- No verifica endpoints de backend (`/api/health`) ni frontend.

### 7. License flow manual (MENOR pero friccional)
- No hay activación automática.
- Email humano en el loop.
- No hay validación de que el license.key aplicado sea válido.

---

## D. Assumptions / Prerequisites

### OS Requirements
- Ubuntu 22.04 o 24.04 (producción usa 24.04)
- Debian 12 probablemente funciona pero no testeado

### System Requirements (observados en producción)
| Recurso | Mínimo | Recomendado | Producción actual |
|---------|--------|-------------|-------------------|
| CPU | 4 cores | 8 cores | 8 cores (Hetzner CCX33) |
| RAM | 8 GB | 16 GB | 16 GB |
| Disk | 150 GB | 200+ GB | 400 GB (22% usado) |

### Software Dependencies
| Dependency | Required | Check command |
|------------|----------|---------------|
| Docker Engine | ≥20.10 | `docker --version` |
| Docker Compose v2 | ≥2.20 | `docker compose version` |
| curl | any | `command -v curl` |
| openssl | any | `command -v openssl` |
| jq | any | `command -v jq` |
| git | any (for clone) | `command -v git` |

### Network Requirements
- Puertos usados: 80, 443 (nginx), 3000 (grafana), 5432 (postgres), 6379 (redis), 8105 (backend), 9090 (prometheus), 9093 (alertmanager), 16686 (jaeger), 3100 (loki), 5000 (license-server)
- Acceso a Docker Hub para pull de imágenes base (postgres, redis, grafana, prometheus, etc.)
- Acceso a npm/pip registries si se buildean imágenes localmente

### Data Directories (created by compose)
```
${HOME}/rhinometric_data_v2.5/
├── ai-anomaly/{models,data}
├── alertmanager/
├── blackbox/
├── console-backend/{logs,data}
├── jaeger/
├── license-server/logs
├── loki/
├── postgres/
└── redis/
```

### Container inventory (21 services in compose, 20 running)
```
rhinometric-postgres          (postgres:15.10-alpine)
rhinometric-redis             (redis)
rhinometric-grafana           (grafana)
rhinometric-prometheus        (prometheus)
rhinometric-loki              (loki)
rhinometric-jaeger            (jaeger)
rhinometric-alertmanager      (alertmanager)
rhinometric-nginx             (nginx)
rhinometric-console-backend   (local build)
rhinometric-console-frontend  (local build)
rhinometric-license-server-v2 (local build)
rhinometric-ai-anomaly        (local build)
rhinometric-otel-collector    (otel)
rhinometric-promtail          (promtail)
rhinometric-node-exporter     (node-exporter)
rhinometric-cadvisor          (cadvisor)
rhinometric-blackbox-exporter (blackbox)
rhinometric-postgres-exporter (postgres-exporter)
rhinometric-redis-exporter    (redis-exporter)
rhinometric-victoria-metrics  (victoria-metrics)
rhinometric-license-ui        (local build — BROKEN, excluded)
```

---

*Documento generado: 25 Febrero 2026 — FASE 1 inventario completado*
