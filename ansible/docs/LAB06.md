# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Mariana Nikolashina  
**Date:** 2026-03-01  
**Lab Points:** 10 (main tasks only, bonus not attempted)

---

## Task 1: Blocks & Tags (2 pts)

### Implementation

Refactored roles with Ansible blocks, rescue, always, and granular tags.

Files:
- `ansible/roles/common/tasks/main.yml`
- `ansible/roles/common/defaults/main.yml`
- `ansible/roles/docker/tasks/main.yml`
- `ansible/roles/docker/handlers/main.yml`
- `ansible/playbooks/provision.yml`

`common` role:
- Package tasks grouped in block with tags `common`, `packages`.
- Rescue path for apt cache issue (`apt-get update --fix-missing`).
- Always step writes `/tmp/ansible-common-packages.log`.
- User tasks grouped in block with tags `common`, `users`.

`docker` role:
- Install block tagged `docker_install`.
- Config block tagged `docker_config`.
- Rescue path retries apt cache and Docker GPG fetch after wait.
- Always step ensures Docker service enabled/running.

### Tag evidence

Tag listings:
- `ansible/docs/evidence/lab06-provision-list-tags.txt`
- `ansible/docs/evidence/lab06-deploy-list-tags.txt`

Provision selective execution runs:
- `--tags docker`: `ansible/docs/evidence/lab06-provision-tags-docker.txt`
- `--skip-tags common`: `ansible/docs/evidence/lab06-provision-skip-common.txt`
- `--tags packages`: `ansible/docs/evidence/lab06-provision-tags-packages.txt`
- `--tags docker --check`: `ansible/docs/evidence/lab06-provision-tags-docker-check.txt`
- `--tags docker_install`: `ansible/docs/evidence/lab06-provision-tags-docker-install.txt`

### Rescue-trigger evidence

Controlled failing run to trigger rescue block:
- Command used: `--tags docker_install -e "docker_repository_key_url=https://invalid.example.invalid/docker-gpg"`
- Evidence: `ansible/docs/evidence/lab06-provision-rescue-trigger.txt`
- Result shows `rescued=1` in play recap.

---

## Task 2: Docker Compose Migration (3 pts)

### Role rename and dependency

Renamed role:
- `ansible/roles/app_deploy` -> `ansible/roles/web_app`

Dependency:
- `ansible/roles/web_app/meta/main.yml` includes dependency on `docker` role.

### Compose template and deployment

Files:
- `ansible/roles/web_app/templates/docker-compose.yml.j2`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/defaults/main.yml`

Implemented:
- Compose file templating with variables for image, tag, app ports, env values, restart policy.
- Deployment via `community.docker.docker_compose_v2`.
- Health verification with `wait_for` and HTTP `uri` checks.
- Rescue diagnostics via `docker compose ps`.

Rendered compose evidence:
- `ansible/docs/evidence/lab06-docker-compose-rendered.txt`

### Idempotency proof

Deployment idempotency runs:
- Run 1: `ansible/docs/evidence/lab06-deploy-idempotency-run1.txt` (recap shows `changed=1`)
- Run 2: `ansible/docs/evidence/lab06-deploy-idempotency-run2.txt` (recap shows `changed=0`)

Application accessibility:
- Root: `ansible/docs/evidence/lab06-curl-root.txt`
- Health: `ansible/docs/evidence/lab06-curl-health.txt`

---

## Task 3: Wipe Logic (1 pt)

### Implementation

Files:
- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/defaults/main.yml`

Safety model:
- Variable gate: `web_app_wipe` (default `false`).
- Tag gate: `web_app_wipe`.
- Wipe included first in `main.yml` to support clean reinstall.

Wipe actions:
- Compose down (`state: absent`).
- Remove compose file.
- Remove app directory.
- Log wipe completion message.

### Scenario results

1. Scenario 1 (normal deploy, wipe should not run)
- Evidence: `ansible/docs/evidence/lab06-deploy-scenario1-normal.txt`
- Wipe tasks are included but skipped; deployment succeeds.

