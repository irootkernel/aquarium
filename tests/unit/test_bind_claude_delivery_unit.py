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

SCRIPTS = Path(__file__).parents[2] / "plugins/aquarium/skills/goal-judge/scripts"
SCRIPT = SCRIPTS / "bind_claude_delivery.py"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


binder = load("bind_claude_delivery")
preparer = load("prepare_assignment")


@pytest.fixture
def inputs(tmp_path):
    root = tmp_path.resolve()
    (root / "role.md").write_bytes(
        b"\xef\xbb\xbfComplete operative role\r\nNo final newline"
    )
    (root / "dependency.md").write_bytes(b"Complete dependency\r\n")
    (root / "evidence.txt").write_bytes("Exact evidence\u00e9\r\n".encode())
    prepared = preparer.prepare(
        root,
        {
            "schema": preparer.REQUEST_SCHEMA,
            "role": {"path": "role.md", "dependencies": ["dependency.md"]},
            "node": {
                "objective": "Review exact evidence",
                "purpose": "Assess complete criteria",
                "instructions": "Use complete immutable evidence",
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
                    "allowed": ["Read evidence"],
                    "excluded": ["Source mutation"],
                },
                "deliverables": ["Complete report"],
                "success_criteria": ["Complete coverage"],
            },
        },
    )
    text = binder.renderer.render_dispatch(prepared)["dispatch_text"]
    # Authentic public SDK shapes with synthetic values: no actual host qualification.
    request = {
        "schema": binder.native.REQUEST_SCHEMA,
        "profile": binder.native.CLAUDE_PROFILE,
        "expected": {
            "scope_ref": "session-1",
            "supervisor_ref": "session-1",
            "worker_ref": "agent-1",
            "rounds": [{"dispatch_ref": "tool-1", "task_ref": "tool-1", "input": text}],
        },
        "records": {
            "invocation": {
                "type": "assistant",
                "uuid": "invocation-1",
                "session_id": "session-1",
                "parent_tool_use_id": None,
                "message": {
                    "id": "message-1",
                    "role": "assistant",
                    "stop_reason": "tool_use",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "tool-1",
                            "name": "Agent",
                            "input": {
                                "description": "Complete review",
                                "prompt": text,
                                "subagent_type": "general-purpose",
                                "run_in_background": False,
                            },
                        }
                    ],
                },
            },
            "delivery": {
                "type": "user",
                "uuid": "delivery-1",
                "session_id": "session-1",
                "parent_tool_use_id": None,
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tool-1",
                            "content": "Model-visible summary is not full structured result",
                        }
                    ],
                },
                "tool_use_result": {
                    "agentId": "agent-1",
                    "agentType": "general-purpose",
                    "prompt": text,
                    "status": "completed",
                    "resolvedModel": "claude-sonnet-4-6",
                    "modelsUsed": ["claude-sonnet-4-6"],
                    "content": [
                        {
                            "type": "text",
                            "text": "Complete result\r\n",
                            "citations": ["original-1"],
                        },
                        {
                            "type": "text",
                            "text": "Second complete result part",
                            "citations": None,
                        },
                    ],
                    "totalToolUseCount": 1,
                    "totalDurationMs": 12.5,
                    "totalTokens": 100,
                    "usage": {
                        "input_tokens": 75,
                        "output_tokens": 25,
                        "cache_creation_input_tokens": None,
                        "cache_read_input_tokens": None,
                        "server_tool_use": None,
                        "service_tier": None,
                        "cache_creation": None,
                        "inference_geo": None,
                    },
                    "toolStats": {
                        "readCount": 1,
                        "searchCount": 0,
                        "bashCount": 0,
                        "editFileCount": 0,
                        "linesAdded": 0,
                        "linesRemoved": 0,
                        "otherToolCount": 0,
                    },
                },
            },
        },
    }
    return prepared, request


def arguments(request):
    return request["records"]["invocation"]["message"]["content"][0]["input"]


def result(request):
    return request["records"]["delivery"]["tool_use_result"]


def rehash(prepared):
    prepared["local_prepared_role_snapshot_sha256"] = binder.native.digest(
        prepared["prepared_role_snapshot"]
    )
    prepared["local_prepared_assignment_sha256"] = binder.native.digest(
        prepared["prepared_assignment"]
    )


