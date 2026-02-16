#!/usr/bin/env bash
# =============================================================================
# RHINOMETRIC SaaS - Customer Provisioning Script
# Version: 2.5.1
# Author: Rhinometric Platform Team
# =============================================================================
# Usage:
#   ./provision-customer.sh <TENANT_ID> [--dry-run]
#
# Prerequisites:
#   1. Fill /opt/rhinometric/config/customer.env with customer data
#   2. Ensure Docker images are built (docker-compose build)
#
# This script:
#   1. Reads customer.env configuration
#   2. Auto-generates secure passwords
#   3. Processes templates → final config files
#   4. Creates tenant record in /opt/rhinometric/tenants/<TENANT_ID>/
#   5. Deploys the stack with docker-compose
#   6. Runs healthchecks
#   7. Generates provision report
#
# SAFETY: Does NOT touch /opt/rhinometric/tenants/*, audits/*, docs/*
#         Only modifies: .env, nginx/nginx.conf, alertmanager/alertmanager.yml,
#                        rhinometric-ai-anomaly/config.yaml,
#                        docker-compose.yml (re-symlinking)
# =============================================================================

set -euo pipefail

# =============================================================================
# COLORS & HELPERS
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

# =============================================================================
# ARGUMENTS
# =============================================================================
if [ $# -lt 1 ]; then
    echo "Usage: $0 <TENANT_ID> [--dry-run]"
    echo ""
    echo "  TENANT_ID  : Unique identifier (e.g., cliente-acme, rhinometric-prod)"
    echo "  --dry-run  : Generate configs without deploying"
    echo ""
    echo "Prerequisites:"
    echo "  1. Fill /opt/rhinometric/config/customer.env"
    echo "  2. Docker images must be built"
    exit 1
fi

TENANT_ID="$1"
DRY_RUN=false
if [ "${2:-}" = "--dry-run" ]; then
    DRY_RUN=true
fi

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR="/opt/rhinometric"
TEMPLATES_DIR="${BASE_DIR}/templates"
CONFIG_DIR="${BASE_DIR}/config"
TENANT_DIR="${BASE_DIR}/tenants/${TENANT_ID}"
CUSTOMER_ENV="${CONFIG_DIR}/customer.env"
PROVISION_DATE=$(date -u '+%Y-%m-%d %H:%M:%S UTC')
PROVISION_TIMESTAMP=$(date -u '+%Y%m%d_%H%M%S')

# =============================================================================
# BANNER
# =============================================================================
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     RHINOMETRIC SaaS - Customer Provisioning v2.5.1      ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Tenant:  ${TENANT_ID}"
echo "║  Date:    ${PROVISION_DATE}"
echo "║  Mode:    $([ "$DRY_RUN" = true ] && echo 'DRY-RUN (no deploy)'  || echo 'FULL DEPLOY')"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# =============================================================================
# STEP 1: VALIDATE PREREQUISITES
# =============================================================================
log_step "STEP 1/7: Validating prerequisites"

# Check we are in the right directory
if [ ! -f "${BASE_DIR}/docker-compose.yml" ]; then
    log_error "docker-compose.yml not found at ${BASE_DIR}"
    exit 1
fi
log_ok "docker-compose.yml found"

# Check templates exist
for tmpl in env.template nginx.conf.template alertmanager.yml.template ai-anomaly-config.yaml.template; do
    if [ ! -f "${TEMPLATES_DIR}/${tmpl}" ]; then
        log_error "Template missing: ${TEMPLATES_DIR}/${tmpl}"
        exit 1
    fi
done
log_ok "All templates present"

# Check customer.env exists and is filled
if [ ! -f "$CUSTOMER_ENV" ]; then
    log_error "customer.env not found at ${CUSTOMER_ENV}"
    log_info "Copy the template: cp ${TEMPLATES_DIR}/customer.env.template ${CUSTOMER_ENV}"
    exit 1
fi
log_ok "customer.env found"

# Source customer.env
set -a
source "$CUSTOMER_ENV"
set +a

# Validate required fields
REQUIRED_FIELDS="CUSTOMER_NAME CUSTOMER_ID CUSTOMER_DOMAIN CUSTOMER_PUBLIC_IP CUSTOMER_SMTP_HOST CUSTOMER_SMTP_PORT CUSTOMER_SMTP_USER CUSTOMER_SMTP_PASSWORD CUSTOMER_SMTP_FROM CUSTOMER_ALERT_EMAIL"
MISSING=0
for field in $REQUIRED_FIELDS; do
    val="${!field:-}"
    if [ -z "$val" ]; then
        log_error "Required field empty in customer.env: $field"
        MISSING=$((MISSING + 1))
    fi
done
if [ $MISSING -gt 0 ]; then
    log_error "$MISSING required fields missing. Edit ${CUSTOMER_ENV} and retry."
    exit 1
fi
log_ok "All required fields present in customer.env"

# Check if tenant already exists
if [ -d "$TENANT_DIR" ]; then
    log_warn "Tenant directory already exists: ${TENANT_DIR}"
    log_warn "This may be a re-provision. Previous config will be backed up."
    if [ -f "${TENANT_DIR}/customer.env" ]; then
        cp "${TENANT_DIR}/customer.env" "${TENANT_DIR}/customer.env.bak.${PROVISION_TIMESTAMP}"
        log_info "Previous customer.env backed up"
    fi
fi

log_ok "Prerequisites validated"

# =============================================================================
# STEP 2: GENERATE SECURE PASSWORDS
# =============================================================================
log_step "STEP 2/7: Generating secure credentials"

gen_password() {
    openssl rand -base64 32 | tr -d '/+=' | head -c "$1"
}

POSTGRES_PASSWORD=$(gen_password 32)
REDIS_PASSWORD=$(gen_password 32)
GRAFANA_PASSWORD=$(gen_password 32)
SECRET_KEY=$(gen_password 48)

# Admin password: use customer-provided or auto-generate
if [ -n "${CUSTOMER_ADMIN_PASSWORD:-}" ]; then
    ADMIN_PASSWORD="${CUSTOMER_ADMIN_PASSWORD}"
    log_info "Using customer-provided admin password"
else
    ADMIN_PASSWORD=$(gen_password 16)
    log_info "Auto-generated admin password"
fi

log_ok "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:0:8}..."
log_ok "REDIS_PASSWORD:    ${REDIS_PASSWORD:0:8}..."
log_ok "GRAFANA_PASSWORD:  ${GRAFANA_PASSWORD:0:8}..."
log_ok "SECRET_KEY:        ${SECRET_KEY:0:8}..."
log_ok "ADMIN_PASSWORD:    ${ADMIN_PASSWORD:0:4}..."

# =============================================================================
# STEP 3: PROCESS TEMPLATES
# =============================================================================
log_step "STEP 3/7: Processing templates"

# Helper: replace __PLACEHOLDER__ in file
replace_placeholders() {
    local file="$1"
    # Customer identity
    sed -i "s|__TENANT_ID__|${TENANT_ID}|g" "$file"
    sed -i "s|__PROVISION_DATE__|${PROVISION_DATE}|g" "$file"
    sed -i "s|__CUSTOMER_DOMAIN__|${CUSTOMER_DOMAIN}|g" "$file"
    sed -i "s|__CUSTOMER_PUBLIC_IP__|${CUSTOMER_PUBLIC_IP}|g" "$file"
    sed -i "s|__CUSTOMER_NAME__|${CUSTOMER_NAME}|g" "$file"

    # Passwords (auto-generated)
    sed -i "s|__POSTGRES_PASSWORD__|${POSTGRES_PASSWORD}|g" "$file"
    sed -i "s|__REDIS_PASSWORD__|${REDIS_PASSWORD}|g" "$file"
    sed -i "s|__GRAFANA_PASSWORD__|${GRAFANA_PASSWORD}|g" "$file"
    sed -i "s|__SECRET_KEY__|${SECRET_KEY}|g" "$file"
    sed -i "s|__ADMIN_PASSWORD__|${ADMIN_PASSWORD}|g" "$file"

    # SMTP
    sed -i "s|__SMTP_HOST__|${CUSTOMER_SMTP_HOST}|g" "$file"
    sed -i "s|__SMTP_PORT__|${CUSTOMER_SMTP_PORT}|g" "$file"
    sed -i "s|__SMTP_USER__|${CUSTOMER_SMTP_USER}|g" "$file"
    sed -i "s|__SMTP_PASSWORD__|${CUSTOMER_SMTP_PASSWORD}|g" "$file"
    sed -i "s|__SMTP_FROM__|${CUSTOMER_SMTP_FROM}|g" "$file"
    sed -i "s|__ALERT_EMAIL__|${CUSTOMER_ALERT_EMAIL}|g" "$file"

    # Slack
    sed -i "s|__SLACK_WEBHOOK_URL__|${CUSTOMER_SLACK_WEBHOOK:-}|g" "$file"
    sed -i "s|__SLACK_CHANNEL_ALERTS__|${CUSTOMER_SLACK_CHANNEL_ALERTS:-#monitoring-alerts}|g" "$file"
    sed -i "s|__SLACK_CHANNEL_CRITICAL__|${CUSTOMER_SLACK_CHANNEL_CRITICAL:-#monitoring-critical}|g" "$file"
    sed -i "s|__SLACK_CHANNEL_INFO__|${CUSTOMER_SLACK_CHANNEL_INFO:-#monitoring-info}|g" "$file"

    # Website
    sed -i "s|__CUSTOMER_WEBSITE_URL__|${CUSTOMER_WEBSITE_URL:-}|g" "$file"
}

# --- 3a. Generate .env ---
log_info "Processing .env"
cp "${TEMPLATES_DIR}/env.template" "${BASE_DIR}/.env.new"
replace_placeholders "${BASE_DIR}/.env.new"
log_ok ".env generated"

# --- 3b. Generate nginx.conf ---
log_info "Processing nginx.conf"
cp "${TEMPLATES_DIR}/nginx.conf.template" "${BASE_DIR}/nginx/nginx.conf.new"
replace_placeholders "${BASE_DIR}/nginx/nginx.conf.new"
log_ok "nginx.conf generated"

# --- 3c. Generate alertmanager.yml ---
log_info "Processing alertmanager.yml"
cp "${TEMPLATES_DIR}/alertmanager.yml.template" "${BASE_DIR}/alertmanager/alertmanager.yml.new"
replace_placeholders "${BASE_DIR}/alertmanager/alertmanager.yml.new"
log_ok "alertmanager.yml generated"

# --- 3d. Generate ai-anomaly config.yaml ---
log_info "Processing ai-anomaly config.yaml"
cp "${TEMPLATES_DIR}/ai-anomaly-config.yaml.template" "${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new"

# Handle website monitoring block
if [ "${CUSTOMER_WEBSITE_MONITORING:-false}" = "true" ] && [ -n "${CUSTOMER_WEBSITE_URL:-}" ]; then
    log_info "Website monitoring ENABLED for: ${CUSTOMER_WEBSITE_URL}"
    # Read the website monitoring block and inline it
    WEBSITE_BLOCK=$(cat "${TEMPLATES_DIR}/website-monitoring.block")
    # Use Python for safe multi-line replacement
    python3 -c "
import sys
with open('${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new', 'r') as f:
    content = f.read()
with open('${TEMPLATES_DIR}/website-monitoring.block', 'r') as f:
    block = f.read()
content = content.replace('__WEBSITE_MONITORING_BLOCK__', block)
with open('${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new', 'w') as f:
    f.write(content)
"
else
    log_info "Website monitoring DISABLED"
    DISABLED_BLOCK=$(cat "${TEMPLATES_DIR}/website-monitoring-disabled.block")
    python3 -c "
import sys
with open('${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new', 'r') as f:
    content = f.read()
with open('${TEMPLATES_DIR}/website-monitoring-disabled.block', 'r') as f:
    block = f.read()
content = content.replace('__WEBSITE_MONITORING_BLOCK__', block)
with open('${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new', 'w') as f:
    f.write(content)
"
fi
replace_placeholders "${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new"
log_ok "ai-anomaly config.yaml generated"

# --- 3e. Patch docker-compose.yml ---
log_info "Patching docker-compose.yml (customer-specific values)"
COMPOSE_SRC="${BASE_DIR}/docker-compose-v2.5.0-SECURE.yml"
cp "${COMPOSE_SRC}" "${BASE_DIR}/docker-compose-v2.5.1-${TENANT_ID}.yml"
COMPOSE_NEW="${BASE_DIR}/docker-compose-v2.5.1-${TENANT_ID}.yml"

# Build CORS_ORIGINS for this customer
CORS_ORIGINS="[\"http://localhost:3002\",\"http://rhinometric-console-frontend:3002\",\"http://${CUSTOMER_PUBLIC_IP}\",\"http://${CUSTOMER_PUBLIC_IP}:80\",\"http://${CUSTOMER_DOMAIN}\",\"https://${CUSTOMER_DOMAIN}\"]"

# Patch CORS_ORIGINS
sed -i "s|CORS_ORIGINS:.*|CORS_ORIGINS: '${CORS_ORIGINS}'|" "$COMPOSE_NEW"

# Patch GF_SERVER_ROOT_URL
sed -i "s|GF_SERVER_ROOT_URL:.*|GF_SERVER_ROOT_URL: http://${CUSTOMER_PUBLIC_IP}/grafana|" "$COMPOSE_NEW"

# Patch GF_SERVER_DOMAIN
sed -i "s|GF_SERVER_DOMAIN:.*|GF_SERVER_DOMAIN: ${CUSTOMER_DOMAIN}|" "$COMPOSE_NEW"

# Patch GRAFANA_URL in ai-anomaly (the env var in compose, not config.yaml)
sed -i "s|GRAFANA_URL: https://grafana\.rhinometric\.com|GRAFANA_URL: http://${CUSTOMER_DOMAIN}/grafana|" "$COMPOSE_NEW"

# Patch SECRET_KEY (hardcoded in compose)
sed -i "s|SECRET_KEY: k3y_f1x3d_rh1n0m3tr1c_s3cur3_2026|SECRET_KEY: ${SECRET_KEY}|" "$COMPOSE_NEW"

# Patch SMTP in license-server-v2 (hardcoded)
sed -i "s|SMTP_HOST: smtp\.zoho\.eu|SMTP_HOST: ${CUSTOMER_SMTP_HOST}|" "$COMPOSE_NEW"
sed -i "s|SMTP_PORT: 465|SMTP_PORT: ${CUSTOMER_SMTP_PORT}|" "$COMPOSE_NEW"
sed -i "s|SMTP_USER: rafael\.canelon@rhinometric\.com|SMTP_USER: ${CUSTOMER_SMTP_USER}|" "$COMPOSE_NEW"
sed -i "s|SMTP_FROM: rafael\.canelon@rhinometric\.com|SMTP_FROM: ${CUSTOMER_SMTP_FROM}|" "$COMPOSE_NEW"

log_ok "docker-compose patched for tenant: ${TENANT_ID}"

log_ok "All templates processed"

# =============================================================================
# STEP 4: CREATE TENANT RECORD
# =============================================================================
log_step "STEP 4/7: Creating tenant record"

mkdir -p "$TENANT_DIR"

# Copy customer.env as tenant record
cp "$CUSTOMER_ENV" "${TENANT_DIR}/customer.env"

# Store generated credentials (READ-PROTECTED)
cat > "${TENANT_DIR}/credentials.env" << CREDS_EOF
# RHINOMETRIC - Auto-generated credentials for ${TENANT_ID}
# Generated: ${PROVISION_DATE}
# ⚠️  CONFIDENTIAL — Do not share
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
SECRET_KEY=${SECRET_KEY}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${ADMIN_PASSWORD}
CREDS_EOF
chmod 600 "${TENANT_DIR}/credentials.env"

# Copy generated configs as snapshot
cp "${BASE_DIR}/.env.new" "${TENANT_DIR}/env.snapshot"
cp "${BASE_DIR}/nginx/nginx.conf.new" "${TENANT_DIR}/nginx.conf.snapshot"
cp "${BASE_DIR}/alertmanager/alertmanager.yml.new" "${TENANT_DIR}/alertmanager.yml.snapshot"
cp "${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new" "${TENANT_DIR}/ai-anomaly-config.yaml.snapshot"
cp "${COMPOSE_NEW}" "${TENANT_DIR}/docker-compose.yml.snapshot"

# Tenant metadata
cat > "${TENANT_DIR}/metadata.json" << META_EOF
{
  "tenant_id": "${TENANT_ID}",
  "customer_name": "${CUSTOMER_NAME}",
  "customer_id": "${CUSTOMER_ID}",
  "customer_domain": "${CUSTOMER_DOMAIN}",
  "customer_ip": "${CUSTOMER_PUBLIC_IP}",
  "license_tier": "${CUSTOMER_LICENSE_TIER:-essentials}",
  "provisioned_at": "${PROVISION_DATE}",
  "provisioned_by": "provision-customer.sh v2.5.1",
  "platform_version": "2.5.1-hardened",
  "website_monitoring": ${CUSTOMER_WEBSITE_MONITORING:-false},
  "ssl_enabled": ${CUSTOMER_SSL_ENABLED:-false}
}
META_EOF

log_ok "Tenant record created at: ${TENANT_DIR}"
ls -la "${TENANT_DIR}/"

# =============================================================================
# STEP 5: ACTIVATE CONFIGS (move .new → live)
# =============================================================================
log_step "STEP 5/7: Activating configurations"

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY-RUN: Skipping config activation"
    log_info "Generated files (not yet activated):"
    echo "  ${BASE_DIR}/.env.new"
    echo "  ${BASE_DIR}/nginx/nginx.conf.new"
    echo "  ${BASE_DIR}/alertmanager/alertmanager.yml.new"
    echo "  ${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new"
    echo "  ${COMPOSE_NEW}"
else
    # Backup current configs
    BACKUP_DIR="${TENANT_DIR}/backup_pre_provision"
    mkdir -p "$BACKUP_DIR"
    [ -f "${BASE_DIR}/.env" ] && cp "${BASE_DIR}/.env" "${BACKUP_DIR}/.env.bak"
    [ -f "${BASE_DIR}/nginx/nginx.conf" ] && cp "${BASE_DIR}/nginx/nginx.conf" "${BACKUP_DIR}/nginx.conf.bak"
    [ -f "${BASE_DIR}/alertmanager/alertmanager.yml" ] && cp "${BASE_DIR}/alertmanager/alertmanager.yml" "${BACKUP_DIR}/alertmanager.yml.bak"
    [ -f "${BASE_DIR}/rhinometric-ai-anomaly/config.yaml" ] && cp "${BASE_DIR}/rhinometric-ai-anomaly/config.yaml" "${BACKUP_DIR}/ai-anomaly-config.yaml.bak"
    log_ok "Current configs backed up to ${BACKUP_DIR}"

    # Activate new configs
    mv "${BASE_DIR}/.env.new" "${BASE_DIR}/.env"
    mv "${BASE_DIR}/nginx/nginx.conf.new" "${BASE_DIR}/nginx/nginx.conf"
    mv "${BASE_DIR}/alertmanager/alertmanager.yml.new" "${BASE_DIR}/alertmanager/alertmanager.yml"
    mv "${BASE_DIR}/rhinometric-ai-anomaly/config.yaml.new" "${BASE_DIR}/rhinometric-ai-anomaly/config.yaml"

    # Update docker-compose symlink
    ln -sf "docker-compose-v2.5.1-${TENANT_ID}.yml" "${BASE_DIR}/docker-compose.yml"
    log_ok "docker-compose.yml → docker-compose-v2.5.1-${TENANT_ID}.yml"

    log_ok "All configs activated"
fi

# =============================================================================
# STEP 6: DEPLOY STACK
# =============================================================================
log_step "STEP 6/7: Deploying stack"

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY-RUN: Skipping deployment"
    log_info "Would run: cd ${BASE_DIR} && docker-compose up -d --force-recreate"
else
    cd "${BASE_DIR}"

    log_info "Stopping current stack..."
    docker-compose down --timeout 30 2>&1 || true

    log_info "Starting stack with new configuration..."
    docker-compose up -d --force-recreate 2>&1

    log_info "Waiting 60s for services to start..."
    sleep 60

    # Check container status
    RUNNING=$(docker-compose ps --format json 2>/dev/null | python3 -c "
import sys, json
lines = sys.stdin.read().strip().split('\n')
running = 0
total = 0
for line in lines:
    if not line.strip():
        continue
    try:
        obj = json.loads(line)
        total += 1
        state = obj.get('State', obj.get('status', '')).lower()
        if 'running' in state or 'up' in state:
            running += 1
    except:
        pass
print(f'{running}/{total}')
" 2>/dev/null || echo "?/?")

    log_info "Containers running: ${RUNNING}"

    # Healthcheck loop
    log_info "Running healthchecks..."
    MAX_RETRIES=6
    RETRY_DELAY=15
    HEALTH_OK=false

    for i in $(seq 1 $MAX_RETRIES); do
        log_info "Healthcheck attempt $i/${MAX_RETRIES}..."

        # Check nginx health
        NGINX_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/nginx-health 2>/dev/null  || echo "000")

        # Check backend health
        BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health 2>/dev/null  || echo "000")

        # Check Grafana
        GRAFANA_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/grafana/api/health 2>/dev/null  || echo "000")

        log_info "  nginx=/nginx-health → ${NGINX_OK}  |  backend=/api/health → ${BACKEND_OK}  |  grafana= → ${GRAFANA_OK}"

        if [ "$NGINX_OK" = "200" ] && [ "$BACKEND_OK" = "200" ] && [ "$GRAFANA_OK" = "200" ]; then
            HEALTH_OK=true
            break
        fi

        if [ $i -lt $MAX_RETRIES ]; then
            log_warn "Some checks failed, retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
        fi
    done

    if [ "$HEALTH_OK" = true ]; then
        log_ok "All healthchecks PASSED ✓"
    else
        log_error "Some healthchecks FAILED after ${MAX_RETRIES} attempts"
        log_error "Check containers: docker-compose ps"
        log_error "Check logs: docker-compose logs --tail=50 <service>"
    fi