2. Scenario 2 (wipe only)
- Evidence: `ansible/docs/evidence/lab06-deploy-scenario2-wipe-only.txt`
- Post-check evidence:
  - Docker PS empty for app: `ansible/docs/evidence/lab06-scenario2-docker-ps.txt`
  - `/opt` listing without app dir: `ansible/docs/evidence/lab06-scenario2-opt-ls.txt`

3. Scenario 3 (clean reinstall = wipe + deploy)
- Evidence: `ansible/docs/evidence/lab06-deploy-scenario3-clean-reinstall.txt`
- Output shows wipe completion then healthy redeployment.

4. Scenario 4a (tag set, variable false)
- Evidence: `ansible/docs/evidence/lab06-deploy-scenario4a-tag-only-variable-false.txt`
- Wipe tasks are skipped due `when: web_app_wipe | bool`.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Workflow

File:
- `.github/workflows/ansible-deploy.yml`

Implemented jobs:
1. `lint`
- Checkout
- Python setup
- Install `ansible-core==2.18.*` and `ansible-lint`
- Install collection requirements
- Run lint on playbooks

2. `deploy` (on push)
- Setup SSH from secrets
- Build runtime inventory file
- Use vault password from secrets
- Run deployment playbook
- Verify root and health endpoints with curl

### Related files

- `ansible/collections/requirements.yml`
- `ansible/.ansible-lint`
- `README.md` badge added for `ansible-deploy.yml`

### Local CI-equivalent checks

- Lint evidence: `ansible/docs/evidence/lab06-ansible-lint.txt`
- Syntax checks:
  - `ansible/docs/evidence/lab06-provision-syntax.txt`
  - `ansible/docs/evidence/lab06-deploy-syntax.txt`

Note:
- Workflow was prepared but not pushed/executed in GitHub Actions in this run (per request: no git submission).

---

## Task 5: Documentation (1 pt)

This file is the complete submission document for Lab 6 main tasks.

---

## Testing Results Summary

Infrastructure and connectivity:
- VM was recreated because previous VM no longer existed.
- Provisioning tool used: `scripts/lab04_evidence.sh terraform`.
- New VM inventory entry updated: `ansible/inventory/hosts.ini` (`lab06-vm`, `130.193.49.28`).
- Connectivity proof: `ansible/docs/evidence/lab06-ping.txt`.

Main provisioning run:
- `ansible/docs/evidence/lab06-provision-full.txt`
- Recap: `ok=23 changed=13 unreachable=0 failed=0`.

Normal deployment run:
- `ansible/docs/evidence/lab06-deploy-scenario1-normal.txt`
- Recap: `ok=24 changed=6 unreachable=0 failed=0 skipped=5`.

Idempotency:
- Second idempotency run recap shows `changed=0`:
  - `ansible/docs/evidence/lab06-deploy-idempotency-run2.txt`

Application checks:
- Root endpoint OK: `ansible/docs/evidence/lab06-curl-root.txt`
- Health endpoint OK: `ansible/docs/evidence/lab06-curl-health.txt`

---

## Challenges & Solutions

1. No active VM
- Problem: Original host in inventory was unreachable.
- Solution: Recreated VM via existing Terraform evidence workflow, then updated Ansible inventory.

2. Expired Yandex IAM token
- Problem: Terraform apply failed with UNAUTHENTICATED (expired token).
- Solution: Generated fresh token and used temporary `terraform/yandex/zz_runtime.auto.tfvars` override.

3. Local Ansible binary mismatch
- Problem: PATH resolved to Ansible core 2.20, which requires Python 3.9+ on target (target has 3.8.10).
- Solution: Pinned workflow/install to `ansible-core==2.18.*` and used 2.18 binary for remote runs.

4. Idempotency drift in Docker repo normalization
- Problem: stale-entry cleanup removed managed `docker.list` each run, causing repeated changes.
- Solution: excluded `/etc/apt/sources.list.d/docker.list` from stale cleanup loops and set apt cache validity window.

