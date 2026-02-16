"""
RHINOMETRIC v2.5.0 - MQTT Collector Template
=============================================

Auto-generated MQTT collector for IoT monitoring.

Configuration variables (injected by system):
- MQTT_BROKER: test.mosquitto.org
- MQTT_PORT: 1883
- MQTT_TOPICS: ['test/otel/trace', 'sensors/#']
- METRICS_PORT: 9324
"""

import asyncio
import aiomqtt
import json
from prometheus_client import start_http_server, Counter, Gauge
from datetime import datetime
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import os

# ============================================================================
# OPENTELEMETRY CONFIGURATION
# ============================================================================

# Initialize OpenTelemetry
resource = Resource.create({
    "service.name": f"mqtt-collector-default",
    "deployment.environment": "production",
    "service.version": "2.5.0"
})

provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
    insecure=True
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# ============================================================================
# CONFIGURATION (auto-injected)
# ============================================================================

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_USERNAME = "None" if "None" else None
MQTT_PASSWORD = "None" if "None" else None
MQTT_CLIENT_ID = "rhinometric-collector"
MQTT_TOPICS = ["test/otel/trace", "sensors/#"]
USE_TLS = False
METRICS_PORT = 9324

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Connection status
mqtt_connection_status = Gauge(
    'mqtt_connection_status',
    'MQTT broker connection status (1=connected, 0=disconnected)'
)

# Message counters
mqtt_messages_received_total = Counter(
    'mqtt_messages_received_total',
    'Total MQTT messages received',
    ['topic', 'device_type']
)

# Active topics
mqtt_active_topics = Gauge(
    'mqtt_active_topics',
    'Number of active MQTT topics'
)

# Message rate
mqtt_messages_per_second = Gauge(
    'mqtt_messages_per_second',
    'Current MQTT message rate'
)

# Last message timestamp
mqtt_last_message_timestamp = Gauge(
    'mqtt_last_message_timestamp',
    'Timestamp of last received message',
    ['topic']
)

# ============================================================================
# MESSAGE PROCESSOR
# ============================================================================

def process_message(topic: str, payload: bytes):
    """
    Process incoming MQTT message and extract metrics.
    """
    with tracer.start_as_current_span("process_mqtt_message") as span:
        try:
            span.set_attribute("mqtt.topic", topic)
            span.set_attribute("mqtt.payload.size", len(payload))
            
            # Try to parse JSON payload
            try:
                data = json.loads(payload.decode())
                device_type = data.get('device_type', data.get('_type', 'unknown'))
                span.set_attribute("mqtt.device_type", device_type)
            except (json.JSONDecodeError, UnicodeDecodeError):
                device_type = 'binary'
                span.set_attribute("mqtt.device_type", "binary")
            
            # Update metrics
            mqtt_messages_received_total.labels(
                topic=topic,
                device_type=device_type
            ).inc()
            
            mqtt_last_message_timestamp.labels(topic=topic).set(
                datetime.now().timestamp()
            )
            
            span.set_attribute("mqtt.processing.status", "success")
            logger.debug(f"📨 Message from {topic} (type: {device_type})")
            
        except Exception as e:
            span.set_attribute("mqtt.processing.status", "error")
            span.record_exception(e)
            logger.error(f"❌ Error processing message: {e}")

# ============================================================================
# MQTT CLIENT
# ============================================================================

async def mqtt_listener():
    """
    Connect to MQTT broker and listen for messages.
    """
    logger.info(f"🚀 MQTT Collector starting...")
    logger.info(f"📡 Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"🔖 Topics: {', '.join(MQTT_TOPICS)}")
    logger.info(f"📊 Metrics: http://localhost:{METRICS_PORT}/metrics")
    
    reconnect_interval = 5
    
    while True:
        with tracer.start_as_current_span("mqtt_connection") as conn_span:
            try:
                conn_span.set_attribute("mqtt.broker.host", MQTT_BROKER)
                conn_span.set_attribute("mqtt.broker.port", MQTT_PORT)
                conn_span.set_attribute("mqtt.topics.count", len(MQTT_TOPICS))
                
                # Connect to broker
                async with aiomqtt.Client(
                    hostname=MQTT_BROKER,
                    port=MQTT_PORT,
                    username=MQTT_USERNAME,
                    password=MQTT_PASSWORD,
                    identifier=MQTT_CLIENT_ID,
                    clean_session=True,
                    keepalive=60
                ) as client:
                    
                    logger.info(f"✅ Connected to {MQTT_BROKER}:{MQTT_PORT}")
                    mqtt_connection_status.set(1)
                    conn_span.set_attribute("mqtt.connection.status", "connected")
                
                # Subscribe to topics
                for topic in MQTT_TOPICS:
                    await client.subscribe(topic)
                    logger.info(f"🔖 Subscribed to: {topic}")
                
                mqtt_active_topics.set(len(MQTT_TOPICS))
                
                # Message counter for rate calculation
                message_count = 0
                last_rate_update = datetime.now()
                
                # Listen for messages
                async for message in client.messages:
                    process_message(message.topic.value, message.payload)
                    
                    message_count += 1
                    
                    # Update message rate every 10 seconds
                    now = datetime.now()
                    elapsed = (now - last_rate_update).total_seconds()
                    if elapsed >= 10:
                        rate = message_count / elapsed
                        mqtt_messages_per_second.set(rate)
                        logger.info(f"📊 Message rate: {rate:.2f} msg/s")
                        message_count = 0
                        last_rate_update = now
        
            except aiomqtt.MqttError as e:
                conn_span.set_attribute("mqtt.connection.status", "error")
                conn_span.record_exception(e)
                logger.error(f"❌ MQTT error: {e}")
                mqtt_connection_status.set(0)
                logger.info(f"🔄 Reconnecting in {reconnect_interval}s...")
                await asyncio.sleep(reconnect_interval)
                
            except Exception as e:
                conn_span.set_attribute("mqtt.connection.status", "error")
                conn_span.record_exception(e)
                logger.error(f"❌ Unexpected error: {e}")
                mqtt_connection_status.set(0)
                await asyncio.sleep(reconnect_interval)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(METRICS_PORT)
    logger.info(f"📊 Prometheus metrics server started on port {METRICS_PORT}")
    
    # Start MQTT listener
    try:
        asyncio.run(mqtt_listener())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down MQTT collector...")
        mqtt_connection_status.set(0)