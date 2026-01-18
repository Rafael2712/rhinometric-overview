#!/bin/bash
# Rhinometric Test Server - Quick Deploy Script

set -e

echo "🚀 Rhinometric v2.5.0 Test Server - Quick Deploy"
echo "================================================"

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not installed. Please install from: https://www.terraform.io/downloads"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
fi

echo "✅ Prerequisites met"
echo ""

# Navigate to terraform directory
cd "$(dirname "$0")/terraform"

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

# Validate configuration
echo "🔍 Validating Terraform configuration..."
terraform validate

# Plan deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
echo "⚠️  This will create AWS resources (estimated cost: ~$35-45/month)"
read -p "Do you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Apply deployment
echo "🏗️  Deploying infrastructure..."
terraform apply tfplan

# Get outputs
echo ""
echo "✅ Deployment complete!"
echo "================================================"
terraform output -json > ../rhinometric-test-server-info.json
terraform output

echo ""
echo "📝 Connection info saved to: rhinometric-test-server-info.json"
echo ""
echo "Next steps:"
echo "1. Wait 2-3 minutes for user-data script to complete"
echo "2. SSH into server: terraform output -raw ssh_command"
echo "3. Transfer project files: rsync or scp"
echo "4. Run deployment: docker-compose -f docker-compose-v2.5.0-core.yml up -d"
