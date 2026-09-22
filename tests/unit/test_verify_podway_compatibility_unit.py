from __future__ import annotations

import copy
import importlib.util
import json
import os
import socket
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Self

import pytest
import yaml

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
        ("aquarium-goal-v2", "confirm-goal-assessment-core"),
        ("aquarium-validation-v2", "confirm-goal-assessment-core"),
    ),
)
def test_completed_low_settlement_destination_is_procedure_specific(
    procedure_id: str, expected: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    assert runtime.completed_low_settlement_destination(procedure_id) == expected


@pytest.mark.parametrize(
    ("scenario", "review_visits", "expected"),
    (
        ("standard", 1, 1),
        ("standard", 2, 2),
        ("standard", 3, 3),
        ("standard", 4, 4),
        ("task-confirmation-only-wait", 1, 3),
        ("task-confirmation-only-wait", 2, 4),
        ("task-confirmation-only-wait", 3, 5),
        ("task-completed-continue-mulgae", 3, 2),
        ("task-resume-active-mulgae", 3, 0),
    ),
)
def test_task_assessment_ordinal_uses_one_scenario_aware_calculation(
    tmp_path: Path, scenario: str, review_visits: int, expected: int
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(
        tmp_path / "podway",
        tmp_path / "podwayd",
        tmp_path / "procedures",
        1,
    )
    managed.scenario = scenario
    managed.node_visits["review"] = review_visits

    assert managed.task_assessment_ordinal() == expected


@pytest.mark.parametrize(
    ("ordinal", "expected"),
    (
        (0, "work-unit"),
        (1, "work-unit"),
        (2, "work-unit"),
        (3, "work-unit"),
        (4, "remediation-confirmation"),
        (5, "remediation-confirmation"),
    ),
)
def test_task_review_kind_uses_the_ordinal_three_boundary(
    ordinal: int, expected: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    assert runtime.task_review_kind(ordinal) == expected


@pytest.mark.parametrize("ordinal", (-1, True, 1.5, "4"))
def test_task_review_kind_rejects_invalid_ordinals(ordinal: object) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    with pytest.raises(runtime.RuntimeQualificationError, match="invalid Task"):
        runtime.task_review_kind(ordinal)


def test_goal_completed_assessment_counter_matches_ordinal_route_destinations() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    goal_path = (
        Path(__file__).parents[2]
        / "plugins/aquarium/assets/podway/procedures/aquarium-goal-v2.yaml"
    )
    goal = yaml.safe_load(goal_path.read_text(encoding="utf-8"))
    graph = {node["id"]: node for node in goal["graph"]["nodes"]}
    ordinal_nodes = {
        "confirm-completed-assessment-ordinal",
        "confirm-waived-assessment-ordinal",
    }
    destinations = {
        route["to"]
        for node_id in ordinal_nodes
        for route in graph[node_id]["routes"].values()
        if route["to"] != "confirm-extra-assessment-ordinal"
    }
    destinations.add(
        graph["confirm-extra-assessment-ordinal"]["routes"]["authorized-extra"]["to"]
    )

    assert runtime.GOAL_COMPLETED_ASSESSMENT_NODES == destinations


def test_runtime_job_inventory_preserves_behavior_scope() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    waits = runtime.wait_scenario_specs()
    terminals = runtime.terminal_scenario_specs()
    reusable = runtime.reusable_scenario_specs()
    isolated = runtime.isolated_scenario_specs()
    jobs = runtime.runtime_jobs()

    expected_waits = {
        ("aquarium-goal-v2.yaml", "low-blocker-wait"),
        ("aquarium-validation-v2.yaml", "validation-low-blocker-wait"),
        ("aquarium-goal-v2.yaml", "medium-wait"),
        ("aquarium-goal-v2.yaml", "goal-closeout-unmet-wait"),
        ("aquarium-validation-v2.yaml", "validation-medium-wait"),
        ("aquarium-task-v2.yaml", "task-confirmation-only-wait"),
        ("aquarium-task-v2.yaml", "task-resume-active-mulgae"),
        ("aquarium-task-v2.yaml", "task-current-only-switch-rejected"),
        ("aquarium-task-v2.yaml", "task-current-only-waive-rejected"),
        ("aquarium-task-v2.yaml", "task-resume-terminal-orca"),
        ("aquarium-task-v2.yaml", "task-switch-with-waiver-basis-rejected"),
        ("aquarium-task-v2.yaml", "task-waive-with-route-change-basis-rejected"),
        ("aquarium-task-v2.yaml", "task-resume-with-explicit-change-rejected"),
        ("aquarium-task-v2.yaml", "task-planned-with-direction-rejected"),
        (
            "aquarium-task-v2.yaml",
            "task-completed-switch-with-waiver-basis-rejected",
        ),
        (
            "aquarium-task-v2.yaml",
            "task-completed-waive-with-route-change-basis-rejected",
        ),
    }
    expected_terminals = {
        ("task-route-mulgae", "aquarium-task-v2.yaml"),
        ("task-route-orca", "aquarium-task-v2.yaml"),
        ("task-route-native-codex", "aquarium-task-v2.yaml"),
        ("task-route-waived", "aquarium-task-v2.yaml"),
        ("goal-route-mulgae", "aquarium-goal-v2.yaml"),
        ("goal-route-orca", "aquarium-goal-v2.yaml"),
        ("goal-route-native-codex", "aquarium-goal-v2.yaml"),
        ("goal-route-waived", "aquarium-goal-v2.yaml"),
        ("validation-route-mulgae", "aquarium-validation-v2.yaml"),
        ("validation-route-orca", "aquarium-validation-v2.yaml"),
        ("validation-route-native-codex", "aquarium-validation-v2.yaml"),
        ("validation-route-waived", "aquarium-validation-v2.yaml"),
        ("goal-resume-changed-orca-after-incomplete", "aquarium-goal-v2.yaml"),
        ("goal-resume-provider-mismatch-rejected", "aquarium-goal-v2.yaml"),
        (
            "validation-resume-changed-orca-after-incomplete",
            "aquarium-validation-v2.yaml",
        ),
        (
            "validation-resume-provider-mismatch-rejected",
            "aquarium-validation-v2.yaml",
        ),
        (
            "validation-waiver-followup-preserves-prior",
            "aquarium-validation-v2.yaml",
        ),
        ("goal-operational-matrix", "aquarium-goal-v2.yaml"),
        ("task-completion-unverified", "aquarium-task-v2.yaml"),
        ("task-completion-mixed-owners", "aquarium-task-v2.yaml"),
        ("task-finding-inconsistent", "aquarium-task-v2.yaml"),
        ("goal-finding-inconsistent", "aquarium-goal-v2.yaml"),
        ("goal-hardening-defer", "aquarium-goal-v2.yaml"),
        ("task-completed-continue-mulgae", "aquarium-task-v2.yaml"),
        ("task-completed-continue-native-codex", "aquarium-task-v2.yaml"),
        ("task-completed-continue-orca", "aquarium-task-v2.yaml"),
        ("task-completed-continue-waiver", "aquarium-task-v2.yaml"),
        ("task-completed-switch-orca", "aquarium-task-v2.yaml"),
        ("task-completed-waiver", "aquarium-task-v2.yaml"),
        ("task-completed-waiver-switch-native-codex", "aquarium-task-v2.yaml"),
        ("task-completion-implementation-owner", "aquarium-task-v2.yaml"),
        ("task-completion-verification-owner", "aquarium-task-v2.yaml"),
        ("task-completion-documentation-owner", "aquarium-task-v2.yaml"),
        ("task-completion-owner-inconsistent", "aquarium-task-v2.yaml"),
        ("goal-completion-unmet", "aquarium-goal-v2.yaml"),
        ("goal-completion-unverified", "aquarium-goal-v2.yaml"),
        ("validation-completion-unmet", "aquarium-validation-v2.yaml"),
        ("validation-completion-unverified", "aquarium-validation-v2.yaml"),
        ("goal-kind-member-closeout", "aquarium-goal-v2.yaml"),
        ("goal-kind-prevalidation-closeout", "aquarium-goal-v2.yaml"),
        ("goal-kind-epic-closeout", "aquarium-goal-v2.yaml"),
        ("goal-kind-member-native", "aquarium-goal-v2.yaml"),
        ("validation-review-fail", "aquarium-validation-v2.yaml"),
        ("validation-review-inconclusive", "aquarium-validation-v2.yaml"),
        ("validation-review-pass-gaps-1", "aquarium-validation-v2.yaml"),
        ("validation-review-pass-gaps-0", "aquarium-validation-v2.yaml"),
        ("task-stop-preserves-completion", "aquarium-task-v2.yaml"),
        ("goal-stop-preserves-completion", "aquarium-goal-v2.yaml"),
        ("validation-stop-preserves-completion", "aquarium-validation-v2.yaml"),
        ("validation-provider-low-settlement", "aquarium-validation-v2.yaml"),
    }

    assert set(waits) == expected_waits
    assert set(terminals) == expected_terminals
    assert len(waits) == 16
    assert len(terminals) == 50
    assert len({scenario for _procedure, scenario in waits}) == len(waits)
    assert len({scenario for scenario, _procedure in terminals}) == len(terminals)
    assert sum(job["kind"] == "wait" for job in jobs) == len(waits)
    assert sum(job["kind"] == "terminal" for job in jobs) == 4
    assert sum(job["kind"] == "isolated" for job in jobs) == len(isolated) == 9
    assert len(reusable) == 41
    assert sorted(
        spec for job in jobs if job["kind"] == "terminal" for spec in job["scenarios"]
    ) == sorted(reusable)
    assert sorted(
        (job["scenario"], job["procedure_name"])
        for job in jobs
        if job["kind"] == "isolated"
    ) == sorted(isolated)
    assert sorted((*reusable, *isolated)) == sorted(terminals)
    assert [
        (job["procedure_name"], job["scenario"])
        for job in jobs
        if job["kind"] == "wait"
    ] == list(waits)
    assert 1 + len(jobs) == 32  # one deliberate cleanup probe plus scheduled roots
    assert 5 + len(waits) + len(terminals) == 71
    assert (
        sum(
            scenario == runtime.VALIDATION_PROVIDER_LOW_SCENARIO
            for scenario, _procedure in terminals
        )
        == 1
    )
    assert runtime.MAX_PARALLEL_RUNTIMES == 4


def test_prepare_scenario_restores_procedure_and_resets_session_state(
    tmp_path: Path,
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    procedures = tmp_path / "procedures"
    procedures.mkdir()
    source = procedures / "aquarium-task-v2.yaml"
    source.write_bytes(b"id: aquarium-task-v2\n")
    other_source = procedures / "aquarium-goal-v2.yaml"
    other_source.write_bytes(b"id: aquarium-goal-v2\n")
    sandbox = tmp_path / "sandbox"
    installed = sandbox / ".podway" / "procedures"
    installed.mkdir(parents=True)
    target = installed / source.name
    target.write_bytes(b"mutated: true\n")
    other_target = installed / other_source.name
    other_target.write_bytes(b"other-mutated: true\n")
    managed = runtime.ManagedRuntime(
        tmp_path / "podway", tmp_path / "podwayd", procedures, 1
    )
    managed.sandbox = sandbox
    managed.fixture_target = "fixture-target"
    managed.command_sequence = 7
    managed.correction_case_variants = {"C-16": {"variant"}}
    managed.task_review_reworked = True
    managed.node_visits = {"review": 3}
    managed.completed_assessments = {"aquarium-task-v2": 2}

    managed.prepare_scenario(source.name)

    assert target.read_bytes() == source.read_bytes()
    assert other_target.read_bytes() == other_source.read_bytes()
    assert managed.fixture_target == "fixture-target"
    assert managed.command_sequence == 7
    assert managed.correction_case_variants == {"C-16": {"variant"}}
    assert managed.task_review_reworked is False
    assert managed.node_visits == {}
    assert managed.completed_assessments == {}
    assert managed.deadline is not None


def test_execute_runtime_job_stops_between_scenarios_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    cancel_event = threading.Event()
    driven: list[str] = []
    cleanup: list[bool] = []

    class FakeRuntime:
        def __init__(self, *_args: object) -> None:
            self.correction_case_variants: dict[str, set[str]] = {}

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            cleanup.append(True)

        def prepare_scenario(self, _procedure_name: str) -> None:
            pass

        def drive_procedure(
            self, _procedure_name: str, *, scenario: str = "standard"
        ) -> None:
            driven.append(scenario)
            cancel_event.set()

    monkeypatch.setattr(runtime, "ManagedRuntime", FakeRuntime)
    job = {
        "kind": "terminal",
        "batch_id": "terminal-test",
        "scenarios": (
            ("first", "aquarium-task-v2.yaml"),
            ("second", "aquarium-goal-v2.yaml"),
        ),
        "order": 1,
    }

    with pytest.raises(runtime.RuntimeJobCancelled, match="between scenarios"):
        runtime.execute_runtime_job(
            tmp_path / "podway",
            tmp_path / "podwayd",
            tmp_path / "procedures",
            job,
            cancel_event,
        )

    assert driven == ["first"]
    assert cleanup == [True]


def test_execute_runtime_jobs_signals_peer_cancellation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    rendezvous = threading.Barrier(2)
    peer_cancelled = threading.Event()
    jobs = [
        {"kind": "test", "batch_id": "failure", "order": 1},
        {"kind": "test", "batch_id": "peer", "order": 2},
    ]

    def fake_execute_runtime_job(
        _binary: Path,
        _daemon: Path,
        _procedures: Path,
        job: dict[str, object],
        cancel_event: threading.Event,
    ) -> dict[str, object]:
        rendezvous.wait(timeout=2)
        if job["batch_id"] == "failure":
            raise runtime.RuntimeQualificationError("injected failure")
        if cancel_event.wait(timeout=2):
            peer_cancelled.set()
        raise runtime.RuntimeJobCancelled("peer cancelled")

    monkeypatch.setattr(runtime, "runtime_jobs", lambda: jobs)
    monkeypatch.setattr(runtime, "execute_runtime_job", fake_execute_runtime_job)

    with pytest.raises(runtime.RuntimeQualificationError, match="injected failure"):
        runtime.execute_runtime_jobs(
            tmp_path / "podway",
            tmp_path / "podwayd",
            tmp_path / "procedures",
        )

    assert peer_cancelled.is_set()


def test_lifecycle_job_renews_each_scenario_deadline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    procedures = tmp_path / "procedures"
    procedures.mkdir()
    names = [
        "aquarium-design-v2.yaml",
        "aquarium-goal-v2.yaml",
        "aquarium-task-v2.yaml",
        "aquarium-validation-v2.yaml",
        "aquarium-war-room-v2.yaml",
    ]
    for name in names:
        (procedures / name).write_text(f"id: {name}\n", encoding="utf-8")
    renewals: list[str] = []
    driven: list[str] = []

    class FakeRuntime:
        task_required_failure = True
        task_list_limit = True
        task_guard_failure = True
        task_verification_reworked = True
        task_review_reworked = True
        task_medium_reworked = True
        task_review_guard_failure = True
        task_evidence_reworked = True
        task_stale_token = True
        task_snapshot_immutable = True

        def __init__(self, *_args: object) -> None:
            self.low_settlement_procedures = {
                "aquarium-task-v2",
                "aquarium-goal-v2",
                "aquarium-validation-v2",
            }
            self.correction_case_variants: dict[str, set[str]] = {}

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            pass

        def renew_deadline(self) -> None:
            renewals.append("renewed")

        def drive_procedure(self, name: str, *, scenario: str = "standard") -> None:
            assert scenario == "standard"
            driven.append(name)

        def exercise_pagination(self) -> None:
            driven.append("pagination")

    monkeypatch.setattr(runtime, "ManagedRuntime", FakeRuntime)
    result = runtime.execute_runtime_job(
        tmp_path / "podway",
        tmp_path / "podwayd",
        procedures,
        {"kind": "lifecycle", "batch_id": "lifecycle", "order": 1},
        threading.Event(),
    )

    assert driven == [*names, "pagination"]
    assert len(renewals) == len(names) + 1
    assert result["lifecycle_run"]["cleanup"] == "passed"


def test_terminate_removes_owned_stale_socket_after_daemon_exit() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    with tempfile.TemporaryDirectory(
        prefix="podway-socket-", dir="/private/tmp"
    ) as root:
        root_path = Path(root)
        managed = runtime.ManagedRuntime(
            root_path / "podway",
            root_path / "podwayd",
            root_path / "procedures",
            1,
        )
        managed.dev_home = root_path
        run_directory = root_path / "run"
        run_directory.mkdir()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stale_socket:
            stale_socket.bind(str(managed.socket))

        managed.terminate()

        assert not managed.socket.exists()


@pytest.mark.parametrize(
    ("scenario", "direction", "basis", "rejection_node"),
    (
        (
            "task-switch-with-waiver-basis-rejected",
            "switch-route",
            "explicit-waiver",
            "validate-review-route-entry",
        ),
        (
            "task-waive-with-route-change-basis-rejected",
            "waive",
            "explicit-route-change",
            "validate-review-route-entry",
        ),
        (
            "task-resume-with-explicit-change-rejected",
            "resume-current",
            "explicit-route-change",
            "validate-review-route-entry",
        ),
        (
            "task-planned-with-direction-rejected",
            "switch-route",
            None,
            "authorize-planned-review-route",
        ),
        (
            "task-completed-switch-with-waiver-basis-rejected",
            "switch-route",
            "explicit-waiver",
            "validate-review-route-entry",
        ),
        (
            "task-completed-waive-with-route-change-basis-rejected",
            "waive",
            "explicit-route-change",
            "validate-review-route-entry",
        ),
    ),
)
def test_task_direction_mismatch_runtime_scenarios_reject_before_review(
    scenario: str,
    direction: str,
    basis: str | None,
    rejection_node: str,
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    configuration = runtime.TASK_RESUME_SCENARIOS[scenario]

    assert scenario in runtime.TASK_DIRECTION_MISMATCH_SCENARIOS
    assert configuration["direction"] == direction
    assert configuration.get("checkpoint_basis") == basis
    assert configuration["rejection_node"] == rejection_node
    assert rejection_node not in {
        "enter-mulgae-review-route",
        "enter-orca-review-route",
        "enter-native-codex-review-route",
        "enter-waived-review-route",
        "review",
    }


@pytest.mark.parametrize(
    ("scenario", "effective_route", "direction", "basis"),
    (
        (
            "task-completed-switch-orca",
            "orca",
            "switch-route",
            "explicit-route-change",
        ),
        (
            "task-completed-waiver",
            "waived",
            "waive",
            "explicit-waiver",
        ),
    ),
)
def test_completed_checkpoint_runtime_scenarios_map_to_guarded_next_ordinal(
    scenario: str,
    effective_route: str,
    direction: str,
    basis: str,
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    configuration = runtime.TASK_RESUME_SCENARIOS[scenario]

    assert scenario in runtime.TASK_COMPLETED_CHANGE_SCENARIOS
    assert scenario in runtime.TASK_COMPLETED_CHANGE_SUCCESS_SCENARIOS
    assert scenario not in runtime.TASK_DIRECTION_MISMATCH_SCENARIOS
    assert configuration["route"] == "mulgae"
    assert configuration["effective_route"] == effective_route
    assert configuration["operation"] == "complete"
    assert configuration["prior_operation"] == "complete"
    assert configuration["readiness"] == "completed-checkpoint"
    assert configuration["direction"] == direction
    assert configuration["checkpoint_basis"] == basis


@pytest.mark.parametrize(
    ("scenario", "route", "prior_operation"),
    (
        ("task-completed-continue-mulgae", "mulgae", "complete"),
        ("task-completed-continue-orca", "orca", "complete"),
        ("task-completed-continue-native-codex", "native-codex", "complete"),
        ("task-completed-continue-waiver", "waived", "waived"),
    ),
)
def test_completed_current_runtime_scenarios_preserve_route_and_consume_next_ordinal(
    scenario: str, route: str, prior_operation: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    configuration = runtime.TASK_RESUME_SCENARIOS[scenario]

    assert scenario in runtime.TASK_COMPLETED_CHANGE_SUCCESS_SCENARIOS
    assert configuration["route"] == route
    assert configuration["effective_route"] == route
    assert configuration["prior_operation"] == prior_operation
    assert configuration["readiness"] == "completed-checkpoint"
    assert configuration["direction"] == "continue-current"
    assert configuration["checkpoint_basis"] == "continued-checkpoint"


def test_completed_waiver_runtime_scenario_can_switch_to_delegated_route() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    scenario = "task-completed-waiver-switch-native-codex"
    configuration = runtime.TASK_RESUME_SCENARIOS[scenario]

    assert scenario in runtime.TASK_COMPLETED_CHANGE_SUCCESS_SCENARIOS
    assert configuration["route"] == "waived"
    assert configuration["effective_route"] == "native-codex"
    assert configuration["prior_operation"] == "waived"
    assert configuration["readiness"] == "completed-checkpoint"
    assert configuration["direction"] == "switch-route"
    assert configuration["checkpoint_basis"] == "explicit-route-change"


def test_goal_recovery_runtime_scenario_preserves_changed_orca_provider() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification

    assert runtime.GOAL_RECOVERY_SCENARIOS == {
        "goal-resume-changed-orca-after-incomplete",
        "goal-resume-provider-mismatch-rejected",
    }


def test_validation_recovery_runtime_scenario_preserves_previous_operation() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification

    assert runtime.VALIDATION_RECOVERY_SCENARIOS == {
        "validation-resume-changed-orca-after-incomplete",
        "validation-resume-provider-mismatch-rejected",
    }
    assert runtime.VALIDATION_WAIVER_FOLLOWUP_SCENARIOS == {
        "validation-waiver-followup-preserves-prior"
    }


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


def test_workspace_removal_replay_requires_success_with_v7_receipt() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    result = runtime.workspace_removal_result(
        removal_replay_process(), "/tmp/repository", None
    )
    assert result["already_absent"] is True
    assert result["workspace_uuid"] is None
    assert (
        verify_podway_compatibility.RESULT_SCHEMA == "aquarium-podway-compatibility.v7"
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
