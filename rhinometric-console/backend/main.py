from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

# Import routers
from routers import auth, kpis, license, anomalies, alerts

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="API Gateway for Rhinometric Console - Enterprise Observability Platform"
)

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

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(kpis.router, prefix=f"{settings.API_PREFIX}/kpis", tags=["KPIs"])
app.include_router(anomalies.router, prefix=f"{settings.API_PREFIX}/anomalies", tags=["Anomalies"])
app.include_router(license.router, prefix=f"{settings.API_PREFIX}/license", tags=["License"])
app.include_router(alerts.router, prefix=f"{settings.API_PREFIX}/alerts", tags=["Alerts"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
