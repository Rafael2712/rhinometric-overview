output "prometheus_volume_ids" {
  description = "OCIDs of the Prometheus volumes"
  value       = oci_core_volume.prometheus_volume[*].id
}

output "grafana_volume_ids" {
  description = "OCIDs of the Grafana volumes"
  value       = oci_core_volume.grafana_volume[*].id
}

output "loki_volume_ids" {
  description = "OCIDs of the Loki volumes"
  value       = oci_core_volume.loki_volume[*].id
}