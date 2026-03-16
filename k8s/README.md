# Lab 09: Kubernetes Fundamentals - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-03-16  
**Chosen local cluster:** `minikube` with Docker driver  
**Why this tool:** the lab allows `minikube` or `kind`, and `minikube` provides a straightforward local Kubernetes cluster plus `minikube service --url` for NodePort access on macOS.

---

## 1. Architecture Overview

The main application is deployed into a dedicated namespace and exposed through a NodePort Service.

```text
                        +------------------------------+
                        | minikube cluster: lab09      |
                        | 1 control-plane node         |
                        +---------------+--------------+
                                        |
                         NodePort 80 -> 30080
                                        |
                              +---------v---------+
                              | Service           |
                              | devops-info-service
                              +---------+---------+
                                        |
                     selector app.kubernetes.io/name=devops-info-service
                                        |
         +------------------------------+------------------------------+
         |                              |                              |
+--------v---------+          +---------v--------+           +---------v--------+
| Pod replica 1    |          | Pod replica 2    |           | Pod replica 3    |
| Flask app :5000  |          | Flask app :5000  |           | Flask app :5000  |
| readiness/liveness|         | readiness/liveness|          | readiness/liveness|
+------------------+          +------------------+           +------------------+
```

Resource allocation strategy:
- Requests: `100m CPU`, `128Mi memory`
- Limits: `250m CPU`, `256Mi memory`
- Rationale: low baseline for a simple Flask service, but enough headroom for probe checks and short bursts during rollouts.

Bonus architecture:
- The same namespace also runs a second Go application behind an Ingress with TLS termination.
- `local.example.com/app1` routes to the Flask service.
- `local.example.com/app2` routes to the Go service.

```text
                    https://local.example.com
                               |
                         Ingress :443
                               |
               +---------------+---------------+
               |                               |
         path /app1                      path /app2
               |                               |
     +---------v---------+           +---------v---------+
     | Service           |           | Service           |
     | devops-info-service|          | devops-info-service-go
     +---------+---------+           +---------+---------+
               |                               |
         3 Flask Pods                    2 Go Pods
```

Additional resource strategy for the second app:
- Requests: `50m CPU`, `64Mi memory`
- Limits: `200m CPU`, `128Mi memory`
- Rationale: the Go binary is lightweight, so it can run with a smaller baseline while still having room for probe traffic and ingress-routed requests.

---

## 2. Manifest Files

### `k8s/namespace.yml`
- Creates namespace `lab09`
- Keeps the lab resources isolated from any default namespace workloads

### `k8s/deployment.yml`
- Deploys `devops-info-service-python:lab09`
- Starts with `3` replicas
- Uses `RollingUpdate` strategy with:
  - `maxSurge: 1`
  - `maxUnavailable: 0`
- Exposes container port `5000`
- Adds:
  - `startupProbe`
  - `readinessProbe`
  - `livenessProbe`
- Includes resource requests and limits
- Keeps the container non-root because the Docker image already switches to `appuser`

Key configuration choices:
- `APP_REVISION=v1` in the steady-state manifest so the rolling update can be demonstrated by changing configuration
- Probes use `/health` because the app already exposes a lightweight health endpoint

### `k8s/service.yml`
- Creates a `NodePort` Service named `devops-info-service`
- Service port: `80`
- Target port: named port `http` -> container `5000`
- Fixed `nodePort: 30080`

Why NodePort:
- The lab explicitly requires `NodePort` for local access
- With minikube on macOS Docker driver, the practical access method is `minikube service --url`

### `k8s/bonus-go-deployment.yml`
- Deploys `devops-info-service-go:lab09`
- Runs `2` replicas of the Go application
- Uses the same rolling-update pattern as the Python deployment
- Exposes container port `8080`
- Adds startup, readiness, and liveness probes on `/health`
- Includes smaller resource requests and limits appropriate for the static Go binary

### `k8s/bonus-go-service.yml`
- Creates internal Service `devops-info-service-go`
- Uses Service port `80` to route to the container's named `http` port
- Intentionally stays `ClusterIP` because the Ingress is the external entry point

### `k8s/ingress.yml`
- Creates Ingress `devops-info-ingress`
- Uses host `local.example.com`
- Terminates TLS with Kubernetes Secret `tls-secret`
- Routes:
  - `/app1` -> `devops-info-service`
  - `/app2` -> `devops-info-service-go`
