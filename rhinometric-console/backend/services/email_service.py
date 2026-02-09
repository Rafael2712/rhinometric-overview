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
    email: EmailStr,
    username: str,
    reset_token: str,
    frontend_url: str = None
) -> bool:
    """
    Send password reset email with reset link.
    
    Args:
        email: User's email address
        username: User's username
        reset_token: Password reset token
        frontend_url: Frontend base URL (from settings if not provided)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        from config import settings
        
        if not frontend_url:
            frontend_url = settings.FRONTEND_URL
        
        # Get mail client
        fm = get_mail_client()
        
        # Construct reset link
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
        # HTML email template
        html_body = f"""
<!DOCTYPE html>
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
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px; font-weight: 600;">Reset Your Password</h2>
                            
                            <p style="margin: 0 0 16px; color: #4b5563; font-size: 16px; line-height: 1.5;">
                                Hello <strong>{username}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 24px; color: #4b5563; font-size: 16px; line-height: 1.5;">
                                We received a request to reset your password for your Rhinometric account. Click the button below to create a new password:
                            </p>
                            
                            <table role="presentation" style="margin: 32px 0; width: 100%;">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_link}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                            Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 24px 0 16px; color: #6b7280; font-size: 14px; line-height: 1.5;">
                                Or copy and paste this link into your browser:
                            </p>
                            
                            <div style="padding: 12px; background-color: #f3f4f6; border-radius: 4px; border-left: 4px solid #667eea;">
                                <a href="{reset_link}" style="color: #667eea; font-size: 14px; word-break: break-all; text-decoration: none;">
                                    {reset_link}
                                </a>
                            </div>
                            
                            <div style="margin-top: 32px; padding: 16px; background-color: #fef3c7; border-radius: 4px; border-left: 4px solid #f59e0b;">
                                <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.5;">
                                    ⚠️ <strong>Security Notice:</strong> This link will expire in <strong>1 hour</strong> and can only be used once. If you didn't request this password reset, please ignore this email or contact your administrator.
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
                                © 2026 Rhinometric. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        # Plain text version (fallback)
        text_body = f"""
Reset Your Password - Rhinometric

Hello {username},

We received a request to reset your password for your Rhinometric account.

Click this link to reset your password:
{reset_link}

This link will expire in 1 hour and can only be used once.

If you didn't request this password reset, please ignore this email or contact your administrator.

---
Rhinometric Platform
© 2026 Rhinometric. All rights reserved.
        """
        
        # Create message
        message = MessageSchema(
            subject="Reset Your Password - Rhinometric Platform",
            recipients=[email],
            body=text_body,
            html=html_body,
            subtype=MessageType.html
        )
        
        # Send email
        await fm.send_message(message)
        
        logger.info(f"✅ Password reset email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send password reset email to {email}: {str(e)}")
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
