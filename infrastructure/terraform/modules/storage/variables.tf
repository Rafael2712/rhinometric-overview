variable "compartment_id" {
  description = "OCID of the compartment"
  type        = string
}

variable "availability_domain" {
  description = "Availability domain for the volumes"
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

variable "prometheus_volume_size_gb" {
  description = "Size of Prometheus volumes in GB"
  type        = number
  default     = 50
}

variable "grafana_volume_size_gb" {
  description = "Size of Grafana volumes in GB"
  type        = number
  default     = 20
}

variable "loki_volume_size_gb" {
  description = "Size of Loki volumes in GB"
  type        = number
  default     = 100
}

variable "prometheus_instance_ids" {
  description = "List of Prometheus instance OCIDs"
  type        = list(string)
}

variable "grafana_instance_ids" {
  description = "List of Grafana instance OCIDs"
  type        = list(string)
}

variable "loki_instance_ids" {
  description = "List of Loki instance OCIDs"
  type        = list(string)
}