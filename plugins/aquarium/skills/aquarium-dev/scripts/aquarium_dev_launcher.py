#!/usr/bin/env python3
"""Prefer one Aquarium development executable, then use its global release."""

from __future__ import annotations

import fcntl
import os
import re
import shutil
import stat
import sys
from pathlib import Path

SUPPORTED_DEVELOPMENT_COMMANDS = frozenset(
    {"podway", "mulgae", "gaori", "sanho", "dolgorae"}
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class DevelopmentGenerationUnavailable(OSError):
    """The tool has no selected Aquarium development generation."""


def development_environment(environment: dict[str, str]) -> dict[str, str]:
    result = environment.copy()
    development_bin = str(Path.home() / ".aquarium-dev" / "bin")
    existing_path = result.get("PATH")
    result["PATH"] = (
        f"{development_bin}{os.pathsep}{existing_path}"
        if existing_path
        else development_bin
    )
    return result


def leased_executable(tool: str) -> tuple[Path, int]:
    host_root = Path.home() / ".aquarium-dev"
    current = host_root / "current" / tool
    if not current.is_symlink():
        if current.exists():
            raise OSError(f"development generation is invalid: {tool}")
        raise DevelopmentGenerationUnavailable(
            f"development generation is unavailable: {tool}"
        )
    generation = current.resolve(strict=True)
    expected_parent = (host_root / "artifacts" / tool).resolve(strict=True)
    if (
        generation.parent != expected_parent
        or SHA_RE.fullmatch(generation.name) is None
    ):
        raise OSError(f"development generation is invalid: {tool}")
    lock_path = host_root / "locks" / "artifacts" / tool / f"{generation.name}.lock"
    descriptor = os.open(lock_path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        identity = os.fstat(descriptor)
        if not stat.S_ISREG(identity.st_mode):
            raise OSError(f"development generation lease is invalid: {tool}")
        fcntl.flock(descriptor, fcntl.LOCK_SH)
        if current.resolve(strict=True) != generation:
            raise OSError(f"development generation changed during launch: {tool}")
        executable = generation / "bin" / tool
        if (
            executable.is_symlink()
            or not executable.is_file()
            or not os.access(executable, os.X_OK)
        ):
            raise OSError(f"development executable is invalid: {tool}")
        os.set_inheritable(descriptor, True)
        return executable, descriptor
    except Exception:
        os.close(descriptor)
        raise


def global_executable(tool: str, environment: dict[str, str]) -> Path:
    home = Path.home().resolve()
    excluded_roots = (home / ".aquarium", home / ".aquarium-dev")
    search_entries = []
    for entry in environment.get("PATH", "").split(os.pathsep):
        candidate = Path(entry)
        if not entry or not candidate.is_absolute():
            continue
        resolved = candidate.resolve(strict=False)
        if any(
            resolved == root or resolved.is_relative_to(root) for root in excluded_roots
        ):
            continue
        search_entries.append(entry)
    selected = shutil.which(tool, path=os.pathsep.join(search_entries))
    if selected is None:
        raise OSError(f"development and global executable are unavailable: {tool}")
    executable = Path(selected).resolve(strict=True)
    if (
        not executable.is_file()
        or not os.access(executable, os.X_OK)
        or any(
            executable == root or executable.is_relative_to(root)
            for root in excluded_roots
        )
    ):
        raise OSError(f"global executable is invalid: {tool}")
    return executable


def main(arguments: list[str] | None = None) -> int:
    command = list(sys.argv[1:] if arguments is None else arguments)
    if not command:
        print("usage: aquarium-dev <tool> [args...]", file=sys.stderr)
        return 2
    if command[0] not in SUPPORTED_DEVELOPMENT_COMMANDS:
        print(
            f"aquarium-dev: unsupported development command: {command[0]}",
            file=sys.stderr,
        )
        return 2
    lease_descriptor = None
    try:
        environment = dict(os.environ)
        try:
            executable, lease_descriptor = leased_executable(command[0])
        except DevelopmentGenerationUnavailable:
            executable = global_executable(command[0], environment)
        os.execve(
            executable,
            command,
            development_environment(environment),
        )
    except OSError as error:
        print(f"aquarium-dev: {error}", file=sys.stderr)
        return 127
    finally:
        if lease_descriptor is not None:
            os.close(lease_descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
