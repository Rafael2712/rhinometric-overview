#!/bin/bash

echo "Logs de Loki (buscando errores de conexión o inicio):"
docker-compose logs loki | tail -50 | grep -i "error\|failed\|warn"

echo "Logs de Promtail (buscando recolecta de logs):"
docker-compose logs promtail | tail -50 | grep -i "error\|failed\|warn\|tailed file"

echo "Logs de Grafana (buscando problemas de datasource):"
docker-compose logs grafana | tail -50 | grep -i "error\|failed\|warn\|loki"

echo "Logs de test-ayuntamiento (para ver si genera logs):"
docker-compose logs test-ayuntamiento | tail -50
