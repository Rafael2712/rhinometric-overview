#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
 RHINOMETRIC TRACE GENERATOR - v2.1.0
═══════════════════════════════════════════════════════════════════════════

Generates realistic traces to populate Tempo via OTEL Collector.

Usage:
  python3 trace-generator.py [--interval=30]
"""

import requests
import json
import time
import random
from datetime import datetime
import sys

OTEL_ENDPOINT = "http://localhost:4320/v1/traces"

SERVICES = [
    "license-server-v2",
    "api-proxy",
    "postgres",
    "redis",
    "prometheus",
    "grafana"
]

OPERATIONS = {
    "license-server-v2": ["validate_license", "check_expiration", "get_user_info"],
    "api-proxy": ["fetch_api", "cache_lookup", "proxy_request"],
    "postgres": ["query_execution", "connection_pool", "index_scan"],
    "redis": ["get_cache", "set_cache", "del_cache"],
    "prometheus": ["scrape_metrics", "query_range", "alert_eval"],
    "grafana": ["render_dashboard", "query_datasource", "auth_check"]
}

def generate_trace_id():
    """Generate random 32-char hex trace ID"""
    return ''.join(random.choices('0123456789abcdef', k=32))

def generate_span_id():
    """Generate random 16-char hex span ID"""
    return ''.join(random.choices('0123456789abcdef', k=16))

def create_trace_payload(service, operation, duration_ms):
    """Create OTLP trace payload"""
    trace_id = generate_trace_id()
    span_id = generate_span_id()
    now_ns = int(time.time() * 1_000_000_000)
    
    return {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": service}},
                    {"key": "service.version", "value": {"stringValue": "2.1.0"}},
                    {"key": "deployment.environment", "value": {"stringValue": "trial"}},
                    {"key": "telemetry.sdk.name", "value": {"stringValue": "rhinometric-trace-gen"}},
                    {"key": "telemetry.sdk.version", "value": {"stringValue": "1.0.0"}}
                ]
            },
            "scopeSpans": [{
                "scope": {
                    "name": "rhinometric-tracer",
                    "version": "2.1.0"
                },
                "spans": [{
                    "traceId": trace_id,
                    "spanId": span_id,
                    "name": operation,
                    "kind": 1,  # SPAN_KIND_INTERNAL
                    "startTimeUnixNano": str(now_ns),
                    "endTimeUnixNano": str(now_ns + duration_ms * 1_000_000),
                    "attributes": [
                        {"key": "http.method", "value": {"stringValue": random.choice(["GET", "POST", "PUT"])}},
                        {"key": "http.status_code", "value": {"intValue": random.choice([200, 200, 200, 201, 404, 500])}},
                        {"key": "operation.name", "value": {"stringValue": operation}},
                        {"key": "latency_ms", "value": {"intValue": duration_ms}},
                        {"key": "success", "value": {"boolValue": duration_ms < 1000}}
                    ],
                    "status": {
                        "code": 1 if duration_ms < 1000 else 2  # STATUS_CODE_OK / ERROR
                    }
                }]
            }]
        }]
    }

def send_trace():
    """Generate and send a random trace"""
    service = random.choice(SERVICES)
    operation = random.choice(OPERATIONS[service])
    duration_ms = random.randint(10, 2000)
    
    payload = create_trace_payload(service, operation, duration_ms)
    
    try:
        response = requests.post(
            OTEL_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if response.status_code in [200, 202]:
            print(f"[{timestamp}] [OK] Trace sent: {service}/{operation} ({duration_ms}ms)")
        else:
            print(f"[{timestamp}] ✗ Failed: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"[{timestamp}] ✗ Error: {e}")

def main():
    interval = 30  # seconds
    
    if len(sys.argv) > 1 and sys.argv[1].startswith("--interval="):
        interval = int(sys.argv[1].split("=")[1])
    
    print("=" * 62)
    print("   RHINOMETRIC TRACE GENERATOR v2.1.0")
    print("=" * 62)
    print(f"Sending traces to: {OTEL_ENDPOINT}")
    print(f"Interval: {interval} seconds")
    print(f"Services: {', '.join(SERVICES)}")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            send_trace()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n[OK] Trace generator stopped")

if __name__ == "__main__":
    main()
