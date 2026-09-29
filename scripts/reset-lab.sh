#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

initialize_environment
require_command docker
require_command git
require_command curl
require_command base64

[[ -d "$SEED_WORKTREE/.git" ]] || fail "Seed worktree not found. Run scripts/start-lab.sh first."
assert_runtime_target "$SEED_WORKTREE"

info "Restoring the tracked repository to the clean baseline template"
seed_git rm -r --ignore-unmatch . >/dev/null 2>&1 || true
seed_git clean -fdx >/dev/null
cp -a "$PROJECT_ROOT/demo/repository/." "$SEED_WORKTREE/"
seed_git add -A
if ! seed_git diff --cached --quiet; then
  seed_git commit -m "reset: restore clean baseline [NJ-BASE-01]" >/dev/null
  auth_header="$(basic_auth_header)"
  seed_git -c "http.extraHeader=Authorization: Basic $auth_header" push origin main
else
  info "Repository is already at the clean baseline"
fi

info "Clearing collected demonstration events"
curl -fsS \
  -X DELETE \
  -H "X-Lab-Reset-Token: $COLLECTOR_RESET_TOKEN" \
  http://127.0.0.1:9000/api/events >/dev/null

if ! compose exec -T developer true >/dev/null 2>&1; then
  fail "Developer container is not running. Inspect it with: docker compose logs --tail=100 developer"
fi

if compose exec -T developer test -d /home/developer/work/nightjar/.git; then
  info "Refreshing the isolated developer checkout"
  compose exec -T developer sh -lc \
    'cd /home/developer/work/nightjar && git fetch origin main && git reset --hard origin/main && git clean -fdx'
fi

info "Clean baseline restored. If repository files changed, the reset commit will trigger a fresh build and deployment."
