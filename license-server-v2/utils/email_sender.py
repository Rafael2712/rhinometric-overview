#!/usr/bin/env python3
"""
Email utilities for Rhinometric License Server
Handles license delivery with PDF attachments and GDPR compliance
"""

import smtplib
import secrets
import string
import logging
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Setup logging
logger = logging.getLogger("rhinometric.email")

def generate_license_key(license_type: str) -> str:
    """Generate unique license key"""
    year = datetime.utcnow().year
    type_prefix = license_type.upper()[:4]
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    return f"RHINO-{type_prefix}-{year}-{random_part}"

async def send_license_email_with_attachments(
    to_email: str,
    customer_name: str,
    license_key: str,
    license_type: str,
    expires_at: datetime,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from: str,
    client_company: str = "",
    docs_dir: Path = Path("/app/docs"),
    retry_count: int = 0,
    server_base_url: str = "http://licensing.rhinometric.com:5000"
) -> bool:
    """
    Send license activation email with PDF attachments and GDPR compliance
    
    Args:
        to_email: Customer email address
        customer_name: Customer name
        license_key: Generated license key
        license_type: Type (trial/annual/permanent)
        expires_at: License expiration date
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password
        smtp_from: From email address
        client_company: Customer company name
        docs_dir: Path to PDF documents directory
        retry_count: Internal retry counter
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    if not smtp_password:
        logger.warning(f"SMTP password not configured - Email not sent to {to_email}")
        return False
    
    # Ensure docs directory exists
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate PDFs if they don't exist
    pdf_manual = docs_dir / "manual_usuario.pdf"
    pdf_install = docs_dir / "guia_instalacion.pdf"
    
    if not (pdf_manual.exists() and pdf_install.exists()):
        logger.info("Generating PDF documentation...")
        try:
            from .pdf_generator import generate_all_documentation_pdfs
            generate_all_documentation_pdfs(docs_dir)
        except Exception as e:
            logger.warning(f"Could not generate PDFs: {e}")
    
    try:
        # Prepare email message
        msg = MIMEMultipart('mixed')
        msg['From'] = smtp_from
        msg['To'] = to_email
        msg['Subject'] = f"[Rhinometric] Activación de su licencia {license_type.capitalize()}"
        
        # Format expiration date
        expiry_str = expires_at.strftime("%d/%m/%Y") if license_type != "permanent" else "Sin expiración"
        
        # Generate UUID/hash for server assignment
        server_hash = secrets.token_hex(8).upper()
        
        # Generate download URLs based on license type
        if license_type == "demo_cloud":
            download_url = f"{server_base_url}/downloads/demo-ova"
            download_text = "Descargar OVA Demo (4 horas)"
            download_description = "Archivo OVA listo para importar en VirtualBox o VMware. Incluye todo el stack Rhinometric pre-configurado."
        elif license_type == "trial":
            download_url = f"{server_base_url}/downloads/trial-installer"
            download_text = "Descargar Instalador Linux (14 días)"
            download_description = "Script de instalación automática para Ubuntu, Debian o CentOS. Requiere Docker 24.0+ y 8GB RAM."
        else:  # annual_standard or other
            download_url = "https://github.com/Rafael2712/rhinometric-overview/releases/latest/download/rhinometric-v2.5.0-stable.tar.gz"
            download_text = "Descargar Rhinometric v2.5.0 Completo"
            download_description = "Paquete completo con todos los componentes para instalación en producción."
        
        # Documentation URLs
        install_guide_url = f"{server_base_url}/docs/installation-guide?lang=es"
        user_manual_url = f"{server_base_url}/docs/user-manual?lang=es"
        install_guide_en_url = f"{server_base_url}/docs/installation-guide?lang=en"
        user_manual_en_url = f"{server_base_url}/docs/user-manual?lang=en"
        
        # HTML email body with modern, interactive design
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2c3e50; background: #ecf0f1; }}
        .email-wrapper {{ max-width: 650px; margin: 40px auto; background: white; box-shadow: 0 10px 40px rgba(0,0,0,0.15); border-radius: 16px; overflow: hidden; }}
        
        /* Header with gradient and logo */
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px 30px; text-align: center; position: relative; }
        .header::after { content: ''; position: absolute; bottom: -20px; left: 0; right: 0; height: 40px; background: white; border-radius: 50% 50% 0 0; }
        .logo-container { margin-bottom: 20px; }
        .logo-img {{ max-width: 220px; height: auto; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3)); animation: float 3s ease-in-out infinite; }}
        @keyframes float {{ 0%%, 100%% {{ transform: translateY(0px); }} 50%% {{ transform: translateY(-10px); }} }}
        .logo-emoji {{ font-size: 48px; margin-bottom: 10px; animation: bounce 2s infinite; }}
        @keyframes bounce {{ 0%%, 100%% {{ transform: translateY(0); }} 50%% {{ transform: translateY(-10px); }} }}
        .header h1 {{ font-size: 32px; margin: 10px 0; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }}
        .header p {{ font-size: 16px; opacity: 0.95; font-weight: 300; }}
        
        /* Content area */
        .content {{ padding: 40px 35px; background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%); }}
        .greeting {{ font-size: 24px; color: #2c3e50; margin-bottom: 20px; font-weight: 600; }}
        .intro {{ font-size: 16px; color: #555; margin-bottom: 30px; line-height: 1.8; }}
        
        /* License card with premium look */
        .license-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3); margin: 30px 0; position: relative; overflow: hidden; }}
        .license-card::before {{ content: '🦏'; position: absolute; top: -20px; right: -20px; font-size: 180px; opacity: 0.1; transform: rotate(-15deg); }}
        .license-title {{ font-size: 18px; font-weight: 700; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid rgba(255,255,255,0.3); padding-bottom: 10px; }}
        .license-field {{ margin: 15px 0; padding: 12px; background: rgba(255,255,255,0.15); border-radius: 6px; backdrop-filter: blur(10px); }}
        .license-label {{ display: inline-block; width: 140px; font-weight: 600; font-size: 14px; }}
        .license-value {{ font-family: 'Courier New', monospace; font-size: 15px; font-weight: 700; letter-spacing: 0.5px; }}
        
        /* Installation steps with icons */
        .steps-section {{ margin: 30px 0; }}
        .steps-title {{ font-size: 22px; color: #2c3e50; margin-bottom: 20px; font-weight: 600; }}
        .step {{ background: white; padding: 20px; margin: 15px 0; border-radius: 10px; border-left: 5px solid #667eea; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: all 0.3s; position: relative; padding-left: 70px; }}
        .step-number {{ position: absolute; left: 20px; top: 50%; transform: translateY(-50%); background: linear-gradient(135deg, #667eea, #764ba2); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 20px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }}
        .step-content {{ color: #555; font-size: 15px; line-height: 1.7; }}
        .step code {{ background: #f0f3f7; padding: 3px 8px; border-radius: 4px; color: #667eea; font-weight: 600; }}
        
        /* Buttons */
        .cta-section {{ text-align: center; margin: 40px 0; }}
        .btn {{ display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; text-decoration: none; border-radius: 50px; font-weight: 600; font-size: 16px; box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4); transition: all 0.3s; }}
        .btn:hover {{ transform: translateY(-3px); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5); }}
        
        /* Attachments box */
        .attachments {{ background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 30px 0; border: 2px dashed #667eea; }}
        .attachments h3 {{ color: #667eea; margin-bottom: 15px; font-size: 18px; }}
        .attachment-item {{ background: white; padding: 12px 15px; margin: 8px 0; border-radius: 6px; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
        .attachment-icon {{ font-size: 24px; margin-right: 12px; }}
        .attachment-name {{ font-weight: 600; color: #2c3e50; }}
        
        /* GDPR notice */
        .gdpr-box {{ background: linear-gradient(to right, #fff3cd, #fff8e1); border-left: 5px solid #ffc107; padding: 20px; margin: 30px 0; border-radius: 8px; }}
        .gdpr-box strong {{ color: #f57c00; display: block; margin-bottom: 10px; font-size: 16px; }}
        .gdpr-box p {{ font-size: 13px; color: #666; line-height: 1.7; }}
        
        /* Support section */
        .support-box {{ background: linear-gradient(135deg, #e3f2fd, #f1f8ff); padding: 25px; border-radius: 10px; margin: 30px 0; text-align: center; }}
        .support-title {{ font-size: 20px; color: #1976d2; margin-bottom: 15px; font-weight: 600; }}
        .support-links {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }}
        .support-link {{ display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: white; border-radius: 25px; text-decoration: none; color: #1976d2; font-weight: 600; box-shadow: 0 3px 10px rgba(25, 118, 210, 0.2); transition: all 0.3s; }}
        .support-link:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(25, 118, 210, 0.3); }}
        
        /* Footer */
        .footer {{ background: #2c3e50; color: #ecf0f1; padding: 30px; text-align: center; }}
        .footer-brand {{ font-size: 18px; font-weight: 700; margin-bottom: 10px; }}
        .footer-tagline {{ font-size: 14px; opacity: 0.8; margin-bottom: 15px; }}
        .footer-legal {{ font-size: 11px; opacity: 0.6; margin-top: 15px; line-height: 1.6; }}
        
        /* Responsive */
        @media only screen and (max-width: 600px) {{
            .email-wrapper {{ margin: 0; border-radius: 0; }}
            .content {{ padding: 25px 20px; }}
            .step {{ padding-left: 65px; }}
            .license-label {{ display: block; margin-bottom: 5px; }}
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <!-- Header -->
        <div class="header">
            <div class="logo-container">
                <!-- Logo SVG embebido inline -->
                <svg class="logo-img" viewBox="0 0 400 150" xmlns="http://www.w3.org/2000/svg">
                    <!-- Rhinometric Logo: Rhino icon + text -->
                    <defs>
                        <linearGradient id="rhino-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#00D4FF;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#00B4D8;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    
                    <!-- Rhino icon -->
                    <g transform="translate(0, 10)">
                        <!-- Rhino body outline -->
                        <path d="M 60 80 Q 45 60 45 45 Q 45 25 60 15 Q 75 5 90 15 L 100 10 L 110 15 Q 120 20 120 35 Q 120 50 110 65 L 115 75 L 110 85 Q 95 95 75 95 Q 60 95 60 80 Z" 
                              fill="url(#rhino-gradient)" stroke="#FFF" stroke-width="3"/>
                        <!-- Rhino horn -->
                        <path d="M 105 25 L 115 10 L 120 25 Z" fill="#FFF" stroke="#FFF" stroke-width="2"/>
                        <!-- Rhino eye -->
                        <circle cx="75" cy="40" r="4" fill="#FFF"/>
                        <!-- Rhino ear -->
                        <ellipse cx="95" cy="25" rx="8" ry="12" fill="#FFF" opacity="0.7"/>
                    </g>
                    
                    <!-- Rhinometric text -->
                    <text x="140" y="75" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="#FFF">
                        Rhinometric
                    </text>
                </svg>
            </div>
            <p style="font-size: 18px; margin-top: 15px; opacity: 0.95; font-weight: 300;">Observability & AIOps Platform</p>
        </div>
        
        <!-- Main Content -->
        <div class="content">
            <div class="greeting">¡Hola {customer_name}! 👋</div>
            <p class="intro">
                Nos complace darte la bienvenida a Rhinometric. Tu licencia <strong>{license_type.upper()}</strong> 
                ha sido generada exitosamente y está lista para usar. A continuación encontrarás toda la información 
                necesaria para comenzar.
            </p>
            
            <!-- License Card -->
            <div class="license-card">
                <div class="license-title">📋 INFORMACIÓN DE TU LICENCIA</div>
                <div class="license-field">
                    <span class="license-label">Tipo:</span>
                    <span class="license-value">{license_type.capitalize()}</span>
                </div>
                <div class="license-field">
                    <span class="license-label">Clave de Licencia:</span>
                    <span class="license-value">{license_key}</span>
                </div>
                <div class="license-field">
                    <span class="license-label">Fecha de Expiración:</span>
                    <span class="license-value">{expiry_str}</span>
                </div>
                <div class="license-field">
                    <span class="license-label">Servidor Asignado:</span>
                    <span class="license-value">{server_hash}</span>
                </div>
            </div>
            
            <!-- Installation Steps -->
            <div class="steps-section">
                <div class="steps-title">🚀 Instalación en 3 simples pasos</div>
                
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <strong>Descarga el paquete</strong><br>
                        Obtén la última versión desde nuestro repositorio de GitHub o tu panel de control personalizado.
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <strong>Configura tu licencia</strong><br>
                        Abre el archivo <code>.env</code> y pega tu clave en el campo <code>LICENSE_KEY</code>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <strong>Ejecuta el instalador</strong><br>
                        • <strong>Linux/macOS:</strong> <code>./install.sh</code><br>
                        • <strong>Windows:</strong> <code>.\\install.ps1</code><br>
                        ¡Y listo! Tu stack estará funcionando en minutos.
                    </div>
                </div>
            </div>
            
            <!-- CTA Button -->
            <div class="cta-section">
                <a href="{download_url}" class="btn">
                    📥 {download_text}
                </a>
                <p style="color: #666; font-size: 13px; margin-top: 15px; max-width: 500px; margin-left: auto; margin-right: auto;">
                    {download_description}
                </p>
            </div>
            
            <!-- Attachments -->
            <div class="attachments">
                <h3>� Documentación Adjunta</h3>
                <div class="attachment-item">
                    <span class="attachment-icon">📘</span>
                    <span class="attachment-name">Manual de Usuario Completo (PDF)</span>
                </div>
                <div class="attachment-item">
                    <span class="attachment-icon">📗</span>
                    <span class="attachment-name">Guía de Instalación Detallada (PDF)</span>
                </div>                
                <p style="margin-top: 15px; color: #666; font-size: 13px;">
                    También puedes descargar la documentación en línea:
                </p>
                <div style="margin-top: 10px;">
                    <a href="{install_guide_url}" style="color: #667eea; text-decoration: none; margin-right: 15px;">📘 Guía Instalación (ES)</a>
                    <a href="{install_guide_en_url}" style="color: #667eea; text-decoration: none; margin-right: 15px;">📘 Installation Guide (EN)</a><br>
                    <a href="{user_manual_url}" style="color: #667eea; text-decoration: none; margin-right: 15px;">📗 Manual Usuario (ES)</a>
                    <a href="{user_manual_en_url}" style="color: #667eea; text-decoration: none;">📗 User Manual (EN)</a>
                </div>            </div>
            
            <!-- Access Credentials -->
            <div class="support-box">
                <div class="support-title">🔐 Credenciales de Acceso</div>
                <p style="margin-bottom: 15px; color: #555;">Una vez instalado, accede a Grafana con:</p>
                <div style="background: white; padding: 15px; border-radius: 8px; display: inline-block;">
                    <strong>URL:</strong> http://localhost:3000<br>
                    <strong>Usuario:</strong> admin<br>
                    <strong>Contraseña inicial:</strong> {server_hash[:8].lower()}<br>
                    <em style="color: #e74c3c; font-size: 13px;">⚠️ Por seguridad, cambie esta contraseña en el primer acceso</em>
                </div>
            </div>
            
            <!-- GDPR Notice -->
            <div class="gdpr-box">
                <strong>🛡️ Protección de Datos (GDPR)</strong>
                <p>
                    Rhinometric cumple con el Reglamento General de Protección de Datos (UE) 2016/679. 
                    Tus datos personales se utilizan exclusivamente para la gestión de licencias y soporte técnico. 
                    Puedes ejercer tus derechos de acceso, rectificación, supresión o portabilidad contactando a: 
                    <strong>rafael.canelon@rhinometric.com</strong>
                </p>
            </div>
            
            <!-- Support Links -->
            <div class="support-box">
                <div class="support-title">💬 ¿Necesitas ayuda?</div>
                <p style="color: #666; font-size: 14px; margin-bottom: 15px;">
                    Soporte técnico disponible de <strong>lunes a viernes, 9:00–18:00 CET</strong>
                </p>
                <div class="support-links">
                    <a href="mailto:rafael.canelon@rhinometric.com" class="support-link">
                        📧 Email Soporte
                    </a>
                    <a href="https://rhinometric.com/docs" class="support-link">
                        📚 Documentación
                    </a>
                    <a href="https://rhinometric.com" class="support-link">
                        🌐 Sitio Web
                    </a>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-brand">RHINOMETRIC v2.1.0</div>
            <div class="footer-tagline">Enterprise Observability Platform</div>
            <div>© 2025 Rhinometric. Todos los derechos reservados.</div>
            <div class="footer-legal">
                Este correo fue enviado a <strong>{to_email}</strong><br>
                Si no solicitaste esta licencia, puedes ignorar este mensaje.<br>
                <a href="https://rhinometric.com/privacy" style="color: #3498db;">Política de Privacidad</a> | 
                <a href="https://rhinometric.com/terms" style="color: #3498db;">Términos de Uso</a>
            </div>
            <div style="font-size: 10px; margin-top: 10px; opacity: 0.7;">
                Rhinometric® es una marca registrada. El uso del software implica la aceptación<br>
                de los términos de licencia incluidos en la documentación adjunta.
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        # Plain text alternative
        text_body = f"""
