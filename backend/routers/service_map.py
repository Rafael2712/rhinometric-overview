"""
Service Map router — Phase 2.8 Service Dependency Map.

Provides:
  GET  /               → Full dependency graph (nodes + edges)
  GET  /services/list  → All services for the dependency creation UI
  POST /dependencies   → Create a new dependency
  DELETE /dependencies/{id}  → Remove a dependency

Status logic (per node):
  1. Active incident          → "incident"
  2. Active critical/warning alert → "degraded"
  3. Otherwise                → "healthy"

Impact propagation:
  If a service has status "incident", every *upstream* service that
  depends on it (i.e. source_service → this_service) is marked "impacted".
  Propagation depth: 1 level (MVP).
"""

import uuid as _uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from database import get_db
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from models.external_service import ExternalService
from models.service_dependency import ServiceDependency
from models.incident import Incident
from models.alert_event import AlertEvent
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

ALLOWED_DEP_TYPES = {"http", "database", "cache", "queue", "external"}


# ── Schemas ─────────────────────────────────────────────────────

class DependencyCreate(BaseModel):
    source_service_id: int
    target_service_id: int
    dependency_type: str = "http"
    description: Optional[str] = None

class DependencyResponse(BaseModel):
    id: str
    source_service_id: int
    target_service_id: int
    dependency_type: str
    description: Optional[str]
    created_at: Optional[str]

class NodeResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    incident_id: Optional[str] = None
    service_type: Optional[str] = None
    environment: Optional[str] = None
    last_response_time_ms: Optional[float] = None
    last_check_at: Optional[str] = None

class EdgeResponse(BaseModel):
    id: str
    source: int
    target: int
    type: str
    description: Optional[str] = None

class GraphResponse(BaseModel):
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]

class ServiceListItem(BaseModel):
    id: int
    name: str
    service_type: str
    status: str
    environment: Optional[str] = None


# ── Helper: Derive service status from incidents + alerts ───────

def _derive_service_statuses(db: Session) -> dict:
    """
    Build a dict mapping service name → (status, incident_id).
    Priority: incident > degraded > healthy.
    """
    statuses = {}  # name → {"status": ..., "incident_id": ...}

    # 1. Open/investigating incidents
    active_incidents = (
        db.query(Incident)
        .filter(Incident.status.in_(["open", "investigating"]))
        .all()
    )
    for inc in active_incidents:
        name = inc.entity_name
        if name not in statuses or statuses[name]["status"] != "incident":
            statuses[name] = {
                "status": "incident",
                "incident_id": str(inc.id),
            }

    # 2. Firing alerts (not resolved)
    active_alerts = (
        db.query(AlertEvent.entity_name)
        .filter(AlertEvent.status == "firing")
        .distinct()
        .all()
    )
    for (name,) in active_alerts:
        if name not in statuses:
            statuses[name] = {"status": "degraded", "incident_id": None}

    return statuses


# ── GET / — Full graph ──────────────────────────────────────────

