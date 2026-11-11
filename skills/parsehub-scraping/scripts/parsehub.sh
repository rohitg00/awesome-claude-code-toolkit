#!/usr/bin/env bash
# parsehub.sh — thin wrapper over the ParseHub API v2.
# Reads PARSEHUB_API_KEY from the environment; never takes the key as an argument
# (argv is visible to other processes via /proc and shell history).
set -euo pipefail

API="https://www.parsehub.com/api/v2"

if [ -z "${PARSEHUB_API_KEY:-}" ]; then
  echo "PARSEHUB_API_KEY is not set. Export it first:" >&2
  echo "  export PARSEHUB_API_KEY=..." >&2
  exit 1
fi

usage() {
  cat >&2 <<'EOF'
Usage: parsehub.sh <command> [args]

  projects                  List projects
  project <PROJECT_TOKEN>   Show one project
  run <PROJECT_TOKEN>       Start a run; prints the run token
  status <RUN_TOKEN>        Show run status
  data <RUN_TOKEN>          Fetch a completed run's data
  last <PROJECT_TOKEN>      Fetch the last successful run's data
  wait <RUN_TOKEN>          Poll until complete, then print the data
  cancel <RUN_TOKEN>        Cancel a running run
EOF
  exit 1
}

need() { [ -n "${1:-}" ] || usage; }

cmd="${1:-}"; shift || true

case "$cmd" in
  projects)
    curl -sS --get "$API/projects" --data-urlencode "api_key=$PARSEHUB_API_KEY"
    ;;
  project)
    need "${1:-}"
    curl -sS --get "$API/projects/$1" --data-urlencode "api_key=$PARSEHUB_API_KEY"
    ;;
  run)
    need "${1:-}"
    curl -sS -X POST "$API/projects/$1/run" --data-urlencode "api_key=$PARSEHUB_API_KEY"
    ;;
  status)
    need "${1:-}"
    curl -sS --get "$API/runs/$1" --data-urlencode "api_key=$PARSEHUB_API_KEY"
    ;;
  data)
    need "${1:-}"
    curl -sS --get "$API/runs/$1/data" --data-urlencode "api_key=$PARSEHUB_API_KEY"
    ;;
  last)
    need "${1:-}"
    curl -sS --get "$API/projects/$1/last_ready_run/data" \
      --data-urlencode "api_key=$PARSEHUB_API_KEY"
    ;;
  cancel)
    need "${1:-}"
    curl -sS -X POST "$API/runs/$1/cancel" --data-urlencode "api_key=$PARSEHUB_API_KEY"
    ;;
  wait)
    need "${1:-}"
    run_token="$1"
    delay=5
    for _ in $(seq 1 60); do
      status=$(curl -sS --get "$API/runs/$run_token" \
        --data-urlencode "api_key=$PARSEHUB_API_KEY" \
        | grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' \
        | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
      case "$status" in
        complete)
          curl -sS --get "$API/runs/$run_token/data" \
            --data-urlencode "api_key=$PARSEHUB_API_KEY"
          exit 0
          ;;
        cancelled|error)
          echo "Run $run_token ended with status: $status" >&2
          exit 1
          ;;
      esac
      sleep "$delay"
      [ "$delay" -lt 30 ] && delay=$((delay * 2))
    done
    echo "Timed out waiting for run $run_token to complete." >&2
    exit 1
    ;;
  *)
    usage
    ;;
esac
