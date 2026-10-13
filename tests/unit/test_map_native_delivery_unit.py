from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/goal-judge/scripts/map_native_delivery.py"
)
SPEC = importlib.util.spec_from_file_location("map_native_delivery", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mapping = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mapping)


def thread(identifier: str, turns: list, *, child=False) -> dict:
    return {
        "id": identifier,
        "sessionId": "session-1",
        "cliVersion": "0.162.0",
        "createdAt": 1,
        "updatedAt": 2,
        "cwd": "/disposable-fixture",
        "ephemeral": False,
        "projectId": None,
        "modelProvider": "openai",
        "preview": "display preview is not task input",
        "historyMode": "legacy",
        "source": {
            "subAgent": {"thread_spawn": {"parent_thread_id": "primary-1", "depth": 1}}
        }
        if child
        else "appServer",
        "parentThreadId": "primary-1" if child else None,
        "status": {"type": "idle"},
        "turns": turns,
    }


@pytest.fixture
def codex_request() -> dict:
    # Synthetic public-schema records test mapping behavior, never host acceptance.
    prompt = "Exact role and task\r\nIncluding evidence\u00e9"
    calls = [
        {
            "type": "collabAgentToolCall",
            "id": "dispatch-1",
            "tool": "spawnAgent",
            "senderThreadId": "primary-1",
            "receiverThreadIds": ["worker-1"],
            "status": "completed",
            "prompt": prompt,
            "agentsStates": {},
        }
    ]
    child_turn = {
        "id": "task-1",
        "status": "completed",
        "itemsView": "full",
        "error": None,
        "items": [
            {
                "id": "input-1",
                "type": "userMessage",
                "content": [{"type": "text", "text": prompt}],
            },
            {
                "id": "progress-1",
                "type": "agentMessage",
                "phase": "commentary",
                "text": "Working",
            },
            {
                "id": "result-1",
                "type": "agentMessage",
                "phase": "final_answer",
                "text": "Complete result\r\n",
            },
        ],
    }
    return {
        "schema": mapping.REQUEST_SCHEMA,
        "profile": mapping.CODEX_PROFILE,
        "expected": {
            "scope_ref": "session-1",
            "supervisor_ref": "primary-1",
            "worker_ref": "worker-1",
            "rounds": [
                {"dispatch_ref": "dispatch-1", "task_ref": "task-1", "input": prompt}
            ],
        },
        "records": {
            "parent_read": {
                "thread": thread(
                    "primary-1",
                    [
                        {
                            "id": "primary-turn",
                            "status": "inProgress",
                            "itemsView": "full",
                            "items": calls,
                        }
                    ],
                )
            },
            "child_read": {"thread": thread("worker-1", [child_turn], child=True)},
        },
    }


@pytest.fixture
def claude_request() -> dict:
    prompt = "Immutable assignment\r\nOriginal evidence\u00e9"
    return {
        "schema": mapping.REQUEST_SCHEMA,
        "profile": mapping.CLAUDE_PROFILE,
        "expected": {
            "scope_ref": "session-1",
            "supervisor_ref": "session-1",
            "worker_ref": "agent-1",
            "rounds": [
                {"dispatch_ref": "tool-1", "task_ref": "tool-1", "input": prompt}
            ],
        },
        "records": {
            "invocation": {
                "type": "assistant",
                "uuid": "invocation-uuid",
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
                                "prompt": prompt,
                                "description": "Fixture delivery",
                                "subagent_type": "general-purpose",
                            },
                        }
                    ],
                },
            },
            "delivery": {
                "type": "user",
                "uuid": "delivery-uuid",
                "session_id": "session-1",
                "parent_tool_use_id": None,
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tool-1",
                            "content": "Model-directed trailer differs from full structured output",
                        }
                    ],
                },
                "tool_use_result": {
                    "agentId": "agent-1",
                    "prompt": prompt,
                    "status": "completed",
                    "content": [
                        {"type": "text", "text": "Full first part\r\n"},
                        {
                            "type": "text",
                            "text": "Full second part",
                            "citations": ["source-1"],
                        },
                    ],
                    "totalToolUseCount": 42,
                    "totalDurationMs": 1234,
                    "totalTokens": 123,
                    "usage": {
                        "input_tokens": 100,
                        "output_tokens": 23,
                        "cache_creation_input_tokens": None,
                        "cache_read_input_tokens": None,
                        "server_tool_use": None,
                        "service_tier": None,
                        "cache_creation": None,
                    },
                },
            },
        },
    }


@pytest.mark.parametrize("fixture", ["codex_request", "claude_request"])
def test_maps_exact_acknowledged_task_and_complete_result_without_acceptance(
    fixture, request
) -> None:
    payload = request.getfixturevalue(fixture)
    original = copy.deepcopy(payload)
    result = mapping.map_delivery(payload)
    assert result["state"] == "delivery_mapped"
    assert payload == original
    assert result["request_digest"] == mapping.digest(payload)
    assert result["records_digest"] == mapping.digest(payload["records"])
    assert result["acceptance_ready"] is False
    assert result["redispatch_allowed"] is False
    assert result["record_authenticity"] == "caller_supplied_unverified"
    assert result["mapped"]["observed_round_count"] == 1
    assert result["mapped"]["rounds_used"] is None
    assert result["mapped"]["worker_disposition"] is None
    assert "accepted_agent_configuration" in result["unresolved_domains"]
    assert "settlement_and_descendant_quiescence" in result["unresolved_domains"]
    mapped_round = result["mapped"]["rounds"][0]
    assert mapped_round["accepted_task_digest"] == mapping.digest(
        mapped_round["accepted_task_domain"]
    )
    native_input = mapped_round["accepted_task_domain"]["input"]
    accepted_text = (
        native_input[0]["text"]
        if fixture == "codex_request"
        else native_input["prompt"]
    )
    assert accepted_text == original["expected"]["rounds"][0]["input"]
    assert "\r\n" in accepted_text
    payload["expected"]["rounds"][0]["input"] = "later caller mutation"
    assert result["expected_recovery_refs"]["rounds"][0][
        "expected_input_digest"
    ] == mapping.digest(original["expected"]["rounds"][0]["input"])


def test_codex_maps_ordered_feedback_rounds_and_rejects_omitted_rounds(
    codex_request,
) -> None:
    payload = codex_request
    parent_items = payload["records"]["parent_read"]["thread"]["turns"][0]["items"]
    feedback = copy.deepcopy(parent_items[0])
    feedback.update(id="dispatch-2", tool="sendInput", prompt="Feedback\r\n")
    parent_items.append(feedback)
    child_turns = payload["records"]["child_read"]["thread"]["turns"]
    turn = copy.deepcopy(child_turns[0])
    turn["id"] = "task-2"
    for item in turn["items"]:
        item["id"] = item["id"].replace("-1", "-2")
    turn["items"][0]["content"][0]["text"] = feedback["prompt"]
    child_turns.append(turn)
    assert mapping.map_delivery(payload)["state"] == "rejected"
    payload["expected"]["rounds"].append(
        {
            "dispatch_ref": "dispatch-2",
            "task_ref": "task-2",
            "input": feedback["prompt"],
        }
    )
    result = mapping.map_delivery(payload)
    assert result["state"] == "delivery_mapped"
    assert result["mapped"]["observed_round_count"] == 2
    assert [entry["task_ref"] for entry in result["mapped"]["rounds"]] == [
        "task-1",
        "task-2",
    ]
    assert (
        result["mapped"]["rounds"][0]["accepted_task_digest"]
        != result["mapped"]["rounds"][1]["accepted_task_digest"]
    )
    payload["expected"]["rounds"].reverse()
    assert mapping.map_delivery(payload)["error"]["code"] == "ROUND_BINDING_MISMATCH"


@pytest.mark.parametrize("domain", ["task", "result", "citation"])
def test_claude_digest_domains_preserve_inputs_results_and_citations(
    claude_request, domain
) -> None:
    before = mapping.map_delivery(claude_request)["mapped"]["rounds"][0]
    records = claude_request["records"]
    if domain == "task":
        claude_request["expected"]["rounds"][0]["input"] += "\r\nChange"
        records["invocation"]["message"]["content"][0]["input"]["prompt"] += (
            "\r\nChange"
        )
        records["delivery"]["tool_use_result"]["prompt"] += "\r\nChange"
    elif domain == "result":
        records["delivery"]["tool_use_result"]["content"][1]["text"] += "\r\nChange"
    else:
        records["delivery"]["tool_use_result"]["content"][1]["citations"].append(
            "source-2"
        )
    after = mapping.map_delivery(claude_request)["mapped"]["rounds"][0]
    assert (before["accepted_task_digest"] != after["accepted_task_digest"]) is (
        domain == "task"
    )
    assert before["result_digest"] != after["result_digest"]


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("parentThreadId", "wrong-primary", "IDENTITY_MISMATCH"),
        ("sessionId", "wrong-session", "IDENTITY_MISMATCH"),
        ("id", "wrong-agent", "IDENTITY_MISMATCH"),
        ("cliVersion", "0.163.0", "UNSUPPORTED_SURFACE"),
        ("ephemeral", True, "UNSUPPORTED_SURFACE"),
        ("historyMode", "paginated", "INCOMPLETE_HISTORY"),
        ("source", "appServer", "REQUIRED_METADATA_MISSING"),
        ("status", {"type": "released"}, "INVALID_RECORD"),
    ],
)
def test_codex_rejects_unbound_or_unsupported_native_metadata(
    codex_request, field, value, code
) -> None:
    codex_request["records"]["child_read"]["thread"][field] = value
    result = mapping.map_delivery(codex_request)
    assert result["state"] != "delivery_mapped"
    assert result["error"]["code"] == code
    assert "mapped" not in result
    assert result["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("itemsView", "summary"),
        ("itemsView", "notLoaded"),
        ("status", "inProgress"),
        ("status", "failed"),
        ("status", "interrupted"),
        ("error", {"message": "failure"}),
    ],
)
def test_codex_incomplete_history_or_result_retains_reconciliation(
    codex_request, field, value
) -> None:
    codex_request["records"]["child_read"]["thread"]["turns"][0][field] = value
    result = mapping.map_delivery(codex_request)
    assert result["state"] == "reconciliation_required"
    assert result["request_digest"] == mapping.digest(codex_request)
    assert result["next_action"] == "reconcile_original_native_operation"
    assert result["expected_recovery_refs"]["rounds"][0]["dispatch_ref"] == "dispatch-1"
    assert "input" not in result["expected_recovery_refs"]["rounds"][0]
    assert result["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "inProgress"),
        ("status", "failed"),
        ("tool", "sendMessage"),
        ("tool", "closeAgent"),
        ("tool", "interruptAgent"),
    ],
)
def test_codex_uncertain_dispatch_or_unsupported_feedback_requires_reconciliation(
    codex_request, field, value
) -> None:
    codex_request["records"]["parent_read"]["thread"]["turns"][0]["items"][0][field] = (
        value
    )
    result = mapping.map_delivery(codex_request)
    assert result["state"] == "reconciliation_required"
    assert result["acceptance_ready"] is False
    assert result["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "change",
    [
        "prompt",
        "persisted_input",
        "missing_final",
        "late_item",
        "duplicate_item",
        "wrong_receiver",
        "wrong_sender",
        "unknown_phase",
        "async_result",
    ],
)
def test_codex_correlation_and_complete_delivery_failures(
    codex_request, change
) -> None:
    call = codex_request["records"]["parent_read"]["thread"]["turns"][0]["items"][0]
    items = codex_request["records"]["child_read"]["thread"]["turns"][0]["items"]
    if change == "prompt":
        call["prompt"] += "Changed target"
    elif change == "persisted_input":
        items[0]["content"][0]["text"] = "summary only"
    elif change == "missing_final":
        items.pop()
    elif change == "late_item":
        items.append(
            {
                "type": "agentMessage",
                "id": "late-1",
                "phase": "commentary",
                "text": "More work",
            }
        )
    elif change == "duplicate_item":
        items.append(copy.deepcopy(items[-1]))
    elif change == "wrong_receiver":
        call["receiverThreadIds"] = ["wrong-worker"]
    elif change == "wrong_sender":
        call["senderThreadId"] = "wrong-primary"
    elif change == "unknown_phase":
        items[-1]["phase"] = None
    else:
        items[-1]["delivery"] = "async"
    result = mapping.map_delivery(codex_request)
    assert result["state"] != "delivery_mapped"
    assert result["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("agentId", "wrong-agent"),
        ("prompt", "different task"),
        ("status", "async_launched"),
        ("content", []),
        ("totalTokens", True),
        ("totalToolUseCount", -1),
    ],
)
def test_claude_rejects_wrong_task_or_incomplete_structured_output(
    claude_request, field, value
) -> None:
    claude_request["records"]["delivery"]["tool_use_result"][field] = value
    result = mapping.map_delivery(claude_request)
    assert result["state"] != "delivery_mapped"
    assert result["acceptance_ready"] is False
    assert result["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "change",
    [
        "session",
        "tool_id",
        "missing_output",
        "summary_only",
        "background",
        "aborted",
        "missing_stop_reason",
        "multiple_invocations",
    ],
)
def test_claude_rejects_ambiguous_or_unavailable_delivery(
    claude_request, change
) -> None:
    records = claude_request["records"]
    if change == "session":
        records["delivery"]["session_id"] = "wrong-session"
    elif change == "tool_id":
        records["delivery"]["message"]["content"][0]["tool_use_id"] = "wrong-task"
    elif change == "missing_output":
        del records["delivery"]["tool_use_result"]
    elif change == "summary_only":
        records["delivery"]["tool_use_result"] = {
            "status": "completed",
            "summary": "Done",
        }
    elif change == "background":
        records["invocation"]["message"]["content"][0]["input"]["run_in_background"] = (
            True
        )
    elif change == "aborted":
        records["invocation"]["aborted"] = True
    elif change == "missing_stop_reason":
        del records["invocation"]["message"]["stop_reason"]
    else:
        records["invocation"]["message"]["content"].append(
            {
                "type": "tool_use",
                "id": "tool-2",
                "name": "Agent",
                "input": {"prompt": "other task"},
            }
        )
    result = mapping.map_delivery(claude_request)
    assert result["state"] != "delivery_mapped"
    assert result["redispatch_allowed"] is False


