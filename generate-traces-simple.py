#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
RHINOMETRIC v2.4.0 - Simple Trace Generator for Tempo
═══════════════════════════════════════════════════════════════════════════

Generates sample traces and sends them to OTEL Collector → Tempo

Usage:
    python3 generate-traces-simple.py

Requirements:
    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
"""

import time
import random
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Configure resource attributes
resource = Resource(attributes={
    "service.name": "rhinometric-trace-generator",
    "service.version": "2.4.0",
    "deployment.environment": "trial",
    "telemetry.sdk.name": "opentelemetry",
    "telemetry.sdk.language": "python",
})

# Set up tracer provider
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Configure OTLP exporter (sends to OTEL Collector)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",  # OTEL Collector gRPC endpoint
    insecure=True
)

# Add batch span processor
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Sample services to simulate
SERVICES = [
    "api-gateway",
    "auth-service",
    "user-service",
    "payment-service",
    "inventory-service",
    "notification-service"
]

# Sample operations
OPERATIONS = [
    "GET /api/users",
    "POST /api/login",
    "GET /api/products",
    "POST /api/orders",
    "PUT /api/users/{id}",
    "DELETE /api/sessions",
]

def generate_trace():
    """Generate a sample distributed trace"""
    
    service = random.choice(SERVICES)
    operation = random.choice(OPERATIONS)
    
    # Create root span
    with tracer.start_as_current_span(
        name=f"{service}: {operation}",
        kind=trace.SpanKind.SERVER
    ) as root_span:
        
        root_span.set_attribute("http.method", operation.split()[0])
        root_span.set_attribute("http.route", operation.split()[1])
        root_span.set_attribute("http.status_code", random.choice([200, 200, 200, 201, 400, 500]))
        root_span.set_attribute("service.name", service)
        
        # Simulate processing time
        time.sleep(random.uniform(0.01, 0.1))
        
        # Create child span (database operation)
        with tracer.start_as_current_span(
            name="db.query",
            kind=trace.SpanKind.CLIENT
        ) as db_span:
            db_span.set_attribute("db.system", "postgresql")
            db_span.set_attribute("db.name", "rhinometric")
            db_span.set_attribute("db.operation", "SELECT")
            time.sleep(random.uniform(0.005, 0.05))
        
        # Create another child span (cache check)
        with tracer.start_as_current_span(
            name="cache.get",
            kind=trace.SpanKind.CLIENT
        ) as cache_span:
            cache_span.set_attribute("cache.system", "redis")
            cache_span.set_attribute("cache.hit", random.choice([True, False]))
            time.sleep(random.uniform(0.001, 0.01))

def main():
    """Generate traces continuously"""
    print("🦏 Rhinometric Trace Generator v2.4.0")
    print("=" * 60)
    print("Generating traces and sending to OTEL Collector (localhost:4317)")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    trace_count = 0
    
    try:
        while True:
            generate_trace()
            trace_count += 1
            
            if trace_count % 10 == 0:
                print(f"✓ Generated {trace_count} traces...")
            
            # Wait 2-5 seconds between traces
            time.sleep(random.uniform(2, 5))
            
    except KeyboardInterrupt:
        print(f"\n\n✓ Generated {trace_count} total traces")
        print("Shutting down...")
        
        # Force flush remaining spans
        trace.get_tracer_provider().force_flush()
        print("✓ All traces sent to Tempo")

if __name__ == "__main__":
    main()
