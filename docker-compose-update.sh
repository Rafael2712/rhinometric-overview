#!/bin/bash
# Hacer backup
cp docker-compose.yml docker-compose.yml.bak2

# Actualizar la sección de promtail para incluir logs locales
sed -i '/mi-proyecto-promtail-1:/,/restart:/{
  /volumes:/a\      - ./logs:/app/logs:ro
}' docker-compose.yml
