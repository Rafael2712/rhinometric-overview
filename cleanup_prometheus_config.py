#!/usr/bin/env python3
"""
Script para eliminar job_names de servicios externos del prometheus-v2.2.yml
"""
import re

# Servicios a ELIMINAR (basados en nombres de jobs que incluyan estos términos)
SERVICES_TO_REMOVE_PATTERNS = [
    'mqtt-collector',
    'rest-collector-jsonplaceholder',
    'rest-collector-public-rest-api',
    'rest-collector-test',
    'rest-collector-posts-api',
    'rest-collector-final-test',
    'rest-collector-working-test',
    'rest-collector-production-test',
    'rest-collector-api-test',
    'rest-collector-rest-countries',
    'rest-collector-coingecko',
    'rest-collector-catfacts',
    'rest-collector-random-activity',
    'rest-collector-albums',
    'rest-collector-dog-images',
    'rest-collector-rest-otel',
]

def should_remove_job(lines, start_idx):
    """Verifica si un job debe ser eliminado basándose en sus targets"""
    for i in range(start_idx, min(start_idx + 30, len(lines))):
        line = lines[i]
        # Buscar líneas de targets (deben empezar con 'rhinometric-')
        if 'rhinometric-' in line or ('- ' in line and ':9' in line):
            target_line = line.strip()
            # Debe contener exactamente uno de los patrones COMPLETOS
            for pattern in SERVICES_TO_REMOVE_PATTERNS:
                # Asegurar que es un match exacto del contenedor
                if f'rhinometric-{pattern}' in target_line or f'{pattern}:9' in target_line:
                    return True, pattern
    return False, None

def cleanup_prometheus_config():
    filepath = 'config/prometheus-v2.2.yml'
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    i = 0
    jobs_removed = []
    
    while i < len(lines):
        line = lines[i]
        
        # Detectar inicio de job (  - job_name:)
        if line.strip().startswith('- job_name:'):
            job_name = line.split(':', 1)[1].strip()
            should_remove, pattern = should_remove_job(lines, i)
            
            if should_remove:
                print(f"🗑️  Eliminando job: {job_name} (match: {pattern})")
                jobs_removed.append(job_name)
                
                # Saltar todas las líneas de este job hasta el siguiente job o final de sección
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    # Si encontramos otro job_name o regresamos al nivel de indentación 0, terminamos
                    if (next_line.strip().startswith('- job_name:') or 
                        (next_line.strip() and not next_line.startswith(' '))):
                        break
                    i += 1
                continue
        
        cleaned_lines.append(line)
        i += 1
    
    # Escribir archivo limpio
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"\n✅ Limpieza de Prometheus completada")
    print(f"📊 Jobs eliminados: {len(jobs_removed)}")
    for job in jobs_removed:
        print(f"   - {job}")

if __name__ == '__main__':
    cleanup_prometheus_config()
