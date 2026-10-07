# Safety and authorization

## Authorized use

Run this project only on a machine and Docker environment you are authorized to control. It is designed for a local presentation lab. Do not point scripts, callbacks, credentials, or Git remotes at company systems.

## Built-in constraints

- Every credential and secret is lab-only and labeled for demonstration use.
- Network listeners bind to loopback on the host.
- The callback receiver accepts structured events and never issues commands.
- Submitted values must remain fake and lab-only because the demo receiver stores and displays them in full.
- The developer event uses a fixed host alias instead of the workstation hostname.
- Scenario files contain no persistence, credential collection, arbitrary command channel, or evasion logic.
- `scripts/validate_project.py` checks selected safety invariants and high-risk capability phrases.

## Runner boundary

The runner does not mount `/var/run/docker.sock`. Jobs labeled `nightjar:host` execute inside the runner container, so repository-controlled workflow commands can affect that container and its mounted runner/release volumes, but they do not directly control the Ubuntu Docker daemon.

Use a dedicated VM, place no company credentials on it, and do not reuse the environment as a shared production runner. The lab intentionally demonstrates why CI runners and their credentials are high-trust assets even without a Docker socket.

## Network validation

The default Compose file does not publish services beyond loopback. Docker networks can still provide outbound access through the host. For a strictly offline delivery:

- Pre-pull and build all images with `bash scripts/preflight.sh --build` while connected.
- Disconnect or block external networking during rehearsal and delivery.
- Confirm the baseline and all three scenarios work after disconnection.
- Do not add external collector URLs, webhooks, package installs, or action downloads to a scenario.

## Data handling

- Never place real tokens, hostnames, email addresses, or source code in `.env` or the seed repository.
- Review screenshots and recordings for notifications, browser history, personal bookmarks, terminal paths, and workstation names.
- Purge disposable state with `bash scripts/stop-lab.sh --purge` after recording or delivery.
- Keep only sanitized logs required for the deck or follow-up.

## Stop conditions

Stop the demonstration if any event targets a non-loopback host address or a destination outside `lotp_lab`, if an unexpected credential appears, or if a scenario executes outside the disposable worktree and lab containers.
