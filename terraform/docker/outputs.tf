output "container_id" {
  description = "ID of the running Docker container"
  value       = docker_container.moscow_time_app.id
}

output "container_ports" {
  description = "Published ports for the container"
  value       = docker_container.moscow_time_app.ports
}

output "container_name" {
  description = "Container name"
  value       = docker_container.moscow_time_app.name
}

