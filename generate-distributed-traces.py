#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
RHINOMETRIC v2.2.0 - Distributed Trace Generator with Service Graph
═══════════════════════════════════════════════════════════════════════════

Generates realistic distributed traces with multiple services and spans
to populate Tempo service graph.

Features:
- Parent-child span relationships
- Multi-service traces (API → Auth → DB)
- Realistic latencies
- Error simulation
- Service dependencies visualization

Usage:
    python3 generate-distributed-traces.py
"""

import requests
import time
import random
import json
from datetime import datetime

OTLP_ENDPOINT = "http://localhost:4318/v1/traces"

# Service dependency graph
SERVICE_DEPENDENCIES = {
    "api-gateway": ["auth-service", "user-service", "order-service"],
    "auth-service": ["postgres", "redis"],
    "user-service": ["postgres", "redis"],
    "order-service": ["postgres", "payment-service", "inventory-service"],
    "payment-service": ["postgres"],
    "inventory-service": ["postgres", "redis"],
    "notification-service": ["redis"],
}

def generate_trace_id():
    return ''.join(['%02x' % random.randint(0, 255) for _ in range(16)])

def generate_span_id():
    return ''.join(['%02x' % random.randint(0, 255) for _ in range(8)])

def generate_distributed_trace():
    """Generate a realistic distributed trace with multiple services"""
    
    trace_id = generate_trace_id()
    root_service = "api-gateway"
    operation = random.choice([
        "GET /api/users/{id}",
        "POST /api/orders",
        "GET /api/products",
        "PUT /api/users/{id}",
        "DELETE /api/sessions",
    ])
    
    # Simulate error rate
    is_error = random.random() < 0.05  # 5% error rate
    status_code = 500 if is_error else 200
    
    base_time = int(time.time() * 1_000_000_000)
    current_time = base_time
    spans = []
    
    # Root span (API Gateway)
    root_duration = random.randint(50, 300) * 1_000_000  # 50-300ms
    root_span_id = generate_span_id()
    
    spans.append({
        "traceId": trace_id,
        "spanId": root_span_id,
        "name": operation,
        "kind": 2,  # SERVER
        "startTimeUnixNano": str(current_time),
        "endTimeUnixNano": str(current_time + root_duration),
        "attributes": [
            {"key": "http.method", "value": {"stringValue": operation.split()[0]}},
            {"key": "http.target", "value": {"stringValue": operation.split()[1]}},
            {"key": "http.status_code", "value": {"intValue": status_code}},
            {"key": "component", "value": {"stringValue": "http"}},
            {"key": "span.kind", "value": {"stringValue": "server"}},
        ],
        "status": {"code": 1 if not is_error else 2}
    })
    
    # Child spans (downstream services)
    parent_span_id = root_span_id
    dependencies = SERVICE_DEPENDENCIES.get(root_service, [])
    
    for dep_service in dependencies[:2]:  # Limit to 2 downstream services
        current_time += random.randint(5, 15) * 1_000_000  # Add 5-15ms latency
        dep_duration = random.randint(10, 80) * 1_000_000  # 10-80ms
        dep_span_id = generate_span_id()
        
        # Determine operation based on service
        if "auth" in dep_service:
            dep_operation = "validate_token"
        elif "user" in dep_service:
            dep_operation = "fetch_user_profile"
        elif "order" in dep_service:
            dep_operation = "create_order"
        elif "postgres" in dep_service:
            dep_operation = "SELECT * FROM users WHERE id = $1"
        elif "redis" in dep_service:
            dep_operation = "GET user:session:abc123"
        else:
            dep_operation = "process_request"
        
        spans.append({
            "traceId": trace_id,
            "spanId": dep_span_id,
            "parentSpanId": parent_span_id,
            "name": dep_operation,
            "kind": 3,  # CLIENT
            "startTimeUnixNano": str(current_time),
            "endTimeUnixNano": str(current_time + dep_duration),
            "attributes": [
                {"key": "service.name", "value": {"stringValue": dep_service}},
                {"key": "component", "value": {"stringValue": "http"}},
                {"key": "span.kind", "value": {"stringValue": "client"}},
            ],
            "status": {"code": 1}
        })
        
        # Add database spans for services that use DB
        if dep_service in ["auth-service", "user-service", "order-service"]:
            db_dependencies = SERVICE_DEPENDENCIES.get(dep_service, [])
            if "postgres" in db_dependencies:
                current_time += random.randint(2, 5) * 1_000_000
                db_duration = random.randint(5, 30) * 1_000_000
                db_span_id = generate_span_id()
                
                spans.append({
                    "traceId": trace_id,
                    "spanId": db_span_id,
                    "parentSpanId": dep_span_id,
                    "name": "db.query",
                    "kind": 3,  # CLIENT
                    "startTimeUnixNano": str(current_time),
                    "endTimeUnixNano": str(current_time + db_duration),
                    "attributes": [
                        {"key": "db.system", "value": {"stringValue": "postgresql"}},
                        {"key": "db.name", "value": {"stringValue": "rhinometric"}},
                        {"key": "db.operation", "value": {"stringValue": "SELECT"}},
                        {"key": "span.kind", "value": {"stringValue": "client"}},
                    ],
                    "status": {"code": 1}
                })
    
    # Build trace payload
    trace_data = {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": root_service}},
                    {"key": "service.version", "value": {"stringValue": "2.2.0"}},
                    {"key": "deployment.environment", "value": {"stringValue": "production"}},
                    {"key": "telemetry.sdk.name", "value": {"stringValue": "opentelemetry"}},
                    {"key": "telemetry.sdk.language", "value": {"stringValue": "python"}},
                ]
            },
            "scopeSpans": [{
                "scope": {
                    "name": "rhinometric-tracer",
                    "version": "1.0.0"
                },
                "spans": spans
            }]
        }]
    }
    
    try:
        response = requests.post(
            OTLP_ENDPOINT,
            json=trace_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        return response.status_code in [200, 202], len(spans), is_error
    except Exception as e:
        print(f"❌ Error sending trace: {e}")
        return False, 0, False

def main():
    print("🔍 RHINOMETRIC Distributed Trace Generator v2.2.0")
    print("=" * 70)
    print(f"Endpoint: {OTLP_ENDPOINT}")
    print("Generating multi-span distributed traces with service dependencies")
    print("=" * 70)
    print()
    
    iteration = 0
    total_traces = 0
    total_spans = 0
    total_errors = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iteration #{iteration}")
            
            # Generate 3-5 distributed traces per iteration
            num_traces = random.randint(3, 5)
            success_count = 0
            
            for _ in range(num_traces):
                success, span_count, is_error = generate_distributed_trace()
                
                if success:
                    success_count += 1
                    total_traces += 1
                    total_spans += span_count
                    if is_error:
                        total_errors += 1
                    
                    status_icon = "✅" if not is_error else "⚠️"
                    print(f"  {status_icon} Trace with {span_count} spans (error: {is_error})")
                
                time.sleep(0.5)
            
            print(f"  📊 Sent {success_count}/{num_traces} traces successfully")
            print(f"  📈 Total: {total_traces} traces, {total_spans} spans, {total_errors} errors")
            
            # Wait before next iteration (30 seconds)
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n")
        print("=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"Total traces generated: {total_traces}")
        print(f"Total spans generated: {total_spans}")
        print(f"Total errors simulated: {total_errors}")
        print(f"Avg spans per trace: {total_spans / total_traces if total_traces > 0 else 0:.2f}")
        print(f"Error rate: {total_errors / total_traces * 100 if total_traces > 0 else 0:.2f}%")
        print("=" * 70)
        print("\n👋 Trace generator stopped")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
