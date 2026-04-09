# Lab 10: Helm Package Manager - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-03-28  
**Local cluster:** `minikube` profile `lab10` with Docker driver  
**Chart path:** `k8s/devops-info-service`

---

## 1. Chart Overview

I converted the Lab 9 Python application manifests into a reusable Helm application chart.

```text
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── NOTES.txt
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

Key template files:
- `templates/_helpers.tpl`: shared naming and label helpers.
- `templates/deployment.yaml`: templated Deployment with replica count, image, resources, env vars, and startup/readiness/liveness probes.
- `templates/service.yaml`: templated Service with configurable type, ports, and optional `nodePort`.
- `templates/hooks/pre-install-job.yaml`: validation Job executed before install.
- `templates/hooks/post-install-job.yaml`: smoke-test Job executed after install.
- `templates/NOTES.txt`: post-install access instructions.

Values organization strategy:
- `values.yaml` keeps the default local/lab-friendly configuration.
- `values-dev.yaml` reduces replicas/resources and keeps `NodePort`.
- `values-prod.yaml` raises replicas/resources and switches the Service to `LoadBalancer`.
- Probe settings stay enabled in all environments and are configurable from values.

---

## 2. Helm Fundamentals

### Why Helm

Helm makes the Lab 9 manifests reusable by turning static YAML into parameterized templates. The main value is:
- one chart can represent dev and prod with different values files;
- upgrades and rollbacks are tracked as release revisions;
- hooks let me run validation and smoke-test steps as part of the release lifecycle;
- labels, names, and common metadata stay consistent through helper templates.

### Helm installation

Local Helm version:

```text
$ helm version --template='{{.Version}}\n'
v4.1.3
```

### Public chart exploration

The sandboxed local Helm client could not resolve public chart repositories directly:

```text
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
Error: looks like "https://prometheus-community.github.io/helm-charts" is not a valid chart repository or cannot be reached: Get "https://prometheus-community.github.io/helm-charts/index.yaml": dial tcp: lookup prometheus-community.github.io: no such host
```

To still inspect a real public chart from this environment, I used a Dockerized Helm client:

```text
$ docker run --rm alpine/helm:4.1.3 show chart oci://registry-1.docker.io/bitnamicharts/nginx
Pulled: registry-1.docker.io/bitnamicharts/nginx:22.6.10
apiVersion: v2
appVersion: 1.29.7
dependencies:
- name: common
  repository: oci://registry-1.docker.io/bitnamicharts
  version: 2.37.0
description: NGINX Open Source is a web server that can be also used as a reverse proxy, load balancer, and HTTP cache.
name: nginx
version: 22.6.10
```

That confirmed the expected public chart structure: metadata in `Chart.yaml`, app version separate from chart version, and dependency support.

---

## 3. Configuration Guide

Important values:
- `replicaCount`: number of application pods.
- `image.repository`, `image.tag`, `image.pullPolicy`: application image settings.
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`: service exposure.
- `resources.requests` and `resources.limits`: CPU and memory sizing.
- `env.*`: runtime environment variables passed into the Flask container.
- `startupProbe`, `readinessProbe`, `livenessProbe`: health-check tuning.
- `hooks.*`: hook enablement, weights, deletion policy, and observation delay.

Default values keep the Lab 9 behavior:
- image `devops-info-service-python:lab10`
- 3 replicas
- `NodePort` service on `30080`
- the same `/health` endpoint for all probes

### Environment overrides

`values-dev.yaml`
- `replicaCount: 1`
- relaxed CPU/memory requests and limits
- `service.type: NodePort`
- `APP_ENV=dev`, `APP_REVISION=dev`
- faster probe timings

`values-prod.yaml`
- `replicaCount: 3`
- higher CPU/memory requests and limits
- `service.type: LoadBalancer`
- `APP_ENV=prod`, `APP_REVISION=prod`
- slower liveness/readiness timings

