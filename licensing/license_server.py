#!/usr/bin/env python3
"""
🦏 RHINOMETRIC LICENSE SERVER
Servidor de validación de licencias para Rhinometric Observability Platform
© 2025 Rhinometric. All rights reserved.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import json
import base64
import hashlib
from datetime import datetime, timedelta
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicialización de Flask
app = Flask(__name__)
CORS(app)

# Configuración desde variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:trial_rhinometric_2024@postgres:5432/rhinometric_trial')
JWT_SECRET = os.getenv('JWT_SECRET', 'trial_jwt_secret_change_this_in_production')
LICENSE_DURATION_DAYS = int(os.getenv('LICENSE_DURATION_DAYS', '180'))
LICENSES_DIR = os.getenv('LICENSES_DIR', '/app/licenses')

# SMTP Configuration for email delivery
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', 'licenses@rhinometric.io')
SMTP_ENABLED = bool(SMTP_USER and SMTP_PASSWORD)

# Banner de inicio
def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🦏 RHINOMETRIC LICENSE SERVER v1.0                ║
    ║        Observability Platform - License Validation       ║
    ║        © 2025 Rhinometric. All rights reserved.          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    logger.info(banner)
    logger.info(f"License Duration: {LICENSE_DURATION_DAYS} days (6 months)")
    logger.info(f"Licenses Directory: {LICENSES_DIR}")
    logger.info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Not configured'}")

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a DB: {e}")
        return None

def init_database():
    """Inicializa la tabla de licencias en PostgreSQL"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(255) UNIQUE NOT NULL,
                license_key TEXT NOT NULL,
                license_type VARCHAR(50) NOT NULL,
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                features JSONB,
                validation_count INTEGER DEFAULT 0,
                last_validation TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_customer ON licenses(customer_name);
            CREATE INDEX IF NOT EXISTS idx_expires ON licenses(expires_at);
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False

# ============================================================================
# LICENSE GENERATION
# ============================================================================

def generate_license(customer_name, license_type='trial', days=None):
    """
    Genera una nueva licencia Rhinometric
    
    Args:
        customer_name: Nombre del cliente
        license_type: 'trial', 'annual', 'permanent'
        days: Días de validez (si no se especifica, usa LICENSE_DURATION_DAYS)
    
    Returns:
        dict: Datos de la licencia generada
    """
    now = datetime.utcnow()
    
    license_data = {
        "customer": customer_name,
        "type": license_type,
        "issued": now.isoformat(),
        "product": "Rhinometric Observability Platform",
        "version": "1.0.0",
        "vendor": "Rhinometric",
        "contact": "soporte@rhinometric.com"
    }
    
    # Configurar según tipo de licencia
    if license_type == "trial":
        expire_date = now + timedelta(days=days or LICENSE_DURATION_DAYS)
        license_data["expires"] = expire_date.isoformat()
        license_data["features"] = [
            "metrics_monitoring",
            "logs_aggregation",
            "distributed_tracing",
            "alerting",
            "dashboards"
        ]
        license_data["limitations"] = [
            "evaluation_only",
            "no_production_use",
            "no_redistribution",
            "single_customer_use"
        ]
        
    elif license_type == "permanent":
        license_data["expires"] = None
        license_data["features"] = [
            "metrics_monitoring",
            "logs_aggregation",
            "distributed_tracing",
            "alerting",
            "dashboards",
            "source_code_access",
            "unlimited_users",
            "priority_support"
        ]
        license_data["limitations"] = []
        
    elif license_type == "annual":
        expire_date = now + timedelta(days=365)
        license_data["expires"] = expire_date.isoformat()
        license_data["features"] = [
            "metrics_monitoring",
            "logs_aggregation",
            "distributed_tracing",
            "alerting",
            "dashboards",
            "standard_support",
            "updates_included"
        ]
        license_data["limitations"] = ["annual_renewal_required"]
    
    # Generar firma
    content = json.dumps(license_data, sort_keys=True)
    license_hash = hashlib.sha256((content + JWT_SECRET).encode()).hexdigest()
    license_data["signature"] = license_hash
    
    # Codificar licencia
    encoded = base64.b64encode(json.dumps(license_data).encode()).decode()
    
    return {
        "license_key": encoded,
        "license_data": license_data
    }

# ============================================================================
# LICENSE VALIDATION
# ============================================================================

