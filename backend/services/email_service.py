"""
Email Service for Rhinometric Console
--------------------------------------
Single source of truth: /app/data/notification_channels.json

Transport strategy (automatic fallback):
  1. SMTP (Port 587 STARTTLS / Port 465 SMTPS)  – preferred
  2. Zoho Mail REST API over HTTPS (Port 443)    – fallback when SMTP ports are blocked

Public URL resolution (for links in emails):
  Priority 1: RHINO_PUBLIC_CONSOLE_URL env var  (recommended)
  Priority 2: FRONTEND_URL env var              (legacy)
  Fallback:   http://localhost:3002

Environment-aware email subjects:
  If RHINO_ENV is set and != "production", subjects are prefixed with [STAGING], [DEV], etc.

Logging: all operations under [EMAIL] prefix.
"""

import os, json, socket, asyncio, logging, ssl, time
from typing import Optional, Tuple, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
import aiosmtplib

logger = logging.getLogger("rhinometric.email")

CHANNELS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "notification_channels.json",
)

# In-memory cache for Zoho access token
_zoho_token_cache: Dict = {"token": None, "expires_at": 0}


# ####################################################################
# PUBLIC URL + ENVIRONMENT HELPERS
# ####################################################################

def _get_public_base_url() -> str:
    """
    Resolve the public console URL for links embedded in emails.

    Priority:
      1. RHINO_PUBLIC_CONSOLE_URL  (explicitly set per environment)
      2. FRONTEND_URL               (legacy / backward-compatible)
      3. http://localhost:3002       (safe dev fallback)
    """
    url = os.getenv("RHINO_PUBLIC_CONSOLE_URL") or os.getenv("FRONTEND_URL", "")
    if not url:
        try:
            from config import settings as _s
            url = _s.FRONTEND_URL
        except Exception:
            url = "http://localhost:3002"
    return url.rstrip("/")


def _env_subject_prefix() -> str:
    """
    If RHINO_ENV is set and is NOT 'production', return a prefix like '[STAGING] '.
    Otherwise return empty string — production emails are clean.
    """
    env = os.getenv("RHINO_ENV", "").strip().lower()
    if env and env != "production":
        return f"[{env.upper()}] "
    return ""


# ####################################################################
# CONFIG LOADERS
# ####################################################################

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


def _load_zoho_api_config() -> Optional[dict]:
    """Return zoho_api block from notification_channels.json or None."""
    try:
        with open(CHANNELS_PATH, "r") as f:
            channels = json.load(f)
        cfg = channels.get("zoho_api", {})
        if cfg.get("client_id") and cfg.get("client_secret") and cfg.get("refresh_token"):
            return cfg
    except Exception as exc:
        logger.error("[EMAIL] zoho-api-config-error: %s", exc)
    return None


def is_smtp_configured() -> bool:
    """Quick check: is SMTP configured (no network test)."""
    return _load_email_config() is not None


