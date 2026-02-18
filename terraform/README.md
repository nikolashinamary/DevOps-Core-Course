# Terraform Documentation

This document captures Terraform structure, key configuration, and example command outputs for provisioning:

1. A Docker container that serves Moscow time via FastAPI (`terraform/docker`)
2. A Yandex Cloud VM (`terraform/yandex`)
3. Existing GitHub repository management via Terraform import (`terraform/github`)

## File Structure

```text
terraform/
├── TF.md
├── .gitignore
├── .tflint.hcl
├── docker/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── yandex/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf
│   └── terraform.tfvars.example
└── github/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    └── terraform.tfvars.example
```

## Docker (`terraform/docker`)

### Commands

```bash
cd terraform/docker
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
terraform state list
terraform state show docker_container.moscow_time_app
terraform output
```

### Expected Resources

- `docker_image.moscow_time_app`
- `docker_container.moscow_time_app`

### Key Variables

- `python_container_name` (default: `moscow-time-app`)
- `app_image_name` (default: `karamkhaddourpro/my-fastapi-app:latest`)
- `internal_port` (default: `8000`)
- `external_port` (default: `8080`)

### Example Outputs

```text
container_id = "62a249ea6101f26fac7950c54502b8ddd52ad1cb1a31ebaadbd8bc0f87caf674"
container_ports = [
  {
    external = 8080
    internal = 8000
    ip       = "0.0.0.0"
    protocol = "tcp"
  }
]
```

## Yandex Cloud (`terraform/yandex`)

### Authentication Notes

Use either:

- `yc iam create-token` and set `yc_token` in `terraform.tfvars` (not committed)
- Environment variables supported by provider (recommended for secrets)

Required identifiers:

- `cloud_id`
- `folder_id`

### Commands

```bash
cd terraform/yandex
cp terraform.tfvars.example terraform.tfvars
# fill values (token, cloud_id, folder_id, ssh_public_key, etc.)

terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
terraform output
```

### Resources Created

- `yandex_vpc_network.network`
- `yandex_vpc_subnet.subnet`
- `yandex_vpc_security_group.vm_sg` (SSH/80/5000 + egress)
- `yandex_compute_disk.boot_disk`
- `yandex_compute_instance.vm`

### Example Outputs

```text
external_ip = "84.201.132.123"
internal_ip = "192.168.10.34"
```

## GitHub Import (`terraform/github`)

### Commands

```bash
cd terraform/github
cp terraform.tfvars.example terraform.tfvars
# set github_token, github_owner, repository_name

terraform init
terraform fmt
terraform validate

# import existing repo into state
terraform import github_repository.repo DevOps-Core-Course

terraform plan
terraform apply
terraform output
```

### Managed Resources

- `github_repository.repo`
- `github_branch_default.default`
- `github_branch_protection.default`

### Example Output

```text
repo_url = "https://github.com/<owner>/DevOps-Core-Course"
```

## Best Practices Applied

- Sensitive values (`yc_token`, `github_token`) are variables and should come from env vars or gitignored tfvars.
- `.gitignore` excludes state files, tfvars, and local overrides.
- `terraform fmt` and `terraform validate` are expected before every apply.
- `terraform plan` is used before apply to review changes.
- Existing infrastructure can be brought under IaC control via `terraform import`.

