variable "compartment_id" {
  description = "OCID of the compartment"
  type        = string
}

variable "vcn_name" {
  description = "Name of the VCN"
  type        = string
}

variable "vcn_dns_label" {
  description = "DNS Label of the VCN"
  type        = string
}

variable "vcn_cidr" {
  description = "CIDR block for VCN"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet"
  type        = string
  default     = "10.0.2.0/24"
}