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

assert_runtime_target "$SEED_WORKTREE"
auth_header="$(basic_auth_header)"
remote_git_url="http://127.0.0.1:3000/$GITEA_ADMIN_USER/nightjar.git"

if ! seed_git rev-parse --git-dir >/dev/null 2>&1; then
  info "Recreating the internal reset worktree from Gitea"
  rm -rf -- "$SEED_WORKTREE"
  if ! git_cmd -c "http.extraHeader=Authorization: Basic $auth_header" clone \
    "$remote_git_url" "$SEED_WORKTREE"; then
    fail "Could not clone the nightjar repository from Gitea. Confirm the lab is running, then retry."
  fi
fi

seed_git config --local user.name "Nightjar Demo Developer"
seed_git config --local user.email "developer@example.invalid"
seed_git remote set-url origin "$remote_git_url"

info "Synchronizing the internal reset worktree with Gitea"
seed_git -c "http.extraHeader=Authorization: Basic $auth_header" fetch origin main
seed_git reset --hard origin/main >/dev/null
seed_git clean -fdx >/dev/null

info "Restoring the tracked repository to the clean baseline template"
seed_git rm -r --ignore-unmatch . >/dev/null 2>&1 || true
seed_git clean -fdx >/dev/null
cp -a "$PROJECT_ROOT/demo/repository/." "$SEED_WORKTREE/"
seed_git add -A
if ! seed_git diff --cached --quiet; then
  seed_git commit -m "reset: restore clean baseline [NJ-BASE-01]" >/dev/null
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
