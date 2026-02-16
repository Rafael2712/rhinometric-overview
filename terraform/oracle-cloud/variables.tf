# Variables de configuración para Oracle Cloud
# Rhinometric v2.1.0 Deployment

# ========================================
# Oracle Cloud Credentials
# ========================================

variable "tenancy_ocid" {
  description = "OCID del tenancy de Oracle Cloud"
  type        = string
  # Obtener en: https://cloud.oracle.com/ → Profile → Tenancy
}

variable "user_ocid" {
  description = "OCID del usuario"
  type        = string
  # Obtener en: https://cloud.oracle.com/ → Profile → User Settings
}

variable "fingerprint" {
  description = "Fingerprint de la API key"
  type        = string
  # Generar con: openssl rsa -pubout -outform DER -in ~/.oci/oci_api_key.pem | openssl md5 -c
}

variable "private_key_path" {
  description = "Ruta a la private key (.pem) para autenticación API"
  type        = string
  default     = "~/.oci/oci_api_key.pem"
}

variable "region" {
  description = "Región de Oracle Cloud"
  type        = string
  default     = "us-ashburn-1"
  # Otras opciones: us-phoenix-1, eu-frankfurt-1, uk-london-1, ap-tokyo-1
}

# ========================================
# Compute Instance Configuration
# ========================================

variable "instance_shape" {
  description = "Shape de la instancia (tipo de VM)"
  type        = string
  default     = "VM.Standard.E4.Flex"
  # E4.Flex permite configurar CPU/RAM flexible
  # Otras opciones: VM.Standard2.1, VM.Standard.E3.Flex
}

variable "instance_ocpus" {
  description = "Número de OCPUs (Oracle CPUs)"
  type        = number
  default     = 4
  # Rhinometric necesita mínimo 4 vCPU, recomendado 4-8
}

variable "instance_memory_in_gbs" {
  description = "RAM en GB"
  type        = number
  default     = 16
  # Rhinometric necesita mínimo 8 GB, recomendado 16 GB
}

variable "instance_display_name" {
  description = "Nombre de la instancia"
  type        = string
  default     = "rhinometric-v2-1-0-trial"
}

variable "availability_domain" {
  description = "Availability Domain (AD-1, AD-2, AD-3)"
  type        = string
  default     = "AD-1"
}

# ========================================
# Network Configuration
# ========================================

variable "vcn_cidr_block" {
  description = "CIDR block para la VCN (Virtual Cloud Network)"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr_block" {
  description = "CIDR block para la subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "allowed_ssh_cidr" {
  description = "CIDR permitido para SSH (tu IP pública)"
  type        = string
  default     = "0.0.0.0/0"
  # IMPORTANTE: Cambiar a tu IP pública para seguridad
  # Ejemplo: "203.0.113.5/32"
}

variable "allowed_http_cidr" {
  description = "CIDR permitido para HTTP/HTTPS (Grafana)"
  type        = string
  default     = "0.0.0.0/0"
  # Para acceso público. Para restringir, usar tu IP
}

# ========================================
# Storage Configuration
# ========================================

variable "boot_volume_size_in_gbs" {
  description = "Tamaño del disco boot en GB"
  type        = number
  default     = 100
  # Rhinometric necesita mínimo 50 GB, recomendado 100-200 GB
}

# ========================================
# OS Image
# ========================================

variable "instance_image_ocid" {
  description = "OCID de la imagen del OS (Ubuntu 22.04)"
  type        = map(string)
  default     = {
    # Ubuntu 22.04 LTS (Canonical)
    us-ashburn-1   = "ocid1.image.oc1.iad.aaaaaaaaba4mrnsh6cobnmwvsxgvbwew5sdx3sswwzlbilx5v5oegxu5xeaq"
    us-phoenix-1   = "ocid1.image.oc1.phx.aaaaaaaaq7ovx4ebxjd3fxbr3wjbhf2jqzkjcpkxncmb4bqvx3vcvsgd2bxq"
    eu-frankfurt-1 = "ocid1.image.oc1.eu-frankfurt-1.aaaaaaaa7zrfurkjrvqwncvvl5qbocacngqb4krvwpq3j2ahjl6nxw45pxna"
    uk-london-1    = "ocid1.image.oc1.uk-london-1.aaaaaaaagz7z2txw4gsgqz3vvobv4tjq7pvx4bsyhh5tlvdnpbwvyebwq5pa"
  }
  # Si tu región no está listada, obtén el OCID en:
  # https://docs.oracle.com/en-us/iaas/images/ubuntu-2204/
}

# ========================================
# SSH Configuration
# ========================================

variable "ssh_public_key_path" {
  description = "Ruta a la SSH public key para acceder a la instancia"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

# ========================================
# Rhinometric Configuration
# ========================================

variable "grafana_admin_password" {
  description = "Password de admin de Grafana"
  type        = string
  default     = "RhinometricSecure2025!"
  sensitive   = true
}

variable "postgres_password" {
  description = "Password de PostgreSQL"
  type        = string
  default     = "PostgresSecure2025!"
  sensitive   = true
}

variable "redis_password" {
  description = "Password de Redis"
  type        = string
  default     = "RedisSecure2025!"
  sensitive   = true
}

# ========================================
# Tags
# ========================================

variable "tags" {
  description = "Tags para recursos de OCI"
  type        = map(string)
  default     = {
    Environment = "trial"
    Project     = "rhinometric"
    Version     = "2.1.0"
    ManagedBy   = "terraform"
  }
}
