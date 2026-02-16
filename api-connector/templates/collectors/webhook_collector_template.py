"""
RHINOMETRIC v2.5.0 - Webhook Collector Template
================================================

Auto-generated webhook receiver for event monitoring.

Configuration variables (injected by system):
- WEBHOOK_PORT: {{ webhook_port }}
- WEBHOOK_PATH: {{ webhook_path }}
- METRICS_PORT: {{ metrics_port }}
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
    "service.name": f"webhook-collector-{{ collector_name | default('default') }}",
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

WEBHOOK_PORT = {{ webhook_port | default(8080) }}
WEBHOOK_PATH = "{{ webhook_path | default('/webhook') | trim }}"
WEBHOOK_SECRET = "{{ webhook_secret | trim }}" if "{{ webhook_secret | trim }}" else None
METRICS_PORT = {{ metrics_port | default(9300) }}

# Security settings
MAX_PAYLOAD_SIZE = {{ max_payload_size | default(10485760) }}  # 10MB default
RATE_LIMIT_PER_MINUTE = {{ rate_limit_per_minute | default(1000) }}  # 1000 requests/min
ALLOWED_CONTENT_TYPES = ['application/json', 'application/x-www-form-urlencoded', 'text/plain']
REQUEST_TIMEOUT = {{ request_timeout | default(30) }}  # seconds

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

# Rate limiting storage (in-memory, consider Redis for production)
from collections import defaultdict, deque
import time

request_history = defaultdict(deque)  # IP -> [timestamp1, timestamp2, ...]

def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client IP has exceeded rate limit.
    Returns True if allowed, False if rate limited.
    """
    now = time.time()
    minute_ago = now - 60
    
    # Clean old requests
    while request_history[client_ip] and request_history[client_ip][0] < minute_ago:
        request_history[client_ip].popleft()
    
    # Check limit
    if len(request_history[client_ip]) >= RATE_LIMIT_PER_MINUTE:
        return False
    
    # Add current request
    request_history[client_ip].append(now)
    return True

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
            # 1. Rate limiting check
            client_ip = request.client.host if request.client else "unknown"
            span.set_attribute("webhook.client_ip", client_ip)
            
            if not check_rate_limit(client_ip):
                span.set_attribute("webhook.status", "rate_limited")
                webhook_events_received_total.labels(
                    event_type='unknown',
                    status='rate_limited'
                ).inc()
                logger.warning(f"⚠️ Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # 2. Content-Type validation
            content_type = request.headers.get('content-type', '').split(';')[0].strip()
            if content_type not in ALLOWED_CONTENT_TYPES:
                span.set_attribute("webhook.status", "invalid_content_type")
                webhook_events_received_total.labels(
                    event_type='unknown',
                    status='invalid_content_type'
                ).inc()
                logger.warning(f"⚠️ Invalid Content-Type: {content_type}")
                raise HTTPException(status_code=415, detail=f"Unsupported Content-Type: {content_type}")
            
            # 3. Payload size check
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > MAX_PAYLOAD_SIZE:
                span.set_attribute("webhook.status", "payload_too_large")
                webhook_events_received_total.labels(
                    event_type='unknown',
                    status='payload_too_large'
                ).inc()
                logger.warning(f"⚠️ Payload too large: {content_length} bytes")
                raise HTTPException(status_code=413, detail=f"Payload too large (max {MAX_PAYLOAD_SIZE} bytes)")
            
            # 4. Secret validation (if configured)
            if WEBHOOK_SECRET:
                auth_header = request.headers.get('X-Webhook-Secret')
                if auth_header != WEBHOOK_SECRET:
                    span.set_attribute("webhook.auth", "failed")
                    span.set_attribute("webhook.status", "unauthorized")
                    webhook_events_received_total.labels(
                        event_type='unknown',
                        status='unauthorized'
                    ).inc()
                    logger.warning(f"⚠️ Invalid webhook secret from IP: {client_ip}")
                    raise HTTPException(status_code=401, detail="Invalid webhook secret")
                span.set_attribute("webhook.auth", "success")
            
            # 5. Read and validate payload
            body = await request.body()
            payload_size = len(body)
            
            # Double-check payload size after reading
            if payload_size > MAX_PAYLOAD_SIZE:
                span.set_attribute("webhook.status", "payload_too_large")
                webhook_events_received_total.labels(
                    event_type='unknown',
                    status='payload_too_large'
                ).inc()
                raise HTTPException(status_code=413, detail=f"Payload too large: {payload_size} bytes")
            
            # Parse payload
            try:
                if content_type == 'application/json':
                    data = json.loads(body.decode('utf-8'))
                    event_type = data.get('type', data.get('event', data.get('action', 'unknown')))
                else:
                    # Non-JSON payload
                    data = {'raw': body.decode('utf-8', errors='ignore')}
                    event_type = 'text'
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                span.set_attribute("webhook.parse_error", str(e))
                event_type = 'parse_error'
                data = {'error': 'Failed to parse payload'}
                logger.warning(f"⚠️ Failed to parse payload: {e}")
            
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
        
        except HTTPException as e:
            span.set_attribute("webhook.status", "http_error")
            span.set_attribute("webhook.error_code", e.status_code)
            span.set_attribute("webhook.error_detail", e.detail)
            logger.error(f"❌ HTTP Exception: {e.status_code} - {e.detail}")
            raise
        
        except Exception as e:
            span.set_attribute("webhook.status", "internal_error")
            span.set_attribute("webhook.error", str(e))
            span.set_attribute("webhook.error_type", type(e).__name__)
            logger.error(f"❌ Unexpected error processing webhook: {type(e).__name__}: {e}")
            webhook_events_received_total.labels(
                event_type='unknown',
                status='internal_error'
            ).inc()
            
            # Don't expose internal errors to client
            raise HTTPException(status_code=500, detail="Internal server error")

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
