variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.xlarge"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI ID for us-east-1"
  type        = string
  # Ubuntu 22.04 LTS (HVM), SSD Volume Type en us-east-1
  # Actualizar si es necesario desde: https://cloud-images.ubuntu.com/locator/ec2/
  default     = "ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS us-east-1
}

variable "key_pair_name" {
  description = "Name of existing EC2 Key Pair for SSH access"
  type        = string
  default     = "rhinometric-test-key"  # Key pair para servidor de pruebas
}

variable "spot_max_price" {
  description = "Maximum price for spot instance (empty = on-demand price)"
  type        = string
  default     = "0.08"  # ~50% descuento vs on-demand ($0.1664/hr), margen de seguridad
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "Rhinometric"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "Test"
}
