#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

BUILD_IMAGES=0
case "${1:-}" in
  "") ;;
  --build) BUILD_IMAGES=1 ;;
  *) fail "Unknown option: $1 (supported: --build)" ;;
esac

as_root() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    fail "Installing packages requires root or sudo access"
  fi
}

apt_install() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
  else
    sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
  fi
}

docker_compose_available() {
  command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1
}

install_ubuntu_requirements() {
  [[ -r /etc/os-release ]] || fail "Cannot identify the operating system"
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "ubuntu" ]] || fail "Automatic package installation supports Ubuntu only (detected: ${ID:-unknown})"
  command -v apt-get >/dev/null 2>&1 || fail "apt-get is required for automatic installation"

  info "Updating apt metadata and installing host utilities"
  as_root apt-get update
  apt_install ca-certificates curl git openssl

  if docker_compose_available; then
    return
  fi

  info "Docker Engine or Compose v2 is missing; configuring Docker's official Ubuntu repository"

  local conflicts=()
  local package
  for package in docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc; do
    if dpkg-query -W -f='${db:Status-Abbrev}' "$package" 2>/dev/null | grep -q '^ii'; then
      conflicts+=("$package")
    fi
  done
  if (( ${#conflicts[@]} > 0 )); then
    info "Removing packages that conflict with Docker's official packages: ${conflicts[*]}"
    if command -v systemctl >/dev/null 2>&1; then
      as_root systemctl stop docker.service docker.socket >/dev/null 2>&1 || true
    fi
    as_root apt-get remove -y "${conflicts[@]}"
  fi

  as_root install -m 0755 -d /etc/apt/keyrings
  as_root curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  as_root chmod a+r /etc/apt/keyrings/docker.asc

  local ubuntu_suite="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
  [[ -n "$ubuntu_suite" ]] || fail "Ubuntu release codename is missing from /etc/os-release"
  local architecture
  architecture="$(dpkg --print-architecture)"
  printf '%s\n' \
    'Types: deb' \
    'URIs: https://download.docker.com/linux/ubuntu' \
    "Suites: $ubuntu_suite" \
    'Components: stable' \
    "Architectures: $architecture" \
    'Signed-By: /etc/apt/keyrings/docker.asc' \
    | as_root tee /etc/apt/sources.list.d/docker.sources >/dev/null

  as_root apt-get update
  apt_install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  if command -v systemctl >/dev/null 2>&1; then
    as_root systemctl daemon-reload
    as_root systemctl enable --now docker
  else
    as_root service docker start
  fi
}

if (( BUILD_IMAGES == 1 )); then
  install_ubuntu_requirements
fi

initialize_environment
require_command docker
require_command git
require_command curl
require_command base64

docker_compose_available || fail "Docker Compose v2 is missing. Run this script again with --build to install it."

info "Checking Docker engine"
if ! docker info >/dev/null 2>&1; then
  fail "Docker is installed but this user cannot reach the daemon. Run as root or grant this user Docker access."
fi
docker compose version

info "Validating Compose configuration"
compose config --quiet

if command -v ss >/dev/null 2>&1; then
  for port in 3000 8000 9000; do
    if ss -H -ltn "sport = :$port" 2>/dev/null | grep -q .; then
      info "Notice: TCP port $port is already listening; it may belong to an existing lab container"
    fi
  done
fi

if (( BUILD_IMAGES == 1 )); then
  info "Pulling base images and building local images"
  compose build --pull gitea runner prod-app developer
fi

info "Preflight checks passed"
