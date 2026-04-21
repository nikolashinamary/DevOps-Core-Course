#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${ROOT_DIR}/docs/lab04-evidence"
TERRAFORM_YANDEX_DIR="${ROOT_DIR}/terraform/yandex"
TERRAFORM_DOCKER_DIR="${ROOT_DIR}/terraform/docker"
TERRAFORM_GITHUB_DIR="${ROOT_DIR}/terraform/github"
PULUMI_DIR="${ROOT_DIR}/pulumi"

mkdir -p "${EVIDENCE_DIR}"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Error: required command '$1' is not installed." >&2
    exit 1
  }
}

terraform_cmd() {
  local cli_cfg=""

  if [[ -n "${TF_CLI_CONFIG_FILE:-}" ]]; then
    if [[ ! -f "${TF_CLI_CONFIG_FILE}" ]]; then
      echo "Error: TF_CLI_CONFIG_FILE points to a missing file: ${TF_CLI_CONFIG_FILE}" >&2
      exit 1
    fi
    cli_cfg="${TF_CLI_CONFIG_FILE}"
  elif [[ -f "${ROOT_DIR}/terraformrc.yandex" ]]; then
    cli_cfg="${ROOT_DIR}/terraformrc.yandex"
  elif [[ -f "${HOME}/.terraformrc" ]]; then
    cli_cfg="${HOME}/.terraformrc"
  fi

  if [[ -n "${cli_cfg}" ]]; then
    TF_CLI_CONFIG_FILE="${cli_cfg}" terraform "$@"
  else
    terraform "$@"
  fi
}

show_terraform_cli_config() {
  if [[ -n "${TF_CLI_CONFIG_FILE:-}" ]]; then
    log "Terraform CLI config (env): ${TF_CLI_CONFIG_FILE}"
    return
  fi
  if [[ -f "${ROOT_DIR}/terraformrc.yandex" ]]; then
    log "Terraform CLI config (project): ${ROOT_DIR}/terraformrc.yandex"
    return
  fi
  if [[ -f "${HOME}/.terraformrc" ]]; then
    log "Terraform CLI config (home): ${HOME}/.terraformrc"
    return
  fi
  log "Terraform CLI config: default"
}

