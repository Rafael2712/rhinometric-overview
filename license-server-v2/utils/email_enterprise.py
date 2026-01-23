#!/usr/bin/env python3
"""
Enterprise Email System for Rhinometric v2.5.0
Handles professional trial bundle emails (demo_cloud + trial)
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("rhinometric.email_enterprise")

# ═══════════════════════════════════════════════════════════════════════════
# PLANTILLA HTML ENTERPRISE
# ═══════════════════════════════════════════════════════════════════════════

def get_trial_bundle_email_template(
    customer_name: str,
    demo_license_key: str,
    trial_license_key: str,
    demo_expires_hours: int = 4,
    trial_expires_days: int = 14,
    locale: str = "es"
) -> Dict[str, str]:
    """
    Genera plantilla HTML profesional para email de trial bundle.
    
    Args:
        customer_name: Nombre del cliente
        demo_license_key: Clave de licencia demo_cloud (4h)
        trial_license_key: Clave de licencia trial (14d)
        demo_expires_hours: Horas de duración demo (default: 4)
        trial_expires_days: Días de duración trial (default: 14)
        locale: Idioma (es/en)
    
    Returns:
        Dict con 'subject', 'html' y 'text'
    """
    
    if locale == "es":
        subject = "🎯 Rhinometric Trial - Sus Licencias de Evaluación"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rhinometric Trial Bundle</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background-color: #f5f7fa;
        }}
        .email-wrapper {{
            max-width: 700px;
            margin: 0 auto;
            background: white;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 36px;
            margin: 0 0 10px 0;
            font-weight: 700;
        }}
        .header p {{
            font-size: 18px;
            opacity: 0.95;
            margin: 0;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .welcome {{
            font-size: 18px;
            color: #34495e;
            margin-bottom: 30px;
            line-height: 1.8;
        }}
        .license-box {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 25px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        .license-box h3 {{
            color: #667eea;
            margin: 0 0 15px 0;
            font-size: 20px;
        }}
        .license-key {{
            background: white;
            border: 2px dashed #667eea;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            font-weight: bold;
            color: #764ba2;
            text-align: center;
            border-radius: 6px;
            margin: 15px 0;
            letter-spacing: 1px;
        }}
        .specs {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }}
        .spec-item {{
            background: white;
            padding: 12px;
            border-radius: 6px;
            font-size: 14px;
        }}
        .spec-label {{
            color: #7f8c8d;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .spec-value {{
            color: #2c3e50;
            font-weight: 600;
            font-size: 16px;
            margin-top: 4px;
        }}
        .download-section {{
            background: #e8f4f8;
            padding: 30px;
            border-radius: 8px;
            margin: 30px 0;
        }}
        .download-section h3 {{
            color: #2c3e50;
            margin: 0 0 20px 0;
            font-size: 22px;
        }}
        .download-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 10px 10px 10px 0;
            font-size: 16px;
            transition: transform 0.2s;
        }}
        .download-button:hover {{
            transform: translateY(-2px);
        }}
        .steps {{
            background: #fff;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .steps h3 {{
            color: #2c3e50;
            margin: 0 0 20px 0;
            font-size: 22px;
        }}
        .step {{
            display: flex;
            margin: 20px 0;
        }}
        .step-number {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            flex-shrink: 0;
        }}
        .step-content {{
            margin-left: 20px;
            flex: 1;
        }}
        .step-title {{
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .step-desc {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .docs-links {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 6px;
        }}
        .docs-links h4 {{
            color: #856404;
            margin: 0 0 15px 0;
        }}
        .docs-links a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            margin-right: 20px;
            display: inline-block;
            margin-bottom: 10px;
        }}
        .support {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            margin: 30px 0;
            text-align: center;
        }}
        .support h3 {{
            color: #2c3e50;
            margin: 0 0 15px 0;
        }}
        .support p {{
            color: #7f8c8d;
            margin: 10px 0;
        }}
        .support strong {{
            color: #667eea;
            font-size: 18px;
        }}
        .footer {{
            background: #34495e;
            color: #ecf0f1;
            padding: 30px;
            text-align: center;
            font-size: 13px;
            line-height: 1.8;
        }}
        .footer strong {{
            color: white;
            display: block;
            margin-bottom: 10px;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
        .highlight strong {{
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <!-- Header -->
        <div class="header">
            <h1>🚀 Rhinometric</h1>
            <p>Observability & AIOps Platform</p>
        </div>

        <!-- Content -->
        <div class="content">
            <div class="welcome">
                <p>Hola <strong>{customer_name}</strong>,</p>
                <p style="margin-top: 15px;">
                    Gracias por solicitar tu evaluación de <strong>Rhinometric v2.5.0</strong>, 
                    la plataforma de observabilidad y AIOps empresarial que centraliza métricas, 
                    logs, traces y detección de anomalías con inteligencia artificial.
                </p>
                <p style="margin-top: 15px;">
                    Hemos generado <strong>DOS licencias de evaluación</strong> para que pruebes 
                    Rhinometric en diferentes escenarios:
                </p>
            </div>

            <!-- Licencia Demo Cloud (4 horas) -->
            <div class="license-box">
                <h3>🎯 Licencia Demo Cloud - Prueba Rápida ({demo_expires_hours} horas)</h3>
                <p style="color: #7f8c8d; margin-bottom: 10px;">
                    Ideal para una <strong>demostración inmediata</strong> sin instalar nada. 
                    Solo importa la OVA en VirtualBox o VMware y activa la licencia.
                </p>
                
                <div class="license-key">
                    {demo_license_key}
                </div>
                
                <div class="specs">
                    <div class="spec-item">
                        <div class="spec-label">Duración</div>
                        <div class="spec-value">{demo_expires_hours} horas</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Máximo Hosts</div>
                        <div class="spec-value">20 hosts</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Tipo</div>
                        <div class="spec-value">OVA Preconfigurada</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Instalación</div>
                        <div class="spec-value">Inmediata</div>
                    </div>
                </div>
                
                <div class="highlight" style="margin-top: 15px;">
                    <strong>💡 Cuándo usarla:</strong> Demo ejecutiva, prueba de concepto rápida, 
                    evaluación inicial del producto sin comprometer recursos de tu infraestructura.
                </div>
            </div>

            <!-- Licencia Trial (14 días) -->
            <div class="license-box">
                <h3>🔬 Licencia Trial - Evaluación Completa ({trial_expires_days} días)</h3>
                <p style="color: #7f8c8d; margin-bottom: 10px;">
                    Ideal para <strong>evaluación técnica profunda</strong> en tu propia infraestructura Linux. 
                    Instala en un servidor Ubuntu/Debian/CentOS y monitorea tu entorno real.
                </p>
                
                <div class="license-key">
                    {trial_license_key}
                </div>
                
                <div class="specs">
                    <div class="spec-item">
                        <div class="spec-label">Duración</div>
                        <div class="spec-value">{trial_expires_days} días</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Máximo Hosts</div>
                        <div class="spec-value">5 hosts</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Tipo</div>
                        <div class="spec-value">Instalación Linux</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Soporte</div>
                        <div class="spec-value">Email</div>
                    </div>
                </div>
                
                <div class="highlight" style="margin-top: 15px;">
                    <strong>💡 Cuándo usarla:</strong> Evaluación técnica completa, prueba de integración 
                    con tu stack actual, POC en entorno de pre-producción, análisis de capacidades de IA.
                </div>
            </div>

            <!-- Descarga e Instalación -->
            <div class="download-section">
                <h3>📦 Descarga e Instalación</h3>
                <p style="margin-bottom: 20px; color: #34495e;">
                    Elige el paquete según la licencia que quieras probar primero:
                </p>
                
                <a href="https://rhinometric.com/downloads/rhinometric-demo-v2.5.0.ova" class="download-button">
                    ⬇️ Descargar OVA Demo (4h)
                </a>
                
                <a href="https://rhinometric.com/downloads/rhinometric-trial-v2.5.0-linux.sh" class="download-button">
                    ⬇️ Descargar Instalador Linux (14d)
                </a>
            </div>

            <!-- Pasos para empezar -->
            <div class="steps">
                <h3>🚀 Cómo Empezar</h3>
                
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <div class="step-title">Descarga el entorno</div>
                        <div class="step-desc">
                            OVA para demo rápida o instalador Linux para evaluación completa.
                        </div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <div class="step-title">Importa/Instala la plataforma</div>
                        <div class="step-desc">
                            OVA: Importa en VirtualBox/VMware. Linux: Ejecuta ./install-trial.sh
                        </div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <div class="step-title">Activa tu licencia</div>
                        <div class="step-desc">
                            Accede a Rhinometric Console (puerto 3002), login: admin/admin, 
                            activa la licencia que elegiste.
                        </div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">4</div>
                    <div class="step-content">
                        <div class="step-title">Empieza a monitorear</div>
                        <div class="step-desc">
                            Conecta tus hosts, servicios y aplicaciones. La IA empezará a detectar 
                            anomalías automáticamente.
                        </div>
                    </div>
                </div>
            </div>

            <!-- Documentación -->
            <div class="docs-links">
                <h4>📚 Documentación de Soporte</h4>
                <a href="/docs/v2.5.0/pdf/guia_instalacion.pdf" target="_blank">📄 Guía de Instalación (ES)</a>
                <a href="/docs/v2.5.0/pdf/installation_guide.pdf" target="_blank">📄 Installation Guide (EN)</a>
                <br>
                <a href="/docs/v2.5.0/pdf/manual_usuario.pdf" target="_blank">📖 Manual de Usuario (ES)</a>
                <a href="/docs/v2.5.0/pdf/user_manual.pdf" target="_blank">📖 User Manual (EN)</a>
            </div>

            <!-- Soporte -->
            <div class="support">
                <h3>💬 Soporte y Contacto</h3>
                <p>¿Tienes dudas o necesitas ayuda con la instalación?</p>
                <p style="margin-top: 15px;">
                    <strong>rafael.canelon@rhinometric.com</strong>
                </p>
                <p style="margin-top: 20px; font-size: 14px;">
                    <strong>🔒 Privacidad:</strong> Todas tus métricas, logs y datos se almacenan 
                    <strong>exclusivamente en tu infraestructura on-premise</strong>. Rhinometric 
                    no envía, almacena ni procesa ningún dato fuera de tu entorno.
                </p>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <strong>Rhinometric v2.5.0 - Enterprise Observability & AIOps</strong>
            <p>
                Este correo contiene información confidencial. Si lo has recibido por error, 
                por favor elimínalo y notifica al remitente.
            </p>
            <p style="margin-top: 15px;">
                <strong>GDPR Compliance:</strong> Tus datos personales (nombre, email, empresa) 
                se utilizan únicamente para la gestión de licencias de evaluación y no se 
                comparten con terceros. Puedes solicitar su eliminación en cualquier momento 
                contactando con rafael.canelon@rhinometric.com
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        text_content = f"""
═══════════════════════════════════════════════════════════════════
RHINOMETRIC v2.5.0 - TUS LICENCIAS DE EVALUACIÓN
═══════════════════════════════════════════════════════════════════

