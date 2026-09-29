# Lab walkthrough

This is the entry point for reproducing the three presentation scenarios on the dedicated Ubuntu VM. The scripts create and reset the environment; the scenario changes themselves are deliberately manual and visible.

## Before you begin

Use only the lab values and services supplied by this project. Do not place company credentials, source code, tokens, or host data in the VM. Read [docs/SAFETY.md](docs/SAFETY.md) before changing a scenario.

From the project root, confirm the clean lab is available:

```bash
bash scripts/start-lab.sh
bash scripts/status-lab.sh
```

Open these pages, directly on the VM or through the SSH tunnel described in [README.md](README.md):

- Gitea: `http://127.0.0.1:3000/demo-admin/nightjar`
- Customer portal: `http://127.0.0.1:8000/`
- Event viewer: `http://127.0.0.1:9000/events`

The Gitea username is `demo-admin`; the password is the `GITEA_ADMIN_PASSWORD` value in the local `.env` file.

## How the manual changes work

The scenario examples under `demo/scenarios/` are readable replacement files. Each walkthrough has you copy one file into the seed worktree, inspect the Git diff, commit it, and push it. There is intentionally no script that performs a complete scenario.

The commands use the project’s Git helper so the exact `.runtime/seed-worktree` path is trusted only for that command. At the beginning of each terminal session, load the helpers:

```bash
cd /opt/presentation
source scripts/common.sh
initialize_environment
```

If you copied the project elsewhere, use that path instead of `/opt/presentation`.

## Recommended order

1. [Pipeline secret exposure](walkthroughs/01-pipeline-secret-exposure.md) — main live demonstration.
2. [Contaminated application](walkthroughs/02-contaminated-application.md) — advanced recorded scenario.
3. [Developer-task contamination](walkthroughs/03-developer-task-contamination.md) — advanced recorded scenario.

Run the reset command before every scenario, including the first:

```bash
bash scripts/reset-lab.sh
```

The reset restores tracked repository files, clears event records, and refreshes the developer checkout. If it creates a new baseline commit, allow the resulting Actions job to finish before starting the next scenario.

## Validation status

The Ubuntu VM has exercised repository seeding, Gitea login, Actions execution, deployment, portal access, and event-receiver access. Reset and developer-container corrections are included in the current files and will be rechecked while validating these walkthroughs. Record a scenario only after its expected result and reset have both succeeded on that VM.

Use [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) if the observed state differs from a walkthrough.
