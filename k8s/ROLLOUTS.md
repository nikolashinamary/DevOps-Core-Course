# Lab 14: Argo Rollouts - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-04-21  
**Cluster:** `minikube` on context `lab11`

## 1. Setup

I installed Argo Rollouts into the dedicated `argo-rollouts` namespace and verified both the controller and the dashboard.

Controller install:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Dashboard install:

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Dashboard proof:

- [`k8s/evidence/lab14/dashboard-root.html`](k8s/evidence/lab14/dashboard-root.html)

Notes:

- The controller and dashboard are both running in `argo-rollouts`.
- The dashboard is reachable on `http://127.0.0.1:3100`.
- The standalone `kubectl-argo-rollouts` binary was not used for the final rollout operations in this sandbox; I exercised the same CRD behavior directly with `kubectl` patches and verified the results in the dashboard/controller state.

## 2. Canary Deployment

The chart now renders a `Rollout` when `rollout.enabled=true`.

Canary configuration:

- `setWeight: 20`
- indefinite pause for manual gate
- analysis step against the app root endpoint
- `setWeight: 40`
- `setWeight: 60`
- `setWeight: 80`
- `setWeight: 100`

The analysis template checks the JSON field `$.service.environment` and compares it to the expected environment value.

Relevant files:

- [`k8s/devops-info-service/templates/rollout.yaml`](k8s/devops-info-service/templates/rollout.yaml)
- [`k8s/devops-info-service/templates/analysis.yaml`](k8s/devops-info-service/templates/analysis.yaml)
- [`k8s/devops-info-service/values-lab14-canary.yaml`](k8s/devops-info-service/values-lab14-canary.yaml)
- [`k8s/devops-info-service/values-lab14-canary-fail.yaml`](k8s/devops-info-service/values-lab14-canary-fail.yaml)

Canary evidence:

- [`k8s/evidence/lab14/canary-final-root.txt`](k8s/evidence/lab14/canary-final-root.txt)
- [`k8s/evidence/lab14/canary-final-health.txt`](k8s/evidence/lab14/canary-final-health.txt)
- [`k8s/evidence/lab14/canary-rollout-final.txt`](k8s/evidence/lab14/canary-rollout-final.txt)
- [`k8s/evidence/lab14/canary-analysis-final.txt`](k8s/evidence/lab14/canary-analysis-final.txt)

What I verified:

- the rollout paused at the first gate
- the analysis step succeeded on the v2 update
- the rollout converged back to a healthy stable state
- a failing v3 revision produced a `Failed` AnalysisRun and the rollout returned to the stable version

## 3. Blue-Green Deployment

Blue-green uses:

- an active service
- a preview service
- `autoPromotionEnabled: false` initially

Relevant files:

- [`k8s/devops-info-service/templates/service-preview.yaml`](k8s/devops-info-service/templates/service-preview.yaml)
- [`k8s/devops-info-service/values-lab14-bluegreen.yaml`](k8s/devops-info-service/values-lab14-bluegreen.yaml)

Blue-green evidence:

- [`k8s/evidence/lab14/bluegreen-active-root.txt`](k8s/evidence/lab14/bluegreen-active-root.txt)
- [`k8s/evidence/lab14/bluegreen-preview-root.txt`](k8s/evidence/lab14/bluegreen-preview-root.txt)
- [`k8s/evidence/lab14/bluegreen-active-post-root.txt`](k8s/evidence/lab14/bluegreen-active-post-root.txt)
- [`k8s/evidence/lab14/bluegreen-rollback-post-root.txt`](k8s/evidence/lab14/bluegreen-rollback-post-root.txt)
- [`k8s/evidence/lab14/bluegreen-services-final.txt`](k8s/evidence/lab14/bluegreen-services-final.txt)
- [`k8s/evidence/lab14/bluegreen-rollout-final.txt`](k8s/evidence/lab14/bluegreen-rollout-final.txt)

What I verified:

- the preview service pointed at the new ReplicaSet before promotion
- the active service was cut over to the new ReplicaSet
- rollback switched the active service back to the stable version

## 4. Strategy Comparison

Canary:

- best when you want gradual exposure and can tolerate a short mixed-version window
- lower blast radius
- slower to complete
- better for riskier application changes and metric-driven validation

Blue-green:

- best when you want a quick switch between two complete stacks
- instant promotion and rollback semantics
- needs extra capacity for the preview stack
- better for releases where you want a clear active/preview split

My recommendation:

- use canary for high-risk application changes and when you need progressive confidence
- use blue-green for fast switchovers, low-downtime cutovers, and simple rollback

## 5. CLI Reference

Controller and dashboard:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Rollout inspection:

```bash
kubectl get rollout -n lab14-canary
kubectl get rollout -n lab14-bluegreen
kubectl get analysisrun -n lab14-canary
kubectl get pods -n lab14-canary
kubectl get pods -n lab14-bluegreen
kubectl get svc -n lab14-bluegreen
```

Common rollout actions:

```bash
kubectl patch rollout <name> -n <namespace> --type merge -p '{"spec":{"paused":false}}'
kubectl patch rollout <name> -n <namespace> --type json -p='[...]'
kubectl patch svc <name> -n <namespace> --type json -p='[...]'
```

## 6. Bonus: Analysis Template

I added an `AnalysisTemplate` named `environment-match`.

It checks:

- the app root endpoint returns JSON
- `$.service.environment` matches the expected environment

Bonus evidence:

- [`k8s/evidence/lab14/canary-analysis-final.txt`](k8s/evidence/lab14/canary-analysis-final.txt)

Result:

- a bad v3 canary revision produced a `Failed` analysis run
- the rollout was restored to the stable version afterward

## 7. Files Changed

- [`k8s/devops-info-service/templates/deployment.yaml`](k8s/devops-info-service/templates/deployment.yaml)
- [`k8s/devops-info-service/templates/rollout.yaml`](k8s/devops-info-service/templates/rollout.yaml)
- [`k8s/devops-info-service/templates/service-preview.yaml`](k8s/devops-info-service/templates/service-preview.yaml)
- [`k8s/devops-info-service/templates/analysis.yaml`](k8s/devops-info-service/templates/analysis.yaml)
- [`k8s/devops-info-service/templates/_helpers.tpl`](k8s/devops-info-service/templates/_helpers.tpl)
- [`k8s/devops-info-service/values.yaml`](k8s/devops-info-service/values.yaml)
- [`k8s/devops-info-service/values-lab14-canary.yaml`](k8s/devops-info-service/values-lab14-canary.yaml)
- [`k8s/devops-info-service/values-lab14-canary-fail.yaml`](k8s/devops-info-service/values-lab14-canary-fail.yaml)
- [`k8s/devops-info-service/values-lab14-bluegreen.yaml`](k8s/devops-info-service/values-lab14-bluegreen.yaml)
- [`k8s/ROLLOUTS.md`](k8s/ROLLOUTS.md)
