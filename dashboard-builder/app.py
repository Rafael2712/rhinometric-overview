"""
RHINOMETRIC v2.4.0 - Dashboard Builder Backend
==============================================

FastAPI backend para creación visual de dashboards en Grafana.

Features:
- CRUD dashboards (Create, Read, Update, Delete)
- Templates predefinidos (Infraestructura, APIs, Messaging, ESG)
- Persistencia en PostgreSQL local
- Validación JWT + licencia
- Audit logging

Security:
- 100% on-premise
- No external APIs
- Local storage only
- License validation required
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import json
import logging
import hashlib
import os
from sqlalchemy.orm import Session

# Import database models
from models import Dashboard, get_db, init_db

# Templates
templates = Jinja2Templates(directory="templates")

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="RHINOMETRIC Dashboard Builder",
    description="Visual dashboard creator for Grafana",
    version="2.4.0"
)

# CORS para Grafana
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup with retries."""
    import time
    max_retries = 10
    retry_delay = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔧 Initializing PostgreSQL database (attempt {attempt}/{max_retries})...")
            init_db()
            logger.info("✅ Database ready")
            return
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("❌ Max retries reached. Database connection failed.")
                raise


# ============================================================================
# MODELS
# ============================================================================

class DashboardPanel(BaseModel):
    """Panel configuration."""
    id: int = Field(..., description="Panel ID")
    type: str = Field(..., description="Panel type (graph, gauge, table, etc.)")
    title: str = Field(..., description="Panel title")
    datasource: Optional[str] = Field(None, description="Datasource name")
    query: Optional[str] = Field(None, description="Query/metric")
    x: int = Field(default=0, description="Grid X position")
    y: int = Field(default=0, description="Grid Y position")
    width: int = Field(default=12, description="Grid width (1-24)")
    height: int = Field(default=8, description="Grid height")
    options: Dict[str, Any] = Field(default_factory=dict, description="Panel-specific options")


class DashboardConfig(BaseModel):
    """Dashboard configuration."""
    title: str = Field(..., description="Dashboard title", min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="Dashboard description")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    template: Optional[str] = Field(None, description="Template ID if created from template")
    panels: List[DashboardPanel] = Field(default_factory=list, description="Dashboard panels")
    time_range: Dict[str, str] = Field(
        default_factory=lambda: {"from": "now-6h", "to": "now"},
        description="Default time range"
    )
    refresh: str = Field(default="30s", description="Auto-refresh interval")
    variables: List[Dict[str, Any]] = Field(default_factory=list, description="Dashboard variables")


class DashboardMetadata(BaseModel):
    """Dashboard metadata for listing."""
    id: str = Field(..., description="Dashboard ID")
    title: str
    description: Optional[str]
    tags: List[str]
    template: Optional[str]
    created_at: str
    updated_at: str
    created_by: str
    panel_count: int
    version: int = Field(default=1)


class DashboardSaveRequest(BaseModel):
    """Request to save dashboard."""
    dashboard: DashboardConfig
    overwrite: bool = Field(default=False, description="Overwrite existing dashboard")


class DashboardExportResponse(BaseModel):
    """Dashboard export (Grafana JSON format)."""
    dashboard: Dict[str, Any]
    metadata: DashboardMetadata


# ============================================================================
# TEMPLATES PREDEFINIDOS
# ============================================================================

