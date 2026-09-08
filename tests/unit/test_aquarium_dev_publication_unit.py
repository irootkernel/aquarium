import io
import json
import os
import shlex
import signal
import stat
import subprocess
import sys
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "plugins/aquarium/tools/aquarium-dev"
CLI = SCRIPT_DIR / "aquarium_dev.py"
sys.path.insert(0, str(SCRIPT_DIR))

import aquarium_dev
import dev_manager
from dev_manager import ManagerError, process_queue, queue_request


@pytest.fixture(autouse=True)
def isolate_development_state(tmp_path, monkeypatch):
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
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
    build_timeout = dev_manager.PRODUCER_BUILD_TIMEOUT_SECONDS
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

    monkeypatch.setattr(dev_manager, "PRODUCER_BUILD_TIMEOUT_SECONDS", build_timeout)
    monkeypatch.setenv("AQUARIUM_TEST_MODE", "success")
    status, details = dev_manager.rebuild(repository, host_root, approve_build=True)
    assert status == "success"
    assert details["git_sha"]


@pytest.mark.parametrize("wait_times_out", [False, True])
def test_process_termination_bounds_waits_and_closes_held_pipes(
    monkeypatch, wait_times_out
):
    grace = 0.1
    monkeypatch.setattr(dev_manager, "PROCESS_TERMINATION_GRACE_SECONDS", grace)
    signals = []
    monkeypatch.setattr(
        dev_manager.os, "killpg", lambda pid, sig: signals.append((pid, sig))
    )

    class ProcessWithHeldPipes:
        pid = 123

        def __init__(self):
            self.stdout = io.StringIO()
            self.stderr = io.StringIO()
            self.drain_timeouts = []
            self.wait_timeouts = []

        def communicate(self, timeout=None):
            assert timeout == grace
            self.drain_timeouts.append(timeout)
            raise subprocess.TimeoutExpired("producer", timeout)

        def wait(self, timeout=None):
            assert self.stdout.closed and self.stderr.closed
            assert timeout == grace
            self.wait_timeouts.append(timeout)
            if wait_times_out:
                raise subprocess.TimeoutExpired("producer", timeout)
            return -signal.SIGKILL

    process = ProcessWithHeldPipes()
    dev_manager._terminate_process_bounded(process)

    assert signals == [(process.pid, signal.SIGTERM), (process.pid, signal.SIGKILL)]
    assert process.drain_timeouts == [grace, grace]
    assert process.wait_timeouts == [grace]
    assert process.stdout.closed and process.stderr.closed


@contextmanager
def escaped_build_pipes(monkeypatch, startup_delay=0):
    # Own the separate-session pipe holder so cleanup never needs a PID file.
    original_popen = subprocess.Popen
    with ExitStack() as stack:
        readers, writers = [], []
        for _ in range(2):
            read_fd, write_fd = os.pipe()
            readers.append(stack.enter_context(os.fdopen(read_fd)))
            writers.append(stack.enter_context(os.fdopen(write_fd, "w")))
        escaped = original_popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            stdout=writers[0],
            stderr=writers[1],
            start_new_session=True,
        )
        builds = []
        try:
            assert os.getpgid(escaped.pid) == escaped.pid

            def start_build(command, **kwargs):
                if command[:3] != ["make", "-s", "aquarium-dev-build"] or (
                    kwargs.get("env", {}).get("AQUARIUM_TEST_MODE") != "escape"
                ):
                    return original_popen(command, **kwargs)
                # Setup may exceed the timeout; only the prepared build is timed.
                time.sleep(startup_delay)
                kwargs.update(stdout=writers[0], stderr=writers[1])
                process = original_popen(command, **kwargs)
                builds.append(process)
                process.stdout, process.stderr = readers
                for writer in writers:
                    writer.close()
                return process

            with monkeypatch.context() as patch:
                patch.setattr(subprocess, "Popen", start_build)
                yield escaped
                assert len(builds) == 1
        finally:
            escaped.kill()
            escaped.wait(timeout=5)
            for process in builds:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)


