#!/usr/bin/env python3
"""
Rhinometric License Dashboard - Versión Trial
Dashboard web para monitorizar licencias
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Configuración
DB_PATH = os.getenv('LICENSE_DB_PATH', '/data/licenses.db')
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 8080))

@app.route('/')
def index():
    """Página principal del dashboard"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "OK", "service": "license-dashboard"})

@app.route('/api/licenses')
def get_licenses():
    """Obtener todas las licencias"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM licenses
            ORDER BY created_at DESC
        """)
        
        licenses = []
        for row in cursor.fetchall():
            license_dict = dict(row)
            
            # Calcular días restantes
            if license_dict.get('expires_at'):
                try:
                    expires = datetime.fromisoformat(license_dict['expires_at'])
                    days_remaining = (expires - datetime.now()).days
                    license_dict['days_remaining'] = days_remaining
                    license_dict['is_expired'] = days_remaining < 0
                    license_dict['is_expiring_soon'] = 0 <= days_remaining <= 30
                except:
                    license_dict['days_remaining'] = None
                    license_dict['is_expired'] = False
                    license_dict['is_expiring_soon'] = False
            
            licenses.append(license_dict)
        
        conn.close()
        return jsonify({"licenses": licenses, "total": len(licenses)})
        
    except sqlite3.OperationalError as e:
        # Base de datos no existe aún
        return jsonify({"licenses": [], "total": 0, "note": "No licenses yet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Obtener estadísticas de licencias"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total de licencias
        cursor.execute("SELECT COUNT(*) FROM licenses")
        total = cursor.fetchone()[0]
        
        # Licencias activas
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE status = 'active'")
        active = cursor.fetchone()[0]
        
        # Licencias expiradas (calculado desde expires_at)
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE expires_at < ?", (datetime.now().isoformat(),))
        expired = cursor.fetchone()[0]
        
        # Licencias trial
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE license_type = 'trial'")
        trial = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "total": total,
            "active": active,
            "expired": expired,
            "trial": trial
        })
        
    except sqlite3.OperationalError:
        return jsonify({"total": 0, "active": 0, "expired": 0, "trial": 0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Rhinometric License Dashboard starting...")
    print(f"📁 Database: {DB_PATH}")
    print(f"🌐 Port: {DASHBOARD_PORT}")
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=False)
