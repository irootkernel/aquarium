#!/usr/bin/env python3
"""Inspect one exact Git target for Aquarium independent review."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from contextlib import ExitStack
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
    command = ["git", "-c", "core.fsmonitor=false", "-C", str(repository)]
    config = subprocess.run(
        [
            *command,
            "config",
            "--null",
            "--name-only",
            "--get-regexp",
            r"^filter\..*\.(clean|smudge|process|required)$",
        ],
        check=False,
        capture_output=True,
        env=environment,
        timeout=30,
    )
    if config.returncode not in {0, 1}:
        raise InspectionError(
            "git_filter_config_failed", "Git filter configuration could not be read"
        )
    keys = sorted(
        {
            key
            for key in decode_utf8(
                config.stdout,
                "git_filter_config_invalid",
                "Git filter configuration is not valid UTF-8",
            ).split("\0")
            if key
        }
    )
    environment["GIT_CONFIG_COUNT"] = str(len(keys))
    for index, key in enumerate(keys):
        environment[f"GIT_CONFIG_KEY_{index}"] = key
        environment[f"GIT_CONFIG_VALUE_{index}"] = (
            "false" if key.endswith(".required") else ""
        )
    return subprocess.run(
        [*command, *arguments],
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


def git_object_format(repository: Path) -> str:
    value = require_git(
        repository,
        ["rev-parse", "--show-object-format"],
        "git_object_format_failed",
        "Git object format could not be read",
    ).strip()
    if value not in {b"sha1", b"sha256"}:
        raise InspectionError(
            "git_object_format_invalid", "Git object format is unsupported"
        )
    return value.decode("ascii")


def git_blob_oid(content: bytes, object_format: str) -> bytes:
    digest = hashlib.new(object_format)
    digest.update(b"blob " + str(len(content)).encode("ascii") + b"\0")
    digest.update(content)
    return digest.hexdigest().encode("ascii")


def index_gitlinks(repository: Path) -> dict[bytes, bytes]:
    records = require_git(
        repository,
        ["ls-files", "--cached", "--stage", "-z"],
        "git_paths_failed",
        "Git index inspection failed",
    ).split(b"\0")
    links: dict[bytes, bytes] = {}
    for record in records:
        if not record:
            continue
        try:
            header, path = record.split(b"\t", 1)
            mode, object_id, stage = header.split()
        except ValueError as error:
            raise InspectionError(
                "git_paths_invalid", "Git index entry is malformed"
            ) from error
        if mode == b"160000" and stage == b"0":
            links[path] = object_id
    return links


def head_projection(repository: Path, head: str) -> dict[bytes, tuple[bytes, bytes]]:
    records = require_git(
        repository,
        ["ls-tree", "-r", "-z", "--full-tree", head],
        "git_tree_failed",
        "HEAD tree could not be read",
    ).split(b"\0")
    projection: dict[bytes, tuple[bytes, bytes]] = {}
    for record in records:
        if not record:
            continue
        try:
            header, path = record.split(b"\t", 1)
            mode, _kind, object_id = header.split()
        except ValueError as error:
            raise InspectionError(
                "git_tree_invalid", "HEAD tree entry is malformed"
            ) from error
        projection[path] = mode, object_id
    return projection


def checked_out_gitlink(repository: Path, relative: Path, index_oid: bytes) -> bytes:
    path = repository / relative
    result = git_command(path, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        return index_oid  # An uninitialized submodule retains its index identity.
    toplevel = decode_utf8(
        result.stdout.strip(), "gitlink_invalid", "submodule root is not valid UTF-8"
    )
    if Path(toplevel) != path:
        return index_oid
    return resolve_commit(path, "HEAD").encode("ascii")


def workspace_entry(
    repository: Path, root_fd: int, relative: Path, index_oid: bytes | None
) -> tuple[bytes, bytes, bytes] | None:
    with ExitStack() as opened:
        directory_fd = root_fd
        for component in relative.parts[:-1]:
            try:
                directory_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                return None  # A tracked deletion is absent from the final projection.
            except OSError as error:
                if error.errno == errno.ENOTDIR:
                    try:
                        parent_mode = os.stat(
                            component, dir_fd=directory_fd, follow_symlinks=False
                        ).st_mode
                    except OSError as inspection_error:
                        raise InspectionError(
                            "candidate_unreadable",
                            "candidate parent changed during inspection",
                        ) from inspection_error
                    if stat.S_ISREG(parent_mode):
                        return None  # A file replaced an indexed parent directory.
                code = (
                    "unsafe_symlink"
                    if error.errno in {errno.ELOOP, errno.ENOTDIR}
                    else "candidate_unreadable"
                )
                raise InspectionError(
                    code, "candidate parent is unsafe or unreadable"
                ) from error
            opened.callback(os.close, directory_fd)

        name = relative.name
        try:
            mode = os.stat(name, dir_fd=directory_fd, follow_symlinks=False).st_mode
        except FileNotFoundError:
            return None
        except OSError as error:
            raise InspectionError(
                "candidate_unreadable", "candidate path is unreadable"
            ) from error

        if stat.S_ISLNK(mode):
            path = repository / relative
            try:
                resolved = path.resolve(strict=True)
            except FileNotFoundError:
                try:
                    resolved = path.resolve()
                except (OSError, RuntimeError) as error:
                    raise InspectionError(
                        "unsafe_symlink", "candidate symlink cannot be resolved"
                    ) from error
            except (OSError, RuntimeError) as error:
                raise InspectionError(
                    "unsafe_symlink", "candidate symlink cannot be resolved"
                ) from error
            if not resolved.is_relative_to(repository):
                raise InspectionError(
                    "unsafe_symlink", "candidate symlink leaves the worktree"
                )
            try:
                content = os.fsencode(os.readlink(name, dir_fd=directory_fd))
            except OSError as error:
                raise InspectionError(
                    "candidate_unreadable", "candidate symlink is unreadable"
                ) from error
            return b"symlink", b"120000", content

        if stat.S_ISDIR(mode):
            if index_oid is None:
                return None  # Directories are not entries in the final projection.
            return (
                b"gitlink",
                b"160000",
                checked_out_gitlink(repository, relative, index_oid),
            )

        if not stat.S_ISREG(mode):
            raise InspectionError(
                "candidate_unsafe", "candidate contains a non-file path"
            )
        try:
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
            with os.fdopen(descriptor, "rb") as stream:
                opened_mode = os.fstat(stream.fileno()).st_mode
                if not stat.S_ISREG(opened_mode):
                    raise InspectionError(
                        "candidate_unsafe", "candidate changed to a non-file path"
                    )
                content = stream.read()
        except OSError as error:
            raise InspectionError(
                "candidate_unreadable", "candidate file is unreadable"
            ) from error
        file_mode = b"100755" if opened_mode & 0o111 else b"100644"
        return b"file", file_mode, content


def final_workspace_projection(
    repository: Path,
) -> tuple[dict[str, Any], dict[bytes, tuple[bytes, bytes]]]:
    paths = require_git(
        repository,
        ["ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        "git_paths_failed",
        "Git path inspection failed",
    ).split(b"\0")
    object_format = git_object_format(repository)
    gitlinks = index_gitlinks(repository)
    digest = hashlib.sha256()
    included = 0
    projection: dict[bytes, tuple[bytes, bytes]] = {}
    try:
        root_fd = os.open(repository, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as error:
        raise InspectionError(
            "candidate_unreadable", "worktree root is unreadable"
        ) from error
    with ExitStack() as opened:
        opened.callback(os.close, root_fd)
        for raw_path in sorted({path for path in paths if path}):
            name = decode_utf8(
                raw_path, "git_path_invalid", "a Git path is not valid UTF-8"
            )
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise InspectionError(
                    "git_path_invalid", "Git path escapes the worktree"
                )
            entry = workspace_entry(
                repository, root_fd, relative, gitlinks.get(raw_path)
            )
            if entry is None:
                continue
            kind, file_mode, content = entry
            object_id = (
                content if kind == b"gitlink" else git_blob_oid(content, object_format)
            )
            projection[raw_path] = file_mode, object_id
            digest.update(len(raw_path).to_bytes(8, "big"))
            digest.update(raw_path)
            digest.update(kind)
            digest.update(file_mode)
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
            included += 1
    return {"file_count": included, "content_sha256": digest.hexdigest()}, projection


def inspect_workspace(repository: Path) -> dict[str, Any]:
    fingerprint, _projection = final_workspace_projection(repository)
    target: dict[str, Any] = {
        "kind": "workspace",
        **fingerprint,
    }
    target["target_digest"] = target_digest(target)
    return target


def inspect_dirty(repository: Path) -> dict[str, Any]:
    head = resolve_commit(repository, "HEAD")
    fingerprint, projection = final_workspace_projection(repository)
    if projection == head_projection(repository, head):
        raise InspectionError("dirty_target_empty", "dirty target is empty")
    target: dict[str, Any] = {
        "kind": "dirty",
        "head_commit": head,
        **fingerprint,
    }
    target["target_digest"] = target_digest(target)
    return target


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
    parents = require_git(
        repository,
        ["rev-list", "--parents", "-n", "1", commit],
        "revision_unresolved",
        "commit parents could not be read",
    ).split()
    if len(parents) > 1:
        diff = binary_diff(
            repository,
            [
                "diff",
                "--binary",
                "--no-ext-diff",
                "--no-textconv",
                parents[1].decode(),
                commit,
            ],
        )
    else:
        diff = binary_diff(
            repository,
            [
                "diff-tree",
                "--root",
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
    if state["conflicts"]:
        raise InspectionError(
            "candidate_conflicted", "candidate contains unresolved conflicts"
        )
    if getattr(arguments, "workspace", False):
        target = inspect_workspace(root)
    elif getattr(arguments, "dirty", False):
        target = inspect_dirty(root)
    elif arguments.staged:
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
    target.add_argument("--workspace", action="store_true")
    target.add_argument("--dirty", action="store_true")
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
