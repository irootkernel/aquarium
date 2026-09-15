#!/usr/bin/env python3
"""Inspect Aquarium user-global tool state without changing it."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

from inspect_ouroboros import InvalidCodexHome, inspect_ouroboros

SCHEMA_VERSION = "aquarium-dev-setup-global-inspection.v3"
GLOBAL_COMPONENTS = (
    "sanho",
    "dolgorae",
    "mulgae",
    "gaori",
    "sorage",
    "lora",
    "deslop",
    "humanizer",
    "im-not-ai",
    "podway",
    "ouroboros",
    "aquarium-dev",
)
PROJECT_INSPECTOR = (
    Path(__file__).resolve().parents[2] / "dev-setup/scripts/inspect_tools.py"
)


class InspectionError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InspectionError("invalid_arguments", "invalid command arguments")


def load_inspector() -> Any:
    if not PROJECT_INSPECTOR.is_file():
        raise InspectionError(
            "inspector_unavailable", "project inspector is unavailable"
        )
    spec = importlib.util.spec_from_file_location(
        "aquarium_project_tool_inspector", PROJECT_INSPECTOR
    )
    if spec is None or spec.loader is None:
        raise InspectionError(
            "inspector_unavailable", "project inspector is unavailable"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def cli_component(tool: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "status",
        "catalog_status",
        "setup_supported",
        "executable",
        "installed",
        "version",
        "version_supported",
        "platform",
    )
    component = {key: tool[key] for key in keys if key in tool}
    version_probe = tool.get("probes", {}).get("version")
    if version_probe is not None:
        component["version_probe"] = version_probe
    capabilities_probe = tool.get("probes", {}).get("capabilities")
    if capabilities_probe is not None:
        component["capabilities_probe"] = capabilities_probe
    return component


def inspect_canonical_agent_skill(
    inspector: Any, name: str, required_files: tuple[str, ...]
) -> dict[str, Any]:
    skill = inspector.inspect_agent_skill(name, required_files)
    canonical_path = Path.home() / ".agents/skills" / name
    canonical_installation = next(
        (
            installation
            for installation in skill.get("installations", [])
            if installation.get("path") == str(canonical_path)
        ),
        None,
    )
    skill["canonical_path"] = str(canonical_path)
    skill["canonical_present"] = canonical_installation is not None
    if skill.get("status") == "configured" and canonical_installation is None:
        skill["status"] = "degraded"
    return skill


def inspect_versioned_cli(
    inspector: Any,
    name: str,
    root: Path,
    timeout_seconds: float,
    version_arguments: list[str],
    supported: Any,
    *,
    platform_required: bool = False,
    normalizer: Any | None = None,
) -> dict[str, Any]:
    neutral_cwd = Path(root.anchor)
    tool = inspector.base_tool(name)
    tool["version_supported"] = False
    if platform_required:
        tool["platform"] = {
            "system": inspector.platform.system(),
            "machine": inspector.platform.machine(),
            "supported": inspector.platform.system() == "Darwin"
            and inspector.platform.machine() in {"arm64", "aarch64"},
        }
    if not tool["installed"]:
        tool["probes"]["version"] = inspector.skipped_probe("executable_missing")
        return tool
    probe = inspector.json_probe(
        [tool["executable"], *version_arguments], neutral_cwd, timeout_seconds
    )
    tool["probes"]["version"] = (
        normalizer(probe) if normalizer else inspector.normalized_probe(probe)
    )
    tool["version"] = inspector.version_from_probe(probe)
    tool["version_supported"] = supported(tool["version"])
    platform_ok = not platform_required or tool["platform"]["supported"]
    tool["status"] = (
        "installed"
        if probe["ok"] and tool["version_supported"] and platform_ok
        else "degraded"
    )
    return tool


def inspect_global_mcp(
    inspector: Any,
    name: str,
    executable: str | None,
    root: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    return inspector.inspect_global_mcp_scope(name, executable, root, timeout_seconds)


def inspect_global_podway(
    inspector: Any, root: Path, timeout_seconds: float
) -> dict[str, Any]:
    neutral_cwd = Path(root.anchor)
    tool = inspect_versioned_cli(
        inspector,
        "podway",
        neutral_cwd,
        timeout_seconds,
        ["version", "--json"],
        inspector.supported_podway_version,
        platform_required=True,
    )
    tool["agent_skill"] = inspect_canonical_agent_skill(
        inspector, "use-podway", inspector.PODWAY_SKILL_FILES
    )
    if not tool["installed"]:
        tool["daemon"] = {
            "installed": False,
            "loaded": False,
            "reachable": False,
            "running": False,
            "version": None,
            "target": None,
            "ready": False,
            "mode": None,
            "readiness_state": None,
            "readiness_stage": None,
            "readiness_elapsed_ms": None,
            "worktree_recovery": None,
            "status": "missing",
            "versions_match": False,
            "probe": inspector.skipped_probe("executable_missing"),
        }
        return tool
    daemon_probe = inspector.json_probe(
        [
            tool["executable"],
            "--json",
            "daemon",
            "wait-ready",
            "--timeout",
            f"{inspector.PODWAY_DAEMON_WAIT_SECONDS:g}s",
        ],
        neutral_cwd,
        max(timeout_seconds, inspector.PODWAY_DAEMON_CALLER_TIMEOUT_SECONDS),
    )
    normalized, daemon = inspector.normalize_podway_daemon_probe(daemon_probe)
    versions_match = bool(
        tool.get("version")
        and daemon["version"]
        and inspector.normalized_version(tool["version"])
        == inspector.normalized_version(daemon["version"])
    )
    configured = bool(
        normalized["ok"]
        and daemon["ready"]
        and daemon["target"] == "aarch64-apple-darwin"
        and versions_match
    )
    tool["daemon"] = {
        **daemon,
        "status": "configured" if configured else "degraded",
        "versions_match": versions_match,
        "probe": normalized,
    }
    return tool


def inspect_global_sorage(
    inspector: Any,
    root: Path,
    timeout_seconds: float,
    include_initialization: bool,
) -> dict[str, Any]:
    neutral_cwd = Path(root.anchor)
    tool = inspect_versioned_cli(
        inspector,
        "sorage",
        neutral_cwd,
        timeout_seconds,
        ["version", "--json"],
        inspector.supported_sorage_version,
        platform_required=True,
        normalizer=inspector.normalize_sorage_version,
    )
    if tool["installed"] and not tool["probes"]["version"].get("contract_valid"):
        tool["version"] = None
        tool["version_supported"] = False
        tool["status"] = "degraded"
    tool["initialization_status"] = "not_applicable"
    if not tool["installed"] or tool["status"] == "degraded":
        tool["probes"]["doctor"] = inspector.skipped_probe(
            "executable_missing" if not tool["installed"] else "unsupported_runtime"
        )
        return tool
    if not include_initialization:
        tool["initialization_status"] = "not_inspected"
        tool["probes"]["doctor"] = inspector.skipped_probe("not_requested")
        return tool
    doctor_probe = inspector.json_probe(
        [tool["executable"], "doctor", "--json"], neutral_cwd, timeout_seconds
    )
    normalized, initialized, blocking_count = inspector.normalize_sorage_doctor(
        doctor_probe
    )
    tool["probes"]["doctor"] = normalized
    if initialized is False:
        tool["initialization_status"] = "not_initialized"
    elif initialized is True and blocking_count == 0:
        tool["initialization_status"] = "initialized"
    else:
        tool["initialization_status"] = "unverifiable"
        tool["status"] = "degraded"
    return tool


def resolve_working_directory(requested_path: str | None) -> Path:
    try:
        working_directory = (
            Path(requested_path).expanduser() if requested_path else Path.cwd()
        ).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise InspectionError(
            "invalid_working_directory", "working directory is unavailable"
        ) from error
    if not working_directory.is_dir():
        raise InspectionError(
            "invalid_working_directory", "working directory must be a directory"
        )
    return working_directory


def inspect_global(
    repository: str | None,
    timeout_seconds: float,
    verify_dolgorae_release: bool,
    include_sorage_initialization: bool = False,
    components: tuple[str, ...] | None = None,
    codex_homes: tuple[str, ...] = (),
    verify_ouroboros_release: bool = False,
) -> dict[str, Any]:
    inspector = load_inspector()
    root = resolve_working_directory(repository)
    neutral_cwd = Path(root.anchor)
    requested_components = set(components or GLOBAL_COMPONENTS)
    selected_components = tuple(
        name for name in GLOBAL_COMPONENTS if name in requested_components
    )
    raw_tools: dict[str, dict[str, Any]] = {}
    if "sanho" in requested_components:
        raw_tools["sanho"] = inspect_versioned_cli(
            inspector,
            "sanho",
            neutral_cwd,
            timeout_seconds,
            ["version", "--json"],
            inspector.supported_sanho_version,
        )
    if "dolgorae" in requested_components:
        raw_tools["dolgorae"] = inspector.inspect_dolgorae(
            neutral_cwd,
            timeout_seconds,
            verify_official_release=verify_dolgorae_release,
        )
    if "mulgae" in requested_components:
        raw_tools["mulgae"] = inspect_versioned_cli(
            inspector,
            "mulgae",
            neutral_cwd,
            timeout_seconds,
            ["version", "--json"],
            inspector.supported_mulgae_version,
            platform_required=True,
        )
    if "gaori" in requested_components:
        raw_tools["gaori"] = inspect_versioned_cli(
            inspector,
            "gaori",
            neutral_cwd,
            timeout_seconds,
            ["version", "--json"],
            inspector.supported_gaori_version,
        )
    if "sorage" in requested_components:
        raw_tools["sorage"] = inspect_global_sorage(
            inspector,
            root,
            timeout_seconds,
            include_sorage_initialization,
        )
    if "podway" in requested_components:
        raw_tools["podway"] = inspect_global_podway(inspector, root, timeout_seconds)
    skill_specs = {
        "sanho": ("use-sanho", inspector.SANHO_SKILL_FILES),
        "dolgorae": ("use-dolgorae", inspector.DOLGORAE_SKILL_FILES),
        "mulgae": ("use-mulgae", inspector.MULGAE_SKILL_FILES),
        "gaori": ("use-gaori", inspector.GAORI_SKILL_FILES),
        "sorage": ("use-sorage", inspector.SORAGE_SKILL_FILES),
    }
    for name, (skill_name, files) in skill_specs.items():
        if name not in raw_tools:
            continue
        raw_tools[name]["agent_skill"] = inspect_canonical_agent_skill(
            inspector, skill_name, files
        )
    if "gaori" in raw_tools:
        raw_tools["gaori"]["status_skill"] = inspect_canonical_agent_skill(
            inspector, "use-gaori-status", inspector.GAORI_STATUS_SKILL_FILES
        )
    if "mulgae" in raw_tools:
        raw_tools["mulgae"]["installation_prerequisites"] = (
            inspector.inspect_mulgae_installation_prerequisites(
                neutral_cwd,
                timeout_seconds,
                environment_overrides={"GOTOOLCHAIN": "local"},
            )
        )
    for name in ("mulgae", "gaori"):
        if name not in raw_tools:
            continue
        raw_tools[name]["global_mcp"] = inspect_global_mcp(
            inspector,
            name,
            raw_tools[name]["executable"],
            root,
            timeout_seconds,
        )
    tools: dict[str, Any] = {}
    for name, raw in raw_tools.items():
        entry: dict[str, Any] = {"cli": cli_component(raw)}
        if "agent_skill" in raw:
            entry["paired_skill"] = raw["agent_skill"]
        if "status_skill" in raw:
            entry["status_skill"] = raw["status_skill"]
        if "global_mcp" in raw:
            entry["global_mcp"] = raw["global_mcp"]
        if "installation_prerequisites" in raw:
            entry["installation_prerequisites"] = raw["installation_prerequisites"]
        if name == "dolgorae":
            for key in (
                "status",
                "arm64_macho",
                "capabilities_compatible",
                "capability_sha256",
                "executable_sha256",
                "file_identity",
                "identity_stable",
                "official_executable",
                "regular_file",
                "release_verification",
                "safe_location",
                "symlinked",
            ):
                if key in raw:
                    entry[key] = raw[key]
        if name == "podway":
            entry["daemon"] = raw["daemon"]
        if name == "sorage":
            entry["initialization_status"] = raw.get("initialization_status")
            entry["initialization_probe"] = raw["probes"]["doctor"]
        tools[name] = entry

    if "ouroboros" in requested_components:
        try:
            tools["ouroboros"] = inspect_ouroboros(
                inspector,
                neutral_cwd,
                timeout_seconds,
                codex_homes,
                verify_ouroboros_release,
            )
        except InvalidCodexHome as error:
            raise InspectionError(
                "invalid_codex_home", "Codex home is unavailable or invalid"
            ) from error
    if "lora" in requested_components:
        tools["lora"] = inspector.inspect_lora()
    if "deslop" in requested_components:
        tools["deslop"] = inspector.inspect_deslop()
    if "humanizer" in requested_components:
        tools["humanizer"] = inspector.inspect_humanizer()
    if "im-not-ai" in requested_components:
        tools["im-not-ai"] = inspector.inspect_im_not_ai()
    if "aquarium-dev" in requested_components:
        script = Path(__file__).resolve().parents[3] / "tools/aquarium-dev/install.py"
        try:
            probe = subprocess.run(
                [sys.executable, "-B", str(script), "diagnose"],
                cwd=neutral_cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            if probe.returncode:
                failure = {
                    "status": "unverifiable",
                    "reason": "probe_failed",
                    "exit_code": probe.returncode,
                    "problem": probe.stderr.strip(),
                }
                try:
                    failure["diagnostic"] = json.loads(probe.stderr)
                except ValueError:
                    pass
                tools["aquarium-dev"] = failure
            else:
                tools["aquarium-dev"] = json.loads(probe.stdout)
        except subprocess.TimeoutExpired as error:
            tools["aquarium-dev"] = {
                "status": "unverifiable",
                "reason": "probe_timeout",
                "timeout_seconds": timeout_seconds,
                "problem": str(error),
            }
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            tools["aquarium-dev"] = {
                "status": "unverifiable",
                "reason": "invalid_json"
                if isinstance(error, ValueError)
                else "probe_failed",
                "problem": str(error),
            }
    tools = {name: tools[name] for name in selected_components}
    return {
        "schema_version": SCHEMA_VERSION,
        "inspection_scope": "user_global",
        "tools": tools,
    }


def parse_arguments() -> argparse.Namespace:
    max_command_timeout_seconds = load_inspector().MAX_COMMAND_TIMEOUT_SECONDS
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        help="Existing directory used only as a safe command working directory",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="Timeout for each ordinary read-only command; Podway readiness uses its fixed catalog wait",
    )
    parser.add_argument(
        "--component",
        action="append",
        choices=GLOBAL_COMPONENTS,
        help="Inspect only this user-global component; repeat to select more",
    )
    parser.add_argument(
        "--verify-dolgorae-release",
        action="store_true",
        help="Verify Dolgorae against bounded official GitHub Release metadata",
    )
    parser.add_argument(
        "--include-sorage-initialization",
        action="store_true",
        help="Include the selected local Sorage initialization diagnostic",
    )
    parser.add_argument(
        "--codex-home",
        action="append",
        default=[],
        help="Additional Ouroboros Codex home to inspect; repeat for multiple homes",
    )
    parser.add_argument(
        "--verify-ouroboros-release",
        action="store_true",
        help="Compare Ouroboros with official PyPI stable releases",
    )
    arguments = parser.parse_args()
    if (
        not math.isfinite(arguments.timeout_seconds)
        or arguments.timeout_seconds <= 0
        or arguments.timeout_seconds > max_command_timeout_seconds
    ):
        raise InspectionError(
            "invalid_arguments",
            "--timeout-seconds is outside the supported range",
        )
    if any(not value.strip() for value in arguments.codex_home):
        raise InspectionError("invalid_arguments", "--codex-home must not be blank")
    selected_components = set(arguments.component or GLOBAL_COMPONENTS)
    if arguments.verify_dolgorae_release and "dolgorae" not in selected_components:
        raise InspectionError(
            "invalid_arguments",
            "--verify-dolgorae-release requires the dolgorae component",
        )
    if arguments.include_sorage_initialization and "sorage" not in selected_components:
        raise InspectionError(
            "invalid_arguments",
            "--include-sorage-initialization requires the sorage component",
        )
    if (
        arguments.codex_home or arguments.verify_ouroboros_release
    ) and "ouroboros" not in selected_components:
        raise InspectionError(
            "invalid_arguments", "Ouroboros options require the ouroboros component"
        )
    arguments.component = tuple(
        name for name in GLOBAL_COMPONENTS if name in selected_components
    )
    return arguments


def emit(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def main() -> int:
    try:
        arguments = parse_arguments()
        emit(
            inspect_global(
                arguments.repository,
                arguments.timeout_seconds,
                arguments.verify_dolgorae_release,
                arguments.include_sorage_initialization,
                arguments.component,
                tuple(arguments.codex_home),
                arguments.verify_ouroboros_release,
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
                    "message": "unexpected global inspection failure",
                    "type": type(error).__name__,
                },
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
