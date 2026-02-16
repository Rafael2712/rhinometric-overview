"""
Settings router for Rhinometric Console.
Manage global system settings including AI alerting toggle.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


class AIAlertsConfig(BaseModel):
    """AI Alerts configuration"""
    enabled: bool
    description: str = "Enable or disable AI anomaly alerting to Slack/Alertmanager"


class SystemSettings(BaseModel):
    """System-wide settings"""
    ai_alerts: AIAlertsConfig


@router.get("", response_model=SystemSettings)
async def get_settings(current_user: UserModel = Depends(get_current_user)):
    """
    Get current system settings.
    Fetches AI alerting status from AI Anomaly service.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Fetch AI service config
            ai_url = f"{settings.AI_ANOMALY_URL}/config"
            response = await client.get(ai_url, timeout=5.0)
            
            if response.status_code == 200:
                ai_config = response.json()
                ai_alerts_enabled = ai_config.get("alertmanager", {}).get("alerts_enabled", False)
            else:
                # Default if AI service unavailable
                logger.warning(f"AI service unreachable: {response.status_code}")
                ai_alerts_enabled = False
        
        return SystemSettings(
            ai_alerts=AIAlertsConfig(
                enabled=ai_alerts_enabled,
                description="Enable or disable AI anomaly alerting to Slack/Alertmanager"
            )
        )
    
    except Exception as e:
        logger.error(f"Failed to fetch settings: {e}")
        # Return defaults on error
        return SystemSettings(
            ai_alerts=AIAlertsConfig(
                enabled=False,
                description="Enable or disable AI anomaly alerting to Slack/Alertmanager"
            )
        )


@router.put("/ai-alerts", response_model=AIAlertsConfig)
async def update_ai_alerts(
    config: AIAlertsConfig,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update AI alerting configuration.
    Requires admin role.
    
    Note: This updates runtime config in AI service.
    For persistent changes, update config.yaml and restart service.
    """
    # TODO: Add role check when roles are implemented
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        async with httpx.AsyncClient() as client:
            # Update AI service config
            ai_url = f"{settings.AI_ANOMALY_URL}/config"
            
            # Fetch current config
            get_response = await client.get(ai_url, timeout=5.0)
            get_response.raise_for_status()
            current_config = get_response.json()
            
            # Update alerts_enabled field
            if "alertmanager" not in current_config:
                current_config["alertmanager"] = {}
            
            current_config["alertmanager"]["alerts_enabled"] = config.enabled
            
            # Send update
            put_response = await client.put(
                ai_url,
                json=current_config,
                timeout=5.0
            )
            put_response.raise_for_status()
            
            logger.info(
                f"AI alerting {'enabled' if config.enabled else 'disabled'} by {current_user.username}"
            )
            
            return AIAlertsConfig(
                enabled=config.enabled,
                description=config.description
            )
    
    except httpx.HTTPStatusError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI Anomaly service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Failed to update AI alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update settings"
        )


@router.get("/system-info")
async def get_system_info(current_user: UserModel = Depends(get_current_user)):
    """
    Get system information and service health.
    """
    services = {
        "prometheus": {"url": settings.PROMETHEUS_URL, "healthy": False},
        "ai_anomaly": {"url": settings.AI_ANOMALY_URL, "healthy": False},
        "alertmanager": {"url": settings.ALERTMANAGER_URL, "healthy": False},
        "grafana": {"url": settings.GRAFANA_URL, "healthy": False},
    }
    
    async with httpx.AsyncClient() as client:
        # Check Prometheus
        try:
            resp = await client.get(f"{settings.PROMETHEUS_URL}/-/healthy", timeout=2.0)
            services["prometheus"]["healthy"] = resp.status_code == 200
        except:
            pass
        
        # Check AI Anomaly
        try:
            resp = await client.get(f"{settings.AI_ANOMALY_URL}/health", timeout=2.0)
            services["ai_anomaly"]["healthy"] = resp.status_code == 200
        except:
            pass
        
        # Check Alertmanager
        try:
            resp = await client.get(f"{settings.ALERTMANAGER_URL}/-/healthy", timeout=2.0)
            services["alertmanager"]["healthy"] = resp.status_code == 200
        except:
            pass
        
        # Check Grafana
        try:
            resp = await client.get(f"{settings.GRAFANA_URL}/api/health", timeout=2.0)
            services["grafana"]["healthy"] = resp.status_code == 200
        except:
            pass
    
    return {
        "services": services,
        "version": settings.API_VERSION,
        "environment": "production"
    }