Hola {customer_name},

Gracias por solicitar tu evaluación de Rhinometric v2.5.0, la plataforma 
de observabilidad y AIOps empresarial.

Hemos generado DOS licencias de evaluación para ti:

───────────────────────────────────────────────────────────────────
🎯 LICENCIA DEMO CLOUD - PRUEBA RÁPIDA ({demo_expires_hours} HORAS)
───────────────────────────────────────────────────────────────────

Clave de Licencia: {demo_license_key}

• Duración: {demo_expires_hours} horas desde la activación
• Máximo Hosts: 20 hosts
• Tipo: OVA preconfigurada (VirtualBox/VMware)
• Ideal para: Demo ejecutiva, prueba de concepto rápida

Descarga: https://rhinometric.com/downloads/rhinometric-demo-v2.5.0.ova

───────────────────────────────────────────────────────────────────
🔬 LICENCIA TRIAL - EVALUACIÓN COMPLETA ({trial_expires_days} DÍAS)
───────────────────────────────────────────────────────────────────

Clave de Licencia: {trial_license_key}

• Duración: {trial_expires_days} días desde la activación
• Máximo Hosts: 5 hosts
• Tipo: Instalación Linux (Ubuntu/Debian/CentOS)
• Ideal para: Evaluación técnica profunda, POC en tu infraestructura

