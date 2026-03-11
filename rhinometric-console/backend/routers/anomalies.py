from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Any
import httpx
import hashlib
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()


# ── Unified Anomaly Model ─────────────────────────────────────────
class UnifiedAnomaly(BaseModel):
    """Unified anomaly schema for Phase 1.2.
    All anomalies (service, infrastructure, website) share this structure.
    """
    id: str
    timestamp: str
    entity_type: str            # "service" | "infrastructure" | "website"
    entity_name: str            # Human-readable name
    source: str                 # "external_services" | "node_exporter" | "cadvisor" | etc.
    metric_name: str            # Real metric being analyzed
    severity: str               # "low" | "medium" | "high" | "critical"
    current_value: float
    expected_value: float
    deviation_percent: float
    status: str                 # "active" | "resolved" | "false_positive" | "suppressed"
    # Optional fields
    confidence: float | None = None
    analysis: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None


class AnomaliesResponse(BaseModel):
    anomalies: list[UnifiedAnomaly]
    total: int
    page: int
    page_size: int


# ── Entity type inference from metric name ────────────────────────
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

# Friendly display names for infrastructure metrics
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


def normalize_anomaly(raw: dict, index: int) -> dict:
    """Normalize any anomaly dict into the unified schema.
    Handles both new (entity_type populated) and legacy (missing fields) anomalies.
    """
    metric_name = raw.get("metric_name", "unknown")
    
    # Strip ::entity_name suffix for base metric lookup
    base_metric = metric_name.split("::")[0].strip()
    entity_suffix = metric_name.split("::")[-1].strip() if "::" in metric_name else ""
    
    # ── Resolve entity_type and source ──
    entity_type = raw.get("entity_type", "").strip()
    source = raw.get("source", "").strip()
    entity_name = raw.get("entity_name", "").strip()
    
    if not entity_type or not source:
        # Infer from metric name
        inferred = METRIC_ENTITY_MAP.get(base_metric)
        if inferred:
            if not entity_type:
                entity_type = inferred[0]
            if not source:
                source = inferred[1]
    
    # Fallback defaults for legacy anomalies
    if not entity_type:
        entity_type = "infrastructure"
    if not source:
        source = "legacy"
        
    # ── Resolve entity_name ──
    if not entity_name:
        if entity_suffix:
            entity_name = entity_suffix
        elif base_metric in METRIC_DISPLAY_NAMES:
            entity_name = METRIC_DISPLAY_NAMES[base_metric]
        else:
            entity_name = base_metric.replace("_", " ").title()
    
    # ── Generate stable ID ──
    raw_id = raw.get("id")
    if raw_id:
        anomaly_id = str(raw_id)
    else:
        # Hash from metric + timestamp for stability
        id_seed = f"{metric_name}:{raw.get('timestamp', index)}"
        anomaly_id = hashlib.sha256(id_seed.encode()).hexdigest()[:12]
    
    # ── Map severity ──
    severity = raw.get("severity", "low").lower()
    # Normalize legacy severity values
    severity_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "warning": "medium",
        "low": "low",
        "info": "low",
    }
    severity = severity_map.get(severity, severity)
    
    # ── Build tags ──
    tags = []
    if raw.get("is_anomaly"):
        tags.append("anomaly")
    models = raw.get("models_used", [])
    if models:
        tags.extend([f"model:{m}" for m in models])
    priority = (raw.get("metadata") or {}).get("priority")
    if priority:
        tags.append(f"priority:{priority}")
    
    # ── Build analysis text ──
    analysis = raw.get("baseline_explanation")
    
    return {
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


@router.get("")
async def get_anomalies(
    current_user: UserModel = Depends(get_current_user),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    entity_type: Optional[str] = Query(None, description="Filter by entity_type: service, infrastructure, website"),
    source: Optional[str] = Query(None, description="Filter by source"),
    time_range: Optional[str] = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get anomalies from AI Anomaly Detection Engine (port 8085).
    Returns anomalies normalized to the Unified Anomaly Model.
    
    Filters:
    - severity: critical, high, medium, low
    - entity_type: service, infrastructure, website
    - source: external_services, node_exporter, cadvisor, etc.
    - time_range: 1h, 24h, 7d, 30d
    - pagination: page, page_size
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "time_range": time_range,
                "limit": page_size
            }
            if severity:
                params["severity"] = severity
            
            response = await client.get(
                f"{settings.AI_ANOMALY_URL}/anomalies",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                raw_anomalies = data.get("anomalies", [])
                
                # Normalize all anomalies to unified schema
                normalized = []
                for i, raw in enumerate(raw_anomalies):
                    normalized.append(normalize_anomaly(raw, i))
                
                # Apply entity_type filter (post-normalization)
                if entity_type:
                    normalized = [a for a in normalized if a["entity_type"] == entity_type]
                
                # Apply source filter (post-normalization)
                if source:
                    normalized = [a for a in normalized if a["source"] == source]
                
                # Sort by timestamp DESC
                normalized.sort(
                    key=lambda x: x.get("timestamp", ""),
                    reverse=True
                )
                
                return {
                    "anomalies": normalized,
                    "total": len(normalized),
                    "page": page,
                    "page_size": page_size,
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AI Anomaly service error: {response.text}"
                )
                
    except httpx.ConnectError as e:
        print(f"Error connecting to AI Anomaly service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"AI Anomaly Detection Engine connection failed: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching anomalies: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"AI Anomaly service error: {str(e)}"
        )


@router.get("/{anomaly_id}")
async def get_anomaly_details(
    anomaly_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    """Get detailed information about a specific anomaly (unified model)"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch all anomalies and find by ID
            response = await client.get(
                f"{settings.AI_ANOMALY_URL}/anomalies",
                params={"limit": 500}
            )
            
            if response.status_code == 200:
                data = response.json()
                raw_anomalies = data.get("anomalies", [])
                
                for i, raw in enumerate(raw_anomalies):
                    normalized = normalize_anomaly(raw, i)
                    if normalized["id"] == anomaly_id:
                        return normalized
                
                raise HTTPException(status_code=404, detail="Anomaly not found")
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="AI Anomaly Detection Engine is not available"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