### Example commands

```bash
# Render development settings
helm template dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# Install development release
helm install lab10-app k8s/devops-info-service \
  --namespace lab10 --create-namespace \
  -f k8s/devops-info-service/values-dev.yaml

# Upgrade the same release to production settings
helm upgrade lab10-app k8s/devops-info-service \
  --namespace lab10 \
  -f k8s/devops-info-service/values-prod.yaml
```

---

## 4. Hook Implementation

I implemented two Jobs in `templates/hooks/`:

### Pre-install hook
- Resource: `Job`
- Annotation: `helm.sh/hook: pre-install`
- Weight: `-5`
- Purpose: print the target namespace, image, and requested replica count before resources are created

### Post-install hook
- Resource: `Job`
- Annotation: `helm.sh/hook: post-install`
- Weight: `5`
- Purpose: call `http://<service-name>:80/health` from inside the cluster and print the JSON response

### Deletion policy

Both Jobs use:

```text
helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
```

This means:
- any previous hook resource is removed before a new hook is created;
- successful Jobs are automatically deleted after completion.

I intentionally used the application image itself for the hook Jobs so the chart does not depend on pulling `busybox` or another external image during installation.

---

## 5. Installation Evidence

### Cluster and image preparation

```bash
minikube start --profile lab10 --driver=docker --cpus=2 --memory=4096
docker build -t devops-info-service-python:lab10 app_python
minikube image load devops-info-service-python:lab10 -p lab10
```

### Lint and render validation

```text
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

`helm template` rendered the expected dev resources: one Deployment, one Service, and two hook Jobs.

`helm install --dry-run=client --debug` also showed both hook manifests before install:

```text
NAME: lab10-devcheck
NAMESPACE: lab10
STATUS: pending-install
DESCRIPTION: Dry run complete

HOOKS:
- lab10-devcheck-devops-info-service-post-install
- lab10-devcheck-devops-info-service-pre-install
```

### Development install

Real install with dev values:

```text
$ helm install lab10-app k8s/devops-info-service --namespace lab10 --create-namespace --wait --wait-for-jobs -f k8s/devops-info-service/values-dev.yaml
NAME: lab10-app
LAST DEPLOYED: Sat Mar 28 21:11:29 2026
NAMESPACE: lab10
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

The release was later upgraded to prod, so the install is now visible in history as revision 1:

```text
$ helm history lab10-app -n lab10
REVISION  UPDATED                  STATUS      CHART                     APP VERSION  DESCRIPTION
1         Sat Mar 28 21:11:29 2026 superseded  devops-info-service-0.1.0 1.0.0        Install complete
2         Sat Mar 28 21:19:01 2026 deployed    devops-info-service-0.1.0 1.0.0        Upgrade complete
```

### Hook execution evidence

To capture hook lifecycle details before automatic deletion, I performed a temporary observation install in namespace `lab10-hooks`.

`kubectl get jobs -w -n lab10-hooks` output:

```text
NAME                                            STATUS               COMPLETIONS   DURATION   AGE
lab10-observe-devops-info-service-pre-install   Running              0/1                      0s
lab10-observe-devops-info-service-pre-install   Complete             1/1           23s        23s
lab10-observe-devops-info-service-post-install  Running              0/1                      0s
lab10-observe-devops-info-service-post-install  Complete             1/1           24s        24s
```

`kubectl describe job lab10-observe-devops-info-service-pre-install -n lab10-hooks`:

```text
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Command:
  python
  -u
  -c
  import time
  print("Preparing release lab10-observe")
  print("Namespace: lab10-hooks")
  print("Image: devops-info-service-python:lab10")
  print("Replicas: 1")
  time.sleep(20)
  print("Pre-install validation passed")
```

`kubectl describe job lab10-observe-devops-info-service-post-install -n lab10-hooks`:

