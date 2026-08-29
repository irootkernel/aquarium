#!/usr/bin/env python3
"""Command-line boundary for the Aquarium development channel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

from dev_contract import (
    DEV_VERSION_RE,
    DIGEST_RE,
    SHA_RE,
    validate_error,
    validate_result,
)
from dev_manager import (
    ManagerError,
    cleanup_generation,
    configure_codex,
    diagnose,
    enroll,
    process_queue,
    queue_request,
    rebuild,
    repair_hook,
    resolve_artifact,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument(
        "--host-root",
        type=Path,
        default=Path.home() / ".aquarium",
        help=argparse.SUPPRESS,
    )
    value.add_argument("--codex-bin", default="codex", help=argparse.SUPPRESS)
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
    resolve_parser = commands.add_parser("resolve")
    resolve_parser.add_argument("--project-id", required=True)
    resolve_parser.add_argument("--stable", type=Path)
    launch_parser = commands.add_parser("launch")
    launch_parser.add_argument("--project-id", required=True)
    launch_parser.add_argument("--stable", type=Path)
    launch_parser.add_argument("--expected-git-sha")
    launch_parser.add_argument("--expected-development-version")
    launch_parser.add_argument("--expected-sha256")
    launch_parser.add_argument("arguments", nargs=argparse.REMAINDER)
    codex_parser = commands.add_parser("configure-codex")
    codex_parser.add_argument("--repository", type=Path, required=True)
    codex_parser.add_argument("--approve-codex", action="store_true")
    return value


def launch_guard(arguments: argparse.Namespace) -> tuple[str, str, str] | None:
    values = (
        arguments.expected_git_sha,
        arguments.expected_development_version,
        arguments.expected_sha256,
    )
    if not any(value is not None for value in values):
        return None
    if not all(value is not None for value in values):
        raise ManagerError(
            "invalid_arguments",
            "Exact launch guards must include Git SHA, development version, and SHA-256 together.",
            "Supply the complete expected generation identity or omit all three guards.",
            "launch",
            arguments.project_id,
        )
    git_sha, development_version, sha256 = values
    assert git_sha is not None
    assert development_version is not None
    assert sha256 is not None
    if (
        not SHA_RE.fullmatch(git_sha)
        or not DEV_VERSION_RE.fullmatch(development_version)
        or not DIGEST_RE.fullmatch(sha256)
    ):
        raise ManagerError(
            "invalid_arguments",
            "One or more exact launch guards have an invalid format.",
            "Supply a full lowercase Git SHA, development version, and prefixed SHA-256.",
            "launch",
            arguments.project_id,
        )
    return git_sha, development_version, sha256


def open_guarded_executable(resolved, expected_sha256: str) -> int:
    try:
        descriptor = os.open(resolved.execution_path, os.O_RDONLY | os.O_CLOEXEC)
    except OSError as error:
        raise ManagerError(
            "artifact_invalid",
            str(error),
            "Repair the selected executable artifact and retry.",
            "launch",
            resolved.project_id,
            resolved.git_sha,
        ) from error
    try:
        descriptor_stat = os.fstat(descriptor)
        path_stat = resolved.path.stat()
        execution_stat = resolved.execution_path.stat()
        if (
            not stat.S_ISREG(descriptor_stat.st_mode)
            or not os.access(resolved.path, os.X_OK)
            or (descriptor_stat.st_dev, descriptor_stat.st_ino)
            != (path_stat.st_dev, path_stat.st_ino)
            or (descriptor_stat.st_dev, descriptor_stat.st_ino)
            != (execution_stat.st_dev, execution_stat.st_ino)
        ):
            raise OSError("the executable path changed before launch")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        if f"sha256:{digest.hexdigest()}" != expected_sha256:
            raise OSError(
                "the opened executable checksum does not match the launch guard"
            )
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.set_inheritable(descriptor, True)
        return descriptor
    except OSError as error:
        os.close(descriptor)
        raise ManagerError(
            "artifact_invalid",
            str(error),
            "Resolve the intended immutable generation and retry with its exact guards.",
            "launch",
            resolved.project_id,
            resolved.git_sha,
        ) from error


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
            details = diagnose(
                arguments.repository, arguments.host_root, arguments.codex_bin
            )
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
        if arguments.command == "resolve":
            with resolve_artifact(
                arguments.project_id, arguments.host_root, arguments.stable
            ) as resolved:
                details = {
                    "source": resolved.source,
                    "path": str(resolved.path),
                    "git_sha": resolved.git_sha,
                    "development_version": resolved.development_version,
                    "sha256": resolved.sha256,
                }
            result(
                "resolve",
                "success",
                arguments.project_id,
                "Artifact resolved and validated.",
                details,
            )
            return 0
        if arguments.command == "launch":
            guard = launch_guard(arguments)
            launch_arguments = arguments.arguments
            if launch_arguments[:1] == ["--"]:
                launch_arguments = launch_arguments[1:]
            source_bearing_dolgorae = arguments.project_id == "dolgorae" and (
                launch_arguments[:2] == ["specialist", "review"]
                or launch_arguments[:2] in (
                    ["review-target", "capture"],
                    ["review-target", "settle"],
                )
            )
            if source_bearing_dolgorae and guard is None:
                raise ManagerError(
                    "invalid_arguments",
                    "Dolgorae review operations require a complete exact-generation guard set.",
                    "Supply the expected Git SHA, development version, and SHA-256.",
                    "launch",
                    arguments.project_id,
                )
            resolved = resolve_artifact(
                arguments.project_id, arguments.host_root, arguments.stable
            )
            if guard is not None and (
                resolved.source != "development"
                or guard
                != (resolved.git_sha, resolved.development_version, resolved.sha256)
            ):
                resolved.close()
                raise ManagerError(
                    "artifact_invalid",
                    "The resolved artifact does not match the complete expected generation identity.",
                    "Resolve the intended immutable generation and retry with its exact guards.",
                    "launch",
                    arguments.project_id,
                    resolved.git_sha,
                )
            executable_descriptor = (
                open_guarded_executable(resolved, guard[2])
                if guard is not None
                else None
            )
            if resolved.artifact_kind == "codex-plugin" or not resolved.path.is_file():
                resolved.close()
                raise ManagerError(
                    "artifact_invalid",
                    "The resolved artifact is not an executable file.",
                    "Use resolve for plugin artifacts and launch only executable tools.",
                    "launch",
                    arguments.project_id,
                    resolved.git_sha,
                )
            if resolved.lease is not None:
                os.set_inheritable(resolved.lease.fileno(), True)
            try:
                os.execv(
                    resolved.execution_path,
                    [str(resolved.path), *launch_arguments],
                )
            except OSError as error:
                if executable_descriptor is not None:
                    os.close(executable_descriptor)
                resolved.close()
                raise ManagerError(
                    "artifact_invalid",
                    str(error),
                    "Repair the selected executable artifact and retry.",
                    "launch",
                    arguments.project_id,
                    resolved.git_sha,
                ) from error
        if arguments.command == "configure-codex":
            status, details = configure_codex(
                arguments.repository,
                arguments.host_root,
                approve_codex=arguments.approve_codex,
                codex_bin=arguments.codex_bin,
            )
            result(
                "configure-codex",
                status,
                "aquarium",
                "Isolated Codex runtime reconciled.",
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