@pytest.mark.parametrize("startup_delay", [0, 0.3])
def test_timed_out_build_does_not_wait_for_pipes_held_by_escaped_child(
    tmp_path, monkeypatch, startup_delay
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    build_timeout = dev_manager.PRODUCER_BUILD_TIMEOUT_SECONDS
    monkeypatch.setattr(dev_manager, "PRODUCER_BUILD_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setattr(dev_manager, "PROCESS_TERMINATION_GRACE_SECONDS", 0.1)
    monkeypatch.setenv("AQUARIUM_TEST_MODE", "escape")

    with escaped_build_pipes(monkeypatch, startup_delay) as escaped:
        with pytest.raises(ManagerError) as failure:
            dev_manager.rebuild(repository, host_root, approve_build=True)
        assert failure.value.code == "producer_build_timeout"
        # Return while another session still holds both output pipes open.
        assert escaped.poll() is None
        assert os.getpgid(escaped.pid) == escaped.pid
        assert not list((host_root / "artifacts/aquarium").glob(".staging-*"))
        monkeypatch.setattr(
            dev_manager, "PRODUCER_BUILD_TIMEOUT_SECONDS", build_timeout
        )
        monkeypatch.setenv("AQUARIUM_TEST_MODE", "success")
        status, _ = dev_manager.rebuild(repository, host_root, approve_build=True)
        assert status == "success"
    assert escaped.returncode is not None


def test_escaped_build_pipes_cleans_up_after_assertion_failure(monkeypatch):
    with (
        pytest.raises(AssertionError, match="injected failure"),
        escaped_build_pipes(monkeypatch) as escaped,
    ):
        assert escaped.poll() is None
        raise AssertionError("injected failure")
    assert escaped.returncode is not None


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


def test_worker_start_failure_reports_and_preserves_admitted_request(
    tmp_path, monkeypatch, capsys
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    original_popen = subprocess.Popen
    admitted = []

    def fail_worker(command, **kwargs):
        if "worker" not in command:
            return original_popen(command, **kwargs)
        requests = list((host_root / "queue/aquarium").glob("*.json"))
        assert len(requests) == 1
        admitted.append(json.loads(requests[0].read_text()))
        assert kwargs["start_new_session"] is True
        assert kwargs["close_fds"] is True
        for stream in ("stdin", "stdout", "stderr"):
            assert kwargs[stream] == subprocess.DEVNULL
        raise OSError("injected worker launch failure")

    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "Popen", fail_worker)
        patch.setattr(
            sys,
            "argv",
            [
                str(CLI),
                "--host-root",
                str(host_root),
                "request",
                "--repository",
                str(repository),
            ],
        )
        assert aquarium_dev.main() == 1
    output = capsys.readouterr()
    assert not output.out
    error = json.loads(output.err)["error"]
    assert error["code"] == "worker_failed"
    assert error["git_sha"] == admitted[0]["git_sha"]
    diagnostic = json.loads(
        (host_root / "diagnostics/aquarium/latest.json").read_text()
    )
    assert diagnostic["code"] == "worker_failed"
    assert diagnostic["git_sha"] == error["git_sha"]
    assert list((host_root / "queue/aquarium").glob("*.json"))
    _, details = process_queue("aquarium", host_root)
    assert details["published"] == 1


def wait_for_path(path: Path, timeout: float = 15) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists():
        assert time.monotonic() < deadline, f"Timed out waiting for {path}"
        time.sleep(0.01)


@pytest.mark.parametrize("legacy_hook", (False, True), ids=("synchronous", "legacy"))
def test_short_lived_commit_caller_admits_before_detaching_worker(
    tmp_path, monkeypatch, legacy_hook
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    repository = create_repository(tmp_path / "repository")
    host_root = home / ".aquarium-dev"
    request_ready = tmp_path / "request-ready"
    admission_release = tmp_path / "admission-release"
    build_ready = tmp_path / "build-ready"
    build_release = tmp_path / "build-release"
    worker_pid = tmp_path / "worker-pid"
    monkeypatch.setenv("AQUARIUM_TEST_MODE", "blocked")
    monkeypatch.setenv("AQUARIUM_TEST_BUILD_READY", str(build_ready))
    monkeypatch.setenv("AQUARIUM_TEST_BUILD_RELEASE", str(build_release))
    wrapper = tmp_path / "request.py"
    wrapper.write_text(
        f"""import sys
import time
from pathlib import Path
sys.path.insert(0, {str(SCRIPT_DIR)!r})
import aquarium_dev
import subprocess
original_popen = subprocess.Popen
def record_worker(command, **kwargs):
    process = original_popen(command, **kwargs)
    if 'worker' in command:
        Path({str(worker_pid)!r}).write_text(str(process.pid))
    return process
subprocess.Popen = record_worker
Path({str(request_ready)!r}).write_text('ready')
deadline = time.monotonic() + 15
while not Path({str(admission_release)!r}).exists():
    if time.monotonic() >= deadline:
        raise SystemExit('Admission barrier timed out')
    time.sleep(0.01)
raise SystemExit(aquarium_dev.main())
"""
    )
    dev_manager.enroll(
        repository,
        host_root,
        wrapper,
        approve_enrollment=True,
        approve_hook=True,
        approve_reenrollment=False,
    )
    hook = repository / ".git/hooks/post-commit"
    if legacy_hook:
        command = shlex.join(
            [
                str(Path(sys.executable).resolve()),
                str(wrapper),
                "request",
                "--repository",
                str(repository),
            ]
        )
        hook.write_text(f"#!/bin/sh\n{command} >/dev/null 2>&1 &\n")
    (repository / "source.txt").write_text("committed\n")
    subprocess.run(["git", "-C", repository, "add", "source.txt"], check=True)
    caller = subprocess.Popen(
        ["git", "-C", repository, "commit", "-q", "-m", "exercise admission"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    caller_group_cleaned = False
    worker_completed = False
    try:
        wait_for_path(request_ready)
        if legacy_hook:
            stdout, stderr = caller.communicate(timeout=5)
            assert caller.returncode == 0, stderr
            os.killpg(caller.pid, signal.SIGKILL)
            caller_group_cleaned = True
            assert not list((host_root / "queue/aquarium").glob("*.json"))
            assert not (host_root / "diagnostics/aquarium/latest.json").exists()
            assert not build_ready.exists()
            return
        with pytest.raises(subprocess.TimeoutExpired):
            caller.wait(timeout=0.2)
        admission_release.touch()
        stdout, stderr = caller.communicate(timeout=15)
        assert caller.returncode == 0, stderr
        assert not stdout
        assert not stderr
        sha = subprocess.check_output(
            ["git", "-C", repository, "rev-parse", "HEAD"], text=True
        ).strip()
        request = host_root / "queue/aquarium" / f"{sha}.json"
        assert json.loads(request.read_text())["git_sha"] == sha
        wait_for_path(build_ready)
        try:
            os.killpg(caller.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        caller_group_cleaned = True
        assert not (host_root / "current/aquarium").exists()
        build_release.touch()
        current = host_root / "current/aquarium"
        wait_for_path(current)
        assert current.resolve().name == sha
        assert (
            current / "plugin/payload.txt"
        ).read_text() == f"artifact {sha} committed\n"
        deadline = time.monotonic() + 15
        while request.exists():
            assert time.monotonic() < deadline, "Worker did not finish the request"
            time.sleep(0.01)
        worker_completed = True
    finally:
        build_release.touch()
        if not caller_group_cleaned:
            try:
                os.killpg(caller.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        caller.communicate(timeout=5)
        if worker_pid.exists() and not worker_completed:
            try:
                os.killpg(int(worker_pid.read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_generated_hook_reports_admission_failure_and_preserves_commit(
    tmp_path, monkeypatch
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    repository = create_repository(tmp_path / "repository")
    host_root = home / ".aquarium-dev"
    hook = repository / ".git/hooks/post-commit"
    hook.write_text("#!/bin/sh\nset -e\n")
    hook.chmod(0o755)
    enroll(repository, host_root)
    with hook.open("a") as stream:
        stream.write("printf 'foreign hook continued\\n' >&2\n")
    (repository / "source.txt").write_text("committed\n")
    subprocess.run(["git", "-C", repository, "add", "source.txt"], check=True)
    (repository / "untracked").touch()
    commit = subprocess.run(
        ["git", "-C", repository, "commit", "-q", "-m", "admission fails"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert commit.returncode == 0
    assert '"code": "dirty_worktree"' in commit.stderr
    assert "the Git commit was created" in commit.stderr
    assert "foreign hook continued" in commit.stderr
    sha = subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()
    diagnostic = json.loads(
        (host_root / "diagnostics/aquarium/latest.json").read_text()
    )
    assert diagnostic["git_sha"] == sha
    assert diagnostic["code"] == "dirty_worktree"
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


@pytest.mark.parametrize("branch", ("feature", "detached"))
def test_hook_skips_non_main_but_explicit_request_rejects(tmp_path, branch):
    repository = create_repository(tmp_path / "repository")
    host_root = Path.home() / ".aquarium-dev"
    enroll(repository, host_root)
    arguments = (
        ["checkout", "--detach"] if branch == "detached" else ["checkout", "-b", branch]
    )
    subprocess.run(
        ["git", "-C", repository, *arguments], check=True, capture_output=True
    )
    request_marker = tmp_path / "request-ran"
    request_script = tmp_path / "request.py"
    request_script.write_text(
        f"from pathlib import Path\nPath({str(request_marker)!r}).touch()\n"
    )
    hook = repository / ".git/hooks/post-commit"
    hook.write_text(
        "#!/bin/sh\nset -eu\n"
        + dev_manager.marker_block(repository, request_script)
        + "printf 'foreign continued\\n' >&2\n"
    )
    result = subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--allow-empty", "-m", "non-main"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stderr == "foreign continued\n"
    assert not request_marker.exists()
    assert not (host_root / "queue").exists()
    assert not (host_root / "diagnostics").exists()
    rejected = run_cli(host_root, "request", "--repository", repository)
    assert rejected.returncode == 1
    assert payload(rejected)["error"]["code"] == "not_local_main"


def test_request_reports_queue_existence_check_failure(tmp_path, monkeypatch, capsys):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    git_sha = subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()
    target = host_root / "queue/aquarium" / f"{git_sha}.json"
    original_exists = Path.exists
    original_popen = subprocess.Popen

    def fail_exists(path):
        if path == target:
            raise PermissionError("queue stat denied")
        return original_exists(path)

    def reject_worker(command, **kwargs):
        assert "worker" not in command, "worker started before durable admission"
        return original_popen(command, **kwargs)

    monkeypatch.setattr(Path, "exists", fail_exists)
    monkeypatch.setattr(subprocess, "Popen", reject_worker)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(CLI),
            "--host-root",
            str(host_root),
            "request",
            "--repository",
            str(repository),
        ],
    )
    assert aquarium_dev.main() == 1
    output = capsys.readouterr()
    assert not output.out
    response = json.loads(output.err)
    assert response["schema"] == "aquarium-dev-error/v1"
    error = response["error"]
    assert error["code"] == "worker_failed"
    assert "queue stat denied" in error["message"]
    assert error["git_sha"] == git_sha
    assert not original_exists(target)
    diagnostic = json.loads(
        (host_root / "diagnostics/aquarium/latest.json").read_text()
    )
    assert diagnostic["code"] == error["code"]
    assert diagnostic["git_sha"] == git_sha


@pytest.mark.parametrize("failure", ("queue", "worker"))
def test_request_reports_primary_error_when_diagnostic_storage_fails(
    tmp_path, monkeypatch, capsys, failure
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    original_write = dev_manager._atomic_json
    original_popen = subprocess.Popen

    def fail_write(path, value):
        if "diagnostics" in path.parts:
            raise OSError("diagnostic storage unavailable")
        if failure == "queue" and "queue" in path.parts:
            raise OSError("queue storage unavailable")
        return original_write(path, value)

    def fail_worker(command, **kwargs):
        if "worker" in command:
            assert failure == "worker", "worker started before durable admission"
            raise OSError("worker launch unavailable")
        return original_popen(command, **kwargs)

    monkeypatch.setattr(dev_manager, "_atomic_json", fail_write)
    monkeypatch.setattr(subprocess, "Popen", fail_worker)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(CLI),
            "--host-root",
            str(host_root),
            "request",
            "--repository",
            str(repository),
        ],
    )
    assert aquarium_dev.main() == 1
    output = capsys.readouterr()
    assert not output.out
    error = json.loads(output.err)["error"]
    assert error["code"] == "worker_failed"
    assert f"{failure} " in error["message"]
    assert "diagnostic storage unavailable" in error["message"]
    assert "Traceback" not in output.err
    assert bool(list((host_root / "queue/aquarium").glob("*.json"))) == (
        failure == "worker"
    )


@pytest.mark.parametrize("probe", ("describe", "build"))
def test_producer_probe_timeout_terminates_child_and_reports_error(
    tmp_path, monkeypatch, probe
):
    repository = create_repository(tmp_path / "repository")
    pid_path = tmp_path / "probe.pid"
    script = tmp_path / "hang.py"
    script.write_text(
        "import os, time\nfrom pathlib import Path\n"
        + f"Path({str(pid_path)!r}).write_text(str(os.getpid()))\ntime.sleep(60)\n"
    )
    makefile = repository / "Makefile"
    command = shlex.join([sys.executable, str(script)])
    contents = makefile.read_text()
    if probe == "describe":
        contents = contents.replace(
            "aquarium-dev-describe:\n", f"aquarium-dev-describe:\n\t@{command}\n"
        )
    else:
        # Recursive recipes run even under make -n.
        contents = contents.replace("\t@python3 producer.py", f"\t+@{command}")
    makefile.write_text(contents)
    monkeypatch.setattr(dev_manager, "PRODUCER_PROBE_TIMEOUT_SECONDS", 0.5)
    monkeypatch.setattr(dev_manager, "PROCESS_TERMINATION_GRACE_SECONDS", 0.1)
    started = time.monotonic()
    with pytest.raises(ManagerError) as failure:
        dev_manager._describe(repository)
    assert failure.value.code == "producer_build_timeout"
    assert f"aquarium-dev-{probe}" in failure.value.message
    assert time.monotonic() - started < 3
    child_pid = int(pid_path.read_text())
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.01)
    else:
        pytest.fail("producer probe child survived timeout cleanup")


@pytest.mark.parametrize("mode", ("success", "checksum"))
def test_rebuild_consumes_only_matching_request_after_publication(
    tmp_path, monkeypatch, mode
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    _, request = queue_request(repository, host_root, CLI, spawn_worker=False)
    target = Path(request["queued"])
    other = target.with_name("0" * 40 + ".json")
    other.write_text("{}")
    original = target.read_bytes()
    monkeypatch.setenv("AQUARIUM_TEST_MODE", mode)
    if mode == "success":
        dev_manager.rebuild(repository, host_root, approve_build=True)
        assert not target.exists()
        assert (host_root / "current/aquarium").resolve().name == request["git_sha"]
    else:
        with pytest.raises(ManagerError):
            dev_manager.rebuild(repository, host_root, approve_build=True)
        assert target.read_bytes() == original
    assert other.read_text() == "{}"


@pytest.mark.parametrize("content", ("malformed", "different-checkout", "symlink"))
def test_rebuild_preserves_unmatched_queue_state(tmp_path, content):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    _, details = queue_request(repository, host_root, CLI, spawn_worker=False)
    target = Path(details["queued"])
    request = json.loads(target.read_text())
    if content == "malformed":
        target.write_text("{")
    elif content == "different-checkout":
        request["checkout"] = str(tmp_path / "another")
        target.write_text(json.dumps(request))
    else:
        foreign = tmp_path / "foreign-request"
        foreign.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(foreign)
    original = target.read_bytes()
    dev_manager.rebuild(repository, host_root, approve_build=True)
    assert target.read_bytes() == original
    assert target.is_symlink() == (content == "symlink")


def test_rebuild_reports_publication_success_when_queue_cleanup_fails(
    tmp_path, monkeypatch
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    _, details = queue_request(repository, host_root, CLI, spawn_worker=False)
    target = Path(details["queued"])
    original_unlink = Path.unlink

    def fail_cleanup(path, *args, **kwargs):
        if path == target:
            raise OSError("queue cleanup unavailable")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_cleanup)
    with pytest.raises(ManagerError) as failure:
        dev_manager.rebuild(repository, host_root, approve_build=True)
    assert failure.value.code == "publication_failed"
    assert "was published" in failure.value.message
    assert target.exists()
    assert (host_root / "current/aquarium").resolve().name == details["git_sha"]


def test_hook_branch_lookup_failure_is_visible_and_preserves_foreign_commands(tmp_path):
    hook = tmp_path / "hook.sh"
    hook.write_text(
        "#!/bin/sh\nset -eu\n"
        + dev_manager.marker_block(tmp_path / "missing-repository", CLI)
        + "printf 'foreign continued\\n' >&2\n"
    )
    result = subprocess.run(["sh", hook], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "Aquarium could not inspect the Git branch" in result.stderr
    assert result.stderr.endswith("foreign continued\n")


@pytest.mark.parametrize("probe", ("describe", "build"))
def test_request_reports_producer_probe_start_failure(
    tmp_path, monkeypatch, capsys, probe
):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll(repository, host_root)
    original_popen = subprocess.Popen
    failed_commands = []

    def fail_probe(command, **kwargs):
        assert "worker" not in command, "worker started after a failed producer probe"
        if command[0] == "make" and f"aquarium-dev-{probe}" in command:
            failed_commands.append(command)
            raise OSError("producer probe cannot start")
        return original_popen(command, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", fail_probe)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(CLI),
            "--host-root",
            str(host_root),
            "request",
            "--repository",
            str(repository),
        ],
    )
    assert aquarium_dev.main() == 1
    assert len(failed_commands) == 1
    output = capsys.readouterr()
    assert not output.out
    result = json.loads(output.err)
    assert result["schema"] == "aquarium-dev-error/v1"
    assert result["error"]["code"] == "producer_contract_missing"
    assert result["error"]["message"] == "producer probe cannot start"
    assert not (host_root / "queue").exists()


def test_request_reports_symbolic_ref_failure(tmp_path, monkeypatch, capsys):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    original_run_git = dev_manager.run_git
    branch_queries = []

    def fail_branch(checkout, *arguments, **kwargs):
        if arguments[0] == "symbolic-ref":
            branch_queries.append(arguments)
            return subprocess.CompletedProcess(
                arguments, 128, "", "cannot read symbolic HEAD\n"
            )
        return original_run_git(checkout, *arguments, **kwargs)

    monkeypatch.setattr(dev_manager, "run_git", fail_branch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(CLI),
            "--host-root",
            str(host_root),
            "request",
            "--repository",
            str(repository),
        ],
    )
    assert aquarium_dev.main() == 1
    assert len(branch_queries) == 1
    output = capsys.readouterr()
    assert not output.out
    result = json.loads(output.err)
    assert result["schema"] == "aquarium-dev-error/v1"
    assert result["error"]["code"] == "not_git_root"
    assert result["error"]["message"] == "cannot read symbolic HEAD"
    assert not (host_root / "queue").exists()
