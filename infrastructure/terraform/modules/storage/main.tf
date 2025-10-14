# Block Volume for Prometheus
resource "oci_core_volume" "prometheus_volume" {
  count               = var.prometheus_node_count
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_id
  display_name        = "prometheus-volume-${count.index + 1}"
  size_in_gbs        = var.prometheus_volume_size_gb
}

resource "oci_core_volume_attachment" "prometheus_volume_attachment" {
  count           = var.prometheus_node_count
  attachment_type = "paravirtualized"
  instance_id     = var.prometheus_instance_ids[count.index]
  volume_id       = oci_core_volume.prometheus_volume[count.index].id
}

# Block Volume for Grafana
resource "oci_core_volume" "grafana_volume" {
  count               = var.grafana_node_count
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_id
  display_name        = "grafana-volume-${count.index + 1}"
  size_in_gbs        = var.grafana_volume_size_gb
}

resource "oci_core_volume_attachment" "grafana_volume_attachment" {
  count           = var.grafana_node_count
  attachment_type = "paravirtualized"
  instance_id     = var.grafana_instance_ids[count.index]
  volume_id       = oci_core_volume.grafana_volume[count.index].id
}

# Block Volume for Loki
resource "oci_core_volume" "loki_volume" {
  count               = var.loki_node_count
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_id
  display_name        = "loki-volume-${count.index + 1}"
  size_in_gbs        = var.loki_volume_size_gb
}

resource "oci_core_volume_attachment" "loki_volume_attachment" {
  count           = var.loki_node_count
  attachment_type = "paravirtualized"
  instance_id     = var.loki_instance_ids[count.index]
  volume_id       = oci_core_volume.loki_volume[count.index].id
}