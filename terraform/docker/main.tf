provider "docker" {}

resource "docker_image" "moscow_time_app" {
  name         = var.app_image_name
  keep_locally = false
}

resource "docker_container" "moscow_time_app" {
  name    = var.python_container_name
  image   = docker_image.moscow_time_app.image_id
  user    = "appuser"
  restart = "no"

  must_run       = true
  remove_volumes = true

  ports {
    internal = var.internal_port
    external = var.external_port
    ip       = "0.0.0.0"
    protocol = "tcp"
  }
}

