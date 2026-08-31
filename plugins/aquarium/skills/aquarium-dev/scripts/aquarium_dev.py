#!/usr/bin/env python3
"""Command-line boundary for the Aquarium development channel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dev_contract import validate_error, validate_result
from dev_manager import (
    ManagerError,
    apply_managed_service,
    cleanup_generation,
    diagnose,
    enroll,
    install_launcher,
    plan_managed_service,
    process_queue,
    queue_request,
    rebuild,
    repair_hook,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument(
        "--host-root",
        type=Path,
        default=Path.home() / ".aquarium-dev",
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
    request_parser = commands.add_parser("request")
    request_parser.add_argument("--repository", type=Path, required=True)
    rebuild_parser = commands.add_parser("rebuild")
    rebuild_parser.add_argument("--repository", type=Path, required=True)
    rebuild_parser.add_argument("--approve-build", action="store_true")
    worker_parser = commands.add_parser("worker", help=argparse.SUPPRESS)
    worker_parser.add_argument("--project-id", required=True, help=argparse.SUPPRESS)
    cleanup_parser = commands.add_parser("cleanup", help=argparse.SUPPRESS)
    cleanup_parser.add_argument("--project-id", required=True, help=argparse.SUPPRESS)
    cleanup_parser.add_argument("--git-sha", required=True, help=argparse.SUPPRESS)
    launcher_parser = commands.add_parser("install-launcher")
    launcher_parser.add_argument(
        "--target", type=Path, default=Path.home() / ".local" / "bin" / "aquarium-dev"
    )
    launcher_parser.add_argument("--approve-launcher", action="store_true")
    service_plan_parser = commands.add_parser("service-plan")
    service_plan_parser.add_argument("--project-id", required=True)
    service_apply_parser = commands.add_parser("service-apply")
    service_apply_parser.add_argument("--project-id", required=True)
    service_apply_parser.add_argument("--plan-token", required=True)
    service_apply_parser.add_argument("--approve-service", action="store_true")
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
        if arguments.command == "repair-hook":
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
        if arguments.command == "request":
            status, details = queue_request(
                arguments.repository,
                arguments.host_root,
                Path(__file__),
            )
            result(
                "publish",
                status,
                details["project_id"],
                "Build request queued.",
                details,
            )
            return 0
        if arguments.command == "rebuild":
            status, details = rebuild(
                arguments.repository,
                arguments.host_root,
                approve_build=arguments.approve_build,
            )
            result(
                "rebuild",
                status,
                details["project_id"],
                "Development artifact reconciled.",
                details,
            )
            return 0
        if arguments.command == "cleanup":
            status, details = cleanup_generation(
                arguments.project_id,
                arguments.git_sha,
                arguments.host_root,
                wait=True,
            )
            result(
                "publish",
                status,
                arguments.project_id,
                "Superseded generation cleanup reconciled.",
                details,
            )
            return 0
        if arguments.command == "install-launcher":
            status, details = install_launcher(
                Path(__file__).with_name("aquarium_dev_launcher.py"),
                arguments.target,
                approve_launcher=arguments.approve_launcher,
            )
            result(
                "install-launcher",
                status,
                None,
                "Aquarium development launcher reconciled.",
                details,
            )
            return 0
        if arguments.command == "service-plan":
            status, details = plan_managed_service(
                arguments.project_id, arguments.host_root
            )
            result(
                "service-plan",
                status,
                arguments.project_id,
                "Managed-service activation planned.",
                details,
            )
            return 0
        if arguments.command == "service-apply":
            status, details = apply_managed_service(
                arguments.project_id,
                arguments.host_root,
                arguments.plan_token,
                approve_service=arguments.approve_service,
            )
            result(
                "service-apply",
                status,
                arguments.project_id,
                "Managed-service activation reconciled.",
                details,
            )
            return 0
        status, details = process_queue(arguments.project_id, arguments.host_root)
        result(
            "publish",
            status,
            arguments.project_id,
            "Queued build requests processed.",
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
