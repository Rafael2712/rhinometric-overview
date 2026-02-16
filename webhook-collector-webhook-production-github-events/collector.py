"""
RHINOMETRIC v2.5.0 - Webhook Collector Template
================================================

Auto-generated webhook receiver for event monitoring.

Configuration variables (injected by system):
- WEBHOOK_PORT: 8094
- WEBHOOK_PATH:  /webhook/github
- METRICS_PORT: 9326
"""

import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from datetime import datetime
import logging
import json

# ============================================================================
# CONFIGURATION (auto-injected)
# ============================================================================

WEBHOOK_PORT = 8094
WEBHOOK_PATH = "/webhook/github"
WEBHOOK_SECRET = "" if "" else None
METRICS_PORT = 9326

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
    
    try:
        # Validate secret if configured
        if WEBHOOK_SECRET:
            auth_header = request.headers.get('X-Webhook-Secret')
            if auth_header != WEBHOOK_SECRET:
                webhook_events_received_total.labels(
                    event_type='unknown',
                    status='unauthorized'
                ).inc()
                raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
        # Read payload
        body = await request.body()
        payload_size = len(body)
        
        try:
            data = json.loads(body.decode())
            event_type = data.get('type', data.get('event', 'unknown'))
        except json.JSONDecodeError:
            event_type = 'binary'
        
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
        raise
    
    except Exception as e:
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