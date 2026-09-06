"""Read-only Ouroboros package and per-Codex-home inspection."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import stat
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PYPI_URL = "https://pypi.org/pypi/ouroboros-ai/json"
SUPPORTED_RANGE = ">=0.51.1,<0.54.0"

# Use the selected CLI's native asset resolver, not an Aquarium-owned skill list.
ASSET_PROBE = """
import hashlib, json
from importlib.metadata import version
from ouroboros.codex.artifacts import resolve_packaged_codex_assets, load_packaged_codex_rules
result = {"version": version("ouroboros-ai"), "artifacts": {}}
with resolve_packaged_codex_assets() as assets:
    for artifact in assets.managed_artifacts:
        source = artifact.source_path
        if source.is_symlink():
            raise ValueError("symlinked package asset")
        target = artifact.relative_install_path.as_posix()
        files = sorted(source.rglob("*")) if source.is_dir() else [source]
        for path in files:
            if path.is_symlink():
                raise ValueError("symlinked package asset")
            if path.is_file():
                relative = target + "/" + path.relative_to(source).as_posix() if source.is_dir() else target
                contents = load_packaged_codex_rules().encode("utf-8") if path == assets.rules_path else path.read_bytes()
                result["artifacts"][relative] = hashlib.sha256(contents).hexdigest()
