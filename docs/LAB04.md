# Lab 04 - Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

### Cloud provider chosen and rationale
I used **Yandex Cloud** because it is available in my region and supports both Terraform and Pulumi providers for the same infrastructure scenario.

### Instance type/size and why
From IaC evidence (`tf-plan.txt` and `tf-apply.txt`), the VM profile is:
- `cores = 2`
- `memory = 1 GB`
- `core_fraction = 20%`
- `disk = 10 GB (network-hdd)`
- `preemptible = true`

This is a low-cost/free-tier-oriented setup and enough for SSH access and next labs.

### Region/zone selected
- `ru-central1-a`

### Total cost
- Target cost: minimal / free-tier-oriented.
- All resources were created with small configuration and preemptible scheduling.

### Resources created (list all)
Terraform (`terraform/yandex`):
- `yandex_vpc_network.network`
- `yandex_vpc_subnet.subnet`
- `yandex_vpc_security_group.vm_sg` (ports `22`, `80`, `5000` + all egress)
- `yandex_compute_disk.boot_disk`
- `yandex_compute_instance.vm`

Pulumi (`pulumi/__main__.py`):
- `VpcNetwork`
- `VpcSubnet`
- `VpcSecurityGroup`
- `ComputeDisk`
- `ComputeInstance`

## 2. Terraform Implementation

### Terraform version used
- `Terraform v1.14.5` (`terraform version`)

### Project structure explanation
- `terraform/yandex` - VM/network/security group/main IaC for Lab04
- `terraform/docker` - local container IaC module
- `terraform/github` - bonus GitHub import module

### Key configuration decisions
- All sensitive values are provided outside code (`terraform.tfvars`, gitignored).
- VM parameters are variable-driven.
- SSH is restricted by `allowed_ssh_cidrs`.
- Outputs expose IP and SSH command.

### Challenges encountered
- `terraform init` initially failed with provider registry host issue.
- Resolved by using project CLI config and re-initialization.
- Verified by successful `tf-init.txt` and provider installation.

### Terminal output from key commands
Evidence files:
- `docs/lab04-evidence/tf-init.txt`
- `docs/lab04-evidence/tf-plan.txt`
- `docs/lab04-evidence/tf-apply.txt`
- `docs/lab04-evidence/tf-output.txt`
- `docs/lab04-evidence/tf-ssh-proof.txt`

Key excerpts:

```text
terraform init
- Installing yandex-cloud/yandex v0.187.0...
Terraform has been successfully initialized!
```

```text
terraform plan
Plan: 5 to add, 0 to change, 0 to destroy.
Saved the plan to: tfplan
```

```text
terraform apply
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.
external_ip = "89.169.138.140"
internal_ip = "192.168.10.31"
ssh_command = "ssh ubuntu@89.169.138.140"
```

```text
SSH proof
ssh ubuntu@89.169.138.140
Welcome to Ubuntu 20.04.6 LTS
```

## 3. Pulumi Implementation

### Pulumi version and language used
- Pulumi CLI: `v3.220.0`
- Pulumi SDK package from evidence install: `pulumi==3.221.0`
- Language: **Python**
- Python runtime used for stack: `Python 3.12.9` (`pulumi-python-version.txt`)

### How code differs from Terraform
Terraform describes resources declaratively in HCL. Pulumi uses Python constructors and config objects, so application language features can be used directly in IaC code.

### Advantages discovered
- Easier to parameterize logic in Python.
- Reuse via Python functions/variables is straightforward.
- Stack outputs are easy to consume from CLI.

### Challenges encountered
- Required Pulumi config keys must be set (`yandex:cloudId`, `yandex:folderId`, `yandex:token`, `app:sshPublicKey`).
- Compatibility issue with `pkg_resources` required pinning `setuptools<81`.
- Provider argument names had to match installed SDK (`ingresses`/`egresses`).

### Terminal output from key commands
Evidence files:
- `docs/lab04-evidence/pulumi-preview.txt`
- `docs/lab04-evidence/pulumi-up.txt`
- `docs/lab04-evidence/pulumi-output.txt`
- `docs/lab04-evidence/pulumi-ssh-proof.txt`

