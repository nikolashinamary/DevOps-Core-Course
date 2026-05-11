#!/usr/bin/env bash
set -euo pipefail

# Lab 17 helper: run from edge-api/ after wrangler auth is configured.
# Auth options:
# 1) Interactive: npx wrangler login
# 2) Non-interactive: export CLOUDFLARE_API_TOKEN=...

echo "Wrangler version:"
npx wrangler --version

echo "Whoami:"
npx wrangler whoami

echo
echo "Create KV namespace SETTINGS and copy the returned id into wrangler.jsonc kv_namespaces[0].id"
npx wrangler kv namespace create SETTINGS

echo
echo "Set required secrets:"
printf '%s\n' "Set API_TOKEN:" && npx wrangler secret put API_TOKEN
printf '%s\n' "Set ADMIN_EMAIL:" && npx wrangler secret put ADMIN_EMAIL

echo
echo "Deploy worker:"
npx wrangler deploy

echo
echo "List deployments:"
npx wrangler deployments list

echo
echo "Tail logs (Ctrl+C to exit):"
npx wrangler tail
