#!/bin/bash
set -eo pipefail

# ============================================
# RHINOMETRIC v2.5.0 - Production Verification
# ============================================
# Verifica que TODA la infraestructura de producción esté operativa

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
PASSED=0
FAILED=0
WARNINGS=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; PASSED=$((PASSED + 1)); }
log_error() { echo -e "${RED}[✗]${NC} $1"; FAILED=$((FAILED + 1)); }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; WARNINGS=$((WARNINGS + 1)); }

echo "╔════════════════════════════════════════════════════════╗"
echo "║  RHINOMETRIC PRODUCTION VERIFICATION v2.5.0           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# ============================================
# 1. VERIFICACIÓN DE SERVICIOS DOCKER
# ============================================
log_info "═══ 1. Docker Services Health ═══"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose-prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Missing $COMPOSE_FILE"
    exit 1
fi

SERVICES=(
    "rhinometric-traefik-prod:traefik"
    "rhinometric-prometheus-prod:prometheus"
    "rhinometric-grafana-prod:grafana"
    "rhinometric-alertmanager-prod:alertmanager"
    "rhinometric-loki-prod:loki"
    "rhinometric-tempo-prod:tempo"
    "rhinometric-postgres-prod:postgres"
    "rhinometric-redis-prod:redis"
    "rhinometric-ai-anomaly-prod:ai-anomaly"
    "rhinometric-report-generator-prod:report-generator"
    "rhinometric-dashboard-builder-prod:dashboard-builder"
    "rhinometric-node-exporter-prod:node-exporter"
    "rhinometric-cadvisor-prod:cadvisor"
    "rhinometric-blackbox-prod:blackbox"
)

for service_pair in "${SERVICES[@]}"; do
    container_name="${service_pair%%:*}"
    service_label="${service_pair##*:}"
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")
        STATUS=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "unknown")
        
        if [ "$STATUS" = "running" ]; then
            if [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "none" ]; then
                log_success "$service_label: Running ($HEALTH)"
            else
                log_warning "$service_label: Running but $HEALTH"
            fi
        else
            log_error "$service_label: Status $STATUS"
        fi
    else
        log_error "$service_label: Container not found"
    fi
done

# ============================================
# 2. PROMETHEUS TARGETS
# ============================================
log_info ""
log_info "═══ 2. Prometheus Targets ═══"

PROM_URL="${PROMETHEUS_URL:-http://localhost:9090}"
EXPECTED_TARGETS=(
    "rhinometric-ai-anomaly-prod:8085/metrics"
    "prometheus:9090/metrics"
    "grafana:3000/metrics"
    "loki:3100/metrics"
    "tempo:3200/metrics"
    "alertmanager:9093/metrics"
    "node-exporter:9100/metrics"
    "cadvisor:8080/metrics"
    "blackbox:9115/metrics"
)

TARGETS_RESPONSE=$(curl -sf "$PROM_URL/api/v1/targets" 2>/dev/null || echo "")

if [ -z "$TARGETS_RESPONSE" ]; then
    log_error "Cannot reach Prometheus API at $PROM_URL"
else
    UP_COUNT=$(echo "$TARGETS_RESPONSE" | grep -o '"health":"up"' | wc -l)
    DOWN_COUNT=$(echo "$TARGETS_RESPONSE" | grep -o '"health":"down"' | wc -l)
    
    log_info "Targets: $UP_COUNT UP, $DOWN_COUNT DOWN"
    
    for target in "${EXPECTED_TARGETS[@]}"; do
        if echo "$TARGETS_RESPONSE" | grep -q "$target"; then
            if echo "$TARGETS_RESPONSE" | grep "$target" | grep -q '"health":"up"'; then
                log_success "Target UP: $target"
            else
                log_error "Target DOWN: $target"
            fi
        else
            log_warning "Target not configured: $target"
        fi
    done
fi

# ============================================
# 3. HEALTH ENDPOINTS
# ============================================
log_info ""
log_info "═══ 3. Service Health Endpoints ═══"

HEALTH_ENDPOINTS=(
    "http://localhost:8085/health:AI Anomaly Detection"
    "http://localhost:8086/health:Report Generator"
    "http://localhost:8001/health:Dashboard Builder"
    "http://localhost:9090/-/healthy:Prometheus"
    "http://localhost:3000/api/health:Grafana"
    "http://localhost:9093/-/healthy:Alertmanager"
)

for endpoint_pair in "${HEALTH_ENDPOINTS[@]}"; do
    endpoint="${endpoint_pair%%:*}"
    name="${endpoint_pair##*:}"
    
    if curl -sf "$endpoint" > /dev/null 2>&1; then
        log_success "$name health check"
    else
        log_error "$name health check failed"
    fi
done

# ============================================
# 4. GRAFANA DATASOURCES & DASHBOARDS
# ============================================
log_info ""
log_info "═══ 4. Grafana Configuration ═══"

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GF_SECURITY_ADMIN_USER:-admin}"
GRAFANA_PASS="${GF_SECURITY_ADMIN_PASSWORD:-admin}"

