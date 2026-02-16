# ============================================================================
# Rhinometric Terraform - Multi-Cloud Infrastructure
# ============================================================================

This directory contains Infrastructure as Code (IaC) configurations for deploying Rhinometric on multiple cloud providers.

## 📁 Directory Structure

```
terraform/
├── oracle-cloud/       ✅ Oracle Cloud Infrastructure (OCI) - COMPLETE
│   ├── compute.tf           # VM instances
│   ├── network.tf           # VCN, subnets, security lists
│   ├── provider.tf          # OCI provider configuration
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Output values
│   ├── terraform.tfvars.example  # Example configuration
│   ├── user-data.sh         # Instance initialization
│   └── README.md            # Full Oracle deployment guide
│
├── aws/                ⏳ AWS deployment (PLANNED)
│   └── README.md            # Coming soon
│
├── azure/              ⏳ Azure deployment (PLANNED)
│   └── README.md            # Coming soon
│
└── gcp/                ⏳ Google Cloud deployment (PLANNED)
    └── README.md            # Coming soon
```

## 🚀 Quick Start

### Oracle Cloud (Production Ready)

```bash
cd oracle-cloud/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OCI credentials
terraform init
terraform plan
terraform apply
```

**Full documentation**: See `oracle-cloud/README.md`

### Other Cloud Providers

AWS, Azure, and GCP configurations are planned for future releases. Contributions welcome!

## 🔑 Prerequisites

- **Terraform**: v1.12.0+ ([install](https://www.terraform.io/downloads))
- **Cloud Provider Account**: OCI Free Tier is sufficient for testing
- **SSH Key**: For VM access (`ssh-keygen -t rsa -b 4096`)
- **API Credentials**: Provider-specific (see individual READMEs)

## 📋 What Gets Deployed

### Oracle Cloud Configuration

- **Compute**: 1x E4.Flex instance (4 OCPU, 24GB RAM)
- **Network**: VCN with public subnet
- **Storage**: 100GB boot volume
- **Security**: Security list with ports 22, 80, 443, 3000, 5000, 8090-8092, 9090
- **Auto-provisioning**: Docker + full Rhinometric stack via user-data script

**Cost**: Free (within OCI Free Tier limits)

### Outputs After Deployment

```hcl
instance_public_ip    = "XXX.XXX.XXX.XXX"
grafana_url          = "http://XXX.XXX.XXX.XXX:3000"
license_server_url   = "http://XXX.XXX.XXX.XXX:5000"
ssh_command          = "ssh ubuntu@XXX.XXX.XXX.XXX -i ~/.ssh/oci_rsa"
```

## 🛠️ Common Commands

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply configuration
terraform apply

# View outputs
terraform output

# Destroy infrastructure
terraform destroy

# Validate configuration
terraform validate

# Format code
terraform fmt
```

## 🔒 Security Best Practices

1. **Never commit** `terraform.tfvars` with real credentials
2. Use **environment variables** for sensitive values:
   ```bash
   export TF_VAR_tenancy_ocid="ocid1.tenancy.oc1...."
   export TF_VAR_user_ocid="ocid1.user.oc1...."
   ```
3. Store **private keys** securely (`~/.ssh/` with `chmod 600`)
4. Enable **MFA** on cloud provider accounts
5. Use **remote state** for team collaboration:
   ```hcl
   terraform {
     backend "s3" {  # or OCI Object Storage
       bucket = "rhinometric-tfstate"
       key    = "production/terraform.tfstate"
     }
   }
   ```

## 📊 Cost Estimates

### Oracle Cloud Free Tier (Forever Free)

| Resource | Quantity | Monthly Cost |
|----------|----------|--------------|
| E4.Flex Instance | 4 OCPU, 24GB RAM | **$0.00** |
| Boot Volume | 100GB | **$0.00** |
| Network Egress | 10TB/month | **$0.00** |
| **Total** | | **$0.00** |

### Oracle Cloud Paid (Typical Production)

| Resource | Quantity | Monthly Cost |
|----------|----------|--------------|
| E4.Flex Instance | 8 OCPU, 48GB RAM | ~$350 |
| Boot Volume | 200GB | ~$5 |
| Load Balancer | 1 flexible | ~$10 |
| **Total** | | **~$365** |

*Prices as of 2025. Check [Oracle Cloud pricing](https://www.oracle.com/cloud/price-list/) for current rates.*

## 🌍 Multi-Cloud Strategy

**Why Oracle Cloud first?**
- ✅ **Generous Free Tier**: 4 OCPU ARM instances forever free
- ✅ **Performance**: Better price/performance than AWS t3/t4
- ✅ **Reliability**: 99.9% SLA even on Free Tier
- ✅ **Global**: 44 regions worldwide

**Coming soon**:
- **AWS**: ECS Fargate + RDS + CloudWatch
- **Azure**: AKS + PostgreSQL Flexible + Monitor
- **GCP**: GKE + Cloud SQL + Operations Suite

## 🤝 Contributing

Want to add support for AWS, Azure, or GCP? PRs welcome!

1. Fork the repository
2. Create your provider directory (e.g., `terraform/aws/`)
3. Follow the Oracle Cloud structure
4. Submit a pull request

## 📚 Additional Resources

- [Terraform Registry - OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [Oracle Cloud Free Tier Guide](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)
- [Rhinometric Documentation](../../rhinometric-trial-v2.1.0-universal/README.md)

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Rafael2712/mi-proyecto/issues)
- **Email**: rafael.canelon@rhinometric.com
- **Documentation**: See individual provider READMEs

---

**Last Updated**: 2025-01-XX  
**Terraform Version**: 1.12.0+  
**Rhinometric Version**: v2.1.0