def align(prepared, request):
    text = binder.renderer.render_dispatch(prepared)["dispatch_text"]
    arguments(request)["prompt"] = result(request)["prompt"] = request["expected"][
        "rounds"
    ][0]["input"] = text


def cli(payload, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--input", "-", *args],
        input=payload,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def assert_rejected(output):
    assert output["state"] in ("rejected", "reconciliation_required")
    assert output["acceptance_ready"] is False and output["redispatch_allowed"] is False
    assert (
        "domains" not in output and "bindings" not in output and "native" not in output
    )


def test_complete_claude_binding_preserves_exact_role_domains_output_and_sources(
    inputs,
):
    prepared, request = inputs
    original = copy.deepcopy(inputs)
    output = binder.bind_delivery(prepared, request)
    assert inputs == original
    assert output["state"] == "delivery_bound"
    assert output["schema"] == binder.OUTPUT_SCHEMA
    assert output["record_authenticity"] == "caller_supplied_unverified"
    assert output["acceptance_ready"] is False and output["redispatch_allowed"] is False
    assert (
        output["bindings"]["role_snapshot_digest"]
        == "sha256:" + prepared["local_prepared_role_snapshot_sha256"]
    )
    for key, field in [
        ("accepted_role_snapshot", "role_snapshot_digest"),
        ("agent_configuration", "agent_configuration_digest"),
        ("accepted_task", "accepted_task_digest"),
        ("result", "result_digest"),
    ]:
        assert output["bindings"][field] == "sha256:" + binder.native.digest(
            output["domains"][key]
        )
    assert (
        output["domains"]["accepted_role_snapshot"]
        == prepared["prepared_role_snapshot"]
    )
    assert output["domains"]["result"]["result"] == result(request)
    config = output["domains"]["agent_configuration"]
    assert set(config) == {
        "schema",
        "role_snapshot",
        "accepted_agent_controls",
        "ignored_agent_input",
        "acknowledged_agent_input",
        "native_resolution",
        "accepted_task_digest",
    }
    assert config["acknowledged_agent_input"] == arguments(request)
    assert config["native_resolution"] == {
        "agentId": "agent-1",
        "delivery_uuid": "delivery-1",
        "tool_use_id": "tool-1",
        "resolvedModel": "claude-sonnet-4-6",
        "modelsUsed": ["claude-sonnet-4-6"],
    }
    assert "effort" not in config["accepted_agent_controls"]
    assert output["native"]["result_refs"] == ["delivery-1"]
    result(request)["content"][0]["text"] = "Later caller mutation"
    assert (
        output["domains"]["result"]["result"]["content"][0]["text"]
        == "Complete result\r\n"
    )


@pytest.mark.parametrize("path", ["role.md", "dependency.md", "evidence.txt"])
def test_changed_role_dependency_or_evidence_requires_exact_new_native_ack(
    inputs, path
):
    prepared, request = inputs
    before = binder.bind_delivery(prepared, request)
    files = (
        prepared["prepared_role_snapshot"]["files"]
        if path != "evidence.txt"
        else prepared["prepared_assignment"]["node"]["selected_evidence"]
    )
    file = next(file for file in files if file["path"] == path)
    content = base64.b64decode(file["content_base64"]) + b"\r\nChanged exact bytes"
    file.update(
        content_base64=base64.b64encode(content).decode(),
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )
    rehash(prepared)
    assert_rejected(binder.bind_delivery(prepared, request))
    align(prepared, request)
    after = binder.bind_delivery(prepared, request)
    assert after["state"] == "delivery_bound"
    assert (
        before["bindings"]["accepted_task_digest"]
        != after["bindings"]["accepted_task_digest"]
    )
    assert (
        before["bindings"]["role_snapshot_digest"]
        == after["bindings"]["role_snapshot_digest"]
    ) == (path == "evidence.txt")


@pytest.mark.parametrize("model", ["sonnet", "opus", "haiku", "fable"])
def test_documented_model_selector_is_distinct_from_native_resolved_model(
    inputs, model
):
    prepared, request = inputs
    arguments(request)["model"] = model
    arguments(request)["effort"] = "high"
    output = binder.bind_delivery(prepared, request)
    assert output["state"] == "delivery_bound"
    config = output["domains"]["agent_configuration"]
    assert config["accepted_agent_controls"]["model"] == model
    assert config["native_resolution"]["resolvedModel"] == "claude-sonnet-4-6"
    assert config["accepted_agent_controls"]["effort"] == "high"


@pytest.mark.parametrize(
    "change",
    [
        "missing_model",
        "empty_model",
        "wrong_model_type",
        "invalid_selector",
        "invalid_effort",
        "agent_alias",
        "fork",
        "definition_mismatch",
        "background_default",
        "background_true",
        "worktree",
        "remote",
        "worktree_output",
        "unknown_control",
        "bad_models_used",
        "bad_model_member",
        "bad_background_type",
        "bad_description",
        "bad_name",
    ],
)
def test_missing_or_unqualified_native_configuration_never_yields_partial_binding(
    inputs, change
):
    prepared, request = inputs
    args, out = arguments(request), result(request)
    if change == "missing_model":
        del out["resolvedModel"]
    elif change == "empty_model":
        out["resolvedModel"] = " "
    elif change == "wrong_model_type":
        out["resolvedModel"] = ["claude-sonnet-4-6"]
    elif change == "invalid_selector":
        args["model"] = "claude-sonnet-4-6"
    elif change == "invalid_effort":
        args["effort"] = "ultra"
    elif change == "agent_alias":
        args["subagent_type"] = "inherit"
    elif change == "fork":
        args.update(subagent_type="fork", model="opus")
    elif change == "definition_mismatch":
        out["agentType"] = "custom-reviewer"
    elif change == "background_default":
        del args["run_in_background"]
    elif change == "background_true":
        args["run_in_background"] = True
    elif change == "worktree":
        args["isolation"] = "worktree"
    elif change == "remote":
        args["isolation"] = "remote"
    elif change == "worktree_output":
        out["worktreePath"] = "/unverified-checkout"
    elif change == "unknown_control":
        args["resume"] = "agent-0"
    elif change == "bad_models_used":
        out["modelsUsed"] = None
    elif change == "bad_model_member":
        out["modelsUsed"] = ["claude-sonnet-4-6", 1]
    elif change == "bad_background_type":
        args["run_in_background"] = 0
    elif change == "bad_description":
        del args["description"]
    elif change == "bad_name":
        args["name"] = None
    output = binder.bind_delivery(prepared, request)
    assert_rejected(output)
    if change in (
        "missing_model",
        "empty_model",
        "wrong_model_type",
        "agent_alias",
        "fork",
        "definition_mismatch",
        "background_default",
        "background_true",
        "worktree",
        "remote",
        "worktree_output",
        "unknown_control",
    ):
        assert output["state"] == "reconciliation_required"
    assert "prompt" not in json.dumps(output)


def test_ignored_deprecated_inputs_remain_distinct_from_effective_controls(inputs):
    prepared, request = inputs
    arguments(request).update(
        mode="bypassPermissions", team_name="ignored-team", name="worker-label"
    )
    output = binder.bind_delivery(prepared, request)
    assert output["state"] == "delivery_bound"
    config = output["domains"]["agent_configuration"]
    assert config["ignored_agent_input"] == {
        "mode": "bypassPermissions",
        "team_name": "ignored-team",
    }
    assert not {"mode", "team_name"} & set(config["accepted_agent_controls"])
    assert config["accepted_agent_controls"]["name"] == "worker-label"


def test_optional_native_models_used_and_type_are_not_mandatory(inputs):
    prepared, request = inputs
    del result(request)["modelsUsed"]
    del result(request)["agentType"]
    del arguments(request)["subagent_type"]
    output = binder.bind_delivery(prepared, request)
    assert output["state"] == "delivery_bound"
    assert (
        "modelsUsed"
        not in output["domains"]["agent_configuration"]["native_resolution"]
    )


def test_native_model_changes_configuration_and_complete_extensions_change_only_result(
    inputs,
):
    prepared, request = inputs
    before = binder.bind_delivery(prepared, request)
    result(request)["resolvedModel"] = "claude-opus-4-6"
    result(request)["modelsUsed"] = ["claude-sonnet-4-6", "claude-opus-4-6"]
    after = binder.bind_delivery(prepared, request)
    assert after["state"] == "delivery_bound"
    assert (
        before["bindings"]["agent_configuration_digest"]
        != after["bindings"]["agent_configuration_digest"]
    )
    assert (
        before["bindings"]["role_snapshot_digest"]
        == after["bindings"]["role_snapshot_digest"]
    )
    assert (
        before["bindings"]["accepted_task_digest"]
        == after["bindings"]["accepted_task_digest"]
    )
    result(request)["usage"]["iterations"] = {"native_extension": [1, 2]}
    result(request)["content"][1]["citations"] = ["extra-original-evidence"]
    extended = binder.bind_delivery(prepared, request)
    assert extended["domains"]["result"]["result"] == result(request)
    assert extended["bindings"]["result_digest"] != after["bindings"]["result_digest"]
    assert (
        extended["bindings"]["agent_configuration_digest"]
        == after["bindings"]["agent_configuration_digest"]
    )


@pytest.mark.parametrize(
    "change",
    [
        "wrong_profile",
        "altered_prep",
        "altered_prompt",
        "missing_ack",
        "wrong_result_id",
        "wrong_worker",
        "wrong_scope",
        "count_float",
        "negative_duration",
    ],
)
def test_native_identity_acknowledgement_and_verified_preparation_are_required(
    inputs, change
):
    prepared, request = inputs
    if change == "wrong_profile":
        request["profile"] = binder.native.CODEX_SPAWN_PROFILE
    elif change == "altered_prep":
        prepared["local_prepared_assignment_sha256"] = "0" * 64
    elif change == "altered_prompt":
        arguments(request)["prompt"] = result(request)["prompt"] = request["expected"][
            "rounds"
        ][0]["input"] = "Unacknowledged preparation"
    elif change == "missing_ack":
        del request["records"]["delivery"]["tool_use_result"]
    elif change == "wrong_result_id":
        request["records"]["delivery"]["message"]["content"][0]["tool_use_id"] = (
            "wrong-tool"
        )
    elif change == "wrong_worker":
        result(request)["agentId"] = "wrong-agent"
    elif change == "wrong_scope":
        request["records"]["delivery"]["session_id"] = "wrong-session"
    elif change == "count_float":
        result(request)["totalTokens"] = 100.5
    elif change == "negative_duration":
        result(request)["totalDurationMs"] = -0.5
    assert_rejected(binder.bind_delivery(prepared, request))


@pytest.mark.parametrize("mode", ["stdin", "file"])
def test_cli_roundtrip(inputs, tmp_path, mode):
    prepared, request = inputs
    envelope = {
        "schema": binder.REQUEST_SCHEMA,
        "preparation": prepared,
        "mapping_request": request,
    }
    payload = binder.native.canonical_bytes(envelope)
    if mode == "stdin":
        response = cli(payload)
    else:
        path = tmp_path / "request.json"
        path.write_bytes(payload)
        response = subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(path)],
            capture_output=True,
            check=False,
        )
    assert response.returncode == 0, response.stderr.decode()
    assert json.loads(response.stdout) == binder.bind_delivery(prepared, request)


