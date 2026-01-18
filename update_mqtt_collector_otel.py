#!/usr/bin/env python3
"""
Script para agregar instrumentación OpenTelemetry a un colector MQTT existente
"""

import sys

def add_otel_to_mqtt_collector(collector_code, collector_name):
    """
    Añade instrumentación OpenTelemetry a código de colector MQTT existente
    """
    
    # 1. Agregar importaciones OTEL después de las importaciones existentes
    otel_imports = """from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import os
"""
    
    # Encontrar donde termina la sección de LOGGING y agregar OTEL config
    otel_config = f"""
# ============================================================================
# OPENTELEMETRY CONFIGURATION
# ============================================================================

# Initialize OpenTelemetry
resource = Resource.create({{
    "service.name": "mqtt-collector-{collector_name}",
    "deployment.environment": "production",
    "service.version": "2.5.0"
}})

provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
    insecure=True
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)
"""
    
    # Insertar importaciones después de "import logging"
    import_marker = "import logging"
    if import_marker in collector_code:
        parts = collector_code.split(import_marker, 1)
        collector_code = parts[0] + import_marker + "\n" + otel_imports + parts[1]
    
    # Insertar configuración OTEL después de logger = logging.getLogger(__name__)
    config_marker = "logger = logging.getLogger(__name__)"
    if config_marker in collector_code:
        parts = collector_code.split(config_marker, 1)
        collector_code = parts[0] + config_marker + "\n" + otel_config + parts[1]
    
    # 2. Instrumentar process_message con span
    old_process_def = "def process_message(topic: str, payload: bytes):"
    new_process_def = """def process_message(topic: str, payload: bytes):
    with tracer.start_as_current_span("process_mqtt_message") as span:
        span.set_attribute("mqtt.topic", topic)
        span.set_attribute("mqtt.payload.size", len(payload))"""
    
    if old_process_def in collector_code:
        collector_code = collector_code.replace(old_process_def, new_process_def)
        # Indentar el resto de la función
        # Esto es complejo, mejor hacerlo manual para garantizar corrección
    
    return collector_code

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_mqtt_collector_otel.py <collector_code_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    
    collector_name = sys.argv[2] if len(sys.argv) > 2 else "default"
    updated_code = add_otel_to_mqtt_collector(code, collector_name)
    
    print(updated_code)
