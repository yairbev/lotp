from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


REQUIRED = [
    "README.md",
    "PLAN.md",
    "WALKTHROUGH.md",
    ".gitignore",
    ".dockerignore",
    ".gitattributes",
    "compose.yaml",
    ".dockerignore",
    ".env.example",
    "config/runner-config.yaml",
    "docker/gitea/Dockerfile",
    "docker/runner/Dockerfile",
    "demo/developer/Dockerfile",
    "demo/prod/Dockerfile",
    "demo/prod/collector.py",
    "demo/prod/supervisor.py",
    "demo/repository/.gitea/workflows/build.yml",
    "demo/repository/app/main.py",
    "demo/scenarios/build-poisoning/.gitea/workflows/build.yml",
    "demo/scenarios/application-contamination/app/main.py",
    "demo/scenarios/developer-targeting/dev/bootstrap.py",
    "scripts/common.sh",
    "scripts/preflight.sh",
    "scripts/start-lab.sh",
    "scripts/status-lab.sh",
    "scripts/reset-lab.sh",
    "scripts/stop-lab.sh",
    "docs/ARCHITECTURE.md",
    "docs/SAFETY.md",
    "walkthroughs/01-pipeline-secret-exposure.md",
    "walkthroughs/02-contaminated-application.md",
    "walkthroughs/03-developer-task-contamination.md",
]

FORBIDDEN_CAPABILITIES = [
    "meterpreter",
    "cobalt strike",
    "powershell -enc",
    "/dev/tcp/",
]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    for relative in REQUIRED:
        if not (root / relative).is_file():
            errors.append(f"missing required artifact: {relative}")

    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append(f"invalid Python: {relative}: {exc}")

    for path in root.rglob("*.json"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"invalid JSON: {relative}: {exc}")

    for path in root.rglob("*.jsonl"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSONL: {relative}:{index}: {exc}")

    anchors = {
        "compose.yaml": [
            "gitea:",
            "runner:",
            "prod-app:",
            "developer:",
            "releases:/srv/releases",
        ],
        "config/runner-config.yaml": ["runner:", "host:", "/data/work"],
        "demo/repository/.gitea/workflows/build.yml": [
            "runs-on: nightjar",
            "pytest -q",
            "release.tar.gz",
            "LAB_RELEASE_ROOT/current",
        ],
        "demo/scenarios/build-poisoning/.gitea/workflows/build.yml": [
            "secrets.DEMO_BUILD_SECRET",
            "http://collector:9000",
            "release.tar.gz",
        ],
        "demo/scenarios/application-contamination/app/main.py": [
            "login-capture",
            "application-secrets",
            "http://collector:9000",
        ],
        "demo/scenarios/developer-targeting/dev/bootstrap.py": [
            ".lab-canary",
            "http://collector:9000",
            "developer-canary",
        ],
    }
    for relative, expected in anchors.items():
        path = root / relative
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        if "\t" in content:
            errors.append(f"tab indentation in YAML: {relative}")
        for text in expected:
            if text not in content:
                errors.append(f"missing expected text {text!r} in {relative}")

    compose_text = (root / "compose.yaml").read_text(encoding="utf-8")
    if "/var/run/docker.sock" in compose_text:
        errors.append("compose.yaml must not mount the host Docker socket")
    if "8088" in compose_text:
        errors.append("obsolete collector port 8088 remains in compose.yaml")

    collector_text = (root / "demo/prod/collector.py").read_text(encoding="utf-8")
    if "record = event.model_dump()" not in collector_text or '"raw_value_retained": True' not in collector_text:
        errors.append("demo receiver must retain and display the submitted lab-only value")
    if 'alias="X-Lab-Reset-Token"' not in collector_text:
        errors.append("demo receiver and reset script must agree on the X-Lab-Reset-Token header")

    reset_text = (root / "scripts/reset-lab.sh").read_text(encoding="utf-8")
    if "fetch origin main" not in reset_text or "reset --hard origin/main" not in reset_text:
        errors.append("reset script must synchronize its internal worktree before restoring the baseline")
    if (
        "Recreating the internal reset worktree from Gitea" not in reset_text
        or '"$remote_git_url" "$SEED_WORKTREE"' not in reset_text
    ):
        errors.append("reset script must recreate a missing internal worktree from Gitea")

    gitignore_text = (root / ".gitignore").read_text(encoding="utf-8")
    for expected in [
        "/*",
        "!/.env.example",
        "!/compose.yaml",
        "!/demo/",
        "!/docker/",
        "!/scripts/",
        "!/walkthroughs/",
        "!/slides/Living-Off-the-Pipeline-Light-Editorial-Draft-04.pptx",
        "!/recordings/*.mp4",
        "/DummyFileShare/",
        "/build_dummy_file_share.py",
    ]:
        if expected not in gitignore_text:
            errors.append(f".gitignore is missing publication guard {expected!r}")

    dockerignore_text = (root / ".dockerignore").read_text(encoding="utf-8")
    for expected in [
        "**",
        "!docker/gitea/Dockerfile",
        "!docker/runner/Dockerfile",
        "!demo/developer/entrypoint.sh",
        "!demo/prod/collector.py",
        "!demo/prod/supervisor.py",
        "!demo/repository/requirements.txt",
        "!demo/repository/requirements-dev.txt",
    ]:
        if expected not in dockerignore_text:
            errors.append(f".dockerignore is missing build-context rule {expected!r}")

    dockerfiles = [
        root / "docker/gitea/Dockerfile",
        root / "docker/runner/Dockerfile",
        root / "demo/prod/Dockerfile",
        root / "demo/developer/Dockerfile",
    ]
    for dockerfile in dockerfiles:
        if dockerfile.exists() and "vim" not in dockerfile.read_text(encoding="utf-8"):
            errors.append(f"vim is missing from container image: {dockerfile.relative_to(root)}")

    forbidden_public_paths = ["DummyFileShare", "dummy_file_share"]
    for name in forbidden_public_paths:
        if (root / name).exists():
            errors.append(f"unrelated dummy file-share path remains: {name}")
    for path in root.rglob("build_dummy_file_share.py"):
        if path.is_file():
            errors.append(f"unrelated dummy file-share generator remains: {path.relative_to(root)}")

    public_text_suffixes = {".md", ".sh", ".py", ".yml", ".yaml", ".json", ".jsonl", ".mjs"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in public_text_suffixes:
            continue
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts) or "node_modules" in relative.parts:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if "C:\\Users\\" in content:
            errors.append(f"local Windows user path remains in publishable source: {relative}")

    scan_suffixes = {".sh", ".ps1", ".py", ".yml", ".yaml"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in scan_suffixes:
            continue
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in FORBIDDEN_CAPABILITIES:
            if phrase in content and path.name != "validate_project.py":
                errors.append(f"forbidden capability phrase {phrase!r} in {relative}")

    for relative in [path for path in REQUIRED if path.endswith(".sh")]:
        content = (root / relative).read_bytes()
        if not content.startswith(b"#!/usr/bin/env bash\n"):
            errors.append(f"shell script lacks a Bash/LF shebang: {relative}")
        if b"\r\n" in content:
            errors.append(f"shell script contains CRLF line endings: {relative}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("Static project checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
