from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
import httpx
import hashlib
from datetime import datetime
import logging
import time
from itertools import groupby as itertools_groupby
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()
logger = logging.getLogger("anomalies")


# -- Phase 2.1: Anomaly Occurrence (single detection event) ------
class AnomalyOccurrence(BaseModel):
    """A single detection event within an anomaly group."""
    timestamp: str
    current_value: float
    expected_value: float
    deviation_percent: float
    severity: str
    confidence: float | None = None
    analysis: str | None = None


# -- Phase 2.1: Anomaly Group (deduplicated, lifecycle-managed) --
class AnomalyGroup(BaseModel):
    """Deduplicated anomaly group with lifecycle management.
    Phase 2.1: Groups occurrences by fingerprint.
    fingerprint = sha256(entity_type|entity_name|metric_name|source)[:16]
    """
    fingerprint: str
    entity_type: str
    entity_name: str
    metric_name: str
    source: str
    first_seen: str
    last_seen: str
    occurrence_count: int
    severity_current: str
    status: str
    occurrences: list[AnomalyOccurrence] = Field(default_factory=list)
    environment: str = Field(default="unknown")
    service_group: str = Field(default="default")
    region: str | None = None
    cluster: str | None = None
    priority: int = Field(default=2)
    tags: list[str] | None = None
    metadata: dict | None = None


class AnomalyGroupsResponse(BaseModel):
    anomaly_groups: list[AnomalyGroup]
    total: int
    page: int
    page_size: int


class OccurrencesResponse(BaseModel):
    fingerprint: str
    entity_type: str
    entity_name: str
    metric_name: str
    source: str
    occurrences: list[AnomalyOccurrence]
    total: int


class StatusUpdateRequest(BaseModel):
    status: str


# -- Priority + severity sort helpers ----------------------------
ENTITY_PRIORITY = {
    "service": 1,
    "website": 2,
    "infrastructure": 3,
}

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


# -- Entity type inference from metric name ----------------------
METRIC_ENTITY_MAP = {
    "node_cpu_usage": ("infrastructure", "node_exporter"),
    "node_memory_usage": ("infrastructure", "node_exporter"),
    "node_disk_usage": ("infrastructure", "node_exporter"),
    "node_disk_io": ("infrastructure", "node_exporter"),
    "node_network_receive": ("infrastructure", "node_exporter"),
    "node_network_transmit": ("infrastructure", "node_exporter"),
    "container_cpu_usage": ("infrastructure", "cadvisor"),
    "container_memory_usage": ("infrastructure", "cadvisor"),
    "rhinometric_website_availability": ("website", "blackbox_exporter"),
    "rhinometric_website_response_time": ("website", "blackbox_exporter"),
    "rhinometric_website_ssl_expiry": ("website", "blackbox_exporter"),
    "rhinometric_website_dns_time": ("website", "blackbox_exporter"),
    "license_validation_rate": ("infrastructure", "internal_monitoring"),
    "license_expired_count": ("infrastructure", "internal_monitoring"),
    "external_service_latency": ("service", "external_services"),
    "external_service_health": ("service", "external_services"),
    "external_service_availability": ("service", "external_services"),
}

METRIC_DISPLAY_NAMES = {
    "node_cpu_usage": "Node CPU",
    "node_memory_usage": "Node Memory",
    "node_disk_usage": "Node Disk",
    "node_disk_io": "Node Disk I/O",
    "node_network_receive": "Network Receive",
    "node_network_transmit": "Network Transmit",
    "container_cpu_usage": "Container CPU",
    "container_memory_usage": "Container Memory",
    "rhinometric_website_availability": "Rhinometric Website",
    "rhinometric_website_response_time": "Rhinometric Website",
    "rhinometric_website_ssl_expiry": "Website SSL Certificate",
    "rhinometric_website_dns_time": "Website DNS",
    "license_validation_rate": "License Validation",
    "license_expired_count": "Expired Licenses",
}

INFRA_SERVICE_GROUPS = {
    "node_cpu_usage": "compute",
    "node_memory_usage": "compute",
    "node_disk_usage": "storage",
    "node_disk_io": "storage",
    "node_network_receive": "network",
    "node_network_transmit": "network",
    "container_cpu_usage": "containers",
    "container_memory_usage": "containers",
    "license_validation_rate": "licensing",
    "license_expired_count": "licensing",
}


# -- Service Registry Cache --------------------------------------
_service_registry_cache: Dict[str, dict] = {}
_service_registry_ttl: float = 0


