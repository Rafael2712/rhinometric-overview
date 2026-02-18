#!/usr/bin/env bash
# =============================================================================
# rhino-lic-gen.sh ??? Rhinometric License Generator Wrapper
# =============================================================================
#
# INTERNAL TOOL ??? Not for customer distribution.
# Wraps `rhino-lic issue` to simplify license generation for predefined SKUs.
#
# The Ed25519 private key is NEVER stored in the repo.
# It must be supplied at runtime via --privkey.
#
# SUPPORTED SKUs:
#   community-trial-1-host-3m       ??? 1 host,  90-day community trial
#   community-annual-1-host         ??? 1 host,  365-day community
#   starter-selfhosted-5-hosts      ??? 5 hosts, 365-day starter (on-prem)
#   starter-saas-20-hosts           ??? 20 hosts, 365-day starter (SaaS)
#   professional-saas-50-hosts      ??? 50 hosts, 365-day professional (SaaS)
#   enterprise-saas-100-hosts       ??? 100 hosts, 365-day enterprise (SaaS)
#
# EXAMPLE USAGE:
#
#   # Community trial (1 host, 3 months):
#   bash scripts/rhino-lic-gen.sh \
#     --sku community-trial-1-host-3m \
#     --tenant-id "demo-001" \
#     --customer "Demo Customer" \
#     --fingerprint "sha256:abcdef1234567890..." \
#     --privkey /secure/keys/license.key \
#     --out /tmp/demo-license.key
#
#   # Starter self-hosted (5 hosts, 1 year):
#   bash scripts/rhino-lic-gen.sh \
#     --sku starter-selfhosted-5-hosts \
#     --tenant-id "customer-001" \
#     --customer "Customer Name" \
#     --fingerprint "sha256:abcdef1234567890..." \
#     --privkey /secure/keys/license.key \
#     --out customer-001-license.key
#
#   # Enterprise SaaS with custom expiry (testing):
#   bash scripts/rhino-lic-gen.sh \
#     --sku enterprise-saas-100-hosts \
#     --tenant-id "test-short" \
#     --customer "Short Expiry Test" \
#     --fingerprint "sha256:abcdef1234567890..." \
#     --privkey /secure/keys/license.key \
#     --expires-in-days 3 \
#     --out /tmp/test-3day.key
#
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults & constants
# ---------------------------------------------------------------------------
VERSION="1.0.0"
SCRIPT_NAME="$(basename "$0")"

# Default features applied to ALL SKUs (matches existing license schema).
# Can be overridden per invocation with --features.
DEFAULT_FEATURES="monitoring,alerting,anomaly-detection,license-server"

# ---------------------------------------------------------------------------
# Color helpers (disabled if not a terminal)
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; NC=''
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
die()  { printf "${RED}ERROR:${NC} %s\n" "$1" >&2; exit 1; }
warn() { printf "${YELLOW}WARN:${NC} %s\n" "$1" >&2; }
info() { printf "${CYAN}???${NC} %s\n" "$1"; }

usage() {
    cat <<EOF
${BOLD}${SCRIPT_NAME}${NC} v${VERSION} ??? Rhinometric License Generator

${BOLD}USAGE:${NC}
    ${SCRIPT_NAME} --sku <SKU> --tenant-id <ID> --customer <NAME> \\
                    --fingerprint <SHA256> --privkey <PATH> --out <PATH>

${BOLD}REQUIRED:${NC}
    --sku              SKU identifier (see list below)
    --tenant-id        Unique tenant identifier (e.g. "acme-001")
    --customer         Customer display name (e.g. "Acme Corp")
    --fingerprint      Target machine fingerprint (sha256:<hex>)
    --privkey          Path to Ed25519 private key file
    --out              Output path for the signed license file

${BOLD}OPTIONAL:${NC}
    --expires-in-days  Override default validity period (days)
    --plan             Override plan name from SKU default
    --features         Comma-separated features (default: ${DEFAULT_FEATURES})
    --help             Show this help message

${BOLD}AVAILABLE SKUs:${NC}
    community-trial-1-host-3m       1 host,   90 days  (community_trial)
    community-annual-1-host         1 host,  365 days  (community)
    starter-selfhosted-5-hosts      5 hosts, 365 days  (starter_onprem)
    starter-saas-20-hosts          20 hosts, 365 days  (starter_saas)
    professional-saas-50-hosts     50 hosts, 365 days  (professional_saas)
    enterprise-saas-100-hosts     100 hosts, 365 days  (enterprise_saas)

EOF
    exit 0
}