def validate_license(license_key):
    """
    Valida una licencia Rhinometric
    
    Args:
        license_key: Licencia codificada en Base64
    
    Returns:
        tuple: (is_valid, license_data or error_message)
    """
    try:
        # Decodificar
        decoded = base64.b64decode(license_key)
        license_data = json.loads(decoded)
        
        # Verificar campos requeridos
        required_fields = ["customer", "type", "issued", "product", "signature"]
        for field in required_fields:
            if field not in license_data:
                return False, f"Missing required field: {field}"
        
        # Verificar firma
        temp_data = license_data.copy()
        original_signature = temp_data.pop("signature")
        content = json.dumps(temp_data, sort_keys=True)
        expected_signature = hashlib.sha256((content + JWT_SECRET).encode()).hexdigest()
        
        if original_signature != expected_signature:
            return False, "Invalid signature"
        
        # Verificar expiración
        if license_data.get("expires"):
            expire_date = datetime.fromisoformat(license_data["expires"])
            if datetime.utcnow() > expire_date:
                days_expired = (datetime.utcnow() - expire_date).days
                return False, f"License expired {days_expired} days ago"
        
        # Validación exitosa
        return True, license_data
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

# ============================================================================
# EMAIL DELIVERY
# ============================================================================

def send_license_email(customer_email, customer_name, license_key, license_data):
    """
    Envía la licencia por email al cliente
    
    Args:
        customer_email: Email del cliente
        customer_name: Nombre del cliente
        license_key: Clave de licencia codificada
        license_data: Datos de la licencia (dict)
    
    Returns:
        bool: True si el email se envió exitosamente
    """
    if not SMTP_ENABLED:
        logger.warning("⚠️  SMTP not configured, skipping email. Set SMTP_USER and SMTP_PASSWORD env vars.")
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Rhinometric Licenses <{SMTP_FROM}>"
        msg['To'] = customer_email
        msg['Subject'] = f"🦏 Your Rhinometric License - {customer_name}"
        msg['Date'] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        # Formatear fecha de expiración
        expires_str = "N/A"
        if license_data.get('expires'):
            try:
                expires_dt = datetime.fromisoformat(license_data['expires'])
                expires_str = expires_dt.strftime('%B %d, %Y')
            except:
                expires_str = license_data['expires']
        
        # Features como lista
        features = license_data.get('features', [])
        features_html = "".join([f"<li>{f}</li>" for f in features])
        features_text = "\n        • ".join(features)
        
        # HTML template
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6; 
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 600px; 
            margin: 20px auto; 
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{ 
            background: linear-gradient(135deg, #1a73e8 0%, #34a853 100%); 
            color: white; 
            padding: 40px 30px; 
            text-align: center;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 32px;
            font-weight: 600;
        }}
        .header p {{
            margin: 0;
            font-size: 16px;
            opacity: 0.95;
        }}
        .content {{ 
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #1a73e8;
            margin-bottom: 20px;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h3 {{
            color: #1a73e8;
            margin: 0 0 15px 0;
            font-size: 16px;
            font-weight: 600;
        }}
        .info-grid {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #1a73e8;
        }}
        .info-row {{
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
        }}
        .info-label {{
            font-weight: 600;
            color: #5f6368;
        }}
        .info-value {{
            color: #1a73e8;
            font-weight: 500;
        }}
        .license-box {{ 
            background: #f8f9fa;
            padding: 20px; 
            margin: 20px 0; 
            border-radius: 6px; 
            border: 2px dashed #1a73e8;
            word-break: break-all;
        }}
        .license-key {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #202124;
            line-height: 1.8;
        }}
        .warning-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .warning-box strong {{
            color: #856404;
        }}
        .steps {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
        }}
        .steps ol {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .steps li {{
            margin: 8px 0;
            color: #202124;
        }}
        .button {{ 
            display: inline-block; 
            padding: 14px 28px; 
            background: #1a73e8; 
            color: white !important;
            text-decoration: none; 
            border-radius: 6px; 
            margin: 20px 0;
            font-weight: 600;
            transition: background 0.3s;
        }}
        .button:hover {{
            background: #1557b0;
        }}
        .features-list {{
            list-style: none;
            padding: 0;
            margin: 10px 0;
        }}
        .features-list li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }}
        .features-list li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #34a853;
            font-weight: bold;
        }}
        .footer {{ 
            background: #f8f9fa;
            text-align: center; 
            padding: 30px;
            color: #5f6368; 
            font-size: 13px;
        }}
        .footer p {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦏 Welcome to Rhinometric!</h1>
            <p>Your Observability Platform License</p>
        </div>
        
        <div class="content">
            <div class="greeting">
                Hello {customer_name}! 👋
            </div>
            
            <p style="margin-bottom: 20px;">
                Thank you for choosing <strong>Rhinometric Observability Platform</strong>. 
                Your license has been generated and is ready to use.
            </p>
            
            <div class="section">
                <h3>📋 License Details</h3>
                <div class="info-grid">
                    <div class="info-row">
                        <span class="info-label">Type:</span>
                        <span class="info-value">{license_data.get('type', 'trial').upper()}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Valid Until:</span>
                        <span class="info-value">{expires_str}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Product:</span>
                        <span class="info-value">{license_data.get('product', 'Rhinometric')}</span>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>✨ Included Features</h3>
                <ul class="features-list">
                    {features_html}
                </ul>
            </div>
            
            <div class="section">
                <h3>🔑 Your License Key</h3>
                <div class="license-box">
                    <div class="license-key">{license_key}</div>
                </div>
            </div>
            
            <div class="warning-box">
                <strong>⚠️ Important:</strong> Keep this license key secure and confidential. 
                You will need it to activate your Rhinometric installation.
            </div>
            
            <div class="section">
                <h3>🚀 Next Steps</h3>
                <div class="steps">
                    <ol>
                        <li>Download the installer from <a href="https://github.com/Rafael2712/mi-proyecto/releases">GitHub Releases</a></li>
                        <li>Run the installer on your server (Linux, Windows, or Mac)</li>
                        <li>Enter this license key when prompted</li>
                        <li>Access your dashboard at <strong>http://your-server:3000</strong></li>
                        <li>Login with username: <strong>admin</strong> / password: <strong>admin</strong></li>
                    </ol>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://github.com/Rafael2712/mi-proyecto/wiki/Quick-Start" class="button">
                    📚 Read Quickstart Guide
                </a>
            </div>
            
            <p style="margin-top: 30px; color: #5f6368;">
                Need help? Our support team is here for you:<br>
                📧 Email: <a href="mailto:support@rhinometric.io">support@rhinometric.io</a><br>
                📖 Docs: <a href="https://github.com/Rafael2712/mi-proyecto/wiki">github.com/Rafael2712/mi-proyecto/wiki</a>
            </p>
        </div>
        
        <div class="footer">
            <p><strong>Rhinometric Observability Platform v2.5.0</strong></p>
            <p>Enterprise-grade monitoring, logging, and tracing</p>
            <p style="margin-top: 15px;">© 2025 Rhinometric. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Plain text fallback
        text = f"""
🦏 Welcome to Rhinometric!

Hello {customer_name},

Thank you for choosing Rhinometric Observability Platform. Your license has been generated:

📋 LICENSE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type:           {license_data.get('type', 'trial').upper()}
Valid Until:    {expires_str}
Product:        {license_data.get('product', 'Rhinometric')}

✨ INCLUDED FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        • {features_text}

🔑 YOUR LICENSE KEY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{license_key}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  IMPORTANT: Keep this license key secure and confidential.

🚀 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Download installer from: https://github.com/Rafael2712/mi-proyecto/releases
2. Run installer on your server (Linux, Windows, or Mac)
3. Enter license key when prompted
4. Access dashboard at: http://your-server:3000
5. Login with: admin / admin (change on first login)

📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quickstart: https://github.com/Rafael2712/mi-proyecto/wiki/Quick-Start
Full Docs:  https://github.com/Rafael2712/mi-proyecto/wiki

💬 SUPPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email: support@rhinometric.io
Docs:  github.com/Rafael2712/mi-proyecto/wiki

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rhinometric Observability Platform v2.5.0
© 2025 Rhinometric. All rights reserved.
        """
        
        # Adjuntar ambas versiones
        msg.attach(MIMEText(text, 'plain', 'utf-8'))
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        
        # Enviar email via SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ License email sent successfully to {customer_email}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error sending license email to {customer_email}: {e}")
        return False

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Rhinometric License Server",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route('/api/license/generate', methods=['POST'])
def api_generate_license():
    """
    Genera una nueva licencia y opcionalmente la envía por email
    
    Body:
    {
        "customer_name": "Ayuntamiento de Madrid",
        "customer_email": "admin@madrid.es",  // OPCIONAL - Si se incluye, envía email
        "license_type": "trial",
        "days": 180
    }
    """
    try:
        data = request.get_json()
        
        customer_name = data.get('customer_name')
        customer_email = data.get('customer_email')  # Nuevo campo opcional
        license_type = data.get('license_type', 'trial')
        days = data.get('days')
        
        if not customer_name:
            return jsonify({"error": "customer_name is required"}), 400
        
        # Generar licencia
        result = generate_license(customer_name, license_type, days)
        license_key = result['license_key']
        license_data = result['license_data']
        
        # Guardar en base de datos
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO licenses (customer_name, license_key, license_type, expires_at, features)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_name) 
                DO UPDATE SET 
                    license_key = EXCLUDED.license_key,
                    license_type = EXCLUDED.license_type,
                    expires_at = EXCLUDED.expires_at,
                    features = EXCLUDED.features,
                    issued_at = CURRENT_TIMESTAMP,
                    is_active = TRUE
                RETURNING id
            """, (
                customer_name,
                license_key,
                license_type,
                license_data.get('expires'),
                json.dumps(license_data.get('features', []))
            ))
            license_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ License generated for {customer_name} (ID: {license_id})")
        
        # Enviar email si se proporcionó customer_email
        email_sent = False
        if customer_email:
            logger.info(f"📧 Sending license email to {customer_email}...")
            email_sent = send_license_email(
                customer_email,
                customer_name,
                license_key,
                {
                    'type': license_type,
                    'expires': license_data.get('expires'),
                    'product': license_data.get('product', 'Rhinometric Observability Platform'),
                    'features': license_data.get('features', [])
                }
            )
            if email_sent:
                logger.info(f"✅ Email sent successfully to {customer_email}")
            else:
                logger.warning(f"⚠️  Failed to send email to {customer_email}")
        
        response = {
            "success": True,
            "customer": customer_name,
            "license_key": license_key,
            "license_type": license_type,
            "expires": license_data.get('expires'),
            "features": license_data.get('features'),
            "message": f"🦏 Rhinometric {license_type} license generated for {customer_name}"
        }
        
        # Agregar info de email al response
        if customer_email:
            response["email_sent"] = email_sent
            response["email_to"] = customer_email
        
        return jsonify(response), 201
        
    except Exception as e:
        logger.error(f"Error generating license: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/license/validate', methods=['POST'])
def api_validate_license():
    """
    Valida una licencia
    
    Body:
    {
        "license_key": "base64_encoded_license"
    }
    """
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        
        if not license_key:
            return jsonify({"error": "license_key is required"}), 400
        
        # Validar licencia
        is_valid, result = validate_license(license_key)
        
        if not is_valid:
            return jsonify({
                "valid": False,
                "error": result
            }), 200
        
        license_data = result
        
        # Actualizar contador de validaciones
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE licenses 
                SET validation_count = validation_count + 1,
                    last_validation = CURRENT_TIMESTAMP
                WHERE customer_name = %s
            """, (license_data['customer'],))
            conn.commit()
            cursor.close()
            conn.close()
        
        # Calcular días restantes
        days_remaining = None
        if license_data.get('expires'):
            expire_date = datetime.fromisoformat(license_data['expires'])
            days_remaining = (expire_date - datetime.utcnow()).days
        
        return jsonify({
            "valid": True,
            "customer": license_data['customer'],
            "type": license_data['type'],
            "expires": license_data.get('expires'),
            "days_remaining": days_remaining,
            "features": license_data.get('features'),
            "limitations": license_data.get('limitations'),
            "message": f"✅ Valid {license_data['type']} license for {license_data['customer']}"
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating license: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/license/status/<customer_name>', methods=['GET'])
def api_license_status(customer_name):
    """Obtiene el estado de una licencia por nombre de cliente"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT customer_name, license_type, issued_at, expires_at, 
                   is_active, validation_count, last_validation
            FROM licenses
            WHERE customer_name = %s
        """, (customer_name,))
        
        license_info = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not license_info:
            return jsonify({"error": "License not found"}), 404
        
        # Calcular días restantes
        days_remaining = None
        if license_info['expires_at']:
            days_remaining = (license_info['expires_at'] - datetime.utcnow()).days
        
        return jsonify({
            "customer": license_info['customer_name'],
            "type": license_info['license_type'],
            "issued": license_info['issued_at'].isoformat(),
            "expires": license_info['expires_at'].isoformat() if license_info['expires_at'] else None,
            "days_remaining": days_remaining,
            "active": license_info['is_active'],
            "validations": license_info['validation_count'],
            "last_validation": license_info['last_validation'].isoformat() if license_info['last_validation'] else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting license status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/license/list', methods=['GET'])
def api_list_licenses():
    """Lista todas las licencias"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT customer_name, license_type, issued_at, expires_at, 
                   is_active, validation_count
            FROM licenses
            ORDER BY issued_at DESC
        """)
        
        licenses = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Formatear respuesta
        result = []
        for lic in licenses:
            days_remaining = None
            if lic['expires_at']:
                days_remaining = (lic['expires_at'] - datetime.utcnow()).days
            
            result.append({
                "customer": lic['customer_name'],
                "type": lic['license_type'],
                "issued": lic['issued_at'].isoformat(),
                "expires": lic['expires_at'].isoformat() if lic['expires_at'] else None,
                "days_remaining": days_remaining,
                "active": lic['is_active'],
                "validations": lic['validation_count']
            })
        
        return jsonify({
            "total": len(result),
            "licenses": result
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing licenses: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

if __name__ == '__main__':
    print_banner()
    
    # Inicializar base de datos
    init_database()
    
    # Iniciar servidor
    port = int(os.getenv('PORT', '5000'))
    logger.info(f"🚀 Starting Rhinometric License Server on port {port}")
    logger.info(f"📧 Support: soporte@rhinometric.com")
    logger.info(f"💼 Sales: ventas@rhinometric.com")
    
    app.run(host='0.0.0.0', port=port, debug=False)