def test_cli_reconciliation_preserves_error_and_recovery_refs(inputs):
    prepared, request = inputs
    del result(request)["resolvedModel"]
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
    output = json.loads(response.stdout)
    assert output["state"] == "reconciliation_required"
    assert output["recovery_refs"]["worker_ref"] == "agent-1"
    assert output["error"]["code"] == "RESOLVED_MODEL_REQUIRED"


@pytest.mark.parametrize(
    "payload", [b'{"schema":1,"schema":2}', b'{"x":NaN}', b"[]", b"{}", b"not json"]
)
def test_cli_rejects_invalid_or_unversioned_envelope(payload):
    assert cli(payload).returncode == 2


def test_cli_rejects_self_asserted_acceptance_envelope(inputs):
    prepared, request = inputs
    response = cli(
        binder.native.canonical_bytes(
            {
                "schema": binder.REQUEST_SCHEMA,
                "preparation": prepared,
                "mapping_request": request,
                "accepted": True,
            }
        )
    )
    assert response.returncode == 2


@pytest.fixture
def feedback_inputs(inputs):
    prepared, initial_request = inputs
    feedback_prepared = copy.deepcopy(prepared)
    feedback_prepared["prepared_assignment"]["node"]["instructions"] = (
        "Reassess the new candidate using unchanged role and original complete evidence"
    )
    feedback_prepared["prepared_assignment"]["node"]["context"]["target"] = (
        "candidate-2"
    )
    rehash(feedback_prepared)
    text = binder.renderer.render_dispatch(feedback_prepared)["dispatch_text"]
    initial = copy.deepcopy(initial_request["records"])
    invocation = copy.deepcopy(initial["invocation"])
    invocation["uuid"] = "feedback-invocation"
    invocation["message"]["content"] = [
        {
            "type": "tool_use",
            "id": "send-1",
            "name": "SendMessage",
            "input": {
                "to": "agent-1",
                "message": text,
                "summary": "Reassess new candidate",
            },
        }
    ]
    delivery = copy.deepcopy(initial["delivery"])
    delivery["uuid"] = "feedback-delivery"
    delivery["message"]["content"] = [
        {
            "type": "tool_result",
            "tool_use_id": "send-1",
            "content": "Resumed original agent",
        }
    ]
    delivery["tool_use_result"] = {
        "success": True,
        "resumedAgentId": "agent-1",
        "pin": {"ref": "opaque-native-pin"},
    }

    def child(kind, uuid, body):
        return {
            "type": kind,
            "uuid": uuid,
            "session_id": "session-1",
            "parent_tool_use_id": "tool-1",
            "parent_agent_id": None,
            "message": {"role": kind, **body},
        }

    public = [
        child(
            "user", "initial-user", {"content": arguments(initial_request)["prompt"]}
        ),
        child(
            "assistant",
            "initial-final",
            {
                "id": "initial-message",
                "model": "claude-sonnet-4-6",
                "stop_reason": "end_turn",
                "content": copy.deepcopy(result(initial_request)["content"]),
            },
        ),
        child(
            "user",
            "feedback-user",
            {"content": "Opaque complete native coordinator wrapper"},
        ),
        child(
            "assistant",
            "feedback-final",
            {
                "id": "feedback-message",
                "model": "native-feedback-model",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "New candidate complete report"}],
            },
        ),
    ]
    forwarded = copy.deepcopy(public[-1])
    forwarded["message"]["stop_reason"] = None
    forwarded["agent_id"] = "agent-1"

    def event(kind, uuid, **data):
        return {
            "type": "system",
            "subtype": kind,
            "uuid": uuid,
            "session_id": "session-1",
            **data,
        }

    run = {"task_id": "agent-1", "run_id": "run-1"}
    events = [
        event("background_tasks_changed", "active", tasks=[run]),
        event(
            "task_started",
            "started",
            **run,
            tool_use_id="send-1",
            prompt=text,
            is_backgrounded=True,
            spawn_depth=1,
            task_type="local_agent",
            subagent_type="general-purpose",
        ),
        event("task_updated", "updated", **run, patch={"status": "completed"}),
        event(
            "task_notification",
            "notification",
            **run,
            tool_use_id="send-1",
            status="completed",
            output_file="/owned-native-output",
            summary="Not the complete result",
            usage={"tool_uses": 0},
        ),
        event("background_tasks_changed", "finished", tasks=[]),
    ]
    request = copy.deepcopy(initial_request)
    request["profile"] = binder.native.CLAUDE_ROUNDS_PROFILE
    request["expected"]["rounds"].append(
        {"dispatch_ref": "send-1", "task_ref": "run-1", "input": text}
    )
    request["records"] = {
        "initial": initial,
        "feedback": [
            {
                "invocation": invocation,
                "delivery": delivery,
                "events": events,
                "forwarded_result": forwarded,
                "public_history": {
                    "sdk_version": "0.3.295",
                    "session_id": "session-1",
                    "agent_id": "agent-1",
                    "agents": ["agent-1"],
                    "child": public,
                },
            }
        ],
    }
    return [copy.deepcopy(prepared), feedback_prepared], request


