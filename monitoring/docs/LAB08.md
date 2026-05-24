# Lab 08: Metrics & Monitoring with Prometheus - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-03-16  
**Lab scope:** Main tasks completed with runtime proofs and reproducible Grafana provisioning

---

## 1. Architecture

The Lab 8 stack extends the Lab 7 logging stack with Prometheus-based metrics collection.

```text
                        metrics (/metrics)
+-------------------+ ------------------------------> +------------------------+
| app-python :5000  |                                 | Prometheus :9090       |
| Flask + RED       | <------------------------------ | scrape interval: 15s   |
| business metrics  |        PromQL queries           | retention: 15d / 10GB  |
+-------------------+                                 +-----------+------------+
                                                                |
                                                                | queries / datasource
                                                                v
                                                        +------------------------+
                                                        | Grafana :3000          |
                                                        | Prometheus dashboard   |
                                                        | login required         |
                                                        +------------------------+

+-------------------+      container logs      +-------------------+      push      +-------------------+
| app-python/app-go | -----------------------> | Promtail :9080    | -------------> | Loki :3100        |
+-------------------+                          +-------------------+                +-------------------+
```

Why both paths matter:
- Metrics answer rate, latency, uptime, and trends.
- Logs answer what happened in a specific request and why.
- Grafana now has both Loki logs and Prometheus metrics available.

---

## 2. Application Instrumentation

### Implemented files
- `app_python/app.py`
- `app_python/requirements.txt`
- `app_python/tests/test_app.py`

### Added metrics
HTTP RED metrics:
- `http_requests_total{method,endpoint,status_code}`: counter for request volume and status breakdown
- `http_request_duration_seconds{method,endpoint}`: histogram for latency distribution and p95
- `http_requests_in_progress`: gauge for concurrent request visibility

Application-specific metrics:
- `devops_info_endpoint_calls_total{endpoint}`: counter for business endpoint usage
- `devops_info_system_collection_seconds`: histogram for system-info collection cost on `/`

### Implementation choices
- Metrics are exposed on `/metrics` using `prometheus_client`.
- Endpoint labels are normalized with `request.url_rule.rule`; unknown routes are grouped as `unmatched` to avoid high-cardinality labels.
- Request timing is captured in `before_request` / `after_request`.
- The in-progress gauge is decremented in `teardown_request` so it is released even on error paths.

### Runtime proof
From `monitoring/docs/evidence/lab08-app-metrics.txt`:

```text
http_requests_total{endpoint="/health",method="GET",status_code="200"} 74.0
http_requests_total{endpoint="/metrics",method="GET",status_code="200"} 29.0
http_requests_total{endpoint="/",method="GET",status_code="200"} 40.0
http_requests_total{endpoint="unmatched",method="GET",status_code="404"} 3.0
```

Business metrics are also exported:

```text
devops_info_endpoint_calls_total{endpoint="/health"} 74.0
devops_info_endpoint_calls_total{endpoint="/"} 40.0
devops_info_system_collection_seconds_count 40.0
```

---

## 3. Prometheus Configuration

### Implemented files
- `monitoring/docker-compose.yml`
- `monitoring/prometheus/prometheus.yml`

### Scrape configuration
- Global scrape interval: `15s`
- Targets:
  - `localhost:9090` as job `prometheus`
  - `app-python:5000/metrics` as job `app`
  - `loki:3100/metrics` as job `loki`
  - `grafana:3000/metrics` as job `grafana`

### Retention and persistence
- Retention flags:
  - `--storage.tsdb.retention.time=15d`
  - `--storage.tsdb.retention.size=10GB`
- Persistent volume: `prometheus-data`

### Runtime proof
Prometheus health endpoint returned:

```text
Prometheus Server is Healthy.
```

`up` query proof from `monitoring/docs/evidence/lab08-prometheus-query-up.json`:

```text
grafana:3000  -> 1
localhost:9090 -> 1
app-python:5000 -> 1
loki:3100 -> 1
```

Target proof from `monitoring/docs/evidence/lab08-prometheus-targets.json` shows all four active targets with `"health":"up"`.

---

## 4. Dashboard Walkthrough

### Implemented files
- `monitoring/grafana/dashboards/lab08-app-metrics-dashboard.json`
- `monitoring/scripts/provision-grafana.sh`

### Why API provisioning is used
Grafana file provisioning failed against the existing persistent Grafana state with a datasource startup error. To keep the stack stable and reproducible, I added `monitoring/scripts/provision-grafana.sh`, which:
- waits for Grafana health
- ensures the Prometheus datasource exists
- imports the dashboard JSON through the Grafana API

### Dashboard identity
- Title: `Lab08 App Metrics`
- UID: `lab08metrics`
- URL: `/d/lab08metrics/lab08-app-metrics`

Grafana API creation proof:

```json
{"status":"success","uid":"lab08metrics","url":"/d/lab08metrics/lab08-app-metrics"}
```

