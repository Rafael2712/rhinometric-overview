"""
Prometheus metrics instrumentation for Rhinometric Console Backend
Exposes HTTP metrics, latency, and custom business metrics
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# HTTP METRICS
# ============================================================================

# Request counter by endpoint, method, and status code
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Request duration histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Active requests gauge
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)

# Request size histogram
http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1000, 10000, 100000, 1000000)
)

# Response size histogram
http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1000, 10000, 100000, 1000000)
)

# Error counter by type
http_errors_total = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'status_code', 'error_type']
)

# ============================================================================
# BUSINESS METRICS
# ============================================================================

# API Gateway specific metrics
api_auth_attempts_total = Counter(
    'api_auth_attempts_total',
    'Total authentication attempts',
    ['result']  # success, failed, expired
)

api_license_validations_total = Counter(
    'api_license_validations_total',
    'Total license validation requests',
    ['status']  # valid, invalid, expired, error
)

api_anomaly_queries_total = Counter(
    'api_anomaly_queries_total',
    'Total AI anomaly queries',
    ['endpoint']  # /anomalies, /anomalies/active, etc.
)

api_alert_operations_total = Counter(
    'api_alert_operations_total',
    'Total alert operations',
    ['operation']  # list, acknowledge, silence, create
)

# Database connection pool metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Currently active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Currently idle database connections in pool'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],  # select, insert, update, delete
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
)

# ============================================================================
# EXTERNAL SERVICES METRICS
# ==============================================================================

external_service_up = Gauge(
    'external_service_up',
    'External service reachability (1=up, 0=down)',
    ['service_name', 'service_type']
)

external_service_latency_ms = Gauge(
    'external_service_latency_ms',
    'External service last response time in milliseconds',
    ['service_name', 'service_type']
)

external_service_checks_total = Counter(
    'external_service_checks_total',
    'Total external service health checks performed',
    ['service_name', 'service_type', 'result']
)

# ==============================================================================
# PROMETHEUS MIDDLEWARE
# ============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to collect HTTP metrics automatically
    """
    
    def __init__(self, app, app_name: str = "rhinometric-console-backend"):
        super().__init__(app)
        self.app_name = app_name
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Extract endpoint info
        method = request.method
        endpoint = request.url.path
        
        # Simplify endpoint for metrics (group dynamic IDs)
        endpoint = self._normalize_endpoint(endpoint)
        
        # Track request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(int(content_length))
            except ValueError:
                pass
        
        # Mark request as in progress
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Start timer
        start_time = time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time() - start_time
            
            # Record metrics
            status_code = response.status_code
            http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Track response size
            response_size = response.headers.get("content-length")
            if response_size:
                try:
                    http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(int(response_size))
                except ValueError:
                    pass
            
            # Track errors
            if status_code >= 400:
                error_type = "client_error" if status_code < 500 else "server_error"
                http_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                    error_type=error_type
                ).inc()
            
            return response
        
        except Exception as e:
            # Record exception
            duration = time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            http_errors_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500,
                error_type="exception"
            ).inc()
            logger.error(f"Error processing request {method} {endpoint}: {e}")
            raise
        
        finally:
            # Mark request as completed
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
    
    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for metrics aggregation
        Replace UUIDs, IDs with placeholders to avoid high cardinality
        
        Examples:
            /api/users/123 -> /api/users/{id}
            /api/anomalies/uuid-here -> /api/anomalies/{id}
        """
        parts = path.split("/")
        normalized = []
        
        for part in parts:
            # Replace numeric IDs
            if part.isdigit():
                normalized.append("{id}")
            # Replace UUID-like strings
            elif len(part) > 20 and ("-" in part or "_" in part):
                normalized.append("{id}")
            else:
                normalized.append(part)
        
        return "/".join(normalized)

# ============================================================================
# METRICS ENDPOINT
# ============================================================================

async def metrics_endpoint(request: Request):
    """
    Expose Prometheus metrics at /metrics endpoint
    """
    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def update_db_pool_metrics(engine):
    """
    Update database connection pool metrics from SQLAlchemy engine
    Should be called periodically or in health check
    """
    try:
        pool = engine.pool
        db_connections_active.set(pool.checkedout())
        # Calculate idle = total - active
        idle = pool.size() - pool.checkedout()
        db_connections_idle.set(max(0, idle))
    except Exception as e:
        logger.error(f"Error updating DB pool metrics: {e}")

def track_auth_attempt(success: bool):
    """Helper to track authentication attempts"""
    result = "success" if success else "failed"
    api_auth_attempts_total.labels(result=result).inc()

def track_license_validation(status: str):
    """Helper to track license validations"""
    api_license_validations_total.labels(status=status).inc()

def track_anomaly_query(endpoint: str):
    """Helper to track anomaly queries"""
    api_anomaly_queries_total.labels(endpoint=endpoint).inc()

def track_alert_operation(operation: str):
    """Helper to track alert operations"""
    api_alert_operations_total.labels(operation=operation).inc()
