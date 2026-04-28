"""
Alert Email Notification Service.

Sends alert firing and recovery emails DIRECTLY via Zoho Mail API,
bypassing Alertmanager (whose SMTP is blocked by Hetzner).

Design:
  - Sync API for use from _fire_rule_alert() and _resolve_recovered_services()
  - Persistent dedup via AlertEvent.notification_sent_at / recovery_notification_sent_at
  - Recipients: ALL active Keycloak users with an email address
  - Thread-safe: sends in a background thread to avoid blocking the evaluation loop
"""

import json
import ssl
import time
import logging
import threading
import html as html_mod
from typing import List, Optional
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode

logger = logging.getLogger("rhinometric.alert_email")

CHANNELS_PATH = "/app/data/notification_channels.json"

# Reuse token cache from email_service (module-level singleton)
_zoho_token_cache = {"token": None, "expires_at": 0.0}


# ============================================================
# Zoho API helpers (sync, replicates logic from email_service.py)
# ============================================================

def _load_zoho_api_config() -> Optional[dict]:
    try:
        with open(CHANNELS_PATH, "r") as f:
            channels = json.load(f)
        cfg = channels.get("zoho_api", {})
        if cfg.get("client_id") and cfg.get("client_secret") and cfg.get("refresh_token"):
            return cfg
    except Exception as exc:
        logger.error("[ALERT-EMAIL] zoho config error: %s", exc)
    return None


