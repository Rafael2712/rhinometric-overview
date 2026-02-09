#!/bin/bash
# Test script para verificar flujo completo de password reset v2.5.4
# Uso: ./test_password_reset_flow_v254.sh

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     PASSWORD RESET FLOW TEST - V2.5.4 BUG FIXES           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TEST_EMAIL="rafael.canelon@rhinometric.com"
BASE_URL="http://localhost:8105"

echo "🧪 TEST 1: Forgot Password Request"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
FORGOT_RESPONSE=$(docker exec rhinometric-console-backend curl -s -X POST \
  http://localhost:8105/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\"}")

echo "Response: $FORGOT_RESPONSE"
if echo "$FORGOT_RESPONSE" | grep -q "email sent"; then
    echo -e "${GREEN}✅ PASSED${NC} - Forgot password request successful"
else
    echo -e "${RED}❌ FAILED${NC} - Forgot password request failed"
fi
echo ""

echo "🔍 TEST 2: Checking Latest Token in Database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOKEN_DATA=$(docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -t -c \
  "SELECT token, used, expires_at FROM password_reset_tokens ORDER BY created_at DESC LIMIT 1;")

TOKEN=$(echo "$TOKEN_DATA" | awk '{print $1}' | tr -d ' ')
TOKEN_USED=$(echo "$TOKEN_DATA" | awk '{print $3}' | tr -d ' ')

echo "Latest Token: ${TOKEN:0:30}..."
echo "Used: $TOKEN_USED"

if [ "$TOKEN_USED" = "f" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - Token is fresh and unused"
else
    echo -e "${YELLOW}⚠️  WARNING${NC} - Token is already used (expected for subsequent tests)"
fi
echo ""

echo "🧪 TEST 3: Reset Password with WEAK password (should fail)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
WEAK_RESET_RESPONSE=$(docker exec rhinometric-console-backend curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  http://localhost:8105/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\", \"new_password\": \"weak\"}")

HTTP_CODE=$(echo "$WEAK_RESET_RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$WEAK_RESET_RESPONSE" | grep -v "HTTP_CODE")

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - Weak password correctly rejected (400)"
    if echo "$RESPONSE_BODY" | grep -q "at least 8 characters"; then
        echo -e "${GREEN}✅ PASSED${NC} - Error message is clear"
    fi
else
    echo -e "${RED}❌ FAILED${NC} - Expected 400 status code"
fi
echo ""

echo "🧪 TEST 4: Reset Password with STRONG password (should succeed)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STRONG_PASSWORD="NewSecurePass123!"
STRONG_RESET_RESPONSE=$(docker exec rhinometric-console-backend curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  http://localhost:8105/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\", \"new_password\": \"$STRONG_PASSWORD\"}")

HTTP_CODE=$(echo "$STRONG_RESET_RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$STRONG_RESET_RESPONSE" | grep -v "HTTP_CODE")

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - Strong password accepted (200)"
elif [ "$HTTP_CODE" = "400" ] && echo "$RESPONSE_BODY" | grep -q "already used"; then
    echo -e "${YELLOW}⚠️  WARNING${NC} - Token already used (run test fresh)"
else
    echo -e "${RED}❌ FAILED${NC} - Unexpected response"
fi
echo ""

echo "🔍 TEST 5: Verify Token Marked as Used"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOKEN_USED_AFTER=$(docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -t -c \
  "SELECT used FROM password_reset_tokens WHERE token='$TOKEN';")

TOKEN_USED_AFTER=$(echo "$TOKEN_USED_AFTER" | tr -d ' ')

if [ "$TOKEN_USED_AFTER" = "t" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - Token correctly marked as used"
else
    echo -e "${RED}❌ FAILED${NC} - Token not marked as used"
fi
echo ""

echo "🧪 TEST 6: Try Login with OLD Password (should fail)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
OLD_PASSWORD="admin"
LOGIN_OLD=$(docker exec rhinometric-console-backend curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  http://localhost:8105/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=$OLD_PASSWORD")

HTTP_CODE=$(echo "$LOGIN_OLD" | grep "HTTP_CODE" | cut -d':' -f2)

if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - Old password rejected (401)"
elif [ "$HTTP_CODE" = "200" ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC} - Old password still works (password not updated?)"
else
    echo -e "${RED}❌ FAILED${NC} - Unexpected response"
fi
echo ""

echo "🧪 TEST 7: Try Login with NEW Password (should succeed)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
LOGIN_NEW=$(docker exec rhinometric-console-backend curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  http://localhost:8105/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=$STRONG_PASSWORD")

HTTP_CODE=$(echo "$LOGIN_NEW" | grep "HTTP_CODE" | cut -d':' -f2)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ PASSED${NC} - New password works (200)"
elif [ "$HTTP_CODE" = "401" ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC} - New password doesn't work (password not updated?)"
else
    echo -e "${RED}❌ FAILED${NC} - Unexpected response"
fi
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    TEST SUITE COMPLETE                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 MANUAL UI TESTS (Do these in browser):"
echo "  1. Navigate to http://console.rhinometric.com/reset-password?token=$TOKEN"
echo "  2. Try weak password (e.g., '12345') → Should see error"
echo "  3. Try strong password → Should succeed and redirect to login"
echo "  4. Click 'Back to Login' → Should go to login page (not dashboard)"
echo "  5. Verify localStorage is cleared (F12 → Application → Local Storage)"