def test_submitted_configuration_and_idle_status_never_prove_acceptance(
    codex_request,
) -> None:
    child = codex_request["records"]["child_read"]["thread"]
    child.update(
        model="gpt-6.1-sol",
        reasoningEffort="medium",
        agentRole="Judge",
        instructions="Client supplied role",
    )
    result = mapping.map_delivery(codex_request)
    assert result["state"] == "delivery_mapped"
    assert result["mapped"]["reported_worker_status"] == "idle"
    assert result["mapped"]["worker_disposition"] is None
    assert "accepted_role_and_dependencies" in result["unresolved_domains"]
    assert "explicit_primary_acceptance" in result["unresolved_domains"]
    assert result["acceptance_ready"] is False


def test_claude_echoed_prompt_does_not_acknowledge_submitted_controls(
    claude_request,
) -> None:
    before = mapping.map_delivery(claude_request)
    claude_request["records"]["invocation"]["message"]["content"][0]["input"][
        "model"
    ] = "unacknowledged-model"
    after = mapping.map_delivery(claude_request)
    assert (
        before["mapped"]["rounds"][0]["accepted_task_digest"]
        == after["mapped"]["rounds"][0]["accepted_task_digest"]
    )
    assert before["records_digest"] != after["records_digest"]
    assert set(after["mapped"]["rounds"][0]["accepted_task_domain"]["input"]) == {
        "prompt"
    }
    assert "accepted_agent_configuration" in after["unresolved_domains"]


def cli(payload: bytes) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--input", "-"],
        input=payload,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def test_cli_roundtrip_and_reconciliation_exit_status(codex_request) -> None:
    result = cli(mapping.canonical_bytes(codex_request))
    assert result.returncode == 0
    assert json.loads(result.stdout)["state"] == "delivery_mapped"
    assert result.stderr == b""
    codex_request["records"]["child_read"]["thread"]["turns"][0]["status"] = (
        "inProgress"
    )
    result = cli(mapping.canonical_bytes(codex_request))
    assert result.returncode == 2
    assert json.loads(result.stdout)["state"] == "reconciliation_required"


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
def test_cli_rejects_noncanonical_or_invalid_json(payload) -> None:
    result = cli(payload)
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr.startswith(b"error:")


@pytest.mark.parametrize(
    "change",
    ["schema", "profile", "extra_acceptance", "missing_metadata", "duplicate_round"],
)
def test_closed_request_rejects_self_asserted_native_acceptance(
    codex_request, change
) -> None:
    if change == "schema":
        codex_request["schema"] = "aquarium.native-delivery-request/v2"
    elif change == "profile":
        codex_request["profile"] = "hosted-responses"
    elif change == "extra_acceptance":
        codex_request["native_configuration_accepted"] = True
    elif change == "missing_metadata":
        del codex_request["expected"]["worker_ref"]
    else:
        codex_request["expected"]["rounds"].append(
            copy.deepcopy(codex_request["expected"]["rounds"][0])
        )
    result = mapping.map_delivery(codex_request)
    assert result["state"] == "rejected"
    assert result["acceptance_ready"] is False
    assert result["redispatch_allowed"] is False


@pytest.fixture
def journal_spawn_request(codex_request) -> dict:
    # Match the observed public bridge shape, with synthetic identities and journal.
    # Real historical thread records lack this original pre-dispatch journal.
    request = copy.deepcopy(codex_request)
    request["profile"] = mapping.CODEX_SPAWN_PROFILE
    parent = request["records"]["parent_read"]["thread"]
    child = request["records"]["child_read"]["thread"]
    parent["historyMode"] = child["historyMode"] = "paginated"
    parent["status"] = {"type": "active", "activeFlags": []}
    child["source"]["subAgent"]["thread_spawn"]["agent_path"] = "/root/native_worker"
    parent["turns"][0]["items"] = [
        {
            "type": "subAgentActivity",
            "id": "dispatch-1",
            "kind": "started",
            "agentThreadId": "worker-1",
            "agentPath": "/root/native_worker",
            "model": "gpt-6.1-sol",
            "reasoningEffort": "high",
        },
        {
            "type": "subAgentActivity",
            "id": "completed-1",
            "kind": "completed",
            "agentThreadId": "worker-1",
            "agentPath": "/root/native_worker",
            "model": None,
            "reasoningEffort": None,
        },
    ]
    child["turns"][0]["items"] = [child["turns"][0]["items"][-1]]
    request["records"]["journal"] = {
        "request": {
            "task_name": "native_worker",
            "fork_turns": "all",
            "message": request["expected"]["rounds"][0]["input"],
        },
        "response": {"task_name": "/root/native_worker"},
    }
    return request


def test_journal_spawn_maps_acknowledged_request_without_native_prompt_echo(
    journal_spawn_request,
) -> None:
    original = copy.deepcopy(journal_spawn_request)
    result = mapping.map_delivery(journal_spawn_request)
    assert journal_spawn_request == original
    assert result["state"] == "delivery_mapped"
    mapped = result["mapped"]
    assert mapped["worker_ref"] == "worker-1"
    assert mapped["native_agent_path"] == "/root/native_worker"
    assert mapped["observed_round_count"] == 1
    assert mapped["reported_worker_status"] == "idle"
    assert mapped["worker_disposition"] is None
    assert mapped["rounds_used"] is None
    assert mapped["creation_controls"] == {
        "source_ref": "dispatch-1",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "high",
    }
    assert mapped["dispatch_acknowledgement"]["request_digest"] == mapping.digest(
        original["records"]["journal"]["request"]
    )
    assert mapped["dispatch_acknowledgement"]["response"] == {
        "task_name": "/root/native_worker"
    }
    task = mapped["rounds"][0]
    assert (
        task["accepted_task_domain"]["input"]
        == original["records"]["journal"]["request"]
    )
    assert task["accepted_task_digest"] == mapping.digest(task["accepted_task_domain"])
    assert task["result_refs"] == ["result-1"]
    assert result["record_authenticity"] == "caller_supplied_unverified"
    assert result["acceptance_ready"] is False
    assert result["redispatch_allowed"] is False
    assert "accepted_agent_configuration" in result["unresolved_domains"]
    journal_spawn_request["records"]["journal"]["request"]["message"] = (
        "later caller mutation"
    )
    assert (
        task["accepted_task_domain"]["input"]
        == original["records"]["journal"]["request"]
    )


@pytest.mark.parametrize(
    "response",
    [
        None,
        {},
        {"error": "lost response"},
        {"accepted": True},
        {"task_name": "/root/native_worker", "accepted": True},
    ],
)
def test_journal_spawn_missing_successful_ack_requires_reconciliation_even_with_matching_history(
    journal_spawn_request, response
) -> None:
    journal_spawn_request["records"]["journal"]["response"] = response
    result = mapping.map_delivery(journal_spawn_request)
    assert result["state"] == "reconciliation_required"
    assert result["error"]["code"] == "NATIVE_ACKNOWLEDGEMENT_REQUIRED"
    assert result["request_digest"] == mapping.digest(journal_spawn_request)
    assert result["expected_recovery_refs"]["worker_ref"] == "worker-1"
    assert result["next_action"] == "reconcile_original_native_operation"
    assert result["redispatch_allowed"] is False
    assert "mapped" not in result


def test_journal_spawn_absent_response_key_is_uncertain(journal_spawn_request) -> None:
    del journal_spawn_request["records"]["journal"]["response"]
    result = mapping.map_delivery(journal_spawn_request)
    assert result["state"] == "reconciliation_required"
    assert result["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("task_name", "../escape"),
        ("task_name", "WrongName"),
        ("fork_turns", "unknown"),
        ("message", "different assignment"),
        ("model", "gpt-6-sol"),
        ("reasoning_effort", "medium"),
        ("native_accepted", True),
    ],
)
def test_journal_spawn_rejects_invalid_or_unsupported_exact_requests(
    journal_spawn_request, field, value
) -> None:
    journal_spawn_request["records"]["journal"]["request"][field] = value
    result = mapping.map_delivery(journal_spawn_request)
    assert result["state"] == "rejected"
    assert result["acceptance_ready"] is False


