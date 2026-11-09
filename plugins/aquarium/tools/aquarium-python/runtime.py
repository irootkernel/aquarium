#!/usr/bin/env python3
"""Manage the shared Aquarium Python environment without project dependencies."""

import argparse
import fcntl
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import uuid
import venv
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
SCHEMA = "aquarium-python-runtime/v1"


class RuntimeFailure(ValueError):
    """A runtime-owned failure with a public result status."""

    def __init__(self, message, status="missing-prerequisite"):
        super().__init__(message)
        self.status = status


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def root():
    return Path.home().resolve() / ".aquarium/python-runtime"


def safe(path, *, directory=False):
    if path.is_symlink() or not (path.is_dir() if directory else path.is_file()):
        raise RuntimeFailure(f"Unsafe or missing runtime path: {path}")
    return path


def identity(source):
    try:
        return digest(safe(source / "requirements.txt"))
    except (OSError, RuntimeFailure) as error:
        raise RuntimeFailure(str(error), "invalid-package") from error


def family(source):
    return root() / identity(source)


def managed_directory(path, *, create=False):
    home = Path.home().resolve()
    relative = path.relative_to(home)
    current = home
    for part in relative.parts:
        current /= part
        if create and not current.exists() and not current.is_symlink():
            current.mkdir(mode=0o700, exist_ok=True)
        safe(current, directory=True)
    return path


def library_files(environment):
    files = {}
    for path in (environment / "lib").rglob("*"):
        if path.is_symlink():
            raise RuntimeFailure(f"Linked runtime library: {path}")
        if path.is_file() and path.suffix != ".pyc":
            files[path.relative_to(environment).as_posix()] = digest(path)
    return files


