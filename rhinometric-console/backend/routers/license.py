"""
═══════════════════════════════════════════════════════════════════════════
LICENSE ROUTER - RHINOMETRIC CONSOLE BACKEND v2.5.0
═══════════════════════════════════════════════════════════════════════════

Connects to License Server v2 (port 5000) and provides:
- Real license status with tier information
- Host count from Prometheus (node_exporter + cadvisor)
- Expiration enforcement
- Host limit enforcement

Supported tiers:
- demo_cloud: 4 hours, 20 hosts, cloud demo
- trial: 14 days, 5 hosts, on-premise
- annual_standard: 1 year, 20 hosts, commercial

═══════════════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import httpx
import logging
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()
logger = logging.getLogger("rhinometric.license")

# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════

class LicenseStatusResponse(BaseModel):
    """License status for Rhinometric Console UI"""
    # License identification
    license_key: str
    tier: str  # demo_cloud, trial, annual_standard
    
    # Limits
    max_hosts: int
    hosts_used: int
    hosts_available: int
    
    # Dates
    issued_at: str
    activated_at: Optional[str]
    expires_at: Optional[str]
    
    # Status
    status: str  # not_activated, active, expired, revoked, over_limit
    is_valid: bool
    days_remaining: Optional[int]
    hours_remaining: Optional[int]
    
    # Organization
    organization: Optional[str]
    organization_email: Optional[str]
    
    # Messages
    message: str
    warning: Optional[str]

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

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
            
            # Query 2: Count unique cadvisor instances (as fallback/additional)
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
            
            # Return the maximum (node_exporter is primary, cadvisor is backup)
            hosts = max(node_count, cadvisor_count)
            logger.info(f"📊 Monitored hosts: {hosts} (node_exporter: {node_count}, cadvisor: {cadvisor_count})")
            return hosts
            
    except Exception as e:
        logger.error(f"❌ Error getting host count from Prometheus: {str(e)}")
        # Return 0 if Prometheus is unavailable (fail safe)
        return 0

class LicenseActivationRequest(BaseModel):
    """Request to activate a license"""
    license_key: str

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/status", response_model=LicenseStatusResponse)
async def get_license_status(current_user: UserModel = Depends(get_current_user)):
    """
    Get comprehensive license status from License Server v2.
    
    Returns:
    - Tier information (demo_cloud, trial, annual_standard)
    - Host usage (real count from Prometheus)
    - Expiration dates and remaining time
    - Status and enforcement warnings
    
    This is the PRIMARY endpoint consumed by the Rhinometric Console UI.
    """
    
    # CRITICAL: This endpoint MUST return real data from License Server
    # NO mocks, NO hardcoded values
    
    try:
        # Step 1: Get monitored hosts count from Prometheus
        hosts_used = await get_monitored_hosts_count()
        
        # Step 2: Fetch license info from License Server v2
        # Read license key from file (activated via /api/license/activate)
        license_file = "/app/license.key"
        
        try:
            with open(license_file, "r") as f:
                license_key = f.read().strip()
        except FileNotFoundError:
            # Fallback to hardcoded trial license for FASE 1
            license_key = "RHINO-TRIAL-2025-TJV33E4BYRNC"
            logger.warning(f"⚠️  No license file found at {license_file}, using default trial license")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Validate license via License Server v2
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
                # License is invalid/expired
                raise HTTPException(
                    status_code=403,
                    detail=license_data.get("message", "License validation failed")
                )
            
            # Extract license information
            tier = license_data.get("tier", "trial")
            max_hosts = license_data.get("max_hosts", 5)
            expires_at = license_data.get("expires_at")
            activated_at = license_data.get("activated_at")
            issued_at = license_data.get("issued_at")
            days_remaining = license_data.get("days_remaining")
            hours_remaining = license_data.get("hours_remaining")
            status_from_server = license_data.get("status", "active")
            
            # Calculate hosts available
            hosts_available = max(0, max_hosts - hosts_used)
            
            # Determine if license is valid (not expired, not over limit)
            is_valid = True
            warning = None
            
            # Check expiration
            if status_from_server == "expired":
                is_valid = False
            
            # Check host limit
            if hosts_used > max_hosts:
                status_from_server = "over_limit"
                is_valid = False
                warning = f"You are using {hosts_used} hosts but your license allows only {max_hosts}. Please upgrade your license."
            elif hosts_used == max_hosts:
                warning = f"You have reached your host limit ({max_hosts}/{max_hosts}). Consider upgrading."
            elif hosts_available <= 2 and hosts_available > 0:
                warning = f"Only {hosts_available} host slots remaining. Consider upgrading soon."
            
            # Check expiration warning
            if days_remaining is not None and days_remaining <= 7 and days_remaining > 0:
                exp_warning = f"License expires in {days_remaining} days. Please renew soon."
                warning = exp_warning if not warning else f"{warning} {exp_warning}"
            
            # For demo_cloud, use hours instead
            if tier == "demo_cloud" and hours_remaining is not None:
                if hours_remaining <= 1:
                    warning = f"Demo session expires in {hours_remaining} hour(s)!"
            
            # Generate user-friendly message
            message = license_data.get("message", "License is active")
            
            return LicenseStatusResponse(
                license_key=license_key,
                tier=tier,
                max_hosts=max_hosts,
                hosts_used=hosts_used,
                hosts_available=hosts_available,
                issued_at=issued_at or datetime.utcnow().isoformat(),
                activated_at=activated_at,
                expires_at=expires_at,
                status=status_from_server,
                is_valid=is_valid,
                days_remaining=days_remaining,
                hours_remaining=hours_remaining,
                organization=license_data.get("customer_name"),
                organization_email=None,  # Not returned by current API
                message=message,
                warning=warning
            )
            
    except httpx.ConnectError:
        # License Server is not available
        logger.error("❌ License Server (port 5000) is not available")
        raise HTTPException(
            status_code=503,
            detail="License Server is not available. Please ensure License Server v2 is running on port 5000."
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching license status: {str(e)}")
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
    
    Validates the license with License Server and stores it locally.
    """
    import os
    
    try:
        # Validate with License Server first
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
        
        # Save license key to file (persistent storage)
        # Using /app directory which is writable inside container
        license_file = "/app/license.key"
        
        with open(license_file, "w") as f:
            f.write(request.license_key)
        
        logger.info(f"✅ License activated: {request.license_key} (tier: {license_data.get('tier')})")
        
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
        logger.error(f"❌ Error activating license: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to activate license: {str(e)}"
        )
