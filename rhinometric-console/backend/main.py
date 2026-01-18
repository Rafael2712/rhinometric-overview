from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import engine, check_db_connection
from models.user import Base as UserBase
from models.role import Base as RoleBase

# Import routers
from routers import auth, kpis, license, anomalies, alerts, logs, traces, dashboards, settings as settings_router, users, grafana_proxy

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="API Gateway for Rhinometric Console - Enterprise Observability Platform"
)

# Startup event - Initialize database connection
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Check database connection
    db_ok = check_db_connection()
    if not db_ok:
        print("⚠️  WARNING: Database connection failed")
        print("⚠️  RBAC features will not work properly")
    else:
        print("✅ Database connected successfully")
    
    # NOTE: Tables should already exist from migration script
    # If you need to create tables automatically (not recommended for production):
    # UserBase.metadata.create_all(bind=engine)
    # RoleBase.metadata.create_all(bind=engine)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "prometheus": settings.PROMETHEUS_URL,
            "ai_anomaly": settings.AI_ANOMALY_URL,
            "license_validator": settings.LICENSE_VALIDATOR_URL,
            "alertmanager": settings.ALERTMANAGER_URL
        }
    }

@app.get("/debug-headers")
async def debug_headers(request: Request):
    """DEBUG: Ver todos los headers de la petición"""
    return {
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None
    }

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_PREFIX}/users", tags=["Users"])  # RBAC User Management
app.include_router(grafana_proxy.router, prefix=f"{settings.API_PREFIX}/grafana", tags=["Grafana"])  # Grafana RBAC Proxy
app.include_router(kpis.router, prefix=f"{settings.API_PREFIX}/kpis", tags=["KPIs"])
app.include_router(anomalies.router, prefix=f"{settings.API_PREFIX}/anomalies", tags=["Anomalies"])
app.include_router(license.router, prefix=f"{settings.API_PREFIX}/license", tags=["License"])
app.include_router(alerts.router, prefix=f"{settings.API_PREFIX}/alerts", tags=["Alerts"])
app.include_router(logs.router, prefix=f"{settings.API_PREFIX}/logs", tags=["Logs"])
app.include_router(traces.router, prefix=f"{settings.API_PREFIX}/traces", tags=["Traces"])
app.include_router(dashboards.router, prefix=f"{settings.API_PREFIX}/dashboards", tags=["Dashboards"])
app.include_router(settings_router.router, prefix=f"{settings.API_PREFIX}/settings", tags=["Settings"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
