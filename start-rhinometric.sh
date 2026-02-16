#!/usr/bin/env bash
# ============================================================================
# start-rhinometric.sh — Rhinometric Stack Launcher with License Validation
# ============================================================================
# This script MUST be run from /opt/rhinometric (or with cd beforehand).
#
# Flow:
#   1. Check that /opt/rhinometric/license.key exists
#   2. Run `rhino-lic validate` against it (embedded Ed25519 public key)
#   3. If valid  → docker-compose up -d
#   4. If invalid → print error, refuse to start, exit 1
# ============================================================================

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
RHINO_DIR="/opt/rhinometric"
LICENSE_FILE="${RHINO_DIR}/license.key"
COMPOSE_FILE="docker-compose-v2.5.0-SECURE.yml"
RHINO_LIC="/usr/local/bin/rhino-lic"

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ── Functions ───────────────────────────────────────────────────────────────
log_ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_err()  { echo -e "${RED}[ERROR]${NC} $1"; }
log_info() { echo -e "        $1"; }

# ── Pre-flight checks ──────────────────────────────────────────────────────
echo "============================================================"
echo " Rhinometric Stack Launcher"
echo " $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"
echo ""

# 1. Check binary exists
if [ ! -x "${RHINO_LIC}" ]; then
    log_err "License validator not found: ${RHINO_LIC}"
    log_info "Install it with: cp /opt/rhinometric/rust-licenses/target/release/rhino-lic ${RHINO_LIC}"
    exit 1
fi

# 2. Check license file exists
if [ ! -f "${LICENSE_FILE}" ]; then
    log_err "License file not found: ${LICENSE_FILE}"
    log_info "Contact your Rhinometric administrator to obtain a valid license."
    log_info "Place the signed license JSON at: ${LICENSE_FILE}"
    exit 1
fi

# 3. Validate license
echo "Validating license: ${LICENSE_FILE}"
echo ""

VALIDATION_OUTPUT=$("${RHINO_LIC}" validate "${LICENSE_FILE}" 2>&1) || true
VALIDATION_EXIT=${PIPESTATUS[0]:-$?}

# Re-run to capture exit code cleanly (set +e to avoid bash -e killing us)
set +e
"${RHINO_LIC}" validate "${LICENSE_FILE}" > /tmp/.rhino-lic-result.json 2>/dev/null
VALIDATION_EXIT=$?
set -e

VALIDATION_OUTPUT=$(cat /tmp/.rhino-lic-result.json 2>/dev/null)

if [ ${VALIDATION_EXIT} -ne 0 ]; then
    echo ""
    log_err "LICENSE VALIDATION FAILED (exit code ${VALIDATION_EXIT})"
    echo ""
    case ${VALIDATION_EXIT} in
        1) log_err "Reason: Invalid Ed25519 signature — license file may be tampered" ;;
        2) log_err "Reason: License expired or not yet valid" ;;
        3) log_err "Reason: Machine fingerprint mismatch — this license is not for this host" ;;
        4) log_err "Reason: License file parse error or I/O failure" ;;
        *) log_err "Reason: Unknown error" ;;
    esac
    echo ""
    log_info "Validation output:"
    echo "${VALIDATION_OUTPUT}"
    echo ""
    log_err "Rhinometric stack will NOT start."
    log_info "To resolve:"
    log_info "  - Check license expiry:      rhino-lic validate ${LICENSE_FILE}"
    log_info "  - Check machine fingerprint: rhino-lic fingerprint"
    log_info "  - Request a new license from your Rhinometric administrator."
    echo ""
    exit 1
fi

# ── License valid — extract info ────────────────────────────────────────────
PLAN=$(echo "${VALIDATION_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('plan','?'))" 2>/dev/null || echo "?")
MAX_HOSTS=$(echo "${VALIDATION_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('max_hosts','?'))" 2>/dev/null || echo "?")
EXPIRES=$(echo "${VALIDATION_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('expires_at','?'))" 2>/dev/null || echo "?")

echo ""
log_ok "License is VALID"
log_info "Plan      : ${PLAN}"
log_info "Max hosts : ${MAX_HOSTS}"
log_info "Expires   : ${EXPIRES}"
echo ""

# ── Start the stack ─────────────────────────────────────────────────────────
echo "Starting Rhinometric stack..."
echo ""

cd "${RHINO_DIR}"

# Skip services whose images haven't been built yet
SCALE_OVERRIDES=""
if ! docker image inspect rhinometric-license-ui:latest >/dev/null 2>&1; then
    log_warn "Skipping service 'license-ui' (image not built)"
    SCALE_OVERRIDES="--scale license-ui=0"
fi

docker-compose -f "${COMPOSE_FILE}" up -d --no-build ${SCALE_OVERRIDES}

echo ""
log_ok "Rhinometric stack started successfully."
echo ""
