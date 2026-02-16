from flask import Flask, jsonify
import json
import base64
from datetime import datetime

app = Flask(__name__)

@app.route('/metrics')
def license_metrics():
    # Lee todas las licencias activas
    licenses = []
    with open('/app/licenses.log', 'r') as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            # Cada línea está codificada en base64 con un JSON
            lic = json.loads(base64.b64decode(raw))
            licenses.append({
                'customer': lic['customer'],
                'type': lic['type'],
                'expires': lic['expires'],
                'days_left': (datetime.fromisoformat(lic['expires']) - datetime.now()).days
            })
    return jsonify(licenses)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