```text
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: 5
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Command:
  python
  -u
  -c
  import time
  import urllib.request
  response = urllib.request.urlopen(
      "http://lab10-observe-devops-info-service:80/health",
      timeout=5,
  )
  print(response.read().decode())
  time.sleep(20)
  print("Post-install smoke test passed")
```

Live post-install smoke-test output:

```json
{"status":"healthy","timestamp":"2026-03-28T18:18:05.831613+00:00","uptime_seconds":3}
```

Deletion policy verification after hook completion:

```text
$ kubectl get jobs -n lab10-hooks
No resources found in lab10-hooks namespace.
```

### Production upgrade

Upgrade command:

```text
$ helm upgrade lab10-app k8s/devops-info-service --namespace lab10 --wait -f k8s/devops-info-service/values-prod.yaml
Release "lab10-app" has been upgraded. Happy Helming!
NAME: lab10-app
LAST DEPLOYED: Sat Mar 28 21:19:01 2026
NAMESPACE: lab10
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

Final release list:

```text
$ helm list -n lab10
NAME       NAMESPACE  REVISION  UPDATED                              STATUS    CHART                     APP VERSION
lab10-app  lab10      2         2026-03-28 21:19:01.082254 +0300 MSK deployed  devops-info-service-0.1.0 1.0.0
```

Final cluster state:

```text
$ kubectl get all -n lab10
NAME                                                 READY   STATUS        RESTARTS   AGE
pod/lab10-app-devops-info-service-b7db974b7-j2xv6    1/1     Running       0          22s
pod/lab10-app-devops-info-service-b7db974b7-mx2s6    1/1     Running       0          33s
pod/lab10-app-devops-info-service-b7db974b7-tsdfp    1/1     Running       0          43s

NAME                                    TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab10-app-devops-info-service   LoadBalancer   10.106.244.19   <pending>     80:30080/TCP   8m7s

NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-app-devops-info-service   3/3     3            3           8m7s
```

`EXTERNAL-IP` stayed `<pending>` because I did not start `minikube tunnel`, but the chart did switch correctly from `NodePort` in dev to `LoadBalancer` in prod.

Computed prod values:

```text
env:
  appEnv: prod
  appRevision: prod
replicaCount: 3
service:
  type: LoadBalancer
resources:
  requests:
    cpu: 150m
    memory: 192Mi
  limits:
    cpu: 300m
    memory: 384Mi
```

---

## 6. Operations

Commands used most often:

```bash
# Validate
helm lint k8s/devops-info-service
helm template dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
helm install --dry-run=client --debug lab10-devcheck k8s/devops-info-service --namespace lab10 -f k8s/devops-info-service/values-dev.yaml

# Install dev
helm install lab10-app k8s/devops-info-service \
  --namespace lab10 --create-namespace \
  --wait --wait-for-jobs \
  -f k8s/devops-info-service/values-dev.yaml

# Upgrade to prod
helm upgrade lab10-app k8s/devops-info-service \
  --namespace lab10 \
  --wait \
  -f k8s/devops-info-service/values-prod.yaml

# Inspect
helm list -n lab10
helm history lab10-app -n lab10
helm get values lab10-app -n lab10 --all
kubectl get all -n lab10

# Roll back to the dev revision if needed
helm rollback lab10-app 1 -n lab10

# Uninstall
helm uninstall lab10-app -n lab10
```

---

## 7. Testing & Validation

Validation summary:
- `helm lint` passed with 0 failures.
- `helm template` rendered the Deployment, Service, and both hook Jobs.
- `helm install --dry-run=client --debug` showed the rendered hook order and computed values.
- real `helm install` succeeded for dev settings;
- real `helm upgrade` succeeded for prod settings;
- `helm history` shows revision `1` for install and revision `2` for upgrade;
- the post-install hook successfully called `/health` through the in-cluster Service;
- `kubectl get jobs` confirmed the hook Jobs were deleted after success.

Bonus library chart task was intentionally not implemented.
