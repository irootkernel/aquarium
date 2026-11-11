#!/usr/bin/env python3
"""Offline guest-python wrapper for the simulation: venv/pip are recorded,
everything else runs the real interpreter."""

import json
import os
import shlex
import sys
from pathlib import Path


def require_absolute_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value or not os.path.isabs(value):
        raise SystemExit(f"{name} must be a non-empty absolute path")
    return value


arguments = sys.argv[1:]
log = os.environ.get("FAKE_PYTHON_LOG")


def note(entry):
    if log:
        with open(log, "a") as stream:
            stream.write(json.dumps(entry) + "\n")


if len(arguments) >= 2 and arguments[:2] == ["-m", "venv"]:
    destination = Path(arguments[2])
    bin_dir = destination / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / "python"
    target.write_text(
        "#!/bin/sh\nexec "
        + shlex.join(
            [
                require_absolute_env("FAKE_PYTHON_REAL"),
                require_absolute_env("FAKE_PYTHON_BINDING"),
            ]
        )
        + ' "$@"\n'
    )
    target.chmod(0o755)
    note({"venv": str(destination)})
    raise SystemExit(0)

if len(arguments) >= 2 and arguments[:2] == ["-m", "pip"]:
    note({"pip": arguments})
    lock = Path(arguments[arguments.index("-r") + 1])
    lines = [
        line.strip()
        for line in lock.read_text().splitlines()
        if line.strip() and "--hash=sha256:" in line
    ]
    if not lines or not all(line.split(" ")[0].count("==") == 1 for line in lines):
        print("invalid hash-locked requirements", file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(0)

os.execv(
    require_absolute_env("FAKE_PYTHON_REAL"),
    [os.environ["FAKE_PYTHON_REAL"], *arguments],
)
