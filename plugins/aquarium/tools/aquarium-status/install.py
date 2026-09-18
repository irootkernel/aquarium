#!/usr/bin/env python3
"""Diagnose and install the user-global aquarium-status runtime."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

RUNTIME_SCHEMA = "aquarium-status-runtime/v1"
INSPECTION_SCHEMA = "aquarium-status-runtime-inspection/v1"
ERROR_SCHEMA = "aquarium-status-runtime-error/v1"
PAYLOAD = (
    "aquarium_status.py",
    "status_contract.py",
    "status_store.py",
    "status_report.py",
    "runtime_entry.py",
    "requirements.txt",
)
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
VERSION_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")


class RuntimeFailure(RuntimeError):
    """Managed runtime state is missing, broken, or unsafe."""


class UnsafeRuntimeFailure(RuntimeFailure):
    """An owned runtime path has an unsafe type, link, or mode."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise RuntimeFailure("invalid installer arguments")


def runtime_root() -> Path:
    return Path.home() / ".aquarium/status-runtime"


def launcher_path() -> Path:
    return Path.home() / ".local/bin/aquarium-status"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def source_digest(files: dict[str, str]) -> str:
    data = "".join(f"{files[name]}  {name}\n" for name in sorted(files)).encode()
    return hashlib.sha256(data).hexdigest()


def source_identity(source: Path) -> dict[str, Any]:
    files = {name: sha256(source / name) for name in PAYLOAD}
    manifest = source.parents[1] / ".codex-plugin/plugin.json"
    plugin_version = f"v{json.loads(manifest.read_text(encoding='utf-8'))['version']}"
    if VERSION_RE.fullmatch(plugin_version) is None:
        raise RuntimeFailure("bundled plugin version is invalid")
    return {
        "plugin_version": plugin_version,
        "source_sha256": source_digest(files),
        "files": files,
    }


def _kind(path: Path) -> str:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return "missing"
    if stat.S_ISLNK(info.st_mode):
        return "unsafe"
    if stat.S_ISREG(info.st_mode):
        return "regular"
    if stat.S_ISDIR(info.st_mode):
        return "directory"
    return "unsafe"


def _directory(path: Path, mode: int | None = None) -> None:
    kind = _kind(path)
    if kind == "missing":
        raise RuntimeFailure(f"owned directory is missing: {path}")
    if kind != "directory":
        raise UnsafeRuntimeFailure(f"owned directory is unavailable or unsafe: {path}")
    if mode is not None and stat.S_IMODE(path.stat().st_mode) != mode:
        raise UnsafeRuntimeFailure(f"owned directory mode is unsafe: {path}")


def _regular(path: Path, mode: int | None = None) -> None:
    kind = _kind(path)
    if kind == "missing":
        raise RuntimeFailure(f"owned file is missing: {path}")
    if kind != "regular":
        raise UnsafeRuntimeFailure(f"owned file is unavailable or unsafe: {path}")
    if mode is not None and stat.S_IMODE(path.stat().st_mode) != mode:
        raise UnsafeRuntimeFailure(f"owned file mode is unsafe: {path}")


def _regular_external(path: Path) -> None:
    if _kind(path) != "regular":
        raise RuntimeFailure(f"recorded external file is unavailable: {path}")


def _existing_roots(root: Path) -> None:
    aquarium = root.parent
    if _kind(aquarium) != "missing":
        _directory(aquarium, 0o700)
    if _kind(root) != "missing":
        _directory(root, 0o700)
    if _kind(root / "versions") != "missing":
        _directory(root / "versions", 0o700)
    local = Path.home() / ".local"
    if _kind(local) != "missing":
        _directory(local)
    if _kind(local / "bin") != "missing":
        _directory(local / "bin")


def _validate_hash_map(value: Any, *, dependencies: bool) -> dict[str, str]:
    if not isinstance(value, dict) or any(
        not isinstance(name, str)
        or not isinstance(digest, str)
        or SHA_RE.fullmatch(digest) is None
        for name, digest in value.items()
    ):
        raise RuntimeFailure("runtime receipt hash map is invalid")
    if dependencies:
        for name in value:
            path = Path(name)
            if (
                not name.startswith("dependencies/")
                or path.is_absolute()
                or ".." in path.parts
                or "." in path.parts
            ):
                raise RuntimeFailure("runtime dependency path is invalid")
    elif set(value) != set(PAYLOAD):
        raise RuntimeFailure("runtime payload manifest is incomplete")
    return value


