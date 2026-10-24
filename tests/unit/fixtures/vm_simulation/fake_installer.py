#!/usr/bin/env python3
"""Facts-shaped fake status installer for the offline guest simulation."""

import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path


def require_absolute_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value or not os.path.isabs(value):
        raise SystemExit(f"{name} must be a non-empty absolute path")
    return value


arguments = sys.argv[1:]
command = arguments[0] if arguments else "diagnose"
source = Path(arguments[arguments.index("--source") + 1])
home = Path(require_absolute_env("AQUARIUM_GUEST_HOME"))
runtime = home / ".aquarium/status-runtime"
versions = runtime / "versions"
PAYLOAD = ("install.py", "plugin.json", "requirements.txt")


def source_digest() -> str:
    payload = "".join(
        hashlib.sha256((source / name).read_bytes()).hexdigest() + "  " + name + "\n"
        for name in sorted(PAYLOAD)
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def plugin_version() -> str:
    manifest = source.parents[1] / ".codex-plugin/plugin.json"
    version = json.loads(manifest.read_text())["version"]
    return "v" + version


def diagnose():
    current = runtime / "current"
    if not current.is_file():
        return {"schema": "aquarium-status-runtime-inspection/v1", "status": "missing"}
    name = current.read_text().strip().removeprefix("versions/")
    receipt = json.loads((versions / name / "runtime.json").read_text())
    return {
        "schema": "aquarium-status-runtime-inspection/v1",
        "status": "ready",
        "generation": name,
        "receipt": receipt,
    }


def valid_generation(path: Path) -> bool:
    receipt = path / "runtime.json"
    if not receipt.is_file():
        return False
    document = json.loads(receipt.read_text())
    return (
        document.get("source_sha256") == source_digest()
        and document.get("plugin_version") == plugin_version()
    )


def install():
    fail_version = os.environ.get("FAKE_INSTALLER_FAIL_VERSION")
    if fail_version and plugin_version() == fail_version:
        print(
            json.dumps(
                {
                    "schema": "aquarium-status-runtime-error/v1",
                    "error": {
                        "code": "runtime_install_failed",
                        "message": "injected failure",
                    },
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)
    launcher = home / ".local/bin/aquarium-status"
    if launcher.is_symlink():
        print(
            json.dumps(
                {
                    "schema": "aquarium-status-runtime-error/v1",
                    "error": {
                        "code": "runtime_install_failed",
                        "message": "unsafe launcher",
                    },
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)
    digest = source_digest()
    version = plugin_version()
    base = f"{digest}-py{sys.version_info.major}.{sys.version_info.minor}"
    generation = versions / base
    staging_seconds = int(os.environ.get("FAKE_INSTALLER_STAGE_SECONDS", "0"))
    if not (generation.exists() and valid_generation(generation)):
        if generation.exists():
            base = f"{base}-r{uuid.uuid4().hex}"
            generation = versions / base
        versions.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".generation.", dir=versions))
        if staging_seconds:
            time.sleep(staging_seconds)
        for name in sorted(PAYLOAD):
            shutil.copyfile(source / name, staging / name)
            os.chmod(staging / name, 0o600)
        receipt = {
            "schema": "aquarium-status-runtime/v1",
            "source_sha256": digest,
            "plugin_version": version,
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "python_executable_sha256": (
                # Fixture-side fault: a wrong binding digest makes the
                # receipt identity check fail functionally while the run
                # still leaves a clean end state.
                "e" * 64
                if os.environ.get("FAKE_INSTALLER_MISMATCH_RECEIPT")
                else hashlib.sha256(
                    Path(require_absolute_env("FAKE_PYTHON_BINDING")).read_bytes()
                ).hexdigest()
            ),
            "requirements_sha256": hashlib.sha256(
                (source / "requirements.txt").read_bytes()
            ).hexdigest(),
            "files": {},
            "dependency_files": {},
        }
        (staging / "runtime.json").write_text(json.dumps(receipt))
        os.rename(staging, generation)
    if os.environ.get("FAKE_INSTALLER_LEAVE_FIFO"):
        versions.mkdir(parents=True, exist_ok=True)
        evil = versions / ".evil-fifo"
        if not evil.exists() and not evil.is_symlink():
            os.mkfifo(evil)
    if os.environ.get("FAKE_INSTALLER_TOUCH_SKILLS"):
        skills = home / ".agents/skills/deslop"
        skills.mkdir(parents=True, exist_ok=True)
        (skills / "UNEXPECTED.md").write_text("drift\n")
    current = runtime / "current"
    current.write_text(f"versions/{base}\n")
    os.chmod(current, 0o600)
    launcher.parent.mkdir(parents=True, exist_ok=True)
    temporary = launcher.with_name(".launcher.tmp")
    temporary.write_text("#!/bin/sh\n# aquarium-status managed launcher v1\n")
    os.chmod(temporary, 0o755)
    os.rename(temporary, launcher)
    print(json.dumps(diagnose()))


if command == "install":
    if "--approve-install" not in arguments or "--approve-launcher" not in arguments:
        print(
            json.dumps(
                {
                    "schema": "aquarium-status-runtime-error/v1",
                    "error": {"code": "runtime_install_failed"},
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)
    install()
elif command == "diagnose":
    print(json.dumps(diagnose()))
else:
    print(
        json.dumps(
            {
                "schema": "aquarium-status-runtime-error/v1",
                "error": {"code": "unsupported"},
            }
        ),
        file=sys.stderr,
    )
    raise SystemExit(1)
