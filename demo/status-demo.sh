#!/usr/bin/env bash
set -euo pipefail
docker compose -f docker-compose.yml -f demo/docker-compose.override.demo.yml ps
echo
echo "Probar salud:"
echo "- Grafana:    curl -s http://127.0.0.1:3002/api/health"
echo "- Prometheus: curl -s http://127.0.0.1:9090/-/ready"
echo "- Loki:       curl -s http://127.0.0.1:3100/ready"
