# Living Off the Pipeline

Presenter-led security briefing and a local CI/CD lab for showing how trusted development automation can carry an attacker-controlled change.

The clean baseline is running on the Ubuntu VM: Gitea accepts a source change, a Gitea runner tests and packages it, and the production service deploys the resulting release. Three manual scenario walkthroughs and their readable replacement files are included for presenter validation before recording.

## Lab shape

The Ubuntu VM runs four containers on one private Docker network:

- **Gitea** — source control, repository settings, secrets, and Actions history.
- **Runner** — executes `nightjar:host` jobs inside the runner container. It does not receive the host Docker socket.
- **Production service** — combines the deployed customer portal, release watcher, and lab event viewer.
- **Developer workstation** — an isolated Linux checkout used for the developer-targeting demonstration.

The normal flow is:

```text
developer -> Git push -> Gitea -> pipeline job -> release archive -> automatic deployment
```

The release archive crosses from the runner to the production service through a read-only deployment volume. The production service verifies its SHA-256 value before starting it.

## Ubuntu quick start

Prerequisites:

- A dedicated supported Ubuntu VM with internet access during setup.
- Root access or `sudo` permission for package installation.
- At least 6 GB of free memory and 10 GB of free disk space.

Copy this project directory to the VM, then run from its root:

```bash
chmod +x scripts/*.sh
bash scripts/preflight.sh --build
bash scripts/start-lab.sh
```

With `--build`, preflight installs Git, curl, OpenSSL, Docker Engine, Buildx, and Compose v2 when they are missing. It follows Docker's official Ubuntu apt-repository setup. If Ubuntu-provided Docker packages conflict with the official packages, preflight removes those packages first; Docker data under `/var/lib/docker` is not deliberately deleted.

Run the commands as root, or use `sudo bash ...` when the current account does not have Docker access.

The start script creates `.env` when needed, generates a local runner registration token, creates the Gitea administrator and repository, enables Actions, installs a fake pipeline secret, pushes the clean baseline, starts the runner, and waits for the deployment.

Useful commands:

```bash
bash scripts/status-lab.sh
bash scripts/reset-lab.sh
bash scripts/stop-lab.sh
bash scripts/stop-lab.sh --purge
```

`reset-lab.sh` restores the seed repository and developer checkout to the clean template and clears demonstration events. `stop-lab.sh` preserves named volumes. `stop-lab.sh --purge` deletes all lab volumes and the local `.runtime` worktree, but keeps `.env`.

## Open the lab

By default every published port binds only to the Ubuntu VM's loopback interface:

- Gitea repository: `http://127.0.0.1:3000/demo-admin/nightjar`
- Deployed portal: `http://127.0.0.1:8000/`
- Lab event viewer: `http://127.0.0.1:9000/events`

If you operate the VM remotely, create an SSH tunnel from your workstation:

```bash
ssh -L 3000:127.0.0.1:3000 \
    -L 8000:127.0.0.1:8000 \
    -L 9000:127.0.0.1:9000 user@ubuntu-vm
```

Then use the same `127.0.0.1` URLs in your local browser. Changing `LAB_BIND_ADDRESS` to the VM address is possible, but an SSH tunnel is the safer default.

## What is intentionally not automated

The scripts provision and reset the environment. They do not perform scenarios. [WALKTHROUGH.md](WALKTHROUGH.md) links to the manual changes used for:

1. Pipeline secret exposure — the main live demonstration.
2. Application contamination — one deployed change that can illustrate access to application configuration and login data.
3. Developer targeting — repository-controlled code executed when a developer deliberately runs the application or helper command.

All submitted values are lab-only. The event receiver intentionally stores and displays them in full so attendees can see exactly what crossed the boundary. Read [docs/SAFETY.md](docs/SAFETY.md) before adding any scenario material.

## Project map

```text
compose.yaml                    Four-container lab definition
config/runner-config.yaml       Host-mode runner configuration
demo/repository/                Clean repository pushed into Gitea
demo/prod/                      Release manager, portal host, and event viewer
demo/developer/                 Isolated developer workstation
docker/runner/                  Runner image with the build dependencies
scripts/*.sh                    Ubuntu start, status, reset, and stop commands
docs/ARCHITECTURE.md            Boundaries and deployment flow
docs/BUILD-STATUS.md            What has and has not been validated
WALKTHROUGH.md                  Entry point for all three manual scenarios
walkthroughs/                   Scenario-specific steps and expected evidence
slides/                         Current PowerPoint presentation
```

## Public repository contents

The repository is intentionally limited to the runnable lab, its attendee documentation, and the current presentation deck:

- [Living-Off-the-Pipeline-Light-Editorial-Draft-04.pptx](slides/Living-Off-the-Pipeline-Light-Editorial-Draft-04.pptx) is the current deck.
- `.env.example` contains only labelled demo values. The generated `.env`, runtime worktree, events, deployment records, and private key formats are ignored.
- Plans, slide source, speaker-note drafts, templates, visual assets already embedded in the deck, render directories, validation reports, and superseded presentations remain local.
- Future PoC videos may be placed under `recordings/`. GitHub rejects individual files over 100 MB, so larger recordings should be attached to a GitHub Release instead.

Before every public push, run:

```bash
python scripts/validate_project.py .
git status --short --ignored
git diff --cached --check
```

Inspect the staged file list before committing. Never use `git add -f` for ignored configuration, runtime, credential, or build-output paths.

## Current validation boundary

Static validation passes in the shared Windows workspace. The Ubuntu VM has also completed dependency setup, Gitea bootstrap, repository seeding, Actions execution, release deployment, portal access, and event-receiver access. Reset and developer-container corrections are implemented and will be exercised again as part of the newly corrected three-scenario walkthroughs. Record each scenario only after its expected result and reset both succeed on that VM. See [docs/BUILD-STATUS.md](docs/BUILD-STATUS.md).
