# Oracle Cloud Infrastructure Configuration
# =====================================
# 
# To obtain these values, follow these steps:
# 1. Log into your Oracle Cloud Console
# 2. Go to Identity & Security -> Users -> Your Profile
# 3. Note your User OCID
# 4. Go to Tenancy Details to get Tenancy OCID
# 5. Create API Key pair and note the fingerprint
# 6. Create or use existing compartment OCID

# Authentication Variables
# -----------------------
user_ocid         = "ocid1.user.oc1..aaaaaaaam5uanx5neoueaqab7pnqp7qu6lrdt6l4atyclnaxoild6kfq2qpq" # Your user OCID
tenancy_ocid      = "ocid1.tenancy.oc1..aaaaaaaaimgn6bsdh4ivbsnxyvaclsfemgnjxw2342zdm55cy37rblglvjoa" # Your tenancy OCID  
fingerprint       = "1c:7d:cb:a9:20:0f:4e:1d:ca:36:bf:c8:4c:ad:44:9a" # API key fingerprint
private_key_path  = "/home/rafaelcl/.oci/terraform_key.pem" # Path to your private API key

# Regional Configuration
# ---------------------
region            = "eu-madrid-1" # Choose your preferred region
compartment_ocid  = "ocid1.tenancy.oc1..aaaaaaaaimgn6bsdh4ivbsnxyvaclsfemgnjxw2342zdm55cy37rblglvjoa" # Target compartment (using root)

# SSH Access Configuration
# -----------------------
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCl+hGhQxsCMcuMh7wMvMkAL9DHL12N7DtqYH+MYViO7uBuk83xEC0TxiK8W2kO74uB8UK7aK3wnR/9v0GIQhxgqOzy9PzwDATY7x67gPtezAvDoR/dDwwV0ix0oo1O9qRpGr/0sskarbU2/UWTloptR2MgTuWHaSMTmv54nCcLWE80xqJNXmSzUcTXR/Mm/4S5/kDr06K+Mt6y6+yGkV1OFxmNVhPs7+OLKLh2L61aXdTSCqCWaq8vYzRIMyyhgQolHqtJ+xeWjfltB6RvnwRCsAS25qvE+U9yhvtgg5K+DC+k4DUy4azUy4b49GDoH+TbMLrteGSbioeabUflWrF17WAi+lmo7NQvUdPSTGcr5mTVGN7CDkXFbRAZB1VU52s0UoQw/WJTZZlaXkOhTqPd2LPpC5eOtO2PcsME9N+UROPF/3Jha0a31eK3C22wVHa9MoW4hmhYoTtod3vJHWMmlvBuolYVLn8sqPAE2nRrdXENYM1uqXctcg4M7JqZXMB/ndNx9xVJpukMayyhLL4M9scPOk1z+cE+hLU54MHgpYUdVCzaazahIZI8SJRC8FcwVvGFRTXclDwfKCH26IGC67IuSGp1pCySHL8jJ3AbGUhGZNcR694mZIIWGftC4JT12CeAdNiUq88Nv/9PIZy6EAS8VThCmvn+/pGxDi1HmQ== oracle-cloud-vm"

# Project Configuration
# --------------------
project_name = "saas-monitoring"

# Instance Configuration (Paid Tier with Credits)
# ---------------------------------------------
# Using €250 credits with guaranteed capacity
# VM.Standard.E2.1 (Intel) - better availability than A1.Flex
instance_ocpus     = 1    # 1 OCPU for VM.Standard.E2.1
instance_memory_gb = 8    # 8GB RAM for VM.Standard.E2.1

# Oracle Linux 8 for ARM (Ampere A1) - Update this OCID for your region
# Get latest image OCID with: oci compute image list --compartment-id <tenancy-ocid> --operating-system "Oracle Linux" --shape "VM.Standard.A1.Flex"
instance_image_ocid = "ocid1.image.oc1.eu-madrid-1.aaaaaaaa6nmyu2iwgth5hbjjoc2bkig7qidc456gam5hf5bcqloxp5orq6pq" # Oracle Linux 8 ARM64

# =====================================
# How to obtain required OCIDs:
# =====================================

# 1. TENANCY OCID:
#    - Oracle Cloud Console -> Administration -> Tenancy Details
#    - Copy the OCID value

# 2. USER OCID:
#    - Oracle Cloud Console -> Identity & Security -> Users
#    - Click your username -> Copy User OCID

# 3. COMPARTMENT OCID:
#    - Oracle Cloud Console -> Identity & Security -> Compartments
#    - Select compartment -> Copy OCID
#    - Or use tenancy OCID as compartment for root compartment

# 4. API KEY SETUP:
#    - Generate key pair: openssl genrsa -out ~/.oci/oci_api_key.pem 2048
#    - Public key: openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
#    - Add public key to OCI Console -> User Profile -> API Keys
#    - Copy the fingerprint shown after adding the key

# 5. SSH KEY PAIR:
#    - Generate: ssh-keygen -t rsa -b 4096 -f ~/.ssh/oci_key
#    - Use public key content (~/.ssh/oci_key.pub) for ssh_public_key variable

# 6. REGION SELECTION:
#    - Choose region closest to your users
#    - Popular regions: us-ashburn-1, us-phoenix-1, eu-frankfurt-1, ap-tokyo-1

# 7. IMAGE OCID (for ARM/Ampere):
#    - Use OCI CLI: oci compute image list --compartment-id <tenancy-ocid> --operating-system "Oracle Linux" --shape "VM.Standard.A1.Flex"
#    - Or Oracle Cloud Console -> Compute -> Custom Images -> Oracle Images
#    - Filter by: Oracle Linux 8, ARM64, Latest

# =====================================
# Deployment Commands:
# =====================================
# 1. Copy this file: cp terraform.tfvars.example terraform.tfvars
# 2. Edit terraform.tfvars with your actual values
# 3. Initialize: terraform init
# 4. Plan: terraform plan
# 5. Deploy: terraform apply