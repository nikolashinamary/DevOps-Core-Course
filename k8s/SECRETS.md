# Lab 11: Kubernetes Secrets & HashiCorp Vault - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-04-09  
**Local cluster:** `minikube` profile `lab11` with Docker driver  
**Application chart:** `k8s/devops-info-service`  
**Helm release:** `lab11-app` in namespace `lab11`  
**Vault release:** `vault` in namespace `vault`

---

## 1. Kubernetes Secrets Fundamentals

### Secret creation

I created the imperative Kubernetes Secret required by the lab in namespace `lab11`:

```bash
kubectl create secret generic app-credentials -n lab11 \
  --from-literal=username=lab11-demo \
  --from-literal=password=lab11-password
```

### Secret inspection

`kubectl get secret app-credentials -n lab11 -o yaml`:

```yaml
apiVersion: v1
data:
  password: bGFiMTEtcGFzc3dvcmQ=
  username: bGFiMTEtZGVtbw==
kind: Secret
metadata:
  name: app-credentials
  namespace: lab11
type: Opaque
```

The encoded values decode back to the original plaintext:

```bash
kubectl get secret app-credentials -n lab11 -o jsonpath='{.data.username}' | base64 -d
lab11-demo

kubectl get secret app-credentials -n lab11 -o jsonpath='{.data.password}' | base64 -d
lab11-password
```

### Base64 encoding vs encryption

- Base64 is only a transport/storage encoding. It makes binary-safe YAML/JSON fields possible, but it does not protect the value.
- Anyone who can read the Secret from the Kubernetes API can decode it immediately.
- Actual encryption at rest requires Kubernetes API server encryption configuration for etcd data.

### Security implications

Upstream Kubernetes Secrets are not meaningfully protected by base64 alone. In a default cluster, the API resource exists as ordinary Secret data unless the cluster administrator enables encryption at rest for the relevant resources.

What etcd encryption does:
- The kube-apiserver encrypts Secret data before persisting it in etcd.
- This protects against direct etcd disk/snapshot access and some backup exposure scenarios.
- It does not replace RBAC. Anyone with API permission to read a Secret can still retrieve it through Kubernetes.

When to enable it:
- In every production cluster that stores credentials, tokens, API keys, or TLS private keys in Kubernetes Secrets.
- In managed clusters whenever the platform exposes envelope/KMS-backed secret encryption.
- In self-managed clusters alongside strict RBAC, audit logging, and backup protection.

---

## 2. Helm Secret Integration

### Chart structure

I extended the Lab 10 chart with a Secret template, a ServiceAccount template for Vault auth binding, and a dedicated values file for Vault-enabled installs.

```text
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── values-vault.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── secrets.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    └── NOTES.txt
```

### Secret template

`templates/secrets.yaml` uses `stringData` so Helm values can stay readable while Kubernetes performs the base64 encoding automatically:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info-service.secretName" . }}
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
type: {{ .Values.secrets.type }}
stringData:
  username: {{ .Values.secrets.data.username | quote }}
  password: {{ .Values.secrets.data.password | quote }}
```

Default values in `values.yaml` are placeholders only:

```yaml
secrets:
  enabled: true
  type: Opaque
  nameOverride: ""
  data:
    username: "change-me"
    password: "change-me"
