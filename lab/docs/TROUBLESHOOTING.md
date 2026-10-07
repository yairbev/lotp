# Troubleshooting the Ubuntu lab

## Docker command or Compose plugin is unavailable

Confirm both commands succeed before continuing:

```bash
docker info
docker compose version
```

If `docker info` fails with a permission error, use an authorized account that can access the Docker daemon. Follow Docker's Ubuntu installation documentation rather than installing an unrelated distribution package.

## Docker reports “no sockets found via socket activation”

This can happen when an earlier `docker.io` removal or Docker CE installation leaves systemd with a stale or inactive `docker.socket` unit while `docker.service` still starts `dockerd -H fd://`.

Repair this one-time systemd state directly on the affected VM:

```bash
systemctl stop docker.service docker.socket || true
systemctl daemon-reload
systemctl reset-failed docker.service docker.socket || true
systemctl enable --now docker.socket
systemctl enable --now docker.service
```

If `docker.socket` is missing rather than merely stale, reinstall the Docker Engine package first with `apt-get install --reinstall docker-ce`, reload systemd, and repeat the commands. None of these commands remove `/var/lib/docker`.

## An image does not build

Run the build again with plain progress and inspect the first failed instruction:

```bash
docker compose build --progress=plain runner prod-app developer
```

The runner image supports both Alpine- and Debian-derived official base images. Do not replace the official Gitea Runner image with an unrelated runner image.

## Gitea starts but the administrator is not created

Inspect Gitea and verify the configuration path:

```bash
docker compose logs --tail=150 gitea
docker compose exec gitea gitea admin user list --config /etc/gitea/app.ini
```

The bootstrap is repeatable: after correcting the issue, rerun `bash scripts/start-lab.sh`.

## Runner does not register

```bash
docker compose logs --tail=150 runner gitea
docker compose exec runner sh -c 'test -f /data/.runner && echo registered'
```

Confirm `GITEA_INSTANCE_URL` remains `http://gitea:3000/` and the generated `GITEA_RUNNER_REGISTRATION_TOKEN` is identical in Gitea and runner containers. A full lab purge generates a clean registration on the next start.

## Workflow remains queued

- Open the repository's Actions page and confirm Actions is enabled.
- Confirm the runner is online and advertises `nightjar`.
- Compare `GITEA_RUNNER_LABELS=nightjar:host` in `.env` with `runs-on: nightjar` in the workflow.
- Inspect `docker compose logs --tail=200 runner`.

The job runs inside the runner container. It does not create another Docker container.

## Build succeeds but the portal is unavailable

```bash
docker compose logs --tail=200 runner prod-app
docker compose exec prod-app sh -c 'cat /srv/releases/current; cat /data/deployment.json'
```

Check that the release archive and SHA-256 file exist under `/srv/releases/releases/<commit>/`. A checksum mismatch is deliberately rejected by the release manager while the event viewer stays available.

## Reset reports that the developer container is restarting

An older developer image may still contain the startup logic that tried to change file ownership after all Linux capabilities were dropped. Rebuild and recreate only that service:

```bash
docker compose build --no-cache developer
docker compose up -d --force-recreate developer
docker compose logs --tail=100 developer
```

The corrected image starts directly as the non-root `developer` user. Rerun `bash scripts/reset-lab.sh` only after `docker compose exec -T developer true` succeeds.

## Reset reports that the seed worktree is missing

The internal `.runtime/seed-worktree` directory is disposable and is intentionally excluded from Git. The current reset script recreates it from the running Gitea repository automatically. Update the lab project on the VM and rerun:

```bash
bash scripts/reset-lab.sh
```

If the automatic clone fails, confirm Gitea is running and reachable at `http://127.0.0.1:3000`, then retry. There is no need to repeat a scenario or manually work inside `.runtime`.

## Reset receives HTTP 403 while clearing events

The current reset script and receiver use the `X-Lab-Reset-Token` header. If the VM is still running an older production-service image, rebuild and recreate it, then retry reset:

```bash
docker compose build prod-app
docker compose up -d --force-recreate prod-app
bash scripts/reset-lab.sh
```

Do not change the token in only one place. `COLLECTOR_RESET_TOKEN` must be identical in `.env` and the running `prod-app` container.

## Repository exists in Gitea but is empty

Rerun `bash scripts/start-lab.sh`. The current startup script detects a missing remote `main` branch and seeds the clean repository even when the Gitea repository object already exists.

## Tests fail with `ModuleNotFoundError: No module named 'app'`

Confirm the repository workflow contains this exact test command:

```bash
PYTHONPATH="$PWD" python -m pytest -q
```

If Gitea still shows the older command, rerun `bash scripts/reset-lab.sh` to restore and push the current clean workflow.

## Port conflict

The default ports are 3000, 8000, and 9000 on `127.0.0.1`. Stop the conflicting local service, or change only the host side of the mapping in `compose.yaml`. Keep the internal container ports and service names unchanged.

## Remote browser cannot connect

Loopback binding is intentional. From your workstation, create an SSH tunnel to the VM:

```bash
ssh -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 -L 9000:127.0.0.1:9000 user@ubuntu-vm
```

Then browse to the local `127.0.0.1` URLs. Exposing the ports on the VM network is optional and should be intentional.

## Return to a known state

Use `bash scripts/reset-lab.sh` to restore the clean repository while keeping Gitea history. For a completely new environment:

```bash
bash scripts/stop-lab.sh --purge
bash scripts/start-lab.sh
```
