"""
LICENSE ROUTER - RHINOMETRIC CONSOLE BACKEND v2.6.0

Connects to Rust license validator (rhino-lic) for cryptographic
Ed25519 license validation. Falls back to License Server v2 if
the Rust binary is unavailable.

Provides:
- Real license status from signed license file
- Host count from Prometheus (node_exporter + cadvisor)
- Expiration enforcement
- Host limit enforcement
- License limits per role (from DB)

Supported plans (Rust license):
- trial: 14 days, 5 hosts
- annual_standard: 1 year, 20 hosts
- enterprise: unlimited hosts, custom expiry
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import httpx
import logging
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel
from utils.rust_license_validator import (
    validate_license as rust_validate,
    is_binary_available as rust_binary_available,
    RustLicenseResult,
)

router = APIRouter()
logger = logging.getLogger("rhinometric.license")

# ═══════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════

class LicenseStatusResponse(BaseModel):
    """License status for Rhinometric Console UI"""
    # License identification
    license_key: str
    tier: str  # trial, annual_standard, enterprise

    # Limits
    max_hosts: int
    hosts_used: int
    hosts_available: int

    # Dates
    issued_at: str
    activated_at: Optional[str] = None
    expires_at: Optional[str] = None

    # Status
    status: str  # active, expired, invalid_signature, over_limit, error
    is_valid: bool
    days_remaining: Optional[int] = None
    hours_remaining: Optional[int] = None

    # Organization
    organization: Optional[str] = None
    organization_email: Optional[str] = None

    # Messages
    message: str
    warning: Optional[str] = None

    # Deployment mode
    deployment_mode: str = "ON_PREMISE"  # ON_PREMISE or SAAS_SINGLE_TENANT

    # Rust validator extras
    tenant_id: Optional[str] = None
    features: Optional[list] = None
    validator: str = "rust"  # "rust" or "legacy"

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

async def get_monitored_hosts_count() -> int:
    """
    Get number of monitored hosts from Prometheus.

    Counts unique instances from:
    - node_exporter (system metrics)
    - cadvisor (container metrics)

    Returns actual host count based on real data.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query 1: Count unique node_exporter instances
            node_query = 'count(count by (instance) (up{job="node-exporter"}))'
            node_response = await client.get(
                f"{settings.PROMETHEUS_URL}/api/v1/query",
                params={"query": node_query}
            )

            node_count = 0
            if node_response.status_code == 200:
                data = node_response.json()
                if data.get("status") == "success":
                    result = data.get("data", {}).get("result", [])
                    if result:
                        node_count = int(float(result[0]["value"][1]))

            # Query 2: Count unique cadvisor instances
            cadvisor_query = 'count(count by (instance) (up{job="cadvisor"}))'
            cadvisor_response = await client.get(
                f"{settings.PROMETHEUS_URL}/api/v1/query",
                params={"query": cadvisor_query}
            )

            cadvisor_count = 0
            if cadvisor_response.status_code == 200:
                data = cadvisor_response.json()
                if data.get("status") == "success":
                    result = data.get("data", {}).get("result", [])
                    if result:
                        cadvisor_count = int(float(result[0]["value"][1]))

            hosts = max(node_count, cadvisor_count)
            logger.info(f"Monitored hosts: {hosts} (node_exporter: {node_count}, cadvisor: {cadvisor_count})")
            return hosts

    except Exception as e:
        logger.error(f"Error getting host count from Prometheus: {str(e)}")
        return 0


