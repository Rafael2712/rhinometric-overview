#!/bin/bash

##############################################################################
# RHINOMETRIC v2.4.0 - Messaging Connectors Test Runner
# ======================================================
# 
# Ejecuta tests unitarios para los nuevos conectores de messaging:
# - RabbitMQ
# - Kafka
# - MQTT
#
# Genera reporte HTML con resultados detallados.
##############################################################################

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  RHINOMETRIC Messaging Connectors Tests"
echo "  Version: 2.4.0"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found${NC}"
    echo "Installing pytest..."
    pip install pytest pytest-asyncio pytest-html pytest-cov
fi

# Check if required packages are installed
echo "Checking dependencies..."
pip install -q aiohttp kafka-python aiomqtt 2>/dev/null || true

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/api-connector"

# Run tests
echo ""
echo -e "${YELLOW}🧪 Running messaging connector tests...${NC}"
echo ""

pytest tests/test_messaging_connectors.py \
    -v \
    --tb=short \
    --color=yes \
    --html=tests/reports/test_messaging_report.html \
    --self-contained-html \
    --cov=api-connector/connectors \
    --cov-report=term-missing \
    --cov-report=html:tests/reports/coverage_messaging \
    2>&1 | tee tests/logs/test_messaging_execution.log

# Check exit code
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All messaging connector tests passed!${NC}"
    echo ""
    echo "📊 Reports generated:"
    echo "   - HTML Report: tests/reports/test_messaging_report.html"
    echo "   - Coverage:    tests/reports/coverage_messaging/index.html"
    echo "   - Logs:        tests/logs/test_messaging_execution.log"
    echo ""
    
    # Summary
    echo "📈 Test Summary:"
    grep -E "passed|failed|skipped|error" tests/logs/test_messaging_execution.log | tail -1
    
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Check logs at: tests/logs/test_messaging_execution.log"
    exit 1
fi
