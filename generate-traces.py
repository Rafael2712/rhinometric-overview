#!/usr/bin/env python3
"""
Generate test traces for Tempo using OTLP protocol
"""
import json
import random
import time
import requests
from datetime import datetime

TEMPO_OTLP_HTTP = "http://localhost:4318/v1/traces"

def generate_trace_id():
    """Generate a random 16-byte trace ID"""
    return ''.join(['%02x' % random.randint(0, 255) for _ in range(16)])

def generate_span_id():
    """Generate a random 8-byte span ID"""
    return ''.join(['%02x' % random.randint(0, 255) for _ in range(8)])

def generate_trace(service_name, operation_name, duration_ms):
    """Generate a single trace with OTLP format"""
    trace_id = generate_trace_id()
    span_id = generate_span_id()
    start_time = int(time.time() * 1_000_000_000)  # nanoseconds
    end_time = start_time + (duration_ms * 1_000_000)
    
    trace_data = {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": service_name}},
                    {"key": "service.version", "value": {"stringValue": "2.2.0"}},
                    {"key": "deployment.environment", "value": {"stringValue": "production"}}
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
                    "kind": 1,  # SPAN_KIND_INTERNAL
                    "startTimeUnixNano": str(start_time),
                    "endTimeUnixNano": str(end_time),
                    "attributes": [
                        {"key": "http.method", "value": {"stringValue": "GET"}},
                        {"key": "http.status_code", "value": {"intValue": 200}},
                        {"key": "http.target", "value": {"stringValue": f"/api/{operation_name}"}},
                        {"key": "component", "value": {"stringValue": "http"}}
                    ],
                    "status": {"code": 1}  # STATUS_CODE_OK
                }]
            }]
        }]
    }
    
    try:
        response = requests.post(
            TEMPO_OTLP_HTTP,
            json=trace_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        return response.status_code == 200 or response.status_code == 202
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔍 Generando trazas de prueba para Tempo...")
    print()
    
    traces = [
        ("rhinometric-grafana", "render_dashboard", 10),
        ("rhinometric-prometheus", "query_metrics", 10),
        ("rhinometric-veriverde", "collect_sustainability_metrics", 10),
        ("rhinometric-ai-anomaly", "detect_anomalies", 10),
        ("rhinometric-license-server", "validate_license", 10),
        ("rhinometric-api-proxy", "proxy_request", 10),
        ("rhinometric-loki", "push_logs", 5),
        ("rhinometric-postgres", "execute_query", 5),
    ]
    
    success_count = 0
    total_count = 0
    
    for service, operation, count in traces:
        print(f"📊 Generando {count} trazas para {service}...")
        for i in range(count):
            duration = random.randint(20, 500)
            if generate_trace(service, operation, duration):
                success_count += 1
            total_count += 1
            time.sleep(0.1)
    
    print()
    print(f"✅ Generación completa: {success_count}/{total_count} trazas exitosas")
    print()
    print("🔗 Verifica en Grafana:")
    print("   http://localhost:3000/explore")
    print("   Selecciona 'Tempo' como datasource")
    print()
    print("🔗 O consulta en Tempo:")
    print("   http://localhost:3200/api/search")

if __name__ == "__main__":
    main()
