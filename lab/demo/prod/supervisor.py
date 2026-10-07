from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path


RELEASE_ROOT = Path(os.getenv("RELEASE_ROOT", "/srv/releases"))
RUNTIME_ROOT = Path(os.getenv("RUNTIME_ROOT", "/srv/runtime"))
DATA_ROOT = Path("/data")
MARKER = RELEASE_ROOT / "current"

stopping = False
collector_process: subprocess.Popen[str] | None = None
app_process: subprocess.Popen[str] | None = None
active_release: str | None = None


def log(message: str) -> None:
    print(f"[release-manager] {message}", flush=True)


def stop_process(process: subprocess.Popen[str] | None, name: str) -> None:
    if process is None or process.poll() is not None:
        return
    log(f"stopping {name}")
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def handle_signal(_signum: int, _frame: object) -> None:
    global stopping
    stopping = True


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(destination, filter="data")


def deploy(release_id: str) -> None:
    global app_process, active_release

    release_dir = RELEASE_ROOT / "releases" / release_id
    archive_path = release_dir / "release.tar.gz"
    checksum_path = release_dir / "release.sha256"
    if not archive_path.is_file() or not checksum_path.is_file():
        raise RuntimeError(f"release {release_id} is incomplete")

    expected = checksum_path.read_text(encoding="utf-8").split()[0]
    actual = sha256(archive_path)
    if actual != expected:
        raise RuntimeError(f"release {release_id} failed checksum verification")

    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{release_id[:12]}-", dir=RUNTIME_ROOT))
    try:
        safe_extract(archive_path, temp_dir)
        metadata_path = temp_dir / "release.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}

        stop_process(app_process, "application")
        app_env = os.environ.copy()
        app_env.update(
            {
                "RELEASE_COMMIT": str(metadata.get("commit", release_id)),
                "RELEASE_RUN_ID": str(metadata.get("run_id", "unknown")),
                "RELEASE_ARTIFACT_SHA256": actual,
                "RELEASE_DEPLOYED_AT": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        app_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"],
            cwd=temp_dir,
            env=app_env,
            text=True,
        )
        active_release = release_id
        deployment = {
            "release_id": release_id,
            "commit": app_env["RELEASE_COMMIT"],
            "run_id": app_env["RELEASE_RUN_ID"],
            "artifact_sha256": actual,
            "deployed_at": app_env["RELEASE_DEPLOYED_AT"],
        }
        temp_record = DATA_ROOT / "deployment.json.tmp"
        temp_record.write_text(json.dumps(deployment, indent=2) + "\n", encoding="utf-8")
        temp_record.replace(DATA_ROOT / "deployment.json")
        log(f"deployed {release_id[:12]} with artifact {actual[:12]}")
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def main() -> int:
    global collector_process, app_process, active_release
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)

    collector_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "collector:app", "--host", "0.0.0.0", "--port", "9000", "--no-access-log"],
        cwd=Path(__file__).parent,
        text=True,
    )
    log("collector started on port 9000")

    last_error: str | None = None
    while not stopping:
        if collector_process.poll() is not None:
            log("collector stopped unexpectedly")
            break
        try:
            release_id = MARKER.read_text(encoding="utf-8").strip() if MARKER.exists() else ""
            if release_id and (release_id != active_release or app_process is None or app_process.poll() is not None):
                deploy(release_id)
                last_error = None
        except Exception as exc:  # keep collector available while a bad release is investigated
            message = str(exc)
            if message != last_error:
                log(f"deployment pending: {message}")
                last_error = message
        time.sleep(2)

    stop_process(app_process, "application")
    stop_process(collector_process, "collector")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
