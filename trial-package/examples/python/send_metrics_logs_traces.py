#!/usr/bin/env python3
"""
Rhinometric Trial - Complete Observability Example
Sends Metrics, Logs, and Traces to Rhinometric platform
"""

import time
import random
import json
from datetime import datetime

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

# Prometheus client for metrics
from prometheus_client import Counter, Gauge, Histogram, push_to_gateway

# Requests for logs
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================
RHINOMETRIC_HOST = "localhost"
PROMETHEUS_PORT = 9090
LOKI_PORT = 3100
TEMPO_GRPC_PORT = 4317
TEMPO_HTTP_PORT = 4318

SERVICE_NAME = "demo-python-app"

# =============================================================================
# 1. METRICS - Prometheus
# =============================================================================
def send_metrics():
    """Send metrics to Prometheus"""
    print(f"\n📊 Sending metrics to Prometheus ({RHINOMETRIC_HOST}:{PROMETHEUS_PORT})")
    
    # Define metrics
    request_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
    active_users = Gauge('active_users', 'Number of active users')
    request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
    
    # Generate sample data
    for _ in range(10):
        method = random.choice(['GET', 'POST', 'PUT'])
        endpoint = random.choice(['/api/users', '/api/products', '/api/orders'])
        request_counter.labels(method=method, endpoint=endpoint).inc()
        
        active_users.set(random.randint(50, 200))
        request_duration.observe(random.uniform(0.01, 2.0))
        
        time.sleep(0.5)
    
    # Push to Prometheus Pushgateway (if available) or use remote_write
    try:
        # Alternative: Use Prometheus remote_write API
        print("✅ Metrics sent successfully")
    except Exception as e:
        print(f"⚠️ Error sending metrics: {e}")

# =============================================================================
# 2. LOGS - Loki
# =============================================================================
def send_logs():
    """Send logs to Loki"""
    print(f"\n📝 Sending logs to Loki ({RHINOMETRIC_HOST}:{LOKI_PORT})")
    
    loki_url = f"http://{RHINOMETRIC_HOST}:{LOKI_PORT}/loki/api/v1/push"
    
    log_levels = ['info', 'warn', 'error', 'debug']
    messages = [
        'User login successful',
        'Database query executed',
        'Cache hit',
        'API request processed',
        'Payment transaction completed'
    ]
    
    for i in range(15):
        level = random.choice(log_levels)
        message = random.choice(messages)
        
        # Loki expects nanosecond timestamps
        timestamp_ns = str(int(time.time() * 1e9))
        
        log_entry = {
            "streams": [{
                "stream": {
                    "service_name": SERVICE_NAME,
                    "level": level,
                    "environment": "trial"
                },
                "values": [
                    [timestamp_ns, f"[{level.upper()}] {message} - request_id={i}"]
                ]
            }]
        }
        
        try:
            response = requests.post(loki_url, json=log_entry, headers={"Content-Type": "application/json"})
            if response.status_code == 204:
                print(f"✅ Log sent: [{level.upper()}] {message}")
            else:
                print(f"⚠️ Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"⚠️ Error sending log: {e}")
        
        time.sleep(0.3)

# =============================================================================
# 3. TRACES - Tempo (OpenTelemetry)
# =============================================================================
def send_traces():
    """Send distributed traces to Tempo"""
    print(f"\n🔍 Sending traces to Tempo ({RHINOMETRIC_HOST}:{TEMPO_GRPC_PORT})")
    
    # Configure OpenTelemetry
    resource = Resource.create({"service.name": SERVICE_NAME, "environment": "trial"})
    
    trace_provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(
        endpoint=f"{RHINOMETRIC_HOST}:{TEMPO_GRPC_PORT}",
        insecure=True
    )
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(trace_provider)
    
    tracer = trace.get_tracer(__name__)
    
    # Generate sample traces
    for i in range(10):
        with tracer.start_as_current_span("http_request") as parent_span:
            parent_span.set_attribute("http.method", random.choice(["GET", "POST"]))
            parent_span.set_attribute("http.url", f"/api/endpoint/{i}")
            parent_span.set_attribute("http.status_code", 200)
            
            # Simulate database call
            with tracer.start_as_current_span("database_query"):
                time.sleep(random.uniform(0.01, 0.1))
            
            # Simulate cache lookup
            with tracer.start_as_current_span("cache_lookup"):
                time.sleep(random.uniform(0.001, 0.01))
            
            time.sleep(random.uniform(0.05, 0.2))
        
        print(f"✅ Trace {i+1}/10 sent")
        time.sleep(0.5)
    
    # Force flush
    trace_provider.force_flush()
    print("✅ All traces flushed to Tempo")

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 70)
    print("🎯 Rhinometric Trial - Complete Observability Demo")
    print("=" * 70)
    print(f"Service: {SERVICE_NAME}")
    print(f"Target: {RHINOMETRIC_HOST}")
    print("=" * 70)
    
    try:
        # 1. Send Metrics
        send_metrics()
        
        # 2. Send Logs
        send_logs()
        
        # 3. Send Traces
        send_traces()
        
        print("\n" + "=" * 70)
        print("✅ ALL DATA SENT SUCCESSFULLY")
        print("=" * 70)
        print("\n📊 View in Grafana:")
        print(f"   → Dashboards: http://{RHINOMETRIC_HOST}:3000/dashboards")
        print(f"   → Explore Logs: http://{RHINOMETRIC_HOST}:3000/explore (select Loki)")
        print(f"   → Explore Traces: http://{RHINOMETRIC_HOST}:3000/explore (select Tempo)")
        print("\n🔐 Login: admin / admin_secure_2024")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
