# Annual License Endpoint - Simplified for existing database schema

from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import secrets

class AnnualLicenseRequest(BaseModel):
    customer_name: str
    client_email: str
    client_company: str

def send_annual_license_email_simple(license_key: str, recipient_email: str, expires_at):
    """Send Annual license email with Rhinometric logo SVG"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Get SMTP config
    smtp_host = os.getenv("SMTP_HOST", "smtp.zoho.eu")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "rafael.canelon@rhinometric.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", "rafael.canelon@rhinometric.com")
    server_base_url = os.getenv("SERVER_BASE_URL", "http://54.197.192.198:8090")
    
    if not smtp_password:
        print("⚠️ SMTP password not configured")
        return False
    
    # Calculate expiration info
    expires_at_str = expires_at.strftime("%B %d, %Y")
    days_remaining = (expires_at - datetime.utcnow()).days
    
    # Unique ID for SVG gradient to avoid email client conflicts
    unique_id = license_key[-8:]
    
    # HTML Email Template with SVG Logo
    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 32px; }}
        .content {{ background: #f9fafb; padding: 30px; }}
        .license-box {{ background: white; padding: 25px; margin: 20px 0;
                       border-left: 4px solid #10b981; border-radius: 8px; 
                       box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .license-key {{ background: #f3f4f6; padding: 15px; 
                       font-family: 'Courier New', monospace;
                       font-size: 18px; font-weight: bold; 
                       border-radius: 6px; word-break: break-all; 
                       margin: 15px 0; border: 2px dashed #667eea; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
        .info-item {{ background: #f9fafb; padding: 12px; border-radius: 6px; }}
        .info-item strong {{ display: block; color: #6b7280; font-size: 12px; 
                             text-transform: uppercase; margin-bottom: 5px; }}
        .info-item span {{ color: #1e3a8a; font-size: 16px; font-weight: 600; }}
        .download-section {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                             padding: 30px; border-radius: 8px; margin: 25px 0; text-align: center; }}
        .btn {{ display: inline-block; padding: 14px 28px; background: white; color: #10b981; 
               text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;
               box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .features {{ background: white; padding: 25px; border-radius: 8px; margin: 20px 0; }}
        .features ul {{ list-style: none; padding: 0; margin: 10px 0; }}
        .features li {{ padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
        .warning-box {{ background: #fffbeb; border: 2px solid #fcd34d;
                       padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .support-box {{ text-align: center; margin: 25px 0; padding: 20px;
                       background: white; border-radius: 8px; }}
        .footer {{ background: #1f2937; color: #9ca3af; padding: 25px; 
                  text-align: center; font-size: 12px; }}
        .highlight {{ color: #10b981; font-weight: bold; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Rhinometric Logo Section -->
        <div style="text-align: center; padding: 30px 20px; background: #1e293b;">
            <div style="width: 120px; height: 120px; margin: 0 auto 15px auto;">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="120" height="120" style="display: block;">
                  <defs>
                    <linearGradient id="rhino{unique_id}" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                    </linearGradient>
                  </defs>
                  <path d="M 150,200 Q 140,160 160,130 Q 180,100 220,100 Q 260,100 280,130 Q 300,160 290,200 Q 285,240 270,260 Q 250,280 220,280 Q 190,280 170,260 Q 155,240 150,200 Z" 
                        fill="none" stroke="url(#rhino{unique_id})" stroke-width="8" stroke-linecap="round"/>
                  <path d="M 240,120 Q 250,80 260,60 Q 265,50 270,55 Q 275,60 270,70 Q 265,90 260,110" 
                        fill="none" stroke="url(#rhino{unique_id})" stroke-width="6" stroke-linecap="round"/>
                  <path d="M 220,130 Q 222,110 225,100 Q 227,95 230,98 Q 232,102 230,108" 
                        fill="none" stroke="url(#rhino{unique_id})" stroke-width="5" stroke-linecap="round"/>
                  <circle cx="200" cy="160" r="6" fill="#667eea"/>
                  <path d="M 160,140 Q 145,135 140,145 Q 135,155 145,160 Q 155,165 160,155" 
                        fill="none" stroke="url(#rhino{unique_id})" stroke-width="5" stroke-linecap="round"/>
                  <circle cx="250" cy="190" r="4" fill="#667eea"/>
                </svg>
            </div>
            <p style="color: #f3f4f6; margin: 0 0 8px 0; font-size: 28px; font-weight: 600; letter-spacing: 3px;">RHINOMETRIC</p>
            <p style="color: #94a3b8; margin: 0; font-size: 13px; letter-spacing: 1px;">Enterprise Observability Platform</p>
        </div>
        
        <div class="header">
            <h1>🔑 Your Rhinometric Annual License</h1>
            <p>On-Premise Observability Platform</p>
        </div>

        <div class="content">
            <div class="license-box">
                <h2 style="color: #1e3a8a; margin-top: 0;">📋 License Information</h2>
                <p style="margin-bottom: 10px;"><strong>License Key:</strong></p>
                <div class="license-key">{license_key}</div>
                <div class="info-grid">
                    <div class="info-item">
                        <strong>Type</strong>
                        <span>Annual License</span>
                    </div>
                    <div class="info-item">
                        <strong>Max Hosts</strong>
                        <span>20 hosts</span>
                    </div>
                    <div class="info-item">
                        <strong>Expires</strong>
                        <span>{expires_at_str}</span>
                    </div>
                    <div class="info-item">
                        <strong>Days Remaining</strong>
                        <span class="highlight">{days_remaining} days</span>
                    </div>
                </div>
            </div>

            <div class="download-section">
                <h3 style="color: white; margin: 0 0 15px 0;">📥 Download Annual Installer</h3>
                <p style="color: rgba(255,255,255,0.9); margin-bottom: 20px;">
                    Production-ready installer for Linux (Ubuntu/Debian/CentOS)<br>
                    <strong>Direct download - no login required</strong>
                </p>
                <a href="{server_base_url}/downloads/annual-installer" class="btn">
                    ⬇️ Download Installer (Annual License)
                </a>
                <p style="color: rgba(255,255,255,0.8); margin-top: 15px; font-size: 13px;">
                    File: rhinometric-annual-2.5.0-install.sh (12 KB)
                </p>
            </div>

            <div style="background: #f0f9ff; border: 2px solid #0ea5e9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h4 style="color: #0369a1; margin: 0 0 10px 0;">📘 Documentation</h4>
                <p style="margin: 0; color: #075985;">
                    Complete installation guides and user manuals are available at:<br>
                    <a href="https://rhinometric.com/documentation" style="color: #0ea5e9; font-weight: 600;">rhinometric.com/documentation</a>
                </p>
            </div>

            <div class="features">
                <h3 style="color: #1e3a8a; margin-top: 0;">✅ Included Features</h3>
                <ul>
                    <li>📊 Pre-configured Grafana dashboards</li>
                    <li>📈 Prometheus monitoring (30-day retention)</li>
                    <li>📝 Centralized logs with Loki</li>
                    <li>🔍 Distributed tracing (Tempo + Jaeger)</li>
                    <li>🚨 Advanced alerting with Alertmanager</li>
                    <li>🤖 AI anomaly detection</li>
                    <li>🎨 Rhinometric Console</li>
                    <li>🔗 API Connector for integrations</li>
                </ul>
            </div>

            <div class="warning-box">
                <h4 style="color: #d97706; margin: 0 0 10px 0;">⚠️ Important - On-Premise Solution</h4>
                <p style="margin: 0; color: #78350f;">
                    Rhinometric is a <strong>100% on-premise</strong> solution. 
                    All your data stays in your infrastructure. <strong>GDPR compliant</strong> by design.
                </p>
            </div>

            <div class="support-box">
                <p style="font-size: 16px; color: #1e3a8a;"><strong>Need Help?</strong></p>
                <p>📧 <a href="mailto:rafael.canelon@rhinometric.com" style="color: #667eea; text-decoration: none;">rafael.canelon@rhinometric.com</a></p>
                <p>🌐 <a href="https://rhinometric.com" style="color: #667eea; text-decoration: none;">rhinometric.com</a></p>
                <p style="color: #6b7280; font-size: 14px; margin-top: 15px;">
                    <strong>Support:</strong> Mon-Fri, 9:00-18:00 CET | <strong>Response:</strong> &lt; 4 hours
                </p>
            </div>
        </div>

        <div class="footer">
            <p><strong style="color: #f3f4f6;">RHINOMETRIC</strong> | Enterprise Observability Platform</p>
            <p>© 2025 Rhinometric. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Send email
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Your Rhinometric License - {license_key}"
        msg['From'] = smtp_from
        msg['To'] = recipient_email
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, recipient_email, msg.as_string())
        
        print(f"✅ Annual license email sent (EN): {license_key} → {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

@app.post("/api/v1/admin/licenses/create-annual")
def create_annual_license(request: AnnualLicenseRequest, db: Session = Depends(get_db)):
    """Create annual license (365 days) and send email notification"""
    # Generate unique license key
    random_hex = secrets.token_hex(8).upper()
    license_key = f"RHINO-ANNU-{random_hex}"
    
    # Calculate expiration (365 days)
    expires_at = datetime.utcnow() + timedelta(days=365)
    
    # Create license in database (using existing schema fields only)
    license_obj = License(
        license_key=license_key,
        email=request.client_email,
        expires_at=expires_at,
        max_activations=1,  # Annual licenses allow 1 activation
        is_active=True
    )
    
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    
    # Send email notification
    email_sent = send_annual_license_email_simple(
        license_key=license_key,
        recipient_email=request.client_email,
        expires_at=expires_at
    )
    
    return {
        "license_key": license_key,
        "expires_at": expires_at.isoformat(),
        "client_email": request.client_email,
        "customer_name": request.customer_name,
        "client_company": request.client_company,
        "duration_days": 365,
        "email_sent": email_sent
    }
