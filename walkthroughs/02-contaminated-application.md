# Scenario 2: contaminated application

This advanced scenario shows one deployed application change producing two effects: copying the clearly labelled demo login and reading the lab-only values available to the application process.

## Clean starting state

```bash
bash scripts/reset-lab.sh
source scripts/common.sh
initialize_environment
```

Wait for the clean Actions run to finish if reset created a commit. Confirm the portal signs in normally and the event viewer is empty.

## Trust boundary

The pipeline packages application code from the repository and deploys it automatically after tests pass. In this version of the scenario, the source file is changed directly so the mechanism remains easy to inspect. The same behavior could instead be introduced during packaging, which would make the reviewed source and deployed artifact differ.

The deployed application receives only three designated lab values: a demo JWT value, a fake database password, and a named key-canary file. It does not inspect the host or other credential locations.

## Make and inspect the change

```bash
cp demo/scenarios/application-contamination/app/main.py \
  "$SEED_WORKTREE/app/main.py"

seed_git diff -- app/main.py
```

The added login-handler logic posts two structured events to the local receiver. It is disabled during the pipeline tests and becomes active only when the code is running as a deployed release.

Commit and push:

```bash
seed_git add app/main.py
seed_git commit -m "demo: contaminate the deployed portal [NJ-APP-02]"
auth_header="$(basic_auth_header)"
seed_git -c "http.extraHeader=Authorization: Basic $auth_header" push origin main
```

## Trigger and expected result

Wait for the Actions run to complete. Refresh the portal until its release panel shows the new commit, then sign in with the credentials printed on the page:

```text
demo.user / DemoPortal-Only-2026!
```

The login should still succeed. Refresh the event viewer. It should contain two events for the same deployed commit:

1. `login-capture` with the submitted demo username and password.
2. `application-secrets` with the lab-only JWT, database, and key-canary values.

## Evidence to inspect

- The source change and commit in Gitea.
- The successful tests, artifact creation, and deployment run.
- The portal’s commit, run ID, artifact fingerprint, and deployment time.
- Both receiver events and their matching commit and run ID.
- Production-service logs if an expected event is missing:

  ```bash
  docker compose logs --tail=120 prod-app
  ```

Ask: which application identity was used, which configuration values were reachable, which users interacted with this release, and can responders identify every deployment of the artifact?

## Reset

```bash
bash scripts/reset-lab.sh
```

Wait for the clean release to redeploy. Confirm the event viewer is empty, sign in once more, and verify that no new event appears.

## How the lab differs from a real incident

Every credential and configuration value is fake and shown openly. The application reports only the values explicitly provided to its container. It has no host access, command channel, persistence, or ability to read arbitrary customer data. Real impact is limited by the application identity and the systems and data that identity can reach.
