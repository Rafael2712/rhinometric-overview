# Terraform Provider Configuration for Oracle Cloud Infrastructure (OCI)
# Rhinometric v2.1.0 Deployment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  # Credentials se leen de:
  # 1. Variables de entorno: TF_VAR_tenancy_ocid, TF_VAR_user_ocid, etc.
  # 2. O archivo ~/.oci/config (default profile)
  
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}
