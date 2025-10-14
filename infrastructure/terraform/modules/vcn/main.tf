resource "oci_core_vcn" "monitoring_vcn" {
  cidr_block     = var.vcn_cidr
  compartment_id = var.compartment_id
  display_name   = var.vcn_name
  dns_label      = var.vcn_dns_label
}

# Public Subnet
resource "oci_core_subnet" "public_subnet" {
  cidr_block        = var.public_subnet_cidr
  compartment_id    = var.compartment_id
  vcn_id           = oci_core_vcn.monitoring_vcn.id
  display_name     = "${var.vcn_name}-public-subnet"
  dns_label        = "public"
  security_list_ids = [oci_core_security_list.public_security_list.id]
  route_table_id   = oci_core_route_table.public_route_table.id
}

# Private Subnet
resource "oci_core_subnet" "private_subnet" {
  cidr_block        = var.private_subnet_cidr
  compartment_id    = var.compartment_id
  vcn_id           = oci_core_vcn.monitoring_vcn.id
  display_name     = "${var.vcn_name}-private-subnet"
  dns_label        = "private"
  security_list_ids = [oci_core_security_list.private_security_list.id]
  route_table_id   = oci_core_route_table.private_route_table.id
  prohibit_public_ip_on_vnic = true
}

# Internet Gateway
resource "oci_core_internet_gateway" "ig" {
  compartment_id = var.compartment_id
  vcn_id        = oci_core_vcn.monitoring_vcn.id
  display_name  = "${var.vcn_name}-internet-gateway"
}

# NAT Gateway
resource "oci_core_nat_gateway" "nat" {
  compartment_id = var.compartment_id
  vcn_id        = oci_core_vcn.monitoring_vcn.id
  display_name  = "${var.vcn_name}-nat-gateway"
}

# Public Route Table
resource "oci_core_route_table" "public_route_table" {
  compartment_id = var.compartment_id
  vcn_id        = oci_core_vcn.monitoring_vcn.id
  display_name  = "${var.vcn_name}-public-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.ig.id
  }
}

# Private Route Table
resource "oci_core_route_table" "private_route_table" {
  compartment_id = var.compartment_id
  vcn_id        = oci_core_vcn.monitoring_vcn.id
  display_name  = "${var.vcn_name}-private-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.nat.id
  }
}

# Security Lists
resource "oci_core_security_list" "public_security_list" {
  compartment_id = var.compartment_id
  vcn_id        = oci_core_vcn.monitoring_vcn.id
  display_name  = "${var.vcn_name}-public-security-list"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
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
}

resource "oci_core_security_list" "private_security_list" {
  compartment_id = var.compartment_id
  vcn_id        = oci_core_vcn.monitoring_vcn.id
  display_name  = "${var.vcn_name}-private-security-list"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  ingress_security_rules {
    protocol = "all"
    source   = var.vcn_cidr
  }
}