fi

# =============================================================================
# STEP 7: GENERATE PROVISION REPORT
# =============================================================================
log_step "STEP 7/7: Generating provision report"

REPORT_FILE="${BASE_DIR}/audits/PROVISION_${TENANT_ID}_${PROVISION_TIMESTAMP}.md"
mkdir -p "${BASE_DIR}/audits"

cat > "$REPORT_FILE" << REPORT_EOF
# Rhinometric — Provision Report

## Tenant Information

| Field | Value |
|-------|-------|
| **Tenant ID** | \`${TENANT_ID}\` |
| **Customer Name** | ${CUSTOMER_NAME} |
| **Customer ID** | ${CUSTOMER_ID} |
| **Domain** | ${CUSTOMER_DOMAIN} |
| **Public IP** | ${CUSTOMER_PUBLIC_IP} |
| **License Tier** | ${CUSTOMER_LICENSE_TIER:-essentials} |
| **Provisioned At** | ${PROVISION_DATE} |
| **Platform Version** | 2.5.1-hardened |
| **Mode** | $([ "$DRY_RUN" = true ] && echo 'DRY-RUN'  || echo 'FULL DEPLOY') |

## Generated Credentials

| Credential | Value |
|-----------|-------|
| **Admin User** | \`admin\` |
| **Admin Password** | \`${ADMIN_PASSWORD}\` |
| **Grafana User** | \`admin\` |
| **Grafana Password** | \`${GRAFANA_PASSWORD}\` |

> ⚠️ Full credentials stored at: \`${TENANT_DIR}/credentials.env\` (chmod 600)

## Configuration Files Modified

| File | Status |
|------|--------|
| \`.env\` | ✅ Generated with unique passwords |
| \`nginx/nginx.conf\` | ✅ Domain: ${CUSTOMER_DOMAIN} |
| \`alertmanager/alertmanager.yml\` | ✅ SMTP: ${CUSTOMER_SMTP_HOST}, Email: ${CUSTOMER_ALERT_EMAIL} |
| \`rhinometric-ai-anomaly/config.yaml\` | ✅ CORS: ${CUSTOMER_DOMAIN} |
| \`docker-compose-v2.5.1-${TENANT_ID}.yml\` | ✅ CORS, Grafana URLs, SMTP patched |

## Features

| Feature | Status |
|---------|--------|
| Website Monitoring | $([ "${CUSTOMER_WEBSITE_MONITORING:-false}" = "true" ] && echo "✅ Enabled (${CUSTOMER_WEBSITE_URL})"  || echo '❌ Disabled') |
| SSL/TLS | $([ "${CUSTOMER_SSL_ENABLED:-false}" = "true" ] && echo '✅ Enabled'  || echo '❌ Disabled (HTTP only)') |
| Slack Notifications | $([ -n "${CUSTOMER_SLACK_WEBHOOK:-}" ] && echo '✅ Enabled'  || echo '❌ Disabled (no webhook)') |

## Healthcheck Results

$(if [ "$DRY_RUN" = true ]; then
    echo "| Endpoint | Status |"
    echo "|----------|--------|"
    echo "| All | ⏭️ Skipped (dry-run) |"
elif [ "${HEALTH_OK:-false}" = true ]; then
    echo "| Endpoint | Status |"
    echo "|----------|--------|"
    echo "| \`/nginx-health\` | ✅ 200 |"
    echo "| \`/api/health\` | ✅ 200 |"
    echo "| \`/grafana/api/health\` | ✅ 200 |"
else
    echo "| Endpoint | Status |"
    echo "|----------|--------|"
    echo "| \`/nginx-health\` | ${NGINX_OK:-?} |"
    echo "| \`/api/health\` | ${BACKEND_OK:-?} |"
    echo "| \`/grafana/api/health\` | ${GRAFANA_OK:-?} |"
    echo ""
    echo "> ⚠️ Some healthchecks failed. Review with \`docker-compose logs\`"
fi)

## Tenant Record

\`\`\`
${TENANT_DIR}/
├── customer.env              # Customer config (source)
├── credentials.env           # Auto-generated passwords (600)
├── metadata.json             # Tenant metadata
├── env.snapshot              # Generated .env copy
├── nginx.conf.snapshot       # Generated nginx.conf copy
├── alertmanager.yml.snapshot # Generated alertmanager copy
├── ai-anomaly-config.yaml.snapshot
├── docker-compose.yml.snapshot
└── backup_pre_provision/     # Pre-provision backups
\`\`\`

## Access URLs

| Service | URL |
|---------|-----|
| Console | http://${CUSTOMER_PUBLIC_IP}/ |
| Console (domain) | http://${CUSTOMER_DOMAIN}/ |
| Grafana (embed) | http://${CUSTOMER_PUBLIC_IP}/grafana/ |
| Grafana (admin) | http://${CUSTOMER_PUBLIC_IP}/admin/grafana/ |
| API Health | http://${CUSTOMER_PUBLIC_IP}/api/health |

## Next Steps

1. Configure DNS: \`${CUSTOMER_DOMAIN}\` → \`${CUSTOMER_PUBLIC_IP}\`
2. $([ "${CUSTOMER_SSL_ENABLED:-false}" = "true" ] && echo "Install SSL certs and enable HTTPS"  || echo "Consider enabling SSL/TLS for production")
3. Login at http://${CUSTOMER_PUBLIC_IP}/ with admin / \`${ADMIN_PASSWORD}\`
4. Verify Grafana dashboards at http://${CUSTOMER_PUBLIC_IP}/grafana/
5. Test alert delivery to ${CUSTOMER_ALERT_EMAIL}

---
*Generated by provision-customer.sh v2.5.1 — ${PROVISION_DATE}*
REPORT_EOF

log_ok "Report saved: ${REPORT_FILE}"

# =============================================================================
# SUMMARY
# =============================================================================
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              PROVISIONING COMPLETE                        ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}  Tenant:     ${TENANT_ID}"
echo -e "${GREEN}║${NC}  Domain:     ${CUSTOMER_DOMAIN}"
echo -e "${GREEN}║${NC}  IP:         ${CUSTOMER_PUBLIC_IP}"
echo -e "${GREEN}║${NC}  Console:    http://${CUSTOMER_PUBLIC_IP}/"
echo -e "${GREEN}║${NC}  Admin:      admin / ${ADMIN_PASSWORD}"
echo -e "${GREEN}║${NC}  Report:     ${REPORT_FILE}"
echo -e "${GREEN}║${NC}  Tenant dir: ${TENANT_DIR}/"
if [ "$DRY_RUN" = true ]; then
echo -e "${YELLOW}║${NC}  ⚠️  DRY-RUN: No deployment was made"
echo -e "${YELLOW}║${NC}  Review .new files and run without --dry-run to deploy"
fi
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
