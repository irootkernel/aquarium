#!/usr/bin/env python3
"""Inspect local Aquarium development-tool state without mutating it."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "aquarium-dev-setup-inspection.v9"
MULGAE_COMMAND_RESULT_SCHEMA = "mulgae-command-result.v5"
MULGAE_DOCTOR_RESULT_SCHEMA = "mulgae-doctor-result.v2"
MULGAE_MCP_TOOL_TIMEOUT_SEC = 7501
GAORI_MCP_TOOL_TIMEOUT_SEC = 3601
MAX_COMMAND_TIMEOUT_SECONDS = 86_400.0
CONFLICT_STATUSES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}
CANONICAL_NUMERIC_COMPONENT = r"(?:0|[1-9][0-9]*)"
CANONICAL_SEMVER = re.compile(
    rf"v?{CANONICAL_NUMERIC_COMPONENT}\."
    rf"{CANONICAL_NUMERIC_COMPONENT}\."
    rf"{CANONICAL_NUMERIC_COMPONENT}(?:[-+][0-9A-Za-z.-]+)?"
)
SANHO_SKILL_FILES = (
    "SKILL.md",
    "references/lifecycle.md",
    "references/authoring.md",
    "references/recovery.md",
)
GAORI_SKILL_FILES = (
    "SKILL.md",
    "references/lifecycle.md",
    "references/authoring.md",
    "references/recovery.md",
)
MULGAE_SKILL_FILES = (
    "SKILL.md",
    "references/lifecycle.md",
    "references/authoring.md",
    "references/recovery.md",
)
PODWAY_SKILL_FILES = (
    "SKILL.md",
    "references/lifecycle.md",
    "references/goal.md",
    "references/recovery.md",
)
PODWAY_PROCEDURES = (
    "aquarium-task-v2.yaml",
    "aquarium-goal-v2.yaml",
    "aquarium-validation-v2.yaml",
    "aquarium-design-v2.yaml",
    "aquarium-war-room-v2.yaml",
)
LEGACY_PODWAY_PROCEDURES = (
    "root-kernel-task-v2.yaml",
    "root-kernel-goal-v2.yaml",
    "root-kernel-validation-v2.yaml",
)
PODWAY_SOURCE_DIRECTORY = (
    Path(__file__).resolve().parents[3] / "assets" / "podway" / "procedures"
)
OUROBOROS_UVX_MCP_ARGS = (
    "--isolated",
    "--python",
    ">=3.12",
    "--from",
    "ouroboros-ai[mcp]",
    "ouroboros",
    "mcp",
    "serve",
)
OUROBOROS_CODEX_MCP_SUFFIX = (
    "--runtime",
    "codex",
    "--llm-backend",
    "codex",
)
OUROBOROS_CODEX_MCP_ENV = {
    "OUROBOROS_AGENT_RUNTIME": "codex",
    "OUROBOROS_LLM_BACKEND": "codex",
}
OUROBOROS_RUNTIME_SELECTOR_KEYS = {
    *OUROBOROS_CODEX_MCP_ENV,
    "OUROBOROS_RUNTIME",
}
OUROBOROS_MCP_PACKAGE = re.compile(
    rf"ouroboros-ai\[mcp\](?:==(0\.51\.{CANONICAL_NUMERIC_COMPONENT}))?"
)


class InspectionError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InspectionError("invalid_arguments", "invalid command-line arguments")


def strict_json_loads(content: str) -> Any:
    def object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise ValueError("invalid JSON constant")

    def finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("non-finite JSON number")
        return parsed

    return json.loads(
        content,
        object_pairs_hook=object_from_pairs,
        parse_constant=reject_constant,
        parse_float=finite_float,
    )


def finite_number(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def run_command(
    arguments: list[str],
    cwd: Path,
    timeout_seconds: float,
    environment_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_"):
            del environment[name]
    environment["LANG"] = "C"
    environment["LC_ALL"] = "C"
    if environment_overrides:
        environment.update(environment_overrides)
    try:
        completed = subprocess.run(
            arguments,
            cwd=cwd,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {
            "attempted": True,
            "ok": False,
            "exit_code": None,
            "timed_out": True,
            "stdout": "",
            "stderr": "",
        }
    except OSError as error:
        return {
            "attempted": True,
            "ok": False,
            "exit_code": None,
            "timed_out": False,
            "stdout": "",
            "stderr": "",
            "error_code": "execution_failed",
            "error_type": type(error).__name__,
        }
    return {
        "attempted": True,
        "ok": completed.returncode == 0,
        "exit_code": completed.returncode,
        "timed_out": False,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def skipped_probe(reason: str) -> dict[str, Any]:
    return {
        "attempted": False,
        "ok": False,
        "exit_code": None,
        "timed_out": False,
        "reason": reason,
    }


def parse_json_probe(raw_probe: dict[str, Any]) -> dict[str, Any]:
    probe = {
        key: raw_probe[key] for key in ("attempted", "ok", "exit_code", "timed_out")
    }
    if raw_probe.get("error_code"):
        probe["error_code"] = raw_probe["error_code"]
        return probe
    if not raw_probe["attempted"] or raw_probe["timed_out"]:
        return probe
    try:
        probe["result"] = strict_json_loads(raw_probe["stdout"])
    except (json.JSONDecodeError, ValueError):
        probe["ok"] = False
        probe["error_code"] = "invalid_json"
    return probe


def json_probe(
    arguments: list[str],
    repository: Path,
    timeout_seconds: float,
    environment_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    if environment_overrides is None:
        return parse_json_probe(run_command(arguments, repository, timeout_seconds))
    return parse_json_probe(
        run_command(
            arguments,
            repository,
            timeout_seconds,
            environment_overrides,
        )
    )


def named_mcp_server_missing(raw_probe: dict[str, Any], name: str) -> bool:
    return bool(
        raw_probe["exit_code"] == 1
        and not raw_probe["timed_out"]
        and not raw_probe.get("stdout", "").strip()
        and re.fullmatch(
            rf"\s*Error: No MCP server named (?P<quote>['\"]?){re.escape(name)}(?P=quote) found\.\s*",
            raw_probe.get("stderr", ""),
        )
    )


def version_from_probe(probe: dict[str, Any]) -> str | None:
    result = probe.get("result")
    version = result.get("version") if isinstance(result, dict) else None
    if isinstance(version, str) and CANONICAL_SEMVER.fullmatch(version):
        return version
    return None


def normalized_version(version: str | None) -> str | None:
    if not version:
        return None
    return version.removeprefix("v")


def codex_version_from_output(output: str) -> str | None:
    match = re.search(
        r"\bcodex(?:-cli)?\s+v?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)\b", output
    )
    return match.group(1) if match else None


def supported_podway_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.2\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 6)


def podway_v025_workaround_bytes(name: str, source: bytes) -> bytes | None:
    if name == "aquarium-goal-v2.yaml":
        declaration = b"        max_total_length: 1000000\n"
        if source.count(declaration) != 1:
            return None
        return source.replace(declaration, b"", 1)
    if name in {"aquarium-task-v2.yaml", "aquarium-validation-v2.yaml"}:
        declaration = (
            b"        max_item_length: 1200\n        max_total_length: 1000000\n"
        )
        if source.count(declaration) != 1:
            return None
        return source.replace(declaration, b"        max_item_length: 1000\n", 1)
    return None


def supported_sanho_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.2\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 7)


def supported_gaori_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.1\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 14)


def supported_mulgae_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.1\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 18)


def supported_mulgae_go_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(
        rf"go({CANONICAL_NUMERIC_COMPONENT})\."
        rf"({CANONICAL_NUMERIC_COMPONENT})\."
        rf"({CANONICAL_NUMERIC_COMPONENT})",
        version,
    )
    return bool(match and tuple(map(int, match.groups())) >= (1, 26, 6))


def supported_ouroboros_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.51\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 1)


def ouroboros_version_from_output(output: str) -> str | None:
    plain = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)
    match = re.search(
        r"\bOuroboros\b.*?\bversion\s+v?(\d+\.\d+\.\d+)\b",
        plain,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else None


def file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def file_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def git_output(repository: Path, timeout_seconds: float, *arguments: str) -> str | None:
    probe = run_command(["git", *arguments], repository, timeout_seconds)
    if not probe["ok"]:
        return None
    return probe["stdout"].strip()


def resolve_repository(requested_path: str, timeout_seconds: float) -> Path:
    candidate = Path(requested_path).expanduser().resolve()
    if not candidate.is_dir():
        raise InspectionError(
            "invalid_repository_path", "repository path must be an existing directory"
        )
    root = git_output(candidate, timeout_seconds, "rev-parse", "--show-toplevel")
    if not root:
        raise InspectionError(
            "not_a_git_repository", "repository path is not inside a Git worktree"
        )
    return Path(root).resolve()


def worktree_counts(repository: Path, timeout_seconds: float) -> dict[str, int]:
    probe = run_command(
        ["git", "status", "--porcelain=v1", "-z"], repository, timeout_seconds
    )
    if not probe["ok"]:
        raise InspectionError("git_status_failed", "unable to inspect Git worktree", 1)
    entries = probe["stdout"].split("\0")
    counts = {"staged": 0, "unstaged": 0, "untracked": 0, "conflicted": 0}
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        status = entry[:2]
        if status == "??":
            counts["untracked"] += 1
            continue
        if status in CONFLICT_STATUSES:
            counts["conflicted"] += 1
        else:
            if status[0] != " ":
                counts["staged"] += 1
            if status[1] != " ":
                counts["unstaged"] += 1
        if "R" in status or "C" in status:
            index += 1
    return counts


def repository_inventory(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    branch = git_output(
        repository, timeout_seconds, "symbolic-ref", "--quiet", "--short", "HEAD"
    )
    if branch is None:
        branch = git_output(repository, timeout_seconds, "rev-parse", "--short", "HEAD")
    upstream = git_output(
        repository,
        timeout_seconds,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    )
    return {
        "root": str(repository),
        "branch": branch,
        "upstream": upstream,
        "worktree": worktree_counts(repository, timeout_seconds),
    }


def ignored_by_git(
    repository: Path, relative_path: str, timeout_seconds: float
) -> bool:
    probe = run_command(
        ["git", "check-ignore", "--quiet", "--", relative_path],
        repository,
        timeout_seconds,
    )
    return probe["exit_code"] == 0


def tracked_by_git(
    repository: Path, relative_path: str, timeout_seconds: float
) -> bool:
    probe = run_command(
        ["git", "ls-files", "--error-unmatch", "--", relative_path],
        repository,
        timeout_seconds,
    )
    return probe["exit_code"] == 0


def configuration_entry(
    repository: Path,
    relative_path: str,
    timeout_seconds: float,
    ignore_probe_path: str | None = None,
) -> dict[str, Any]:
    path = repository.joinpath(relative_path)
    present, symlinked = safe_managed_file_state(path, repository)
    if relative_path.endswith("/") and not symlinked:
        present = path.is_dir()
    return {
        "path": relative_path,
        "present": present,
        "symlinked": symlinked,
        "ignored": ignored_by_git(
            repository, ignore_probe_path or relative_path, timeout_seconds
        ),
    }


def base_tool(
    name: str, catalog_status: str = "active", setup_supported: bool = True
) -> dict[str, Any]:
    executable = shutil.which(name)
    return {
        "catalog_status": catalog_status,
        "setup_supported": setup_supported,
        "installed": executable is not None,
        "executable": str(Path(executable).resolve()) if executable else None,
        "version": None,
        "status": "installed" if executable else "missing",
        "configuration": [],
        "probes": {},
    }


def normalized_probe(probe: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        key: probe[key] for key in ("attempted", "ok", "exit_code", "timed_out")
    }
    if probe.get("error_code"):
        normalized["error_code"] = probe["error_code"]
    if probe.get("reason"):
        normalized["reason"] = probe["reason"]
    return normalized


def resolved_executable(command: Any) -> Path | None:
    if not isinstance(command, str) or not command:
        return None
    candidate = Path(command).expanduser()
    if candidate.is_absolute():
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
        return None
    discovered = shutil.which(command)
    return Path(discovered).resolve() if discovered else None


def ouroboros_direct_launcher_matches(
    transport: Any, ouroboros_executable: str | None
) -> bool:
    if not isinstance(transport, dict) or not ouroboros_executable:
        return False
    resolved_command = resolved_executable(transport.get("command"))
    return bool(
        transport.get("type") == "stdio"
        and transport.get("args") == ["mcp", "serve"]
        and resolved_command
        and resolved_command == Path(ouroboros_executable).resolve()
    )


def ouroboros_isolated_launcher_matches(transport: Any) -> bool:
    if not isinstance(transport, dict) or transport.get("type") != "stdio":
        return False
    resolved_command = resolved_executable(transport.get("command"))
    selected_uvx = shutil.which("uvx")
    if not resolved_command or not selected_uvx:
        return False
    if resolved_command != Path(selected_uvx).resolve():
        return False

    args = transport.get("args")
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        return False
    normalized_args = list(args)
    if len(normalized_args) < 5:
        return False
    package_match = OUROBOROS_MCP_PACKAGE.fullmatch(normalized_args[4])
    if not package_match:
        return False
    pinned_version = package_match.group(1)
    if pinned_version and not supported_ouroboros_version(pinned_version):
        return False
    normalized_args[4] = "ouroboros-ai[mcp]"

    env = transport.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in env.items()
    ):
        return False
    if "_OUROBOROS_NESTED" in env:
        return False
    if set(env) - OUROBOROS_RUNTIME_SELECTOR_KEYS:
        return False
    if any(
        env.get(key) not in {None, "codex"} for key in OUROBOROS_RUNTIME_SELECTOR_KEYS
    ):
        return False

    normalized = tuple(normalized_args)
    if normalized == OUROBOROS_UVX_MCP_ARGS:
        return all(
            env.get(key) == value for key, value in OUROBOROS_CODEX_MCP_ENV.items()
        )
    return normalized == (*OUROBOROS_UVX_MCP_ARGS, *OUROBOROS_CODEX_MCP_SUFFIX)


def classify_ouroboros_registration(
    raw_probe: dict[str, Any], ouroboros_executable: str | None
) -> dict[str, Any]:
    probe = {
        key: raw_probe[key] for key in ("attempted", "ok", "exit_code", "timed_out")
    }
    if raw_probe["timed_out"]:
        probe["reason"] = "registration_probe_timed_out"
        return {"status": "degraded", "probe": probe}
    if raw_probe.get("error_code"):
        probe["error_code"] = raw_probe["error_code"]
        probe["reason"] = "registration_probe_failed"
        return {"status": "degraded", "probe": probe}

    if not raw_probe["ok"]:
        not_found = named_mcp_server_missing(raw_probe, "ouroboros")
        probe["reason"] = (
            "registration_not_found" if not_found else "registration_probe_failed"
        )
        return {
            "status": "missing" if not_found else "degraded",
            "probe": probe,
        }

    parsed = parse_json_probe(raw_probe)
    if parsed.get("error_code") == "invalid_json":
        probe["error_code"] = "invalid_json"
        probe["reason"] = "registration_invalid_json"
        return {"status": "degraded", "probe": probe}
    result = parsed.get("result")
    if not isinstance(result, dict):
        probe["reason"] = "registration_result_invalid"
        return {"status": "degraded", "probe": probe}
    transport = result.get("transport")
    direct_registration_matches = bool(
        result.get("name") == "ouroboros"
        and result.get("enabled") is True
        and ouroboros_direct_launcher_matches(transport, ouroboros_executable)
    )
    isolated_registration_matches = bool(
        result.get("name") == "ouroboros"
        and result.get("enabled") is True
        and ouroboros_isolated_launcher_matches(transport)
    )
    if direct_registration_matches or isolated_registration_matches:
        return {"status": "configured", "probe": probe}
    if result.get("enabled") is True:
        probe["reason"] = "registration_mismatch"
        return {"status": "degraded", "probe": probe}
    if result.get("enabled") is False:
        probe["reason"] = "registration_disabled"
    elif "enabled" not in result:
        probe["reason"] = "registration_enabled_missing"
    else:
        probe["reason"] = "registration_enabled_invalid"
    return {"status": "degraded", "probe": probe}


def selected_fields(value: Any, names: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {name: value[name] for name in names if name in value}


def normalize_sanho_status(probe: dict[str, Any]) -> dict[str, Any]:
    normalized = normalized_probe(probe)
    result = probe.get("result")
    if not isinstance(result, dict) or isinstance(result.get("error"), dict):
        return normalized
    safe: dict[str, Any] = {}
    relation = result.get("relation")
    if (
        isinstance(relation, dict)
        and isinstance(relation.get("known"), bool)
        and all(
            isinstance(relation.get(name), int)
            and not isinstance(relation.get(name), bool)
            and relation[name] >= 0
            for name in ("behind", "ahead")
        )
    ):
        safe["relation"] = selected_fields(relation, ("known", "behind", "ahead"))
    for name, fields in (
        ("publication", ("known", "pending")),
        ("working_copy", ("known", "docs_clean")),
    ):
        source = result.get(name)
        if isinstance(source, dict) and all(
            isinstance(source.get(field), bool) for field in fields
        ):
            safe[name] = selected_fields(source, fields)
    raw_preview = result.get("sync_preview")
    preview = {}
    if isinstance(raw_preview, dict) and all(
        isinstance(raw_preview.get(field), bool) for field in ("known", "clean")
    ):
        preview = selected_fields(raw_preview, ("known", "clean"))
    if isinstance(raw_preview, dict) and isinstance(raw_preview.get("conflicts"), list):
        preview["conflict_count"] = len(raw_preview["conflicts"])
    if preview:
        safe["sync_preview"] = preview
    readiness = result.get("local_readiness")
    if isinstance(readiness, dict):
        safe_readiness = {}
        for operation in ("sync", "pull"):
            source = readiness.get(operation)
            if (
                isinstance(source, dict)
                and isinstance(source.get("ready"), bool)
                and isinstance(source.get("blocked_by"), list)
            ):
                safe_readiness[operation] = {
                    "ready": source["ready"],
                    "blocked_by_count": len(source["blocked_by"]),
                }
        if safe_readiness:
            safe["local_readiness"] = safe_readiness
    if isinstance(result.get("sync_in_progress"), bool):
        safe["sync_in_progress"] = result["sync_in_progress"]
    normalized["contract_valid"] = {
        "relation",
        "publication",
        "working_copy",
        "sync_preview",
        "local_readiness",
        "sync_in_progress",
    }.issubset(safe)
    if safe:
        normalized["result"] = safe
    return normalized


def normalize_sanho_doctor(probe: dict[str, Any]) -> dict[str, Any]:
    normalized = normalized_probe(probe)
    result = probe.get("result")
    if not isinstance(result, dict) or isinstance(result.get("error"), dict):
        return normalized
    safe: dict[str, Any] = {}
    if (
        isinstance(result.get("warnings"), int)
        and not isinstance(result.get("warnings"), bool)
        and result["warnings"] >= 0
    ):
        safe["warnings"] = result["warnings"]
    checks = result.get("checks")
    checks_valid = False
    if isinstance(checks, list):
        checks_valid = all(
            isinstance(check, dict)
            and isinstance(check.get("name"), str)
            and bool(check["name"])
            and check.get("severity") in {"ok", "warning", "error"}
            for check in checks
        )
        if checks_valid:
            safe["check_count"] = len(checks)
            safe["warning_check_count"] = sum(
                1 for check in checks if check.get("severity") == "warning"
            )
    normalized["contract_valid"] = (
        "warnings" in safe
        and checks_valid
        and safe["warnings"] == safe.get("warning_check_count")
    )
    if safe:
        normalized["result"] = safe
    return normalized


def skill_root_symlinked(root: Path) -> bool:
    try:
        anchor = Path(os.path.commonpath((Path.home(), root)))
        relative = root.relative_to(anchor)
    except (ValueError, OSError):
        return True
    current = anchor
    if current.is_symlink():
        return True
    for part in relative.parts:
        if part == "..":
            current = current.parent
            continue
        if part == ".":
            continue
        current = current / part
        if current.is_symlink():
            return True
    return False


def safe_skill_file_state(directory: Path, relative_path: str) -> tuple[bool, bool]:
    if skill_root_symlinked(directory.parent):
        return False, True
    current = directory
    if current.is_symlink():
        return False, True
    for part in Path(relative_path).parts:
        current = current / part
        if current.is_symlink():
            return False, True
    return current.is_file(), False


def safe_managed_file_state(path: Path, boundary: Path) -> tuple[bool, bool]:
    try:
        relative = path.relative_to(boundary)
    except ValueError:
        return False, True
    current = boundary
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return False, True
    return current.is_file(), False


def managed_directory_tree_symlinked(path: Path, boundary: Path) -> bool:
    _, symlinked = safe_managed_file_state(path, boundary)
    if symlinked:
        return True
    if not path.is_dir():
        return False
    try:
        for root, directories, files in os.walk(path, followlinks=False):
            root_path = Path(root)
            if any((root_path / name).is_symlink() for name in directories + files):
                return True
    except OSError:
        return True
    return False


def inspect_agent_skill(name: str, required_files: tuple[str, ...]) -> dict[str, Any]:
    installations: list[dict[str, Any]] = []
    for root in skill_roots():
        directory = root / name
        if skill_root_symlinked(root):
            installations.append(
                {
                    "path": str(directory),
                    "symlinked": True,
                    "frontmatter_valid": False,
                    "files": [
                        {
                            "path": relative_path,
                            "present": False,
                            "symlinked": True,
                            "sha256": None,
                        }
                        for relative_path in required_files
                    ],
                }
            )
            continue
        if not directory.exists() and not directory.is_symlink():
            continue
        files = []
        for relative_path in required_files:
            path = directory / relative_path
            present, symlinked = safe_skill_file_state(directory, relative_path)
            files.append(
                {
                    "path": relative_path,
                    "present": present,
                    "symlinked": symlinked,
                    "sha256": file_sha256(path) if present else None,
                }
            )
        skill_entry = next(entry for entry in files if entry["path"] == "SKILL.md")
        skill_path = directory / "SKILL.md"
        installations.append(
            {
                "path": str(directory),
                "symlinked": any(entry["symlinked"] for entry in files),
                "frontmatter_valid": bool(skill_entry["present"])
                and frontmatter_name(skill_path) == name,
                "files": files,
            }
        )
    if not installations:
        status = "missing"
    elif (
        len(installations) == 1
        and not installations[0]["symlinked"]
        and installations[0]["frontmatter_valid"]
        and all(entry["present"] for entry in installations[0]["files"])
        and not any(entry["symlinked"] for entry in installations[0]["files"])
    ):
        status = "configured"
    else:
        status = "degraded"
    return {
        "status": status,
        "present": bool(installations),
        "duplicate": len(installations) > 1,
        "installations": installations,
    }


def inspect_sanho_skill() -> dict[str, Any]:
    return inspect_agent_skill("use-sanho", SANHO_SKILL_FILES)


def normalize_podway_envelope(
    probe: dict[str, Any],
    command: str,
    result_schemas: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    normalized = normalized_probe(probe)
    envelope = probe.get("result")
    if not isinstance(envelope, dict):
        return normalized, None
    schema = envelope.get("schema")
    if schema == "podway.error/v1":
        code = envelope.get("code")
        if code in {"SESSION_NOT_FOUND", "LEGACY_PROCEDURE_STATE_UNSUPPORTED"}:
            normalized["error_code"] = code
        else:
            normalized["error_code"] = "unrecognized_podway_error"
        normalized["output_schema"] = schema
        return normalized, None
    if schema != "podway.output/v3":
        normalized["ok"] = False
        normalized["error_code"] = "unexpected_output_schema"
        return normalized, None
    normalized["output_schema"] = schema
    if envelope.get("command") != command:
        normalized["ok"] = False
        normalized["error_code"] = "unexpected_command"
        return normalized, None
    payload = envelope.get("result")
    if not isinstance(payload, dict):
        normalized["ok"] = False
        normalized["error_code"] = "invalid_result"
        return normalized, None
    result_schema = payload.get("schema")
    if result_schemas and result_schema not in result_schemas:
        normalized["ok"] = False
        normalized["error_code"] = "unexpected_result_schema"
        return normalized, None
    if isinstance(result_schema, str):
        normalized["result_schema"] = result_schema
    return normalized, payload


def inspect_sanho(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("sanho")
    tool["version_supported"] = False
    tool["agent_skill"] = inspect_sanho_skill()
    tool["configuration"] = [
        configuration_entry(repository, ".sanho.json", timeout_seconds),
        configuration_entry(repository, ".sanho_base.json", timeout_seconds),
    ]
    if not tool["installed"]:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        return tool
    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = normalized_probe(version_probe)
    tool["version"] = version_from_probe(version_probe)
    tool["version_supported"] = supported_sanho_version(tool["version"])
    if not version_probe["ok"] or not tool["version_supported"]:
        tool["status"] = "degraded"
    if any(entry["symlinked"] for entry in tool["configuration"]):
        tool["probes"]["status"] = skipped_probe("configuration_symlinked")
        tool["probes"]["doctor"] = skipped_probe("configuration_symlinked")
        tool["status"] = "degraded"
        return tool
    if not tool["configuration"][0]["present"]:
        tool["probes"]["status"] = skipped_probe("configuration_missing")
        tool["probes"]["doctor"] = skipped_probe("configuration_missing")
        return tool
    status_probe = json_probe(
        [tool["executable"], "status", "--json"], repository, timeout_seconds
    )
    doctor_probe = json_probe(
        [tool["executable"], "doctor", "--json"], repository, timeout_seconds
    )
    normalized_status = normalize_sanho_status(status_probe)
    normalized_doctor = normalize_sanho_doctor(doctor_probe)
    tool["probes"].update({"status": normalized_status, "doctor": normalized_doctor})
    doctor_result = normalized_doctor.get("result")
    no_doctor_warnings = (
        isinstance(doctor_result, dict) and doctor_result.get("warnings") == 0
    )
    tool["status"] = (
        "configured"
        if version_probe["ok"]
        and tool["version_supported"]
        and normalized_status["ok"]
        and normalized_doctor["ok"]
        and normalized_status.get("contract_valid") is True
        and normalized_doctor.get("contract_valid") is True
        and no_doctor_warnings
        else "degraded"
    )
    return tool


def normalize_mulgae_command_envelope(
    probe: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    normalized = normalized_probe(probe)
    envelope = probe.get("result")
    if not isinstance(envelope, dict):
        return normalized, None
    schema = envelope.get("schema_version")
    if isinstance(schema, str):
        normalized["output_schema"] = schema
    if schema != MULGAE_COMMAND_RESULT_SCHEMA:
        normalized["error_code"] = "unsupported_output_schema"
        return normalized, None
    return normalized, envelope


def mulgae_reason_codes(envelope: Any) -> list[str]:
    if not isinstance(envelope, dict) or not isinstance(envelope.get("reasons"), list):
        return []
    return [
        reason["code"]
        for reason in envelope["reasons"]
        if isinstance(reason, dict)
        and isinstance(reason.get("code"), str)
        and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", reason["code"])
    ]


def normalize_mulgae_diagnostic_check(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    status = value.get("status")
    reason_codes = value.get("reason_codes")
    if status not in {"verified", "failed", "unverifiable", "not_applicable"}:
        return None
    if not isinstance(reason_codes, list) or not all(
        isinstance(reason, str)
        and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", reason) is not None
        for reason in reason_codes
    ):
        return None
    return {"status": status, "reason_codes": reason_codes}


def normalize_mulgae_readiness(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    state = value.get("state")
    exit_code = value.get("exit_code")
    reason_codes = value.get("reason_codes")
    if state not in {"ready", "degraded", "unverified", "unsafe"}:
        return None
    if (
        exit_code not in {0, 4, 8}
        or isinstance(exit_code, bool)
        or not isinstance(reason_codes, list)
    ):
        return None
    if not all(
        isinstance(reason, str)
        and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", reason) is not None
        for reason in reason_codes
    ):
        return None
    return {"state": state, "exit_code": exit_code, "reason_codes": reason_codes}


def normalize_mulgae_cli_compatibility(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    status = value.get("status")
    if status not in {"verified", "failed", "unverifiable", "not_applicable"}:
        return None
    fields = (
        "observed_version",
        "eligibility",
        "compatibility",
        "minimum_version",
        "verified_latest",
        "reason_code",
    )
    if not all(isinstance(value.get(field), str) for field in fields):
        return None
    if value["eligibility"] not in {"eligible", "ineligible", "not_evaluated"}:
        return None
    if value["compatibility"] not in {
        "verified",
        "newer_than_verified",
        "below_minimum",
        "malformed",
        "not_observed",
    }:
        return None
    version_pattern = r"(?:|\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)"
    if any(
        re.fullmatch(version_pattern, value[field]) is None
        for field in ("observed_version", "minimum_version", "verified_latest")
    ):
        return None
    if (
        value["reason_code"]
        and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value["reason_code"]) is None
    ):
        return None
    return {"status": status, **{field: value[field] for field in fields}}


def normalize_mulgae_provider_inventory(value: Any) -> list[dict[str, Any]] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    inventory: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            return None
        family = row.get("family")
        configured = row.get("configured")
        referenced_by_roles = row.get("referenced_by_roles")
        state = row.get("state")
        reason = row.get("reason")
        binary_available = normalize_mulgae_diagnostic_check(
            row.get("binary_available")
        )
        cli_compatible = normalize_mulgae_cli_compatibility(row.get("cli_compatible"))
        if (
            family not in {"kimi", "zcode", "agy", "codex"}
            or not isinstance(configured, bool)
            or not isinstance(referenced_by_roles, list)
            or not all(
                role
                in {
                    "logic",
                    "security",
                    "maintainability",
                    "product",
                    "documentation",
                    "testing",
                    "artist",
                }
                for role in referenced_by_roles
            )
            or state
            not in {
                "eligible",
                "unavailable",
                "not_configured",
                "not_observed",
            }
            or not isinstance(reason, str)
            or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", reason) is None
            or binary_available is None
            or cli_compatible is None
        ):
            return None
        inventory.append(
            {
                "family": family,
                "configured": configured,
                "referenced_by_roles": referenced_by_roles,
                "state": state,
                "reason": reason,
                "binary_available": binary_available,
                "cli_compatible": cli_compatible,
            }
        )
    if [row["family"] for row in inventory] != ["kimi", "zcode", "agy", "codex"]:
        return None
    return inventory


def normalize_mulgae_doctor(probe: dict[str, Any]) -> dict[str, Any]:
    normalized, envelope = normalize_mulgae_command_envelope(probe)
    if not isinstance(envelope, dict):
        return normalized
    result = envelope.get("result")
    doctor = result.get("doctor") if isinstance(result, dict) else None
    if isinstance(result, dict):
        safe: dict[str, Any] = {}
        if isinstance(doctor, dict):
            schema = doctor.get("schema_version")
            if isinstance(schema, str):
                normalized["result_schema"] = schema
            if schema != MULGAE_DOCTOR_RESULT_SCHEMA:
                normalized["doctor_capability"] = "unsupported"
                normalized["result"] = safe
                return normalized
            safe_doctor: dict[str, Any] = {"schema_version": schema}
            raw_config = doctor.get("config")
            config: dict[str, Any] = {}
            if isinstance(raw_config, dict):
                allowed_config_values = {
                    "status": {"ready", "missing", "invalid", "unsafe"},
                    "locality": {"verified", "rejected", "not_observed"},
                    "provenance_state": {"accepted", "rejected", "not_observed"},
                }
                for name, allowed in allowed_config_values.items():
                    value = raw_config.get(name)
                    if value in allowed:
                        config[name] = value
                reason_codes = raw_config.get("reason_codes")
                allowed_config_reasons = {
                    "config_missing",
                    "local_config_missing",
                    "config_provider_identity_invalid",
                    "config_role_mapping_invalid",
                    "config_yaml_invalid",
                    "config_locality_unsafe",
                    "config_not_observed_due_to_locality",
                }
                if isinstance(reason_codes, list) and all(
                    code in allowed_config_reasons for code in reason_codes
                ):
                    config["reason_codes"] = reason_codes
            if config:
                safe_doctor["config"] = config
            configured = doctor.get("configured_provider_ids")
            if isinstance(configured, list) and all(
                isinstance(provider, str) for provider in configured
            ):
                canonical = ["kimi", "zcode", "agy", "codex"]
                if configured == [
                    provider for provider in canonical if provider in configured
                ]:
                    safe_doctor["configured_provider_ids"] = configured
            inventory = doctor.get("provider_inventory")
            if isinstance(inventory, list):
                safe_inventory = normalize_mulgae_provider_inventory(inventory)
                if safe_inventory is not None:
                    safe_doctor["provider_inventory"] = safe_inventory
            for name in (
                "config_v3",
                "local_configuration",
                "provider_identity",
            ):
                selected = normalize_mulgae_diagnostic_check(doctor.get(name))
                if selected is not None:
                    safe_doctor[name] = selected
            raw_assignment = doctor.get("assignment")
            assignment = {}
            if isinstance(raw_assignment, dict):
                for name in ("state", "resilience"):
                    value = raw_assignment.get(name)
                    if value in {"ready", "unavailable", "not_observed"}:
                        assignment[name] = value
            if assignment:
                safe_doctor["assignment"] = assignment
            for name in (
                "readiness",
                "configured_readiness",
                "role_route_readiness",
            ):
                selected = normalize_mulgae_readiness(doctor.get(name))
                if selected is not None:
                    safe_doctor[name] = selected
            platform_evidence = doctor.get("platform_evidence")
            if isinstance(platform_evidence, list):
                safe_doctor["platform_evidence"] = [
                    {"cell": evidence["cell"], "native": evidence["native"]}
                    for evidence in platform_evidence
                    if isinstance(evidence, dict)
                    and evidence.get("cell")
                    in {"darwin-arm64", "darwin-amd64", "linux-amd64", "linux-arm64"}
                    and isinstance(evidence.get("native"), bool)
                ]
            required_fields = {
                "config_v3",
                "local_configuration",
                "provider_identity",
                "configured_provider_ids",
                "provider_inventory",
                "readiness",
                "configured_readiness",
                "role_route_readiness",
            }
            if not required_fields.issubset(safe_doctor):
                normalized["doctor_capability"] = "invalid"
                normalized["result"] = safe
                return normalized
            normalized["doctor_capability"] = "supported"
            safe["doctor"] = safe_doctor
        else:
            normalized["doctor_capability"] = "unsupported"
        normalized["result"] = safe
    reason_codes = mulgae_reason_codes(envelope)
    if reason_codes:
        normalized["reason_codes"] = reason_codes
    return normalized


def inspect_mulgae_installation_prerequisites(
    repository: Path, timeout_seconds: float
) -> dict[str, Any]:
    go_executable = shutil.which("go")
    prerequisite: dict[str, Any] = {
        "go": {
            "installed": go_executable is not None,
            "version": None,
            "supported": False,
            "minimum": "go1.26.6",
        }
    }
    if not go_executable:
        prerequisite["go"]["probe"] = skipped_probe("executable_missing")
        return prerequisite
    probe = json_probe(
        [go_executable, "env", "-json", "GOVERSION", "GOOS", "GOARCH"],
        repository,
        timeout_seconds,
    )
    normalized = normalized_probe(probe)
    result = probe.get("result")
    if isinstance(result, dict):
        version = result.get("GOVERSION")
        safe_result: dict[str, str] = {}
        if isinstance(version, str) and re.fullmatch(
            rf"go{CANONICAL_NUMERIC_COMPONENT}\."
            rf"{CANONICAL_NUMERIC_COMPONENT}(?:\."
            rf"{CANONICAL_NUMERIC_COMPONENT})?(?:[-+][0-9A-Za-z.-]+)?",
            version,
        ):
            prerequisite["go"]["version"] = version
            prerequisite["go"]["supported"] = supported_mulgae_go_version(version)
            safe_result["GOVERSION"] = version
        goos = result.get("GOOS")
        if goos in {
            "aix",
            "android",
            "darwin",
            "dragonfly",
            "freebsd",
            "illumos",
            "ios",
            "js",
            "linux",
            "netbsd",
            "openbsd",
            "plan9",
            "solaris",
            "wasip1",
            "windows",
        }:
            safe_result["GOOS"] = goos
        goarch = result.get("GOARCH")
        if goarch in {
            "386",
            "amd64",
            "arm",
            "arm64",
            "loong64",
            "mips",
            "mips64",
            "mips64le",
            "mipsle",
            "ppc64",
            "ppc64le",
            "riscv64",
            "s390x",
            "wasm",
        }:
            safe_result["GOARCH"] = goarch
        normalized["result"] = safe_result
    prerequisite["go"]["probe"] = normalized
    return prerequisite


def mulgae_configuration_entry(
    repository: Path, relative_path: str, timeout_seconds: float
) -> dict[str, Any]:
    entry = configuration_entry(repository, relative_path, timeout_seconds)
    entry["tracked"] = tracked_by_git(repository, relative_path, timeout_seconds)
    if relative_path == ".mulgae/local.yaml":
        entry["mode"] = None
        if entry["present"]:
            try:
                entry["mode"] = oct(
                    repository.joinpath(relative_path).stat().st_mode & 0o777
                )
            except OSError:
                pass
        entry["mode_0600"] = entry["mode"] == "0o600"
    return entry


def mcp_registration_probe(
    codex_executable: str,
    name: str,
    cwd: Path,
    timeout_seconds: float,
    environment_overrides: dict[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = run_command(
        [codex_executable, "mcp", "get", name, "--json"],
        cwd,
        timeout_seconds,
        environment_overrides,
    )
    return raw, parse_json_probe(raw)


def resolve_mcp_command(command: Any) -> Path | None:
    if not isinstance(command, str) or not command:
        return None
    candidate = Path(command).expanduser()
    if (
        candidate.is_absolute()
        and candidate.is_file()
        and os.access(candidate, os.X_OK)
    ):
        return candidate.resolve()
    if not candidate.is_absolute():
        discovered = shutil.which(command)
        if discovered:
            return Path(discovered).resolve()
    return None


def missing_mcp_scope(reason: str = "registration_not_found") -> dict[str, Any]:
    return {"status": "missing", "reason": reason}


def failed_mcp_scope(
    raw_probe: dict[str, Any], probe: dict[str, Any], name: str
) -> dict[str, Any]:
    if named_mcp_server_missing(raw_probe, name):
        return missing_mcp_scope()
    return {
        "status": "degraded",
        "reason": (
            "registration_probe_timed_out"
            if probe["timed_out"]
            else "registration_probe_failed"
        ),
    }


def classify_mulgae_mcp_scope(
    raw_probe: dict[str, Any],
    probe: dict[str, Any],
    mulgae_executable: str | None,
    repository: Path,
    scope: str,
) -> dict[str, Any]:
    if not probe["ok"]:
        return failed_mcp_scope(raw_probe, probe, "mulgae")
    result = probe.get("result")
    transport = result.get("transport") if isinstance(result, dict) else None
    if not isinstance(result, dict) or not isinstance(transport, dict):
        return {"status": "degraded", "reason": "invalid_registration_result"}

    if "required" not in result:
        required = None
        required_verification = "unverifiable"
        required_output_capability = "not_reported"
        compatibility_reason = "required_unverifiable"
    elif isinstance(result["required"], bool):
        required = result["required"]
        required_verification = "verified" if required else "mismatch"
        required_output_capability = "reported"
        compatibility_reason = None
    else:
        return {
            "status": "degraded",
            "reason": "invalid_registration_result",
            "required_output_capability": "invalid",
        }

    resolved_command = resolve_mcp_command(transport.get("command"))
    args = transport.get("args")
    arguments_match = False
    repository_bound = scope == "global"
    if isinstance(args, list) and all(isinstance(argument, str) for argument in args):
        if scope == "global":
            arguments_match = args == ["mcp"]
        elif len(args) == 3 and args[:2] == ["mcp", "--project-root"]:
            try:
                repository_bound = Path(args[2]).expanduser().resolve() == repository
            except OSError:
                repository_bound = False
            arguments_match = repository_bound

    raw_cwd = transport.get("cwd", result.get("cwd"))
    if scope == "global":
        cwd_bound = raw_cwd in {None, ""}
    else:
        try:
            cwd_bound = (
                isinstance(raw_cwd, str)
                and Path(raw_cwd).expanduser().resolve() == repository
            )
        except OSError:
            cwd_bound = False
    startup_timeout = result.get("startup_timeout_sec")
    tool_timeout = result.get("tool_timeout_sec")
    binary_matches = bool(
        resolved_command
        and mulgae_executable
        and resolved_command == Path(mulgae_executable).resolve()
    )
    registration = {
        "status": "degraded",
        "enabled": result.get("enabled") is True,
        "stdio": transport.get("type") == "stdio",
        "repository_bound": repository_bound,
        "arguments_match": arguments_match,
        "cwd_bound": cwd_bound,
        "required": required,
        "required_verification": required_verification,
        "required_output_capability": required_output_capability,
        "compatibility_reason": compatibility_reason,
        "command_resolvable": resolved_command is not None,
        "binary_matches_selected": binary_matches,
        "startup_timeout_sec": startup_timeout,
        "tool_timeout_sec": tool_timeout,
    }
    if (
        registration["enabled"]
        and registration["stdio"]
        and arguments_match
        and cwd_bound
        and required_verification in {"verified", "unverifiable"}
        and binary_matches
        and finite_number(startup_timeout)
        and startup_timeout >= 30
        and finite_number(tool_timeout)
        and tool_timeout >= MULGAE_MCP_TOOL_TIMEOUT_SEC
    ):
        registration["status"] = "configured"
    else:
        registration["reason"] = "registration_mismatch"
    return registration


def mcp_recommendation(global_status: str, local_present: bool) -> str:
    if local_present:
        if global_status == "configured":
            return "confirm_or_remove_local_registration"
        return "confirm_local_intent_or_migrate_to_global"
    if global_status == "configured":
        return "none"
    if global_status == "missing":
        return "install_global_registration"
    return "repair_global_registration"


def effective_mcp_registration(
    name: str,
    global_registration: dict[str, Any],
    local_registration: dict[str, Any],
    local_symlinked: bool,
    effective_raw: dict[str, Any],
    effective_probe: dict[str, Any],
) -> tuple[str, str, str | None]:
    if local_symlinked:
        return "unverifiable", "unverifiable", "project_configuration_symlinked"
    selected_scope = (
        "local"
        if local_registration["status"] != "missing"
        else "global"
        if global_registration["status"] != "missing"
        else "none"
    )
    if selected_scope == "none":
        if named_mcp_server_missing(effective_raw, name):
            return "missing", "none", "registration_not_found"
        if not effective_probe["ok"]:
            return "degraded", "unverifiable", "effective_registration_probe_failed"
        return "degraded", "unverifiable", "unexpected_effective_registration"

    selected = local_registration if selected_scope == "local" else global_registration
    if selected["status"] != "configured":
        return selected["status"], selected_scope, selected.get("reason")
    if not effective_probe["ok"] or effective_probe.get("result") != selected.get(
        "_result"
    ):
        return "degraded", selected_scope, "effective_registration_mismatch"
    return selected["status"], selected_scope, selected.get("reason")


def inspect_mulgae_mcp(
    repository: Path, mulgae_executable: str | None, timeout_seconds: float
) -> dict[str, Any]:
    project_config_present, project_config_symlinked = safe_managed_file_state(
        repository / ".codex" / "config.toml", repository
    )
    registration: dict[str, Any] = {
        "status": "missing",
        "preferred_scope": "global",
        "effective_scope": "none",
        "local_confirmation_required": None,
        "codex_version": None,
    }
    codex_executable = shutil.which("codex")
    if not codex_executable:
        registration.update(
            {
                "status": "unavailable",
                "effective_scope": "unverifiable",
                "reason": "codex_executable_missing",
                "global": {"status": "unavailable"},
                "local": {
                    "status": "unverifiable"
                    if project_config_symlinked
                    else "unavailable",
                    "project_config_present": project_config_present,
                    "project_config_symlinked": project_config_symlinked,
                },
            }
        )
        return registration
    version_probe = run_command(
        [codex_executable, "--version"], repository, timeout_seconds
    )
    if version_probe["ok"]:
        registration["codex_version"] = codex_version_from_output(
            version_probe["stdout"]
        )
    neutral_cwd = Path(repository.anchor)
    global_raw, global_probe = mcp_registration_probe(
        codex_executable, "mulgae", neutral_cwd, timeout_seconds
    )
    global_registration = classify_mulgae_mcp_scope(
        global_raw, global_probe, mulgae_executable, repository, "global"
    )
    if global_probe["ok"]:
        global_registration["_result"] = global_probe.get("result")

    if project_config_symlinked:
        local_registration = {
            "status": "unverifiable",
            "reason": "project_configuration_symlinked",
        }
    elif not project_config_present:
        local_registration = missing_mcp_scope("project_configuration_missing")
    else:
        local_raw, local_probe = mcp_registration_probe(
            codex_executable,
            "mulgae",
            neutral_cwd,
            timeout_seconds,
            {"CODEX_HOME": str(repository / ".codex")},
        )
        local_registration = classify_mulgae_mcp_scope(
            local_raw, local_probe, mulgae_executable, repository, "local"
        )
        if local_probe["ok"]:
            local_registration["_result"] = local_probe.get("result")
    local_registration.update(
        {
            "project_config_present": project_config_present,
            "project_config_symlinked": project_config_symlinked,
        }
    )

    effective_raw, effective_probe = mcp_registration_probe(
        codex_executable, "mulgae", repository, timeout_seconds
    )
    status, effective_scope, reason = effective_mcp_registration(
        "mulgae",
        global_registration,
        local_registration,
        project_config_symlinked,
        effective_raw,
        effective_probe,
    )
    global_registration.pop("_result", None)
    local_registration.pop("_result", None)
    local_confirmable = (
        None if project_config_symlinked else local_registration["status"] != "missing"
    )
    registration.update(
        {
            "status": status,
            "effective_scope": effective_scope,
            "local_confirmation_required": local_confirmable,
            "global": global_registration,
            "local": local_registration,
            "recommendation": (
                "resolve_symlinked_local_configuration"
                if project_config_symlinked
                else mcp_recommendation(
                    global_registration["status"],
                    bool(local_confirmable),
                )
            ),
        }
    )
    if reason:
        registration["reason"] = reason
    return registration


def inspect_mulgae(
    repository: Path, timeout_seconds: float, require_mcp: bool = False
) -> dict[str, Any]:
    tool = base_tool("mulgae")
    tool["version_supported"] = False
    tool["platform"] = {
        "system": platform.system(),
        "machine": platform.machine(),
        "supported": platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"},
    }
    tool["installation_prerequisites"] = inspect_mulgae_installation_prerequisites(
        repository, timeout_seconds
    )
    tool["agent_skill"] = inspect_agent_skill("use-mulgae", MULGAE_SKILL_FILES)
    tool["configuration"] = [
        mulgae_configuration_entry(repository, ".mulgae/config.yaml", timeout_seconds),
        mulgae_configuration_entry(repository, ".mulgae/local.yaml", timeout_seconds),
        configuration_entry(
            repository,
            ".mulgae/runtime/",
            timeout_seconds,
            ".mulgae/runtime/example",
        ),
        mulgae_configuration_entry(repository, ".mulgaeignore", timeout_seconds),
        configuration_entry(repository, ".codex/config.toml", timeout_seconds),
    ]
    tool["mcp_registration"] = inspect_mulgae_mcp(
        repository, tool["executable"], timeout_seconds
    )
    unavailable_check = {"status": "not_applicable", "reason_codes": []}
    unavailable_readiness = {
        "state": "unverified",
        "exit_code": 4,
        "reason_codes": ["doctor_v2_not_observed"],
    }
    tool["provider_inventory"] = []
    tool["mcp_required_for_status"] = require_mcp
    tool["health"] = {
        "mulgae_cli_compatibility": (
            "unavailable" if not tool["installed"] else "unverifiable"
        ),
        "doctor_contract": "not_observed",
        "config_v3": unavailable_check.copy(),
        "local_configuration": unavailable_check.copy(),
        "provider_identity": unavailable_check.copy(),
        "configured_readiness": unavailable_readiness.copy(),
        "role_route_readiness": unavailable_readiness.copy(),
        "mcp_registration": tool["mcp_registration"]["status"],
    }
    if not tool["installed"]:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        tool["probes"]["doctor"] = skipped_probe("executable_missing")
        return tool
    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = normalized_probe(version_probe)
    tool["version"] = version_from_probe(version_probe)
    tool["version_supported"] = supported_mulgae_version(tool["version"])
    project_config, local_config = tool["configuration"][:2]
    unsafe_configuration = any(
        entry["symlinked"] for entry in (project_config, local_config)
    )
    missing_configuration = not all(
        entry["present"] for entry in (project_config, local_config)
    )
    if unsafe_configuration or missing_configuration:
        tool["probes"]["doctor"] = skipped_probe(
            "configuration_symlinked"
            if unsafe_configuration
            else "configuration_missing"
        )
        tool["health"]["mulgae_cli_compatibility"] = (
            "compatible"
            if version_probe["ok"]
            and tool["version_supported"]
            and tool["platform"]["supported"]
            else "incompatible"
        )
        both_missing = not project_config["present"] and not local_config["present"]
        tool["status"] = (
            "installed"
            if both_missing
            and not unsafe_configuration
            and tool["health"]["mulgae_cli_compatibility"] == "compatible"
            else "degraded"
        )
        return tool
    doctor_probe = json_probe(
        [tool["executable"], "doctor", "--output", "json"],
        repository,
        timeout_seconds,
    )
    normalized_doctor = normalize_mulgae_doctor(doctor_probe)
    tool["probes"]["doctor"] = normalized_doctor

    both_missing = not project_config["present"] and not local_config["present"]
    doctor_result = normalized_doctor.get("result")
    doctor_payload = (
        doctor_result.get("doctor") if isinstance(doctor_result, dict) else None
    )
    mulgae_cli_compatible = (
        version_probe["ok"]
        and tool["version_supported"]
        and tool["platform"]["supported"]
    )
    health = tool["health"]
    health["mulgae_cli_compatibility"] = (
        "compatible" if mulgae_cli_compatible else "incompatible"
    )
    doctor_supported = normalized_doctor.get("doctor_capability") == "supported"
    doctor_command_ok = normalized_doctor["ok"]
    doctor_capability = normalized_doctor.get("doctor_capability")
    health["doctor_contract"] = (
        doctor_capability
        if doctor_capability in {"supported", "unsupported", "invalid"}
        else "unsupported"
    )
    if doctor_supported and isinstance(doctor_payload, dict):
        for name in (
            "config_v3",
            "local_configuration",
            "provider_identity",
            "configured_readiness",
            "role_route_readiness",
        ):
            value = doctor_payload.get(name)
            if isinstance(value, dict):
                health[name] = value
        inventory = doctor_payload.get("provider_inventory")
        if isinstance(inventory, list):
            tool["provider_inventory"] = inventory
    else:
        capability_reason = (
            "doctor_v2_invalid"
            if health["doctor_contract"] == "invalid"
            else "doctor_v2_unsupported"
        )
        unsupported = {
            "status": "unverifiable",
            "reason_codes": [capability_reason],
        }
        health["config_v3"] = unsupported.copy()
        health["local_configuration"] = unsupported.copy()
        health["provider_identity"] = unsupported.copy()
        unsupported_readiness = {
            "state": "unverified",
            "exit_code": 4,
            "reason_codes": [capability_reason],
        }
        health["configured_readiness"] = unsupported_readiness.copy()
        health["role_route_readiness"] = unsupported_readiness.copy()

    configured_readiness = health["configured_readiness"]
    offline_ready = (
        configured_readiness.get("state") == "ready"
        and configured_readiness.get("exit_code") == 0
    )
    mcp_status = tool["mcp_registration"]["status"]
    mcp_blocks = mcp_status == "degraded" or (
        require_mcp and mcp_status != "configured"
    )
    if (
        mulgae_cli_compatible
        and doctor_supported
        and doctor_command_ok
        and offline_ready
        and not mcp_blocks
    ):
        tool["status"] = "configured"
    elif (
        both_missing
        and mulgae_cli_compatible
        and doctor_supported
        and doctor_command_ok
        and not mcp_blocks
    ):
        tool["status"] = "installed"
    else:
        tool["status"] = "degraded"
    return tool


def classify_gaori_mcp_scope(
    raw_probe: dict[str, Any],
    probe: dict[str, Any],
    gaori_executable: str | None,
    repository: Path,
    scope: str,
) -> dict[str, Any]:
    if not probe["ok"]:
        return failed_mcp_scope(raw_probe, probe, "gaori")
    result = probe.get("result")
    transport = result.get("transport") if isinstance(result, dict) else None
    if not isinstance(result, dict) or not isinstance(transport, dict):
        return {"status": "degraded", "reason": "invalid_registration_result"}

    args = transport.get("args")
    repository_bound = scope == "global"
    arguments_match = False
    if isinstance(args, list) and all(isinstance(argument, str) for argument in args):
        if scope == "global":
            arguments_match = args == ["mcp"]
        elif len(args) == 3 and args[0] == "--repo" and args[2] == "mcp":
            try:
                repository_bound = Path(args[1]).expanduser().resolve() == repository
            except OSError:
                repository_bound = False
            arguments_match = repository_bound
    raw_cwd = transport.get("cwd", result.get("cwd"))
    cwd_unbound = raw_cwd in {None, ""}
    resolved_command = resolve_mcp_command(transport.get("command"))
    tool_timeout = result.get("tool_timeout_sec")
    binary_matches = bool(
        resolved_command
        and gaori_executable
        and resolved_command == Path(gaori_executable).resolve()
    )
    registration = {
        "status": "degraded",
        "enabled": result.get("enabled") is True,
        "stdio": transport.get("type") == "stdio",
        "repository_bound": repository_bound,
        "arguments_match": arguments_match,
        "cwd_unbound": cwd_unbound,
        "command_resolvable": resolved_command is not None,
        "binary_matches_selected": binary_matches,
        "tool_timeout_sec": tool_timeout,
    }
    if (
        registration["enabled"]
        and registration["stdio"]
        and arguments_match
        and cwd_unbound
        and binary_matches
        and finite_number(tool_timeout)
        and tool_timeout >= GAORI_MCP_TOOL_TIMEOUT_SEC
    ):
        registration["status"] = "configured"
    else:
        registration["reason"] = "registration_mismatch"
    return registration


def inspect_gaori_mcp(
    repository: Path, gaori_executable: str | None, timeout_seconds: float
) -> dict[str, Any]:
    project_config_present, project_config_symlinked = safe_managed_file_state(
        repository / ".codex" / "config.toml", repository
    )
    registration: dict[str, Any] = {
        "status": "missing",
        "preferred_scope": "global",
        "effective_scope": "none",
        "local_confirmation_required": None,
    }
    codex_executable = shutil.which("codex")
    if not codex_executable:
        registration.update(
            {
                "status": "unavailable",
                "effective_scope": "unverifiable",
                "reason": "codex_executable_missing",
                "global": {"status": "unavailable"},
                "local": {
                    "status": "unverifiable"
                    if project_config_symlinked
                    else "unavailable",
                    "project_config_present": project_config_present,
                    "project_config_symlinked": project_config_symlinked,
                },
            }
        )
        return registration

    neutral_cwd = Path(repository.anchor)
    global_raw, global_probe = mcp_registration_probe(
        codex_executable, "gaori", neutral_cwd, timeout_seconds
    )
    global_registration = classify_gaori_mcp_scope(
        global_raw, global_probe, gaori_executable, repository, "global"
    )
    if global_probe["ok"]:
        global_registration["_result"] = global_probe.get("result")

    if project_config_symlinked:
        local_registration = {
            "status": "unverifiable",
            "reason": "project_configuration_symlinked",
        }
    elif not project_config_present:
        local_registration = missing_mcp_scope("project_configuration_missing")
    else:
        local_raw, local_probe = mcp_registration_probe(
            codex_executable,
            "gaori",
            neutral_cwd,
            timeout_seconds,
            {"CODEX_HOME": str(repository / ".codex")},
        )
        local_registration = classify_gaori_mcp_scope(
            local_raw, local_probe, gaori_executable, repository, "local"
        )
        if local_probe["ok"]:
            local_registration["_result"] = local_probe.get("result")
    local_registration.update(
        {
            "project_config_present": project_config_present,
            "project_config_symlinked": project_config_symlinked,
        }
    )

    effective_raw, effective_probe = mcp_registration_probe(
        codex_executable, "gaori", repository, timeout_seconds
    )
    status, effective_scope, reason = effective_mcp_registration(
        "gaori",
        global_registration,
        local_registration,
        project_config_symlinked,
        effective_raw,
        effective_probe,
    )
    global_registration.pop("_result", None)
    local_registration.pop("_result", None)
    local_confirmable = (
        None if project_config_symlinked else local_registration["status"] != "missing"
    )
    registration.update(
        {
            "status": status,
            "effective_scope": effective_scope,
            "local_confirmation_required": local_confirmable,
            "global": global_registration,
            "local": local_registration,
            "recommendation": (
                "resolve_symlinked_local_configuration"
                if project_config_symlinked
                else mcp_recommendation(
                    global_registration["status"],
                    bool(local_confirmable),
                )
            ),
        }
    )
    if reason:
        registration["reason"] = reason
    return registration


def inspect_gaori(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("gaori")
    tool["version_supported"] = False
    tool["agent_skill"] = inspect_agent_skill("use-gaori", GAORI_SKILL_FILES)
    tool["configuration"] = [
        configuration_entry(repository, ".gaori/tester.yaml", timeout_seconds),
        configuration_entry(
            repository,
            ".gaori/tester/rules/",
            timeout_seconds,
            ".gaori/tester/rules/example.yaml",
        ),
        configuration_entry(repository, ".gaori/toolchain.yaml", timeout_seconds),
        configuration_entry(repository, ".codex/config.toml", timeout_seconds),
    ]
    tool["configuration"][1]["tree_symlinked"] = managed_directory_tree_symlinked(
        repository / ".gaori/tester/rules", repository
    )
    tool["mcp_registration"] = inspect_gaori_mcp(
        repository, tool["executable"], timeout_seconds
    )
    if not tool["installed"]:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        tool["probes"]["config_check"] = skipped_probe("executable_missing")
        return tool
    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = normalized_probe(version_probe)
    tool["version"] = version_from_probe(version_probe)
    tool["version_supported"] = supported_gaori_version(tool["version"])
    if not version_probe["ok"] or not tool["version_supported"]:
        tool["status"] = "degraded"
    if (
        any(entry["symlinked"] for entry in tool["configuration"][:3])
        or tool["configuration"][1]["tree_symlinked"]
    ):
        tool["probes"]["config_check"] = skipped_probe("configuration_symlinked")
        tool["status"] = "degraded"
        return tool
    if not tool["configuration"][0]["present"]:
        tool["probes"]["config_check"] = skipped_probe("configuration_missing")
        return tool
    config_probe = json_probe(
        [tool["executable"], "--json", "config", "check"],
        repository,
        timeout_seconds,
    )
    tool["probes"]["config_check"] = normalized_probe(config_probe)
    tool["status"] = (
        "configured"
        if version_probe["ok"] and tool["version_supported"] and config_probe["ok"]
        else "degraded"
    )
    return tool


def skill_roots() -> list[Path]:
    candidates: list[Path] = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home).expanduser().joinpath("skills"))
    candidates.extend(
        [Path.home().joinpath(".codex/skills"), Path.home().joinpath(".agents/skills")]
    )
    roots: list[Path] = []
    for candidate in candidates:
        lexical = candidate if candidate.is_absolute() else Path.cwd() / candidate
        if lexical not in roots:
            roots.append(lexical)
    return roots


def frontmatter_name(skill_path: Path) -> str | None:
    try:
        content = skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", content, re.DOTALL)
    if not match:
        return None
    name_match = re.search(
        r"^name:\s*[\"']?([^\"'#\n]+?)[\"']?\s*$", match.group(1), re.MULTILINE
    )
    return name_match.group(1).strip() if name_match else None


def inspect_lora() -> dict[str, Any]:
    expected_names = ("lore-commits", "lore-query", "lore-setup")
    skills: dict[str, dict[str, Any]] = {}
    for name in expected_names:
        installations: list[dict[str, Any]] = []
        for root in skill_roots():
            skill_directory = root.joinpath(name)
            skill_path = skill_directory.joinpath("SKILL.md")
            if skill_root_symlinked(root):
                installations.append(
                    {
                        "location": str(skill_directory),
                        "skill_file_present": False,
                        "frontmatter_valid": False,
                        "symlinked": True,
                    }
                )
                continue
            if not (skill_directory.exists() or skill_directory.is_symlink()):
                continue
            skill_file_present, symlinked = safe_skill_file_state(
                skill_directory, "SKILL.md"
            )
            installations.append(
                {
                    "location": str(skill_directory),
                    "skill_file_present": skill_file_present,
                    "frontmatter_valid": skill_file_present
                    and frontmatter_name(skill_path) == name,
                    "symlinked": symlinked,
                }
            )
        skills[name] = {
            "present": bool(installations),
            "duplicate": len(installations) > 1,
            "locations": [entry["location"] for entry in installations],
            "frontmatter_valid": bool(installations)
            and all(entry["frontmatter_valid"] for entry in installations),
            "symlinked": any(entry["symlinked"] for entry in installations),
            "installations": installations,
        }
    required_ready = all(
        len(skills[name]["installations"]) == 1
        and skills[name]["installations"][0]["skill_file_present"]
        and skills[name]["frontmatter_valid"]
        and not skills[name]["symlinked"]
        for name in ("lore-commits", "lore-query")
    )
    any_present = any(skill["present"] for skill in skills.values())
    return {
        "catalog_status": "active",
        "setup_supported": True,
        "installed": required_ready,
        "complete_tree_verified": False,
        "verification_scope": "structure_only",
        "executable": None,
        "version": None,
        "status": "unverifiable"
        if required_ready
        else ("degraded" if any_present else "missing"),
        "skills": skills,
        "lore_setup_present": skills["lore-setup"]["present"],
        "configuration": [],
        "probes": {},
    }


def inspect_deslop() -> dict[str, Any]:
    name = "deslop"
    installations: list[dict[str, Any]] = []
    for root in skill_roots():
        skill_directory = root.joinpath(name)
        skill_path = skill_directory.joinpath("SKILL.md")
        if skill_root_symlinked(root):
            installations.append(
                {
                    "location": str(skill_directory),
                    "skill_file_present": False,
                    "license_file_present": False,
                    "frontmatter_valid": False,
                    "symlinked": True,
                }
            )
            continue
        if not (skill_directory.exists() or skill_directory.is_symlink()):
            continue
        skill_file_present, skill_symlinked = safe_skill_file_state(
            skill_directory, "SKILL.md"
        )
        license_file_present, license_symlinked = safe_skill_file_state(
            skill_directory, "LICENSE"
        )
        symlinked = skill_symlinked or license_symlinked
        installations.append(
            {
                "location": str(skill_directory),
                "skill_file_present": skill_file_present,
                "license_file_present": license_file_present,
                "frontmatter_valid": skill_file_present
                and frontmatter_name(skill_path) == name,
                "symlinked": symlinked,
            }
        )

    ready = (
        len(installations) == 1
        and installations[0]["skill_file_present"]
        and installations[0]["license_file_present"]
        and installations[0]["frontmatter_valid"]
        and not installations[0]["symlinked"]
    )
    return {
        "catalog_status": "active",
        "setup_supported": True,
        "installed": ready,
        "executable": None,
        "version": None,
        "status": "configured"
        if ready
        else ("degraded" if installations else "missing"),
        "agent_skill": {
            "present": bool(installations),
            "duplicate": len(installations) > 1,
            "installations": installations,
        },
        "configuration": [],
        "probes": {},
    }


def inspect_ouroboros(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("ooo")
    tool["supported_range"] = ">=0.51.1,<0.52.0"
    codex = shutil.which("codex")
    direct_runtime_configured = False
    isolated_runtime_configured = False
    if codex:
        registration_raw = run_command(
            [
                str(Path(codex).resolve()),
                "mcp",
                "get",
                "ouroboros",
                "--json",
            ],
            repository,
            timeout_seconds,
        )
        tool["mcp_registration"] = classify_ouroboros_registration(
            registration_raw, tool["executable"]
        )
        parsed_registration = parse_json_probe(registration_raw)
        registration_result = parsed_registration.get("result")
        registration_transport = (
            registration_result.get("transport")
            if isinstance(registration_result, dict)
            else None
        )
        direct_runtime_configured = tool["mcp_registration"][
            "status"
        ] == "configured" and ouroboros_direct_launcher_matches(
            registration_transport, tool["executable"]
        )
        isolated_runtime_configured = tool["mcp_registration"][
            "status"
        ] == "configured" and ouroboros_isolated_launcher_matches(
            registration_transport
        )
    else:
        tool["mcp_registration"] = {
            "status": "unverifiable",
            "probe": skipped_probe("codex_executable_missing"),
        }

    if not tool["installed"]:
        tool["version_supported"] = False
        tool["probes"]["version"] = skipped_probe("executable_missing")
        tool["codex_integration"] = {
            "status": "missing",
            "probe": skipped_probe("executable_missing"),
        }
        if isolated_runtime_configured:
            runtime_probe = normalized_probe(registration_raw)
            runtime_probe["reason"] = "isolated_launcher_configured"
            tool["mcp_runtime"] = {
                "status": "configured",
                "probe": runtime_probe,
            }
        else:
            tool["mcp_runtime"] = {
                "status": "missing",
                "probe": skipped_probe("executable_missing"),
            }
        return tool

    version_raw = run_command(
        [tool["executable"], "--version"], repository, timeout_seconds
    )
    tool["version"] = ouroboros_version_from_output(
        f"{version_raw.get('stdout', '')}\n{version_raw.get('stderr', '')}"
    )
    tool["version_supported"] = version_raw["ok"] and supported_ouroboros_version(
        tool["version"]
    )
    tool["probes"]["version"] = {
        key: version_raw[key] for key in ("attempted", "ok", "exit_code", "timed_out")
    }

    codex_doctor = run_command(
        [tool["executable"], "codex", "doctor"], repository, timeout_seconds
    )
    tool["codex_integration"] = {
        "status": "configured" if codex_doctor["ok"] else "degraded",
        "probe": {
            key: codex_doctor[key]
            for key in ("attempted", "ok", "exit_code", "timed_out")
        },
    }

    if isolated_runtime_configured:
        runtime_probe = normalized_probe(registration_raw)
        runtime_probe["reason"] = "isolated_launcher_configured"
        tool["mcp_runtime"] = {
            "status": "configured",
            "probe": runtime_probe,
        }
    elif direct_runtime_configured:
        mcp_doctor = json_probe(
            [tool["executable"], "mcp", "doctor", "--json"],
            repository,
            timeout_seconds,
        )
        tool["mcp_runtime"] = {
            "status": "configured" if mcp_doctor["ok"] else "degraded",
            "probe": normalized_probe(mcp_doctor),
        }
    else:
        registration_reason = tool["mcp_registration"].get("probe", {}).get("reason")
        runtime_reason = (
            "registration_not_supported_launcher"
            if registration_reason in {None, "registration_mismatch"}
            else registration_reason
        )
        tool["mcp_runtime"] = {
            "status": "unverifiable",
            "probe": skipped_probe(runtime_reason),
        }

    components_ready = (
        tool["version_supported"]
        and tool["codex_integration"]["status"] == "configured"
        and tool["mcp_runtime"]["status"] == "configured"
        and tool["mcp_registration"]["status"] == "configured"
    )
    tool["status"] = "configured" if components_ready else "degraded"
    return tool


def inspect_podway(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("podway")
    tool["agent_skill"] = inspect_agent_skill("use-podway", PODWAY_SKILL_FILES)
    tool["platform"] = {
        "system": platform.system(),
        "machine": platform.machine(),
        "supported": platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"},
    }
    managed: list[dict[str, Any]] = []
    legacy_managed: list[dict[str, Any]] = []
    present_count = 0
    legacy_present_count = 0
    matching_count = 0
    workaround_count = 0
    tracked_count = 0
    for name in PODWAY_PROCEDURES:
        source = PODWAY_SOURCE_DIRECTORY / name
        target = repository / ".podway" / "procedures" / name
        relative_path = str(target.relative_to(repository))
        source_present, source_symlinked = safe_managed_file_state(
            source, PODWAY_SOURCE_DIRECTORY
        )
        present, symlinked = safe_managed_file_state(target, repository)
        source_digest = file_sha256(source) if source_present else None
        target_digest = file_sha256(target) if present else None
        source_bytes = file_bytes(source) if source_present else None
        target_bytes = file_bytes(target) if present else None
        matching = (
            present
            and not symlinked
            and source_present
            and not source_symlinked
            and source_digest is not None
            and target_digest == source_digest
        )
        workaround = (
            podway_v025_workaround_bytes(name, source_bytes)
            if source_bytes is not None
            else None
        )
        if symlinked or source_symlinked:
            source_state = "unsafe"
        elif not present:
            source_state = "missing"
        elif not source_present:
            source_state = "unsafe"
        elif matching:
            source_state = "canonical"
        elif workaround is not None and target_bytes == workaround:
            source_state = "podway_v0.2.5_workaround"
        else:
            source_state = "diverged"
        tracked = present and tracked_by_git(repository, relative_path, timeout_seconds)
        present_count += int(present or symlinked)
        matching_count += int(matching)
        workaround_count += int(source_state == "podway_v0.2.5_workaround")
        tracked_count += int(tracked)
        managed.append(
            {
                "path": relative_path,
                "present": present,
                "symlinked": symlinked,
                "tracked": tracked,
                "source_sha256": source_digest,
                "installed_sha256": target_digest,
                "matches_source": matching,
                "source_state": source_state,
            }
        )
    for name in LEGACY_PODWAY_PROCEDURES:
        target = repository / ".podway" / "procedures" / name
        relative_path = str(target.relative_to(repository))
        present, symlinked = safe_managed_file_state(target, repository)
        legacy_present_count += int(present or symlinked)
        legacy_managed.append(
            {
                "path": relative_path,
                "present": present,
                "symlinked": symlinked,
                "tracked": present
                and tracked_by_git(repository, relative_path, timeout_seconds),
            }
        )
    tool["configuration"] = [
        configuration_entry(repository, ".podway/config.yaml", timeout_seconds),
        configuration_entry(repository, ".podway/.gitignore", timeout_seconds),
        configuration_entry(repository, ".podway/runtime/", timeout_seconds),
    ]
    tool["managed_procedures"] = managed
    tool["legacy_managed_procedures"] = legacy_managed
    tool["migration_kinds"] = {
        "product_rename": legacy_present_count > 0,
        "podway_v0.2.5_workaround": workaround_count > 0,
    }
    tool["migration_required"] = any(tool["migration_kinds"].values())
    tool["readiness_status"] = (
        "not_configured"
        if present_count == 0 and legacy_present_count == 0
        else "degraded"
    )
    tool["legacy_state_detected"] = False
    tool["version_supported"] = False
    tool["daemon_version"] = None
    tool["versions_match"] = False
    if not tool["installed"]:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        tool["probes"]["daemon_status"] = skipped_probe("executable_missing")
        tool["probes"]["doctor"] = skipped_probe("executable_missing")
        tool["probes"]["session_status"] = skipped_probe("executable_missing")
        if present_count or legacy_present_count:
            tool["status"] = "degraded"
            tool["readiness_status"] = "degraded"
        return tool
    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = normalized_probe(version_probe)
    tool["version"] = version_from_probe(version_probe)
    tool["version_supported"] = supported_podway_version(tool["version"])

    daemon_probe = json_probe(
        [
            tool["executable"],
            "--json",
            "daemon",
            "wait-ready",
            "--timeout",
            "120s",
        ],
        repository,
        max(timeout_seconds, 125.0),
    )
    normalized_daemon, daemon_payload = normalize_podway_envelope(
        daemon_probe,
        "daemon.wait-ready",
        ("podway.daemon-status-result/v2",),
    )
    daemon_version = None
    daemon_reachable = False
    daemon_ready = False
    daemon_target = None
    if isinstance(daemon_payload, dict):
        daemon_schema = daemon_payload.get("schema")
        observed_daemon_version = daemon_payload.get("daemon_version")
        daemon_version = (
            observed_daemon_version
            if isinstance(observed_daemon_version, str)
            and re.fullmatch(
                r"v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?",
                observed_daemon_version,
            )
            else None
        )
        daemon_reachable = daemon_payload.get("reachable") is True
        observed_target = daemon_payload.get("target")
        daemon_target = (
            observed_target
            if observed_target in {"aarch64-apple-darwin", "x86_64-apple-darwin"}
            else None
        )
        readiness_state = None
        readiness_stage = None
        readiness_elapsed_ms = None
        worktree_recovery = None
        if daemon_schema == "podway.daemon-status-result/v2":
            observed_state = daemon_payload.get("readiness_state")
            observed_stage = daemon_payload.get("readiness_stage")
            observed_elapsed = daemon_payload.get("readiness_elapsed_ms")
            observed_recovery = daemon_payload.get("worktree_recovery")
            readiness_state = (
                observed_state
                if observed_state
                in {
                    "not_running",
                    "unreachable",
                    "starting",
                    "recovering",
                    "ready",
                    "failed",
                }
                else None
            )
            readiness_stage = (
                observed_stage
                if observed_stage
                in {"endpoint", "registry", "workspaces", "jobs", "ready", "failed"}
                else None
            )
            readiness_elapsed_ms = (
                observed_elapsed
                if isinstance(observed_elapsed, int)
                and not isinstance(observed_elapsed, bool)
                and observed_elapsed >= 0
                else None
            )
            if isinstance(observed_recovery, dict):
                recovery_counts = {
                    key: observed_recovery.get(key)
                    for key in ("total", "completed", "failed")
                }
                if all(
                    isinstance(value, int)
                    and not isinstance(value, bool)
                    and 0 <= value <= 10_000
                    for value in recovery_counts.values()
                ):
                    worktree_recovery = recovery_counts
            if readiness_state in {"not_running", "unreachable"}:
                v2_contract_valid = bool(
                    observed_stage is None
                    and observed_elapsed is None
                    and observed_recovery is None
                )
            else:
                v2_contract_valid = bool(
                    readiness_state is not None
                    and readiness_stage is not None
                    and readiness_elapsed_ms is not None
                    and worktree_recovery is not None
                )
            if not v2_contract_valid:
                normalized_daemon["ok"] = False
                normalized_daemon["error_code"] = "invalid_daemon_readiness"
            daemon_ready = bool(
                v2_contract_valid
                and daemon_reachable
                and daemon_payload.get("status") == "running"
                and readiness_state == "ready"
                and readiness_stage == "ready"
                and worktree_recovery["completed"] == worktree_recovery["total"]
            )
        normalized_daemon["result"] = {
            "installed": daemon_payload.get("installed") is True,
            "loaded": daemon_payload.get("loaded") is True,
            "reachable": daemon_reachable,
            "running": daemon_payload.get("status") == "running",
            "version_valid": daemon_version is not None,
            "target_supported": daemon_target is not None,
            "ready": daemon_ready,
            "readiness_state": readiness_state,
            "readiness_stage": readiness_stage,
            "readiness_elapsed_ms": readiness_elapsed_ms,
            "worktree_recovery": worktree_recovery,
        }
    tool["probes"]["daemon_status"] = normalized_daemon
    tool["daemon_version"] = daemon_version
    tool["versions_match"] = (
        normalized_version(tool["version"]) == normalized_version(daemon_version)
        if tool["version"] and daemon_version
        else False
    )

    initialized = tool["configuration"][0]["present"]
    session_contract_ok = True
    if initialized:
        doctor_probe = json_probe(
            [tool["executable"], "doctor", "--json"], repository, timeout_seconds
        )
        session_probe = json_probe(
            [tool["executable"], "--json", "status"], repository, timeout_seconds
        )
        normalized_doctor, doctor_payload = normalize_podway_envelope(
            doctor_probe, "workspace.doctor"
        )
        normalized_session, session_result = normalize_podway_envelope(
            session_probe,
            "session.status",
            ("podway.status-result/v3", "podway.compact-status-result/v3"),
        )
        if isinstance(doctor_payload, dict) and isinstance(
            doctor_payload.get("healthy"), bool
        ):
            normalized_doctor["result"] = {"healthy": doctor_payload["healthy"]}
        session_payload_valid = False
        if isinstance(session_result, dict):
            procedure = session_result.get("procedure")
            session = session_result.get("session")
            current = session_result.get("current")
            node = current.get("node") if isinstance(current, dict) else None
            normalized_session["result"] = {
                "procedure_present": isinstance(procedure, dict),
                "procedure_schema_valid": isinstance(procedure, dict)
                and procedure.get("schema") == "podway.procedure/v2",
                "goal_revision": session_result.get("goal_revision")
                if isinstance(session_result.get("goal_revision"), int)
                and not isinstance(session_result.get("goal_revision"), bool)
                else None,
                "session_present": isinstance(session, dict),
                "session_lifecycle": session.get("lifecycle")
                if isinstance(session, dict)
                and session.get("lifecycle")
                in {"prepared", "active", "completed", "cancelled", "discarded"}
                else None,
                "session_revision": session.get("revision")
                if isinstance(session, dict)
                and isinstance(session.get("revision"), int)
                and not isinstance(session.get("revision"), bool)
                else None,
                "current_graph_node_present": isinstance(node, dict)
                and isinstance(node.get("graph_node_id"), str),
            }
            allowed_procedure_ids = {Path(name).stem for name in PODWAY_PROCEDURES}
            session_payload_valid = bool(
                isinstance(procedure, dict)
                and procedure.get("schema") == "podway.procedure/v2"
                and procedure.get("id") in allowed_procedure_ids
                and isinstance(procedure.get("version"), str)
                and re.fullmatch(r"\d+", procedure["version"])
                and isinstance(procedure.get("digest"), str)
                and re.fullmatch(r"sha256:[0-9A-Za-z._-]{1,128}", procedure["digest"])
                and isinstance(session, dict)
                and isinstance(session.get("id"), str)
                and re.fullmatch(
                    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
                    session["id"],
                    re.IGNORECASE,
                )
                and session.get("lifecycle")
                in {"prepared", "active", "completed", "cancelled", "discarded"}
                and isinstance(session.get("revision"), int)
                and not isinstance(session.get("revision"), bool)
            )
        tool["probes"]["doctor"] = normalized_doctor
        tool["probes"]["session_status"] = normalized_session
        session_contract_ok = (
            normalized_session["ok"] and session_payload_valid
        ) or normalized_session.get("error_code") == "SESSION_NOT_FOUND"
        tool["legacy_state_detected"] = any(
            probe.get("error_code") == "LEGACY_PROCEDURE_STATE_UNSUPPORTED"
            for probe in (normalized_doctor, normalized_session)
        )
    else:
        tool["probes"]["doctor"] = skipped_probe("workspace_not_initialized")
        tool["probes"]["session_status"] = skipped_probe("workspace_not_initialized")

    procedure_checks_ok = True
    for entry in managed:
        if not entry["present"] or entry["symlinked"]:
            continue
        check = json_probe(
            [
                tool["executable"],
                "--json",
                "procedure",
                "check",
                "--warnings-as-errors",
                entry["path"],
            ],
            repository,
            timeout_seconds,
        )
        normalized_check, payload = normalize_podway_envelope(
            check,
            "procedure.check",
            ("podway.procedure-diagnostics-result/v1",),
        )
        entry["check"] = normalized_check
        if isinstance(payload, dict):
            entry["check"]["valid"] = payload.get("valid") is True
        procedure_checks_ok = (
            procedure_checks_ok
            and normalized_check["ok"]
            and isinstance(payload, dict)
            and payload.get("valid") is True
        )

    doctor_ok = not initialized
    doctor_payload = tool["probes"]["doctor"].get("result") if initialized else None
    if initialized:
        doctor_ok = bool(
            tool["probes"]["doctor"]["ok"]
            and isinstance(doctor_payload, dict)
            and doctor_payload.get("healthy") is True
        )
    healthy = (
        version_probe["ok"]
        and tool["version_supported"]
        and tool["platform"]["supported"]
        and normalized_daemon["ok"]
        and daemon_ready
        and daemon_target == "aarch64-apple-darwin"
        and tool["versions_match"]
        and doctor_ok
        and session_contract_ok
    )
    if present_count == 0:
        tool["status"] = "installed" if healthy else "degraded"
    elif (
        matching_count == len(PODWAY_PROCEDURES)
        and tracked_count == len(PODWAY_PROCEDURES)
        and procedure_checks_ok
        and initialized
        and tool["configuration"][1]["present"]
        and healthy
        and legacy_present_count == 0
    ):
        tool["readiness_status"] = "ready"
        tool["status"] = "configured"
    else:
        tool["readiness_status"] = "degraded"
        tool["status"] = "degraded"
    return tool


def inspect(
    requested_path: str,
    timeout_seconds: float,
    include_podway: bool = False,
    include_ouroboros: bool = False,
    require_mulgae_mcp: bool = False,
) -> dict[str, Any]:
    repository = resolve_repository(requested_path, timeout_seconds)
    tools = {
        "sanho": inspect_sanho(repository, timeout_seconds),
        "mulgae": inspect_mulgae(
            repository, timeout_seconds, require_mcp=require_mulgae_mcp
        ),
        "gaori": inspect_gaori(repository, timeout_seconds),
        "lora": inspect_lora(),
        "deslop": inspect_deslop(),
    }
    if include_podway:
        tools["podway"] = inspect_podway(repository, timeout_seconds)
    if include_ouroboros:
        tools["ouroboros"] = inspect_ouroboros(repository, timeout_seconds)
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": repository_inventory(repository, timeout_seconds),
        "tools": tools,
    }


def parse_arguments() -> argparse.Namespace:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository", required=True, help="Path inside the Git worktree to inspect"
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="Timeout for each read-only command",
    )
    parser.add_argument(
        "--include-podway",
        action="store_true",
        help="Include explicitly requested Podway readiness diagnostics",
    )
    parser.add_argument(
        "--include-ouroboros",
        action="store_true",
        help="Include explicitly requested Ouroboros integration diagnostics",
    )
    parser.add_argument(
        "--require-mulgae-mcp",
        action="store_true",
        help="Require an explicitly selected Mulgae MCP registration for status",
    )
    arguments = parser.parse_args()
    if (
        not math.isfinite(arguments.timeout_seconds)
        or arguments.timeout_seconds <= 0
        or arguments.timeout_seconds > MAX_COMMAND_TIMEOUT_SECONDS
    ):
        raise InspectionError(
            "invalid_arguments",
            f"--timeout-seconds must be greater than zero and at most {MAX_COMMAND_TIMEOUT_SECONDS:g}",
        )
    return arguments


def emit(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def main() -> int:
    try:
        arguments = parse_arguments()
        emit(
            inspect(
                arguments.repository,
                arguments.timeout_seconds,
                include_podway=arguments.include_podway,
                include_ouroboros=arguments.include_ouroboros,
                require_mulgae_mcp=arguments.require_mulgae_mcp,
            )
        )
        return 0
    except InspectionError as error:
        emit(
            {
                "schema_version": SCHEMA_VERSION,
                "error": {"code": error.code, "message": str(error)},
            }
        )
        return error.exit_code
    except Exception as error:  # noqa: BLE001 - keep the CLI error boundary JSON-only
        emit(
            {
                "schema_version": SCHEMA_VERSION,
                "error": {
                    "code": "inspection_failed",
                    "message": "unexpected local inspection failure",
                    "type": type(error).__name__,
                },
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