Estimado/a {customer_name},

Gracias por adquirir una licencia {license_type.capitalize()} de Rhinometric.

═══════════════════════════════════════════════════════════════
INFORMACIÓN DE SU LICENCIA
═══════════════════════════════════════════════════════════════

• Tipo de licencia: {license_type.capitalize()}
• Clave: {license_key}
• Expira el: {expiry_str}
• Servidor asignado: {server_hash}

═══════════════════════════════════════════════════════════════
GUÍA RÁPIDA DE INSTALACIÓN
═══════════════════════════════════════════════════════════════

1. Descargue el paquete de instalación desde GitHub o su panel
2. Copie su clave en el archivo .env (campo LICENSE_KEY)
3. Ejecute el instalador:
   - Linux/Mac: ./install.sh
   - Windows: .\\install.ps1

═══════════════════════════════════════════════════════════════
DOCUMENTOS ADJUNTOS
═══════════════════════════════════════════════════════════════

• Manual de usuario (PDF)
• Guía de instalación completa (PDF)

═══════════════════════════════════════════════════════════════
CUMPLIMIENTO GDPR
═══════════════════════════════════════════════════════════════

Rhinometric garantiza el tratamiento responsable de datos personales conforme
al Reglamento General de Protección de Datos (UE) 2016/679. Sus datos se
utilizan únicamente para emisión, validación y soporte de su licencia.

