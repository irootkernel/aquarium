"""Read bounded repository declarations for the production status ledger."""

from __future__ import annotations

import configparser
import errno
import json
import os
import re
import select
import signal
import stat
import subprocess
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tomllib
import yaml
from status_contract import valid_language_declaration

MAX_MANIFEST_BYTES = 1024 * 1024
MAX_GIT_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_TRACKED_PATHS = 100_000
SCAN_TIMEOUT_SECONDS = 20
SENSITIVE_PATH_COMPONENT = re.compile(
    r"(?i)(?:^|[._-])(?:auth(?:entication)?|credentials?|keys?|secrets?|tokens?)(?:[._-]|$)"
)
LANGUAGE_SUFFIXES = {
    ".go": "go",
    ".rs": "rust",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".dart": "dart",
}
ROOT_MANIFESTS = {
    "go.mod",
    "go.work",
    "Cargo.toml",
    "rust-toolchain.toml",
    "rust-toolchain",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    ".python-version",
    "package.json",
    "pubspec.yaml",
}


class InventoryError(ValueError):
    """Repository language declarations could not be observed safely."""


class PubspecLoader(yaml.SafeLoader):
    """Reject aliases before PyYAML expands repeated merge mappings."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.AliasEvent):
            raise yaml.constructor.ConstructorError(None, None, "aliases are forbidden")
        return super().compose_node(parent, index)


def _load_pubspec(content: str, deadline: float) -> Any:
    if signal.getitimer(signal.ITIMER_REAL)[0] > 0:
        raise InventoryError("language scan timer is unavailable")
    previous_handler = signal.getsignal(signal.SIGALRM)

    def timed_out(_signal: int, _frame: Any) -> None:
        raise InventoryError("language scan timed out")

    signal.signal(signal.SIGALRM, timed_out)
    try:
        signal.setitimer(signal.ITIMER_REAL, _remaining(deadline))
        return yaml.load(content, Loader=PubspecLoader)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def _candidate(path: str) -> bool:
    if Path(path).suffix in LANGUAGE_SUFFIXES:
        return True
    parts = Path(path).parts
    if any(
        part.lower().startswith(".env") or SENSITIVE_PATH_COMPONENT.search(part)
        for part in parts
    ):
        return False
    name = Path(path).name
    return (
        name in ROOT_MANIFESTS
        or name.startswith("requirements")
        and name.endswith(".txt")
        or name.startswith("tsconfig")
        and name.endswith(".json")
    )


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise InventoryError("language scan timed out")
    return remaining


def _tracked_candidates(root: Path, deadline: float) -> list[str]:
    _remaining(deadline)
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    try:
        process = subprocess.Popen(
            ["git", "-C", str(root), "ls-files", "--cached", "-z"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=environment,
        )
        try:
            assert process.stdout is not None
            paths: set[str] = set()
            pending = bytearray()
            total_bytes = 0
            total_paths = 0
            while True:
                if not select.select([process.stdout], [], [], _remaining(deadline))[0]:
                    raise InventoryError("language scan timed out")
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_GIT_OUTPUT_BYTES:
                    raise InventoryError("repository file inventory is oversized")
                pending.extend(chunk)
                while (end := pending.find(b"\0")) >= 0:
                    relative = bytes(pending[:end]).decode("utf-8")
                    del pending[: end + 1]
                    total_paths += 1
                    if total_paths > MAX_TRACKED_PATHS:
                        raise InventoryError("repository file inventory is oversized")
                    if _candidate(relative):
                        paths.add(relative)
            if pending or process.wait(timeout=_remaining(deadline)) != 0:
                raise InventoryError("repository file inventory is unavailable")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()
        for name in ROOT_MANIFESTS:
            _remaining(deadline)
            if (root / name).exists() or (root / name).is_symlink():
                paths.add(name)
                if len(paths) > MAX_TRACKED_PATHS:
                    raise InventoryError("repository file inventory is oversized")
        for pattern in ("requirements*.txt", "tsconfig*.json"):
            for path in root.glob(pattern):
                _remaining(deadline)
                paths.add(path.name)
                if len(paths) > MAX_TRACKED_PATHS:
                    raise InventoryError("repository file inventory is oversized")
        candidates = sorted(path for path in paths if _candidate(path))
        _remaining(deadline)
        return candidates
    except (OSError, UnicodeError, subprocess.SubprocessError) as error:
        raise InventoryError("repository file inventory is unavailable") from error


def _open_parent(root: Path, relative: str, deadline: float) -> tuple[int, str]:
    path = Path(relative)
    if (
        not root.is_absolute()
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        raise InventoryError("manifest path is unsafe")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parts = (*root.parts[1:], *path.parts)
        for part in parts[:-1]:
            _remaining(deadline)
            next_descriptor = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor, parts[-1]
    except BaseException:
        os.close(descriptor)
        raise


def _regular_file(root: Path, relative: str, deadline: float) -> bool | None:
    try:
        descriptor, name = _open_parent(root, relative, deadline)
    except OSError as error:
        if error.errno == errno.ENOENT:
            return None
        if error.errno in {errno.ENOTDIR, errno.ELOOP}:
            return False
        raise
    try:
        _remaining(deadline)
        info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        return stat.S_ISREG(info.st_mode)
    except OSError as error:
        if error.errno == errno.ENOENT:
            return None
        if error.errno in {errno.ENOTDIR, errno.ELOOP}:
            return False
        raise
    finally:
        os.close(descriptor)


def _read_manifest(root: Path, relative: str, deadline: float) -> str:
    descriptor = -1
    parent = -1
    try:
        parent, name = _open_parent(root, relative, deadline)
        _remaining(deadline)
        descriptor = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
        )
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_MANIFEST_BYTES:
            raise InventoryError("manifest is unsafe or oversized")
        content = bytearray()
        while len(content) <= MAX_MANIFEST_BYTES:
            _remaining(deadline)
            chunk = os.read(
                descriptor, min(65536, MAX_MANIFEST_BYTES + 1 - len(content))
            )
            if not chunk:
                return content.decode("utf-8")
            content.extend(chunk)
        raise InventoryError("manifest is unsafe or oversized")
    except (OSError, UnicodeError) as error:
        raise InventoryError("manifest is unreadable") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if parent >= 0:
            os.close(parent)


def _declaration(
    versions: dict[str, list[dict[str, str]]],
    language: str,
    relative: str,
    kind: str,
    value: Any,
) -> None:
    if value is None:
        return
    if value == {"workspace": True}:
        return
    if not isinstance(value, str):
        return
    value = value.strip()
    if unicodedata.normalize("NFC", relative) != relative:
        raise InventoryError("declaration path is invalid")
    if not valid_language_declaration(language, kind, value):
        return
    versions[language].append({"path": relative, "kind": kind, "value": value})


def _go_directives(
    versions: dict[str, list[dict[str, str]]], relative: str, content: str
) -> None:
    for line in content.splitlines():
        match = re.fullmatch(r"\s*(go|toolchain)\s+(\S+)\s*(?://.*)?", line)
        if match:
            _declaration(versions, "go", relative, match[1], match[2])


def _scan_manifest(
    versions: dict[str, list[dict[str, str]]],
    root: Path,
    relative: str,
    deadline: float,
) -> None:
    name = Path(relative).name
    if name.startswith("requirements") and name.endswith(".txt") or name == "setup.py":
        versions.setdefault("python", [])
        return
    if name.startswith("tsconfig") and name.endswith(".json"):
        versions.setdefault("typescript", [])
        return
    if name in {"go.mod", "go.work"}:
        versions.setdefault("go", [])
        _go_directives(versions, relative, _read_manifest(root, relative, deadline))
    elif name in {"Cargo.toml", "rust-toolchain.toml", "rust-toolchain"}:
        versions.setdefault("rust", [])
        content = _read_manifest(root, relative, deadline)
        if name == "rust-toolchain":
            _declaration(versions, "rust", relative, "channel", content.strip())
        else:
            data = tomllib.loads(content)
            if name == "rust-toolchain.toml":
                _declaration(
                    versions,
                    "rust",
                    relative,
                    "channel",
                    data.get("toolchain", {}).get("channel"),
                )
            else:
                _declaration(
                    versions,
                    "rust",
                    relative,
                    "rust-version",
                    data.get("package", {}).get("rust-version"),
                )
                _declaration(
                    versions,
                    "rust",
                    relative,
                    "rust-version",
                    data.get("workspace", {}).get("package", {}).get("rust-version"),
                )
    elif name == "pyproject.toml":
        versions.setdefault("python", [])
        data = tomllib.loads(_read_manifest(root, relative, deadline))
        poetry_python = (
            data.get("tool", {}).get("poetry", {}).get("dependencies", {}).get("python")
        )
        if isinstance(poetry_python, dict):
            poetry_python = poetry_python.get("version")
        _declaration(
            versions,
            "python",
            relative,
            "requires-python",
            data.get("project", {}).get("requires-python"),
        )
        _declaration(
            versions,
            "python",
            relative,
            "poetry-python",
            poetry_python,
        )
    elif name == "setup.cfg":
        versions.setdefault("python", [])
        config = configparser.ConfigParser(interpolation=None)
        config.read_string(_read_manifest(root, relative, deadline))
        _declaration(
            versions,
            "python",
            relative,
            "python_requires",
            config.get("options", "python_requires", fallback=None),
        )
    elif name == ".python-version":
        versions.setdefault("python", [])
        for line in _read_manifest(root, relative, deadline).splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                _declaration(versions, "python", relative, "python-version", line)
    elif name == "package.json":
        data = json.loads(_read_manifest(root, relative, deadline))
        if not isinstance(data, dict):
            raise InventoryError("package manifest is invalid")
        for section in (
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
        ):
            dependencies = data.get(section, {})
            if not isinstance(dependencies, dict):
                raise InventoryError("package dependencies are invalid")
            if "typescript" in dependencies:
                versions.setdefault("typescript", [])
                _declaration(
                    versions,
                    "typescript",
                    relative,
                    section,
                    dependencies["typescript"],
                )
    elif name == "pubspec.yaml":
        versions.setdefault("dart", [])
        data = _load_pubspec(_read_manifest(root, relative, deadline), deadline)
        if not isinstance(data, dict):
            raise InventoryError("pubspec manifest is invalid")
        environment = data.get("environment", {})
        if not isinstance(environment, dict):
            raise InventoryError("pubspec environment is invalid")
        _declaration(versions, "dart", relative, "sdk", environment.get("sdk"))


def scan(root: Path, deadline: float | None = None) -> dict[str, Any]:
    """Return one source-only observation for an already verified Git root."""
    versions: dict[str, list[dict[str, str]]] = {}
    if deadline is None:
        deadline = time.monotonic() + SCAN_TIMEOUT_SECONDS
    try:
        for relative in _tracked_candidates(root, deadline):
            _remaining(deadline)
            path = Path(relative)
            name = path.name
            manifest = (
                name in ROOT_MANIFESTS
                or name.startswith("requirements")
                and name.endswith(".txt")
                or name.startswith("tsconfig")
                and name.endswith(".json")
            )
            regular = _regular_file(root, relative, deadline)
            if regular is None:
                continue
            if not regular and manifest:
                raise InventoryError("manifest path is unsafe")
            if not regular:
                continue
            suffix = path.suffix
            if suffix in LANGUAGE_SUFFIXES:
                versions.setdefault(LANGUAGE_SUFFIXES[suffix], [])
            if manifest:
                _scan_manifest(versions, root, relative, deadline)
    except (
        InventoryError,
        ValueError,
        TypeError,
        AttributeError,
        OSError,
        tomllib.TOMLDecodeError,
        json.JSONDecodeError,
        yaml.YAMLError,
        RecursionError,
        configparser.Error,
    ) as error:
        raise InventoryError("language declarations are unavailable") from error
    languages = []
    for name in sorted(versions):
        _remaining(deadline)
        declarations = versions[name]
        declarations.sort(key=lambda item: (item["path"], item["kind"], item["value"]))
        unique = []
        for declaration in declarations:
            if not unique or declaration != unique[-1]:
                unique.append(declaration)
        languages.append({"name": name, "declarations": unique})
    _remaining(deadline)
    return {
        "git_root": str(root),
        "observed_at": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "languages": languages,
    }
