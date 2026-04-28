"""
Configuration validation service for External Services.

Orchestrates schema validation (Pydantic) + SSRF protection for HTTP URLs.
Returns structured error lists for the API layer.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from models.service_configs import HttpServiceConfig, PostgresServiceConfig
from security.ssrf_protection import validate_url

logger = logging.getLogger("rhinometric.config_validation")


def validate_service_config(
    service_type: str,
    config: Dict[str, Any],
    service_name: str = "",
) -> Tuple[Dict[str, Any], Optional[List[str]]]:
    """
    Validate a service configuration based on service_type.

    Returns:
        (validated_config_dict, errors)
        - If valid:  (clean_dict, None)
        - If invalid: ({}, [list of error strings])
    """
    errors: List[str] = []

    if service_type == "http":
        errors = _validate_http(config, service_name)
    elif service_type == "postgresql":
        errors = _validate_postgres(config)
    else:
        errors = [f"Unknown service_type: {service_type!r}. Must be 'http' or 'postgresql'."]

    if errors:
        logger.warning(
            f"[ConfigValidation] Rejected {service_type} config for "
            f"'{service_name}': {errors}"
        )
        return {}, errors

    return config, None


def _validate_http(config: Dict[str, Any], service_name: str) -> List[str]:
    """Validate HTTP service config: schema + SSRF."""
    errors: List[str] = []

    # Step 1: Schema validation
    try:
        validated = HttpServiceConfig(**config)
    except ValidationError as e:
        for err in e.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            errors.append(f"{field}: {err['msg']}")
        return errors

    # Step 2: SSRF validation on the URL
    ssrf_result = validate_url(validated.url, service_name=service_name)
    if not ssrf_result.is_safe:
        errors.append(f"url: SSRF protection blocked this URL — {ssrf_result.reason}")
        return errors

    return errors


def _validate_postgres(config: Dict[str, Any]) -> List[str]:
    """Validate PostgreSQL service config: schema only."""
    errors: List[str] = []

    try:
        validated = PostgresServiceConfig(**config)
    except ValidationError as e:
        for err in e.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            errors.append(f"{field}: {err['msg']}")

    return errors
