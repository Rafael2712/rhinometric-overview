"""
Email Service for Rhinometric Console
?????????????????????????????????????
Single source of truth: /app/data/notification_channels.json
Supports:
  - Port 587 (STARTTLS)
  - Port 465 (implicit SSL / SMTPS)
  - TCP pre-check to fail-fast when ports are blocked
"""

import os, json, socket, asyncio, logging
from typing import Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

logger = logging.getLogger("rhinometric.email")

CHANNELS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "notification_channels.json",
)


# ???????????????????????????????????????????????????
# CONFIG LOADER
# ???????????????????????????????????????????????????
def _load_email_config() -> Optional[dict]:
    """Return email block from notification_channels.json or None."""
    try:
        with open(CHANNELS_PATH, "r") as f:
            channels = json.load(f)
        cfg = channels.get("email", {})
        if cfg.get("enabled") and cfg.get("smtp_host") and cfg.get("smtp_username"):
            return cfg
    except Exception as exc:
        logger.error("[EMAIL] config-load-error: %s", exc)
    return None


def is_smtp_configured() -> bool:
    """Quick check: is SMTP configured (no network test)."""
    return _load_email_config() is not None


# ???????????????????????????????????????????????????
# TCP PRE-CHECK
# ???????????????????????????????????????????????????
def _tcp_check(host: str, port: int, timeout: float = 4.0) -> Tuple[bool, str]:
    """
    Attempt a raw TCP connect.  Returns (ok, reason).
    This is fast and tells us if the firewall blocks the port.
    """
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True, "tcp-ok"
    except socket.timeout:
        return False, f"tcp-timeout host={host} port={port}"
    except OSError as exc:
        return False, f"tcp-error host={host} port={port} err={exc}"


def is_email_service_available() -> Tuple[bool, str]:
    """
    Full availability probe:
      1. Config present?
      2. TCP reachable?
    Returns (available, reason).
    """
    cfg = _load_email_config()
    if cfg is None:
        return False, "smtp-not-configured"
    host = cfg["smtp_host"]
    port = cfg.get("smtp_port", 587)
    ok, reason = _tcp_check(host, port)
    if not ok:
        # Try port 465 as fallback if 587 is blocked
        if port != 465:
            ok2, reason2 = _tcp_check(host, 465)
            if ok2:
                return True, f"tcp-ok-fallback-465 (primary {port} blocked)"
        return False, reason
    return True, "smtp-available"


# ???????????????????????????????????????????????????
# SEND HELPERS
# ???????????????????????????????????????????????????
async def _send_mime(msg: MIMEMultipart, cfg: dict) -> bool:
    """
    Low-level send via aiosmtplib.
    Detects port to choose STARTTLS vs implicit-SSL.
    """
    host = cfg["smtp_host"]
    port = cfg.get("smtp_port", 587)
    user = cfg["smtp_username"]
    pwd  = cfg.get("smtp_password", "")
    use_tls = cfg.get("smtp_require_tls", True)

    # Decide send strategy based on port
    send_kwargs = dict(
        hostname=host,
        port=port,
        username=user,
        password=pwd,
        timeout=15,
    )

    # TCP pre-check primary port
    tcp_ok, tcp_reason = _tcp_check(host, port, timeout=5)
    if not tcp_ok and port != 465:
        # fallback 465
        tcp_ok2, _ = _tcp_check(host, 465, timeout=5)
        if tcp_ok2:
            port = 465
            send_kwargs["port"] = 465
            logger.info("[EMAIL] primary port blocked, falling back to 465 SMTPS")

    if port == 465:
        send_kwargs["use_tls"] = True      # implicit SSL
        send_kwargs.pop("start_tls", None)
    else:
        send_kwargs["start_tls"] = use_tls
        send_kwargs.pop("use_tls", None)

    await aiosmtplib.send(msg, **send_kwargs)
    return True


def _mask_email(email: str) -> str:
    """Mask email for logs: user@domain -> u***@domain"""
    parts = email.split("@")
    if len(parts) == 2:
        local = parts[0]
        return f"{local[0]}***@{parts[1]}" if local else f"***@{parts[1]}"
    return "***"


# ???????????????????????????????????????????????????
# PASSWORD RESET EMAIL
# ???????????????????????????????????????????????????
async def send_password_reset_email(
    email: str,
    username: str,
    reset_token: str,
    frontend_url: str = None,
) -> bool:
    """Send password-reset email. Returns True on success."""
    try:
        from config import settings as app_settings
        if not frontend_url:
            frontend_url = app_settings.FRONTEND_URL

        cfg = _load_email_config()
        if cfg is None:
            logger.warning("[EMAIL] RESET skip: smtp not configured")
            return False

        from_email = cfg.get("from_email", cfg["smtp_username"])
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        html = _reset_html(username, reset_link)
        text = f"Hello {username},\nReset your password: {reset_link}\nExpires in 1 hour."

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset Your Password - Rhinometric"
        msg["From"] = f"Rhinometric <{from_email}>"
        msg["To"] = email
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        await _send_mime(msg, cfg)
        logger.info("[EMAIL] RESET sent target=%s", _mask_email(email))
        return True

    except Exception as exc:
        logger.error("[EMAIL] RESET failed target=%s err=%s", _mask_email(email), exc)
        return False


