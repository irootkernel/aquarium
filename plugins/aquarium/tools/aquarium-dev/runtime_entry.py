#!/usr/bin/env -S python3 -E -s -B
"""Launch the explicitly installed Aquarium development manager without installing it."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

RUNTIME_SCHEMA = "aquarium-dev-runtime/v1"
SETUP_ACTION = "Use $aquarium:dev-setup-global to diagnose and explicitly install or update aquarium-dev."
GENERATION_RE = re.compile(r"([0-9a-f]{64}-py[0-9]+\.[0-9]+)(?:-r[0-9a-f]{32})?")


class RuntimeUnavailable(ValueError):
    """The installed runtime cannot be used safely."""


def manager_root() -> Path:
    return Path.home() / ".aquarium-dev/manager"


def regular_path(path: Path) -> None:
    """Reject symbolic paths below the user's home before reading or writing state."""
    relative = path.relative_to(Path.home())
    current = Path.home()
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise RuntimeUnavailable(f"Symbolic runtime path: {current}")


def payload_identity(directory: Path, version: str) -> dict:
    files = {}
    for path in sorted([*directory.glob("*.py"), directory / "requirements.txt"]):
        if path.is_symlink() or not path.is_file():
            raise RuntimeUnavailable(f"Invalid runtime source: {path}")
        files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    required = {
        "aquarium_dev.py",
        "dev_manager.py",
        "dev_contract.py",
        "aquarium_dev_launcher.py",
        "runtime_entry.py",
        "mcp_server.py",
        "install.py",
    }
    if not required <= files.keys():
        raise RuntimeUnavailable("The runtime source is incomplete.")
    encoded = json.dumps(
        {"plugin_version": version, "files": files}, sort_keys=True
    ).encode()
    return {
        "schema": RUNTIME_SCHEMA,
        "plugin_version": version,
        "source_sha256": hashlib.sha256(encoded).hexdigest(),
        "files": files,
    }


def bundled_identity(directory: Path) -> dict:
    manifest = directory.parent.parent / ".codex-plugin/plugin.json"
    if manifest.is_symlink():
        raise RuntimeUnavailable("The plugin manifest is symbolic.")
    metadata = json.loads(manifest.read_text())
    if metadata["name"] != "aquarium":
        raise RuntimeUnavailable("The runtime source is not an Aquarium plugin.")
    return payload_identity(directory, metadata["version"])


def runtime_python(generation: Path) -> Path:
    regular_path(generation / "venv/pyvenv.cfg")
    regular_path(generation / "venv/bin")
    if not (generation / "venv/pyvenv.cfg").is_file():
        raise RuntimeUnavailable("The runtime virtual environment is invalid.")
    python = generation / "venv/bin/python"
    if not python.is_file():
        raise RuntimeUnavailable("The runtime Python environment is missing.")
    return python


def selected_runtime() -> tuple[Path, dict]:
    root = manager_root()
    regular_path(root / "versions")
    current = root / "current"
    if not current.is_symlink():
        raise RuntimeUnavailable(
            "The aquarium-dev runtime is missing or its selector is invalid."
        )
    target = Path(os.readlink(current))
    if (
        len(target.parts) != 2
        or target.parts[0] != "versions"
        or not GENERATION_RE.fullmatch(target.name)
    ):
        raise RuntimeUnavailable(
            "The runtime selector escapes the managed generations."
        )
    generation = root / target
    regular_path(generation / "runtime.json")
    receipt = json.loads((generation / "runtime.json").read_text())
    identity = payload_identity(generation, receipt["plugin_version"])
    if any(receipt.get(key) != value for key, value in identity.items()):
        raise RuntimeUnavailable("The installed runtime no longer matches its receipt.")
    if GENERATION_RE.fullmatch(generation.name).group(1) != (
        f"{identity['source_sha256']}-py{receipt['python_version']}"
    ):
        raise RuntimeUnavailable("The runtime generation identity is invalid.")
    runtime_python(generation)
    return generation, receipt


def main() -> int:
    try:
        generation, receipt = selected_runtime()
        command = sys.argv[1:]
        # Plugin MCP startup must not silently run a different installed package.
        if (
            command == ["mcp"]
            and Path(__file__).with_name("requirements.txt").is_file()
            and not Path(__file__).with_name("runtime.json").exists()
            and bundled_identity(Path(__file__).parent)["source_sha256"]
            != receipt["source_sha256"]
        ):
            raise RuntimeUnavailable(
                "The Aquarium plugin and installed runtime differ; an explicit runtime update is required."
            )
        python = generation / "venv/bin/python"
        os.execv(
            python,
            [
                str(python),
                "-E",
                "-s",
                "-B",
                str(generation / "aquarium_dev.py"),
                *command,
            ],
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(
            json.dumps(
                {
                    "schema": "aquarium-dev-runtime-error/v1",
                    "error": {
                        "code": "runtime_unavailable",
                        "message": str(error),
                        "action": SETUP_ACTION,
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
