#!/usr/bin/env python3
"""
Script para eliminar servicios externos de prueba del docker-compose-v2.5.0.yml
"""

# Servicios a ELIMINAR (externos/pruebas)
SERVICES_TO_REMOVE = [
    'mqtt-collector',
    'rest-collector-jsonplaceholder-posts',
    'rest-collector-public-rest-api-for-testing',
    'rest-collector-jsonplaceholder-api',
    'rest-collector-test-deploy',
    'rest-collector-posts-api',
    'rest-collector-final-test',
    'rest-collector-working-test',
    'rest-collector-production-test',
    'rest-collector-jsonplaceholder-users',
    'rest-collector-api-test-nov14',
    'rest-collector-test-comments',
    'rest-collector-test-todos',
    'rest-collector-rest-countries-api---americas-region-data',
    'rest-collector-coingecko-crypto',
    'rest-collector-catfacts',
    'rest-collector-random-activity-suggestions',
    'rest-collector-albums-api',
    'rest-collector-test-final',
    'rest-collector-dog-images',
    'mqtt-collector-mqtt-final-working',
    'mqtt-collector-test-mqtt-production',
    'mqtt-collector-mqtt-production-test',
    'mqtt-collector-mqtt-production-demo',
    'mqtt-collector-mqtt-testing-hivemq',
    'mqtt-collector-mqtt-live-test-e2e',
    'mqtt-collector-mqtt-otel-test',
    'mqtt-collector-otel-trace-demo',
    'rest-collector-rest-otel-demo',
]

def cleanup_docker_compose():
    with open('docker-compose-v2.5.0.yml', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    skip_until_next_service = False
    current_service = None
    
    for i, line in enumerate(lines):
        # Detectar inicio de servicio (2 espacios + nombre + :)
        if line.startswith('  ') and ':' in line and not line.startswith('    '):
            service_name = line.strip().replace(':', '')
            
            if service_name in SERVICES_TO_REMOVE:
                print(f"🗑️  Eliminando: {service_name}")
                skip_until_next_service = True
                current_service = service_name
                continue
            else:
                skip_until_next_service = False
                current_service = service_name
        
        if not skip_until_next_service:
            cleaned_lines.append(line)
    
    # Escribir archivo limpio
    with open('docker-compose-v2.5.0.yml', 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"\n✅ Limpieza completada")
    print(f"📊 Servicios eliminados: {len(SERVICES_TO_REMOVE)}")

if __name__ == '__main__':
    cleanup_docker_compose()
