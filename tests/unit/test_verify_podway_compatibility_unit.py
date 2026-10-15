from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
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


@pytest.mark.parametrize(
    ("scenario", "procedure", "node", "expected"),
    [
        (
            "goal-completion-unmet",
            "goal",
            "judge-goal",
            ("rework", "not-achieved", 1, 0),
        ),
        (
            "goal-completion-unverified",
            "goal",
            "judge-goal",
            ("evidence-needed", "not-achieved", 0, 1),
        ),
        (
            "validation-completion-unmet",
            "validation",
            "judge-validation",
            ("rework", "not-achieved", 1, 0),
        ),
        (
            "validation-completion-unverified",
            "validation",
            "judge-stopped-validation",
            ("evidence-needed", "not-achieved", 0, 1),
        ),
        (
            "task-stop-preserves-completion",
            "task",
            "judge-stopped-task",
            ("rework", "not-achieved", 1, 0),
        ),
        (
            "goal-stop-preserves-completion",
            "goal",
            "judge-stopped-goal",
            ("rework", "not-achieved", 1, 0),
        ),
        (
            "validation-stop-preserves-completion",
            "validation",
            "judge-stopped-validation",
            ("rework", "not-achieved", 1, 0),
        ),
        ("goal-completion-unmet", "goal", "judge-work", ("pass", "achieved", 0, 0)),
        (
            "goal-completion-unverified",
            "goal",
            "judge-goal-evidence",
            ("pass", "achieved", 0, 0),
        ),
        (
            "validation-completion-unmet",
            "validation",
            "judge-remediation",
            ("pass", "achieved", 0, 0),
        ),
        (
            "validation-completion-unverified",
            "validation",
            "judge-validation-evidence",
            ("pass", "achieved", 0, 0),
        ),
        ("standard", "goal", "judge-goal", ("pass", "achieved", 0, 0)),
        ("standard", "validation", "judge-validation", ("pass", "achieved", 0, 0)),
    ],
)
def test_fixture_judge_preserves_final_gaps_and_phase_results(
    tmp_path: Path,
    scenario: str,
    procedure: str,
    node: str,
    expected: tuple[str, str, int, int],
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.scenario = scenario
    managed.current_procedure_id = f"aquarium-{procedure}-v2"
    actual = []
    for item_id, item_type, constraints in [
        ("judge-verdict", "choice", {"choices": ["pass", "rework", "evidence-needed"]}),
        (
            "judge-goal-outcome",
            "choice",
            {"choices": ["achieved", "not-achieved", "superseded"]},
        ),
        ("judge-unmet-criteria", "integer", {"minimum": 0}),
        ("judge-unverified-criteria", "integer", {"minimum": 0}),
    ]:
        record = managed.value_for(
            {"item_id": item_id, "type": item_type, "constraints": constraints}, node
        )
        assert record["type"] == item_type
        actual.append(record["value"])
    assert tuple(actual) == expected


def git(repository: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repository, check=True)


@pytest.mark.parametrize(
    ("scenario", "review_visit", "verdict", "unmet", "unverified", "checkpoint"),
    [
        ("task-stop-preserves-completion", 1, "rework", 1, 0, "fail"),
        ("task-stop-preserves-completion", 3, "rework", 1, 0, "fail"),
        ("task-stop-preserves-completion", 4, "pass", 0, 0, "pass"),
        ("task-completion-unverified", 2, "evidence-needed", 0, 1, "inconclusive"),
        ("task-completion-unverified", 3, "pass", 0, 0, "pass"),
        ("task-completion-mixed-owners", 2, "rework", 1, 0, "fail"),
        ("task-completion-owner-inconsistent", 2, "rework", 1, 0, "fail"),
    ],
)
def test_fixture_review_judge_preserves_completion_and_checkpoint_results(
    tmp_path: Path,
    scenario: str,
    review_visit: int,
    verdict: str,
    unmet: int,
    unverified: int,
    checkpoint: str,
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.current_procedure_id = "aquarium-task-v2"
    managed.scenario = scenario
    managed.node_visits["review"] = review_visit
    for item_id, item_type, constraints, expected in [
        (
            "judge-verdict",
            "choice",
            {"choices": ["pass", "rework", "evidence-needed"]},
            verdict,
        ),
        ("judge-unmet-criteria", "integer", {"minimum": 0}, unmet),
        ("judge-unverified-criteria", "integer", {"minimum": 0}, unverified),
        (
            "judge-checkpoint-result",
            "check_result",
            {
                "operation_id": "fixture-checkpoint",
                "operation_digest": "sha256:" + "1" * 64,
            },
            checkpoint,
        ),
        (
            "judge-applicability",
            "check_result",
            {
                "operation_id": "fixture-applicability",
                "operation_digest": "sha256:" + "2" * 64,
            },
            "pass",
        ),
    ]:
        record = managed.value_for(
            {"item_id": item_id, "type": item_type, "constraints": constraints},
            "judge-review",
        )
        assert record["type"] == item_type
        assert record["outcome" if item_type == "check_result" else "value"] == expected


@pytest.mark.parametrize("node", ["remediate", "settle-remediation-group"])
@pytest.mark.parametrize("completed", [0, 2, 3, 4])
def test_fixture_preserves_completed_assessments_through_group_settlement(
    tmp_path: Path, node: str, completed: int
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.current_procedure_id = "aquarium-validation-v2"
    managed.completed_assessments["aquarium-validation-v2"] = completed
    assert managed.value_for(
        {
            "item_id": "completed-review-assessments",
            "type": "integer",
            "constraints": {"minimum": 0},
        },
        node,
    ) == {"type": "integer", "value": completed}


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
                "schema": "podway.output/v4",
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
            {"schema": "podway.output/v3", "command": "procedure.check"}
        )


def removal_replay_process(**changes: object) -> subprocess.CompletedProcess[bytes]:
    result = {
        "schema": "podway.workspace-removal-result/v2",
        "worktree_root": "/tmp/repository",
        "workspace_uuid": None,
        "podway_directory_removed": False,
        "already_absent": True,
    }
    result.update(changes)
    return subprocess.CompletedProcess(
        ["podway"],
        0,
        stdout=json.dumps(
            {
                "schema": "podway.output/v4",
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
                "schema": "podway.output/v4",
                "command": "session.decide",
                "result": {
                    "schema": "podway.decision-result/v2",
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
        ("aquarium-task-v2.yaml", "task-low-blocker-implementation"),
        ("aquarium-task-v2.yaml", "task-low-blocker-verification"),
        ("aquarium-task-v2.yaml", "task-low-blocker-documentation"),
        ("aquarium-task-v2.yaml", "task-low-blocker-stop"),
        ("aquarium-task-v2.yaml", "task-low-blocker-one-shot"),
        ("aquarium-goal-v2.yaml", "goal-low-blocker-remediation"),
        ("aquarium-validation-v2.yaml", "validation-low-blocker-remediation"),
        ("aquarium-goal-v2.yaml", "low-blocker-wait"),
        ("aquarium-validation-v2.yaml", "validation-low-blocker-wait"),
        ("aquarium-goal-v2.yaml", "medium-wait"),
        ("aquarium-goal-v2.yaml", "goal-closeout-unmet-wait"),
        ("aquarium-validation-v2.yaml", "validation-medium-wait"),
        ("aquarium-task-v2.yaml", "task-confirmation-only-wait"),
        ("aquarium-task-v2.yaml", "task-resume-active-mulgae"),
        ("aquarium-task-v2.yaml", "task-current-only-switch-rejected"),
        ("aquarium-task-v2.yaml", "task-current-only-waive-rejected"),
        ("aquarium-task-v2.yaml", "task-resume-terminal-herdr"),
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
        ("war-room-no-work", "aquarium-war-room-v2.yaml"),
        ("task-route-mulgae", "aquarium-task-v2.yaml"),
        ("task-route-herdr", "aquarium-task-v2.yaml"),
        ("task-route-independent-review", "aquarium-task-v2.yaml"),
        ("task-route-waived", "aquarium-task-v2.yaml"),
        ("goal-route-mulgae", "aquarium-goal-v2.yaml"),
        ("goal-route-herdr", "aquarium-goal-v2.yaml"),
        ("goal-route-independent-review", "aquarium-goal-v2.yaml"),
        ("goal-route-waived", "aquarium-goal-v2.yaml"),
        ("validation-route-mulgae", "aquarium-validation-v2.yaml"),
        ("validation-route-herdr", "aquarium-validation-v2.yaml"),
        ("validation-route-independent-review", "aquarium-validation-v2.yaml"),
        ("validation-route-waived", "aquarium-validation-v2.yaml"),
        ("goal-resume-changed-herdr-after-incomplete", "aquarium-goal-v2.yaml"),
        ("goal-resume-provider-mismatch-rejected", "aquarium-goal-v2.yaml"),
        (
            "validation-resume-changed-herdr-after-incomplete",
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
        ("task-completed-continue-independent-review", "aquarium-task-v2.yaml"),
        ("task-completed-continue-herdr", "aquarium-task-v2.yaml"),
        ("task-completed-continue-waiver", "aquarium-task-v2.yaml"),
        ("task-completed-switch-herdr", "aquarium-task-v2.yaml"),
        ("task-legacy-orca-switch-herdr", "aquarium-task-v2.yaml"),
        ("task-completed-waiver", "aquarium-task-v2.yaml"),
        ("task-completed-waiver-switch-independent-review", "aquarium-task-v2.yaml"),
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

    expected_terminals.update(
        (f"{family}-local-{mode}", f"aquarium-{family}-v2.yaml")
        for family in ("task", "goal", "validation")
        for mode in ("settled", "retry")
    )
    assert set(waits) == expected_waits
    expected_terminals.update(
        (scenario, "aquarium-task-v2.yaml") for scenario in runtime.GROUPED_TASK_OWNERS
    )
    expected_terminals.update(
        (scenario, f"{procedure}.yaml")
        for scenario, (
            procedure,
            _phase,
            _owner,
        ) in runtime.GROUPED_EVIDENCE_OWNERS.items()
    )
    assert set(terminals) == expected_terminals
    assert len(waits) == 23
    assert len(terminals) == 65
    assert len({scenario for _procedure, scenario in waits}) == len(waits)
    assert len({scenario for scenario, _procedure in terminals}) == len(terminals)
    assert sum(job["kind"] == "wait" for job in jobs) == len(waits)
    terminal_jobs = [job for job in jobs if job["kind"] == "terminal"]
    assert len(terminal_jobs) == len(reusable)
    assert all(len(job["scenarios"]) == 1 for job in terminal_jobs)
    assert sum(job["kind"] == "isolated" for job in jobs) == len(isolated) == 17
    assert len(reusable) == 48
    assert [job["batch_id"] for job in jobs if job["kind"] == "historical-formal"] == [
        "historical-formal-task-v30"
    ]
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
    assert 1 + len(jobs) == 4 + len(terminals) + len(waits)
    assert 6 + len(waits) + len(terminals) == 94
    assert (
        sum(
            scenario == runtime.VALIDATION_PROVIDER_LOW_SCENARIO
            for scenario, _procedure in terminals
        )
        == 1
    )
    assert runtime.MAX_PARALLEL_RUNTIMES == 4


@pytest.mark.parametrize(
    "scenario",
    [
        "task-grouped-implementation",
        "task-grouped-refinement",
        "task-grouped-verification",
        "design-context-evidence",
        "design-discovery-evidence",
        "war-room-baseline-evidence",
        "war-room-investigation-evidence",
    ],
)
def test_grouped_owner_fixture_records_failure_and_selects_exact_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scenario: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.sandbox = tmp_path
    evidence_group = runtime.GROUPED_EVIDENCE_OWNERS.get(scenario)
    if evidence_group:
        procedure, phase, owner = evidence_group
        option = owner
        source = f"record-{phase}-evidence-needed"
        gate = f"confirm-{phase}-evidence-needed-authority"
        expected_route, expected_outcome = "evidence-needed", "inconclusive"
        owners = {
            value[2]
            for value in runtime.GROUPED_EVIDENCE_OWNERS.values()
            if value[0] == procedure
        }
        rejected_options = owners - {owner}
    else:
        procedure, phase = "aquarium-task-v2", "verification"
        option, owner = runtime.GROUPED_TASK_OWNERS[scenario]
        source, gate = (
            "record-verification-followup",
            "confirm-verification-followup-authority",
        )
        expected_route, expected_outcome = "rework", "fail"
        owners = {value[1] for value in runtime.GROUPED_TASK_OWNERS.values()}
        rejected_options = {"implementation", "refinement", "verification"} - {option}
    installed = tmp_path / f".podway/procedures/{procedure}.yaml"
    installed.parent.mkdir(parents=True)
    installed.write_text(f"id: {procedure}\n")
    digest = "sha256:" + "0" * 64
    monkeypatch.setattr(
        managed,
        "preview",
        lambda _: {
            "procedure_id": procedure,
            "procedure_digest": digest,
            "start_suggestion": {
                "argv": [
                    "podway",
                    "start",
                    "--procedure",
                    f".podway/procedures/{procedure}.yaml",
                    "--expect-procedure-digest",
                    digest,
                    "--task",
                    "<title>",
                ]
            },
        },
    )
    monkeypatch.setattr(
        managed,
        "raw",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [],
            0,
            json.dumps(
                {
                    "schema": runtime.OUTPUT_SCHEMA,
                    "command": "session.start",
                    "result": {
                        "schema": "podway.session-start-result/v4",
                        "session_state": "prepared",
                    },
                }
            ).encode(),
            b"",
        ),
    )
    monkeypatch.setattr(managed, "begin_goal", lambda *_: None)

    def observation(node: str) -> dict:
        return {
            "status": {
                "procedure": {"digest": digest},
                "session": {"lifecycle": "running"},
            },
            "guidance": {"node": {"graph_node_id": node, "node_type": "decision"}},
        }

    observed = iter(
        [
            observation("prepared"),
            observation(
                f"decide-{phase}-assessment"
                if evidence_group
                else "decide-verification"
            ),
            observation(gate),
            observation(owner),
        ]
    )
    monkeypatch.setattr(managed, "observe", lambda: next(observed))
    rejected = []
    monkeypatch.setattr(
        managed,
        "reject_guarded_decision",
        lambda obs, value: rejected.append(value) or obs,
    )
    monkeypatch.setattr(managed, "decide", lambda _obs, value: value)
    destinations = []
    monkeypatch.setattr(
        managed,
        "decision_destination",
        lambda decision, target: destinations.append((decision, target)),
    )
    result = managed.drive_procedure(installed.name, scenario=scenario)
    assert result["semantic_owner"] == owner
    assert result["guarded_owner_route"] == option
    assert destinations == [(expected_route, source), (option, owner)]
    assert set(rejected) == {
        "passed",
        "blocked",
        *rejected_options,
    }
    owner_record = managed.value_for(
        {
            "type": "choice",
            "item_id": "semantic-owner",
            "constraints": {"choices": sorted(owners)},
        },
        source,
    )
    assert owner_record["value"] == owner
    check = managed.value_for(
        {
            "type": "check_result",
            "item_id": "judge-checkpoint-result",
            "constraints": {"operation_id": "checkpoint", "operation_digest": digest},
        },
        f"judge-{phase}",
    )
    assert check["outcome"] == expected_outcome


@pytest.mark.parametrize("formal", [False, True])
@pytest.mark.parametrize("item_id", ["worker-handoff", "judge-assessment"])
def test_structural_reports_select_contract_without_claiming_actual_delivery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, formal: bool, item_id: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.sandbox = tmp_path
    managed.placements = {"fixture": {}} if formal else {}
    monkeypatch.setattr(managed, "raw", lambda *_args, **_kwargs: None)
    managed.attach_fixture_report(
        {
            "guidance": {"node": {"graph_node_id": "fixture"}},
            "mutation_templates": [
                {
                    "command": "item.attach",
                    "argv": ["podway", item_id, "<path>", "<idempotency-key>"],
                }
            ],
        },
        {"item_id": item_id},
    )
    report = json.loads(next(tmp_path.glob("synthetic-*.json")).read_text())
    assert report["schema"] == "aquarium.synthetic-structural-report/v1"
    assert report["synthetic"] is True
    assert (
        report["expected_report_schema"]
        == f"aquarium.{item_id}/{'v1' if formal else 'v2'}"
    )


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
    managed = runtime.ManagedRuntime(tmp_path / "podway", procedures, 1)
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
        delegation_receipt_count = 0
        missing_receipt_guards = frozenset()
        stale_receipt_guards = frozenset()
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
        preparation_reworks = 2
        low_delta_composed = True
        plan_artifact_verified_nodes = frozenset(
            {"record-plan", "prepare-implementation", "implement"}
        )

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

        def raw(self, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
            assert arguments == ["archive", "list", "--json"]
            summary = {"session_id": "archived-session"}
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout=json.dumps(
                    {
                        "schema": "podway.output/v4",
                        "command": "session.archive_list",
                        "result": {
                            "schema": "podway.session-archive-list-result/v2",
                            "count": 1,
                            "truncated": False,
                            "oldest": summary,
                            "sessions": [summary],
                        },
                    }
                ).encode(),
                stderr=b"",
            )

    monkeypatch.setattr(runtime, "ManagedRuntime", FakeRuntime)
    result = runtime.execute_runtime_job(
        tmp_path / "podway",
        procedures,
        {"kind": "lifecycle", "batch_id": "lifecycle", "order": 1},
        threading.Event(),
    )

    assert driven == [*names, "pagination"]
    assert len(renewals) == len(names) + 1
    assert result["lifecycle_run"]["cleanup"] == "passed"


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
        "enter-herdr-review-route",
        "enter-independent-review-route",
        "enter-waived-review-route",
        "review",
    }


@pytest.mark.parametrize(
    ("scenario", "effective_route", "direction", "basis"),
    (
        (
            "task-completed-switch-herdr",
            "herdr",
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
        ("task-completed-continue-herdr", "herdr", "complete"),
        (
            "task-completed-continue-independent-review",
            "independent-review",
            "complete",
        ),
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
    scenario = "task-completed-waiver-switch-independent-review"
    configuration = runtime.TASK_RESUME_SCENARIOS[scenario]

    assert scenario in runtime.TASK_COMPLETED_CHANGE_SUCCESS_SCENARIOS
    assert configuration["route"] == "waived"
    assert configuration["effective_route"] == "independent-review"
    assert configuration["prior_operation"] == "waived"
    assert configuration["readiness"] == "completed-checkpoint"
    assert configuration["direction"] == "switch-route"
    assert configuration["checkpoint_basis"] == "explicit-route-change"


def test_goal_recovery_runtime_scenario_preserves_changed_herdr_provider() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification

    assert runtime.GOAL_RECOVERY_SCENARIOS == {
        "goal-resume-changed-herdr-after-incomplete",
        "goal-resume-provider-mismatch-rejected",
    }


def test_validation_recovery_runtime_scenario_preserves_previous_operation() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification

    assert runtime.VALIDATION_RECOVERY_SCENARIOS == {
        "validation-resume-changed-herdr-after-incomplete",
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
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path / "procedures", 1)
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


@pytest.mark.parametrize(
    "scenario,authority_node,effect_node",
    [
        (
            "goal-low-blocker-remediation",
            "decide-goal-rework-authority",
            "confirm-goal-rework-effect-authority",
        ),
        (
            "validation-low-blocker-remediation",
            "decide-validation-rework-authority",
            "confirm-validation-rework-effect-authority",
        ),
    ],
)
def test_low_blocker_rework_effect_records_complete_cause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
    authority_node: str,
    effect_node: str,
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path / "procedures", 1)
    managed.scenario = scenario
    managed.fixture_target = "a" * 40
    basis = '{"source_id":"fixture:low-source","blocker":"current"}\n'
    evidence = {
        "low-disposition-summary": basis,
        "after-target": managed.fixture_target,
    }
    monkeypatch.setattr(
        managed,
        "read_complete_evidence",
        lambda _observation, source, item: (
            evidence[item]
            if source == "record-low-disposition"
            else pytest.fail("The rework cause must come from its original disposition")
        ),
    )
    observation = {
        "guidance": {"node": {"graph_node_id": authority_node}},
        "mutation_templates": [
            {
                "command": "session.decide",
                "argv": [
                    "podway",
                    "decide",
                    "--option",
                    "remediation",
                    "--reason",
                    "<reason>",
                    "--if-attempt",
                    "current-effect-attempt",
                    "--idempotency-key",
                    "<idempotency-key>",
                ],
            }
        ],
    }
    calls = []

    def raw(arguments: list[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr(managed, "raw", raw)
    managed.decide(observation, "remediation")
    original_cause = managed.entry_rework_reason
    observation["guidance"]["node"]["graph_node_id"] = effect_node
    observation["mutation_templates"][0]["argv"][3] = "authorized"
    monkeypatch.setattr(
        managed,
        "read_complete_evidence",
        lambda *_args: pytest.fail("The effect must reuse the complete original cause"),
    )
    managed.decide(observation, "authorized")
    assert len(calls) == 2
    arguments = calls[1]
    cause = arguments[arguments.index("--reason") + 1]
    assert json.loads(cause) == {
        "basis": basis,
        "target": managed.fixture_target,
        "authority": "fixture-current-envelope",
    }
    assert managed.entry_rework_reason == cause == original_cause
    assert arguments[arguments.index("--if-attempt") + 1] == "current-effect-attempt"


def test_workspace_removal_replay_requires_success_with_v9_receipt() -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    result = runtime.workspace_removal_result(
        removal_replay_process(), "/tmp/repository", None
    )
    assert result["already_absent"] is True
    assert result["workspace_uuid"] is None
    assert (
        verify_podway_compatibility.RESULT_SCHEMA == "aquarium-podway-compatibility.v9"
    )
    assert verify_podway_compatibility.EXPECTED_VERSION == "v0.2.14"


@pytest.mark.parametrize(
    ("name", "version", "accepted"),
    [
        ("podway", "v0.2.14", True),
        ("podway", "v0.2.13", False),
        ("podway", "v0.2.11", False),
        ("podway", "v0.3.0", False),
    ],
)
def test_compatibility_requires_exact_release_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    version: str,
    accepted: bool,
) -> None:
    monkeypatch.setattr(
        verify_podway_compatibility,
        "run",
        lambda *_args: (0, {"name": name, "version": version}),
    )
    if accepted:
        verify_podway_compatibility.require_version(tmp_path / name, tmp_path, name)
    else:
        with pytest.raises(verify_podway_compatibility.CompatibilityError):
            verify_podway_compatibility.require_version(tmp_path / name, tmp_path, name)


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
        {"schema": "podway.workspace-removal-result/v1"},
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
                "schema": "podway.error/v2",
                "command": "workspace.remove",
                "code": "WORKSPACE_CONFIG_INVALID",
                "retryable": False,
            }
        ).encode(),
        stderr=b"",
    )
    with pytest.raises(runtime.RuntimeQualificationError):
        runtime.workspace_removal_result(completed, "/tmp/repository", None)


def test_managed_runtime_cleans_up_when_setup_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_module = verify_podway_compatibility.podway_runtime_qualification
    binary = tmp_path / "podway"
    procedures = tmp_path / "procedures"
    procedures.mkdir()
    for executable in (binary,):
        executable.write_bytes(b"fixture")
        executable.chmod(0o755)

    def fail_setup(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        raise runtime_module.RuntimeQualificationError("setup fixture failed")

    monkeypatch.setattr(runtime_module, "bounded_process", fail_setup)
    managed = runtime_module.ManagedRuntime(binary, procedures, 1)

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
    procedures = tmp_path / "procedures"
    procedures.mkdir()
    for executable in (binary,):
        executable.write_bytes(b"fixture")
        executable.chmod(0o755)

    def fail_chmod(self: Path, mode: int) -> None:
        raise OSError("chmod fixture failed")

    monkeypatch.setattr(runtime_module.Path, "chmod", fail_chmod)
    managed = runtime_module.ManagedRuntime(binary, procedures, 1)

    with pytest.raises(OSError, match="chmod fixture failed"):
        managed.__enter__()

    assert managed.root is not None
    assert not managed.root.exists()


def test_exact_binary_requires_an_absolute_path() -> None:
    with pytest.raises(
        verify_podway_compatibility.CompatibilityError,
        match="absolute path",
    ):
        verify_podway_compatibility.exact_binary("podway")


@pytest.mark.parametrize(
    "procedure_name",
    [
        "aquarium-task-v2.yaml",
        "aquarium-goal-v2.yaml",
        "aquarium-validation-v2.yaml",
        "aquarium-design-v2.yaml",
        "aquarium-war-room-v2.yaml",
    ],
)
@pytest.mark.parametrize("delegated", [False, True])
@pytest.mark.parametrize("wrong_schema", [False, True])
def test_procedure_authoring_binds_preview_schema_to_delegation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    delegated: bool,
    wrong_schema: bool,
    procedure_name: str,
) -> None:
    module = verify_podway_compatibility
    procedure = tmp_path / procedure_name
    placement = {"id": "candidate", "use": "work"}
    if delegated:
        placement["delegation"] = {"role_ref": "worker"}
    procedure.write_text(
        yaml.safe_dump(
            {"schema": "podway.procedure/v2", "graph": {"nodes": [placement]}}
        )
    )
    digest = "sha256:" + "a" * 64

    def run(binary: Path, arguments: list[str], repository: Path) -> tuple[int, dict]:
        stage = arguments[2]
        schema = (
            module.SOURCE_SCHEMA if stage == "format" else module.DIAGNOSTICS_SCHEMA
        )
        result = {"schema": schema, "valid": True}
        if stage == "preview":
            is_delegated_schema = delegated != wrong_schema
            result = {
                "schema": module.DELEGATED_PREVIEW_SCHEMA
                if is_delegated_schema
                else module.PREVIEW_SCHEMA,
                "admissible": True,
                "procedure_id": procedure.stem,
                "procedure_digest": digest,
                "start_suggestion": {
                    "argv": [
                        "podway",
                        "start",
                        "--procedure",
                        procedure.name,
                        "--expect-procedure-digest",
                        digest,
                        "--task",
                        "<title>",
                    ]
                },
            }
            if delegated:
                result.update(
                    delegated_placement_count=1, delegated_placements=["candidate"]
                )
        return 0, {
            "schema": module.OUTPUT_SCHEMA,
            "command": "procedure." + stage,
            "result": result,
        }

    monkeypatch.setattr(module, "run", run)
    if wrong_schema:
        with pytest.raises(module.CompatibilityError, match="incompatible preview"):
            module.require_valid_procedure(tmp_path / "podway", tmp_path, procedure)
    else:
        module.require_valid_procedure(tmp_path / "podway", tmp_path, procedure)


@pytest.mark.parametrize("delegated", [False, True])
@pytest.mark.parametrize("wrong_schema", [False, True])
def test_runtime_preview_and_observation_follow_admitted_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    delegated: bool,
    wrong_schema: bool,
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.sandbox = tmp_path
    declaration = {"role_ref": "fixture-worker"}
    node = {"id": "fixture-action", "use": "fixture"}
    if delegated:
        node["delegation"] = declaration
    (tmp_path / "fixture.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "podway.procedure/v2",
                "id": "fixture",
                "version": "7",
                "graph": {"nodes": [node]},
            }
        )
    )

    def raw(arguments: list[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
        preview = "procedure" in arguments
        version = (2 if delegated else 1) if preview else 5
        if wrong_schema:
            version = (3 - version) if preview else (7 - version)
        result = {
            "schema": f"podway.procedure-preview-result/v{version}"
            if preview
            else f"podway.observation-result/v{version}"
        }
        if preview:
            result.update(
                procedure_id="fixture",
                procedure_schema="podway.procedure/v2",
                procedure_version="7",
                admissible=True,
            )
        if preview and delegated:
            result.update(
                delegated_placement_count=1, delegated_placements=["fixture-action"]
            )
        payload = {
            "schema": runtime.OUTPUT_SCHEMA,
            "command": "procedure.preview" if preview else "session.observe",
            "result": result,
        }
        return subprocess.CompletedProcess(
            arguments, 0, json.dumps(payload).encode(), b""
        )

    monkeypatch.setattr(managed, "raw", raw)
    if wrong_schema:
        with pytest.raises(runtime.RuntimeQualificationError):
            managed.preview("fixture.yaml")
    else:
        managed.preview("fixture.yaml")
        assert managed.placements == (
            {"fixture-action": declaration} if delegated else {}
        )
        managed.observe()
        monkeypatch.setattr(
            managed,
            "raw",
            lambda args, **kw: subprocess.CompletedProcess(
                args,
                0,
                json.dumps(
                    {
                        "schema": runtime.OUTPUT_SCHEMA,
                        "command": "session.observe",
                        "result": {"schema": "podway.observation-result/v4"},
                    }
                ).encode(),
                b"",
            ),
        )
        with pytest.raises(runtime.RuntimeQualificationError):
            managed.observe()


@pytest.mark.parametrize(
    "field",
    [
        "placement_id",
        "procedure_digest",
        "workspace_uuid",
        "session_id",
        "attempt_id",
        "goal",
        "delegation",
    ],
)
def test_runtime_rejects_delegation_package_for_different_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    declaration = {
        "binding_ref": "fixture",
        "role_ref": "worker",
        "role_snapshot_digest": "sha256:" + "a" * 64,
        "after_accept": "retain",
        "max_rounds": 32,
    }
    managed.placements = {"fixture-action": declaration}
    status = {
        "session": {"id": "fixture-session", "revision": 3},
        "current": {"attempt": {"attempt_id": "fixture-attempt"}},
        "procedure": {"digest": "sha256:" + "b" * 64},
        "goal_revision": 1,
    }
    observation = {
        "status": status,
        "guidance": {
            "node": {"graph_node_id": "fixture-action"},
            "goal": {"revision": 1, "statement": "Fixture goal", "criteria": []},
        },
        "mutation_templates": [
            {"preconditions": {"workspace_uuid": "fixture-workspace"}}
        ],
    }
    package = {
        "workspace_uuid": "fixture-workspace",
        "session_id": "fixture-session",
        "attempt_id": "fixture-attempt",
        "placement_id": "fixture-action",
        "procedure_digest": status["procedure"]["digest"],
        "schema": "podway.delegation-work-package/v1",
        "goal": {"revision": 1, "statement": "Fixture goal", "criteria": []},
        "delegation": declaration,
    }
    package[field] = (
        {"revision": 2}
        if field == "goal"
        else {}
        if field == "delegation"
        else "different"
    )
    calls = []

    def raw(arguments: list[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
        calls.append(arguments)
        result = {
            "schema": "podway.delegation-package-result/v1",
            "session_revision": 3,
            "workspace_uuid": "fixture-workspace",
            "session_id": "fixture-session",
            "attempt_id": "fixture-attempt",
            "package": package,
        }
        return subprocess.CompletedProcess(
            arguments,
            0,
            json.dumps(
                {
                    "schema": runtime.OUTPUT_SCHEMA,
                    "command": "delegation.package",
                    "result": result,
                }
            ).encode(),
            b"",
        )

    monkeypatch.setattr(managed, "raw", raw)
    with pytest.raises(
        runtime.RuntimeQualificationError, match="changed admitted inputs"
    ):
        managed.accept_fixture_delegation(observation)
    assert calls == [["--json", "delegation", "package"]]


def test_delegated_completion_uses_accepted_revision_and_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.placements = {"fixture-action": {}}
    original = {"guidance": {"node": {"graph_node_id": "fixture-action"}}}
    accepted = {
        "mutation_templates": [
            {
                "command": "session.complete",
                "argv": [
                    "podway",
                    "complete",
                    "--if-session-revision",
                    "7",
                    "--if-attempt",
                    "retried-attempt",
                    "--idempotency-key",
                    "<idempotency-key>",
                ],
            }
        ]
    }
    monkeypatch.setattr(managed, "accept_fixture_delegation", lambda _: accepted)
    monkeypatch.setattr(
        managed, "observe", lambda: pytest.fail("No mutation needs another observation")
    )
    calls = []

    def raw(arguments: list[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr(managed, "raw", raw)
    managed.invoke_template(original, "session.complete")
    assert len(calls) == 1
    arguments = calls[0]
    assert arguments[arguments.index("--if-session-revision") + 1] == "7"
    assert arguments[arguments.index("--if-attempt") + 1] == "retried-attempt"


def test_action_returns_observation_after_its_last_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    before = {
        "guidance": {"node": {"graph_node_id": "fixture-action"}},
        "active_items": [{"item_id": "summary", "type": "text", "required_now": True}],
    }
    after = {**before, "active_items": [], "revision": 2}
    records = []
    monkeypatch.setattr(managed, "value_for", lambda *_: {"type": "text", "value": "x"})
    monkeypatch.setattr(managed, "record", lambda _, values: records.append(values))
    monkeypatch.setattr(managed, "observe", lambda: after)
    assert managed.fill_action(before, "fixture-procedure") is after
    assert records == [{"summary": {"type": "text", "value": "x"}}]


def test_conditional_verification_returns_fresh_post_rejection_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    before = {
        "guidance": {"node": {"graph_node_id": "verify"}},
        "active_items": [
            {
                "item_id": "verification-result",
                "type": "check_result",
                "required_now": True,
            },
            {"item_id": "verification-observations", "type": "list"},
        ],
    }
    missing = copy.deepcopy(before)
    full = {**before, "revision": 3}
    after_rejection = {**full, "post_rejection_readback": True}
    readbacks = iter([before, missing, full, after_rejection])
    monkeypatch.setattr(managed, "qualify_plan_artifact", lambda *_: None)
    monkeypatch.setattr(managed, "observe", lambda: next(readbacks))
    monkeypatch.setattr(managed, "record", lambda *_: None)
    monkeypatch.setattr(managed, "value_for", lambda *_: {"type": "check_result"})
    monkeypatch.setattr(
        managed,
        "invoke_template",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [],
            1,
            json.dumps(
                {"schema": runtime.ERROR_SCHEMA, "code": "REQUIRED_ITEMS_MISSING"}
            ).encode(),
            b"",
        ),
    )
    rejected = []

    def reject(observation, values):
        rejected.append((observation, values))
        return "ITEM_CONSTRAINT_FAILED"

    monkeypatch.setattr(managed, "try_record_failure", reject)
    assert managed.fill_action(before, "aquarium-task-v2") is after_rejection
    assert rejected[0][0] is full
    assert len(rejected[0][1]["verification-observations"]["value"]) == 21
    assert managed.task_required_failure and managed.task_list_limit


@pytest.mark.parametrize("elapsed", [0, 1])
def test_expired_runtime_deadline_rejects_before_invoking_a_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, elapsed: int
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.snapshot_binary = tmp_path / "podway"
    managed.sandbox = tmp_path
    managed.environment = {}
    managed.deadline = 100
    monkeypatch.setattr(runtime.time, "monotonic", lambda: 100 + elapsed)
    monkeypatch.setattr(
        runtime,
        "bounded_process",
        lambda *_args, **_kwargs: pytest.fail("Expired deadline invoked a child"),
    )
    with pytest.raises(runtime.RuntimeQualificationError):
        managed.raw(["observe", "--json"])


@pytest.mark.parametrize("remaining_fraction", [0.25, 2])
def test_runtime_clips_child_timeout_to_remaining_scenario_and_command_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, remaining_fraction: float
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.snapshot_binary = tmp_path / "podway"
    managed.sandbox = tmp_path
    managed.environment = {}
    remaining = runtime.COMMAND_TIMEOUT_SECONDS * remaining_fraction
    managed.deadline = 100 + remaining
    monkeypatch.setattr(runtime.time, "monotonic", lambda: 100)
    timeouts = []

    def run(arguments, **kwargs):
        timeouts.append(kwargs["timeout_seconds"])
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr(runtime, "bounded_process", run)
    managed.raw(["observe", "--json"])
    assert timeouts == [min(remaining, runtime.COMMAND_TIMEOUT_SECONDS)]


def test_execute_runtime_jobs_isolates_lifecycle_and_preserves_results(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    jobs = [
        {"kind": "terminal", "batch_id": "first", "order": 1, "scenario": "alpha"},
        {"kind": "wait", "batch_id": "waiting", "order": 2},
        {"kind": "lifecycle", "batch_id": "canonical", "order": 3},
        {"kind": "terminal", "batch_id": "second", "order": 4, "scenario": "beta"},
        {"kind": "workspace-removal", "batch_id": "removal", "order": 5},
        {"kind": "isolated", "batch_id": "isolated", "order": 6, "scenario": "gamma"},
    ]
    original_jobs = copy.deepcopy(jobs)
    canonical_started = threading.Event()
    canonical_release = threading.Event()
    canonical_finished = threading.Event()
    independent_started = threading.Event()
    first_wave_started = threading.Event()
    independent_release = threading.Event()
    lock = threading.Lock()
    observed_jobs: list[dict[str, object]] = []
    active = 0
    maximum_active = 0

    def fake_execute_runtime_job(
        _binary: Path,
        _procedures: Path,
        job: dict[str, object],
        _cancel_event: threading.Event,
    ) -> dict[str, object]:
        nonlocal active, maximum_active
        with lock:
            observed_jobs.append(job)
        if job["kind"] == "lifecycle":
            canonical_started.set()
            assert canonical_release.wait(timeout=3)
            canonical_finished.set()
        else:
            independent_started.set()
            assert canonical_finished.is_set()
            with lock:
                active += 1
                maximum_active = max(maximum_active, active)
                if active == 4:
                    first_wave_started.set()
            try:
                assert independent_release.wait(timeout=3)
            finally:
                with lock:
                    active -= 1
        result: dict[str, object] = {
            "order": job["order"],
            "batch": {"batch_id": job["batch_id"]},
            "case_variants": {"fixture-case": {str(job["order"])}},
        }
        if job["kind"] == "lifecycle":
            result["lifecycle_run"] = {"pass": "canonical"}
        elif job["kind"] == "workspace-removal":
            result["workspace_removal"] = {"removed": True}
        elif job["kind"] == "wait":
            result["wait_scenario"] = {"batch_id": job["batch_id"]}
        else:
            result["scenario_runs"] = [{"scenario": job["scenario"]}]
        return result

    monkeypatch.setattr(runtime, "runtime_jobs", lambda: jobs)
    monkeypatch.setattr(runtime, "execute_runtime_job", fake_execute_runtime_job)
    monkeypatch.setattr(
        runtime,
        "terminal_scenario_specs",
        lambda: (("gamma", "fixture"), ("alpha", "fixture"), ("beta", "fixture")),
    )
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=1) as driver:
        future = driver.submit(
            runtime.execute_runtime_jobs,
            tmp_path / "podway",
            tmp_path / "procedures",
        )
        try:
            assert canonical_started.wait(timeout=3)
            assert not independent_started.wait(timeout=0.02)
            canonical_release.set()
            assert first_wave_started.wait(timeout=3)
            with lock:
                assert active == 4
                assert maximum_active == 4
            independent_release.set()
            result = future.result(timeout=3)
        finally:
            canonical_release.set()
            independent_release.set()

    assert jobs == original_jobs
    assert observed_jobs[0] is jobs[2]
    assert len(observed_jobs) == len(jobs)
    assert {id(job) for job in observed_jobs} == {id(job) for job in jobs}
    assert maximum_active == 4
    assert [batch["batch_id"] for batch in result["runtime_batches"]] == [
        job["batch_id"] for job in jobs
    ]
    assert result["case_variants"] == {"fixture-case": {"1", "2", "3", "4", "5", "6"}}
    assert result["lifecycle_runs"] == [{"pass": "canonical"}]
    assert result["workspace_removal"] == {"removed": True}
    assert result["wait_scenarios"] == [{"batch_id": "waiting"}]
    assert [item["scenario"] for item in result["scenario_runs"]] == [
        "gamma",
        "alpha",
        "beta",
    ]


def test_execute_runtime_jobs_failed_lifecycle_dispatches_no_independent_jobs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    jobs = [
        {"kind": "test", "batch_id": "independent", "order": 1},
        {"kind": "lifecycle", "batch_id": "canonical", "order": 2},
    ]
    original_jobs = copy.deepcopy(jobs)
    called: list[dict[str, object]] = []
    failure = runtime.RuntimeQualificationError("canonical failure")

    def fake_execute_runtime_job(
        _binary: Path,
        _procedures: Path,
        job: dict[str, object],
        _cancel_event: threading.Event,
    ) -> dict[str, object]:
        called.append(job)
        if job["kind"] != "lifecycle":
            raise AssertionError("independent work dispatched before canonical pass")
        raise failure

    monkeypatch.setattr(runtime, "runtime_jobs", lambda: jobs)
    monkeypatch.setattr(runtime, "execute_runtime_job", fake_execute_runtime_job)
    with pytest.raises(runtime.RuntimeQualificationError) as captured:
        runtime.execute_runtime_jobs(tmp_path / "podway", tmp_path / "procedures")
    assert captured.value is failure
    assert called == [jobs[1]]
    assert called[0] is jobs[1]
    assert jobs == original_jobs


@pytest.mark.parametrize("family", ["task", "goal", "validation"])
@pytest.mark.parametrize("mode", ["settled", "retry"])
def test_local_qualification_profiles_retain_source_and_retry_current_checks(
    tmp_path: Path, family: str, mode: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    scenario = f"{family}-local-{mode}"
    assert (scenario, f"aquarium-{family}-v2.yaml") in runtime.terminal_scenario_specs()
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.scenario = scenario
    managed.current_procedure_id = f"aquarium-{family}-v2"
    source = {
        "task": "review",
        "goal": "record-evidence",
        "validation": "final-review",
    }[family]
    procedure = yaml.safe_load(
        (
            Path(__file__).parents[2]
            / f"plugins/aquarium/assets/podway/procedures/aquarium-{family}-v2.yaml"
        ).read_bytes()
    )
    graph = {node["id"]: node for node in procedure["graph"]["nodes"]}
    source_items = {
        item["id"]: item
        for item in procedure["node_definitions"][graph[source]["use"]]["items"]
    }
    settlement_items = {
        item["id"]: item
        for item in procedure["node_definitions"][
            graph["record-low-disposition"]["use"]
        ]["items"]
    }
    for visit in (1, 2):
        managed.node_visits["record-low-disposition"] = visit
        for item_id in (
            "local-correction-count",
            "medium-or-higher-findings"
            if family == "validation"
            else "effective-medium-or-higher-findings",
            "completion-unmet-criteria",
        ):
            assert source_items[item_id]["type"] == "integer"
            assert (
                managed.value_for(
                    {
                        "item_id": item_id,
                        "type": "integer",
                        "constraints": {"minimum": 0},
                    },
                    source,
                )["value"]
                == 1
            )
        pending = managed.value_for(
            {
                "item_id": "pending-local-corrections",
                "type": "integer",
                "constraints": {"minimum": 0},
            },
            "record-low-disposition",
        )
        assert pending["value"] == int(mode == "retry" and visit == 1)
        managed.low_settlement_rounds[managed.current_procedure_id] = visit - 1
        for item_id in (
            "pending-low-dispositions",
            "current-blocking-findings",
            "completion-unmet-criteria",
            "completion-unverified-criteria",
            *(("current-required-evidence-gaps",) if family == "validation" else ()),
        ):
            assert settlement_items[item_id]["type"] == "integer"
            assert (
                managed.value_for(
                    {
                        "item_id": item_id,
                        "type": "integer",
                        "constraints": {"minimum": 0},
                    },
                    "record-low-disposition",
                )["value"]
                == 0
            )
        check = managed.value_for(
            {
                "item_id": "low-disposition-verification",
                "type": "check_result",
                "constraints": {
                    "operation_id": "fixture",
                    "operation_digest": "sha256:" + "a" * 64,
                },
            },
            "record-low-disposition",
        )
        assert check["outcome"] == (
            "fail" if mode == "retry" and visit == 1 else "pass"
        )
        assert isinstance(check["input_basis"], dict)
        assert isinstance(check["executor"], dict)


@pytest.mark.parametrize(
    "verdict,expected",
    [
        ("pass", "complete"),
        ("rework", "rework"),
        ("evidence-needed", "evidence-needed"),
    ],
)
def test_local_task_qualification_routes_latest_judge_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, verdict: str, expected: str
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    managed = runtime.ManagedRuntime(tmp_path / "podway", tmp_path, 1)
    managed.scenario = "task-local-settled"

    def read(observation: dict, node: str, item: str) -> str:
        assert node == "judge-review" and item == "judge-verdict"
        return verdict

    monkeypatch.setattr(managed, "read_complete_evidence", read)
    assert (
        managed.local_correction_decision({}, "confirm-review-completion") == expected
    )


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"version": "v0.2.13"},
        {"version": "v0.3.0"},
        {"target": "x86_64-apple-darwin"},
        {"source_commit": "a" * 40},
        {"contract_manifest_digest": "sha256:" + "a" * 64},
        {"contract_manifest_schema": "podway.contract-manifest/v1"},
        {"build_identity": "invalid"},
    ],
)
def test_exact_artifact_identity_requires_release_contract(changes: dict) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    identity = {
        "schema": "podway.version-result/v2",
        "product": "podway",
        "version": runtime.EXPECTED_VERSION,
        "target": "aarch64-apple-darwin",
        "source_commit": runtime.RELEASE_SOURCE_COMMIT,
        "contract_manifest_digest": runtime.CONTRACT_MANIFEST_DIGEST,
        "contract_manifest_schema": "podway.contract-manifest/v2",
        "build_identity": "sha256:" + "b" * 64,
    } | changes
    completed = subprocess.CompletedProcess(
        [],
        0,
        json.dumps(
            {"schema": "podway.output/v4", "command": "version", "result": identity}
        ).encode(),
        b"",
    )
    if changes:
        with pytest.raises(runtime.RuntimeQualificationError):
            runtime.release_identity(completed)
    else:
        assert runtime.release_identity(completed) == identity


@pytest.mark.parametrize("guards_exercised", [False, True])
def test_historical_formal_job_requires_its_preserved_source_and_receipt_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guards_exercised: bool
) -> None:
    runtime = verify_podway_compatibility.podway_runtime_qualification
    procedures = Path(__file__).parents[2] / "plugins/aquarium/assets/podway/procedures"
    fixture = Path(__file__).parents[1] / "fixtures/aquarium-task-v30.yaml"
    target = tmp_path / ".podway/procedures/aquarium-task-v2.yaml"
    target.parent.mkdir(parents=True)
    cleaned = []

    class FakeRuntime:
        def __init__(self, *_args: object) -> None:
            self.sandbox = tmp_path
            self.correction_case_variants = {}
            self.delegation_receipt_count = int(guards_exercised)
            self.missing_receipt_guards = (
                {("record-plan", "attempt")} if guards_exercised else set()
            )
            self.stale_receipt_guards = (
                {("record-plan", "attempt")} if guards_exercised else set()
            )

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            cleaned.append(True)

        def drive_procedure(self, name: str) -> None:
            assert name == target.name
            assert target.read_bytes() == fixture.read_bytes()

    monkeypatch.setattr(runtime, "ManagedRuntime", FakeRuntime)
    job = {
        "kind": "historical-formal",
        "batch_id": "historical-formal-task-v30",
        "order": 1,
    }
    if guards_exercised:
        result = runtime.execute_runtime_job(
            tmp_path / "podway", procedures, job, threading.Event()
        )
        assert result["batch"]["synthetic_delegation_receipt_count"] == 1
        assert result["batch"]["cleanup"] == "passed"
    else:
        with pytest.raises(runtime.RuntimeQualificationError, match="receipt guards"):
            runtime.execute_runtime_job(
                tmp_path / "podway", procedures, job, threading.Event()
            )
    assert cleaned == [True]
