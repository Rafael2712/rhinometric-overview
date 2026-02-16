#!/bin/bash
set -e

# SaaS Monitoring Platform - Oracle Cloud Deployment Script
# =========================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if OCI CLI is installed (optional but recommended)
    if ! command -v oci &> /dev/null; then
        print_warning "OCI CLI is not installed. It's recommended for easier setup."
    fi
    
    print_success "Prerequisites check completed"
}

# Setup configuration
setup_config() {
    print_status "Setting up configuration..."
    
    # Copy terraform.tfvars if it doesn't exist
    if [ ! -f "terraform.tfvars" ]; then
        if [ -f "terraform.tfvars.example" ]; then
            cp terraform.tfvars.example terraform.tfvars
            print_warning "Created terraform.tfvars from example. Please edit it with your OCI credentials."
            print_status "Opening terraform.tfvars for editing..."
            
            # Try to open with common editors
            if command -v code &> /dev/null; then
                code terraform.tfvars
            elif command -v nano &> /dev/null; then
                nano terraform.tfvars
            elif command -v vi &> /dev/null; then
                vi terraform.tfvars
            else
                print_warning "Please edit terraform.tfvars manually with your OCI configuration"
            fi
            
            echo
            read -p "Press Enter after you've configured terraform.tfvars..."
        else
            print_error "terraform.tfvars.example not found!"
            exit 1
        fi
    fi
    
    # Check if essential files exist
    local required_files=("docker-compose-saas-minimal.yml" ".env.saas")
    for file in "${required_files[@]}"; do
        if [ ! -f "../$file" ]; then
            print_error "Required file $file not found in parent directory!"
            exit 1
        fi
    done
    
    print_success "Configuration setup completed"
}

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    terraform init
    print_success "Terraform initialized"
}

# Validate configuration
validate_config() {
    print_status "Validating Terraform configuration..."
    terraform validate
    print_success "Configuration is valid"
}

# Plan deployment
plan_deployment() {
    print_status "Creating deployment plan..."
    terraform plan -out=tfplan
    print_success "Deployment plan created"
    
    echo
    print_status "Deployment plan summary:"
    echo "This will create the following resources in Oracle Cloud:"
    echo "  - 1 Compartment for the SaaS platform"
    echo "  - 1 VCN with public subnet"
    echo "  - 1 VM.Standard.A1.Flex instance (4 OCPUs, 24GB RAM)"
    echo "  - 1 Block storage volume (50GB)"
    echo "  - Security lists and routing tables"
    echo "  - Internet gateway for public access"
    echo
}

# Deploy infrastructure
deploy() {
    print_status "Deploying infrastructure to Oracle Cloud..."
    terraform apply tfplan
    
    if [ $? -eq 0 ]; then
        print_success "Deployment completed successfully!"
        
        # Get outputs
        print_status "Getting deployment information..."
        PUBLIC_IP=$(terraform output -raw instance_public_ip 2>/dev/null || echo "Not available")
        
        echo
        print_success "=== DEPLOYMENT COMPLETE ==="
        echo -e "${GREEN}Public IP:${NC} $PUBLIC_IP"
        echo
        print_status "Your SaaS monitoring platform is being set up automatically."
        print_status "It may take 5-10 minutes for all services to be fully operational."
        echo
        echo -e "${BLUE}Access URLs (replace with your actual IP):${NC}"
        echo "  • Grafana:      http://$PUBLIC_IP:3000"
        echo "  • Prometheus:   http://$PUBLIC_IP:9090"
        echo "  • Alertmanager: http://$PUBLIC_IP:9093"
        echo
        echo -e "${BLUE}SSH Access:${NC}"
        echo "  ssh opc@$PUBLIC_IP"
        echo
        echo -e "${BLUE}Useful commands on the server:${NC}"
        echo "  • Check status: docker-compose -f /opt/saas-platform/docker-compose.yml ps"
        echo "  • View logs:    docker-compose -f /opt/saas-platform/docker-compose.yml logs"
        echo "  • Restart:      docker-compose -f /opt/saas-platform/docker-compose.yml restart"
        echo
    else
        print_error "Deployment failed!"
        exit 1
    fi
}

# Main menu
show_menu() {
    echo
    echo "=== SaaS Monitoring Platform - Oracle Cloud Deployment ==="
    echo "1) Full deployment (init + validate + plan + deploy)"
    echo "2) Initialize Terraform only"
    echo "3) Validate configuration"
    echo "4) Create deployment plan"
    echo "5) Deploy (apply existing plan)"
    echo "6) Show current status"
    echo "7) Destroy infrastructure"
    echo "8) Exit"
    echo
}

# Show current status
show_status() {
    print_status "Current deployment status:"
    
    if [ -f "terraform.tfstate" ]; then
        terraform show -no-color | head -20
        echo
        PUBLIC_IP=$(terraform output -raw instance_public_ip 2>/dev/null || echo "Not deployed")
        echo -e "${BLUE}Public IP:${NC} $PUBLIC_IP"
    else
        print_warning "No deployment found (terraform.tfstate not present)"
    fi
}

# Destroy infrastructure
destroy_infrastructure() {
    print_warning "This will DESTROY all resources created by this deployment!"
    print_warning "This action cannot be undone!"
    echo
    read -p "Type 'yes' to confirm destruction: " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_status "Destroying infrastructure..."
        terraform destroy -auto-approve
        print_success "Infrastructure destroyed"
    else
        print_status "Destruction cancelled"
    fi
}

# Main script logic
main() {
    # Change to terraform directory
    cd "$(dirname "$0")"
    
    print_status "SaaS Monitoring Platform - Oracle Cloud Deployment"
    print_status "=================================================="
    
    check_prerequisites
    
    if [ "$1" = "--auto" ]; then
        # Automated deployment
        setup_config
        init_terraform
        validate_config
        plan_deployment
        
        echo
        read -p "Proceed with deployment? (y/N): " proceed
        if [[ $proceed =~ ^[Yy]$ ]]; then
            deploy
        else
            print_status "Deployment cancelled"
        fi
    else
        # Interactive menu
        while true; do
            show_menu
            read -p "Choose an option (1-8): " choice
            
            case $choice in
                1)
                    setup_config
                    init_terraform
                    validate_config
                    plan_deployment
                    echo
                    read -p "Proceed with deployment? (y/N): " proceed
                    if [[ $proceed =~ ^[Yy]$ ]]; then
                        deploy
                    fi
                    ;;
                2)
                    init_terraform
                    ;;
                3)
                    validate_config
                    ;;
                4)
                    plan_deployment
                    ;;
                5)
                    if [ -f "tfplan" ]; then
                        deploy
                    else
                        print_error "No deployment plan found. Run option 4 first."
                    fi
                    ;;
                6)
                    show_status
                    ;;
                7)
                    destroy_infrastructure
                    ;;
                8)
                    print_status "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option"
                    ;;
            esac
        done
    fi
}

# Run main function
main "$@"