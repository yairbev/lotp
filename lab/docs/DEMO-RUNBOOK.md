# Lab rehearsal runbook

This runbook covers environment readiness and the normal automated deployment. Use [WALKTHROUGH.md](../WALKTHROUGH.md) for the three manual scenario demonstrations.

## First deployment

From the copied project directory on the Ubuntu VM:

```bash
chmod +x scripts/*.sh
bash scripts/preflight.sh --build
bash scripts/start-lab.sh
bash scripts/status-lab.sh
```

If you connect remotely, open a second terminal on your workstation and keep this tunnel running:

```bash
ssh -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 -L 9000:127.0.0.1:9000 user@ubuntu-vm
```

## Acceptance checks

1. Open `http://127.0.0.1:3000/demo-admin/nightjar` and sign in with the lab credentials printed by `start-lab.sh`.
2. Open Actions and confirm **Build and deploy Customer Account Portal** completed successfully.
3. Open `http://127.0.0.1:8000/` and confirm the release panel shows a commit, run ID, artifact fingerprint, and deployment time.
4. Open `http://127.0.0.1:9000/events` and confirm the clean baseline contains no attack event.
5. Run:

   ```bash
   docker compose exec --user developer developer \
     sh -lc 'cd /home/developer/work/nightjar && git log -1 --oneline && python dev/bootstrap.py'
   ```

   Confirm the repository exists and the baseline bootstrap reports that no repository-controlled network action occurred.

## Evidence to capture for troubleshooting

Before restarting or purging a failed lab, save:

```bash
docker compose ps
docker compose logs --tail=200 gitea runner prod-app developer
curl -fsS http://127.0.0.1:8000/api/release
curl -fsS http://127.0.0.1:9000/api/events
```

## Reset and repeatability

After the first successful deployment:

```bash
bash scripts/reset-lab.sh
bash scripts/status-lab.sh
bash scripts/stop-lab.sh
bash scripts/start-lab.sh
```

The preserved restart should return the same repository and deployment state. Use `bash scripts/stop-lab.sh --purge` only when you intentionally want a completely fresh lab; it deletes the named volumes and `.runtime` worktree.

## Scenario and recording preparation

Complete all three walkthroughs from a reset baseline before recording. The compatible replacement files under `demo/scenarios/` are applied manually by the walkthroughs; no script performs a scenario. Record only after the expected evidence and reset behavior have both succeeded on the presentation VM.
