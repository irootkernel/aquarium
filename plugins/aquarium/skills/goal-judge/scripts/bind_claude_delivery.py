"""Bind a prepared dispatch to one correlated completed Claude SDK Agent delivery.

Call bind_delivery(preparation, mapping_request), or use --input (file or '-')
with aquarium.claude-prepared-delivery-request/v1 and preparation/mapping_request.
Both preparation rendering and native delivery mapping are recomputed locally.
The exact echoed operative prompt acknowledges the immutable role snapshot.
For the serialized-rounds profile, preparation is an ordered list containing
one preparation per assignment. Complete role snapshots must match. The v1
rounds route remains exactly two rounds; the v2 route retains every serialized
round independently and leaves actual lifetime/tool-host qualification unresolved.
The hook-native profile independently binds each preparation to acknowledged
effective input while preserving the original model request and native hook
outputs. It keeps creation and per-assignment configuration domains separate.
The initial AgentOutput remains intact; feedback uses the complete public child
message slice and correlated native completion evidence. Runtime model and
background state are retained per run, separately from creation controls.

The applicable AgentInput surface is pinned to official SDK 0.3.295: description,
prompt, optional built-in general-purpose selection, model/effort selectors, name,
and explicit run_in_background=false. The declared default is background=true;
omission cannot establish this synchronous route. Custom/fork definitions,
isolation, worktree records and unknown controls need separate qualification.
These are native capabilities, not disabled policies. Deprecated mode/team_name
are retained as ignored inputs, never claimed as effective configuration.

Configuration binds the complete role snapshot, acknowledged applicable input
controls, exact correlated tool input, and AgentOutput.resolvedModel with native
source IDs. Requested model aliases remain distinct from resolved model IDs;
no alias expansion or hidden host/system configuration is inferred. Optional
modelsUsed is retained with its native string-list type, without extra semantics.
The complete structured AgentOutput remains the result domain, including optional
extensions. No SDK invocation, source discovery, acceptance or settlement occurs.

Compact sorted-key ASCII JSON is the digest domain, without a final newline.
The role digest is the preparer's existing snapshot digest, with sha256: prefix.
Caller authenticity, dependency completeness and actual host qualification remain
unverified. A successful binding is not a Podway acceptance document.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REQUEST_SCHEMA = "aquarium.claude-prepared-delivery-request/v1"
OUTPUT_SCHEMA = "aquarium.claude-prepared-delivery-binding/v1"
CONFIGURATION_SCHEMA = "aquarium.claude-accepted-agent-configuration/v1"


def _load_helper(name: str):
    spec = importlib.util.spec_from_file_location(
        f"aquarium_claude_binding_{name}", Path(__file__).with_name(f"{name}.py")
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load required helper: {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


renderer = _load_helper("render_dispatch")
native = _load_helper("map_native_delivery")


class BindingError(ValueError):
    """Rejected preparation or a native route needing further reconciliation."""

    def __init__(self, code: str, message: str, *, reconcile: bool = False):
        super().__init__(message)
        self.code = code
        self.reconcile = reconcile


def _require(condition: bool, code: str, message: str, *, reconcile=False):
    if not condition:
        raise BindingError(code, message, reconcile=reconcile)


def _controls(arguments: dict, result: dict) -> tuple[dict, dict]:
    """Validate only the pinned public input keys; preserve native semantics."""
    _require(
        set(arguments)
        <= {
            "description",
            "prompt",
            "subagent_type",
            "model",
            "effort",
            "run_in_background",
            "name",
            "team_name",
            "mode",
            "isolation",
        },
        "UNQUALIFIED_AGENT_CONTROL",
        "unknown Agent input controls need a qualified native mapping",
        reconcile=True,
    )
    _require(
        isinstance(arguments.get("description"), str),
        "INVALID_AGENT_INPUT",
        "Agent description must retain its native string type",
    )
    for key in ("subagent_type", "name", "team_name"):
        if key in arguments:
            _require(
                isinstance(arguments[key], str),
                "INVALID_AGENT_INPUT",
                "Agent string controls must retain native types",
            )
    enums = {
        "model": {"sonnet", "opus", "haiku", "fable"},
        "effort": {"low", "medium", "high", "xhigh", "max"},
        "mode": {
            "acceptEdits",
            "auto",
            "bypassPermissions",
            "default",
            "dontAsk",
            "plan",
        },
        "isolation": {"worktree", "remote"},
    }
    for key, choices in enums.items():
        if key in arguments:
            _require(
                isinstance(arguments[key], str) and arguments[key] in choices,
                "INVALID_AGENT_INPUT",
                "Agent selector is outside the pinned public input schema",
            )
    if "run_in_background" in arguments:
        _require(
            type(arguments["run_in_background"]) is bool,
            "INVALID_AGENT_INPUT",
            "background control must be a native boolean",
        )
    _require(
        arguments.get("run_in_background") is False,
        "UNQUALIFIED_BACKGROUND_ROUTE",
        "synchronous binding requires explicit acknowledged run_in_background=false",
        reconcile=True,
    )
    _require(
        arguments.get("subagent_type", "general-purpose") == "general-purpose",
        "UNQUALIFIED_AGENT_DEFINITION",
        "separate custom or fork definitions require their own configuration acknowledgement",
        reconcile=True,
    )
    if "agentType" in result:
        _require(
            isinstance(result["agentType"], str),
            "INVALID_AGENT_OUTPUT",
            "native agentType must retain its string type",
        )
        _require(
            result["agentType"] == "general-purpose",
            "UNQUALIFIED_AGENT_DEFINITION",
            "resolved separate agent definition has not been bound",
            reconcile=True,
        )
    _require(
        "isolation" not in arguments
        and not ({"worktreePath", "worktreeBranch"} & set(result)),
        "UNQUALIFIED_ISOLATION_ROUTE",
        "worktree or remote isolation requires checkout and native configuration proof",
        reconcile=True,
    )
    return (
        {
            key: arguments[key]
            for key in ("subagent_type", "model", "effort", "name", "run_in_background")
            if key in arguments
        },
        {key: arguments[key] for key in ("mode", "team_name") if key in arguments},
    )


def _bind_hook_delivery(preparations, request, output):
    expected = request.get("expected")
    _require(
        isinstance(expected, dict)
        and isinstance(expected.get("rounds"), list)
        and isinstance(preparations, list)
        and bool(preparations)
        and len(preparations) == len(expected["rounds"]),
        "INVALID_PREPARATION",
        "hook binding requires one independent preparation per actual assignment",
    )
    try:
        dispatches = [renderer.render_dispatch(value) for value in preparations]
    except (ValueError, TypeError) as error:
        raise BindingError(
            "INVALID_PREPARATION", "prepared role and assignment cannot be verified"
        ) from error
    snapshot = preparations[0]["prepared_role_snapshot"]
    _require(
        all(value["prepared_role_snapshot"] == snapshot for value in preparations),
        "ROLE_SNAPSHOT_MISMATCH",
        "hook rounds must preserve every operative role and dependency byte",
    )
    mapping = native.map_delivery(request)
    if "expected_recovery_refs" in mapping:
        output["recovery_refs"] = mapping["expected_recovery_refs"]
    if mapping["state"] != "delivery_mapped":
        output.update({key: mapping[key] for key in ("state", "error", "next_action")})
        return json.loads(native.canonical_bytes(output))
    mapped = mapping["mapped"]
    records = request["records"]["rounds"]
    initial = records[0]["post_hook"]["input"]
    arguments, response = initial["tool_input"], initial["tool_response"]
    controls, ignored = _controls(arguments, response)
    creation = {
        "schema": "aquarium.claude-hook-agent-creation-configuration/v1",
        "role_snapshot": snapshot,
        "accepted_agent_controls": controls,
        "ignored_agent_input": ignored,
        "acknowledged_agent_input": arguments,
        "native_resolution": {
            "agentId": response["agentId"],
            "resolvedModel": response["resolvedModel"],
            "tool_use_id": initial["tool_use_id"],
        },
        "original_creation_hooks": {
            "pre_hook": records[0]["pre_hook"],
            "post_hook": records[0]["post_hook"],
        },
    }
    bindings = []
    for index, (round_record, record, rendered) in enumerate(
        zip(mapped["rounds"], records, dispatches)
    ):
        effective = record["post_hook"]["input"]["tool_input"]
        key = "message" if index else "prompt"
        _require(
            effective[key] == rendered["dispatch_text"],
            "DISPATCH_INPUT_MISMATCH",
            "each effective native assignment must equal its own verified preparation",
        )
        _require(
            native.digest(round_record["result_domain"])
            == round_record["result_digest"],
            "RESULT_DOMAIN_MISMATCH",
            "each hook round must retain its own complete original result",
        )
        configuration = {
            "schema": "aquarium.claude-hook-assignment-configuration/v1",
            "creation_configuration": creation,
            "accepted_task_digest": "sha256:" + round_record["accepted_task_digest"],
            "actual_assignment_runtime": round_record["runtime"],
            "original_assignment_hooks": {
                "pre_hook": record["pre_hook"],
                "post_hook": record["post_hook"],
            },
        }
        if index:
            configuration["native_terminal_model"] = record["public_history"][
                "children"
            ][mapped["worker_ref"]][-1]["message"]["model"]
        bindings.append(
            {
                "dispatch_ref": round_record["dispatch_ref"],
                "task_ref": round_record["task_ref"],
                "local_prepared_assignment_sha256": rendered[
                    "local_prepared_assignment_sha256"
                ],
                "local_dispatch_input_sha256": rendered["local_dispatch_input_sha256"],
                "accepted_task_domain": round_record["accepted_task_domain"],
                "result_domain": round_record["result_domain"],
                "agent_configuration_domain": configuration,
                "accepted_task_digest": "sha256:"
                + round_record["accepted_task_digest"],
                "result_digest": "sha256:" + round_record["result_digest"],
                "agent_configuration_digest": "sha256:" + native.digest(configuration),
            }
        )
    final = bindings[-1]
    output.update(
        {
            "state": "delivery_bound",
            "profile": native.CLAUDE_HOOKS_PROFILE,
            "local_prepared_role_snapshot_sha256": dispatches[-1][
                "local_prepared_role_snapshot_sha256"
            ],
            "local_prepared_assignment_sha256": dispatches[-1][
                "local_prepared_assignment_sha256"
            ],
            "local_dispatch_input_sha256": dispatches[-1][
                "local_dispatch_input_sha256"
            ],
            "native_mapping_digest": native.digest(mapping),
            "domains": {
                "accepted_role_snapshot": snapshot,
                "agent_creation_configuration": creation,
                "agent_configuration": final["agent_configuration_domain"],
                "accepted_task": final["accepted_task_domain"],
                "result": final["result_domain"],
            },
            "bindings": {
                "role_snapshot_digest": "sha256:"
                + dispatches[-1]["local_prepared_role_snapshot_sha256"],
                "agent_creation_configuration_digest": "sha256:"
                + native.digest(creation),
                **{
                    key: final[key]
                    for key in (
                        "agent_configuration_digest",
                        "accepted_task_digest",
                        "result_digest",
                    )
                },
            },
            "round_bindings": bindings,
            "native": {
                **{
                    key: mapped[key]
                    for key in ("scope_ref", "supervisor_ref", "worker_ref")
                },
                "dispatch_ref": final["dispatch_ref"],
                "task_ref": final["task_ref"],
                "result_refs": mapped["rounds"][-1]["result_refs"],
                "delivery_ref": records[-1]["post_hook"]["input"]["tool_use_id"],
                "feedback_runs": mapped["feedback_runs"],
                "feedback_acknowledgements": mapped["feedback_acknowledgements"],
            },
            "unresolved_domains": [
                "explicit_primary_acceptance",
                "complete_lifetime_round_accounting",
                "settlement_and_descendant_quiescence",
                "podway_package_and_context_binding",
                "durable_host_qualification",
                "complete_projection_and_native_hidden_controls",
            ],
            "next_action": "qualify_remaining_acceptance_domains",
        }
    )
    return json.loads(native.canonical_bytes(output))


def bind_delivery(preparation: dict | list[dict], mapping_request: dict) -> dict:
    """Return complete independent domains or a bounded recovery checkpoint."""
    output = {
        "schema": OUTPUT_SCHEMA,
        "acceptance_ready": False,
        "redispatch_allowed": False,
        "record_authenticity": "caller_supplied_unverified",
    }
    try:
        preparations = preparation if isinstance(preparation, list) else [preparation]
        if any(
            isinstance(value, dict) and value.get("schema") == "aquarium.assignment/v2"
            for value in preparations
        ):
            raise BindingError(
                "INVALID_PREPARATION",
                "ordinary v2 assignments are not formal native preparations",
            )
        output["request_digest"] = native.digest(
            {
                "schema": REQUEST_SCHEMA,
                "preparation": preparation,
                "mapping_request": mapping_request,
            }
        )
        _require(
            isinstance(mapping_request, dict)
            and mapping_request.get("profile")
            in (
                native.CLAUDE_PROFILE,
                native.CLAUDE_ROUNDS_PROFILE,
                native.CLAUDE_LIFETIME_PROFILE,
                native.CLAUDE_HOOKS_PROFILE,
            ),
            "UNSUPPORTED_PROFILE",
            "Claude binding requires a supported correlated Agent delivery profile",
        )
        profile = mapping_request["profile"]
        if profile == native.CLAUDE_HOOKS_PROFILE:
            return _bind_hook_delivery(preparation, mapping_request, output)
        rounds_profile = profile in (
            native.CLAUDE_ROUNDS_PROFILE,
            native.CLAUDE_LIFETIME_PROFILE,
        )
        expected = mapping_request.get("expected")
        _require(
            isinstance(expected, dict) and isinstance(expected.get("rounds"), list),
            "INVALID_PREPARATION",
            "binding requires complete expected assignment records",
        )
        _require(
            not rounds_profile
            or isinstance(preparation, list)
            and len(preparation) >= 2
            and len(preparation) == len(expected["rounds"])
            and (profile != native.CLAUDE_ROUNDS_PROFILE or len(preparation) == 2),
            "INVALID_PREPARATION",
            "serialized Claude binding requires exactly one preparation per expected assignment",
        )
        preparations = preparation if rounds_profile else [preparation]
        try:
            dispatches = [renderer.render_dispatch(value) for value in preparations]
        except (ValueError, TypeError) as error:
            raise BindingError(
                "INVALID_PREPARATION", "prepared role and assignment cannot be verified"
            ) from error
        preparation = preparations[-1]
        dispatch = dispatches[-1]
        _require(
            all(
                value["prepared_role_snapshot"] == preparation["prepared_role_snapshot"]
                for value in preparations
            ),
            "ROLE_SNAPSHOT_MISMATCH",
            "serialized Claude rounds must preserve the complete operative role snapshot",
        )
        mapping = native.map_delivery(mapping_request)
        if "expected_recovery_refs" in mapping:
            output["recovery_refs"] = mapping["expected_recovery_refs"]
        if mapping["state"] != "delivery_mapped":
            output.update(
                {
                    "state": mapping["state"],
                    "error": mapping["error"],
                    "next_action": mapping["next_action"],
                }
            )
            return json.loads(native.canonical_bytes(output))
        mapped = mapping["mapped"]
        round_record = mapped["rounds"][-1]
        records = (
            mapping_request["records"]["initial"]
            if rounds_profile
            else mapping_request["records"]
        )
        tool_use = next(
            item
            for item in records["invocation"]["message"]["content"]
            if isinstance(item, dict) and item.get("type") == "tool_use"
        )
        arguments = tool_use["input"]
        result = records["delivery"]["tool_use_result"]
        _require(
            arguments["prompt"] == result["prompt"] == dispatches[0]["dispatch_text"],
            "DISPATCH_INPUT_MISMATCH",
            "native echoed operative prompt differs from the verified preparation",
        )
        accepted_controls, ignored_inputs = _controls(arguments, result)
        if rounds_profile:
            _require(
                len(mapped["rounds"]) == len(dispatches),
                "INVALID_PREPARATION",
                "mapped rounds and independently rendered preparations must have equal cardinality",
            )
            for native_round, rendered in zip(mapped["rounds"][1:], dispatches[1:]):
                _require(
                    native_round["accepted_task_domain"]["input"]["message"]
                    == rendered["dispatch_text"],
                    "DISPATCH_INPUT_MISMATCH",
                    "every acknowledged feedback must match its independently rendered preparation",
                )
        _require(
            isinstance(result.get("resolvedModel"), str)
            and bool(result["resolvedModel"].strip()),
            "RESOLVED_MODEL_REQUIRED",
            "native completed AgentOutput must acknowledge a nonempty resolvedModel",
            reconcile=True,
        )
        resolution = {
            "agentId": result["agentId"],
            "delivery_uuid": records["delivery"]["uuid"],
            "tool_use_id": tool_use["id"],
            "resolvedModel": result["resolvedModel"],
        }
        if "modelsUsed" in result:
            _require(
                isinstance(result["modelsUsed"], list)
                and all(isinstance(model, str) for model in result["modelsUsed"]),
                "INVALID_AGENT_OUTPUT",
                "native modelsUsed must retain its string-list type",
            )
            resolution["modelsUsed"] = result["modelsUsed"]
        task_digest = round_record["accepted_task_digest"]
        configuration = {
            "schema": CONFIGURATION_SCHEMA,
            "role_snapshot": preparation["prepared_role_snapshot"],
            "accepted_agent_controls": accepted_controls,
            "ignored_agent_input": ignored_inputs,
            "acknowledged_agent_input": arguments,
            "native_resolution": resolution,
            "accepted_task_digest": f"sha256:{task_digest}",
        }
        initial_result_domain = {
            "schema": "aquarium.native-result-domain/v1",
            "profile": native.CLAUDE_PROFILE,
            "accepted_task_digest": mapped["rounds"][0]["accepted_task_digest"],
            "result": result,
        }
        result_domain = (
            round_record["result_domain"] if rounds_profile else initial_result_domain
        )
        _require(
            native.digest(result_domain) == round_record["result_digest"],
            "RESULT_DOMAIN_MISMATCH",
            "complete AgentOutput differs from the recomputed native result",
        )
        if rounds_profile:
            _require(
                native.digest(initial_result_domain)
                == mapped["rounds"][0]["result_digest"],
                "RESULT_DOMAIN_MISMATCH",
                "initial complete AgentOutput domain must remain unchanged",
            )
        output.update(
            {
                "state": "delivery_bound",
                "profile": profile,
                "local_prepared_role_snapshot_sha256": dispatch[
                    "local_prepared_role_snapshot_sha256"
                ],
                "local_prepared_assignment_sha256": dispatch[
                    "local_prepared_assignment_sha256"
                ],
                "local_dispatch_input_sha256": dispatch["local_dispatch_input_sha256"],
                "native_mapping_digest": native.digest(mapping),
                "domains": {
                    "accepted_role_snapshot": preparation["prepared_role_snapshot"],
                    "agent_configuration": configuration,
                    "accepted_task": round_record["accepted_task_domain"],
                    "result": result_domain,
                },
                "bindings": {
                    "role_snapshot_digest": f"sha256:{dispatch['local_prepared_role_snapshot_sha256']}",
                    "agent_configuration_digest": f"sha256:{native.digest(configuration)}",
                    "accepted_task_digest": f"sha256:{task_digest}",
                    "result_digest": f"sha256:{round_record['result_digest']}",
                },
                "native": {
                    **{
                        key: mapped[key]
                        for key in ("scope_ref", "supervisor_ref", "worker_ref")
                    },
                    "dispatch_ref": round_record["dispatch_ref"],
                    "task_ref": round_record["task_ref"],
                    "result_refs": round_record["result_refs"],
                    "delivery_ref": mapping_request["records"]["feedback"][-1][
                        "forwarded_result"
                    ]["uuid"]
                    if rounds_profile
                    else records["delivery"]["uuid"],
                },
                "unresolved_domains": [
                    "explicit_primary_acceptance",
                    "complete_lifetime_round_accounting",
                    "settlement_and_descendant_quiescence",
                    "podway_package_and_context_binding",
                    "durable_host_qualification",
                ],
                "next_action": "qualify_remaining_acceptance_domains",
            }
        )
        if rounds_profile:
            output["round_bindings"] = [
                {
                    "dispatch_ref": native_round["dispatch_ref"],
                    "task_ref": native_round["task_ref"],
                    "local_prepared_assignment_sha256": rendered[
                        "local_prepared_assignment_sha256"
                    ],
                    "local_dispatch_input_sha256": rendered[
                        "local_dispatch_input_sha256"
                    ],
                    "accepted_task_domain": native_round["accepted_task_domain"],
                    "result_domain": initial_result_domain
                    if index == 0
                    else native_round["result_domain"],
                    "accepted_task_digest": f"sha256:{native_round['accepted_task_digest']}",
                    "result_digest": f"sha256:{native_round['result_digest']}",
                }
                for index, (native_round, rendered) in enumerate(
                    zip(mapped["rounds"], dispatches)
                )
            ]
            output["native"]["feedback_run"] = mapped["feedback_run"]
        if profile == native.CLAUDE_LIFETIME_PROFILE:
            creation = {
                key: value
                for key, value in configuration.items()
                if key != "accepted_task_digest"
            }
            output["domains"]["agent_creation_configuration"] = creation
            output["bindings"]["agent_creation_configuration_digest"] = (
                f"sha256:{native.digest(creation)}"
            )
            output["native"]["feedback_runs"] = mapped["feedback_runs"]
            output["native"]["feedback_acknowledgements"] = mapped[
                "feedback_acknowledgements"
            ]
            output["unresolved_domains"].append(
                "serialized_lifetime_and_tool_history_host_qualification"
            )
            for index, entry in enumerate(output["round_bindings"]):
                envelope = {
                    **creation,
                    "accepted_task_digest": entry["accepted_task_digest"],
                }
                if index:
                    envelope["assignment_runtime"] = mapped["feedback_runs"][index - 1]
                    envelope["assignment_acknowledgement"] = mapped[
                        "feedback_acknowledgements"
                    ][index - 1]
                    envelope["acknowledgement_source_ref"] = mapping_request["records"][
                        "feedback"
                    ][index - 1]["delivery"]["uuid"]
                entry["agent_configuration_domain"] = envelope
                entry["agent_configuration_digest"] = (
                    f"sha256:{native.digest(envelope)}"
                )
                _require(
                    native.digest(entry["result_domain"])
                    == entry["result_digest"].removeprefix("sha256:"),
                    "RESULT_DOMAIN_MISMATCH",
                    "each round must preserve its own complete native result domain",
                )
            output["domains"]["agent_configuration"] = output["round_bindings"][-1][
                "agent_configuration_domain"
            ]
            output["bindings"]["agent_configuration_digest"] = output["round_bindings"][
                -1
            ]["agent_configuration_digest"]
    except BindingError as error:
        output.update(
            {
                "state": "reconciliation_required" if error.reconcile else "rejected",
                "error": {"code": error.code, "message": str(error)},
                "next_action": "reconcile_original_native_operation"
                if error.reconcile
                else "resolve_binding_gap",
            }
        )
    except (ValueError, TypeError):
        output.update(
            {
                "state": "rejected",
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "binding input must be finite JSON data",
                },
                "next_action": "resolve_binding_gap",
            }
        )
    return json.loads(native.canonical_bytes(output))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, help="binding request JSON file, or '-' for stdin"
    )
    args = parser.parse_args()
    try:
        payload = (
            sys.stdin.buffer.read()
            if args.input == "-"
            else Path(args.input).read_bytes()
        )
        request = json.loads(
            payload,
            object_pairs_hook=native._unique_keys,
            parse_constant=native._reject_constant,
        )
        if (
            not isinstance(request, dict)
            or set(request) != {"schema", "preparation", "mapping_request"}
            or request["schema"] != REQUEST_SCHEMA
        ):
            raise ValueError(
                f"request must be {REQUEST_SCHEMA} with preparation and mapping_request"
            )
        output = bind_delivery(request["preparation"], request["mapping_request"])
        sys.stdout.buffer.write(native.canonical_bytes(output) + b"\n")
        return 0 if output["state"] == "delivery_bound" else 2
    except (ValueError, TypeError, OSError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
