# Scenario 2: contaminated application

This advanced scenario shows one deployed application change producing two effects at different moments: reading the lab-only values available to the application as soon as it starts, and copying the clearly labelled demo credentials when a user signs in.

## Clean starting state

```bash
repository_root="/opt/lotp"
lab_root="$repository_root/lab"
cd "$lab_root"
bash scripts/reset-lab.sh
cd "$HOME/lotp-lab/nightjar"
git pull --ff-only origin main
git status --short
```

Wait for the clean Actions run to finish if reset created a commit. Confirm the portal signs in normally and the event viewer is empty.

## Trust boundary

The pipeline packages application code from the repository and deploys it automatically after tests pass. In this version of the scenario, the source file is changed directly so the mechanism remains easy to inspect. The same behavior could instead be introduced during packaging, which would make the reviewed source and deployed artifact differ.

The deployed application receives only three designated lab values: a demo JWT value, a fake database password, and a named key-canary file. It does not inspect the host or other credential locations.

## Make and inspect the change

```bash
cp "$lab_root/demo/scenarios/application-contamination/app/main.py" \
  app/main.py

git diff -- app/main.py
```

The added application-lifespan logic reports the designated application secrets once when the contaminated release starts. Separate login-handler logic reports the submitted demo credentials only when someone signs in. Both behaviors are disabled during pipeline tests and become active only when the code is running as a deployed release.

Commit and push:

```bash
git add app/main.py
git commit -m "demo: contaminate the deployed portal [NJ-APP-02]"
git push origin main
```

When Git prompts, use the lab account `demo-admin` and the `GITEA_ADMIN_PASSWORD` value from `$lab_root/.env`.

## Deployment trigger and expected result

Wait for the Actions run to complete and refresh the portal until its release panel shows the new commit. Before signing in, refresh the event viewer. It should already contain one event:

- `application-secrets` with the lab-only JWT, database, and key-canary values.

This event is produced when the contaminated application process starts; it does not require user activity.

## Login trigger and expected result

Sign in with the credentials printed on the page:

```text
demo.user / DemoPortal-Only-2026!
```

The login should still succeed. Refresh the event viewer. It should now contain a second event for the same deployed commit:

- `login-capture` with the submitted demo username and password.

The final view should show both events: application access exercised at process startup, followed by user credentials captured during login.

## Evidence to inspect

- The source change and commit in Gitea.
- The successful tests, artifact creation, and deployment run.
- The portal’s commit, run ID, artifact fingerprint, and deployment time.
- The application-secrets event appearing before any login.
- The later login-capture event and the matching commit and run ID on both events.
- Production-service logs if an expected event is missing:

  ```bash
  docker compose logs --tail=120 prod-app
  ```

Ask: which application identity was used, which configuration values were reachable, which users interacted with this release, and can responders identify every deployment of the artifact?

## Reset

```bash
cd "$lab_root"
bash scripts/reset-lab.sh
```

Wait for the clean release to redeploy. Confirm the event viewer is empty, sign in once more, and verify that no new event appears.

## How the lab differs from a real incident

Every credential and configuration value is fake and shown openly. The application reports only the values explicitly provided to its container. It has no host access, command channel, persistence, or ability to read arbitrary customer data. Real impact is limited by the application identity and the systems and data that identity can reach.
