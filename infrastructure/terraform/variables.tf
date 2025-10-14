# Core variables for Oracle Cloud
variable "tenancy_ocid" {
  description = "OCID of your Oracle Cloud tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID of the Oracle Cloud user"
  type        = string
}

variable "private_key_path" {
  description = "Path to your Oracle Cloud API private key file"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of your Oracle Cloud API key"
  type        = string
}

variable "region" {
  description = "Oracle Cloud region"
  type        = string
  default     = "eu-madrid-1"
}

# SSH Configuration
variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for the SaaS platform"
  type        = string
  default     = "monitor.rhinometric.com"
}

# Environment Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Notification Configuration
variable "notification_email" {
  description = "Email for notifications and alerts"
  type        = string
  default     = "admin@rhinometric.com"
}