def validate_receipt(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != RECEIPT_KEYS:
        raise RuntimeFailure("runtime receipt shape is invalid")
    if (
        value["schema"] != RUNTIME_SCHEMA
        or not isinstance(value["plugin_version"], str)
        or VERSION_RE.fullmatch(value["plugin_version"]) is None
        or not isinstance(value["source_sha256"], str)
        or SHA_RE.fullmatch(value["source_sha256"]) is None
        or not isinstance(value["python_version"], str)
        or not isinstance(value["python_executable"], str)
        or not Path(value["python_executable"]).is_absolute()
        or any(
            not isinstance(value[name], str) or SHA_RE.fullmatch(value[name]) is None
            for name in ("python_executable_sha256", "requirements_sha256")
        )
    ):
        raise RuntimeFailure("runtime receipt identity is invalid")
    files = _validate_hash_map(value["files"], dependencies=False)
    _validate_hash_map(value["dependency_files"], dependencies=True)
    if value["requirements_sha256"] != files["requirements.txt"] or value[
        "source_sha256"
    ] != source_digest(files):
        raise RuntimeFailure("runtime receipt digest relationship is invalid")
    return value


def launcher_bytes(generation: Path, receipt: dict[str, Any]) -> bytes:
    interpreter = shlex.quote(receipt["python_executable"])
    entry = shlex.quote(str(generation / "runtime_entry.py"))
    return (
        "#!/bin/sh\n"
        "# aquarium-status managed launcher v1\n"
        f'exec {interpreter} -B -I -S {entry} "$@"\n'
    ).encode()


def _selector_claims_generation(root: Path, generation: Path) -> bool:
    current = root / "current"
    kind = _kind(current)
    if kind == "missing":
        return False
    _regular(current, 0o600)
    try:
        return current.read_text(encoding="utf-8").strip() == (
            f"versions/{generation.name}"
        )
    except (OSError, UnicodeError):
        return False


def managed_launcher_candidate(path: Path, root: Path) -> bool:
    try:
        _regular(path, 0o755)
        raw = path.read_bytes()
        if len(raw) > 4096:
            return False
        lines = raw.decode("utf-8").splitlines()
        if (
            lines[:2]
            != [
                "#!/bin/sh",
                "# aquarium-status managed launcher v1",
            ]
            or len(lines) != 3
        ):
            return False
        tokens = shlex.split(lines[2])
        if len(tokens) != 7 or tokens[0] != "exec":
            return False
        if tokens[2:5] != ["-B", "-I", "-S"] or tokens[6] != "$@":
            return False
        interpreter = Path(tokens[1])
        entry = Path(tokens[5])
        generation = entry.parent
        if (
            not interpreter.is_absolute()
            or entry.name != "runtime_entry.py"
            or generation.parent != root / "versions"
        ):
            return False
        selector_claim = _selector_claims_generation(root, generation)
        try:
            receipt = _read_generation(generation, require_children=False)
        except UnsafeRuntimeFailure:
            raise
        except (OSError, UnicodeError, ValueError, TypeError, RuntimeFailure):
            return selector_claim
        return interpreter == Path(
            receipt["python_executable"]
        ) and path.read_bytes() == launcher_bytes(generation, receipt)
    except (OSError, UnicodeError, ValueError):
        return False


def _read_generation(
    generation: Path, *, require_children: bool = True
) -> dict[str, Any]:
    _directory(generation, 0o700)
    children = list(generation.iterdir())
    if any(_kind(path) == "unsafe" for path in children):
        raise UnsafeRuntimeFailure("runtime generation contains an unsafe path")
    if require_children and {path.name for path in children} != set(PAYLOAD) | {
        "dependencies",
        "runtime.json",
    }:
        raise RuntimeFailure("runtime generation contains unexpected paths")
    receipt_path = generation / "runtime.json"
    _regular(receipt_path, 0o600)
    receipt = validate_receipt(json.loads(receipt_path.read_text(encoding="utf-8")))
    major_minor = ".".join(receipt["python_version"].split(".")[:2])
    pattern = re.compile(
        rf"^{receipt['source_sha256']}-py{re.escape(major_minor)}(?:-r[0-9a-f]{{32}})?$"
    )
    if pattern.fullmatch(generation.name) is None:
        raise RuntimeFailure("runtime generation name is invalid")
    return receipt


def _read_selected(root: Path) -> tuple[Path, dict[str, Any]]:
    _existing_roots(root)
    _directory(root, 0o700)
    _directory(root / "versions", 0o700)
    current = root / "current"
    _regular(current, 0o600)
    relative = current.read_text(encoding="utf-8").strip()
    if not relative.startswith("versions/") or Path(
        relative
    ).name != relative.removeprefix("versions/"):
        raise RuntimeFailure("runtime selector is invalid")
    generation = root / relative
    receipt = _read_generation(generation)
    return generation, receipt


def verify_generation(
    generation: Path,
    receipt: dict[str, Any],
    *,
    execute: bool,
) -> None:
    receipt = validate_receipt(receipt)
    _directory(generation, 0o700)
    if {path.name for path in generation.iterdir()} != set(PAYLOAD) | {
        "dependencies",
        "runtime.json",
    }:
        raise RuntimeFailure("runtime generation contains unexpected paths")
    interpreter = Path(receipt["python_executable"])
    _regular_external(interpreter)
    if sha256(interpreter) != receipt["python_executable_sha256"]:
        raise RuntimeFailure("runtime interpreter changed")
    for name in PAYLOAD:
        path = generation / name
        _regular(path, 0o600)
        if sha256(path) != receipt["files"][name]:
            raise RuntimeFailure("runtime payload changed")
    dependency_root = generation / "dependencies"
    _directory(dependency_root)
    observed: dict[str, str] = {}
    for path in dependency_root.rglob("*"):
        kind = _kind(path)
        if kind == "directory":
            continue
        if kind != "regular":
            raise UnsafeRuntimeFailure("runtime dependency path is unsafe")
        observed[path.relative_to(generation).as_posix()] = sha256(path)
    if observed != receipt["dependency_files"]:
        raise RuntimeFailure("runtime dependency content changed")
    if execute:
        program = "import json,sys; sys.dont_write_bytecode=True; sys.path.insert(0,sys.argv[1]); import yaml; print(json.dumps({'python':sys.version.split()[0],'yaml':yaml.__version__}))"
        process = subprocess.run(
            [
                str(interpreter),
                "-B",
                "-I",
                "-S",
                "-c",
                program,
                str(dependency_root),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if json.loads(process.stdout) != {
            "python": receipt["python_version"],
            "yaml": "6.0.3",
        }:
            raise RuntimeFailure("runtime dependency verification failed")


def _inspection(
    bundled: dict[str, Any],
    installed: dict[str, Any] | None,
    launcher: Path,
    launcher_state: str,
    root: Path,
    status: str,
    action: str | None,
) -> dict[str, Any]:
    return {
        "schema": INSPECTION_SCHEMA,
        "status": status,
        "bundled": {
            name: bundled[name] for name in ("plugin_version", "source_sha256")
        },
        "installed": installed,
        "launcher": {"path": str(launcher), "state": launcher_state},
        "runtime_root": str(root),
        "action": action,
    }


def diagnose(source: Path) -> dict[str, Any]:
    bundled = source_identity(source)
    root = runtime_root()
    launcher = launcher_path()
    launcher_kind = _kind(launcher)
    launcher_managed = False
    try:
        _existing_roots(root)
        if launcher_kind in {"unsafe", "directory"}:
            raise RuntimeFailure("launcher is unsafe")
        if launcher_kind == "regular":
            launcher_managed = managed_launcher_candidate(launcher, root)
            if not launcher_managed:
                return _inspection(
                    bundled, None, launcher, "unknown", root, "unsafe", None
                )
        if _kind(root / "current") == "missing":
            if launcher_kind == "regular":
                return _inspection(
                    bundled,
                    None,
                    launcher,
                    "managed_outdated",
                    root,
                    "broken",
                    "repair",
                )
            return _inspection(
                bundled, None, launcher, "missing", root, "missing", "install"
            )
        try:
            generation, receipt = _read_selected(root)
            verify_generation(generation, receipt, execute=True)
            installed = {
                name: receipt[name]
                for name in ("plugin_version", "source_sha256", "python_version")
            }
        except UnsafeRuntimeFailure:
            raise
        except (
            OSError,
            ValueError,
            TypeError,
            RuntimeFailure,
            subprocess.SubprocessError,
        ):
            if launcher_kind == "regular":
                return _inspection(
                    bundled,
                    None,
                    launcher,
                    "managed_outdated",
                    root,
                    "broken",
                    "repair",
                )
            return _inspection(
                bundled, None, launcher, "missing", root, "broken", "repair"
            )
        if launcher_kind == "missing":
            return _inspection(
                bundled, installed, launcher, "missing", root, "broken", "repair"
            )
        if launcher.read_bytes() != launcher_bytes(generation, receipt):
            return _inspection(
                bundled,
                installed,
                launcher,
                "managed_outdated",
                root,
                "broken",
                "repair",
            )
        current = (
            receipt["source_sha256"] == bundled["source_sha256"]
            and receipt["plugin_version"] == bundled["plugin_version"]
        )
        return _inspection(
            bundled,
            installed,
            launcher,
            "managed_current" if current else "managed_outdated",
            root,
            "current" if current else "outdated",
            None if current else "update",
        )
    except RuntimeFailure:
        launcher_state = (
            "managed_outdated"
            if launcher_managed
            else {
                "missing": "missing",
                "regular": "unknown",
                "directory": "unsafe",
                "unsafe": "unsafe",
            }[launcher_kind]
        )
        return _inspection(
            bundled, None, launcher, launcher_state, root, "unsafe", None
        )


def atomic_file(path: Path, content: bytes, mode: int) -> None:
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _create_directory(path: Path, mode: int, parent: Path) -> None:
    _directory(parent)
    if _kind(path) == "missing":
        path.mkdir(mode=mode)
    _directory(path, mode)


def _snapshot(path: Path) -> tuple[bool, bytes, int]:
    if _kind(path) == "missing":
        return False, b"", 0
    _regular(path)
    return True, path.read_bytes(), stat.S_IMODE(path.stat().st_mode)


def _restore(path: Path, snapshot: tuple[bool, bytes, int]) -> None:
    existed, content, mode = snapshot
    if existed:
        atomic_file(path, content, mode)
    else:
        path.unlink(missing_ok=True)


def install(
    source: Path, approve_install: bool, approve_launcher: bool
) -> dict[str, Any]:
    if not approve_install or not approve_launcher:
        raise RuntimeFailure(
            "runtime and launcher installation require explicit approval"
        )
    if (
        platform.system() != "Darwin"
        or platform.machine() != "arm64"
        or sys.version_info < (3, 11)
    ):
        raise RuntimeFailure(
            "aquarium-status requires Python 3.11+ on Apple Silicon macOS"
        )
    if diagnose(source)["status"] == "unsafe":
        raise RuntimeFailure(
            "an unsafe or unknown launcher must be resolved explicitly"
        )
    root = runtime_root()
    aquarium = root.parent
    _create_directory(aquarium, 0o700, Path.home())
    _create_directory(root, 0o700, aquarium)
    versions = root / "versions"
    _create_directory(versions, 0o700, root)
    local = Path.home() / ".local"
    if _kind(local) == "missing":
        local.mkdir(mode=0o755)
    _directory(local)
    binary = local / "bin"
    if _kind(binary) == "missing":
        binary.mkdir(mode=0o755)
    _directory(binary)
    lock_path = root / "install.lock"
    if _kind(lock_path) not in {"missing", "regular"}:
        raise RuntimeFailure("installer lock is unsafe")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "r+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if diagnose(source)["status"] == "unsafe":
            raise RuntimeFailure("runtime state changed to unsafe")
        identity = source_identity(source)
        python_path = Path(sys.executable).resolve(strict=True)
        _regular_external(python_path)
        python_version = platform.python_version()
        base_name = f"{identity['source_sha256']}-py{sys.version_info.major}.{sys.version_info.minor}"
        generation = versions / base_name
        if _kind(generation) != "missing":
            try:
                _directory(generation, 0o700)
                _regular(generation / "runtime.json", 0o600)
                existing = validate_receipt(
                    json.loads((generation / "runtime.json").read_text())
                )
                verify_generation(generation, existing, execute=True)
                if (
                    existing["source_sha256"] != identity["source_sha256"]
                    or existing["plugin_version"] != identity["plugin_version"]
                ):
                    raise RuntimeFailure("generation identity differs")
            except (
                OSError,
                ValueError,
                TypeError,
                RuntimeFailure,
                subprocess.SubprocessError,
            ):
                generation = versions / f"{base_name}-r{uuid.uuid4().hex}"
        if _kind(generation) == "missing":
            temporary = Path(tempfile.mkdtemp(prefix=".generation.", dir=versions))
            os.chmod(temporary, 0o700)
            try:
                for name in PAYLOAD:
                    shutil.copyfile(source / name, temporary / name)
                    os.chmod(temporary / name, 0o600)
                dependencies = temporary / "dependencies"
                environment = {
                    "PATH": os.environ.get("PATH", ""),
                    "PIP_CONFIG_FILE": os.devnull,
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
                subprocess.run(
                    [
                        str(python_path),
                        "-I",
                        "-m",
                        "pip",
                        "install",
                        "--isolated",
                        "--index-url",
                        "https://pypi.org/simple",
                        "--no-cache-dir",
                        "--disable-pip-version-check",
                        "--no-deps",
                        "--no-compile",
                        "--require-hashes",
                        "--only-binary=:all:",
                        "--target",
                        str(dependencies),
                        "-r",
                        str(source / "requirements.txt"),
                    ],
                    check=True,
                    env=environment,
                )
                dependency_files: dict[str, str] = {}
                for path in dependencies.rglob("*"):
                    kind = _kind(path)
                    if kind == "directory":
                        continue
                    if kind != "regular":
                        raise RuntimeFailure("installed dependency path is unsafe")
                    dependency_files[path.relative_to(temporary).as_posix()] = sha256(
                        path
                    )
                receipt = {
                    "schema": RUNTIME_SCHEMA,
                    **identity,
                    "python_version": python_version,
                    "python_executable": str(python_path),
                    "python_executable_sha256": sha256(python_path),
                    "requirements_sha256": identity["files"]["requirements.txt"],
                    "dependency_files": dependency_files,
                }
                atomic_file(
                    temporary / "runtime.json",
                    (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode(),
                    0o600,
                )
                verify_generation(temporary, receipt, execute=True)
                os.replace(temporary, generation)
                directory = os.open(versions, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
        receipt = validate_receipt(
            json.loads((generation / "runtime.json").read_text())
        )
        verify_generation(generation, receipt, execute=True)
        current = root / "current"
        launcher = launcher_path()
        current_snapshot = _snapshot(current)
        launcher_snapshot = _snapshot(launcher)
        try:
            atomic_file(current, f"versions/{generation.name}\n".encode(), 0o600)
            atomic_file(launcher, launcher_bytes(generation, receipt), 0o755)
        except OSError:
            _restore(current, current_snapshot)
            _restore(launcher, launcher_snapshot)
            raise
    return diagnose(source)


def run_bundled(source: Path, arguments: list[str]) -> int:
    generation, receipt = _read_selected(runtime_root())
    verify_generation(generation, receipt, execute=True)
    bundled = source_identity(source)
    if (
        receipt["source_sha256"] != bundled["source_sha256"]
        or receipt["plugin_version"] != bundled["plugin_version"]
    ):
        raise RuntimeFailure("installed dependencies do not match the bundled source")
    with tempfile.TemporaryDirectory(prefix="aquarium-status-bundled-") as name:
        isolated_source = Path(name)
        for payload_name in PAYLOAD:
            target = isolated_source / payload_name
            shutil.copyfile(source / payload_name, target)
            os.chmod(target, 0o600)
            if sha256(target) != bundled["files"][payload_name]:
                raise RuntimeFailure("bundled source changed during isolation")
        program = (
            "import sys; sys.dont_write_bytecode=True; "
            "sys.path[:0]=[sys.argv[1],sys.argv[2]]; "
            "import aquarium_status; "
            "aquarium_status.VERSION_OVERRIDE=(sys.argv[3],'bundled_plugin_manifest'); "
            "raise SystemExit(aquarium_status.main(sys.argv[4:]))"
        )
        process = subprocess.run(
            [
                receipt["python_executable"],
                "-B",
                "-I",
                "-S",
                "-c",
                program,
                str(generation / "dependencies"),
                str(isolated_source),
                bundled["plugin_version"],
                *arguments,
            ],
            check=False,
        )
        return process.returncode


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser()
    commands = parser.add_subparsers(
        dest="command", required=True, parser_class=JsonArgumentParser
    )
    default_source = str(Path(__file__).resolve().parent)
    diagnose_parser = commands.add_parser("diagnose")
    diagnose_parser.add_argument("--source", default=default_source)
    install_parser = commands.add_parser("install")
    install_parser.add_argument("--source", default=default_source)
    install_parser.add_argument("--approve-install", action="store_true")
    install_parser.add_argument("--approve-launcher", action="store_true")
    run_parser = commands.add_parser("run-bundled")
    run_parser.add_argument("--source", default=default_source)
    run_parser.add_argument("arguments", nargs=argparse.REMAINDER)
    try:
        arguments = parser.parse_args(argv)
        source = Path(arguments.source).resolve(strict=True)
        if arguments.command == "run-bundled":
            return run_bundled(source, arguments.arguments)
        output = (
            diagnose(source)
            if arguments.command == "diagnose"
            else install(source, arguments.approve_install, arguments.approve_launcher)
        )
        print(json.dumps(output, sort_keys=True))
        return 0
    except Exception:  # noqa: BLE001 - keep the installer error boundary JSON-only
        payload = {
            "schema": ERROR_SCHEMA,
            "error": {
                "code": "runtime_install_failed",
                "message": "aquarium-status runtime operation failed safely",
                "action": "Inspect owned runtime paths and retry the approved operation.",
            },
        }
        print(json.dumps(payload, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