Descarga: https://rhinometric.com/downloads/rhinometric-trial-v2.5.0-linux.sh

───────────────────────────────────────────────────────────────────
🚀 CÓMO EMPEZAR
───────────────────────────────────────────────────────────────────

1. Descarga el paquete que prefieras (OVA o instalador Linux)
2. Importa/Instala la plataforma
3. Accede a Rhinometric Console (puerto 3002, login: admin/admin)
4. Activa la licencia correspondiente
5. Empieza a monitorear tus hosts y servicios

📚 DOCUMENTACIÓN
───────────────────────────────────────────────────────────────────

• Guía de Instalación (ES): /docs/v2.5.0/pdf/guia_instalacion.pdf
• Installation Guide (EN): /docs/v2.5.0/pdf/installation_guide.pdf
• Manual de Usuario (ES): /docs/v2.5.0/pdf/manual_usuario.pdf
• User Manual (EN): /docs/v2.5.0/pdf/user_manual.pdf

💬 SOPORTE
───────────────────────────────────────────────────────────────────

¿Dudas o problemas con la instalación?
Email: rafael.canelon@rhinometric.com

🔒 PRIVACIDAD: Todos tus datos se almacenan exclusivamente en tu 
infraestructura on-premise. Rhinometric no envía ni procesa ningún 
dato fuera de tu entorno.

