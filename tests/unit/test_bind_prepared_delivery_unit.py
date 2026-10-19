from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[2] / "plugins/aquarium/skills/goal-evaluator/scripts"
SCRIPT = SCRIPTS / "bind_prepared_delivery.py"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


binder = load("bind_prepared_delivery")
preparer = load("prepare_assignment")


@pytest.fixture
def inputs(tmp_path: Path) -> tuple[dict, dict]:
    root = tmp_path.resolve()
    (root / "role.md").write_bytes(b"\xef\xbb\xbfOperative role\r\nReport only")
    (root / "dependency.md").write_bytes(b"Required dependency\r\n")
    (root / "evidence.txt").write_bytes("Original evidence\u00e9\r\n".encode())
    prepared = preparer.prepare(
        root,
        {
            "schema": preparer.REQUEST_SCHEMA,
            "role": {"path": "role.md", "dependencies": ["dependency.md"]},
            "node": {
                "objective": "Return complete assessment",
                "purpose": "Verify exact candidate",
                "instructions": "Read complete original evidence",
                "canonical_sources": ["docs/roadmap/README.md#TASK-111"],
                "context": {
                    "work_identity": "TASK-111",
                    "goal_ref": "goal-1",
                    "goal_revision": "revision-1",
                    "target": "candidate-1",
                    "base": "base-1",
                    "procedure": "procedure-1",
                    "node": "node-1",
                },
                "selected_evidence": ["evidence.txt"],
                "permitted_effects": {
                    "allowed": ["Read original evidence"],
                    "excluded": ["Source mutation"],
                },
                "deliverables": ["Complete report"],
                "success_criteria": ["Complete criterion coverage"],
            },
        },
    )
    text = binder.renderer.render_dispatch(prepared)["dispatch_text"]
    common = {
        "sessionId": "session-1",
        "cliVersion": "0.162.0",
        "ephemeral": False,
        "historyMode": "paginated",
        "status": {"type": "idle"},
    }
    # Synthetic authentic-shape records establish behavior, never host qualification.
    mapping_request = {
        "schema": binder.native.REQUEST_SCHEMA,
        "profile": binder.native.CODEX_SPAWN_PROFILE,
        "expected": {
            "scope_ref": "session-1",
            "supervisor_ref": "primary-1",
            "worker_ref": "worker-1",
            "rounds": [
                {"dispatch_ref": "dispatch-1", "task_ref": "task-1", "input": text}
            ],
        },
        "records": {
            "journal": {
                "request": {
                    "task_name": "worker",
                    "fork_turns": "all",
                    "message": text,
                },
                "response": {"task_name": "/root/worker"},
            },
            "parent_read": {
                "thread": {
                    **common,
                    "id": "primary-1",
                    "status": {"type": "active", "activeFlags": []},
                    "turns": [
                        {
                            "id": "primary-turn",
                            "status": "inProgress",
                            "itemsView": "full",
                            "items": [
                                {
                                    "id": "dispatch-1",
                                    "type": "subAgentActivity",
                                    "kind": "started",
                                    "agentThreadId": "worker-1",
                                    "agentPath": "/root/worker",
                                    "model": "gpt-6.1-sol",
                                    "reasoningEffort": "high",
                                }
                            ],
                        }
                    ],
                }
            },
            "child_read": {
                "thread": {
                    **common,
                    "id": "worker-1",
                    "parentThreadId": "primary-1",
                    "source": {
                        "subAgent": {
                            "thread_spawn": {
                                "parent_thread_id": "primary-1",
                                "agent_path": "/root/worker",
                                "depth": 1,
                            }
                        }
                    },
                    "turns": [
                        {
                            "id": "task-1",
                            "status": "completed",
                            "itemsView": "full",
                            "error": None,
                            "items": [
                                {
                                    "id": "final-1",
                                    "type": "agentMessage",
                                    "phase": "final_answer",
                                    "text": "Complete assessment\r\n",
                                    "memoryCitation": {"entries": []},
                                }
                            ],
                        }
                    ],
                }
            },
        },
    }
    return prepared, mapping_request


def rehash(prepared: dict) -> None:
    prepared["local_prepared_role_snapshot_sha256"] = hashlib.sha256(
        preparer.canonical_bytes(prepared["prepared_role_snapshot"])
    ).hexdigest()
    prepared["local_prepared_assignment_sha256"] = hashlib.sha256(
        preparer.canonical_bytes(prepared["prepared_assignment"])
    ).hexdigest()


