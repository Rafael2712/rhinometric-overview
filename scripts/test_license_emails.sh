#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════
# RHINOMETRIC v2.5.0 - LICENSE EMAIL TESTING SCRIPT
# ════════════════════════════════════════════════════════════════════════════
#
# Purpose: Test end-to-end license creation and email sending
# Usage:   ./test_license_emails.sh [LICENSE_SERVER_URL]
# Example: ./test_license_emails.sh https://licensing.rhinometric.com:5000
#          ./test_license_emails.sh http://localhost:5000
#
# This script will:
#  1. Health check del License Server
#  2. Crear licencia TRIAL de prueba
#  3. Crear licencia DEMO_CLOUD de prueba
#  4. Mostrar las respuestas para que verifiques que los emails se envían
#
# IMPORTANTE: Edita la variable TEST_EMAIL con tu correo real antes de ejecutar
# ════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# License Server URL (default: localhost)
LICENSE_SERVER_URL="${1:-http://localhost:5000}"

# ⚠️ MODIFICA ESTO CON TU EMAIL REAL
TEST_EMAIL="${TEST_EMAIL:-your-email@example.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ═══════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

print_header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${PURPLE}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# PRE-CHECKS
# ═══════════════════════════════════════════════════════════════════════════

print_header "RHINOMETRIC v2.5.0 - LICENSE EMAIL TESTING"

# Check dependencies
if ! command -v curl &> /dev/null; then
    print_error "curl is not installed. Please install it first."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    print_warning "jq is not installed. Output will not be formatted."
    print_info "To install: sudo apt-get install jq  (Ubuntu/Debian)"
    print_info "            brew install jq           (macOS)"
    USE_JQ=false
else
    USE_JQ=true
fi

# Validate email
if [[ "$TEST_EMAIL" == "your-email@example.com" ]]; then
    print_error "Please edit this script and change TEST_EMAIL to your real email address"
    print_info "Edit line 27 of this file: TEST_EMAIL=\"your-email@example.com\""
    exit 1
fi

print_info "License Server URL: ${BOLD}${LICENSE_SERVER_URL}${NC}"
print_info "Test Email: ${BOLD}${TEST_EMAIL}${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════

print_header "TEST 1: Health Check"

HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${LICENSE_SERVER_URL}/api/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | sed '$ d')

if [[ "$HTTP_CODE" == "200" ]]; then
    print_success "License Server is healthy (HTTP 200)"
    
    if [[ "$USE_JQ" == true ]]; then
        echo -e "${CYAN}Response:${NC}"
        echo "$BODY" | jq '.'
    else
        echo "$BODY"
    fi
else
    print_error "Health check failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: CREATE TRIAL LICENSE
# ═══════════════════════════════════════════════════════════════════════════

print_header "TEST 2: Create TRIAL License (14 días)"

TRIAL_PAYLOAD=$(cat <<EOF
{
  "customer_name": "Test User TRIAL",
  "client_email": "${TEST_EMAIL}",
  "client_company": "Test Company TRIAL",
  "license_type": "trial",
  "client_phone": "+34123456789",
  "client_country": "España",
  "client_city": "Madrid",
  "industry": "Technology",
  "company_size": "10-50",
  "servers_count": 5,
  "services_count": 15
}
EOF
)

print_info "Creating TRIAL license..."
TRIAL_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "${LICENSE_SERVER_URL}/api/admin/licenses" \
    -H "Content-Type: application/json" \
    -d "$TRIAL_PAYLOAD")