# Check Prometheus datasource with UID
DS_RESPONSE=$(curl -sf -u "$GRAFANA_USER:$GRAFANA_PASS" \
    "$GRAFANA_URL/api/datasources/uid/prometheus" 2>/dev/null || echo "")

if echo "$DS_RESPONSE" | grep -q '"uid":"prometheus"'; then
    log_success "Grafana datasource 'prometheus' (UID: prometheus) exists"
else
    log_error "Grafana datasource 'prometheus' with UID 'prometheus' NOT found"
fi

# Check expected dashboards
EXPECTED_DASHBOARDS=(
    "System Overview"
    "Application Performance"
    "AI Anomaly Detection"
)

DASHBOARDS_RESPONSE=$(curl -sf -u "$GRAFANA_USER:$GRAFANA_PASS" \
    "$GRAFANA_URL/api/search?type=dash-db" 2>/dev/null || echo "")

if [ -z "$DASHBOARDS_RESPONSE" ]; then
    log_error "Cannot fetch Grafana dashboards"
else
    for dashboard in "${EXPECTED_DASHBOARDS[@]}"; do
        if echo "$DASHBOARDS_RESPONSE" | grep -q "\"title\":\"$dashboard\""; then
            log_success "Dashboard exists: $dashboard"
        else
            log_warning "Dashboard missing: $dashboard"
        fi
    done
fi

# ============================================
# 5. AI METRICS VALIDATION
# ============================================
log_info ""
log_info "═══ 5. AI Anomaly Metrics ═══"

AI_METRICS=(
    "rhinometric_anomaly_detections_total"
    "rhinometric_anomaly_active_count"
    "rhinometric_anomaly_models_trained"
)

for metric in "${AI_METRICS[@]}"; do
    QUERY_RESULT=$(curl -sf "$PROM_URL/api/v1/query?query=$metric" 2>/dev/null || echo "")
    
    if echo "$QUERY_RESULT" | grep -q '"status":"success"'; then
        VALUE=$(echo "$QUERY_RESULT" | grep -o '"value":\[[^]]*\]' | grep -o '\[.*\]' | grep -o '[0-9.]*' | tail -1)
        if [ -n "$VALUE" ]; then
            log_success "Metric $metric = $VALUE"
        else
            log_warning "Metric $metric exists but has no value"
        fi
    else
        log_error "Metric $metric not found in Prometheus"
    fi
done

# Validate 24h increase
QUERY="increase(rhinometric_anomaly_detections_total[24h])"
RESULT=$(curl -sf "$PROM_URL/api/v1/query?query=$(echo "$QUERY" | jq -sRr @uri)" 2>/dev/null || echo "")
if echo "$RESULT" | grep -q '"status":"success"'; then
    log_success "Query works: $QUERY"
else
    log_warning "Query failed: $QUERY"
fi

# Validate rate
QUERY="rate(rhinometric_anomaly_detections_total[5m])"
RESULT=$(curl -sf "$PROM_URL/api/v1/query?query=$(echo "$QUERY" | jq -sRr @uri)" 2>/dev/null || echo "")
if echo "$RESULT" | grep -q '"status":"success"'; then
    log_success "Query works: $QUERY"
else
    log_warning "Query failed: $QUERY"
fi

# ============================================
# 6. SECURITY & CONFIG VALIDATION
# ============================================
log_info ""
log_info "═══ 6. Security Configuration ═══"

# Check ENABLE_DOCS is false in prod
if grep -q "ENABLE_DOCS=false" "$ENV_FILE" 2>/dev/null; then
    log_success "ENABLE_DOCS=false in production"
else
    log_warning "ENABLE_DOCS should be false in production"
fi

# Check no hardcoded IPs/domains in critical files
HARDCODED_CHECK=$(grep -r "192.168\|10.0\|172.16\|@gmail\|@hotmail" \
    --include="*.yml" --include="*.yaml" \
    alertmanager/ prometheus/ grafana/ traefik/ 2>/dev/null || echo "")

if [ -z "$HARDCODED_CHECK" ]; then
    log_success "No hardcoded IPs/emails found in configs"
else
    log_error "Hardcoded values found:"
    echo "$HARDCODED_CHECK"
fi

# Check Traefik TLS
if docker exec rhinometric-traefik-prod cat /etc/traefik/traefik.yml 2>/dev/null | grep -q "certResolver"; then
    log_success "Traefik TLS configured"
else
    log_warning "Traefik TLS configuration not found"
fi

# ============================================
# 7. FINAL SUMMARY
# ============================================
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║            VERIFICATION SUMMARY                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${GREEN}Passed:   ${PASSED}${NC}"
echo -e "${YELLOW}Warnings: ${WARNINGS}${NC}"
echo -e "${RED}Failed:   ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ VERIFY-PROD PASSED${NC}"
    echo "Production environment is healthy and ready."
    exit 0
else
    echo -e "${RED}✗ VERIFY-PROD FAILED${NC}"
    echo "Production environment has $FAILED critical issues."
    exit 1
fi
