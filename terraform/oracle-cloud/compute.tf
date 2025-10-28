# Compute Instance Configuration
# Rhinometric v2.1.0 - Oracle Cloud VM

# ========================================
# Data Source: Availability Domain
# ========================================

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# ========================================
# Compute Instance (VM)
# ========================================

resource "oci_core_instance" "rhinometric_instance" {
  compartment_id      = var.tenancy_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = var.instance_display_name
  shape               = var.instance_shape
  
  # Shape configuration (para Flex shapes)
  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }
  
  # Source (imagen del OS)
  source_details {
    source_type             = "image"
    source_id               = var.instance_image_ocid[var.region]
    boot_volume_size_in_gbs = var.boot_volume_size_in_gbs
  }
  
  # Network configuration
  create_vnic_details {
    subnet_id        = oci_core_subnet.rhinometric_subnet.id
    display_name     = "rhinometric-vnic"
    assign_public_ip = true
    hostname_label   = "rhinometric"
  }
  
  # SSH key para acceso
  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data           = base64encode(templatefile("${path.module}/user-data.sh", {
      grafana_password  = var.grafana_admin_password
      postgres_password = var.postgres_password
      redis_password    = var.redis_password
    }))
  }
  
  # Opciones de preservación
  preserve_boot_volume = false
  
  freeform_tags = var.tags
  
  # Lifecycle
  lifecycle {
    ignore_changes = [
      source_details[0].source_id,
    ]
  }
}

# ========================================
# Boot Volume Backup Policy (opcional)
# ========================================

# resource "oci_core_volume_backup_policy_assignment" "rhinometric_boot_volume_backup" {
#   asset_id  = oci_core_instance.rhinometric_instance.boot_volume_id
#   policy_id = data.oci_core_volume_backup_policies.default_boot_volume_backup_policy.volume_backup_policies[0].id
# }