HTTP_CODE=$(echo "$TRIAL_RESPONSE" | tail -n1)
BODY=$(echo "$TRIAL_RESPONSE" | sed '$ d')

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
    print_success "TRIAL license created (HTTP $HTTP_CODE)"
    
    if [[ "$USE_JQ" == true ]]; then
        LICENSE_KEY=$(echo "$BODY" | jq -r '.license_key')
        EXPIRES_AT=$(echo "$BODY" | jq -r '.expires_at')
        EMAIL_SENT=$(echo "$BODY" | jq -r '.email_sent')
        
        echo ""
        echo -e "${BOLD}License Details:${NC}"
        echo -e "  ${CYAN}License Key:${NC} ${GREEN}${LICENSE_KEY}${NC}"
        echo -e "  ${CYAN}Expires:${NC} ${YELLOW}${EXPIRES_AT}${NC}"
        echo -e "  ${CYAN}Email Sent:${NC} ${GREEN}${EMAIL_SENT}${NC}"
        echo ""
        echo -e "${CYAN}Full Response:${NC}"
        echo "$BODY" | jq '.'
    else
        echo "$BODY"
    fi
    
    print_warning "Check your email inbox (${TEST_EMAIL}) for the TRIAL license email"
    print_info "Email should contain:"
    print_info "  • License key"
    print_info "  • Download button: 'Descargar Instalador Linux (14 días)'"
    print_info "  • Link to ${LICENSE_SERVER_URL}/downloads/trial-installer"
    print_info "  • Links to PDFs (ES/EN)"
    
else
    print_error "Failed to create TRIAL license (HTTP $HTTP_CODE)"
    echo "$BODY"
fi

# Wait before next test
sleep 3

# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: CREATE DEMO_CLOUD LICENSE
# ═══════════════════════════════════════════════════════════════════════════

print_header "TEST 3: Create DEMO_CLOUD License (4 horas)"

# NOTE: Backend might not support "demo_cloud" type yet
# Try with "trial" or "annual" depending on your implementation

DEMO_PAYLOAD=$(cat <<EOF
{
  "customer_name": "Test User DEMO",
  "client_email": "${TEST_EMAIL}",
  "client_company": "Test Company DEMO",
  "license_type": "trial",
  "client_phone": "+34987654321",
  "client_country": "España",
  "client_city": "Barcelona",
  "industry": "Finance",
  "company_size": "1-10",
  "servers_count": 3,
  "services_count": 10,
  "notes": "Testing DEMO OVA workflow"
}
EOF
)

print_info "Creating DEMO license..."
DEMO_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "${LICENSE_SERVER_URL}/api/admin/licenses" \
    -H "Content-Type: application/json" \
    -d "$DEMO_PAYLOAD")

HTTP_CODE=$(echo "$DEMO_RESPONSE" | tail -n1)
BODY=$(echo "$DEMO_RESPONSE" | sed '$ d')

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
    print_success "DEMO license created (HTTP $HTTP_CODE)"
    
    if [[ "$USE_JQ" == true ]]; then
        LICENSE_KEY=$(echo "$BODY" | jq -r '.license_key')
        EXPIRES_AT=$(echo "$BODY" | jq -r '.expires_at')
        EMAIL_SENT=$(echo "$BODY" | jq -r '.email_sent')
        
        echo ""
        echo -e "${BOLD}License Details:${NC}"
        echo -e "  ${CYAN}License Key:${NC} ${GREEN}${LICENSE_KEY}${NC}"
        echo -e "  ${CYAN}Expires:${NC} ${YELLOW}${EXPIRES_AT}${NC}"
        echo -e "  ${CYAN}Email Sent:${NC} ${GREEN}${EMAIL_SENT}${NC}"
        echo ""
        echo -e "${CYAN}Full Response:${NC}"
        echo "$BODY" | jq '.'
    else
        echo "$BODY"
    fi
    
    print_warning "Check your email inbox (${TEST_EMAIL}) for the DEMO license email"
    print_info "Email should contain:"
    print_info "  • License key"
    print_info "  • Download button: 'Descargar OVA Demo (4 horas)'"
    print_info "  • Link to ${LICENSE_SERVER_URL}/downloads/demo-ova"
    print_info "  • Links to PDFs (ES/EN)"
    
else
    print_error "Failed to create DEMO license (HTTP $HTTP_CODE)"
    echo "$BODY"
fi

# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: VERIFY DOWNLOAD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

print_header "TEST 4: Verify Download Endpoints Accessibility"

# Test /downloads/info
print_info "Testing /downloads/info endpoint..."
INFO_RESPONSE=$(curl -s -w "\n%{http_code}" "${LICENSE_SERVER_URL}/downloads/info")
HTTP_CODE=$(echo "$INFO_RESPONSE" | tail -n1)

