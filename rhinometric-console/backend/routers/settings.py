"""
Settings router for Rhinometric Console.
Manage global system settings including AI alerting toggle.

Architecture:
  - The ai_alerting_enabled setting controls whether AI anomaly
    notifications are sent to Slack/Email via Alertmanager.
  - Defense in depth: toggle controls BOTH:
    1) AI engine gate (enable_notifications flag via HTTP API)
    2) Alertmanager receiver routing (blackhole vs ai-anomaly-alerts)
  - Only severity="critical" anomalies trigger notifications when enabled.
  - When disabled, ALL anomalies are still detected by the AI engine
    and visible in the console UI, but no external notifications are sent.
  - The setting is persisted to /app/data/settings.json (volume-mounted).
  - Prometheus generic alerts are NOT affected by this toggle.
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

logger = logging.getLogger("rhinometric.settings")

router = APIRouter(tags=["settings"])

# --- Persistence ---
SETTINGS_FILE = os.environ.get("SETTINGS_FILE", "/app/data/settings.json")

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
    # Create default if missing
    _ensure_data_dir()
    try:
        with open(SETTINGS_FILE, "w") as fh:
            json.dump(DEFAULT_SETTINGS, fh, indent=2)
        logger.info(f"Created default settings: {SETTINGS_FILE}")
    except Exception:
        pass
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
AI_ANOMALY_URL = os.environ.get("AI_ANOMALY_URL", "http://rhinometric-ai-anomaly:8085")


async def _sync_ai_engine(enabled: bool) -> bool:
    """
    Sync notification toggle to AI engine via HTTP API.
    This is the PRIMARY gate - prevents alerts from being sent at source.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{AI_ANOMALY_URL}/api/settings/notifications",
                json={"enabled": enabled}
            )
            if resp.status_code == 200:
                logger.info(f"AI engine notifications synced: enabled={enabled}")
                return True
            else:
                logger.warning(f"AI engine sync returned {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to sync AI engine: {e}")
        return False


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
    Update the AI anomaly critical-route receiver in alertmanager.yml.
    Uses stable label match on rhinometric_source: ai-anomaly.
    This is the SECONDARY gate (defense in depth).
    """
    try:
        if not os.path.exists(ALERTMANAGER_CONFIG):
            logger.warning(f"Alertmanager config not found at {ALERTMANAGER_CONFIG}")
            return False

        with open(ALERTMANAGER_CONFIG, "r") as fh:
            text = fh.read()

        target = "ai-anomaly-alerts" if enabled else "blackhole"

        # Find the Route AI block: rhinometric_source: ai-anomaly + severity: critical
        # and replace just the receiver value.
        pattern = re.compile(
            r'(- match:\s*\n\s+rhinometric_source:\s*ai-anomaly\s*\n\s+severity:\s*critical\s*\n\s+receiver:\s*)"[^"]*"',
            re.MULTILINE
        )
        new_text, count = pattern.subn(lambda m: m.group(1) + f'"{target}"', text, count=1)

        if count == 0:
            # Fallback: try old component-based pattern
            pattern_old = re.compile(
                r'(- match:\s*\n\s+component:\s*ai-anomaly\s*\n\s+severity:\s*critical\s*\n\s+receiver:\s*)"[^"]*"',
                re.MULTILINE
            )
            new_text, count = pattern_old.subn(lambda m: m.group(1) + f'"{target}"', text, count=1)

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
    """Get current system settings."""
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
      2. Syncs to AI engine (primary gate - stops alerts at source).
      3. Updates alertmanager.yml receiver (secondary gate - defense in depth).
      4. Triggers an Alertmanager reload.

    NOTE: Prometheus generic alerts are NOT affected by this toggle.
    """
    # Check admin role
    user_roles = current_user.get_roles()
    if "ADMIN" not in user_roles and "OWNER" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin or Owner role required")

    # 1. Persist
    data = _load_settings()
    data["ai_alerting_enabled"] = config.enabled
    _save_settings(data)

    # 2. Sync AI engine (PRIMARY gate)
    ai_synced = await _sync_ai_engine(config.enabled)
    if not ai_synced:
        logger.warning("AI engine sync failed - alertmanager gate still applies")

    # 3. Update Alertmanager config (SECONDARY gate)
    _update_alertmanager_config(config.enabled)

    # 4. Reload Alertmanager
    await _reload_alertmanager()

    state = "enabled" if config.enabled else "disabled"
    logger.info(
        f"AI alerting {state} by {current_user.username} "
        f"(ai_engine_synced={ai_synced})"
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
