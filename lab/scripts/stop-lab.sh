#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

initialize_environment
require_command docker

if [[ "${1:-}" == "--purge" ]]; then
  info "Stopping the lab and deleting its named Docker volumes"
  compose down --volumes --remove-orphans
  assert_runtime_target "$RUNTIME_DIR"
  rm -rf -- "$RUNTIME_DIR"
  info "Purged lab state. The generated .env file was kept."
else
  info "Stopping the lab while preserving Gitea and lab data"
  compose down --remove-orphans
fi
