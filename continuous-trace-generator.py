#!/usr/bin/env python3
"""
Continuous Trace Generator for Tempo
Generates realistic traces every minute to populate Tempo
"""
import requests
import time
import random
import json
from datetime import datetime

OTLP_ENDPOINT = "http://localhost:4318/v1/traces"

SERVICES = [
    ("rhinometric-grafana", ["render_dashboard", "load_panel", "query_datasource", "save_dashboard"]),
    ("rhinometric-prometheus", ["query_range", "query_instant", "scrape_targets", "evaluate_rules"]),
    ("rhinometric-loki", ["push_logs", "query_logs", "tail_logs", "labels"]),
    ("rhinometric-veriverde", ["collect_metrics", "calculate_efficiency", "read_sensors"]),
    ("rhinometric-ai-anomaly", ["detect_anomalies", "analyze_metrics", "train_model"]),
    ("rhinometric-license-server", ["validate_license", "check_expiry", "activate_trial"]),
    ("rhinometric-api-proxy", ["proxy_request", "auth_middleware", "rate_limit"]),
    ("rhinometric-postgres", ["execute_query", "transaction_commit", "vacuum"]),
    ("rhinometric-nginx", ["handle_request", "serve_static", "proxy_upstream"]),
    ("rhinometric-redis", ["get_cache", "set_cache", "pub_message"]),
]

def generate_trace_id():
    return ''.join(['%02x' % random.randint(0, 255) for _ in range(16)])

def generate_span_id():
    return ''.join(['%02x' % random.randint(0, 255) for _ in range(8)])

def generate_trace(service_name, operation_name, duration_ms, status_code=200):
    trace_id = generate_trace_id()
    span_id = generate_span_id()
    start_time = int(time.time() * 1_000_000_000)
    end_time = start_time + (duration_ms * 1_000_000)
    
    trace_data = {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": service_name}},
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
                "spans": [{
                    "traceId": trace_id,
                    "spanId": span_id,
                    "name": operation_name,
                    "kind": 1,
                    "startTimeUnixNano": str(start_time),
                    "endTimeUnixNano": str(end_time),
                    "attributes": [
                        {"key": "http.method", "value": {"stringValue": random.choice(["GET", "POST", "PUT"])}},
                        {"key": "http.status_code", "value": {"intValue": status_code}},
                        {"key": "http.target", "value": {"stringValue": f"/api/{operation_name}"}},
                        {"key": "component", "value": {"stringValue": "http"}},
                        {"key": "span.kind", "value": {"stringValue": "server"}},
                    ],
                    "status": {"code": 1 if status_code == 200 else 2}
                }]
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
        return response.status_code in [200, 202]
    except Exception as e:
        print(f"❌ Error sending trace: {e}")
        return False

def main():
    print("🔍 RHINOMETRIC Continuous Trace Generator v2.2.0")
    print("=" * 60)
    print(f"Endpoint: {OTLP_ENDPOINT}")
    print(f"Services: {len(SERVICES)}")
    print("=" * 60)
    print()
    
    iteration = 0
    while True:
        iteration += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iteration #{iteration}")
        
        # Generate 5-10 traces per iteration
        num_traces = random.randint(5, 10)
        success_count = 0
        
        for _ in range(num_traces):
            service_name, operations = random.choice(SERVICES)
            operation = random.choice(operations)
            duration = random.randint(10, 500)
            status_code = random.choices([200, 200, 200, 500, 404], weights=[80, 10, 5, 3, 2])[0]
            
            if generate_trace(service_name, operation, duration, status_code):
                success_count += 1
                status_icon = "✅" if status_code == 200 else "⚠️"
                print(f"  {status_icon} {service_name}/{operation} ({duration}ms, {status_code})")
            
            time.sleep(0.3)
        
        print(f"  📊 Sent {success_count}/{num_traces} traces successfully")
        
        # Wait before next iteration (generate traces every 30 seconds)
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Trace generator stopped")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
