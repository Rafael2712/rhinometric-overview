output "load_balancer_ip" {
  description = "Public IP address of the load balancer"
  value       = oci_load_balancer.monitoring_lb.ip_addresses[0]
}