### Panels and queries
1. Request Rate  
   Query: `sum by (endpoint) (rate(http_requests_total[5m]))`

2. Error Rate  
   Query: `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`

3. Request Duration p95  
   Query: `histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))`

4. Request Duration Heatmap  
   Query: `sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m]))`

5. Active Requests  
   Query: `http_requests_in_progress`

6. Status Code Distribution  
   Query: `sum by (status_code) (rate(http_requests_total[5m]))`

7. App Uptime  
   Query: `up{job="app"}`

### Dashboard proof
Dashboard search result from `monitoring/docs/evidence/lab08-grafana-dashboard-search.json`:

```text
title="Lab08 App Metrics" uid="lab08metrics"
```

---

## 5. PromQL Examples

1. `up`
- Purpose: verify every scrape target is alive
- Proof: all four targets returned `1`

2. `sum by (endpoint) (rate(http_requests_total[5m]))`
- Purpose: request rate per endpoint
- Proof from `lab08-promql-request-rate.json`:
  - `/health` ≈ `0.1684 req/s`
  - `/metrics` ≈ `0.0667 req/s`
  - `/` ≈ `0.0883 req/s`

3. `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`
- Purpose: server-side error rate
- Proof from `lab08-promql-error-rate.json`: empty result vector, which is expected because no 5xx traffic was generated

4. `histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))`
- Purpose: p95 latency by endpoint
- Proof from `lab08-promql-p95-latency.json`:
  - `/health` ≈ `0.00475s`
  - `/metrics` ≈ `0.00842s`
  - `/` ≈ `0.00475s`

5. `http_requests_in_progress`
- Purpose: concurrent in-flight requests
- Proof from `lab08-promql-active-requests.json`: sampled as `1` during a scrape

6. `sum by (status_code) (rate(http_requests_total[5m]))`
- Purpose: live status-code mix
- Proof from `lab08-promql-status-distribution.json` after sustained 404 traffic:
  - `200` ≈ `0.1684 req/s`
  - `404` ≈ `0.0750 req/s`

Useful note:
- `rate()` on very short bursts can flatten to `0` if Prometheus only has one sample for that series.
- I kept an extra proof file, `lab08-promql-status-distribution-increase.json`, to show the same split with `increase(...)` semantics.

---

## 6. Production Setup

### Health checks
Configured in `monitoring/docker-compose.yml`:
- Loki: readiness probe on `http://localhost:3100/ready`
- Promtail: process-based health check (`/proc/1/comm`) because the image does not include `wget`
- Grafana: `http://localhost:3000/api/health`
- Prometheus: `http://localhost:9090/-/healthy`
- Python app: inline Python HTTP probe to `http://localhost:5000/health`
- Go app: `wget` probe to `http://localhost:8080/health`

### Resource limits
- Prometheus: `1 CPU`, `1G`
- Loki: `1 CPU`, `1G`
- Grafana: `0.5 CPU`, `512M`
- `app-python` / `app-go`: `0.5 CPU`, `256M`
- Promtail: `0.5 CPU`, `512M`

### Security and persistence
- Grafana anonymous access remains disabled.
- Root request proof from `monitoring/docs/evidence/lab08-grafana-root-headers.txt`:

```text
HTTP/1.1 302 Found
Location: /login
```

- Persistent volumes:
  - `grafana-data`
  - `loki-data`
  - `promtail-data`
  - `prometheus-data`

### Persistence proof
I performed `docker compose down` followed by `docker compose up -d` without deleting volumes.

Results:
- `monitoring/docs/evidence/lab08-persistence-compose-ps.txt`: all services returned healthy
- `monitoring/docs/evidence/lab08-persistence-dashboard-search.json`: dashboard `Lab08 App Metrics` still exists
- `monitoring/docs/evidence/lab08-persistence-datasources.json`: Prometheus datasource still exists

---

## 7. Testing Results

### Container-level verification
Proof timestamp:

```text
2026-03-16T08:43:42Z
```

`docker compose ps` proof from `monitoring/docs/evidence/lab08-compose-ps.txt` shows:
- `app-go` healthy
- `app-python` healthy
- `grafana` healthy
- `loki` healthy
- `prometheus` healthy
- `promtail` healthy

### Automated tests
Because the local sandbox cannot install Python packages from the network, I ran the test suite in a disposable Docker container.

`monitoring/docs/evidence/lab08-pytest.txt`:

```text
32 passed in 0.13s
```

### Metrics vs Logs comparison
- Metrics: best for dashboards, alert thresholds, rates, latency percentiles, uptime, and capacity trends.
- Logs: best for request forensics, payload/context details, exception text, and timeline reconstruction.
- In this repo:
  - Lab 8 metrics answer "how many / how fast / is it up?"
  - Lab 7 logs answer "which request failed and what context did it carry?"

### Screenshot evidence collected
The required screenshots were captured and confirm the UI-side requirements:

1. Screenshot 1: `/metrics` endpoint output
- File: `monitoring/docs/screenshots/01-metrics.png`
- Shows exported Prometheus text exposition including:
  - `http_request_duration_seconds`
  - `http_requests_in_progress`
  - `devops_info_endpoint_calls_total`
  - `devops_info_system_collection_seconds`

2. Screenshot 2: Prometheus `/targets`
- File: `monitoring/docs/screenshots/02-prometheus-targets.png`
- Shows all required scrape jobs in `UP` state:
  - `app`
  - `grafana`
  - `loki`
  - `prometheus`

3. Screenshot 3: successful PromQL query
- File: `monitoring/docs/screenshots/03-prometheus-query.png`
- Query shown: `sum by (endpoint) (rate(http_requests_total[5m]))`
- Result includes visible series for `/`, `/health`, `/metrics`, and `unmatched`

4. Screenshot 4: Grafana application dashboard with live data
- File: `monitoring/docs/screenshots/04-grafana-dashboards-all.png`
- Shows the custom dashboard `Lab08 App Metrics`
- Live panels displayed:
  - Request Rate
  - Error Rate
  - Request Duration p95
  - Active Requests
  - App Uptime
  - Status Code Distribution
  - Request Duration Heatmap
- This screenshot also satisfies the requirement to show all 6+ panels working.

5. Screenshot 5: Grafana data sources
- File: `monitoring/docs/screenshots/05-grafana-datasources.png`
- Shows both `Loki` and `Prometheus`
- Confirms Prometheus is configured as the default data source

---

## 8. Challenges & Solutions

1. Grafana startup failed with datasource provisioning
- Problem: Grafana exited with `Datasource provisioning error: data source not found`.
- Fix: removed startup provisioning from Compose and added `monitoring/scripts/provision-grafana.sh` to provision the datasource and dashboard through the Grafana API after Grafana is healthy.

2. Promtail health check failed
- Problem: the Promtail image does not ship with `wget`, so the HTTP health check always failed.
- Fix: switched Promtail to a process-based health check using `/proc/1/comm`.

3. Local sandbox could not install Python dependencies
- Problem: direct `pip install` from the sandbox failed because outbound package access is blocked.
- Fix: validated syntax locally, built the real container image, and executed `pytest` in a disposable Docker container instead.

4. Short bursts can under-report in `rate()`
- Problem: a tight burst of 404 traffic initially showed a `0` rate in Prometheus.
- Fix: generated slower sustained 404 traffic across multiple scrape intervals and refreshed the evidence.

---

## 9. Screenshot Index

- `monitoring/docs/screenshots/01-metrics.png`
- `monitoring/docs/screenshots/02-prometheus-targets.png`
- `monitoring/docs/screenshots/03-prometheus-query.png`
- `monitoring/docs/screenshots/04-grafana-dashboards-all.png`
- `monitoring/docs/screenshots/05-grafana-datasources.png`

---

## 10. Evidence Index

- `monitoring/docs/evidence/lab08-proof-timestamp.txt`
- `monitoring/docs/evidence/lab08-compose-ps.txt`
- `monitoring/docs/evidence/lab08-app-metrics.txt`
- `monitoring/docs/evidence/lab08-generated-404-status.txt`
- `monitoring/docs/evidence/lab08-prometheus-healthy.txt`
- `monitoring/docs/evidence/lab08-prometheus-targets.json`
- `monitoring/docs/evidence/lab08-prometheus-query-up.json`
- `monitoring/docs/evidence/lab08-promql-request-rate.json`
- `monitoring/docs/evidence/lab08-promql-error-rate.json`
- `monitoring/docs/evidence/lab08-promql-p95-latency.json`
- `monitoring/docs/evidence/lab08-promql-active-requests.json`
- `monitoring/docs/evidence/lab08-promql-status-distribution.json`
- `monitoring/docs/evidence/lab08-promql-status-distribution-increase.json`
- `monitoring/docs/evidence/lab08-grafana-health.json`
- `monitoring/docs/evidence/lab08-grafana-datasources.json`
- `monitoring/docs/evidence/lab08-grafana-root-headers.txt`
- `monitoring/docs/evidence/lab08-dashboard-payload.json`
- `monitoring/docs/evidence/lab08-grafana-dashboard-create.json`
- `monitoring/docs/evidence/lab08-grafana-dashboard-search.json`
- `monitoring/docs/evidence/lab08-grafana-dashboard-export.json`
- `monitoring/docs/evidence/lab08-persistence-down.txt`
- `monitoring/docs/evidence/lab08-persistence-up.txt`
- `monitoring/docs/evidence/lab08-persistence-compose-ps.txt`
- `monitoring/docs/evidence/lab08-persistence-dashboard-search.json`
- `monitoring/docs/evidence/lab08-persistence-datasources.json`
- `monitoring/docs/evidence/lab08-pytest.txt`
