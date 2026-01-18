"""
OpenTelemetry instrumentation for FastAPI backend
Exports traces to Tempo via OTLP
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_telemetry(app, service_name: str = "rhinometric-console-backend", service_version: str = "0.1.0"):
    """
    Setup OpenTelemetry tracing for FastAPI application
    Exports to Tempo on localhost:4317 (gRPC)
    """
    
    # Create resource with service information
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": "development"
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter to send to Tempo
    otlp_exporter = OTLPSpanExporter(
        endpoint="localhost:4317",  # Tempo gRPC endpoint (no http:// prefix for gRPC)
        insecure=True
    )
    
    # Add batch span processor with faster export
    span_processor = BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=2048,
        schedule_delay_millis=1000,  # Export every 1 second (default is 5s)
        max_export_batch_size=512
    )
    provider.add_span_processor(span_processor)
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument httpx (for outgoing HTTP requests to Prometheus, Loki, etc.)
    HTTPXClientInstrumentor().instrument()
    
    print(f"[OK] OpenTelemetry initialized for {service_name}")
    print(f"[OK] Exporting traces to Tempo at localhost:4317")
    
    return provider
