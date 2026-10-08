# Lab walkthrough

This is the entry point for reproducing the three presentation scenarios on the dedicated Ubuntu VM. The scripts create and reset the environment; the scenario changes themselves are deliberately manual and visible.

## Before you begin

Use only the lab values and services supplied by this project. Do not place company credentials, source code, tokens, or host data in the VM. Read [docs/SAFETY.md](docs/SAFETY.md) before changing a scenario.

From the repository's `lab` directory, confirm the clean lab is available:

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

The `.runtime/seed-worktree` directory belongs to the lab’s provisioning and reset automation. Do not use it for scenario work. Before Scenario 1, clone the Gitea repository into a separate working directory:

```bash
mkdir -p "$HOME/lotp-lab"
cd "$HOME/lotp-lab"
git clone http://127.0.0.1:3000/demo-admin/nightjar.git
cd nightjar
git config user.name "Nightjar Demo Developer"
git config user.email "developer@example.invalid"
```

All scenario changes, commits, and pushes are performed from `$HOME/lotp-lab/nightjar` with the normal Git CLI. The scenario examples are copied from `/opt/lotp/lab/demo/scenarios/`; adjust the repository path if the project is installed elsewhere.

After `reset-lab.sh` restores Gitea, update the external clone before beginning the next scenario:

```bash
cd "$HOME/lotp-lab/nightjar"
git pull --ff-only origin main
```

## Recommended order

1. [Pipeline secret exposure](walkthroughs/01-pipeline-secret-exposure.md) — main live demonstration.
2. [Contaminated application](walkthroughs/02-contaminated-application.md) — additional live demonstration.
3. [Developer-task contamination](walkthroughs/03-developer-task-contamination.md) — additional live demonstration.

Run the reset command before every scenario, including the first:

```bash
bash scripts/reset-lab.sh
```

The reset restores tracked repository files, clears event records, and refreshes the developer checkout. If it creates a new baseline commit, allow the resulting Actions job to finish before starting the next scenario.

## Validation status

The Ubuntu VM has exercised repository seeding, Gitea login, Actions execution, deployment, portal access, event-receiver access, and all three scenarios. The current files include the reset and developer-container corrections. Recheck the full sequence after a fresh deployment before presenting it.

Use [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) if the observed state differs from a walkthrough.
