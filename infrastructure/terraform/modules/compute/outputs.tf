output "prometheus_nodes" {
  description = "List of Prometheus node instances"
  value       = oci_core_instance.prometheus_nodes[*]
}

output "grafana_nodes" {
  description = "List of Grafana node instances"
  value       = oci_core_instance.grafana_nodes[*]
}

output "loki_nodes" {
  description = "List of Loki node instances"
  value       = oci_core_instance.loki_nodes[*]
}

output "backend_sets" {
  description = "Backend sets for load balancer configuration"
  value = {
    prometheus = [for instance in oci_core_instance.prometheus_nodes : {
      ip = instance.private_ip
      port = 9090
    }]
    grafana = [for instance in oci_core_instance.grafana_nodes : {
      ip = instance.private_ip
      port = 3000
    }]
    loki = [for instance in oci_core_instance.loki_nodes : {
      ip = instance.private_ip
      port = 3100
    }]
  }
}