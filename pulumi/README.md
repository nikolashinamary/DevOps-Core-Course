# Pulumi Lab04 Starter

This folder contains a Python Pulumi stack that mirrors the Yandex VM infrastructure used in Terraform.

## Setup

```bash
cd pulumi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pulumi login
pulumi stack init dev
```

## Required Config

```bash
pulumi config set yandex:cloudId "<cloud-id>"
pulumi config set yandex:folderId "<folder-id>"
pulumi config set --secret yandex:token "<iam-token>"

pulumi config set app:sshPublicKey "ssh-rsa AAAA... user@example.com"
pulumi config set app:sshUsername "ubuntu"
pulumi config set app:zone "ru-central1-a"
```

Optional defaults (if needed):

```bash
pulumi config set app:vmName "pulumi-vm"
pulumi config set app:networkName "pulumi-network"
pulumi config set app:subnetName "pulumi-subnet"
pulumi config set app:subnetCidr "192.168.20.0/24"
pulumi config set app:imageId "fd865v46cboopthn7u0k"
pulumi config set app:sshAllowedCidr "203.0.113.5/32"
pulumi config set app:cores 2
pulumi config set app:memoryGb 1
pulumi config set app:coreFraction 20
pulumi config set app:diskSizeGb 10
pulumi config set app:preemptible true
```

## Commands

```bash
pulumi preview
pulumi up
pulumi stack output
pulumi destroy
```
