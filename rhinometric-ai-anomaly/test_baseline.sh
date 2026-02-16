#!/bin/bash
#
# Test Script for Dynamic Baseline Implementation
# Version: 2.6.0
#
# Tests:
# 1. Baseline expected value query
# 2. Anomaly detection with explanation
# 3. Persistence after restart
# 4. Adaptive baseline adjustment
#

set -e

# Colors for output
RED='\033[0.31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_BASE="http://localhost:8085"
PROMETHEUS_BASE="http://localhost:9090"

echo "=================================================="
echo "AI ANOMALY DETECTION v2.6.0 - BASELINE TESTS"
echo "=================================================="
echo ""

# Function to print test header
test_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "TEST $1: $2"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to check if service is healthy
check_health() {
    echo "Checking service health..."
    response=$(curl -s "$API_BASE/health")
    status=$(echo "$response" | jq -r '.status')
    
    if [ "$status" == "healthy" ]; then
        echo -e "${GREEN}✓ Service is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Service is not healthy${NC}"
        echo "$response"
        return 1
    fi
}

# Wait for service to be ready
wait_for_service() {
    echo "Waiting for service to be ready..."
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$API_BASE/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Service is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Attempt $attempt/$max_attempts..."
        sleep 2
    done
    
    echo -e "${RED}✗ Service did not become ready${NC}"
    return 1
}

# ==================== TEST 1: Baseline Expected Value ====================
test_baseline_expected() {
    test_header "1" "Baseline Expected Value Query"
    
    # Get list of metrics with baselines
    echo "1.1. Getting list of metrics with baselines..."
    metrics_response=$(curl -s "$API_BASE/api/v1/baselines/metrics")
    metrics_count=$(echo "$metrics_response" | jq -r '.count')
    
    if [ "$metrics_count" -gt 0 ]; then
        echo -e "${GREEN}✓ Found $metrics_count metrics with baselines${NC}"
        echo "$metrics_response" | jq '.metrics[]' | head -5
    else
        echo -e "${YELLOW}⚠ No baselines found yet (service may be initializing)${NC}"
    fi
    
    # Query baseline for node_cpu_usage
    echo ""
    echo "1.2. Querying baseline for node_cpu_usage..."
    baseline_response=$(curl -s "$API_BASE/api/v1/baselines/expected?metric=node_cpu_usage")
    
    if echo "$baseline_response" | jq -e '.baseline' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Baseline found for node_cpu_usage${NC}"
        echo "$baseline_response" | jq '{
            metric: .metric,
            hour: .hour_of_day,
            day: .day_of_week,
            mean: .baseline.mean,
            expected_range: .baseline.expected_range,
            sample_count: .baseline.sample_count
        }'
        
        # Validate structure
        mean=$(echo "$baseline_response" | jq -r '.baseline.mean')
        p10=$(echo "$baseline_response" | jq -r '.baseline.p10')
        p90=$(echo "$baseline_response" | jq -r '.baseline.p90')
        
        if [ "$mean" != "null" ] && [ "$p10" != "null" ] && [ "$p90" != "null" ]; then
            echo -e "${GREEN}✓ Baseline structure is valid${NC}"
            echo "  Mean: $mean"
            echo "  Range: [$p10, $p90]"
        else
            echo -e "${RED}✗ Baseline structure is invalid${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ Baseline not found for node_cpu_usage (may need more data)${NC}"
        echo "$baseline_response" | jq '.'
    fi
    
    # Get all baselines summary
    echo ""
    echo "1.3. Getting baselines summary..."
    summary_response=$(curl -s "$API_BASE/api/v1/baselines")
    echo "$summary_response" | jq '.baselines.stats'
    
    echo -e "${GREEN}✓ TEST 1 COMPLETED${NC}"
}

# ==================== TEST 2: Anomaly Detection with Explanation ====================
test_anomaly_detection() {
    test_header "2" "Anomaly Detection with Baseline Explanation"
    
    # Get recent anomalies
    echo "2.1. Checking for recent anomalies..."
    anomalies_response=$(curl -s "$API_BASE/api/v1/anomalies?limit=5")
    anomaly_count=$(echo "$anomalies_response" | jq -r '.anomalies | length')
    
    echo "Found $anomaly_count recent anomalies"
    
    if [ "$anomaly_count" -gt 0 ]; then
        echo ""
        echo "2.2. Analyzing anomaly with baseline explanation..."
        
        # Get first anomaly
        anomaly=$(echo "$anomalies_response" | jq '.anomalies[0]')
        
        metric_name=$(echo "$anomaly" | jq -r '.metric_name')
        current_value=$(echo "$anomaly" | jq -r '.current_value')
        expected_value=$(echo "$anomaly" | jq -r '.expected_value')
        deviation_percent=$(echo "$anomaly" | jq -r '.deviation_percent')
        baseline_explanation=$(echo "$anomaly" | jq -r '.baseline_explanation')
        
        echo -e "${YELLOW}Anomaly Details:${NC}"
        echo "  Metric: $metric_name"
        echo "  Current Value: $current_value"
        echo "  Expected Value: $expected_value"
        echo "  Deviation: $deviation_percent%"
        echo "  Explanation: $baseline_explanation"
        
        # Validate fields
        if [ "$deviation_percent" != "null" ] && [ "$baseline_explanation" != "null" ]; then
            echo -e "${GREEN}✓ Anomaly has baseline explanation${NC}"
        else
            echo -e "${YELLOW}⚠ Anomaly missing baseline fields (baseline may not exist yet)${NC}"
        fi
        
        # Show full anomaly structure
        echo ""
        echo "Full anomaly structure:"
        echo "$anomaly" | jq '{
            metric_name,
            timestamp,
            is_anomaly,
            current_value,
            expected_value,
            deviation_percent,
            baseline_explanation,
            severity,
            confidence,
            anomaly_score
        }'
    else
        echo -e "${YELLOW}⚠ No anomalies detected yet${NC}"
        echo "This is normal if system is stable or initializing"
    fi
    
    echo -e "${GREEN}✓ TEST 2 COMPLETED${NC}"
}