@pytest.mark.parametrize(
    "field,native_field,value",
    [
        ("model", "model", "gpt-6-sol"),
        ("reasoning_effort", "reasoningEffort", "medium"),
    ],
)
def test_journal_spawn_explicit_controls_must_match_resolved_creation(
    journal_spawn_request, field, native_field, value
) -> None:
    arguments = journal_spawn_request["records"]["journal"]["request"]
    arguments.update(fork_turns="none", **{field: value})
    result = mapping.map_delivery(journal_spawn_request)
    assert result["state"] == "rejected"
    assert result["error"]["code"] == "CONFIGURATION_MISMATCH"
    creation = journal_spawn_request["records"]["parent_read"]["thread"]["turns"][0][
        "items"
    ][0]
    creation[native_field] = value
    result = mapping.map_delivery(journal_spawn_request)
    assert result["state"] == "delivery_mapped"
    assert result["mapped"]["creation_controls"][field] == value
    assert (
        result["mapped"]["rounds"][0]["accepted_task_domain"]["input"][field] == value
    )
    assert result["acceptance_ready"] is False


def test_journal_spawn_acknowledged_control_and_result_domains_remain_distinct(
    journal_spawn_request,
) -> None:
    before = mapping.map_delivery(journal_spawn_request)["mapped"]["rounds"][0]
    journal_spawn_request["records"]["journal"]["request"]["fork_turns"] = "none"
    after = mapping.map_delivery(journal_spawn_request)["mapped"]["rounds"][0]
    assert before["accepted_task_digest"] != after["accepted_task_digest"]
    assert before["result_digest"] != after["result_digest"]
    final = journal_spawn_request["records"]["child_read"]["thread"]["turns"][0][
        "items"
    ][-1]
    final["text"] += "\r\nFull additional result"
    changed_result = mapping.map_delivery(journal_spawn_request)["mapped"]["rounds"][0]
    assert changed_result["accepted_task_digest"] == after["accepted_task_digest"]
    assert changed_result["result_digest"] != after["result_digest"]


def test_journal_spawn_preserves_unselected_defaults_without_inventing_controls(
    journal_spawn_request,
) -> None:
    creation = journal_spawn_request["records"]["parent_read"]["thread"]["turns"][0][
        "items"
    ][0]
    creation["model"] = None
    del creation["reasoningEffort"]
    result = mapping.map_delivery(journal_spawn_request)
    assert result["state"] == "delivery_mapped"
    assert result["mapped"]["creation_controls"] == {
        "source_ref": "dispatch-1",
        "model": None,
        "reasoning_effort": None,
    }
    assert set(result["mapped"]["rounds"][0]["accepted_task_domain"]["input"]) == {
        "task_name",
        "fork_turns",
        "message",
    }
    assert result["acceptance_ready"] is False


@pytest.mark.parametrize(
    "change",
    [
        "missing_creation",
        "duplicate_path",
        "wrong_path",
        "wrong_native_id",
        "path_as_native_id",
        "wrong_dispatch",
        "wrong_task",
        "wrong_source_path",
        "wrong_parent",
        "wrong_source_parent",
        "wrong_session",
        "noncanonical_response",
        "different_response_name",
    ],
)
def test_journal_spawn_requires_native_creation_child_and_scope_correlations(
    journal_spawn_request, change
) -> None:
    records = journal_spawn_request["records"]
    activities = records["parent_read"]["thread"]["turns"][0]["items"]
    child = records["child_read"]["thread"]
    if change == "missing_creation":
        activities.pop(0)
    elif change == "duplicate_path":
        duplicate = copy.deepcopy(activities[0])
        duplicate.update(id="dispatch-2", agentThreadId="other-worker")
        activities.append(duplicate)
    elif change == "wrong_path":
        activities[0]["agentPath"] = "/root/wrong-worker"
    elif change == "wrong_native_id":
        activities[0]["agentThreadId"] = "wrong-worker"
    elif change == "path_as_native_id":
        journal_spawn_request["expected"]["worker_ref"] = "/root/native_worker"
    elif change == "wrong_dispatch":
        journal_spawn_request["expected"]["rounds"][0]["dispatch_ref"] = (
            "wrong-dispatch"
        )
    elif change == "wrong_task":
        journal_spawn_request["expected"]["rounds"][0]["task_ref"] = "wrong-task"
    elif change == "wrong_source_path":
        child["source"]["subAgent"]["thread_spawn"]["agent_path"] = "/root/wrong-worker"
    elif change == "wrong_parent":
        child["parentThreadId"] = "wrong-primary"
    elif change == "wrong_source_parent":
        child["source"]["subAgent"]["thread_spawn"]["parent_thread_id"] = (
            "wrong-primary"
        )
    elif change == "wrong_session":
        child["sessionId"] = "wrong-session"
    elif change == "noncanonical_response":
        records["journal"]["response"]["task_name"] = "/root/../native_worker"
    else:
        records["journal"]["response"]["task_name"] = "/root/different_worker"
    result = mapping.map_delivery(journal_spawn_request)
    assert result["state"] == "rejected"
    assert "mapped" not in result
    assert result["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "change",
    [
        "summary",
        "unloaded",
        "missing_items_view",
        "running",
        "failed",
        "no_final",
        "late_work",
        "async_result",
        "second_turn",
        "interacted",
        "second_completed",
        "collab_followup",
    ],
)
def test_journal_spawn_incomplete_initial_result_or_unqualified_followup_requires_reconciliation(
    journal_spawn_request, change
) -> None:
    records = journal_spawn_request["records"]
    child_turns = records["child_read"]["thread"]["turns"]
    turn = child_turns[0]
    activities = records["parent_read"]["thread"]["turns"][0]["items"]
    if change == "summary":
        turn["itemsView"] = "summary"
    elif change == "unloaded":
        turn["itemsView"] = "notLoaded"
    elif change == "missing_items_view":
        del turn["itemsView"]
    elif change == "running":
        turn["status"] = "inProgress"
    elif change == "failed":
        turn["status"] = "failed"
    elif change == "no_final":
        turn["items"][-1]["phase"] = "commentary"
    elif change == "late_work":
        turn["items"].append(
            {
                "id": "late-work",
                "type": "agentMessage",
                "phase": "commentary",
                "text": "More work",
            }
        )
    elif change == "async_result":
        turn["items"][-1]["delivery"] = "async"
    elif change == "second_turn":
        later = copy.deepcopy(turn)
        later["id"] = "later-task"
        later["items"][-1]["id"] = "later-result"
        child_turns.append(later)
    elif change in ("interacted", "second_completed"):
        extra = copy.deepcopy(activities[-1])
        extra.update(
            id="extra-activity",
            kind="interacted" if change == "interacted" else "completed",
        )
        activities.append(extra)
    else:
        activities.append(
            {
                "id": "followup-1",
                "type": "collabAgentToolCall",
                "tool": "followupTask",
                "status": "completed",
                "senderThreadId": "primary-1",
                "receiverThreadIds": ["worker-1"],
                "agentsStates": {},
            }
        )
    result = mapping.map_delivery(journal_spawn_request)
    assert result["state"] == "reconciliation_required"
    assert result["next_action"] == "reconcile_original_native_operation"
    assert result["redispatch_allowed"] is False


def test_journal_spawn_optional_echo_must_not_contradict_successful_request(
    journal_spawn_request,
) -> None:
    turn = journal_spawn_request["records"]["child_read"]["thread"]["turns"][0]
    turn["items"].insert(
        0,
        {
            "id": "input-1",
            "type": "userMessage",
            "content": [
                {
                    "type": "text",
                    "text": journal_spawn_request["records"]["journal"]["request"][
                        "message"
                    ],
                }
            ],
        },
    )
    assert mapping.map_delivery(journal_spawn_request)["state"] == "delivery_mapped"
    turn["items"][0]["content"][0]["text"] = "contradictory native input"
    assert (
        mapping.map_delivery(journal_spawn_request)["error"]["code"] == "INPUT_MISMATCH"
    )


def test_journal_spawn_cli_and_old_profile_remain_separate(
    journal_spawn_request, codex_request
) -> None:
    result = cli(mapping.canonical_bytes(journal_spawn_request))
    assert result.returncode == 0
    assert json.loads(result.stdout)["state"] == "delivery_mapped"
    codex_request["records"]["child_read"]["thread"]["historyMode"] = "paginated"
    assert mapping.map_delivery(codex_request)["error"]["code"] == "INCOMPLETE_HISTORY"


@pytest.fixture
def serialized_request(journal_spawn_request) -> dict:
    request = copy.deepcopy(journal_spawn_request)
    request["profile"] = mapping.CODEX_ROUNDS_PROFILE
    initial = request["records"]
    initial["preparation"] = {"integration_data": "mapper does not verify preparation"}
    after_parent = copy.deepcopy(initial["parent_read"])
    after_child = copy.deepcopy(initial["child_read"])
    template = initial["parent_read"]["thread"]["turns"][0]["items"][-1]
    after_parent["thread"]["turns"][0]["items"].extend(
        [
            {**template, "id": "dispatch-2", "kind": "interacted"},
            {**template, "id": "delivery-event-not-turn-id", "kind": "completed"},
        ]
    )
    turn = copy.deepcopy(after_child["thread"]["turns"][0])
    turn["id"] = "task-2"
    turn["items"] = [
        {**turn["items"][-1], "id": "final-2", "text": "Feedback final\r\n"}
    ]
    after_child["thread"]["turns"].append(turn)
    request["expected"]["rounds"].append(
        {
            "dispatch_ref": "dispatch-2",
            "task_ref": "task-2",
            "input": "Reassess changed candidate\r\n",
        }
    )
    request["records"] = {
        "initial": initial,
        "feedback": [
            {
                "request": {
                    "target": "/root/native_worker",
                    "message": request["expected"]["rounds"][1]["input"],
                },
                "feedback_completion_output_utf8": "",
                "before_parent_read": copy.deepcopy(initial["parent_read"]),
                "before_child_read": copy.deepcopy(initial["child_read"]),
                "after_parent_read": after_parent,
                "after_child_read": after_child,
                "preparation": {"integration_data": "binder owns verification"},
            }
        ],
    }
    return request


def test_serialized_feedback_preserves_exact_domains_and_counts_without_acceptance(
    serialized_request,
):
    original = copy.deepcopy(serialized_request)
    output = mapping.map_delivery(serialized_request)
    assert serialized_request == original
    assert output["state"] == "delivery_mapped"
    mapped = output["mapped"]
    assert mapped["observed_round_count"] == 2
    assert mapped["rounds_used"] is None and mapped["worker_disposition"] is None
    assert (
        mapped["rounds"][0]["accepted_task_domain"]["profile"]
        == mapping.CODEX_SPAWN_PROFILE
    )
    second = mapped["rounds"][1]
    assert second["task_ref"] == "task-2"
    assert (
        second["accepted_task_domain"]["input"]
        == serialized_request["records"]["feedback"][0]["request"]
    )
    assert (
        mapped["feedback_acknowledgements"][0]["feedback_completion_output_utf8"] == ""
    )
    assert output["record_authenticity"] == "caller_supplied_unverified"
    assert output["acceptance_ready"] is False and output["redispatch_allowed"] is False
    assert mapped["creation_controls"]["source_ref"] == "dispatch-1"


