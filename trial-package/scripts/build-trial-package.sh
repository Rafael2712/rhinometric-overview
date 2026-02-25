#!/usr/bin/env bash
###############################################################################
# build-trial-package.sh — Builds the Rhinometric trial distribution package
#
# Usage:
#   sudo bash build-trial-package.sh              # Online-only package
#   sudo bash build-trial-package.sh --offline    # Include Docker images (larger)
#
# Output: /tmp/rhinometric-trial-v2.6.0.tar.gz
###############################################################################
set -euo pipefail

readonly VERSION="2.6.0"
readonly REPO_DIR="/opt/rhinometric"
readonly OUTPUT_DIR="/tmp/rhinometric-trial-v${VERSION}"
readonly COMPOSE_SRC="docker-compose-v2.5.0-SECURE.yml"
INCLUDE_IMAGES=false

if [[ "${1:-}" == "--offline" ]]; then
    INCLUDE_IMAGES=true
fi

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║  Building Rhinometric Trial Package v${VERSION}      ║"
echo "║  Mode: $(if $INCLUDE_IMAGES; then echo 'OFFLINE (with images)'; else echo 'ONLINE (lightweight)'; fi)"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Clean previous build
rm -rf "$OUTPUT_DIR" "${OUTPUT_DIR}.tar.gz"
mkdir -p "$OUTPUT_DIR"

# 1. Copy docker-compose
echo "[1/8] Copying docker-compose..."
cp "$REPO_DIR/$COMPOSE_SRC" "$OUTPUT_DIR/docker-compose.yml"

# 2. Copy build contexts (services that need docker build)
echo "[2/8] Copying build contexts..."
for ctx in license-server-v2 rhinometric-ai-anomaly license-management-ui; do
    if [[ -d "$REPO_DIR/$ctx" ]]; then
        cp -a "$REPO_DIR/$ctx" "$OUTPUT_DIR/$ctx"
    fi
done

# Copy console (backend + frontend)
if [[ -d "$REPO_DIR/rhinometric-console" ]]; then
    cp -a "$REPO_DIR/rhinometric-console" "$OUTPUT_DIR/rhinometric-console"
fi

# 3. Copy configs
echo "[3/8] Copying configuration files..."
for cfgdir in nginx grafana prometheus alertmanager loki jaeger otel-collector; do
    if [[ -d "$REPO_DIR/$cfgdir" ]]; then
        cp -a "$REPO_DIR/$cfgdir" "$OUTPUT_DIR/$cfgdir"
    fi
done

# Copy extra configs
for f in prometheus-alerts-container.yml prometheus.yml promtail-docker.yml alertmanager-notifications.yml; do
    [[ -f "$REPO_DIR/$f" ]] && cp "$REPO_DIR/$f" "$OUTPUT_DIR/$f"
done

# Config dirs
for cfgdir in config grafana-provisioning grafana-dashboards grafana-plugins grafana-plugins-simple init-db blackbox pgbouncer; do
    if [[ -d "$REPO_DIR/$cfgdir" ]]; then
        cp -a "$REPO_DIR/$cfgdir" "$OUTPUT_DIR/$cfgdir"
    fi
done

# 4. Copy .env.example
echo "[4/8] Creating .env.example..."
cat > "$OUTPUT_DIR/.env.example" << 'ENVEOF'
# RHINOMETRIC v2.6.0 — Environment Configuration
# Copy this to .env and customize, or let install.sh generate it automatically.
#
# The installer will generate secure random passwords if .env doesn't exist.
#
# PUBLIC_IP=auto-detected
# DOMAIN=your-domain.com
# POSTGRES_PASSWORD=auto-generated
# REDIS_PASSWORD=auto-generated
# GRAFANA_PASSWORD=auto-generated
# ADMIN_PASSWORD=auto-generated
ENVEOF

# 5. Copy install scripts
echo "[5/8] Copying installer scripts..."
cp "$REPO_DIR/trial-package/install.sh" "$OUTPUT_DIR/install.sh"
cp "$REPO_DIR/trial-package/rhinoctl" "$OUTPUT_DIR/rhinoctl"
chmod +x "$OUTPUT_DIR/install.sh" "$OUTPUT_DIR/rhinoctl"

# 6. Copy license files
echo "[6/8] Copying license templates..."
for lic in license.lic ClienteDemo.lic license_ClienteDemo_15d.lic; do
    [[ -f "$REPO_DIR/$lic" ]] && cp "$REPO_DIR/$lic" "$OUTPUT_DIR/$lic"