def align_dispatch(prepared: dict, mapping_request: dict) -> None:
    text = binder.renderer.render_dispatch(prepared)["dispatch_text"]
    mapping_request["expected"]["rounds"][0]["input"] = text
    mapping_request["records"]["journal"]["request"]["message"] = text


def assert_rejected(output: dict) -> None:
    assert output["state"] in ("rejected", "reconciliation_required")
    assert output["acceptance_ready"] is False
    assert output["redispatch_allowed"] is False
    assert "domains" not in output
    assert "bindings" not in output
    assert "native" not in output


def test_binds_complete_domains_with_stable_role_snapshot_and_distinct_digests(
    inputs,
) -> None:
    prepared, request = inputs
    original = copy.deepcopy(inputs)
    result = binder.bind_delivery(prepared, request)
    assert inputs == original
    assert result["state"] == "delivery_bound"
    assert result["schema"] == binder.OUTPUT_SCHEMA
    assert (
        result["domains"]["accepted_role_snapshot"]
        == prepared["prepared_role_snapshot"]
    )
    bindings = result["bindings"]
    assert (
        bindings["role_snapshot_digest"]
        == "sha256:" + prepared["local_prepared_role_snapshot_sha256"]
    )
    for field, domain in (
        ("role_snapshot_digest", "accepted_role_snapshot"),
        ("agent_configuration_digest", "agent_configuration"),
        ("accepted_task_digest", "accepted_task"),
        ("result_digest", "result"),
    ):
        assert bindings[field] == "sha256:" + binder.native.digest(
            result["domains"][domain]
        )
    assert len(set(bindings.values())) == 4
    assert (
        result["domains"]["accepted_task"]["input"]
        == request["records"]["journal"]["request"]
    )
    assert (
        result["domains"]["result"]["result"]
        == request["records"]["child_read"]["thread"]["turns"][0]["items"]
    )
    config = result["domains"]["agent_configuration"]
    assert set(config) == {
        "schema",
        "role_snapshot",
        "controls",
        "native_creation",
        "accepted_task_digest",
    }
    assert config["schema"] == binder.CONFIGURATION_SCHEMA
    assert config["role_snapshot"] == prepared["prepared_role_snapshot"]
    assert config["controls"] == {
        "fork_turns": "all",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "high",
    }
    assert config["native_creation"] == {
        "scope_ref": "session-1",
        "supervisor_ref": "primary-1",
        "worker_ref": "worker-1",
        "source_ref": "dispatch-1",
    }
    assert config["accepted_task_digest"] == bindings["accepted_task_digest"]
    assert result["record_authenticity"] == "caller_supplied_unverified"
    assert result["acceptance_ready"] is False
    assert result["redispatch_allowed"] is False
    assert set(result["unresolved_domains"]) == {
        "explicit_primary_acceptance",
        "complete_lifetime_round_accounting",
        "settlement_and_descendant_quiescence",
        "podway_package_and_context_binding",
        "durable_host_qualification",
    }
    prepared["prepared_role_snapshot"]["role_path"] = "later-caller-mutation"
    assert result["domains"]["accepted_role_snapshot"]["role_path"] == "role.md"


@pytest.mark.parametrize("path", ["role.md", "dependency.md"])
def test_role_and_dependency_changes_require_new_native_input_and_change_bound_configuration(
    inputs, path
) -> None:
    prepared, request = inputs
    before = binder.bind_delivery(prepared, request)
    file = next(
        file
        for file in prepared["prepared_role_snapshot"]["files"]
        if file["path"] == path
    )
    content = (
        base64.b64decode(file["content_base64"]) + b"\r\nChanged role instructions"
    )
    file.update(
        content_base64=base64.b64encode(content).decode(),
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )
    rehash(prepared)
    rejected = binder.bind_delivery(prepared, request)
    assert_rejected(rejected)
    assert rejected["error"]["code"] == "DISPATCH_INPUT_MISMATCH"
    align_dispatch(prepared, request)
    after = binder.bind_delivery(prepared, request)
    assert after["state"] == "delivery_bound"
    for field in before["bindings"]:
        assert before["bindings"][field] != after["bindings"][field]


