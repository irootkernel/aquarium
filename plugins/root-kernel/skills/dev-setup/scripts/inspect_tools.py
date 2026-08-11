#!/usr/bin/env python3
"""Inspect local Root Kernel development-tool state without mutating it."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "root-kernel-dev-setup-inspection.v1"
CONFLICT_STATUSES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}


class InspectionError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InspectionError("invalid_arguments", message)


def run_command(
    arguments: list[str], cwd: Path, timeout_seconds: float
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["LANG"] = "C"
    environment["LC_ALL"] = "C"
    try:
        completed = subprocess.run(
            arguments,
            cwd=cwd,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
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
    if not raw_probe["attempted"] or raw_probe["timed_out"]:
        return probe
    try:
        probe["result"] = json.loads(raw_probe["stdout"])
    except json.JSONDecodeError:
        probe["ok"] = False
        probe["error_code"] = "invalid_json"
    return probe


def json_probe(
    arguments: list[str], repository: Path, timeout_seconds: float
) -> dict[str, Any]:
    return parse_json_probe(run_command(arguments, repository, timeout_seconds))


def version_from_probe(probe: dict[str, Any]) -> str | None:
    result = probe.get("result")
    if isinstance(result, dict) and isinstance(result.get("version"), str):
        return result["version"]
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


def configuration_entry(
    repository: Path, relative_path: str, timeout_seconds: float
) -> dict[str, Any]:
    return {
        "path": relative_path,
        "present": repository.joinpath(relative_path).exists(),
        "ignored": ignored_by_git(repository, relative_path, timeout_seconds),
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


def inspect_sanho(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("sanho")
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
    tool["probes"]["version"] = version_probe
    tool["version"] = version_from_probe(version_probe)
    if not version_probe["ok"]:
        tool["status"] = "degraded"
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
    tool["probes"].update({"status": status_probe, "doctor": doctor_probe})
    tool["status"] = (
        "configured"
        if version_probe["ok"] and status_probe["ok"] and doctor_probe["ok"]
        else "degraded"
    )
    return tool


def normalize_mulgae_config(probe: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        key: probe[key] for key in ("attempted", "ok", "exit_code", "timed_out")
    }
    result = probe.get("result")
    if isinstance(result, dict):
        command_result = result.get("result")
        if isinstance(command_result, dict):
            normalized["result"] = {
                key: command_result[key]
                for key in ("kind", "config_uri", "config_sha256")
                if isinstance(command_result.get(key), str)
            }
        reasons = result.get("reasons")
        if isinstance(reasons, list):
            normalized["reason_codes"] = [
                reason["code"]
                for reason in reasons
                if isinstance(reason, dict) and isinstance(reason.get("code"), str)
            ]
    if probe.get("error_code"):
        normalized["error_code"] = probe["error_code"]
    return normalized


def parse_mulgae_providers(raw_probe: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        key: raw_probe[key] for key in ("attempted", "ok", "exit_code", "timed_out")
    }
    providers: list[dict[str, str]] = []
    diagnostic: dict[str, str] = {}
    for line in raw_probe["stdout"].splitlines():
        fields = dict(re.findall(r"([a-z_]+)=([^\s]+)", line))
        if fields:
            providers.append(fields)
    for line in raw_probe["stderr"].splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in {"code", "stage", "hint"}:
            diagnostic[key.strip()] = value.strip()
    normalized["providers"] = providers
    if diagnostic:
        normalized["diagnostic"] = diagnostic
    return normalized


def inspect_mulgae(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("mulgae")
    tool["configuration"] = [
        configuration_entry(repository, ".mulgae/config.yaml", timeout_seconds),
        configuration_entry(repository, ".mulgae/", timeout_seconds),
        configuration_entry(repository, ".mulgaeignore", timeout_seconds),
    ]
    if not tool["installed"]:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        tool["probes"]["providers"] = skipped_probe("executable_missing")
        return tool
    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = version_probe
    tool["version"] = version_from_probe(version_probe)
    if not version_probe["ok"]:
        tool["status"] = "degraded"
    providers_probe = run_command(
        [tool["executable"], "providers", "--include-unverified"],
        repository,
        timeout_seconds,
    )
    tool["probes"]["providers"] = parse_mulgae_providers(providers_probe)
    if not tool["configuration"][0]["present"]:
        tool["probes"]["effective_config"] = skipped_probe("configuration_missing")
        return tool
    config_probe = json_probe(
        [tool["executable"], "config", "--mode", "effective", "--output", "json"],
        repository,
        timeout_seconds,
    )
    tool["probes"]["effective_config"] = normalize_mulgae_config(config_probe)
    tool["status"] = (
        "configured" if version_probe["ok"] and config_probe["ok"] else "degraded"
    )
    return tool


def text_probe(
    arguments: list[str], repository: Path, timeout_seconds: float
) -> dict[str, Any]:
    raw_probe = run_command(arguments, repository, timeout_seconds)
    return {
        "attempted": raw_probe["attempted"],
        "ok": raw_probe["ok"],
        "exit_code": raw_probe["exit_code"],
        "timed_out": raw_probe["timed_out"],
        "lines": [line for line in raw_probe["stdout"].splitlines() if line],
    }


def inspect_gaori(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("gaori")
    tool["configuration"] = [
        configuration_entry(repository, ".gaori/tester.yaml", timeout_seconds),
        configuration_entry(repository, ".gaori/", timeout_seconds),
    ]
    if not tool["installed"]:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        return tool
    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = version_probe
    tool["version"] = version_from_probe(version_probe)
    if not version_probe["ok"]:
        tool["status"] = "degraded"
    if not tool["configuration"][0]["present"]:
        tool["probes"]["rules"] = skipped_probe("configuration_missing")
        return tool
    rules_probe = text_probe(
        [tool["executable"], "rules", "list"], repository, timeout_seconds
    )
    tool["probes"]["rules"] = rules_probe
    tool["status"] = (
        "configured" if version_probe["ok"] and rules_probe["ok"] else "degraded"
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
        resolved = candidate.resolve()
        if resolved not in roots:
            roots.append(resolved)
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
        paths = [root.joinpath(name, "SKILL.md") for root in skill_roots()]
        matches = [path for path in paths if path.is_file()]
        skills[name] = {
            "present": bool(matches),
            "locations": [str(path) for path in matches],
            "frontmatter_valid": bool(matches)
            and all(frontmatter_name(path) == name for path in matches),
        }
    required_ready = all(
        skills[name]["present"] and skills[name]["frontmatter_valid"]
        for name in ("lore-commits", "lore-query")
    )
    any_present = any(skill["present"] for skill in skills.values())
    return {
        "catalog_status": "active",
        "setup_supported": True,
        "installed": required_ready,
        "executable": None,
        "version": None,
        "status": "configured"
        if required_ready
        else ("degraded" if any_present else "missing"),
        "skills": skills,
        "lore_setup_present": skills["lore-setup"]["present"],
        "configuration": [],
        "probes": {},
    }


def inspect_podway(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("podway", catalog_status="planned", setup_supported=False)
    if not tool["installed"]:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        tool["status"] = "planned"
        return tool
    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = version_probe
    tool["version"] = version_from_probe(version_probe)
    tool["status"] = "planned"
    return tool


def inspect(requested_path: str, timeout_seconds: float) -> dict[str, Any]:
    repository = resolve_repository(requested_path, timeout_seconds)
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": repository_inventory(repository, timeout_seconds),
        "tools": {
            "sanho": inspect_sanho(repository, timeout_seconds),
            "mulgae": inspect_mulgae(repository, timeout_seconds),
            "gaori": inspect_gaori(repository, timeout_seconds),
            "lora": inspect_lora(),
            "podway": inspect_podway(repository, timeout_seconds),
        },
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
    arguments = parser.parse_args()
    if arguments.timeout_seconds <= 0:
        raise InspectionError(
            "invalid_arguments", "--timeout-seconds must be greater than zero"
        )
    return arguments


def emit(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def main() -> int:
    try:
        arguments = parse_arguments()
        emit(inspect(arguments.repository, arguments.timeout_seconds))
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
