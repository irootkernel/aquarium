import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "plugins/aquarium/skills/dev-aquarium/scripts"
CLI = SCRIPT_DIR / "dev_aquarium.py"
sys.path.insert(0, str(SCRIPT_DIR))

from dev_manager import process_queue, queue_request

PRODUCER = r"""import hashlib
import json
import os
import subprocess
from pathlib import Path

output = Path(os.environ["AQUARIUM_DEV_OUTPUT"])
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
artifact = output / "plugin"
artifact.mkdir()
(artifact / "payload.txt").write_text(f"artifact {sha}\n", encoding="utf-8")
file_digest = hashlib.sha256((artifact / "payload.txt").read_bytes()).digest()
tree = hashlib.sha256()
tree.update(b"payload.txt\0")
tree.update(file_digest)
tree.update(b"\n")
mode = os.environ.get("AQUARIUM_TEST_MODE", "success")
manifest = {
    "schema": "aquarium-dev-artifact-manifest/v1",
    "project_id": "aquarium",
    "git_sha": sha,
    "development_version": f"v0.1.14-dev.{sha[:12]}",
    "artifact_kind": "codex-plugin",
    "artifact_path": "plugin",
    "sha256": f"sha256:{tree.hexdigest()}",
}
if mode == "checksum":
    manifest["sha256"] = "sha256:" + "0" * 64
elif mode == "sha":
    manifest["git_sha"] = "0" * 40
elif mode == "build":
    raise SystemExit(1)
print(json.dumps(manifest, sort_keys=True))
"""


def create_repository(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", path], check=True)
    subprocess.run(["git", "-C", path, "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", path, "config", "user.email", "test@example.invalid"],
        check=True,
    )
    (path / "Makefile").write_text(
        """aquarium-dev-describe:
\t@printf '%s\\n' '{"schema":"aquarium-dev-producer-description/v1","project_id":"aquarium","next_version":"v0.1.14","artifact_kind":"codex-plugin","artifact_path":"plugin"}'

aquarium-dev-build:
\t@python3 producer.py
""",
        encoding="utf-8",
    )
    (path / "producer.py").write_text(PRODUCER, encoding="utf-8")
    subprocess.run(["git", "-C", path, "add", "."], check=True)
    subprocess.run(["git", "-C", path, "commit", "-q", "-m", "initial"], check=True)
    return path


def run_cli(host_root: Path, *arguments: str, mode: str = "success"):
    environment = os.environ.copy()
    environment["AQUARIUM_TEST_MODE"] = mode
    return subprocess.run(
        [sys.executable, CLI, "--host-root", host_root, *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def payload(result: subprocess.CompletedProcess[str]):
    return json.loads(result.stdout or result.stderr)


def enroll(repository: Path, host_root: Path) -> None:
    result = run_cli(
        host_root,
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    assert result.returncode == 0, result.stderr


def test_rebuild_requires_approval_and_publishes_validated_generation(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)

    rejected = run_cli(host_root, "rebuild", "--repository", repository)
    result = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )

    assert rejected.returncode == 2
    assert payload(rejected)["error"]["code"] == "approval_required"
    assert result.returncode == 0, result.stderr
    sha = subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()
    current = host_root / "current/aquarium"
    assert current.is_symlink()
    assert current.resolve() == host_root / "artifacts/aquarium" / sha
    manifest = json.loads((current / ".aquarium-manifest.json").read_text())
    assert manifest["git_sha"] == sha
    assert (current / "plugin/payload.txt").read_text() == f"artifact {sha}\n"


def test_aquarium_rebuild_retains_previous_marketplace_until_configuration(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    first = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )
    first_sha = payload(first)["details"]["git_sha"]
    marker = repository / "revision.txt"
    marker.write_text("next", encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", marker.name], check=True)
    subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--no-verify", "-m", "next"],
        check=True,
    )

    second = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )

    assert second.returncode == 0, second.stderr
    assert (host_root / "artifacts/aquarium" / first_sha).is_dir()


def test_failed_rebuild_preserves_previous_selector_and_writes_diagnostic(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    assert (
        run_cli(
            host_root,
            "rebuild",
            "--repository",
            repository,
            "--approve-build",
        ).returncode
        == 0
    )
    original = os.readlink(host_root / "current/aquarium")

    result = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
        mode="checksum",
    )

    assert result.returncode == 1
    assert payload(result)["error"]["code"] == "checksum_mismatch"
    assert os.readlink(host_root / "current/aquarium") == original
    diagnostic = json.loads(
        (host_root / "diagnostics/aquarium/latest.json").read_text()
    )
    assert diagnostic["code"] == "checksum_mismatch"
    assert diagnostic["stage"] == "validate"
    assert len(diagnostic["message"]) <= 1000


def test_manifest_identity_mismatch_never_exposes_staging(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)

    result = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
        mode="sha",
    )

    assert result.returncode == 1
    assert payload(result)["error"]["code"] == "producer_manifest_invalid"
    assert not (host_root / "current/aquarium").exists()
    assert not list((host_root / "artifacts/aquarium").glob(".staging-*"))


def test_duplicate_requests_coalesce_and_worker_publishes_once(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)

    first_status, first = queue_request(repository, host_root, CLI, spawn_worker=False)
    second_status, second = queue_request(
        repository, host_root, CLI, spawn_worker=False
    )
    status, details = process_queue("aquarium", host_root)

    assert first_status == "success"
    assert second_status == "no-change"
    assert first == second
    assert status == "success"
    assert details["processed"] == 1
    assert details["published"] == 1
    assert not list((host_root / "queue/aquarium").glob("*.json"))


def test_request_rejects_dirty_checkout_and_runs_asynchronously(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    (repository / "dirty.txt").write_text("dirty", encoding="utf-8")
    rejected = run_cli(host_root, "request", "--repository", repository)
    assert rejected.returncode == 1
    assert payload(rejected)["error"]["code"] == "dirty_worktree"
    diagnostic = json.loads(
        (host_root / "diagnostics/aquarium/latest.json").read_text()
    )
    assert (
        diagnostic["git_sha"]
        == subprocess.check_output(
            ["git", "-C", repository, "rev-parse", "HEAD"], text=True
        ).strip()
    )
    (repository / "dirty.txt").unlink()

    requested = run_cli(host_root, "request", "--repository", repository)

    assert requested.returncode == 0, requested.stderr
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if (host_root / "current/aquarium").is_symlink():
            break
        time.sleep(0.05)
    assert (host_root / "current/aquarium").is_symlink()
