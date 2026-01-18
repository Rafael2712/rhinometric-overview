"""
RHINOMETRIC v2.5.0 - Webhook Collector
=======================================

Webhook receiver for GitHub events testing
"""

import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from datetime import datetime
import logging
import json
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import os

# ============================================================================
# OPENTELEMETRY CONFIGURATION
# ============================================================================

# Initialize OpenTelemetry
resource = Resource.create({
    "service.name": "webhook-collector-github-test",
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
# CONFIGURATION
# ============================================================================

WEBHOOK_PORT = 8090
WEBHOOK_PATH = "/webhook/github"
WEBHOOK_SECRET = None
METRICS_PORT = 9350

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

# Event counters
webhook_events_received_total = Counter(
    'webhook_events_received_total',
    'Total webhook events received',
    ['event_type', 'status']
)

# Processing time
webhook_processing_duration_seconds = Histogram(
    'webhook_processing_duration_seconds',
    'Webhook event processing time in seconds',
    ['event_type']
)

# Event rate
webhook_events_per_second = Gauge(
    'webhook_events_per_second',
    'Current webhook event rate'
)

# Last event timestamp
webhook_last_event_timestamp = Gauge(
    'webhook_last_event_timestamp',
    'Timestamp of last received event',
    ['event_type']
)

# Payload size
webhook_payload_size_bytes = Histogram(
    'webhook_payload_size_bytes',
    'Webhook payload size in bytes',
    ['event_type']
)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="RHINOMETRIC Webhook Collector",
    description="Auto-generated webhook receiver",
    version="2.5.0"
)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Event counter for rate calculation
event_count = 0
last_rate_update = datetime.now()

# ============================================================================
# WEBHOOK ENDPOINT
# ============================================================================

@app.post(WEBHOOK_PATH)
async def receive_webhook(request: Request):
    """
    Receive and process webhook events.
    """
    global event_count
    
    start_time = datetime.now()
    
    # Create OTEL span for webhook processing
    with tracer.start_as_current_span("webhook_event") as span:
        try:
            # Validate secret if configured
            if WEBHOOK_SECRET:
                auth_header = request.headers.get('X-Webhook-Secret')
                if auth_header != WEBHOOK_SECRET:
                    span.set_attribute("webhook.auth", "failed")
                    span.set_attribute("webhook.status", "unauthorized")
                    webhook_events_received_total.labels(
                        event_type='unknown',
                        status='unauthorized'
                    ).inc()
                    raise HTTPException(status_code=401, detail="Invalid webhook secret")
                span.set_attribute("webhook.auth", "success")
            
            # Read payload
            body = await request.body()
            payload_size = len(body)
            
            try:
                data = json.loads(body.decode())
                event_type = data.get('type', data.get('event', data.get('action', 'unknown')))
            except json.JSONDecodeError:
                event_type = 'binary'
            
            # Add OTEL attributes
            span.set_attribute("webhook.path", WEBHOOK_PATH)
            span.set_attribute("webhook.event_type", event_type)
            span.set_attribute("webhook.payload_size", payload_size)
            span.set_attribute("webhook.method", "POST")
            span.set_attribute("webhook.status", "success")
            
            # Update metrics
            webhook_events_received_total.labels(
                event_type=event_type,
                status='success'
            ).inc()
            
            webhook_payload_size_bytes.labels(
                event_type=event_type
            ).observe(payload_size)
            
            duration = (datetime.now() - start_time).total_seconds()
            webhook_processing_duration_seconds.labels(
                event_type=event_type
            ).observe(duration)
            
            webhook_last_event_timestamp.labels(
                event_type=event_type
            ).set(datetime.now().timestamp())
            
            event_count += 1
            
            span.set_attribute("webhook.duration", duration)
            
            logger.info(f"📨 Webhook received: type={event_type}, size={payload_size}B, duration={duration:.3f}s")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Webhook received",
                    "event_type": event_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except HTTPException:
            span.set_attribute("webhook.status", "error")
            span.set_attribute("webhook.error", "http_exception")
            raise
        
        except Exception as e:
            span.set_attribute("webhook.status", "error")
            span.set_attribute("webhook.error", str(e))
            logger.error(f"❌ Error processing webhook: {e}")
            webhook_events_received_total.labels(
                event_type='unknown',
                status='error'
            ).inc()
            
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint with info"""
    return {
        "service": "RHINOMETRIC Webhook Collector",
        "version": "2.5.0",
        "webhook_path": WEBHOOK_PATH,
        "metrics_url": f"http://localhost:{METRICS_PORT}/metrics"
    }

# ============================================================================
# RATE CALCULATOR
# ============================================================================

async def calculate_rate():
    """
    Calculate webhook event rate periodically.
    """
    global event_count, last_rate_update
    
    while True:
        await asyncio.sleep(10)
        
        now = datetime.now()
        elapsed = (now - last_rate_update).total_seconds()
        
        if elapsed > 0:
            rate = event_count / elapsed
            webhook_events_per_second.set(rate)
            logger.info(f"📊 Event rate: {rate:.2f} events/s")
            
            event_count = 0
            last_rate_update = now

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(METRICS_PORT)
    logger.info(f"📊 Prometheus metrics server started on port {METRICS_PORT}")
    
    # Start rate calculator in background
    import threading
    def run_rate_calculator():
        asyncio.run(calculate_rate())
    
    rate_thread = threading.Thread(target=run_rate_calculator, daemon=True)
    rate_thread.start()
    
    # Start FastAPI webhook server
    logger.info(f"🚀 Webhook Collector started")
    logger.info(f"🪝 Webhook endpoint: http://0.0.0.0:{WEBHOOK_PORT}{WEBHOOK_PATH}")
    logger.info(f"📊 Metrics: http://localhost:{METRICS_PORT}/metrics")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        log_level="info"
    )