print(json.dumps(result))
"""


class InvalidCodexHome(ValueError):
    """An explicitly supplied home cannot be used as an installation target."""


def directory_entries(root: Path) -> list[Path]:
    with os.scandir(root) as entries:
        return sorted(Path(entry.path) for entry in entries)


def artifact_targets(root: Path, kind: str) -> list[Path]:
    try:
        entries = directory_entries(root)
    except FileNotFoundError:
        return []
    prefix = "ouroboros-" if kind == "skills" else "ouroboros"
    return [path for path in entries if path.name.startswith(prefix)]


def artifact_paths(target: Path):
    yield target
    if stat.S_ISDIR(target.lstat().st_mode):
        for child in directory_entries(target):
            yield from artifact_paths(child)


def discover_homes(
    explicit: tuple[str, ...] = (),
) -> tuple[Path, list[Path], dict[Path, str]]:
    requested = []
    for value in explicit:
        if not value.strip():
            raise InvalidCodexHome("Codex home must not be blank")
        try:
            path = Path(value).expanduser().resolve()
            not_directory = path.exists() and not path.is_dir()
        except (OSError, ValueError, RuntimeError) as error:
            raise InvalidCodexHome("Codex home is unavailable or invalid") from error
        if not_directory:
            raise InvalidCodexHome("Codex home must be a directory")
        requested.append(path)

    failures: dict[Path, str] = {}
    homes: list[Path] = []
    identities: dict[tuple[int, int], Path] = {}

    def include(path: Path) -> Path:
        try:
            path = path.expanduser().resolve()
        except (OSError, ValueError, RuntimeError):
            # Keep the original spelling for diagnosis; never probe an unresolved home.
            failures[path] = "home_resolution_failed"
        if path not in failures:
            try:
                info = path.stat()
                if stat.S_ISDIR(info.st_mode):
                    identity = (info.st_dev, info.st_ino)
                    if identity in identities:
                        return identities[identity]
                    identities[identity] = path
            except FileNotFoundError:
                pass
            except OSError:
                failures[path] = "home_inspection_failed"
        if path not in homes:
            homes.append(path)
        return path

    current = include(Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex"))
    default = Path.home() / ".codex"
    try:
        if default.is_dir():
            include(default)
    except OSError:
        failures[include(default)] = "home_inspection_failed"
    try:
        candidates = [
            path
            for path in directory_entries(Path.home())
            if path.name.startswith(".codex-")
        ]
    except OSError:
        candidates = []
    for path in candidates:
        try:
            if not path.is_dir():
                continue
            try:
                has_config = stat.S_ISREG((path / "config.toml").stat().st_mode)
            except FileNotFoundError:
                has_config = False
            if (
                has_config
                or artifact_targets(path / "rules", "rules")
                or artifact_targets(path / "skills", "skills")
            ):
                include(path)
        except OSError:
            failures[include(path)] = "home_inspection_failed"
    for path in requested:
        include(path)
    return current, homes, failures


def release_freshness(
    inspector: Any, cli: dict[str, Any], timeout: float
) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "freshness_unverifiable", "source": PYPI_URL}
    try:
        with urllib.request.urlopen(PYPI_URL, timeout=timeout) as response:
            if response.geturl() != PYPI_URL:
                raise ValueError("unexpected metadata source")
            payload = response.read(8 * 1024 * 1024 + 1)
        if len(payload) > 8 * 1024 * 1024:
            raise ValueError("metadata too large")
        metadata = json.loads(payload)
        if metadata["info"]["name"] != "ouroboros-ai":
            raise ValueError("unexpected package")
        releases = [
            version
            for version, files in metadata["releases"].items()
            if re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version)
            and any(file.get("yanked") is False for file in files)
        ]
        key = lambda version: tuple(map(int, version.split(".")))
        latest = max(releases, key=key)
        supported = max(
            filter(inspector.supported_ouroboros_version, releases), key=key
        )
        result.update(
            latest_stable=latest,
            latest_supported=supported,
            compatibility_review_required=not inspector.supported_ouroboros_version(
                latest
            ),
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
        installed = cli["version"]
        if not cli["installed"]:
            result["status"] = "missing"
        elif not cli["probes"]["version"]["ok"] or installed is None:
            result["reason"] = "cli_version_unverifiable"
        elif not inspector.supported_ouroboros_version(installed):
            result["status"] = "incompatible"
        elif key(installed) < key(supported):
            result["status"] = "update_available"
        else:
            result["status"] = "current" if installed in releases else "different"
    except (
        OSError,
        http.client.HTTPException,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ):
        result["reason"] = "release_metadata_unverifiable"
    return result


def packaged_assets(
    inspector: Any, cli: dict[str, Any], cwd: Path, timeout: float
) -> dict[str, str] | None:
    if not cli.get("installed") or not cli.get("version_supported"):
        return None
    # uv tool installations keep the package interpreter beside the CLI entrypoint.
    interpreter = Path(cli["executable"]).parent / "python"
    if not interpreter.is_file():
        return None
    probe = inspector.json_probe(
        [str(interpreter), "-I", "-c", ASSET_PROBE], cwd, timeout
    )
    result = probe.get("result")
    if (
        not probe["ok"]
        or not isinstance(result, dict)
        or result.get("version") != cli["version"]
    ):
        return None
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        return None
    for relative, digest in artifacts.items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            return None
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or len(path.parts) < 2:
            return None
        if path.parts[0] not in {"rules", "skills"} or not path.parts[1].startswith(
            "ouroboros"
        ):
            return None
        if re.fullmatch(r"[a-f0-9]{64}", digest) is None:
            return None
    if not all(
        any(name.startswith(kind + "/") for name in artifacts)
        for kind in ("rules", "skills")
    ):
        return None
    return artifacts


def inspect_artifacts(
    home: Path, kind: str, expected: dict[str, str] | None
) -> dict[str, Any]:
    try:
        root = home / kind
        if home.exists() and not home.is_dir():
            return {"status": "unverifiable", "reason": "home_not_a_directory"}
        if any(path.is_symlink() for path in (root, *root.parents)):
            return {"status": "unsafe", "reason": "artifact_root_symlinked"}
        if expected is None:
            return {"status": "unverifiable", "reason": "package_assets_unverifiable"}
        wanted = {
            name: digest
            for name, digest in expected.items()
            if name.startswith(kind + "/")
        }
        observed: dict[str, str] = {}
        extra_directories: list[str] = []
        for target in artifact_targets(root, kind):
            if target.is_symlink():
                return {"status": "unsafe", "reason": "artifact_symlinked"}
            if stat.S_ISDIR(target.lstat().st_mode) and not any(
                name.startswith(target.relative_to(home).as_posix() + "/")
                for name in wanted
            ):
                extra_directories.append(target.relative_to(home).as_posix())
            for path in artifact_paths(target):
                if path.is_symlink():
                    return {"status": "unsafe", "reason": "artifact_symlinked"}
                if stat.S_ISREG(path.lstat().st_mode):
                    observed[path.relative_to(home).as_posix()] = hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest()
        missing = sorted(wanted.keys() - observed.keys())
        extra = sorted((observed.keys() - wanted.keys()) | set(extra_directories))
        different = sorted(
            name
            for name in wanted.keys() & observed.keys()
            if wanted[name] != observed[name]
        )
        return {
            "status": "missing"
            if not observed
            else "different"
            if missing or extra or different
            else "configured",
            "missing": missing,
            "extra": extra,
            "different": different,
        }
    except OSError:
        return {"status": "unverifiable", "reason": "artifact_read_failed"}


def legacy_skills(expected: dict[str, str] | None) -> list[str]:
    root = Path.home() / ".agents" / "skills"
    candidates = set(root.glob("ouroboros-*"))
    if expected:
        # Recognize unprefixed legacy copies only by exact upstream bytes.
        for relative, digest in expected.items():
            parts = Path(relative).parts
            if len(parts) == 3 and parts[0] == "skills" and parts[2] == "SKILL.md":
                candidate = root / parts[1].removeprefix("ouroboros-")
                try:
                    if (
                        hashlib.sha256(
                            (candidate / "SKILL.md").read_bytes()
                        ).hexdigest()
                        == digest
                    ):
                        candidates.add(candidate)
                except OSError:
                    pass
    return sorted(str(path) for path in candidates)


def unavailable_home(home: Path, current: Path, reason: str) -> dict[str, Any]:
    row = {
        key: {"status": "unverifiable", "reason": reason}
        for key in (
            "rules",
            "skills",
            "codex_integration",
            "mcp_registration",
            "mcp_runtime",
            "home_binding",
            "runtime_package",
        )
    }
    row.update(
        home=str(home), current=home == current, status="degraded", reason=reason
    )
    row["live_runtime"] = {"status": "not_observed", "reason": "configuration_only"}
    return row


def inspect_home(
    inspector: Any,
    cwd: Path,
    timeout: float,
    home: Path,
    current: Path,
    cli: dict[str, Any],
    assets: dict[str, str] | None,
) -> dict[str, Any]:
    raw = inspector.inspect_ouroboros(
        cwd, timeout, codex_home=home, cli_observation=cli
    )
    row = {
        key: raw[key]
        for key in (
            "codex_integration",
            "mcp_registration",
            "mcp_runtime",
            "home_binding",
            "runtime_package",
        )
    }
    row.update(home=str(home), current=home == current)
    if home.exists() and not home.is_dir():
        row["reason"] = "home_not_a_directory"
    row["rules"] = inspect_artifacts(home, "rules", assets)
    row["skills"] = inspect_artifacts(home, "skills", assets)
    row["live_runtime"] = {"status": "not_observed", "reason": "configuration_only"}
    row["status"] = (
        "configured"
        if (
            raw["version_supported"]
            and all(
                row[key]["status"] == "configured"
                for key in (
                    "rules",
                    "skills",
                    "codex_integration",
                    "mcp_registration",
                    "mcp_runtime",
                    "home_binding",
                )
            )
            and row["runtime_package"]["status"] in {"pinned", "selected_cli"}
        )
        else "degraded"
    )
    return row


def inspect_ouroboros(
    inspector: Any,
    cwd: Path,
    timeout: float,
    explicit_homes: tuple[str, ...] = (),
    verify_release: bool = False,
) -> dict[str, Any]:
    current, homes, failures = discover_homes(explicit_homes)
    rows = []
    cli = inspector.inspect_ouroboros_cli(cwd, timeout)
    assets = packaged_assets(inspector, cli, cwd, timeout)
    for home in homes:
        if home in failures:
            row = unavailable_home(home, current, failures[home])
        else:
            try:
                row = inspect_home(inspector, cwd, timeout, home, current, cli, assets)
            except (OSError, ValueError, RuntimeError):
                row = unavailable_home(home, current, "home_inspection_failed")
        rows.append(row)
    freshness = (
        release_freshness(inspector, cli, timeout)
        if verify_release
        else {"status": "not_checked", "source": PYPI_URL}
    )
    return {
        "status": rows[0]["status"],
        "supported_range": SUPPORTED_RANGE,
        "cli": {
            **{
                key: cli[key]
                for key in ("installed", "executable", "version", "version_supported")
            },
            "status": "missing"
            if not cli["installed"]
            else "installed"
            if cli["version_supported"]
            else "degraded",
            "version_probe": cli["probes"]["version"],
        },
        "freshness": freshness,
        "current_home": str(current),
        "current_home_readiness": rows[0]["status"],
        "all_discovered_homes_readiness": "configured"
        if all(row["status"] == "configured" for row in rows)
        else "degraded",
        "homes": rows,
        "legacy_shared_skills": legacy_skills(assets),
    }
