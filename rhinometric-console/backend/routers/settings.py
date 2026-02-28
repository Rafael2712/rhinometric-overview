"""
Settings router for Rhinometric Console.
Manage global system settings including AI alerting toggle
and notification channel configuration (Slack + Email).

Architecture:
  - AI alerting toggle controls whether AI anomaly notifications are sent.
  - Notification channels configure WHERE notifications go (Slack/Email).
  - Defense in depth: toggle controls BOTH:
    1) AI engine gate (enable_notifications flag via HTTP API)
    2) Alertmanager receiver routing (blackhole vs ai-anomaly-alerts)
  - Alertmanager config is rendered from a template (not regex).
  - Secrets are persisted to /app/data/notification_channels.json (chmod 600).
  - Prometheus generic alerts are NOT affected by the AI toggle.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from config import settings
from routers.auth import get_current_user
from models.user import User as UserModel
import httpx
import json
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("rhinometric.settings")

router = APIRouter(tags=["settings"])

# --- Persistence ---
SETTINGS_FILE = os.environ.get("SETTINGS_FILE", "/app/data/settings.json")

DEFAULT_SETTINGS = {
    "ai_alerting_enabled": False
}


def _ensure_data_dir():
    d = os.path.dirname(SETTINGS_FILE)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _load_settings() -> dict:
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as fh:
                return json.load(fh)
    except Exception as e:
        logger.error(f"Failed to load settings from {SETTINGS_FILE}: {e}")
    _ensure_data_dir()
    try:
        with open(SETTINGS_FILE, "w") as fh:
            json.dump(DEFAULT_SETTINGS, fh, indent=2)
    except Exception:
        pass
    return dict(DEFAULT_SETTINGS)


def _save_settings(data: dict):
    _ensure_data_dir()
    with open(SETTINGS_FILE, "w") as fh:
        json.dump(data, fh, indent=2)
    logger.info(f"Settings saved to {SETTINGS_FILE}")


# --- External service URLs ---
ALERTMANAGER_URL = os.environ.get("ALERTMANAGER_URL_INTERNAL", "http://alertmanager:9093")
AI_ANOMALY_URL = os.environ.get("AI_ANOMALY_URL", "http://rhinometric-ai-anomaly:8085")


# --- Alertmanager template engine ---
from services.alertmanager_template import (
    load_channels, save_channels, redact_channels,
    write_alertmanager_config,
)


async def _sync_ai_engine(enabled: bool) -> bool:
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
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{ALERTMANAGER_URL}/-/reload", timeout=5.0)
            if resp.status_code == 200:
                logger.info("Alertmanager reloaded successfully")
            else:
                logger.warning(f"Alertmanager reload returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"Failed to reload Alertmanager: {e}")


def _regenerate_alertmanager(ai_alerting_enabled: bool):
    """Regenerate alertmanager.yml from template + current channels."""
    channels = load_channels()
    write_alertmanager_config(channels, ai_alerting_enabled)


# =====================================================================
# Models
# =====================================================================

class AIAlertsConfig(BaseModel):
    enabled: bool
    description: str = "Enable or disable AI anomaly alerting to Slack and email"

class SystemSettings(BaseModel):
    ai_alerts: AIAlertsConfig

class SlackChannelConfig(BaseModel):
    enabled: bool = False
    webhook_url: str = ""
    channel: str = "#rhinometric-alerts"

class EmailChannelConfig(BaseModel):
    enabled: bool = False
    smtp_host: str = "smtp.zoho.eu"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_require_tls: bool = True
    from_email: str = ""
    to_emails: List[str] = Field(default_factory=list)

class NotificationChannelsConfig(BaseModel):
    slack: SlackChannelConfig = Field(default_factory=SlackChannelConfig)
    email: EmailChannelConfig = Field(default_factory=EmailChannelConfig)

class NotificationChannelsResponse(BaseModel):
    slack: dict
    email: dict
    slack_status: str  # "configured" | "not_configured"
    email_status: str  # "configured" | "not_configured"


# =====================================================================
# AI Alerting Toggle Endpoints
# =====================================================================

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
    """Toggle AI alerting on/off with defense in depth."""
    user_roles = current_user.get_roles()
    if "ADMIN" not in user_roles and "OWNER" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin or Owner role required")

    data = _load_settings()
    data["ai_alerting_enabled"] = config.enabled
    _save_settings(data)

    ai_synced = await _sync_ai_engine(config.enabled)
    _regenerate_alertmanager(config.enabled)
    await _reload_alertmanager()

    state = "enabled" if config.enabled else "disabled"
    logger.info(f"AI alerting {state} by {current_user.username} (ai_synced={ai_synced})")
    return AIAlertsConfig(enabled=config.enabled, description=config.description)


# =====================================================================
# Notification Channels Endpoints
# =====================================================================

@router.get("/notification-channels")
async def get_notification_channels(current_user: UserModel = Depends(get_current_user)):
    """
    Get notification channel configuration.
    Secrets (webhook_url, smtp_password) are redacted.
    """
    user_roles = current_user.get_roles()
    if "ADMIN" not in user_roles and "OWNER" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin or Owner role required")

    channels = load_channels()
    redacted = redact_channels(channels)

    slack = channels.get("slack", {})
    email = channels.get("email", {})

    slack_status = "configured" if (slack.get("enabled") and slack.get("webhook_url")) else "not_configured"
    email_status = "configured" if (email.get("enabled") and email.get("smtp_username") and email.get("to_emails")) else "not_configured"

    return {
        "slack": redacted.get("slack", {}),
        "email": redacted.get("email", {}),
        "slack_status": slack_status,
        "email_status": email_status,
    }


@router.post("/notification-channels")
async def save_notification_channels(
    config: NotificationChannelsConfig,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Save notification channel configuration.
    
    - Persists to /app/data/notification_channels.json (chmod 600)
    - Regenerates alertmanager.yml from template
    - Reloads Alertmanager
    
    If smtp_password is "••••••••" (redacted), keeps the existing password.
    If webhook_url ends with "..." (redacted), keeps the existing webhook.
    """
    user_roles = current_user.get_roles()
    if "ADMIN" not in user_roles and "OWNER" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin or Owner role required")

    new_data = config.dict()
    existing = load_channels()

    # Preserve secrets if redacted values are sent back
    if new_data["slack"]["webhook_url"].endswith("...") or new_data["slack"]["webhook_url"] == "***configured***":
        new_data["slack"]["webhook_url"] = existing.get("slack", {}).get("webhook_url", "")
    if new_data["email"]["smtp_password"] == "••••••••":
        new_data["email"]["smtp_password"] = existing.get("email", {}).get("smtp_password", "")

    # Save channels
    save_channels(new_data)

    # Regenerate Alertmanager config
    settings_data = _load_settings()
    ai_enabled = settings_data.get("ai_alerting_enabled", False)
    _regenerate_alertmanager(ai_enabled)

    # Reload Alertmanager
    await _reload_alertmanager()

    logger.info(f"Notification channels updated by {current_user.username}")

    # Return redacted response
    redacted = redact_channels(new_data)
    slack = new_data.get("slack", {})
    email = new_data.get("email", {})
    slack_status = "configured" if (slack.get("enabled") and slack.get("webhook_url")) else "not_configured"
    email_status = "configured" if (email.get("enabled") and email.get("smtp_username") and email.get("to_emails")) else "not_configured"

    return {
        "status": "ok",
        "message": "Notification channels saved and Alertmanager reloaded",
        "slack": redacted.get("slack", {}),
        "email": redacted.get("email", {}),
        "slack_status": slack_status,
        "email_status": email_status,
    }


