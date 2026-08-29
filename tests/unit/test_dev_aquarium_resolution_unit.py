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

from dev_manager import resolve_artifact  # isort: skip


PRODUCER = r'''import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

output = Path(os.environ["AQUARIUM_DEV_OUTPUT"])
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
artifact = output / "bin/tool"
artifact.parent.mkdir()
artifact.write_text("""#!/bin/sh
if [ "$1" = hold ]; then
  : > "$AQUARIUM_TEST_READY"
  trap 'exit 0' TERM INT
  while :; do sleep 0.05; done
fi
printf '%s\\n' 'development tool'
""", encoding="utf-8")
artifact.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
manifest = {
    "schema": "aquarium-dev-artifact-manifest/v1",
    "project_id": "podway",
    "git_sha": sha,
    "development_version": f"v0.2.7-dev.{sha[:12]}",
    "artifact_kind": "executable",
    "artifact_path": "bin/tool",
    "sha256": "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
}
print(json.dumps(manifest, sort_keys=True))
'''


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
\t@printf '%s\\n' '{"schema":"aquarium-dev-producer-description/v1","project_id":"podway","next_version":"v0.2.7","artifact_kind":"executable","artifact_path":"bin/tool"}'

aquarium-dev-build:
\t@python3 producer.py
""",
        encoding="utf-8",
    )
    (path / "producer.py").write_text(PRODUCER, encoding="utf-8")
    subprocess.run(["git", "-C", path, "add", "."], check=True)
    subprocess.run(["git", "-C", path, "commit", "-q", "-m", "initial"], check=True)
    return path


def run_cli(host_root: Path, *arguments: str, environment=None):
    return subprocess.run(
        [sys.executable, CLI, "--host-root", host_root, *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def payload(result: subprocess.CompletedProcess[str]):
    return json.loads(result.stdout or result.stderr)


def enroll_and_build(repository: Path, host_root: Path) -> str:
    enrolled = run_cli(
        host_root,
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    assert enrolled.returncode == 0, enrolled.stderr
    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )
    assert rebuilt.returncode == 0, rebuilt.stderr
    return payload(rebuilt)["details"]["git_sha"]


def commit_next_revision(repository: Path) -> str:
    marker = repository / "revision.txt"
    marker.write_text(str(time.monotonic_ns()), encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", marker.name], check=True)
    subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--no-verify", "-m", "next"],
        check=True,
    )
    return subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()


def wait_missing(path: Path) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and path.exists():
        time.sleep(0.05)
    assert not path.exists()


def test_stable_fallback_is_allowed_only_without_enrollment(tmp_path):
    host_root = tmp_path / "host"
    stable = tmp_path / "stable"
    stable.write_text("stable", encoding="utf-8")

    result = run_cli(
        host_root,
        "resolve",
        "--project-id",
        "podway",
        "--stable",
        stable,
    )

    assert result.returncode == 0
    assert payload(result)["details"]["source"] == "stable"

    repository = create_repository(tmp_path / "repository")
    enrolled = run_cli(
        host_root,
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    assert enrolled.returncode == 0
    rejected = run_cli(
        host_root,
        "resolve",
        "--project-id",
        "podway",
        "--stable",
        stable,
    )
    assert rejected.returncode == 1
    assert payload(rejected)["error"]["code"] == "artifact_missing"


def test_resolution_fails_closed_on_corrupt_enrolled_artifact(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll_and_build(repository, host_root)
    artifact = (host_root / "current/podway/bin/tool").resolve()
    artifact.write_text("corrupt", encoding="utf-8")

    result = run_cli(host_root, "resolve", "--project-id", "podway")

    assert result.returncode == 1
    assert payload(result)["error"]["code"] == "checksum_mismatch"


def test_shared_resolution_lease_defers_cleanup_until_release(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    first_sha = enroll_and_build(repository, host_root)
    first_generation = host_root / "artifacts/podway" / first_sha
    first_resolution = resolve_artifact("podway", host_root)
    second_resolution = resolve_artifact("podway", host_root)
    second_sha = commit_next_revision(repository)

    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )

    assert rebuilt.returncode == 0, rebuilt.stderr
    assert (host_root / "current/podway").resolve().name == second_sha
    assert first_generation.exists()
    assert first_resolution.git_sha == first_sha
    assert second_resolution.git_sha == first_sha
    first_resolution.close()
    assert first_generation.exists()
    second_resolution.close()
    wait_missing(first_generation)


def test_publication_immediately_removes_an_unleased_generation(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    first_sha = enroll_and_build(repository, host_root)
    first_generation = host_root / "artifacts/podway" / first_sha
    commit_next_revision(repository)

    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )

    assert rebuilt.returncode == 0, rebuilt.stderr
    assert not first_generation.exists()


def test_launch_holds_lease_through_child_interruption(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    first_sha = enroll_and_build(repository, host_root)
    first_generation = host_root / "artifacts/podway" / first_sha
    ready = tmp_path / "ready"
    environment = os.environ.copy()
    environment["AQUARIUM_TEST_READY"] = str(ready)
    child = subprocess.Popen(
        [
            sys.executable,
            CLI,
            "--host-root",
            host_root,
            "launch",
            "--project-id",
            "podway",
            "--",
            "hold",
        ],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not ready.exists():
        time.sleep(0.05)
    assert ready.exists(), child.stderr.read() if child.poll() is not None else ""
    commit_next_revision(repository)

    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )

    assert rebuilt.returncode == 0, rebuilt.stderr
    assert first_generation.exists()
    child.terminate()
    child.wait(timeout=5)
    wait_missing(first_generation)


def test_guarded_launch_accepts_only_the_complete_exact_generation(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    git_sha = enroll_and_build(repository, host_root)
    manifest = json.loads(
        (
            host_root
            / "artifacts/podway"
            / git_sha
            / ".aquarium-manifest.json"
        ).read_text(encoding="utf-8")
    )

    launched = run_cli(
        host_root,
        "launch",
        "--project-id",
        "podway",
        "--expected-git-sha",
        manifest["git_sha"],
        "--expected-development-version",
        manifest["development_version"],
        "--expected-sha256",
        manifest["sha256"],
    )

    assert launched.returncode == 0, launched.stderr
    assert launched.stdout == "development tool\n"

    mismatched = run_cli(
        host_root,
        "launch",
        "--project-id",
        "podway",
        "--expected-git-sha",
        "0" * 40,
        "--expected-development-version",
        manifest["development_version"],
        "--expected-sha256",
        manifest["sha256"],
    )
    assert mismatched.returncode == 1
    assert payload(mismatched)["error"]["code"] == "artifact_invalid"


def test_guarded_launch_rejects_partial_or_stable_identity(tmp_path):
    host_root = tmp_path / "host"
    partial = run_cli(
        host_root,
        "launch",
        "--project-id",
        "podway",
        "--expected-git-sha",
        "0" * 40,
    )
    assert partial.returncode == 2
    assert payload(partial)["error"]["code"] == "invalid_arguments"

    stable = tmp_path / "stable"
    stable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stable.chmod(0o700)
    guarded_stable = run_cli(
        host_root,
        "launch",
        "--project-id",
        "podway",
        "--stable",
        stable,
        "--expected-git-sha",
        "0" * 40,
        "--expected-development-version",
        "v0.2.7-dev.000000000000",
        "--expected-sha256",
        "sha256:" + "0" * 64,
    )
    assert guarded_stable.returncode == 1
    assert payload(guarded_stable)["error"]["code"] == "artifact_invalid"