def _load_service_registry() -> Dict[str, dict]:
    """Load external services from DB for context enrichment.
    Cached for 60 seconds to avoid DB pressure.
    """
    global _service_registry_cache, _service_registry_ttl

    now = time.time()
    if _service_registry_cache and now < _service_registry_ttl:
        return _service_registry_cache

    try:
        from database import SessionLocal
        from models.external_service import ExternalService
        db = SessionLocal()
        services = db.query(ExternalService).filter(ExternalService.enabled == True).all()
        registry = {}
        for svc in services:
            d = svc.to_dict()
            svc_name = d["name"]
            svc_type = d.get("service_type") or "unknown"
            if svc_type == "postgresql":
                service_group = "databases"
            elif svc_type == "http":
                service_group = "apis"
            else:
                service_group = "default"
            tags = []
            if svc_type:
                tags.append(f"type:{svc_type}")
            if d.get("status"):
                tags.append(f"status:{d['status']}")
            registry[svc_name] = {
                "environment": d.get("environment") or "unknown",
                "service_type": svc_type,
                "service_group": service_group,
                "description": d.get("description") or "",
                "tags": tags,
            }
        db.close()
        _service_registry_cache = registry
        _service_registry_ttl = now + 60
        logger.debug(f"Service registry loaded: {len(registry)} services")
        return registry
    except Exception as e:
        logger.warning(f"Failed to load service registry: {e}")
        return _service_registry_cache


def _enrich_anomaly(normalized: dict) -> dict:
    """Add context enrichment + priority to a normalized anomaly."""
    entity_type = normalized.get("entity_type", "")
    entity_name = normalized.get("entity_name", "")
    base_metric = normalized.get("metric_name", "")

    if entity_type == "service":
        registry = _load_service_registry()
        svc_info = registry.get(entity_name, {})
        normalized["environment"] = svc_info.get("environment", "unknown")
        normalized["service_group"] = svc_info.get("service_group", "default")
        existing_tags = normalized.get("tags") or []
        registry_tags = svc_info.get("tags", [])
        merged_tags = list(dict.fromkeys(existing_tags + registry_tags))
        normalized["tags"] = merged_tags if merged_tags else None
    elif entity_type == "infrastructure":
        normalized["environment"] = "production"
        normalized["service_group"] = INFRA_SERVICE_GROUPS.get(base_metric, "system")
    elif entity_type == "website":
        normalized["environment"] = "production"
        normalized["service_group"] = "websites"
    else:
        normalized["environment"] = "unknown"
        normalized["service_group"] = "default"

    normalized.setdefault("region", None)
    normalized.setdefault("cluster", None)
    normalized["priority"] = ENTITY_PRIORITY.get(entity_type, 3)

    return normalized


def normalize_anomaly(raw: dict, index: int) -> dict:
    """Normalize any anomaly dict into unified schema + enrichment."""
    metric_name = raw.get("metric_name", "unknown")
    base_metric = metric_name.split("::")[0].strip()
    entity_suffix = metric_name.split("::")[-1].strip() if "::" in metric_name else ""

    entity_type = raw.get("entity_type", "").strip()
    source = raw.get("source", "").strip()
    entity_name = raw.get("entity_name", "").strip()

    if not entity_type or not source:
        inferred = METRIC_ENTITY_MAP.get(base_metric)
        if inferred:
            if not entity_type:
                entity_type = inferred[0]
            if not source:
                source = inferred[1]

    if not entity_type:
        entity_type = "infrastructure"
    if not source:
        source = "legacy"

    if not entity_name:
        if entity_suffix:
            entity_name = entity_suffix
        elif base_metric in METRIC_DISPLAY_NAMES:
            entity_name = METRIC_DISPLAY_NAMES[base_metric]
        else:
            entity_name = base_metric.replace("_", " ").title()

    raw_id = raw.get("id")
    if raw_id:
        anomaly_id = str(raw_id)
    else:
        id_seed = f"{metric_name}:{raw.get('timestamp', index)}"
        anomaly_id = hashlib.sha256(id_seed.encode()).hexdigest()[:12]

    severity = raw.get("severity", "low").lower()
    severity_map = {
        "critical": "critical", "high": "high", "medium": "medium",
        "warning": "medium", "low": "low", "info": "low",
    }
    severity = severity_map.get(severity, severity)

    tags = []
    if raw.get("is_anomaly"):
        tags.append("anomaly")
    models = raw.get("models_used", [])
    if models:
        tags.extend([f"model:{m}" for m in models])
    priority_tag = (raw.get("metadata") or {}).get("priority")
    if priority_tag:
        tags.append(f"priority:{priority_tag}")

    analysis = raw.get("baseline_explanation")

    normalized = {
        "id": anomaly_id,
        "timestamp": raw.get("timestamp", ""),
        "entity_type": entity_type,
        "entity_name": entity_name,
        "source": source,
        "metric_name": base_metric,
        "severity": severity,
        "current_value": float(raw.get("current_value", 0)),
        "expected_value": float(raw.get("expected_value", 0)),
        "deviation_percent": float(raw.get("deviation_percent", 0)),
        "status": raw.get("status", "active"),
        "confidence": raw.get("confidence"),
        "analysis": analysis,
        "tags": tags if tags else None,
        "metadata": raw.get("metadata"),
    }

    normalized = _enrich_anomaly(normalized)
    return normalized


