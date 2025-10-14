# Load Balancer
resource "oci_load_balancer" "monitoring_lb" {
  compartment_id = var.compartment_id
  display_name   = "monitoring-load-balancer"
  shape          = "flexible"
  shape_details {
    minimum_bandwidth_in_mbps = 10
    maximum_bandwidth_in_mbps = 100
  }
  subnet_ids = [var.subnet_id]
}

# Prometheus Backend Set
resource "oci_load_balancer_backend_set" "prometheus_backend_set" {
  name             = "prometheus-backend-set"
  load_balancer_id = oci_load_balancer.monitoring_lb.id
  policy           = "ROUND_ROBIN"

  health_checker {
    protocol            = "HTTP"
    port               = 9090
    url_path           = "/-/healthy"
    return_code        = 200
    interval_ms        = 10000
    timeout_in_millis  = 3000
    retries            = 3
  }
}

# Grafana Backend Set
resource "oci_load_balancer_backend_set" "grafana_backend_set" {
  name             = "grafana-backend-set"
  load_balancer_id = oci_load_balancer.monitoring_lb.id
  policy           = "ROUND_ROBIN"

  health_checker {
    protocol            = "HTTP"
    port               = 3000
    url_path           = "/api/health"
    return_code        = 200
    interval_ms        = 10000
    timeout_in_millis  = 3000
    retries            = 3
  }
}

# Loki Backend Set
resource "oci_load_balancer_backend_set" "loki_backend_set" {
  name             = "loki-backend-set"
  load_balancer_id = oci_load_balancer.monitoring_lb.id
  policy           = "ROUND_ROBIN"

  health_checker {
    protocol            = "HTTP"
    port               = 3100
    url_path           = "/ready"
    return_code        = 200
    interval_ms        = 10000
    timeout_in_millis  = 3000
    retries            = 3
  }
}

# Add Backends for Prometheus
resource "oci_load_balancer_backend" "prometheus_backends" {
  count            = length(var.backend_sets.prometheus)
  backendset_name  = oci_load_balancer_backend_set.prometheus_backend_set.name
  ip_address       = var.backend_sets.prometheus[count.index].ip
  load_balancer_id = oci_load_balancer.monitoring_lb.id
  port            = var.backend_sets.prometheus[count.index].port
}

# Add Backends for Grafana
resource "oci_load_balancer_backend" "grafana_backends" {
  count            = length(var.backend_sets.grafana)
  backendset_name  = oci_load_balancer_backend_set.grafana_backend_set.name
  ip_address       = var.backend_sets.grafana[count.index].ip
  load_balancer_id = oci_load_balancer.monitoring_lb.id
  port            = var.backend_sets.grafana[count.index].port
}

# Add Backends for Loki
resource "oci_load_balancer_backend" "loki_backends" {
  count            = length(var.backend_sets.loki)
  backendset_name  = oci_load_balancer_backend_set.loki_backend_set.name
  ip_address       = var.backend_sets.loki[count.index].ip
  load_balancer_id = oci_load_balancer.monitoring_lb.id
  port            = var.backend_sets.loki[count.index].port
}

# HTTPS Listener for Grafana
resource "oci_load_balancer_listener" "grafana_listener" {
  name             = "grafana-listener"
  load_balancer_id = oci_load_balancer.monitoring_lb.id
  port            = 443
  protocol        = "HTTP"
  
  default_backend_set_name = oci_load_balancer_backend_set.grafana_backend_set.name
}