@router.get("", response_model=GraphResponse)
@router.get("/", response_model=GraphResponse)
async def get_service_map(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return the full service dependency graph with live status."""

    # 1. Fetch all enabled services (nodes)
    services = (
        db.query(ExternalService)
        .filter(ExternalService.enabled == True)
        .order_by(ExternalService.name)
        .all()
    )

    # 2. Fetch all dependencies (edges)
    deps = db.query(ServiceDependency).all()

    # 3. Derive live statuses
    status_map = _derive_service_statuses(db)

    # 4. Build node list
    nodes = []
    service_id_map = {}  # id → name (for impact propagation)
    for svc in services:
        svc_status_info = status_map.get(svc.name, {"status": "healthy", "incident_id": None})
        node = NodeResponse(
            id=svc.id,
            name=svc.name,
            type=svc.service_type.value if svc.service_type else "http",
            status=svc_status_info["status"],
            incident_id=svc_status_info.get("incident_id"),
            service_type=svc.service_type.value if svc.service_type else None,
            environment=svc.environment,
            last_response_time_ms=svc.last_response_time_ms,
            last_check_at=svc.last_check_at.isoformat() if svc.last_check_at else None,
        )
        nodes.append(node)
        service_id_map[svc.id] = svc.name

    # 5. Impact propagation (1 level)
    #    If target_service has status=incident → source_service becomes "impacted"
    incident_target_ids = set()
    for node in nodes:
        if node.status == "incident":
            incident_target_ids.add(node.id)

    if incident_target_ids:
        for dep in deps:
            if dep.target_service_id in incident_target_ids:
                # Mark source as impacted (unless already incident)
                for node in nodes:
                    if node.id == dep.source_service_id and node.status not in ("incident",):
                        node.status = "impacted"

    # 6. Build edge list
    edges = []
    for dep in deps:
        edges.append(EdgeResponse(
            id=str(dep.id),
            source=dep.source_service_id,
            target=dep.target_service_id,
            type=dep.dependency_type,
            description=dep.description,
        ))

    return GraphResponse(nodes=nodes, edges=edges)


# ── GET /services/list — Services list for UI ──────────────────

@router.get("/services/list", response_model=List[ServiceListItem])
async def list_services_for_map(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """List all services (for dependency creation UI)."""
    services = (
        db.query(ExternalService)
        .filter(ExternalService.enabled == True)
        .order_by(ExternalService.name)
        .all()
    )
    return [
        ServiceListItem(
            id=s.id,
            name=s.name,
            service_type=s.service_type.value if s.service_type else "http",
            status=s.status.value if s.status else "unknown",
            environment=s.environment,
        )
        for s in services
    ]


# ── POST /dependencies — Create dependency ─────────────────────

@router.post("/dependencies", status_code=status.HTTP_201_CREATED)
async def create_dependency(
    body: DependencyCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
):
    """Create a directional dependency between two services."""

    # Validate type
    if body.dependency_type not in ALLOWED_DEP_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dependency_type. Allowed: {sorted(ALLOWED_DEP_TYPES)}",
        )

    # Self-reference check
    if body.source_service_id == body.target_service_id:
        raise HTTPException(status_code=400, detail="A service cannot depend on itself")

    # Verify services exist
    src = db.query(ExternalService).filter(ExternalService.id == body.source_service_id).first()
    tgt = db.query(ExternalService).filter(ExternalService.id == body.target_service_id).first()
    if not src:
        raise HTTPException(status_code=404, detail=f"Source service {body.source_service_id} not found")
    if not tgt:
        raise HTTPException(status_code=404, detail=f"Target service {body.target_service_id} not found")

    # Check duplicate
    existing = (
        db.query(ServiceDependency)
        .filter(
            ServiceDependency.source_service_id == body.source_service_id,
            ServiceDependency.target_service_id == body.target_service_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Dependency already exists")

    dep = ServiceDependency(
        source_service_id=body.source_service_id,
        target_service_id=body.target_service_id,
        dependency_type=body.dependency_type,
        description=body.description,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)

    logger.info(
        f"Dependency created: {src.name} → {tgt.name} ({body.dependency_type})",
        extra={"user": current_user.username},
    )

    return {
        "id": str(dep.id),
        "source_service_id": dep.source_service_id,
        "target_service_id": dep.target_service_id,
        "dependency_type": dep.dependency_type,
        "description": dep.description,
        "source_name": src.name,
        "target_name": tgt.name,
        "created_at": dep.created_at.isoformat() if dep.created_at else None,
    }


# ── DELETE /dependencies/{id} — Remove dependency ──────────────

@router.delete("/dependencies/{dep_id}", status_code=status.HTTP_200_OK)
async def delete_dependency(
    dep_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["OWNER", "ADMIN"])),
):
    """Remove a dependency."""
    try:
        dep_uuid = _uuid.UUID(dep_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dependency ID")

    dep = db.query(ServiceDependency).filter(ServiceDependency.id == dep_uuid).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")

    src_name = dep.source_service.name if dep.source_service else "?"
    tgt_name = dep.target_service.name if dep.target_service else "?"

    db.delete(dep)
    db.commit()

    logger.info(
        f"Dependency deleted: {src_name} → {tgt_name}",
        extra={"user": current_user.username},
    )

    return {"status": "deleted", "id": dep_id}