# -- Phase 2.1: Fingerprint + Grouping Engine --------------------

def _generate_fingerprint(entity_type: str, entity_name: str, metric_name: str, source: str) -> str:
    """Generate deterministic fingerprint for anomaly grouping.
    fingerprint = sha256(entity_type|entity_name|metric_name|source)[:16]
    """
    seed = f"{entity_type}|{entity_name}|{metric_name}|{source}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


# In-memory lifecycle status store (Phase 2.1)
_status_overrides: Dict[str, str] = {}
VALID_STATUSES = {"active", "acknowledged", "false_positive", "suppressed", "resolved", "alert_created"}

# Auto-resolution: groups with no new occurrences within this window
# are automatically transitioned to "resolved".
AUTO_RESOLVE_WINDOW = 1800  # seconds (30 minutes)
# Statuses that must NOT be auto-resolved (user-intent statuses)
_NO_AUTO_RESOLVE = {"false_positive", "suppressed", "alert_created"}


def _build_anomaly_groups(normalized_anomalies: list[dict]) -> list[dict]:
    """Transform flat normalized anomalies into deduplicated groups.
    Each unique (entity_type, entity_name, metric_name, source) combination
    becomes one AnomalyGroup with multiple occurrences.
    """
    groups: Dict[str, dict] = {}

    for a in normalized_anomalies:
        fp = _generate_fingerprint(
            a["entity_type"], a["entity_name"],
            a["metric_name"], a["source"]
        )

        occurrence = {
            "timestamp": a["timestamp"],
            "current_value": a["current_value"],
            "expected_value": a["expected_value"],
            "deviation_percent": a["deviation_percent"],
            "severity": a["severity"],
            "confidence": a.get("confidence"),
            "analysis": a.get("analysis"),
        }

        if fp in groups:
            g = groups[fp]
            g["occurrences"].append(occurrence)
            g["occurrence_count"] += 1
            if a["timestamp"] > g["last_seen"]:
                g["last_seen"] = a["timestamp"]
                g["severity_current"] = a["severity"]
            if a["timestamp"] < g["first_seen"]:
                g["first_seen"] = a["timestamp"]
        else:
            groups[fp] = {
                "fingerprint": fp,
                "entity_type": a["entity_type"],
                "entity_name": a["entity_name"],
                "metric_name": a["metric_name"],
                "source": a["source"],
                "first_seen": a["timestamp"],
                "last_seen": a["timestamp"],
                "occurrence_count": 1,
                "severity_current": a["severity"],
                "status": _status_overrides.get(fp, "active"),
                "occurrences": [occurrence],
                "environment": a.get("environment", "unknown"),
                "service_group": a.get("service_group", "default"),
                "region": a.get("region"),
                "cluster": a.get("cluster"),
                "priority": a.get("priority", 2),
                "tags": a.get("tags"),
                "metadata": a.get("metadata"),
            }

    # Sort occurrences DESC by timestamp within each group
    for g in groups.values():
        g["occurrences"].sort(key=lambda o: o["timestamp"], reverse=True)
        g["status"] = _status_overrides.get(g["fingerprint"], "active")

    # ── Auto-resolution pass ──────────────────────────────────────
    # If a group's last_seen is older than AUTO_RESOLVE_WINDOW and its
    # status is eligible, automatically transition it to "resolved".
    now = datetime.utcnow()
    for g in groups.values():
        if g["status"] in _NO_AUTO_RESOLVE:
            continue  # never auto-resolve user-intent statuses
        try:
            last = datetime.fromisoformat(g["last_seen"].replace("Z", "+00:00").replace("+00:00", ""))
        except Exception:
            continue
        age_seconds = (now - last).total_seconds()
        if age_seconds > AUTO_RESOLVE_WINDOW:
            g["status"] = "resolved"
            # Persist so the override survives between API calls
            _status_overrides[g["fingerprint"]] = "resolved"

    return list(groups.values())


