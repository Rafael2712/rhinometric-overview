"""
Bulk Import Service for External Services.

Parses CSV and JSON files, validates each row reusing existing
config validation, detects duplicates, and creates services.

Duplicate policy (v1):
  - A service is considered a duplicate if another service with the
    same name AND the same primary target already exists.
    For HTTP:       same name + same config.url
    For PostgreSQL: same name + same host:port/database_name
  - Duplicates are SKIPPED (never overwritten or merged).
  - No existing services are modified or deleted.

Execution model:
  - dry_run=True:  validate only, return preview, write nothing.
  - dry_run=False: insert valid rows, skip invalid/duplicate, return report.

Field alias support (v2):
  The importer accepts multiple column/key names for the same
  canonical field.  See FIELD_ALIASES below.  This keeps backward
  compatibility with earlier imports while aligning with the UI.
"""

import csv
import io
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models.external_service import ExternalService, ServiceType, ServiceStatus
from services.config_validation import validate_service_config

logger = logging.getLogger("rhinometric.bulk_import")

VALID_CATALOG_TYPES = {
    "REST_API", "SOAP_API", "WEB_APP", "MOBILE_API",
    "DATABASE", "INTERNAL_SERVICE", "EXTERNAL_SERVICE", "OTHER",
}

VALID_SERVICE_TYPES = {"http", "postgresql"}

# Default values matching the existing create flow
DEFAULT_TIMEOUT = 10
DEFAULT_INTERVAL = 60

# ── Field alias mapping ─────────────────────────────────────────
# All keys are lowercase (applied AFTER lowercasing raw keys).
# Maps alternative column/key names -> canonical internal name.
FIELD_ALIASES: Dict[str, str] = {
    # service_type
    "type":                     "service_type",
    "servicetype":              "service_type",
    "service_type":             "service_type",
    # url
    "target":                   "url",
    "endpoint":                 "url",
    "url":                      "url",
    # catalog_type
    "catalogtype":              "catalog_type",
    "catalog_type":             "catalog_type",
    # check_interval_seconds
    "checkinterval":            "check_interval_seconds",
    "check_interval":           "check_interval_seconds",
    "checkintervalseconds":     "check_interval_seconds",
    "check_interval_seconds":   "check_interval_seconds",
    # timeout_seconds
    "timeout":                  "timeout_seconds",
    "timeout_seconds":          "timeout_seconds",
    # auth
    "authtype":                 "auth_type",
    "auth_type":                "auth_type",
    "authvalue":                "auth_value",
    "auth_value":               "auth_value",
    # group_name
    "group_name":              "group_name",
    "group":                   "group_name",
    "groupname":               "group_name",
}


# ── Helpers ─────────────────────────────────────────────────────

def _parse_bool(val: Any) -> bool:
    """Parse a boolean from various string representations."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    s = str(val).strip().lower()
    if s in ("true", "1", "yes", "on", ""):
        return True
    if s in ("false", "0", "no", "off"):
        return False
    return True  # default to enabled


def _parse_int(val: Any, default: int) -> int:
    """Parse an integer with fallback default."""
    if val is None or str(val).strip() == "":
        return default
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default


def _parse_tags(val: Any) -> List[str]:
    """Parse tags from string (| ; , separated) or list."""
    if val is None:
        return []
    if isinstance(val, list):
        return list(dict.fromkeys(t.strip().lower() for t in val if str(t).strip()))
    s = str(val).strip()
    if not s:
        return []
    # Support |  ;  and , as separators (priority order)
    if "|" in s:
        parts = s.split("|")
    elif ";" in s:
        parts = s.split(";")
    else:
        parts = s.split(",")
    return list(dict.fromkeys(t.strip().lower() for t in parts if t.strip()))


def _normalize_auth(val: Any) -> Optional[str]:
    """Normalize auth_type: 'none'/'None'/'null'/'' -> None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "n/a", "na", "-"):
        return None
    return s


