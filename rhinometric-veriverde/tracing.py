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
