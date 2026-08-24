#!/usr/bin/env python3
"""Inspect one exact Git target for Aquarium independent review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "aquarium-independent-review-target/v1"
ERROR_SCHEMA_VERSION = "aquarium-independent-review-target-error/v1"
RANGE = re.compile(r"^(.+?)(\.\.\.?)(.+)$")
CONFLICT_CODES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}


class InspectionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InspectionError("invalid_arguments", "invalid command-line arguments")


def git_command(
    repository: Path, arguments: list[str]
) -> subprocess.CompletedProcess[bytes]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
    }
    return subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        env=environment,
        timeout=30,
    )


def require_git(
    repository: Path, arguments: list[str], code: str, message: str
) -> bytes:
    result = git_command(repository, arguments)
    if result.returncode != 0:
        raise InspectionError(code, message)
    return result.stdout


def decode_utf8(value: bytes, code: str, message: str) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeError as error:
        raise InspectionError(code, message) from error


def canonical_git_root(requested: Path) -> Path:
    if not requested.is_absolute():
        raise InspectionError("repository_not_absolute", "repository must be absolute")
    output = require_git(
        requested,
        ["rev-parse", "--show-toplevel"],
        "repository_not_git",
        "repository must be a Git worktree",
    )
    root = Path(
        decode_utf8(
            output, "repository_path_invalid", "Git root is not valid UTF-8"
        ).strip()
    )
    if not root.is_absolute() or root != requested:
        raise InspectionError(
            "repository_not_root",
            "repository must be the exact canonical Git worktree root",
        )
    return root


def resolve_commit(repository: Path, revision: str) -> str:
    if not revision or any(character in revision for character in "\0\r\n"):
        raise InspectionError("revision_invalid", "revision is invalid")
    output = require_git(
        repository,
        ["rev-parse", "--verify", f"{revision}^{{commit}}"],
        "revision_unresolved",
        "revision does not resolve to one commit",
    )
    value = decode_utf8(
        output, "revision_invalid", "resolved revision is not valid UTF-8"
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", value):
        raise InspectionError("revision_invalid", "resolved revision is malformed")
    return value


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def target_digest(target: dict[str, Any]) -> str:
    encoded = json.dumps(
        target, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return sha256(encoded)


def parse_status(output: bytes) -> dict[str, Any]:
    records = output.split(b"\0")
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []
    ignored: list[str] = []
    conflicts: list[str] = []
    path_changes: list[dict[str, str]] = []
    index = 0

    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2:3] != b" ":
            raise InspectionError(
                "git_status_invalid", "Git status output is malformed"
            )
        code = decode_utf8(
            record[:2], "git_status_invalid", "Git status code is not valid UTF-8"
        )
        destination = decode_utf8(
            record[3:], "git_path_invalid", "a Git path is not valid UTF-8"
        )
        source: str | None = None
        if code[0] in {"R", "C"} or code[1] in {"R", "C"}:
            if index >= len(records) or not records[index]:
                raise InspectionError(
                    "git_status_invalid", "Git rename status is malformed"
                )
            source = decode_utf8(
                records[index],
                "git_path_invalid",
                "a Git rename source is not valid UTF-8",
            )
            index += 1
            path_changes.append(
                {
                    "status": code,
                    "kind": "rename" if "R" in code else "copy",
                    "source": source,
                    "destination": destination,
                }
            )

        if code == "??":
            untracked.append(destination)
        elif code == "!!":
            ignored.append(destination)
        elif code in CONFLICT_CODES or "U" in code:
            conflicts.append(destination)
        else:
            if code[0] != " ":
                staged.append(destination)
            if code[1] != " ":
                unstaged.append(destination)
                if code[1] == "R" and source is not None:
                    unstaged.append(source)

    return {
        "staged": sorted(set(staged)),
        "unstaged": sorted(set(unstaged)),
        "untracked": sorted(set(untracked)),
        "ignored": sorted(set(ignored)),
        "conflicts": sorted(set(conflicts)),
        "path_changes": sorted(
            path_changes,
            key=lambda change: (
                change["source"],
                change["destination"],
                change["status"],
            ),
        ),
    }


def repository_state(repository: Path) -> dict[str, Any]:
    output = require_git(
        repository,
        [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored=matching",
        ],
        "git_status_failed",
        "Git status inspection failed",
    )
    return parse_status(output)


def binary_diff(repository: Path, arguments: list[str]) -> bytes:
    return require_git(
        repository,
        arguments,
        "git_diff_failed",
        "Git target diff inspection failed",
    )


def inspect_staged(repository: Path) -> dict[str, Any]:
    head = resolve_commit(repository, "HEAD")
    diff = binary_diff(
        repository,
        ["diff", "--cached", "--binary", "--no-ext-diff", "--no-textconv"],
    )
    if not diff:
        raise InspectionError("staged_target_empty", "staged target is empty")
    target: dict[str, Any] = {
        "kind": "staged",
        "head_commit": head,
        "diff_sha256": sha256(diff),
    }
    target["target_digest"] = target_digest(target)
    return target


def inspect_head(repository: Path) -> dict[str, Any]:
    commit = resolve_commit(repository, "HEAD")
    target: dict[str, Any] = {"kind": "head", "commit": commit}
    target["target_digest"] = target_digest(target)
    return target


def inspect_commit(repository: Path, revision: str) -> dict[str, Any]:
    commit = resolve_commit(repository, revision)
    diff = binary_diff(
        repository,
        [
            "diff-tree",
            "--root",
            "-m",
            "--binary",
            "--no-ext-diff",
            "--no-textconv",
            "-p",
            commit,
        ],
    )
    target: dict[str, Any] = {
        "kind": "commit",
        "revision": revision,
        "commit": commit,
        "diff_sha256": sha256(diff),
    }
    target["target_digest"] = target_digest(target)
    return target


def inspect_range(repository: Path, expression: str) -> dict[str, Any]:
    if any(character in expression for character in "\0\r\n"):
        raise InspectionError("range_invalid", "range expression is invalid")
    match = RANGE.fullmatch(expression)
    if match is None:
        raise InspectionError(
            "range_invalid", "range must be one explicit A..B or A...B expression"
        )
    left_revision, operator, right_revision = match.groups()
    left = resolve_commit(repository, left_revision)
    right = resolve_commit(repository, right_revision)

    if operator == "...":
        merge_base_bytes = require_git(
            repository,
            ["merge-base", left, right],
            "range_unresolved",
            "range endpoints do not have one merge base",
        )
        merge_base = decode_utf8(
            merge_base_bytes, "range_invalid", "merge base is not valid UTF-8"
        ).strip()
        diff_base = merge_base
    else:
        merge_base = None
        diff_base = left

    diff = binary_diff(
        repository,
        ["diff", "--binary", "--no-ext-diff", "--no-textconv", diff_base, right],
    )
    commits_bytes = require_git(
        repository,
        ["rev-list", "--reverse", f"{diff_base}..{right}"],
        "range_unresolved",
        "range commit inspection failed",
    )
    commits = [
        value
        for value in decode_utf8(
            commits_bytes, "range_invalid", "range commits are not valid UTF-8"
        ).splitlines()
        if value
    ]
    target: dict[str, Any] = {
        "kind": "range",
        "expression": expression,
        "operator": operator,
        "base_commit": left,
        "head_commit": right,
        "merge_base": merge_base,
        "commits": commits,
        "diff_sha256": sha256(diff),
    }
    target["target_digest"] = target_digest(target)
    return target


def inspect(repository: Path, arguments: argparse.Namespace) -> dict[str, Any]:
    root = canonical_git_root(repository)
    state = repository_state(root)
    if arguments.staged:
        target = inspect_staged(root)
    elif arguments.head:
        target = inspect_head(root)
    elif arguments.commit is not None:
        target = inspect_commit(root, arguments.commit)
    else:
        target = inspect_range(root, arguments.range)
    return {
        "schema_version": SCHEMA_VERSION,
        "semantic_scope": "not_evaluated",
        "repository": str(root),
        "target": target,
        "state": state,
    }


def parser() -> argparse.ArgumentParser:
    result = JsonArgumentParser()
    result.add_argument("--repository", required=True)
    target = result.add_mutually_exclusive_group(required=True)
    target.add_argument("--staged", action="store_true")
    target.add_argument("--head", action="store_true")
    target.add_argument("--commit")
    target.add_argument("--range")
    return result


def main() -> int:
    try:
        arguments = parser().parse_args()
        repository = Path(arguments.repository)
        result = inspect(repository, arguments)
    except (InspectionError, subprocess.TimeoutExpired) as error:
        code = error.code if isinstance(error, InspectionError) else "git_timeout"
        message = (
            str(error)
            if isinstance(error, InspectionError)
            else "Git inspection timed out"
        )
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
