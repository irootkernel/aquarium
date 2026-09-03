from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "verify_podway_compatibility.py"
SPEC = importlib.util.spec_from_file_location("verify_podway_compatibility", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verify_podway_compatibility = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_podway_compatibility)


def git(repository: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repository, check=True)


def test_repository_identity_rejects_dirty_worktree(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "-q")
    git(repository, "config", "user.name", "Test User")
    git(repository, "config", "user.email", "test@example.com")
    (repository / "tracked.txt").write_text("initial\n", encoding="utf-8")
    git(repository, "add", "tracked.txt")
    git(repository, "commit", "-qm", "initial")
    (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")

    with pytest.raises(
        verify_podway_compatibility.CompatibilityError,
        match="dirty Aquarium worktree",
    ):
        verify_podway_compatibility.repository_identity(repository)


def test_replace_once_applies_one_exact_declaration_change() -> None:
    assert (
        verify_podway_compatibility.replace_once(
            b"before limit: 100 after",
            b"limit: 100",
            b"limit: 101",
            "limit",
        )
        == b"before limit: 101 after"
    )


@pytest.mark.parametrize("source", [b"missing", b"limit limit"])
def test_replace_once_rejects_fixture_drift(source: bytes) -> None:
    with pytest.raises(
        verify_podway_compatibility.CompatibilityError,
        match="canonical fixture drifted",
    ):
        verify_podway_compatibility.replace_once(source, b"limit", b"new", "limit")


def test_procedure_result_accepts_only_the_expected_contract() -> None:
    result = {"schema": "podway.procedure-diagnostics-result/v1", "valid": True}
    assert (
        verify_podway_compatibility.procedure_result(
            {
                "schema": "podway.output/v3",
                "command": "procedure.check",
                "result": result,
            }
        )
        is result
    )


def test_procedure_result_rejects_an_unexpected_envelope() -> None:
    with pytest.raises(
        verify_podway_compatibility.CompatibilityError,
        match="output envelope is incompatible",
    ):
        verify_podway_compatibility.procedure_result(
            {"schema": "podway.output/v4", "command": "procedure.check"}
        )


def test_workspace_removal_contract_uses_v4_receipt() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    completed = subprocess.CompletedProcess(
        ["podway"],
        0,
        stdout=json.dumps(
            {
                "schema": "podway.output/v3",
                "command": "workspace.remove",
                "result": {
                    "schema": "podway.workspace-removal-result/v1",
                    "worktree_root": "/tmp/repository",
                    "workspace_uuid": None,
                    "registry_entry_removed": False,
                    "podway_directory_removed": False,
                    "already_absent": True,
                },
            }
        ).encode(),
        stderr=b"",
    )

    result = runtime.output_result(
        completed,
        "workspace.remove",
        "podway.workspace-removal-result/v1",
    )

    assert result["already_absent"] is True
    assert (
        verify_podway_compatibility.RESULT_SCHEMA == "aquarium-podway-compatibility.v4"
    )
    assert verify_podway_compatibility.EXPECTED_VERSION == "v0.2.8"


def test_workspace_removal_replay_accepts_only_the_v028_terminal() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    completed = subprocess.CompletedProcess(
        ["podway"],
        5,
        stdout=json.dumps(
            {
                "schema": "podway.error/v1",
                "command": "workspace.remove",
                "code": "WORKSPACE_CONFIG_INVALID",
                "retryable": False,
            }
        ).encode(),
        stderr=b"",
    )

    assert runtime.workspace_removal_replay_error(completed)["code"] == (
        "WORKSPACE_CONFIG_INVALID"
    )


@pytest.mark.parametrize(
    ("returncode", "code", "retryable"),
    [
        (0, "WORKSPACE_CONFIG_INVALID", False),
        (5, "WORKSPACE_NOT_INITIALIZED", False),
        (5, "WORKSPACE_CONFIG_INVALID", True),
    ],
)
def test_workspace_removal_replay_rejects_other_outcomes(
    returncode: int, code: str, retryable: bool
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    completed = subprocess.CompletedProcess(
        ["podway"],
        returncode,
        stdout=json.dumps(
            {
                "schema": "podway.error/v1",
                "command": "workspace.remove",
                "code": code,
                "retryable": retryable,
            }
        ).encode(),
        stderr=b"",
    )

    with pytest.raises(runtime.RuntimeQualificationError, match="bounded v0.2.8"):
        runtime.workspace_removal_replay_error(completed)


def test_managed_runtime_cleans_up_when_readiness_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_module = verify_podway_compatibility.podway_runtime_qualification
    binary = tmp_path / "podway"
    daemon = tmp_path / "podwayd"
    procedures = tmp_path / "procedures"
    procedures.mkdir()
    for executable in (binary, daemon):
        executable.write_bytes(b"fixture")
        executable.chmod(0o755)

    class ExitedProcess:
        def poll(self) -> int:
            return 0

    monkeypatch.setattr(
        runtime_module,
        "bounded_process",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, b"", b""),
    )
    monkeypatch.setattr(
        runtime_module.subprocess,
        "Popen",
        lambda *args, **kwargs: ExitedProcess(),
    )
    managed = runtime_module.ManagedRuntime(binary, daemon, procedures, 1)

    def fail_readiness() -> None:
        raise runtime_module.RuntimeQualificationError("readiness fixture failed")

    monkeypatch.setattr(managed, "wait_ready", fail_readiness)

    with pytest.raises(
        runtime_module.RuntimeQualificationError, match="readiness fixture failed"
    ):
        managed.__enter__()

    assert managed.root is not None
    assert not managed.root.exists()


def test_managed_runtime_cleans_up_when_setup_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_module = verify_podway_compatibility.podway_runtime_qualification
    binary = tmp_path / "podway"
    daemon = tmp_path / "podwayd"
    procedures = tmp_path / "procedures"
    procedures.mkdir()
    for executable in (binary, daemon):
        executable.write_bytes(b"fixture")
        executable.chmod(0o755)

    def fail_setup(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        raise runtime_module.RuntimeQualificationError("setup fixture failed")

    monkeypatch.setattr(runtime_module, "bounded_process", fail_setup)
    managed = runtime_module.ManagedRuntime(binary, daemon, procedures, 1)

    with pytest.raises(
        runtime_module.RuntimeQualificationError, match="setup fixture failed"
    ):
        managed.__enter__()

    assert managed.root is not None
    assert not managed.root.exists()


def test_managed_runtime_preserves_failure_before_snapshot_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_module = verify_podway_compatibility.podway_runtime_qualification
    binary = tmp_path / "podway"
    daemon = tmp_path / "podwayd"
    procedures = tmp_path / "procedures"
    procedures.mkdir()
    for executable in (binary, daemon):
        executable.write_bytes(b"fixture")
        executable.chmod(0o755)

    def fail_chmod(self: Path, mode: int) -> None:
        raise OSError("chmod fixture failed")

    monkeypatch.setattr(runtime_module.Path, "chmod", fail_chmod)
    managed = runtime_module.ManagedRuntime(binary, daemon, procedures, 1)

    with pytest.raises(OSError, match="chmod fixture failed"):
        managed.__enter__()

    assert managed.dev_home is None
    assert managed.root is not None
    assert not managed.root.exists()


def test_managed_runtime_closes_log_and_cleans_up_when_daemon_start_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_module = verify_podway_compatibility.podway_runtime_qualification
    binary = tmp_path / "podway"
    daemon = tmp_path / "podwayd"
    procedures = tmp_path / "procedures"
    procedures.mkdir()
    for executable in (binary, daemon):
        executable.write_bytes(b"fixture")
        executable.chmod(0o755)

    monkeypatch.setattr(
        runtime_module,
        "bounded_process",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, b"", b""),
    )

    def fail_start(*args: object, **kwargs: object) -> None:
        raise OSError("daemon fixture failed")

    monkeypatch.setattr(runtime_module.subprocess, "Popen", fail_start)
    managed = runtime_module.ManagedRuntime(binary, daemon, procedures, 1)

    with pytest.raises(OSError, match="daemon fixture failed"):
        managed.__enter__()

    assert managed.log is not None
    assert managed.log.closed
    assert managed.root is not None
    assert not managed.root.exists()


def test_exact_binary_requires_an_absolute_path() -> None:
    with pytest.raises(
        verify_podway_compatibility.CompatibilityError,
        match="absolute path",
    ):
        verify_podway_compatibility.exact_binary("podway")


def test_exact_sibling_daemon_requires_an_executable_peer(tmp_path: Path) -> None:
    binary = tmp_path / "podway"
    binary.write_bytes(b"cli")
    binary.chmod(0o755)
    with pytest.raises(
        verify_podway_compatibility.podway_runtime_qualification.RuntimeQualificationError,
        match="executable sibling",
    ):
        verify_podway_compatibility.podway_runtime_qualification.exact_sibling_daemon(
            binary
        )

    daemon = tmp_path / "podwayd"
    daemon.write_bytes(b"daemon")
    daemon.chmod(0o755)
    assert (
        verify_podway_compatibility.podway_runtime_qualification.exact_sibling_daemon(
            binary
        )
        == daemon
    )


def test_exact_sibling_daemon_rejects_a_symlink(tmp_path: Path) -> None:
    binary = tmp_path / "podway"
    binary.write_bytes(b"cli")
    binary.chmod(0o755)
    target = tmp_path / "real-podwayd"
    target.write_bytes(b"daemon")
    target.chmod(0o755)
    os.symlink(target.name, tmp_path / "podwayd")
    with pytest.raises(
        verify_podway_compatibility.podway_runtime_qualification.RuntimeQualificationError,
        match="must not be symlinks",
    ):
        verify_podway_compatibility.podway_runtime_qualification.exact_sibling_daemon(
            binary
        )