def _get_access_token(zoho_cfg: dict) -> str:
    global _zoho_token_cache
    if _zoho_token_cache["token"] and time.time() < _zoho_token_cache["expires_at"]:
        return _zoho_token_cache["token"]

    base = zoho_cfg.get("accounts_url", "https://accounts.zoho.eu")
    url = f"{base}/oauth/v2/token"
    params = urlencode({
        "grant_type": "refresh_token",
        "refresh_token": zoho_cfg["refresh_token"],
        "client_id": zoho_cfg["client_id"],
        "client_secret": zoho_cfg["client_secret"],
    }).encode("utf-8")

    ctx = ssl.create_default_context()
    req = Request(url, data=params, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    resp = urlopen(req, timeout=15, context=ctx)
    result = json.loads(resp.read().decode("utf-8"))

    access_token = result.get("access_token")
    if not access_token:
        raise ValueError(f"Zoho token refresh failed: {result}")
    expires_in = result.get("expires_in", 3600)
    _zoho_token_cache["token"] = access_token
    _zoho_token_cache["expires_at"] = time.time() + expires_in - 120
    return access_token


def _get_account_id(zoho_cfg: dict, access_token: str) -> str:
    if zoho_cfg.get("account_id"):
        return str(zoho_cfg["account_id"])
    base = zoho_cfg.get("mail_url", "https://mail.zoho.eu")
    url = f"{base}/api/accounts"
    ctx = ssl.create_default_context()
    req = Request(url, method="GET")
    req.add_header("Authorization", f"Zoho-oauthtoken {access_token}")
    resp = urlopen(req, timeout=15, context=ctx)
    result = json.loads(resp.read().decode("utf-8"))
    accounts = result.get("data", [])
    if not accounts:
        raise ValueError("No Zoho Mail accounts found")
    return str(accounts[0]["accountId"])


def _send_email_sync(to_email: str, subject: str, html_body: str,
                     from_email: str, zoho_cfg: dict) -> bool:
    """Send one email via Zoho Mail REST API (sync, blocking)."""
    access_token = _get_access_token(zoho_cfg)
    account_id = _get_account_id(zoho_cfg, access_token)

    base = zoho_cfg.get("mail_url", "https://mail.zoho.eu")
    url = f"{base}/api/accounts/{account_id}/messages"
    payload = {
        "fromAddress": from_email,
        "toAddress": to_email,
        "subject": subject,
        "content": html_body,
        "mailFormat": "html",
    }
    ctx = ssl.create_default_context()
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Zoho-oauthtoken {access_token}")
    req.add_header("Content-Type", "application/json")
    resp = urlopen(req, timeout=15, context=ctx)
    result = json.loads(resp.read().decode("utf-8"))
    sc = result.get("status", {}).get("code", -1)
    if sc == 200:
        logger.info("[ALERT-EMAIL] sent to %s: %s", to_email, subject)
        return True
    desc = result.get("status", {}).get("description", "unknown")
    logger.error("[ALERT-EMAIL] Zoho API error %s: %s", sc, desc)
    return False


# ============================================================
# Recipient discovery: all active KC users with email
# ============================================================

def get_all_user_emails() -> List[str]:
    """Return email addresses of ALL enabled Keycloak users."""
    try:
        import httpx
        from services.keycloak_admin import ADMIN_API, _headers
        headers = _headers()
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{ADMIN_API}/users", params={"max": 500, "enabled": "true"}, headers=headers)
            resp.raise_for_status()
            users = resp.json()
        emails = []
        for u in users:
            email = u.get("email", "").strip()
            if email and u.get("enabled", True):
                emails.append(email)
        logger.info("[ALERT-EMAIL] Found %d active user emails from KC", len(emails))
        return emails
    except Exception as exc:
        logger.warning("[ALERT-EMAIL] KC user query failed, falling back to notification_channels: %s", exc)
        return _fallback_emails()


def _fallback_emails() -> List[str]:
    """Fall back to notification_channels.json email list."""
    try:
        with open(CHANNELS_PATH, "r") as f:
            channels = json.load(f)
        return channels.get("email", {}).get("to_emails", [])
    except Exception:
        return []


# ============================================================
# Email HTML templates
# ============================================================

RED = chr(0x1F534)
GREEN = chr(0x2705)
ORANGE = chr(0x1F7E0)

def _render_firing_email(alert_name: str, entity_name: str,
                         severity: str, summary: str,
                         metric: str, current_value=None) -> tuple:
    """Return (subject, html_body) for a firing alert email."""
    sev_upper = severity.upper()
    icon = RED if sev_upper == "CRITICAL" else ORANGE
    bg = "#dc2626" if sev_upper == "CRITICAL" else "#f59e0b" if sev_upper == "WARNING" else "#3b82f6"

    subject = f"[{sev_upper}] Rhinometric Alert: {entity_name} - {alert_name}"

    console_url = "https://console-staging.rhinometric.com"
    html = (
        '<div style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;">'
        f'<div style="background:{bg};color:white;padding:18px 24px;border-radius:10px 10px 0 0;">'
        f'<h2 style="margin:0;">{icon} [{sev_upper}] {html_mod.escape(alert_name)}</h2>'
        f'<p style="margin:6px 0 0;opacity:0.9;">Service: <strong>{html_mod.escape(entity_name)}</strong></p>'
        '</div>'
        '<div style="background:#1e293b;color:#e2e8f0;padding:22px 24px;border-radius:0 0 10px 10px;">'
        f'<p><strong>Severity:</strong> {html_mod.escape(sev_upper)}</p>'
        f'<p><strong>Metric:</strong> {html_mod.escape(metric)}</p>'
        f'<p><strong>Summary:</strong> {html_mod.escape(summary)}</p>'
    )
    if current_value is not None:
        html += f'<p><strong>Current Value:</strong> {html_mod.escape(str(current_value))}</p>'

    html += (
        '<hr style="border-color:#334155;margin:16px 0;">'
        '<p style="margin-top:14px;">'
        f'<a href="{console_url}/alerts" style="background:#3b82f6;color:white;padding:10px 22px;'
        'border-radius:6px;text-decoration:none;font-weight:600;">View in Console</a>'
        '</p>'
        '<p style="color:#64748b;font-size:12px;margin-top:18px;">'
        'Rhinometric AI-Powered Observability Platform<br>'
        'This is an automated alert notification. Do not reply to this email.</p>'
        '</div></div>'
    )
    return subject, html


def _render_recovery_email(alert_name: str, entity_name: str,
                           severity: str, duration_str: str) -> tuple:
    """Return (subject, html_body) for a recovery email."""
    subject = f"[RESOLVED] Rhinometric Alert: {entity_name} - {alert_name}"

    console_url = "https://console-staging.rhinometric.com"
    html = (
        '<div style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;">'
        '<div style="background:#16a34a;color:white;padding:18px 24px;border-radius:10px 10px 0 0;">'
        f'<h2 style="margin:0;">{GREEN} [RESOLVED] {html_mod.escape(alert_name)}</h2>'
        f'<p style="margin:6px 0 0;opacity:0.9;">Service: <strong>{html_mod.escape(entity_name)}</strong></p>'
        '</div>'
        '<div style="background:#1e293b;color:#e2e8f0;padding:22px 24px;border-radius:0 0 10px 10px;">'
        f'<p>The alert <strong>{html_mod.escape(alert_name)}</strong> for '
        f'<strong>{html_mod.escape(entity_name)}</strong> has been <span style="color:#4ade80;font-weight:700;">resolved</span>.</p>'
        f'<p><strong>Original Severity:</strong> {html_mod.escape(severity.upper())}</p>'
        f'<p><strong>Duration:</strong> {html_mod.escape(duration_str)}</p>'
        '<hr style="border-color:#334155;margin:16px 0;">'
        '<p style="margin-top:14px;">'
        f'<a href="{console_url}/alerts" style="background:#16a34a;color:white;padding:10px 22px;'
        'border-radius:6px;text-decoration:none;font-weight:600;">View in Console</a>'
        '</p>'
        '<p style="color:#64748b;font-size:12px;margin-top:18px;">'
        'Rhinometric AI-Powered Observability Platform<br>'
        'This is an automated recovery notification. Do not reply to this email.</p>'
        '</div></div>'
    )
    return subject, html


def _format_duration(started_at, ended_at) -> str:
    """Format alert duration as human-readable string."""
    if not started_at or not ended_at:
        return "unknown"
    delta = ended_at - started_at
    total_secs = int(delta.total_seconds())
    if total_secs < 60:
        return f"{total_secs}s"
    elif total_secs < 3600:
        return f"{total_secs // 60}m {total_secs % 60}s"
    else:
        h = total_secs // 3600
        m = (total_secs % 3600) // 60
        return f"{h}h {m}m"


# ============================================================
# Public API: send alert / recovery notifications
# ============================================================

def send_firing_notification(alert_event, current_value=None):
    """
    Send firing alert email to ALL active users.
    Called from _fire_rule_alert() on CREATION path only.
    Checks notification_sent_at to prevent duplicates.
    Runs in a background thread to avoid blocking the eval loop.
    """
    if getattr(alert_event, "notification_sent_at", None):
        logger.info("[ALERT-EMAIL] Already notified for %s, skipping", alert_event.fingerprint)
        return

    def _do():
        try:
            zoho_cfg = _load_zoho_api_config()
            if not zoho_cfg:
                logger.warning("[ALERT-EMAIL] Zoho API not configured, cannot send alert email")
                return

            emails = get_all_user_emails()
            if not emails:
                logger.warning("[ALERT-EMAIL] No recipient emails found")
                return

            metric = alert_event.metric_name or alert_event.labels.get("rule_type", "") if alert_event.labels else ""
            subject, html_body = _render_firing_email(
                alert_name=alert_event.alert_name,
                entity_name=alert_event.entity_name,
                severity=alert_event.severity,
                summary=alert_event.summary or "",
                metric=metric,
                current_value=current_value,
            )
            # Phase 1.5 Rule 4: SERVICE_DOWN gets [URGENT] prefix
            _rule_type = alert_event.labels.get("rule_type", "") if alert_event.labels and isinstance(alert_event.labels, dict) else ""
            if _rule_type == "SERVICE_DOWN":
                subject = "[URGENT] " + subject
            from_addr = zoho_cfg.get("from_address", "rafael.canelon@rhinometric.com")

            sent_count = 0
            for email in emails:
                try:
                    if _send_email_sync(email, subject, html_body, from_addr, zoho_cfg):
                        sent_count += 1
                except Exception as e:
                    logger.error("[ALERT-EMAIL] Failed to send to %s: %s", email, e)

            logger.info("[ALERT-EMAIL] Firing notification sent to %d/%d recipients for %s",
                        sent_count, len(emails), alert_event.alert_name)

        except Exception as exc:
            logger.error("[ALERT-EMAIL] Firing notification error: %s", exc)

    t = threading.Thread(target=_do, name="alert-email-firing", daemon=True)
    t.start()


def send_recovery_notification(alert_event):
    """
    Send recovery email to ALL active users.
    Called from _resolve_recovered_services() and lifecycle_resolve/dismiss.
    Checks recovery_notification_sent_at to prevent duplicates.
    Runs in a background thread.
    """
    if getattr(alert_event, "recovery_notification_sent_at", None):
        logger.info("[ALERT-EMAIL] Recovery already notified for %s, skipping", alert_event.fingerprint)
        return

    # Only send recovery if a firing notification was sent
    if not getattr(alert_event, "notification_sent_at", None):
        logger.info("[ALERT-EMAIL] No firing notification was sent for %s, skip recovery", alert_event.fingerprint)
        return

    def _do():
        try:
            zoho_cfg = _load_zoho_api_config()
            if not zoho_cfg:
                return

            emails = get_all_user_emails()
            if not emails:
                return

            duration_str = _format_duration(alert_event.started_at, alert_event.ended_at)
            subject, html_body = _render_recovery_email(
                alert_name=alert_event.alert_name,
                entity_name=alert_event.entity_name,
                severity=alert_event.severity,
                duration_str=duration_str,
            )
            from_addr = zoho_cfg.get("from_address", "rafael.canelon@rhinometric.com")

            sent_count = 0
            for email in emails:
                try:
                    if _send_email_sync(email, subject, html_body, from_addr, zoho_cfg):
                        sent_count += 1
                except Exception as e:
                    logger.error("[ALERT-EMAIL] Recovery send failed for %s: %s", email, e)

            logger.info("[ALERT-EMAIL] Recovery notification sent to %d/%d for %s",
                        sent_count, len(emails), alert_event.alert_name)

        except Exception as exc:
            logger.error("[ALERT-EMAIL] Recovery notification error: %s", exc)

    t = threading.Thread(target=_do, name="alert-email-recovery", daemon=True)
    t.start()


def resolve_alertmanager_alert(alert_name: str, entity_name: str,
                                severity: str, labels: dict = None):
    """
    Send endsAt to Alertmanager to stop it from repeating the alert.
    Called on resolve/dismiss to tell AM the alert is over.
    
    Phase 3 FIX-3: Added label validation and diagnostic logging.
    """
    def _do():
        try:
            import httpx
            import json
            from config import settings as _cfg
            now = datetime.now(timezone.utc)
            
            # Build labels - prefer passed labels over fallback
            if not labels:
                logger.warning(
                    "[ALERT-EMAIL] resolve_alertmanager_alert called without labels for %s - "
                    "building fallback labels. AM may not match if fire labels differed!",
                    alert_name
                )
                resolve_labels = {
                    "alertname": alert_name,
                    "service_name": entity_name,
                    "severity": severity,
                    "source": "alert_policy",
                    "category": "external-services",
                }
            else:
                resolve_labels = labels
            
            # Log labels for diagnosis
            logger.info(
                "[ALERT-EMAIL] Sending endsAt for %s with labels: %s",
                alert_name, json.dumps(resolve_labels)
            )
            
            payload = [{
                "labels": resolve_labels,
                "endsAt": now.isoformat(),
                "startsAt": (now - __import__("datetime").timedelta(hours=1)).isoformat(),
            }]
            
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(f"{_cfg.ALERTMANAGER_URL}/api/v2/alerts", json=payload)
                if resp.status_code in (200, 201, 202):
                    logger.info(
                        "[ALERT-EMAIL] Successfully sent endsAt to AM for %s: status=%d",
                        alert_name, resp.status_code
                    )
                else:
                    logger.error(
                        "[ALERT-EMAIL] AM rejected endsAt for %s: status=%d, response=%s",
                        alert_name, resp.status_code, resp.text[:200]
                    )
        except Exception as exc:
            logger.warning("[ALERT-EMAIL] endsAt to AM failed (non-fatal): %s", exc)

    t = threading.Thread(target=_do, name="alert-am-resolve", daemon=True)
    t.start()