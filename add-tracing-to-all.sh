#!/bin/bash
# Script para agregar OpenTelemetry a TODOS los servicios Rhinometric

echo "=== AGREGANDO OPENTELEMETRY A TODOS LOS SERVICIOS ==="

SERVICES=(
    "rhinometric-ai-anomaly"
    "rhinometric-api-proxy"
    "rhinometric-api-connector"
    "rhinometric-veriverde"
    "rhinometric-report-generator"
    "license-server-v2"
    "dashboard-builder"
)

for service in "${SERVICES[@]}"; do
    echo ""
    echo ">>> Procesando $service..."
    
    if [ -f "$service/requirements.txt" ]; then
        # Agregar OpenTelemetry si no existe
        if ! grep -q "opentelemetry" "$service/requirements.txt"; then
            echo "  ✓ Agregando OpenTelemetry a $service/requirements.txt"
            cat >> "$service/requirements.txt" << 'EOF'

# OpenTelemetry Auto-Instrumentation (v2.5.0)
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation==0.42b0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-requests==0.42b0
opentelemetry-instrumentation-logging==0.42b0
opentelemetry-exporter-otlp==1.21.0
EOF
        else
            echo "  ⏭ $service ya tiene OpenTelemetry"
        fi
    else
        echo "  ✗ $service no tiene requirements.txt"
    fi
    
    # Crear archivo de auto-instrumentación
    if [ ! -f "$service/tracing.py" ]; then
        echo "  ✓ Creando $service/tracing.py"
        cat > "$service/tracing.py" << 'TRACEPY'
"""
OpenTelemetry Auto-Instrumentation for Rhinometric v2.5.0
Automatically sends traces to Tempo via OpenTelemetry Collector
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
import os

def setup_tracing(service_name: str):
    """
    Setup OpenTelemetry tracing for a service
    """
    # Resource with service name
    resource = Resource(attributes={
        "service.name": service_name,
        "service.version": "2.5.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "production")
    })
    
    # Tracer Provider
    provider = TracerProvider(resource=resource)
    
    # OTLP Exporter (to OpenTelemetry Collector)
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "rhinometric-otel-collector:4317"),
        insecure=True
    )
    
    # Batch Span Processor
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set as global tracer
    trace.set_tracer_provider(provider)
    
    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument()
    
    # Auto-instrument requests library
    RequestsInstrumentor().instrument()
    
    # Auto-instrument logging
    LoggingInstrumentor().instrument()
    
    print(f"✓ OpenTelemetry tracing initialized for {service_name}")
    return trace.get_tracer(__name__)
TRACEPY
    fi
done

echo ""
echo "=== COMPLETADO ==="
echo "Ahora REBUILD todos los servicios con:"
echo "docker compose -f docker-compose-v2.5.0.yml build --no-cache"