done

# 7. Create docs
echo "[7/8] Creating documentation..."
mkdir -p "$OUTPUT_DIR/docs"
cat > "$OUTPUT_DIR/docs/QUICKSTART.md" << 'DOCEOF'
# Rhinometric Trial — Quick Start Guide

## Requirements
- Ubuntu 22.04/24.04 or Debian 12
- 4+ CPU cores, 8+ GB RAM, 50+ GB disk
- Root/sudo access
- Internet connection (online mode) or pre-packaged images (offline mode)

## Installation (3 steps)

### Step 1: Extract the package
```bash
tar xzf rhinometric-trial-v2.6.0.tar.gz
cd rhinometric-trial-v2.6.0
```

### Step 2: Run the installer
```bash
# Online mode (downloads images from Internet)
sudo bash install.sh

# Offline mode (uses pre-packaged images, no Internet needed)
sudo bash install.sh --offline

# Non-interactive
sudo bash install.sh --non-interactive
```

### Step 3: Access the platform
After installation, the console will show:
- **Console URL**: http://<your-ip>
- **Grafana URL**: http://<your-ip>/grafana/
- **Credentials**: saved in `/opt/rhinometric/CREDENTIALS.txt`

## Licensing

### Get your Hardware ID
```bash
rhinoctl fingerprint
```

### Apply a license
```bash
rhinoctl apply-license /path/to/your-license.lic
```

## Management Commands
```bash
rhinoctl status          # Show service status
rhinoctl health          # Detailed health check
rhinoctl start           # Start platform
rhinoctl stop            # Stop platform
rhinoctl restart         # Restart all services
rhinoctl logs            # View logs
rhinoctl credentials     # Show saved credentials
rhinoctl fingerprint     # Show hardware ID
rhinoctl apply-license   # Apply license file
```

## Troubleshooting

### Services not starting?
```bash
rhinoctl health          # Check which services are down
rhinoctl logs <service>  # View specific service logs
```

### Re-run installer
The installer is idempotent — safe to run again:
```bash
sudo bash install.sh --skip-build
```

## Support
- Email: support@rhinometric.com
- Docs: https://docs.rhinometric.com
DOCEOF

# 8. Save Docker images (offline mode)
if $INCLUDE_IMAGES; then
    echo "[8/8] Saving Docker images (this takes several minutes)..."
    mkdir -p "$OUTPUT_DIR/images"

    # Get list of all images from compose
    cd "$REPO_DIR"
    images=$(docker compose config --images 2>/dev/null | sort -u)

    for img in $images; do
        safe_name=$(echo "$img" | tr '/:' '__')
        printf "  Saving %-50s" "$img..."
        if docker save "$img" > "$OUTPUT_DIR/images/${safe_name}.tar" 2>/dev/null; then
            echo "OK ($(du -sh "$OUTPUT_DIR/images/${safe_name}.tar" | awk '{print $1}'))"
        else
            echo "SKIP (not found locally)"
            rm -f "$OUTPUT_DIR/images/${safe_name}.tar"
        fi
    done
else
    echo "[8/8] Skipping image export (online mode)"

    # Create manifest of required images
    cd "$REPO_DIR"
    docker compose config --images 2>/dev/null | sort -u > "$OUTPUT_DIR/images-manifest.txt"
    echo "  Image manifest saved: $(wc -l < "$OUTPUT_DIR/images-manifest.txt") images"
fi

# Remove .git dirs from build contexts (save space)
find "$OUTPUT_DIR" -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true

# Generate checksums
echo ""
echo "Generating checksums..."
cd "$OUTPUT_DIR"
find . -type f ! -name "checksums.sha256" -exec sha256sum {} + > checksums.sha256

# Create tar.gz
echo "Creating archive..."
cd /tmp
tar czf "rhinometric-trial-v${VERSION}.tar.gz" "rhinometric-trial-v${VERSION}"

final_size=$(du -sh "/tmp/rhinometric-trial-v${VERSION}.tar.gz" | awk '{print $1}')
echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║  Package ready!                                    ║"
echo "║  /tmp/rhinometric-trial-v${VERSION}.tar.gz (${final_size})  ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "To distribute:"
echo "  scp /tmp/rhinometric-trial-v${VERSION}.tar.gz user@client-server:/tmp/"
echo ""
echo "Client installs with:"
echo "  tar xzf rhinometric-trial-v${VERSION}.tar.gz"
echo "  cd rhinometric-trial-v${VERSION}"
echo "  sudo bash install.sh"
echo ""
