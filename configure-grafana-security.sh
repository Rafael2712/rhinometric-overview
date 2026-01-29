#!/bin/bash
set -e

echo "=== Configurando Seguridad de Grafana ==="

# 1. Cambiar password de admin
NEW_ADMIN_PASS="Rhino2026SecureAdmin"
echo "Cambiando password de admin..."
docker exec rhinometric-grafana grafana cli admin reset-admin-password "$NEW_ADMIN_PASS"
echo "✓ Password de admin cambiado"

# 2. Crear usuario console-viewer con rol Viewer
echo "Creando usuario console-viewer..."
docker exec rhinometric-grafana grafana cli admin users create \
  --login console-viewer \
  --password "ConsoleView2026Secure" \
  --email "console@rhinometric.internal" \
  --role Viewer 2>/dev/null || echo "Usuario ya existe"

echo "✓ Usuario console-viewer creado (password: ConsoleView2026Secure)"

# 3. Reiniciar Grafana para aplicar cambios de anonymous
echo "Reiniciando Grafana..."
cd /opt/rhinometric
docker compose -f docker-compose-v2.5.0.yml restart grafana
sleep 10

# 4. Verificar estado
docker ps | grep grafana

echo ""
echo "=== Configuración Completa ==="
echo "Admin user: admin"
echo "Admin pass: $NEW_ADMIN_PASS"
echo ""
echo "Console user: console-viewer"  
echo "Console pass: ConsoleView2026Secure"
echo ""
echo "Anonymous access: DISABLED"
