# Build and validation status

Status updated on 2026-09-29.

## Implemented

- Four-container Compose design: Gitea, host-mode runner, combined production/event service, and isolated developer workstation.
- No Docker socket and no separate attacker or collector container.
- Gitea administrator, repository, Actions, runner, and fake repository-secret bootstrap.
- Clean workflow that checks out the triggering commit, runs tests, packages a release, hashes it, and deploys it automatically.
- Production release manager that verifies SHA-256 and reloads the portal.
- Event receiver that intentionally displays submitted lab-only values in full.
- Loopback-only published ports and an SSH-tunnel access pattern.
- Start, status, reset, stop, and purge shell scripts.
- Ubuntu dependency bootstrap for Git, curl, OpenSSL, Docker Engine, Buildx, and Compose v2.
- Three manual walkthroughs with compatible, readable scenario replacement files.

## Verified in the shared authoring workspace

- Python source parses successfully.
- JSON and JSONL support files parse successfully.
- The project validator passes.
- Compose contains no Docker socket mount or obsolete receiver port.
- Workflow and runner labels agree on `nightjar`.
- The runner configuration uses host mode inside the runner container.
- Every project-owned Markdown file has been reviewed against the current architecture and lab behavior.

## Exercised on the Ubuntu VM during development

- Docker and Compose installation and recovery from the earlier socket-activation issue.
- Gitea startup and login with `demo-admin`.
- Creation and seeding of the `nightjar` repository on `main`.
- Runner execution of the readable tests after correcting the Python import path.
- Release packaging and automatic deployment to the portal.
- Event-receiver readiness and reset authorization.
- Repository restoration reached Gitea after correcting command-scoped Git safe-directory handling.
- Event clearing succeeded after aligning the reset-request header.

## Final corrections verified

- The developer image starts directly as the non-root `developer` user and no longer attempts a forbidden ownership change under `cap_drop: ALL`.
- Reset fails clearly if the developer container is unavailable instead of reporting a successful complete reset.
- The walkthrough replacement files use port 9000, the deployed workflow, raw lab-only values, and the named developer canary.

## Scenario validation

The presenter completed all three walkthroughs successfully in order from [WALKTHROUGH.md](../WALKTHROUGH.md):

1. Pipeline secret exposure.
2. Contaminated application.
3. Developer-task contamination.

Each scenario produced its documented result, and the fallback recordings are stored under `presentation/recordings/` at the repository root.

If a scenario fails, capture this output before changing or purging anything:

```bash
docker compose ps
docker compose logs --tail=200 gitea runner prod-app developer
curl -fsS http://127.0.0.1:8000/api/release
curl -fsS http://127.0.0.1:9000/api/events
```

## Packaged artifacts

- Approved deck: `presentation/Living-Off-the-Pipeline.pptx` at the repository root.
- Scenario recordings: `presentation/recordings/` at the repository root.
- Runnable lab: the current `lab/` directory.
