"""Shared haepari-tree-sha256/v1 encoding for host sealing and guest recipes.

Both the host bundle builder and the guest recipes must produce exactly the
native controller's selected-file digest: SHA-256 over the algorithm label
and a NUL byte, then per entry (in the native order) an 8-byte big-endian
path length, the UTF-8 path bytes, one byte 0x00/0x01 for the executable
bit, an 8-byte big-endian file size, and the raw 32-byte content SHA-256.

Sealed trees stay strict: the directory walkers used for sealed bundles and
sidecar digests refuse symlinks and special files. Guest-state inventories
and the Codex component digest instead use the symlink-aware inventory walk
below, because real guest layout carries symlinks (for example a standalone
release's ``codex -> bin/codex``).
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any

TREE_ALGORITHM = "haepari-tree-sha256/v1"
SYMLINK_INVENTORY_LABEL = "aquarium-symlink/v1"


class TreeDigestError(RuntimeError):
    pass


def _entry(root: Path, relative: str) -> tuple[bytes, bytes, bytes]:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise TreeDigestError(f"unsafe selected input: {relative}")
    mode = stat.S_IMODE(path.stat().st_mode)
    executable = b"\x01" if mode & 0o111 else b"\x00"
    content = path.read_bytes()
    return (
        len(relative.encode("utf-8")).to_bytes(8, "big")
        + relative.encode("utf-8")
        + executable
        + len(content).to_bytes(8, "big"),
        hashlib.sha256(content).digest(),
        executable,
    )


def tree_sha256(root: Path, selected_files: list[str]) -> str:
    digest = hashlib.sha256(TREE_ALGORITHM.encode("utf-8") + b"\x00")
    for relative in sorted(selected_files, key=lambda item: item.encode("utf-8")):
        framing, content_digest, _executable = _entry(Path(root), relative)
        digest.update(framing)
        digest.update(content_digest)
    return digest.hexdigest()


def directory_files(root: Path) -> list[str]:
    root = Path(root)
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise TreeDigestError(f"symlink inside sealed tree: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise TreeDigestError(f"special file inside sealed tree: {path}")
        files.append(path.relative_to(root).as_posix())
    return files


def tree_sha256_from_directory(root: Path) -> str:
    return tree_sha256(root, directory_files(root))


def _symlink_content(path: Path) -> bytes:
    """A symlink's inventory content: the label, a NUL byte, the target."""
    return (
        SYMLINK_INVENTORY_LABEL.encode("utf-8")
        + b"\x00"
        + os.readlink(path).encode("utf-8")
    )


CHUNK_BYTES = 1024 * 1024


def _file_entry(path: Path) -> tuple[int, bytes]:
    """A regular file's content size and SHA-256, read in bounded chunks."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_BYTES):
            digest.update(chunk)
            size += len(chunk)
    return size, digest.digest()


def inventory_walk(root: Path) -> list[tuple[str, bool, int, bytes]]:
    """Symlink-aware walk for guest-state inventories and component digests.

    Every entry yields its relative path, its executable bit, its content
    size in bytes and its raw 32-byte content SHA-256. A regular file is
    hashed in bounded chunks and its bytes are never retained; a symlink's
    size and digest come from the labeled target encoding (with
    ``executable`` false). The walk itself may resolve a symlinked root
    (``root.is_dir()`` follows it); below the root it never follows a symlink
    and never descends into a symlinked directory, and a special file raises
    instead of being inventoried. Entries come back sorted by the path's
    UTF-8 bytes, the same order the strict selected-file digest uses.
    """
    root = Path(root)
    if not root.is_dir():
        return []
    walked: list[tuple[str, bool, int, bytes]] = []

    def visit(directory: Path, relative: str) -> None:
        for name in sorted(os.listdir(directory)):
            child = f"{relative}/{name}" if relative else name
            path = directory / name
            if os.path.islink(path):
                content = _symlink_content(path)
                digest = hashlib.sha256(content).digest()
                walked.append((child, False, len(content), digest))
            elif os.path.isdir(path):
                visit(path, child)
            elif os.path.isfile(path):
                mode = stat.S_IMODE(os.stat(path).st_mode)
                size, digest = _file_entry(path)
                walked.append((child, bool(mode & 0o111), size, digest))
            else:
                raise TreeDigestError(f"special file inside inventory scope: {path}")

    visit(root, "")
    walked.sort(key=lambda item: item[0].encode("utf-8"))
    return walked


def inventory_tree_sha256_from_directory(root: Path) -> str:
    """Component digest over the symlink-aware inventory walk."""
    digest = hashlib.sha256(TREE_ALGORITHM.encode("utf-8") + b"\x00")
    for relative, executable, size, content_digest in inventory_walk(root):
        name = relative.encode("utf-8")
        digest.update(
            len(name).to_bytes(8, "big")
            + name
            + (b"\x01" if executable else b"\x00")
            + size.to_bytes(8, "big")
        )
        digest.update(content_digest)
    return digest.hexdigest()


def inventory_entries(root: Path, scope: str, base: str) -> list[dict[str, Any]]:
    """Inventory entries whose identities are relative to the scoped base."""
    entries: list[dict[str, Any]] = []
    for relative, executable, _size, content_digest in inventory_walk(root):
        entries.append(
            {
                "installation_scope": scope,
                "relative_path": (base + "/" + relative) if base else relative,
                "executable": executable,
                "sha256": content_digest.hex(),
            }
        )
    return entries