# ???????????????????????????????????????????????????
# WELCOME EMAIL
# ???????????????????????????????????????????????????
async def send_welcome_email(
    email: str,
    username: str,
    password: str,
    full_name: str = None,
    roles: list = None,
    login_url: str = None,
) -> bool:
    """Send welcome email with temporary credentials. Returns True on success."""
    try:
        cfg = _load_email_config()
        if cfg is None:
            logger.warning("[EMAIL] WELCOME skip: smtp not configured")
            return False

        from_email = cfg.get("from_email", cfg["smtp_username"])
        display = full_name or username
        roles_str = ", ".join(roles) if roles else "VIEWER"
        url = login_url or "http://rhinometric.local"

        html = _welcome_html(display, username, password, roles_str, url)
        text = (
            f"Welcome {display}!\n"
            f"Username: {username}\nPassword: {password}\nRole: {roles_str}\n"
            f"Login: {url}\nYou must change your password on first login."
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to Rhinometric Platform"
        msg["From"] = f"Rhinometric <{from_email}>"
        msg["To"] = email
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        await _send_mime(msg, cfg)
        logger.info("[EMAIL] WELCOME sent target=%s user=%s", _mask_email(email), username)
        return True

    except Exception as exc:
        logger.error("[EMAIL] WELCOME failed target=%s err=%s", _mask_email(email), exc)
        return False


# ???????????????????????????????????????????????????
# HTML TEMPLATES
# ???????????????????????????????????????????????????
_HEADER = """<tr><td style="padding:40px 40px 20px;text-align:center;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:8px 8px 0 0;"><h1 style="margin:0;color:#fff;font-size:28px">Rhinometric</h1><p style="margin:10px 0 0;color:#e0e7ff;font-size:14px">AI-Powered Observability Platform</p></td></tr>"""
_FOOTER = """<tr><td style="padding:24px 40px;background:#f9fafb;border-top:1px solid #e5e7eb;border-radius:0 0 8px 8px;text-align:center;color:#9ca3af;font-size:12px">&copy; 2026 Rhinometric. All rights reserved.</td></tr>"""
_WRAP = '<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:#f5f5f5"><table style="width:100%;background:#f5f5f5"><tr><td align="center" style="padding:40px 0"><table style="width:600px;max-width:100%;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1)">'


def _reset_html(username, reset_link):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
{_WRAP}
{_HEADER}
<tr><td style="padding:40px">
<h2 style="color:#1f2937;font-size:24px">Reset Your Password</h2>
<p style="color:#4b5563">Hello <strong>{username}</strong>,</p>
<p style="color:#4b5563">Click below to reset your password:</p>
<p style="text-align:center;margin:32px 0"><a href="{reset_link}" style="display:inline-block;padding:16px 32px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;text-decoration:none;border-radius:6px;font-weight:600">Reset Password</a></p>
<div style="padding:12px;background:#f3f4f6;border-radius:4px;border-left:4px solid #667eea"><a href="{reset_link}" style="color:#667eea;font-size:14px;word-break:break-all">{reset_link}</a></div>
<div style="margin-top:24px;padding:12px;background:#fef3c7;border-radius:4px;border-left:4px solid #f59e0b"><p style="margin:0;color:#92400e;font-size:14px"><strong>Security:</strong> Expires in 1 hour, single use.</p></div>
</td></tr>
{_FOOTER}
</table></td></tr></table></body></html>"""


def _welcome_html(display, username, password, roles_str, url):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
{_WRAP}
{_HEADER}
<tr><td style="padding:40px">
<h2 style="color:#1f2937;font-size:24px">Welcome to Rhinometric!</h2>
<p style="color:#4b5563">Hello <strong>{display}</strong>, your account has been created.</p>
<div style="padding:20px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;margin:20px 0">
<table style="width:100%">
<tr><td style="padding:6px 0;color:#6b7280;width:100px">Username:</td><td style="font-weight:600;color:#1f2937">{username}</td></tr>
<tr><td style="padding:6px 0;color:#6b7280">Password:</td><td style="font-weight:600;color:#1f2937;font-family:monospace">{password}</td></tr>
<tr><td style="padding:6px 0;color:#6b7280">Role:</td><td style="font-weight:600;color:#1f2937">{roles_str}</td></tr>
</table>
</div>
<p style="text-align:center"><a href="{url}" style="display:inline-block;padding:16px 32px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;text-decoration:none;border-radius:6px;font-weight:600">Login to Rhinometric</a></p>
<div style="margin-top:24px;padding:12px;background:#fef3c7;border-radius:4px;border-left:4px solid #f59e0b"><p style="margin:0;color:#92400e;font-size:14px"><strong>Security:</strong> Change your password on first login. Do not share credentials.</p></div>
</td></tr>
{_FOOTER}
</table></td></tr></table></body></html>"""
