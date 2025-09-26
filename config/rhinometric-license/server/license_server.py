from flask import Flask, request, jsonify
import jwt
import sqlite3
from datetime import datetime, timedelta
import hashlib
import uuid

app = Flask(__name__)
SECRET_KEY = "rhinometric-2025-secret-key"
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

@app.route('/generate', methods=['POST'])
def generate_license():
    data = request.json
    client_name = data.get('client_name')
    license_type = data.get('type', 'trial')
    hardware_id = data.get('hardware_id')
    
    # Generar ID único
    client_id = str(uuid.uuid4())
    
    # Calcular expiración
    if license_type == 'trial':
        expires = datetime.now() + timedelta(days=15)
    elif license_type == 'annual':
        expires = datetime.now() + timedelta(days=365)
    else:  # permanent
        expires = datetime.now() + timedelta(days=36500)
    
    # Crear token
    payload = {
        'client_id': client_id,
        'client_name': client_name,
        'type': license_type,
        'hardware_id': hardware_id,
        'exp': expires.timestamp()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    # Guardar en DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO licenses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (client_id, client_name, client_id, license_type, hardware_id,
               datetime.now(), expires, None, 'active'))
    conn.commit()
    conn.close()
    
    return jsonify({
        'license_key': token,
        'client_id': client_id,
        'expires': expires.isoformat()
    })

@app.route('/validate', methods=['POST'])
def validate_license():
    token = request.json.get('license_key')
    hardware_id = request.json.get('hardware_id')
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        # Verificar hardware
        if payload.get('hardware_id') != hardware_id:
            return jsonify({'valid': False, 'reason': 'Hardware mismatch'}), 403
        
        # Verificar expiración
        if datetime.fromtimestamp(payload['exp']) < datetime.now():
            return jsonify({'valid': False, 'reason': 'Expired'}), 403
        
        # Actualizar último check
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE licenses SET last_check = ? WHERE client_id = ?',
                  (datetime.now(), payload['client_id']))
        conn.commit()
        conn.close()
        
        return jsonify({'valid': True, 'expires': payload['exp']})
    
    except Exception as e:
        return jsonify({'valid': False, 'reason': str(e)}), 403

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