def test_assignment_target_change_preserves_role_and_invalidates_old_native_input(
    inputs,
) -> None:
    prepared, request = inputs
    before = binder.bind_delivery(prepared, request)
    prepared["prepared_assignment"]["node"]["context"]["target"] = "new-candidate"
    rehash(prepared)
    assert_rejected(binder.bind_delivery(prepared, request))
    align_dispatch(prepared, request)
    after = binder.bind_delivery(prepared, request)
    assert (
        after["bindings"]["role_snapshot_digest"]
        == before["bindings"]["role_snapshot_digest"]
    )
    assert (
        after["bindings"]["accepted_task_digest"]
        != before["bindings"]["accepted_task_digest"]
    )
    assert (
        after["bindings"]["agent_configuration_digest"]
        != before["bindings"]["agent_configuration_digest"]
    )


@pytest.mark.parametrize(
    "field,value", [("model", "gpt-6-sol"), ("reasoningEffort", "medium")]
)
def test_resolved_native_control_changes_affect_configuration_without_relabeling_role(
    inputs, field, value
) -> None:
    prepared, request = inputs
    before = binder.bind_delivery(prepared, request)
    request["records"]["parent_read"]["thread"]["turns"][0]["items"][0][field] = value
    after = binder.bind_delivery(prepared, request)
    assert after["state"] == "delivery_bound"
    assert (
        after["bindings"]["role_snapshot_digest"]
        == before["bindings"]["role_snapshot_digest"]
    )
    assert (
        after["bindings"]["accepted_task_digest"]
        == before["bindings"]["accepted_task_digest"]
    )
    assert after["bindings"]["result_digest"] == before["bindings"]["result_digest"]
    assert (
        after["bindings"]["agent_configuration_digest"]
        != before["bindings"]["agent_configuration_digest"]
    )


def test_result_content_changes_preserve_configuration_and_task_domains(inputs) -> None:
    prepared, request = inputs
    before = binder.bind_delivery(prepared, request)
    request["records"]["child_read"]["thread"]["turns"][0]["items"][0]["text"] += (
        "\r\nFull additional result"
    )
    after = binder.bind_delivery(prepared, request)
    assert after["bindings"]["result_digest"] != before["bindings"]["result_digest"]
    for field in (
        "role_snapshot_digest",
        "agent_configuration_digest",
        "accepted_task_digest",
    ):
        assert after["bindings"][field] == before["bindings"][field]


@pytest.mark.parametrize("field", ["model", "reasoningEffort"])
@pytest.mark.parametrize("missing", [True, False])
def test_requires_both_actual_creation_controls(inputs, field, missing) -> None:
    prepared, request = inputs
    creation = request["records"]["parent_read"]["thread"]["turns"][0]["items"][0]
    if missing:
        del creation[field]
    else:
        creation[field] = None
    result = binder.bind_delivery(prepared, request)
    assert_rejected(result)
    assert result["error"]["code"] == "RESOLVED_CONTROLS_REQUIRED"


@pytest.mark.parametrize(
    "change",
    [
        "preparation_digest",
        "file_digest",
        "snapshot_alias",
        "native_message",
        "missing_ack",
        "wrong_worker",
        "wrong_session",
        "partial_result",
        "unqualified_followup",
        "supplied_mapping",
        "constructor_only",
    ],
)
def test_rejects_inconsistent_or_incomplete_binding_without_partial_success(
    inputs, change
) -> None:
    prepared, request = inputs
    if change == "preparation_digest":
        prepared["local_prepared_assignment_sha256"] = "0" * 64
    elif change == "file_digest":
        prepared["prepared_role_snapshot"]["files"][0]["sha256"] = "0" * 64
        rehash(prepared)
    elif change == "snapshot_alias":
        prepared["prepared_assignment"]["role_snapshot"] = copy.deepcopy(
            prepared["prepared_role_snapshot"]
        )
        prepared["prepared_assignment"]["role_snapshot"]["role_path"] = "dependency.md"
        rehash(prepared)
    elif change == "native_message":
        request["records"]["journal"]["request"]["message"] += "\nChanged task"
        request["expected"]["rounds"][0]["input"] = request["records"]["journal"][
            "request"
        ]["message"]
    elif change == "missing_ack":
        request["records"]["journal"]["response"] = None
    elif change == "wrong_worker":
        request["expected"]["worker_ref"] = "wrong-worker"
    elif change == "wrong_session":
        request["records"]["child_read"]["thread"]["sessionId"] = "wrong-session"
    elif change == "partial_result":
        request["records"]["child_read"]["thread"]["turns"][0]["itemsView"] = "summary"
    elif change == "unqualified_followup":
        activities = request["records"]["parent_read"]["thread"]["turns"][0]["items"]
        activity = copy.deepcopy(activities[0])
        activity.update(id="followup-1", kind="interacted")
        activities.append(activity)
    elif change == "supplied_mapping":
        request = binder.native.map_delivery(request)
    else:
        request["records"] = {"journal": request["records"]["journal"]}
    result = binder.bind_delivery(prepared, request)
    assert_rejected(result)
    assert result["request_digest"] == binder.native.digest(
        {
            "schema": binder.REQUEST_SCHEMA,
            "preparation": prepared,
            "mapping_request": request,
        }
    )
    if change == "missing_ack":
        assert result["state"] == "reconciliation_required"
        assert result["recovery_refs"]["rounds"][0]["dispatch_ref"] == "dispatch-1"
    assert "Operative role" not in json.dumps(result)
    assert "Complete assessment" not in json.dumps(result)