@pytest.mark.parametrize(
    "change",
    [
        "missing_completion",
        "null_completion",
        "fake_success",
        "wrong_target",
        "wrong_message",
        "active_before",
        "changed_before_prefix",
        "changed_after_prefix",
        "extra_turn",
        "incomplete_turn",
        "wrong_turn",
        "wrong_worker",
        "wrong_source",
        "wrong_session",
        "missing_completion_event",
        "extra_interaction",
        "wrong_dispatch",
        "wrong_event_worker",
        "unloaded_projection",
        "missing_final",
        "extra_call",
        "stale_parent",
        "initial_active",
        "initial_missing_delivery",
        "omitted_expected",
    ],
)
def test_serialized_feedback_rejects_uncertain_or_mismatched_operation(
    serialized_request, change
):
    records = serialized_request["records"]
    feedback = records["feedback"][0]
    before = feedback["before_child_read"]["thread"]
    after = feedback["after_child_read"]["thread"]
    items = feedback["after_parent_read"]["thread"]["turns"][0]["items"]
    if change == "missing_completion":
        del feedback["feedback_completion_output_utf8"]
    elif change == "null_completion":
        feedback["feedback_completion_output_utf8"] = None
    elif change == "fake_success":
        feedback["success"] = True
    elif change == "wrong_target":
        feedback["request"]["target"] = "worker-1"
    elif change == "wrong_message":
        feedback["request"]["message"] = "altered"
    elif change == "active_before":
        before["status"]["type"] = "active"
    elif change == "changed_before_prefix":
        before["turns"][0]["items"][-1]["text"] = "changed"
    elif change == "changed_after_prefix":
        after["turns"][0]["items"][-1]["text"] = "changed"
    elif change == "extra_turn":
        after["turns"].append(
            {**copy.deepcopy(after["turns"][-1]), "id": "extra-turn", "items": []}
        )
    elif change == "incomplete_turn":
        after["turns"][-1]["status"] = "inProgress"
    elif change == "wrong_turn":
        after["turns"][-1]["id"] = "wrong"
    elif change == "wrong_worker":
        after["id"] = "wrong"
    elif change == "wrong_source":
        after["source"]["subAgent"]["thread_spawn"]["agent_path"] = "/root/wrong"
    elif change == "wrong_session":
        after["sessionId"] = "wrong"
    elif change == "missing_completion_event":
        items.pop()
    elif change == "extra_interaction":
        items.append({**items[-2], "id": "extra-interaction"})
    elif change == "wrong_dispatch":
        items[-2]["id"] = "wrong"
    elif change == "wrong_event_worker":
        items[-2]["agentThreadId"] = "wrong"
    elif change == "unloaded_projection":
        after["turns"][-1]["itemsView"] = "summary"
    elif change == "missing_final":
        after["turns"][-1]["items"][-1]["phase"] = "commentary"
    elif change == "extra_call":
        items.append(
            {
                "id": "extra-call",
                "type": "collabAgentToolCall",
                "receiverThreadIds": ["worker-1"],
                "tool": "wait",
                "status": "completed",
            }
        )
    elif change == "stale_parent":
        feedback["after_parent_read"] = copy.deepcopy(feedback["before_parent_read"])
    elif change == "initial_active":
        records["initial"]["child_read"]["thread"]["status"]["type"] = "active"
    elif change == "initial_missing_delivery":
        records["initial"]["parent_read"]["thread"]["turns"][0]["items"].pop()
    elif change == "omitted_expected":
        serialized_request["expected"]["rounds"].pop()
    output = mapping.map_delivery(serialized_request)
    assert output["state"] in ("rejected", "reconciliation_required")
    assert output["redispatch_allowed"] is False
    assert "mapped" not in output
    if change in (
        "missing_completion",
        "active_before",
        "changed_before_prefix",
        "changed_after_prefix",
        "extra_turn",
        "incomplete_turn",
        "wrong_turn",
        "missing_completion_event",
        "extra_interaction",
        "wrong_dispatch",
        "unloaded_projection",
        "missing_final",
        "extra_call",
        "stale_parent",
        "initial_active",
        "initial_missing_delivery",
        "omitted_expected",
    ):
        assert output["state"] == "reconciliation_required"


def test_serialized_feedback_maps_multiple_idle_rounds_and_allows_unrelated_primary_work(
    serialized_request,
):
    request = serialized_request
    prior = request["records"]["feedback"][0]
    later = copy.deepcopy(prior)
    later["before_parent_read"] = copy.deepcopy(prior["after_parent_read"])
    later["before_child_read"] = copy.deepcopy(prior["after_child_read"])
    later["after_parent_read"] = copy.deepcopy(later["before_parent_read"])
    events = later["after_parent_read"]["thread"]["turns"][0]["items"]
    events.extend(
        [{**events[-2], "id": "dispatch-3"}, {**events[-1], "id": "completed-3"}]
    )
    events.insert(
        0,
        {
            "id": "primary-comment",
            "type": "agentMessage",
            "text": "Unrelated Primary activity",
            "phase": "commentary",
        },
    )
    later["after_child_read"] = copy.deepcopy(later["before_child_read"])
    turn = copy.deepcopy(later["after_child_read"]["thread"]["turns"][-1])
    turn.update(id="task-3", items=[{**turn["items"][-1], "id": "final-3"}])
    later["after_child_read"]["thread"]["turns"].append(turn)
    later["request"]["message"] = "Third exact assignment"
    request["expected"]["rounds"].append(
        {
            "dispatch_ref": "dispatch-3",
            "task_ref": "task-3",
            "input": later["request"]["message"],
        }
    )
    request["records"]["feedback"].append(later)
    output = mapping.map_delivery(request)
    assert output["state"] == "delivery_mapped"
    assert output["mapped"]["observed_round_count"] == 3
    assert len(output["mapped"]["feedback_acknowledgements"]) == 2


def test_serialized_feedback_cli_retains_empty_completion_and_reconciles_omission(
    serialized_request,
):
    result = cli(mapping.canonical_bytes(serialized_request))
    assert result.returncode == 0
    assert (
        json.loads(result.stdout)["mapped"]["feedback_acknowledgements"][0][
            "feedback_completion_output_utf8"
        ]
        == ""
    )
    del serialized_request["records"]["feedback"][0]["feedback_completion_output_utf8"]
    result = cli(mapping.canonical_bytes(serialized_request))
    assert result.returncode == 2
    assert json.loads(result.stdout)["state"] == "reconciliation_required"


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
def test_serialized_feedback_rejects_malformed_status_with_recovery_refs(
    serialized_request, snapshot, status
):
    serialized_request["records"]["feedback"][0][snapshot]["thread"]["status"] = status
    output = mapping.map_delivery(serialized_request)
    assert output["state"] == "rejected"
    assert output["error"]["code"] == "REQUIRED_METADATA_MISSING"
    assert output["acceptance_ready"] is False
    assert output["redispatch_allowed"] is False
    assert output["expected_recovery_refs"]["worker_ref"] == "worker-1"
    result = cli(mapping.canonical_bytes(serialized_request))
    assert result.returncode == 2
    assert not result.stderr
    assert json.loads(result.stdout) == output


@pytest.mark.parametrize(
    "change",
    [
        "missing_after",
        "duplicate_turn",
        "reversed_initial_delivery",
        "duplicated_started",
    ],
)
def test_serialized_missing_or_ambiguous_history_reconciles(serialized_request, change):
    record = serialized_request["records"]["feedback"][0]
    if change == "missing_after":
        del record["after_child_read"]
    elif change == "duplicate_turn":
        record["after_child_read"]["thread"]["turns"].append(
            copy.deepcopy(record["after_child_read"]["thread"]["turns"][-1])
        )
    elif change == "reversed_initial_delivery":
        serialized_request["records"]["initial"]["parent_read"]["thread"]["turns"][0][
            "items"
        ].reverse()
    elif change == "duplicated_started":
        items = serialized_request["records"]["initial"]["parent_read"]["thread"][
            "turns"
        ][0]["items"]
        items.append({**items[0], "id": "second-started"})
    output = mapping.map_delivery(serialized_request)
    assert output["state"] == "reconciliation_required"
    assert output["redispatch_allowed"] is False
    assert "mapped" not in output


@pytest.mark.parametrize("duration", [0, 0.0, -0.0, 0.125, 1234.75, 10**100])
def test_claude_completed_duration_accepts_native_finite_nonnegative_numbers(
    claude_request, duration
):
    claude_request["records"]["delivery"]["tool_use_result"]["totalDurationMs"] = (
        duration
    )
    output = mapping.map_delivery(claude_request)
    assert output["state"] == "delivery_mapped"
    expected = mapping._round(
        mapping.CLAUDE_PROFILE,
        "session-1",
        "agent-1",
        "tool-1",
        "tool-1",
        {"prompt": claude_request["expected"]["rounds"][0]["input"]},
        claude_request["records"]["delivery"]["tool_use_result"],
        ["delivery-uuid"],
    )
    assert output["mapped"]["rounds"][0]["result_digest"] == expected["result_digest"]


@pytest.mark.parametrize(
    "duration",
    [True, False, -1, -0.1, float("nan"), float("inf"), float("-inf"), "1", None],
)
def test_claude_completed_duration_rejects_non_native_or_nonfinite_numbers(
    claude_request, duration
):
    claude_request["records"]["delivery"]["tool_use_result"]["totalDurationMs"] = (
        duration
    )
    output = mapping.map_delivery(claude_request)
    assert output["state"] == "rejected"
    assert output["redispatch_allowed"] is False
    assert "mapped" not in output


@pytest.mark.parametrize("field", ["totalTokens", "totalToolUseCount"])
def test_claude_completed_counts_still_require_integers(claude_request, field):
    claude_request["records"]["delivery"]["tool_use_result"][field] = 1.5
    assert mapping.map_delivery(claude_request)["state"] == "rejected"


@pytest.fixture
def claude_null_stop_request(claude_request):
    # Sanitized shape from actual CLI 2.1.295 stream: null stop reason with a
    # paired completed AgentOutput, zero tool calls and opaque harness fields.
    request = copy.deepcopy(claude_request)
    request["records"]["invocation"]["message"]["stop_reason"] = None
    request["records"]["invocation"]["message"]["content"][0]["input"][
        "run_in_background"
    ] = False
    request["records"]["delivery"]["tool_use_result"].update(
        resolvedModel="native-resolved-model",
        totalToolUseCount=0,
        canContinueAgent=True,
        harnessNoteCount=0,
        harnessTailCount=0,
        harnessSectionHash="opaque-native-harness-hash",
    )
    return request


