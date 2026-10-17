#!/usr/bin/env python3
"""Select or prepare Procedure source from an ordinary Worker assignment."""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument(
        "--assignment",
        required=True,
        help="Ordinary aquarium.assignment/v2 JSON file, or - for stdin",
    )
    parser.add_argument(
        "--podway",
        help="Exact supported binary; required only for approved preparation",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Prepare initial suitability recording for a changed/new definition; unchanged reuse keeps its source.",
    )
    parser.add_argument(
        "--podway-opt-out",
        action="store_true",
        help="Continue ordinary Design without native or source preparation",
    )
    args = parser.parse_args()
    try:
        text = (
            sys.stdin.read()
            if args.assignment == "-"
            else Path(args.assignment).read_text()
        )
        assignment = json.loads(text)
    except (ValueError, OSError, RecursionError) as error:
        print(
            json.dumps(
                {"status": "invalid-input", "message": str(error), "details": {}}
            )
        )
        return 2
    from adaptive_entrypoint import EntryPointError, branch

    target = assignment.get("target", {}) if isinstance(assignment, dict) else {}
    plan = target.get("procedure_plan", {}) if isinstance(target, dict) else {}
    entrypoint = plan.get("entrypoint") if isinstance(plan, dict) else None
    try:
        skipped = branch(args.repository, entrypoint, opt_out=args.podway_opt_out)
    except EntryPointError as error:
        print(json.dumps({"status": error.code, "message": str(error), "details": {}}))
        return 2
    if skipped is not None:
        print(json.dumps(skipped, sort_keys=True))
        return 0
    try:
        from adaptive_admission import NativeClient
        from adaptive_bundles import BundleError
        from adaptive_definitions import DefinitionError
        from adaptive_preparation import prepare
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
        args.repository = str(Path(args.repository).expanduser().resolve())
        mode = assignment["target"]["procedure_plan"]["mode"]
        if mode == "prepare" and not args.podway:
            raise BundleError(
                "missing-prerequisite",
                "Approved preparation requires an explicit Podway binary",
            )
        client = (
            NativeClient(args.repository, args.podway) if mode == "prepare" else None
        )
        print(
            json.dumps(
                prepare(
                    args.repository,
                    assignment,
                    client=client,
                    bootstrap=args.bootstrap,
                    opt_out=args.podway_opt_out,
                ),
                sort_keys=True,
            )
        )
        return 0
    except (
        BundleError,
        DefinitionError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
        RecursionError,
    ) as error:
        code = getattr(error, "code", "invalid-input")
        if isinstance(error, DefinitionError):
            code = "incompatible"
        print(
            json.dumps(
                {
                    "status": code,
                    "message": str(error),
                    "details": getattr(error, "details", {}),
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