@pytest.mark.parametrize(
    "profile",
    [
        "unsupported/v1",
        "aquarium.codex-app-server-delivery/v1",
        "aquarium.claude-agent-sdk-delivery/v1",
    ],
)
def test_rejects_unqualified_profiles(inputs, profile) -> None:
    prepared, request = inputs
    request["profile"] = profile
    result = binder.bind_delivery(prepared, request)
    assert_rejected(result)
    assert result["error"]["code"] == "UNSUPPORTED_PROFILE"


def test_binding_reads_no_assignment_or_native_config_files(
    inputs, monkeypatch
) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("binder attempted source or configuration file access")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr("builtins.open", forbidden)
    assert binder.bind_delivery(*inputs)["state"] == "delivery_bound"


def cli(payload: bytes, input_path: Path | None = None) -> subprocess.CompletedProcess:
    if input_path is not None:
        input_path.write_bytes(payload)
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(input_path) if input_path is not None else "-",
        ],
        input=payload if input_path is None else None,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


@pytest.mark.parametrize("mode", ["stdin", "file"])
def test_cli_roundtrip(inputs, tmp_path, mode) -> None:
    prepared, request = inputs
    payload = binder.native.canonical_bytes(
        {
            "schema": binder.REQUEST_SCHEMA,
            "preparation": prepared,
            "mapping_request": request,
        }
    )
    result = cli(payload, tmp_path / "binding.json" if mode == "file" else None)
    assert result.returncode == 0
    assert result.stderr == b""
    assert json.loads(result.stdout) == binder.bind_delivery(prepared, request)


def test_cli_reconciliation_preserves_exit_status_and_bounded_recovery(inputs) -> None:
    prepared, request = inputs
    request["records"]["journal"]["response"] = None
    result = cli(
        binder.native.canonical_bytes(
            {
                "schema": binder.REQUEST_SCHEMA,
                "preparation": prepared,
                "mapping_request": request,
            }
        )
    )
    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert_rejected(output)
    assert output["state"] == "reconciliation_required"
    assert (
        request["records"]["journal"]["request"]["message"].encode()
        not in result.stdout
    )


@pytest.mark.parametrize(
    "payload",
    [
        b'{"schema":"first","schema":"second"}',
        b'{"number":NaN}',
        b'{"number":Infinity}',
        b'{"unfinished":',
        b"\xff",
    ],
)
def test_cli_rejects_invalid_json(payload) -> None:
    result = cli(payload)
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr.startswith(b"error:")


@pytest.mark.parametrize("change", ["schema", "missing", "extra_mapping"])
def test_cli_envelope_is_closed_and_versioned(inputs, change) -> None:
    prepared, request = inputs
    envelope = {
        "schema": binder.REQUEST_SCHEMA,
        "preparation": prepared,
        "mapping_request": request,
    }
    if change == "schema":
        envelope["schema"] = "unsupported/v2"
    elif change == "missing":
        del envelope["mapping_request"]
    else:
        envelope["mapping"] = binder.native.map_delivery(request)
    result = cli(binder.native.canonical_bytes(envelope))
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr.startswith(b"error:")