def test_claude_null_stop_reason_maps_only_the_correlated_complete_native_output(
    claude_null_stop_request,
):
    request = claude_null_stop_request
    original = copy.deepcopy(request)
    output = mapping.map_delivery(request)
    assert request == original
    assert output["state"] == "delivery_mapped"
    round_record = output["mapped"]["rounds"][0]
    structured = request["records"]["delivery"]["tool_use_result"]
    expected_domain = {
        "schema": "aquarium.native-result-domain/v1",
        "profile": mapping.CLAUDE_PROFILE,
        "accepted_task_digest": round_record["accepted_task_digest"],
        "result": structured,
    }
    assert round_record["result_digest"] == mapping.digest(expected_domain)
    assert round_record["result_refs"] == ["delivery-uuid"]
    assert output["mapped"]["observed_round_count"] == 1
    assert output["mapped"]["rounds_used"] is None
    assert output["mapped"]["worker_disposition"] is None
    assert output["acceptance_ready"] is False and output["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("canContinueAgent", False),
        ("harnessNoteCount", 1),
        ("harnessTailCount", 1),
        ("harnessSectionHash", "changed-opaque-native-harness-hash"),
    ],
)
def test_claude_null_stop_preserves_opaque_native_extensions_in_full_result_digest(
    claude_null_stop_request, field, value
):
    before = mapping.map_delivery(claude_null_stop_request)
    claude_null_stop_request["records"]["delivery"]["tool_use_result"][field] = value
    after = mapping.map_delivery(claude_null_stop_request)
    assert after["state"] == "delivery_mapped"
    assert (
        before["mapped"]["rounds"][0]["result_digest"]
        != after["mapped"]["rounds"][0]["result_digest"]
    )
    assert (
        before["mapped"]["rounds"][0]["accepted_task_digest"]
        == after["mapped"]["rounds"][0]["accepted_task_digest"]
    )
    assert after["mapped"]["worker_disposition"] is None


@pytest.mark.parametrize(
    "change",
    [
        "missing_output",
        "missing_usage",
        "missing_stop_reason",
        "async",
        "empty_content",
        "invocation_prompt",
        "output_prompt",
        "tool_result_id",
        "worker_id",
        "session_id",
        "tool_error",
        "aborted",
        "multiple_invocations",
    ],
)
def test_claude_null_stop_reason_does_not_bypass_complete_output_and_identity_checks(
    claude_null_stop_request, change
):
    request = claude_null_stop_request
    records = request["records"]
    message = records["invocation"]["message"]
    output = records["delivery"]["tool_use_result"]
    if change == "missing_output":
        del records["delivery"]["tool_use_result"]
    elif change == "missing_usage":
        del output["usage"]
    elif change == "missing_stop_reason":
        del message["stop_reason"]
    elif change == "async":
        output["status"] = "async_launched"
    elif change == "empty_content":
        output["content"] = []
    elif change == "invocation_prompt":
        message["content"][0]["input"]["prompt"] = "Wrong exact input"
    elif change == "output_prompt":
        output["prompt"] = "Wrong echoed prompt"
    elif change == "tool_result_id":
        records["delivery"]["message"]["content"][0]["tool_use_id"] = "wrong-tool"
    elif change == "worker_id":
        output["agentId"] = "wrong-worker"
    elif change == "session_id":
        records["delivery"]["session_id"] = "wrong-session"
    elif change == "tool_error":
        records["delivery"]["message"]["content"][0]["is_error"] = True
    elif change == "aborted":
        records["invocation"]["aborted"] = True
    elif change == "multiple_invocations":
        message["content"].append(
            {**copy.deepcopy(message["content"][0]), "id": "second-tool"}
        )
    mapped = mapping.map_delivery(request)
    assert mapped["state"] in ("rejected", "reconciliation_required")
    assert mapped["redispatch_allowed"] is False
    assert "mapped" not in mapped


@pytest.mark.parametrize(
    "stop_reason",
    [
        "end_turn",
        "max_tokens",
        "stop_sequence",
        "pause_turn",
        "refusal",
        "",
        False,
        0,
        {},
    ],
)
def test_claude_other_stop_reasons_do_not_qualify_completed_agent_pair(
    claude_null_stop_request, stop_reason
):
    claude_null_stop_request["records"]["invocation"]["message"]["stop_reason"] = (
        stop_reason
    )
    output = mapping.map_delivery(claude_null_stop_request)
    assert output["state"] == "reconciliation_required"
    assert output["error"]["code"] == "INCOMPLETE_RESULT"
    assert "mapped" not in output


@pytest.mark.parametrize("mismatch", ["invocation_and_output", "output_only"])
def test_claude_null_stop_reason_never_normalizes_missing_final_prompt_lf(
    claude_null_stop_request, mismatch
):
    request = claude_null_stop_request
    exact = request["expected"]["rounds"][0]["input"] + "\n"
    request["expected"]["rounds"][0]["input"] = exact
    if mismatch == "output_only":
        request["records"]["invocation"]["message"]["content"][0]["input"]["prompt"] = (
            exact
        )
    output = mapping.map_delivery(request)
    assert output["state"] == "rejected"
    assert output["error"]["code"] == "INPUT_MISMATCH"
    assert output["redispatch_allowed"] is False
    assert "mapped" not in output


@pytest.fixture
def claude_feedback_request(claude_null_stop_request):
    request = copy.deepcopy(claude_null_stop_request)
    initial = request["records"]
    scope, worker, original_use = "session-1", "agent-1", "tool-1"
    exact_input = "Exact serialized feedback\r\nFinal newline\n"
    request["profile"] = mapping.CLAUDE_ROUNDS_PROFILE
    request["expected"]["rounds"].append(
        {"dispatch_ref": "send-1", "task_ref": "run-1", "input": exact_input}
    )
    invocation = copy.deepcopy(initial["invocation"])
    invocation["uuid"] = "feedback-invocation"
    invocation["message"]["content"] = [
        {
            "type": "tool_use",
            "id": "send-1",
            "name": "SendMessage",
            "input": {
                "to": worker,
                "message": exact_input,
                "summary": "Feedback task",
                "type": "message",
                "recipient": worker,
                "recipient_kind": "agent",
                "content": "Ellipsized legacy field; do not interpret",
            },
        }
    ]
    delivery = copy.deepcopy(initial["delivery"])
    delivery["uuid"] = "feedback-delivery"
    delivery["message"]["content"] = [
        {"type": "tool_result", "tool_use_id": "send-1", "content": "Resumed"}
    ]
    delivery["tool_use_result"] = {
        "success": True,
        "resumedAgentId": worker,
        "pin": {"id": worker, "ref": "opaque-pin"},
    }

    def child(kind, uuid, body):
        return {
            "type": kind,
            "uuid": uuid,
            "session_id": scope,
            "parent_tool_use_id": original_use,
            "parent_agent_id": None,
            "message": {"role": kind, **body},
            "timestamp": "native-timestamp",
        }

    public = [
        child(
            "user",
            "child-input-1",
            {"content": request["expected"]["rounds"][0]["input"]},
        ),
        child(
            "assistant",
            "child-thought-1",
            {
                "id": "message-a",
                "model": "native-resolved-model",
                "stop_reason": None,
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "Opaque complete thinking",
                        "signature": "native-signature",
                    }
                ],
            },
        ),
        child(
            "assistant",
            "child-final-1",
            {
                "id": "message-a",
                "model": "native-resolved-model",
                "stop_reason": "end_turn",
                "content": copy.deepcopy(
                    initial["delivery"]["tool_use_result"]["content"]
                ),
            },
        ),
        child(
            "user",
            "child-feedback-wrapper",
            {"content": "Opaque coordinator wrapper; not a parser contract"},
        ),
        child(
            "assistant",
            "child-final-2",
            {
                "id": "message-b",
                "model": "native-feedback-model",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "Complete feedback answer"}],
                "usage": {"output_tokens": 5},
            },
        ),
    ]
    forwarded = copy.deepcopy(public[-1])
    forwarded["message"]["stop_reason"] = None
    forwarded["agent_id"] = worker

    def event(subtype, uuid, **fields):
        return {
            "type": "system",
            "subtype": subtype,
            "uuid": uuid,
            "session_id": scope,
            **fields,
        }

    common = {"task_id": worker, "run_id": "run-1"}
    events = [
        event(
            "background_tasks_changed",
            "active-snapshot",
            tasks=[{**common, "task_type": "local_agent"}],
        ),
        event(
            "task_started",
            "started-event",
            **common,
            tool_use_id="send-1",
            prompt=exact_input,
            is_backgrounded=True,
            spawn_depth=1,
            task_type="local_agent",
            subagent_type="general-purpose",
        ),
        event(
            "task_updated",
            "completed-event",
            **common,
            patch={"status": "completed", "end_time": 123},
        ),
        event(
            "task_notification",
            "notification-event",
            **common,
            tool_use_id="send-1",
            status="completed",
            output_file="/caller-owned-output",
            summary="Summary is not full answer",
            usage={"duration_ms": 1, "tool_uses": 0},
        ),
        event("background_tasks_changed", "finished-snapshot", tasks=[]),
    ]
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
                    "session_id": scope,
                    "agent_id": worker,
                    "agents": [worker],
                    "child": public,
                },
            }
        ],
    }
    return request


