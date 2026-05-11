# Lab 12: ConfigMaps & Persistent Volumes - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-04-13  
**Chart path:** `k8s/devops-info-service`  
**Application:** `app_python`  
**Live cluster verification:** minikube context `lab11`, namespace `lab12`, release `lab12-app`

---

## 1. Application Changes

I extended the Python service to persist a visits counter in a file and expose it through a dedicated endpoint.

Implemented behavior:
- `GET /` increments the visits counter and writes the updated value to `VISITS_FILE`.
- `GET /visits` returns the current persisted count without incrementing it.
- The counter uses an advisory file lock (`fcntl.flock`) so concurrent requests from multiple processes on the same mounted volume do not overwrite each other.
- The application reads the current value from disk on startup; if the file does not exist or is empty, the counter starts from `0`.

Relevant files:
- `app_python/app.py`
- `app_python/tests/test_app.py`
- `app_python/docker-compose.yml`
- `app_python/README.md`

### Local Docker persistence workflow

The local Docker Compose file mounts `./data` from the application directory to `/app/data` in the container:

```yaml
volumes:
  - ./data:/app/data
```

Recommended commands:

```bash
cd app_python
docker compose up --build -d
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/visits
cat ./data/visits
docker compose restart
curl http://localhost:5000/visits
docker compose down
```

Expected result:
- the value in `./data/visits` increases after requests to `/`;
- after `docker compose restart`, `GET /visits` returns the same value that was stored before restart.

Actual local validation on 2026-04-13:
- initial `/visits` inside the container returned `0`;
- after generating traffic, `/app/data/visits` contained `4`;
- after `docker compose restart`, `/visits` still returned `4`.

---

## 2. ConfigMap Implementation

### Files and templates

Created:
- `k8s/devops-info-service/files/config.json`
- `k8s/devops-info-service/templates/configmap.yaml`

The chart now creates two ConfigMaps:

1. File-backed ConfigMap
- Name helper: `{{ include "devops-info-service.configFileMapName" . }}`
- Source: `tpl (.Files.Get "files/config.json") .`
- Mounted into the container as `/config/config.json`

2. Environment ConfigMap
- Name helper: `{{ include "devops-info-service.configEnvMapName" . }}`
- Injected with `envFrom`
- Provides:
  - `APP_NAME`
  - `APP_DEPLOY_ENV`
  - `APP_LOG_LEVEL`
  - `APP_FEATURE_VISITS`
  - `APP_CONFIG_RELOAD_STRATEGY`

### Mounted file

The deployment mounts the whole ConfigMap directory:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
    readOnly: true
```

This intentionally avoids `subPath`, because full ConfigMap directory mounts can receive updates from kubelet.

### Application usage

The Flask app reads `CONFIG_FILE` on every request to `/`, so configuration changes in the mounted file can be picked up without changing application code again. The response includes:
- `configuration.file`
- `configuration.environment_variables`
- `configuration.feature_flags`
- `configuration.settings`

### Verification commands

Store terminal outputs in `k8s/evidence/lab12/`:

```bash
kubectl get configmap,pvc -n <namespace> > k8s/evidence/lab12/get-configmap-pvc.txt
kubectl exec -n <namespace> <pod-name> -- cat /config/config.json > k8s/evidence/lab12/pod-config-json.txt
kubectl exec -n <namespace> <pod-name> -- printenv | grep '^APP_' > k8s/evidence/lab12/pod-app-env.txt
```

Expected verification:
- `kubectl get configmap,pvc` shows both ConfigMaps and one PVC in `Bound` state.
- `cat /config/config.json` returns the rendered JSON from the chart file.
- `printenv | grep '^APP_'` shows values from the env ConfigMap.

### Live verification results

I deployed the chart with:

```bash
minikube image load devops-info-service-python:lab12 -p lab11
helm upgrade --install lab12-app k8s/devops-info-service \
  --namespace lab12 --create-namespace \
  -f k8s/devops-info-service/values-dev.yaml \
  --wait --wait-for-jobs
