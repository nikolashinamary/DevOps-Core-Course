output "external_ip" {
  description = "Public NAT IP address of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "internal_ip" {
  description = "Internal private IP address of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].ip_address
}

output "vm_id" {
  description = "Yandex compute instance ID"
  value       = yandex_compute_instance.vm.id
}

output "ssh_command" {
  description = "SSH command template"
  value       = "ssh ${var.ssh_username}@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}

