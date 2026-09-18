"""Isolated verified installed entrypoint for aquarium-status."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
import sys
from pathlib import Path
from typing import Any

PAYLOAD = {
    "aquarium_status.py",
    "status_contract.py",
    "status_store.py",
    "status_report.py",
    "runtime_entry.py",
    "requirements.txt",
}
RECEIPT_KEYS = {
    "schema",
    "plugin_version",
    "source_sha256",
    "python_version",
    "python_executable",
    "python_executable_sha256",
    "requirements_sha256",
    "files",
    "dependency_files",
}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _regular(path: Path, digest: str, mode: int | None = None) -> None:
    info = path.lstat()
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or (mode is not None and stat.S_IMODE(info.st_mode) != mode)
        or _digest(path) != digest
    ):
        raise RuntimeError("installed runtime integrity check failed")


def _directory(path: Path, mode: int | None = None) -> None:
    info = path.lstat()
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISDIR(info.st_mode)
        or (mode is not None and stat.S_IMODE(info.st_mode) != mode)
    ):
        raise RuntimeError("installed runtime directory is unsafe")


def _launcher_bytes(generation: Path, receipt: dict[str, Any]) -> bytes:
    interpreter = shlex.quote(receipt["python_executable"])
    entry = shlex.quote(str(generation / "runtime_entry.py"))
    return (
        "#!/bin/sh\n"
        "# aquarium-status managed launcher v1\n"
        f'exec {interpreter} -B -I -S {entry} "$@"\n'
    ).encode()


def _receipt(generation: Path) -> dict[str, Any]:
    path = generation / "runtime.json"
    info = path.lstat()
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise RuntimeError("installed runtime receipt is unsafe")
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value) != RECEIPT_KEYS
        or value["schema"] != "aquarium-status-runtime/v1"
    ):
        raise RuntimeError("installed runtime receipt is invalid")
    files = value["files"]
    dependencies = value["dependency_files"]
    hashes = (
        {**files, **dependencies}
        if isinstance(files, dict) and isinstance(dependencies, dict)
        else {}
    )
    if (
        not isinstance(files, dict)
        or set(files) != PAYLOAD
        or not isinstance(dependencies, dict)
        or any(
            not isinstance(name, str)
            or not isinstance(digest, str)
            or SHA_RE.fullmatch(digest) is None
            for name, digest in hashes.items()
        )
        or any(
            not name.startswith("dependencies/") or ".." in Path(name).parts
            for name in dependencies
        )
    ):
        raise RuntimeError("installed runtime receipt hashes are invalid")
    source = "".join(f"{files[name]}  {name}\n" for name in sorted(files)).encode()
    if (
        hashlib.sha256(source).hexdigest() != value["source_sha256"]
        or files["requirements.txt"] != value["requirements_sha256"]
        or not isinstance(value["python_executable_sha256"], str)
        or SHA_RE.fullmatch(value["python_executable_sha256"]) is None
    ):
        raise RuntimeError("installed runtime receipt relationships are invalid")
    return value


def _selected() -> tuple[Path, dict[str, Any]]:
    generation = Path(__file__).absolute().parent
    home = Path.home()
    aquarium = home / ".aquarium"
    root = aquarium / "status-runtime"
    versions = root / "versions"
    if generation.parent != versions:
        raise RuntimeError("installed generation escaped its runtime root")
    for directory in (aquarium, root, versions, generation):
        _directory(directory, 0o700)
    local = home / ".local"
    binary = local / "bin"
    for directory in (local, binary):
        _directory(directory)
    current = root / "current"
    info = current.lstat()
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise RuntimeError("installed runtime selector is unsafe")
    if current.read_text(encoding="utf-8").strip() != f"versions/{generation.name}":
        raise RuntimeError("installed generation is not selected")
    receipt = _receipt(generation)
    if {path.name for path in generation.iterdir()} != PAYLOAD | {
        "dependencies",
        "runtime.json",
    }:
        raise RuntimeError("installed generation contains unexpected paths")
    major_minor = ".".join(receipt["python_version"].split(".")[:2])
    if (
        re.fullmatch(
            rf"{receipt['source_sha256']}-py{re.escape(major_minor)}(?:-r[0-9a-f]{{32}})?",
            generation.name,
        )
        is None
    ):
        raise RuntimeError("installed generation name is invalid")
    interpreter = Path(receipt["python_executable"])
    _regular(interpreter, receipt["python_executable_sha256"])
    if (
        Path(sys.executable).resolve() != interpreter.resolve()
        or not sys.flags.isolated
        or not sys.flags.no_site
        or not sys.dont_write_bytecode
        or sys.version.split()[0] != receipt["python_version"]
    ):
        raise RuntimeError("aquarium-status used an unrecorded interpreter")
    for name in PAYLOAD:
        _regular(generation / name, receipt["files"][name], 0o600)
    dependency_root = generation / "dependencies"
    info = dependency_root.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise RuntimeError("installed dependency root is unsafe")
    observed: dict[str, str] = {}
    for path in dependency_root.rglob("*"):
        if path.is_dir() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("installed dependency path is unsafe")
        observed[path.relative_to(generation).as_posix()] = _digest(path)
    if observed != receipt["dependency_files"]:
        raise RuntimeError("installed dependencies changed")
    launcher = binary / "aquarium-status"
    expected_launcher = _launcher_bytes(generation, receipt)
    _regular(launcher, hashlib.sha256(expected_launcher).hexdigest(), 0o755)
    return generation, receipt


def main() -> int:
    try:
        generation, _ = _selected()
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(generation / "dependencies"))
        sys.path.insert(0, str(generation))
        from aquarium_status import main as status_main

        return status_main()
    except Exception:  # noqa: BLE001 - fail closed before loading runtime code
        payload = {
            "schema": "aquarium-status-runtime-error/v1",
            "error": {
                "code": "runtime_unavailable",
                "message": "The installed aquarium-status runtime is unavailable.",
                "action": "Run $aquarium:dev-setup-global and approve aquarium-status repair.",
            },
        }
        sys.stderr.write(json.dumps(payload, sort_keys=True) + "\n")
        return 1


if __name__ == "__main__":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    raise SystemExit(main())
