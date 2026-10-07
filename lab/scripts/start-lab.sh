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

info "Validating configuration"
compose config --quiet

info "Starting Gitea, the production service, and the developer workstation"
compose up -d --build gitea prod-app developer
wait_for_url "Gitea" "http://127.0.0.1:3000/api/healthz" 180 || {
  compose logs --tail=120 gitea >&2 || true
  exit 1
}
wait_for_url "Collector" "http://127.0.0.1:9000/healthz" 180 || {
  compose logs --tail=120 prod-app >&2 || true
  exit 1
}

if ! compose exec -T gitea gitea admin user list --config /etc/gitea/app.ini 2>/dev/null | awk -v user="$GITEA_ADMIN_USER" '$0 ~ "[[:space:]]" user "[[:space:]]" {found=1} END {exit !found}'; then
  info "Creating the lab administrator"
  compose exec -T gitea gitea admin user create \
    --config /etc/gitea/app.ini \
    --username "$GITEA_ADMIN_USER" \
    --password "$GITEA_ADMIN_PASSWORD" \
    --email "$GITEA_ADMIN_EMAIL" \
    --admin \
    --must-change-password=false
fi

repo_url="http://127.0.0.1:3000/api/v1/repos/$GITEA_ADMIN_USER/nightjar"
repo_status="$(curl -sS -o /dev/null -w '%{http_code}' --user "$GITEA_ADMIN_USER:$GITEA_ADMIN_PASSWORD" "$repo_url")"
if [[ "$repo_status" == "404" ]]; then
  info "Creating the nightjar demonstration repository"
  gitea_api \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{"name":"nightjar","description":"Living Off the Pipeline demonstration repository","private":false,"auto_init":false}' \
    http://127.0.0.1:3000/api/v1/user/repos >/dev/null
elif [[ "$repo_status" != "200" ]]; then
  fail "Gitea returned HTTP $repo_status while checking the nightjar repository"
fi

info "Enabling repository Actions and installing the lab-only pipeline secret"
gitea_api \
  -H 'Content-Type: application/json' \
  -X PATCH \
  -d '{"has_actions":true}' \
  "$repo_url" >/dev/null
gitea_api \
  -H 'Content-Type: application/json' \
  -X PUT \
  -d "{\"data\":\"$DEMO_BUILD_SECRET\"}" \
  "$repo_url/actions/secrets/DEMO_BUILD_SECRET" >/dev/null

auth_header="$(basic_auth_header)"
remote_git_url="http://127.0.0.1:3000/$GITEA_ADMIN_USER/nightjar.git"
remote_main_exists=0
if git_cmd -c "http.extraHeader=Authorization: Basic $auth_header" \
  ls-remote --exit-code "$remote_git_url" refs/heads/main >/dev/null 2>&1; then
  remote_main_exists=1
fi

if (( remote_main_exists == 0 )); then
  info "Seeding the clean application and workflow"
  assert_runtime_target "$SEED_WORKTREE"
  rm -rf -- "$SEED_WORKTREE"
  mkdir -p "$SEED_WORKTREE"
  cp -a "$PROJECT_ROOT/demo/repository/." "$SEED_WORKTREE/"
  git_cmd -c init.defaultBranch=main init "$SEED_WORKTREE" >/dev/null
  seed_git rev-parse --git-dir >/dev/null 2>&1 \
    || fail "Git did not create a usable repository at $SEED_WORKTREE"
  seed_git symbolic-ref HEAD refs/heads/main
  seed_git config --local user.name "Nightjar Demo Developer"
  seed_git config --local user.email "developer@example.invalid"
  seed_git add -A
  seed_git commit -m "baseline: clean portal and pipeline [NJ-BASE-01]" >/dev/null
  seed_git remote add origin "$remote_git_url"
  seed_git -c "http.extraHeader=Authorization: Basic $auth_header" push -u origin main
elif ! seed_git rev-parse --git-dir >/dev/null 2>&1; then
  info "Restoring the local seed worktree from the existing Gitea repository"
  assert_runtime_target "$SEED_WORKTREE"
  rm -rf -- "$SEED_WORKTREE"
  git_cmd -c "http.extraHeader=Authorization: Basic $auth_header" clone \
    "$remote_git_url" "$SEED_WORKTREE"
else
  info "Keeping the existing nightjar repository and local seed worktree"
fi
seed_git config --local user.name "Nightjar Demo Developer"
seed_git config --local user.email "developer@example.invalid"
gitea_api \
  -H 'Content-Type: application/json' \
  -X PATCH \
  -d '{"default_branch":"main"}' \
  "$repo_url" >/dev/null

info "Starting the host-mode Gitea runner (no Docker socket)"
compose up -d --build runner

if ! wait_for_url "Deployed portal" "http://127.0.0.1:8000/healthz" 240; then
  compose logs --tail=120 runner prod-app >&2 || true
  exit 1
fi

if ! compose exec -T --user developer developer test -d /home/developer/work/nightjar/.git; then
  info "Cloning the repository into the isolated developer workstation"
  compose exec -T --user developer developer \
    git clone "http://gitea:3000/$GITEA_ADMIN_USER/nightjar.git" /home/developer/work/nightjar
fi

cat <<EOF

Lab baseline is ready.

  Gitea:       http://127.0.0.1:3000/$GITEA_ADMIN_USER/nightjar
  Portal:      http://127.0.0.1:8000/
  Event log:   http://127.0.0.1:9000/events

  Gitea user:  $GITEA_ADMIN_USER
  Gitea pass:  $GITEA_ADMIN_PASSWORD

The services bind to the VM loopback interface by default. From another machine,
use an SSH tunnel or intentionally change LAB_BIND_ADDRESS in .env.
EOF
