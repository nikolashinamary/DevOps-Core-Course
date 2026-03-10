# Lab 07: Observability & Logging with Loki Stack - Submission

**Name:** Mariana Nikolashina  
**Date:** 2026-03-10  
**Lab scope:** Main tasks completed with runtime proofs

---

## 1. Architecture

The logging stack is deployed with Docker Compose and includes Loki, Promtail, Grafana, and two apps.

```text
+------------------+       Docker logs        +--------------------+
| app-python:5000  | -----------------------> |                    |
| label app=...    |                          |                    |
+------------------+                          |                    |
                                              |     Promtail       |   push logs
+------------------+       Docker logs        |      :9080         | ----------+
| app-go:8080      | -----------------------> |                    |           |
| label app=...    |                          |                    |           v
+------------------+                          +--------------------+    +-------------+
                                                                      | Loki :3100 |
                                                                      +-------------+
                                                                             |
                                                                             | query
                                                                             v
                                                                      +---------------+
                                                                      | Grafana :3000 |
                                                                      +---------------+
```

---

## 2. Task 1 - Deploy Loki Stack

### Implemented files
- `monitoring/docker-compose.yml`
- `monitoring/loki/config.yml`
- `monitoring/promtail/config.yml`
- `monitoring/.env.example` (+ local `.env` for runtime)

### Key configuration decisions
- Loki: TSDB + schema `v13`, filesystem storage, 7-day retention (`168h`).
- Promtail: Docker service discovery with label filter `logging=promtail`.
- Grafana: anonymous access disabled, admin password from `.env`.
- All services run on shared `logging` network with named volumes.

### Runtime proof
Deployment timestamp:
```text
2026-03-10T16:27:41Z
```

`docker compose ps` proof (all services up, Loki/Grafana healthy):
```text
NAME                      IMAGE                              STATUS
monitoring-app-go-1       devops-info-service-go:lab07      Up
monitoring-app-python-1   devops-info-service-python:lab07  Up
monitoring-grafana-1      grafana/grafana:12.3.1            Up (healthy)
monitoring-loki-1         grafana/loki:3.0.0                Up (healthy)
monitoring-promtail-1     grafana/promtail:3.0.0            Up
```

Health endpoints:
- Loki ready: `ready`
- Grafana health: `{"database":"ok","version":"12.3.1",...}`

---

## 3. Task 2 - Integrate Applications + Structured Logging

### Integration
Both apps are included in `monitoring/docker-compose.yml` and labeled for Promtail:
- `app-python` with `logging=promtail`, `app=devops-python`
- `app-go` with `logging=promtail`, `app=devops-go`

Promtail filters only labeled containers.

### Structured JSON logging (Python app)
`app_python/app.py` uses a custom `JSONFormatter` and request lifecycle hooks (`before_request`/`after_request`) to emit structured logs.

Example captured log line:
```json
{"timestamp": "2026-03-10T16:27:42.402889+00:00", "level": "WARNING", "logger": "devops-info-service", "message": "route_not_found", "method": "GET", "path": "/does-not-exist", "status_code": 404, "client_ip": "192.168.165.1", "user_agent": "curl/8.6.0"}
```

### Log ingestion proof
Loki `app` label values:
```json
{"status":"success","data":["devops-go","devops-python"]}
```

Generated traffic (including `/`, `/health`, and 404s) is captured and visible in Loki query results.

### LogQL proof queries
Saved successful query responses:
1. `{app="devops-python"}` (range query)
2. `{app=~"devops-.*"} | json | method="GET"` (range query)
3. `sum by (app) (count_over_time({app=~"devops-.*"}[5m]))` (instant query)
4. `{app="devops-python"} |= "WARNING"` (range query)

Example metric result snippet:
```json
{"metric":{"app":"devops-go"},"value":[...,"3"]}
{"metric":{"app":"devops-python"},"value":[...,"5"]}
```

---

## 4. Task 3 - Grafana Dashboard

### Data source proof
Loki data source was created via Grafana API:
```json
{"message":"Datasource added","name":"Loki",...}
```

### Dashboard proof
Dashboard created via Grafana API:
```json
{"status":"success","uid":"lab07logs","url":"/d/lab07logs/lab07-loki-dashboard"}
```

Dashboard title: `Lab07 Loki Dashboard`  
Panels implemented:
1. Logs Table: `{app=~"devops-.*"}`
2. Request Rate: `sum by (app) (rate({app=~"devops-.*"}[1m]))`
3. Error Logs: `{app=~"devops-.*"} | json | level="ERROR"`
4. Log Level Distribution: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

