from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import engine, check_db_connection
from models.user import Base as UserBase
from models.role import Base as RoleBase
from models.alert_acknowledgement import AlertAcknowledgement

# Observability imports
from telemetry import setup_telemetry
from metrics import PrometheusMiddleware, metrics_endpoint, update_db_pool_metrics
from logging_config import setup_json_logging, get_logger, set_request_context, clear_request_context, log_request

# Initialize JSON structured logging
setup_json_logging(service_name="console-backend", log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO")
logger = get_logger(__name__)

# Import routers
from routers import auth, kpis, license, anomalies, alerts, logs, traces, dashboards, settings as settings_router, users, grafana_proxy, correlation, external_services

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="API Gateway for Rhinometric Console - Enterprise Observability Platform"
)

# ============================================================================
# OBSERVABILITY SETUP
# ============================================================================

# Setup OpenTelemetry tracing
setup_telemetry(app, service_name="rhinometric-console-backend", service_version=settings.API_VERSION)

# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware, app_name="rhinometric-console-backend")

# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================

# Startup event - Initialize database connection
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Check database connection
    db_ok = check_db_connection()
    if not db_ok:
        logger.warning("Database connection failed - RBAC features unavailable", extra={"db_status": "failed"})
    else:
        logger.info("Database connected successfully", extra={"db_status": "connected"})
        
        # ✅ BOOTSTRAP: Ensure admin user exists (immortal admin)
        try:
            from core.bootstrap import ensure_admin_user
            ensure_admin_user()
        except Exception as e:
            logger.error(f"Failed to run bootstrap: {str(e)}")
    
    # Update DB pool metrics
    update_db_pool_metrics(engine)
    
    logger.info("Console backend started", extra={
        "service_version": settings.API_VERSION,
        "environment": "production"
    })
    
    # Auto-create alert_acknowledgements table if it doesn't exist
    try:
        # engine already imported at module level
        AlertAcknowledgement.__table__.create(bind=engine, checkfirst=True)
        logger.info("Alert acknowledgements table ready")
    except Exception as e:
        logger.warning(f"Could not create alert_acknowledgements table: {e}")

    # NOTE: Tables should already exist from migration script

    # Auto-create external_services table if it doesn't exist
    try:
        from models.external_service import ExternalService
        ExternalService.__table__.create(bind=engine, checkfirst=True)
        logger.info("External services table ready")
    except Exception as e:
        logger.warning(f"Could not create external_services table: {e}")

    # RUST LICENSE VALIDATOR - Startup Check
    try:
        from utils.rust_license_validator import is_binary_available, validate_license
        if is_binary_available():
            lic = validate_license()
            if lic.is_valid:
                logger.info(
                    "Rust license validator OK",
                    extra={
                        "license_status": lic.status,
                        "plan": lic.plan,
                        "max_hosts": lic.max_hosts,
                        "customer": lic.customer,
                        "expires_at": lic.expires_at,
                        "validator": "rust",
                    }
                )
            else:
                logger.warning(
                    "License validation FAILED: %s - %s" % (lic.status, lic.error_message),
                    extra={"license_status": lic.status, "validator": "rust"}
                )
        else:
            logger.warning(
                "rhino-lic binary not found - Rust license validation unavailable",
                extra={"validator": "rust", "binary_path": "/usr/local/bin/rhino-lic"}
            )
    except Exception as e:
        logger.warning("Startup license check failed: %s" % e)
    # Tables are now auto-created in startup_event above


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# LOGGING CONTEXT MIDDLEWARE (correlate logs with traces)
# ============================================================================
@app.middleware("http")
async def logging_correlation_middleware(request: Request, call_next):
    """Extract trace context and set logging correlation"""
    import uuid
    from time import time
    from opentelemetry import trace
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Get trace context from OpenTelemetry
    span = trace.get_current_span()
    span_context = span.get_span_context()
    
    if span_context and span_context.is_valid:
        trace_id = format(span_context.trace_id, '032x')
        span_id = format(span_context.span_id, '016x')
    else:
        trace_id = None
        span_id = None
    
    # Set context for logging
    set_request_context(
        request_id=request_id,
        trace_id=trace_id,
        span_id=span_id
    )
    
    # Process request
    start_time = time()
    try:
        response = await call_next(request)
        duration_ms = (time() - start_time) * 1000
        
        # Log request
        log_request(
            logger,
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        # Add correlation headers to response
        response.headers["X-Request-ID"] = request_id
        if trace_id:
            response.headers["X-Trace-ID"] = trace_id
        
        return response
    
    except Exception as e:
        duration_ms = (time() - start_time) * 1000
        logger.error(f"Request failed: {str(e)}", extra={
            "method": request.method,
            "endpoint": str(request.url.path),
            "duration_ms": duration_ms,
            "error_code": "INTERNAL_ERROR"
        }, exc_info=True)
        raise
    
    finally:
        # Clear context
        clear_request_context()

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Rhinometric Console API Gateway",
        "version": settings.API_VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health():
    """Detailed health check with DB pool metrics"""
    update_db_pool_metrics(engine)  # Update metrics on health check
    return {
        "status": "healthy",
        "services": {
            "prometheus": settings.PROMETHEUS_URL,
            "ai_anomaly": settings.AI_ANOMALY_URL,
            "license_validator": settings.LICENSE_VALIDATOR_URL,
            "alertmanager": settings.ALERTMANAGER_URL
        }
    }

@app.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics endpoint"""
    return await metrics_endpoint(request)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_PREFIX}/users", tags=["Users"])  # RBAC User Management
app.include_router(grafana_proxy.router, prefix=f"{settings.API_PREFIX}/grafana", tags=["Grafana"])  # Grafana RBAC Proxy
app.include_router(grafana_proxy.router, prefix=f"{settings.API_PREFIX}/grafana-proxy", tags=["Grafana Render"])  # Panel rendering
app.include_router(kpis.router, prefix=f"{settings.API_PREFIX}/kpis", tags=["KPIs"])
app.include_router(anomalies.router, prefix=f"{settings.API_PREFIX}/anomalies", tags=["Anomalies"])
app.include_router(license.router, prefix=f"{settings.API_PREFIX}/license", tags=["License"])
app.include_router(alerts.router, prefix=f"{settings.API_PREFIX}/alerts", tags=["Alerts"])
app.include_router(logs.router, prefix=f"{settings.API_PREFIX}/logs", tags=["Logs"])
app.include_router(traces.router, prefix=f"{settings.API_PREFIX}/traces", tags=["Traces"])
app.include_router(dashboards.router, prefix=f"{settings.API_PREFIX}/dashboards", tags=["Dashboards"])
app.include_router(settings_router.router, prefix=f"{settings.API_PREFIX}/settings", tags=["Settings"])
app.include_router(correlation.router, prefix=f"{settings.API_PREFIX}/correlation", tags=["Correlation"])  # Rhino Core - Correlation Engine
app.include_router(external_services.router, prefix=f"{settings.API_PREFIX}/external-services", tags=["External Services"])  # External Services Connector MVP

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
