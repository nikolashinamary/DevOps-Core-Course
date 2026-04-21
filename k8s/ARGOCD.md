# Lab 13: GitOps with ArgoCD - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-04-21  
**Local cluster:** `minikube` profile `lab11`  
**Helm chart:** `k8s/devops-info-service`

## 1. ArgoCD installation and access

I installed ArgoCD into a dedicated `argocd` namespace with Helm and accessed the controller through port-forwarding.

Installation flow:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd -n argocd
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

UI access:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

CLI access:

```bash
argocd login localhost:8080 --insecure
argocd app list
```

The lab environment uses a local `git daemon` on the host, exposed to the cluster through `host.docker.internal`, so ArgoCD can fetch the repo without relying on outbound GitHub access.

## 2. Application manifests

Created the following manifests:

- [`k8s/argocd/application.yaml`](/Users/marianikolashina/DevOps-Core-Course/k8s/argocd/application.yaml)
- [`k8s/argocd/application-dev.yaml`](/Users/marianikolashina/DevOps-Core-Course/k8s/argocd/application-dev.yaml)
- [`k8s/argocd/application-prod.yaml`](/Users/marianikolashina/DevOps-Core-Course/k8s/argocd/application-prod.yaml)

Common source settings:

- `repoURL`: `git://host.docker.internal:9418/DevOps-Core-Course.git`
- `targetRevision`: `lab12`
- `path`: `k8s/devops-info-service`

Destination layout:

- main app: namespace `lab13`
- dev app: namespace `dev`
- prod app: namespace `prod`

Sync policy:

- main app: manual sync, only `CreateNamespace=true`
- dev app: automated sync with `prune` and `selfHeal`
- prod app: manual sync with `CreateNamespace=true`

## 3. Multi-environment deployment

I used the existing Helm values files from Lab 12:

- `k8s/devops-info-service/values-dev.yaml`
- `k8s/devops-info-service/values-prod.yaml`

The environment-specific differences are:

- dev runs with `replicaCount: 1`, smaller requests and limits, and a `NodePort`
- prod runs with `replicaCount: 3`, larger requests and limits, and `LoadBalancer`

This keeps dev fast and cheap while leaving production changes gated behind a manual sync.

## 4. Self-healing and drift

Dev uses ArgoCD automated sync with `selfHeal: true`, so cluster drift is reverted back to the Git state.

Behavior difference:

- if Kubernetes deletes a pod, the Deployment/ReplicaSet recreates it
- if someone manually changes a tracked manifest, ArgoCD notices the drift and restores the Git-defined version

The lab default sync interval is the ArgoCD controller reconciliation cycle, which is typically about 3 minutes unless webhooks or manual sync are used.

## 5. Evidence and verification

I captured command output under:

- `k8s/evidence/lab13/`

Recommended checks:

```bash
kubectl get pods -n argocd
kubectl get applications.argoproj.io -n argocd
kubectl get pods -n dev
kubectl get pods -n prod
argocd app list
argocd app get devops-info-service-dev
argocd app get devops-info-service-prod
```

For the GitOps workflow test, I changed the Helm chart values, committed the change, and let ArgoCD detect and reconcile the drift.

## 6. Bonus: ApplicationSet

I also prepared an ApplicationSet pattern for generating the dev and prod applications from a single template. The list generator is the right fit here because the environments are known and small in number.

Use ApplicationSet when:

- you want one template to produce many similar applications
- you need consistent application metadata and destination rules
- you plan to scale the same GitOps pattern across many environments or clusters

Use separate Application manifests when:

- the environments need materially different sync policies or exceptions
- you want the configuration to stay very explicit
- the deployment surface is small

## 7. Files changed for the lab

- [`k8s/argocd/application.yaml`](/Users/marianikolashina/DevOps-Core-Course/k8s/argocd/application.yaml)
- [`k8s/argocd/application-dev.yaml`](/Users/marianikolashina/DevOps-Core-Course/k8s/argocd/application-dev.yaml)
- [`k8s/argocd/application-prod.yaml`](/Users/marianikolashina/DevOps-Core-Course/k8s/argocd/application-prod.yaml)
- [`k8s/ARGOCD.md`](/Users/marianikolashina/DevOps-Core-Course/k8s/ARGOCD.md)
