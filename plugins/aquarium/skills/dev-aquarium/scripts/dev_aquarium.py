#!/usr/bin/env python3
"""Command-line boundary for the Aquarium development channel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dev_contract import validate_error, validate_result
from dev_manager import ManagerError, diagnose, enroll, repair_hook


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument(
        "--host-root",
        type=Path,
        default=Path.home() / ".aquarium",
        help=argparse.SUPPRESS,
    )
    commands = value.add_subparsers(dest="command", required=True)
    diagnose_parser = commands.add_parser("diagnose")
    diagnose_parser.add_argument("--repository", type=Path, required=True)
    enroll_parser = commands.add_parser("enroll")
    enroll_parser.add_argument("--repository", type=Path, required=True)
    enroll_parser.add_argument("--approve-enrollment", action="store_true")
    enroll_parser.add_argument("--approve-hook", action="store_true")
    enroll_parser.add_argument("--approve-reenrollment", action="store_true")
    repair_parser = commands.add_parser("repair-hook")
    repair_parser.add_argument("--repository", type=Path, required=True)
    repair_parser.add_argument("--approve-hook", action="store_true")
    return value


def result(operation: str, status: str, project_id: str | None, message: str, details):
    value = {
        "schema": "aquarium-dev-manager-result/v1",
        "operation": operation,
        "status": status,
        "project_id": project_id,
        "message": message,
        "details": details,
    }
    validate_result(value)
    print(json.dumps(value, sort_keys=True))


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.command == "diagnose":
            details = diagnose(arguments.repository, arguments.host_root)
            result(
                "diagnose",
                "diagnosed",
                details["description"]["project_id"],
                "Diagnosis complete.",
                details,
            )
            return 0
        if arguments.command == "enroll":
            status, details = enroll(
                arguments.repository,
                arguments.host_root,
                Path(__file__),
                approve_enrollment=arguments.approve_enrollment,
                approve_hook=arguments.approve_hook,
                approve_reenrollment=arguments.approve_reenrollment,
            )
            result(
                "enroll",
                status,
                details["description"]["project_id"],
                "Enrollment reconciled.",
                details,
            )
            return 0
        status, details = repair_hook(
            arguments.repository,
            arguments.host_root,
            Path(__file__),
            approve_hook=arguments.approve_hook,
        )
        result(
            "repair",
            status,
            details["description"]["project_id"],
            "Hook reconciled.",
            details,
        )
        return 0
    except ManagerError as error:
        value = {
            "schema": "aquarium-dev-error/v1",
            "error": {
                "code": error.code,
                "message": error.message,
                "action": error.action,
                "stage": error.stage,
                "project_id": error.project_id,
                "git_sha": error.git_sha,
            },
        }
        validate_error(value)
        print(json.dumps(value, sort_keys=True), file=sys.stderr)
        return 2 if error.code in {"approval_required", "invalid_arguments"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
