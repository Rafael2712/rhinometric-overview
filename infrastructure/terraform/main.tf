terraform {
  required_providers {
    oci = {
      source = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  private_key_path = var.private_key_path
  fingerprint      = var.fingerprint
  region           = var.region
}

# Data sources
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

data "oci_core_images" "oracle_linux" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Standard2.1"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# Compartment for our SaaS platform
resource "oci_identity_compartment" "saas_platform" {
  compartment_id = var.tenancy_ocid
  name           = "saas-monitoring-platform"
  description    = "SaaS Monitoring Platform - Free Tier Optimized"
  enable_delete  = true
}

# VCN (Virtual Cloud Network)
resource "oci_core_vcn" "saas_vcn" {
  compartment_id = oci_identity_compartment.saas_platform.id
  display_name   = "saas-vcn"
  dns_label      = "saasvcn"
  cidr_blocks    = ["10.0.0.0/16"]
}

# Internet Gateway
resource "oci_core_internet_gateway" "saas_igw" {
  compartment_id = oci_identity_compartment.saas_platform.id
  vcn_id         = oci_core_vcn.saas_vcn.id
  display_name   = "saas-internet-gateway"
  enabled        = true
}

# Route Table
resource "oci_core_route_table" "saas_route_table" {
  compartment_id = oci_identity_compartment.saas_platform.id
  vcn_id         = oci_core_vcn.saas_vcn.id
  display_name   = "saas-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.saas_igw.id
  }
}

# Security List
resource "oci_core_security_list" "saas_security_list" {
  compartment_id = oci_identity_compartment.saas_platform.id
  vcn_id         = oci_core_vcn.saas_vcn.id
  display_name   = "saas-security-list"

  # Outbound rules
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  # Inbound rules
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 443
      max = 443
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 3000
      max = 3000
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 9090
      max = 9093
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 3100
      max = 3100
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 3200
      max = 3200
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 14268
      max = 14268
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    
    tcp_options {
      min = 9411
      max = 9411
    }
  }
}

# Subnet
resource "oci_core_subnet" "saas_subnet" {
  compartment_id      = oci_identity_compartment.saas_platform.id
  vcn_id              = oci_core_vcn.saas_vcn.id
  display_name        = "saas-public-subnet"
  dns_label           = "saaspublic"
  cidr_block          = "10.0.1.0/24"
  route_table_id      = oci_core_route_table.saas_route_table.id
  security_list_ids   = [oci_core_security_list.saas_security_list.id]
  prohibit_public_ip_on_vnic = false
}

# Block Volume for persistent storage
resource "oci_core_volume" "saas_storage" {
  compartment_id      = oci_identity_compartment.saas_platform.id
  availability_domain = try(data.oci_identity_availability_domains.ads.availability_domains[1].name, data.oci_identity_availability_domains.ads.availability_domains[0].name)
  display_name        = "saas-platform-storage"
  size_in_gbs         = 50 # Free tier allows 200GB total
}

  # Single VM Instance (Paid Standard2.1 - Better availability and compatibility)
