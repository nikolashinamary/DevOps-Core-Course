variable "python_container_name" {
  description = "Name of the Docker container"
  type        = string
  default     = "moscow-time-app"
}

variable "app_image_name" {
  description = "Docker image to run"
  type        = string
  default     = "karamkhaddourpro/my-fastapi-app:latest"
}

variable "internal_port" {
  description = "Internal app port exposed by the container"
  type        = number
  default     = 8000
}

variable "external_port" {
  description = "Host port mapped to the app container"
  type        = number
  default     = 8080
}

