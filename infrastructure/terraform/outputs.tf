# Instance outputs
output "saas_server_public_ip" {
  description = "Public IP address of the SaaS monitoring server"
  value       = oci_core_instance.saas_server.public_ip
}

output "saas_server_private_ip" {
  description = "Private IP address of the SaaS monitoring server"
  value       = oci_core_instance.saas_server.private_ip
}

# Network outputs
output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.saas_vcn.id
}

output "subnet_id" {
  description = "OCID of the public subnet"
  value       = oci_core_subnet.saas_subnet.id
}

# Storage outputs
output "storage_volume_id" {
  description = "OCID of the storage volume"
  value       = oci_core_volume.saas_storage.id
}

# Connection information
output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh opc@${oci_core_instance.saas_server.public_ip}"
}

output "grafana_url" {
  description = "Grafana dashboard URL"
  value       = "http://${oci_core_instance.saas_server.public_ip}:3000"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://${oci_core_instance.saas_server.public_ip}:9090"
}