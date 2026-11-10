#!/usr/bin/env bash
# One-command deploy on the Hostinger VPS (Docker). Run from anywhere:  contacts-db/deploy/deploy.sh [path-to-ntxp-branded-document-2]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="${1:-${NTXP_DOC_SKILL:-}}"

[ -f "$HERE/.env" ] || { echo "Missing $HERE/.env — copy .env.example and fill it in."; exit 1; }
grep -q '^NTXP_DB_URL=postgresql' "$HERE/.env"      || { echo ".env: NTXP_DB_URL (Supabase) is not set."; exit 1; }
grep -q '^NTXP_GOOGLE_CLIENT_ID=.*apps.googleusercontent.com' "$HERE/.env" || { echo ".env: NTXP_GOOGLE_CLIENT_ID is not set."; exit 1; }
grep -qi '^NTXP_MCP_AUTH=none' "$HERE/.env" && { echo "Refusing to deploy with NTXP_MCP_AUTH=none."; exit 1; } || true

if [ -n "$SKILL" ]; then
  [ -f "$SKILL/scripts/render.py" ] || { echo "$SKILL is not the NTXP Branded Document skill folder."; exit 1; }
  echo "Copying the NTXP document engine and logo (proprietary — stays on this server, never committed)…"
  rm -rf "$HERE/engine" && mkdir -p "$HERE/engine" && cp -r "$SKILL/scripts" "$SKILL/templates" "$SKILL/types" "$SKILL/assets" "$SKILL/SKILL.md" "$HERE/engine/" 2>/dev/null || true
  [ -d "$SKILL/reference" ] && cp -r "$SKILL/reference" "$HERE/engine/" || true
  cp "$SKILL/assets/ntxp_logo_reversed.png" "$HERE/assets/"
else
  echo "No skill path given: building WITHOUT the doc engine (the app falls back to the browser's Save-as-PDF)."
  sed -i 's/^WITH_ENGINE=.*/WITH_ENGINE=0/' "$HERE/.env" || true
fi

docker compose -f "$HERE/docker-compose.yml" --env-file "$HERE/.env" up -d --build
echo "Waiting for health…"; for i in $(seq 1 30); do
  docker compose -f "$HERE/docker-compose.yml" exec -T app python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)" 2>/dev/null && { echo "App is healthy."; break; }; sleep 2; done
echo "First run: initialise the schema once →  docker compose -f $HERE/docker-compose.yml exec app ntxp init"
echo "Then open https://contacts.ntxpllc.com"
