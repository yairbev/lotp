#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
RUNTIME_DIR="$PROJECT_ROOT/.runtime"
SEED_WORKTREE="$RUNTIME_DIR/seed-worktree"

info() {
  printf '[lab] %s\n' "$*"
}

fail() {
  printf '[lab] ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

set_env_value() {
  local key="$1"
  local value="$2"
  local temp_file
  temp_file="$(mktemp "$PROJECT_ROOT/.env.tmp.XXXXXX")"
  awk -v key="$key" -v value="$value" '
    BEGIN { found = 0 }
    $0 ~ "^" key "=" { print key "=" value; found = 1; next }
    { print }
    END { if (!found) print key "=" value }
  ' "$ENV_FILE" > "$temp_file"
  mv "$temp_file" "$ENV_FILE"
}

initialize_environment() {
  require_command openssl
  if [[ ! -f "$ENV_FILE" ]]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    info "Created .env from .env.example"
  fi

  local registration_token
  registration_token="$(awk -F= '$1 == "GITEA_RUNNER_REGISTRATION_TOKEN" {sub(/^[^=]*=/, ""); print; exit}' "$ENV_FILE")"
  if [[ -z "$registration_token" ]]; then
    registration_token="$(openssl rand -hex 24)"
    set_env_value GITEA_RUNNER_REGISTRATION_TOKEN "$registration_token"
    info "Generated a lab-only runner registration token"
  fi

  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a

  : "${GITEA_ADMIN_USER:?GITEA_ADMIN_USER is required in .env}"
  : "${GITEA_ADMIN_PASSWORD:?GITEA_ADMIN_PASSWORD is required in .env}"
  : "${GITEA_ADMIN_EMAIL:?GITEA_ADMIN_EMAIL is required in .env}"
  : "${DEMO_BUILD_SECRET:?DEMO_BUILD_SECRET is required in .env}"
  : "${COLLECTOR_RESET_TOKEN:?COLLECTOR_RESET_TOKEN is required in .env}"

  [[ "$GITEA_ADMIN_USER" =~ ^[A-Za-z0-9._-]+$ ]] || fail "GITEA_ADMIN_USER contains unsupported characters"
  [[ "$DEMO_BUILD_SECRET" =~ ^[A-Za-z0-9._-]+$ ]] || fail "DEMO_BUILD_SECRET must use letters, numbers, dot, underscore, or dash"
  mkdir -p "$RUNTIME_DIR"
}

compose() {
  (
    cd "$PROJECT_ROOT"
    docker compose --env-file "$ENV_FILE" "$@"
  )
}

wait_for_url() {
  local label="$1"
  local url="$2"
  local timeout_seconds="${3:-120}"
  local started
  started="$(date +%s)"
  until curl -fsS --max-time 3 "$url" >/dev/null 2>&1; do
    if (( $(date +%s) - started >= timeout_seconds )); then
      printf '[lab] ERROR: %s did not become ready within %ss (%s)\n' "$label" "$timeout_seconds" "$url" >&2
      return 1
    fi
    sleep 2
  done
  info "$label is ready"
}

gitea_api() {
  curl -fsS --user "$GITEA_ADMIN_USER:$GITEA_ADMIN_PASSWORD" "$@"
}

basic_auth_header() {
  printf '%s' "$GITEA_ADMIN_USER:$GITEA_ADMIN_PASSWORD" | base64 | tr -d '\r\n'
}

git_cmd() {
  env \
    -u GIT_DIR \
    -u GIT_WORK_TREE \
    -u GIT_INDEX_FILE \
    -u GIT_OBJECT_DIRECTORY \
    -u GIT_COMMON_DIR \
    git "$@"
}

seed_git() {
  assert_runtime_target "$SEED_WORKTREE"
  git_cmd -c "safe.directory=$SEED_WORKTREE" -C "$SEED_WORKTREE" "$@"
}

assert_runtime_target() {
  local target="$1"
  case "$target" in
    "$RUNTIME_DIR"|"$RUNTIME_DIR"/*) ;;
    *) fail "Refusing destructive operation outside $RUNTIME_DIR: $target" ;;
  esac
}
