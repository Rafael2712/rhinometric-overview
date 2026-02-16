variable "compartment_id" {
  description = "OCID of the compartment"
  type        = string
}

variable "subnet_id" {
  description = "OCID of the subnet"
  type        = string
}

variable "backend_sets" {
  description = "Configuration for backend sets"
  type = object({
    prometheus = list(object({
      ip   = string
      port = number
    }))
    grafana = list(object({
      ip   = string
      port = number
    }))
    loki = list(object({
      ip   = string
      port = number
    }))
  })
}