def test_claude_feedback_maps_two_distinct_complete_native_result_domains(
    claude_feedback_request,
):
    original = copy.deepcopy(claude_feedback_request)
    output = mapping.map_delivery(claude_feedback_request)
    assert output["state"] == "delivery_mapped", output
    assert claude_feedback_request == original
    mapped = output["mapped"]
    assert mapped["observed_round_count"] == 2
    assert mapped["rounds_used"] is None and mapped["worker_disposition"] is None
    initial, feedback = mapped["rounds"]
    assert initial["accepted_task_domain"]["profile"] == mapping.CLAUDE_PROFILE
    assert (
        feedback["accepted_task_domain"]["input"]
        == claude_feedback_request["records"]["feedback"][0]["invocation"]["message"][
            "content"
        ][0]["input"]
    )
    assert feedback["task_ref"] == "run-1"
    assert feedback["result_refs"] == ["child-final-2", "notification-event"]
    domain = feedback["result_domain"]
    assert mapping.digest(domain) == feedback["result_digest"]
    assert domain["result"]["schema"] == "aquarium.claude-feedback-result/v1"
    assert (
        domain["result"]["public_child_messages"]
        == claude_feedback_request["records"]["feedback"][0]["public_history"]["child"][
            3:
        ]
    )
    assert domain["result"]["forwarded_result"]["message"]["stop_reason"] is None
    assert (
        domain["result"]["public_child_messages"][-1]["message"]["stop_reason"]
        == "end_turn"
    )
    assert domain["result"]["send_message_delivery"]["tool_use_result"]["pin"] == {
        "id": "agent-1",
        "ref": "opaque-pin",
    }
    assert (
        mapped["creation_controls"]["acknowledged_input"]["run_in_background"] is False
    )
    assert mapped["creation_controls"]["resolvedModel"] == "native-resolved-model"
    assert mapped["feedback_run"]["is_backgrounded"] is True
    assert mapped["feedback_run"]["model"] == "native-feedback-model"
    assert output["acceptance_ready"] is False and output["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "change",
    [
        "wrong_target",
        "wrong_message",
        "wrong_reply_agent",
        "missing_success",
        "false_success",
        "wrong_result_use",
        "wrong_scope",
        "wrong_task",
        "wrong_run",
        "wrong_started_prompt",
        "wrong_notification_use",
        "pending_update",
        "pending_notification",
        "pending_snapshot",
        "extra_started",
        "extra_round",
        "missing_notification",
        "truncated_final",
        "missing_initial_terminal",
        "wrong_predecessor",
        "wrong_initial_prompt",
        "extra_user",
        "assistant_after_initial_terminal",
        "wrong_child_ancestry",
        "wrong_history_agent",
        "wrong_forwarded_uuid",
        "wrong_forwarded_content",
        "wrong_forwarded_model",
        "wrong_initial_model",
        "nonterminal_final",
        "summary_only",
        "missing_full_history",
    ],
)
def test_claude_feedback_rejects_uncertain_or_mismatched_native_records(
    claude_feedback_request, change
):
    request = claude_feedback_request
    record = request["records"]["feedback"][0]
    args = record["invocation"]["message"]["content"][0]["input"]
    reply = record["delivery"]["tool_use_result"]
    events, child = record["events"], record["public_history"]["child"]
    if change == "wrong_target":
        args["to"] = "wrong-agent"
    elif change == "wrong_message":
        args["message"] = args["message"][:-1]
    elif change == "wrong_reply_agent":
        reply["resumedAgentId"] = "wrong-agent"
    elif change == "missing_success":
        del reply["success"]
    elif change == "false_success":
        reply["success"] = False
    elif change == "wrong_result_use":
        record["delivery"]["message"]["content"][0]["tool_use_id"] = "wrong-use"
    elif change == "wrong_scope":
        events[1]["session_id"] = "wrong-session"
    elif change == "wrong_task":
        events[1]["task_id"] = "wrong-task"
    elif change == "wrong_run":
        events[2]["run_id"] = "wrong-run"
    elif change == "wrong_started_prompt":
        events[1]["prompt"] = args["message"][:-1]
    elif change == "wrong_notification_use":
        events[3]["tool_use_id"] = "wrong-use"
    elif change == "pending_update":
        events[2]["patch"]["status"] = "running"
    elif change == "pending_notification":
        events[3]["status"] = "running"
    elif change == "pending_snapshot":
        events[-1]["tasks"] = copy.deepcopy(events[0]["tasks"])
    elif change == "extra_started":
        events.insert(
            2,
            {**copy.deepcopy(events[1]), "uuid": "extra-start", "run_id": "extra-run"},
        )
    elif change == "extra_round":
        request["expected"]["rounds"].append(
            {
                "dispatch_ref": "send-2",
                "task_ref": "run-2",
                "input": "Unmapped extra round",
            }
        )
    elif change == "missing_notification":
        events.pop(3)
    elif change == "truncated_final":
        child[-1]["message"]["content"][0]["text"] = "Complete feedback..."
    elif change == "missing_initial_terminal":
        child.pop(2)
    elif change == "wrong_predecessor":
        child[2]["message"]["content"][0]["text"] = "Different initial result"
    elif change == "wrong_initial_prompt":
        child[0]["message"]["content"] = "Wrong original input"
    elif change == "extra_user":
        child.insert(4, {**copy.deepcopy(child[3]), "uuid": "competing-user"})
    elif change == "assistant_after_initial_terminal":
        child.insert(3, {**copy.deepcopy(child[1]), "uuid": "unmatched-assistant"})
    elif change == "wrong_child_ancestry":
        child[-1]["parent_tool_use_id"] = "send-1"
    elif change == "wrong_history_agent":
        record["public_history"]["agent_id"] = "wrong-agent"
    elif change == "wrong_forwarded_uuid":
        record["forwarded_result"]["uuid"] = "wrong-uuid"
    elif change == "wrong_forwarded_content":
        record["forwarded_result"]["message"]["content"] = [
            {"type": "text", "text": "Summary"}
        ]
    elif change == "wrong_forwarded_model":
        record["forwarded_result"]["message"]["model"] = "contradictory-model"
    elif change == "wrong_initial_model":
        child[2]["message"]["model"] = "contradictory-initial-model"
    elif change == "nonterminal_final":
        child[-1]["message"]["stop_reason"] = None
    elif change == "summary_only":
        child[-1]["message"]["content"] = []
    elif change == "missing_full_history":
        record["public_history"]["child"] = child[3:]
    output = mapping.map_delivery(request)
    assert output["state"] in ("rejected", "reconciliation_required"), output
    assert output["redispatch_allowed"] is False and "mapped" not in output


def test_claude_feedback_preserves_unrelated_agents_and_background_tasks(
    claude_feedback_request,
):
    record = claude_feedback_request["records"]["feedback"][0]
    record["public_history"]["agents"].append("unrelated-agent")
    record["events"][0]["tasks"].append(
        {"task_id": "unrelated-agent", "run_id": "unrelated-run"}
    )
    record["events"][-1]["tasks"].append(
        {"task_id": "unrelated-agent", "run_id": "unrelated-run"}
    )
    output = mapping.map_delivery(claude_feedback_request)
    assert output["state"] == "delivery_mapped"
    assert output["mapped"]["worker_disposition"] is None


def test_claude_feedback_cli_uses_complete_projection_domain(claude_feedback_request):
    response = cli(mapping.canonical_bytes(claude_feedback_request))
    assert response.returncode == 0, response.stderr.decode()
    assert (
        json.loads(response.stdout)["mapped"]["rounds"][1]["result_domain"]["result"][
            "schema"
        ]
        == "aquarium.claude-feedback-result/v1"
    )


def extend_claude_lifetime(request, count):
    request["profile"] = mapping.CLAUDE_LIFETIME_PROFILE
    template = request["records"]["feedback"][0]
    for index in range(2, count):
        substitutions = {
            "send-1": f"send-{index}",
            "run-1": f"run-{index}",
            request["expected"]["rounds"][1][
                "input"
            ]: f"Assignment {index}\r\nFinal newline\n",
        }

        def replace(value, substitutions=substitutions):
            if isinstance(value, dict):
                return {key: replace(item) for key, item in value.items()}
            if isinstance(value, list):
                return [replace(item) for item in value]
            if isinstance(value, str):
                return substitutions.get(value, value)
            return value

        record = replace(copy.deepcopy(template))
        for item in [record["invocation"], record["delivery"], *record["events"]]:
            item["uuid"] += f"-{index}"
        pair = record["public_history"]["child"][-2:]
        for item in pair:
            item["uuid"] += f"-{index}"
        pair[-1]["message"]["id"] += f"-{index}"
        pair[-1]["message"]["model"] = f"native-model-{index}"
        pair[-1]["message"]["content"][0]["text"] = f"Round {index} result\r\n"
        record["public_history"]["child"] = (
            copy.deepcopy(request["records"]["feedback"][-1]["public_history"]["child"])
            + pair
        )
        record["forwarded_result"] = copy.deepcopy(pair[-1])
        record["forwarded_result"]["message"]["stop_reason"] = None
        record["forwarded_result"]["agent_id"] = request["expected"]["worker_ref"]
        record["events"][1]["is_backgrounded"] = index % 2 == 1
        request["records"]["feedback"].append(record)
        request["expected"]["rounds"].append(
            {
                "dispatch_ref": f"send-{index}",
                "task_ref": f"run-{index}",
                "input": substitutions[request["expected"]["rounds"][1]["input"]],
            }
        )
    return request


@pytest.mark.parametrize("count", [3, 4, 34])
def test_claude_lifetime_retains_each_round_without_total_lifetime_quota(
    claude_feedback_request, count
):
    request = extend_claude_lifetime(claude_feedback_request, count)
    original = copy.deepcopy(request)
    output = mapping.map_delivery(request)
    assert output["state"] == "delivery_mapped", output
    assert request == original
    mapped = output["mapped"]
    assert len(mapped["rounds"]) == count
    assert (
        len(mapped["feedback_runs"])
        == len(mapped["feedback_acknowledgements"])
        == count - 1
    )
    assert mapped["feedback_run"] == mapped["feedback_runs"][-1]
    assert mapped["rounds_used"] is None
    for index, entry in enumerate(mapped["rounds"][1:], 1):
        assert mapping.digest(entry["result_domain"]) == entry["result_digest"]
        assert entry["task_ref"] == request["expected"]["rounds"][index]["task_ref"]
        if index > 1:
            previous = request["records"]["feedback"][index - 2]["public_history"][
                "child"
            ]
            assert (
                entry["result_domain"]["result"]["predecessor_terminal_uuid"]
                == previous[-1]["uuid"]
            )
    shorter = copy.deepcopy(request)
    shorter["expected"]["rounds"].pop()
    shorter["records"]["feedback"].pop()
    assert mapping.map_delivery(shorter)["mapped"]["rounds"] == mapped["rounds"][:-1]
    assert output["acceptance_ready"] is False and output["redispatch_allowed"] is False


@pytest.mark.parametrize(
    "change",
    [
        "missing_middle",
        "extra_record",
        "reorder",
        "duplicate_run",
        "duplicate_dispatch",
        "duplicate_event",
        "missing_ack",
        "changed_prefix",
        "truncated_prefix",
        "changed_middle_model",
        "pending_middle",
        "superseded_middle",
        "orphan_assignment",
    ],
)
def test_claude_lifetime_rejects_incomplete_or_stale_middle_rounds(
    claude_feedback_request, change
):
    request = extend_claude_lifetime(claude_feedback_request, 4)
    feedback = request["records"]["feedback"]
    middle = feedback[1]
    if change == "missing_middle":
        feedback.pop(1)
    elif change == "extra_record":
        feedback.append(copy.deepcopy(middle))
    elif change == "reorder":
        feedback[0], feedback[1] = feedback[1], feedback[0]
    elif change in ("duplicate_run", "duplicate_dispatch"):
        key = "task_ref" if change == "duplicate_run" else "dispatch_ref"
        request["expected"]["rounds"][2][key] = request["expected"]["rounds"][1][key]
    elif change == "duplicate_event":
        middle["events"][0]["uuid"] = feedback[0]["events"][0]["uuid"]
    elif change == "missing_ack":
        del middle["delivery"]["tool_use_result"]
    elif change == "changed_prefix":
        middle["public_history"]["child"][1]["message"]["content"][0]["thinking"] += (
            " edited"
        )
    elif change == "truncated_prefix":
        middle["public_history"]["child"].pop(1)
    elif change == "changed_middle_model":
        middle["forwarded_result"]["message"]["model"] = "wrong-model"
    elif change == "pending_middle":
        middle["events"][2]["patch"]["status"] = "running"
    elif change == "superseded_middle":
        middle["public_history"]["child"][-1]["supersedes"] = "old-result"
    elif change == "orphan_assignment":
        child = middle["public_history"]["child"]
        child.insert(-1, {**copy.deepcopy(child[-2]), "uuid": "orphan-user"})
    output = mapping.map_delivery(request)
    assert output["state"] in ("rejected", "reconciliation_required")
    assert "mapped" not in output and output["redispatch_allowed"] is False


