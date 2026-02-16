#!/usr/bin/env python3
"""
Genera prometheus.yml LIMPIO basado en servicios reales del docker-compose
"""
import subprocess
import yaml

# Obtener servicios activos del docker-compose
result = subprocess.run(
    ['docker-compose', '-f', 'docker-compose-v2.5.0.yml', 'config', '--services'],
    capture_output=True,
    text=True
)

services = result.stdout.strip().split('\n')
print(f"✅ Encontrados {len(services)} servicios en docker-compose")

# Configuración base de Prometheus
config = {
    'global': {
        'scrape_interval': '15s',
        'evaluation_interval': '15s',
        'external_labels': {
            'cluster': 'rhinometric-v2.5.0',
            'environment': 'production'
        }
    },
    'alerting': {
        'alertmanagers': [{
            'static_configs': [{
                'targets': ['alertmanager:9093']
            }]
        }]
    },
    'rule_files': [
        '/etc/prometheus/rules/*.yml'
    ],
    'scrape_configs': []
}

# Core infrastructure
core_jobs = {
    'prometheus': ('localhost:9090', 15),
    'grafana': ('grafana:3000', 30),
    'alertmanager': ('alertmanager:9093', 30),
    'loki': ('loki:3100', 30),
    'node-exporter': ('node-exporter:9100', 30),
    'cadvisor': ('cadvisor:8080', 30),
    'otel-collector': ('otel-collector:8889', 30),
}

for job, (target, interval) in core_jobs.items():
    config['scrape_configs'].append({
        'job_name': job,
        'static_configs': [{'targets': [target]}],
        'scrape_interval': f'{interval}s'
    })

# Database collectors
for service in services:
    if 'database-collector' in service or 'postgres-exporter' in service:
        port = 9187 if 'postgres-exporter' in service else 9332  # default
        config['scrape_configs'].append({
            'job_name': service,
            'static_configs': [{'targets': [f'{service}:{port}']}],
            'scrape_interval': '15s',
            'labels': {'service_type': 'database_collector'}
        })

# Webhook collectors
for service in services:
    if 'webhook-collector' in service or 'webhook-test' in service:
        config['scrape_configs'].append({
            'job_name': service,
            'static_configs': [{'targets': [f'{service}:9326']}],
            'scrape_interval': '15s',
            'labels': {'service_type': 'webhook'}
        })

# AI services
if 'rhinometric-ai-anomaly' in services:
    config['scrape_configs'].append({
        'job_name': 'ai-anomaly-detector',
        'static_configs': [{'targets': ['rhinometric-ai-anomaly:9090']}],
        'scrape_interval': '30s',
        'labels': {'component': 'ai'}
    })

# Rhinometric Console
if 'rhinometric-console-backend' in services:
    config['scrape_configs'].append({
        'job_name': 'rhinometric-console',
        'static_configs': [{'targets': ['rhinometric-console-backend:8105']}],
        'scrape_interval': '30s',
        'labels': {'component': 'console'}
    })

# Escribir archivo
with open('config/prometheus-v2.2.yml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print(f"\n✅ Generado prometheus.yml con {len(config['scrape_configs'])} jobs")
print("📊 Jobs incluidos:")
for job in config['scrape_configs']:
    print(f"   - {job['job_name']}")
