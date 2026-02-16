# Terraform Outputs
# Rhinometric v2.1.0 - Oracle Cloud

output "instance_id" {
  description = "OCID de la instancia EC2"
  value       = oci_core_instance.rhinometric_instance.id
}

output "instance_state" {
  description = "Estado de la instancia"
  value       = oci_core_instance.rhinometric_instance.state
}

output "public_ip" {
  description = "IP pública de la instancia"
  value       = oci_core_instance.rhinometric_instance.public_ip
}

output "private_ip" {
  description = "IP privada de la instancia"
  value       = oci_core_instance.rhinometric_instance.private_ip
}

output "ssh_command" {
  description = "Comando SSH para conectarse"
  value       = "ssh ubuntu@${oci_core_instance.rhinometric_instance.public_ip}"
}

output "grafana_url" {
  description = "URL de Grafana"
  value       = "http://${oci_core_instance.rhinometric_instance.public_ip}:3000"
}

output "grafana_credentials" {
  description = "Credenciales de Grafana"
  value       = "Usuario: admin | Password: ${var.grafana_admin_password}"
  sensitive   = true
}

output "api_connector_url" {
  description = "URL del API Connector"
  value       = "http://${oci_core_instance.rhinometric_instance.public_ip}:8091"
}

output "prometheus_url" {
  description = "URL de Prometheus"
  value       = "http://${oci_core_instance.rhinometric_instance.public_ip}:9090"
}

output "vcn_id" {
  description = "OCID de la VCN"
  value       = oci_core_vcn.rhinometric_vcn.id
}

output "subnet_id" {
  description = "OCID de la subnet"
  value       = oci_core_subnet.rhinometric_subnet.id
}

output "instance_shape" {
  description = "Shape de la instancia"
  value       = "${var.instance_shape} (${var.instance_ocpus} OCPU, ${var.instance_memory_in_gbs} GB RAM)"
}

output "region" {
  description = "Región de Oracle Cloud"
  value       = var.region
}

output "installation_instructions" {
  description = "Instrucciones post-instalación"
  sensitive   = true
  value       = <<-EOT
  
  ========================================
  🦏 RHINOMETRIC v2.1.0 - DEPLOYMENT INFO
  ========================================
  
  📍 Región: ${var.region}
  💻 Instance: ${var.instance_shape} (${var.instance_ocpus} OCPU, ${var.instance_memory_in_gbs} GB RAM)
  🌐 IP Pública: ${oci_core_instance.rhinometric_instance.public_ip}
  
  ⏳ La instalación automática toma ~15 minutos.
  
  🔍 Verificar progreso:
     ssh ubuntu@${oci_core_instance.rhinometric_instance.public_ip}
     tail -f /var/log/cloud-init-output.log
  
  ✅ Una vez completado, acceder a:
  
     🎨 Grafana:       http://${oci_core_instance.rhinometric_instance.public_ip}:3000
        Usuario: admin
        Password: ${var.grafana_admin_password}
     
     🔌 API Connector: http://${oci_core_instance.rhinometric_instance.public_ip}:8091
     📊 Prometheus:    http://${oci_core_instance.rhinometric_instance.public_ip}:9090
  
  🐳 Verificar containers:
     ssh ubuntu@${oci_core_instance.rhinometric_instance.public_ip}
     docker ps | grep rhinometric
  
  🗑️ IMPORTANTE: Destruir recursos para evitar costos:
     terraform destroy
  
  ========================================
  EOT
}
