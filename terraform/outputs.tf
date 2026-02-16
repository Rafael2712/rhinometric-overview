output "instance_id" {
  description = "ID of the Spot instance"
  value       = aws_spot_instance_request.rhinometric_test.spot_instance_id
}

output "instance_public_ip" {
  description = "Public IP address (Elastic IP)"
  value       = aws_eip.rhinometric_test.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name"
  value       = aws_eip.rhinometric_test.public_dns
}

output "security_group_id" {
  description = "Security Group ID"
  value       = aws_security_group.rhinometric_test.id
}

output "data_volume_id" {
  description = "EBS Data Volume ID"
  value       = aws_ebs_volume.rhinometric_data.id
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.rhinometric_test.public_ip}"
}

output "access_urls" {
  description = "URLs to access services"
  value = {
    nginx           = "http://${aws_eip.rhinometric_test.public_ip}"
    console         = "http://${aws_eip.rhinometric_test.public_ip}:3002"
    grafana         = "http://${aws_eip.rhinometric_test.public_ip}:3000"
    prometheus      = "http://${aws_eip.rhinometric_test.public_ip}:9090"
    jaeger          = "http://${aws_eip.rhinometric_test.public_ip}:16686"
  }
}

output "cost_estimate" {
  description = "Estimated monthly cost"
  value       = "~$35-45/month (Spot) vs ~$132/month (On-Demand)"
}