═══════════════════════════════════════════════════════════════════

Rhinometric v2.5.0 - Enterprise Observability & AIOps
        """
    
    else:  # English
        subject = "🎯 Rhinometric Trial - Your Evaluation Licenses"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rhinometric Trial Bundle</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background-color: #f5f7fa;
        }
        .email-wrapper {
            max-width: 700px;
            margin: 0 auto;
            background: white;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 36px;
            margin: 0 0 10px 0;
            font-weight: 700;
        }
        .header p {
            font-size: 18px;
            opacity: 0.95;
            margin: 0;
        }
        .content {
            padding: 40px 30px;
        }
        .welcome {
            font-size: 18px;
            color: #34495e;
            margin-bottom: 30px;
            line-height: 1.8;
        }
        .license-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 25px;
            margin: 20px 0;
            border-radius: 8px;
        }
        .license-box h3 {
            color: #667eea;
            margin: 0 0 15px 0;
            font-size: 20px;
        }
        .license-key {
            background: white;
            border: 2px dashed #667eea;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            font-weight: bold;
            color: #764ba2;
            text-align: center;
            border-radius: 6px;
            margin: 15px 0;
            letter-spacing: 1px;
        }
        .specs {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }
        .spec-item {
            background: white;
            padding: 12px;
            border-radius: 6px;
            font-size: 14px;
        }
        .spec-label {
            color: #7f8c8d;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .spec-value {
            color: #2c3e50;
            font-weight: 600;
            font-size: 16px;
            margin-top: 4px;
        }
        .download-section {
            background: #e8f4f8;
            padding: 30px;
            border-radius: 8px;
            margin: 30px 0;
        }
        .download-section h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 22px;
        }
        .download-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .download-btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 25px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            text-align: center;
            transition: transform 0.2s;
        }
        .download-btn:hover {
            transform: translateY(-2px);
        }
        .steps {
            margin: 30px 0;
        }
        .steps h3 {
            color: #2c3e50;
            margin-bottom: 25px;
            font-size: 22px;
        }
        .step {
            display: flex;
            margin: 20px 0;
            align-items: flex-start;
        }
        .step-number {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
            flex-shrink: 0;
            margin-right: 20px;
        }
        .step-content {
            flex: 1;
        }
        .step-title {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
            font-size: 16px;
        }
        .step-desc {
            color: #7f8c8d;
            font-size: 14px;
        }
        .docs-links {
            background: #fffbe6;
            padding: 25px;
            border-radius: 8px;
            border-left: 4px solid #f39c12;
            margin: 30px 0;
        }
        .docs-links h4 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        .docs-links a {
            display: inline-block;
            color: #667eea;
            text-decoration: none;
            margin: 5px 15px 5px 0;
            font-weight: 500;
        }
        .docs-links a:hover {
            text-decoration: underline;
        }
        .support {
            background: #f0f0f0;
            padding: 25px;
            border-radius: 8px;
            margin: 30px 0;
            text-align: center;
        }
        .support h3 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        .footer {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
            font-size: 14px;
        }
        .footer p {
            margin: 10px 0;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <!-- Header -->
        <div class="header">
            <h1>🦏 Rhinometric</h1>
            <p>Enterprise Observability & AIOps Platform</p>
        </div>

        <div class="content">
            <!-- Welcome -->
            <div class="welcome">
                <p>Hello <strong>{customer_name}</strong>,</p>
                <br>
                <p>
                    Thank you for requesting your evaluation of <strong>Rhinometric v2.5.0</strong>, 
                    the enterprise observability and AIOps platform.
                </p>
                <br>
                <p>
                    We have generated <strong>TWO evaluation licenses</strong> for you:
                </p>
            </div>

            <!-- Demo Cloud License -->
            <div class="license-box" style="border-left-color: #3498db;">
                <h3>🚀 Demo Cloud License - Quick Test ({demo_expires_hours} Hours)</h3>
                
                <div class="license-key">{demo_license_key}</div>
                
                <div class="specs">
                    <div class="spec-item">
                        <div class="spec-label">Duration</div>
                        <div class="spec-value">{demo_expires_hours} hours</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Max Hosts</div>
                        <div class="spec-value">20 hosts</div>
                    </div>
                </div>
                
                <p style="margin-top: 15px; font-size: 14px; color: #7f8c8d;">
                    <strong>When to use:</strong> Executive demo, quick proof of concept. 
                    Pre-configured OVA for VirtualBox/VMware.
                </p>
            </div>

            <!-- Trial License -->
            <div class="license-box" style="border-left-color: #27ae60;">
                <h3>🔬 Trial License - Full Evaluation ({trial_expires_days} Days)</h3>
                
                <div class="license-key">{trial_license_key}</div>
                
                <div class="specs">
                    <div class="spec-item">
                        <div class="spec-label">Duration</div>
                        <div class="spec-value">{trial_expires_days} days</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Max Hosts</div>
                        <div class="spec-value">5 hosts</div>
                    </div>
                </div>
                
                <p style="margin-top: 15px; font-size: 14px; color: #7f8c8d;">
                    <strong>When to use:</strong> In-depth technical evaluation, POC in your infrastructure. 
                    Linux installer (Ubuntu/Debian/CentOS).
                </p>
            </div>

            <!-- Download Section -->
            <div class="download-section">
                <h3>📥 Download & Installation</h3>
                <p style="margin-bottom: 20px;">Choose the package that best fits your needs:</p>
                
                <div class="download-buttons">
                    <a href="https://rhinometric.com/downloads/rhinometric-demo-v2.5.0.ova" class="download-btn" target="_blank">
                        ⬇️ Download OVA Demo (4h)
                    </a>
                    <a href="https://rhinometric.com/downloads/rhinometric-trial-v2.5.0-linux.sh" class="download-btn" target="_blank">
                        ⬇️ Download Linux Installer (14d)
                    </a>
                </div>
            </div>

            <!-- Steps -->
            <div class="steps">
                <h3>🚀 How to Get Started</h3>
                
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <div class="step-title">Download your preferred package</div>
                        <div class="step-desc">
                            OVA for quick demo or Linux installer for full evaluation
                        </div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <div class="step-title">Import/Install the platform</div>
                        <div class="step-desc">
                            OVA: Import into VirtualBox/VMware. Linux: Run ./install-trial.sh
                        </div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <div class="step-title">Activate your license</div>
                        <div class="step-desc">
                            Access Rhinometric Console (port 3002), login: admin/admin, 
                            activate the license you chose.
                        </div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">4</div>
                    <div class="step-content">
                        <div class="step-title">Start monitoring</div>
                        <div class="step-desc">
                            Connect your hosts, services and applications. AI will start detecting 
                            anomalies automatically.
                        </div>
                    </div>
                </div>
            </div>

            <!-- Documentation -->
            <div class="docs-links">
                <h4>📚 Support Documentation</h4>
                <a href="/docs/v2.5.0/pdf/guia_instalacion.pdf" target="_blank">📄 Installation Guide (ES)</a>
                <a href="/docs/v2.5.0/pdf/installation_guide.pdf" target="_blank">📄 Installation Guide (EN)</a>
                <br>
                <a href="/docs/v2.5.0/pdf/manual_usuario.pdf" target="_blank">📖 User Manual (ES)</a>
                <a href="/docs/v2.5.0/pdf/user_manual.pdf" target="_blank">📖 User Manual (EN)</a>
            </div>

            <!-- Support -->
            <div class="support">
                <h3>💬 Support & Contact</h3>
                <p>Do you have questions or need help with the installation?</p>
                <p style="margin-top: 15px;">
                    <strong>rafael.canelon@rhinometric.com</strong>
                </p>
                <p style="margin-top: 20px; font-size: 14px;">
                    <strong>🔒 Privacy:</strong> All your metrics, logs and data are stored 
                    <strong>exclusively in your on-premise infrastructure</strong>. Rhinometric 
                    does not send, store or process any data outside your environment.
                </p>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <strong>Rhinometric v2.5.0 - Enterprise Observability & AIOps</strong>
            <p>
                This email contains confidential information. If you received it by mistake, 
                please delete it and notify the sender.
            </p>
            <p style="margin-top: 15px;">
                <strong>GDPR Compliance:</strong> Your personal data (name, email, company) 
                is used exclusively for evaluation license management and is not shared with 
                third parties. You can request its deletion at any time by contacting 
                rafael.canelon@rhinometric.com
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        text_content = f"""
═══════════════════════════════════════════════════════════════════
RHINOMETRIC v2.5.0 - YOUR EVALUATION LICENSES
═══════════════════════════════════════════════════════════════════

