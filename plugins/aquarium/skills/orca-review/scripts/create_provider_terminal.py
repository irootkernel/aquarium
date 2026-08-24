#!/usr/bin/env python3
"""Create one Orca provider terminal from a consent-bound JSON request."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUEST_SCHEMA_VERSION = "aquarium-orca-provider-terminal-request/v1"
RESULT_SCHEMA_VERSION = "aquarium-orca-provider-terminal-result/v1"
ERROR_SCHEMA_VERSION = "aquarium-orca-provider-terminal-error/v1"
MAX_REQUEST_BYTES = 64 * 1024
SHA256 = frozenset("0123456789abcdef")


class RequestError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_string(value: object, code: str, message: str) -> str:
    if not isinstance(value, str) or "\0" in value:
        raise RequestError(code, message)
    return value


def canonical_entrypoint(
    descriptor: object, repository: Path, label: str
) -> tuple[Path, Path, str]:
    if not isinstance(descriptor, dict) or set(descriptor) != {
        "entrypoint",
        "canonical_target",
        "sha256",
    }:
        raise RequestError(
            f"{label}_identity_invalid", f"{label} identity is malformed"
        )
    entrypoint = Path(
        require_string(
            descriptor["entrypoint"],
            f"{label}_entrypoint_invalid",
            f"{label} entrypoint is invalid",
        )
    )
    expected_target = Path(
        require_string(
            descriptor["canonical_target"],
            f"{label}_target_invalid",
            f"{label} canonical target is invalid",
        )
    )
    expected_digest = require_string(
        descriptor["sha256"],
        f"{label}_digest_invalid",
        f"{label} digest is invalid",
    )
    if (
        not entrypoint.is_absolute()
        or not expected_target.is_absolute()
        or len(expected_digest) != 64
        or any(character not in SHA256 for character in expected_digest)
    ):
        raise RequestError(
            f"{label}_identity_invalid", f"{label} identity is malformed"
        )
    try:
        observed_target = entrypoint.resolve(strict=True)
        mode = observed_target.stat().st_mode
    except OSError as error:
        raise RequestError(
            f"{label}_unavailable", f"{label} entrypoint is unavailable"
        ) from error
    if observed_target != expected_target or not stat.S_ISREG(mode):
        raise RequestError(
            f"{label}_identity_changed", f"{label} identity changed before launch"
        )
    try:
        observed_target.relative_to(repository)
    except ValueError:
        pass
    else:
        raise RequestError(
            f"{label}_inside_repository",
            f"{label} canonical target must be outside the repository",
        )
    if sha256_file(observed_target) != expected_digest:
        raise RequestError(
            f"{label}_identity_changed", f"{label} digest changed before launch"
        )
    return entrypoint, observed_target, expected_digest


def parse_request(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "repository",
        "orca",
        "provider",
        "arguments",
        "title",
        "worktree",
    }:
        raise RequestError("request_invalid", "terminal request is malformed")
    if payload["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise RequestError(
            "schema_unsupported", "terminal request schema is unsupported"
        )
    repository = Path(
        require_string(
            payload["repository"],
            "repository_invalid",
            "repository path is invalid",
        )
    )
    try:
        repository = repository.resolve(strict=True)
    except OSError as error:
        raise RequestError(
            "repository_unavailable", "repository is unavailable"
        ) from error
    if not repository.is_absolute() or not repository.is_dir():
        raise RequestError("repository_invalid", "repository path is invalid")
    worktree = require_string(
        payload["worktree"], "worktree_invalid", "worktree selector is invalid"
    )
    if worktree != "current":
        raise RequestError("worktree_invalid", "worktree selector must be current")
    title = require_string(
        payload["title"], "title_invalid", "terminal title is invalid"
    )
    if not title or len(title) > 200:
        raise RequestError("title_invalid", "terminal title is invalid")
    arguments = payload["arguments"]
    if not isinstance(arguments, list) or not all(
        isinstance(argument, str) and "\0" not in argument for argument in arguments
    ):
        raise RequestError("arguments_invalid", "provider arguments are invalid")
    orca_entrypoint, _, _ = canonical_entrypoint(payload["orca"], repository, "orca")
    provider_entrypoint, provider_target, provider_digest = canonical_entrypoint(
        payload["provider"], repository, "provider"
    )
    return {
        "repository": repository,
        "worktree": worktree,
        "title": title,
        "arguments": arguments,
        "orca_entrypoint": orca_entrypoint,
        "provider_entrypoint": provider_entrypoint,
        "provider_target": provider_target,
        "provider_digest": provider_digest,
    }


def create_terminal(payload: object) -> dict[str, object]:
    request = parse_request(payload)
    if os.environ.get("ORCA_ENVIRONMENT") or os.environ.get("ORCA_PAIRING_CODE"):
        raise RequestError(
            "remote_routing_forbidden",
            "remote or paired Orca routing is forbidden for review",
        )
    provider_argv = [
        str(request["provider_entrypoint"]),
        *request["arguments"],
    ]
    command = shlex.join(provider_argv)
    result = subprocess.run(
        [
            str(request["orca_entrypoint"]),
            "terminal",
            "create",
            "--worktree",
            request["worktree"],
            "--title",
            request["title"],
            "--command",
            command,
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RequestError(
            "orca_terminal_create_failed", "Orca terminal creation failed"
        )
    try:
        orca_result = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RequestError(
            "orca_terminal_output_invalid", "Orca terminal output is not valid JSON"
        ) from error
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "provider_target": str(request["provider_target"]),
        "provider_sha256": request["provider_digest"],
        "provider_argv_sha256": hashlib.sha256(
            json.dumps(
                provider_argv, ensure_ascii=False, separators=(",", ":")
            ).encode()
        ).hexdigest(),
        "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
        "orca_result": orca_result,
    }


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise RequestError("request_oversized", "terminal request is too large")
        try:
            payload = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise RequestError(
                "request_invalid", "terminal request is not valid JSON"
            ) from error
        result = create_terminal(payload)
    except (OSError, RequestError, subprocess.TimeoutExpired) as error:
        if isinstance(error, RequestError):
            code = error.code
            message = str(error)
        elif isinstance(error, subprocess.TimeoutExpired):
            code = "orca_terminal_create_timeout"
            message = "Orca terminal creation timed out"
        else:
            code = "terminal_helper_failed"
            message = "terminal helper failed"
        print(
            json.dumps(
                {
                    "schema_version": ERROR_SCHEMA_VERSION,
                    "error": {"code": code, "message": message},
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
