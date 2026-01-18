from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import httpx
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel

router = APIRouter()

class Anomaly(BaseModel):
    id: int
    timestamp: str
    metric: str
    service: str
    severity: str
    deviation: str
    baseline: float
    current: float
    confidence: float | None = None
    description: str | None = None

class AnomaliesResponse(BaseModel):
    anomalies: list[Anomaly]
    total: int
    page: int
    page_size: int

@router.get("")
async def get_anomalies(
    current_user: UserModel = Depends(get_current_user),
    severity: Optional[str] = Query(None, description="Filter by severity: high, medium, low"),
    time_range: Optional[str] = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get anomalies from AI Anomaly Detection Engine (port 8085)
    
    Filters:
    - severity: high, medium, low
    - time_range: 1h, 24h, 7d, 30d
    - pagination: page, page_size
    
    Note: Response format is passed through directly from AI service (not validated)
    """
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # AI Anomaly service uses "limit" instead of "page_size"
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
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AI Anomaly service error: {response.text}"
                )
                
    except httpx.ConnectError as e:
        # AI Anomaly Detection Engine connection error
        print(f"Error connecting to AI Anomaly service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"AI Anomaly Detection Engine connection failed: {str(e)}"
        )
    except Exception as e:
        # Other errors (DNS, timeout, etc.)
        print(f"Error fetching anomalies: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"AI Anomaly service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch anomalies: {str(e)}"
        )

@router.get("/{anomaly_id}")
async def get_anomaly_details(
    anomaly_id: int,
    current_user: UserModel = Depends(get_current_user)
):
    """Get detailed information about a specific anomaly"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.AI_ANOMALY_URL}/anomalies/{anomaly_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
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
