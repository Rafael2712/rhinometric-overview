"""
Bulk HTTP Service Creation.

Accepts a structured payload with common fields + list of HTTP endpoints,
validates each item reusing existing config validation, detects duplicates,
and creates services.

Reuses: _parse_tags, _parse_bool, _parse_int, _get_existing_services,
        _get_primary_target from bulk_import_service.
Reuses: validate_service_config from config_validation.

Duplicate policy: same as bulk import — same name + same URL → skipped.
Execution model: dry_run=True → preview only; dry_run=False → create.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from sqlalchemy.orm import Session

from models.external_service import ExternalService, ServiceType, ServiceStatus
from services.config_validation import validate_service_config
from services.bulk_import_service import (
    _parse_tags,
    _parse_int,
    _parse_bool,
    _get_existing_services,
    _get_primary_target,
    VALID_CATALOG_TYPES,
    DEFAULT_TIMEOUT,
    DEFAULT_INTERVAL,
)

logger = logging.getLogger("rhinometric.bulk_http")


def _build_full_url(base_url: Optional[str], path_or_url: str) -> str:
    """
    Resolve an endpoint to a full URL.
    
    - If path_or_url is already absolute (http/https), return as-is.
    - If base_url is provided and path_or_url starts with /, join them.
    - Otherwise return path_or_url stripped.
    """
    path_or_url = path_or_url.strip()
    
    # Already a full URL
    if path_or_url.lower().startswith(("http://", "https://")):
        return path_or_url
    
    # We have a base URL — join
    if base_url:
        base = base_url.strip().rstrip("/")
        path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
        return f"{base}{path}"
    
    # No base, no scheme — invalid, will be caught by validation
    return path_or_url


def process_bulk_http(
    payload: Dict[str, Any],
    db: Session,
    current_user_id: int,
) -> Dict[str, Any]:
    """
    Process a bulk HTTP creation request.
    
    Payload shape:
    {
        "dry_run": true,
        "common": {
            "base_url": "https://api.example.com",
            "method": "GET",
            "environment": "production",
            "timeout_seconds": 10,
            "check_interval_seconds": 60,
            "enabled": true,
            "catalog_type": "REST_API",
            "category": "payments",
            "tags": ["api"],
            "auth_type": "bearer",
            "auth_value": "token-xxx"
        },
        "items": [
            {"name": "Auth API", "path": "/auth"},
            {"name": "Payments API", "path": "/payments", "method": "POST"},
        ]
    }
    """
    dry_run = payload.get("dry_run", True)
    common = payload.get("common", {})
    items = payload.get("items", [])
    
    # Extract common fields
    base_url = (common.get("base_url") or "").strip() or None
    method_common = (common.get("method") or "GET").strip().upper()
    environment = (common.get("environment") or "").strip() or None
    timeout = _parse_int(common.get("timeout_seconds"), DEFAULT_TIMEOUT)
    timeout = max(1, min(120, timeout))
    interval = _parse_int(common.get("check_interval_seconds"), DEFAULT_INTERVAL)
    interval = max(10, min(86400, interval))
    enabled = _parse_bool(common.get("enabled", True))
    
    # Catalog metadata
    catalog_type = (common.get("catalog_type") or "REST_API").strip().upper()
    if catalog_type not in VALID_CATALOG_TYPES:
        catalog_type = "REST_API"
    category = (common.get("category") or "").strip() or None
    tags_common = _parse_tags(common.get("tags"))
    
    # Auth
    auth_type = (common.get("auth_type") or "").strip() or None
    auth_value = (common.get("auth_value") or "").strip() or None
    
    # Health path common
    health_path_common = (common.get("health_path") or "").strip() or None
    
    result = {
        "total_received": len(items),
        "valid_count": 0,
        "invalid_count": 0,
        "duplicate_count": 0,
        "created_count": 0,
        "skipped_count": 0,
        "dry_run": dry_run,
        "errors": [],
        "created_services": [],
        "valid_preview": [],
    }
    
    if not items:
        return result
    
    existing_map = _get_existing_services(db)
    seen_in_batch = set()
    valid_services = []
    
    for i, item in enumerate(items):
        row_num = i + 1
        errors = []
        
        # Name: required
        name = (item.get("name") or "").strip()
        if not name:
            errors.append("name is required")
        
        # Path or full URL: required
        path_raw = (item.get("path") or item.get("url") or "").strip()
        if not path_raw:
            errors.append("path or url is required")
        
        if errors:
            result["invalid_count"] += 1
            result["errors"].append({
                "row": row_num,
                "name": name or f"(item {row_num})",
                "errors": errors,
            })
            continue
        
        # Build full URL
        full_url = _build_full_url(base_url, path_raw)
        
        # Per-item overrides
        method = (item.get("method") or method_common).strip().upper()
        health_path = (item.get("health_path") or health_path_common or "").strip() or None
        
        # Merge tags: common + per-item extra
        item_extra_tags = _parse_tags(item.get("tags"))
        merged_tags = list(dict.fromkeys(tags_common + item_extra_tags)) if (tags_common or item_extra_tags) else None
        
        # Build HTTP config
        config = {
            "url": full_url,
            "method": method,
        }
        if health_path:
            config["health_path"] = health_path
        if auth_type:
            config["auth_type"] = auth_type
        if auth_value:
            config["auth_value"] = auth_value
        
        # Validate config using existing validation
        _, config_errors = validate_service_config("http", config, service_name=name)
        if config_errors:
            result["invalid_count"] += 1
            result["errors"].append({
                "row": row_num,
                "name": name,
                "errors": config_errors,
            })
            continue
        
        # Duplicate detection
        target = _get_primary_target("http", config)
        dup_key = f"{name.lower().strip()}|{target}"
        
        if dup_key in existing_map:
            result["duplicate_count"] += 1
            result["skipped_count"] += 1
            result["errors"].append({
                "row": row_num,
                "name": name,
                "errors": [f"Duplicate: service with same name and URL already exists (id={existing_map[dup_key]})"],
                "status": "skipped",
            })
            continue
        
        if dup_key in seen_in_batch:
            result["duplicate_count"] += 1
            result["skipped_count"] += 1
            result["errors"].append({
                "row": row_num,
                "name": name,
                "errors": ["Duplicate: same name and URL appears earlier in this batch"],
                "status": "skipped",
            })
            continue
        
        seen_in_batch.add(dup_key)
        result["valid_count"] += 1
        
        svc_data = {
            "name": name,
            "service_type": "http",
            "environment": environment,
            "enabled": enabled,
            "config": config,
            "timeout_seconds": timeout,
            "check_interval_seconds": interval,
            "catalog_type": catalog_type,
            "category": category,
            "tags": merged_tags,
        }
        valid_services.append(svc_data)
        
        result["valid_preview"].append({
            "row": row_num,
            "name": name,
            "service_type": "http",
            "url": full_url,
            "method": method,
            "environment": environment,
            "catalog_type": catalog_type,
            "category": category,
            "tags": merged_tags or [],
        })
    
    # dry_run → stop here
    if dry_run:
        return result
    
    # Create services
    for svc_data in valid_services:
        try:
            svc = ExternalService(
                name=svc_data["name"],
                service_type=ServiceType("http"),
                environment=svc_data.get("environment"),
                enabled=svc_data.get("enabled", True),
                config=svc_data["config"],
                timeout_seconds=svc_data.get("timeout_seconds", DEFAULT_TIMEOUT),
                check_interval_seconds=svc_data.get("check_interval_seconds", DEFAULT_INTERVAL),
                catalog_type=svc_data.get("catalog_type"),
                category=svc_data.get("category"),
                tags=svc_data.get("tags"),
                group_name=svc_data.get("group_name", "Default"),
                status=ServiceStatus.UNKNOWN,
                created_by=current_user_id,
            )
            db.add(svc)
            db.flush()
            result["created_count"] += 1
            result["created_services"].append({
                "id": svc.id,
                "name": svc.name,
                "service_type": "http",
                "url": svc.config.get("url", ""),
                "status": "created",
            })
            logger.info(f"[BulkHTTP] Created: {svc.name} (id={svc.id})")
        except Exception as e:
            result["skipped_count"] += 1
            result["valid_count"] -= 1
            result["errors"].append({
                "row": None,
                "name": svc_data["name"],
                "errors": [f"Database error: {str(e)}"],
                "status": "error",
            })
            logger.error(f"[BulkHTTP] Failed: {svc_data['name']}: {e}")
    
    if not dry_run:
        result.pop("valid_preview", None)
    
    return result
