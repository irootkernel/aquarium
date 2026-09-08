#!/usr/bin/env python3
"""Diagnose or explicitly install the runtime bundled with this Aquarium plugin."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import venv
from pathlib import Path

from dev_manager import ManagerError, require_supported_host
from runtime_entry import (
    SETUP_ACTION,
    RuntimeUnavailable,
    bundled_identity,
    manager_root,
    payload_identity,
    regular_path,
    runtime_python,
    selected_runtime,
)


def check_launcher(target: Path) -> None:
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise RuntimeUnavailable("The launcher target is not a regular file.")


def diagnose(source: Path) -> dict:
    bundled = bundled_identity(source)
    installed = None
    problem = None
    try:
        generation, installed = selected_runtime()
        verify_environment(generation)
        status = (
            "current"
            if installed["source_sha256"] == bundled["source_sha256"]
            else "outdated"
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        current = manager_root() / "current"
        status = "broken" if current.exists() or current.is_symlink() else "missing"
        problem = str(error)
    launcher = Path.home() / ".local/bin/aquarium-dev"
    try:
        check_launcher(launcher)
        launcher_current = (
            launcher.is_file()
            and os.access(launcher, os.X_OK)
            and launcher.read_bytes() == (source / "runtime_entry.py").read_bytes()
        )
    except (OSError, ValueError):
        launcher_current = False
    return {
        "schema": "aquarium-dev-runtime-inspection/v1",
        "status": status,
        "bundled": {key: bundled[key] for key in ("plugin_version", "source_sha256")},
        "installed": {
            key: installed[key]
            for key in ("plugin_version", "source_sha256", "python_version")
        }
        if installed
        else None,
        "launcher_current": launcher_current,
        "source": str(source),
        "manager_root": str(manager_root()),
        "launcher": str(launcher),
        "problem": problem,
        "action": SETUP_ACTION if status != "current" or not launcher_current else None,
    }


def install_dependencies(generation: Path) -> None:
    venv.EnvBuilder(with_pip=True).create(generation / "venv")
    subprocess.run(
        [
            str(generation / "venv/bin/python"),
            "-E",
            "-s",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "--no-input",
            "install",
            "--index-url",
            "https://pypi.org/simple",
            "--require-hashes",
            "--only-binary=:all:",
            "-r",
            str(generation / "requirements.txt"),
        ],
        check=True,
        stdout=sys.stderr,
    )


def verify_environment(generation: Path) -> None:
    python = runtime_python(generation)
    program = """
import importlib.metadata as metadata
import pathlib, sys
from mcp.server import Server
from mcp.types import CallToolResult
assert pathlib.Path(sys.prefix).resolve() == pathlib.Path(sys.argv[2], 'venv').resolve()
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
    if '==' in line and not line.startswith(' '):
        name, expected = line.split('==')
        assert metadata.version(name) == expected.rstrip(' \\\\'), name
