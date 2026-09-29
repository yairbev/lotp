from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path


def main() -> int:
    collector_url = os.getenv("COLLECTOR_URL", "http://collector:9000")
    canary_path = Path.home() / ".lab-canary"
    canary_value = canary_path.read_text(encoding="utf-8").strip()

    print("Nightjar developer bootstrap complete.")
    payload = {
        "scenario": "developer-targeting",
        "source": "developer-bootstrap",
        "scenario_id": "NJ-DEV-03",
        "event_type": "developer-canary",
        "commit": "working-tree",
        "run_id": "local-bootstrap",
        "host_alias": "developer-workstation",
        "nonce": "nj-dev-03",
        "detail": "Named lab canary read after the developer ran the repository task.",
        "canary_value": canary_value,
    }
    request = urllib.request.Request(
        collector_url.rstrip("/") + "/events",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=4) as response:
        if response.status != 201:
            raise RuntimeError(f"collector returned HTTP {response.status}")
    print("The repository task sent the named lab-only canary to the local receiver.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
