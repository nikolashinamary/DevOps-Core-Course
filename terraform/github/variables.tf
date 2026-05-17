variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub user or organization owner"
  type        = string
}

variable "repository_name" {
  description = "Repository name to create/import"
  type        = string
}

variable "repository_description" {
  description = "Repository description"
  type        = string
  default     = "DevOps course repository managed by Terraform"
}

variable "repository_visibility" {
  description = "Repository visibility (public/private)"
  type        = string
  default     = "public"
}

variable "default_branch" {
  description = "Default branch name"
  type        = string
  default     = "master"
}

variable "required_approving_review_count" {
  description = "Required PR approvals for protected branch"
  type        = number
  default     = 1
}

