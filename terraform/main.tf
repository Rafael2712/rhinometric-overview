terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Security Group para Rhinometric Test Server
resource "aws_security_group" "rhinometric_test" {
  name        = "rhinometric-test-server-sg"
  description = "Security group for Rhinometric v2.5.0 test server"

  # SSH
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Grafana (para pruebas directas)
  ingress {
    description = "Grafana Direct Access"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Console Frontend (para pruebas directas)
  ingress {
    description = "Console Frontend Direct Access"
    from_port   = 3002
    to_port     = 3002
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus (para pruebas)
  ingress {
    description = "Prometheus"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Jaeger UI (para pruebas)
  ingress {
    description = "Jaeger UI"
    from_port   = 16686
    to_port     = 16686
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress - Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "rhinometric-test-server-sg"
    Project     = "Rhinometric"
    Environment = "Test"
    Version     = "v2.5.0"
  }
}

# Spot Instance Request para EC2 t3.xlarge
resource "aws_spot_instance_request" "rhinometric_test" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.rhinometric_test.id]
  availability_zone      = "${var.aws_region}b"  # Forzar zona específica
  
  # Spot configuration
  spot_type            = "persistent"
  wait_for_fulfillment = true
  spot_price           = var.spot_max_price
  
  # User data para instalar Docker automáticamente
  user_data = file("${path.module}/user-data.sh")

  # Root volume
  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name        = "rhinometric-test-server"
    Project     = "Rhinometric"
    Environment = "Test"
    Version     = "v2.5.0"
    Purpose     = "Core Stack Testing"
  }
}

# EBS Volume para data persistence
resource "aws_ebs_volume" "rhinometric_data" {
  availability_zone = "${var.aws_region}b"  # Misma zona que la instancia
  size              = 150
  type              = "gp3"
  iops              = 3000
  throughput        = 125

  tags = {
    Name        = "rhinometric-test-data"
    Project     = "Rhinometric"
    Environment = "Test"
  }
}

# Elastic IP para mantener IP fija
resource "aws_eip" "rhinometric_test" {
  domain = "vpc"

  tags = {
    Name        = "rhinometric-test-server-eip"
    Project     = "Rhinometric"
    Environment = "Test"
  }
}

# Asociar EIP a la instancia Spot
resource "aws_eip_association" "rhinometric_test" {
  instance_id   = aws_spot_instance_request.rhinometric_test.spot_instance_id
  allocation_id = aws_eip.rhinometric_test.id

  depends_on = [aws_spot_instance_request.rhinometric_test]
}

# Attach EBS volume a la instancia
resource "aws_volume_attachment" "rhinometric_data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.rhinometric_data.id
  instance_id = aws_spot_instance_request.rhinometric_test.spot_instance_id

  depends_on = [aws_spot_instance_request.rhinometric_test]
}
