# ============================================================================
# RHINOMETRIC v2.5.0 CORE - HEALTH CHECK VALIDATION MATRIX
# ============================================================================
# Use esta matriz para validar que todos los servicios core están operativos
# Ejecutar después de: docker compose -f docker-compose-v2.5.0-core.yml up -d
# ============================================================================

## SERVICIOS CORE (17 servicios obligatorios)

### 1. DATABASES & CACHE (2 servicios)

| # | Servicio | Puerto | Endpoint | Comando de Prueba | Resultado Esperado |
|---|----------|--------|----------|-------------------|-------------------|
| 1 | postgres | 5432 | N/A (TCP) | `docker exec rhinometric-postgres pg_isready -U rhinometric` | `accepting connections` |
| 2 | redis | 6379 | N/A (TCP) | `docker exec rhinometric-redis redis-cli --raw incr ping` | `(integer) 1` o mayor |

**Validación rápida:**
```bash
docker exec rhinometric-postgres pg_isready -U rhinometric
docker exec rhinometric-redis redis-cli --raw incr ping
```

---

### 2. LICENSE MANAGEMENT (1 servicio)

| # | Servicio | Puerto | Endpoint | Comando de Prueba | Resultado Esperado |
|---|----------|--------|----------|-------------------|-------------------|
| 3 | license-server-v2 | 5000 | `/api/health` | `curl -s http://localhost:5000/api/health` | HTTP 200 + JSON `{"status":"ok"}` o similar |

**Validación rápida:**
```bash
curl -s http://localhost:5000/api/health | jq .
```

---

### 3. OBSERVABILITY CORE (7 servicios)

| # | Servicio | Puerto | Endpoint | Comando de Prueba | Resultado Esperado |
|---|----------|--------|----------|-------------------|-------------------|
| 4 | prometheus | 9090 | `/-/healthy` | `curl -s http://localhost:9090/-/healthy` | HTTP 200 + `Prometheus is Healthy.` |
| 5 | loki | 3100 | `/ready` | `curl -s http://localhost:3100/ready` | HTTP 200 + `ready` |
| 6 | jaeger | 16686 | `/` | `curl -s -o /dev/null -w "%{http_code}" http://localhost:16686` | HTTP 200 |
| 7 | grafana | 3000 | `/api/health` | `curl -s http://localhost:3000/api/health` | HTTP 200 + JSON `{"database":"ok"}` |
| 8 | otel-collector | 4317 | N/A (gRPC) | `docker logs rhinometric-otel-collector 2>&1 \| grep -i "Everything is ready"` | Log con "Everything is ready" |
| 9 | promtail | N/A | `/` (version) | `docker exec rhinometric-promtail promtail --version` | Versión `promtail, version 3.0.0` |
| 10 | alertmanager | 9093 | `/-/healthy` | `curl -s http://localhost:9093/-/healthy` | HTTP 200 + `OK` |

**Validación rápida:**
```bash
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:3100/ready
curl -s http://localhost:16686 -o /dev/null -w "Jaeger: %{http_code}\n"
curl -s http://localhost:3000/api/health | jq .
curl -s http://localhost:9093/-/healthy
```

---

### 4. EXPORTERS (2 servicios)

| # | Servicio | Puerto | Endpoint | Comando de Prueba | Resultado Esperado |
|---|----------|--------|----------|-------------------|-------------------|
| 11 | node-exporter | 9100 | `/metrics` | `curl -s http://localhost:9100/metrics \| head -5` | Métricas Prometheus (texto plano) |
| 12 | cadvisor | 8080 | `/metrics` | `curl -s http://localhost:8080/metrics \| head -5` | Métricas Prometheus (texto plano) |

**Validación rápida:**
```bash
curl -s http://localhost:9100/metrics | head -5
curl -s http://localhost:8080/metrics | head -5
```

---

### 5. AI ANOMALY DETECTION (1 servicio)

| # | Servicio | Puerto | Endpoint | Comando de Prueba | Resultado Esperado |
|---|----------|--------|----------|-------------------|-------------------|
| 13 | rhinometric-ai-anomaly | 8085 | `/health` | `curl -s http://localhost:8085/health` | HTTP 200 + JSON `{"status":"healthy"}` o similar |

**Validación rápida:**
```bash
curl -s http://localhost:8085/health | jq .
```

---

