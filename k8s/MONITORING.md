# Lab 16: Kubernetes Monitoring & Init Containers - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-04-23  
**Cluster:** `minikube` on context `lab16`  
**Monitoring stack:** `prometheus-community/kube-prometheus-stack`

## 1. Stack Components

I installed the kube-prometheus-stack and used it to monitor the cluster.

Component roles in my own words:

- Prometheus Operator: manages Prometheus, Alertmanager, and related CRDs such as ServiceMonitor.
- Prometheus: scrapes metrics from cluster targets and stores/query them.
- Alertmanager: receives firing alerts from Prometheus and handles alert routing.
- Grafana: visualizes the collected metrics in dashboards.
- kube-state-metrics: exports Kubernetes object state like pods, deployments, and services.
- node-exporter: exports node-level CPU, memory, filesystem, and network metrics from the host.

## 2. Installation Evidence

I installed the stack into the `monitoring` namespace with Helm.

Install command:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace --wait --timeout 15m
```

Final monitoring state:

- [monitoring stack resources](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/monitoring-stack.txt)
- [final monitoring pods/services](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/monitoring-final.txt)
- [ServiceMonitors](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/servicemonitors.txt)

Observed monitoring pods:

```text
monitoring-grafana
monitoring-kube-prometheus-operator
monitoring-kube-state-metrics
monitoring-prometheus-node-exporter
monitoring-kube-prometheus-prometheus
alertmanager-monitoring-kube-prometheus-alertmanager-0
```

## 3. Grafana / Dashboard Answers

I used Grafana dashboards and Alertmanager UI directly, and cross-checked values with Prometheus/Alertmanager API outputs.

### 3.1 StatefulSet Pod Resources

StatefulSet CPU usage:

```text
devops-info-service-ss-1 -> 0.0036740211761873503
devops-info-service-ss-2 -> 0.003645784508072255
devops-info-service-ss-0 -> 0.0035183827863339155
```

StatefulSet memory usage:

```text
devops-info-service-ss-2 -> 23.26171875 MiB
devops-info-service-ss-1 -> 23.2578125 MiB
devops-info-service-ss-0 -> 23.2421875 MiB
```

Interpretation:

- the StatefulSet pods are all healthy and roughly equal in memory
- CPU is low and the minor differences are normal background variation

Evidence:

- [final Prometheus answers](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/final-prometheus-answers-2.txt)
- [screenshot: StatefulSet resources](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/01-statefulset-resources.png)

### 3.2 Default Namespace CPU

Default namespace CPU usage:

```text
devops-info-service-default-6958b748b4-chntf -> 0.007084103131196094
devops-info-service-default-6958b748b4-j8c86  -> 0.0035955252875979494
```

Most CPU:

- `devops-info-service-default-6958b748b4-chntf`

Least CPU:

- `devops-info-service-default-6958b748b4-j8c86`

Evidence:

- [screenshot: default namespace CPU most/least](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/02-default-cpu-most-least.png)

### 3.3 Node Metrics

Node `lab16`:

- CPU cores: `10`
- Memory used: `3928.1953125 MiB`
- Memory used: `74.84041995024124%`

Evidence:

- [screenshot: node metrics](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/03-node-metrics.png)

### 3.4 Kubelet

Cluster totals from kubelet / kube-state metrics:

- pods managed: `54`
- containers managed: `86`

Evidence:

- [screenshot: kubelet pods/containers](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/04-kubelet-pods-containers.png)

### 3.5 Traffic

I used the app's HTTP request counter as the traffic signal for the default namespace because pod-level container network byte counters were not exposed in this cluster's Prometheus scrape.

Default namespace request rate on `/`:

```text
devops-info-service-default-6958b748b4-chntf -> 0.13104555555555555 req/s
devops-info-service-default-6958b748b4-j8c86  -> 0.04172814814814814 req/s
```

Default namespace request rate on `/health`:

```text
devops-info-service-default-6958b748b4-chntf -> 0.11794299999999999 req/s
devops-info-service-default-6958b748b4-j8c86  -> 0.112668 req/s
```

Evidence:

- [default traffic query output](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/final-prometheus-answers-2.txt)
- [default HTTP series](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/http-request-series-default.txt)
- [screenshot: default namespace traffic](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/05-default-traffic.png)

### 3.6 Alerts

Active alerts in Alertmanager: `5`

Active alert names:

- `TargetDown`
- `etcdInsufficientMembers`
- `TargetDown`
- `Watchdog`
- `TargetDown`

The active alerts are cluster-level alerts from the kube-prometheus stack, which is expected in this kind of lab environment.

Evidence:

- [Alertmanager query output](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/final-prometheus-answers-2.txt)
- [screenshot: active alerts in Alertmanager](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/06-alertmanager-active-alerts.png)

### 3.7 Screenshot Evidence Index

- [01-statefulset-resources.png](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/01-statefulset-resources.png)
- [02-default-cpu-most-least.png](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/02-default-cpu-most-least.png)
- [03-node-metrics.png](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/03-node-metrics.png)
- [04-kubelet-pods-containers.png](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/04-kubelet-pods-containers.png)
- [05-default-traffic.png](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/05-default-traffic.png)
- [06-alertmanager-active-alerts.png](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/screenshots/06-alertmanager-active-alerts.png)

## 4. Init Containers

I implemented two init-container patterns through chart values and the existing Deployment template.

Relevant files:

- [init-container values: download](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab16-init-download.yaml)
- [init-container values: wait](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab16-wait.yaml)
- [dependency release values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab16-dependency.yaml)
- [download release values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab16-default.yaml)
- [ServiceMonitor template](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/servicemonitor.yaml)
- [standalone ServiceMonitor for default namespace traffic](/Users/marianikolashina/DevOps-Core-Course/k8s/lab16-default-servicemonitor.yaml)

### 4.1 Download Init Container

Pattern:

- init container runs `wget`
- saves `index.html` into the shared PVC mounted at `/data`
- main app container can read the file after startup

Evidence:

- [download pod state](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/init-download-pod.txt)
- [download logs](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/init-download-logs.txt)
- [download file contents](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/init-download-file.txt)

Observed result:

- `/data/index.html` exists in the running app container
- the file contains the Example Domain HTML downloaded by the init container

### 4.2 Wait-for-Service Init Container

Pattern:

- init container loops on `nslookup devops-info-service-dependency.lab16-wait.svc.cluster.local`
- the main container stays blocked until the Service exists
- once the dependency Service is created, the pod transitions to `Running`

Evidence:

- [wait pod state](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/init-wait-pod.txt)
- [wait logs](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/init-wait-logs.txt)
- [wait services](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/lab16-wait-services.txt)

Observed result:

- before the dependency Service existed, the init container logged repeated `NXDOMAIN` failures
- after the dependency Service was created, DNS resolved successfully
- the pod became `1/1 Running`

## 5. Bonus: Custom Metrics & ServiceMonitor

I added ServiceMonitor support to the chart and used it for the metrics release.

Relevant files:

- [ServiceMonitor template](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/servicemonitor.yaml)
- [metrics release values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab16-metrics.yaml)
- [default-namespace ServiceMonitor](/Users/marianikolashina/DevOps-Core-Course/k8s/lab16-default-servicemonitor.yaml)

Verification:

- `up{namespace="lab16-metrics",service="devops-info-service-metrics"} = 1`

Evidence:

- [final Prometheus answers](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/final-prometheus-answers.txt)
- [final Prometheus answers after default ServiceMonitor fix](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/final-prometheus-answers-2.txt)

## 6. Files Changed

- [Monitoring report](/Users/marianikolashina/DevOps-Core-Course/k8s/MONITORING.md)
- [Kube-prometheus-stack install evidence](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/monitoring-stack.txt)
- [Prometheus query evidence](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/final-prometheus-answers-2.txt)
- [Init container evidence](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/init-download-file.txt)
- [Init wait evidence](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab16/init-wait-logs.txt)
