"""
FastAPI Application - Report Generator v2.2.0
RESTful API for report generation, scheduling, and delivery
"""
import os
import logging
import asyncio
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import config_manager
from app.data_aggregator import data_aggregator
from app.pdf_generator import pdf_generator
from app.email_service import email_service

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Custom registry to avoid duplicate metrics
custom_registry = CollectorRegistry()

# Prometheus metrics with custom registry
REPORTS_GENERATED = Counter(
    'rhinometric_reports_generated_total',
    'Total number of reports generated',
    ['report_type', 'format'],
    registry=custom_registry
)
REPORTS_SENT = Counter(
    'rhinometric_reports_sent_total',
    'Total number of reports sent via email',
    ['report_type', 'success'],
    registry=custom_registry
)
REPORT_GENERATION_TIME = Histogram(
    'rhinometric_report_generation_seconds',
    'Time spent generating reports',
    ['report_type'],
    registry=custom_registry
)
ACTIVE_REPORTS = Gauge(
    'rhinometric_active_reports',
    'Number of reports currently being generated',
    registry=custom_registry
)

# FastAPI app
app = FastAPI(
    title="RhinoMetric Report Generator",
    description="Professional PDF/HTML report generation and email delivery",
    version="2.2.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Pydantic Models ===

class ReportRequest(BaseModel):
    """Report generation request"""
    report_type: str = Field(
        default="executive",
        description="Type of report: executive, technical, or anomaly"
    )
    period_hours: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Time period in hours (1-720)"
    )
    formats: List[str] = Field(
        default=["pdf"],
        description="Output formats: pdf and/or html"
    )
    recipients: List[str] = Field(
        default=[],
        description="Email recipients (optional)"
    )
    include_charts: bool = Field(default=True, description="Include charts in report")
    include_anomalies: bool = Field(default=True, description="Include anomalies section")
    include_metrics: bool = Field(default=True, description="Include metrics section")


class ReportResponse(BaseModel):
    """Report generation response"""
    report_id: str
    report_type: str
    status: str
    generated_at: datetime
    formats: List[str]
    files: dict
    email_sent: bool = False
    recipients: List[str] = []


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime_seconds: float
    reports_generated: int
    last_report_at: Optional[datetime] = None


class ScheduleRequest(BaseModel):
    """Schedule report request"""
    report_name: str
    report_type: str = "executive"
    period_hours: int = 24
    formats: List[str] = ["pdf", "html"]
    recipients: List[str]
    cron: str = "0 8 * * *"  # Daily at 8 AM
    enabled: bool = True


# === Global State ===
app_start_time = datetime.now()
reports_count = 0
last_report_time = None


