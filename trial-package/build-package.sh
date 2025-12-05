#!/bin/bash
#
# RHINOMETRIC TRIAL V1.0 - PACKAGE BUILDER
# Crea el paquete distributable para clientes
#

set -e

VERSION="1.0.0"
PACKAGE_NAME="rhinometric-trial-v${VERSION}-production"
BUILD_DIR="build"
PACKAGE_DIR="$BUILD_DIR/$PACKAGE_NAME"

echo "════════════════════════════════════════════════════════════"
echo "  RHINOMETRIC TRIAL PACKAGE BUILDER"
echo "  Version: $VERSION"
echo "════════════════════════════════════════════════════════════"
echo ""

# Limpiar build anterior
if [ -d "$BUILD_DIR" ]; then
    echo "🗑️  Limpiando build anterior..."
    rm -rf "$BUILD_DIR"
fi

# Crear estructura
echo "📁 Creando estructura de directorios..."
mkdir -p "$PACKAGE_DIR"

# Copiar archivos esenciales
echo "📋 Copiando archivos principales..."
cp docker-compose.yml "$PACKAGE_DIR/"
cp .env.example "$PACKAGE_DIR/.env" 2>/dev/null || echo "# License Server Configuration" > "$PACKAGE_DIR/.env"

# Dockerfiles
echo "🐳 Copiando Dockerfiles..."
cp Dockerfile.grafana-timebomb "$PACKAGE_DIR/"
cp -r licensing "$PACKAGE_DIR/"
cp -r grafana "$PACKAGE_DIR/"
cp -r prometheus "$PACKAGE_DIR/"

# Configuraciones
echo "⚙️  Copiando configuraciones..."
mkdir -p "$PACKAGE_DIR/config"
cp config/prometheus-saas.yml "$PACKAGE_DIR/config/" 2>/dev/null || echo "WARNING: prometheus config not found"
cp config/loki-saas.yml "$PACKAGE_DIR/config/" 2>/dev/null || echo "WARNING: loki config not found"
cp config/tempo-saas.yml "$PACKAGE_DIR/config/" 2>/dev/null || echo "WARNING: tempo config not found"
cp config/alertmanager-saas.yml "$PACKAGE_DIR/config/" 2>/dev/null || echo "WARNING: alertmanager config not found"
cp config/nginx-trial.conf "$PACKAGE_DIR/config/" 2>/dev/null || echo "WARNING: nginx config not found"
cp config/promtail-config.yml "$PACKAGE_DIR/config/" 2>/dev/null || echo "WARNING: promtail config not found"
cp config/blackbox.yml "$PACKAGE_DIR/config/" 2>/dev/null || echo "WARNING: blackbox config not found"

# Init DB
if [ -d "init-db" ]; then
    echo "💾 Copiando init scripts DB..."
    cp -r init-db "$PACKAGE_DIR/"
fi

# Ejemplos
if [ -d "examples" ]; then
    echo "📝 Copiando ejemplos de integración..."
    cp -r examples "$PACKAGE_DIR/"
fi

# Installers
if [ -d "installers" ]; then
    echo "💿 Copiando instaladores multi-plataforma..."
    cp -r installers "$PACKAGE_DIR/"
fi

# Documentación
echo "📚 Copiando documentación..."
cp README.md "$PACKAGE_DIR/" 2>/dev/null || echo "WARNING: README not found"
cp PRODUCTION_READY.md "$PACKAGE_DIR/"
cp TIMEBOMB_IMPLEMENTATION.md "$PACKAGE_DIR/"
cp RELEASE_VALIDATION.md "$PACKAGE_DIR/"
cp INTEGRATION_GUIDE.md "$PACKAGE_DIR/" 2>/dev/null || echo "WARNING: INTEGRATION_GUIDE not found"
cp SECURITY_AUDIT.md "$PACKAGE_DIR/" 2>/dev/null || echo "WARNING: SECURITY_AUDIT not found"
cp PRUEBA_LOCAL.md "$PACKAGE_DIR/" 2>/dev/null || echo "WARNING: PRUEBA_LOCAL not found"
cp WELCOME.html "$PACKAGE_DIR/" 2>/dev/null || echo "WARNING: WELCOME.html not found"

# Scripts útiles
echo "🔧 Copiando scripts..."
cp test-timebomb.sh "$PACKAGE_DIR/" 2>/dev/null || echo "WARNING: test-timebomb not found"
cat > "$PACKAGE_DIR/start.sh" << 'EOF'
#!/bin/bash
echo "🚀 Starting Rhinometric Trial..."
docker compose up -d
sleep 10
echo ""
echo "✅ Rhinometric Trial started!"
echo "🌐 Grafana: http://localhost:3000"
echo "📊 Prometheus: http://localhost:9090"
echo "🔒 License Server: http://localhost:5000"
echo ""
echo "Credentials:"
echo "  User: admin"
echo "  Pass: admin_trial_2024"
EOF
chmod +x "$PACKAGE_DIR/start.sh"

