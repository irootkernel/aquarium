#!/usr/bin/env python3
"""Qualify exact prepared source and request or import its pre-start Evaluator assessment."""

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
        help="Ordinary prepared aquarium.assignment/v3 JSON file or -",
    )
    parser.add_argument(
        "--assessment", help="Actual aquarium.evaluator-assessment/v3 JSON file"
    )
    parser.add_argument(
        "--podway", required=True, help="Exact supported source-check binary"
    )
    parser.add_argument(
        "--retain",
        action="store_true",
        help="Retain the qualified exact bundle under the assignment's existing local preparation grant",
    )
    parser.add_argument(
        "--combined-task-plan",
        action="store_true",
        help="Include the compatible due Task plan assessment in this exact Evaluator scope",
    )
    args = parser.parse_args()
    try:
        from adaptive_admission import NativeClient
        from adaptive_bundles import BundleError, sha256
        from adaptive_definitions import DefinitionError
        from adaptive_suitability import qualify_prepared
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
        assignment = json.loads(
            sys.stdin.read()
            if args.assignment == "-"
            else Path(args.assignment).read_text()
        )
        assessment = (
            json.loads(Path(args.assessment).read_text()) if args.assessment else None
        )
        result = qualify_prepared(
            args.repository,
            assignment,
            client=NativeClient(args.repository, args.podway),
            assessment=assessment,
            retain=args.retain,
            combined_task_plan=args.combined_task_plan,
        )
        if result.get("retention") is not None:
            retained = result["retention"]
            source = retained["source"]
            result["retention"] = {
                **retained,
                "source": {"sha256": sha256(source), "byte_size": len(source)},
            }
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] != "assessment-required" else 3
    except (
        BundleError,
        DefinitionError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
        RecursionError,
    ) as error:
        print(
            json.dumps(
                {
                    "status": getattr(error, "code", "invalid-input"),
                    "message": str(error),
                    "details": getattr(error, "details", {}),
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