Hello {customer_name},

Thank you for requesting your evaluation of Rhinometric v2.5.0, the 
enterprise observability and AIOps platform.

We have generated TWO evaluation licenses for you:

───────────────────────────────────────────────────────────────────
🎯 DEMO CLOUD LICENSE - QUICK TEST ({demo_expires_hours} HOURS)
───────────────────────────────────────────────────────────────────

License Key: {demo_license_key}

• Duration: {demo_expires_hours} hours from activation
• Max Hosts: 20 hosts
• Type: Pre-configured OVA (VirtualBox/VMware)
• Best for: Executive demo, quick proof of concept

Download: https://rhinometric.com/downloads/rhinometric-demo-v2.5.0.ova

───────────────────────────────────────────────────────────────────
🔬 TRIAL LICENSE - FULL EVALUATION ({trial_expires_days} DAYS)
───────────────────────────────────────────────────────────────────

License Key: {trial_license_key}

• Duration: {trial_expires_days} days from activation
• Max Hosts: 5 hosts
• Type: Linux installer (Ubuntu/Debian/CentOS)
• Best for: In-depth technical evaluation, POC in your infrastructure

Download: https://rhinometric.com/downloads/rhinometric-trial-v2.5.0-linux.sh

───────────────────────────────────────────────────────────────────
🚀 HOW TO GET STARTED
───────────────────────────────────────────────────────────────────