# ---------------------------------------------------------------------------
# SKU ??? (plan, max_hosts, expires_in_days) mapping
# ---------------------------------------------------------------------------
resolve_sku() {
    local sku="$1"
    case "${sku}" in
        community-trial-1-host-3m)
            SKU_PLAN="community_trial"
            SKU_MAX_HOSTS=1
            SKU_EXPIRES_DAYS=90
            ;;
        community-annual-1-host)
            SKU_PLAN="community"
            SKU_MAX_HOSTS=1
            SKU_EXPIRES_DAYS=365
            ;;
        starter-selfhosted-5-hosts)
            SKU_PLAN="starter_onprem"
            SKU_MAX_HOSTS=5
            SKU_EXPIRES_DAYS=365
            ;;
        starter-saas-20-hosts)
            SKU_PLAN="starter_saas"
            SKU_MAX_HOSTS=20
            SKU_EXPIRES_DAYS=365
            ;;
        professional-saas-50-hosts)
            SKU_PLAN="professional_saas"
            SKU_MAX_HOSTS=50
            SKU_EXPIRES_DAYS=365
            ;;
        enterprise-saas-100-hosts)
            SKU_PLAN="enterprise_saas"
            SKU_MAX_HOSTS=100
            SKU_EXPIRES_DAYS=365
            ;;
        *)
            die "Unknown SKU: '${sku}'

Valid SKUs:
  community-trial-1-host-3m
  community-annual-1-host
  starter-selfhosted-5-hosts
  starter-saas-20-hosts
  professional-saas-50-hosts
  enterprise-saas-100-hosts"
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Compute expires_at in RFC 3339 / ISO 8601 format
# ---------------------------------------------------------------------------
compute_expires_at() {
    local days="$1"
    # Try GNU date first (Linux), then BSD date (macOS)
    if date --version >/dev/null 2>&1; then
        # GNU date
        date -u -d "+${days} days" "+%Y-%m-%dT%H:%M:%SZ"
    else
        # BSD date (macOS)
        date -u -v "+${days}d" "+%Y-%m-%dT%H:%M:%SZ"
    fi
}

# ---------------------------------------------------------------------------
# Parse CLI arguments
# ---------------------------------------------------------------------------
ARG_SKU=""
ARG_TENANT_ID=""
ARG_CUSTOMER=""
ARG_FINGERPRINT=""
ARG_PRIVKEY=""
ARG_OUT=""
ARG_EXPIRES_IN_DAYS=""
ARG_PLAN=""
ARG_FEATURES=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sku)              ARG_SKU="$2";              shift 2 ;;
        --tenant-id)        ARG_TENANT_ID="$2";        shift 2 ;;
        --customer)         ARG_CUSTOMER="$2";         shift 2 ;;
        --fingerprint)      ARG_FINGERPRINT="$2";      shift 2 ;;
        --privkey)          ARG_PRIVKEY="$2";           shift 2 ;;
        --out)              ARG_OUT="$2";               shift 2 ;;
        --expires-in-days)  ARG_EXPIRES_IN_DAYS="$2";  shift 2 ;;
        --plan)             ARG_PLAN="$2";              shift 2 ;;
        --features)         ARG_FEATURES="$2";          shift 2 ;;
        --help|-h)          usage ;;
        *)                  die "Unknown argument: '$1'. Use --help for usage." ;;
    esac
done

# ---------------------------------------------------------------------------
# Validate required arguments
# ---------------------------------------------------------------------------
[[ -z "${ARG_SKU}" ]]         && die "Missing required argument: --sku"
[[ -z "${ARG_TENANT_ID}" ]]   && die "Missing required argument: --tenant-id"
[[ -z "${ARG_CUSTOMER}" ]]    && die "Missing required argument: --customer"
[[ -z "${ARG_FINGERPRINT}" ]] && die "Missing required argument: --fingerprint"
[[ -z "${ARG_PRIVKEY}" ]]     && die "Missing required argument: --privkey"
[[ -z "${ARG_OUT}" ]]         && die "Missing required argument: --out"