async def _fetch_and_normalize(time_range: str = "24h", limit: int = 500) -> list[dict]:
    """Fetch raw anomalies from AI service and normalize them."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.AI_ANOMALY_URL}/anomalies",
            params={"time_range": time_range, "limit": limit}
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"AI Anomaly service error: {response.text}"
            )
        data = response.json()
        raw_anomalies = data.get("anomalies", [])
        return [normalize_anomaly(raw, i) for i, raw in enumerate(raw_anomalies)]


# -- API Endpoints ------------------------------------------------

@router.get("")
async def get_anomalies(
    current_user: UserModel = Depends(get_current_user),
    severity: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    service_group: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by lifecycle status"),
    time_range: Optional[str] = Query("24h"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Get anomaly groups -- deduplicated with occurrence counts and lifecycle status."""
    try:
        normalized = await _fetch_and_normalize(time_range, page_size * 3)
        groups = _build_anomaly_groups(normalized)

        if entity_type:
            groups = [g for g in groups if g["entity_type"] == entity_type]
        if source:
            groups = [g for g in groups if g["source"] == source]
        if environment:
            groups = [g for g in groups if g["environment"] == environment]
        if service_group:
            groups = [g for g in groups if g["service_group"] == service_group]
        if severity:
            groups = [g for g in groups if g["severity_current"] == severity]
        if status:
            groups = [g for g in groups if g["status"] == status]

        # Sort: priority ASC -> severity DESC -> last_seen DESC
        temp = sorted(groups, key=lambda g: (
            g.get("priority", 3),
            SEVERITY_ORDER.get(g.get("severity_current", "low"), 3),
        ))
        result = []
        for _, grp in itertools_groupby(temp, key=lambda g: (
            g.get("priority", 3),
            SEVERITY_ORDER.get(g.get("severity_current", "low"), 3),
        )):
            bucket = sorted(grp, key=lambda x: x.get("last_seen", ""), reverse=True)
            result.extend(bucket)

        # Build backward-compat flat list for cached old frontends
        compat_list = []
        for g in result:
            latest = g["occurrences"][0] if g.get("occurrences") else {}
            flat = {
                "id": g["fingerprint"],
                "timestamp": g["last_seen"],
                "entity_type": g["entity_type"],
                "entity_name": g["entity_name"],
                "source": g["source"],
                "metric_name": g["metric_name"],
                "severity": g["severity_current"],
                "current_value": latest.get("current_value", 0),
                "expected_value": latest.get("expected_value", 0),
                "deviation_percent": latest.get("deviation_percent", 0),
                "status": g["status"],
                "confidence": latest.get("confidence"),
                "analysis": latest.get("analysis"),
                "tags": g.get("tags"),
                "metadata": g.get("metadata"),
                "environment": g.get("environment", "unknown"),
                "service_group": g.get("service_group", "default"),
                "region": g.get("region"),
                "cluster": g.get("cluster"),
                "priority": g.get("priority", 2),
            }
            compat_list.append(flat)

        return {
            "anomaly_groups": result,
            "anomalies": compat_list,  # backward compat: flat format for cached old frontends
            "total": len(result),
            "page": page,
            "page_size": page_size,
        }

    except httpx.ConnectError as e:
        raise HTTPException(status_code=503, detail=f"AI Anomaly Detection Engine connection failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching anomaly groups: {e}")
        raise HTTPException(status_code=503, detail=f"AI Anomaly service error: {str(e)}")


@router.get("/{fingerprint}/occurrences")
async def get_occurrences(
    fingerprint: str,
    current_user: UserModel = Depends(get_current_user),
    time_range: Optional[str] = Query("24h"),
):
    """Get all occurrences for a specific anomaly group."""
    try:
        normalized = await _fetch_and_normalize(time_range, 500)
        groups = _build_anomaly_groups(normalized)

        for g in groups:
            if g["fingerprint"] == fingerprint:
                return {
                    "fingerprint": g["fingerprint"],
                    "entity_type": g["entity_type"],
                    "entity_name": g["entity_name"],
                    "metric_name": g["metric_name"],
                    "source": g["source"],
                    "occurrences": g["occurrences"],
                    "total": g["occurrence_count"],
                }

        raise HTTPException(status_code=404, detail="Anomaly group not found")

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="AI Anomaly Detection Engine is not available")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{fingerprint}/status")
async def update_anomaly_status(
    fingerprint: str,
    body: StatusUpdateRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """Update lifecycle status for an anomaly group.
    Valid statuses: active, acknowledged, false_positive, suppressed, resolved, alert_created
    """
    new_status = body.status.lower().strip()
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid: {', '.join(sorted(VALID_STATUSES))}"
        )

    _status_overrides[fingerprint] = new_status
    logger.info(f"Anomaly {fingerprint} status -> {new_status} by {current_user.username}")
    return {"fingerprint": fingerprint, "status": new_status, "message": f"Status updated to {new_status}"}


@router.get("/{fingerprint}")
async def get_anomaly_group(
    fingerprint: str,
    current_user: UserModel = Depends(get_current_user),
    time_range: Optional[str] = Query("24h"),
):
    """Get detailed anomaly group by fingerprint."""
    try:
        normalized = await _fetch_and_normalize(time_range, 500)
        groups = _build_anomaly_groups(normalized)

        for g in groups:
            if g["fingerprint"] == fingerprint:
                return g

        raise HTTPException(status_code=404, detail="Anomaly group not found")

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="AI Anomaly Detection Engine is not available")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))