# Annual License Endpoint for Rhinometric License Server v2.5.0
# Add this to main.py on AWS server

from pydantic import BaseModel
import os

class AnnualLicenseRequest(BaseModel):
    customer_name: str
    client_email: str
    client_company: str
    max_hosts: int = 20
    duration_days: int = 365

def send_annual_license_email(license_key: str, recipient_email: str, expires_at, tier: str, max_hosts: int, db):
    """Send Annual license email in ENGLISH with all download links"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import datetime
    
    # Get SMTP config
    smtp_host = os.getenv("SMTP_HOST", "smtp.zoho.eu")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "rafael.canelon@rhinometric.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", "rafael.canelon@rhinometric.com")
    server_base_url = os.getenv("SERVER_BASE_URL", "http://54.197.192.198:8090")
    
    if not smtp_password:
        raise Exception("SMTP not configured")
    
    # Calculate expiration info
    expires_at_str = expires_at.strftime("%B %d, %Y") if expires_at else "N/A"
    days_remaining = (expires_at - datetime.utcnow()).days if expires_at else 0
    
    # HTML Email Template (ENGLISH) with Rhinometric Logo
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .logo-section {{ text-align: center; padding: 30px 20px 20px 20px; background: #1e293b; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; padding: 30px 30px; text-align: center; }}
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
            .docs-section {{ background: white; padding: 25px; border-radius: 8px; margin: 20px 0; }}
            .docs-links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }}
            .doc-link {{ display: block; padding: 12px; background: #f3f4f6; 
                        text-decoration: none; color: #667eea; border-radius: 6px;
                        text-align: center; font-weight: 500; border: 1px solid #e5e7eb; }}
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
            <!-- Rhinometric Logo -->
            <div class="logo-section" style="text-align: center; padding: 30px 20px; background: #1e293b;">
                <!-- Logo SVG embebido directamente (compatible con la mayoría de clientes de email) -->
                <div style="width: 120px; height: 120px; margin: 0 auto 15px auto; background: #1e293b;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="120" height="120" style="display: block;">
                      <defs>
                        <linearGradient id="rhinoGradient{license_key[-6:]}" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                          <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                        </linearGradient>
                      </defs>
                      <path d="M 150,200 Q 140,160 160,130 Q 180,100 220,100 Q 260,100 280,130 Q 300,160 290,200 Q 285,240 270,260 Q 250,280 220,280 Q 190,280 170,260 Q 155,240 150,200 Z" 
                            fill="none" stroke="url(#rhinoGradient{license_key[-6:]})" stroke-width="8" stroke-linecap="round"/>
                      <path d="M 240,120 Q 250,80 260,60 Q 265,50 270,55 Q 275,60 270,70 Q 265,90 260,110" 
                            fill="none" stroke="url(#rhinoGradient{license_key[-6:]})" stroke-width="6" stroke-linecap="round"/>
                      <path d="M 220,130 Q 222,110 225,100 Q 227,95 230,98 Q 232,102 230,108" 
                            fill="none" stroke="url(#rhinoGradient{license_key[-6:]})" stroke-width="5" stroke-linecap="round"/>
                      <circle cx="200" cy="160" r="6" fill="#667eea"/>
                      <path d="M 160,140 Q 145,135 140,145 Q 135,155 145,160 Q 155,165 160,155" 
                            fill="none" stroke="url(#rhinoGradient{license_key[-6:]})" stroke-width="5" stroke-linecap="round"/>
                      <circle cx="250" cy="190" r="4" fill="#667eea"/>
                    </svg>
                </div>
                <p style="color: #f3f4f6; margin: 0 0 8px 0; font-size: 28px; font-weight: 600; letter-spacing: 3px;">RHINOMETRIC</p>
                <p style="color: #94a3b8; margin: 0; font-size: 13px; letter-spacing: 1px;">Enterprise Observability Platform</p>
            </div>
            
            <div class="header">
                <h1>🔑 Your Rhinometric License</h1>
                <p>Enterprise On-Premise Observability Platform</p>
            </div>

            <div class="content">
                <div class="license-box">
                    <h2 style="color: #1e3a8a; margin-top: 0;">📋 License Information</h2>
                    <p style="margin-bottom: 10px;"><strong>License Key:</strong></p>
                    <div class="license-key">{license_key}</div>
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Tier</strong>
                            <span>{tier.replace('_', ' ').title()}</span>
                        </div>
                        <div class="info-item">
                            <strong>Max Hosts</strong>
                            <span>{max_hosts} hosts</span>
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
                        <strong>Direct download link - no login required</strong>
                    </p>
                    <a href="{server_base_url}/downloads/annual-installer" class="btn">
                        ⬇️ Download Installer (Annual License)
                    </a>
                    <p style="color: rgba(255,255,255,0.8); margin-top: 15px; font-size: 13px;">
                        File: rhinometric-annual-2.5.0-install.sh (12 KB)
                    </p>
                </div>

                <div class="warning-box" style="background: #f0f9ff; border: 2px solid #0ea5e9;">
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
                        <li>🤖 AI anomaly detection (Prophet + ML)</li>
                        <li>🎨 Rhinometric Console (Vue.js dashboard)</li>
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
                <p style="margin-top: 15px; font-size: 10px; opacity: 0.8;">
                    Automatically generated by RHINOMETRIC License Monitor<br>
                    On-premise monitoring - 100% GDPR compliant
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Your Rhinometric License - {license_key[:20]}..."
        msg['From'] = smtp_from
        msg['To'] = recipient_email
        msg['Reply-To'] = smtp_from
        
        msg.attach(MIMEText(html_body, 'html'))
        
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                if smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                if smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
        
        print(f"✅ Annual license email sent (EN): {license_key} → {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        raise Exception(f"Email failed: {str(e)}")

@app.post("/api/v1/admin/licenses/create-annual")
def create_annual_license(request: AnnualLicenseRequest, db: Session = Depends(get_db)):
    """Create a new annual license"""
    import secrets
    from datetime import datetime, timedelta
    
    # Generate license key
    license_key = f"RHINO-ANNU-{secrets.token_hex(8).upper()}"
    
    # Set expiration
    expires_at = datetime.utcnow() + timedelta(days=request.duration_days)
    issued_at = datetime.utcnow()
    
    # Create license object
    license_obj = License(
        license_key=license_key,
        email=request.client_email,
        expires_at=expires_at,
        max_activations=1,
        tier="annual_standard",
        max_hosts=request.max_hosts,
        issued_at=issued_at,
        status="not_activated",
        organization=request.client_company,
        organization_email=request.client_email,
        is_active=True
    )
    
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    
    # Send email with new English template
    try:
        send_annual_license_email(
            license_key=license_key,
            recipient_email=request.client_email,
            expires_at=expires_at,
            tier="annual_standard",
            max_hosts=request.max_hosts,
            db=db
        )
        email_sent = True
    except Exception as e:
        print(f"⚠️ License created but email failed: {str(e)}")
        email_sent = False
    
    return {
        "license_key": license_key,
        "expires_at": expires_at.isoformat(),
        "tier": "annual_standard",
        "max_hosts": request.max_hosts,
        "duration_days": request.duration_days,
        "customer_name": request.customer_name,
        "client_email": request.client_email,
        "client_company": request.client_company,
        "status": "not_activated",
        "email_sent": email_sent
    }
