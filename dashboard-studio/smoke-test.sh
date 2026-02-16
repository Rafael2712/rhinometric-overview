#!/bin/bash

###############################################################################
# RhinoMetric Dashboard Builder - Smoke Test (End-to-End)
# Tests: API → Dashboard Creation → Grafana Validation
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8001"
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="rhinometric_v22"
JWT_SECRET="your_jwt_secret_for_license_system_change_this"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  RhinoMetric Dashboard Builder - Smoke Test       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Step 1: Check API Connectivity
###############################################################################

echo -e "${YELLOW}[1/7]${NC} Checking Dashboard Builder API connectivity..."

if curl -s --connect-timeout 5 "$API_BASE/" > /dev/null 2>&1; then
    API_STATUS=$(curl -s "$API_BASE/" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    API_VERSION=$(curl -s "$API_BASE/" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓${NC} API is ${GREEN}$API_STATUS${NC} (version: $API_VERSION)"
else
    echo -e "${RED}✗${NC} Cannot connect to Dashboard Builder API at $API_BASE"
    echo -e "${RED}  Make sure the service is running:${NC}"
    echo -e "  docker ps | grep dashboard-builder"
    exit 1
fi

###############################################################################
# Step 2: Generate JWT Token
###############################################################################

echo -e "\n${YELLOW}[2/7]${NC} Generating JWT token..."

JWT_TOKEN=$(docker exec rhinometric-dashboard-builder python -c \
  "import jwt; from datetime import datetime, timedelta, timezone; \
   print(jwt.encode({'user_id': 'smoketest', 'username': 'smoketest', 'role': 'admin', \
   'iat': datetime.now(timezone.utc), 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}, \
   '$JWT_SECRET', algorithm='HS256'))" 2>/dev/null)

if [ -z "$JWT_TOKEN" ]; then
    echo -e "${RED}✗${NC} Failed to generate JWT token"
    exit 1
fi

echo -e "${GREEN}✓${NC} JWT token generated (expires in 1 hour)"

###############################################################################
# Step 3: Check Grafana Connectivity
###############################################################################

echo -e "\n${YELLOW}[3/7]${NC} Checking Grafana connectivity..."

if curl -s --connect-timeout 5 -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
   "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Grafana is accessible"
else
    echo -e "${RED}✗${NC} Cannot connect to Grafana at $GRAFANA_URL"
    exit 1
fi

###############################################################################
# Step 4: Verify Prometheus Datasource
###############################################################################

echo -e "\n${YELLOW}[4/7]${NC} Verifying Prometheus datasource..."

DATASOURCES=$(curl -s "$API_BASE/api/v1/datasources" -H "Authorization: Bearer $JWT_TOKEN")
PROMETHEUS_UID=$(echo "$DATASOURCES" | grep -o '"uid":"prometheus"' | head -1)

if [ -n "$PROMETHEUS_UID" ]; then
    echo -e "${GREEN}✓${NC} Prometheus datasource found (UID: prometheus)"
else
    echo -e "${RED}✗${NC} Prometheus datasource not found"
    echo -e "${RED}  Available datasources:${NC}"
    echo "$DATASOURCES" | grep -o '"name":"[^"]*"' | cut -d'"' -f4
    exit 1
fi

###############################################################################
# Step 5: List Available Templates
###############################################################################

echo -e "\n${YELLOW}[5/7]${NC} Listing available templates..."

TEMPLATES=$(curl -s "$API_BASE/api/v1/templates" -H "Authorization: Bearer $JWT_TOKEN")
TEMPLATE_COUNT=$(echo "$TEMPLATES" | grep -o '"id":"[^"]*"' | wc -l)

if [ "$TEMPLATE_COUNT" -ge 1 ]; then
    echo -e "${GREEN}✓${NC} Found $TEMPLATE_COUNT templates"
    echo "$TEMPLATES" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sed 's/^/  - /'
else
    echo -e "${RED}✗${NC} No templates found"
    exit 1
fi

###############################################################################
# Step 6: Create Test Dashboard
###############################################################################

echo -e "\n${YELLOW}[6/7]${NC} Creating test dashboard (System Overview)..."

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
DASHBOARD_PAYLOAD=$(cat <<EOF
{
  "template": "system-overview",
  "title": "Smoke Test - $TIMESTAMP",
  "description": "Automated smoke test dashboard",
  "tags": ["smoke-test", "automated"]
}
EOF
)

CREATE_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/dashboards" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DASHBOARD_PAYLOAD")

DASHBOARD_UID=$(echo "$CREATE_RESPONSE" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
DASHBOARD_TITLE=$(echo "$CREATE_RESPONSE" | grep -o '"title":"[^"]*"' | cut -d'"' -f4)

if [ -n "$DASHBOARD_UID" ]; then
    echo -e "${GREEN}✓${NC} Dashboard created successfully"
    echo -e "  UID: ${BLUE}$DASHBOARD_UID${NC}"
    echo -e "  Title: $DASHBOARD_TITLE"
else
    echo -e "${RED}✗${NC} Failed to create dashboard"
    echo -e "${RED}  Response:${NC} $CREATE_RESPONSE"
    exit 1
fi

###############################################################################
# Step 7: Validate Dashboard in Grafana
###############################################################################

echo -e "\n${YELLOW}[7/7]${NC} Validating dashboard in Grafana..."

sleep 2  # Wait for Grafana to index the dashboard

GRAFANA_DASHBOARD=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
  "$GRAFANA_URL/api/dashboards/uid/$DASHBOARD_UID")

PANEL_COUNT=$(echo "$GRAFANA_DASHBOARD" | grep -o '"panels":\[' | wc -l)

if [ "$PANEL_COUNT" -gt 0 ]; then
    ACTUAL_PANELS=$(echo "$GRAFANA_DASHBOARD" | grep -o '"id":[0-9]*' | wc -l)
    echo -e "${GREEN}✓${NC} Dashboard validated in Grafana"
    echo -e "  Panels: ${GREEN}$ACTUAL_PANELS${NC}"
else
    echo -e "${RED}✗${NC} Dashboard exists but has no panels"
    exit 1
fi

###############################################################################
# Summary
###############################################################################

echo -e "\n${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║             ✓ Smoke Test PASSED                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Dashboard URL:${NC}"
echo -e "  ${BLUE}$GRAFANA_URL/d/$DASHBOARD_UID${NC}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Open Dashboard Studio: ${BLUE}http://localhost:3001${NC}"
echo -e "  2. Use JWT token for authentication"
echo -e "  3. Create dashboards visually"
echo ""

# Open dashboard in default browser (optional)
read -p "Open dashboard in browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open > /dev/null; then
        xdg-open "$GRAFANA_URL/d/$DASHBOARD_UID"
    elif command -v open > /dev/null; then
        open "$GRAFANA_URL/d/$DASHBOARD_UID"
    else
        echo "Please open manually: $GRAFANA_URL/d/$DASHBOARD_UID"
    fi
fi

exit 0
