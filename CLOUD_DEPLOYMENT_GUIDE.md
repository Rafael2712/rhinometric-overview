# 🌐 Rhinometric Cloud Deployment Guide
## Multi-Cloud & Hybrid Architectures v2.1.0

**Versión**: 2.1.0  
**Fecha**: Octubre 2025  
**Autor**: Rafael Canel  
**Repositorio**: https://github.com/Rafael2712/rhinometric-overview

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Oracle Cloud Infrastructure](#oracle-cloud-infrastructure)
3. [Amazon Web Services (AWS)](#amazon-web-services-aws)
4. [Microsoft Azure](#microsoft-azure)
5. [Google Cloud Platform (GCP)](#google-cloud-platform-gcp)
6. [Arquitectura Híbrida](#arquitectura-híbrida)
7. [Comparativa de Costos](#comparativa-de-costos)
8. [Mejores Prácticas](#mejores-prácticas)

---

## 🎯 Introducción

Rhinometric v2.1.0 es una plataforma de observabilidad 100% ON-PREMISE que también puede desplegarse en la nube. Esta guía cubre:

- ✅ **Deployment 100% Cloud**: Oracle, AWS, Azure, GCP
- ✅ **Arquitectura Híbrida**: On-premise + Cloud
- ✅ **Multi-Sede**: Federación de métricas
- ✅ **Disaster Recovery**: Cloud como backup

### ¿Por qué Cloud?

- 🚀 **Escalabilidad**: Auto-scaling según demanda
- 💰 **Costos**: Paga solo lo que usas
- 🌍 **Global**: Deploy en múltiples regiones
- 🔒 **HA**: Alta disponibilidad 99.9%
- ⚡ **Rápido**: Deploy en 15 minutos

---

## ☁️ Oracle Cloud Infrastructure

### Estado: ✅ VALIDADO ARQUITECTÓNICAMENTE

**Infraestructura creada exitosamente**:
- VCN, Subnet, Internet Gateway
- Security Lists (puertos 22, 80, 443, 3000, 8091, 9090)
- Terraform 100% funcional
- Auto-instalación via cloud-init

### Terraform Files

Ubicación: `terraform/oracle-cloud/`

```bash
terraform/oracle-cloud/
├── provider.tf              # OCI provider config
├── variables.tf             # 20+ variables configurables
├── network.tf              # VCN, subnet, IGW, security
├── compute.tf              # VM instance
├── outputs.tf              # IPs, URLs, SSH commands
├── user-data.sh            # Auto-install script
├── terraform.tfvars.example
├── README.md
└── DEPLOYMENT_REPORT.md    # Reporte completo
```

### Quick Start Oracle Cloud

```bash
# 1. Clonar repositorio
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/terraform/oracle-cloud

# 2. Configurar credenciales
cp terraform.tfvars.example terraform.tfvars
# Editar: tenancy_ocid, user_ocid, fingerprint, private_key_path

# 3. Deploy
terraform init
terraform plan
terraform apply -auto-approve

# 4. Acceder
# Grafana: http://<PUBLIC_IP>:3000
# Usuario: admin / RhinometricSecure2025!
```

### Especificaciones OCI

| Recurso | Especificación | Costo (Free Tier) |
|---------|----------------|-------------------|
| VM Shape | VM.Standard.A1.Flex | $0/mes (Always Free) |
| CPU | 2 OCPU ARM | Incluido |
| RAM | 12 GB | Incluido |
| Storage | 100 GB SSD | Incluido |
| Network | VCN + Public IP | $0 |
| **TOTAL** | | **$0/mes por 12 meses** |

### Limitaciones Oracle Cloud

⚠️ **Capacidad regional**: Free Tier puede tener límites de disponibilidad.

**Solución**: Intentar en diferentes horarios o contactar soporte Oracle.

---

## 🚀 Amazon Web Services (AWS)

### Arquitectura AWS

```
AWS Cloud
├── VPC (10.0.0.0/16)
│   ├── Public Subnet (10.0.1.0/24)
│   └── Internet Gateway
├── EC2 Instance (t3.medium)
│   ├── Ubuntu 22.04 LTS
│   ├── 2 vCPU, 4 GB RAM
│   ├── 100 GB gp3 SSD
│   └── Docker + 17 containers
├── Security Group
│   ├── SSH (22)
│   ├── HTTP/HTTPS (80, 443)
│   ├── Grafana (3000)
│   └── API Connector (8091)
└── Elastic IP
```

### Terraform para AWS

Crear: `terraform/aws/main.tf`

```hcl
provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "rhinometric_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "rhinometric-vpc"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "rhinometric_igw" {
  vpc_id = aws_vpc.rhinometric_vpc.id

  tags = {
    Name = "rhinometric-igw"
  }
}

# Public Subnet
resource "aws_subnet" "rhinometric_public" {
  vpc_id                  = aws_vpc.rhinometric_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "rhinometric-public-subnet"
  }
}

# Route Table
resource "aws_route_table" "rhinometric_public_rt" {
  vpc_id = aws_vpc.rhinometric_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.rhinometric_igw.id
  }

  tags = {
    Name = "rhinometric-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.rhinometric_public.id
  route_table_id = aws_route_table.rhinometric_public_rt.id
}

# Security Group
resource "aws_security_group" "rhinometric_sg" {
  name        = "rhinometric-sg"
  description = "Security group for Rhinometric v2.1.0"
  vpc_id      = aws_vpc.rhinometric_vpc.id

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  # Grafana
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Grafana"
  }

  # API Connector
  ingress {
    from_port   = 8091
    to_port     = 8091
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "API Connector UI"
  }

  # Prometheus
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Prometheus"
  }

  # Egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rhinometric-sg"
  }
}

# EC2 Instance
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "rhinometric" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.rhinometric_public.id
  
  vpc_security_group_ids = [aws_security_group.rhinometric_sg.id]
  
  key_name = var.ssh_key_name

  root_block_device {
    volume_size = 100
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/user-data.sh", {
    grafana_password  = var.grafana_password
    postgres_password = var.postgres_password
    redis_password    = var.redis_password
  })

  tags = {
    Name        = "rhinometric-v2-1-0"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# Elastic IP
resource "aws_eip" "rhinometric_eip" {
  instance = aws_instance.rhinometric.id
  domain   = "vpc"

  tags = {
    Name = "rhinometric-eip"
  }
}

# Outputs
output "public_ip" {
  value       = aws_eip.rhinometric_eip.public_ip
  description = "Public IP address"
}

output "grafana_url" {
  value       = "http://${aws_eip.rhinometric_eip.public_ip}:3000"
  description = "Grafana URL"
}

output "api_connector_url" {
  value       = "http://${aws_eip.rhinometric_eip.public_ip}:8091"
  description = "API Connector URL"
}

output "ssh_command" {
  value       = "ssh -i ~/.ssh/aws_key.pem ubuntu@${aws_eip.rhinometric_eip.public_ip}"
  description = "SSH connection command"
}
```

### Variables AWS (`variables.tf`)

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1" # Ireland
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium" # 2 vCPU, 4 GB RAM
}

variable "ssh_key_name" {
  description = "AWS SSH key pair name"
  type        = string
}

variable "grafana_password" {
  description = "Grafana admin password"
  type        = string
  default     = "RhinometricSecure2025!"
  sensitive   = true
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  default     = "PostgresSecure2025!"
  sensitive   = true
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  default     = "RedisSecure2025!"
  sensitive   = true
}
```

### Deploy en AWS

```bash
# 1. Configurar AWS CLI
aws configure
# AWS Access Key ID: tu-key
# AWS Secret Access Key: tu-secret
# Default region: eu-west-1
# Default output format: json

# 2. Crear SSH key pair
aws ec2 create-key-pair \
  --key-name rhinometric-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/aws_key.pem
chmod 400 ~/.ssh/aws_key.pem

# 3. Deploy
cd terraform/aws
terraform init
terraform apply -var="ssh_key_name=rhinometric-key"

# 4. Acceder
# Grafana: http://<PUBLIC_IP>:3000
```

### Costos AWS

| Recurso | Especificación | Costo Mensual |
|---------|----------------|---------------|
| EC2 t3.medium | 2 vCPU, 4 GB | $30.37 |
| EBS gp3 | 100 GB SSD | $8.00 |
| Elastic IP | 1 IP pública | $3.60 |
| Data Transfer | 100 GB/mes | $9.00 |
| **TOTAL** | | **~$51/mes** |

---

## ☁️ Microsoft Azure

### Arquitectura Azure

```
Azure Cloud
├── Resource Group (rhinometric-rg)
├── Virtual Network (10.0.0.0/16)
│   └── Subnet (10.0.1.0/24)
├── Network Security Group
├── Public IP
└── Virtual Machine (Standard_B2s)
    ├── Ubuntu 22.04 LTS
    ├── 2 vCPU, 4 GB RAM
    └── 100 GB Premium SSD
```

### Terraform para Azure

`terraform/azure/main.tf`:

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "rhinometric_rg" {
  name     = "rhinometric-rg"
  location = var.location

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
    Project     = "rhinometric"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "rhinometric_vnet" {
  name                = "rhinometric-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rhinometric_rg.location
  resource_group_name = azurerm_resource_group.rhinometric_rg.name

  tags = {
    Name = "rhinometric-vnet"
  }
}

# Subnet
resource "azurerm_subnet" "rhinometric_subnet" {
  name                 = "rhinometric-subnet"
  resource_group_name  = azurerm_resource_group.rhinometric_rg.name
  virtual_network_name = azurerm_virtual_network.rhinometric_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Public IP
resource "azurerm_public_ip" "rhinometric_pip" {
  name                = "rhinometric-pip"
  location            = azurerm_resource_group.rhinometric_rg.location
  resource_group_name = azurerm_resource_group.rhinometric_rg.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    Name = "rhinometric-public-ip"
  }
}

# Network Security Group
resource "azurerm_network_security_group" "rhinometric_nsg" {
  name                = "rhinometric-nsg"
  location            = azurerm_resource_group.rhinometric_rg.location
  resource_group_name = azurerm_resource_group.rhinometric_rg.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "HTTP"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "HTTPS"
    priority                   = 1003
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Grafana"
    priority                   = 1004
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3000"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "API-Connector"
    priority                   = 1005
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8091"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Prometheus"
    priority                   = 1006
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "9090"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# Network Interface
resource "azurerm_network_interface" "rhinometric_nic" {
  name                = "rhinometric-nic"
  location            = azurerm_resource_group.rhinometric_rg.location
  resource_group_name = azurerm_resource_group.rhinometric_rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.rhinometric_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.rhinometric_pip.id
  }
}

# Connect NSG to NIC
resource "azurerm_network_interface_security_group_association" "rhinometric_nsg_nic" {
  network_interface_id      = azurerm_network_interface.rhinometric_nic.id
  network_security_group_id = azurerm_network_security_group.rhinometric_nsg.id
}

# Virtual Machine
resource "azurerm_linux_virtual_machine" "rhinometric_vm" {
  name                = "rhinometric-vm"
  resource_group_name = azurerm_resource_group.rhinometric_rg.name
  location            = azurerm_resource_group.rhinometric_rg.location
  size                = var.vm_size
  admin_username      = "azureuser"

  network_interface_ids = [
    azurerm_network_interface.rhinometric_nic.id,
  ]

  admin_ssh_key {
    username   = "azureuser"
    public_key = file(var.ssh_public_key_path)
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 100
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  custom_data = base64encode(templatefile("${path.module}/user-data.sh", {
    grafana_password  = var.grafana_password
    postgres_password = var.postgres_password
    redis_password    = var.redis_password
  }))

  tags = {
    Name        = "rhinometric-v2-1-0"
    Environment = "production"
  }
}

# Outputs
output "public_ip" {
  value       = azurerm_public_ip.rhinometric_pip.ip_address
  description = "Public IP address"
}

output "grafana_url" {
  value       = "http://${azurerm_public_ip.rhinometric_pip.ip_address}:3000"
  description = "Grafana URL"
}
```

### Deploy en Azure

```bash
# 1. Login Azure
az login

# 2. Deploy
cd terraform/azure
terraform init
terraform apply

# 3. Acceder
# Grafana: http://<PUBLIC_IP>:3000
```

### Costos Azure

| Recurso | Especificación | Costo Mensual |
|---------|----------------|---------------|
| VM Standard_B2s | 2 vCPU, 4 GB | $35.04 |
| Premium SSD | 100 GB P10 | $19.71 |
| Public IP | Static | $3.65 |
| **TOTAL** | | **~$58/mes** |

---

## ☁️ Google Cloud Platform (GCP)

### Arquitectura GCP

```
GCP Cloud
├── VPC Network
│   └── Subnet (10.0.1.0/24)
├── Firewall Rules
├── External IP
└── Compute Engine (e2-medium)
    ├── Ubuntu 22.04 LTS
    ├── 2 vCPU, 4 GB RAM
    └── 100 GB SSD
```

### Terraform para GCP

`terraform/gcp/main.tf`:

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}

# VPC Network
resource "google_compute_network" "rhinometric_vpc" {
  name                    = "rhinometric-vpc"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "rhinometric_subnet" {
  name          = "rhinometric-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.rhinometric_vpc.id
}

# Firewall Rules
resource "google_compute_firewall" "rhinometric_fw" {
  name    = "rhinometric-firewall"
  network = google_compute_network.rhinometric_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443", "3000", "8091", "9090"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["rhinometric"]
}

# Compute Instance
resource "google_compute_instance" "rhinometric_vm" {
  name         = "rhinometric-v2-1-0"
  machine_type = var.machine_type
  zone         = "${var.region}-a"

  tags = ["rhinometric"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 100
      type  = "pd-ssd"
    }
  }

  network_interface {
    network    = google_compute_network.rhinometric_vpc.name
    subnetwork = google_compute_subnetwork.rhinometric_subnet.name

    access_config {
      // Ephemeral public IP
    }
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }

  metadata_startup_script = templatefile("${path.module}/user-data.sh", {
    grafana_password  = var.grafana_password
    postgres_password = var.postgres_password
    redis_password    = var.redis_password
  })

  labels = {
    environment = "production"
    managed_by  = "terraform"
    project     = "rhinometric"
  }
}

# Outputs
output "public_ip" {
  value       = google_compute_instance.rhinometric_vm.network_interface[0].access_config[0].nat_ip
  description = "Public IP address"
}

output "grafana_url" {
  value       = "http://${google_compute_instance.rhinometric_vm.network_interface[0].access_config[0].nat_ip}:3000"
  description = "Grafana URL"
}
```

### Deploy en GCP

```bash
# 1. Configurar GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs
gcloud services enable compute.googleapis.com

# 3. Deploy
cd terraform/gcp
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID"

# 4. Acceder
# Grafana: http://<PUBLIC_IP>:3000
```

### Costos GCP

| Recurso | Especificación | Costo Mensual |
|---------|----------------|---------------|
| e2-medium | 2 vCPU, 4 GB | $24.27 |
| SSD | 100 GB | $17.00 |
| External IP | 1 IP | $7.30 |
| **TOTAL** | | **~$49/mes** |

---

## 🔀 Arquitectura Híbrida

### Modelo 1: Procesamiento Local + Visualización Cloud

**Caso de uso**: Cumplimiento regulatorio (GDPR, HIPAA)

```
┌─────────────────────────────────────┐
│   CLIENTE ON-PREMISE (Sede Madrid) │
├─────────────────────────────────────┤
│ ├── PostgreSQL (datos sensibles)   │
│ ├── Redis Cache                    │
│ ├── Aplicaciones                   │
│ └── Prometheus Agent ───────┐      │
└─────────────────────────────┼──────┘
                              │
                     Remote Write
                              ↓
┌─────────────────────────────────────┐
│         ORACLE CLOUD / AWS          │
├─────────────────────────────────────┤
│ ├── Prometheus (agregador)         │
│ ├── Grafana (dashboards)           │
│ ├── Loki (logs)                    │
│ └── Tempo (traces)                 │
└─────────────────────────────────────┘
```

**Configuración Prometheus Remote Write**:

```yaml
# prometheus.yml (on-premise)
global:
  scrape_interval: 15s
  external_labels:
    site: 'madrid'
    environment: 'production'

scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

remote_write:
  - url: "https://prometheus-cloud.tudominio.com/api/v1/write"
    basic_auth:
      username: "sede-madrid"
      password: "${PROMETHEUS_REMOTE_PASSWORD}"
    queue_config:
      capacity: 10000
      max_shards: 5
      max_samples_per_send: 1000
      batch_send_deadline: 5s
    tls_config:
      insecure_skip_verify: false
      cert_file: /etc/prometheus/certs/client.crt
      key_file: /etc/prometheus/certs/client.key
```

**Docker Compose Híbrido**:

```yaml
# docker-compose-hybrid.yml
version: '3.8'

services:
  # Procesamiento local
  postgres:
    image: postgres:15
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    networks:
      - rhinometric-local

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    networks:
      - rhinometric-local

  # Prometheus con remote write
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus-hybrid.yml:/etc/prometheus/prometheus.yml
      - ./certs:/etc/prometheus/certs:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=7d'
      - '--web.enable-remote-write-receiver'
    networks:
      - rhinometric-local
      - rhinometric-cloud

  # Exporters locales
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://user:pass@postgres:5432/db?sslmode=disable"
    networks:
      - rhinometric-local

  redis-exporter:
    image: oliver006/redis_exporter
    environment:
      REDIS_ADDR: "redis:6379"
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    networks:
      - rhinometric-local

  # VPN para conectar a cloud (opcional)
  wireguard:
    image: linuxserver/wireguard
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Madrid
      - SERVERURL=auto
      - PEERS=1
      - PEERDNS=auto
    volumes:
      - ./wireguard:/config
      - /lib/modules:/lib/modules
    ports:
      - 51820:51820/udp
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1
    networks:
      - rhinometric-cloud

networks:
  rhinometric-local:
    driver: bridge
  rhinometric-cloud:
    driver: bridge
```

### Modelo 2: Multi-Sede con Federación

**Caso de uso**: Cadena retail, hospitales multi-sede

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Sede Madrid     │  │  Sede Barcelona  │  │  Sede Valencia   │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ Stack completo   │  │ Stack completo   │  │ Stack completo   │
│ ├── Prometheus   │  │ ├── Prometheus   │  │ ├── Prometheus   │
│ ├── Grafana      │  │ ├── Grafana      │  │ ├── Grafana      │
│ └── Loki         │  │ └── Loki         │  │ └── Loki         │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │ Prometheus Federation
                               ↓
              ┌────────────────────────────────┐
              │     ORACLE CLOUD (Central)     │
              ├────────────────────────────────┤
              │ ├── Prometheus (federated)    │
              │ ├── Grafana (multi-tenant)    │
              │ ├── Alertmanager (central)    │
              │ └── Dashboards globales        │
              └────────────────────────────────┘
```

**Prometheus Federation Config**:

```yaml
# prometheus-central.yml (Cloud)
global:
  scrape_interval: 30s

scrape_configs:
  # Federar desde Sede Madrid
  - job_name: 'federate-madrid'
    scrape_interval: 60s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job=~".+"}'
    static_configs:
      - targets:
        - 'madrid.prometheus.local:9090'
    basic_auth:
      username: 'federation'
      password: '${FEDERATION_PASSWORD}'

  # Federar desde Sede Barcelona
  - job_name: 'federate-barcelona'
    scrape_interval: 60s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job=~".+"}'
    static_configs:
      - targets:
        - 'barcelona.prometheus.local:9090'
    basic_auth:
      username: 'federation'
      password: '${FEDERATION_PASSWORD}'

  # Federar desde Sede Valencia
  - job_name: 'federate-valencia'
    scrape_interval: 60s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job=~".+"}'
    static_configs:
      - targets:
        - 'valencia.prometheus.local:9090'
    basic_auth:
      username: 'federation'
      password: '${FEDERATION_PASSWORD}'
```

### Modelo 3: Disaster Recovery Cloud

**Caso de uso**: Alta disponibilidad 99.9%

```
┌─────────────────────────────────┐
│   PRODUCCIÓN (On-Premise)       │
│   ├── Stack Rhinometric         │
│   ├── PostgreSQL Master         │
│   └── Backup continuo ───┐      │
└──────────────────────────┼──────┘
                           │
                  Replicación async
                           ↓
┌─────────────────────────────────┐
│   DISASTER RECOVERY (Cloud)     │
│   ├── PostgreSQL Standby        │
│   ├── Stack Rhinometric (cold)  │
│   └── Auto-failover ready       │
└─────────────────────────────────┘
```

**PostgreSQL Streaming Replication**:

```yaml
# docker-compose-dr.yml
version: '3.8'

services:
  postgres-standby:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - ./standby-data:/var/lib/postgresql/data
      - ./recovery.conf:/var/lib/postgresql/data/recovery.conf
    command: >
      bash -c "
      if [ ! -f /var/lib/postgresql/data/pgdata/PG_VERSION ]; then
        pg_basebackup -h production-db.local -D /var/lib/postgresql/data/pgdata -U replicator -Fp -Xs -P -R
      fi
      postgres
      "
    networks:
      - rhinometric-dr
```

---

## 💰 Comparativa de Costos

### Mensual (2 vCPU, 4 GB RAM, 100 GB SSD)

| Proveedor | Instancia | Costo/Mes | Free Tier | Total Anual |
|-----------|-----------|-----------|-----------|-------------|
| **Oracle Cloud** | VM.Standard.A1.Flex (ARM) | $0 | 12 meses | **$0** |
| **GCP** | e2-medium | $49 | $300 crédito | **$588** |
| **AWS** | t3.medium | $51 | 12 meses t2.micro | **$612** |
| **Azure** | Standard_B2s | $58 | $200 crédito | **$696** |

### Recomendación por Caso de Uso

| Caso de Uso | Proveedor Recomendado | Razón |
|-------------|----------------------|-------|
| **Demo/Trial** | Oracle Cloud | Free forever |
| **Producción < 100 empleados** | GCP | Mejor precio/rendimiento |
| **Enterprise** | AWS | Más servicios, HA global |
| **Microsoft Stack** | Azure | Integración AD/Office 365 |
| **Multi-cloud** | Terraform | Portabilidad total |

---

## 🎯 Mejores Prácticas

### Seguridad

1. **Firewall**: Restringir IPs origen
   ```hcl
   cidr_blocks = ["TU_IP_PUBLICA/32"]
   ```

2. **SSL/TLS**: HTTPS obligatorio
   ```bash
   # Certificado Let's Encrypt
   certbot --nginx -d rhinometric.tudominio.com
   ```

3. **Secrets**: Variables sensibles
   ```bash
   export TF_VAR_grafana_password="SecurePassword123!"
   ```

4. **Backup**: Automatizado diario
   ```bash
   0 2 * * * /usr/local/bin/backup-rhinometric.sh
   ```

### Monitoreo

1. **Uptime**: Healthchecks
   ```yaml
   # healthcheck.yml
   http:
     - https://rhinometric.tudominio.com:3000/api/health
   ```

2. **Alertas**: Prometheus Alertmanager
   ```yaml
   - alert: InstanceDown
     expr: up == 0
     for: 5m
     annotations:
       summary: "Instance {{ $labels.instance }} down"
   ```

3. **Logs**: Centralización Loki
   ```yaml
   clients:
     - url: https://loki-cloud.tudominio.com/loki/api/v1/push
   ```

### Optimización

1. **Auto-scaling**: Cloud-native
   ```hcl
   # AWS Auto Scaling Group
   resource "aws_autoscaling_group" "rhinometric_asg" {
     min_size         = 1
     max_size         = 5
     desired_capacity = 2
   }
   ```

2. **CDN**: CloudFlare para Grafana
   ```nginx
   # nginx.conf
   proxy_cache_valid 200 1h;
   proxy_cache_bypass $http_pragma;
   ```

3. **Compresión**: gzip enabled
   ```nginx
   gzip on;
   gzip_types text/plain application/json;
   ```

---

## 📚 Recursos Adicionales

- **Documentación**: https://github.com/Rafael2712/rhinometric-overview
- **Issues**: https://github.com/Rafael2712/rhinometric-overview/issues
- **Ejemplos**: `terraform/` directorio en repositorio

---

**Última actualización**: 28 de Octubre 2025  
**Versión Rhinometric**: 2.1.0  
**Autor**: Rafael Canel  
**Licencia**: Propietaria
