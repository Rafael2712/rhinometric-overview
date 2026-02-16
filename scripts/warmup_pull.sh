#!/usr/bin/env bash
set -euo pipefail

# Reemplaza TU_ORG si ya tienes GHCR/ECR/Harbor configurado
REG="ghcr.io/TU_ORG"

# Lista de imágenes del trial (ejemplos)
IMAGES=(
  "$REG/mi-proyecto-grafana:trial"
  "$REG/mi-proyecto-prometheus:trial"
  "$REG/mi-proyecto-alertmanager:trial"
  "$REG/mi-proyecto-loki:trial"
  "$REG/mi-proyecto-promtail:trial"
  "$REG/mi-proyecto-blackbox-exporter:trial"
  "$REG/mi-proyecto-web:trial"
  "$REG/mi-proyecto-cadvisor:trial"
  "$REG/mi-proyecto-node-exporter:trial"
  "$REG/mi-proyecto-mailhog:trial"
)

echo ">> Pre-pull de imágenes (puede tardar la primera vez)..."
for img in "${IMAGES[@]}"; do
  echo " - $img"
  docker pull "$img" || true
done
echo ">> Warmup listo."