- Uses regex path matching plus rewrite so `/app1/health` becomes `/health` on the backend service

---

## 3. Deployment Evidence

### Cluster setup
`kubectl` is pointed to the local minikube context:

```text
lab09
```

`kubectl cluster-info` proof:

```text
Kubernetes control plane is running at https://127.0.0.1:32769
CoreDNS is running at https://127.0.0.1:32769/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

`kubectl get nodes -o wide` proof:

```text
NAME    STATUS   ROLES           VERSION   INTERNAL-IP    CONTAINER-RUNTIME
lab09   Ready    control-plane   v1.35.1   192.168.49.2   docker://29.2.1
```

### Initial application deployment
Initial `kubectl get pods,svc -n lab09 -o wide`:

```text
pod/devops-info-service-...   1/1 Running   ...   10.244.0.3   lab09
pod/devops-info-service-...   1/1 Running   ...   10.244.0.4   lab09
pod/devops-info-service-...   1/1 Running   ...   10.244.0.5   lab09

service/devops-info-service   NodePort   80:30080/TCP
```

`kubectl describe deployment devops-info-service -n lab09` confirms:
- `3 desired | 3 updated | 3 total | 3 available`
- `RollingUpdateStrategy: 0 max unavailable, 1 max surge`
- requests/limits configured
- liveness, readiness, and startup probes configured

### Service access proof
minikube service URL proof:

```text
http://127.0.0.1:55181
```

Health endpoint proof:

```json
{"status":"healthy","timestamp":"2026-03-16T10:26:18.762905+00:00","uptime_seconds":82}
```

Root endpoint proof:

```json
{"service":{"name":"devops-info-service","framework":"Flask","version":"1.0.0"}, ...}
```

This satisfies the lab requirement for "screenshot or curl output showing app working"; curl output is included.

---

## 4. Operations Performed

### Commands used to deploy

```bash
minikube start --profile lab09 --driver=docker --cpus=2 --memory=4096
docker build -t devops-info-service-python:lab09 app_python
minikube image load devops-info-service-python:lab09 -p lab09
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl rollout status deployment/devops-info-service -n lab09
```

### Scaling demonstration
I used the imperative scaling path for the demonstration step:

```bash
kubectl scale deployment/devops-info-service -n lab09 --replicas=5
kubectl rollout status deployment/devops-info-service -n lab09
kubectl get deployment devops-info-service -n lab09
kubectl get pods -n lab09 -o wide
```

Proof:
- Deployment reached `5/5` ready replicas
- Five Pods were running simultaneously

### Rolling update demonstration
I updated `k8s/deployment.yml` by changing:

```yaml
APP_REVISION: v1 -> v2
```

Then applied the updated manifest:

```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-info-service -n lab09
kubectl rollout history deployment/devops-info-service -n lab09
```

Rollout history after update:

```text
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

### Zero-downtime verification
During the rolling update I kept a port-forward open and sent one health-check request per second:

```bash
kubectl port-forward service/devops-info-service -n lab09 18080:80
curl http://127.0.0.1:18080/health
```

Proof from `k8s/evidence/lab09-zero-downtime-curl.txt`:

```text
10:23:51 200
10:23:52 200
10:23:53 200
...
10:24:16 200
```

All recorded requests returned `200`, so the Service stayed available while Pods were replaced.

### Rollback demonstration
I then rolled the deployment back:

```bash
kubectl rollout undo deployment/devops-info-service -n lab09
kubectl rollout status deployment/devops-info-service -n lab09
kubectl rollout history deployment/devops-info-service -n lab09
```

Rollback proof:

```text
deployment.apps/devops-info-service rolled back
```

History after rollback:

```text
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

Important note:
- Kubernetes created a new revision during rollback, so the history ends at revision `3`.
- After collecting the proof, I restored `k8s/deployment.yml` to stable `APP_REVISION=v1` so the repo manifest matches the final intended state.

---

## 5. Production Considerations

### Health checks
- `startupProbe` protects slow initialization and avoids premature liveness failures
- `readinessProbe` removes unready Pods from Service traffic
- `livenessProbe` restarts unhealthy containers
- All probes use `/health` because it is fast and deterministic

### Resource limits rationale
- Requests guarantee schedulability on a small local cluster
- Limits protect the node from a noisy container
- The chosen values are conservative but appropriate for a lightweight Flask app

### Improvements for production
- Push images to a registry instead of loading local tags into minikube
- Use separate ConfigMaps and Secrets instead of plain env values in the manifest
- Add PodDisruptionBudgets and anti-affinity for multi-node resilience
- Add HPA based on CPU or custom metrics
- Add Ingress instead of direct NodePort for HTTP routing
- Use dedicated namespaces, RBAC, NetworkPolicies, and admission controls

### Monitoring and observability strategy
- Reuse Lab 7 and Lab 8 observability work:
  - logs: Loki + Promtail + Grafana
  - metrics: Prometheus + Grafana
- Next production step would be:
  - kube-state-metrics
  - node-exporter
  - application scraping via Kubernetes Service discovery

---

## 6. Challenges & Solutions

1. Existing kubeconfig pointed to a remote cluster
- Problem: the default `kubectl` context was not local.
- Fix: started `minikube` profile `lab09`, which switched `kubectl` to the local cluster context.

2. Local cluster bootstrap took time
- Problem: first `minikube start` had to download the base image and Kubernetes preload.
- Fix: waited for the initial bootstrap; subsequent minikube operations are much faster.

3. NodePort access on macOS Docker driver is indirect
- Problem: direct node IP access is not the most convenient path on macOS Docker driver.
- Fix: used `minikube service devops-info-service --url` for service access and `kubectl port-forward` for active rollout validation.

4. Scaling and rolling update were separate concerns
- Problem: the scaling demo moved to 5 replicas, while the declarative manifest still defined 3.
- Fix: documented scaling as an explicit imperative demonstration step, then used the manifest-controlled 3-replica configuration for the rolling-update and rollback walkthrough.

5. Ingress testing on macOS Docker driver should avoid host OS edits when possible
- Problem: the lab examples use `/etc/hosts`, but changing host networking for local verification is unnecessary.
- Fix: used `kubectl port-forward` to the ingress controller and `curl --resolve local.example.com:8443:127.0.0.1`, which still tests host-based routing and TLS without modifying system files.

What I learned:
- Kubernetes is easiest to reason about when desired state is explicit
- Probes and rollout strategy are the core features that make Deployments production-worthy
- `kubectl rollout` and `describe` provide most of the first-line debugging needed for stateless apps

---

## 7. Bonus Task — Ingress with TLS

### Multi-app deployment
The bonus task uses two applications in the same namespace:
- `devops-info-service` -> existing Flask application from the main lab
- `devops-info-service-go` -> second Go application built from `app_go/`

The first app keeps its `NodePort` Service for the required main task. The second app uses a `ClusterIP` Service because ingress is the public HTTP entry point for the bonus.

### Ingress controller
Ingress was enabled in minikube with:

```bash
minikube addons enable ingress --profile lab09
```

Controller verification:

```text
NAME                                        READY   STATUS
ingress-nginx-controller-596f8778bc-k2wxx   1/1     Running
```

### TLS configuration and certificate creation
I generated a self-signed certificate for `local.example.com` and created the Kubernetes TLS Secret:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/lab09-tls.key \
  -out /tmp/lab09-tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls tls-secret -n lab09 \
  --key /tmp/lab09-tls.key \
  --cert /tmp/lab09-tls.crt
```

Certificate proof from `openssl x509 -noout -subject -issuer -dates`:

```text
subject=CN = local.example.com, O = local.example.com
issuer=CN = local.example.com, O = local.example.com
```

### Bonus resource deployment
Commands used:

```bash
docker build -t devops-info-service-go:lab09 app_go
minikube image load devops-info-service-go:lab09 -p lab09
kubectl apply -f k8s/bonus-go-deployment.yml -f k8s/bonus-go-service.yml -f k8s/ingress.yml
kubectl rollout status deployment/devops-info-service-go -n lab09
kubectl get all,ingress,secret -n lab09 -o wide
kubectl describe ingress devops-info-ingress -n lab09
```

Terminal proof that all required bonus resources exist:

```text
deployment.apps/devops-info-service-go   2/2   2   2
service/devops-info-service-go           ClusterIP   80/TCP
ingress.networking.k8s.io/devops-info-ingress   nginx   local.example.com   80, 443
secret/tls-secret   kubernetes.io/tls   2
```

Ingress routing proof from `kubectl describe ingress devops-info-ingress -n lab09`:

```text
TLS:
  tls-secret terminates local.example.com
Rules:
  local.example.com
    /app1(/|$)(.*)   devops-info-service:80
    /app2(/|$)(.*)   devops-info-service-go:80
```

