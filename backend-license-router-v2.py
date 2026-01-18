"""
Rhinometric Console Backend - License Router (V2 con tier support)
Conecta con License Server v2 (puerto 5000) para obtener información de licencias
con tier, max_hosts, activated_at, expiration, etc.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import httpx
import os
from routers.auth import get_current_user, User

router = APIRouter()

# Configuración
LICENSE_SERVER_URL = os.getenv("LICENSE_VALIDATOR_URL", "http://rhinometric-license-server-v2:5000")
LICENSE_KEY = os.getenv("RHINOMETRIC_LICENSE_KEY", "RHINO-TRIAL-2025-2W7NIMI9JPXQ")  # Licencia trial creada
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

class LicenseStatusResponse(BaseModel):
    """Response model for license status"""
    # License identification
    license_key: str
    tier: str  # demo_cloud, trial, annual_standard
    
    # Host limits
    max_hosts: int
    hosts_used: int
    hosts_available: int
    
    # Dates
    issued_at: datetime
    activated_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    # Status
    status: str  # not_activated, active, expired, revoked, over_limit
    is_valid: bool
    days_remaining: Optional[int]
    hours_remaining: Optional[int]  # For demo_cloud
    
    # Organization
    organization: Optional[str]
    organization_email: Optional[str]
    
    # UI messages
    message: str
    warning: Optional[str]

async def get_monitored_hosts_count() -> int:
    """
    Get the number of monitored hosts from Prometheus
    
    Uses two queries:
    1. count(count by (instance) (up{job="node-exporter"})) - Linux/Windows agents
    2. count(count by (instance) (container_cpu_usage_seconds_total)) - Docker hosts via cadvisor
    
    Returns the maximum of both counts
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Query 1: node-exporter instances (host-level monitoring)
            node_query = 'count(count by (instance) (up{job="node-exporter"}))'
            response1 = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": node_query}
            )
            
            node_count = 0
            if response1.status_code == 200:
                data = response1.json()
                if data.get("status") == "success" and data.get("data", {}).get("result"):
                    result = data["data"]["result"][0]
                    node_count = int(float(result["value"][1]))
            
            # Query 2: cadvisor instances (container-level, fallback)
            cadvisor_query = 'count(count by (instance) (container_cpu_usage_seconds_total))'
            response2 = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": cadvisor_query}
            )
            
            cadvisor_count = 0
            if response2.status_code == 200:
                data = response2.json()
                if data.get("status") == "success" and data.get("data", {}).get("result"):
                    result = data["data"]["result"][0]
                    cadvisor_count = int(float(result["value"][1]))
            
            # Return the maximum of both counts
            return max(node_count, cadvisor_count)
            
    except Exception as e:
        print(f"⚠️ Error querying Prometheus for host count: {e}")
        return 0  # Fail-open: if Prometheus is down, return 0

@router.get("/status", response_model=LicenseStatusResponse)
async def get_license_status(current_user: User = Depends(get_current_user)):
    """
    Get license status from License Server v2
    
    Returns:
    - Tier information (demo_cloud/trial/annual_standard)
    - Host usage vs max_hosts limit
    - Expiration date and days remaining
    - Status (not_activated/active/expired/revoked/over_limit)
    """
    
    try:
        # 1. Validate license with License Server v2
        async with httpx.AsyncClient(timeout=10.0) as client:
            validate_request = {
                "license_key": LICENSE_KEY,
                "hostname": os.getenv("HOSTNAME", "rhinometric-console"),
                "ip_address": "172.22.0.1"  # Console IP
            }
            
            response = await client.post(
                f"{LICENSE_SERVER_URL}/api/licenses/validate/v2",
                json=validate_request
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"License Server error: {response.text}"
                )
            
            license_data = response.json()
        
        # 2. Get actual host count from Prometheus
        hosts_used = await get_monitored_hosts_count()
        
        # 3. Calculate hosts_available
        max_hosts = license_data.get("max_hosts", 5)
        hosts_available = max(0, max_hosts - hosts_used)
        
        # 4. Determine warnings
        warning = None
        days_remaining = license_data.get("days_remaining", 0)
        hours_remaining = license_data.get("hours_remaining")
        tier = license_data.get("tier", "trial")
        
        # Warning: approaching expiration
        if tier == "demo_cloud" and hours_remaining is not None and hours_remaining < 2:
            warning = f"Demo license expires in {hours_remaining} hours"
        elif days_remaining is not None and days_remaining < 7:
            warning = f"License expires in {days_remaining} days"
        
        # Warning: approaching host limit
        if hosts_used >= max_hosts:
            warning = f"⚠️ Host limit reached ({hosts_used}/{max_hosts})"
        elif hosts_used >= max_hosts * 0.8:
            warning = f"Approaching host limit ({hosts_used}/{max_hosts})"
        
        # 5. Build response
        return LicenseStatusResponse(
            license_key=LICENSE_KEY,
            tier=tier,
            max_hosts=max_hosts,
            hosts_used=hosts_used,
            hosts_available=hosts_available,
            issued_at=license_data.get("issued_at"),
            activated_at=license_data.get("activated_at"),
            expires_at=license_data.get("expires_at"),
            status=license_data.get("status", "unknown"),
            is_valid=license_data.get("valid", False),
            days_remaining=days_remaining,
            hours_remaining=hours_remaining,
            organization=license_data.get("customer_name"),
            organization_email=None,  # Not exposed in v2 validate response
            message=license_data.get("message", "Unknown status"),
            warning=warning
        )
        
    except httpx.ConnectError:
        # License Server unavailable - FAIL-OPEN for demo/development
        raise HTTPException(
            status_code=503,
            detail="License Server not available. Please contact your administrator."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch license status: {str(e)}"
        )

@router.get("/validate")
async def validate_license(current_user: User = Depends(get_current_user)):
    """
    Quick license validation endpoint
    
    Returns basic validation status without full host counting
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            validate_request = {
                "license_key": LICENSE_KEY,
                "hostname": os.getenv("HOSTNAME", "rhinometric-console")
            }
            
            response = await client.post(
                f"{LICENSE_SERVER_URL}/api/licenses/validate/v2",
                json=validate_request
            )
            
            return response.json()
            
    except httpx.ConnectError:
        # Fail-open: if License Server is down, allow access
        return {
            "valid": True,
            "message": "License Server not available - operating in demo mode",
            "tier": "trial"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
