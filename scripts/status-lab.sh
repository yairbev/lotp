#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

initialize_environment
require_command docker
require_command curl

compose ps
printf '\nHealth checks\n'
for endpoint in \
  'Gitea|http://127.0.0.1:3000/api/healthz' \
  'Portal|http://127.0.0.1:8000/healthz' \
  'Collector|http://127.0.0.1:9000/healthz'; do
  label="${endpoint%%|*}"
  url="${endpoint#*|}"
  if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
    printf '  %-10s ready\n' "$label"
  else
    printf '  %-10s unavailable\n' "$label"
  fi
done

printf '\nCurrent deployment\n'
compose exec -T prod-app sh -c 'if [ -f /data/deployment.json ]; then cat /data/deployment.json; else echo "No completed deployment yet."; fi'
