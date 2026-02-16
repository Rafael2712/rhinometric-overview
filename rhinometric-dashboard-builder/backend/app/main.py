"""
FastAPI Application - Dashboard Builder v2.2.0
Visual dashboard creation tool for non-technical users
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import JSONResponse
import structlog

from app.config import config
from app.grafana_api import grafana_client
from app.prometheus_api import query_builder, MetricType, Aggregation
from app.panels import panel_builder, PanelType
from app.templates import dashboard_templates, TemplateType

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Prometheus metrics
DASHBOARDS_CREATED = Counter('rhinometric_dashboards_created_total', 'Total dashboards created')
DASHBOARD_CREATION_TIME = Histogram('rhinometric_dashboard_creation_seconds', 'Dashboard creation time')

# FastAPI app
app = FastAPI(
    title="RhinoMetric Dashboard Builder",
    description="Visual dashboard creation tool for non-technical users",
    version="2.2.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Pydantic Models ===

class PanelRequest(BaseModel):
    """Panel creation request"""
    title: str
    type: PanelType
    metric_type: Optional[MetricType] = None
    metric_subtype: Optional[str] = None
    query: Optional[str] = None
    x: int = 0
    y: int = 0
    width: int = 12
    height: int = 8
    unit: Optional[str] = "short"
    legend: Optional[str] = ""


class DashboardRequest(BaseModel):
    """Dashboard creation request"""
    title: str
    description: Optional[str] = ""
    folder: Optional[str] = None
    tags: List[str] = []
    panels: List[PanelRequest] = []
    template: Optional[TemplateType] = None
    refresh: str = "30s"


class QueryBuildRequest(BaseModel):
    """Query builder request"""
    metric_type: MetricType
    subtype: str
    aggregation: Optional[Aggregation] = None
    filters: Optional[Dict[str, str]] = None
    group_by: Optional[List[str]] = None


class DashboardResponse(BaseModel):
    """Dashboard response"""
    uid: str
    title: str
    url: str
    created_at: datetime


# === API Endpoints ===

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "service": "RhinoMetric Dashboard Builder",
        "version": "2.2.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "dashboards": "/api/v1/dashboards",
            "templates": "/api/v1/templates",
            "panels": "/api/v1/panels",
            "query": "/api/v1/query",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check"""
    # Test connections
    grafana_ok = await grafana_client.test_connection()
    prometheus_ok = await query_builder.test_connection()
    
    status = "healthy" if (grafana_ok and prometheus_ok) else "degraded"
    
    return {
        "status": status,
        "version": "2.2.0",
        "connections": {
            "grafana": "ok" if grafana_ok else "error",
            "prometheus": "ok" if prometheus_ok else "error"
        }
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics"""
    return JSONResponse(
        content=generate_latest().decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


# === Dashboard Endpoints ===

@app.post("/api/v1/dashboards", response_model=DashboardResponse, tags=["Dashboards"])
async def create_dashboard(request: DashboardRequest):
    """Create a new dashboard"""
    logger.info("dashboard_creation_requested", title=request.title)
    
    try:
        with DASHBOARD_CREATION_TIME.time():
            # Use template if specified
            if request.template:
                dashboard_data = dashboard_templates.get_template(request.template)
                dashboard_data["title"] = request.title
                if request.description:
                    dashboard_data["description"] = request.description
            else:
                # Build dashboard from panels
                panels = []
                for idx, panel_req in enumerate(request.panels):
                    # Build query if metric_type specified
                    if panel_req.metric_type and panel_req.metric_subtype:
                        query = query_builder.build_query(
                            metric_type=panel_req.metric_type,
                            subtype=panel_req.metric_subtype
                        )
                    else:
                        query = panel_req.query or ""
                    
                    # Create panel based on type
                    if panel_req.type == PanelType.GRAPH:
                        panel = panel_builder.create_graph_panel(
                            panel_id=idx + 1,
                            title=panel_req.title,
                            query=query,
                            x=panel_req.x,
                            y=panel_req.y,
                            width=panel_req.width,
                            height=panel_req.height,
                            unit=panel_req.unit,
                            legend=panel_req.legend,
                        )
                    elif panel_req.type == PanelType.STAT:
                        panel = panel_builder.create_stat_panel(
                            panel_id=idx + 1,
                            title=panel_req.title,
                            query=query,
                            x=panel_req.x,
                            y=panel_req.y,
                            width=panel_req.width,
                            height=panel_req.height,
                            unit=panel_req.unit,
                        )
                    elif panel_req.type == PanelType.GAUGE:
                        panel = panel_builder.create_gauge_panel(
                            panel_id=idx + 1,
                            title=panel_req.title,
                            query=query,
                            x=panel_req.x,
                            y=panel_req.y,
                            width=panel_req.width,
                            height=panel_req.height,
                            unit=panel_req.unit,
                        )
                    elif panel_req.type == PanelType.TABLE:
                        panel = panel_builder.create_table_panel(
                            panel_id=idx + 1,
                            title=panel_req.title,
                            query=query,
                            x=panel_req.x,
                            y=panel_req.y,
                            width=panel_req.width,
                            height=panel_req.height,
                        )
                    elif panel_req.type == PanelType.PIE_CHART:
                        panel = panel_builder.create_pie_chart_panel(
                            panel_id=idx + 1,
                            title=panel_req.title,
                            query=query,
                            x=panel_req.x,
                            y=panel_req.y,
                            width=panel_req.width,
                            height=panel_req.height,
                        )
                    else:
                        raise ValueError(f"Unsupported panel type: {panel_req.type}")
                    
                    panels.append(panel)
                
                dashboard_data = {
                    "title": request.title,
                    "description": request.description,
                    "tags": request.tags,
                    "timezone": "browser",
                    "editable": True,
                    "panels": panels,
                    "refresh": request.refresh,
                    "time": {"from": "now-6h", "to": "now"},
                }
            
            # Create in Grafana
            result = await grafana_client.create_dashboard(dashboard_data)
            
            DASHBOARDS_CREATED.inc()
            
            logger.info("dashboard_created", uid=result.get("uid"))
            
            return DashboardResponse(
                uid=result.get("uid", ""),
                title=request.title,
                url=f"{config.grafana.url}/d/{result.get('uid')}",
                created_at=datetime.now()
            )
    
    except Exception as e:
        logger.error("dashboard_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/dashboards", tags=["Dashboards"])
async def list_dashboards():
    """List all dashboards"""
    try:
        dashboards = await grafana_client.list_dashboards()
        return {"dashboards": dashboards, "count": len(dashboards)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/dashboards/{uid}", tags=["Dashboards"])
async def get_dashboard(uid: str):
    """Get dashboard by UID"""
    try:
        dashboard = await grafana_client.get_dashboard(uid)
        return {"dashboard": dashboard}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/v1/dashboards/{uid}", tags=["Dashboards"])
async def delete_dashboard(uid: str):
    """Delete dashboard"""
    try:
        result = await grafana_client.delete_dashboard(uid)
        return {"status": "deleted", "uid": uid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Template Endpoints ===

@app.get("/api/v1/templates", tags=["Templates"])
async def list_templates():
    """List all dashboard templates"""
    templates = dashboard_templates.list_templates()
    return {"templates": templates, "count": len(templates)}


@app.get("/api/v1/templates/{template_type}", tags=["Templates"])
async def get_template(template_type: TemplateType):
    """Get dashboard template"""
    try:
        template = dashboard_templates.get_template(template_type)
        return {"template": template}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# === Query Builder Endpoints ===

@app.post("/api/v1/query/build", tags=["Query Builder"])
async def build_query(request: QueryBuildRequest):
    """Build Prometheus query from parameters"""
    try:
        query = query_builder.build_query(
            metric_type=request.metric_type,
            subtype=request.subtype,
            aggregation=request.aggregation,
            filters=request.filters,
            group_by=request.group_by
        )
        return {"query": query}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/query/validate", tags=["Query Builder"])
async def validate_query(query: str = Query(...)):
    """Validate Prometheus query"""
    try:
        valid = await query_builder.validate_query(query)
        return {"valid": valid, "query": query}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/query/metrics", tags=["Query Builder"])
async def get_metric_types():
    """Get available metric types"""
    metrics = [
        {
            "type": metric_type.value,
            "name": metric_type.value.title(),
            "options": query_builder.get_metric_options(metric_type)
        }
        for metric_type in MetricType
    ]
    return {"metrics": metrics}


# === Panel Endpoints ===

@app.get("/api/v1/panels/types", tags=["Panels"])
async def get_panel_types():
    """Get available panel types"""
    panel_types = [
        {
            "type": panel_type.value,
            "name": panel_type.value.title().replace("_", " "),
            "description": f"{panel_type.value} panel",
        }
        for panel_type in PanelType
    ]
    return {"panel_types": panel_types}


# === Datasource Endpoints ===

@app.get("/api/v1/datasources", tags=["Datasources"])
async def list_datasources():
    """List Grafana datasources"""
    try:
        datasources = await grafana_client.get_datasources()
        return {"datasources": datasources, "count": len(datasources)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=config.server.host,
        port=config.server.port,
        workers=config.server.workers,
        log_level=config.server.log_level.lower(),
        reload=False
    )