resource "oci_core_instance" "saas_server" {
  compartment_id      = oci_identity_compartment.saas_platform.id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "saas-monitoring-server-complete"
  shape               = "VM.Standard2.1"

  # VM.Standard2.1: 1 OCPU, 15GB RAM - Intel instance with high availability

  create_vnic_details {
    subnet_id              = oci_core_subnet.saas_subnet.id
    assign_public_ip       = true
    display_name           = "saas-server-vnic"
    hostname_label         = "saas-server"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux.images[0].id
    boot_volume_size_in_gbs = 50 # Free tier boot volume (minimum allowed)
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = "I2Nsb3VkLWNvbmZpZwpwYWNrYWdlX3VwZGF0ZTogdHJ1ZQpwYWNrYWdlX3VwZ3JhZGU6IHRydWUKCnBhY2thZ2VzOgogIC0gZG9ja2VyLWVuZ2luZQogIC0gZG9ja2VyLWNvbXBvc2UKICAtIGdpdAogIC0gd2dldAogIC0gY3VybAogIC0gaHRvcAogIC0gdW56aXAKCnJ1bmNtZDoKICAjIEluc3RhbGwgRG9ja2VyIENvbXBvc2UgaWYgbm90IGF2YWlsYWJsZQogIC0gfAogICAgaWYgISBjb21tYW5kIC12IGRvY2tlci1jb21wb3NlICY+IC9kZXYvbnVsbDsgdGhlbgogICAgICBjdXJsIC1MICJodHRwczovL2dpdGh1Yi5jb20vZG9ja2VyL2NvbXBvc2UvcmVsZWFzZXMvZG93bmxvYWQvdjIuMjEuMC9kb2NrZXItY29tcG9zZS0kKHVuYW1lIC1zKS0kKHVuYW1lIC1tKSIgLW8gL3Vzci9sb2NhbC9iaW4vZG9ja2VyLWNvbXBvc2UKICAgICAgY2htb2QgK3ggL3Vzci9sb2NhbC9iaW4vZG9ja2VyLWNvbXBvc2UKICAgICAgbG4gLXMgL3Vzci9sb2NhbC9iaW4vZG9ja2VyLWNvbXBvc2UgL3Vzci9iaW4vZG9ja2VyLWNvbXBvc2UKICAgIGZpCgogICMgU3RhcnQgYW5kIGVuYWJsZSBEb2NrZXIKICAtIHN5c3RlbWN0bCBzdGFydCBkb2NrZXIKICAtIHN5c3RlbWN0bCBlbmFibGUgZG9ja2VyCiAgLSB1c2VybW9kIC1hRyBkb2NrZXIgb3BjCgogICMgQ3JlYXRlIGFwcGxpY2F0aW9uIGRpcmVjdG9yeQogIC0gbWtkaXIgLXAgL29wdC9zYWFzLXBsYXRmb3JtCiAgLSBjZCAvb3B0L3NhYXMtcGxhdGZvcm0KCiAgIyBEZWNvZGUgYW5kIHdyaXRlIGRvY2tlci1jb21wb3NlIGZpbGUgKE9wdGltaXplZCBmb3IgOEdCKQogIC0gZWNobyAiZG1WeWMybHZiam9nSnpNdU9DY0tDbk5sY25acFkyVnpPZ29nSUNNZ1BUMDNQVDA5UFQwOVBUMDlQVDA5UFQwOVBUMDlQVDA5UFQwOVBUMDlDaUFnSXlCVVNVVlNJREU2SUVKQlUwVWdSRVVnUkVGVVQxTWdXU0JEUVVOSVVRb2dJQ01nUFQwOVBUMDlQVDA5UFQwOVBUMDlQVDA5UFQwOVBUMDlQVDA5UFQwOUNpQWdDaUFnSXlCQ1lYTmxJR1JsSUdSaGRHOXpJSEJ5YVc1amFYQmhiQ0FvYlhWc2RHa3RkR1Z1WVc1MElIQnZjaUJ6WTJobGJXRXBDaUFnY0c5emRHZHlaWE02Q2lBZ0lDQnBiV0ZuWlRvZ2NHOXpkR2R5WlhNNk1UVUtJQ0FnSUdOdmJuUmhhVzVsY2w5dVlXMWxPaUJ6WVdGekxYQnZjM1JuY21WekNpQWdJQ0JsYm5acGNtOXViV1Z1ZERvS0lDQWdJQ0FnVUU5VFZFZFNSVk5mUkVJNklITmhZWE5mY0d4aGRHWnZjbTBLSUNBZ0lDQWdVRTlUVkVkU1JWTmZWVk5GVWpvZ2NHOXpkR2R5WlhNS0lDQWdJQ0FnVUU5VFZFZFNSVk5mVUVGVFUxZFBVa1E2SUNSN1VFOVRWRWRTUlZOZlVFRlRVMWRQVWtRNkxYTmxZM1Z5WlY5d1lYTnpkMjl5WkY4eU1ESTBmUW9nSUNBZ2RtOXNkVzFsY3pvS0lDQWdJQ0FnTFNCd2IzTjBaM0psYzE5a1lYUmhPaTkyWVhJdmJHbGlMM0J2YzNSbmNtVnpjV3d2WkdGMFlRb2dJQ0FnSUNBdElDNHZhVzVwZEMxa1lqb3ZaRzlqYTJWeUxXVnVkSEo1Y0c5cGJuUXRhVzVwZEdSaUxtUUtJQ0FnSUc1bGRIZHZjbXR6T2dvZ0lDQWdJQ0F0SUhOaFlYTmZibVYwZDI5eWF3b2dJQ0FnY21WemRHRnlkRG9nZFc1c1pYTnpMWE4wYjNCd1pXUUtJQ0FnSUdSbGNHeHZlVG9LSUNBZ0lDQWdjbVZ6YjNWeVkyVnpPZ29nSUNBZ0lDQWdJR3hwYldsMGN6b0tJQ0FnSUNBZ0lDQWdJR053ZFhNNklDY3hMalVuQ2lBZ0lDQWdJQ0FnSUNCdFpXMXZjbms2SUREQ3dLQ3ZFU0JrVEdBSUJTUUNBQUEiIHwgYmFzZTY0IC1kID4gZG9ja2VyLWNvbXBvc2UueW1s"
  }

  preserve_boot_volume = false
}

# Volume attachment
resource "oci_core_volume_attachment" "saas_storage_attachment" {
  attachment_type = "paravirtualized"
  instance_id     = oci_core_instance.saas_server.id
  volume_id       = oci_core_volume.saas_storage.id
  display_name    = "saas-storage-attachment"
}