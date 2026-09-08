#!/usr/bin/env python3
"""Command-line boundary for the Aquarium development channel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aquarium_dev_launcher import SUPPORTED_DEVELOPMENT_COMMANDS
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
    value = JsonArgumentParser(
        prog="aquarium-dev",
        description=__doc__,
        epilog="Use 'aquarium-dev version' for runtime identity, 'aquarium-dev mcp' for stdio, or 'aquarium-dev <tool> [args...]' to run podway, mulgae, gaori, sanho, or dolgorae.",
    )
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
    return value


def execute(arguments: argparse.Namespace) -> dict:
    if arguments.command == "diagnose":
        details = diagnose(arguments.repository, arguments.host_root, hook_entrypoint())
        return result(
            "diagnose",
            "diagnosed",
            details["description"]["project_id"],
            "Diagnosis complete.",
            details,
        )
    if arguments.command == "enroll":
        status, details = enroll(
            arguments.repository,
            arguments.host_root,
            hook_entrypoint(),
            approve_enrollment=arguments.approve_enrollment,
            approve_hook=arguments.approve_hook,
            approve_reenrollment=arguments.approve_reenrollment,
        )
        return result(
            "enroll",
            status,
            details["description"]["project_id"],
            "Enrollment reconciled.",
            details,
        )
    if arguments.command == "repair-hook":
        status, details = repair_hook(
            arguments.repository,
            arguments.host_root,
            hook_entrypoint(),
            approve_hook=arguments.approve_hook,
        )
        return result(
            "repair",
            status,
            details["description"]["project_id"],
            "Hook reconciled.",
            details,
        )
    if arguments.command == "request":
        status, details = queue_request(
            arguments.repository,
            arguments.host_root,
            Path(__file__),
        )
        return result(
            "publish",
            status,
            details["project_id"],
            "Build request queued.",
            details,
        )
    if arguments.command == "rebuild":
        status, details = rebuild(
            arguments.repository,
            arguments.host_root,
            approve_build=arguments.approve_build,
        )
        return result(
            "rebuild",
            status,
            details["project_id"],
            "Development artifact reconciled.",
            details,
        )
    if arguments.command == "cleanup":
        status, details = cleanup_generation(
            arguments.project_id,
            arguments.git_sha,
            arguments.host_root,
            wait=True,
        )
        return result(
            "publish",
            status,
            arguments.project_id,
            "Superseded generation cleanup reconciled.",
            details,
        )
    if arguments.command == "install-launcher":
        status, details = install_launcher(
            Path(__file__).with_name("runtime_entry.py"),
            arguments.target,
            approve_launcher=arguments.approve_launcher,
        )
        return result(
            "install-launcher",
            status,
            None,
            "Aquarium development launcher reconciled.",
            details,
        )
    if arguments.command == "service-plan":
        status, details = plan_managed_service(
            arguments.project_id, arguments.host_root
        )
        return result(
            "service-plan",
            status,
            arguments.project_id,
            "Managed-service activation planned.",
            details,
        )
    if arguments.command == "service-apply":
        status, details = apply_managed_service(
            arguments.project_id,
            arguments.host_root,
            arguments.plan_token,
            approve_service=arguments.approve_service,
        )
        return result(
            "service-apply",
            status,
            arguments.project_id,
            "Managed-service activation reconciled.",
            details,
        )
    status, details = process_queue(arguments.project_id, arguments.host_root)
    return result(
        "publish",
        status,
        arguments.project_id,
        "Queued build requests processed.",
        details,
    )


def error_result(error: ManagerError) -> dict:
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
    return value


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ManagerError(
            "invalid_arguments", message, "Run aquarium-dev --help.", "arguments"
        )


def hook_entrypoint() -> Path:
    if Path(__file__).with_name("runtime.json").is_file():
        return Path.home() / ".local/bin/aquarium-dev"
    return Path(__file__)


def invoke(arguments: list[str]) -> tuple[dict, int]:
    try:
        return execute(parser().parse_args(arguments)), 0
    except ManagerError as error:
        return error_result(error), 2 if error.code in {
            "approval_required",
            "invalid_arguments",
        } else 1
    except Exception as error:  # noqa: BLE001 - Public CLI/MCP error envelope boundary.
        return error_result(
            ManagerError(
                "internal_error",
                str(error),
                "Diagnose the current state before retrying; the operation may have applied effects.",
                "execute",
            )
        ), 1


def main(arguments: list[str] | None = None) -> int:
    command = list(sys.argv[1:] if arguments is None else arguments)
    if command and command[0] in SUPPORTED_DEVELOPMENT_COMMANDS:
        from aquarium_dev_launcher import main as launch

        return launch(command)
    if command and command[0] == "mcp":
        from mcp_server import main as serve

        return serve()
    if command and command[0] in {"version", "--version"}:
        from runtime_entry import bundled_identity

        receipt_path = Path(__file__).with_name("runtime.json")
        receipt = (
            json.loads(receipt_path.read_text())
            if receipt_path.exists()
            else bundled_identity(Path(__file__).parent)
        )
        print(json.dumps(receipt, sort_keys=True))
        return 0
    value, exit_code = invoke(command)
    print(
        json.dumps(value, sort_keys=True), file=sys.stderr if exit_code else sys.stdout
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