cat > "$PACKAGE_DIR/stop.sh" << 'EOF'
#!/bin/bash
echo "🛑 Stopping Rhinometric Trial..."
docker compose down
echo "✅ Stopped!"
EOF
chmod +x "$PACKAGE_DIR/stop.sh"

cat > "$PACKAGE_DIR/status.sh" << 'EOF'
#!/bin/bash
echo "📊 Rhinometric Trial Status"
echo "════════════════════════════════════════════════════════════"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep rhinometric
echo ""
echo "License Status:"
curl -s http://localhost:5000/status | jq . 2>/dev/null || echo "License server not responding"
EOF
chmod +x "$PACKAGE_DIR/status.sh"

# README específico del package
cat > "$PACKAGE_DIR/README-PACKAGE.txt" << EOF
═══════════════════════════════════════════════════════════════
  RHINOMETRIC TRIAL v${VERSION}
  Observability Platform - 30 Days Trial
═══════════════════════════════════════════════════════════════

📦 CONTENIDO DEL PACKAGE:

1. Docker Compose setup completo
2. License Server con Time-Bomb protection
3. Grafana con Time-Bomb Validator
4. Prometheus, Loki, Tempo (observability stack)
5. 6 dashboards precargados
6. Documentación completa
7. Ejemplos de integración (Python, Node.js)
8. Instaladores multi-plataforma

🚀 INICIO RÁPIDO:

1. Requisitos:
   - Docker Engine 20.10+ o Docker Desktop
   - Docker Compose v2.0+
   - 4 GB RAM mínimo
   - 10 GB espacio en disco

2. Instalación:
   $ cd $PACKAGE_NAME
   $ docker compose up -d

3. Acceso:
   Grafana: http://localhost:3000
   Usuario: admin
   Password: admin_trial_2024

4. Validar:
   $ ./status.sh

📚 DOCUMENTACIÓN:

- PRODUCTION_READY.md      → Guía completa de despliegue
- TIMEBOMB_IMPLEMENTATION.md → Arquitectura técnica
- RELEASE_VALIDATION.md    → Validación de release
- INTEGRATION_GUIDE.md     → Integración con aplicaciones
- SECURITY_AUDIT.md        → Análisis de seguridad

🔒 PROTECCIÓN:

- Hardware Fingerprinting: Licencia vinculada a hardware
- Time-Bomb Validator: Validación cada 6 horas
- Vigencia: 30 días desde instalación
- Auto-shutdown: Al detectar violación

⚠️  IMPORTANTE:

- Este es un TRIAL limitado a 30 días
- La licencia está vinculada al hardware
- NO copiar a otra máquina
- Para licencia completa: sales@rhinometric.com

📞 SOPORTE:

Ventas: sales@rhinometric.com
Soporte: support@rhinometric.com
Docs: https://docs.rhinometric.com

═══════════════════════════════════════════════════════════════
Version: ${VERSION}
Released: $(date +"%Y-%m-%d")
═══════════════════════════════════════════════════════════════
EOF

# Crear archivos comprimidos
echo ""
echo "📦 Creando archivos comprimidos..."

cd "$BUILD_DIR"

# TAR.GZ para Linux/Mac
echo "   → Creando ${PACKAGE_NAME}.tar.gz..."
tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
TAR_SIZE=$(du -h "${PACKAGE_NAME}.tar.gz" | cut -f1)

# ZIP para Windows
echo "   → Creando ${PACKAGE_NAME}.zip..."
zip -q -r "${PACKAGE_NAME}.zip" "$PACKAGE_NAME"
ZIP_SIZE=$(du -h "${PACKAGE_NAME}.zip" | cut -f1)

cd ..

# Generar checksums
echo ""
echo "🔐 Generando checksums..."
cd "$BUILD_DIR"
sha256sum "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}.tar.gz.sha256"
sha256sum "${PACKAGE_NAME}.zip" > "${PACKAGE_NAME}.zip.sha256"
cd ..

# Resumen
echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ PACKAGE CREADO EXITOSAMENTE"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📦 Archivos generados:"
echo "   → ${PACKAGE_NAME}.tar.gz ($TAR_SIZE)"
echo "   → ${PACKAGE_NAME}.zip ($ZIP_SIZE)"
echo ""
echo "📁 Ubicación: $BUILD_DIR/"
echo ""
echo "🔐 Checksums:"
cat "$BUILD_DIR/${PACKAGE_NAME}.tar.gz.sha256"
cat "$BUILD_DIR/${PACKAGE_NAME}.zip.sha256"
echo ""
echo "🚀 Listo para distribución a clientes!"
echo "════════════════════════════════════════════════════════════"