```

### Deployment consumption

I chose explicit `env` entries with `secretKeyRef` instead of `envFrom`. This keeps the application-facing variable names stable while still sourcing the real values from the Secret.

Shared environment variables are rendered through a named template in `_helpers.tpl`:

```yaml
{{- define "devops-info-service.commonEnv" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: APP_ENV
  value: {{ .Values.env.appEnv | quote }}
- name: APP_REVISION
  value: {{ .Values.env.appRevision | quote }}
{{- end -}}
```

Secret-backed variables are kept in a second helper:

```yaml
{{- define "devops-info-service.secretEnv" -}}
- name: APP_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-service.secretName" . }}
      key: username
- name: APP_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-service.secretName" . }}
      key: password
{{- end -}}
```

The deployment consumes both helpers:

```yaml
env:
  {{- include "devops-info-service.commonEnv" . | nindent 12 }}
  {{- if .Values.secrets.enabled }}
  {{- include "devops-info-service.secretEnv" . | nindent 12 }}
  {{- end }}
```

### Helm install and verification

I deployed the chart with development values and demo secret overrides:

```bash
helm upgrade --install lab11-app k8s/devops-info-service \
  --namespace lab11 --create-namespace \
  --wait --wait-for-jobs \
  -f k8s/devops-info-service/values-dev.yaml \
  --set-string secrets.data.username=helm-demo-user \
  --set-string secrets.data.password=helm-demo-password
```

Deployment status after install:

```text
NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab11-app-devops-info-service   1/1     1            1           25s
```

Rendered Secret stored by Kubernetes:

```yaml
apiVersion: v1
data:
  password: aGVsbS1kZW1vLXBhc3N3b3Jk
  username: aGVsbS1kZW1vLXVzZXI=
kind: Secret
metadata:
  name: lab11-app-devops-info-service-secret
  namespace: lab11
type: Opaque
```

`kubectl exec` inside the pod confirms the variables exist, but the report intentionally redacts the actual values:

```text
APP_USERNAME=<redacted>
APP_ENV=<redacted>
APP_REVISION=<redacted>
APP_PASSWORD=<redacted>
```

`kubectl describe pod lab11-app-devops-info-service-7959b766f-s278z -n lab11` proves the Secret values are not printed in plaintext:

```text
Environment:
  HOST:          0.0.0.0
  PORT:          5000
  APP_ENV:       dev
  APP_REVISION:  dev
  APP_USERNAME:  <set to the key 'username' in secret 'lab11-app-devops-info-service-secret'>  Optional: false
  APP_PASSWORD:  <set to the key 'password' in secret 'lab11-app-devops-info-service-secret'>  Optional: false
```

That satisfies the requirement to inject the secret into the workload while avoiding secret disclosure in `kubectl describe`.

---

## 3. Resource Management

The chart already had resource requests and limits from Lab 10, and I kept them configurable in values files.

`values.yaml` defaults:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

`values-dev.yaml` for the lab deployment:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Observed on the deployed workload:

```text
Limits:
  cpu:     100m
  memory:  128Mi
Requests:
  cpu:      50m
  memory:   64Mi
```

Explanation:
- Requests are the minimum resources Kubernetes uses for scheduling decisions.
- Limits are the maximum resources the container may consume before throttling or OOM handling applies.
- For this Flask service, low dev values are enough because the workload is small and only exposes `/`, `/health`, and `/metrics`.
- Production values should be chosen from real metrics: request rate, latency, memory usage during GC spikes, and rollout behavior under load.

---

## 4. Vault Integration

### Vault install

I added the official HashiCorp repository and confirmed the current chart line available locally:

```text
NAME              CHART VERSION  APP VERSION  DESCRIPTION
hashicorp/vault   0.32.0         1.21.2       Official HashiCorp Vault Chart
```

Install command used for the lab:

```bash
helm upgrade --install vault hashicorp/vault \
  --namespace vault --create-namespace \
  --wait \
  --set server.dev.enabled=true \
  --set server.dev.devRootToken=root \
  --set injector.enabled=true
```

Verification:

```text
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          16m
vault-agent-injector-8c76487db-fz798   1/1     Running   0          16m
```

### Vault configuration

I used a dedicated KV v2 mount named `apps` so the lab explicitly demonstrates enabling a secrets engine rather than relying on the dev server's default mount.

Commands executed inside `vault-0`:

```bash
vault secrets enable -path=apps kv-v2
vault kv put apps/devops-info-service/config \
  username="vault-demo-user" \
  password="vault-demo-password"
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}"
vault policy write devops-info-service /tmp/devops-info-service-policy.hcl
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names=lab11-app-devops-info-service \
  bound_service_account_namespaces=lab11 \
  policies=devops-info-service \
  ttl=1h
```

Sanitized auth config proof:

```text
Key                                  Value
---                                  -----
disable_iss_validation               true
disable_local_ca_jwt                 false
issuer                               n/a
kubernetes_ca_cert                   n/a
kubernetes_host                      https://10.96.0.1:443
pem_keys                             []
token_reviewer_jwt_set               false
use_annotations_as_alias_metadata    false
```

Policy:

```hcl
path "apps/data/devops-info-service/config" {
  capabilities = ["read"]
}
```

Role:

```text
bound_service_account_names                 [lab11-app-devops-info-service]
bound_service_account_namespaces            [lab11]
policies                                    [devops-info-service]
token_ttl                                   1h
ttl                                         1h
```

### Vault Agent injection

I upgraded the same Helm release with `values-vault.yaml`, which enables Vault annotations in the pod template:

```bash
helm upgrade lab11-app k8s/devops-info-service \
  --namespace lab11 \
  --wait --wait-for-jobs \
  -f k8s/devops-info-service/values-dev.yaml \
  -f k8s/devops-info-service/values-vault.yaml \
  --set-string secrets.data.username=helm-demo-user \
  --set-string secrets.data.password=helm-demo-password
```

The deployment template now carries these annotations:

```yaml
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/auth-type: "kubernetes"
vault.hashicorp.com/auth-path: "auth/kubernetes"
vault.hashicorp.com/role: "devops-info-service"
vault.hashicorp.com/agent-inject-secret-config-env: "apps/data/devops-info-service/config"
vault.hashicorp.com/agent-inject-template-config-env: |
  {{- with secret "apps/data/devops-info-service/config" -}}
  APP_USERNAME={{ .Data.data.username }}
  APP_PASSWORD={{ .Data.data.password }}
  {{- end }}
```

Final pod state after upgrade:

```text
NAME                                             READY   STATUS    RESTARTS   AGE
lab11-app-devops-info-service-6b7d95986d-tdkpd   2/2     Running   0          86s
```

`kubectl describe pod` shows successful mutation by the injector:

```text
Annotations:
  vault.hashicorp.com/agent-inject: true
  vault.hashicorp.com/agent-inject-status: injected
  vault.hashicorp.com/role: devops-info-service

Init Containers:
  vault-agent-init:
    State: Terminated
      Reason: Completed

Containers:
  app:
  vault-agent:

Volumes:
  vault-secrets:
    Type: EmptyDir
    Medium: Memory
```

Inside the application container, the rendered secret file exists at the expected path:

```text
$ ls -l /vault/secrets
total 4
-rw-r--r-- 1 100 1000 62 Apr  9 13:05 config-env
```

Rendered file content, redacted:

```text
APP_USERNAME=<redacted>
APP_PASSWORD=<redacted>
```

### Sidecar injection pattern

This deployment uses the standard Vault Agent Injector pattern:
- a mutating admission webhook sees the Vault annotations on the pod;
- an init container authenticates to Vault and pre-populates the shared in-memory volume;
- a long-running `vault-agent` sidecar keeps templates rendered and refreshes them when needed;
- the application container reads files from `/vault/secrets` without containing Vault credentials or Vault CLI logic itself.

---

## 5. Security Analysis

### Kubernetes Secrets vs Vault

| Aspect | Kubernetes Secret | HashiCorp Vault |
|---|---|---|
| Storage | Kubernetes API / etcd | External secret manager |
| Default protection | Base64 only, plus whatever the cluster already enforces | Authn/authz, audit, leases, policy model |
| Rotation | Manual / app-driven | Centralized, automated workflows possible |
| Blast radius | Anyone with K8s Secret read access can retrieve values | Policy can narrow access to exact paths and identities |
| Best fit | Simple internal cluster config, low complexity | Sensitive production credentials, multi-app/shared secrets, rotation-heavy environments |

### When to use each

Use Kubernetes Secrets when:
- the value is low-risk or short-lived;
- the application already only runs inside one cluster;
- operational simplicity matters more than centralized secret governance.

Use Vault when:
- secrets must be centrally managed, audited, rotated, or revoked;
- multiple workloads need different policies against the same secret platform;
- you want to avoid storing the real secret material in Git and reduce long-lived Kubernetes Secret usage.

### Production recommendations

- Never commit real credentials to `values.yaml`; use placeholders and inject real values at deploy time.
- Enable encryption at rest for Secrets in Kubernetes.
- Restrict Secret reads with RBAC and namespace boundaries.
- Prefer dedicated service accounts per workload.
- For production Vault, do not use dev mode. Use HA storage, TLS, backups, unseal strategy, and audited auth methods.
- Prefer short-lived credentials and dynamic secrets where possible.

---

## 6. Bonus - Vault Agent Templates

### Template annotation implemented

The chart implements `vault.hashicorp.com/agent-inject-template-config-env` and renders multiple fields into one `.env`-style file:

```text
APP_USERNAME=...
APP_PASSWORD=...
```

### Named templates in Helm

The chart now uses named templates in `_helpers.tpl`:
- `devops-info-service.commonEnv`
- `devops-info-service.secretEnv`
- `devops-info-service.vaultAgentTemplate`

This keeps the Deployment manifest smaller and avoids repeating the same environment-variable blocks inline.

### Rotation and post-render command

Vault Agent refresh behavior:
- leased/dynamic secrets are renewed or re-fetched according to lease semantics;
- non-leased static secrets such as KV v2 are re-rendered on Vault Agent's static secret render interval;
- the injector also supports `vault.hashicorp.com/template-static-secret-render-interval` when that refresh interval needs to be tuned.

`vault.hashicorp.com/agent-inject-command-SECRET-NAME` can run an application-specific action after a template is rendered. Typical uses:
- `kill -HUP` to reload a process;
- copying or reformatting a rendered file;
- touching a marker file for a sidecar/process supervisor.

The chart exposes this as `vault.injectCommand`; if populated, it emits:

```yaml
vault.hashicorp.com/agent-inject-command-config-env: "<command>"
```

I left it disabled by default because this Flask lab application does not need runtime reload hooks.

---

## References

- Kubernetes Secrets: https://kubernetes.io/docs/concepts/configuration/secret/
- Kubernetes encryption at rest: https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- Vault Helm chart: https://developer.hashicorp.com/vault/docs/platform/k8s/helm
- Vault injector annotations: https://developer.hashicorp.com/vault/docs/deploy/kubernetes/injector/annotations
- Vault Agent templates: https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent/template