def _calculate_time_remaining(expires_at_str: Optional[str]):
    """Calculate days and hours remaining from expiry string."""
    if not expires_at_str:
        return None, None

    try:
        # Parse ISO 8601 datetime
        if expires_at_str.endswith("Z"):
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        else:
            expires_at = datetime.fromisoformat(expires_at_str)

        now = datetime.now(timezone.utc)
        delta = expires_at - now

        if delta.total_seconds() <= 0:
            return 0, 0

        days = delta.days
        hours = int(delta.total_seconds() // 3600)
        return days, hours
    except Exception as e:
        logger.warning(f"Could not parse expires_at '{expires_at_str}': {e}")
        return None, None


def _build_response_from_rust(
    lic: RustLicenseResult,
    hosts_used: int,
) -> LicenseStatusResponse:
    """Build a LicenseStatusResponse from a RustLicenseResult."""

    days_remaining, hours_remaining = _calculate_time_remaining(lic.expires_at)
    max_hosts = lic.max_hosts or 0
    hosts_available = max(0, max_hosts - hosts_used)

    # Determine effective status
    if not lic.is_valid:
        status = lic.status  # expired, invalid_signature, etc.
        is_valid = False
        message = lic.error_message or f"License is {lic.status}"
    elif hosts_used > max_hosts and max_hosts > 0:
        status = "over_limit"
        is_valid = False
        message = f"Host limit exceeded: {hosts_used}/{max_hosts}"
    else:
        status = "active"
        is_valid = True
        message = "License is active and valid"

    # Build warnings
    warning = None
    if is_valid:
        if hosts_used > max_hosts and max_hosts > 0:
            warning = f"You are using {hosts_used} hosts but your license allows only {max_hosts}. Please upgrade."
        elif hosts_used == max_hosts and max_hosts > 0:
            warning = f"You have reached your host limit ({max_hosts}/{max_hosts}). Consider upgrading."
        elif hosts_available <= 2 and hosts_available > 0:
            warning = f"Only {hosts_available} host slots remaining. Consider upgrading soon."

        if days_remaining is not None and 0 < days_remaining <= 7:
            exp_warning = f"License expires in {days_remaining} days. Please renew soon."
            warning = exp_warning if not warning else f"{warning} {exp_warning}"

    # Mask the license key (show tenant_id instead of raw key)
    display_key = lic.tenant_id or "rhinometric"

    return LicenseStatusResponse(
        license_key=display_key,
        tier=lic.plan or "unknown",
        max_hosts=max_hosts,
        hosts_used=hosts_used,
        hosts_available=hosts_available,
        issued_at=lic.issued_at or datetime.now(timezone.utc).isoformat(),
        activated_at=lic.issued_at,
        expires_at=lic.expires_at,
        status=status,
        is_valid=is_valid,
        days_remaining=days_remaining,
        hours_remaining=hours_remaining,
        organization=lic.customer,
        organization_email=None,
        message=message,
        warning=warning,
        deployment_mode=lic.deployment_mode,
        tenant_id=lic.tenant_id,
        features=lic.features,
        validator="rust",
    )


class LicenseActivationRequest(BaseModel):
    """Request to activate a license"""
    license_key: str

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/status", response_model=LicenseStatusResponse)
async def get_license_status(current_user: UserModel = Depends(get_current_user)):
    """
    Get comprehensive license status.

    Primary path: Rust validator (rhino-lic) for Ed25519 signed license.
    Fallback: License Server v2 (legacy, port 5000).

    This is the PRIMARY endpoint consumed by the Rhinometric Console UI.
    """

    # Step 1: Get monitored hosts count from Prometheus
    hosts_used = await get_monitored_hosts_count()

    # Step 2: Try Rust validator first (preferred)
    if rust_binary_available():
        logger.info("Using Rust license validator (rhino-lic)")
        lic = rust_validate()

        if lic.status not in ("binary_not_found", "license_file_missing"):
            # Rust validator ran — use its result (even if license is invalid/expired)
            return _build_response_from_rust(lic, hosts_used)
        else:
            logger.warning(f"Rust validator issue: {lic.status}, falling back to legacy")

    # Step 3: Fallback to License Server v2 (legacy)
    logger.warning("Rust validator unavailable, falling back to License Server v2")
    return await _legacy_license_status(hosts_used)


async def _legacy_license_status(hosts_used: int) -> LicenseStatusResponse:
    """Fallback: query License Server v2 (port 5000) for license status."""
    try:
        license_file = "/app/license.key"
        try:
            with open(license_file, "r") as f:
                license_key = f.read().strip()
        except FileNotFoundError:
            license_key = "RHINO-TRIAL-2025-TJV33E4BYRNC"
            logger.warning(f"No license file found at {license_file}, using default trial key")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.LICENSE_VALIDATOR_URL}/api/licenses/validate",
                json={
                    "license_key": license_key,
                    "hostname": "rhinometric-console",
                    "ip_address": "internal"
                }
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail="License Server unavailable or license invalid"
                )

            license_data = response.json()

            if not license_data.get("valid", False):
                raise HTTPException(
                    status_code=403,
                    detail=license_data.get("message", "License validation failed")
                )

            tier = license_data.get("tier", "trial")
            max_hosts = license_data.get("max_hosts", 5)
            expires_at = license_data.get("expires_at")
            activated_at = license_data.get("activated_at")
            issued_at = license_data.get("issued_at")
            days_remaining = license_data.get("days_remaining")
            hours_remaining = license_data.get("hours_remaining")
            status_from_server = license_data.get("status", "active")

            hosts_available = max(0, max_hosts - hosts_used)
            is_valid = True
            warning = None

            if status_from_server == "expired":
                is_valid = False

            if hosts_used > max_hosts:
                status_from_server = "over_limit"
                is_valid = False
                warning = f"You are using {hosts_used} hosts but your license allows only {max_hosts}. Please upgrade."
            elif hosts_used == max_hosts:
                warning = f"You have reached your host limit ({max_hosts}/{max_hosts}). Consider upgrading."
            elif hosts_available <= 2 and hosts_available > 0:
                warning = f"Only {hosts_available} host slots remaining. Consider upgrading soon."

            if days_remaining is not None and 0 < days_remaining <= 7:
                exp_warning = f"License expires in {days_remaining} days. Please renew soon."
                warning = exp_warning if not warning else f"{warning} {exp_warning}"

            if tier == "demo_cloud" and hours_remaining is not None:
                if hours_remaining <= 1:
                    warning = f"Demo session expires in {hours_remaining} hour(s)!"

            message = license_data.get("message", "License is active")

            return LicenseStatusResponse(
                license_key=license_key,
                tier=tier,
                max_hosts=max_hosts,
                hosts_used=hosts_used,
                hosts_available=hosts_available,
                issued_at=issued_at or datetime.now(timezone.utc).isoformat(),
                activated_at=activated_at,
                expires_at=expires_at,
                status=status_from_server,
                is_valid=is_valid,
                days_remaining=days_remaining,
                hours_remaining=hours_remaining,
                organization=license_data.get("customer_name"),
                organization_email=None,
                message=message,
                warning=warning,
                deployment_mode=license_data.get("deployment_mode", "ON_PREMISE"),
                validator="legacy",
            )

    except httpx.ConnectError:
        logger.error("License Server (port 5000) is not available")
        raise HTTPException(
            status_code=503,
            detail="License Server is not available. Please ensure License Server v2 is running on port 5000."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching license status (legacy): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch license status: {str(e)}"
        )


