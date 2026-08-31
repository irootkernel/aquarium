import json
import os
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "plugins/aquarium/skills/aquarium-dev/scripts"
CLI = SCRIPT_DIR / "aquarium_dev.py"
sys.path.insert(0, str(SCRIPT_DIR))

import aquarium_dev
import dev_manager
from dev_manager import ManagerError, process_queue, queue_request


@pytest.fixture(autouse=True)
def clear_managed_immutable_flags(tmp_path):
    yield
    for current, directories, files in os.walk(tmp_path):
        os.chflags(current, 0)
        for name in (*directories, *files):
            target = Path(current) / name
            if not target.is_symlink():
                os.chflags(target, 0)


PRODUCER = r"""import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

output = Path(os.environ["AQUARIUM_DEV_OUTPUT"])
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
mode = os.environ.get("AQUARIUM_TEST_MODE", "success")
if mode == "blocked":
    ready = Path(os.environ["AQUARIUM_TEST_BUILD_READY"])
    release = Path(os.environ["AQUARIUM_TEST_BUILD_RELEASE"])
    ready.write_text("ready", encoding="utf-8")
    while not release.exists():
        time.sleep(0.01)
artifact = output / "plugin"
artifact.mkdir()
(artifact / "payload.txt").write_text(
    f"artifact {sha} {Path('source.txt').read_text(encoding='utf-8').strip()}\n",
    encoding="utf-8",
)
file_digest = hashlib.sha256((artifact / "payload.txt").read_bytes()).digest()
tree = hashlib.sha256()
tree.update(b"payload.txt\0")
tree.update(file_digest)
tree.update(b"\n")
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
elif mode == "hang":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    Path(os.environ["AQUARIUM_TEST_CHILD_PID"]).write_text(str(child.pid))
    time.sleep(60)
elif mode == "escape":
    child = subprocess.Popen([
        sys.executable,
        "-c",
        "import os,time; os.setsid(); "
        "open(os.environ['AQUARIUM_TEST_ESCAPE_READY'], 'w').write(str(os.getpid())); "
        "time.sleep(60)",
    ])
    ready = Path(os.environ["AQUARIUM_TEST_ESCAPE_READY"])
    while not ready.exists():
        time.sleep(0.01)
    time.sleep(60)
print(json.dumps(manifest, sort_keys=True))
"""


def create_repository(path: Path, project_id: str = "aquarium") -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", path], check=True)
    subprocess.run(["git", "-C", path, "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", path, "config", "user.email", "test@example.invalid"],
        check=True,
    )
    artifact_kind = "codex-plugin" if project_id == "aquarium" else "executable"
    artifact_path = "plugin" if project_id == "aquarium" else f"bin/{project_id}"
    (path / "Makefile").write_text(
        f"""aquarium-dev-describe:
\t@printf '%s\\n' '{{"schema":"aquarium-dev-producer-description/v1","project_id":"{project_id}","next_version":"v0.1.14","artifact_kind":"{artifact_kind}","artifact_path":"{artifact_path}"}}'

aquarium-dev-build:
\t@python3 producer.py
""",
        encoding="utf-8",
    )
    producer = PRODUCER.replace(
        '"project_id": "aquarium"', f'"project_id": "{project_id}"'
    )
    (path / "producer.py").write_text(producer, encoding="utf-8")
    (path / "source.txt").write_text("initial\n", encoding="utf-8")
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


@pytest.mark.parametrize("code", ("producer_build_timeout", "worker_failed"))
def test_cli_serializes_new_worker_error_codes(code, tmp_path, monkeypatch, capsys):
    def fail_worker(*_args, **_kwargs):
        raise ManagerError(
            code,
            "bounded worker failure",
            "Retry after inspection.",
            "schedule",
            "aquarium",
        )

    monkeypatch.setattr(aquarium_dev, "process_queue", fail_worker)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(CLI),
            "--host-root",
            str(tmp_path / "host"),
            "worker",
            "--project-id",
            "aquarium",
        ],
    )

    assert aquarium_dev.main() == 1
    error = json.loads(capsys.readouterr().err)
    assert error["schema"] == "aquarium-dev-error/v1"
    assert error["error"]["code"] == code


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
    assert (current / "plugin/payload.txt").read_text() == f"artifact {sha} initial\n"
    assert current.resolve().stat().st_flags & stat.UF_IMMUTABLE
    with pytest.raises(OSError):
        (current / "plugin/payload.txt").write_text("mutated", encoding="utf-8")


