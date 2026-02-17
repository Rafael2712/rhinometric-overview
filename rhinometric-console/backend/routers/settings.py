"""
Settings router for Rhinometric Console.
Manage global system settings including AI alerting toggle.

Architecture:
  - The ai_alerting_enabled setting controls whether AI anomaly
    notifications are sent to Slack/Email via Alertmanager.
  - Only severity="critical" anomalies trigger notifications when enabled.
  - When disabled, ALL anomalies (including critical) are still detected
    by the AI engine and visible in the console UI, but no external
    notifications are sent.
  - The setting is persisted to /app/data/settings.json (volume-mounted).
  - On toggle change, the backend rewrites Alertmanager's config to swap
    the AI route receiver between the real one and a blackhole.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel
import httpx
import json
import os
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"])

# --- Persistence ---
# Settings file path: persisted in the volume-mounted data directory.
# In docker-compose this maps to ~/rhinometric_data_v2.5/console-backend/logs/
# but we use a dedicated path inside the container.
SETTINGS_FILE = os.environ.get("SETTINGS_FILE", "/app/data/settings.json")

# Default: OFF in current production to stop spam.
# For new client installations, the recommended default is True.
DEFAULT_SETTINGS = {
    "ai_alerting_enabled": False
}

def _ensure_data_dir():
    """Ensure the directory for the settings file exists."""
    d = os.path.dirname(SETTINGS_FILE)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _load_settings() -> dict:
    """Load settings from disk. Returns defaults if file doesn't exist."""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as fh:
                return json.load(fh)
    except Exception as e:
        logger.error(f"Failed to load settings from {SETTINGS_FILE}: {e}")
    return dict(DEFAULT_SETTINGS)

def _save_settings(data: dict):
    """Persist settings to disk."""
    _ensure_data_dir()
    try:
        with open(SETTINGS_FILE, "w") as fh:
            json.dump(data, fh, indent=2)
        logger.info(f"Settings saved to {SETTINGS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save settings to {SETTINGS_FILE}: {e}")
        raise

# --- Alertmanager config management ---
ALERTMANAGER_CONFIG = "/etc/alertmanager/alertmanager.yml"
ALERTMANAGER_URL = os.environ.get("ALERTMANAGER_URL_INTERNAL", "http://alertmanager:9093")

async def _reload_alertmanager():
    """Tell Alertmanager to reload its configuration."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{ALERTMANAGER_URL}/-/reload", timeout=5.0)
            if resp.status_code == 200:
                logger.info("Alertmanager reloaded successfully")
            else:
                logger.warning(f"Alertmanager reload returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"Failed to reload Alertmanager: {e}")

def _update_alertmanager_config(enabled: bool):
    """
    Swap the AI anomaly critical-route receiver in alertmanager.yml.
    Uses text-based replacement to preserve Go template strings intact.
    When enabled=True  -> receiver: ai-anomaly-alerts  (sends Slack+email for critical)
    When enabled=False -> receiver: blackhole           (silent)
    Only Route 1 (component: ai-anomaly + severity: critical) is toggled.
    Route 2 (catchall for non-critical AI anomalies) always stays blackhole.
    """
    try:
        if not os.path.exists(ALERTMANAGER_CONFIG):
            logger.warning(f"Alertmanager config not found at {ALERTMANAGER_CONFIG}")
            return False

        with open(ALERTMANAGER_CONFIG, "r") as fh:
            text = fh.read()

        target = "ai-anomaly-alerts" if enabled else "blackhole"

        # Find the Route 1 block: component: ai-anomaly + severity: critical
        # and replace just the receiver value.
        # This avoids yaml.dump which corrupts Go template quoted strings.
        pattern = re.compile(
            r'(- match:\s*\n\s+component:\s*ai-anomaly\s*\n\s+severity:\s*critical\s*\n\s+receiver:\s*)"[^"]*"',
            re.MULTILINE
        )
        new_text, count = pattern.subn(lambda m: m.group(1) + f'"{target}"', text, count=1)

        if count == 0:
            logger.warning("Could not find critical AI anomaly route in alertmanager config")
            return False

        with open(ALERTMANAGER_CONFIG, "w") as fh:
            fh.write(new_text)

        logger.info(f"AI anomaly critical-route receiver set to: {target}")
        return True
    except Exception as e:
        logger.error(f"Failed to update alertmanager config: {e}")
        return False


class AIAlertsConfig(BaseModel):
    """AI Alerts configuration"""
    enabled: bool
    description: str = "Enable or disable AI anomaly alerting to Slack and email"

class SystemSettings(BaseModel):
    """System-wide settings"""
    ai_alerts: AIAlertsConfig


# --- Endpoints ---
@router.get("", response_model=SystemSettings)
async def get_settings(current_user: UserModel = Depends(get_current_user)):
    """
    Get current system settings.
    Reads ai_alerting_enabled from local persistence.
    """
    data = _load_settings()
    return SystemSettings(
        ai_alerts=AIAlertsConfig(
            enabled=data.get("ai_alerting_enabled", False),
            description="Enable or disable AI anomaly alerting to Slack and email"
        )
    )


@router.put("/ai-alerts", response_model=AIAlertsConfig)
async def update_ai_alerts(
    config: AIAlertsConfig,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Toggle AI alerting on/off.

    When enabled:
      - Only severity="critical" AI anomalies send Slack + email notifications.
      - Lower severities (high, medium, low) remain visible in the console only.
    When disabled:
      - No AI anomaly notifications are sent externally.
      - All anomalies still appear in the AI Anomalies page.

    This endpoint:
      1. Persists the setting to disk.
      2. Updates alertmanager.yml to swap receiver.
      3. Triggers an Alertmanager reload.
    """
    # Check admin role
    user_roles = current_user.get_roles()
    if "ADMIN" not in user_roles and "OWNER" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin or Owner role required")

    # 1. Persist
    data = _load_settings()
    data["ai_alerting_enabled"] = config.enabled
    _save_settings(data)

    # 2. Update Alertmanager config
    _update_alertmanager_config(config.enabled)

    # 3. Reload Alertmanager
    await _reload_alertmanager()

    logger.info(
        f"AI alerting {'enabled' if config.enabled else 'disabled'} "
        f"by {current_user.username}"
    )

    return AIAlertsConfig(
        enabled=config.enabled,
        description=config.description
    )


@router.get("/system-info")
async def get_system_info(current_user: UserModel = Depends(get_current_user)):
    """Get system information and service health."""
    services = {
        "prometheus": {"url": settings.PROMETHEUS_URL, "healthy": False},
        "ai_anomaly": {"url": settings.AI_ANOMALY_URL, "healthy": False},
        "alertmanager": {"url": settings.ALERTMANAGER_URL, "healthy": False},
        "grafana": {"url": settings.GRAFANA_URL, "healthy": False},
    }

    async with httpx.AsyncClient() as client:
        for svc, info in services.items():
            try:
                health_path = {
                    "prometheus": "/-/healthy",
                    "ai_anomaly": "/health",
                    "alertmanager": "/-/healthy",
                    "grafana": "/api/health",
                }.get(svc, "/health")
                resp = await client.get(f"{info['url']}{health_path}", timeout=2.0)
                info["healthy"] = resp.status_code == 200
            except:
                pass

    return {
        "services": services,
        "version": settings.API_VERSION,
        "environment": "production"
    }
