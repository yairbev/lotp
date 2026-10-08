# Scenario 3: developer-task contamination

This advanced scenario shows trust moving back toward a developer. Pulling the changed repository does nothing by itself; the boundary is crossed only when the developer deliberately runs the repository-controlled bootstrap task.

## Clean starting state

```bash
repository_root="/opt/lotp"
lab_root="$repository_root/lab"


bash "$lab_root/scripts/reset-lab.sh"
cd "$HOME/lotp-lab/nightjar"
git pull --ff-only origin main
git status --short
```

Confirm the event viewer is empty. Confirm the clean task inside the isolated developer container:

```bash
docker compose -f "$lab_root/compose.yaml" exec -T --user developer developer \
  sh -lc 'cd /home/developer/work/nightjar && python dev/bootstrap.py'
```

It should report that no repository-controlled network action occurred, and the receiver should remain empty.

## Trust boundary

The repository controls `dev/bootstrap.py`. The isolated developer container contains one named fake value at `/home/developer/.lab-canary`. The changed task reads only that file and sends it to the local receiver. It does not scan the developer home directory, SSH files, browser data, environment, or host VM.

## Make and inspect the change

```bash
cp "$lab_root/demo/scenarios/developer-targeting/dev/bootstrap.py" \
  "$HOME/lotp-lab/nightjar/dev/bootstrap.py"

git diff -- dev/bootstrap.py
git add dev/bootstrap.py
git commit -m "demo: change the developer bootstrap [NJ-DEV-03]"
git push origin main
```

When Git prompts, use the lab account `demo-admin` and the `GITEA_ADMIN_PASSWORD` value from `$lab_root/.env`.

The push also starts the normal pipeline, but this scenario’s effect does not depend on that job.

## Pull without executing

Update the isolated developer checkout:

```bash
docker compose -f "$lab_root/compose.yaml" exec -T --user developer developer \
  sh -lc 'cd /home/developer/work/nightjar && git pull --ff-only'
```

Refresh the event viewer. It should still say **No events recorded**. This is an important pause for the presentation: the pull changed files but did not execute the bootstrap code.

## Run the trusted task

```bash
docker compose -f "$lab_root/compose.yaml" exec -T --user developer developer \
  sh -lc 'cd /home/developer/work/nightjar && python dev/bootstrap.py'
```

Refresh the event viewer. One event should show:

- Scenario: `developer-targeting`
- Event: `developer-canary`
- Source: `developer-bootstrap`
- Captured value: `LAB_ONLY_DEVELOPER_CANARY`
- Host alias: `developer-workstation` in the API record

## Evidence to inspect

- Gitea commit and the change to an executable development path.
- The developer’s explicit `python dev/bootstrap.py` command.
- The receiver event time, source, fixed host alias, and captured lab value.
- The absence of an event between `git pull` and task execution.

Ask: which development tasks run repository code, which developers invoked the affected version, what those processes could access, and whether their network destinations are monitored.

## Reset

```bash
bash "$lab_root/scripts/reset-lab.sh"
```

The reset restores the clean Git version, refreshes the developer checkout, and clears events. Run the clean bootstrap once more and confirm the receiver stays empty.

## How the lab differs from a real incident

The task reads one fixed fake file from an isolated container and contacts only the local receiver. It contains no credential discovery, arbitrary command execution, persistence, or external callback. A real development environment may expose broader access, which is why repository-controlled setup, build, test, package, IDE, and start tasks deserve explicit review and monitoring.