def _apply_aliases(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply field alias mapping to a normalized (lowercase-keyed) row.
    If both an alias and the canonical name exist, canonical wins.
    """
    result: Dict[str, Any] = {}
    for key, value in row.items():
        canonical = FIELD_ALIASES.get(key, key)  # unmapped keys pass through
        if canonical in result:
            continue  # don't overwrite if canonical already set
        result[canonical] = value
    return result


def _build_config(row: Dict[str, Any], service_type: str) -> Dict[str, Any]:
    """Build the config dict from flat row fields."""
    config: Dict[str, Any] = {}
    if service_type == "http":
        if row.get("url"):
            config["url"] = str(row["url"]).strip()
        if row.get("config.url"):
            config["url"] = str(row["config.url"]).strip()
        method = str(row.get("method") or row.get("config.method") or "GET").strip().upper()
        config["method"] = method
        hp = row.get("health_path") or row.get("config.health_path")
        if hp and str(hp).strip():
            config["health_path"] = str(hp).strip()
        # Auth — normalize "None"/"none"/"null" to actual None
        at = _normalize_auth(row.get("auth_type") or row.get("config.auth_type"))
        if at:
            config["auth_type"] = at
        av = row.get("auth_value") or row.get("config.auth_value")
        if av and str(av).strip() and str(av).strip().lower() not in ("none", "null", ""):
            config["auth_value"] = str(av).strip()
    elif service_type == "postgresql":
        if row.get("host") or row.get("config.host"):
            config["host"] = str(row.get("host") or row.get("config.host")).strip()
        port = row.get("port") or row.get("config.port")
        if port:
            config["port"] = _parse_int(port, 5432)
        db_name = (row.get("database") or row.get("config.database")
                   or row.get("database_name") or row.get("config.database_name"))
        if db_name:
            config["database_name"] = str(db_name).strip()
        user = row.get("username") or row.get("config.username")
        if user:
            config["username"] = str(user).strip()
        pwd = row.get("password") or row.get("config.password")
        if pwd:
            config["password"] = str(pwd).strip()
        ssl = row.get("ssl_mode") or row.get("config.ssl_mode")
        if ssl and str(ssl).strip():
            config["ssl_mode"] = str(ssl).strip()
    # If the row already has a nested "config" dict (JSON import), merge it
    if isinstance(row.get("config"), dict):
        for k, v in row["config"].items():
            if v is not None and str(v).strip() != "":
                # Normalize auth_type inside config too
                if k == "auth_type":
                    v = _normalize_auth(v)
                    if v is None:
                        continue
                if k == "auth_value":
                    if str(v).strip().lower() in ("none", "null", ""):
                        continue
                config[k] = v
    return config


def _get_primary_target(service_type: str, config: Dict[str, Any]) -> str:
    """Get the primary target identifier for duplicate detection."""
    if service_type == "http":
        return (config.get("url") or "").strip().lower()
    elif service_type == "postgresql":
        h = (config.get("host") or "").strip().lower()
        p = str(config.get("port", 5432))
        d = (config.get("database_name") or "").strip().lower()
        return f"{h}:{p}/{d}"
    return ""


def _normalize_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a row dict: strip keys, lowercase, apply aliases."""
    lowered = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
    return _apply_aliases(lowered)


def _validate_row(row: Dict[str, Any], row_num: int) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Validate a single import row.
    Returns (parsed_service_dict, errors).
    If errors is non-empty, parsed_service_dict is None.
    """
    errors: List[str] = []
    normalized = _normalize_row(row)

    # Required: name
    name = str(normalized.get("name") or "").strip()
    if not name:
        errors.append("name is required")

    # Required: service_type (with alias support)
    stype_raw = str(normalized.get("service_type") or "").strip().lower()
    if not stype_raw:
        errors.append(
            "service_type is required (http or postgresql). "
            "Accepted aliases: type, serviceType"
        )
    elif stype_raw not in VALID_SERVICE_TYPES:
        errors.append(f"service_type must be 'http' or 'postgresql', got: '{stype_raw}'")

    if errors:
        return None, errors

    service_type = stype_raw

    # Optional fields
    environment = str(normalized.get("environment") or "").strip() or None
    description = str(normalized.get("description") or "").strip() or None
    enabled = _parse_bool(normalized.get("enabled", True))
    timeout = _parse_int(normalized.get("timeout_seconds"), DEFAULT_TIMEOUT)
    interval = _parse_int(normalized.get("check_interval_seconds"), DEFAULT_INTERVAL)

    # Clamp values to valid ranges
    timeout = max(1, min(120, timeout))
    interval = max(10, min(86400, interval))

    # Catalog metadata
    catalog_type = str(normalized.get("catalog_type") or "").strip().upper() or None
    if catalog_type and catalog_type not in VALID_CATALOG_TYPES:
        errors.append(f"catalog_type must be one of {sorted(VALID_CATALOG_TYPES)}, got: '{catalog_type}'")
    category = str(normalized.get("category") or "").strip() or None
    tags = _parse_tags(normalized.get("tags"))

    # Build config
    config = _build_config(normalized, service_type)

    # Validate config using existing validation logic
    _, config_errors = validate_service_config(service_type, config, service_name=name)
    if config_errors:
        # Enrich url-missing error when service_type is http
        enriched = []
        for ce in config_errors:
            if "url" in ce.lower() and "required" in ce.lower():
                enriched.append(
                    f"{ce} — Accepted column names: url, target, endpoint"
                )
            else:
                enriched.append(ce)
        errors.extend(enriched)

    if errors:
        return None, errors

    return {
        "name": name,
        "service_type": service_type,
        "environment": environment,
        "description": description,
        "enabled": enabled,
        "config": config,
        "timeout_seconds": timeout,
        "check_interval_seconds": interval,
        "catalog_type": catalog_type,
        "category": category,
        "tags": tags if tags else None,
    }, []


def _sniff_delimiter(sample: str) -> str:
    """Detect CSV delimiter from a sample of content."""
    # Try csv.Sniffer first
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        return dialect.delimiter
    except csv.Error:
        pass
    # Fallback: count occurrences in first line
    first_line = sample.split("\n")[0] if "\n" in sample else sample
    counts = {
        ",": first_line.count(","),
        ";": first_line.count(";"),
        "\t": first_line.count("\t"),
    }
    # Pick the delimiter with most occurrences (min 1)
    best = max(counts, key=counts.get)
    if counts[best] >= 1:
        return best
    return ","  # ultimate fallback


# Canonical required columns and their known aliases, for early
# header-level validation.  Lowercase.
_REQUIRED_HEADER_MAP = {
    "service_type": {"service_type", "type", "servicetype"},
}

# Optional but useful to detect: url (required for HTTP but not PG)
_USEFUL_HEADER_MAP = {
    "url": {"url", "target", "endpoint"},
}


def _validate_csv_headers(
    fieldnames: List[str],
) -> Optional[str]:
    """
    Check that required columns (or their aliases) exist in headers.
    Returns an error string or None if OK.
    """
    if not fieldnames:
        return "CSV file has no header row"

    headers_lower = {h.strip().lower() for h in fieldnames if h}

    # Must have 'name'
    if "name" not in headers_lower:
        return (
            "CSV missing required column: name. "
            "First row must be a header with column names."
        )

    # Must have service_type or alias
    for canonical, aliases in _REQUIRED_HEADER_MAP.items():
        if not headers_lower & aliases:
            alias_list = ", ".join(sorted(aliases - {canonical}))
            return (
                f"CSV missing required column: {canonical} "
                f"(accepted aliases: {alias_list}). "
                "Check that your CSV uses comma, semicolon, or tab as delimiter "
                "and that the first row contains column headers."
            )

    return None


def parse_csv(content: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Parse CSV content into list of row dicts.

    Supports comma, semicolon, and tab delimiters (auto-detected).
    Handles UTF-8 BOM, Windows/Mac line endings, and header spacing.
    """
    try:
        # Handle BOM
        if content.startswith("\ufeff"):
            content = content[1:]

        # Normalize line endings to \n
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Strip leading/trailing whitespace (empty lines)
        content = content.strip()
        if not content:
            return [], "CSV file is empty"

        # Sniff delimiter from first ~3 lines
        sample_lines = "\n".join(content.split("\n")[:3])
        delimiter = _sniff_delimiter(sample_lines)

        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

        # Strip whitespace from header names
        if reader.fieldnames:
            reader.fieldnames = [
                (f.strip() if f else f) for f in reader.fieldnames
            ]

        # Early structural header validation
        header_err = _validate_csv_headers(reader.fieldnames or [])
        if header_err:
            detected = {"," : "comma", ";": "semicolon", "\t": "tab"}.get(delimiter, delimiter)
            return [], f"{header_err} (detected delimiter: {detected})"

        rows = list(reader)
        if not rows:
            return [], "CSV file has headers but no data rows"

        # Strip whitespace from all cell values
        cleaned_rows = []
        for row in rows:
            cleaned = {}
            for k, v in row.items():
                if k is None:
                    continue  # extra columns beyond header
                key = k.strip() if k else k
                val = v.strip() if isinstance(v, str) else v
                cleaned[key] = val
            cleaned_rows.append(cleaned)

        return cleaned_rows, None
    except Exception as e:
        return [], f"Failed to parse CSV: {str(e)}"


def parse_json(content: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Parse JSON content into list of row dicts."""
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "services" in data:
            data = data["services"]
        if not isinstance(data, list):
            return [], "JSON must be an array of service objects, or an object with a 'services' array"
        if not data:
            return [], "JSON array is empty"
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                return [], f"Item at index {i} is not an object"
        return data, None
    except json.JSONDecodeError as e:
        return [], f"Invalid JSON: {str(e)}"


def _get_existing_services(db: Session) -> Dict[str, int]:
    """Get map of 'lowercase_name|target' -> service_id for duplicate detection."""
    existing = {}
    services = db.query(ExternalService).all()
    for svc in services:
        target = _get_primary_target(svc.service_type.value, svc.config or {})
        key = f"{svc.name.lower().strip()}|{target}"
        existing[key] = svc.id
    return existing


def process_import(
    rows: List[Dict[str, Any]],
    db: Session,
    current_user_id: int,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Process a list of service rows for import.

    Args:
        rows: List of raw row dicts from CSV or JSON parsing.
        db: SQLAlchemy session.
        current_user_id: ID of the importing user.
        dry_run: If True, validate only; if False, insert valid services.

    Returns:
        Import result dict with counts, errors, and created services.
    """
    result = {
        "total_received": len(rows),
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

    existing_map = _get_existing_services(db)
    seen_in_batch = set()  # Track duplicates within the same import batch
    valid_services = []

    for i, raw_row in enumerate(rows):
        row_num = i + 1  # 1-based for user display

        # Validate
        parsed, errors = _validate_row(raw_row, row_num)
        if errors:
            result["invalid_count"] += 1
            result["errors"].append({
                "row": row_num,
                "name": str(raw_row.get("name") or "").strip() or f"(row {row_num})",
                "errors": errors,
            })
            continue

        # Check for duplicates against existing DB services
        target = _get_primary_target(parsed["service_type"], parsed["config"])
        dup_key = f"{parsed['name'].lower().strip()}|{target}"

        if dup_key in existing_map:
            result["duplicate_count"] += 1
            result["skipped_count"] += 1
            result["errors"].append({
                "row": row_num,
                "name": parsed["name"],
                "errors": [f"Duplicate: service with same name and target already exists (id={existing_map[dup_key]})"],
                "status": "skipped",
            })
            continue

        # Check for duplicates within the same batch
        if dup_key in seen_in_batch:
            result["duplicate_count"] += 1
            result["skipped_count"] += 1
            result["errors"].append({
                "row": row_num,
                "name": parsed["name"],
                "errors": ["Duplicate: same name and target appears earlier in this import batch"],
                "status": "skipped",
            })
            continue

        seen_in_batch.add(dup_key)
        result["valid_count"] += 1
        valid_services.append(parsed)

        # Add to preview
        result["valid_preview"].append({
            "row": row_num,
            "name": parsed["name"],
            "service_type": parsed["service_type"],
            "environment": parsed.get("environment"),
            "catalog_type": parsed.get("catalog_type"),
            "category": parsed.get("category"),
            "tags": parsed.get("tags") or [],
            "target": target,
        })

    # If dry_run, stop here - don't write anything
    if dry_run:
        return result

    # Insert valid services
    for svc_data in valid_services:
        try:
            svc = ExternalService(
                name=svc_data["name"],
                service_type=ServiceType(svc_data["service_type"]),
                environment=svc_data.get("environment"),
                description=svc_data.get("description"),
                enabled=svc_data.get("enabled", True),
                config=svc_data["config"],
                timeout_seconds=svc_data.get("timeout_seconds", DEFAULT_TIMEOUT),
                check_interval_seconds=svc_data.get("check_interval_seconds", DEFAULT_INTERVAL),
                catalog_type=svc_data.get("catalog_type"),
                category=svc_data.get("category"),
                tags=svc_data.get("tags"),
                status=ServiceStatus.UNKNOWN,
                created_by=current_user_id,
                group_name=svc_data.get("group_name", "Default"),
            )
            db.add(svc)
            db.flush()  # Get the ID
            result["created_count"] += 1
            result["created_services"].append({
                "id": svc.id,
                "name": svc.name,
                "service_type": svc.service_type.value,
                "status": "created",
            })
            logger.info(f"[BulkImport] Created service: {svc.name} (id={svc.id})")
        except Exception as e:
            result["skipped_count"] += 1
            result["valid_count"] -= 1
            result["errors"].append({
                "row": None,
                "name": svc_data["name"],
                "errors": [f"Database error: {str(e)}"],
                "status": "error",
            })
            logger.error(f"[BulkImport] Failed to create {svc_data['name']}: {e}")

    # Remove valid_preview from confirm response (not needed after actual import)
    if not dry_run:
        result.pop("valid_preview", None)

    return result


def generate_csv_template() -> str:
    """Generate a CSV template with example rows aligned with the UI."""
    header = (
        "name,service_type,url,method,environment,description,"
        "timeout_seconds,check_interval_seconds,enabled,"
        "catalog_type,category,tags,auth_type,auth_value,"
        "host,port,database_name,username,password"
    )
    examples = [
        'Payment Gateway API,http,https://api.payments.example.com/health,GET,production,'
        'Payment processing API,15,60,true,REST_API,payments,"critical,external,payments",bearer,token-xxxx,,,,,',
        'User Service,http,https://users.internal.example.com/status,GET,production,'
        'Internal user service,10,60,true,INTERNAL_SERVICE,backend,"internal,users",,,,,,',
        'Analytics DB,postgresql,,,,Main analytics database,10,120,true,'
        'DATABASE,infrastructure,"internal,postgresql",,,db.internal.example.com,5432,'
        'analytics_db,analytics_user,secure_password',
    ]
    return header + "\n" + "\n".join(examples) + "\n"


def generate_json_template() -> str:
    """Generate a JSON template with example entries and alias docs."""
    template = {
        "_documentation": {
            "required_fields": ["name", "service_type (or type)"],
            "http_required": "config.url (or top-level url / target / endpoint)",
            "postgresql_required": "config.host, config.port, config.database_name, config.username",
            "accepted_aliases": {
                "type / serviceType": "service_type",
                "target / endpoint": "url (top-level or inside config)",
                "catalogType": "catalog_type",
                "timeout": "timeout_seconds",
                "checkInterval / check_interval": "check_interval_seconds",
                "authType": "auth_type",
                "authValue": "auth_value",
            },
            "auth_note": "Omit auth_type and auth_value if not needed. Do NOT send auth_type: 'None'.",
            "tags_note": "JSON array of strings, e.g. [\"critical\", \"api\"]. In CSV use comma, semicolon, or pipe.",
            "catalog_types": sorted(list(VALID_CATALOG_TYPES)),
        },
        "services": [
            {
                "name": "Payment Gateway API",
                "service_type": "http",
                "environment": "production",
                "description": "Payment processing API",
                "timeout_seconds": 15,
                "check_interval_seconds": 60,
                "enabled": True,
                "catalog_type": "REST_API",
                "category": "payments",
                "tags": ["critical", "external", "payments"],
                "config": {
                    "url": "https://api.payments.example.com/health",
                    "method": "GET",
                    "health_path": "/health",
                    "auth_type": "bearer",
                    "auth_value": "your-token-here",
                },
            },
            {
                "name": "User Service",
                "service_type": "http",
                "environment": "production",
                "description": "Internal user management",
                "timeout_seconds": 10,
                "check_interval_seconds": 60,
                "enabled": True,
                "catalog_type": "INTERNAL_SERVICE",
                "category": "backend",
                "tags": ["internal", "users"],
                "config": {
                    "url": "https://users.internal.example.com/status",
                    "method": "GET",
                },
            },
            {
                "name": "Analytics DB",
                "service_type": "postgresql",
                "environment": "production",
                "description": "Main analytics database",
                "timeout_seconds": 10,
                "check_interval_seconds": 120,
                "enabled": True,
                "catalog_type": "DATABASE",
                "category": "infrastructure",
                "tags": ["internal", "postgresql"],
                "config": {
                    "host": "db.internal.example.com",
                    "port": 5432,
                    "database_name": "analytics_db",
                    "username": "analytics_user",
                    "password": "secure_password",
                },
            },
        ],
    }
    return json.dumps(template, indent=2)
