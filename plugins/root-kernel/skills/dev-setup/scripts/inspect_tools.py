#!/usr/bin/env python3
"""Inspect local Root Kernel development-tool state without mutating it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "root-kernel-dev-setup-inspection.v4"
MULGAE_COMMAND_RESULT_SCHEMA = "mulgae-command-result.v4"
MULGAE_DOCTOR_RESULT_SCHEMA = "mulgae-doctor-result.v2"
CONFLICT_STATUSES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}
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
    "references/authoring.md",
    "references/recovery.md",
)
PODWAY_PROCEDURES = (
    "root-kernel-task-v2.yaml",
    "root-kernel-goal-v2.yaml",
    "root-kernel-validation-v2.yaml",
)
PODWAY_SOURCE_DIRECTORY = (
    Path(__file__).resolve().parents[3] / "assets" / "podway" / "procedures"
)


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
        return probe
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


def normalized_version(version: str | None) -> str | None:
    if not version:
        return None
    return version.removeprefix("v")


def codex_version_from_output(output: str) -> str | None:
    match = re.search(r"\bcodex(?:-cli)?\s+v?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)\b", output)
    return match.group(1) if match else None


def supported_podway_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(r"v?0\.2\.(\d+)", version)
    return bool(match and int(match.group(1)) >= 3)


def supported_sanho_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(r"v?0\.2\.(\d+)", version)
    return bool(match and int(match.group(1)) >= 6)


def supported_gaori_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(r"v?0\.1\.(\d+)", version)
    return bool(match and int(match.group(1)) >= 12)


def supported_mulgae_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(r"v?0\.1\.(\d+)", version)
    return bool(match and int(match.group(1)) >= 15)


def supported_mulgae_go_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(r"go(\d+)\.(\d+)\.(\d+)", version)
    return bool(match and tuple(map(int, match.groups())) >= (1, 26, 6))


def file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
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
    return {
        "path": relative_path,
        "present": repository.joinpath(relative_path).exists(),
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
    result = probe.get("result")
    if isinstance(result, dict):
        error = result.get("error")
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            normalized["error_code"] = error["code"]
    if probe.get("error_code"):
        normalized["error_code"] = probe["error_code"]
    if probe.get("reason"):
        normalized["reason"] = probe["reason"]
    return normalized


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
    for name, fields in (
        ("relation", ("known", "behind", "ahead")),
        ("publication", ("known", "pending")),
        ("working_copy", ("known", "docs_clean")),
    ):
        selected = selected_fields(result.get(name), fields)
        if selected:
            safe[name] = selected
    preview = selected_fields(result.get("sync_preview"), ("known", "clean"))
    raw_preview = result.get("sync_preview")
    if isinstance(raw_preview, dict) and isinstance(raw_preview.get("conflicts"), list):
        preview["conflict_count"] = len(raw_preview["conflicts"])
    if preview:
        safe["sync_preview"] = preview
    readiness = result.get("local_readiness")
    if isinstance(readiness, dict):
        safe_readiness = {}
        for operation in ("sync", "pull"):
            selected = selected_fields(readiness.get(operation), ("ready", "blocked_by"))
            if selected:
                safe_readiness[operation] = selected
        if safe_readiness:
            safe["local_readiness"] = safe_readiness
    if isinstance(result.get("sync_in_progress"), bool):
        safe["sync_in_progress"] = result["sync_in_progress"]
    if safe:
        normalized["result"] = safe
    return normalized


def normalize_sanho_doctor(probe: dict[str, Any]) -> dict[str, Any]:
    normalized = normalized_probe(probe)
    result = probe.get("result")
    if not isinstance(result, dict) or isinstance(result.get("error"), dict):
        return normalized
    safe: dict[str, Any] = {}
    if isinstance(result.get("warnings"), int):
        safe["warnings"] = result["warnings"]
    checks = result.get("checks")
    if isinstance(checks, list):
        safe["checks"] = [
            selected_fields(check, ("name", "severity"))
            for check in checks
            if isinstance(check, dict)
        ]
    if safe:
        normalized["result"] = safe
    return normalized


def inspect_agent_skill(
    name: str, required_files: tuple[str, ...]
) -> dict[str, Any]:
    installations: list[dict[str, Any]] = []
    for root in skill_roots():
        directory = root / name
        if not directory.exists() and not directory.is_symlink():
            continue
        skill_path = directory / "SKILL.md"
        files = [
            {
                "path": relative_path,
                "present": (directory / relative_path).is_file(),
                "sha256": file_sha256(directory / relative_path),
            }
            for relative_path in required_files
        ]
        installations.append(
            {
                "path": str(directory),
                "frontmatter_valid": frontmatter_name(skill_path) == name,
                "files": files,
            }
        )
    if not installations:
        status = "missing"
    elif len(installations) == 1 and installations[0]["frontmatter_valid"] and all(
        entry["present"] for entry in installations[0]["files"]
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
        if isinstance(code, str):
            normalized["error_code"] = code
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
    tool["probes"]["version"] = version_probe
    tool["version"] = version_from_probe(version_probe)
    tool["version_supported"] = supported_sanho_version(tool["version"])
    if not version_probe["ok"] or not tool["version_supported"]:
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
    normalized_status = normalize_sanho_status(status_probe)
    normalized_doctor = normalize_sanho_doctor(doctor_probe)
    tool["probes"].update(
        {"status": normalized_status, "doctor": normalized_doctor}
    )
    doctor_result = normalized_doctor.get("result")
    no_doctor_warnings = (
        isinstance(doctor_result, dict) and doctor_result.get("warnings") == 0
    )
    tool["status"] = (
        "configured"
        if version_probe["ok"]
        and tool["version_supported"]
        and status_probe["ok"]
        and doctor_probe["ok"]
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
    if value["reason_code"] and re.fullmatch(
        r"[a-z][a-z0-9_]{0,63}", value["reason_code"]
    ) is None:
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
        cli_compatible = normalize_mulgae_cli_compatibility(
            row.get("cli_compatible")
        )
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
            or state not in {
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
        safe: dict[str, Any] = selected_fields(result, ("kind", "readiness"))
        if isinstance(doctor, dict):
            schema = doctor.get("schema_version")
            if isinstance(schema, str):
                normalized["result_schema"] = schema
            if schema != MULGAE_DOCTOR_RESULT_SCHEMA:
                normalized["doctor_capability"] = "unsupported"
                normalized["result"] = safe
                return normalized
            safe_doctor: dict[str, Any] = {"schema_version": schema}
            config = selected_fields(
                doctor.get("config"),
                (
                    "status",
                    "uri",
                    "locality",
                    "native_home_identity",
                    "provenance_state",
                    "reason_codes",
                ),
            )
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
            assignment = selected_fields(doctor.get("assignment"), ("state", "resilience"))
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
                    selected_fields(evidence, ("cell", "native"))
                    for evidence in platform_evidence
                    if isinstance(evidence, dict)
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
        if isinstance(version, str):
            prerequisite["go"]["version"] = version
            prerequisite["go"]["supported"] = supported_mulgae_go_version(version)
        normalized["result"] = selected_fields(
            result, ("GOVERSION", "GOOS", "GOARCH")
        )
    prerequisite["go"]["probe"] = normalized
    return prerequisite


def mulgae_configuration_entry(
    repository: Path, relative_path: str, timeout_seconds: float
) -> dict[str, Any]:
    entry = configuration_entry(repository, relative_path, timeout_seconds)
    entry["tracked"] = tracked_by_git(repository, relative_path, timeout_seconds)
    if relative_path == ".mulgae/local.yaml":
        try:
            entry["mode"] = oct(repository.joinpath(relative_path).stat().st_mode & 0o777)
        except OSError:
            entry["mode"] = None
        entry["mode_0600"] = entry["mode"] == "0o600"
    return entry


def inspect_mulgae_mcp(
    repository: Path, mulgae_executable: str | None, timeout_seconds: float
) -> dict[str, Any]:
    registration: dict[str, Any] = {
        "status": "missing",
        "project_config_present": repository.joinpath(".codex/config.toml").is_file(),
        "enabled": None,
        "stdio": None,
        "repository_bound": None,
        "arguments_match": None,
        "cwd_bound": None,
        "required": None,
        "required_verification": "unverifiable",
        "required_output_capability": "unknown",
        "compatibility_reason": None,
        "codex_version": None,
        "command_resolvable": None,
        "binary_matches_selected": None,
        "startup_timeout_sec": None,
        "tool_timeout_sec": None,
    }
    codex_executable = shutil.which("codex")
    if not codex_executable:
        registration.update(
            {"status": "unavailable", "reason": "codex_executable_missing"}
        )
        return registration
    version_probe = run_command(
        [codex_executable, "--version"], repository, timeout_seconds
    )
    if version_probe["ok"]:
        registration["codex_version"] = codex_version_from_output(
            version_probe["stdout"]
        )
    probe = json_probe(
        [codex_executable, "mcp", "get", "mulgae", "--json"],
        repository,
        timeout_seconds,
    )
    if not probe["ok"]:
        if probe["exit_code"] == 1 and not probe["timed_out"]:
            return registration
        if probe["timed_out"] or probe.get("error_code"):
            registration.update(
                {"status": "degraded", "reason": "registration_probe_failed"}
            )
        return registration
    result = probe.get("result")
    transport = result.get("transport") if isinstance(result, dict) else None
    if not isinstance(result, dict) or not isinstance(transport, dict):
        registration.update(
            {"status": "degraded", "reason": "invalid_registration_result"}
        )
        return registration

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
        registration.update(
            {
                "status": "degraded",
                "reason": "invalid_registration_result",
                "required_output_capability": "invalid",
            }
        )
        return registration

    command = transport.get("command")
    resolved_command: Path | None = None
    if isinstance(command, str) and command:
        candidate = Path(command).expanduser()
        if candidate.is_absolute() and candidate.is_file() and os.access(candidate, os.X_OK):
            resolved_command = candidate.resolve()
        elif not candidate.is_absolute():
            discovered = shutil.which(command)
            if discovered:
                resolved_command = Path(discovered).resolve()

    args = transport.get("args")
    repository_bound = False
    arguments_match = False
    if isinstance(args, list) and all(isinstance(argument, str) for argument in args):
        try:
            configured_root = Path(args[2]).expanduser().resolve()
            repository_bound = configured_root == repository
            arguments_match = (
                len(args) == 3
                and args[0] == "mcp"
                and args[1] == "--project-root"
                and repository_bound
            )
        except (IndexError, OSError):
            repository_bound = False

    raw_cwd = transport.get("cwd", result.get("cwd"))
    try:
        cwd_bound = isinstance(raw_cwd, str) and Path(raw_cwd).expanduser().resolve() == repository
    except OSError:
        cwd_bound = False
    startup_timeout = result.get("startup_timeout_sec")
    tool_timeout = result.get("tool_timeout_sec")
    startup_supported = (
        isinstance(startup_timeout, (int, float))
        and not isinstance(startup_timeout, bool)
        and startup_timeout >= 30
    )
    tool_supported = (
        isinstance(tool_timeout, (int, float))
        and not isinstance(tool_timeout, bool)
        and tool_timeout >= 54000
    )
    binary_matches = bool(
        resolved_command
        and mulgae_executable
        and resolved_command == Path(mulgae_executable).resolve()
    )
    registration.update(
        {
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
    )
    if (
        registration["project_config_present"]
        and registration["enabled"]
        and registration["stdio"]
        and arguments_match
        and cwd_bound
        and required_verification in {"verified", "unverifiable"}
        and binary_matches
        and startup_supported
        and tool_supported
    ):
        registration["status"] = "configured"
    else:
        registration.update(
            {"status": "degraded", "reason": "registration_mismatch"}
        )
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
    tool["probes"]["version"] = version_probe
    tool["version"] = version_from_probe(version_probe)
    tool["version_supported"] = supported_mulgae_version(tool["version"])
    doctor_probe = json_probe(
        [tool["executable"], "doctor", "--output", "json"],
        repository,
        timeout_seconds,
    )
    normalized_doctor = normalize_mulgae_doctor(doctor_probe)
    tool["probes"]["doctor"] = normalized_doctor

    project_config, local_config = tool["configuration"][:2]
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
    if mulgae_cli_compatible and doctor_supported and offline_ready and not mcp_blocks:
        tool["status"] = "configured"
    elif both_missing and mulgae_cli_compatible and doctor_supported and not mcp_blocks:
        tool["status"] = "installed"
    else:
        tool["status"] = "degraded"
    return tool


def inspect_gaori_mcp(
    repository: Path, gaori_executable: str | None, timeout_seconds: float
) -> dict[str, Any]:
    project_config = repository.joinpath(".codex/config.toml")
    project_config_present = project_config.is_file()
    registration: dict[str, Any] = {
        "status": "missing",
        "project_config_present": project_config_present,
        "enabled": None,
        "stdio": None,
        "repository_bound": None,
        "command_resolvable": None,
        "binary_matches_selected": None,
        "tool_timeout_sec": None,
    }
    codex_executable = shutil.which("codex")
    if not codex_executable:
        registration["status"] = "unavailable"
        registration["reason"] = "codex_executable_missing"
        return registration

    probe = json_probe(
        [codex_executable, "mcp", "get", "gaori", "--json"],
        repository,
        timeout_seconds,
    )
    if not probe["ok"]:
        if project_config_present:
            registration["status"] = "degraded"
            registration["reason"] = (
                "registration_probe_timed_out"
                if probe["timed_out"]
                else "project_registration_inactive_or_invalid"
            )
        return registration

    result = probe.get("result")
    if not isinstance(result, dict):
        registration.update(
            {"status": "degraded", "reason": "invalid_registration_result"}
        )
        return registration

    transport = result.get("transport")
    if not isinstance(transport, dict):
        registration.update(
            {"status": "degraded", "reason": "missing_registration_transport"}
        )
        return registration

    enabled = result.get("enabled") is True
    stdio = transport.get("type") == "stdio"
    command = transport.get("command")
    args = transport.get("args")
    resolved_command: Path | None = None
    if isinstance(command, str) and command:
        candidate = Path(command).expanduser()
        if (
            candidate.is_absolute()
            and candidate.is_file()
            and os.access(candidate, os.X_OK)
        ):
            resolved_command = candidate.resolve()
        elif not candidate.is_absolute():
            discovered = shutil.which(command)
            if discovered:
                resolved_command = Path(discovered).resolve()

    repository_bound = False
    server_mode = False
    if isinstance(args, list) and all(isinstance(argument, str) for argument in args):
        try:
            repo_index = args.index("--repo")
            configured_repository = Path(args[repo_index + 1]).expanduser().resolve()
            repository_bound = configured_repository == repository
        except (ValueError, IndexError, OSError):
            repository_bound = False
        server_mode = bool(args and args[-1] == "mcp")

    tool_timeout = result.get("tool_timeout_sec")
    timeout_supported = tool_timeout in (None, 60)
    binary_matches = bool(
        resolved_command
        and gaori_executable
        and resolved_command == Path(gaori_executable).resolve()
    )
    registration.update(
        {
            "enabled": enabled,
            "stdio": stdio,
            "repository_bound": repository_bound,
            "command_resolvable": resolved_command is not None,
            "binary_matches_selected": binary_matches,
            "tool_timeout_sec": tool_timeout,
        }
    )
    if (
        project_config_present
        and enabled
        and stdio
        and repository_bound
        and server_mode
        and resolved_command is not None
        and timeout_supported
    ):
        registration["status"] = "configured"
    else:
        registration["status"] = "degraded"
        registration["reason"] = "registration_mismatch"
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
    tool["probes"]["version"] = version_probe
    tool["version"] = version_from_probe(version_probe)
    tool["version_supported"] = supported_gaori_version(tool["version"])
    if not version_probe["ok"] or not tool["version_supported"]:
        tool["status"] = "degraded"
    if not tool["configuration"][0]["present"]:
        tool["probes"]["config_check"] = skipped_probe("configuration_missing")
        return tool
    config_probe = json_probe(
        [tool["executable"], "--json", "config", "check"],
        repository,
        timeout_seconds,
    )
    tool["probes"]["config_check"] = config_probe
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
    tool = base_tool("podway")
    tool["agent_skill"] = inspect_agent_skill("use-podway", PODWAY_SKILL_FILES)
    tool["platform"] = {
        "system": platform.system(),
        "machine": platform.machine(),
        "supported": platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"},
    }
    managed: list[dict[str, Any]] = []
    present_count = 0
    matching_count = 0
    tracked_count = 0
    for name in PODWAY_PROCEDURES:
        source = PODWAY_SOURCE_DIRECTORY / name
        target = repository / ".podway" / "procedures" / name
        relative_path = str(target.relative_to(repository))
        source_digest = file_sha256(source)
        target_digest = file_sha256(target)
        present = target.is_file()
        matching = (
            present and source_digest is not None and target_digest == source_digest
        )
        tracked = present and tracked_by_git(repository, relative_path, timeout_seconds)
        present_count += int(present)
        matching_count += int(matching)
        tracked_count += int(tracked)
        managed.append(
            {
                "path": relative_path,
                "present": present,
                "tracked": tracked,
                "source_sha256": source_digest,
                "installed_sha256": target_digest,
                "matches_source": matching,
            }
        )
    tool["configuration"] = [
        configuration_entry(repository, ".podway/config.yaml", timeout_seconds),
        configuration_entry(repository, ".podway/.gitignore", timeout_seconds),
        configuration_entry(repository, ".podway/runtime/", timeout_seconds),
    ]
    tool["managed_procedures"] = managed
    tool["readiness_status"] = (
        "not_configured" if present_count == 0 else "degraded"
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
        if present_count:
            tool["status"] = "degraded"
            tool["readiness_status"] = "degraded"
        return tool
    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = version_probe
    tool["version"] = version_from_probe(version_probe)
    tool["version_supported"] = supported_podway_version(tool["version"])

    daemon_probe = json_probe(
        [tool["executable"], "daemon", "status", "--json"],
        repository,
        timeout_seconds,
    )
    normalized_daemon, daemon_payload = normalize_podway_envelope(
        daemon_probe,
        "daemon.status",
        ("podway.daemon-status-result/v1",),
    )
    daemon_version = None
    daemon_reachable = False
    daemon_target = None
    if isinstance(daemon_payload, dict):
        daemon_version = daemon_payload.get("daemon_version")
        daemon_reachable = daemon_payload.get("reachable") is True
        daemon_target = daemon_payload.get("target")
        normalized_daemon["result"] = {
            key: daemon_payload[key]
            for key in (
                "installed",
                "loaded",
                "reachable",
                "status",
                "daemon_version",
                "target",
                "contract_manifest_schema",
                "contract_manifest_digest",
            )
            if key in daemon_payload
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
            ("podway.status-result/v2", "podway.compact-status-result/v2"),
        )
        if isinstance(doctor_payload, dict) and isinstance(
            doctor_payload.get("healthy"), bool
        ):
            normalized_doctor["result"] = {"healthy": doctor_payload["healthy"]}
        if isinstance(session_result, dict):
            procedure = session_result.get("procedure")
            session = session_result.get("session")
            current = session_result.get("current")
            node = current.get("node") if isinstance(current, dict) else None
            normalized_session["result"] = {
                "procedure": {
                    key: procedure[key]
                    for key in ("schema", "id", "version", "digest")
                    if isinstance(procedure, dict) and key in procedure
                },
                "goal_revision": session_result.get("goal_revision"),
                "session": {
                    key: session[key]
                    for key in ("id", "lifecycle", "revision")
                    if isinstance(session, dict) and key in session
                },
                "current_graph_node_id": (
                    node.get("graph_node_id")
                    if isinstance(node, dict)
                    else None
                ),
            }
        tool["probes"]["doctor"] = normalized_doctor
        tool["probes"]["session_status"] = normalized_session
        session_contract_ok = normalized_session["ok"] or normalized_session.get(
            "error_code"
        ) == "NO_ACTIVE_SESSION"
        tool["legacy_state_detected"] = any(
            probe.get("error_code") == "LEGACY_PROCEDURE_STATE_UNSUPPORTED"
            for probe in (normalized_doctor, normalized_session)
        )
    else:
        tool["probes"]["doctor"] = skipped_probe("workspace_not_initialized")
        tool["probes"]["session_status"] = skipped_probe(
            "workspace_not_initialized"
        )

    procedure_checks_ok = True
    if matching_count == len(PODWAY_PROCEDURES):
        for entry in managed:
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
                entry["check"]["valid"] = payload.get("valid")
                entry["check"]["digest"] = payload.get("digest")
            procedure_checks_ok = (
                procedure_checks_ok
                and normalized_check["ok"]
                and isinstance(payload, dict)
                and payload.get("valid") is True
            )

    doctor_ok = tool["probes"]["doctor"]["ok"] if initialized else True
    doctor_payload = tool["probes"]["doctor"].get("result") if initialized else None
    if isinstance(doctor_payload, dict) and doctor_payload.get("healthy") is False:
        doctor_ok = False
    healthy = (
        version_probe["ok"]
        and tool["version_supported"]
        and tool["platform"]["supported"]
        and normalized_daemon["ok"]
        and daemon_reachable
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
    }
    if include_podway:
        tools["podway"] = inspect_podway(repository, timeout_seconds)
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
        "--require-mulgae-mcp",
        action="store_true",
        help="Require an explicitly selected Mulgae MCP registration for status",
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
        emit(
            inspect(
                arguments.repository,
                arguments.timeout_seconds,
                include_podway=arguments.include_podway,
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
