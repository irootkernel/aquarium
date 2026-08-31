#!/usr/bin/env python3
"""Prefer one Aquarium development executable, then use its global release."""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SUPPORTED_DEVELOPMENT_COMMANDS = frozenset(
    {"podway", "mulgae", "gaori", "sanho", "dolgorae"}
)
REQUIRED_GLOBAL_COMMANDS = frozenset({"podway", "mulgae", "gaori", "dolgorae"})
MANAGED_SERVICE_COMMANDS = frozenset({"podway"})
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


def _lock_descriptor(path: Path) -> int:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    identity = os.fstat(descriptor)
    if not stat.S_ISREG(identity.st_mode):
        os.close(descriptor)
        raise OSError("development generation lease is invalid")
    fcntl.flock(descriptor, fcntl.LOCK_SH)
    os.set_inheritable(descriptor, True)
    return descriptor


def _managed_service_executable(
    host_root: Path, tool: str, generation: Path
) -> tuple[Path, int]:
    manifest_path = generation / ".aquarium-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise OSError(f"managed-service manifest is invalid: {tool}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OSError(f"managed-service manifest is invalid: {tool}") from error
    expected_fields = {
        "schema",
        "project_id",
        "git_sha",
        "development_version",
        "artifact_kind",
        "artifact_path",
        "command_path",
        "controller_path",
        "sha256",
    }
    if (
        not isinstance(manifest, dict)
        or set(manifest) != expected_fields
        or manifest.get("schema") != "aquarium-dev-artifact-manifest/v2"
        or manifest.get("project_id") != tool
        or manifest.get("git_sha") != generation.name
        or manifest.get("artifact_kind") != "managed-service"
        or manifest.get("artifact_path") != "bundle"
        or manifest.get("command_path") != f"bin/{tool}"
        or manifest.get("controller_path") != "libexec/aquarium-dev-service"
    ):
        raise OSError(f"managed-service manifest is invalid: {tool}")
    artifact = generation / manifest["artifact_path"]
    executable = artifact / manifest["command_path"]
    controller = artifact / manifest["controller_path"]
    for candidate in (executable, controller):
        if (
            candidate.is_symlink()
            or not candidate.is_file()
            or not os.access(candidate, os.X_OK)
        ):
            raise OSError(f"managed-service entrypoint is invalid: {tool}")
    service_lock = _lock_descriptor(host_root / "locks" / "services" / f"{tool}.lock")
    try:
        result = subprocess.run(
            [
                os.fspath(controller),
                "status",
                "--json",
                "--runtime-root",
                os.fspath(host_root / "runtime" / tool),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        status = json.loads(result.stdout) if result.returncode == 0 else None
        if (
            not isinstance(status, dict)
            or set(status)
            != {
                "schema",
                "project_id",
                "state",
                "active_git_sha",
                "busy",
                "recovery_required",
            }
            or status.get("schema") != "aquarium-dev-service-status/v1"
            or status.get("project_id") != tool
            or status.get("state") not in {"ready", "busy"}
            or status.get("active_git_sha") != generation.name
            or status.get("busy") != (status.get("state") == "busy")
            or status.get("recovery_required") is not False
        ):
            raise OSError(f"managed development service is unavailable: {tool}")
        return executable, service_lock
    except Exception:
        os.close(service_lock)
        raise


def leased_executable(tool: str) -> tuple[Path, tuple[int, ...]]:
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
    descriptor = _lock_descriptor(lock_path)
    try:
        if current.resolve(strict=True) != generation:
            raise OSError(f"development generation changed during launch: {tool}")
        manifest_path = generation / ".aquarium-manifest.json"
        managed_generation = False
        if manifest_path.is_file() and not manifest_path.is_symlink():
            try:
                managed_generation = (
                    json.loads(manifest_path.read_text(encoding="utf-8")).get("schema")
                    == "aquarium-dev-artifact-manifest/v2"
                )
            except (OSError, AttributeError, json.JSONDecodeError):
                pass
        if tool in MANAGED_SERVICE_COMMANDS or managed_generation:
            executable, service_descriptor = _managed_service_executable(
                host_root, tool, generation
            )
            if current.resolve(strict=True) != generation:
                os.close(service_descriptor)
                raise OSError(
                    f"development generation changed during service launch: {tool}"
                )
            return executable, (descriptor, service_descriptor)
        executable = generation / "bin" / tool
        if (
            executable.is_symlink()
            or not executable.is_file()
            or not os.access(executable, os.X_OK)
        ):
            raise OSError(f"development executable is invalid: {tool}")
        return executable, (descriptor,)
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
        message = f"development and global executable are unavailable: {tool}"
        if tool in REQUIRED_GLOBAL_COMMANDS:
            message += f"; request $aquarium:dev-setup for {tool}"
        raise OSError(message)
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
    lease_descriptors: tuple[int, ...] = ()
    try:
        environment = dict(os.environ)
        try:
            executable, lease_descriptors = leased_executable(command[0])
        except DevelopmentGenerationUnavailable:
            pending = Path.home() / ".aquarium-dev" / "pending" / command[0]
            if command[0] in MANAGED_SERVICE_COMMANDS or pending.is_symlink():
                raise OSError(
                    f"managed development service is unavailable: {command[0]}"
                )
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
        for descriptor in lease_descriptors:
            os.close(descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