@router.post("/activate")
async def activate_license(
    request: LicenseActivationRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Activate a license key in this Rhinometric instance.

    With Rust validator: license activation is done at VM level
    via start-rhinometric.sh. This endpoint is kept for legacy
    License Server v2 compatibility.
    """
    import os

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.LICENSE_VALIDATOR_URL}/api/licenses/validate",
                json={
                    "license_key": request.license_key,
                    "hostname": "rhinometric-console",
                    "ip_address": "internal"
                }
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid license key or License Server unavailable"
                )

            license_data = response.json()

            if not license_data.get("valid", False):
                raise HTTPException(
                    status_code=400,
                    detail=license_data.get("message", "License is not valid")
                )

        license_file = "/app/license.key"
        with open(license_file, "w") as f:
            f.write(request.license_key)

        logger.info(f"License activated: {request.license_key} (tier: {license_data.get('tier')})")

        return {
            "success": True,
            "message": "License activated successfully",
            "license_key": request.license_key,
            "tier": license_data.get("tier"),
            "max_hosts": license_data.get("max_hosts"),
            "expires_at": license_data.get("expires_at"),
            "days_remaining": license_data.get("days_remaining")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating license: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to activate license: {str(e)}"
        )


@router.get("/limits")
async def get_license_limits(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get license limits summary showing role limits and current usage.

    Returns current usage vs. limits for each role (OWNER, ADMIN, OPERATOR, VIEWER).
    """
    from database import get_db
    from services.license_validator import get_license_limits_summary
    from sqlalchemy.orm import Session

    db: Session = next(get_db())
    try:
        summary = get_license_limits_summary(db)
        return {
            "success": True,
            "limits": summary
        }
    finally:
        db.close()
