"""Check the selected test environment against declared minimum versions."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    from packaging.version import InvalidVersion, Version
except ImportError:
    print("packaging is unavailable; prepare the test environment", file=sys.stderr)
    raise SystemExit(2)


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def read_minimums(path: Path) -> dict[str, Version]:
    minimums = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.split("#", 1)[0].strip()
        if not value:
            continue
        match = re.fullmatch(r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*>=\s*(\S+)", value)
        if match is None:
            raise ValueError(f"expected a minimum requirement: {value}")
        name, version = match.groups()
        key = normalize_name(name)
        if key in minimums:
            raise ValueError(f"duplicate requirement: {name}")
        minimums[key] = Version(version)
    return minimums


def dependency_errors(
    minimums: dict[str, Version], installed: dict[str, str]
) -> list[str]:
    errors = []
    for name, minimum in minimums.items():
        # Ruff may be a standalone executable, independent of Python metadata.
        if name == "ruff":
            continue
        observed = installed.get(name)
        if observed is None:
            errors.append(f"missing distribution: {name}")
        elif Version(observed) < minimum:
            errors.append(f"{name} {observed} is below minimum {minimum}")
    return errors


def ruff_error(output: str, returncode: int, minimum: Version) -> str | None:
    match = re.fullmatch(r"ruff\s+(\S+)", output.strip())
    if returncode != 0 or match is None:
        return f"Ruff version could not be read: {output.strip()}"
    observed = Version(match.group(1))
    if observed < minimum:
        return f"Ruff {observed} is below minimum {minimum}"
    return None


def main() -> int:
    try:
        minimums = read_minimums(Path("requirements.txt"))
        installed = {}
        for name in minimums:
            if name == "ruff":
                continue
            try:
                installed[name] = version(name)
            except PackageNotFoundError:
                pass
        errors = dependency_errors(minimums, installed)
        if sys.version_info < (3, 11):
            errors.append("Python 3.11 or newer is required")
        for module in ("pytest", "yaml", "mcp"):
            if importlib.util.find_spec(module) is None:
                errors.append(f"missing module: {module}")
        ruff = subprocess.run(
            [sys.argv[1], "--version"], capture_output=True, text=True, check=False
        )
        failure = ruff_error(
            ruff.stdout or ruff.stderr, ruff.returncode, minimums["ruff"]
        )
        if failure:
            errors.append(failure)
    except (OSError, ValueError, InvalidVersion) as error:
        errors = [str(error)]
    if errors:
        print("; ".join(errors), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