@pytest.fixture
def feedback_inputs(inputs):
    prepared, initial_request = inputs
    initial = copy.deepcopy(initial_request["records"])
    initial["preparation"] = copy.deepcopy(prepared)
    # Native initial delivery, retained before any new interaction.
    creation = initial["parent_read"]["thread"]["turns"][0]["items"][0]
    initial["parent_read"]["thread"]["turns"][0]["items"].append(
        {
            **creation,
            "id": "completed-1",
            "kind": "completed",
            "model": None,
            "reasoningEffort": None,
        }
    )
    final_preparation = copy.deepcopy(prepared)
    final_preparation["prepared_assignment"]["node"]["context"]["target"] = (
        "candidate-2"
    )
    final_preparation["prepared_assignment"]["node"]["instructions"] = (
        "Assess the new candidate against original evidence"
    )
    rehash(final_preparation)
    final_text = binder.renderer.render_dispatch(final_preparation)["dispatch_text"]
    after_parent = copy.deepcopy(initial["parent_read"])
    after_parent["thread"]["turns"][0]["items"].extend(
        [
            {
                **creation,
                "id": "dispatch-2",
                "kind": "interacted",
                "model": None,
                "reasoningEffort": None,
            },
            {
                **creation,
                "id": "native-completion-event",
                "kind": "completed",
                "model": None,
                "reasoningEffort": None,
            },
        ]
    )
    after_child = copy.deepcopy(initial["child_read"])
    turn = copy.deepcopy(after_child["thread"]["turns"][0])
    turn.update(
        id="task-2",
        items=[
            {
                **turn["items"][-1],
                "id": "final-2",
                "text": "Complete new candidate report",
            }
        ],
    )
    after_child["thread"]["turns"].append(turn)
    request = copy.deepcopy(initial_request)
    request["profile"] = binder.native.CODEX_ROUNDS_PROFILE
    request["expected"]["rounds"].append(
        {"dispatch_ref": "dispatch-2", "task_ref": "task-2", "input": final_text}
    )
    request["records"] = {
        "initial": initial,
        "feedback": [
            {
                "preparation": copy.deepcopy(final_preparation),
                "request": {"target": "/root/worker", "message": final_text},
                "feedback_completion_output_utf8": "",
                "before_parent_read": copy.deepcopy(initial["parent_read"]),
                "before_child_read": copy.deepcopy(initial["child_read"]),
                "after_parent_read": after_parent,
                "after_child_read": after_child,
            }
        ],
    }
    return final_preparation, request


