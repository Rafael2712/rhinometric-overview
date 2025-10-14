variable "compartment_id" {
  description = "OCID of the compartment"
  type        = string
}

variable "vcn_id" {
  description = "OCID of the VCN"
  type        = string
}

variable "subnet_id" {
  description = "OCID of the subnet"
  type        = string
}

variable "availability_domains" {
  description = "List of availability domains"
  type        = list(object({
    name = string
  }))
}

variable "instance_shape" {
  description = "Shape of compute instances"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "instance_ocpus" {
  description = "Number of OCPUs for Flex shapes"
  type        = number
  default     = 2
}

variable "instance_memory_in_gbs" {
  description = "Amount of memory in GBs for Flex shapes"
  type        = number
  default     = 16
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "prometheus_node_count" {
  description = "Number of Prometheus nodes"
  type        = number
  default     = 2
}

variable "grafana_node_count" {
  description = "Number of Grafana nodes"
  type        = number
  default     = 2
}

variable "loki_node_count" {
  description = "Number of Loki nodes"
  type        = number
  default     = 2
}