Derechos: Acceso, rectificación, supresión, portabilidad
Contacto: rafael.canelon@rhinometric.com

═══════════════════════════════════════════════════════════════

Para soporte técnico:
📧 soporte@rhinometric.com
🌐 https://rhinometric.com

Atentamente,
Equipo Rhinometric

---
Rhinometric v2.1.0 - Enterprise Observability Platform
© 2025 Rhinometric. Todos los derechos reservados.
"""
        
        # Attach both text and HTML versions
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Attach documentation as text files
        doc_manual = docs_dir / "manual_usuario.pdf"
        doc_install = docs_dir / "guia_instalacion.pdf"
        
        doc_attachments = [
            (doc_manual, "Manual_Usuario_Rhinometric_v2.1.0.pdf"),
            (doc_install, "Guia_Instalacion_Rhinometric_v2.1.0.pdf"),
        ]
        
        for doc_path, filename in doc_attachments:
            if doc_path.exists():
                with open(doc_path, 'rb') as f:
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)
                    logger.info(f"Attached PDF: {filename}")
            else:
                logger.info(f"PDF not found (will be generated): {doc_path}")
        
        # Send email via SMTP SSL (port 465)
        try:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {to_email} | License: {license_key} | Type: {license_type}")
            return True
            
        except Exception as e_ssl:
            logger.warning(f"SSL method failed: {e_ssl}. Trying STARTTLS...")
            
            # Fallback to STARTTLS (port 587)
            try:
                with smtplib.SMTP(smtp_host, 587, timeout=30) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                
                logger.info(f"✅ Email sent via STARTTLS to {to_email} | License: {license_key}")
                return True
                
            except Exception as e_tls:
                raise Exception(f"Both SSL and STARTTLS failed: SSL={str(e_ssl)}, TLS={str(e_tls)}")
    
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        
        # Retry once after 30 seconds
        if retry_count < 1:
            logger.info(f"Retrying email to {to_email} in 30 seconds...")
            await asyncio.sleep(30)
            return await send_license_email_with_attachments(
                to_email, customer_name, license_key, license_type, 
                expires_at, smtp_host, smtp_port, smtp_user, smtp_password, smtp_from,
                client_company, docs_dir, retry_count + 1
            )
        
        return False
