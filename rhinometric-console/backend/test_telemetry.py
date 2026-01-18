"""
Simple test to verify OpenTelemetry is working
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
import time

def test_telemetry():
    print("Testing OpenTelemetry export to localhost:4317...")
    
    # Create resource
    resource = Resource(attributes={
        SERVICE_NAME: "test-backend",
    })
    
    # Create provider
    provider = TracerProvider(resource=resource)
    
    # Create exporter
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint="localhost:4317",
            insecure=True
        )
        print(f"✓ OTLP Exporter created successfully")
    except Exception as e:
        print(f"✗ Failed to create exporter: {e}")
        return
    
    # Add processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)
    
    # Get tracer and create test span
    tracer = trace.get_tracer(__name__)
    
    print("Creating test span...")
    with tracer.start_as_current_span("test_operation") as span:
        span.set_attribute("test.attribute", "value")
        print("  - Span created")
        time.sleep(0.5)
    
    print("Forcing span export...")
    provider.force_flush()
    
    print("✓ Test complete - check collector logs for traces from 'test-backend'")
    
if __name__ == "__main__":
    test_telemetry()
