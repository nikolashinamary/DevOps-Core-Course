# Lab 17: Cloudflare Workers Edge Deployment - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-05-04  
**Runtime:** Cloudflare Workers (TypeScript, Worker only template)  
**Project directory:** `edge-api/`

## 1. Deployment Summary

Project initialization:
- Created with C3 (`npm create cloudflare@latest edge-api`)
- Template: **Hello World**
- Platform: **Worker only**
- Language: **TypeScript**

Worker configuration:
- File: `edge-api/wrangler.jsonc`
- Worker name: `devops-core-lab17-edge-api`
- Compatibility date: `2026-03-10`
- Plaintext vars:
  - `APP_NAME=devops-core-edge-api`
  - `COURSE_NAME=devops-core`
  - `DEPLOYMENT_STAGE=prod`
- KV binding:
  - `SETTINGS` with namespace id `c3b84352b69748fbbf3553bf73c459c6`

Public Worker URL:
- `https://devops-core-lab17-edge-api.m-nikolashina.workers.dev`

Implemented routes:
- `GET /` - app metadata and available routes
- `GET /health` - health endpoint
- `GET /edge` - edge metadata from `request.cf`
- `GET /config` - non-sensitive config summary and secret presence flags
- `GET /counter` - KV-backed persisted counter
- `POST /counter/reset` - reset persisted counter to 0

## 2. Evidence

### 2.1 CLI/Auth and Deploy Operations

- Wrangler version: `k8s/evidence/lab17/wrangler-version.txt`
- Wrangler auth (`whoami`, logged in): `k8s/evidence/lab17/wrangler-whoami.txt`
- Deploy output (successful): `k8s/evidence/lab17/wrangler-deploy.txt`
- Deployment history: `k8s/evidence/lab17/wrangler-deployments-list.txt`

### 2.2 Public Endpoint Validation (`workers.dev`)

- Public URL: `k8s/evidence/lab17/public-url.txt`
- Root response: `k8s/evidence/lab17/public-root.json`
- Health response: `k8s/evidence/lab17/public-health.json`
- Edge metadata response: `k8s/evidence/lab17/public-edge.json`
- Config response: `k8s/evidence/lab17/public-config.json`
- KV counter (1st call): `k8s/evidence/lab17/public-counter-1.json`
- KV counter (2nd call): `k8s/evidence/lab17/public-counter-2.json`

Observed public behavior:
- `/health` returns `status=ok`
- `/edge` returns Cloudflare edge fields (`colo`, `country`, `city`, `asn`, `httpProtocol`, `tlsVersion`)
- `/counter` increments persistently (`3` then `4` in captured evidence)
- `/config` confirms secrets are configured via boolean flags

### 2.3 Local Validation and Tests

- Local route checks (`wrangler dev --local`): `k8s/evidence/lab17/local-*.json`, `local-404.txt`
- Worker tests: `k8s/evidence/lab17/npm-test.txt` (`6 passed, 0 failed`)

### 2.4 Required Screenshots

Stored in `k8s/evidence/lab17/screenshots/`:
- `dashboard-overview.png` - Worker overview in Cloudflare dashboard
- `workers-dev-edge-response.png` - `/edge` JSON from public `workers.dev` URL
- `logs-or-metrics.png` - observability evidence (logs or metrics)

## 3. Global Edge Behavior Explanation

Workers run on Cloudflare’s global edge network automatically. A single deploy publishes a Worker version, and Cloudflare routes each request through its network to execute near users without manual multi-region VM orchestration.

Why there is no “deploy to 3 regions” step:
- VM/PaaS models require explicit region planning and rollout.
- Workers handles global placement and routing as part of the platform model.

Routing concepts:
- `workers.dev`: immediate public URL for a Worker.
- Routes: attach Worker to traffic on an existing Cloudflare-managed zone.
- Custom Domains: assign a dedicated domain/subdomain to the Worker.

## 4. Configuration, Secrets, and Persistence

### Plaintext Variables

Configured in `wrangler.jsonc` under `vars`:
- `APP_NAME`
- `COURSE_NAME`
- `DEPLOYMENT_STAGE`

Why vars are not secrets:
- They are plain runtime configuration and not intended for sensitive credentials.

### Secrets

Configured using Wrangler secrets and consumed as:
- `env.API_TOKEN`
- `env.ADMIN_EMAIL`

Secret values are not committed to Git.

### KV Persistence

Binding:
- `SETTINGS: KVNamespace` in Worker env

Behavior:
- `GET /counter` reads `visits`, increments, persists, and returns updated value.

Persistence verification:
- Public evidence shows increasing values across calls (`3` then `4`), proving persisted state in KV.

## 5. Observability and Operations

Logging:
- `console.log()` added per request with path and edge metadata.

Metrics/logs evidence:
- Screenshot in `k8s/evidence/lab17/screenshots/logs-or-metrics.png`.

Deployment operations demonstrated:
- `npx wrangler deploy`
- `npx wrangler deployments list`

## 6. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | High (cluster, manifests, ingress, ops) | Low-Medium (Wrangler config + deploy) |
| Deployment speed | Slower, more moving parts | Very fast for edge APIs |
| Global distribution | Manual multi-region architecture | Built-in global edge routing |
| Cost (for small apps) | Often higher baseline overhead | Usually cheaper for lightweight APIs |
| State/persistence model | Native patterns for long-running/stateful apps | Stateless compute + bindings (KV, D1, R2, etc.) |
| Control/flexibility | Maximum control and runtime breadth | Less low-level control, opinionated runtime |
| Best use case | Complex microservices/platform workloads | Edge APIs, request transforms, lightweight serverless logic |

## 7. When to Use Each

Use Kubernetes when:
- You need full container/runtime control.
- You run complex multi-service systems with advanced networking and scheduling.
- You need strong portability across infrastructure vendors.

Use Cloudflare Workers when:
- You need globally distributed low-latency HTTP logic quickly.
- You want minimal operational overhead for APIs or edge middleware.
- You can work within serverless runtime constraints.

Recommendation:
- For this lab API workload, Workers provides faster delivery and simpler operations.
- For broader platform workloads, Kubernetes remains the stronger option.

## 8. Reflection

What felt easier than Kubernetes:
- Faster setup and deployment workflow.
- Immediate global edge execution model without cluster operations.

What felt more constrained:
- Tighter runtime/platform model and less low-level infrastructure control.

What changed because Workers is not a Docker host:
- No container image build/deploy path.
- Runtime configuration moved to `wrangler.jsonc`, secrets, and platform bindings.
- Persistence moved to managed services like KV instead of container/pod storage patterns.

## 9. Files Included

- `edge-api/src/index.ts`
- `edge-api/wrangler.jsonc`
- `edge-api/test/index.spec.ts`
- `edge-api/.dev.vars.example`
- `edge-api/scripts/lab17-cloud-commands.sh`
- `k8s/evidence/lab17/*`
- `WORKERS.md`
