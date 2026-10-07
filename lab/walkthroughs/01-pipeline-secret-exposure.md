# Scenario 1: pipeline secret exposure

This is the main live demonstration. It shows a repository workflow change causing the trusted runner to submit the job’s lab-only repository secret to the local event receiver.

## Clean starting state

From the project root:

```bash
project_root="/opt/lotp"
cd "$project_root"
bash scripts/reset-lab.sh

mkdir -p "$HOME/lotp-lab"
cd "$HOME/lotp-lab"
git clone http://127.0.0.1:3000/demo-admin/nightjar.git
cd nightjar
git config user.name "Nightjar Demo Developer"
git config user.email "developer@example.invalid"
```

If the clone already exists from an earlier attempt, skip `git clone`, change to `$HOME/lotp-lab/nightjar`, and run `git pull --ff-only origin main`.

Confirm the latest Actions run is green, the portal is available, and the event viewer says **No events recorded**.

## Trust boundary

The repository controls the workflow instruction. Gitea supplies `DEMO_BUILD_SECRET` only to the job that references it. The runner executes the changed instruction inside the runner container and can reach `collector:9000` on the private lab network.

## Make and inspect the change

Replace the clean workflow with the prepared, readable example:

```bash
cp "$project_root/demo/scenarios/build-poisoning/.gitea/workflows/build.yml" \
  .gitea/workflows/build.yml

git diff -- .gitea/workflows/build.yml
```

Point out the additional **Publish build diagnostics** step. It maps the repository secret into the job environment and passes it to `tools/report_canary.py`. No application source has changed.

Commit and push the change:

```bash
git add .gitea/workflows/build.yml
git commit -m "demo: expose the pipeline secret [NJ-BUILD-02]"
git push origin main
```

When Git prompts, use the lab account `demo-admin` and the `GITEA_ADMIN_PASSWORD` value from `$project_root/.env`.

## Trigger and expected result

The push automatically starts **Build and deploy Customer Account Portal**. In Gitea, open **Actions** and wait for the run to complete.

Refresh `http://127.0.0.1:9000/events`. One event should show:

- Scenario: `build-poisoning`
- Event: `canary`
- Source: `ci-runner`
- Captured value: the lab’s `DEMO_BUILD_SECRET` value
- Commit: the scenario commit

The pipeline should still package and deploy the portal. That is the central point: the automation performed its normal work and the extra trusted instruction.

## Evidence to inspect

- Gitea commit author, time, changed path, and diff.
- Actions run, triggering commit, runner label, and added step.
- Event receiver timestamp, source, captured value, and commit.
- Portal release panel showing the same commit after deployment.

Ask: who could change the workflow, was independent review required, why was this job allowed the secret, and was the runner expected to contact this destination?

## Reset

```bash
cd "$project_root"
bash scripts/reset-lab.sh
```

Confirm the event viewer is empty and wait for any reset-triggered Actions run to finish.

## How the lab differs from a real incident

The submitted value is fake, the receiver is local, and the workflow change is intentionally obvious. A real compromise might use a less visible data path, short-lived credentials, or an allowed external service. The defensive question remains the same: can the organization connect a sensitive workflow change to the exact run, identity, network activity, artifact, and deployment?