# ####################################################################
# TCP PRE-CHECK
# ####################################################################

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
      1. SMTP config + TCP reachable?
      2. Zoho API configured?
    Returns (available, reason).
    """
    cfg = _load_email_config()
    if cfg is None:
        zoho_cfg = _load_zoho_api_config()
        if zoho_cfg:
            return True, "zoho-api-configured (smtp not configured)"
        return False, "smtp-not-configured"

    host = cfg["smtp_host"]
    port = cfg.get("smtp_port", 587)
    ok, reason = _tcp_check(host, port)
    if not ok:
        # Try port 465 as fallback
        if port != 465:
            ok2, reason2 = _tcp_check(host, 465)
            if ok2:
                return True, f"tcp-ok-fallback-465 (primary {port} blocked)"
        # SMTP blocked — check Zoho API fallback
        zoho_cfg = _load_zoho_api_config()
        if zoho_cfg:
            return True, f"zoho-api-fallback (smtp {reason})"
        return False, reason
    return True, "smtp-available"


# ####################################################################
# ZOHO MAIL API OVER HTTPS (FALLBACK)
# ####################################################################

def _get_zoho_access_token(zoho_cfg: dict) -> str:
    """Exchange refresh_token for a fresh access_token. Caches result."""
    global _zoho_token_cache
    if _zoho_token_cache["token"] and time.time() < _zoho_token_cache["expires_at"]:
        return _zoho_token_cache["token"]

    base = zoho_cfg.get("accounts_url", "https://accounts.zoho.eu")
    token_url = f"{base}/oauth/v2/token"
    params = urlencode({
        "grant_type": "refresh_token",
        "refresh_token": zoho_cfg["refresh_token"],
        "client_id": zoho_cfg["client_id"],
        "client_secret": zoho_cfg["client_secret"],
    }).encode("utf-8")

    ctx = ssl.create_default_context()
    req = Request(token_url, data=params, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    resp = urlopen(req, timeout=15, context=ctx)
    result = json.loads(resp.read().decode("utf-8"))

    access_token = result.get("access_token")
    if not access_token:
        raise ValueError(f"Zoho token refresh failed: {result}")

    expires_in = result.get("expires_in", 3600)
    _zoho_token_cache["token"] = access_token
    _zoho_token_cache["expires_at"] = time.time() + expires_in - 120

    logger.info("[EMAIL] Zoho API token refreshed, expires_in=%ds", expires_in)
    return access_token


def _get_zoho_account_id(zoho_cfg: dict, access_token: str) -> str:
    """Discover Zoho Mail account ID (or use cached value from config)."""
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

    from_email = zoho_cfg.get("from_email", "")
    for acc in accounts:
        if from_email and acc.get("primaryEmailAddress") == from_email:
            account_id = str(acc["accountId"])
            logger.info("[EMAIL] Zoho account matched by email: %s", account_id)
            _cache_zoho_account_id(account_id)
            return account_id

    account_id = str(accounts[0]["accountId"])
    logger.info("[EMAIL] Zoho account auto-selected: %s", account_id)
    _cache_zoho_account_id(account_id)
    return account_id


def _cache_zoho_account_id(account_id: str):
    """Persist discovered account_id to config for faster next lookup."""
    try:
        with open(CHANNELS_PATH, "r") as f:
            channels = json.load(f)
        if "zoho_api" in channels:
            channels["zoho_api"]["account_id"] = account_id
            with open(CHANNELS_PATH, "w") as f:
                json.dump(channels, f, indent=2)
    except Exception:
        pass  # Non-critical — will rediscover next time


async def _send_via_zoho_api(
    to_email: str, subject: str, html_body: str,
    from_email: str, zoho_cfg: dict,
) -> bool:
    """Send email via Zoho Mail REST API (HTTPS port 443)."""
    loop = asyncio.get_event_loop()

    access_token = await loop.run_in_executor(None, _get_zoho_access_token, zoho_cfg)
    account_id = await loop.run_in_executor(None, _get_zoho_account_id, zoho_cfg, access_token)

    base = zoho_cfg.get("mail_url", "https://mail.zoho.eu")
    url = f"{base}/api/accounts/{account_id}/messages"
    payload = {
        "fromAddress": from_email,
        "toAddress": to_email,
        "subject": subject,
        "content": html_body,
        "mailFormat": "html",
    }

    def _do_send():
        ctx = ssl.create_default_context()
        body = json.dumps(payload).encode("utf-8")
        req = Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Zoho-oauthtoken {access_token}")
        req.add_header("Content-Type", "application/json")
        resp = urlopen(req, timeout=15, context=ctx)
        return json.loads(resp.read().decode("utf-8"))

    result = await loop.run_in_executor(None, _do_send)
    status_code = result.get("status", {}).get("code", -1)
    if status_code == 200:
        logger.info("[EMAIL] Zoho API send OK to=%s", _mask_email(to_email))
        return True
    else:
        desc = result.get("status", {}).get("description", "unknown")
        logger.error("[EMAIL] Zoho API send failed code=%s desc=%s", status_code, desc)
        raise RuntimeError(f"Zoho API error: {status_code} {desc}")


# ####################################################################
# SMTP SEND + FALLBACK LOGIC
# ####################################################################

async def _send_mime(msg: MIMEMultipart, cfg: dict) -> bool:
    """
    Attempt SMTP delivery; if TCP-blocked, auto-fallback to Zoho API.
    """
    host = cfg["smtp_host"]
    port = cfg.get("smtp_port", 587)
    user = cfg["smtp_username"]
    pwd  = cfg.get("smtp_password", "")
    use_tls = cfg.get("smtp_require_tls", True)

    send_kwargs = dict(
        hostname=host, port=port, username=user, password=pwd, timeout=15,
    )

    # TCP pre-check primary port
    tcp_ok, tcp_reason = _tcp_check(host, port, timeout=5)
    if not tcp_ok and port != 465:
        tcp_ok2, _ = _tcp_check(host, 465, timeout=5)
        if tcp_ok2:
            port = 465
            send_kwargs["port"] = 465
            tcp_ok = True
            logger.info("[EMAIL] primary port blocked, falling back to 465 SMTPS")

    # If SMTP totally blocked → try Zoho API
    if not tcp_ok:
        zoho_cfg = _load_zoho_api_config()
        if zoho_cfg:
            logger.info("[EMAIL] SMTP blocked (%s), routing via Zoho API (HTTPS)", tcp_reason)
            to_email = msg["To"]
            subject = msg["Subject"]
            from_email = cfg.get("from_email", user)
            html_body = _extract_html(msg)
            return await _send_via_zoho_api(to_email, subject, html_body, from_email, zoho_cfg)
        else:
            raise ConnectionError(
                f"SMTP blocked ({tcp_reason}) and Zoho API fallback not configured. "
                "Add zoho_api section to notification_channels.json."
            )

    # SMTP path — ports are reachable
    if port == 465:
        send_kwargs["use_tls"] = True
        send_kwargs.pop("start_tls", None)
    else:
        send_kwargs["start_tls"] = use_tls
        send_kwargs.pop("use_tls", None)

    await aiosmtplib.send(msg, **send_kwargs)
    return True


def _extract_html(msg: MIMEMultipart) -> str:
    """Extract HTML body from MIMEMultipart, fall back to plain text."""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            return part.get_payload(decode=True).decode("utf-8")
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            return part.get_payload(decode=True).decode("utf-8")
    return ""


def _mask_email(email: str) -> str:
    """Mask email for logs: user@domain -> u***@domain"""
    parts = email.split("@")
    if len(parts) == 2:
        local = parts[0]
        return f"{local[0]}***@{parts[1]}" if local else f"***@{parts[1]}"
    return "***"


# ####################################################################
# PASSWORD RESET EMAIL
# ####################################################################

async def send_password_reset_email(
    email: str,
    username: str,
    reset_token: str,
    frontend_url: str = None,
) -> bool:
    """Send password-reset email. Returns True on success."""
    try:
        # ── Resolve public URL ───────────────────────
        base_url = _get_public_base_url()
        if frontend_url:
            # Caller override (backward compat), but env var still wins
            rhino_url = os.getenv("RHINO_PUBLIC_CONSOLE_URL")
            if rhino_url:
                base_url = rhino_url.rstrip("/")
            else:
                base_url = frontend_url.rstrip("/")

        reset_link = f"{base_url}/reset-password?token={reset_token}"
        prefix = _env_subject_prefix()
        subject = f"{prefix}Reset Your Password - Rhinometric"

        logger.info("[EMAIL] reset link built: %s (base_url=%s)", reset_link[:60] + "...", base_url)

        cfg = _load_email_config()
        if cfg is None:
            # Try pure Zoho API (no SMTP config at all)
            zoho_cfg = _load_zoho_api_config()
            if zoho_cfg:
                from_email = zoho_cfg.get("from_email", "noreply@rhinometric.com")
                html = _reset_html(username, reset_link)
                await _send_via_zoho_api(email, subject, html, from_email, zoho_cfg)
                logger.info("[EMAIL] RESET sent (zoho-api) target=%s", _mask_email(email))
                return True
            logger.warning("[EMAIL] RESET skip: smtp not configured, zoho api not configured")
            return False

        from_email = cfg.get("from_email", cfg["smtp_username"])
        html = _reset_html(username, reset_link)
        text = f"Hello {username},\nReset your password: {reset_link}\nExpires in 1 hour."

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
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


# ####################################################################
# WELCOME EMAIL
# ####################################################################

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
        # ── Resolve public URL ───────────────────────
        base_url = _get_public_base_url()
        # If caller passed login_url, env var still takes priority
        if login_url:
            rhino_url = os.getenv("RHINO_PUBLIC_CONSOLE_URL")
            if rhino_url:
                base_url = rhino_url.rstrip("/")
            else:
                base_url = login_url.rstrip("/")

        prefix = _env_subject_prefix()
        subject = f"{prefix}Welcome to Rhinometric Platform"

        display = full_name or username
        roles_str = ", ".join(roles) if roles else "VIEWER"

        cfg = _load_email_config()
        if cfg is None:
            zoho_cfg = _load_zoho_api_config()
            if zoho_cfg:
                from_email = zoho_cfg.get("from_email", "noreply@rhinometric.com")
                html = _welcome_html(display, username, password, roles_str, base_url)
                await _send_via_zoho_api(email, subject, html, from_email, zoho_cfg)
                logger.info("[EMAIL] WELCOME sent (zoho-api) target=%s user=%s", _mask_email(email), username)
                return True
            logger.warning("[EMAIL] WELCOME skip: smtp not configured, zoho api not configured")
            return False

        from_email = cfg.get("from_email", cfg["smtp_username"])
        html = _welcome_html(display, username, password, roles_str, base_url)
        text = (
            f"Welcome {display}!\n"
            f"Username: {username}\nPassword: {password}\nRole: {roles_str}\n"
            f"Login: {base_url}\nYou must change your password on first login."
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
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


# ####################################################################
# HTML TEMPLATES
# ####################################################################
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
