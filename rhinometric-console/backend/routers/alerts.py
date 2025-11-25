from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import httpx
from config import settings
from routers.auth import get_current_user, User

router = APIRouter()

class Alert(BaseModel):
    fingerprint: str
    status: str
    labels: dict
    annotations: dict
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str
    severity: str

class AlertsResponse(BaseModel):
    alerts: list[Alert]
    total: int

@router.get("", response_model=AlertsResponse)
async def get_alerts(
    current_user: User = Depends(get_current_user),
    active: Optional[bool] = Query(True, description="Filter active alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity")
):
    """
    Get alerts from AlertManager (port 9093)
    
    Filters:
    - active: true/false (default: true)
    - severity: critical, warning, info
    """
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # AlertManager API endpoint
            url = f"{settings.ALERTMANAGER_URL}/api/v2/alerts"
            
            params = {}
            if active is not None:
                params["active"] = str(active).lower()
            if severity:
                params["filter"] = f"severity={severity}"
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                alerts_data = response.json()
                
                # Parse and format alerts
                formatted_alerts = []
                for alert in alerts_data:
                    formatted_alerts.append(Alert(
                        fingerprint=alert.get("fingerprint", ""),
                        status=alert.get("status", {}).get("state", "unknown"),
                        labels=alert.get("labels", {}),
                        annotations=alert.get("annotations", {}),
                        startsAt=alert.get("startsAt", ""),
                        endsAt=alert.get("endsAt"),
                        generatorURL=alert.get("generatorURL", ""),
                        severity=alert.get("labels", {}).get("severity", "unknown")
                    ))
                
                return AlertsResponse(
                    alerts=formatted_alerts,
                    total=len(formatted_alerts)
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AlertManager error: {response.text}"
                )
                
    except httpx.ConnectError:
        # Return empty list if AlertManager is not available
        return AlertsResponse(alerts=[], total=0)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch alerts: {str(e)}"
        )

@router.post("/silence")
async def silence_alert(
    fingerprint: str,
    duration: str = "1h",
    current_user: User = Depends(get_current_user)
):
    """Create a silence for an alert"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            silence_data = {
                "matchers": [{"name": "alertname", "value": fingerprint, "isRegex": False}],
                "startsAt": "",
                "endsAt": "",
                "createdBy": current_user.username,
                "comment": f"Silenced via Rhinometric Console for {duration}"
            }
            
            response = await client.post(
                f"{settings.ALERTMANAGER_URL}/api/v2/silences",
                json=silence_data
            )
            
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="AlertManager is not available"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
