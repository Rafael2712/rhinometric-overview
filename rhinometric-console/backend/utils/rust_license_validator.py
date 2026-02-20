"""
Rust License Validator Wrapper
Calls /usr/local/bin/rhino-lic validate via subprocess.
Used by routers/license.py to get real license info from the signed Ed25519 license.

Exit codes from rhino-lic:
  0 = valid
  1 = invalid signature
  2 = expired / date out of range
  3 = fingerprint mismatch
  4 = parse error
"""

import subprocess
import json
import os
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("rhinometric.rust_license")

RHINO_LIC_BINARY = os.getenv("RHINO_LIC_BINARY", "/usr/local/bin/rhino-lic")
LICENSE_FILE = os.getenv("RHINO_LICENSE_FILE", "/opt/rhinometric/license.key")

EXIT_CODE_MAP = {
    0: "valid",
    1: "invalid_signature",
    2: "expired",
    3: "fingerprint_mismatch",
    4: "parse_error",
}

# Allowed deployment modes
VALID_DEPLOYMENT_MODES = {"ON_PREMISE", "SAAS_SINGLE_TENANT"}
DEFAULT_DEPLOYMENT_MODE = "ON_PREMISE"


@dataclass
class RustLicenseResult:
    """Result from rhino-lic validate"""
    is_valid: bool
    status: str           # valid, expired, invalid_signature, fingerprint_mismatch, parse_error
    plan: Optional[str] = None
    max_hosts: Optional[int] = None
    expires_at: Optional[str] = None
    customer: Optional[str] = None
    tenant_id: Optional[str] = None
    issued_at: Optional[str] = None
    features: Optional[list] = field(default_factory=list)
    fingerprint: Optional[str] = None
    deployment_mode: str = "ON_PREMISE"  # ON_PREMISE or SAAS_SINGLE_TENANT
    error_message: Optional[str] = None
    exit_code: int = -1


def is_binary_available() -> bool:
    """Check if rhino-lic binary is present and executable."""
    return os.path.isfile(RHINO_LIC_BINARY) and os.access(RHINO_LIC_BINARY, os.X_OK)


def validate_license(license_path: Optional[str] = None, skip_fingerprint: bool = True) -> RustLicenseResult:
    """
    Run rhino-lic validate and return structured result.

    Args:
        license_path: Path to the license.key file (default: /opt/rhinometric/license.key)
        skip_fingerprint: Skip fingerprint check (True inside Docker containers)

    Returns:
        RustLicenseResult with validation outcome
    """
    path = license_path or LICENSE_FILE

    if not is_binary_available():
        logger.error(f"rhino-lic binary not found at {RHINO_LIC_BINARY}")
        return RustLicenseResult(
            is_valid=False,
            status="binary_not_found",
            error_message=f"License validator binary not found at {RHINO_LIC_BINARY}",
            exit_code=-1,
        )

    if not os.path.isfile(path):
        logger.error(f"License file not found at {path}")
        return RustLicenseResult(
            is_valid=False,
            status="license_file_missing",
            error_message=f"License file not found at {path}",
            exit_code=-1,
        )

    cmd = [RHINO_LIC_BINARY, "validate", path]
    if skip_fingerprint:
        cmd.append("--skip-fingerprint")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        exit_code = result.returncode
        status = EXIT_CODE_MAP.get(exit_code, f"unknown_{exit_code}")
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        logger.info(f"rhino-lic validate exit={exit_code} status={status}")

        if exit_code == 0 and stdout:
            try:
                data = json.loads(stdout)
                # Also read the license file directly for extra payload fields
                payload = _read_license_payload(path)
                # Read deployment_mode from payload, default to ON_PREMISE for backward compat
                raw_mode = payload.get("deployment_mode", DEFAULT_DEPLOYMENT_MODE)
                deployment_mode = raw_mode if raw_mode in VALID_DEPLOYMENT_MODES else DEFAULT_DEPLOYMENT_MODE

                return RustLicenseResult(
                    is_valid=True,
                    status="valid",
                    plan=data.get("plan"),
                    max_hosts=data.get("max_hosts"),
                    expires_at=data.get("expires_at"),
                    customer=payload.get("customer"),
                    tenant_id=payload.get("tenant_id"),
                    issued_at=payload.get("issued_at"),
                    features=payload.get("features", []),
                    fingerprint=payload.get("fingerprint"),
                    deployment_mode=deployment_mode,
                    exit_code=0,
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse rhino-lic JSON output: {e}")
                return RustLicenseResult(
                    is_valid=False,
                    status="parse_error",
                    error_message=f"Invalid JSON from validator: {stdout}",
                    exit_code=exit_code,
                )
        else:
            raw_msg = stderr or stdout or ""
            # Try to extract "reason" from JSON error output
            error_msg = f"Validation failed with exit code {exit_code}"
            try:
                err_data = json.loads(raw_msg)
                error_msg = err_data.get("reason", error_msg)
            except (json.JSONDecodeError, TypeError):
                if raw_msg:
                    error_msg = raw_msg
            return RustLicenseResult(
                is_valid=False,
                status=status,
                error_message=error_msg,
                exit_code=exit_code,
            )

    except subprocess.TimeoutExpired:
        logger.error("rhino-lic validate timed out after 10s")
        return RustLicenseResult(
            is_valid=False,
            status="timeout",
            error_message="License validation timed out",
            exit_code=-1,
        )
    except Exception as e:
        logger.error(f"Error running rhino-lic: {e}")
        return RustLicenseResult(
            is_valid=False,
            status="error",
            error_message=str(e),
            exit_code=-1,
        )


def _read_license_payload(license_path: str) -> dict:
    """Read the license JSON file and extract payload fields."""
    try:
        with open(license_path, "r") as f:
            data = json.load(f)
        payload = data.get("payload", {})
        # payload might be a JSON string or dict
        if isinstance(payload, str):
            payload = json.loads(payload)
        return payload
    except Exception as e:
        logger.warning(f"Could not read license payload: {e}")
        return {}


def get_license_info(license_path: Optional[str] = None) -> dict:
    """
    Convenience function: validate + return dict suitable for API response.
    """
    result = validate_license(license_path)
    return {
        "is_valid": result.is_valid,
        "status": result.status,
        "plan": result.plan,
        "max_hosts": result.max_hosts,
        "expires_at": result.expires_at,
        "customer": result.customer,
        "tenant_id": result.tenant_id,
        "issued_at": result.issued_at,
        "features": result.features,
        "fingerprint": result.fingerprint,
        "deployment_mode": result.deployment_mode,
        "error_message": result.error_message,
    }
