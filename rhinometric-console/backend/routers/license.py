"""
LICENSE ROUTER - RHINOMETRIC CONSOLE BACKEND v3.0.0

SERVICE-BASED LICENSE MODEL.

- Real license validation via Rust validator (rhino-lic) for cryptographic Ed25519.
- Service usage from DB (external_services table).
- User/role counts from DB.
- Plan definitions: starter / growth / scale.

Endpoints:
  GET  /status   ? Full license status (service-based)
  POST /activate ? Activate a new license key (legacy compat)
  GET  /limits   ? License limits summary

Environment variables:
  RHINO_LICENSE_VALIDATOR: "rust" | "legacy" | "auto" (default: "auto")
"""

import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import httpx
import logging
from config import settings
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger("rhinometric.license")

VALIDATOR_MODE = os.getenv("RHINO_LICENSE_VALIDATOR", "auto").lower().strip()
if VALIDATOR_MODE not in ("rust", "legacy", "auto"):
    logger.warning(f"Invalid RHINO_LICENSE_VALIDATOR='{VALIDATOR_MODE}', defaulting to 'auto'")
    VALIDATOR_MODE = "auto"

logger.info(f"License validator mode: {VALIDATOR_MODE}")


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _calculate_time_remaining(expires_at_str: Optional[str]):
    """Calculate days and hours remaining from expiry string."""
    if not expires_at_str:
        return None, None
    try:
        if expires_at_str.endswith("Z"):
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        else:
            expires_at = datetime.fromisoformat(expires_at_str)
        now = datetime.now(timezone.utc)
        delta = expires_at - now
        if delta.total_seconds() <= 0:
            return 0, 0
        return delta.days, int(delta.total_seconds() // 3600)
    except Exception as e:
        logger.warning(f"Could not parse expires_at '{expires_at_str}': {e}")
        return None, None


# ------------------------------------------------------------------
# MODELS
# ------------------------------------------------------------------

class LicenseActivationRequest(BaseModel):
    license_key: str


# ------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------

@router.get("/status")
async def get_license_status(
    current_user: UserModel = Depends(require_role(["OWNER"])),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive license status ? SERVICE-BASED MODEL.

    Returns plan info, service usage, user/role counts, features,
    and breach flags. All data is live from DB + Rust validator.
    """
    from services.license_validator import get_license_status_payload

    try:
        payload = get_license_status_payload(db)
        return payload
    except Exception as e:
        logger.error(f"Error building license status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build license status: {e}")


@router.post("/activate")
async def activate_license(
    request: LicenseActivationRequest,
    current_user: UserModel = Depends(require_role(["OWNER"])),
):
    """
    Activate a license key in this Rhinometric instance.

    With Rust validator: license activation is done at VM level
    via start-rhinometric.sh. This endpoint is kept for legacy
    License Server v2 compatibility.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.LICENSE_VALIDATOR_URL}/api/licenses/validate",
                json={
                    "license_key": request.license_key,
                    "hostname": "rhinometric-console",
                    "ip_address": "internal",
                },
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid license key or License Server unavailable")
            license_data = response.json()
            if not license_data.get("valid", False):
                raise HTTPException(status_code=400, detail=license_data.get("message", "License is not valid"))

        license_file = "/app/license.key"
        with open(license_file, "w") as f:
            f.write(request.license_key)

        logger.info(f"License activated: {request.license_key} (tier: {license_data.get('tier')})")
        return {
            "success": True,
            "message": "License activated successfully",
            "license_key": request.license_key,
            "tier": license_data.get("tier"),
            "expires_at": license_data.get("expires_at"),
            "days_remaining": license_data.get("days_remaining"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating license: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate license: {e}")


@router.get("/limits")
async def get_license_limits(
    current_user: UserModel = Depends(require_role(["OWNER"])),
    db: Session = Depends(get_db),
):
    """
    Get license limits summary showing service/role limits and current usage.
    """
    from services.license_validator import get_license_limits_summary

    try:
        summary = get_license_limits_summary(db)
        return {"success": True, "limits": summary}
    except Exception as e:
        logger.error(f"Error getting license limits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get license limits: {e}")