def test_feedback_binding_verifies_changed_assignment_and_preserves_role_snapshot(
    feedback_inputs,
):
    prepared, request = feedback_inputs
    original = copy.deepcopy(feedback_inputs)
    output = binder.bind_delivery(prepared, request)
    assert output["state"] == "delivery_bound"
    assert feedback_inputs == original
    assert output["profile"] == binder.native.CODEX_ROUNDS_PROFILE
    assert (
        output["bindings"]["role_snapshot_digest"]
        == "sha256:" + prepared["local_prepared_role_snapshot_sha256"]
    )
    assert (
        output["domains"]["accepted_task"]["input"]
        == request["records"]["feedback"][0]["request"]
    )
    assert output["domains"]["result"]["result"][0]["id"] == "final-2"
    assert output["native"]["task_ref"] == "task-2"
    rounds = output["round_bindings"]
    assert len(rounds) == 2
    assert (
        rounds[0]["local_prepared_assignment_sha256"]
        != rounds[1]["local_prepared_assignment_sha256"]
    )
    assert (
        rounds[1]["accepted_task_digest"] == output["bindings"]["accepted_task_digest"]
    )
    assert rounds[1]["result_digest"] == output["bindings"]["result_digest"]
    assert output["domains"]["agent_configuration"]["controls"]["fork_turns"] == "all"
    assert (
        output["domains"]["agent_configuration"]["native_creation"]["source_ref"]
        == "dispatch-1"
    )
    for entry in rounds:
        assert entry["accepted_task_digest"] == "sha256:" + binder.native.digest(
            entry["accepted_task_domain"]
        )
        assert entry["result_digest"] == "sha256:" + binder.native.digest(
            entry["result_domain"]
        )
    assert output["acceptance_ready"] is False and output["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "change",
    [
        "role",
        "dependency",
        "initial_preparation",
        "feedback_preparation",
        "current_preparation",
        "missing_initial_preparation",
        "missing_feedback_preparation",
        "missing_ack",
        "wrong_identity",
        "missing_control",
        "wrong_target",
    ],
)
def test_feedback_binding_requires_exact_preparations_role_continuity_and_native_ack(
    feedback_inputs, change
):
    prepared, request = feedback_inputs
    initial = request["records"]["initial"]
    feedback = request["records"]["feedback"][0]
    if change in ("role", "dependency"):
        original_prep = initial["preparation"]
        path = "role.md" if change == "role" else "dependency.md"
        file = next(
            file
            for file in original_prep["prepared_role_snapshot"]["files"]
            if file["path"] == path
        )
        content = (
            base64.b64decode(file["content_base64"])
            + b" altered operative instructions"
        )
        file.update(
            content_base64=base64.b64encode(content).decode(),
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )
        rehash(original_prep)
        text = binder.renderer.render_dispatch(original_prep)["dispatch_text"]
        initial["journal"]["request"]["message"] = text
        request["expected"]["rounds"][0]["input"] = text
    elif change == "initial_preparation":
        initial["preparation"]["local_prepared_assignment_sha256"] = "0" * 64
    elif change == "feedback_preparation":
        feedback["preparation"]["local_prepared_assignment_sha256"] = "0" * 64
    elif change == "current_preparation":
        prepared["prepared_assignment"]["node"]["context"]["target"] = (
            "unacknowledged-new-candidate"
        )
        rehash(prepared)
    elif change == "missing_initial_preparation":
        del initial["preparation"]
    elif change == "missing_feedback_preparation":
        del feedback["preparation"]
    elif change == "missing_ack":
        del feedback["feedback_completion_output_utf8"]
    elif change == "wrong_identity":
        feedback["after_child_read"]["thread"]["id"] = "wrong"
    elif change == "missing_control":
        for snapshot in (
            initial["parent_read"],
            feedback["before_parent_read"],
            feedback["after_parent_read"],
        ):
            snapshot["thread"]["turns"][0]["items"][0]["reasoningEffort"] = None
    elif change == "wrong_target":
        feedback["request"]["target"] = "worker-1"
    output = binder.bind_delivery(prepared, request)
    assert_rejected(output)
    assert "round_bindings" not in output
    if change in ("role", "dependency"):
        assert output["error"]["code"] == "ROLE_SNAPSHOT_MISMATCH"
    if change == "missing_ack":
        assert output["state"] == "reconciliation_required"
        assert len(output["recovery_refs"]["rounds"]) == 2
    if change == "missing_control":
        assert output["error"]["code"] == "RESOLVED_CONTROLS_REQUIRED"


def test_feedback_control_changes_affect_configuration_and_final_result_changes_preserve_task(
    feedback_inputs,
):
    prepared, request = feedback_inputs
    before = binder.bind_delivery(prepared, request)
    for snapshot in (
        request["records"]["initial"]["parent_read"],
        request["records"]["feedback"][0]["before_parent_read"],
        request["records"]["feedback"][0]["after_parent_read"],
    ):
        snapshot["thread"]["turns"][0]["items"][0]["model"] = "gpt-6-sol"
    after = binder.bind_delivery(prepared, request)
    assert after["state"] == "delivery_bound"
    assert (
        before["bindings"]["role_snapshot_digest"]
        == after["bindings"]["role_snapshot_digest"]
    )
    assert (
        before["bindings"]["agent_configuration_digest"]
        != after["bindings"]["agent_configuration_digest"]
    )
    assert (
        before["bindings"]["accepted_task_digest"]
        == after["bindings"]["accepted_task_digest"]
    )
    feedback = request["records"]["feedback"][0]
    feedback["after_child_read"]["thread"]["turns"][-1]["items"][-1]["text"] += (
        "\nAdditional complete result"
    )
    changed = binder.bind_delivery(prepared, request)
    assert changed["state"] == "delivery_bound"
    assert (
        changed["bindings"]["accepted_task_digest"]
        == after["bindings"]["accepted_task_digest"]
    )
    assert (
        changed["bindings"]["agent_configuration_digest"]
        == after["bindings"]["agent_configuration_digest"]
    )
    assert changed["bindings"]["result_digest"] != after["bindings"]["result_digest"]


def test_feedback_binding_cli_roundtrip(feedback_inputs):
    prepared, request = feedback_inputs
    payload = {
        "schema": binder.REQUEST_SCHEMA,
        "preparation": prepared,
        "mapping_request": request,
    }
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", "-"],
        input=binder.native.canonical_bytes(payload),
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()
    assert json.loads(result.stdout) == binder.bind_delivery(prepared, request)