# Validate fingerprint format
if [[ ! "${ARG_FINGERPRINT}" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    die "Invalid fingerprint format. Expected: sha256:<64 hex chars>
Got: ${ARG_FINGERPRINT}"
fi

# Validate privkey file exists
[[ ! -f "${ARG_PRIVKEY}" ]] && die "Private key file not found: ${ARG_PRIVKEY}"

# Validate rhino-lic is available
if ! command -v rhino-lic >/dev/null 2>&1; then
    die "rhino-lic binary not found in PATH.
Install it to /usr/local/bin/rhino-lic or add its location to PATH."
fi

# ---------------------------------------------------------------------------
# Resolve SKU to defaults
# ---------------------------------------------------------------------------
resolve_sku "${ARG_SKU}"

# Apply overrides
FINAL_PLAN="${ARG_PLAN:-${SKU_PLAN}}"
FINAL_MAX_HOSTS="${SKU_MAX_HOSTS}"
FINAL_EXPIRES_DAYS="${ARG_EXPIRES_IN_DAYS:-${SKU_EXPIRES_DAYS}}"
FINAL_FEATURES="${ARG_FEATURES:-${DEFAULT_FEATURES}}"

# Validate expires_in_days is a positive integer
if ! [[ "${FINAL_EXPIRES_DAYS}" =~ ^[0-9]+$ ]] || [[ "${FINAL_EXPIRES_DAYS}" -eq 0 ]]; then
    die "--expires-in-days must be a positive integer. Got: '${FINAL_EXPIRES_DAYS}'"
fi

# Compute expiration date
FINAL_EXPIRES_AT="$(compute_expires_at "${FINAL_EXPIRES_DAYS}")"
if [[ -z "${FINAL_EXPIRES_AT}" ]]; then
    die "Failed to compute expiration date. Is 'date' available?"
fi

# ---------------------------------------------------------------------------
# Print generation plan
# ---------------------------------------------------------------------------
echo ""
printf "${BOLD}============================================================${NC}\n"
printf "${BOLD} Rhinometric License Generator v${VERSION}${NC}\n"
printf "${BOLD}============================================================${NC}\n"
echo ""
info "SKU             : ${ARG_SKU}"
info "Tenant ID       : ${ARG_TENANT_ID}"
info "Customer        : ${ARG_CUSTOMER}"
info "Plan            : ${FINAL_PLAN}"
info "Max hosts       : ${FINAL_MAX_HOSTS}"
info "Validity        : ${FINAL_EXPIRES_DAYS} days"
info "Expires at      : ${FINAL_EXPIRES_AT}"
info "Features        : ${FINAL_FEATURES}"
info "Fingerprint     : ${ARG_FINGERPRINT}"
info "Output          : ${ARG_OUT}"
echo ""

# ---------------------------------------------------------------------------
# Call rhino-lic issue
# ---------------------------------------------------------------------------
info "Calling rhino-lic issue ..."
echo ""

rhino-lic issue \
    --tenant-id "${ARG_TENANT_ID}" \
    --customer "${ARG_CUSTOMER}" \
    --plan "${FINAL_PLAN}" \
    --max-hosts "${FINAL_MAX_HOSTS}" \
    --expires-at "${FINAL_EXPIRES_AT}" \
    --fingerprint-value "${ARG_FINGERPRINT}" \
    --features "${FINAL_FEATURES}" \
    --privkey "${ARG_PRIVKEY}" \
    --out "${ARG_OUT}"

ISSUE_EXIT=$?

if [[ ${ISSUE_EXIT} -ne 0 ]]; then
    die "rhino-lic issue failed with exit code ${ISSUE_EXIT}"
fi

# ---------------------------------------------------------------------------
# Verify output file
# ---------------------------------------------------------------------------
if [[ ! -f "${ARG_OUT}" ]]; then
    die "License file was not created at: ${ARG_OUT}"
fi

FILE_SIZE=$(stat -c%s "${ARG_OUT}" 2>/dev/null || stat -f%z "${ARG_OUT}" 2>/dev/null || echo "unknown")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
printf "${BOLD}============================================================${NC}\n"
printf "${GREEN}${BOLD} ??? License generated successfully${NC}\n"
printf "${BOLD}============================================================${NC}\n"
echo ""
printf "  ${BOLD}SKU${NC}          : %s\n" "${ARG_SKU}"
printf "  ${BOLD}Plan${NC}         : %s\n" "${FINAL_PLAN}"
printf "  ${BOLD}Max hosts${NC}    : %s\n" "${FINAL_MAX_HOSTS}"
printf "  ${BOLD}Tenant${NC}       : %s\n" "${ARG_TENANT_ID}"
printf "  ${BOLD}Customer${NC}     : %s\n" "${ARG_CUSTOMER}"
printf "  ${BOLD}Expires${NC}      : %s (%s days)\n" "${FINAL_EXPIRES_AT}" "${FINAL_EXPIRES_DAYS}"
printf "  ${BOLD}Features${NC}     : %s\n" "${FINAL_FEATURES}"
printf "  ${BOLD}Fingerprint${NC}  : %s\n" "${ARG_FINGERPRINT}"
printf "  ${BOLD}Output file${NC}  : %s (%s bytes)\n" "${ARG_OUT}" "${FILE_SIZE}"
echo ""
printf "  ${CYAN}Validate with:${NC}\n"
printf "    rhino-lic validate %s --pubkey <pubkey-path>\n" "${ARG_OUT}"
echo ""
printf "  ${CYAN}Deploy to target VM:${NC}\n"
printf "    scp %s root@<VM_IP>:/opt/rhinometric/license.key\n" "${ARG_OUT}"
echo ""