@router.post("/notification-channels/test/slack")
async def test_slack(current_user: UserModel = Depends(get_current_user)):
    """
    Send a test message to Slack using the configured webhook.
    """
    user_roles = current_user.get_roles()
    if "ADMIN" not in user_roles and "OWNER" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin or Owner role required")

    channels = load_channels()
    slack = channels.get("slack", {})

    if not slack.get("webhook_url"):
        raise HTTPException(status_code=400, detail="Slack webhook URL not configured")

    try:
        payload = {
            "channel": slack.get("channel", "#rhinometric-alerts"),
            "username": "Rhinometric AI",
            "icon_emoji": ":brain:",
            "text": ":white_check_mark: *Rhinometric Test Notification*\n\nThis is a test message from Rhinometric Console.\nSlack notifications are configured correctly!\n\n_Sent by: " + current_user.username + "_"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(slack["webhook_url"], json=payload)
            if resp.status_code == 200 and resp.text == "ok":
                logger.info(f"Slack test sent by {current_user.username}")
                return {"status": "ok", "message": "Test message sent to Slack successfully"}
            else:
                logger.warning(f"Slack test failed: {resp.status_code} {resp.text}")
                return {"status": "error", "message": f"Slack returned: {resp.status_code} - {resp.text}"}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Slack webhook timed out. Check the URL.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slack test failed: {str(e)}")


@router.post("/notification-channels/test/email")
async def test_email(current_user: UserModel = Depends(get_current_user)):
    """
    Send a test email using the configured SMTP settings.
    Sends directly via SMTP (not through Alertmanager).
    """
    user_roles = current_user.get_roles()
    if "ADMIN" not in user_roles and "OWNER" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin or Owner role required")

    channels = load_channels()
    email = channels.get("email", {})

    if not email.get("smtp_host") or not email.get("smtp_username"):
        raise HTTPException(status_code=400, detail="SMTP not configured")
    if not email.get("to_emails"):
        raise HTTPException(status_code=400, detail="No recipient email addresses configured")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Rhinometric - Test Email Notification"
        msg["From"] = email.get("from_email", email["smtp_username"])
        msg["To"] = ", ".join(email["to_emails"])

        html = f"""
        <html>
        <body style="font-family: -apple-system, sans-serif; background: #0f1923; color: #e0e0e0; padding: 40px;">
          <div style="max-width: 600px; margin: 0 auto; background: #1a2332; border-radius: 12px; padding: 32px; border: 1px solid #2a3a4a;">
            <h1 style="color: #00d4aa; margin: 0 0 8px;">&#x2705; Rhinometric Test</h1>
            <p style="color: #8899aa; margin: 0 0 24px;">Email notifications are configured correctly.</p>
            <div style="background: #0f1923; border-radius: 8px; padding: 16px; border: 1px solid #2a3a4a;">
              <p style="margin: 0; color: #e0e0e0;">This is a test email from <strong>Rhinometric Console</strong>.</p>
              <p style="margin: 8px 0 0; color: #8899aa; font-size: 13px;">Sent by: {current_user.username}</p>
            </div>
            <p style="color: #556677; font-size: 12px; margin: 24px 0 0;">Rhinometric AI-Powered Observability Platform</p>
          </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        smtp_host = email["smtp_host"]
        smtp_port = email.get("smtp_port", 587)
        use_tls = email.get("smtp_require_tls", True)

        if use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)

        server.login(email["smtp_username"], email["smtp_password"])
        server.sendmail(msg["From"], email["to_emails"], msg.as_string())
        server.quit()

        logger.info(f"Test email sent by {current_user.username} to {email['to_emails']}")
        return {"status": "ok", "message": f"Test email sent to {', '.join(email['to_emails'])}"}

    except smtplib.SMTPAuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"SMTP authentication failed: {str(e)}")
    except smtplib.SMTPConnectError as e:
        raise HTTPException(status_code=502, detail=f"Cannot connect to SMTP server: {str(e)}")
    except TimeoutError:
        raise HTTPException(status_code=504, detail=f"SMTP connection timed out ({email['smtp_host']}:{email.get('smtp_port', 587)})")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")


# =====================================================================
# System Info
# =====================================================================

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
            except Exception:
                pass
    return {"services": services, "version": settings.API_VERSION, "environment": "production"}
