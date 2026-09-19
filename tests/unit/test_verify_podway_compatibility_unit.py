from __future__ import annotations

import copy
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


def reversed_json(value: dict[str, object]) -> str:
    return json.dumps(dict(reversed(list(value.items()))), separators=(",", ":"))


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


def removal_replay_process(**changes: object) -> subprocess.CompletedProcess[bytes]:
    result = {
        "schema": "podway.workspace-removal-result/v1",
        "worktree_root": "/tmp/repository",
        "workspace_uuid": None,
        "registry_entry_removed": False,
        "podway_directory_removed": False,
        "already_absent": True,
    }
    result.update(changes)
    return subprocess.CompletedProcess(
        ["podway"],
        0,
        stdout=json.dumps(
            {
                "schema": "podway.output/v3",
                "command": "workspace.remove",
                "result": result,
            }
        ).encode(),
        stderr=b"",
    )


def decision_process(target: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(
        ["podway"],
        0,
        stdout=json.dumps(
            {
                "schema": "podway.output/v3",
                "command": "session.decide",
                "result": {
                    "schema": "podway.decision-result/v1",
                    "target_graph_node_id": target,
                },
            }
        ).encode(),
        stderr=b"",
    )


def test_decision_destination_uses_decision_result_target() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    runtime.ManagedRuntime.decision_destination(
        decision_process("complete-work"), "complete-work"
    )
    with pytest.raises(runtime.RuntimeQualificationError, match="wrong destination"):
        runtime.ManagedRuntime.decision_destination(
            decision_process("record-evidence"), "complete-work"
        )


@pytest.mark.parametrize(
    ("procedure_id", "expected"),
    (
        ("aquarium-task-v2", "confirm-goal-assessment-core"),
        ("aquarium-goal-v2", "assess-goal"),
        ("aquarium-validation-v2", "assess-goal"),
    ),
)
def test_completed_low_settlement_destination_is_procedure_specific(
    procedure_id: str, expected: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    assert runtime.completed_low_settlement_destination(procedure_id) == expected


@pytest.mark.parametrize(
    "scenario",
    ["low-blocker-wait", "validation-low-blocker-wait"],
)
@pytest.mark.parametrize(
    "variant",
    [
        "exact",
        "wrong-source",
        "missing-blocker",
        "wrong-blocker",
        "wrong-description",
        "wrong-scope",
        "wrong-target",
        "wrong-count",
    ],
)
def test_low_blocker_readback_requires_exact_scenario_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
    variant: str,
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(
        tmp_path / "podway", tmp_path / "podwayd", tmp_path / "procedures", 1
    )
    managed.scenario = scenario
    managed.fixture_target = "a" * 40
    expected = runtime.low_blocker_fixture(scenario, managed.fixture_target)
    source_basis = copy.deepcopy(expected["source_basis"])
    disposition = copy.deepcopy(expected["disposition_summary"])
    blockers = 1
    after_target = managed.fixture_target

    if variant == "wrong-source":
        source_basis["source_id"] = "fixture:unrelated-source:01"
    elif variant == "missing-blocker":
        disposition.pop("new_blocker")
    elif variant == "wrong-blocker":
        disposition["new_blocker"]["id"] = "fixture:blocker:unrelated:01"
    elif variant == "wrong-description":
        disposition["new_blocker"]["description"] = "An unrelated condition."
    elif variant == "wrong-scope":
        disposition["new_blocker"]["affected_scope"] = "fixture/unrelated"
    elif variant == "wrong-target":
        after_target = "b" * 40
    elif variant == "wrong-count":
        blockers = 2

    readback = {
        "source-review-basis": reversed_json(source_basis),
        "low-disposition-summary": reversed_json(disposition),
        "current-blocking-findings": blockers,
        "after-target": after_target,
    }
    monkeypatch.setattr(
        managed,
        "read_complete_evidence",
        lambda _observation, _source, item: readback[item],
    )
    observation = {
        "guidance": {"node": {"graph_node_id": "await-user-direction"}},
        "active_items": [],
    }

    if variant == "exact":
        managed.fill_action(observation, "unused")
        assert managed.low_blocker_readback_verified is True
    else:
        with pytest.raises(
            runtime.RuntimeQualificationError,
            match="exact settlement evidence|source basis",
        ):
            managed.fill_action(observation, "unused")
        assert managed.low_blocker_readback_verified is False


def test_workspace_removal_replay_requires_success_with_v6_receipt() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    result = runtime.workspace_removal_result(
        removal_replay_process(), "/tmp/repository", None
    )
    assert result["already_absent"] is True
    assert result["workspace_uuid"] is None
    assert (
        verify_podway_compatibility.RESULT_SCHEMA == "aquarium-podway-compatibility.v6"
    )
    assert verify_podway_compatibility.EXPECTED_VERSION == "v0.2.10"


@pytest.mark.parametrize(
    "changes",
    [
        {"worktree_root": "/tmp/other"},
        {"workspace_uuid": "original-uuid"},
        {"registry_entry_removed": True},
        {"podway_directory_removed": True},
        {"already_absent": False},
        {"registry_entry_removed": 0},
        {"podway_directory_removed": 0},
        {"already_absent": 1},
        {"schema": "podway.workspace-removal-result/v2"},
    ],
)
def test_workspace_removal_replay_rejects_incompatible_results(changes: dict) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    with pytest.raises(runtime.RuntimeQualificationError):
        runtime.workspace_removal_result(
            removal_replay_process(**changes), "/tmp/repository", None
        )


@pytest.mark.parametrize("workspace_uuid", [None, "original-uuid"])
@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"registry_entry_removed": 0},
        {"registry_entry_removed": 1},
        {"podway_directory_removed": 0},
        {"podway_directory_removed": 1},
        {"already_absent": 0},
        {"already_absent": 1},
        {"registry_entry_removed": None},
        {"podway_directory_removed": "true"},
        {"worktree_root": "/tmp/other"},
        {"workspace_uuid": "wrong-uuid"},
        {"extra": True},
    ],
)
def test_workspace_removal_requires_exact_fields_and_boolean_flags(
    workspace_uuid, changes
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    expected = {
        "workspace_uuid": workspace_uuid,
        "registry_entry_removed": workspace_uuid is not None,
        "podway_directory_removed": workspace_uuid is not None,
        "already_absent": workspace_uuid is None,
    }
    completed = removal_replay_process(**(expected | changes))
    if changes:
        with pytest.raises(runtime.RuntimeQualificationError):
            runtime.workspace_removal_result(
                completed, "/tmp/repository", workspace_uuid
            )
    else:
        result = runtime.workspace_removal_result(
            completed, "/tmp/repository", workspace_uuid
        )
        assert result["workspace_uuid"] == workspace_uuid
        assert result["already_absent"] is (workspace_uuid is None)


@pytest.mark.parametrize("returncode", [0, 5])
def test_workspace_removal_replay_rejects_the_old_error(returncode: int) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    completed = subprocess.CompletedProcess(
        ["podway"],
        returncode,
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
    with pytest.raises(runtime.RuntimeQualificationError):
        runtime.workspace_removal_result(completed, "/tmp/repository", None)


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"daemon_version": "0.2.10"},
        {"daemon_version": "v0.2.9"},
        {"contract_manifest_digest": "sha256:" + "0" * 64},
    ],
)
def test_managed_runtime_requires_v0210_daemon_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changes: dict
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(
        tmp_path / "podway", tmp_path / "podwayd", tmp_path / "procedures", 1
    )
    status = {
        "pid": 123,
        "readiness_state": "ready",
        "readiness_stage": "ready",
        "mode": "release-qa",
        "daemon_version": "v0.2.10",
        "contract_manifest_digest": (
            "sha256:bff8af8f57f1390446333cc56775ca71209e99bd3ff6fd556c39906b77a90635"
        ),
        "in_flight_client_count": 0,
        "maintenance_operation_count": 0,
    }
    status.update(changes)
    monkeypatch.setattr(managed, "daemon_status_probe", lambda: status)
    times = iter([0, 0, runtime.READINESS_TIMEOUT_SECONDS + 1])
    monkeypatch.setattr(runtime.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(runtime.time, "sleep", lambda _: None)
    if changes:
        with pytest.raises(runtime.RuntimeQualificationError):
            managed.wait_ready()
    else:
        managed.wait_ready()
        assert managed.daemon_pid == 123


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