def check(environment, source):
    managed_directory(environment)
    receipt = json.loads(safe(environment / "runtime.json").read_text())
    base = Path(receipt["base_python"])
    if receipt["requirements_sha256"] != identity(source):
        raise RuntimeFailure("Runtime requirements differ from this plugin")
    if not base.is_absolute() or digest(base) != receipt["base_sha256"]:
        raise RuntimeFailure("Base Python changed; repair the Aquarium environment")
    if library_files(environment) != receipt["library_files"]:
        raise RuntimeFailure(
            "Runtime libraries changed; repair the Aquarium environment"
        )
    interpreter = environment / "bin/python"
    if interpreter.resolve(strict=True) != base:
        raise RuntimeFailure("Runtime interpreter differs from its recorded base")
    probe = subprocess.run(
        [
            str(interpreter),
            "-B",
            "-I",
            "-c",
            (
                "import sys,yaml,jsonschema; from jsonschema import Draft202012Validator; "
                "assert sys.prefix != sys.base_prefix; assert sys.version_info >= (3,11)"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if probe.returncode:
        raise RuntimeFailure("Runtime dependency import failed")
    return interpreter


def selected(source):
    directory = managed_directory(family(source))
    name = safe(directory / "current").read_text().strip()
    if re.fullmatch(r"env-[0-9a-f]{32}", name) is None:
        raise RuntimeFailure("Invalid runtime selection")
    environment = directory / name
    return environment, check(environment, source)


def inspect(source=SOURCE):
    result = {
        "schema": SCHEMA,
        "component": "aquarium-python",
        "runtime_root": str(root()),
    }
    try:
        result["requirements_sha256"] = identity(source)
    except (OSError, ValueError) as error:
        return {**result, "status": "invalid-package", "reason": str(error)}
    try:
        environment, interpreter = selected(source)
        result.update(
            status="current", environment=str(environment), interpreter=str(interpreter)
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        result.update(
            status="missing-prerequisite",
            reason=str(error),
            continuation={
                "skill": "aquarium:dev-setup-global",
                "component": "aquarium-python",
            },
        )
    return result


def require_pinned_wheel_support():
    # PyYAML 6.0.3's five pinned wheels, verified against official PyPI metadata.
    # Update this coverage with requirements.txt when admitting new wheel hashes.
    # This describes this lock's artifacts, not a permanent Python version policy.
    version = tuple(sys.version_info[:2])
    free_threaded = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    supported = (
        platform.system() == "Darwin"
        and platform.machine() == "arm64"
        and sys.implementation.name == "cpython"
        and version in {(3, 11), (3, 12), (3, 13), (3, 14)}
        and (not free_threaded or version == (3, 14))
    )
    if not supported:
        raise RuntimeFailure(
            "This lock has wheels for Apple Silicon macOS CPython 3.11–3.14 "
            "(including 3.14t). Select an installed matching host interpreter; "
            f"found {sys.executable} ({sys.version.split()[0]}, "
            f"{sys.implementation.name}, {platform.system()} {platform.machine()}, "
            f"free_threaded={free_threaded}).",
            "unsupported-runtime",
        )


def install(source=SOURCE, *, approved=False):
    if not approved:
        raise RuntimeFailure(
            "Installation requires --approve-install", "approval-required"
        )
    if sys.version_info < (3, 11):
        raise RuntimeFailure(
            f"Aquarium requires Python 3.11 or newer; found {sys.executable} ({sys.version.split()[0]})",
            "unsupported-runtime",
        )
    state = inspect(source)
    if state["status"] == "current":
        return state
    if state["status"] == "invalid-package":
        raise RuntimeFailure(state["reason"], "invalid-package")
    require_pinned_wheel_support()
    directory = managed_directory(family(source), create=True)
    descriptor = os.open(
        directory / "install.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = inspect(source)
        if state["status"] == "current":
            return state
        selector = directory / "current"
        if selector.exists() or selector.is_symlink():
            safe(selector)
        environment = directory / f"env-{uuid.uuid4().hex}"
        try:
            # Venv entrypoints embed absolute paths: build at the final location.
            venv.EnvBuilder(with_pip=True, symlinks=True).create(environment)
            interpreter = environment / "bin/python"
            installer_env = dict(
                os.environ,
                PIP_CONFIG_FILE=os.devnull,
                PYTHONNOUSERSITE="1",
                PYTHONDONTWRITEBYTECODE="1",
            )
            subprocess.run(
                [
                    str(interpreter),
                    "-I",
                    "-m",
                    "pip",
                    "install",
                    "--isolated",
                    "--index-url",
                    "https://pypi.org/simple",
                    "--no-cache-dir",
                    "--disable-pip-version-check",
                    "--only-binary=:all:",
                    "--require-hashes",
                    "--no-deps",
                    "--no-compile",
                    "-r",
                    str(source / "requirements.txt"),
                ],
                check=True,
                stdout=sys.stderr,
                env=installer_env,
            )
            subprocess.run(
                [str(interpreter), "-I", "-m", "pip", "check", "--isolated"],
                check=True,
                stdout=sys.stderr,
                env=installer_env,
            )
            base = interpreter.resolve(strict=True)
            receipt = {
                "requirements_sha256": identity(source),
                "base_python": str(base),
                "base_sha256": digest(base),
                "library_files": library_files(environment),
            }
            (environment / "runtime.json").write_text(
                json.dumps(receipt, sort_keys=True)
            )
            check(environment, source)
            temporary = directory / f".current-{uuid.uuid4().hex}"
            try:
                temporary.write_text(environment.name + "\n")
                os.replace(temporary, selector)
            finally:
                temporary.unlink(missing_ok=True)
        except BaseException:
            if environment.exists():
                shutil.rmtree(environment)
            raise
    return inspect(source)


def run(script, arguments, source=SOURCE):
    plugin = source.parents[1]
    target = plugin / script
    if Path(script).is_absolute() or ".." in Path(script).parts:
        raise RuntimeFailure(
            "Helper must be relative to the installed plugin", "invalid-arguments"
        )
    current = plugin
    for part in Path(script).parts:
        current /= part
        if current.is_symlink():
            raise RuntimeFailure(
                "Linked helper paths are unsupported", "invalid-arguments"
            )
    try:
        safe(target)
    except (OSError, RuntimeFailure) as error:
        raise RuntimeFailure(str(error), "invalid-arguments") from error
    if target.suffix != ".py":
        raise RuntimeFailure("Helper must be a Python script", "invalid-arguments")
    _, interpreter = selected(source)
    # -I excludes project and user packages; restore only the helper's imports.
    program = (
        "import runpy,sys; p=sys.argv[1]; sys.argv=sys.argv[1:]; "
        "sys.path.insert(0,__import__('os').path.dirname(p)); "
        "runpy.run_path(p,run_name='__main__')"
    )
    os.execv(
        str(interpreter),
        [str(interpreter), "-B", "-I", "-c", program, str(target), *arguments],
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("inspect")
    installer = commands.add_parser("install")
    installer.add_argument("--approve-install", action="store_true")
    runner = commands.add_parser("run")
    runner.add_argument("script")
    runner.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.action == "run":
            run(args.script, args.arguments)
        result = (
            install(approved=args.approve_install)
            if args.action == "install"
            else inspect()
        )
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "current" else 2
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        status = (
            error.status
            if isinstance(error, RuntimeFailure)
            else "install-failed"
            if args.action == "install"
            else "missing-prerequisite"
        )
        if args.action == "install" and status == "missing-prerequisite":
            status = "install-failed"
        # Runtime-owned results use stdout; helper streams are untouched after exec.
        result = {
            "schema": SCHEMA,
            "status": status,
            "component": "aquarium-python",
            "reason": str(error),
        }
        if status == "missing-prerequisite":
            result["continuation"] = {
                "skill": "aquarium:dev-setup-global",
                "component": "aquarium-python",
            }
        print(json.dumps(result, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