sys.path.insert(0, sys.argv[2])
import mcp_server
assert mcp_server.create_server()
"""
    try:
        subprocess.run(
            [
                str(python),
                "-I",
                "-B",
                "-c",
                program,
                str(generation / "requirements.txt"),
                str(generation),
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or b"")[-4096:].decode("utf-8", errors="replace").strip()
        message = f"Runtime environment verification failed (exit {error.returncode})."
        raise RuntimeUnavailable(
            f"{message} {detail}" if detail else message
        ) from error


def atomic_file(target: Path, content: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.", dir=target.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def select_generation(root: Path, target: str) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".current.", dir=root)
    os.close(descriptor)
    Path(temporary).unlink()
    try:
        os.symlink(target, temporary)
        os.replace(temporary, root / "current")
    finally:
        Path(temporary).unlink(missing_ok=True)


def reusable_generation(generation: Path, receipt: dict) -> bool:
    try:
        regular_path(generation / "runtime.json")
        if json.loads((generation / "runtime.json").read_text()) != receipt:
            return False
        identity = {
            key: value for key, value in receipt.items() if key != "python_version"
        }
        if payload_identity(generation, receipt["plugin_version"]) != identity:
            return False
        verify_environment(generation)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return False
    return True


def install(source: Path, *, approve_install: bool, approve_launcher: bool) -> dict:
    if not approve_install or not approve_launcher:
        raise RuntimeUnavailable(
            "Runtime installation and launcher installation require explicit approval (--approve-install --approve-launcher)."
        )
    require_supported_host()
    if sys.version_info < (3, 11):
        raise RuntimeUnavailable("Python 3.11 or newer is required.")
    identity = bundled_identity(source)
    root = manager_root()
    launcher = Path.home() / ".local/bin/aquarium-dev"
    for path in (root / "versions", root / "install.lock"):
        regular_path(path)
    check_launcher(launcher)
    current = root / "current"
    if current.exists() and not current.is_symlink():
        raise RuntimeUnavailable("The runtime selector is not a symbolic link.")
    root.mkdir(parents=True, exist_ok=True)
    with (root / "install.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Recheck after the installer lock; never switch to an unverified payload.
        check_launcher(launcher)
        (root / "versions").mkdir(exist_ok=True)
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        generation = (
            root / "versions" / f"{identity['source_sha256']}-py{python_version}"
        )
        regular_path(generation)
        receipt = {**identity, "python_version": python_version}
        try:
            selected, selected_receipt = selected_runtime()
        except (OSError, ValueError, KeyError, TypeError):
            selected = None
        if selected is not None and selected_receipt == receipt:
            generation = selected
        if generation.exists() and not reusable_generation(generation, receipt):
            # Existing sessions may still use this directory, even when damaged.
            generation = (
                root
                / "versions"
                / (
                    f"{identity['source_sha256']}-py{python_version}-r{uuid.uuid4().hex}"
                )
            )
        created = False
        try:
            if not generation.exists():
                generation.mkdir()
                created = True
                for name in identity["files"]:
                    shutil.copyfile(source / name, generation / name)
                # venv paths must remain fixed: prepare at the final unselected path.
                install_dependencies(generation)
                atomic_file(
                    generation / "runtime.json",
                    (json.dumps(receipt, sort_keys=True) + "\n").encode(),
                    0o644,
                )
            if json.loads((generation / "runtime.json").read_text()) != receipt:
                raise RuntimeUnavailable(
                    "The existing runtime generation has a conflicting receipt."
                )
            if (
                payload_identity(generation, identity["plugin_version"]) != identity
                or bundled_identity(source) != identity
            ):
                raise RuntimeUnavailable(
                    "The runtime source changed during installation."
                )
            verify_environment(generation)
            launcher.parent.mkdir(parents=True, exist_ok=True)
            old_launcher = launcher.read_bytes() if launcher.exists() else None
            old_mode = (
                launcher.stat().st_mode & 0o777 if old_launcher is not None else 0o755
            )
            target = f"versions/{generation.name}"
            old_target = os.readlink(current) if current.is_symlink() else None
            content = (generation / "runtime_entry.py").read_bytes()
            if old_target == target and old_launcher == content and old_mode == 0o755:
                return {"status": "no-change", "details": diagnose(source)}
            try:
                atomic_file(launcher, content, 0o755)
                select_generation(root, target)
            except BaseException:
                if current.is_symlink() and os.readlink(current) == target:
                    if old_target is None:
                        current.unlink()
                    else:
                        select_generation(root, old_target)
                if old_launcher is None:
                    launcher.unlink(missing_ok=True)
                else:
                    atomic_file(launcher, old_launcher, old_mode)
                raise
        except BaseException:
            if created and not (
                current.is_symlink()
                and os.readlink(current) == f"versions/{generation.name}"
            ):
                shutil.rmtree(generation, ignore_errors=True)
            raise
    # Retain prior versions: admitted workers and open MCP sessions still use them.
    return {"status": "success", "details": diagnose(source)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("diagnose", "install"))
    parser.add_argument("--approve-install", action="store_true")
    parser.add_argument("--approve-launcher", action="store_true")
    arguments = parser.parse_args()
    source = Path(__file__).resolve().parent
    try:
        value = (
            diagnose(source)
            if arguments.operation == "diagnose"
            else install(
                source,
                approve_install=arguments.approve_install,
                approve_launcher=arguments.approve_launcher,
            )
        )
        print(json.dumps(value, sort_keys=True))
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
        ManagerError,
    ) as error:
        print(
            json.dumps(
                {
                    "schema": "aquarium-dev-runtime-error/v1",
                    "error": {
                        "code": "runtime_install_failed",
                        "message": error.message
                        if isinstance(error, ManagerError)
                        else str(error),
                        "action": SETUP_ACTION,
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
