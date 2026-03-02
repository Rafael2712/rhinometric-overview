"""
Email Service for Rhinometric Console
Uses fastapi-mail with Zoho SMTP for password reset emails
"""

import os
from pathlib import Path
from typing import List, Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
import logging

logger = logging.getLogger("rhinometric.email")

# Global FastMail instance (initialized lazily)
_fm: Optional[FastMail] = None


def get_mail_client() -> FastMail:
    """
    Get FastMail client (lazy initialization).
    This prevents validation errors when email is not configured.
    """
    global _fm
    
    if _fm is None:
        from config import settings
        
        # Email configuration from settings
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        
        _fm = FastMail(conf)
    
    return _fm


async def send_password_reset_email(
    email: str,
    username: str,
    reset_token: str,
    frontend_url: str = None
) -> bool:
    """
    Send password reset email with reset link.
    Uses SMTP config from notification_channels.json (same as send_welcome_email).

    Args:
        email: User's email address
        username: User's username
        reset_token: Password reset token
        frontend_url: Frontend base URL

    Returns:
        True if email sent successfully, False otherwise
    """
    import json
    import aiosmtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        from config import settings

        if not frontend_url:
            frontend_url = settings.FRONTEND_URL

        # ?? Load SMTP config from notification_channels.json ??
        channels_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "notification_channels.json"
        )
        if not os.path.exists(channels_path):
            logger.warning("PASSWORD_RESET_EMAIL_FAILED: notification_channels.json not found")
            return False

        with open(channels_path, "r") as f:
            channels = json.load(f)

        email_cfg = channels.get("email", {})
        if not email_cfg.get("enabled"):
            logger.info("PASSWORD_RESET_EMAIL_FAILED: email channel disabled in notification_channels.json")
            return False

        smtp_host = email_cfg.get("smtp_host", "")
        smtp_port = email_cfg.get("smtp_port", 587)
        smtp_user = email_cfg.get("smtp_username", "")
        smtp_pass = email_cfg.get("smtp_password", "")
        smtp_tls  = email_cfg.get("smtp_require_tls", True)
        from_email = email_cfg.get("from_email", smtp_user)

        if not smtp_host or not smtp_user:
            logger.warning("PASSWORD_RESET_EMAIL_FAILED: SMTP not configured in notification_channels.json")
            return False

        # Construct reset link
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        # HTML email template
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password - Rhinometric</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Rhinometric</h1>
                            <p style="margin: 10px 0 0; color: #e0e7ff; font-size: 14px;">AI-Powered Observability Platform</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px; font-weight: 600;">Reset Your Password</h2>
                            <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.5;">
                                Hello <strong>{username}</strong>,
                            </p>
                            <p style="margin: 0 0 24px; color: #4b5563; font-size: 16px; line-height: 1.5;">
                                We received a request to reset your password. Click the button below to create a new password:
                            </p>
                            <table role="presentation" style="margin: 32px 0; width: 100%;">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_link}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600;">
                                            Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 24px 0 16px; color: #6b7280; font-size: 14px;">Or copy this link: </p>
                            <div style="padding: 12px; background-color: #f3f4f6; border-radius: 4px; border-left: 4px solid #667eea;">
                                <a href="{reset_link}" style="color: #667eea; font-size: 14px; word-break: break-all;">{reset_link}</a>
                            </div>
                            <div style="margin-top: 32px; padding: 16px; background-color: #fef3c7; border-radius: 4px; border-left: 4px solid #f59e0b;">
                                <p style="margin: 0; color: #92400e; font-size: 14px;">
                                    <strong>Security Notice:</strong> This link expires in <strong>1 hour</strong> and can only be used once.
                                </p>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 32px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">&copy; 2026 Rhinometric. All rights reserved.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

        text_body = f"""Reset Your Password - Rhinometric

Hello {username},

We received a request to reset your password.
Click this link: {reset_link}

This link expires in 1 hour and can only be used once.

---
Rhinometric Platform"""

        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset Your Password - Rhinometric"
        msg["From"] = f"Rhinometric Platform <{from_email}>"
        msg["To"] = email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Send via aiosmtplib (same transport as send_welcome_email)
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            start_tls=smtp_tls,
            timeout=15,
        )

        logger.info(f"PASSWORD_RESET_EMAIL_OK: sent to {email} for user {username}")
        return True

    except Exception as e:
        logger.error("PASSWORD_RESET_EMAIL_FAILED: target=%s error=%s", email, str(e))
        return False


def is_smtp_configured() -> bool:
    """
    Quick check: is SMTP configured in notification_channels.json?
    Does NOT test connectivity, just validates config exists.
    Used by forgot-password to decide UX (email vs contact-admin).
    """
    import json
    try:
        channels_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "notification_channels.json"
        )
        with open(channels_path, "r") as f:
            channels = json.load(f)
        email_cfg = channels.get("email", {})
        return bool(
            email_cfg.get("enabled")
            and email_cfg.get("smtp_host")
            and email_cfg.get("smtp_username")
        )
    except Exception:
        return False


