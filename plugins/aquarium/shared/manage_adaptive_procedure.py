#!/usr/bin/env python3
"""Inspect or recover admitted work; explicitly consented atomic replacement is separate."""

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path


def transition_json(path):
    from adaptive_bundles import BundleError

    try:
        return json.loads(Path(path).read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BundleError(
            "invalid-input", "Transition input is not readable JSON"
        ) from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "inspect",
            "retain",
            "resume",
            "context",
            "transition-plan",
            "transition",
            "transition-recover",
        ),
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--root", action="append", default=[])
    parser.add_argument("--source")
    parser.add_argument("--write-root")
    parser.add_argument("--entrypoint")
    parser.add_argument("--review-route")
    parser.add_argument(
        "--podway-opt-out",
        action="store_true",
        help="Use the approved ordinary Design path without Podway discovery or rendering",
    )
    parser.add_argument("--bootstrap")
    parser.add_argument("--session", help="Exact continuation session ID")
    parser.add_argument("--binding", help="Exact adaptive binding JSON path")
    parser.add_argument(
        "--qualification", help="Ordinary assignment/assessment context JSON file"
    )
    parser.add_argument("--customization-basis")
    parser.add_argument("--podway")
    parser.add_argument(
        "--transition-input",
        help="Disclosed transition arguments or retained exact checkpoint JSON",
    )
    parser.add_argument(
        "--consent", help="Actual explicit user consent for the exact disclosure JSON"
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="After native lookup and readback, replay only the original request/key",
    )
    arguments = parser.parse_args()
    from adaptive_entrypoint import EntryPointError, branch

    try:
        skipped = branch(
            arguments.repository, arguments.entrypoint, opt_out=arguments.podway_opt_out
        )
    except EntryPointError as error:
        print(
            json.dumps(
                {
                    "status": error.code,
                    "message": str(error),
                    "interpreter": sys.executable,
                    "details": {},
                }
            )
        )
        return 2
    if skipped is not None:
        print(json.dumps(skipped, sort_keys=True))
        return 0
    if arguments.entrypoint is None:
        parser.error("Native admission requires --entrypoint")
    if not arguments.root:
        parser.error("Native admission requires at least one approved --root")
    try:
        from adaptive_admission import (
            NativeClient,
            retain_selected,
            selected_session,
            selected_source,
            session_context,
        )
        from adaptive_bundles import BundleError, sha256
    except ModuleNotFoundError as error:
        print(
            json.dumps(
                {
                    "status": "missing-prerequisite",
                    "dependency": error.name,
                    "interpreter": sys.executable,
                }
            )
        )
        return 2
    try:
        arguments.podway = arguments.podway or shutil.which("podway")
        if not arguments.podway:
            raise BundleError(
                "missing-prerequisite", "Podway executable is unavailable"
            )
        if arguments.action in {"inspect", "retain"} and not arguments.source:
            raise BundleError(
                "invalid-arguments", "Source is required for inspect or retain"
            )
        qualification = (
            (
                transition_json(arguments.qualification)
                if arguments.action.startswith("transition")
                else json.loads(Path(arguments.qualification).read_text())
            )
            if arguments.qualification
            else None
        )
        if qualification is not None:
            from adaptive_execution import invocation_assignment

            invocation_assignment(qualification)
        inspector_path = (
            Path(__file__).resolve().parents[1]
            / "skills/dev-setup/scripts/inspect_tools.py"
        )
        spec = importlib.util.spec_from_file_location(
            "adaptive_setup_inspector", inspector_path
        )
        inspector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inspector)
        try:
            arguments.repository = str(
                inspector.resolve_repository(arguments.repository, 30)
            )
            if arguments.action.startswith("transition"):
                from adaptive_supersede import (
                    execute_transition,
                    prepare_transition,
                    recover_transition,
                )

                if not arguments.transition_input or qualification is None:
                    raise BundleError(
                        "invalid-arguments",
                        "Transition needs its ordinary qualification and exact input",
                    )
                value = transition_json(arguments.transition_input)
                if not isinstance(value, dict):
                    raise BundleError(
                        "invalid-input", "Transition input must be an object"
                    )
                client = NativeClient(arguments.repository, arguments.podway)
                if arguments.action == "transition-plan":
                    fields = {
                        "title",
                        "reason",
                        "missing_topology",
                        "pending_operations",
                        "remaining_authority",
                        "effects_reconciled",
                        "idempotency_key",
                    }
                    if not fields.issubset(value) or {
                        "repository",
                        "roots",
                        "qualification",
                        "client",
                    }.intersection(value):
                        raise BundleError(
                            "invalid-input",
                            "Transition plan has missing or conflicting inputs",
                        )
                    if not isinstance(value["effects_reconciled"], bool):
                        raise BundleError(
                            "invalid-input", "effects_reconciled must be a boolean"
                        )
                    result = prepare_transition(
                        arguments.repository,
                        roots=arguments.root,
                        qualification=qualification,
                        client=client,
                        **{name: value[name] for name in fields},
                    )
                else:
                    consent = (
                        transition_json(arguments.consent)
                        if arguments.consent
                        else None
                    )
                    kwargs = {
                        "checkpoint": value,
                        "consent": consent,
                        "qualification": qualification,
                        "client": client,
                    }
                    result = (
                        recover_transition(
                            arguments.repository, replay=arguments.replay, **kwargs
                        )
                        if arguments.action == "transition-recover"
                        else execute_transition(arguments.repository, **kwargs)
                    )
                print(json.dumps(result, sort_keys=True))
                return 0
            if arguments.action == "context":
                from adaptive_execution import execution_context

                result = execution_context(
                    arguments.repository,
                    roots=arguments.root,
                    entrypoint=arguments.entrypoint,
                    qualification=qualification,
                    client=NativeClient(arguments.repository, arguments.podway),
                    session=arguments.session,
                    bootstrap=arguments.bootstrap,
                    route=arguments.review_route,
                )
                print(json.dumps(result, sort_keys=True))
                return 0
            diagnostic = inspector.inspect_selected_podway(
                Path(arguments.repository),
                30,
                source=arguments.source,
                roots=arguments.root,
                entrypoint=arguments.entrypoint,
                route=arguments.review_route,
                resume=arguments.action == "resume",
                bootstrap=arguments.bootstrap,
                customization_basis=arguments.customization_basis,
                executable=arguments.podway,
                binding_path=arguments.binding,
                qualification=qualification,
            )
        except inspector.InspectionError as error:
            raise BundleError(
                error.code, str(error), {"inspection_exit_code": error.exit_code}
            ) from error
        selected = diagnostic["selected_procedure"]
        if selected["status"] != "ready" and not (
            arguments.action == "retain" and selected["status"] == "session-conflict"
        ):
            raise BundleError(
                selected["status"],
                selected.get("message", "Selected source needs reconciliation"),
                selected.get("details", selected),
            )
        client = NativeClient(arguments.repository, arguments.podway)
        observation = client.health()
        kwargs = {
            "roots": arguments.root,
            "entrypoint": arguments.entrypoint,
            "route": arguments.review_route,
            "client": client,
            "qualification": qualification,
        }
        if arguments.action == "resume":
            if observation is None:
                raise BundleError(
                    "missing-session", "There is no native session to resume"
                )
            result = selected_session(
                arguments.repository,
                observation["status"]["procedure"],
                bootstrap=arguments.bootstrap,
                **kwargs,
            )
        else:
            if not arguments.source:
                raise BundleError(
                    "invalid-arguments", "Source is required for inspect or retain"
                )
            kwargs.update(runtime_ready=True, binding_path=arguments.binding)
            if arguments.action == "retain":
                if not arguments.write_root:
                    raise BundleError(
                        "invalid-arguments", "Retention needs an approved write root"
                    )
                result = retain_selected(
                    arguments.repository,
                    Path(arguments.source),
                    write_root=arguments.write_root,
                    **kwargs,
                )
            else:
                result = selected_source(
                    arguments.repository, Path(arguments.source), **kwargs
                )
        result["session"] = session_context(observation, result["binding"])
        if arguments.action == "retain":
            result["status"] = "retained"
        elif result["session"].get("definition_conflict"):
            result["status"] = "session-conflict"

        def public(value):
            if isinstance(value, bytes):
                return {"sha256": sha256(value), "byte_size": len(value)}
            if isinstance(value, dict):
                return {key: public(item) for key, item in value.items()}
            if isinstance(value, list):
                return [public(item) for item in value]
            return value

        print(json.dumps(public(result), sort_keys=True))
        return 2 if result["status"] == "session-conflict" else 0
    except (BundleError, ValueError, KeyError, TypeError, OSError) as error:
        print(
            json.dumps(
                {
                    "status": getattr(error, "code", "runtime-failure"),
                    "message": str(error),
                    "interpreter": sys.executable,
                    "details": getattr(error, "details", {}),
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
