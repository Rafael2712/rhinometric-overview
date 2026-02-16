#!/usr/bin/env python3
"""
Script para crear silences en Alertmanager para todas las alertas de servicios externos eliminados
"""
import requests
import json
from datetime import datetime, timedelta

ALERTMANAGER_URL = "http://localhost:9093"

# Patrones de servicios externos eliminados
EXTERNAL_SERVICE_PATTERNS = [
    'mqtt-collector',
    'rest-collector-coingecko',
    'rest-collector-catfacts',
    'rest-collector-dog-images',
    'rest-collector-albums',
    'rest-collector-jsonplaceholder',
    'rest-collector-test',
    'rest-collector-posts',
    'rest-collector-public-rest-api',
    'rest-collector-rest-countries',
    'rest-collector-random-activity',
    'rest-collector-working-test',
    'rest-collector-production-test',
    'rest-collector-final-test',
    'rest-collector-api-test',
    'rest-collector-rest-otel',
    'mqtt-collector-iot-sensors',
    'mqtt-collector-mqtt',
    'mqtt-collector-otel',
    'mqtt-collector-eclipse',
    'mqtt-collector-hivemq',
]

def get_active_alerts():
    """Obtiene todas las alertas activas"""
    response = requests.get(f"{ALERTMANAGER_URL}/api/v2/alerts")
    return response.json()

def create_silence(instance_pattern):
    """Crea un silence para un patrón de instancia específico"""
    # Silence por 365 días (hasta que se reinicie Alertmanager)
    starts_at = datetime.utcnow()
    ends_at = starts_at + timedelta(days=365)
    
    silence_data = {
        "matchers": [
            {
                "name": "instance",
                "value": f".*{instance_pattern}.*",
                "isRegex": True,
                "isEqual": True
            }
        ],
        "startsAt": starts_at.isoformat() + "Z",
        "endsAt": ends_at.isoformat() + "Z",
        "createdBy": "cleanup_script",
        "comment": f"Silencing alerts for removed external service: {instance_pattern}"
    }
    
    try:
        response = requests.post(
            f"{ALERTMANAGER_URL}/api/v2/silences",
            json=silence_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 Obteniendo alertas activas...")
    alerts = get_active_alerts()
    
    # Filtrar alertas de servicios externos
    external_alerts = [
        alert for alert in alerts
        if any(pattern in alert['labels'].get('instance', '') for pattern in EXTERNAL_SERVICE_PATTERNS)
    ]
    
    print(f"📊 Total alertas activas: {len(alerts)}")
    print(f"⚠️  Alertas de servicios externos: {len(external_alerts)}")
    
    if not external_alerts:
        print("✅ No hay alertas de servicios externos para silenciar")
        return
    
    # Crear silences para cada patrón
    silences_created = 0
    for pattern in EXTERNAL_SERVICE_PATTERNS:
        success, result = create_silence(pattern)
        if success:
            print(f"✅ Silence creado para: {pattern}")
            silences_created += 1
        else:
            print(f"❌ Error al crear silence para {pattern}: {result}")
    
    print(f"\n✅ Total silences creados: {silences_created}/{len(EXTERNAL_SERVICE_PATTERNS)}")
    print("⏳ Las alertas desaparecerán en 1-2 minutos...")

if __name__ == '__main__':
    main()