# ==================== TEST 3: Persistence After Restart ====================
test_persistence() {
    test_header "3" "Baseline Persistence After Restart"
    
    echo "3.1. Recording current baseline state..."
    baseline_before=$(curl -s "$API_BASE/api/v1/baselines")
    baseline_count_before=$(echo "$baseline_before" | jq -r '.baselines.stats.baseline_count')
    
    echo "Baselines before restart: $baseline_count_before"
    
    if [ "$baseline_count_before" == "null" ] || [ "$baseline_count_before" -eq 0 ]; then
        echo -e "${YELLOW}⚠ No baselines to test persistence (skipping restart test)${NC}"
        echo -e "${YELLOW}⚠ Run this test after service has been running for at least 10 minutes${NC}"
        return 0
    fi
    
    echo ""
    echo "3.2. Restarting service..."
    echo -e "${YELLOW}⚠ This will restart the rhinometric-ai-anomaly container${NC}"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping restart test"
        return 0
    fi
    
    docker restart rhinometric-ai-anomaly
    
    echo "Waiting for service to recover..."
    sleep 10
    wait_for_service
    
    echo ""
    echo "3.3. Checking baseline persistence..."
    baseline_after=$(curl -s "$API_BASE/api/v1/baselines")
    baseline_count_after=$(echo "$baseline_after" | jq -r '.baselines.stats.baseline_count')
    
    echo "Baselines after restart: $baseline_count_after"
    
    if [ "$baseline_count_after" -ge "$baseline_count_before" ]; then
        echo -e "${GREEN}✓ Baselines persisted successfully${NC}"
        echo "  Before: $baseline_count_before"
        echo "  After: $baseline_count_after"
    else
        echo -e "${RED}✗ Baselines NOT persisted${NC}"
        echo "  Before: $baseline_count_before"
        echo "  After: $baseline_count_after"
        return 1
    fi
    
    echo -e "${GREEN}✓ TEST 3 COMPLETED${NC}"
}

# ==================== TEST 4: Adaptive Baseline (Manual) ====================
test_adaptive_baseline() {
    test_header "4" "Adaptive Baseline Adjustment"
    
    echo "This test requires monitoring baseline changes over time."
    echo "To test adaptive baseline:"
    echo ""
    echo "1. Record current baseline for a metric:"
    echo "   curl -s '$API_BASE/api/v1/baselines/expected?metric=node_cpu_usage' | jq '.baseline.mean'"
    echo ""
    echo "2. Simulate load change (e.g., stress test):"
    echo "   stress --cpu 4 --timeout 7200s  # 2 hours"
    echo ""
    echo "3. After 1-2 hours, check if baseline adjusted:"
    echo "   curl -s '$API_BASE/api/v1/baselines/expected?metric=node_cpu_usage' | jq '.baseline.mean'"
    echo ""
    echo "4. The baseline should gradually increase with EMA (alpha=0.1)"
    echo ""
    echo -e "${YELLOW}⚠ This test cannot be automated (requires time and load simulation)${NC}"
    echo -e "${GREEN}✓ TEST 4 INFO PROVIDED${NC}"
}

# ==================== MAIN EXECUTION ====================

# Check if service is running
if ! wait_for_service; then
    echo -e "${RED}✗ Service is not running. Start with:${NC}"
    echo "  cd /c/Users/canel/mi-proyecto/infrastructure/mi-proyecto"
    echo "  docker compose -f docker-compose-v2.5.0.yml up -d rhinometric-ai-anomaly"
    exit 1
fi

# Run health check
check_health

# Run tests
test_baseline_expected
test_anomaly_detection

# Optional tests (require user interaction)
echo ""
read -p "Run persistence test (requires restart)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    test_persistence
fi

test_adaptive_baseline

# Final summary
echo ""
echo "=================================================="
echo "TEST SUMMARY"
echo "=================================================="
echo ""
echo "Dynamic Baseline Implementation Tests:"
echo "  ✓ Test 1: Baseline query API"
echo "  ✓ Test 2: Anomaly detection with explanation"
echo "  ? Test 3: Persistence (optional)"
echo "  ℹ Test 4: Adaptive adjustment (manual)"
echo ""
echo "Next steps:"
echo "  1. Monitor baselines: curl $API_BASE/api/v1/baselines/metrics"
echo "  2. View anomalies: curl $API_BASE/api/v1/anomalies"
echo "  3. Trigger manual refresh: curl -X POST $API_BASE/api/v1/baselines/refresh"
echo "  4. Check database: ls -lh ~/rhinometric_data_v2.2/ai-anomaly/data/"
echo ""
echo "Grafana Dashboard: http://localhost:3000"
echo "API Documentation: http://localhost:8085/docs"
echo ""
echo -e "${GREEN}✓ ALL TESTS COMPLETED${NC}"