def add_claude_tool_pair(request, name="Read"):
    record = request["records"]["feedback"][0]
    child = record["public_history"]["child"]
    invocation = copy.deepcopy(child[-1])
    invocation["uuid"] = "child-tool-use"
    invocation["message"].update(
        id="child-tool-message",
        stop_reason="tool_use",
        content=[
            {
                "type": "tool_use",
                "id": "inner-tool",
                "name": name,
                "input": {"prompt": "Original nested assignment\r\n"}
                if name == "Agent"
                else {"file_path": "/exact/source"},
            }
        ],
    )
    reply = copy.deepcopy(child[-2])
    reply["uuid"] = "child-tool-reply"
    reply["message"]["content"] = [
        {
            "type": "tool_result",
            "tool_use_id": "inner-tool",
            "content": [{"type": "text", "text": "Complete original tool result\r\n"}],
            "opaque_extension": {"native": True},
        }
    ]
    child[-1:-1] = [invocation, reply]
    return invocation, reply


def test_claude_lifetime_tool_results_do_not_become_assignments(
    claude_feedback_request,
):
    request = extend_claude_lifetime(claude_feedback_request, 2)
    add_claude_tool_pair(request)
    output = mapping.map_delivery(request)
    assert output["state"] == "delivery_mapped", output
    assert output["mapped"]["observed_round_count"] == 2
    assert (
        output["mapped"]["rounds"][-1]["result_domain"]["result"][
            "public_child_messages"
        ]
        == request["records"]["feedback"][0]["public_history"]["child"][3:]
    )
    assert output["acceptance_ready"] is False


@pytest.mark.parametrize(
    "change",
    [
        "missing_reply",
        "wrong_id",
        "duplicate_use",
        "orphan_reply",
        "pending",
        "incomplete",
        "nested_without_output",
    ],
)
def test_claude_lifetime_requires_complete_correlated_tool_delivery(
    claude_feedback_request, change
):
    request = extend_claude_lifetime(claude_feedback_request, 2)
    invocation, reply = add_claude_tool_pair(
        request, "Agent" if change == "nested_without_output" else "Read"
    )
    child = request["records"]["feedback"][0]["public_history"]["child"]
    if change == "missing_reply":
        child.remove(reply)
    elif change == "wrong_id":
        reply["message"]["content"][0]["tool_use_id"] = "wrong-tool"
    elif change == "duplicate_use":
        invocation["message"]["content"].append(
            copy.deepcopy(invocation["message"]["content"][0])
        )
    elif change == "orphan_reply":
        child.remove(invocation)
    elif change == "pending":
        child[-1]["message"]["stop_reason"] = "pause_turn"
    elif change == "incomplete":
        del reply["message"]["content"][0]["content"]
    output = mapping.map_delivery(request)
    assert output["state"] in ("rejected", "reconciliation_required")
    assert "mapped" not in output


def test_claude_lifetime_keeps_original_nested_agent_output(claude_feedback_request):
    request = extend_claude_lifetime(claude_feedback_request, 2)
    invocation, reply = add_claude_tool_pair(request, "Agent")
    native_reply = copy.deepcopy(reply)
    output = copy.deepcopy(request["records"]["initial"]["delivery"]["tool_use_result"])
    output.update(
        agentId="nested-agent",
        prompt="Original nested assignment\r\n",
        extension={"unmodified": [1, 2]},
    )
    native_reply["tool_use_result"] = output
    request["records"]["feedback"][0]["nested_deliveries"] = [
        {"invocation": copy.deepcopy(invocation), "delivery": native_reply}
    ]
    mapped = mapping.map_delivery(request)
    assert mapped["state"] == "delivery_mapped", mapped
    assert (
        mapped["mapped"]["rounds"][-1]["result_domain"]["result"]["nested_deliveries"][
            0
        ]["delivery"]["tool_use_result"]
        == output
    )
    assert mapped["acceptance_ready"] is False


@pytest.mark.parametrize(
    "change",
    [
        "missing_output",
        "missing_model",
        "changed_uuid",
        "changed_result",
        "duplicate_record",
        "malformed_invocation",
        "malformed_delivery",
        "wrong_ancestry",
    ],
)
def test_claude_lifetime_nested_original_output_cannot_be_reconstructed_or_misattributed(
    claude_feedback_request, change
):
    request = extend_claude_lifetime(claude_feedback_request, 2)
    invocation, reply = add_claude_tool_pair(request, "Agent")
    output = copy.deepcopy(request["records"]["initial"]["delivery"]["tool_use_result"])
    output.update(agentId="nested-agent", prompt="Original nested assignment\r\n")
    native_reply = {**copy.deepcopy(reply), "tool_use_result": output}
    nested = {"invocation": copy.deepcopy(invocation), "delivery": native_reply}
    request["records"]["feedback"][0]["nested_deliveries"] = [nested]
    if change == "missing_output":
        del native_reply["tool_use_result"]
    elif change == "missing_model":
        del output["resolvedModel"]
    elif change == "changed_uuid":
        native_reply["uuid"] = "wrong-original-source"
    elif change == "changed_result":
        native_reply["message"]["content"][0]["content"] = (
            "Projected wrapper instead of original result"
        )
    elif change == "duplicate_record":
        request["records"]["feedback"][0]["nested_deliveries"].append(
            copy.deepcopy(nested)
        )
    elif change == "malformed_invocation":
        nested["invocation"] = None
    elif change == "malformed_delivery":
        nested["delivery"] = []
    elif change == "wrong_ancestry":
        native_reply["parent_tool_use_id"] = "another-parent-invocation"
    result = mapping.map_delivery(request)
    assert result["state"] in ("rejected", "reconciliation_required")
    assert "mapped" not in result


def make_hook_request(initial_output, inputs, *, nested=False):
    """Synthetic native hook/stream/read projections; never runtime qualification."""
    scope, worker = "session-1", "agent-1"
    forwarded, public, rounds, expected = [], [], [], []
    initial_output = copy.deepcopy(initial_output)
    initial_output.update(
        agentId=worker,
        prompt=inputs[0],
        resolvedModel="native-model",
        totalToolUseCount=1,
    )

    def message(uuid, kind, content, stamp, *, stop=None):
        body = {"role": kind, "content": content}
        if kind == "assistant":
            body.update(id="message-" + uuid, model="native-model", stop_reason=stop)
        return {
            "type": kind,
            "uuid": uuid,
            "session_id": scope,
            "agent_id": worker,
            "parent_tool_use_id": "hook-0",
            "timestamp": stamp,
            "message": body,
        }

    def operation(
        index, name, arguments, response, *, agent=None, invocation=None, tool_id=None
    ):
        tool = tool_id or "hook-" + str(index)
        requested = {
            **arguments,
            "prompt" if name == "Agent" else "message": "model placeholder",
        }
        invocation = invocation or message(
            "invocation-" + str(index),
            "assistant",
            [{"type": "tool_use", "id": tool, "name": name, "input": requested}],
            f"2026-01-01T00:0{index}:00.000Z",
        )
        if agent is None:
            invocation["parent_tool_use_id"] = None
            invocation.pop("agent_id")
        context = {
            "session_id": scope,
            "hook_event_name": "PreToolUse",
            "tool_name": name,
            "tool_input": copy.deepcopy(requested),
            "tool_use_id": tool,
            "prompt_id": "prompt-" + str(index),
            "cwd": "/fixture",
            "transcript_path": "/fixture/transcript",
            "permission_mode": "default",
            "effort": {"level": "medium"},
        }
        if agent is not None:
            context["agent_id"] = agent
        pre = {
            "at": f"2026-01-01T00:0{index}:00.001Z",
            "toolUseID": tool,
            "input": context,
            "output": {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "updatedInput": arguments,
                }
            },
        }
        post = {
            "at": f"2026-01-01T00:0{index}:00.010Z",
            "toolUseID": tool,
            "input": {
                **context,
                "hook_event_name": "PostToolUse",
                "tool_input": arguments,
                "tool_response": response,
                "duration_ms": 9,
            },
        }
        if index == 0:
            post["at"] = "2026-01-01T00:00:10.000Z"
        return {"invocation": invocation, "pre_hook": pre, "post_hook": post}

    for index, text in enumerate(inputs):
        tool, run = "hook-" + str(index), "run-" + str(index)
        arguments = (
            {
                "description": "fixture",
                "prompt": text,
                "subagent_type": "general-purpose",
                "run_in_background": False,
            }
            if index == 0
            else {"to": worker, "message": text, "summary": "fixture"}
        )
        response = (
            initial_output
            if index == 0
            else {"success": True, "resumedAgentId": worker}
        )
        record = operation(
            index, "Agent" if index == 0 else "SendMessage", arguments, response
        )
        expected.append({"dispatch_ref": tool, "task_ref": run, "input": text})
        assignment = message(
            "assignment-" + str(index), "user", text, f"2026-01-01T00:0{index}:01.000Z"
        )
        public.append(assignment)
        if index == 0:
            raw_assignment = copy.deepcopy(assignment)
            raw_assignment["message"]["content"] = [{"type": "text", "text": text}]
            forwarded.append(raw_assignment)
            use = message(
                "read-use",
                "assistant",
                [
                    {
                        "type": "tool_use",
                        "id": "read-1",
                        "name": "Read",
                        "input": {"file_path": "/fixture/evidence"},
                    }
                ],
                "2026-01-01T00:00:02.000Z",
            )
            reply = message(
                "read-reply",
                "user",
                [
                    {
                        "type": "tool_result",
                        "tool_use_id": "read-1",
                        "content": "complete original",
                    }
                ],
                "2026-01-01T00:00:03.000Z",
            )
            forwarded.extend([use, reply])
            public.append(copy.deepcopy(use))
        nested_deliveries = []
        if nested and index == 2:
            nested_args = {
                "description": "nested",
                "prompt": "original nested task",
                "subagent_type": "general-purpose",
                "run_in_background": False,
            }
            nested_response = copy.deepcopy(initial_output)
            nested_response.update(
                agentId="nested-agent",
                prompt=nested_args["prompt"],
                content=[{"type": "text", "text": '{"sum":42}'}],
                totalToolUseCount=0,
            )
            nested_requested = {**nested_args, "prompt": "model placeholder"}
            nested_invocation = message(
                "nested-invocation",
                "assistant",
                [
                    {
                        "type": "tool_use",
                        "id": "nested-hook",
                        "name": "Agent",
                        "input": nested_requested,
                    }
                ],
                "2026-01-01T00:02:02.000Z",
            )
            nested_operation = operation(
                2,
                "Agent",
                nested_args,
                nested_response,
                agent=worker,
                invocation=nested_invocation,
                tool_id="nested-hook",
            )
            nested_operation["pre_hook"]["at"] = "2026-01-01T00:02:02.001Z"
            nested_operation["post_hook"]["at"] = "2026-01-01T00:02:03.000Z"
            reply = message(
                "nested-reply",
                "user",
                [
                    {
                        "type": "tool_result",
                        "tool_use_id": "nested-hook",
                        "content": '[native handback] {"sum":42}',
                    }
                ],
                "2026-01-01T00:02:03.001Z",
            )
            forwarded.extend([nested_invocation, reply])
            public.extend(copy.deepcopy([nested_invocation, reply]))
            nested_deliveries = [nested_operation]
        result_content = (
            initial_output["content"]
            if index == 0
            else [{"type": "text", "text": "result-" + str(index)}]
        )
        terminal = message(
            "terminal-" + str(index),
            "assistant",
            result_content,
            f"2026-01-01T00:0{index}:09.000Z",
            stop="end_turn",
        )
        public.append(terminal)
        if index:
            raw_terminal = copy.deepcopy(terminal)
            raw_terminal["message"]["stop_reason"] = None
            forwarded.append(raw_terminal)
        record.update(
            events=[
                {
                    "type": "system",
                    "subtype": "task_started",
                    "uuid": "started-" + str(index),
                    "session_id": scope,
                    "task_id": worker,
                    "run_id": run,
                    "tool_use_id": tool,
                    "prompt": text,
                    "is_backgrounded": bool(index),
                    "spawn_depth": 1,
                    "task_type": "local_agent",
                    "subagent_type": "general-purpose",
                },
                {
                    "type": "system",
                    "subtype": "task_updated",
                    "uuid": "updated-" + str(index),
                    "session_id": scope,
                    "task_id": worker,
                    "run_id": run,
                    "patch": {
                        "status": "completed",
                        "end_time": 1767225609000 + index * 60000,
                    },
                },
                {
                    "type": "system",
                    "subtype": "task_notification",
                    "uuid": "notified-" + str(index),
                    "session_id": scope,
                    "task_id": worker,
                    "run_id": run,
                    "tool_use_id": tool,
                    "status": "completed",
                    "output_file": "/fixture/output",
                    "summary": "".join(block["text"] for block in result_content),
                    "usage": {"tool_uses": 0},
                },
            ],
            forwarded_history=copy.deepcopy(forwarded),
            nested_deliveries=nested_deliveries,
        )
        if index:
            record["public_history"] = {
                "session_id": scope,
                "target": worker,
                "agents": [worker],
                "children": {worker: copy.deepcopy(public)},
                "primary": [],
            }
        rounds.append(record)
    return {
        "schema": mapping.REQUEST_SCHEMA,
        "profile": mapping.CLAUDE_HOOKS_PROFILE,
        "expected": {
            "scope_ref": scope,
            "supervisor_ref": scope,
            "worker_ref": worker,
            "rounds": expected,
        },
        "records": {"rounds": rounds},
    }


