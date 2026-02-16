from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import httpx
from config import settings
from routers.auth import get_current_user, User

router = APIRouter()

class LicenseFeature(BaseModel):
    name: str
    enabled: bool

class LicenseResponse(BaseModel):
    license_type: str
    status: str
    hosts_used: int
    hosts_limit: int
    expiration_date: str
    days_remaining: int
    features: list[LicenseFeature]
    organization: str | None = None

@router.get("/status", response_model=LicenseResponse)
async def get_license_status(current_user: User = Depends(get_current_user)):
    """
    Get license status from License Validator service (port 8091)
    
    Returns license information including:
    - License type (Starter/Standard/Enterprise)
    - Status (Active/Expired/Invalid)
    - Host usage and limits
    - Expiration date
    - Enabled features
    """
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try to connect to License Validator
            response = await client.get(f"{settings.LICENSE_VALIDATOR_URL}/api/license/status")
            
            if response.status_code == 200:
                license_data = response.json()
                return LicenseResponse(**license_data)
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"License Validator returned error: {response.text}"
                )
                
    except httpx.ConnectError:
        # License Validator is not available - return honest error
        raise HTTPException(
            status_code=503,
            detail="License Validator service is not configured or unavailable. Please contact your administrator."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch license status: {str(e)}"
        )

@router.get("/validate")
async def validate_license(current_user: User = Depends(get_current_user)):
    """Validate current license key"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.LICENSE_VALIDATOR_URL}/api/license/validate")
            return response.json()
    except httpx.ConnectError:
        return {"valid": True, "message": "License Validator service not available - using demo mode"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