---

## Research Answers

### Task 1

1. What happens if rescue block also fails?
- The play fails for that host after rescue failure.

2. Can you have nested blocks?
- Yes, nested blocks are supported.

3. How do tags inherit to block tasks?
- Tags on a block are inherited by tasks in `block`, `rescue`, and `always`.

### Task 2

1. `restart: always` vs `restart: unless-stopped`
- `always`: restarts even after daemon restart regardless of previous manual stop intent.
- `unless-stopped`: does not auto-resume containers intentionally stopped by operator.

2. Compose networks vs bridge networks
- Compose creates project-scoped networks with automatic service-name DNS.
- Plain bridge networking is lower-level/manual unless configured explicitly.

3. Can Vault vars be used in templates?
- Yes. Vault values are decrypted at runtime and rendered by Jinja templates.

### Task 3

1. Why variable + tag?
- Double safety: explicit intent (`web_app_wipe=true`) + explicit execution scope (`--tags web_app_wipe`).

2. `never` tag vs this approach
- `never` is tag-only gating; variable+tag adds runtime policy guard and cleaner reinstall flow.

3. Why wipe before deploy?
- Required for deterministic clean reinstall in one playbook run.

4. Clean reinstall vs rolling update
- Clean reinstall: remove drift/corruption and redeploy from clean state.
- Rolling update: minimize downtime when state is healthy.

5. Extending wipe for images/volumes
- Add optional gated tasks (`web_app_wipe_images`, `web_app_wipe_volumes`) for `docker image rm/prune` and `docker volume rm`.

### Task 4

1. Security implications of SSH keys in GitHub Secrets
- Keys are protected at rest but exposed at runtime to jobs; enforce least privilege and environment protections.

2. Staging -> production pipeline
- Use separate inventories/environments, staged jobs, approvals, and promotion gates.

3. Rollbacks
- Keep immutable image tags and add rollback playbook/job to redeploy previous known-good tag.

4. Self-hosted vs GitHub-hosted security
- Self-hosted can keep access inside private perimeter but increases runner hardening/maintenance responsibility.

---

## Evidence Index

- `ansible/docs/evidence/lab06-ansible-lint.txt`
- `ansible/docs/evidence/lab06-ping.txt`
- `ansible/docs/evidence/lab06-provision-syntax.txt`
- `ansible/docs/evidence/lab06-deploy-syntax.txt`
- `ansible/docs/evidence/lab06-provision-list-tags.txt`
- `ansible/docs/evidence/lab06-deploy-list-tags.txt`
- `ansible/docs/evidence/lab06-provision-full.txt`
- `ansible/docs/evidence/lab06-provision-tags-docker.txt`
- `ansible/docs/evidence/lab06-provision-skip-common.txt`
- `ansible/docs/evidence/lab06-provision-tags-packages.txt`
- `ansible/docs/evidence/lab06-provision-tags-docker-check.txt`
- `ansible/docs/evidence/lab06-provision-tags-docker-install.txt`
- `ansible/docs/evidence/lab06-provision-rescue-trigger.txt`
- `ansible/docs/evidence/lab06-deploy-scenario1-normal.txt`
- `ansible/docs/evidence/lab06-deploy-idempotency-run1.txt`
- `ansible/docs/evidence/lab06-deploy-idempotency-run2.txt`
- `ansible/docs/evidence/lab06-deploy-scenario2-wipe-only.txt`
- `ansible/docs/evidence/lab06-scenario2-docker-ps.txt`
- `ansible/docs/evidence/lab06-scenario2-opt-ls.txt`
- `ansible/docs/evidence/lab06-deploy-scenario3-clean-reinstall.txt`
- `ansible/docs/evidence/lab06-deploy-scenario4a-tag-only-variable-false.txt`
- `ansible/docs/evidence/lab06-docker-compose-rendered.txt`
- `ansible/docs/evidence/lab06-curl-root.txt`
- `ansible/docs/evidence/lab06-curl-health.txt`