1. Download your preferred package (OVA or Linux installer)
2. Import/Install the platform
3. Access Rhinometric Console (port 3002, login: admin/admin)
4. Activate the corresponding license
5. Start monitoring your hosts and services

📚 DOCUMENTATION
───────────────────────────────────────────────────────────────────

• Installation Guide (ES): /docs/v2.5.0/pdf/guia_instalacion.pdf
• Installation Guide (EN): /docs/v2.5.0/pdf/installation_guide.pdf
• User Manual (ES): /docs/v2.5.0/pdf/manual_usuario.pdf
• User Manual (EN): /docs/v2.5.0/pdf/user_manual.pdf

💬 SUPPORT
───────────────────────────────────────────────────────────────────

Questions or problems with installation?
Email: rafael.canelon@rhinometric.com

🔒 PRIVACY: All your data is stored exclusively in your on-premise 
infrastructure. Rhinometric does not send or process any data outside 
your environment.

═══════════════════════════════════════════════════════════════════

Rhinometric v2.5.0 - Enterprise Observability & AIOps
        """
    
    return {
        "subject": subject,
        "html": html_content,
        "text": text_content
    }


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN CENTRALIZADA DE ENVÍO
# ═══════════════════════════════════════════════════════════════════════════

async def send_trial_bundle_email(
    customer_email: str,
    customer_name: str,
    demo_license_key: str,
    trial_license_key: str,
    smtp_config: Dict[str, Any],
    locale: str = "es"
) -> bool:
    """
    Envía email profesional con bundle de licencias (demo_cloud + trial).
    
    Args:
        customer_email: Email del cliente
        customer_name: Nombre del cliente
        demo_license_key: Clave licencia demo_cloud (4h)
        trial_license_key: Clave licencia trial (14d)
        smtp_config: Dict con host, port, user, password, from_addr
        locale: Idioma (es/en)
    
    Returns:
        bool: True si envío exitoso, False si falla
    """
    
    if not smtp_config.get("password"):
        logger.warning(f"SMTP password not configured - Email NOT sent to {customer_email}")
        return False
    
    try:
        # Generar contenido del email
        template = get_trial_bundle_email_template(
            customer_name=customer_name,
            demo_license_key=demo_license_key,
            trial_license_key=trial_license_key,
            locale=locale
        )
        
        # Crear mensaje MIME
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_config.get("from_addr", "no-reply@rhinometric.com")
        msg['To'] = customer_email
        msg['Subject'] = template["subject"]
        
        # Adjuntar versiones texto y HTML
        part_text = MIMEText(template["text"], 'plain', 'utf-8')
        part_html = MIMEText(template["html"], 'html', 'utf-8')
        
        msg.attach(part_text)
        msg.attach(part_html)
        
        # Conectar y enviar
        logger.info(f"📧 Connecting to SMTP: {smtp_config['host']}:{smtp_config['port']}")
        
        with smtplib.SMTP_SSL(
            smtp_config["host"],
            smtp_config["port"],
            timeout=30
        ) as server:
            server.login(smtp_config["user"], smtp_config["password"])
            server.send_message(msg)
        
        logger.info(f"✅ Trial bundle email sent successfully to {customer_email}")
        logger.info(f"   Demo license: {demo_license_key}")
        logger.info(f"   Trial license: {trial_license_key}")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ SMTP Authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP error sending email to {customer_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending email to {customer_email}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# WRAPPER SIMPLIFICADO PARA COMPATIBILIDAD
# ═══════════════════════════════════════════════════════════════════════════

async def send_license_bundle(
    to_email: str,
    customer_name: str,
    demo_license_key: str,
    trial_license_key: str,
    smtp_host: str = "smtp.zoho.eu",
    smtp_port: int = 465,
    smtp_user: str = "rafael.canelon@rhinometric.com",
    smtp_password: str = "",
    smtp_from: str = "rafael.canelon@rhinometric.com",
    locale: str = "es"
) -> bool:
    """
    Wrapper simplificado para compatibilidad con código existente.
    """
    
    smtp_config = {
        "host": smtp_host,
        "port": smtp_port,
        "user": smtp_user,
        "password": smtp_password,
        "from_addr": smtp_from
    }
    
    return await send_trial_bundle_email(
        customer_email=to_email,
        customer_name=customer_name,
        demo_license_key=demo_license_key,
        trial_license_key=trial_license_key,
        smtp_config=smtp_config,
        locale=locale
    )
