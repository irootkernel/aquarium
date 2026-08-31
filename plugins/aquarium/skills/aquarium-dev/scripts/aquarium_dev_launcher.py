#!/usr/bin/env python3
"""Run one supported Aquarium development executable without stable fallback."""

from __future__ import annotations

import fcntl
import os
import re
import stat
import sys
from pathlib import Path

SUPPORTED_DEVELOPMENT_COMMANDS = frozenset({"podway", "mulgae", "gaori", "sanho"})
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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
        raise OSError(f"development generation is unavailable: {tool}")
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
        executable, lease_descriptor = leased_executable(command[0])
        os.execve(
            executable,
            command,
            development_environment(dict(os.environ)),
        )
    except OSError as error:
        print(f"aquarium-dev: {error}", file=sys.stderr)
        return 127
    finally:
        if lease_descriptor is not None:
            os.close(lease_descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
