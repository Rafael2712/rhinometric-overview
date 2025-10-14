#!/bin/bash

echo "Verificando estado de la plataforma..."
docker-compose ps

echo "Contenedores en Restarting o Unhealthy:"
docker-compose ps | grep -i "restarting\|unhealthy"

echo "Puertos mapeados:"
docker-compose ps --format "table {{.Names}}\t{{.Ports}}"
