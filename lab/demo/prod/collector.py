from __future__ import annotations

import html
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


DATA_PATH = Path(os.getenv("COLLECTOR_DATA_PATH", "/data/events.jsonl"))
RESET_TOKEN = os.getenv("COLLECTOR_RESET_TOKEN", "local-reset-only")
WRITE_LOCK = threading.Lock()

app = FastAPI(
    title="Living Off the Pipeline Lab Collector",
    description="Local-only receiver that stores and displays submitted lab-only values.",
    version="2.0.0",
)


class LabEvent(BaseModel):
    scenario: str = Field(min_length=1, max_length=48)
    source: str = Field(min_length=1, max_length=48)
    scenario_id: str = Field(pattern=r"^[A-Z0-9-]{3,32}$")
    event_type: str = Field(default="canary", max_length=48)
    commit: str = Field(default="unknown", max_length=64)
    run_id: str = Field(default="unknown", max_length=64)
    host_alias: str = Field(default="lab", max_length=64)
    nonce: str = Field(default="none", max_length=64)
    detail: str = Field(default="", max_length=160)
    canary_value: str = Field(default="", max_length=512)


def _read_events() -> list[dict[str, object]]:
    if not DATA_PATH.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in DATA_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "lab-collector"}


@app.get("/api/events")
def events_api() -> dict[str, object]:
    rows = _read_events()
    return {"count": len(rows), "events": rows}


@app.get("/", response_class=HTMLResponse)
@app.get("/events", response_class=HTMLResponse)
def events_page() -> str:
    rows = list(reversed(_read_events()))
    if rows:
        table_rows = "".join(
            "<tr>"
            f"<td>{html.escape(str(row.get('received_at', '')))}</td>"
            f"<td>{html.escape(str(row.get('scenario', '')))}</td>"
            f"<td>{html.escape(str(row.get('event_type', '')))}</td>"
            f"<td>{html.escape(str(row.get('source', '')))}</td>"
            f"<td><code>{html.escape(str(row.get('canary_value', '')))}</code></td>"
            f"<td><code>{html.escape(str(row.get('commit', ''))[:12])}</code></td>"
            "</tr>"
            for row in rows
        )
    else:
        table_rows = '<tr><td colspan="6" class="empty">No events recorded</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="3">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lab Collector</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #f4f1e9; color: #17212b; }}
    main {{ max-width: 1100px; margin: 48px auto; padding: 0 28px; }}
    h1 {{ margin-bottom: 6px; }}
    p {{ color: #56616c; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 28px; background: #fbfaf6; }}
    th, td {{ padding: 14px; text-align: left; border-bottom: 1px solid #d1ccc2; }}
    th {{ color: #255d84; }}
    .empty {{ text-align: center; padding: 56px; color: #2f7560; font-size: 1.2rem; }}
    code {{ font-size: 0.95rem; }}
  </style>
</head>
<body><main>
  <h1>Lab Collector</h1>
  <p>{len(rows)} event(s). Submitted values are lab-only and intentionally displayed in full.</p>
  <table><thead><tr><th>Received</th><th>Scenario</th><th>Event</th><th>Source</th><th>Captured value</th><th>Commit</th></tr></thead>
  <tbody>{table_rows}</tbody></table>
</main></body></html>"""


@app.post("/events", status_code=201)
def receive_event(event: LabEvent) -> dict[str, object]:
    raw = event.canary_value.encode("utf-8")
    record = event.model_dump()
    record.update(
        {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "canary_present": bool(raw),
            "canary_length": len(raw),
        }
    )
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WRITE_LOCK:
        with DATA_PATH.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps({"event": "lab_event_received", **record}, sort_keys=True), flush=True)
    return {"stored": True, "raw_value_retained": True, "event": record}


@app.delete("/api/events")
@app.delete("/events")
def reset_events(
    x_lab_reset_token: str | None = Header(default=None, alias="X-Lab-Reset-Token"),
) -> Response:
    if x_lab_reset_token != RESET_TOKEN:
        raise HTTPException(status_code=403, detail="invalid reset token")
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WRITE_LOCK:
        DATA_PATH.write_text("", encoding="utf-8")
    return Response(status_code=204)
