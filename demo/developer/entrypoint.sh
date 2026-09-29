#!/usr/bin/env bash
set -euo pipefail

mkdir -p /home/developer/work
printf '%s\n' "${DEMO_DEVELOPER_CANARY:-LAB_ONLY_DEVELOPER_CANARY}" > /home/developer/.lab-canary
chmod 0600 /home/developer/.lab-canary

exec sleep infinity
