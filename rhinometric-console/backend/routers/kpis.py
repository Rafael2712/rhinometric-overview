from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
from config import settings
from routers.auth import get_current_user, User

router = APIRouter()

class KPIResponse(BaseModel):
    service_status: dict
    monitored_hosts: dict
    active_anomalies: dict
    alerts_24h: dict

@router.get("", response_model=KPIResponse)
async def get_kpis(current_user: User = Depends(get_current_user)):
    """
    Aggregate KPIs from Prometheus and other services
    
    Returns:
    - Service status (uptime from Prometheus)
    - Monitored hosts count
    - Active anomalies count (from AI Anomaly service)
    - Alerts in last 24h (from AlertManager)
    """
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query Prometheus for service status
            prom_url = f"{settings.PROMETHEUS_URL}/api/v1/query"
            
            # Get number of up services
            services_response = await client.get(
                prom_url,
                params={"query": "up"}
            )
            services_data = services_response.json()
            
            # Count operational services
            operational_count = 0
            total_count = 0
            if services_data.get("status") == "success":
                results = services_data.get("data", {}).get("result", [])
                total_count = len(results)
                operational_count = sum(1 for r in results if r.get("value", [None, "0"])[1] == "1")
            
            # Calculate uptime percentage
            uptime_pct = (operational_count / total_count * 100) if total_count > 0 else 100.0
            
            # Get unique hosts
            hosts_response = await client.get(
                prom_url,
                params={"query": "count(up) by (instance)"}
            )
            hosts_data = hosts_response.json()
            host_count = len(hosts_data.get("data", {}).get("result", []))
            
            return KPIResponse(
                service_status={
                    "value": "Operational" if operational_count == total_count else "Degraded",
                    "status": "success" if operational_count == total_count else "warning",
                    "change": f"{uptime_pct:.1f}% Uptime (Last 30d)",
                    "operational_count": operational_count,
                    "total_count": total_count
                },
                monitored_hosts={
                    "value": str(host_count),
                    "status": "success",
                    "change": f"of {host_count} used"
                },
                active_anomalies={
                    "value": "0",  # TODO: Connect to AI Anomaly service
                    "status": "success",
                    "change": "No issues detected"
                },
                alerts_24h={
                    "value": "0",  # TODO: Connect to AlertManager
                    "status": "success",
                    "change": "Last 24 hours"
                }
            )
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Prometheus: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
