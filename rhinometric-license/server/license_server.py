from flask import Flask, request, jsonify
import jwt
import sqlite3
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
SECRET_KEY = "rhinometric-2025-secret-key"  # Cambia esto por una clave segura y única
DB_PATH = "/data/licenses.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS licenses
                 (id TEXT PRIMARY KEY,
                  client_name TEXT,
                  client_id TEXT UNIQUE,
                  license_type TEXT,
                  hardware_id TEXT,
                  created_at TIMESTAMP,
                  expires_at TIMESTAMP,
                  last_check TIMESTAMP,
                  status TEXT)''')
    conn.commit()
    conn.close()

init_db()
@app.route('/generate', methods=['POST'])
def generate_license():
    data = request.json
    client_name = data.get('client_name')
    license_type = data.get('type', 'trial')
    hardware_id = data.get('hardware_id')

    if not client_name or not hardware_id:
        return jsonify({"error": "Missing required fields"}), 400

    expires_at = datetime.now() + timedelta(days=30 if license_type == 'trial' else 365 if license_type == 'annual' else 9999)

    payload = {
        'client_name': client_name,
        'license_type': license_type,
        'hardware_id': hardware_id,
        'exp': expires_at.timestamp()
    }

    license_key = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO licenses (id, client_name, client_id, license_type, hardware_id, created_at, expires_at, last_check, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (uuid.uuid4().hex, client_name, uuid.uuid4().hex, license_type, hardware_id, datetime.now(), expires_at, datetime.now(), 'active'))
    conn.commit()
    conn.close()

    return jsonify({"license_key": license_key, "expires": expires_at.isoformat()})
@app.route('/validate', methods=['POST'])
def validate_license():
    data = request.json
    license_key = data.get('license_key')
    hardware_id = data.get('hardware_id')

    try:
        payload = jwt.decode(license_key, SECRET_KEY, algorithms=['HS256'])
        if payload['hardware_id'] != hardware_id:
            return jsonify({"error": "Hardware ID mismatch"}), 401
        if payload['exp'] < datetime.now().timestamp():
            return jsonify({"error": "License expired"}), 403
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE licenses SET last_check = ? WHERE client_id = ?", (datetime.now(), payload.get('client_id', '')))
        conn.commit()
        conn.close()
        return jsonify({"status": "valid", "expires": datetime.fromtimestamp(payload['exp']).isoformat()})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "License expired"}), 403
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid license"}), 401

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