@pytest.fixture
def hooks_request(claude_request):
    return make_hook_request(
        claude_request["records"]["delivery"]["tool_use_result"],
        ["initial exact\r\n", "second exact\n", "third exact\n", "fourth exact\n"],
    )


def test_hook_profile_preserves_requested_effective_inputs_and_original_projections(
    hooks_request,
):
    original = copy.deepcopy(hooks_request)
    result = mapping.map_delivery(hooks_request)
    assert result["state"] == "delivery_mapped"
    assert hooks_request == original
    assert result["acceptance_ready"] is False and result["redispatch_allowed"] is False
    for expected, record, bound in zip(
        hooks_request["expected"]["rounds"],
        hooks_request["records"]["rounds"],
        result["mapped"]["rounds"],
    ):
        assert bound["task_ref"] == expected["task_ref"]
        assert (
            bound["accepted_task_domain"]["input"]
            == record["post_hook"]["input"]["tool_input"]
        )
        assert bound["result_domain"]["result"]["operation"] == record
        assert bound["result_digest"] == mapping.digest(bound["result_domain"])
    assert (
        hooks_request["records"]["rounds"][1]["public_history"]["children"]["agent-1"][
            0
        ]["message"]["content"]
        == "initial exact\r\n"
    )
    assert (
        hooks_request["records"]["rounds"][0]["forwarded_history"][-1]["uuid"]
        == "read-reply"
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing-post",
        "requested-input",
        "effective-input",
        "callback-input",
        "wrong-worker",
        "run",
        "pending",
        "forwarded-prefix",
        "public-prefix",
        "tool-reply",
        "reused-terminal",
        "round-omitted",
        "round-reordered",
        "nested-omitted",
        "early-dispatch",
        "missing-completion-time",
    ],
)
def test_hook_profile_reconciles_missing_or_mismatched_native_operations(
    hooks_request, change
):
    records = hooks_request["records"]["rounds"]
    if change == "missing-post":
        del records[1]["post_hook"]
    elif change == "requested-input":
        records[1]["pre_hook"]["input"]["tool_input"]["message"] = "different"
    elif change == "effective-input":
        records[1]["post_hook"]["input"]["tool_input"]["message"] = "different"
    elif change == "callback-input":
        records[1]["pre_hook"]["output"]["hookSpecificOutput"]["updatedInput"][
            "message"
        ] = "different"
    elif change == "wrong-worker":
        records[1]["post_hook"]["input"]["tool_response"]["resumedAgentId"] = "other"
    elif change == "run":
        records[1]["events"][1]["run_id"] = "other"
    elif change == "pending":
        records[1]["events"][1]["patch"]["status"] = "running"
    elif change == "forwarded-prefix":
        records[1]["forwarded_history"][0]["message"]["content"][0]["text"] = "changed"
    elif change == "public-prefix":
        records[2]["public_history"]["children"]["agent-1"][0]["message"]["content"] = (
            "changed"
        )
    elif change == "tool-reply":
        records[0]["forwarded_history"].pop()
    elif change == "reused-terminal":
        records[2]["public_history"]["children"]["agent-1"][-1] = copy.deepcopy(
            records[1]["public_history"]["children"]["agent-1"][-1]
        )
    elif change == "round-omitted":
        records.pop(1)
    elif change == "round-reordered":
        records[1], records[2] = records[2], records[1]
    elif change == "early-dispatch":
        records[1]["pre_hook"]["at"] = records[0]["pre_hook"]["at"]
    elif change == "missing-completion-time":
        del records[1]["events"][1]["patch"]["end_time"]
    else:
        records[1]["nested_deliveries"].append({})
    result = mapping.map_delivery(hooks_request)
    assert result["state"] in ("rejected", "reconciliation_required")
    assert result["redispatch_allowed"] is False and result["acceptance_ready"] is False


def codex_v2_records(request):
    request["profile"] = mapping.CODEX_ROUNDS_V2_PROFILE
    request["records"]["initial"]["child_read"]["thread"]["cliVersion"] = "0.162.1"
    for record in request["records"]["feedback"]:
        for key in ("before_child_read", "after_child_read"):
            record[key]["thread"]["cliVersion"] = "0.162.1"
    return request


def test_codex_v2_keeps_original_supported_alias_and_new_digest_domains(
    serialized_request,
):
    request = codex_v2_records(serialized_request)
    path = request["records"]["initial"]["journal"]["response"]["task_name"]
    request["records"]["feedback"][0]["request"]["target"] = path.rsplit("/", 1)[-1]
    original = copy.deepcopy(request)
    output = mapping.map_delivery(request)
    assert output["state"] == "delivery_mapped"
    assert request == original
    assert (
        output["mapped"]["rounds"][0]["accepted_task_domain"]["profile"]
        == mapping.CODEX_SPAWN_V2_PROFILE
    )
    assert (
        output["mapped"]["rounds"][1]["accepted_task_domain"]["profile"]
        == mapping.CODEX_ROUNDS_V2_PROFILE
    )
    assert (
        output["mapped"]["rounds"][1]["accepted_task_domain"]["input"]["target"]
        == path.rsplit("/", 1)[-1]
    )
    assert output["redispatch_allowed"] is False and output["acceptance_ready"] is False


@pytest.mark.parametrize(
    "change",
    [
        "legacy-profile",
        "child-version",
        "parent-version",
        "other-alias",
        "noncanonical-alias",
        "changed-native-path",
    ],
)
def test_codex_v2_cannot_admit_unqualified_versions_or_aliases(
    serialized_request, change
):
    request = codex_v2_records(serialized_request)
    record = request["records"]["feedback"][0]
    if change == "legacy-profile":
        request["profile"] = mapping.CODEX_ROUNDS_PROFILE
    elif change == "child-version":
        record["after_child_read"]["thread"]["cliVersion"] = "0.162.0"
    elif change == "parent-version":
        record["after_parent_read"]["thread"]["cliVersion"] = "0.162.1"
    elif change == "other-alias":
        record["request"]["target"] = "other_agent"
    elif change == "noncanonical-alias":
        record["request"]["target"] = "../native_worker"
    else:
        record["after_child_read"]["thread"]["source"]["subAgent"]["thread_spawn"][
            "agent_path"
        ] = "/root/other"
    output = mapping.map_delivery(request)
    assert output["state"] in ("rejected", "reconciliation_required")
    assert output["redispatch_allowed"] is False


def test_hook_nested_agent_retains_original_complete_output(claude_request):
    request = make_hook_request(
        claude_request["records"]["delivery"]["tool_use_result"],
        ["initial", "second", "third", "fourth"],
        nested=True,
    )
    output = mapping.map_delivery(request)
    assert output["state"] == "delivery_mapped"
    original = request["records"]["rounds"][2]["nested_deliveries"][0]
    assert output["mapped"]["rounds"][2]["result_domain"]["result"]["operation"][
        "nested_deliveries"
    ] == [original]
    original["post_hook"]["input"]["tool_response"]["content"][0]["text"] = (
        "reconstructed summary"
    )
    assert mapping.map_delivery(request)["state"] in (
        "rejected",
        "reconciliation_required",
    )


@pytest.mark.parametrize(
    "change",
    [None, "missing-projection", "changed-request", "wrong-time", "wrong-event"],
)
def test_hook_collector_envelope_preserves_originals_and_native_dispatch_clock(
    hooks_request, change
):
    record = hooks_request["records"]["rounds"][-1]
    projection = copy.deepcopy(record["invocation"])
    projection["timestamp"] = record["invocation"]["timestamp"]
    projection["message"]["stop_reason"] = "tool_use"
    record["invocation_projection"] = projection
    for key, event in (("pre_hook", "PreToolUse"), ("post_hook", "PostToolUse")):
        old = record[key]
        record[key] = {
            "event": event,
            "toolUseId": old["toolUseID"],
            "input": old["input"],
            "callbackOutput": old.get("output", {}),
        }
    record["pre_hook"]["allowed"] = True
    if change == "missing-projection":
        del record["invocation_projection"]
    elif change == "changed-request":
        projection["message"]["content"][0]["input"]["message"] = "changed"
    elif change == "wrong-time":
        projection["timestamp"] = hooks_request["records"]["rounds"][0]["pre_hook"][
            "at"
        ]
    elif change == "wrong-event":
        record["pre_hook"]["event"] = "PostToolUse"
    original = copy.deepcopy(hooks_request)
    result = mapping.map_delivery(hooks_request)
    assert hooks_request == original
    if change is None:
        assert result["state"] == "delivery_mapped"
    else:
        assert result["state"] in ("rejected", "reconciliation_required")
    assert result["acceptance_ready"] is False


@pytest.mark.parametrize("record", ["parent_read", "child_read"])
@pytest.mark.parametrize("field", ["historyMode", "itemsView"])
def test_codex_missing_history_metadata_requires_reconciliation(
    codex_request, record, field
):
    native_thread = codex_request["records"][record]["thread"]
    if field == "historyMode":
        del native_thread[field]
    else:
        for turn in native_thread["turns"]:
            del turn[field]
    output = mapping.map_delivery(codex_request)
    assert output["state"] == "reconciliation_required"
    assert output["error"]["code"] == "INCOMPLETE_HISTORY"
    assert output["acceptance_ready"] is False
    assert output["redispatch_allowed"] is False
