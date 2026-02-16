# Virtual Cloud Network (VCN) Configuration
# Rhinometric v2.1.0 - Oracle Cloud

# ========================================
# VCN (Virtual Cloud Network)
# ========================================

resource "oci_core_vcn" "rhinometric_vcn" {
  compartment_id = var.tenancy_ocid
  cidr_block     = var.vcn_cidr_block
  display_name   = "rhinometric-vcn"
  dns_label      = "rhinometric"
  
  freeform_tags = var.tags
}

# ========================================
# Internet Gateway (para acceso público)
# ========================================

resource "oci_core_internet_gateway" "rhinometric_igw" {
  compartment_id = var.tenancy_ocid
  vcn_id         = oci_core_vcn.rhinometric_vcn.id
  display_name   = "rhinometric-igw"
  enabled        = true
  
  freeform_tags = var.tags
}

# ========================================
# Route Table (rutas de red)
# ========================================

resource "oci_core_route_table" "rhinometric_route_table" {
  compartment_id = var.tenancy_ocid
  vcn_id         = oci_core_vcn.rhinometric_vcn.id
  display_name   = "rhinometric-route-table"
  
  route_rules {
    network_entity_id = oci_core_internet_gateway.rhinometric_igw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
  
  freeform_tags = var.tags
}

# ========================================
# Security List (Firewall rules)
# ========================================

resource "oci_core_security_list" "rhinometric_security_list" {
  compartment_id = var.tenancy_ocid
  vcn_id         = oci_core_vcn.rhinometric_vcn.id
  display_name   = "rhinometric-security-list"
  
  # Egress: Permitir TODO el tráfico saliente
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }
  
  # Ingress: SSH (puerto 22)
  ingress_security_rules {
    protocol  = "6" # TCP
    source    = var.allowed_ssh_cidr
    stateless = false
    
    tcp_options {
      min = 22
      max = 22
    }
    
    description = "SSH access"
  }
  
  # Ingress: Grafana (puerto 3000)
  ingress_security_rules {
    protocol  = "6" # TCP
    source    = var.allowed_http_cidr
    stateless = false
    
    tcp_options {
      min = 3000
      max = 3000
    }
    
    description = "Grafana web interface"
  }
  
  # Ingress: API Connector UI (puerto 8091)
  ingress_security_rules {
    protocol  = "6" # TCP
    source    = var.allowed_http_cidr
    stateless = false
    
    tcp_options {
      min = 8091
      max = 8091
    }
    
    description = "API Connector UI"
  }
  
  # Ingress: Prometheus (puerto 9090)
  ingress_security_rules {
    protocol  = "6" # TCP
    source    = var.allowed_http_cidr
    stateless = false
    
    tcp_options {
      min = 9090
      max = 9090
    }
    
    description = "Prometheus web UI"
  }
  
  # Ingress: HTTP (puerto 80) - para Nginx
  ingress_security_rules {
    protocol  = "6" # TCP
    source    = var.allowed_http_cidr
    stateless = false
    
    tcp_options {
      min = 80
      max = 80
    }
    
    description = "HTTP access (Nginx)"
  }
  
  # Ingress: HTTPS (puerto 443) - para Nginx con SSL
  ingress_security_rules {
    protocol  = "6" # TCP
    source    = var.allowed_http_cidr
    stateless = false
    
    tcp_options {
      min = 443
      max = 443
    }
    
    description = "HTTPS access (Nginx SSL)"
  }
  
  # Ingress: ICMP (ping)
  ingress_security_rules {
    protocol  = "1" # ICMP
    source    = "0.0.0.0/0"
    stateless = false
    
    icmp_options {
      type = 3
      code = 4
    }
    
    description = "ICMP Path MTU Discovery"
  }
  
  ingress_security_rules {
    protocol  = "1" # ICMP
    source    = var.vcn_cidr_block
    stateless = false
    
    icmp_options {
      type = 3
    }
    
    description = "ICMP Destination Unreachable"
  }
  
  freeform_tags = var.tags
}

# ========================================
# Subnet (subred pública)
# ========================================

resource "oci_core_subnet" "rhinometric_subnet" {
  compartment_id      = var.tenancy_ocid
  vcn_id              = oci_core_vcn.rhinometric_vcn.id
  cidr_block          = var.subnet_cidr_block
  display_name        = "rhinometric-subnet"
  dns_label           = "rhinometric"
  route_table_id      = oci_core_route_table.rhinometric_route_table.id
  security_list_ids   = [oci_core_security_list.rhinometric_security_list.id]
  prohibit_public_ip_on_vnic = false
  
  freeform_tags = var.tags
}