pulumi_backend_login() {
  if [[ -z "${PULUMI_HOME:-}" ]]; then
    export PULUMI_HOME="${ROOT_DIR}/.pulumi-home"
  fi
  mkdir -p "${PULUMI_HOME}"

  if [[ -z "${PULUMI_CONFIG_PASSPHRASE:-}" && -z "${PULUMI_CONFIG_PASSPHRASE_FILE:-}" ]]; then
    export PULUMI_CONFIG_PASSPHRASE="${PULUMI_DEFAULT_PASSPHRASE:-lab04-local-passphrase}"
    log "Pulumi passphrase: using local default (set PULUMI_CONFIG_PASSPHRASE to override)"
  fi

  local backend_url="${PULUMI_BACKEND_URL:-file://${ROOT_DIR}/.pulumi-local-backend}"
  if [[ "${backend_url}" == file://* ]]; then
    mkdir -p "${backend_url#file://}"
  fi

  log "Pulumi home: ${PULUMI_HOME}"
  log "Pulumi backend: ${backend_url}"
  pulumi login "${backend_url}" >/dev/null
}

ensure_pulumi_stack() {
  local stack_name="${PULUMI_STACK:-dev}"
  if pulumi stack select "${stack_name}" >/dev/null 2>&1; then
    log "Pulumi stack selected: ${stack_name}"
  else
    log "Pulumi stack init: ${stack_name}"
    pulumi stack init "${stack_name}" | tee "${EVIDENCE_DIR}/pulumi-stack-init.txt"
  fi
}

set_pulumi_config_if_missing() {
  local key="$1"
  local value="$2"
  local secret="${3:-false}"

  if pulumi config get "${key}" >/dev/null 2>&1; then
    return
  fi
  if [[ -z "${value}" ]]; then
    return
  fi

  if [[ "${secret}" == "true" ]]; then
    pulumi config set --secret "${key}" "${value}" >/dev/null
  else
    pulumi config set "${key}" "${value}" >/dev/null
  fi
  log "Pulumi config set: ${key}"
}

ensure_pulumi_config() {
  local cloud_id=""
  local folder_id=""
  local yc_token=""
  local ssh_pub=""
  local my_ip=""

  if command -v yc >/dev/null 2>&1; then
    cloud_id="$(yc config get cloud-id 2>/dev/null || true)"
    folder_id="$(yc config get folder-id 2>/dev/null || true)"
    yc_token="$(yc iam create-token 2>/dev/null || true)"
  fi

  if [[ -f "${HOME}/.ssh/id_ed25519.pub" ]]; then
    ssh_pub="$(cat "${HOME}/.ssh/id_ed25519.pub")"
  fi

  if command -v curl >/dev/null 2>&1; then
    my_ip="$(curl -4 -s --max-time 5 ifconfig.me 2>/dev/null || true)"
  fi

  set_pulumi_config_if_missing "yandex:cloudId" "${cloud_id}"
  set_pulumi_config_if_missing "yandex:folderId" "${folder_id}"
  set_pulumi_config_if_missing "yandex:token" "${yc_token}" "true"
  set_pulumi_config_if_missing "app:sshPublicKey" "${ssh_pub}"
  set_pulumi_config_if_missing "app:sshUsername" "ubuntu"
  set_pulumi_config_if_missing "app:zone" "ru-central1-a"

  if [[ -n "${my_ip}" ]]; then
    set_pulumi_config_if_missing "app:sshAllowedCidr" "${my_ip}/32"
  fi

  if ! pulumi config get yandex:cloudId >/dev/null 2>&1 \
    || ! pulumi config get yandex:folderId >/dev/null 2>&1 \
    || ! pulumi config get yandex:token >/dev/null 2>&1 \
    || ! pulumi config get app:sshPublicKey >/dev/null 2>&1; then
    cat >&2 <<'ERR'
Error: missing required Pulumi config.
Run these commands in ./pulumi (with stack selected):
  pulumi config set yandex:cloudId "<cloud-id>"
  pulumi config set yandex:folderId "<folder-id>"
  pulumi config set --secret yandex:token "<iam-token>"
  pulumi config set app:sshPublicKey "$(cat ~/.ssh/id_ed25519.pub)"
ERR
    exit 1
  fi
}

select_pulumi_python() {
  if [[ -n "${PULUMI_PYTHON:-}" ]]; then
    echo "${PULUMI_PYTHON}"
    return
  fi

  if command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
    return
  fi
  if command -v python3.11 >/dev/null 2>&1; then
    echo "python3.11"
    return
  fi
  if command -v python3.10 >/dev/null 2>&1; then
    echo "python3.10"
    return
  fi
  echo "python3"
}

ensure_pulumi_venv() {
  local py_cmd
  py_cmd="$(select_pulumi_python)"
  require_cmd "${py_cmd}"

  local recreate="false"
  if [[ -d venv ]]; then
    local venv_ver
    venv_ver="$(venv/bin/python -c 'import sys; print(f\"{sys.version_info[0]}.{sys.version_info[1]}\")' 2>/dev/null || true)"
    if [[ -n "${venv_ver}" ]]; then
      log "Pulumi venv python: ${venv_ver}"
      if [[ "${venv_ver}" == 3.13 || "${venv_ver}" == 3.14 || "${venv_ver}" == 3.15 ]]; then
        recreate="true"
      fi
    else
      recreate="true"
    fi
  fi

  if [[ ! -d venv || "${recreate}" == "true" ]]; then
    if [[ "${recreate}" == "true" ]]; then
      log "Pulumi: recreating venv with ${py_cmd} (existing venv is incompatible)"
      rm -rf venv
    else
      log "Pulumi: creating venv with ${py_cmd}"
    fi
    "${py_cmd}" -m venv venv
  fi

  # shellcheck disable=SC1091
  source venv/bin/activate
  python --version | tee "${EVIDENCE_DIR}/pulumi-python-version.txt"
}

run_terraform_yandex() {
  require_cmd terraform
  require_cmd ssh

  cd "${TERRAFORM_YANDEX_DIR}"
  show_terraform_cli_config
  log "Terraform (yandex): init"
  terraform_cmd init -no-color -input=false | tee "${EVIDENCE_DIR}/tf-init.txt"

  log "Terraform (yandex): fmt"
  terraform_cmd fmt -recursive | tee "${EVIDENCE_DIR}/tf-fmt.txt"

  log "Terraform (yandex): validate"
  terraform_cmd validate -no-color | tee "${EVIDENCE_DIR}/tf-validate.txt"

  log "Terraform (yandex): plan"
  terraform_cmd plan -no-color -out=tfplan | tee "${EVIDENCE_DIR}/tf-plan.txt"

  log "Terraform (yandex): apply"
  terraform_cmd apply -no-color -auto-approve tfplan | tee "${EVIDENCE_DIR}/tf-apply.txt"

  log "Terraform (yandex): output"
  terraform_cmd output -no-color | tee "${EVIDENCE_DIR}/tf-output.txt"

  local ip
  ip="$(terraform_cmd output -raw external_ip)"
  local ssh_user="${SSH_USER:-ubuntu}"

  log "Terraform (yandex): ssh proof"
  ssh -o StrictHostKeyChecking=accept-new "${ssh_user}@${ip}" \
    "hostname; uptime; free -h" \
    | tee "${EVIDENCE_DIR}/tf-ssh-proof.txt"

  log "Terraform (yandex) evidence completed"
}

run_terraform_yandex_destroy() {
  require_cmd terraform
  cd "${TERRAFORM_YANDEX_DIR}"
  show_terraform_cli_config
  log "Terraform (yandex): destroy"
  terraform_cmd destroy -no-color -auto-approve | tee "${EVIDENCE_DIR}/tf-destroy.txt"
}

run_terraform_docker_destroy() {
  require_cmd terraform
  cd "${TERRAFORM_DOCKER_DIR}"
  show_terraform_cli_config
  log "Terraform (docker): destroy"
  terraform_cmd destroy -no-color -auto-approve | tee "${EVIDENCE_DIR}/tf-docker-destroy.txt"
}

run_pulumi() {
  require_cmd pulumi
  require_cmd ssh

  cd "${PULUMI_DIR}"
  ensure_pulumi_venv
  log "Pulumi: install dependencies"
  pip install --upgrade pip "setuptools<81.0.0" wheel | tee "${EVIDENCE_DIR}/pulumi-pip-bootstrap.txt"
  pip install -r requirements.txt | tee "${EVIDENCE_DIR}/pulumi-pip-install.txt"

  pulumi_backend_login
  ensure_pulumi_stack
  ensure_pulumi_config

  log "Pulumi: preview"
  pulumi preview --non-interactive | tee "${EVIDENCE_DIR}/pulumi-preview.txt"

  log "Pulumi: up"
  pulumi up --yes --non-interactive | tee "${EVIDENCE_DIR}/pulumi-up.txt"

  log "Pulumi: stack output"
  pulumi stack output | tee "${EVIDENCE_DIR}/pulumi-output.txt"

  local ip
  ip="$(pulumi stack output externalIp)"
  local ssh_user
  ssh_user="$(pulumi config get app:sshUsername 2>/dev/null || echo ubuntu)"

  log "Pulumi: ssh proof"
  ssh -o StrictHostKeyChecking=accept-new "${ssh_user}@${ip}" \
    "hostname; uptime; free -h" \
    | tee "${EVIDENCE_DIR}/pulumi-ssh-proof.txt"

  log "Pulumi evidence completed"
}

run_pulumi_destroy() {
  require_cmd pulumi
  cd "${PULUMI_DIR}"
  ensure_pulumi_venv

  pulumi_backend_login
  ensure_pulumi_stack
  ensure_pulumi_config

  log "Pulumi: destroy"
  pulumi destroy --yes --non-interactive | tee "${EVIDENCE_DIR}/pulumi-destroy.txt"
}

run_bonus_import() {
  require_cmd terraform
  cd "${TERRAFORM_GITHUB_DIR}"
  show_terraform_cli_config

  log "Terraform (github): init"
  terraform_cmd init -no-color -input=false | tee "${EVIDENCE_DIR}/gh-init.txt"

  log "Terraform (github): validate"
  terraform_cmd validate -no-color | tee "${EVIDENCE_DIR}/gh-validate.txt"

  if [[ -z "${IMPORT_REPO_ID:-}" ]]; then
    echo "Error: set IMPORT_REPO_ID env var, example: IMPORT_REPO_ID=DevOps-Core-Course" >&2
    exit 1
  fi

  log "Terraform (github): import ${IMPORT_REPO_ID}"
  terraform_cmd import "github_repository.repo" "${IMPORT_REPO_ID}" | tee "${EVIDENCE_DIR}/gh-import.txt"

  log "Terraform (github): plan after import"
  terraform_cmd plan -no-color | tee "${EVIDENCE_DIR}/gh-plan-after-import.txt"

  log "Terraform (github): output"
  terraform_cmd output -no-color | tee "${EVIDENCE_DIR}/gh-output.txt"
}

usage() {
  cat <<USAGE
Usage: $(basename "$0") <command>

Commands:
  terraform          Run Terraform Yandex init/plan/apply/output + SSH proof
  pulumi             Run Pulumi preview/up/output + SSH proof
  bonus              Run GitHub import flow (requires IMPORT_REPO_ID env var)
  cleanup-terraform  Destroy terraform/yandex resources
  cleanup-docker     Destroy terraform/docker resources
  cleanup-pulumi     Destroy Pulumi resources

Examples:
  $(basename "$0") terraform
  SSH_USER=ubuntu $(basename "$0") terraform
  $(basename "$0") pulumi
  IMPORT_REPO_ID=DevOps-Core-Course $(basename "$0") bonus
USAGE
}

main() {
  if [[ $# -ne 1 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    terraform)
      run_terraform_yandex
      ;;
    pulumi)
      run_pulumi
      ;;
    bonus)
      run_bonus_import
      ;;
    cleanup-terraform)
      run_terraform_yandex_destroy
      ;;
    cleanup-docker)
      run_terraform_docker_destroy
      ;;
    cleanup-pulumi)
      run_pulumi_destroy
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
