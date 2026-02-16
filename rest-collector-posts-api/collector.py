"""
RHINOMETRIC v2.5.0 - REST API Collector Template
=================================================

Auto-generated REST API collector for monitoring external APIs.

Configuration variables (injected by system):
- API_URL: https://jsonplaceholder.typicode.com
- API_TOKEN: None
- API_ENDPOINT: /posts/1
- API_METHOD: GET
- METRICS_PORT: 
- FETCH_INTERVAL: 60
"""

import asyncio
import requests
import json
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from datetime import datetime
import logging

# ============================================================================
# CONFIGURATION (auto-injected)
# ============================================================================

API_URL = "https://jsonplaceholder.typicode.com"
API_TOKEN = "None"
API_ENDPOINT = "/posts/1"
API_METHOD = "GET"
API_HEADERS = {}
METRICS_PORT = 9300
FETCH_INTERVAL = 60

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
        try:
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
                try:
                    data = response.json()
                    
                    # Count records
                    if isinstance(data, list):
                        record_count = len(data)
                    elif isinstance(data, dict):
                        record_count = len(data.get('items', data.get('results', [data])))
                    else:
                        record_count = 1
                    
                    api_data_count.set(record_count)
                    api_last_success_timestamp.set(datetime.now().timestamp())
                    
                    logger.info(f"✅ Fetched {record_count} records from {API_ENDPOINT} ({duration:.2f}s)")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️  Response is not JSON: {e}")
                    api_errors_total.labels(
                        endpoint=API_ENDPOINT,
                        error_type='json_decode_error'
                    ).inc()
            else:
                logger.warning(f"⚠️  API returned status {response.status_code}")
                api_errors_total.labels(
                    endpoint=API_ENDPOINT,
                    error_type=f'http_{response.status_code}'
                ).inc()
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout fetching data from {API_ENDPOINT}")
            api_errors_total.labels(
                endpoint=API_ENDPOINT,
                error_type='timeout'
            ).inc()
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            api_errors_total.labels(
                endpoint=API_ENDPOINT,
                error_type='connection_error'
            ).inc()
            
        except Exception as e:
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