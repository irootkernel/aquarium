#!/usr/bin/env python3
"""Inspect, retain or recover an exact known Procedure; never start a session."""

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inspect", "retain", "resume"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--root", action="append", required=True)
    parser.add_argument("--source")
    parser.add_argument("--write-root")
    parser.add_argument("--entrypoint", required=True)
    parser.add_argument("--review-route")
    parser.add_argument("--bootstrap")
    parser.add_argument("--customization-basis")
    parser.add_argument("--podway", default=shutil.which("podway"))
    arguments = parser.parse_args()
    try:
        from adaptive_admission import (
            NativeClient,
            resume_selected,
            retain_selected,
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
        if not arguments.podway:
            raise BundleError(
                "missing-prerequisite", "Podway executable is unavailable"
            )
        if arguments.action != "resume" and not arguments.source:
            raise BundleError(
                "invalid-arguments", "Source is required for inspect or retain"
            )
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
        if arguments.action == "resume":
            if observation is None:
                raise BundleError(
                    "missing-session", "There is no native session to resume"
                )
            bundle = resume_selected(
                arguments.repository,
                arguments.root,
                observation["status"]["procedure"],
                client=client,
                bootstrap=arguments.bootstrap,
            )
            arguments.source = str(Path(bundle["path"]) / "procedure.yaml")
        if not arguments.source:
            raise BundleError(
                "invalid-arguments", "Source is required for inspect or retain"
            )
        kwargs = {
            "roots": arguments.root,
            "entrypoint": arguments.entrypoint,
            "route": arguments.review_route,
            "runtime_ready": True,
            "client": client,
        }
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
    except (BundleError, ValueError, KeyError, OSError) as error:
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
