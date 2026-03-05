#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# build-release.sh — Build Rhinometric On-Prem Release Tarball
# ═══════════════════════════════════════════════════════════════════════════════
#
# Usage:  cd /opt/rhinometric  &&  bash dist/build-release.sh
#
# Optional environment variables:
#   EXPORT_IMAGES=true   — Export pre-built Docker images into the tarball
#   VERSION=3.0.1        — Override the version string
#
# Output:  /tmp/rhinometric-v${VERSION}.tar.gz  +  .sha256
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

readonly VERSION="${VERSION:-3.0.3}"
readonly EXPORT_IMAGES="${EXPORT_IMAGES:-false}"
readonly STAGING="/tmp/rhinometric-staging"
readonly OUTPUT="/tmp/rhinometric-v${VERSION}.tar.gz"

RED="[0;31m"; GREEN="[0;32m"; NC="[0m"
info()  { echo -e "${GREEN}[BUILD]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Verify we are in the repo root ────────────────────────────────────────────
if [[ ! -f "docker-compose.yml" ]]; then
    error "docker-compose.yml not found. Run this script from the repo root."
    error "Usage: cd /opt/rhinometric && bash dist/build-release.sh"
    exit 1
fi

info "Building Rhinometric v${VERSION} release tarball..."

# ── Clean staging area ────────────────────────────────────────────────────────
rm -rf "${STAGING}"
mkdir -p "${STAGING}"

# ── 1. Copy installer scripts ────────────────────────────────────────────────
info "Copying installer scripts..."
cp dist/install-rhinometric.sh "${STAGING}/install-rhinometric.sh"
chmod 755 "${STAGING}/install-rhinometric.sh"

if [[ -f dist/uninstall-rhinometric.sh ]]; then
    cp dist/uninstall-rhinometric.sh "${STAGING}/uninstall-rhinometric.sh"
    chmod 755 "${STAGING}/uninstall-rhinometric.sh"
fi

# ── 2. Copy docker-compose.yml ───────────────────────────────────────────────
info "Copying docker-compose.yml..."
cp docker-compose.yml "${STAGING}/docker-compose.yml"

# ── 3. Copy .env.template if exists ──────────────────────────────────────────
if [[ -f dist/.env.template ]]; then
    cp dist/.env.template "${STAGING}/.env.template"
fi

# ── 4. Copy rhino-lic binary ─────────────────────────────────────────────────
if [[ -f /usr/local/bin/rhino-lic ]]; then
    info "Copying rhino-lic license binary..."
    cp /usr/local/bin/rhino-lic "${STAGING}/rhino-lic"
    chmod 755 "${STAGING}/rhino-lic"
elif [[ -f dist/rhino-lic ]]; then
    cp dist/rhino-lic "${STAGING}/rhino-lic"
    chmod 755 "${STAGING}/rhino-lic"
fi

# ── 5. Copy configuration directories ────────────────────────────────────────
info "Copying configuration directories..."
config_dirs=("config" "alertmanager" "grafana" "nginx" "blackbox" "init-db" "prometheus" "loki")
for dir in "${config_dirs[@]}"; do
    if [[ -d "${dir}" ]]; then
        cp -a "${dir}" "${STAGING}/${dir}"
        info "  ✓ ${dir}/"
    else
        echo "  ⚠ ${dir}/ not found (skipping)"
    fi
done

# ── 6. Copy build context directories ────────────────────────────────────────
info "Copying build context directories (for locally-built services)..."
build_dirs=("rhinometric-ai-anomaly" "rhinometric-console" "license-server-v2" "license-management-ui")
for dir in "${build_dirs[@]}"; do
    if [[ -d "${dir}" ]]; then
        cp -a "${dir}" "${STAGING}/${dir}"
        info "  ✓ ${dir}/"
    else
        echo "  ⚠ ${dir}/ not found (skipping)"
    fi
done

# ── 7. Clean development artifacts from staging ──────────────────────────────
info "Cleaning development artifacts..."
find "${STAGING}" -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find "${STAGING}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "${STAGING}" -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
find "${STAGING}" -name ".env" -type f -delete 2>/dev/null || true
find "${STAGING}" -name "*.pyc" -type f -delete 2>/dev/null || true
find "${STAGING}" -name ".DS_Store" -type f -delete 2>/dev/null || true

# ── 8. Optional: Export pre-built Docker images ──────────────────────────────
if [[ "${EXPORT_IMAGES}" == "true" ]]; then
    info "Exporting pre-built Docker images (this may take several minutes)..."
    local_images=(
        "rhinometric-console-backend:v2.5.2-alerts"
        "rhinometric-console-frontend:v2.5.2-alerts"
        "rhinometric-rhinometric-ai-anomaly:latest"
        "rhinometric-license-ui:latest"
        "rhinometric-license-server-v2:latest"
    )
    existing_images=()
    for img in "${local_images[@]}"; do
        if docker image inspect "${img}" >/dev/null 2>&1; then
            existing_images+=("${img}")
        fi
    done
    if [[ ${#existing_images[@]} -gt 0 ]]; then
        docker save "${existing_images[@]}" | gzip > "${STAGING}/images.tar.gz"
        info "  ✓ Exported ${#existing_images[@]} images to images.tar.gz"
    else
        echo "  ⚠ No local images found to export"
    fi
fi

# ── 9. Create tarball ────────────────────────────────────────────────────────
info "Creating tarball..."
tar -czf "${OUTPUT}" -C /tmp rhinometric-staging

# Rename the inner directory in the tarball
# (tarball extracts as rhinometric-staging/ but we want a clean name)
cd /tmp
mv rhinometric-staging "rhinometric-v${VERSION}" 2>/dev/null || true
tar -czf "${OUTPUT}" "rhinometric-v${VERSION}"
rm -rf "rhinometric-v${VERSION}"

# ── 10. Generate checksum ────────────────────────────────────────────────────
sha256sum "${OUTPUT}" > "${OUTPUT}.sha256"

# ── Summary ──────────────────────────────────────────────────────────────────
info ""
info "═══════════════════════════════════════════════════════════════"
info "═══════════════════════════════════════════════════════════════"
info "  Tarball:  ${OUTPUT}"
info "  SHA-256:  "
info "  Size:     "
info ""
info "  To install on a customer server:"
info "    scp ${OUTPUT} user@server:/tmp/"
info "    ssh user@server"
info "    tar -xzf /tmp/rhinometric-v${VERSION}.tar.gz"
info "    cd rhinometric-v${VERSION}"
info "    sudo bash install-rhinometric.sh"
info "═══════════════════════════════════════════════════════════════"
