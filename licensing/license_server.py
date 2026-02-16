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
    Genera una nueva licencia
    
    Body:
    {
        "customer_name": "Ayuntamiento de Madrid",
        "license_type": "trial",
        "days": 180
    }
    """
    try:
        data = request.get_json()
        
        customer_name = data.get('customer_name')
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
        
        return jsonify({
            "success": True,
            "customer": customer_name,
            "license_key": license_key,
            "license_type": license_type,
            "expires": license_data.get('expires'),
            "features": license_data.get('features'),
            "message": f"🦏 Rhinometric trial license generated for {customer_name}"
        }), 201
        
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