Note: generated test traffic produced `INFO` and `WARNING` entries; `ERROR` panel query is configured and ready but can be empty without 5xx events.

---

## 5. Task 4 - Production Readiness

Implemented hardening in Compose/config:
- Resource limits/reservations for all services (`deploy.resources`).
- Grafana anonymous mode disabled (`GF_AUTH_ANONYMOUS_ENABLED=false`).
- Admin credentials loaded from `.env` (`GRAFANA_ADMIN_PASSWORD`).
- Health checks:
  - Loki: `http://localhost:3100/ready`
  - Grafana: `http://localhost:3000/api/health`
- Loki retention: `retention_period: 168h`.

Important Loki 3.0 fix applied:
- Added `compactor.delete_request_store: filesystem` required when retention is enabled.

Security proof (no anonymous dashboard access):
```text
HTTP/1.1 302 Found
Location: /login
```

---

## 6. Research Answers

1. How is Loki different from Elasticsearch?
- Loki indexes labels, not full log content; this reduces storage/index costs and keeps log lines in compressed chunks.

2. What are log labels and why do they matter?
- Labels are indexed key/value metadata (`app`, `service`, `container`) used for fast stream selection and filtering in LogQL.

3. How does Promtail discover containers?
- Through Docker service discovery (`docker_sd_configs`) using Docker socket metadata, then relabeling into Loki labels.

---

## 7. Challenges and Fixes

1. Loki startup failure with retention enabled
- Problem: Loki failed validation with `compactor.delete-request-store should be configured when retention is enabled`.
- Fix: Added `delete_request_store: filesystem` in `monitoring/loki/config.yml`.

2. Too many irrelevant Docker logs
- Problem: Without filtering, Promtail can ingest all container logs.
- Fix: Added Docker SD filter `logging=promtail` and labeled only required services.

3. Reliable proof collection in headless environment
- Problem: UI screenshots are not ideal in this execution environment.
- Fix: Added reproducible CLI/API proof artifacts under `monitoring/docs/evidence/` and supplemented them with manual Grafana screenshots under `monitoring/docs/screenshots/`.

---

## 8. Evidence Index

- `monitoring/docs/evidence/lab07-proof-timestamp.txt`
- `monitoring/docs/evidence/lab07-compose-ps.txt`
- `monitoring/docs/evidence/lab07-loki-ready.txt`
- `monitoring/docs/evidence/lab07-promtail-targets.txt`
- `monitoring/docs/evidence/lab07-grafana-health.txt`
- `monitoring/docs/evidence/lab07-grafana-root-headers.txt`
- `monitoring/docs/evidence/lab07-generated-404-status.txt`
- `monitoring/docs/evidence/lab07-app-python-logs-tail40.txt`
- `monitoring/docs/evidence/lab07-app-go-logs-tail40.txt`
- `monitoring/docs/evidence/lab07-promtail-logs-tail80.txt`
- `monitoring/docs/evidence/lab07-loki-logs-tail80.txt`
- `monitoring/docs/evidence/lab07-loki-labels.json`
- `monitoring/docs/evidence/lab07-loki-app-label-values.json`
- `monitoring/docs/evidence/lab07-logql-query1-python-stream.json`
- `monitoring/docs/evidence/lab07-logql-query2-json-method-get.json`
- `monitoring/docs/evidence/lab07-logql-query3-count-over-time.json`
- `monitoring/docs/evidence/lab07-logql-query4-warning-logs.json`
- `monitoring/docs/evidence/lab07-grafana-datasource-create.json`
- `monitoring/docs/evidence/lab07-grafana-datasources-list.json`
- `monitoring/docs/evidence/lab07-dashboard-payload.json`
- `monitoring/docs/evidence/lab07-grafana-dashboard-create.json`
- `monitoring/docs/evidence/lab07-grafana-dashboard-search.json`

## 9. Screenshot Index

- `monitoring/docs/screenshots/01-grafana-loki-datasource.jpg`
- `monitoring/docs/screenshots/02-explore-logs-containers.jpg`
- `monitoring/docs/screenshots/03-json-logs-python.jpg`
- `monitoring/docs/screenshots/04-logql-query-app-python.jpg`
- `monitoring/docs/screenshots/05-logql-query-json-get.jpg`
- `monitoring/docs/screenshots/06-logql-query-warning.jpg`
- `monitoring/docs/screenshots/07-dashboard-4-panels.png`
- `monitoring/docs/screenshots/08-grafana-login-no-anon.jpg`
