# Data source for listing available images
data "oci_core_images" "os_images" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.instance_shape
  sort_by                 = "TIMECREATED"
  sort_order              = "DESC"
}

# Instance Configuration for Prometheus
resource "oci_core_instance" "prometheus_nodes" {
  count               = var.prometheus_node_count
  availability_domain = var.availability_domains[count.index % length(var.availability_domains)].name
  compartment_id      = var.compartment_id
  display_name        = "prometheus-node-${count.index + 1}"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    assign_public_ip = false
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.os_images.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/templates/cloud-init.yaml", {
      node_type = "prometheus"
      node_index = count.index + 1
    }))
  }
}

# Instance Configuration for Grafana
resource "oci_core_instance" "grafana_nodes" {
  count               = var.grafana_node_count
  availability_domain = var.availability_domains[count.index % length(var.availability_domains)].name
  compartment_id      = var.compartment_id
  display_name        = "grafana-node-${count.index + 1}"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    assign_public_ip = false
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.os_images.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/templates/cloud-init.yaml", {
      node_type = "grafana"
      node_index = count.index + 1
    }))
  }
}

# Instance Configuration for Loki
resource "oci_core_instance" "loki_nodes" {
  count               = var.loki_node_count
  availability_domain = var.availability_domains[count.index % length(var.availability_domains)].name
  compartment_id      = var.compartment_id
  display_name        = "loki-node-${count.index + 1}"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    assign_public_ip = false
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.os_images.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/templates/cloud-init.yaml", {
      node_type = "loki"
      node_index = count.index + 1
    }))
  }
}