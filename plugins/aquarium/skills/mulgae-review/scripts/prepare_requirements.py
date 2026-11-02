#!/usr/bin/env python3
"""Prepare caller-owned native Mulgae input; never infer requirements from prose."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from pathlib import Path

IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
OWNED_NAME = re.compile(r"aquarium-review-input-[0-9a-f]{32}\.json\Z")
ROLES = {
    "logic",
    "security",
    "maintainability",
    "product",
    "documentation",
    "testing",
    "artist",
}


def text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def build(request: dict) -> tuple[dict, list]:
    roles = request.get("roles")
    criteria = request.get("criteria")
    if (
        not isinstance(roles, list)
        or not roles
        or any(not isinstance(r, str) or r not in ROLES for r in roles)
        or len(set(roles)) != len(roles)
    ):
        raise ValueError("selected enabled roles are required")
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= 100:
        raise ValueError("native input requires 1 through 100 requirements")
    ids = [row.get("id") for row in criteria if isinstance(row, dict)]
    if (
        len(ids) != len(criteria)
        or not all(text(value) for value in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValueError("original criterion identities must be nonempty and unique")
    reserved = {value for value in ids if IDENTIFIER.fullmatch(value)}
    items, mapping = [], []
    for ordinal, row in enumerate(criteria, 1):
        acceptance = row.get("acceptance_criteria")
        if (
            not text(row.get("source"))
            or not text(row.get("text"))
            or row.get("owner_role") not in roles
        ):
            raise ValueError("each criterion needs source, text and a selected owner")
        if (
            not isinstance(acceptance, list)
            or not 1 <= len(acceptance) <= 32
            or not all(text(value) for value in acceptance)
        ):
            raise ValueError("native requirement needs 1 through 32 nonempty criteria")
        identifier = row["id"]
        if not IDENTIFIER.fullmatch(identifier):
            identifier = f"Aquarium{ordinal}"
            suffix = 0
            while identifier in reserved:
                suffix += 1
                identifier = f"Aquarium{ordinal}_{suffix}"
            if not IDENTIFIER.fullmatch(identifier):
                raise ValueError("cannot allocate native criterion identity")
            reserved.add(identifier)
        items.append(
            {
                "id": identifier,
                "text": f"{row['text']}\nAuthority: {row['source']}",
                "acceptance_criteria": acceptance,
                "owner_role": row["owner_role"],
            }
        )
        mapping.append(
            {
                "id": identifier,
                "original_id": row["id"],
                "source": row["source"],
                "owner_role": row["owner_role"],
            }
        )
    return {
        "schema_version": "mulgae-requirements-input.v1",
        "requirements": items,
    }, mapping


def prepare(root: Path, request: dict) -> dict:
    document, mapping = build(request)
    raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path = root / f"aquarium-review-input-{uuid.uuid4().hex}.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    identity = os.fstat(fd)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            identity = os.fstat(stream.fileno())
    except BaseException:
        try:
            current = path.lstat()
            if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                path.unlink()
        except FileNotFoundError:
            pass
        raise
    return {
        "requirements_path": path.name,
        "input_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "device": identity.st_dev,
        "inode": identity.st_ino,
        "mapping": mapping,
    }


def cleanup(root: Path, prepared: dict) -> dict:
    name = prepared.get("requirements_path")
    if not isinstance(name, str) or not OWNED_NAME.fullmatch(name):
        raise ValueError("cleanup requires the exact prepared input")
    path = root / name
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        identity = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(identity.st_mode)
            or stat.S_IMODE(identity.st_mode) != 0o600
            or (identity.st_dev, identity.st_ino)
            != (
                prepared.get("device"),
                prepared.get("inode"),
            )
        ):
            raise ValueError("input identity changed; preserve the file")
        digest = "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()
    current = path.lstat()
    if digest != prepared.get("input_sha256") or (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
    ) != (identity.st_dev, identity.st_ino, identity.st_size, identity.st_mtime_ns):
        raise ValueError("input changed; preserve the file")
    path.unlink()
    return {"removed": name}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "cleanup"))
    parser.add_argument("--repository", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.repository.resolve(strict=True)
        request = json.load(sys.stdin)
        if not root.is_dir() or not isinstance(request, dict):
            raise ValueError("repository and object input are required")
        result = (
            prepare(root, request)
            if args.operation == "prepare"
            else cleanup(root, request)
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
