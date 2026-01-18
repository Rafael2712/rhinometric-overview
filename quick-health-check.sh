#!/bin/bash

# RHINOMETRIC Quick Health Check Script
# Verifies all services are operational

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🔍 RHINOMETRIC Quick Health Check v2.4.0              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected" ] || [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $response)"
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local name=$1
    local url=$2
    
    echo -n "Testing $name... "
    
    response=$(curl -s "$url" 2>/dev/null)
    
    if echo "$response" | grep -q "version\|healthy\|ready"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

# Counter
total=0
passed=0
failed=0

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🌐 Testing Web UIs${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Test Grafana (via nginx)
((total++))
if test_endpoint "Grafana (port 80)" "http://localhost:80/api/health" "200"; then
    ((passed++))
else
    ((failed++))
fi

# Test API Connector
((total++))
if test_endpoint "API Connector (port 8000)" "http://localhost:8000" "200"; then
    ((passed++))
else
    ((failed++))
fi

# Test Dashboard Builder
((total++))
if test_endpoint "Dashboard Builder (port 8001)" "http://localhost:8001" "200"; then
    ((passed++))
else
    ((failed++))
fi

# Test License UI
((total++))
if test_endpoint "License UI (port 8092)" "http://localhost:8092" "200"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🔌 Testing Backend APIs${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Test License Server
((total++))
if test_json_endpoint "License Server (port 5000)" "http://localhost:5000/health"; then
    ((passed++))
else
    ((failed++))
fi

# Test Prometheus
((total++))
if test_endpoint "Prometheus (port 9090)" "http://localhost:9090/-/healthy" "200"; then
    ((passed++))
else
    ((failed++))
fi

# Test Loki
((total++))
if test_endpoint "Loki (port 3100)" "http://localhost:3100/ready" "200"; then
    ((passed++))
else
    ((failed++))
fi

# Test Tempo
((total++))
if test_endpoint "Tempo (port 3200)" "http://localhost:3200/ready" "200"; then
    ((passed++))
else
    ((failed++))
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🐳 Docker Containers Status${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Count healthy containers
healthy_count=$(docker ps --filter "name=rhinometric" --filter "health=healthy" --format "{{.Names}}" | wc -l)
total_count=$(docker ps --filter "name=rhinometric" --format "{{.Names}}" | wc -l)

echo "Healthy containers: $healthy_count / $total_count"

if [ "$healthy_count" -eq "$total_count" ]; then
    echo -e "${GREEN}✅ All containers healthy${NC}"
    ((passed++))
else
    echo -e "${RED}❌ Some containers unhealthy${NC}"
    ((failed++))
fi

((total++))

# Show unhealthy containers
unhealthy=$(docker ps --filter "name=rhinometric" --format "{{.Names}}\t{{.Status}}" | grep -v "healthy" | grep -v "NAMES" || true)
if [ -n "$unhealthy" ]; then
    echo -e "${RED}Unhealthy containers:${NC}"
    echo "$unhealthy"
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📊 Summary${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Total tests: $total"
echo -e "Passed: ${GREEN}$passed${NC}"
echo -e "Failed: ${RED}$failed${NC}"

echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ALL SERVICES OPERATIONAL                            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ SOME SERVICES HAVE ISSUES                           ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Check logs with: docker logs <container-name>"
    exit 1
fi
