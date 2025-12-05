#!/usr/bin/env bash

# ═══════════════════════════════════════════════════════════════════════════
#  RHINOMETRIC v2.1.0 - PACKAGE CREATOR
# ═══════════════════════════════════════════════════════════════════════════

set -e

VERSION="2.1.0"
PACKAGE_NAME="rhinometric-trial-v${VERSION}-universal"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "═══════════════════════════════════════════════════════════════════════════"
echo "  Creating Rhinometric v${VERSION} Universal Package"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Create temporary directory
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="${TEMP_DIR}/${PACKAGE_NAME}"

echo "▶ Creating package structure..."
mkdir -p "${PACKAGE_DIR}"/{config,grafana/provisioning,init-db,api-proxy,license-server-v2}

# Copy main files
echo "▶ Copying Docker Compose and configs..."
cp docker-compose-v2.1.0.yml "${PACKAGE_DIR}/"
cp install-v2.1.sh "${PACKAGE_DIR}/"
cp validate-v2.1.sh "${PACKAGE_DIR}/"
cp README-v2.1.md "${PACKAGE_DIR}/README.md"
cp nginx.conf "${PACKAGE_DIR}/" 2>/dev/null || true

# Copy config files
echo "▶ Copying configuration files..."
cp config/prometheus-v2.1.yml "${PACKAGE_DIR}/config/"
cp config/loki-v2.1.yml "${PACKAGE_DIR}/config/"
cp config/tempo-v2.1.yml "${PACKAGE_DIR}/config/"
cp config/promtail-v2.1.yml "${PACKAGE_DIR}/config/"
cp config/otel-collector-config.yml "${PACKAGE_DIR}/config/"
cp config/alertmanager.yml "${PACKAGE_DIR}/config/"
cp config/blackbox.yml "${PACKAGE_DIR}/config/"

# Copy Grafana dashboards
echo "▶ Copying Grafana provisioning..."
cp -r grafana/provisioning/* "${PACKAGE_DIR}/grafana/provisioning/" 2>/dev/null || true

# Copy init database
echo "▶ Copying database initialization..."
cp init-db/init.sql "${PACKAGE_DIR}/init-db/"

# Copy API Proxy
echo "▶ Copying API Proxy..."
cp api-proxy/package.json "${PACKAGE_DIR}/api-proxy/"
cp api-proxy/server.js "${PACKAGE_DIR}/api-proxy/"
cp api-proxy/Dockerfile "${PACKAGE_DIR}/api-proxy/"

# Copy License Server v2
echo "▶ Copying License Server v2..."
cp license-server-v2/requirements.txt "${PACKAGE_DIR}/license-server-v2/"
cp license-server-v2/main.py "${PACKAGE_DIR}/license-server-v2/"
cp license-server-v2/Dockerfile "${PACKAGE_DIR}/license-server-v2/"

# Create .env.example
echo "▶ Creating .env.example..."
cat > "${PACKAGE_DIR}/.env.example" <<'EOF'
# Rhinometric v2.1.0 Enterprise Configuration

# Database
POSTGRES_PASSWORD=rhinometric

# Cache
REDIS_PASSWORD=rhinometric

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# System
HOME=$HOME
EOF

# Create checksums
echo "▶ Generating checksums..."
cd "${PACKAGE_DIR}"
find . -type f -exec sha256sum {} \; > CHECKSUMS.txt
cd - > /dev/null

# Create tarball
echo "▶ Creating tarball..."
cd "${TEMP_DIR}"
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"
cd - > /dev/null

# Move to current directory
mv "${TEMP_DIR}/${PACKAGE_NAME}.tar.gz" "./"

# Generate checksums for package
PACKAGE_SHA256=$(sha256sum "${PACKAGE_NAME}.tar.gz" | awk '{print $1}')

# Cleanup
rm -rf "${TEMP_DIR}"

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  Package Created Successfully!"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Package: ${PACKAGE_NAME}.tar.gz"
echo "SHA256:  ${PACKAGE_SHA256}"
echo "Size:    $(du -h ${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "To install:"
echo "  1. tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "  2. cd ${PACKAGE_NAME}"
echo "  3. ./install-v2.1.sh"
echo ""

# Create installation guide
cat > INSTALL-GUIDE-v${VERSION}.txt <<EOF
═══════════════════════════════════════════════════════════════════════════
  RHINOMETRIC v${VERSION} ENTERPRISE - INSTALLATION GUIDE
═══════════════════════════════════════════════════════════════════════════

PACKAGE INFORMATION
-------------------
File:     ${PACKAGE_NAME}.tar.gz
Version:  ${VERSION}
SHA256:   ${PACKAGE_SHA256}
Date:     $(date)

SYSTEM REQUIREMENTS
-------------------
- Docker 20.10+ or Docker Desktop
- Docker Compose v2.0+
- 4 GB RAM minimum (6 GB recommended)
- 4 CPU cores minimum
- 20 GB disk space

SUPPORTED PLATFORMS
-------------------
✓ macOS (Intel/Apple Silicon)
✓ Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
✓ Windows WSL2 (Ubuntu 24.04)

INSTALLATION STEPS
------------------

1. Extract Package
   $ tar -xzf ${PACKAGE_NAME}.tar.gz
   $ cd ${PACKAGE_NAME}

2. Verify Checksums (Optional)
   $ sha256sum -c CHECKSUMS.txt

3. Run Universal Installer
   $ ./install-v2.1.sh

4. Validate Installation
   $ ./validate-v2.1.sh

ACCESS URLS
-----------
Grafana:         http://localhost:3000 (admin/admin)
Prometheus:      http://localhost:9090
License Server:  http://localhost:5000/api/docs
API Proxy:       http://localhost:8090/health

MANUAL INSTALLATION
-------------------
If the installer fails:

1. Create environment file
   $ cp .env.example .env

2. Start services
   $ docker compose -f docker-compose-v2.1.0.yml up -d

3. Validate
   $ ./validate-v2.1.sh

TROUBLESHOOTING
---------------

Services not starting:
  $ docker compose -f docker-compose-v2.1.0.yml logs -f

Check container health:
  $ docker ps --format "table {{.Names}}\t{{.Status}}"

Restart services:
  $ docker compose -f docker-compose-v2.1.0.yml restart

Stop all services:
  $ docker compose -f docker-compose-v2.1.0.yml down

WHAT'S NEW IN v2.1.0
--------------------
✓ GUI-based API connectivity
✓ 8 pre-loaded enterprise dashboards
✓ OpenTelemetry Collector (replaces telemetrygen)
✓ FastAPI License Server (replaces Flask)
✓ One-command installation
✓ 30% resource reduction vs v2.0.0
✓ 100% healthchecks (16/16)

DOCUMENTATION
-------------
Full documentation: README.md
API Documentation: http://localhost:5000/api/docs

═══════════════════════════════════════════════════════════════════════════
  For support, check logs and documentation
═══════════════════════════════════════════════════════════════════════════
EOF

echo "Installation guide: INSTALL-GUIDE-v${VERSION}.txt"
echo ""
