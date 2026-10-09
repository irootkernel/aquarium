"""Bind a verified prepared role and assignment to a recomputed native delivery.

Call bind_delivery(preparation, mapping_request), or pass --input (file or '-')
with aquarium.prepared-delivery-request/v1 and exactly preparation/mapping_request.
The initial-spawn and serialized-idle-rounds collaboration profiles are supported.
Both helpers run independently; a supplied mapping cannot establish a binding.
The rounds profile requires a preparation for every acknowledged request, with
the same complete operative role snapshot throughout. Assignments may change.

The role digest retains the preparer's exact immutable role snapshot domain.
Its acknowledgement comes from the exact accepted operative dispatch text. The
closed configuration domain covers that snapshot, acknowledged fork_turns,
creation-resolved model/effort, their native creation source, and accepted task
binding. It does not inventory hidden host/system configuration. A constructor
request alone supplies no resolved configuration acknowledgement. Source
authenticity, dependency completeness and pre-dispatch journal capture remain
collector responsibilities. No source discovery or native configuration read
occurs. This helper performs no dispatch, acceptance, settlement or Podway work.

Digests cover compact sorted-key ASCII JSON without a final newline. Existing
local preparation digests remain bare hex; acceptance-field bindings use sha256:
prefixes. A successful binding still has caller-supplied unverified authenticity
and acceptance_ready=false. Preserve the original request for recovery.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REQUEST_SCHEMA = "aquarium.prepared-delivery-request/v1"
OUTPUT_SCHEMA = "aquarium.prepared-delivery-binding/v1"
CONFIGURATION_SCHEMA = "aquarium.accepted-agent-configuration/v1"


def _load_helper(name: str):
    spec = importlib.util.spec_from_file_location(
        f"aquarium_binding_{name}", Path(__file__).with_name(f"{name}.py")
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load required helper: {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


renderer = _load_helper("render_dispatch")
native = _load_helper("map_native_delivery")


class BindingError(ValueError):
    """Prepared assignment and public native acknowledgement cannot be bound."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def bind_delivery(preparation: dict, mapping_request: dict) -> dict:
    """Recompute both helpers and return a full binding or bounded rejection."""
    output = {
        "schema": OUTPUT_SCHEMA,
        "acceptance_ready": False,
        "redispatch_allowed": False,
        "record_authenticity": "caller_supplied_unverified",
    }
    try:
        output["request_digest"] = native.digest(
            {
                "schema": REQUEST_SCHEMA,
                "preparation": preparation,
                "mapping_request": mapping_request,
            }
        )
        if not isinstance(mapping_request, dict) or mapping_request.get(
            "profile"
        ) not in (
            native.CODEX_SPAWN_PROFILE,
            native.CODEX_ROUNDS_PROFILE,
            native.CODEX_SPAWN_V2_PROFILE,
            native.CODEX_ROUNDS_V2_PROFILE,
        ):
            raise BindingError(
                "UNSUPPORTED_PROFILE",
                "binding requires a journal-backed collaboration profile",
            )
        try:
            dispatch = renderer.render_dispatch(preparation)
        except (ValueError, TypeError) as error:
            raise BindingError(
                "INVALID_PREPARATION", "prepared role and assignment cannot be verified"
            ) from error
        mapping = native.map_delivery(mapping_request)
        if "expected_recovery_refs" in mapping:
            refs = mapping["expected_recovery_refs"]
            output["recovery_refs"] = {
                **{
                    key: refs[key]
                    for key in ("scope_ref", "supervisor_ref", "worker_ref")
                },
                "rounds": refs["rounds"],
            }
        if mapping["state"] != "delivery_mapped":
            output.update(
                {
                    "state": mapping["state"],
                    "error": {
                        "code": mapping["error"]["code"],
                        "message": "native delivery has not been mapped",
                    },
                    "next_action": mapping["next_action"],
                }
            )
            return json.loads(native.canonical_bytes(output))
        mapped = mapping["mapped"]
        profile = mapping_request["profile"]
        round_bindings = []
        if profile in (native.CODEX_ROUNDS_PROFILE, native.CODEX_ROUNDS_V2_PROFILE):
            records = mapping_request["records"]
            round_records = [records["initial"], *records["feedback"]]
            for index, (record, native_round) in enumerate(
                zip(round_records, mapped["rounds"])
            ):
                try:
                    round_dispatch = renderer.render_dispatch(record["preparation"])
                except (ValueError, TypeError) as error:
                    raise BindingError(
                        "INVALID_PREPARATION",
                        "each round preparation must verify independently",
                    ) from error
                if (
                    record["preparation"]["prepared_role_snapshot"]
                    != preparation["prepared_role_snapshot"]
                ):
                    raise BindingError(
                        "ROLE_SNAPSHOT_MISMATCH",
                        "serialized feedback must preserve the complete initial operative role snapshot",
                    )
                if (
                    native_round["accepted_task_domain"]["input"]["message"]
                    != round_dispatch["dispatch_text"]
                ):
                    raise BindingError(
                        "DISPATCH_INPUT_MISMATCH",
                        "each acknowledged round must match its exact rendered preparation",
                    )
                child = (
                    record["child_read"] if index == 0 else record["after_child_read"]
                )
                result = {
                    "schema": "aquarium.native-result-domain/v1",
                    "profile": native_round["accepted_task_domain"]["profile"],
                    "accepted_task_digest": native_round["accepted_task_digest"],
                    "result": [
                        item
                        for item in child["thread"]["turns"][-1]["items"]
                        if item["id"] in native_round["result_refs"]
                    ],
                }
                if native.digest(result) != native_round["result_digest"]:
                    raise BindingError(
                        "RESULT_DOMAIN_MISMATCH",
                        "round result differs from recomputed native delivery",
                    )
                round_bindings.append(
                    {
                        "dispatch_ref": native_round["dispatch_ref"],
                        "task_ref": native_round["task_ref"],
                        "local_prepared_assignment_sha256": round_dispatch[
                            "local_prepared_assignment_sha256"
                        ],
                        "local_dispatch_input_sha256": round_dispatch[
                            "local_dispatch_input_sha256"
                        ],
                        "accepted_task_domain": native_round["accepted_task_domain"],
                        "result_domain": result,
                        "accepted_task_digest": f"sha256:{native_round['accepted_task_digest']}",
                        "result_digest": f"sha256:{native_round['result_digest']}",
                    }
                )
        round_record = mapped["rounds"][-1]
        task_domain = round_record["accepted_task_domain"]
        arguments = task_domain["input"]
        if arguments["message"] != dispatch["dispatch_text"]:
            raise BindingError(
                "DISPATCH_INPUT_MISMATCH",
                "accepted native message differs from the verified prepared dispatch",
            )
        controls = mapped["creation_controls"]
        for key in ("model", "reasoning_effort"):
            if not isinstance(controls[key], str) or not controls[key].strip():
                raise BindingError(
                    "RESOLVED_CONTROLS_REQUIRED",
                    "native creation must acknowledge both model and effort",
                )
        task_digest = round_record["accepted_task_digest"]
        role_snapshot = preparation["prepared_role_snapshot"]
        configuration = {
            "schema": CONFIGURATION_SCHEMA,
            "role_snapshot": role_snapshot,
            "controls": {
                "fork_turns": mapped["rounds"][0]["accepted_task_domain"]["input"][
                    "fork_turns"
                ],
                "model": controls["model"],
                "reasoning_effort": controls["reasoning_effort"],
            },
            "native_creation": {
                "scope_ref": mapped["scope_ref"],
                "supervisor_ref": mapped["supervisor_ref"],
                "worker_ref": mapped["worker_ref"],
                "source_ref": controls["source_ref"],
            },
            "accepted_task_digest": f"sha256:{task_digest}",
        }
        child_read = (
            mapping_request["records"]["feedback"][-1]["after_child_read"]
            if profile in (native.CODEX_ROUNDS_PROFILE, native.CODEX_ROUNDS_V2_PROFILE)
            else mapping_request["records"]["child_read"]
        )
        items = child_read["thread"]["turns"][-1]["items"]
        result_domain = {
            "schema": "aquarium.native-result-domain/v1",
            "profile": task_domain["profile"],
            "accepted_task_digest": task_digest,
            "result": [
                item for item in items if item["id"] in round_record["result_refs"]
            ],
        }
        if native.digest(result_domain) != round_record["result_digest"]:
            raise BindingError(
                "RESULT_DOMAIN_MISMATCH",
                "complete result domain differs from the recomputed delivery",
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
                    "accepted_role_snapshot": role_snapshot,
                    "agent_configuration": configuration,
                    "accepted_task": task_domain,
                    "result": result_domain,
                },
                "bindings": {
                    "role_snapshot_digest": f"sha256:{dispatch['local_prepared_role_snapshot_sha256']}",
                    "agent_configuration_digest": f"sha256:{native.digest(configuration)}",
                    "accepted_task_digest": f"sha256:{task_digest}",
                    "result_digest": f"sha256:{round_record['result_digest']}",
                },
                "native": {
                    key: mapped[key]
                    for key in (
                        "scope_ref",
                        "supervisor_ref",
                        "worker_ref",
                        "native_agent_path",
                    )
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
        output["native"].update(
            {
                "creation_ref": controls["source_ref"],
                "task_ref": round_record["task_ref"],
                "result_refs": round_record["result_refs"],
            }
        )
        if round_bindings:
            output["round_bindings"] = round_bindings
    except BindingError as error:
        output.update(
            {
                "state": "rejected",
                "error": {"code": error.code, "message": str(error)},
                "next_action": "resolve_binding_gap",
            }
        )
    except (ValueError, TypeError):
        output.update(
            {
                "state": "rejected",
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "binding input must be valid JSON data",
                },
                "next_action": "resolve_binding_gap",
            }
        )
    return json.loads(native.canonical_bytes(output))


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
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
            payload, object_pairs_hook=_unique_keys, parse_constant=_reject_constant
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
