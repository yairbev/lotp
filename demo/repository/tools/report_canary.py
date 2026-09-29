from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request


def post_event(url: str, payload: dict[str, str]) -> None:
    request = urllib.request.Request(
        url.rstrip("/") + "/events",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=4) as response:
        if response.status != 201:
            raise RuntimeError(f"collector returned HTTP {response.status}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a harmless event to the local lab collector.")
    parser.add_argument("scenario", choices=["build-poisoning", "developer-targeting"])
    parser.add_argument("--collector-url", required=True)
    parser.add_argument("--canary", default="")
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--source", choices=["ci-runner", "developer-bootstrap"], required=True)
    parser.add_argument("--commit", default=os.getenv("GITHUB_SHA", "unknown"))
    parser.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", "unknown"))
    args = parser.parse_args()

    payload = {
        "scenario": args.scenario,
        "source": args.source,
        "scenario_id": args.scenario_id,
        "commit": args.commit,
        "run_id": args.run_id,
        "host_alias": "nightjar-runner" if args.source == "ci-runner" else "developer-workstation",
        "nonce": args.scenario_id.lower(),
        "canary_value": args.canary,
    }
    post_event(args.collector_url, payload)
    print(f"Sent {args.scenario_id}; the demo receiver displays the submitted lab-only value.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
