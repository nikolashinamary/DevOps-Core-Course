output "repo_url" {
  description = "HTTPS URL of the managed repository"
  value       = github_repository.repo.html_url
}

output "repo_name" {
  description = "Repository name"
  value       = github_repository.repo.name
}

