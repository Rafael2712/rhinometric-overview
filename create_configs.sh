#!/bin/bash

# Crear directorio config si no existe
mkdir -p ./config

# Crear traefik.yml
cat << 'EOF' > ./config/traefik.yml
entryPoints:
  web:
    address: ":80"
providers:
  docker: {}
EOF

# Crear alertmanager.yml
cat << 'EOF' > ./config/alertmanager.yml
global:
  resolve_timeout: 5m
route:
  receiver: 'default'
receivers:
  - name: 'default'
EOF

# Crear promtail-config.yml
cat << 'EOF' > ./config/promtail-config.yml
server:
  http_listen_port: 9080
positions:
  filename: /tmp/positions.yaml
clients:
  - url: http://loki:3100/loki/api/v1/push
scrape_configs:
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: varlogs
          __path__: /var/log/*log
EOF

# Crear blackbox.yml
cat << 'EOF' > ./config/blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_status_codes: [200, 201]
EOF

# Establecer permisos (opcional, descomenta si hay problemas)
# chmod 644 ./config/*

echo "Archivos de configuración creados en ./config/"
