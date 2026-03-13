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
from urllib.parse import quote as _url_quote
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
    if "..." in new_data["slack"]["webhook_url"] or new_data["slack"]["webhook_url"] == "***configured***":
        new_data["slack"]["webhook_url"] = existing.get("slack", {}).get("webhook_url", "")
    if new_data["email"]["smtp_password"] == "••••••••":
        new_data["email"]["smtp_password"] = existing.get("email", {}).get("smtp_password", "")

    # Preserve extra sections (zoho_api, etc.) that the UI doesn't manage
    for key in existing:
        if key not in new_data:
            new_data[key] = existing[key]

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
    Send a test email using SMTP or Zoho API fallback.
    Uses email_service._send_mime (same path as real emails).
    """
    user_roles = current_user.get_roles()
    if "ADMIN" not in user_roles and "OWNER" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin or Owner role required")

    from services.email_service import (
        _load_email_config, _load_zoho_api_config,
        _send_mime, _send_via_zoho_api, is_email_service_available,
    )

    available, reason = is_email_service_available()
    if not available:
        raise HTTPException(status_code=400, detail=f"Email not available: {reason}")

    cfg = _load_email_config()
    channels = load_channels()
    email_ch = channels.get("email", {})
    recipients = email_ch.get("to_emails", [])
    if not recipients:
        raise HTTPException(status_code=400, detail="No recipient email addresses configured")

    try:
        to_addr = ", ".join(recipients)
        from_addr = email_ch.get("from_email", email_ch.get("smtp_username", "noreply@rhinometric.com"))

        html = f"""
        <html>
        <body style="font-family: -apple-system, sans-serif; background: #0f1923; color: #e0e0e0; padding: 40px;">
          <div style="max-width: 600px; margin: 0 auto; background: #1a2332; border-radius: 12px; padding: 32px; border: 1px solid #2a3a4a;">
            <h1 style="color: #00d4aa; margin: 0 0 8px;">&#x2705; Rhinometric Test</h1>
            <p style="color: #8899aa; margin: 0 0 24px;">Email notifications are working ({reason}).</p>
            <div style="background: #0f1923; border-radius: 8px; padding: 16px; border: 1px solid #2a3a4a;">
              <p style="margin: 0; color: #e0e0e0;">This is a test email from <strong>Rhinometric Console</strong>.</p>
              <p style="margin: 8px 0 0; color: #8899aa; font-size: 13px;">Sent by: {current_user.username} | Transport: {reason}</p>
            </div>
            <p style="color: #556677; font-size: 12px; margin: 24px 0 0;">Rhinometric AI-Powered Observability Platform</p>
          </div>
        </body>
        </html>
        """

        if cfg:
            # Build MIME and send through _send_mime (handles SMTP + Zoho API fallback)
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Rhinometric - Test Email Notification"
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg.attach(MIMEText(html, "html"))
            await _send_mime(msg, cfg)
        else:
            # No SMTP config, send directly via Zoho API
            zoho_cfg = _load_zoho_api_config()
            if not zoho_cfg:
                raise HTTPException(status_code=400, detail="Neither SMTP nor Zoho API configured")
            await _send_via_zoho_api(to_addr, "Rhinometric - Test Email Notification", html, from_addr, zoho_cfg)

        logger.info(f"Test email sent by {current_user.username} to {recipients} via {reason}")
        return {"status": "ok", "message": f"Test email sent to {to_addr}", "transport": reason}

    except HTTPException:
        raise
    except TimeoutError:
        raise HTTPException(status_code=504, detail=f"Connection timed out")
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


# ???????????????????????????????????????????????????
# EMAIL SERVICE STATUS (admin-only)
# ???????????????????????????????????????????????????

@router.get("/email/status")
async def get_email_status(
    current_user: UserModel = Depends(get_current_user),
):
    """
    Admin-only: Check email delivery service availability.
    Performs TCP pre-check against configured SMTP host/port.
    Returns: {available: bool, reason: str, config_summary: {...}}
    """
    from routers.auth import require_role
    # Manual role check (OWNER/ADMIN only)
    user_roles = current_user.get_roles()
    if not any(r in user_roles for r in ["OWNER", "ADMIN"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    from services.email_service import is_email_service_available, _load_email_config

    available, reason = is_email_service_available()
    cfg = _load_email_config()

    config_summary = None
    if cfg:
        config_summary = {
            "smtp_host": cfg.get("smtp_host"),
            "smtp_port": cfg.get("smtp_port"),
            "from_email": cfg.get("from_email"),
            "tls": cfg.get("smtp_require_tls", True),
        }

    return {
        "available": available,
        "reason": reason,
        "config_summary": config_summary,
    }



# --- Alertmanager Webhook for Email Forwarding via Zoho API ---
from fastapi import Request


# ── Email cooldown deduplication ──
# Prevents repeated email alerts for the same metric+severity within a cooldown window.
# Defense-in-depth alongside Alertmanager group_interval increase.
import time as _time

_EMAIL_COOLDOWN: dict = {}          # key=(metric,severity,status) → last_sent_ts
EMAIL_COOLDOWN_SECONDS = 3600       # 1 hour cooldown per unique alert


def _email_cooldown_ok(metric: str, severity: str, status: str) -> bool:
    """Return True if this alert should be emailed (not in cooldown)."""
    key = (metric, severity, status)
    now = _time.time()
    last = _EMAIL_COOLDOWN.get(key, 0)
    if now - last < EMAIL_COOLDOWN_SECONDS:
        return False
    _EMAIL_COOLDOWN[key] = now
    # Prune stale entries (keep cache bounded)
    if len(_EMAIL_COOLDOWN) > 500:
        cutoff = now - EMAIL_COOLDOWN_SECONDS * 2
        stale = [k for k, v in _EMAIL_COOLDOWN.items() if v < cutoff]
        for k in stale:
            del _EMAIL_COOLDOWN[k]
    return True

RED_CIRCLE = chr(0x1F534)
ORANGE_CIRCLE = chr(0x1F7E0)

@router.post("/alertmanager-webhook/email", include_in_schema=False)
async def alertmanager_email_webhook(request: Request):
    """
    Webhook called by Alertmanager to send email alerts via Zoho API.
    Alertmanager cannot use native SMTP because Hetzner blocks SMTP ports.
    This endpoint receives alert data and sends it via Zoho Mail API.
    No auth required - only accessible from internal Docker network.
    """
    import html as html_mod
    try:
        data = await request.json()
        alerts = data.get("alerts", [])
        status = data.get("status", "firing")
        
        from services.email_service import _load_zoho_api_config, _send_via_zoho_api
        from services.alertmanager_template import load_channels
        
        channels = load_channels()
        email_cfg = channels.get("email", {})
        zoho_cfg = _load_zoho_api_config()
        
        if not zoho_cfg:
            return {"status": "error", "message": "Zoho API not configured"}
        
        to_emails = email_cfg.get("to_emails", [])
        if not to_emails:
            return {"status": "error", "message": "No recipient emails configured"}
        
        console_url = os.getenv("RHINO_PUBLIC_CONSOLE_URL", "https://console-staging.rhinometric.com")
        
        for alert in alerts:
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            alert_status = alert.get("status", status)
            severity = labels.get("severity", "unknown").upper()
            metric = labels.get("metric", labels.get("alertname", "unknown"))
            
            subject = "[{}] Rhinometric AI Alert: {}".format(severity, metric)
            if alert_status == "resolved":
                subject = "[RESOLVED] " + subject
            
            icon = RED_CIRCLE if severity == "CRITICAL" else ORANGE_CIRCLE
            bg_color = "#dc2626" if severity == "CRITICAL" else "#f59e0b" if severity in ("WARNING", "HIGH") else "#3b82f6"
            metric_escaped = html_mod.escape(metric)
            component = html_mod.escape(labels.get("component", "unknown"))
            service = html_mod.escape(labels.get("service", "unknown"))
            cur_val = html_mod.escape(annotations.get("current_value", "N/A"))
            base_val = html_mod.escape(annotations.get("baseline_value", "N/A"))
            dev_pct = html_mod.escape(annotations.get("deviation_percent", "N/A"))
            

            # Map metric to correct Grafana dashboard/panel
            grafana_base = "http://46.225.231.117/grafana"
            metric_raw = labels.get("metric", labels.get("alertname", "unknown"))
            # ── Parse metric label (format: metric_name::entity_name or just metric_name) ──
            if "::" in metric_raw:
                metric_key, entity_name_parsed = metric_raw.split("::", 1)
            else:
                metric_key = metric_raw
                entity_name_parsed = ""

            # ── Grafana deep link: correct dashboard + panel + time range + entity filter ──
            _time_range = "from=now-1h&to=now"
            _svc_filter = f"&var-service_name={_url_quote(entity_name_parsed)}" if entity_name_parsed else ""

            if metric_key == "external_service_latency":
                grafana_url = f"{grafana_base}/d/ext-svc-intelligence/external-services-intelligence?viewPanel=6&{_time_range}&theme=dark{_svc_filter}"
            elif metric_key == "external_service_availability":
                grafana_url = f"{grafana_base}/d/ext-svc-intelligence/external-services-intelligence?viewPanel=5&{_time_range}&theme=dark{_svc_filter}"
            elif metric_key == "external_service_health":
                grafana_url = f"{grafana_base}/d/ext-svc-intelligence/external-services-intelligence?viewPanel=12&{_time_range}&theme=dark{_svc_filter}"
            elif metric_key == "node_cpu_usage":
                grafana_url = f"{grafana_base}/d/rhinometric-system-overview/system-overview?viewPanel=1&{_time_range}&theme=dark"
            elif metric_key == "node_memory_usage":
                grafana_url = f"{grafana_base}/d/rhinometric-system-overview/system-overview?viewPanel=2&{_time_range}&theme=dark"
            elif metric_key in ("node_disk_usage", "node_disk_io"):
                grafana_url = f"{grafana_base}/d/rhinometric-system-overview/system-overview?viewPanel=3&{_time_range}&theme=dark"
            elif metric_key in ("node_network_receive", "node_network_transmit"):
                grafana_url = f"{grafana_base}/d/rhinometric-system-overview/system-overview?viewPanel=6&{_time_range}&theme=dark"
            elif metric_key.startswith("container_"):
                grafana_url = f"{grafana_base}/d/docker-new/docker-containers?{_time_range}&theme=dark"
            else:
                grafana_url = f"{grafana_base}/d/ai-anomaly-service/ai-anomaly-service?{_time_range}&theme=dark"

            # ── Console deep link: /anomalies with metric + entity query params ──
            console_params = f"metric={_url_quote(metric_key)}"
            if entity_name_parsed:
                console_params += f"&entity={_url_quote(entity_name_parsed)}"
            console_dash_path = f"/anomalies?{console_params}"

            body_html = (
                '<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">'
                '<div style="background:{bg};color:white;padding:16px;border-radius:8px 8px 0 0;">'
                '<h2 style="margin:0;">{icon} [{sev}] AI Anomaly: {met}</h2>'
                '<p style="margin:4px 0 0 0;opacity:0.9;">Status: {st}</p>'
                '</div>'
                '<div style="background:#1e293b;color:#e2e8f0;padding:20px;border-radius:0 0 8px 8px;">'
                '<p><strong>Metric:</strong> {met}</p>'
                '<p><strong>Severity:</strong> {sev}</p>'
                '<p><strong>Component:</strong> {comp}</p>'
                '<p><strong>Service:</strong> {svc}</p>'
                '<p><strong>Current Value:</strong> {cur}</p>'
                '<p><strong>Expected Value:</strong> {base}</p>'
                '<p><strong>Deviation:</strong> {dev}</p>'
                '<hr style="border-color:#334155;">'
                '<p style="margin-top:16px;">'
                '<a href="{url}{console_dash}" style="background:#3b82f6;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;margin-right:10px;">Ver Dashboard en Consola</a> '
                '<a href="{grafana_url}" style="background:#f59e0b;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;">Ver en Grafana</a>'
                '</p>'
                '</div></div>'

            ).format(
                bg=bg_color, icon=icon, sev=severity, met=metric_escaped,
                st=alert_status.upper(), comp=component, svc=service,
                cur=cur_val, base=base_val, dev=dev_pct, url=console_url,
                grafana_url=grafana_url,
                console_dash=console_dash_path
            )
            
            for to_email in to_emails:
                try:
                    from_addr = zoho_cfg.get("from_address", "rafael.canelon@rhinometric.com")
                    await _send_via_zoho_api(
                        zoho_cfg=zoho_cfg,
                        to_email=to_email,
                        subject=subject,
                        html_body=body_html,
                        from_email=from_addr
                    )
                    logger.info("Alert email sent to %s: %s", to_email, subject)
                except Exception as e:
                    logger.error("Failed to send alert email to %s: %s", to_email, e)
        
        return {"status": "ok", "message": "Processed {} alerts".format(len(alerts))}
    except Exception as e:
        logger.error("Alertmanager webhook error: %s", e)
        return {"status": "error", "message": str(e)}