def test_aquarium_rebuild_retains_plugin_generation_without_consumer_lease(tmp_path):
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
    assert (host_root / "artifacts/aquarium" / first_sha).exists()


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


def test_build_uses_admitted_commit_when_main_advances_concurrently(
    tmp_path, monkeypatch
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    ready = tmp_path / "build.ready"
    release = tmp_path / "build.release"
    enroll(repository, host_root)
    admitted_sha = subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()
    monkeypatch.setenv("AQUARIUM_TEST_MODE", "blocked")
    monkeypatch.setenv("AQUARIUM_TEST_BUILD_READY", str(ready))
    monkeypatch.setenv("AQUARIUM_TEST_BUILD_RELEASE", str(release))

    process = subprocess.Popen(
        [
            sys.executable,
            CLI,
            "--host-root",
            host_root,
            "rebuild",
            "--repository",
            repository,
            "--approve-build",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not ready.exists():
        time.sleep(0.01)
    assert ready.exists()
    (repository / "source.txt").write_text("advanced\n", encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", "source.txt"], check=True)
    subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--no-verify", "-m", "advance"],
        check=True,
    )
    release.write_text("release", encoding="utf-8")
    stdout, stderr = process.communicate(timeout=10)

    assert process.returncode == 0, stderr
    result = json.loads(stdout)
    assert result["details"]["git_sha"] == admitted_sha
    current = host_root / "current/aquarium"
    assert current.resolve().name == admitted_sha
    assert (current / "plugin/payload.txt").read_text() == (
        f"artifact {admitted_sha} initial\n"
    )


def test_timed_out_build_kills_process_group_and_releases_publisher_lock(
    tmp_path, monkeypatch
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    child_pid_path = tmp_path / "child.pid"
    enroll(repository, host_root)
    monkeypatch.setattr(dev_manager, "PRODUCER_BUILD_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setenv("AQUARIUM_TEST_MODE", "hang")
    monkeypatch.setenv("AQUARIUM_TEST_CHILD_PID", str(child_pid_path))

    with pytest.raises(ManagerError) as failure:
        dev_manager.rebuild(repository, host_root, approve_build=True)

    assert failure.value.code == "producer_build_timeout"
    assert not list((host_root / "artifacts/aquarium").glob(".staging-*"))
    child_pid = int(child_pid_path.read_text())
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        pytest.fail("producer child survived process-group timeout cleanup")

    monkeypatch.setenv("AQUARIUM_TEST_MODE", "success")
    status, details = dev_manager.rebuild(repository, host_root, approve_build=True)
    assert status == "success"
    assert details["git_sha"]


def test_timed_out_build_does_not_wait_for_pipes_held_by_escaped_child(
    tmp_path, monkeypatch
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    ready = tmp_path / "escaped.pid"
    enroll(repository, host_root)
    monkeypatch.setattr(dev_manager, "PRODUCER_BUILD_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setattr(dev_manager, "PROCESS_TERMINATION_GRACE_SECONDS", 0.1)
    monkeypatch.setenv("AQUARIUM_TEST_MODE", "escape")
    monkeypatch.setenv("AQUARIUM_TEST_ESCAPE_READY", str(ready))

    started = time.monotonic()
    with pytest.raises(ManagerError) as failure:
        dev_manager.rebuild(repository, host_root, approve_build=True)
    elapsed = time.monotonic() - started
    escaped_pid = int(ready.read_text())
    try:
        assert failure.value.code == "producer_build_timeout"
        assert elapsed < 1
        assert not list((host_root / "artifacts/aquarium").glob(".staging-*"))
        monkeypatch.setenv("AQUARIUM_TEST_MODE", "success")
        status, _ = dev_manager.rebuild(repository, host_root, approve_build=True)
        assert status == "success"
    finally:
        try:
            os.kill(escaped_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


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


def test_worker_retains_failed_request_and_reports_failure(tmp_path, monkeypatch):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    _, queued = queue_request(repository, host_root, CLI, spawn_worker=False)
    request_path = Path(queued["queued"])
    monkeypatch.setenv("AQUARIUM_TEST_MODE", "build")

    with pytest.raises(ManagerError) as failure:
        process_queue("aquarium", host_root)

    assert failure.value.code == "producer_build_failed"
    assert request_path.is_file()
    monkeypatch.delenv("AQUARIUM_TEST_MODE")
    status, details = process_queue("aquarium", host_root)
    assert status == "success"
    assert details["published"] == 1
    assert not request_path.exists()


def test_worker_quarantines_stale_request_without_poisoning_future_runs(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    _, old = queue_request(repository, host_root, CLI, spawn_worker=False)
    old_request = Path(old["queued"])
    marker = repository / "revision.txt"
    marker.write_text("next\n", encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", marker.name], check=True)
    subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--no-verify", "-m", "next"],
        check=True,
    )
    _, current = queue_request(repository, host_root, CLI, spawn_worker=False)

    with pytest.raises(ManagerError) as failure:
        process_queue("aquarium", host_root)

    assert failure.value.code == "sha_mismatch"
    assert not old_request.exists()
    quarantined = list((host_root / "queue-failures/aquarium").glob("*.json"))
    assert len(quarantined) == 1
    assert json.loads(quarantined[0].read_text())["git_sha"] == old["git_sha"]
    status, details = process_queue("aquarium", host_root)
    assert status == "success"
    assert details["published"] in {0, 1}
    assert (host_root / "current/aquarium").resolve().name == current["git_sha"]


def test_worker_quarantines_request_for_another_enrolled_project(tmp_path):
    repository = create_repository(tmp_path / "mulgae", project_id="mulgae")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    git_sha = subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()
    request_path = host_root / "queue/aquarium/request.json"
    request_path.parent.mkdir(parents=True)
    request_path.write_text(
        json.dumps(
            {
                "schema": "aquarium-dev-build-request/v1",
                "project_id": "aquarium",
                "git_sha": git_sha,
                "checkout": str(repository),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManagerError) as failure:
        process_queue("aquarium", host_root)

    assert failure.value.code == "invalid_arguments"
    assert not request_path.exists()
    quarantined = list((host_root / "queue-failures/aquarium").glob("*.json"))
    assert len(quarantined) == 1
    assert json.loads(quarantined[0].read_text())["checkout"] == str(repository)
    assert not (host_root / "current/aquarium").exists()
    assert not (host_root / "current/podway").exists()


def test_worker_quarantines_non_regular_queue_entry(tmp_path):
    host_root = tmp_path / "host"
    invalid = host_root / "queue/aquarium/invalid.json"
    invalid.mkdir(parents=True)

    with pytest.raises(ManagerError) as failure:
        process_queue("aquarium", host_root)

    assert failure.value.code == "invalid_arguments"
    assert not invalid.exists()
    quarantined = list((host_root / "queue-failures/aquarium").glob("*.json"))
    assert len(quarantined) == 1
    assert quarantined[0].is_dir()
    status, details = process_queue("aquarium", host_root)
    assert status == "success"
    assert details["processed"] == 0


def test_worker_preserves_valid_request_after_operational_io_failure(
    tmp_path, monkeypatch
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    _, queued = queue_request(repository, host_root, CLI, spawn_worker=False)
    request_path = Path(queued["queued"])

    def fail_build(*_args, **_kwargs):
        raise OSError("transient producer filesystem failure")

    monkeypatch.setattr(dev_manager, "_validated_build", fail_build)
    with pytest.raises(ManagerError) as failure:
        process_queue("aquarium", host_root)

    assert failure.value.code == "worker_failed"
    assert request_path.is_file()
    assert not (host_root / "queue-failures/aquarium").exists()


def test_worker_reports_failure_when_terminal_request_cannot_be_quarantined(
    tmp_path, monkeypatch
):
    host_root = tmp_path / "host"
    invalid = host_root / "queue/aquarium/invalid.json"
    invalid.mkdir(parents=True)

    def fail_quarantine(*_args, **_kwargs):
        raise OSError("quarantine unavailable")

    monkeypatch.setattr(dev_manager, "_quarantine_build_request", fail_quarantine)
    with pytest.raises(ManagerError) as failure:
        process_queue("aquarium", host_root)

    assert failure.value.code == "worker_failed"
    assert invalid.is_dir()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("checkout", None),
        ("checkout", {}),
        ("checkout", []),
        ("checkout", "invalid\0path"),
        ("git_sha", None),
        ("git_sha", "not-a-full-lowercase-sha"),
    ),
)
def test_worker_quarantines_invalid_request_field_types(tmp_path, field, value):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    _, queued = queue_request(repository, host_root, CLI, spawn_worker=False)
    request_path = Path(queued["queued"])
    request = json.loads(request_path.read_text())
    request[field] = value
    request_path.write_text(json.dumps(request), encoding="utf-8")

    with pytest.raises(ManagerError) as failure:
        process_queue("aquarium", host_root)

    assert failure.value.code == "invalid_arguments"
    assert not request_path.exists()
    assert len(list((host_root / "queue-failures/aquarium").glob("*.json"))) == 1


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