Key excerpts:

```text
pulumi preview
Resources:
    + 7 to create
```

```text
pulumi up
Resources:
    + 7 created
Duration: 54s
Outputs:
    externalIp: "89.169.151.150"
    internalIp: "192.168.20.19"
    sshCommand: "ssh ubuntu@89.169.151.150"
```

```text
SSH proof
ssh ubuntu@89.169.151.150
Welcome to Ubuntu 20.04.6 LTS
```

## 4. Terraform vs Pulumi Comparison

### Ease of Learning
Terraform was easier to start with because the workflow is strict and predictable: `init -> plan -> apply`. Error messages during planning are usually direct. Pulumi required additional environment setup (venv, backend, stack config), so first start was longer.

### Code Readability
For this lab scope, Terraform was more compact and easier to scan quickly. Pulumi code is readable too, but has more boilerplate around config and resource args. As logic grows, Pulumi can become clearer due to native language abstractions.

### Debugging
Terraform debugging was mostly around provider init and plan diff interpretation. Pulumi debugging included Python/package issues plus provider API argument differences. In this run, Pulumi required more troubleshooting steps before first successful `up`.

### Documentation
Terraform docs/examples were enough to finish baseline resources quickly. Pulumi docs were useful, but some API details depended on exact installed package version. Both are usable; Terraform felt smoother for this beginner task.

### Use Case
I would use Terraform for standard infrastructure lifecycle with strong plan review process. I would use Pulumi when infrastructure needs richer programming logic and reuse through code abstractions. For this lab, both achieved the same infrastructure outcome.

## 5. Lab 5 Preparation & Cleanup

### VM for Lab 5
- Are you keeping your VM for Lab 5? **Yes**
- Which VM is kept? **Pulumi-created VM**
- Public IP: `89.169.151.150`

### Cleanup status
Terraform resources were destroyed before switching to Pulumi:

```text
docs/lab04-evidence/tf-destroy.txt
Destroy complete! Resources: 5 destroyed.
```

Pulumi resources are currently running and accessible:
- Creation proof: `docs/lab04-evidence/pulumi-up.txt`
- SSH proof: `docs/lab04-evidence/pulumi-ssh-proof.txt`

### Cloud console screenshots (optional)
- This report uses terminal evidence files (`.txt`) as primary proof.
- Add only sanitized screenshots (without tokens/keys) if your instructor requests them.

## Bonus Task - IaC CI/CD + Infrastructure Import

### Current status
Based on available evidence `.txt` files, bonus evidence is **not completed yet** in this report:
- no `gh-import.txt`
- no `gh-plan-after-import.txt`
- no GitHub Actions run screenshot for Terraform CI in evidence folder

Workflow file exists in repo:
- `.github/workflows/terraform-ci.yml`

To complete bonus later, run:
- `IMPORT_REPO_ID=DevOps-Core-Course ./scripts/lab04_evidence.sh bonus`
- attach GitHub Actions screenshot for Terraform CI run.

## Evidence Index

Terraform:
- `docs/lab04-evidence/tf-init.txt`
- `docs/lab04-evidence/tf-fmt.txt`
- `docs/lab04-evidence/tf-validate.txt`
- `docs/lab04-evidence/tf-plan.txt`
- `docs/lab04-evidence/tf-apply.txt`
- `docs/lab04-evidence/tf-output.txt`
- `docs/lab04-evidence/tf-ssh-proof.txt`
- `docs/lab04-evidence/tf-destroy.txt`

Pulumi:
- `docs/lab04-evidence/pulumi-python-version.txt`
- `docs/lab04-evidence/pulumi-pip-bootstrap.txt`
- `docs/lab04-evidence/pulumi-pip-install.txt`
- `docs/lab04-evidence/pulumi-preview.txt`
- `docs/lab04-evidence/pulumi-up.txt`
- `docs/lab04-evidence/pulumi-output.txt`
- `docs/lab04-evidence/pulumi-ssh-proof.txt`