DASHBOARD_TEMPLATES = {
    "infrastructure": {
        "id": "infrastructure",
        "name": "Infraestructura Completa",
        "description": "Monitoreo de infraestructura: CPU, memoria, disco, red",
        "category": "infrastructure",
        "icon": "🏗️",
        "panels": [
            {
                "id": 1,
                "type": "graph",
                "title": "CPU Usage",
                "datasource": "Prometheus",
                "query": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                "x": 0, "y": 0, "width": 12, "height": 8,
                "options": {"unit": "percent", "color": "blue"}
            },
            {
                "id": 2,
                "type": "graph",
                "title": "Memory Usage",
                "datasource": "Prometheus",
                "query": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
                "x": 12, "y": 0, "width": 12, "height": 8,
                "options": {"unit": "percent", "color": "green"}
            },
            {
                "id": 3,
                "type": "gauge",
                "title": "Disk Usage",
                "datasource": "Prometheus",
                "query": "(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100",
                "x": 0, "y": 8, "width": 8, "height": 6,
                "options": {"unit": "percent", "thresholds": [50, 80, 90]}
            },
            {
                "id": 4,
                "type": "graph",
                "title": "Network Traffic",
                "datasource": "Prometheus",
                "query": "rate(node_network_receive_bytes_total[5m])",
                "x": 8, "y": 8, "width": 16, "height": 6,
                "options": {"unit": "bytes", "color": "purple"}
            }
        ]
    },
    "api-monitoring": {
        "id": "api-monitoring",
        "name": "Monitoreo de APIs REST",
        "description": "Latencia, error rate, throughput de APIs",
        "category": "api",
        "icon": "🌐",
        "panels": [
            {
                "id": 1,
                "type": "stat",
                "title": "Request Rate",
                "datasource": "Prometheus",
                "query": "sum(rate(http_requests_total[5m]))",
                "x": 0, "y": 0, "width": 6, "height": 6,
                "options": {"unit": "reqps", "color": "blue"}
            },
            {
                "id": 2,
                "type": "gauge",
                "title": "Error Rate",
                "datasource": "Prometheus",
                "query": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
                "x": 6, "y": 0, "width": 6, "height": 6,
                "options": {"unit": "percent", "thresholds": [1, 5, 10]}
            },
            {
                "id": 3,
                "type": "graph",
                "title": "Response Time P95",
                "datasource": "Prometheus",
                "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                "x": 12, "y": 0, "width": 12, "height": 6,
                "options": {"unit": "seconds", "color": "green"}
            },
            {
                "id": 4,
                "type": "table",
                "title": "Top Endpoints by Latency",
                "datasource": "Prometheus",
                "query": "topk(10, avg(http_request_duration_seconds) by (endpoint))",
                "x": 0, "y": 6, "width": 24, "height": 8,
                "options": {"sort": "desc"}
            }
        ]
    },
    "messaging": {
        "id": "messaging",
        "name": "Flujo de Mensajería",
        "description": "Kafka, RabbitMQ: throughput, lag, consumers",
        "category": "messaging",
        "icon": "💬",
        "panels": [
            {
                "id": 1,
                "type": "graph",
                "title": "Message Rate (Kafka)",
                "datasource": "Prometheus",
                "query": "sum(rate(kafka_server_BrokerTopicMetrics_MessagesInPerSec[5m]))",
                "x": 0, "y": 0, "width": 12, "height": 8,
                "options": {"unit": "msg/s", "color": "blue"}
            },
            {
                "id": 2,
                "type": "gauge",
                "title": "Consumer Lag",
                "datasource": "Prometheus",
                "query": "sum(kafka_consumergroup_lag)",
                "x": 12, "y": 0, "width": 12, "height": 8,
                "options": {"unit": "messages", "thresholds": [1000, 10000, 100000]}
            },
            {
                "id": 3,
                "type": "graph",
                "title": "RabbitMQ Queue Depth",
                "datasource": "Prometheus",
                "query": "sum(rabbitmq_queue_messages)",
                "x": 0, "y": 8, "width": 12, "height": 6,
                "options": {"unit": "messages", "color": "orange"}
            },
            {
                "id": 4,
                "type": "stat",
                "title": "Active Consumers",
                "datasource": "Prometheus",
                "query": "sum(rabbitmq_queue_consumers)",
                "x": 12, "y": 8, "width": 12, "height": 6,
                "options": {"color": "green"}
            }
        ]
    },
    "sustainability": {
        "id": "sustainability",
        "name": "VeriVerde ESG Dashboard",
        "description": "Carbon intensity, renewable energy, ESG score",
        "category": "esg",
        "icon": "🌱",
        "panels": [
            {
                "id": 1,
                "type": "gauge",
                "title": "Carbon Intensity",
                "datasource": "Prometheus",
                "query": "avg(carbon_intensity_gco2_per_kwh)",
                "x": 0, "y": 0, "width": 8, "height": 8,
                "options": {"unit": "gCO2/kWh", "thresholds": [100, 300, 500], "color": "green"}
            },
            {
                "id": 2,
                "type": "stat",
                "title": "Renewable Energy %",
                "datasource": "Prometheus",
                "query": "avg(renewable_energy_percentage)",
                "x": 8, "y": 0, "width": 8, "height": 8,
                "options": {"unit": "percent", "color": "blue"}
            },
            {
                "id": 3,
                "type": "gauge",
                "title": "ESG Compliance Score",
                "datasource": "Prometheus",
                "query": "avg(esg_compliance_score)",
                "x": 16, "y": 0, "width": 8, "height": 8,
                "options": {"unit": "score", "thresholds": [50, 70, 85], "max": 100}
            },
            {
                "id": 4,
                "type": "graph",
                "title": "Energy Consumption Trend",
                "datasource": "Prometheus",
                "query": "sum(rate(energy_consumption_kwh[1h]))",
                "x": 0, "y": 8, "width": 24, "height": 8,
                "options": {"unit": "kWh", "color": "purple"}
            }
        ]
    }
}


