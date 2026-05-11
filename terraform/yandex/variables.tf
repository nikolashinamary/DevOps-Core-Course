variable "yc_token" {
  description = "Yandex Cloud IAM token (or set YC_TOKEN env var)"
  type        = string
  sensitive   = true
  default     = null
}

variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Folder ID"
  type        = string
}

variable "zone" {
  description = "Availability zone for resources"
  type        = string
  default     = "ru-central1-a"
}

variable "network_name" {
  description = "VPC network name"
  type        = string
  default     = "terraform-network"
}

variable "subnet_name" {
  description = "VPC subnet name"
  type        = string
  default     = "terraform-subnet"
}

variable "subnet_cidr" {
  description = "Subnet CIDR block"
  type        = string
  default     = "192.168.10.0/24"
}

variable "vm_name" {
  description = "Virtual machine name"
  type        = string
  default     = "terraform-vm"
}

variable "image_id" {
  description = "Ubuntu image ID in Yandex Cloud"
  type        = string
  default     = "fd865v46cboopthn7u0k"
}

variable "disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}

variable "cores" {
  description = "CPU cores for VM"
  type        = number
  default     = 2
}

variable "memory_gb" {
  description = "RAM in GB"
  type        = number
  default     = 1
}

variable "core_fraction" {
  description = "Guaranteed CPU percentage"
  type        = number
  default     = 20
}

variable "preemptible" {
  description = "Use preemptible instance to reduce cost"
  type        = bool
  default     = true
}

variable "ssh_username" {
  description = "Linux username for SSH key injection"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key" {
  description = "SSH public key content (ssh-rsa ...)"
  type        = string
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH into VM"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