def test_serialized_claude_binding_verifies_both_preparations_and_final_public_result(
    feedback_inputs,
):
    preparations, request = feedback_inputs
    original = copy.deepcopy(feedback_inputs)
    output = binder.bind_delivery(preparations, request)
    assert output["state"] == "delivery_bound", output
    assert feedback_inputs == original
    assert output["profile"] == binder.native.CLAUDE_ROUNDS_PROFILE
    assert len(output["round_bindings"]) == 2
    assert (
        output["round_bindings"][0]["result_domain"]["result"]
        == request["records"]["initial"]["delivery"]["tool_use_result"]
    )
    assert output["round_bindings"][1]["result_domain"] == output["domains"]["result"]
    assert (
        output["domains"]["result"]["result"]["schema"]
        == "aquarium.claude-feedback-result/v1"
    )
    assert output["native"]["dispatch_ref"] == "send-1"
    assert output["native"]["task_ref"] == "run-1"
    assert output["native"]["delivery_ref"] == "feedback-final"
    assert output["native"]["feedback_run"]["model"] == "native-feedback-model"
    config = output["domains"]["agent_configuration"]
    assert config["accepted_agent_controls"]["run_in_background"] is False
    assert config["native_resolution"]["tool_use_id"] == "tool-1"
    assert config["native_resolution"]["resolvedModel"] == "claude-sonnet-4-6"
    assert (
        output["bindings"]["role_snapshot_digest"]
        == "sha256:" + preparations[0]["local_prepared_role_snapshot_sha256"]
    )
    for entry in output["round_bindings"]:
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
        "missing_preparation",
        "extra_preparation",
        "single_preparation",
        "bad_initial_digest",
        "bad_feedback_digest",
        "changed_initial_assignment",
        "changed_feedback_assignment",
        "changed_role",
        "changed_dependency",
        "missing_forwarded_result",
        "missing_notification",
        "missing_resolved_model",
    ],
)
def test_serialized_claude_binding_rejects_missing_ack_or_changed_role_or_assignment(
    feedback_inputs, change
):
    preparations, request = feedback_inputs
    if change == "missing_preparation":
        preparations.pop()
    elif change == "extra_preparation":
        preparations.append(copy.deepcopy(preparations[-1]))
    elif change == "single_preparation":
        preparations = preparations[-1]
    elif change == "bad_initial_digest":
        preparations[0]["local_prepared_assignment_sha256"] = "0" * 64
    elif change == "bad_feedback_digest":
        preparations[-1]["local_prepared_assignment_sha256"] = "0" * 64
    elif change in ("changed_initial_assignment", "changed_feedback_assignment"):
        prep = (
            preparations[0]
            if change == "changed_initial_assignment"
            else preparations[-1]
        )
        prep["prepared_assignment"]["node"]["context"]["target"] = (
            "unacknowledged-target"
        )
        rehash(prep)
    elif change in ("changed_role", "changed_dependency"):
        path = "role.md" if change == "changed_role" else "dependency.md"
        prep = preparations[-1]
        file = next(
            file
            for file in prep["prepared_role_snapshot"]["files"]
            if file["path"] == path
        )
        content = base64.b64decode(file["content_base64"]) + b" changed operative bytes"
        file.update(
            content_base64=base64.b64encode(content).decode(),
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )
        rehash(prep)
    elif change == "missing_forwarded_result":
        del request["records"]["feedback"][0]["forwarded_result"]
    elif change == "missing_notification":
        request["records"]["feedback"][0]["events"].pop(3)
    elif change == "missing_resolved_model":
        del request["records"]["initial"]["delivery"]["tool_use_result"][
            "resolvedModel"
        ]
    output = binder.bind_delivery(preparations, request)
    assert_rejected(output)
    assert "round_bindings" not in output


def test_serialized_claude_cli_preserves_preparation_list_api(feedback_inputs):
    preparations, request = feedback_inputs
    response = cli(
        binder.native.canonical_bytes(
            {
                "schema": binder.REQUEST_SCHEMA,
                "preparation": preparations,
                "mapping_request": request,
            }
        )
    )
    assert response.returncode == 0, response.stderr.decode()
    assert json.loads(response.stdout) == binder.bind_delivery(preparations, request)
