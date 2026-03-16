#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MONITORING_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

if [ ! -f "$MONITORING_DIR/.env" ]; then
  echo "missing $MONITORING_DIR/.env" >&2
  exit 1
fi

set -a
. "$MONITORING_DIR/.env"
set +a

GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
GRAFANA_USER=${GRAFANA_ADMIN_USER:-admin}
GRAFANA_PASSWORD=${GRAFANA_ADMIN_PASSWORD:?set in monitoring/.env}
PROMETHEUS_UID=prometheus-lab08
DASHBOARD_UID=lab08metrics
DASHBOARD_FILE="$MONITORING_DIR/grafana/dashboards/lab08-app-metrics-dashboard.json"

curl_auth() {
  curl -sS -u "$GRAFANA_USER:$GRAFANA_PASSWORD" "$@"
}

wait_for_grafana() {
  attempts=0
  until curl_auth "$GRAFANA_URL/api/health" >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 30 ]; then
      echo "grafana did not become ready at $GRAFANA_URL" >&2
      exit 1
    fi
    sleep 2
  done
}

ensure_prometheus_datasource() {
  status=$(curl_auth -o /dev/null -w "%{http_code}" "$GRAFANA_URL/api/datasources/uid/$PROMETHEUS_UID")
  if [ "$status" = "200" ]; then
    curl_auth "$GRAFANA_URL/api/datasources/uid/$PROMETHEUS_UID"
    return
  fi

  curl_auth \
    -H "Content-Type: application/json" \
    -X POST \
    "$GRAFANA_URL/api/datasources" \
    -d '{
      "name": "Prometheus",
      "type": "prometheus",
      "access": "proxy",
      "url": "http://prometheus:9090",
      "uid": "prometheus-lab08",
      "isDefault": true,
      "basicAuth": false
    }'
}

import_dashboard() {
  python3 - "$DASHBOARD_FILE" <<'PY' | curl_auth \
    -H "Content-Type: application/json" \
    -X POST \
    "$GRAFANA_URL/api/dashboards/db" \
    -d @-
import json
import sys

dashboard_path = sys.argv[1]
with open(dashboard_path, encoding="utf-8") as dashboard_file:
    dashboard = json.load(dashboard_file)

payload = {
    "dashboard": dashboard,
    "folderId": 0,
    "overwrite": True,
}

json.dump(payload, sys.stdout)
PY
}

wait_for_grafana
ensure_prometheus_datasource
import_dashboard
