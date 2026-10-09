"""Map supplied public native records without dispatching or accepting work.

Input: aquarium.native-delivery-request/v1 with profile, expected, and records.
Expected contains scope_ref, supervisor_ref, worker_ref, and ordered rounds
(dispatch_ref, task_ref, input). Codex records contain parent_read and child_read
ThreadReadResponse objects from complete legacy thread/read(includeTurns=true).
Claude records contain one SDK assistant invocation and one SDK user delivery
with its structured AgentOutput; only synchronous initial Agent calls are mapped.
The collaboration-spawn profile instead joins a pre-dispatch client journal
(exact request and successful response) with public started activity and one
complete initial child turn. It does not require an input echo. Journal capture
ordering and authenticity remain the collector's responsibility; historical
records without the original request/response cannot reconstruct this proof.
The collaboration-rounds profile preserves that complete initial snapshot and
maps ordered feedback journals only from observed idle workers, unchanged full
child history, captured tool completion output, and unique subsequent delivery.
Per-round preparations are integration data verified separately by the binder.

The mapper checks correlation, not record authenticity. Preserve the original
request for recovery. All digests hash compact sorted-key ASCII JSON without a
newline. Task digests cover the exact native input and identities; result digests
cover complete delivered native messages/output and the accepted-task digest.
Neither a mapped delivery nor a completed native task proves accepted role
configuration, Primary acceptance, complete lifetime accounting, or settlement.
No output is a Podway acceptance document or a qualified execution mapping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

REQUEST_SCHEMA = "aquarium.native-delivery-request/v1"
OUTPUT_SCHEMA = "aquarium.native-delivery-mapping/v1"
CODEX_PROFILE = "aquarium.codex-app-server-delivery/v1"
CLAUDE_PROFILE = "aquarium.claude-agent-sdk-delivery/v1"
CLAUDE_ROUNDS_PROFILE = "aquarium.claude-agent-sdk-rounds-delivery/v1"
CODEX_SPAWN_PROFILE = "aquarium.codex-collaboration-spawn-delivery/v1"
CODEX_ROUNDS_PROFILE = "aquarium.codex-collaboration-rounds-delivery/v1"


class MappingError(ValueError):
    """Rejected or incomplete public record; never permission to redispatch."""

    def __init__(self, code: str, message: str, *, reconcile: bool = False):
        super().__init__(message)
        self.code = code
        self.reconcile = reconcile


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require(condition: bool, code: str, message: str, *, reconcile=False) -> None:
    if not condition:
        raise MappingError(code, message, reconcile=reconcile)


def _object(value: Any, keys: set[str], name: str, *, closed=False) -> dict:
    _require(
        isinstance(value, dict)
        and (set(value) == keys if closed else keys <= set(value)),
        "REQUIRED_METADATA_MISSING",
        f"{name} requires {', '.join(sorted(keys))}",
    )
    return value


def _text(value: Any, name: str) -> str:
    _require(
        isinstance(value, str) and bool(value.strip()),
        "REQUIRED_METADATA_MISSING",
        f"{name} must be a nonempty string",
    )
    return value


def _list(value: Any, name: str) -> list:
    _require(isinstance(value, list), "INVALID_RECORD", f"{name} must be a list")
    return value


def _unique(records: list, name: str, key="id") -> None:
    ids = [_text(_object(item, {key}, name)[key], f"{name}.{key}") for item in records]
    _require(len(set(ids)) == len(ids), "AMBIGUOUS_IDENTITY", f"duplicate {name} IDs")


def _expected(request: dict) -> dict:
    expected = _object(
        request["expected"],
        {"scope_ref", "supervisor_ref", "worker_ref", "rounds"},
        "expected",
        closed=True,
    )
    for key in ("scope_ref", "supervisor_ref", "worker_ref"):
        _text(expected[key], f"expected.{key}")
    rounds = _list(expected["rounds"], "expected.rounds")
    _require(bool(rounds), "INVALID_REQUEST", "at least one expected round is required")
    for entry in rounds:
        _object(entry, {"dispatch_ref", "task_ref", "input"}, "round", closed=True)
        for key in entry:
            _text(entry[key], f"round.{key}")
    _unique(rounds, "round dispatch", "dispatch_ref")
    _unique(rounds, "round task", "task_ref")
    return expected


def _codex_thread(
    response: Any, expected: dict, key: str, *, journal_spawn: bool = False
) -> dict:
    thread = _object(
        _object(response, {"thread"}, key)["thread"],
        {"id", "sessionId", "turns", "ephemeral", "cliVersion", "status"},
        key,
    )
    _require(
        thread["cliVersion"] == "0.162.0",
        "UNSUPPORTED_SURFACE",
        "Codex profile requires CLI 0.162.0 records",
    )
    _require(
        thread["id"] == expected[key] and thread["sessionId"] == expected["scope_ref"],
        "IDENTITY_MISMATCH",
        f"{key} identity differs from the expected scope",
    )
    _require(
        thread["ephemeral"] is False,
        "UNSUPPORTED_SURFACE",
        "ephemeral records cannot provide durable recovery",
    )
    _object(thread["status"], {"type"}, f"{key}.status")
    _require(
        thread.get("historyMode", "legacy") in ("legacy", "paginated")
        if journal_spawn
        else thread.get("historyMode", "legacy") == "legacy",
        "INCOMPLETE_HISTORY",
        "paginated history must be collected by a separate supported mapper",
        reconcile=True,
    )
    turns = _list(thread["turns"], f"{key}.turns")
    _unique(turns, f"{key} turn")
    items = []
    for turn in turns:
        _object(turn, {"id", "status", "items"}, "turn")
        _require(
            turn.get("itemsView", None if journal_spawn else "full") == "full",
            "INCOMPLETE_HISTORY",
            "summary or unloaded turn items require reconciliation",
            reconcile=True,
        )
        items.extend(_list(turn["items"], "turn.items"))
    _unique(items, f"{key} item")
    return thread


def _round(
    profile: str,
    scope: str,
    worker: str,
    dispatch: str,
    task: str,
    native_input: Any,
    native_result: Any,
    result_refs: list[str],
) -> dict:
    task_domain = {
        "schema": "aquarium.native-task-domain/v1",
        "profile": profile,
        "scope_ref": scope,
        "worker_ref": worker,
        "dispatch_ref": dispatch,
        "task_ref": task,
        "input": native_input,
    }
    task_digest = digest(task_domain)
    result_digest = digest(
        {
            "schema": "aquarium.native-result-domain/v1",
            "profile": profile,
            "accepted_task_digest": task_digest,
            "result": native_result,
        }
    )
    return {
        "dispatch_ref": dispatch,
        "task_ref": task,
        "result_refs": result_refs,
        "accepted_task_domain": task_domain,
        "accepted_task_digest": task_digest,
        "result_digest": result_digest,
    }


def _codex(expected: dict, records: dict) -> dict:
    _object(records, {"parent_read", "child_read"}, "records", closed=True)
    parent = _codex_thread(records["parent_read"], expected, "supervisor_ref")
    child = _codex_thread(records["child_read"], expected, "worker_ref")
    source = _object(child.get("source"), {"subAgent"}, "child.source")
    spawn = _object(
        _object(source["subAgent"], {"thread_spawn"}, "child.source.subAgent")[
            "thread_spawn"
        ],
        {"parent_thread_id", "depth"},
        "thread_spawn",
    )
    _require(
        child.get("parentThreadId") == parent["id"]
        and spawn["parent_thread_id"] == parent["id"],
        "IDENTITY_MISMATCH",
        "child parent provenance does not match supervisor",
    )
    _require(
        type(spawn["depth"]) is int and spawn["depth"] > 0,
        "INVALID_RECORD",
        "child spawn depth must be a positive integer",
    )
    calls = []
    for turn in parent["turns"]:
        for item in turn["items"]:
            if item.get("type") != "collabAgentToolCall":
                continue
            receivers = _list(item.get("receiverThreadIds"), "receiverThreadIds")
            if child["id"] not in receivers:
                continue
            _object(item, {"senderThreadId", "tool", "status"}, "collab call")
            _text(item["tool"], "collab tool")
            _require(
                item["senderThreadId"] == parent["id"],
                "IDENTITY_MISMATCH",
                "collab sender differs from supervisor",
            )
            _require(
                item["status"] == "completed",
                "UNCERTAIN_OPERATION",
                "an unsettled collab call requires native reconciliation",
                reconcile=True,
            )
            if item["tool"] in {"spawnAgent", "sendInput"}:
                _require(
                    receivers == [child["id"]],
                    "AMBIGUOUS_IDENTITY",
                    "assignment must target exactly one worker",
                )
                calls.append(item)
            elif item["tool"] not in {"wait", "listAgents"}:
                raise MappingError(
                    "UNSUPPORTED_OPERATION",
                    "feedback or lifecycle operation lacks a qualified mapping",
                    reconcile=True,
                )
    rounds = expected["rounds"]
    _require(
        [item["id"] for item in calls] == [entry["dispatch_ref"] for entry in rounds],
        "ROUND_BINDING_MISMATCH",
        "expected dispatch rounds do not exhaust worker assignment calls",
    )
    _require(
        bool(calls)
        and calls[0]["tool"] == "spawnAgent"
        and all(item["tool"] == "sendInput" for item in calls[1:]),
        "ROUND_BINDING_MISMATCH",
        "rounds must begin with one spawn followed by sendInput calls",
    )
    _require(
        [turn["id"] for turn in child["turns"]]
        == [entry["task_ref"] for entry in rounds],
        "ROUND_BINDING_MISMATCH",
        "expected task rounds do not exhaust child turns",
    )
    mapped = []
    for entry, call, turn in zip(rounds, calls, child["turns"], strict=True):
        _require(
            call.get("prompt") == entry["input"],
            "INPUT_MISMATCH",
            "dispatch prompt differs from expected exact input",
        )
        _require(
            turn["status"] == "completed" and turn.get("error") is None,
            "INCOMPLETE_RESULT",
            "child turn has no successful complete delivery",
            reconcile=True,
        )
        user = [item for item in turn["items"] if item.get("type") == "userMessage"]
        _require(
            len(user) == 1,
            "AMBIGUOUS_INPUT",
            "each supported round requires exactly one persisted user input",
        )
        content = _list(user[0].get("content"), "userMessage.content")
        _require(
            len(content) == 1
            and isinstance(content[0], dict)
            and content[0].get("type") == "text"
            and content[0].get("text") == entry["input"]
            and content[0].get("text_elements", []) == [],
            "INPUT_MISMATCH",
            "persisted input must be the exact complete text-only dispatch",
        )
        final = [
            item
            for item in turn["items"]
            if item.get("type") == "agentMessage"
            and item.get("phase") == "final_answer"
        ]
        _require(
            bool(final),
            "INCOMPLETE_RESULT",
            "complete final-answer messages are required",
            reconcile=True,
        )
        for item in final:
            _text(item.get("text"), "final answer text")
            _require(
                item.get("delivery") is None,
                "UNSUPPORTED_OPERATION",
                "async delivery requires a separate acknowledgement mapping",
                reconcile=True,
            )
        _require(
            turn["items"][-1]["id"] == final[-1]["id"],
            "INCOMPLETE_RESULT",
            "final answer must close the completed turn",
            reconcile=True,
        )
        mapped.append(
            _round(
                CODEX_PROFILE,
                expected["scope_ref"],
                child["id"],
                call["id"],
                turn["id"],
                content,
                final,
                [item["id"] for item in final],
            )
        )
    status = _object(child["status"], {"type"}, "child.status")
    _require(
        status["type"] in ("notLoaded", "idle", "systemError", "active"),
        "INVALID_RECORD",
        "unsupported native thread status",
    )
    return {"rounds": mapped, "reported_worker_status": status["type"]}


def _claude(expected: dict, records: dict) -> dict:
    _object(records, {"invocation", "delivery"}, "records", closed=True)
    _require(
        len(expected["rounds"]) == 1
        and expected["supervisor_ref"] == expected["scope_ref"],
        "UNSUPPORTED_OPERATION",
        "Claude profile supports one synchronous initial Agent invocation in its Primary session",
    )
    entry = expected["rounds"][0]
    _require(
        entry["task_ref"] == entry["dispatch_ref"],
        "IDENTITY_MISMATCH",
        "Claude initial assignment task identity is its native tool-use ID",
    )
    invocation = _object(
        records["invocation"],
        {"type", "session_id", "uuid", "message", "parent_tool_use_id"},
        "invocation",
    )
    delivery = _object(
        records["delivery"],
        {
            "type",
            "session_id",
            "uuid",
            "message",
            "parent_tool_use_id",
            "tool_use_result",
        },
        "delivery",
    )
    _require(
        invocation["type"] == "assistant"
        and delivery["type"] == "user"
        and invocation["session_id"] == delivery["session_id"] == expected["scope_ref"]
        and invocation["parent_tool_use_id"] is None
        and delivery["parent_tool_use_id"] is None,
        "IDENTITY_MISMATCH",
        "SDK records must belong to the same actual Primary session",
    )
    for record in (invocation, delivery):
        _text(record["uuid"], "SDK message uuid")
        _require(
            not record.get("error")
            and not record.get("aborted")
            and not record.get("supersedes"),
            "INCOMPLETE_RESULT",
            "errored, interrupted or superseding records require reconciliation",
            reconcile=True,
        )
    _require(
        invocation["uuid"] != delivery["uuid"],
        "AMBIGUOUS_IDENTITY",
        "invocation and delivery must have distinct native message IDs",
    )
    message = _object(
        invocation["message"],
        {"id", "role", "content", "stop_reason"},
        "assistant message",
    )
    _require(
        message["role"] == "assistant" and message["stop_reason"] in ("tool_use", None),
        "INCOMPLETE_RESULT",
        "Agent invocation requires tool_use or null stop_reason and a correlated complete output",
        reconcile=True,
    )
    uses = [
        item
        for item in _list(message["content"], "invocation content")
        if isinstance(item, dict) and item.get("type") == "tool_use"
    ]
    _require(
        len(uses) == 1,
        "AMBIGUOUS_IDENTITY",
        "structured Agent output requires exactly one invocation tool-use",
    )
    use = _object(uses[0], {"id", "name", "input"}, "tool_use")
    _require(
        use["id"] == entry["dispatch_ref"] and use["name"] == "Agent",
        "IDENTITY_MISMATCH",
        "Agent tool-use identity differs from the expected dispatch",
    )
    native_input = _object(use["input"], {"prompt"}, "Agent input")
    _require(
        native_input["prompt"] == entry["input"],
        "INPUT_MISMATCH",
        "Agent prompt differs from expected exact input",
    )
    _require(
        not native_input.get("run_in_background"),
        "UNSUPPORTED_OPERATION",
        "background Agent delivery requires task-event and history reconciliation",
        reconcile=True,
    )
    result_message = _object(
        delivery["message"], {"role", "content"}, "delivery message"
    )
    results = _list(result_message["content"], "delivery content")
    _require(
        result_message["role"] == "user"
        and len(results) == 1
        and isinstance(results[0], dict)
        and results[0].get("type") == "tool_result"
        and results[0].get("tool_use_id") == use["id"]
        and not results[0].get("is_error"),
        "IDENTITY_MISMATCH",
        "Agent delivery must correlate one successful tool result",
    )
    output = _object(
        delivery["tool_use_result"],
        {"agentId", "prompt", "status", "content"},
        "AgentOutput",
    )
    _require(
        output["status"] == "completed",
        "INCOMPLETE_RESULT",
        "AgentOutput must contain complete synchronous delivery",
        reconcile=True,
    )
    _object(
        output,
        {"totalToolUseCount", "totalDurationMs", "totalTokens", "usage"},
        "complete AgentOutput",
    )
    for key in ("totalToolUseCount", "totalTokens"):
        _require(
            type(output[key]) is int and output[key] >= 0,
            "INVALID_RECORD",
            f"{key} must be an unsigned integer",
        )
    duration = output["totalDurationMs"]
    _require(
        type(duration) in (int, float)
        and duration >= 0
        and (type(duration) is int or math.isfinite(duration)),
        "INVALID_RECORD",
        "totalDurationMs must be a finite nonnegative number",
    )
    _object(
        output["usage"],
        {
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "server_tool_use",
            "service_tier",
            "cache_creation",
        },
        "AgentOutput.usage",
    )
    _require(
        output["agentId"] == expected["worker_ref"],
        "IDENTITY_MISMATCH",
        "AgentOutput worker differs from expected native agent",
    )
    _require(
        output["prompt"] == entry["input"],
        "INPUT_MISMATCH",
        "AgentOutput accepted prompt differs from exact dispatch",
    )
    content = _list(output["content"], "AgentOutput.content")
    _require(
        bool(content),
        "INCOMPLETE_RESULT",
        "full AgentOutput content is required",
        reconcile=True,
    )
    for item in content:
        _object(item, {"type", "text"}, "AgentOutput content")
        _require(
            item["type"] == "text",
            "UNSUPPORTED_SURFACE",
            "AgentOutput content must preserve complete text blocks",
        )
        _text(item["text"], "AgentOutput text")
    mapped = _round(
        CLAUDE_PROFILE,
        expected["scope_ref"],
        output["agentId"],
        use["id"],
        entry["task_ref"],
        {"prompt": output["prompt"]},
        output,
        [delivery["uuid"]],
    )
    return {"rounds": [mapped], "reported_worker_status": output["status"]}


def _claude_rounds(expected: dict, records: dict) -> dict:
    """Map an initial AgentOutput and one serialized SendMessage history delivery.

    This profile declares two rounds, not a native round quota. Public wrapped
    feedback input is opaque. Completion events and history are caller-collected
    public projections, never reconstruction of an initial AgentOutput.
    """
    _object(records, {"initial", "feedback"}, "records", closed=True)
    feedback = _list(records["feedback"], "feedback")
    _require(
        len(expected["rounds"]) == 2 and len(feedback) == 1,
        "UNSUPPORTED_OPERATION",
        "this profile covers an initial assignment and one serialized feedback delivery",
        reconcile=True,
    )
    initial = _object(
        records["initial"], {"invocation", "delivery"}, "initial", closed=True
    )
    mapped = _claude({**expected, "rounds": expected["rounds"][:1]}, initial)
    entry = expected["rounds"][1]
    record = _object(
        feedback[0],
        {"invocation", "delivery", "events", "forwarded_result", "public_history"},
        "feedback",
        closed=True,
    )
    invocation = _object(
        record["invocation"],
        {"type", "session_id", "uuid", "message", "parent_tool_use_id"},
        "SendMessage invocation",
    )
    delivery = _object(
        record["delivery"],
        {
            "type",
            "session_id",
            "uuid",
            "message",
            "parent_tool_use_id",
            "tool_use_result",
        },
        "SendMessage delivery",
    )
    _require(
        invocation["type"] == "assistant"
        and delivery["type"] == "user"
        and invocation["session_id"] == delivery["session_id"] == expected["scope_ref"]
        and invocation["parent_tool_use_id"] is None
        and delivery["parent_tool_use_id"] is None,
        "IDENTITY_MISMATCH",
        "SendMessage pair must belong to the original Primary session",
    )
    _unique([invocation, delivery], "SendMessage pair", "uuid")
    for message in (invocation, delivery):
        _require(
            not message.get("error")
            and not message.get("aborted")
            and not message.get("supersedes"),
            "INCOMPLETE_RESULT",
            "interrupted feedback requires native reconciliation",
            reconcile=True,
        )
    message = _object(
        invocation["message"], {"role", "content", "stop_reason"}, "SendMessage message"
    )
    _require(
        message["role"] == "assistant" and message["stop_reason"] in (None, "tool_use"),
        "INCOMPLETE_RESULT",
        "SendMessage invocation has an unsupported stop reason",
        reconcile=True,
    )
    uses = [
        item
        for item in _list(message["content"], "SendMessage content")
        if isinstance(item, dict) and item.get("type") == "tool_use"
    ]
    _require(
        len(uses) == 1,
        "AMBIGUOUS_IDENTITY",
        "feedback requires one actual SendMessage tool use",
        reconcile=True,
    )
    use = _object(uses[0], {"id", "name", "input"}, "SendMessage tool use")
    _require(
        use["name"] == "SendMessage" and use["id"] == entry["dispatch_ref"],
        "IDENTITY_MISMATCH",
        "feedback dispatch differs from the actual SendMessage ID",
    )
    arguments = _object(use["input"], {"to", "message", "summary"}, "SendMessage input")
    _require(
        set(arguments)
        <= {
            "to",
            "message",
            "summary",
            "type",
            "recipient",
            "recipient_kind",
            "content",
        }
        and all(isinstance(value, str) for value in arguments.values()),
        "UNSUPPORTED_SURFACE",
        "feedback controls require the pinned string-valued SendMessage surface",
        reconcile=True,
    )
    _require(
        arguments["to"] == expected["worker_ref"]
        and arguments["message"] == entry["input"],
        "INPUT_MISMATCH",
        "feedback must target the original agent with the exact assigned message",
    )
    reply_message = _object(
        delivery["message"], {"role", "content"}, "feedback reply message"
    )
    replies = _list(reply_message["content"], "feedback reply content")
    _require(
        reply_message["role"] == "user"
        and len(replies) == 1
        and isinstance(replies[0], dict)
        and replies[0].get("type") == "tool_result"
        and replies[0].get("tool_use_id") == use["id"]
        and not replies[0].get("is_error"),
        "IDENTITY_MISMATCH",
        "feedback requires a successful correlated tool result",
    )
    acknowledgement = _object(
        delivery["tool_use_result"], {"success", "resumedAgentId"}, "SendMessage output"
    )
    _require(
        acknowledgement["success"] is True
        and acknowledgement["resumedAgentId"] == expected["worker_ref"],
        "NATIVE_ACKNOWLEDGEMENT_REQUIRED",
        "SendMessage success must resume the original native agent",
        reconcile=True,
    )
    events = _list(record["events"], "feedback events")
    _unique(events, "feedback event", "uuid")
    for event in events:
        _object(event, {"type", "subtype", "session_id"}, "feedback event")
        _require(
            event["type"] == "system"
            and event["session_id"] == expected["scope_ref"]
            and event["subtype"]
            in (
                "task_started",
                "task_updated",
                "task_notification",
                "background_tasks_changed",
            ),
            "IDENTITY_MISMATCH",
            "feedback event surface or session differs from the original invocation",
        )

    def event_of(kind: str) -> dict:
        candidates = [event for event in events if event["subtype"] == kind]
        _require(
            len(candidates) == 1,
            "UNCERTAIN_OPERATION",
            "feedback requires one correlated start, completed update and notification",
            reconcile=True,
        )
        return candidates[0]

    started, updated, notification = (
        event_of(kind) for kind in ("task_started", "task_updated", "task_notification")
    )
    for event in (started, updated, notification):
        _require(
            event.get("task_id") == expected["worker_ref"]
            and event.get("run_id") == entry["task_ref"],
            "IDENTITY_MISMATCH",
            "feedback native task/run identity differs from expected delivery",
        )
    _require(
        started.get("tool_use_id") == notification.get("tool_use_id") == use["id"]
        and started.get("prompt") == arguments["message"],
        "INPUT_MISMATCH",
        "native started prompt and dispatch must acknowledge the exact feedback",
    )
    _require(
        type(started.get("is_backgrounded")) is bool
        and type(started.get("spawn_depth")) is int
        and started["spawn_depth"] > 0
        and started.get("task_type") == "local_agent"
        and started.get("subagent_type") == "general-purpose",
        "UNSUPPORTED_SURFACE",
        "feedback run requires actual local-agent background and ancestry metadata",
        reconcile=True,
    )
    _require(
        isinstance(updated.get("patch"), dict)
        and updated["patch"].get("status") == "completed"
        and notification.get("status") == "completed",
        "INCOMPLETE_RESULT",
        "feedback must have a completed native update and notification",
        reconcile=True,
    )
    _object(
        notification, {"output_file", "summary", "usage"}, "complete task notification"
    )
    _require(
        isinstance(notification["output_file"], str)
        and bool(notification["output_file"])
        and isinstance(notification["summary"], str)
        and isinstance(notification["usage"], dict),
        "INCOMPLETE_RESULT",
        "complete notification provenance is required",
        reconcile=True,
    )
    _require(
        events.index(started) < events.index(updated) < events.index(notification),
        "UNCERTAIN_OPERATION",
        "native feedback completion events must follow their start",
        reconcile=True,
    )
    snapshots = [
        event for event in events if event["subtype"] == "background_tasks_changed"
    ]
    _require(
        len(snapshots) == 2,
        "UNCERTAIN_OPERATION",
        "feedback requires the captured active and completed background snapshots",
        reconcile=True,
    )
    active, completed = snapshots
    tasks = _list(active.get("tasks"), "active background tasks")
    remaining = _list(completed.get("tasks"), "completed background tasks")
    _require(
        all(isinstance(task, dict) for task in tasks + remaining),
        "INVALID_RECORD",
        "background task snapshots must retain native objects",
    )
    target_tasks = [
        task for task in tasks if task.get("task_id") == expected["worker_ref"]
    ]
    _require(
        len(target_tasks) == 1
        and target_tasks[0].get("run_id") == entry["task_ref"]
        and not any(task.get("task_id") == expected["worker_ref"] for task in remaining)
        and events.index(active) < events.index(started)
        and events.index(completed) > events.index(notification),
        "UNCERTAIN_OPERATION",
        "background snapshots must correlate the observed target run without pending target work",
        reconcile=True,
    )
    history = _object(
        record["public_history"],
        {"sdk_version", "session_id", "agent_id", "agents", "child"},
        "public history",
    )
    agents = _list(history["agents"], "public agent IDs")
    _require(
        all(isinstance(agent, str) for agent in agents)
        and agents.count(expected["worker_ref"]) == 1
        and history["sdk_version"] == "0.3.295"
        and history["session_id"] == expected["scope_ref"]
        and history["agent_id"] == expected["worker_ref"],
        "IDENTITY_MISMATCH",
        "public child reader must select the original SDK session and actual agent",
    )
    child = _list(history["child"], "public child messages")
    _unique(child, "public child message", "uuid")
    initial_use_id = expected["rounds"][0]["dispatch_ref"]
    model = _text(
        initial["delivery"]["tool_use_result"].get("resolvedModel"),
        "initial native resolvedModel",
    )
    for item in child:
        _object(
            item,
            {"type", "message", "session_id", "parent_tool_use_id"},
            "public child message",
        )
        _require(
            item["session_id"] == expected["scope_ref"]
            and item["parent_tool_use_id"] == initial_use_id
            and item.get("parent_agent_id") is None,
            "IDENTITY_MISMATCH",
            "public child ancestry must retain the original Agent invocation",
        )
        body = _object(item["message"], {"role", "content"}, "public message body")
        _require(
            item["type"] == body["role"] and item["type"] in ("user", "assistant"),
            "UNSUPPORTED_SURFACE",
            "public feedback history requires complete conversation messages",
            reconcile=True,
        )
        if item["type"] == "assistant":
            _object(body, {"id", "model", "stop_reason"}, "complete public assistant")
            _text(body["id"], "public assistant message ID")
            _text(body.get("model"), "public child native model")
            _require(
                isinstance(body["content"], list) and bool(body["content"]),
                "INCOMPLETE_RESULT",
                "public assistant content must be complete",
                reconcile=True,
            )
            _require(
                all(
                    isinstance(block, dict)
                    and block.get("type") in ("text", "thinking")
                    for block in body["content"]
                ),
                "UNSUPPORTED_OPERATION",
                "tool-bearing child history requires a separately qualified feedback mapping",
                reconcile=True,
            )
            for block in body["content"]:
                _require(
                    isinstance(
                        block.get("text" if block["type"] == "text" else "thinking"),
                        str,
                    ),
                    "INCOMPLETE_RESULT",
                    "complete public content blocks are required",
                    reconcile=True,
                )
    users = [index for index, item in enumerate(child) if item["type"] == "user"]
    terminals = [
        index
        for index, item in enumerate(child)
        if item["type"] == "assistant"
        and item["message"].get("stop_reason") == "end_turn"
    ]
    _require(
        len(users) == len(terminals) == 2
        and users[0] == 0
        and users[1] == terminals[0] + 1
        and users[0] < terminals[0] < users[1] < terminals[1] == len(child) - 1,
        "INCOMPLETE_HISTORY",
        "public history must contain exactly the initial and serialized feedback deliveries",
        reconcile=True,
    )
    first_content = child[0]["message"]["content"]
    _require(
        first_content == expected["rounds"][0]["input"]
        and child[terminals[0]]["message"]["content"]
        == initial["delivery"]["tool_use_result"]["content"],
        "INPUT_MISMATCH",
        "initial public predecessor must bind the exact accepted prompt and initial complete result",
    )
    _require(
        child[terminals[0]]["message"].get("model") == model,
        "CONFIGURATION_MISMATCH",
        "initial public terminal model contradicts the initial native resolved model",
    )
    _require(
        isinstance(child[users[1]]["message"]["content"], str)
        and bool(child[users[1]]["message"]["content"]),
        "INCOMPLETE_HISTORY",
        "wrapped feedback user content must remain complete and opaque",
        reconcile=True,
    )
    _require(
        all(
            item["message"].get("stop_reason") is None
            for item in child
            if item["type"] == "assistant"
            and item not in (child[terminals[0]], child[terminals[1]])
        ),
        "INCOMPLETE_RESULT",
        "nonterminal public messages cannot claim another completed delivery",
        reconcile=True,
    )
    final = child[-1]
    _require(
        any(
            block.get("type") == "text" and bool(block.get("text"))
            for block in final["message"]["content"]
        ),
        "INCOMPLETE_RESULT",
        "feedback final message requires complete text",
        reconcile=True,
    )
    forwarded = _object(
        record["forwarded_result"],
        {"type", "uuid", "session_id", "parent_tool_use_id", "agent_id", "message"},
        "forwarded result",
    )
    _require(
        forwarded["type"] == "assistant"
        and forwarded["uuid"] == final["uuid"]
        and forwarded["session_id"] == expected["scope_ref"]
        and forwarded["parent_tool_use_id"] == initial_use_id
        and forwarded["agent_id"] == expected["worker_ref"],
        "IDENTITY_MISMATCH",
        "forwarded feedback result must match the selected actual child terminal UUID",
    )
    forwarded_body = _object(
        forwarded["message"], {"id", "role", "model", "content"}, "forwarded message"
    )
    _require(
        forwarded_body["role"] == "assistant"
        and all(
            forwarded_body[key] == final["message"].get(key)
            for key in ("id", "model", "content")
        ),
        "INCOMPLETE_RESULT",
        "forwarded feedback must preserve complete public final content and model",
        reconcile=True,
    )
    result = {
        "schema": "aquarium.claude-feedback-result/v1",
        "predecessor_terminal_uuid": child[terminals[0]]["uuid"],
        "public_child_messages": child[terminals[0] + 1 :],
        "completion_events": events,
        "send_message_delivery": delivery,
        "forwarded_result": forwarded,
    }
    round_record = _round(
        CLAUDE_ROUNDS_PROFILE,
        expected["scope_ref"],
        expected["worker_ref"],
        entry["dispatch_ref"],
        entry["task_ref"],
        arguments,
        result,
        [final["uuid"], notification["uuid"]],
    )
    round_record["result_domain"] = {
        "schema": "aquarium.native-result-domain/v1",
        "profile": CLAUDE_ROUNDS_PROFILE,
        "accepted_task_digest": round_record["accepted_task_digest"],
        "result": result,
    }
    mapped["rounds"].append(round_record)
    initial_arguments = next(
        item["input"]
        for item in initial["invocation"]["message"]["content"]
        if isinstance(item, dict) and item.get("type") == "tool_use"
    )
    mapped.update(
        {
            "creation_controls": {
                "source_ref": initial_use_id,
                "resolvedModel": model,
                "acknowledged_input": initial_arguments,
            },
            "feedback_run": {
                **{
                    key: started[key]
                    for key in ("task_id", "run_id", "is_backgrounded", "spawn_depth")
                },
                "model": final["message"]["model"],
                "model_source_ref": final["uuid"],
            },
            "reported_worker_status": "completed",
            "feedback_acknowledgement": acknowledgement,
        }
    )
    return mapped


def _codex_spawn(expected: dict, records: dict) -> dict:
    _object(records, {"journal", "parent_read", "child_read"}, "records", closed=True)
    _require(
        len(expected["rounds"]) == 1,
        "UNSUPPORTED_OPERATION",
        "collaboration-spawn profile maps one initial assignment only",
        reconcile=True,
    )
    journal = _object(records["journal"], {"request"}, "journal")
    _require(
        set(journal) <= {"request", "response"},
        "INVALID_RECORD",
        "journal may contain only the exact native request and response",
    )
    arguments = _object(
        journal["request"], {"task_name", "fork_turns", "message"}, "spawn request"
    )
    _require(
        set(arguments)
        <= {"task_name", "fork_turns", "message", "model", "reasoning_effort"},
        "UNSUPPORTED_SURFACE",
        "spawn request contains unsupported native arguments",
    )
    _require(
        isinstance(arguments["task_name"], str)
        and re.fullmatch(r"[a-z0-9_]+", arguments["task_name"]) is not None,
        "INVALID_RECORD",
        "task_name must use lowercase letters, digits or underscores",
    )
    _require(
        arguments["fork_turns"] in ("all", "none"),
        "UNSUPPORTED_SURFACE",
        "fork_turns must be all or none",
    )
    _text(arguments["message"], "spawn request message")
    selected_controls = {
        key: arguments[key] for key in ("model", "reasoning_effort") if key in arguments
    }
    if selected_controls:
        _require(
            arguments["fork_turns"] == "none",
            "UNSUPPORTED_SURFACE",
            "explicit model or effort selection requires fork_turns=none",
        )
        for key, value in selected_controls.items():
            _text(value, f"selected {key}")
    entry = expected["rounds"][0]
    _require(
        arguments["message"] == entry["input"],
        "INPUT_MISMATCH",
        "journaled native message differs from the expected exact dispatch",
    )
    response = journal.get("response")
    _require(
        isinstance(response, dict) and set(response) == {"task_name"},
        "NATIVE_ACKNOWLEDGEMENT_REQUIRED",
        "missing successful spawn response requires reconciliation of the original request",
        reconcile=True,
    )
    path = _text(response["task_name"], "returned native task_name")
    _require(
        path.startswith("/")
        and "\x00" not in path
        and len(path.split("/")) >= 3
        and all(part not in ("", ".", "..") for part in path.split("/")[1:])
        and path.rsplit("/", 1)[1] == arguments["task_name"],
        "IDENTITY_MISMATCH",
        "returned task_name must be its canonical native path",
    )
    parent = _codex_thread(
        records["parent_read"], expected, "supervisor_ref", journal_spawn=True
    )
    activities = [
        item
        for turn in parent["turns"]
        for item in turn["items"]
        if item.get("type") == "subAgentActivity"
    ]
    started = [
        item
        for item in activities
        if item.get("kind") == "started" and item.get("agentPath") == path
    ]
    _require(
        len(started) == 1,
        "AMBIGUOUS_IDENTITY",
        "successful response must join exactly one native started activity",
    )
    creation = _object(
        started[0], {"id", "agentPath", "agentThreadId", "kind"}, "started activity"
    )
    worker_id = _text(creation["agentThreadId"], "native agentThreadId")
    _require(
        creation["id"] == entry["dispatch_ref"]
        and worker_id == expected["worker_ref"]
        and worker_id != parent["id"],
        "IDENTITY_MISMATCH",
        "native creation IDs differ from the expected initial dispatch",
    )
    worker_activity = [
        item for item in activities if item.get("agentThreadId") == worker_id
    ]
    for item in worker_activity:
        _require(
            item.get("agentPath") == path,
            "IDENTITY_MISMATCH",
            "worker activity path differs from its acknowledged native identity",
        )
        _require(
            item.get("kind") in ("started", "completed"),
            "UNSUPPORTED_OPERATION",
            "worker interaction or follow-up requires its own acknowledged mapping",
            reconcile=True,
        )
    _require(
        sum(item["kind"] == "started" for item in worker_activity) == 1
        and sum(item["kind"] == "completed" for item in worker_activity) <= 1,
        "UNSUPPORTED_OPERATION",
        "worker history exceeds one initial assignment",
        reconcile=True,
    )
    for turn in parent["turns"]:
        for item in turn["items"]:
            if item.get("type") == "collabAgentToolCall" and worker_id in _list(
                item.get("receiverThreadIds"), "receiverThreadIds"
            ):
                _require(
                    item.get("tool") == "wait" and item.get("status") == "completed",
                    "UNSUPPORTED_OPERATION",
                    "additional native worker operations require reconciliation",
                    reconcile=True,
                )
    controls = {
        "model": creation.get("model"),
        "reasoning_effort": creation.get("reasoningEffort"),
    }
    for key, value in controls.items():
        if value is not None:
            _text(value, f"native creation {key}")
    for key, selected in selected_controls.items():
        _require(
            controls[key] == selected,
            "CONFIGURATION_MISMATCH",
            f"selected {key} differs from native resolved creation value",
        )
    child = _codex_thread(
        records["child_read"], expected, "worker_ref", journal_spawn=True
    )
    source = _object(child.get("source"), {"subAgent"}, "child.source")
    spawn = _object(
        _object(source["subAgent"], {"thread_spawn"}, "child.source.subAgent")[
            "thread_spawn"
        ],
        {"parent_thread_id", "agent_path", "depth"},
        "thread_spawn",
    )
    _require(
        child.get("parentThreadId") == spawn["parent_thread_id"] == parent["id"]
        and spawn["agent_path"] == path,
        "IDENTITY_MISMATCH",
        "child source does not corroborate the native started activity",
    )
    _require(
        type(spawn["depth"]) is int and spawn["depth"] > 0,
        "INVALID_RECORD",
        "child spawn depth must be a positive integer",
    )
    _require(
        len(child["turns"]) == 1,
        "UNSUPPORTED_OPERATION",
        "initial-spawn mapping requires exactly one child turn",
        reconcile=True,
    )
    turn = child["turns"][0]
    _require(
        turn["id"] == entry["task_ref"],
        "IDENTITY_MISMATCH",
        "initial child task differs from expected task",
    )
    _require(
        turn["status"] == "completed" and turn.get("error") is None,
        "INCOMPLETE_RESULT",
        "initial child turn has no successful complete delivery",
        reconcile=True,
    )
    user_inputs = [item for item in turn["items"] if item.get("type") == "userMessage"]
    _require(
        len(user_inputs) <= 1,
        "AMBIGUOUS_INPUT",
        "initial-spawn mapping cannot account for multiple native user inputs",
    )
    for item in user_inputs:
        content = item.get("content")
        _require(
            isinstance(content, list)
            and len(content) == 1
            and isinstance(content[0], dict)
            and content[0].get("type") == "text"
            and content[0].get("text") == arguments["message"]
            and content[0].get("text_elements", []) == [],
            "INPUT_MISMATCH",
            "available native input contradicts the acknowledged request",
        )
    final = [
        item
        for item in turn["items"]
        if item.get("type") == "agentMessage" and item.get("phase") == "final_answer"
    ]
    _require(
        bool(final),
        "INCOMPLETE_RESULT",
        "complete initial final-answer messages are required",
        reconcile=True,
    )
    for item in final:
        _text(item.get("text"), "final answer text")
        _require(
            item.get("delivery") is None,
            "UNSUPPORTED_OPERATION",
            "async delivery requires a separate acknowledgement mapping",
            reconcile=True,
        )
    _require(
        turn["items"][-1]["id"] == final[-1]["id"],
        "INCOMPLETE_RESULT",
        "final answer must close the initial completed turn",
        reconcile=True,
    )
    status = _object(child["status"], {"type"}, "child.status")
    _require(
        status["type"] in ("notLoaded", "idle", "systemError", "active"),
        "INVALID_RECORD",
        "unsupported native thread status",
    )
    mapped = _round(
        CODEX_SPAWN_PROFILE,
        expected["scope_ref"],
        worker_id,
        creation["id"],
        turn["id"],
        arguments,
        final,
        [item["id"] for item in final],
    )
    return {
        "rounds": [mapped],
        "reported_worker_status": status["type"],
        "native_agent_path": path,
        "creation_controls": {"source_ref": creation["id"], **controls},
        "dispatch_acknowledgement": {
            "request_digest": digest(arguments),
            "response": response,
        },
    }


def _worker_operations(parent: dict, worker: str, path: str) -> list[dict]:
    """Preserve actual target-worker operations, including contradictory identity."""
    operations = []
    for turn in parent["turns"]:
        for item in turn["items"]:
            if item.get("type") == "subAgentActivity" and (
                item.get("agentThreadId") == worker or item.get("agentPath") == path
            ):
                _require(
                    item.get("agentThreadId") == worker
                    and item.get("agentPath") == path,
                    "IDENTITY_MISMATCH",
                    "worker activity identity contradicts its acknowledged creation",
                )
                operations.append(item)
            elif item.get("type") == "collabAgentToolCall" and worker in _list(
                item.get("receiverThreadIds"), "receiverThreadIds"
            ):
                operations.append(item)
    return operations


def _codex_rounds(expected: dict, records: dict) -> dict:
    """Map journalled feedback only between complete, explicitly idle turns.

    Preparations are closed-envelope integration data verified by the binder.
    Captured tool output (including an empty string) is not authenticated here.
    No parent display/completion ID is interpreted as a native child turn ID.
    """
    _object(records, {"initial", "feedback"}, "records", closed=True)
    initial = _object(
        records["initial"],
        {"journal", "parent_read", "child_read", "preparation"},
        "initial",
        closed=True,
    )
    feedback = _list(records["feedback"], "feedback")
    _require(
        bool(feedback) and len(expected["rounds"]) == len(feedback) + 1,
        "INCOMPLETE_HISTORY",
        "expected rounds must cover the initial delivery and every feedback journal",
        reconcile=True,
    )
    mapped = _codex_spawn(
        {**expected, "rounds": expected["rounds"][:1]},
        {key: initial[key] for key in ("journal", "parent_read", "child_read")},
    )
    previous_parent = initial["parent_read"]["thread"]
    previous_child = initial["child_read"]["thread"]
    path, worker = mapped["native_agent_path"], expected["worker_ref"]
    _require(
        previous_child["status"]["type"] == "idle",
        "UNCERTAIN_OPERATION",
        "initial delivery must be observed idle before serialized feedback",
        reconcile=True,
    )
    operations = _worker_operations(previous_parent, worker, path)
    _require(
        [
            item.get("kind")
            for item in operations
            if item.get("type") == "subAgentActivity"
        ]
        == ["started", "completed"],
        "INCOMPLETE_RESULT",
        "initial snapshot requires one observed completed worker delivery",
        reconcile=True,
    )
    acknowledgements = []
    for entry, record in zip(expected["rounds"][1:], feedback):
        required = {
            "request",
            "before_parent_read",
            "before_child_read",
            "after_parent_read",
            "after_child_read",
            "preparation",
        }
        _require(
            isinstance(record, dict)
            and {
                "before_parent_read",
                "before_child_read",
                "after_parent_read",
                "after_child_read",
            }
            <= set(record),
            "INCOMPLETE_HISTORY",
            "missing feedback snapshots require native reconciliation",
            reconcile=True,
        )
        _object(record, required, "feedback record")
        _require(
            set(record) <= required | {"feedback_completion_output_utf8"},
            "INVALID_RECORD",
            "feedback record contains unsupported fields",
        )
        _require(
            "feedback_completion_output_utf8" in record,
            "NATIVE_ACKNOWLEDGEMENT_REQUIRED",
            "unobserved feedback tool completion requires reconciliation",
            reconcile=True,
        )
        completion = record["feedback_completion_output_utf8"]
        _require(
            isinstance(completion, str),
            "INVALID_RECORD",
            "feedback completion must retain the actual captured output string",
        )
        # Reject surrogate strings that cannot be an actual UTF-8 tool output.
        try:
            completion.encode("utf-8")
        except UnicodeError as error:
            raise MappingError(
                "INVALID_RECORD", "feedback output must be UTF-8"
            ) from error
        arguments = _object(
            record["request"], {"target", "message"}, "feedback request", closed=True
        )
        _require(
            arguments["target"] == path and arguments["message"] == entry["input"],
            "INPUT_MISMATCH",
            "feedback target or exact message differs from expected dispatch",
        )
        before_parent = _codex_thread(
            record["before_parent_read"], expected, "supervisor_ref", journal_spawn=True
        )
        after_parent = _codex_thread(
            record["after_parent_read"], expected, "supervisor_ref", journal_spawn=True
        )
        before_child = _codex_thread(
            record["before_child_read"], expected, "worker_ref", journal_spawn=True
        )
        after_child = _codex_thread(
            record["after_child_read"], expected, "worker_ref", journal_spawn=True
        )
        for child in (before_child, after_child):
            _require(
                child.get("source") == previous_child.get("source")
                and child.get("parentThreadId") == previous_child.get("parentThreadId"),
                "IDENTITY_MISMATCH",
                "feedback child provenance differs from initial creation",
            )
        _require(
            before_child["status"].get("type") == "idle"
            and before_child["turns"] == previous_child["turns"]
            and all(
                turn["status"] == "completed" and turn.get("error") is None
                for turn in before_child["turns"]
            )
            and _worker_operations(before_parent, worker, path) == operations,
            "UNCERTAIN_OPERATION",
            "feedback before snapshots must preserve prior delivery and observe an idle worker",
            reconcile=True,
        )
        after_operations = _worker_operations(after_parent, worker, path)
        appended = after_operations[len(operations) :]
        _require(
            after_operations[: len(operations)] == operations
            and len(appended) == 2
            and [item.get("kind") for item in appended] == ["interacted", "completed"]
            and appended[0]["id"] == entry["dispatch_ref"],
            "UNCERTAIN_OPERATION",
            "feedback must add exactly one correlated interaction and completed delivery",
            reconcile=True,
        )
        turns = after_child["turns"]
        _require(
            len(turns) == len(before_child["turns"]) + 1
            and turns[:-1] == before_child["turns"],
            "INCOMPLETE_HISTORY",
            "feedback requires an unchanged completed prefix and exactly one new turn",
            reconcile=True,
        )
        turn = turns[-1]
        _require(
            turn["id"] == entry["task_ref"]
            and turn["status"] == "completed"
            and turn.get("error") is None,
            "INCOMPLETE_RESULT",
            "feedback native task must match and complete successfully",
            reconcile=True,
        )
        user_inputs = [
            item for item in turn["items"] if item.get("type") == "userMessage"
        ]
        _require(
            len(user_inputs) <= 1,
            "AMBIGUOUS_INPUT",
            "feedback has multiple native inputs",
            reconcile=True,
        )
        for item in user_inputs:
            content = item.get("content")
            _require(
                isinstance(content, list)
                and len(content) == 1
                and isinstance(content[0], dict)
                and content[0].get("type") == "text"
                and content[0].get("text") == arguments["message"]
                and content[0].get("text_elements", []) == [],
                "INPUT_MISMATCH",
                "available native feedback input contradicts its journal",
            )
        final = [
            item
            for item in turn["items"]
            if item.get("type") == "agentMessage"
            and item.get("phase") == "final_answer"
        ]
        _require(
            bool(final) and turn["items"][-1]["id"] == final[-1]["id"],
            "INCOMPLETE_RESULT",
            "complete final messages must close the feedback turn",
            reconcile=True,
        )
        for item in final:
            _text(item.get("text"), "feedback final answer")
            _require(
                item.get("delivery") is None,
                "UNSUPPORTED_OPERATION",
                "asynchronous feedback requires reconciliation",
                reconcile=True,
            )
        status = _object(after_child["status"], {"type"}, "feedback child.status")[
            "type"
        ]
        _require(
            status in ("notLoaded", "idle", "systemError", "active"),
            "INVALID_RECORD",
            "unsupported native thread status",
        )
        mapped["rounds"].append(
            _round(
                CODEX_ROUNDS_PROFILE,
                expected["scope_ref"],
                worker,
                entry["dispatch_ref"],
                turn["id"],
                arguments,
                final,
                [item["id"] for item in final],
            )
        )
        acknowledgements.append(
            {
                "dispatch_ref": entry["dispatch_ref"],
                "request_digest": digest(arguments),
                "feedback_completion_output_utf8": completion,
            }
        )
        mapped["reported_worker_status"] = status
        previous_parent, previous_child, operations = (
            after_parent,
            after_child,
            after_operations,
        )
    mapped["feedback_acknowledgements"] = acknowledgements
    return mapped


def map_delivery(request: dict) -> dict:
    """Map a delivery or return a bounded rejection/reconciliation checkpoint.

    Caller-supplied records require actual public collection and host qualification.
    Unmapped metadata remains unresolved; caller booleans/digests cannot fill it.
    """
    output = {
        "schema": OUTPUT_SCHEMA,
        "acceptance_ready": False,
        "redispatch_allowed": False,
        "record_authenticity": "caller_supplied_unverified",
    }
    try:
        output["request_digest"] = digest(request)
    except (ValueError, TypeError):
        return {
            **output,
            "state": "rejected",
            "error": {
                "code": "INVALID_RECORD",
                "message": "input must be finite JSON data",
            },
            "next_action": "resolve_record_gap",
        }
    try:
        _object(
            request,
            {"schema", "profile", "expected", "records"},
            "request",
            closed=True,
        )
        _require(
            request["schema"] == REQUEST_SCHEMA,
            "UNSUPPORTED_SCHEMA",
            f"request schema must be {REQUEST_SCHEMA}",
        )
        _require(
            request["profile"]
            in (
                CODEX_PROFILE,
                CLAUDE_PROFILE,
                CLAUDE_ROUNDS_PROFILE,
                CODEX_SPAWN_PROFILE,
                CODEX_ROUNDS_PROFILE,
            ),
            "UNSUPPORTED_SURFACE",
            "unsupported native delivery profile",
        )
        expected = _expected(request)
        output["expected_recovery_refs"] = {
            **{
                key: expected[key]
                for key in ("scope_ref", "supervisor_ref", "worker_ref")
            },
            "rounds": [
                {
                    "dispatch_ref": entry["dispatch_ref"],
                    "task_ref": entry["task_ref"],
                    "expected_input_digest": digest(entry["input"]),
                }
                for entry in expected["rounds"]
            ],
        }
        mapper = {
            CODEX_PROFILE: _codex,
            CLAUDE_PROFILE: _claude,
            CLAUDE_ROUNDS_PROFILE: _claude_rounds,
            CODEX_SPAWN_PROFILE: _codex_spawn,
            CODEX_ROUNDS_PROFILE: _codex_rounds,
        }[request["profile"]]
        mapped = mapper(expected, request["records"])
        output.update(
            {
                "state": "delivery_mapped",
                "profile": request["profile"],
                "records_digest": digest(request["records"]),
                "mapped": {
                    "scope_ref": expected["scope_ref"],
                    "supervisor_ref": expected["supervisor_ref"],
                    "worker_ref": expected["worker_ref"],
                    **mapped,
                    "observed_round_count": len(mapped["rounds"]),
                    "rounds_used": None,
                    "worker_disposition": None,
                },
                "unresolved_domains": [
                    "accepted_role_and_dependencies",
                    "accepted_agent_configuration",
                    "complete_lifetime_round_accounting",
                    "explicit_primary_acceptance",
                    "settlement_and_descendant_quiescence",
                    "durable_recovery_and_host_qualification",
                ],
                "next_action": "qualify_missing_native_domains",
            }
        )
    except MappingError as error:
        reconcile = error.reconcile or (
            isinstance(request, dict)
            and request.get("profile") in (CODEX_ROUNDS_PROFILE, CLAUDE_ROUNDS_PROFILE)
            and error.code in ("AMBIGUOUS_IDENTITY", "AMBIGUOUS_INPUT")
        )
        output.update(
            {
                "state": "reconciliation_required" if reconcile else "rejected",
                "error": {"code": error.code, "message": str(error)},
                "next_action": "reconcile_original_native_operation"
                if reconcile
                else "resolve_record_gap",
            }
        )
    # Return independent immutable JSON data, including the recovery references.
    return json.loads(canonical_bytes(output))


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, help="JSON request file, or '-' for stdin"
    )
    args = parser.parse_args()
    try:
        payload = (
            sys.stdin.buffer.read()
            if args.input == "-"
            else Path(args.input).read_bytes()
        )
        request = json.loads(
            payload, object_pairs_hook=_unique_keys, parse_constant=_reject_constant
        )
        output = map_delivery(request)
        sys.stdout.buffer.write(canonical_bytes(output) + b"\n")
        return 0 if output["state"] == "delivery_mapped" else 2
    except (ValueError, TypeError, OSError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