```

Notes from the live install:
- `values-dev.yaml` now uses `nodePort: 30081` because `30080` was already allocated by earlier labs in the same cluster.
- The release reached `STATUS: deployed` in namespace `lab12`.

Captured evidence:
- `k8s/evidence/lab12/get-configmap-pvc-pods-svc.txt`
- `k8s/evidence/lab12/pod-config-json.txt`
- `k8s/evidence/lab12/pod-app-env.txt`

Observed results:
- `kubectl get configmap,pvc,pods,svc -n lab12` showed:
  - ConfigMaps `lab12-app-devops-info-service-config` and `lab12-app-devops-info-service-env`
  - PVC `lab12-app-devops-info-service-data` in `Bound` state
  - Service `lab12-app-devops-info-service` on `80:30081/TCP`
- `/config/config.json` inside the pod contained:
  - `application.environment: "dev"`
  - `featureFlags.visitsCounter: true`
  - `settings.reloadStrategy: "checksum-rollout"`
- environment injection inside the pod included:
  - `APP_NAME=devops-info-service`
  - `APP_DEPLOY_ENV=dev`
  - `APP_LOG_LEVEL=INFO`
  - `APP_FEATURE_VISITS=true`
  - `APP_CONFIG_RELOAD_STRATEGY=checksum-rollout`

---

## 3. Persistent Volume Implementation

### PVC configuration

Created:
- `k8s/devops-info-service/templates/pvc.yaml`

Default values in `values.yaml`:

```yaml
persistence:
  enabled: true
  mountPath: /data
  fileName: visits
  size: 100Mi
  storageClass: ""
```

The PVC requests:
- access mode: `ReadWriteOnce`
- size: `100Mi`
- storage class: configurable through `persistence.storageClass`

### Volume mount

The deployment mounts the PVC at `/data`, and the application receives:

```yaml
- name: VISITS_FILE
  value: /data/visits
```

This keeps the visits file outside the image filesystem, so the value survives pod recreation.

### Security context

To make persistent storage work reliably with the non-root container, the chart now sets:
- pod `fsGroup: 1000`
- container `runAsUser: 1000`
- container `runAsGroup: 1000`
- container `runAsNonRoot: true`

### Persistence verification procedure

Run:

```bash
kubectl get pods -n <namespace> -o wide
kubectl exec -n <namespace> <pod-name> -- cat /data/visits
kubectl delete pod -n <namespace> <pod-name>
kubectl get pods -n <namespace> -w
kubectl exec -n <namespace> <new-pod-name> -- cat /data/visits
```

Store outputs in:
- `k8s/evidence/lab12/persistence-before.txt`
- `k8s/evidence/lab12/pod-delete.txt`
- `k8s/evidence/lab12/persistence-after.txt`
- `k8s/evidence/lab12/root-hit-counts.txt`
- `k8s/evidence/lab12/new-pod-name.txt`
- `k8s/evidence/lab12/visits-after-restart.txt`

Expected result:
- the value in `/data/visits` before deletion matches the value after the Deployment creates a replacement pod.

### Live persistence results

The live pod replacement test succeeded:
- initial application pod: `lab12-app-devops-info-service-7f59cdc74d-466cz`
- generated root traffic recorded in `root-hit-counts.txt`: counts `3` and `4`
- value before pod deletion from `/data/visits`: `4`
- deleted pod:
  - `pod "lab12-app-devops-info-service-7f59cdc74d-466cz" deleted from lab12 namespace`
- replacement pod name:
  - `lab12-app-devops-info-service-7f59cdc74d-hl2ld`
- value after replacement pod startup from `/data/visits`: `4`
- `/visits` on the new pod returned:

```json
{"storage_file":"/data/visits","visits":4}
```

This confirms the counter is stored on the PVC rather than in the ephemeral container filesystem.

---

## 4. Bonus: Config Reload Pattern

I implemented the checksum-annotation rollout pattern and documented the default ConfigMap update behavior.

### Default ConfigMap file updates

For mounted ConfigMaps, kubelet eventually refreshes files in the mounted directory. The delay is not instant; it is typically tied to kubelet sync timing and cache refresh, so updates can take around a minute or more to appear.

### Why `subPath` is avoided

`subPath` mounts do not receive live ConfigMap updates because Kubernetes bind-mounts a single file snapshot into the container. For reloadable config, mount the entire directory instead.

### Implemented reload approach

Two complementary mechanisms are present:

1. File reload in the application
- the app reads `CONFIG_FILE` on each root request;
- mounted file changes can be observed by the app without code redeploy.

2. Helm checksum rollout
- the Deployment template includes:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

- when the ConfigMap content changes during `helm upgrade`, the pod template hash changes and Kubernetes rolls the Deployment automatically.

This pattern is especially important for environment-variable ConfigMaps, because container environment variables do not update in place for already-running pods.

---

## 5. ConfigMap vs Secret

### Use ConfigMap when:
- the data is non-sensitive application configuration;
- values are safe to expose as plain text inside manifests or pod environment;
- examples include feature flags, log levels, port numbers, and JSON app settings.

### Use Secret when:
- the data is sensitive and should have tighter RBAC handling;
- values include passwords, API tokens, certificates, or private keys;
- the data may later need external secret-management integration such as Vault.

### Key differences
- ConfigMaps are intended for non-confidential configuration; Secrets are intended for confidential data.
- Both are base64-encoded in manifests when serialized by Kubernetes, but only Secrets are modeled as sensitive resources.
- In production, Secrets should also be protected with etcd encryption at rest and strict RBAC.
