"""Prepare local assignment bytes; native dispatch and acceptance belong to the caller.

Call prepare(source_root, request), or pass a JSON request with --source-root and
--input (use '-' for stdin). Dependency resolution is explicitly caller-owned.
Digests cover ASCII JSON with sorted keys, compact separators, and no final newline.
File content is base64 of exact bytes, including original newline sequences.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

REQUEST_SCHEMA = "aquarium.assignment-request/v1"
SNAPSHOT_SCHEMA = "aquarium.prepared-role-snapshot/v1"
ASSIGNMENT_SCHEMA = "aquarium.prepared-assignment/v1"
OUTPUT_SCHEMA = "aquarium.assignment-preparation/v1"


class PreparationError(ValueError):
    """Invalid input or unsafe/unreadable declared source."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def _object(value: Any, keys: set[str], name: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise PreparationError(
            f"{name} must contain exactly: {', '.join(sorted(keys))}"
        )


def _text(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PreparationError(f"{name} must be a nonempty string")


def _texts(value: Any, name: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise PreparationError(f"{name} must be a list of nonempty strings")
    for item in value:
        _text(item, name)


def _paths(value: Any, name: str) -> list[str]:
    _texts(value, name, allow_empty=True)
    for path in value:
        if (
            path.startswith("/")
            or "\x00" in path
            or any(part in ("", ".", "..") for part in path.split("/"))
        ):
            raise PreparationError(
                f"{name} requires normalized relative paths: {path!r}"
            )
    if len(set(value)) != len(value):
        raise PreparationError(f"{name} contains duplicate paths")
    return sorted(value)


def _open_directory(path: Path) -> int:
    if not path.is_absolute() or ".." in path.parts:
        raise PreparationError("source_root must be an absolute path without '..'")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = os.open("/", flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _file(root: int, path: str) -> dict[str, Any]:
    directory = os.dup(root)
    descriptor = None
    try:
        parts = path.split("/")
        for part in parts[:-1]:
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        descriptor = os.open(
            parts[-1],
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=directory,
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise PreparationError(f"declared source is not a regular file: {path}")
        chunks = []
        while chunk := os.read(descriptor, 65536):
            chunks.append(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
        if before.st_size != len(content) or (
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise PreparationError(f"declared source changed while reading: {path}")
        return {
            "path": path,
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory)


def prepare(source_root: Path, request: dict[str, Any]) -> dict[str, Any]:
    """Return a self-contained local snapshot and assignment without writing state.

    Context references are caller-supplied exact identities, not verified native
    records. Canonical sources name readable authority; selected_evidence names
    files to include in full. An explicitly empty evidence list is permitted.
    """
    if isinstance(request, dict) and request.get("schema") == "aquarium.assignment/v2":
        spec = importlib.util.spec_from_file_location(
            "aquarium_ordinary_assignment",
            Path(__file__).with_name("ordinary_assignment.py"),
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            return module.prepare(request)
        except ValueError as error:
            raise PreparationError(str(error)) from error
    _object(request, {"schema", "role", "node"}, "request")
    if request["schema"] != REQUEST_SCHEMA:
        raise PreparationError(f"request schema must be {REQUEST_SCHEMA}")
    role = request["role"]
    _object(role, {"path", "dependencies"}, "role")
    _text(role["path"], "role.path")
    dependencies = _paths(role["dependencies"], "role.dependencies")
    role_paths = _paths([role["path"], *dependencies], "role sources")
    node = request["node"]
    _object(
        node,
        {
            "objective",
            "purpose",
            "instructions",
            "canonical_sources",
            "context",
            "selected_evidence",
            "permitted_effects",
            "deliverables",
            "success_criteria",
        },
        "node",
    )
    for key in ("objective", "purpose", "instructions"):
        _text(node[key], f"node.{key}")
    for key in ("canonical_sources", "deliverables", "success_criteria"):
        _texts(node[key], f"node.{key}")
    context_keys = {
        "work_identity",
        "goal_ref",
        "goal_revision",
        "target",
        "base",
        "procedure",
        "node",
    }
    _object(node["context"], context_keys, "node.context")
    for key in context_keys:
        _text(node["context"][key], f"node.context.{key}")
    _object(node["permitted_effects"], {"allowed", "excluded"}, "permitted_effects")
    for key in ("allowed", "excluded"):
        _texts(
            node["permitted_effects"][key], f"permitted_effects.{key}", allow_empty=True
        )
    evidence_paths = _paths(node["selected_evidence"], "node.selected_evidence")

    root = None
    try:
        root = _open_directory(Path(source_root))
        snapshot = {
            "schema": SNAPSHOT_SCHEMA,
            "role_path": role["path"],
            "files": [_file(root, path) for path in role_paths],
        }
        # Copy caller-owned data so later caller mutations cannot change this result.
        prepared_node = json.loads(canonical_bytes(node))
        prepared_node["selected_evidence"] = [
            _file(root, path) for path in evidence_paths
        ]
    except OSError as error:
        raise PreparationError(
            f"cannot read declared source safely: {error}"
        ) from error
    finally:
        if root is not None:
            os.close(root)
    assignment = {
        "schema": ASSIGNMENT_SCHEMA,
        "role_snapshot": snapshot,
        "node": prepared_node,
    }
    return {
        "schema": OUTPUT_SCHEMA,
        "prepared_role_snapshot": snapshot,
        "local_prepared_role_snapshot_sha256": hashlib.sha256(
            canonical_bytes(snapshot)
        ).hexdigest(),
        "prepared_assignment": assignment,
        "local_prepared_assignment_sha256": hashlib.sha256(
            canonical_bytes(assignment)
        ).hexdigest(),
    }


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PreparationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PreparationError(f"invalid JSON constant: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument(
        "--input", required=True, help="JSON request file, or '-' for stdin"
    )
    arguments = parser.parse_args()
    try:
        payload = (
            sys.stdin.buffer.read()
            if arguments.input == "-"
            else Path(arguments.input).read_bytes()
        )
        request = json.loads(
            payload, object_pairs_hook=_unique_keys, parse_constant=_reject_constant
        )
        output = prepare(arguments.source_root, request)
        sys.stdout.buffer.write(canonical_bytes(output) + b"\n")
    except (PreparationError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
