#!/bin/bash

# Oracle Cloud IP Discovery and DNS Setup Helper
# ==============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running on Oracle Cloud
check_oracle_cloud() {
    log_info "Checking if running on Oracle Cloud..."
    
    if curl -s -m 5 http://169.254.169.254/opc/v1/instance/ > /dev/null 2>&1; then
        log_success "✅ Running on Oracle Cloud Infrastructure"
        return 0
    else
        log_warning "⚠️  Not running on Oracle Cloud (or metadata service unavailable)"
        return 1
    fi
}

# Get public IP address
get_public_ip() {
    log_info "Getting public IP address..."
    
    # Try multiple services to get public IP
    local ip=""
    
    # Try Oracle Cloud metadata first
    if check_oracle_cloud; then
        ip=$(curl -s -m 10 http://169.254.169.254/opc/v1/vnics/ | jq -r '.[0].publicIp' 2>/dev/null || echo "")
        if [[ -n "$ip" && "$ip" != "null" ]]; then
            log_success "✅ Oracle Cloud Public IP: $ip"
            echo "$ip"
            return 0
        fi
    fi
    
    # Fallback to external services
    for service in "ifconfig.me" "ipinfo.io/ip" "icanhazip.com" "checkip.amazonaws.com"; do
        ip=$(curl -s -m 5 "$service" 2>/dev/null | grep -E '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$' || echo "")
        if [[ -n "$ip" ]]; then
            log_success "✅ Public IP (via $service): $ip"
            echo "$ip"
            return 0
        fi
    done
    
    log_error "❌ Could not determine public IP address"
    return 1
}

# Get Oracle Cloud instance details
get_oracle_details() {
    if ! check_oracle_cloud; then
        return 1
    fi
    
    log_info "Getting Oracle Cloud instance details..."
    
    # Get instance metadata
    local instance_info=$(curl -s -m 10 http://169.254.169.254/opc/v1/instance/)
    local vnic_info=$(curl -s -m 10 http://169.254.169.254/opc/v1/vnics/)
    
    echo ""
    log_info "📊 Oracle Cloud Instance Information:"
    echo "====================================="
    
    # Parse and display information
    if command -v jq >/dev/null 2>&1; then
        echo "Instance ID:     $(echo "$instance_info" | jq -r '.id' 2>/dev/null || echo 'N/A')"
        echo "Display Name:    $(echo "$instance_info" | jq -r '.displayName' 2>/dev/null || echo 'N/A')"
        echo "Shape:           $(echo "$instance_info" | jq -r '.shape' 2>/dev/null || echo 'N/A')"
        echo "Region:          $(echo "$instance_info" | jq -r '.region' 2>/dev/null || echo 'N/A')"
        echo "Availability Domain: $(echo "$instance_info" | jq -r '.availabilityDomain' 2>/dev/null || echo 'N/A')"
        echo ""
        echo "Private IP:      $(echo "$vnic_info" | jq -r '.[0].privateIp' 2>/dev/null || echo 'N/A')"
        echo "Public IP:       $(echo "$vnic_info" | jq -r '.[0].publicIp' 2>/dev/null || echo 'N/A')"
        echo "Subnet:          $(echo "$vnic_info" | jq -r '.[0].subnetCidrBlock' 2>/dev/null || echo 'N/A')"
    else
        log_warning "⚠️  jq not installed, showing raw metadata:"
        echo "$instance_info"
        echo ""
        echo "$vnic_info"
    fi
}

# Generate Cloudflare DNS records
generate_dns_records() {
    local public_ip="$1"
    
    if [[ -z "$public_ip" ]]; then
        log_error "No public IP provided"
        return 1
    fi
    
    log_info "📋 Cloudflare DNS Records Configuration:"
    echo "========================================"
    echo ""
    echo "Add these A records in Cloudflare DNS for rhinometric.com:"
    echo ""
    
    # API records (no proxy for direct API access)
    cat << EOF
┌─────────────────────┬──────┬─────────────────────┬─────────┬──────┐
│ Name                │ Type │ Content             │ Proxy   │ TTL  │
├─────────────────────┼──────┼─────────────────────┼─────────┼──────┤
│ api                 │ A    │ $public_ip         │ 🟠 DNS   │ Auto │
│ staging-api         │ A    │ $public_ip         │ 🟠 DNS   │ Auto │
│ dev-api             │ A    │ $public_ip         │ 🟠 DNS   │ Auto │
│ @                   │ A    │ $public_ip         │ 🟡 Proxy │ Auto │
│ staging             │ A    │ $public_ip         │ 🟡 Proxy │ Auto │
│ dev                 │ A    │ $public_ip         │ 🟡 Proxy │ Auto │
└─────────────────────┴──────┴─────────────────────┴─────────┴──────┘
EOF
    
    echo ""
    log_info "📝 Notes:"
    echo "• API subdomains use DNS only (🟠) for direct access"
    echo "• Frontend subdomains use Proxy (🟡) for CDN and security"
    echo "• Propagation time: 5-10 minutes typically"
    echo ""
}

# Test DNS resolution
test_dns_resolution() {
    local domains=("api.rhinometric.com" "staging-api.rhinometric.com" "dev-api.rhinometric.com")
    
    log_info "🧪 Testing DNS resolution..."
    echo "=============================="
    
    for domain in "${domains[@]}"; do
        printf "%-25s: " "$domain"
        
        local resolved_ip=$(nslookup "$domain" 2>/dev/null | grep -A1 "Name:" | grep "Address:" | head -1 | awk '{print $2}' || echo "")
        
        if [[ -n "$resolved_ip" ]]; then
            echo -e "${GREEN}✅ $resolved_ip${NC}"
        else
            echo -e "${RED}❌ Not resolved${NC}"
        fi
    done
    echo ""
}

# Test API endpoints
test_api_endpoints() {
    local endpoints=("api.rhinometric.com" "staging-api.rhinometric.com" "dev-api.rhinometric.com")
    local ports=("443" "443" "443")  # Assuming HTTPS after SSL setup
    
    log_info "🌐 Testing API endpoints..."
    echo "============================"
    
    for i in "${!endpoints[@]}"; do
        local endpoint="${endpoints[$i]}"
        local port="${ports[$i]}"
        
        printf "%-25s: " "$endpoint"
        
        # Try HTTPS first, then HTTP
        local response=$(curl -s -m 5 "https://$endpoint/api/v1/health" 2>/dev/null || curl -s -m 5 "http://$endpoint/api/v1/health" 2>/dev/null || echo "")
        
        if [[ -n "$response" ]]; then
            local status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")
            if [[ "$status" == "healthy" ]]; then
                echo -e "${GREEN}✅ Healthy${NC}"
            elif [[ "$status" == "unhealthy" ]]; then
                echo -e "${YELLOW}⚠️  Unhealthy${NC}"
            else
                echo -e "${BLUE}ℹ️  Response received${NC}"
            fi
        else
            echo -e "${RED}❌ No response${NC}"
        fi
    done
    echo ""
}

# Generate summary report
generate_summary() {
    local public_ip="$1"
    
    echo ""
    log_success "🎉 Oracle Cloud DNS Setup Summary"
    echo "================================="
    echo ""
    echo "🌐 Your Public IP: $public_ip"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Configure DNS records in Cloudflare (shown above)"
    echo "2. Wait 5-10 minutes for DNS propagation"  
    echo "3. Run: sudo ./infrastructure/configure-nginx-domains.sh"
    echo "4. Test endpoints with curl commands"
    echo ""
    echo "🔧 Management URLs (after setup):"
    echo "• Production API:  https://api.rhinometric.com/api/v1/health"
    echo "• Staging API:     https://staging-api.rhinometric.com/api/v1/health"
    echo "• Development API: https://dev-api.rhinometric.com/api/v1/health"
    echo ""
}

# Main function
main() {
    local command="${1:-discover}"
    
    case "$command" in
        "discover")
            log_info "🔍 Discovering Oracle Cloud configuration..."
            
            local public_ip
            public_ip=$(get_public_ip)
            
            if [[ $? -eq 0 && -n "$public_ip" ]]; then
                get_oracle_details
                generate_dns_records "$public_ip"
                generate_summary "$public_ip"
            else
                log_error "Failed to get public IP address"
                exit 1
            fi
            ;;
            
        "test-dns")
            test_dns_resolution
            ;;
            
        "test-api")
            test_api_endpoints
            ;;
            
        "test-all")
            test_dns_resolution
            test_api_endpoints
            ;;
            
        *)
            echo "Oracle Cloud DNS Setup Helper"
            echo "============================="
            echo ""
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  discover   Get IP and show DNS configuration (default)"
            echo "  test-dns   Test DNS resolution for domains"
            echo "  test-api   Test API endpoint connectivity"  
            echo "  test-all   Run all tests"
            echo ""
            echo "Examples:"
            echo "  $0                    # Discover configuration"
            echo "  $0 test-dns          # Test DNS only"
            echo "  $0 test-all          # Full connectivity test"
            ;;
    esac
}

# Run main function
main "$@"