if [[ "$HTTP_CODE" == "200" ]]; then
    print_success "/downloads/info is accessible"
    if [[ "$USE_JQ" == true ]]; then
        BODY=$(echo "$INFO_RESPONSE" | sed '$ d')
        echo "$BODY" | jq '.'
    fi
else
    print_error "/downloads/info failed (HTTP $HTTP_CODE)"
fi

# Test demo-ova endpoint (HEAD request to avoid downloading)
print_info "Testing /downloads/demo-ova endpoint (HEAD)..."
DEMO_HEAD=$(curl -I -s -w "\n%{http_code}" "${LICENSE_SERVER_URL}/downloads/demo-ova" | tail -n1)

if [[ "$DEMO_HEAD" == "200" ]]; then
    print_success "/downloads/demo-ova is accessible (ready to download)"
elif [[ "$DEMO_HEAD" == "404" ]]; then
    print_warning "/downloads/demo-ova returns 404 (OVA file not yet uploaded to server)"
else
    print_error "/downloads/demo-ova failed (HTTP $DEMO_HEAD)"
fi

# Test trial-installer endpoint
print_info "Testing /downloads/trial-installer endpoint (HEAD)..."
TRIAL_HEAD=$(curl -I -s -w "\n%{http_code}" "${LICENSE_SERVER_URL}/downloads/trial-installer" | tail -n1)

if [[ "$TRIAL_HEAD" == "200" ]]; then
    print_success "/downloads/trial-installer is accessible (ready to download)"
elif [[ "$TRIAL_HEAD" == "404" ]]; then
    print_warning "/downloads/trial-installer returns 404 (installer not yet uploaded)"
else
    print_error "/downloads/trial-installer failed (HTTP $TRIAL_HEAD)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

print_header "TEST SUMMARY"

echo -e "${BOLD}What to check now:${NC}"
echo ""
echo -e "${CYAN}1. EMAIL INBOX${NC}"
echo -e "   Open your email client and check ${BOLD}${TEST_EMAIL}${NC}"
echo -e "   You should have received ${BOLD}2 emails${NC} (one TRIAL, one DEMO)"
echo ""
echo -e "${CYAN}2. EMAIL CONTENT${NC}"
echo -e "   Each email should have:"
echo -e "   ${GREEN}✓${NC} License key displayed prominently"
echo -e "   ${GREEN}✓${NC} Download button with correct URL"
echo -e "   ${GREEN}✓${NC} Links to documentation PDFs (ES/EN)"
echo -e "   ${GREEN}✓${NC} Rhinometric logo (SVG embedded)"
echo -e "   ${GREEN}✓${NC} Professional gradient design"
echo ""
echo -e "${CYAN}3. CLICK LINKS${NC}"
echo -e "   ${YELLOW}TRIAL email:${NC} Click 'Descargar Instalador Linux'"
echo -e "   → Should download ${BOLD}rhinometric-trial-2.5.0-install.sh${NC}"
echo ""
echo -e "   ${PURPLE}DEMO email:${NC} Click 'Descargar OVA Demo'"
echo -e "   → Should download ${BOLD}rhinometric-demo-2.5.0.ova${NC} (or 404 if not uploaded yet)"
echo ""
echo -e "   ${BLUE}PDF links:${NC} Click on 'Guía Instalación (ES)' or 'User Manual (EN)'"
echo -e "   → Should open PDFs in browser or download"
echo ""
echo -e "${CYAN}4. VERIFY URL STRUCTURE${NC}"
echo -e "   Download URLs should be:"
echo -e "   ${GREEN}${LICENSE_SERVER_URL}/downloads/demo-ova${NC}"
echo -e "   ${GREEN}${LICENSE_SERVER_URL}/downloads/trial-installer${NC}"
echo ""
echo -e "${CYAN}5. SPAM FOLDER${NC}"
echo -e "   ${YELLOW}⚠️${NC}  If emails don't appear, check your spam/junk folder"
echo -e "   ${YELLOW}⚠️${NC}  Zoho SMTP may require SPF/DKIM verification for production"
echo ""

print_success "Testing complete!"
print_info "For detailed documentation, see: docs/v2.5.0/EMAIL_TESTING.md"

echo ""
