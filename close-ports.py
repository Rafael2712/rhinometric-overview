import yaml

# Leer archivo original
with open('docker-compose-v2.5.0-PRODUCTION.yml', 'r') as f:
    data = yaml.safe_load(f)

# Eliminar TODAS las secciones 'ports' de TODOS los servicios
for service_name, service_config in data.get('services', {}).items():
    if 'ports' in service_config:
        del service_config['ports']
        print(f'Puertos eliminados de: {service_name}')

# Guardar
with open('docker-compose-v2.5.0-SECURE.yml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print('\n✅ Archivo SECURE creado - TODOS los puertos cerrados')