### 6. RHINOMETRIC CONSOLE - UI PRINCIPAL (2 servicios)

| # | Servicio | Puerto | Endpoint | Comando de Prueba | Resultado Esperado |
|---|----------|--------|----------|-------------------|-------------------|
| 14 | rhinometric-console-backend | 8105 | `/health` | `curl -s http://localhost:8105/health` | HTTP 200 + JSON con `{"status":"ok"}` o similar |
| 15 | rhinometric-console-frontend | 3002 | `/health` o `/` | `curl -s -o /dev/null -w "%{http_code}" http://localhost:3002` | HTTP 200 |

**Validación rápida:**
```bash
curl -s http://localhost:8105/health | jq .
curl -s http://localhost:3002 -o /dev/null -w "Frontend UI: %{http_code}\n"
```

**⚠️ IMPORTANTE:** El frontend en puerto 3002 es la **UI PRINCIPAL** de Rhinometric. Debe ser accesible vía navegador en `http://localhost:3002` o `http://<server-ip>:3002`.

---

### 7. INFRASTRUCTURE (1 servicio)

| # | Servicio | Puerto | Endpoint | Comando de Prueba | Resultado Esperado |
|---|----------|--------|----------|-------------------|-------------------|
| 16 | nginx | 80 | `/health` | `curl -s http://localhost/health` | HTTP 200 + `healthy` |

**Validación rápida:**
```bash
curl -s http://localhost/health
```

**Rutas de Nginx (reverse proxy):**
- `/` → rhinometric-console-frontend (3002) - **UI PRINCIPAL**
- `/grafana` → Grafana (3000)
- `/api/console` → Console Backend (8105)
- `/api/license` → License Server (5000)
- `/jaeger` → Jaeger UI (16686)
- `/prometheus` → Prometheus UI (9090)
- `/api/ai` → AI Anomaly (8085)

**Prueba de routing:**
```bash
curl -s http://localhost/ -o /dev/null -w "Nginx → Frontend: %{http_code}\n"
curl -s http://localhost/grafana -o /dev/null -w "Nginx → Grafana: %{http_code}\n"
curl -s http://localhost/api/console/health -o /dev/null -w "Nginx → Console API: %{http_code}\n"
```

---

### 8. BACKUP (1 servicio)

| # | Servicio | Puerto | Endpoint | Comando de Prueba | Resultado Esperado |
|---|----------|--------|----------|-------------------|-------------------|
| 17 | rhinometric-backup | N/A | N/A (cron job) | `docker logs rhinometric-backup 2>&1 \| tail -20` | Logs sin errores críticos |

**Validación rápida:**
```bash
docker logs rhinometric-backup --tail 20
```

---

## SCRIPT DE VALIDACIÓN AUTOMÁTICA

Copiar y ejecutar después de `docker compose up -d`:

```bash
#!/bin/bash
# validate-rhinometric-core.sh

echo "============================================================================"
echo " RHINOMETRIC v2.5.0 CORE - HEALTH CHECK VALIDATION"
echo "============================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0
PASSED=0

check_service() {
    local name=$1
    local test_cmd=$2
    local expected=$3
    
    echo -n "Checking $name... "
    
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi
}

echo "1. DATABASES & CACHE"
check_service "PostgreSQL" "docker exec rhinometric-postgres pg_isready -U rhinometric" "accepting connections"
check_service "Redis" "docker exec rhinometric-redis redis-cli --raw incr ping" "integer"
echo ""

echo "2. LICENSE MANAGEMENT"
check_service "License Server" "curl -sf http://localhost:5000/api/health" "200"
echo ""

echo "3. OBSERVABILITY CORE"
check_service "Prometheus" "curl -sf http://localhost:9090/-/healthy" "200"
check_service "Loki" "curl -sf http://localhost:3100/ready" "200"
check_service "Jaeger" "curl -sf http://localhost:16686" "200"
check_service "Grafana" "curl -sf http://localhost:3000/api/health" "200"
check_service "Alertmanager" "curl -sf http://localhost:9093/-/healthy" "200"
check_service "OTEL Collector" "docker ps --filter name=rhinometric-otel-collector --filter health=healthy --format '{{.Names}}'" "otel"
check_service "Promtail" "docker ps --filter name=rhinometric-promtail --filter health=healthy --format '{{.Names}}'" "promtail"
echo ""

echo "4. EXPORTERS"
check_service "Node Exporter" "curl -sf http://localhost:9100/metrics | head -1" "200"
check_service "cAdvisor" "curl -sf http://localhost:8080/metrics | head -1" "200"
echo ""

echo "5. AI ANOMALY DETECTION"
check_service "AI Anomaly" "curl -sf http://localhost:8085/health" "200"
echo ""

echo "6. RHINOMETRIC CONSOLE (UI PRINCIPAL)"
check_service "Console Backend" "curl -sf http://localhost:8105/health" "200"
check_service "Console Frontend (3002)" "curl -sf http://localhost:3002" "200"
echo ""

echo "7. INFRASTRUCTURE"
check_service "Nginx" "curl -sf http://localhost/health" "200"
echo ""

echo "8. BACKUP"
check_service "Backup Service" "docker ps --filter name=rhinometric-backup --format '{{.Names}}'" "backup"
echo ""

echo "============================================================================"
echo " SUMMARY"
echo "============================================================================"
echo -e "${GREEN}PASSED: $PASSED${NC}"
echo -e "${RED}FAILED: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL SERVICES HEALTHY - Stack is ready for production${NC}"
    echo ""
    echo "Access points:"
    echo "  - Rhinometric Console UI: http://localhost:3002 (PRINCIPAL)"
    echo "  - Grafana: http://localhost/grafana"
    echo "  - Jaeger: http://localhost/jaeger"
    echo "  - Prometheus: http://localhost/prometheus"
    exit 0
else
    echo -e "${RED}✗ SOME SERVICES FAILED - Check logs with 'docker compose logs <service>'${NC}"
    exit 1
fi
```

**Guardar como:** `validate-rhinometric-core.sh`

**Ejecutar:**
```bash
chmod +x validate-rhinometric-core.sh
./validate-rhinometric-core.sh
```

---

## TROUBLESHOOTING

### Servicio no healthy después de 5 minutos:

```bash
# Ver logs del servicio
docker logs <container-name>

# Ver últimas 50 líneas
docker logs <container-name> --tail 50

# Seguir logs en tiempo real
docker logs <container-name> -f
```

### PostgreSQL no acepta conexiones:
```bash
docker logs rhinometric-postgres
docker exec rhinometric-postgres pg_isready -U rhinometric
```

### Grafana no arranca:
```bash
docker logs rhinometric-grafana
# Verificar permisos de volumen
ls -la ~/rhinometric_data_v2.2/grafana
```

### Frontend 3002 no responde:
```bash
docker logs rhinometric-console-frontend
# Verificar que el backend está healthy primero
curl -s http://localhost:8105/health
```

### Nginx no rutea correctamente:
```bash
docker logs rhinometric-nginx
# Verificar configuración
docker exec rhinometric-nginx nginx -t
```

---

## CRITERIOS DE ÉXITO PARA PRODUCCIÓN

El stack está listo para vender cuando:

- ✅ **17/17 servicios** están en estado `healthy`
- ✅ **Frontend 3002** es accesible vía navegador
- ✅ **Nginx** rutea correctamente todas las URLs
- ✅ **Grafana** carga dashboards
- ✅ **Prometheus** scraping activo (targets UP)
- ✅ **Loki** recibe logs de Promtail
- ✅ **Jaeger** recibe trazas de OTEL
- ✅ **AI Anomaly** conecta con Prometheus
- ✅ **Console Backend** autentica usuarios
- ✅ **License Server** valida licencias

**Estado esperado:**
```
$ docker compose -f docker-compose-v2.5.0-core.yml ps
NAME                                     STATUS
rhinometric-alertmanager                 Up (healthy)
rhinometric-ai-anomaly                   Up (healthy)
rhinometric-cadvisor                     Up
rhinometric-console-backend              Up (healthy)
rhinometric-console-frontend             Up (healthy)
rhinometric-grafana                      Up (healthy)
rhinometric-jaeger                       Up (healthy)
rhinometric-license-server-v2            Up (healthy)
rhinometric-loki                         Up (healthy)
rhinometric-nginx                        Up (healthy)
rhinometric-node-exporter                Up (healthy)
rhinometric-otel-collector               Up (healthy)
rhinometric-postgres                     Up (healthy)
rhinometric-prometheus                   Up (healthy)
rhinometric-promtail                     Up (healthy)
rhinometric-redis                        Up (healthy)
rhinometric-backup                       Up
```
