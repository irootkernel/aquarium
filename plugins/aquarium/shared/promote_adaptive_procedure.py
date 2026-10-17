#!/usr/bin/env python3
"""Offer or apply an exact, separately consented Procedure-library promotion."""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("offer", "apply"))
    parser.add_argument("--repository", required=True)
    parser.add_argument(
        "--input", required=True, help="Ordinary closeout JSON, or - for stdin"
    )
    parser.add_argument(
        "--podway", required=True, help="Explicit supported native binary"
    )
    args = parser.parse_args()
    try:
        from adaptive_admission import NativeClient
        from adaptive_bundles import BundleError
        from adaptive_definitions import DefinitionError
        from adaptive_promotion import apply, offer
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
        data = json.loads(
            sys.stdin.read() if args.input == "-" else Path(args.input).read_text()
        )
        if not isinstance(data, dict):
            raise BundleError("invalid-input", "Closeout input must be an object")
        repository = Path(args.repository).expanduser().resolve()
        client = NativeClient(repository, args.podway)
        result = (
            offer(repository, data, client)
            if args.operation == "offer"
            else apply(
                repository,
                data["proposal"],
                data["decision"],
                data["finalization"],
                client,
                commit_grant=data.get("commit_grant"),
            )
        )
        print(json.dumps(result, sort_keys=True))
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