# ============================================================================
# SECURITY & LICENSE VALIDATION
# ============================================================================

# JWT Secret from environment
JWT_SECRET = os.getenv('JWT_SECRET', 'rhinometric-secret-key-change-in-production')

async def validate_license(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    """
    Validate license and JWT token.
    
    Args:
        authorization: Authorization header with Bearer token
    
    Returns:
        User context (user_id, username, role)
    
    Raises:
        HTTPException: If license invalid or token expired
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        import jwt
        
        # Decode JWT token
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )
        
        # Verify required claims
        required_claims = ["user_id", "username", "exp"]
        for claim in required_claims:
            if claim not in payload:
                raise HTTPException(status_code=401, detail=f"Missing required claim: {claim}")
        
        # Extract user context
        user_context = {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "role": payload.get("role", "user"),
            "license_key": payload.get("license_key"),
            "customer": payload.get("customer")
        }
        
        logger.info(f"✅ JWT validated for user: {user_context['username']}")
        
        return user_context
        
    except jwt.ExpiredSignatureError:
        logger.warning("⚠️ JWT token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"⚠️ Invalid JWT token: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except ImportError:
        # Fallback if jwt library not available (shouldn't happen with requirements.txt)
        logger.error("❌ PyJWT library not installed")
        raise HTTPException(status_code=500, detail="JWT validation not available")


# ============================================================================
# ============================================================================
# DATABASE UTILITIES
# ============================================================================

def generate_dashboard_id(title: str) -> str:
    """Generate deterministic dashboard ID from title (no timestamp)."""
    import re
    # Normalize title: lowercase, replace spaces/underscores with hyphens, remove special chars
    normalized = title.lower().replace(" ", "-").replace("_", "-")
    normalized = re.sub(r'[^a-z0-9-]', '', normalized)
    # Remove consecutive hyphens
    normalized = re.sub(r'-+', '-', normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')
    return normalized or 'dashboard'


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve Dashboard Builder UI."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "service": "RHINOMETRIC Dashboard Builder",
        "version": "2.4.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/templates")
async def get_templates():
    """Get dashboard templates."""
    return {
        "templates": DASHBOARD_TEMPLATES,
        "count": len(DASHBOARD_TEMPLATES)
    }


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get specific template."""
    if template_id not in DASHBOARD_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    
    return {
        "template_id": template_id,
        "template": DASHBOARD_TEMPLATES[template_id]
    }


@app.post("/api/dashboards")
async def create_dashboard(
    request: DashboardSaveRequest,
    user: Dict[str, str] = Depends(validate_license),
    db: Session = Depends(get_db)
):
    """
    Create new dashboard with PostgreSQL persistence.
    
    Requires valid license and JWT token.
    """
    dashboard = request.dashboard
    dashboard_id = generate_dashboard_id(dashboard.title)
    
    # Check if dashboard with same ID/title already exists
    existing = db.query(Dashboard).filter(
        (Dashboard.id == dashboard_id) | (Dashboard.title == dashboard.title)
    ).first()
    
    if existing and not request.overwrite:
        raise HTTPException(
            status_code=409,
            detail=f"Dashboard '{dashboard.title}' already exists. Use overwrite=true to replace."
        )
    
    # Prepare dashboard configuration
    config = dashboard.dict()
    
    if existing:
        # Update existing dashboard
        existing.title = dashboard.title
        existing.description = dashboard.description
        existing.tags = dashboard.tags
        existing.template = dashboard.template
        existing.config = config
        existing.updated_at = datetime.utcnow()
        existing.version += 1
        db_dashboard = existing
    else:
        # Create new dashboard
        db_dashboard = Dashboard(
            id=dashboard_id,
            title=dashboard.title,
            description=dashboard.description,
            tags=dashboard.tags,
            template=dashboard.template,
            config=config,
            created_by=user["username"],
            version=1
        )
        db.add(db_dashboard)
    
    db.commit()
    db.refresh(db_dashboard)
    
    # Audit log
    logger.info(f"Dashboard {'updated' if existing else 'created'}: {dashboard_id} by {user['username']}")
    
    # Build metadata response
    metadata = DashboardMetadata(
        id=db_dashboard.id,
        title=db_dashboard.title,
        description=db_dashboard.description,
        tags=db_dashboard.tags,
        template=db_dashboard.template,
        created_at=db_dashboard.created_at.isoformat(),
        updated_at=db_dashboard.updated_at.isoformat(),
        created_by=db_dashboard.created_by,
        panel_count=len(dashboard.panels),
        version=db_dashboard.version
    )
    
    return {
        "success": True,
        "message": f"Dashboard '{dashboard.title}' {'updated' if existing else 'created'} successfully",
        "dashboard_id": dashboard_id,
        "metadata": metadata
    }


@app.get("/api/dashboards")
async def list_dashboards(
    user: Dict[str, str] = Depends(validate_license),
    tags: Optional[str] = None,
    search: Optional[str] = None
):
    """List all dashboards with optional filtering."""
    dashboards = []
    
    for db_id, db_data in dashboards_db.items():
        metadata = db_data["metadata"]
        
        # Apply filters
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            if not any(tag in metadata["tags"] for tag in tag_list):
                continue
        
        if search:
            if search.lower() not in metadata["title"].lower() and \
               (not metadata["description"] or search.lower() not in metadata["description"].lower()):
                continue
        
        dashboards.append(metadata)
    
    # Sort by updated_at descending
    dashboards.sort(key=lambda x: x["updated_at"], reverse=True)
    
    return {
        "dashboards": dashboards,
        "count": len(dashboards)
    }


@app.get("/api/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    user: Dict[str, str] = Depends(validate_license),
    db: Session = Depends(get_db)
):
    """Get dashboard by ID (PostgreSQL)."""
    db_dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    
    if not db_dashboard:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found")
    
    metadata = DashboardMetadata(
        id=db_dashboard.id,
        title=db_dashboard.title,
        description=db_dashboard.description,
        tags=db_dashboard.tags,
        template=db_dashboard.template,
        created_at=db_dashboard.created_at.isoformat(),
        updated_at=db_dashboard.updated_at.isoformat(),
        created_by=db_dashboard.created_by,
        panel_count=len(db_dashboard.config.get("panels", [])),
        version=db_dashboard.version
    )
    
    return {
        "dashboard": db_dashboard.config,
        "metadata": metadata.dict()
    }


@app.put("/api/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: str,
    dashboard: DashboardConfig,
    user: Dict[str, str] = Depends(validate_license),
    db: Session = Depends(get_db)
):
    """Update existing dashboard (PostgreSQL)."""
    db_dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    
    if not db_dashboard:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found")
    
    # Update dashboard
    db_dashboard.title = dashboard.title
    db_dashboard.description = dashboard.description
    db_dashboard.tags = dashboard.tags
    db_dashboard.config = dashboard.dict()
    db_dashboard.updated_at = datetime.utcnow()
    db_dashboard.version += 1
    
    db.commit()
    db.refresh(db_dashboard)
    
    metadata = DashboardMetadata(
        id=db_dashboard.id,
        title=db_dashboard.title,
        description=db_dashboard.description,
        tags=db_dashboard.tags,
        template=db_dashboard.template,
        created_at=db_dashboard.created_at.isoformat(),
        updated_at=db_dashboard.updated_at.isoformat(),
        created_by=db_dashboard.created_by,
        panel_count=len(dashboard.panels),
        version=db_dashboard.version
    )
    
    logger.info(f"Dashboard updated: {dashboard_id} by {user['username']}")
    
    return {
        "success": True,
        "message": f"Dashboard '{dashboard_id}' updated successfully",
        "metadata": metadata.dict()
    }


@app.delete("/api/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    user: Dict[str, str] = Depends(validate_license),
    db: Session = Depends(get_db)
):
    """Delete dashboard (PostgreSQL)."""
    db_dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    
    if not db_dashboard:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found")
    
    # Delete dashboard
    db.delete(db_dashboard)
    db.commit()
    
    logger.info(f"Dashboard deleted: {dashboard_id} by {user['username']}")
    
    return {
        "success": True,
        "message": f"Dashboard '{dashboard_id}' deleted successfully"
    }


@app.get("/api/dashboards/{dashboard_id}/export")
async def export_dashboard(
    dashboard_id: str,
    user: Dict[str, str] = Depends(validate_license),
    db: Session = Depends(get_db)
):
    """
    Export dashboard to Grafana JSON format (PostgreSQL).
    
    Returns Grafana-compatible JSON that can be imported directly.
    """
    db_dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    
    if not db_dashboard:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found")
    
    dashboard = db_dashboard.config
    metadata = {
        "id": db_dashboard.id,
        "version": db_dashboard.version,
        "created_at": db_dashboard.created_at.isoformat(),
        "updated_at": db_dashboard.updated_at.isoformat()
    }
    
    # Convert to Grafana JSON format
    grafana_json = {
        "dashboard": {
            "id": None,  # Will be assigned by Grafana
            "uid": dashboard_id,
            "title": dashboard["title"],
            "description": dashboard["description"],
            "tags": dashboard["tags"],
            "timezone": "browser",
            "editable": True,
            "schemaVersion": 38,
            "version": metadata["version"],
            "refresh": dashboard["refresh"],
            "time": {
                "from": dashboard["time_range"]["from"],
                "to": dashboard["time_range"]["to"]
            },
            "panels": [
                {
                    "id": panel["id"],
                    "type": panel["type"],
                    "title": panel["title"],
                    "datasource": panel["datasource"],
                    "gridPos": {
                        "x": panel["x"],
                        "y": panel["y"],
                        "w": panel["width"],
                        "h": panel["height"]
                    },
                    "targets": [
                        {
                            "expr": panel["query"],
                            "refId": "A"
                        }
                    ],
                    "options": panel["options"]
                }
                for panel in dashboard["panels"]
            ],
            "templating": {
                "list": dashboard.get("variables", [])
            }
        },
        "message": f"Exported from RHINOMETRIC Dashboard Builder v2.4.0",
        "overwrite": False
    }
    
    return DashboardExportResponse(
        dashboard=grafana_json,
        metadata=DashboardMetadata(**metadata)
    )


# ============================================================================
# MAIN
# ============================================================================

@app.post("/api/dashboards/grafana/create")
async def create_dashboard_in_grafana(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Create dashboard directly in Grafana AND save to PostgreSQL.
    """
    import httpx
    
    GRAFANA_URL = os.getenv("GRAFANA_URL", "http://rhinometric-grafana:3000")
    GRAFANA_API_TOKEN = os.getenv("GRAFANA_API_TOKEN")
    
    if not GRAFANA_API_TOKEN or GRAFANA_API_TOKEN == "PENDING_MANUAL_CREATION":
        raise HTTPException(
            status_code=500,
            detail="GRAFANA_API_TOKEN not configured"
        )
    
    dashboard_data = payload.get("dashboard", {})
    title = dashboard_data.get("title", "Untitled")
    panels = dashboard_data.get("panels", [])
    
    grafana_dashboard = {
        "dashboard": {
            "title": title,
            "tags": dashboard_data.get("tags", ["rhinometric"]),
            "panels": panels,
            "refresh": dashboard_data.get("refresh", "30s"),
            "time": dashboard_data.get("time_range", {"from": "now-6h", "to": "now"}),
            "schemaVersion": 16,
            "version": 0
        },
        "overwrite": False
    }
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {GRAFANA_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = await client.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=grafana_dashboard,
            headers=headers,
            timeout=10.0
        )
        
        if response.status_code == 200:
            result = response.json()
            grafana_uid = result.get("uid")
            
            # Save to PostgreSQL
            db_dashboard = Dashboard(
                id=grafana_uid,
                title=title,
                description=dashboard_data.get("description", ""),
                template="custom",
                tags=dashboard_data.get("tags", []),
                config=dashboard_data,
                created_by="system",
                grafana_uid=grafana_uid,
                enabled=True
            )
            
            db.add(db_dashboard)
            db.commit()
            
            return {
                "success": True,
                "message": f"Dashboard '{title}' created",
                "grafana_uid": grafana_uid,
                "grafana_url": result.get("url", "")
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,  # Different port from api-connector
        reload=True,
        log_level="info"
    )
