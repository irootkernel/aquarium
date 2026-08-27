#!/usr/bin/env python3
"""Snapshot and compare Git-observable repository state for Orca Review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "aquarium-orca-review-repository-state/v1"
ERROR_SCHEMA_VERSION = "aquarium-orca-review-repository-state-error/v1"
MAX_BASELINE_BYTES = 1024 * 1024
DIMENSIONS = (
    "head",
    "refs_sha256",
    "index_sha256",
    "tracked_worktree_sha256",
    "status_sha256",
)


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


def canonical_git_root(requested: Path) -> Path:
    if not requested.is_absolute():
        raise InspectionError("repository_not_absolute", "repository must be absolute")
    output = require_git(
        requested,
        ["rev-parse", "--show-toplevel"],
        "repository_not_git",
        "repository must be a Git worktree",
    )
    try:
        root = Path(output.decode("utf-8").strip())
    except UnicodeError as error:
        raise InspectionError(
            "repository_path_invalid", "Git root is not valid UTF-8"
        ) from error
    if not root.is_absolute() or root != requested:
        raise InspectionError(
            "repository_not_root",
            "repository must be the exact canonical Git worktree root",
        )
    return root


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def untracked_identity(repository: Path) -> bytes:
    paths = require_git(
        repository,
        ["ls-files", "--others", "--exclude-standard", "-z"],
        "worktree_unavailable",
        "untracked worktree state is unavailable",
    )
    identity = hashlib.sha256()
    for raw_path in paths.split(b"\0"):
        if not raw_path:
            continue
        path = repository / os.fsdecode(raw_path)
        try:
            metadata = path.lstat()
        except OSError as error:
            raise InspectionError(
                "worktree_unavailable", "untracked worktree state is unavailable"
            ) from error
        identity.update(len(raw_path).to_bytes(8, "big"))
        identity.update(raw_path)
        identity.update(stat.S_IFMT(metadata.st_mode).to_bytes(8, "big"))
        identity.update(stat.S_IMODE(metadata.st_mode).to_bytes(8, "big"))
        if stat.S_ISREG(metadata.st_mode):
            contents = hashlib.sha256()
            try:
                with path.open("rb") as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        contents.update(chunk)
            except OSError as error:
                raise InspectionError(
                    "worktree_unavailable", "untracked worktree state is unavailable"
                ) from error
            identity.update(b"regular\0")
            identity.update(contents.digest())
        elif stat.S_ISLNK(metadata.st_mode):
            try:
                target = os.fsencode(os.readlink(path))
            except OSError as error:
                raise InspectionError(
                    "worktree_unavailable", "untracked worktree state is unavailable"
                ) from error
            identity.update(b"symlink\0")
            identity.update(len(target).to_bytes(8, "big"))
            identity.update(target)
        else:
            raise InspectionError(
                "worktree_unavailable",
                "untracked worktree contains an unsupported file type",
            )
    return identity.digest()


def tracked_files_identity(repository: Path, visited: set[Path] | None = None) -> bytes:
    try:
        physical_repository = repository.resolve(strict=True)
    except OSError as error:
        raise InspectionError(
            "worktree_unavailable", "tracked worktree state is unavailable"
        ) from error
    seen = visited if visited is not None else set()
    if physical_repository in seen:
        raise InspectionError(
            "worktree_unavailable", "tracked worktree contains a recursive Git link"
        )
    seen.add(physical_repository)

    entries = require_git(
        repository,
        ["ls-files", "--stage", "-z"],
        "worktree_unavailable",
        "tracked worktree state is unavailable",
    )
    identity = hashlib.sha256()
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        try:
            metadata, raw_path = entry.split(b"\t", 1)
            mode, _object_id, stage = metadata.split(b" ", 2)
        except ValueError as error:
            raise InspectionError(
                "worktree_unavailable", "tracked worktree state is unavailable"
            ) from error
        identity.update(len(metadata).to_bytes(8, "big"))
        identity.update(metadata)
        identity.update(len(raw_path).to_bytes(8, "big"))
        identity.update(raw_path)
        if stage != b"0":
            continue

        path = repository / os.fsdecode(raw_path)
        try:
            file_status = path.lstat()
        except FileNotFoundError:
            identity.update(b"missing\0")
            continue
        except OSError as error:
            raise InspectionError(
                "worktree_unavailable", "tracked worktree state is unavailable"
            ) from error
        identity.update(stat.S_IFMT(file_status.st_mode).to_bytes(8, "big"))
        identity.update(stat.S_IMODE(file_status.st_mode).to_bytes(8, "big"))
        if stat.S_ISREG(file_status.st_mode):
            contents = hashlib.sha256()
            try:
                with path.open("rb") as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        contents.update(chunk)
            except OSError as error:
                raise InspectionError(
                    "worktree_unavailable", "tracked worktree state is unavailable"
                ) from error
            identity.update(b"regular\0")
            identity.update(contents.digest())
        elif stat.S_ISLNK(file_status.st_mode):
            try:
                target = os.fsencode(os.readlink(path))
            except OSError as error:
                raise InspectionError(
                    "worktree_unavailable", "tracked worktree state is unavailable"
                ) from error
            identity.update(b"symlink\0")
            identity.update(len(target).to_bytes(8, "big"))
            identity.update(target)
        elif mode == b"160000" and stat.S_ISDIR(file_status.st_mode):
            identity.update(b"gitlink\0")
            identity.update(tracked_files_identity(path, seen))
            identity.update(
                json.dumps(
                    head_state(path), sort_keys=True, separators=(",", ":")
                ).encode()
            )
            identity.update(
                require_git(
                    path,
                    [
                        "for-each-ref",
                        "--format=%(refname)%00%(objectname)%00%(symref)",
                    ],
                    "worktree_unavailable",
                    "tracked worktree state is unavailable",
                )
            )
            identity.update(
                require_git(
                    path,
                    ["rev-parse", "--verify", "HEAD^{commit}"],
                    "worktree_unavailable",
                    "tracked worktree state is unavailable",
                )
            )
            identity.update(
                require_git(
                    path,
                    ["ls-files", "--stage", "-v", "-z"],
                    "worktree_unavailable",
                    "tracked worktree state is unavailable",
                )
            )
            identity.update(untracked_identity(path))
        else:
            identity.update(b"unsupported\0")
    return identity.digest()


def head_state(repository: Path) -> dict[str, str | None]:
    commit = (
        require_git(
            repository,
            ["rev-parse", "--verify", "HEAD^{commit}"],
            "head_unresolved",
            "HEAD does not resolve to a commit",
        )
        .decode("ascii")
        .strip()
    )
    symbolic = git_command(repository, ["symbolic-ref", "-q", "HEAD"])
    if symbolic.returncode not in {0, 1}:
        raise InspectionError("head_unresolved", "HEAD identity is unavailable")
    try:
        symbolic_ref = symbolic.stdout.decode("utf-8").strip() or None
    except UnicodeError as error:
        raise InspectionError("head_invalid", "HEAD ref is not valid UTF-8") from error
    return {"commit": commit, "symbolic_ref": symbolic_ref}


def snapshot(repository: Path) -> dict[str, Any]:
    refs = require_git(
        repository,
        [
            "for-each-ref",
            "--format=%(refname)%00%(objectname)%00%(symref)",
        ],
        "refs_unavailable",
        "Git refs are unavailable",
    )
    index = require_git(
        repository,
        ["ls-files", "--stage", "-v", "-z"],
        "index_unavailable",
        "Git index is unavailable",
    )
    tracked_worktree = require_git(
        repository,
        [
            "diff",
            "--binary",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=none",
        ],
        "worktree_unavailable",
        "tracked worktree state is unavailable",
    )
    status = require_git(
        repository,
        [
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
            "--ignore-submodules=none",
        ],
        "status_unavailable",
        "Git status is unavailable",
    )
    status_identity = status + b"\0untracked-content\0" + untracked_identity(repository)
    state: dict[str, Any] = {
        "head": head_state(repository),
        "refs_sha256": sha256(refs),
        "index_sha256": sha256(index),
        "tracked_worktree_sha256": sha256(
            tracked_worktree + b"\0tracked-files\0" + tracked_files_identity(repository)
        ),
        "status_sha256": sha256(status_identity),
    }
    fingerprint = sha256(
        json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": str(repository),
        "fingerprint": fingerprint,
        "state": state,
    }


def parse_baseline(raw: bytes, repository: Path) -> dict[str, Any]:
    if len(raw) > MAX_BASELINE_BYTES:
        raise InspectionError("baseline_oversized", "baseline is too large")
    try:
        baseline = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InspectionError(
            "baseline_invalid", "baseline is not valid JSON"
        ) from error
    if (
        not isinstance(baseline, dict)
        or baseline.get("schema_version") != SCHEMA_VERSION
        or baseline.get("repository") != str(repository)
        or not isinstance(baseline.get("fingerprint"), str)
        or not isinstance(baseline.get("state"), dict)
        or set(baseline["state"]) != set(DIMENSIONS)
    ):
        raise InspectionError("baseline_invalid", "baseline is malformed")
    encoded = json.dumps(
        baseline["state"], sort_keys=True, separators=(",", ":")
    ).encode()
    if sha256(encoded) != baseline["fingerprint"]:
        raise InspectionError("baseline_invalid", "baseline fingerprint is invalid")
    return baseline


def compare(repository: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    current = snapshot(repository)
    changed = [
        dimension
        for dimension in DIMENSIONS
        if baseline["state"][dimension] != current["state"][dimension]
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": str(repository),
        "baseline_fingerprint": baseline["fingerprint"],
        "current_fingerprint": current["fingerprint"],
        "changed": changed,
        "drift": bool(changed),
        "current": current,
    }


def parser() -> JsonArgumentParser:
    result = JsonArgumentParser(add_help=True)
    result.add_argument("--repository", required=True)
    modes = result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--snapshot", action="store_true")
    modes.add_argument("--compare", action="store_true")
    return result


def main() -> int:
    try:
        arguments = parser().parse_args()
        repository = canonical_git_root(Path(arguments.repository))
        if arguments.snapshot:
            result = snapshot(repository)
        else:
            raw = sys.stdin.buffer.read(MAX_BASELINE_BYTES + 1)
            result = compare(repository, parse_baseline(raw, repository))
    except (OSError, InspectionError, subprocess.TimeoutExpired) as error:
        if isinstance(error, InspectionError):
            code = error.code
            message = str(error)
        elif isinstance(error, subprocess.TimeoutExpired):
            code = "git_timeout"
            message = "Git inspection timed out"
        else:
            code = "inspection_failed"
            message = "repository-state inspection failed"
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
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
