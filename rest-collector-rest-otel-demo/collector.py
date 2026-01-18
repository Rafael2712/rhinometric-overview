"""
RHINOMETRIC v2.5.0 - REST API Collector Template
=================================================

Auto-generated REST API collector for monitoring external APIs.

Configuration variables (injected by system):
- API_URL: https://jsonplaceholder.typicode.com
- API_TOKEN: None
- API_ENDPOINT: /posts/1
- API_METHOD: GET
- METRICS_PORT: 9327
- FETCH_INTERVAL: 30
"""

import asyncio
import requests
import json
from prometheus_client import start_http_server, Counter, Gauge, Histogram
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
    "service.name": f"rest-collector-default",
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

API_URL = "https://jsonplaceholder.typicode.com"
API_TOKEN = "None"
API_ENDPOINT = "/posts/1"
API_METHOD = "GET"
API_HEADERS = {}
METRICS_PORT = 9327
FETCH_INTERVAL = 30

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

# Counters
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests made',
    ['endpoint', 'method', 'status']
)

api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type']
)

# Gauges
api_data_count = Gauge(
    'api_data_count',
    'Number of records returned by API'
)

api_last_success_timestamp = Gauge(
    'api_last_success_timestamp',
    'Timestamp of last successful API call'
)

# Histograms
api_response_time_seconds = Histogram(
    'api_response_time_seconds',
    'API response time in seconds',
    ['endpoint', 'method']
)

# ============================================================================
# DATA FETCHER
# ============================================================================

async def fetch_data():
    """
    Fetch data from REST API periodically.
    """
    logger.info(f"🚀 REST Collector started for {API_URL}{API_ENDPOINT}")
    logger.info(f"📊 Metrics exposed on port {METRICS_PORT}")
    logger.info(f"⏱️  Fetch interval: {FETCH_INTERVAL}s")
    
    while True:
        with tracer.start_as_current_span("api_request") as span:
            try:
                span.set_attribute("http.method", API_METHOD)
                span.set_attribute("http.url", f"{API_URL}{API_ENDPOINT}")
                span.set_attribute("http.endpoint", API_ENDPOINT)
                
                # Prepare headers
                headers = API_HEADERS.copy()
                if API_TOKEN:
                    headers['Authorization'] = f"Bearer {API_TOKEN}"
                
                # Make request with timing
                start_time = datetime.now()
                
                response = requests.request(
                    method=API_METHOD,
                    url=f"{API_URL}{API_ENDPOINT}",
                    headers=headers,
                    timeout=30
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_time", duration)
                
                # Record metrics
                api_requests_total.labels(
                    endpoint=API_ENDPOINT,
                    method=API_METHOD,
                    status=response.status_code
                ).inc()
                
                api_response_time_seconds.labels(
                    endpoint=API_ENDPOINT,
                    method=API_METHOD
                ).observe(duration)
            
                # Process response
                if response.status_code == 200:
                    span.set_attribute("api.response.status", "success")
                    try:
                        data = response.json()
                        
                        # Count records
                        if isinstance(data, list):
                            record_count = len(data)
                        elif isinstance(data, dict):
                            record_count = len(data.get('items', data.get('results', [data])))
                        else:
                            record_count = 1
                        
                        span.set_attribute("api.records.count", record_count)
                        api_data_count.set(record_count)
                        api_last_success_timestamp.set(datetime.now().timestamp())
                        
                        logger.info(f"✅ Fetched {record_count} records from {API_ENDPOINT} ({duration:.2f}s)")
                        
                    except json.JSONDecodeError as e:
                        span.set_attribute("api.response.status", "json_error")
                        span.record_exception(e)
                        logger.warning(f"⚠️  Response is not JSON: {e}")
                        api_errors_total.labels(
                            endpoint=API_ENDPOINT,
                            error_type='json_decode_error'
                        ).inc()
                else:
                    span.set_attribute("api.response.status", "http_error")
                    logger.warning(f"⚠️  API returned status {response.status_code}")
                    api_errors_total.labels(
                        endpoint=API_ENDPOINT,
                        error_type=f'http_{response.status_code}'
                    ).inc()
            
            except requests.exceptions.Timeout:
                span.set_attribute("api.response.status", "timeout")
                span.record_exception(requests.exceptions.Timeout())
                logger.error(f"❌ Timeout fetching data from {API_ENDPOINT}")
                api_errors_total.labels(
                    endpoint=API_ENDPOINT,
                    error_type='timeout'
                ).inc()
                
            except requests.exceptions.ConnectionError as e:
                span.set_attribute("api.response.status", "connection_error")
                span.record_exception(e)
                logger.error(f"❌ Connection error: {e}")
                api_errors_total.labels(
                    endpoint=API_ENDPOINT,
                    error_type='connection_error'
                ).inc()
                
            except Exception as e:
                span.set_attribute("api.response.status", "error")
                span.record_exception(e)
                logger.error(f"❌ Unexpected error: {e}")
                api_errors_total.labels(
                    endpoint=API_ENDPOINT,
                    error_type='unknown'
                ).inc()
        
        # Wait before next fetch
        await asyncio.sleep(FETCH_INTERVAL)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(METRICS_PORT)
    logger.info(f"📊 Prometheus metrics server started on port {METRICS_PORT}")
    
    # Start data fetcher
    try:
        asyncio.run(fetch_data())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down REST collector...")