async def test_smtp_connection() -> dict:
    """
    Test SMTP connection to Zoho.
    Returns connection status and details.
    """
    try:
        from config import settings
        
        # Get mail client
        fm = get_mail_client()
        
        # Try to create a test message
        test_message = MessageSchema(
            subject="SMTP Connection Test - Rhinometric",
            recipients=[settings.MAIL_FROM],  # Send to self
            body="This is a test email to verify SMTP connectivity.",
            subtype=MessageType.plain
        )
        
        # Attempt to send (will fail if SMTP not configured)
        await fm.send_message(test_message)
        
        return {
            "status": "success",
            "message": "SMTP connection successful",
            "server": settings.MAIL_SERVER,
            "port": settings.MAIL_PORT,
            "from": settings.MAIL_FROM,
            "starttls": settings.MAIL_STARTTLS
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "server": settings.MAIL_SERVER,
            "port": settings.MAIL_PORT,
            "from": settings.MAIL_FROM
        }


async def send_welcome_email(
    email: str,
    username: str,
    password: str,
    full_name: str = None,
    roles: list = None,
    login_url: str = None,
) -> bool:
    """
    Send welcome email to newly created user with their credentials.
    Uses SMTP config from notification_channels.json (configured via Settings UI).
    Falls back gracefully if SMTP is not configured or unreachable.
    
    Args:
        email: New user's email address
        username: New user's username
        password: Temporary password (user must change on first login)
        full_name: User's full name (optional)
        roles: List of assigned role names
        login_url: URL to access the platform
    
    Returns:
        True if email sent successfully, False otherwise
    """
    import json
    import aiosmtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        # Load SMTP config from notification_channels.json
        channels_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "notification_channels.json")
        if not os.path.exists(channels_path):
            logger.warning("notification_channels.json not found — skipping welcome email")
            return False

        with open(channels_path, "r") as f:
            channels = json.load(f)

        email_cfg = channels.get("email", {})
        if not email_cfg.get("enabled"):
            logger.info("Email channel is disabled — skipping welcome email")
            return False

        smtp_host = email_cfg.get("smtp_host", "")
        smtp_port = email_cfg.get("smtp_port", 587)
        smtp_user = email_cfg.get("smtp_username", "")
        smtp_pass = email_cfg.get("smtp_password", "")
        smtp_tls  = email_cfg.get("smtp_require_tls", True)
        from_email = email_cfg.get("from_email", smtp_user)

        if not smtp_host or not smtp_user:
            logger.warning("SMTP not configured — skipping welcome email")
            return False

        display_name = full_name or username
        roles_str = ", ".join(roles) if roles else "VIEWER"
        platform_url = login_url or "http://rhinometric.local"

        # HTML email body
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Rhinometric</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Rhinometric</h1>
                            <p style="margin: 10px 0 0; color: #e0e7ff; font-size: 14px;">AI-Powered Observability Platform</p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px; font-weight: 600;">Welcome to Rhinometric!</h2>

                            <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.5;">
                                Hello <strong>{display_name}</strong>,
                            </p>

                            <p style="margin: 0 0 24px; color: #4b5563; font-size: 16px; line-height: 1.5;">
                                Your account has been created on the Rhinometric observability platform.
                                Below are your login credentials. <strong>You will be required to change your password on first login.</strong>
                            </p>

                            <!-- Credentials Box -->
                            <div style="padding: 24px; background-color: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 24px;">
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px; width: 120px;">Username:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 16px; font-weight: 600;">{username}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Password:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 16px; font-weight: 600; font-family: 'Courier New', monospace;">{password}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Role(s):</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 16px; font-weight: 600;">{roles_str}</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Login Button -->
                            <table role="presentation" style="margin: 32px 0; width: 100%;">
                                <tr>
                                    <td align="center">
                                        <a href="{platform_url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                            Login to Rhinometric
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <div style="margin-top: 32px; padding: 16px; background-color: #fef3c7; border-radius: 4px; border-left: 4px solid #f59e0b;">
                                <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.5;">
                                    <strong>Security Notice:</strong> Please change your password immediately after your first login. Do not share your credentials with anyone.
                                </p>
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0 0 8px; color: #6b7280; font-size: 12px; text-align: center;">
                                This is an automated message from Rhinometric Platform.
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
                                &copy; 2026 Rhinometric. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

        # Plain text fallback
        text_body = f"""Welcome to Rhinometric!

Hello {display_name},

Your account has been created on the Rhinometric observability platform.

Your login credentials:
  Username: {username}
  Password: {password}
  Role(s):  {roles_str}

Login URL: {platform_url}

IMPORTANT: You must change your password on first login.
Do not share your credentials with anyone.

---
Rhinometric Platform
(c) 2026 Rhinometric. All rights reserved.
"""

        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to Rhinometric Platform - Your Account Has Been Created"
        msg["From"] = f"Rhinometric Platform <{from_email}>"
        msg["To"] = email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Send via aiosmtplib (already installed as fastapi-mail dependency)
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            start_tls=smtp_tls,
            timeout=15,
        )

        logger.info(f"Welcome email sent to {email} for user {username}")
        return True

    except Exception as e:
        logger.error("WELCOME_EMAIL_FAILED: target=%s error=%s", email, str(e))
        return False
