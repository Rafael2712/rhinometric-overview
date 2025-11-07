#!/bin/bash
# ============================================
# Rhinometric v2.5.0 - Smoke Test Script
# ============================================
# Tests all critical services after deployment
# Usage: bash smoke-test.sh
# Exit codes: 0=success, 1=failure

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Config
DOMAIN="${DOMAIN:-localhost}"
TIMEOUT=10
FAILED_TESTS=()

# Functions
print_header() {
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response, expected $expected_code)"
        FAILED_TESTS+=("$name: Expected $expected_code, got $response")
        return 1
    fi
}

test_metrics() {
    local name=$1
    local url=$2
    local metric=$3
    
    echo -n "Testing $name metrics... "
    
    response=$(curl -s --max-time $TIMEOUT "$url" 2>/dev/null || echo "")
    
    if echo "$response" | grep -q "$metric"; then
        echo -e "${GREEN}✓ OK${NC} (Found $metric)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Metric $metric not found)"
        FAILED_TESTS+=("$name: Metric $metric not found")
        return 1
    fi
}

test_grafana_dashboard() {
    echo -n "Testing Grafana dashboard creation... "
    
    # Login to get cookie
    cookie=$(curl -s -c - -X POST "http://$DOMAIN/api/auth/keys" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"smoke-test\",\"role\":\"Admin\"}" \
        --user "admin:${GRAFANA_ADMIN_PASSWORD:-admin}" 2>/dev/null | grep -o 'grafana_session.*' || echo "")
    
    if [ -z "$cookie" ]; then
        echo -e "${RED}✗ FAILED${NC} (Cannot authenticate)"
        FAILED_TESTS+=("Grafana: Authentication failed")
        return 1
    fi
    
    # Create test dashboard
    dashboard_json='{
      "dashboard": {
        "title": "Smoke Test Dashboard",
        "tags": ["smoke-test"],
        "timezone": "browser",
        "panels": [{
          "id": 1,
          "type": "stat",
          "title": "Test Panel",
          "targets": [{
            "expr": "up",
            "refId": "A"
          }]
        }],
        "schemaVersion": 16,
        "version": 0
      },
      "overwrite": true
    }'
    
    response=$(curl -s -X POST "http://$DOMAIN/api/dashboards/db" \
        -H "Content-Type: application/json" \
        -H "Cookie: $cookie" \
        -d "$dashboard_json" 2>/dev/null || echo "")
    
    if echo "$response" | grep -q '"status":"success"'; then
        uid=$(echo "$response" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✓ OK${NC} (Created dashboard: $uid)"
        
        # Cleanup
        curl -s -X DELETE "http://$DOMAIN/api/dashboards/uid/$uid" \
            -H "Cookie: $cookie" &>/dev/null
        
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED_TESTS+=("Grafana: Dashboard creation failed")
        return 1
    fi
}

test_alertmanager() {
    echo -n "Testing Alertmanager... "
    
    # Post test alert
    alert_json='[{
      "labels": {
        "alertname": "SmokeTest",
        "severity": "info"
      },
      "annotations": {
        "summary": "Smoke test alert",
        "description": "This is a test alert from smoke-test.sh"
      },
      "startsAt": "'$(date -Iseconds)'",
      "endsAt": "'$(date -d '+5 minutes' -Iseconds)'"
    }]'
    
    response=$(curl -s -X POST "http://$DOMAIN:9093/api/v2/alerts" \
        -H "Content-Type: application/json" \
        -d "$alert_json" 2>/dev/null || echo "")
    
    if [ $? -eq 0 ]; then
        # Check if alert is active
        sleep 2
        active=$(curl -s "http://$DOMAIN:9093/api/v2/alerts" 2>/dev/null | grep -o 'SmokeTest' || echo "")
        
        if [ -n "$active" ]; then
            echo -e "${GREEN}✓ OK${NC} (Alert posted and active)"
            return 0
        else
            echo -e "${YELLOW}⚠ WARNING${NC} (Alert posted but not active)"
            return 0
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED_TESTS+=("Alertmanager: Cannot post alert")
        return 1
    fi
}

# ============================================
# MAIN TESTS
# ============================================

print_header "RHINOMETRIC v2.5.0 - SMOKE TESTS"

echo "Domain: $DOMAIN"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Health Endpoints
print_header "Health Endpoints"
test_endpoint "Grafana" "http://$DOMAIN/api/health" 200
test_endpoint "Prometheus" "http://prometheus:9090/-/healthy" 200
test_endpoint "Alertmanager" "http://alertmanager:9093/-/healthy" 200
test_endpoint "Loki" "http://loki:3100/ready" 200
test_endpoint "Dashboard Builder" "http://dashboard-builder:8001/health" 200
test_endpoint "AI Anomaly" "http://ai-anomaly:8085/health" 200
test_endpoint "Report Generator" "http://report-generator:8086/health" 200
test_endpoint "License Server" "http://license-server:8090/health" 200

# Metrics Endpoints
print_header "Metrics Endpoints"
test_metrics "Dashboard Builder" "http://dashboard-builder:8001/metrics" "http_requests_total"
test_metrics "AI Anomaly" "http://ai-anomaly:8085/metrics" "http_requests_total"
test_metrics "Report Generator" "http://report-generator:8086/metrics" "http_requests_total"
test_metrics "Prometheus" "http://prometheus:9090/metrics" "prometheus_build_info"
test_metrics "Node Exporter" "http://node-exporter:9100/metrics" "node_cpu_seconds_total"
test_metrics "cAdvisor" "http://cadvisor:8080/metrics" "container_memory_usage_bytes"

# Grafana Datasources
print_header "Grafana Datasources"
echo -n "Checking Prometheus datasource... "
datasources=$(curl -s "http://$DOMAIN/api/datasources" \
    --user "admin:${GRAFANA_ADMIN_PASSWORD:-admin}" 2>/dev/null || echo "")

if echo "$datasources" | grep -q '"type":"prometheus"'; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    FAILED_TESTS+=("Grafana: Prometheus datasource not found")
fi

# Grafana Dashboard Creation
print_header "Grafana Dashboard Creation"
test_grafana_dashboard

# Alertmanager
print_header "Alertmanager"
test_alertmanager

# ============================================
# RESULTS
# ============================================

print_header "RESULTS"

if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}\n"
    echo "Rhinometric v2.5.0 is healthy and ready for production!"
    exit 0
else
    echo -e "${RED}✗ ${#FAILED_TESTS[@]} TEST(S) FAILED${NC}\n"
    echo "Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}•${NC} $test"
    done
    echo ""
    echo "Please check the logs and fix the issues before going to production."
    exit 1
fi