### HTTPS verification
For local verification on macOS Docker driver, I used a port-forward to the ingress controller instead of editing `/etc/hosts`:

```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8443:443
curl -k -sS --resolve local.example.com:8443:127.0.0.1 https://local.example.com:8443/app1/
curl -k -sS --resolve local.example.com:8443:127.0.0.1 https://local.example.com:8443/app2/
curl -k -sS --resolve local.example.com:8443:127.0.0.1 https://local.example.com:8443/app1/health
curl -k -sS --resolve local.example.com:8443:127.0.0.1 https://local.example.com:8443/app2/health
```

Routing proof:
- `/app1/` returned the Flask payload with `framework: "Flask"`
- `/app2/` returned the Go payload with `framework: "Go net/http"`
- `/app1/health` and `/app2/health` both returned `{"status":"healthy", ...}`

This satisfies the bonus requirement for curl-based proof that both applications are accessible through HTTPS ingress routing.

### Why Ingress is better than direct NodePort Services
- Ingress gives one stable HTTP/HTTPS entry point instead of one exposed port per Service
- It supports path-based routing, so multiple applications can share the same host
- TLS termination is centralized at the ingress layer
- URL routing rules are declarative and easier to evolve than manually tracking many NodePort mappings

---

## 8. Evidence Index

- `k8s/evidence/lab09-minikube-version.txt`
- `k8s/evidence/lab09-minikube-profile-list.txt`
- `k8s/evidence/lab09-kubectl-current-context.txt`
- `k8s/evidence/lab09-cluster-info.txt`
- `k8s/evidence/lab09-get-nodes.txt`
- `k8s/evidence/lab09-get-namespaces.txt`
- `k8s/evidence/lab09-get-all-initial.txt`
- `k8s/evidence/lab09-get-pods-svc-initial.txt`
- `k8s/evidence/lab09-describe-deployment-initial.txt`
- `k8s/evidence/lab09-get-endpoints-initial.txt`
- `k8s/evidence/lab09-scale-to-5-command.txt`
- `k8s/evidence/lab09-scale-to-5-rollout.txt`
- `k8s/evidence/lab09-scale-to-5-deployment.txt`
- `k8s/evidence/lab09-scale-to-5-pods.txt`
- `k8s/evidence/lab09-rollout-v2-apply.txt`
- `k8s/evidence/lab09-rollout-v2-status.txt`
- `k8s/evidence/lab09-rollout-history-after-v2.txt`
- `k8s/evidence/lab09-rollout-v2-pods.txt`
- `k8s/evidence/lab09-zero-downtime-curl.txt`
- `k8s/evidence/lab09-rollout-undo.txt`
- `k8s/evidence/lab09-rollout-undo-status.txt`
- `k8s/evidence/lab09-rollout-history-after-undo.txt`
- `k8s/evidence/lab09-rollout-undo-pods.txt`
- `k8s/evidence/lab09-get-all-final.txt`
- `k8s/evidence/lab09-get-pods-svc-final.txt`
- `k8s/evidence/lab09-describe-deployment-final.txt`
- `k8s/evidence/lab09-minikube-service-url.txt`
- `k8s/evidence/lab09-service-health.json`
- `k8s/evidence/lab09-service-root.json`
- `k8s/evidence/lab09-bonus-minikube-addons.txt`
- `k8s/evidence/lab09-bonus-ingress-controller-pods.txt`
- `k8s/evidence/lab09-bonus-go-docker-build.txt`
- `k8s/evidence/lab09-bonus-go-image-load.txt`
- `k8s/evidence/lab09-bonus-openssl-generate.txt`
- `k8s/evidence/lab09-bonus-tls-cert-details.txt`
- `k8s/evidence/lab09-bonus-create-tls-secret.txt`
- `k8s/evidence/lab09-bonus-apply.txt`
- `k8s/evidence/lab09-bonus-go-rollout-status.txt`
- `k8s/evidence/lab09-bonus-get-all.txt`
- `k8s/evidence/lab09-bonus-describe-ingress.txt`
- `k8s/evidence/lab09-bonus-app1-root.json`
- `k8s/evidence/lab09-bonus-app2-root.json`
- `k8s/evidence/lab09-bonus-app1-health.json`
- `k8s/evidence/lab09-bonus-app2-health.json`
