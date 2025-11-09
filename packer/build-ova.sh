#!/bin/bash
# build-ova.sh - Build RhinoMetric Demo OVA with Packer
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v packer &> /dev/null; then
        log_error "Packer not found. Install: https://www.packer.io/downloads"
        exit 1
    fi
    
    packer_version=$(packer version | head -1 | awk '{print $2}')
    log_info "Packer version: $packer_version"
    
    if ! command -v VBoxManage &> /dev/null; then
        log_warn "VirtualBox not found - VirtualBox builder will fail"
    else
        vbox_version=$(VBoxManage --version)
        log_info "VirtualBox version: $vbox_version"
    fi
    
    if [ ! -d "../deploy/demo" ]; then
        log_error "deploy/demo directory not found"
        exit 1
    fi
    
    log_info "✓ Prerequisites validated"
}

validate_template() {
    log_info "Validating Packer template..."
    
    if ! packer validate ubuntu2204-rhinometric.json; then
        log_error "Template validation failed"
        exit 1
    fi
    
    log_info "✓ Template validated"
}

build_ova() {
    log_info "========================================="
    log_info "Building RhinoMetric v2.5.0 Demo OVA"
    log_info "========================================="
    log_info "This will take 30-45 minutes..."
    log_info ""
    
    mkdir -p logs
    local log_file="logs/build-$(date +%Y%m%d-%H%M%S).log"
    
    log_info "Build log: $log_file"
    
    if packer build -force ubuntu2204-rhinometric.json 2>&1 | tee "$log_file"; then
        log_info ""
        log_info "========================================="
        log_info "✅ BUILD SUCCESSFUL"
        log_info "========================================="
        return 0
    else
        log_error ""
        log_error "========================================="
        log_error "❌ BUILD FAILED"
        log_error "========================================="
        log_error "Check logs at: $log_file"
        return 1
    fi
}

verify_ova() {
    log_info "Verifying OVA output..."
    
    local ova_file
    ova_file=$(find . -name "*.ova" -type f -mmin -60 | head -1)
    
    if [ -z "$ova_file" ]; then
        log_error "OVA file not found"
        return 1
    fi
    
    local ova_size_mb
    ova_size_mb=$(du -m "$ova_file" | awk '{print $1}')
    
    log_info "OVA file: $ova_file"
    log_info "OVA size: ${ova_size_mb}MB"
    
    if [ "$ova_size_mb" -gt 5000 ]; then
        log_warn "OVA size exceeds 5GB (${ova_size_mb}MB)"
    fi
    
    log_info "Generating SHA256 checksum..."
    sha256sum "$ova_file" > "${ova_file}.sha256"
    
    log_info "✓ Checksum: ${ova_file}.sha256"
}

print_usage() {
    echo ""
    log_info "========================================="
    log_info "Next Steps"
    log_info "========================================="
    echo ""
    echo "1. Import OVA:"
    echo "   VBoxManage import output-virtualbox-iso/*.ova"
    echo ""
    echo "2. Start VM:"
    echo "   VBoxManage startvm rhinometric-demo --type headless"
    echo ""
    echo "3. Get VM IP:"
    echo "   VBoxManage guestproperty get rhinometric-demo \"/VirtualBox/GuestInfo/Net/0/V4/IP\""
    echo ""
    echo "4. Access Grafana:"
    echo "   https://<VM_IP>:3000 (admin / rhinometric_demo)"
    echo ""
    echo "5. SSH and verify:"
    echo "   ssh rhinouser@<VM_IP> (password: rhinometric)"
    echo "   cd /opt/rhinometric/deploy/demo && bash scripts/smoke-test.sh"
    echo ""
}

main() {
    local start_time
    start_time=$(date +%s)
    
    check_prerequisites
    validate_template
    
    if build_ova; then
        verify_ova
        
        local end_time
        end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        
        log_info ""
        log_info "Build completed in ${minutes}m ${seconds}s"
        
        print_usage
        exit 0
    else
        exit 1
    fi
}

main "$@"
