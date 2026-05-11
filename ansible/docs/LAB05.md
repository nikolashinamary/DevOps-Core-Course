# Lab 5 - Ansible Fundamentals

## 1. Architecture Overview

**Ansible version used**
- Local virtual environment: `.venv-lab05`
- Version command used: `ansible --version`
- Compatible line used for this VM: `ansible-core 2.18.x`

**Target VM OS and version**
- Host: `lab05-vm` (`84.252.129.209`)
- Ubuntu family host (APT repository codename observed: `focal`)

**Role-based project structure**
```text
ansible/
├── inventory/
│   └── hosts.ini
├── roles/
│   ├── common/
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── provision.yml
│   ├── deploy.yml
│   └── site.yml
├── group_vars/
│   └── all.yml (Vault encrypted)
├── ansible.cfg
└── docs/
    ├── LAB05.md
    └── evidence/
```

**Why roles instead of monolithic playbooks?**
- Clear separation of responsibilities (`common`, `docker`, `app_deploy`).
- Reuse across multiple playbooks (`provision.yml`, `deploy.yml`, `site.yml`).
- Easier debugging and maintenance by isolating logic per domain.

## 2. Roles Documentation

### Role: `common`
- Purpose: baseline package setup, apt cache prep, timezone setup, base utilities.
- Variables: `common_packages`, `timezone`.
- Handlers: none.
- Dependencies: none.

### Role: `docker`
- Purpose: install Docker Engine and runtime dependencies; configure repository and service.
- Variables: `docker_users`, `docker_repository`, `docker_repository_key_url`, `docker_repository_keyring`, `docker_repository_arch`.
- Handlers: `Restart docker`.
- Dependencies: runs after `common`.

### Role: `app_deploy`
- Purpose: authenticate to Docker Hub, pull image, run/recreate container, verify app health endpoint.
- Variables: `dockerhub_username`, `dockerhub_password`, `docker_image`, `docker_image_tag`, `app_container_name`, `app_port`, `app_host_port`, `app_health_check_path`.
- Handlers: `Restart app container`.
- Dependencies: requires Docker installed/running.

## 3. Idempotency Demonstration

Provisioning command used twice:
```bash
ansible-playbook playbooks/provision.yml --ask-vault-pass
```

### First run (`docs/evidence/provision-run1.txt`)
Key recap:
```text
PLAY RECAP
lab05-vm : ok=21 changed=7 unreachable=0 failed=0 skipped=1
```
Main changed tasks on first run:
- `common : Remove stale Docker apt source entries before apt update`
- `docker : Add Docker repository`
- `docker : Update apt cache after adding Docker repo`
- `docker : Install Docker packages`
- `docker : Add users to docker group`
- `docker : Install Docker SDK for Python`
- `RUNNING HANDLER [docker : Restart docker]`

### Second run (`docs/evidence/provision-run2.txt`)
Key recap:
```text
PLAY RECAP
lab05-vm : ok=20 changed=3 unreachable=0 failed=0 skipped=1
```
Observed remaining changes:
- Docker repository normalization tasks (`remove stale entry`, `add repo`, `apt cache`) still report changes due prior repository conflict remediation.

Idempotency conclusion:
- Core package/service state converges correctly.
- Remaining changes are limited to Docker apt source normalization workflow after resolving conflicting source definitions.

## 4. Ansible Vault Usage

**How credentials are stored securely**
- Sensitive values are in `ansible/group_vars/all.yml`.
- File is encrypted with Ansible Vault (AES256 format).

**Vault password strategy**
- Local password file: `ansible/.vault_pass`.
- Referenced in `ansible.cfg` via `vault_password_file = .vault_pass`.
- `.vault_pass` is gitignored.

**Encrypted file proof**
```text
$ANSIBLE_VAULT;1.1;AES256
...
```

Why Vault matters:
- Prevents plaintext credential leakage in repository history/logs.
- Keeps automation reproducible while preserving secret confidentiality.

## 5. Deployment Verification

Deploy command run:
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass | tee docs/evidence/deploy-run.txt
```

Deploy recap (`docs/evidence/deploy-run.txt`):
```text
PLAY RECAP
lab05-vm : ok=14 changed=6 unreachable=0 failed=0 skipped=2
```

### Container status
Command:
```bash
ansible webservers -a "docker ps" | tee docs/evidence/docker-ps.txt
```
Output:
```text
lab05-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                         COMMAND           CREATED         STATUS         PORTS                                         NAMES
ad3656f58bb9   nikolashinamaria/devops-info-service:latest   "python app.py"   5 minutes ago   Up 5 minutes   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   devops-info-service
```

### Health endpoint
Command:
```bash
ansible webservers -a "curl -sS http://127.0.0.1:5000/health" | tee docs/evidence/health-check.txt
```
Output:
```text
lab05-vm | CHANGED | rc=0 >>
{"status":"healthy","timestamp":"2026-02-18T22:25:45.153629+00:00","uptime_seconds":315}
```

### Root endpoint
Command:
```bash
ansible webservers -a "curl -sS http://127.0.0.1:5000/" | tee docs/evidence/root-check.txt
```
Output:
```text
lab05-vm | CHANGED | rc=0 >>
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.17.0.1","method":"GET","path":"/","user_agent":"curl/7.68.0"},"runtime":{"current_time":"2026-02-18T22:25:54.783445+00:00","timezone":"UTC","uptime_human":"0 hours, 5 minutes","uptime_seconds":325},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":2,"hostname":"ad3656f58bb9","platform":"Linux","platform_version":"Linux-5.4.0-208-generic-x86_64-with-glibc2.41","python_version":"3.13.12"}}
```

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
- Roles separate responsibilities, reduce duplication, and keep orchestration files small.

**How do roles improve reusability?**
- Each role can be reused in other inventories/projects by changing only variables.

**What makes a task idempotent?**
- It declares desired state and only changes resources when state differs.

**How do handlers improve efficiency?**
- Handlers trigger only when notified by a changed task, avoiding unnecessary restarts.

**Why is Ansible Vault necessary?**
- It enables committing configuration safely without exposing Docker credentials.

## 7. Challenges and Resolutions

- **Remote Python compatibility:** target host Python is `3.8.10`, so local Ansible was pinned to a compatible core line.
- **APT lock conflicts (`unattended-upgrades`):** resolved by lock-aware apt task settings and reruns.
- **Docker repo `Signed-By` conflicts:** resolved by normalizing stale Docker source entries and enforcing a canonical repository entry.

## 8. Evidence Index

- `ansible/docs/evidence/provision-run1.txt`
- `ansible/docs/evidence/provision-run2.txt`
- `ansible/docs/evidence/deploy-run.txt`
- `ansible/docs/evidence/docker-ps.txt`
- `ansible/docs/evidence/health-check.txt`
- `ansible/docs/evidence/root-check.txt`