# === API Endpoints ===

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "service": "RhinoMetric Report Generator",
        "version": "2.2.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "generate": "/api/v1/reports/generate",
            "list": "/api/v1/reports/list",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - app_start_time).total_seconds()
    
    return HealthResponse(
        status="healthy",
        version="2.2.0",
        uptime_seconds=uptime,
        reports_generated=reports_count,
        last_report_at=last_report_time
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return JSONResponse(
        content=generate_latest(custom_registry).decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/api/v1/reports/generate", response_model=ReportResponse, tags=["Reports"])
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """Generate a new report"""
    global reports_count, last_report_time
    
    logger.info("report_generation_requested", report_type=request.report_type)
    
    try:
        ACTIVE_REPORTS.inc()
        
        with REPORT_GENERATION_TIME.labels(report_type=request.report_type).time():
            # Aggregate data
            logger.info("aggregating_data", period_hours=request.period_hours)
            report_data = await data_aggregator.aggregate_report_data(
                report_type=request.report_type,
                hours=request.period_hours
            )
            
            # Generate report ID
            report_id = f"{request.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            files = {}
            
            # Generate PDF
            if "pdf" in request.formats:
                logger.info("generating_pdf")
                pdf_path = pdf_generator.generate_report(report_data, request.report_type)
                files["pdf"] = pdf_path
                REPORTS_GENERATED.labels(report_type=request.report_type, format="pdf").inc()
            
            # Generate HTML (if requested)
            if "html" in request.formats:
                logger.info("generating_html")
                # HTML generation would go here
                # For now, we'll skip it and focus on PDF
                pass
            
            # Send email if recipients specified
            email_sent = False
            if request.recipients and files.get("pdf"):
                logger.info("sending_email", recipients=len(request.recipients))
                background_tasks.add_task(
                    email_service.send_report_email,
                    recipients=request.recipients,
                    report_name=request.report_type,
                    report_data=report_data,
                    pdf_path=files.get("pdf"),
                    html_path=files.get("html")
                )
                email_sent = True
                REPORTS_SENT.labels(report_type=request.report_type, success="true").inc()
            
            reports_count += 1
            last_report_time = datetime.now()
            
            logger.info(
                "report_generated_successfully",
                report_id=report_id,
                formats=request.formats,
                email_sent=email_sent
            )
            
            return ReportResponse(
                report_id=report_id,
                report_type=request.report_type,
                status="completed",
                generated_at=datetime.now(),
                formats=request.formats,
                files=files,
                email_sent=email_sent,
                recipients=request.recipients
            )
    
    except Exception as e:
        logger.error("report_generation_failed", error=str(e))
        REPORTS_SENT.labels(report_type=request.report_type, success="false").inc()
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    
    finally:
        ACTIVE_REPORTS.dec()


@app.get("/api/v1/reports/list", tags=["Reports"])
async def list_reports(
    limit: int = Query(default=50, ge=1, le=100),
    report_type: Optional[str] = None
):
    """List generated reports"""
    reports_dir = config_manager.config.storage.reports_dir
    
    if not os.path.exists(reports_dir):
        return {"reports": [], "count": 0}
    
    reports = []
    for filename in os.listdir(reports_dir):
        if filename.endswith('.pdf'):
            filepath = os.path.join(reports_dir, filename)
            stat = os.stat(filepath)
            
            # Parse report type from filename
            file_report_type = filename.split('_')[0]
            
            # Filter by report type if specified
            if report_type and file_report_type != report_type:
                continue
            
            reports.append({
                "filename": filename,
                "report_type": file_report_type,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "download_url": f"/api/v1/reports/download/{filename}"
            })
    
    # Sort by creation time (newest first)
    reports.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "reports": reports[:limit],
        "count": len(reports),
        "total": len(reports)
    }


@app.get("/api/v1/reports/download/{filename}", tags=["Reports"])
async def download_report(filename: str):
    """Download a generated report"""
    reports_dir = config_manager.config.storage.reports_dir
    filepath = os.path.join(reports_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Security: prevent directory traversal
    if not os.path.abspath(filepath).startswith(os.path.abspath(reports_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename
    )


@app.delete("/api/v1/reports/{filename}", tags=["Reports"])
async def delete_report(filename: str):
    """Delete a report"""
    reports_dir = config_manager.config.storage.reports_dir
    filepath = os.path.join(reports_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Security check
    if not os.path.abspath(filepath).startswith(os.path.abspath(reports_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    os.remove(filepath)
    logger.info("report_deleted", filename=filename)
    
    return {"status": "deleted", "filename": filename}


@app.post("/api/v1/schedules", tags=["Scheduling"])
async def create_schedule(request: ScheduleRequest):
    """Create a scheduled report"""
    # This would integrate with APScheduler
    # For now, return a placeholder response
    logger.info("schedule_created", report_name=request.report_name)
    
    return {
        "schedule_id": f"schedule_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "report_name": request.report_name,
        "status": "active",
        "next_run": "2024-01-01 08:00:00"  # Placeholder
    }


@app.get("/api/v1/config", tags=["Configuration"])
async def get_config():
    """Get current configuration"""
    config = config_manager.config
    
    return {
        "server": {
            "host": config.server.host,
            "port": config.server.port,
            "log_level": config.server.log_level
        },
        "smtp": {
            "enabled": config.smtp.enabled,
            "host": config.smtp.host,
            "port": config.smtp.port,
            "from_email": config.smtp.from_email
        },
        "storage": {
            "reports_dir": config.storage.reports_dir,
            "max_age_days": config.storage.max_age_days
        },
        "reports_configured": len(config.reports)
    }


@app.post("/api/v1/config/reload", tags=["Configuration"])
async def reload_config():
    """Reload configuration from file"""
    success = config_manager.reload()
    
    if success:
        logger.info("configuration_reloaded")
        return {"status": "success", "message": "Configuration reloaded"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reload configuration")


if __name__ == "__main__":
    import uvicorn
    
    config = config_manager.config.server
    
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        workers=config.workers,
        log_level=config.log_level.lower(),
        reload=False
    )