@pytest.mark.parametrize(
    "snapshot",
    [
        "before_parent_read",
        "after_parent_read",
        "before_child_read",
        "after_child_read",
    ],
)
@pytest.mark.parametrize("status", [None, "idle", [], {}])
def test_feedback_binding_rejects_malformed_status_with_recovery_refs(
    feedback_inputs, snapshot, status
):
    prepared, request = feedback_inputs
    request["records"]["feedback"][0][snapshot]["thread"]["status"] = status
    output = binder.bind_delivery(prepared, request)
    assert output["state"] == "rejected"
    assert output["error"]["code"] == "REQUIRED_METADATA_MISSING"
    assert output["acceptance_ready"] is False
    assert output["redispatch_allowed"] is False
    assert output["recovery_refs"]["worker_ref"] == "worker-1"
    payload = {
        "schema": binder.REQUEST_SCHEMA,
        "preparation": prepared,
        "mapping_request": request,
    }
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", "-"],
        input=binder.native.canonical_bytes(payload),
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert not result.stderr
    assert json.loads(result.stdout) == output


def test_codex_v2_binding_retains_every_preparation_and_actual_alias(feedback_inputs):
    prepared, request = feedback_inputs
    request["profile"] = binder.native.CODEX_ROUNDS_V2_PROFILE
    request["records"]["initial"]["child_read"]["thread"]["cliVersion"] = "0.162.1"
    path = request["records"]["initial"]["journal"]["response"]["task_name"]
    for record in request["records"]["feedback"]:
        for key in ("before_child_read", "after_child_read"):
            record[key]["thread"]["cliVersion"] = "0.162.1"
        record["request"]["target"] = path.rsplit("/", 1)[-1]
    original = copy.deepcopy((prepared, request))
    output = binder.bind_delivery(prepared, request)
    assert output["state"] == "delivery_bound"
    assert (prepared, request) == original
    assert len(output["round_bindings"]) == len(request["expected"]["rounds"])
    assert output["acceptance_ready"] is False and output["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "profile",
    [binder.native.CODEX_ROUNDS_PROFILE, binder.native.CODEX_ROUNDS_V2_PROFILE],
)
@pytest.mark.parametrize("round_kind", ["initial", "feedback"])
def test_ordinary_nested_round_is_rejected_before_formal_binding(
    feedback_inputs, profile: str, round_kind: str
) -> None:
    prepared, request = feedback_inputs
    request["profile"] = profile
    if profile == binder.native.CODEX_ROUNDS_V2_PROFILE:
        request["records"]["initial"]["child_read"]["thread"]["cliVersion"] = "0.162.1"
        path = request["records"]["initial"]["journal"]["response"]["task_name"]
        for record in request["records"]["feedback"]:
            for key in ("before_child_read", "after_child_read"):
                record[key]["thread"]["cliVersion"] = "0.162.1"
            record["request"]["target"] = path.rsplit("/", 1)[-1]
    assert binder.bind_delivery(prepared, request)["state"] == "delivery_bound"
    ordinary = {
        "schema": "aquarium.assignment/v2",
        "work": {"id": "TASK-127"},
        "target": {"basis": "candidate"},
        "authority": {"allowed": ["Read evidence"], "excluded": ["Mutation"]},
        "procedure": None,
        "native": {"harness": "codex", "model": None},
        "evidence": [],
        "gaps": [],
        "role": "judge",
        "purpose": "Assess original criteria",
        "instructions": "Report only",
        "checkpoint": "verification",
        "deliverables": ["Assessment"],
        "success_criteria": ["Preserve original gaps"],
    }
    assert (
        binder.renderer.render_dispatch(ordinary)["schema"]
        == "aquarium.prepared-dispatch/v2"
    )
    record = (
        request["records"]["initial"]
        if round_kind == "initial"
        else request["records"]["feedback"][0]
    )
    record["preparation"] = ordinary
    result = binder.bind_delivery(prepared, request)
    assert result["state"] == "rejected"
    assert result["error"]["code"] == "INVALID_PREPARATION"
    assert result["acceptance_ready"] is False
    response = cli(
        binder.native.canonical_bytes(
            {
                "schema": binder.REQUEST_SCHEMA,
                "preparation": prepared,
                "mapping_request": request,
            }
        )
    )
    assert response.returncode == 2
    assert response.stderr == b""
    assert json.loads(response.stdout) == result
