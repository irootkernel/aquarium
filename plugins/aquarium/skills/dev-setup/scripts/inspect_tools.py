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
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as error:
    if error.name != "yaml":
        raise
    yaml = None  # type: ignore[assignment]

GLOBAL_SCRIPT_DIRECTORY = str(
    Path(__file__).resolve().parents[2] / "dev-setup-global/scripts"
)
if GLOBAL_SCRIPT_DIRECTORY not in sys.path:
    sys.path.insert(0, GLOBAL_SCRIPT_DIRECTORY)

try:
    import verify_dolgorae_release as dolgorae_release
except ModuleNotFoundError as error:
    if error.name != "verify_dolgorae_release":
        raise
    dolgorae_release = None

SCHEMA_VERSION = "aquarium-dev-setup-inspection.v21"
DOLGORAE_INVOCATION_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
MULGAE_COMMAND_RESULT_SCHEMA = "mulgae-command-result.v8"
MULGAE_DOCTOR_RESULT_SCHEMA = "mulgae-doctor-result.v2"
MULGAE_MCP_TOOL_TIMEOUT_SEC = 7501
GAORI_MCP_TOOL_TIMEOUT_SEC = 3601
MAX_COMMAND_TIMEOUT_SECONDS = 86_400.0
PODWAY_DAEMON_WAIT_SECONDS = 120.0
PODWAY_DAEMON_CALLER_TIMEOUT_SECONDS = 125.0
CONFLICT_STATUSES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}
CANONICAL_NUMERIC_COMPONENT = r"(?:0|[1-9][0-9]*)"
CANONICAL_SEMVER = re.compile(
    rf"v?{CANONICAL_NUMERIC_COMPONENT}\."
    rf"{CANONICAL_NUMERIC_COMPONENT}\."
    rf"{CANONICAL_NUMERIC_COMPONENT}(?:[-+][0-9A-Za-z.-]+)?"
)
SORAGE_ERROR_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
DOLGORAE_SKILL_FILES = (
    "SKILL.md",
    "references/configuration.md",
    "references/lifecycle.md",
    "references/recovery.md",
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
GAORI_STATUS_SKILL_FILES = ("SKILL.md",)
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
SORAGE_SKILL_FILES = ("SKILL.md",)
SORAGE_DOCTOR_CATALOG = (
    "home.permissions",
    "config.schema",
    "config.lock",
    "vault.marker",
    "vault.gitattributes",
    "vault.writable",
    "db.integrity",
    "db.pendingIntents",
    "db.migrations",
    "artifacts.checksums",
    "bindings.exist",
    "bindings.nested",
    "bindings.ambiguous",
    "daemon.reachable",
    "daemon.port",
    "token.permissions",
    "service.installed",
    "backup.schedule",
    "git.state",
    "platform.tcc",
)
HUMANIZER_SKILL_FILES = (
    "SKILL.md",
    "LICENSE",
)
HUMANIZER_SUPPORTED_RELEASE = "v2.11.1"
HUMANIZE_KOREAN_SKILL_FILES = (
    "SKILL.md",
    "LICENSE",
    "references/ai-tell-taxonomy.md",
    "references/baseline.json",
    "references/baseline_v2.json",
    "references/design-notes.md",
    "references/diagnosis-rules.md",
    "references/empirical-validation.md",
    "references/metrics.py",
    "references/metrics_v2.py",
    "references/quick-rules.footer.md",
    "references/quick-rules.header.md",
    "references/quick-rules.md",
    "references/rewriting-playbook.md",
    "references/scholarship.md",
    "references/web-service-spec.md",
)
IM_NOT_AI_SUPPORTED_RELEASE = "v2.3.2"
PODWAY_PROCEDURES = (
    "aquarium-task-v2.yaml",
    "aquarium-goal-v2.yaml",
    "aquarium-validation-v2.yaml",
    "aquarium-design-v2.yaml",
    "aquarium-war-room-v2.yaml",
)
PODWAY_PRIOR_CANONICAL_SHA256 = {
    "aquarium-task-v2.yaml": {
        "aa916a0e0dfa49384da1bb1affede4af58dd4dbc43e17f248d69537db6aeda52",
        "76fbe6842b178524d8c19ce17a58d1eb1fffa13dac07e9a9ae57fe98474194a6",
        "ff32214898ddb5a737e7a4c55447a16976d42da34b70cacc11c3b286d695cc77",
        "6bb336f321a83bba429c4173942eb977000014c627245839b3434da7d1055602",
        "c666f17cf41e8a9403f610f89b0b7397352d8ac6e2e5e05e1c268fc0e6ece3d9",
        "0ae730df9ca5854ff61b02679e3ac58aa4508ee35c5a09ba76c35e7d0ef3d45d",
        "b703da6c798801a396d144be1c9c71e0fdb05c95e9e293386bf83c0d238ef927",
        "35adb91998294f3c271e4ca7cba5ee1c8b94ce1265a828ff92cd206bc68d6e9c",
        "fb3d9a05dca7b09e34164b7a3022f0ab3fc2c742d1a3771064ac9174d0de43e7",
    },
    "aquarium-goal-v2.yaml": {
        "2921280e4a57e02896efb126abbd56829b6a2c99867d357ecc98413aadd15b7b",
        "5150a2ad3b33823a8935bd445155054bb0de037436c2d4121ae0892bd94e08c4",
        "f6d456438ba69a06fb322e4c2220bb824233c2ab239df1f68157c139ebb3a8c5",
        "7bf4460688335c1d1985fc1171313ac42ba7f82a64d8bc8733826a4fdd116e38",
        "90411e16758cb79a01294e008d9a091a52b341fc1e9bb968ce9521fed2910ec3",
        "8ca12a8ba36e9dd035bc70c903b8a5a0a9e4fd6db00cf75e2448f66082ab6ac6",
        "42eee85a406f46c3c7c40a467bfa1764d1e0b3042247b0604564ea20547f8d96",
        "97e73a08bb10167dc93da803ba899f19388affec000b4b3014a4e032ca57569b",
        "9ee8fb5c63ca3129e1a104c54c2e0dde0beb7939b70ab7da66431cde4ba490c7",
    },
    "aquarium-validation-v2.yaml": {
        "2d1e9995216ac4fcdf3b08baba80a31662485fc4daa3f0bfd42e4f1ff2f4c788",
        "423655c9d8b14c97820f36738c1ef32905bc26452113c69d886058f2bb54f8b3",
        "bc454955ef56d9607a9128a085177eb8557f8b24774cba59ddca3c0db88428e8",
        "45192a644087b811eb34952576798ae4f3e85ebdf87c77fc8dc097d3c8bb2f50",
        "9f3c0a0628f6ea820dbffee2355b949a2d2459e595ea3044d9aa53d81482eb5c",
        "53a20b71169bb206237474342f9c33f205e347f82686a7729b1c6447312523df",
        "aa89b01cd7007563861789304f11853e969fa0312676b8a256013dee808b7904",
    },
    "aquarium-design-v2.yaml": {
        "4ec653b2b4d740d77bcd4826f40288d9fadd7d696a3939c197b9789dbba824b6",
        "7582829afbb5c188c349e8f57c486a8de5eae2327e331680d7ccc09e1c6ecda8",
    },
    "aquarium-war-room-v2.yaml": {
        "ca9f2363107b315e829ba9f0357d35cbc242d07fbbf5a4702868bbb781dee1cb",
        "c8ce6585a735eb3a159a6f14f40d3dd413cc33812b254e10703c76b3d49dddd9",
    },
}

PODWAY_HANDLER_CONTRACTS = {
    "aquarium-task-v2.yaml": {
        "nodes": {
            "prepare-implementation",
            "implement",
            "document",
            "confirm-review-findings",
            "decide-review-ci",
            "confirm-review-completion",
            "decide-review",
            "decide-task-rework-authority",
            "decide-implementation-owner",
            "decide-verification-owner",
            "decide-documentation-owner",
            "await-user-direction",
            "choose-user-direction",
            "record-low-disposition",
            "decide-low-result",
            "decide-low-completion",
        },
        "definition_items": {
            "implementation-entry-record": {"implementation-entry-summary"},
            "review-record": {
                "finding-count-consistency",
                "completion-assessment-summary",
                "completion-unmet-criteria",
                "completion-unverified-criteria",
                "unresolved-implementation-findings",
                "unresolved-documentation-findings",
                "implementation-rework-obligations",
                "verification-rework-obligations",
                "documentation-rework-obligations",
            },
            "low-disposition-record": {
                "source-review-basis",
                "low-disposition-summary",
                "completion-assessment-summary",
                "completion-unmet-criteria",
                "completion-unverified-criteria",
                "pending-low-dispositions",
                "current-blocking-findings",
                "before-target",
                "after-target",
                "coverage-relationship",
                "low-disposition-verification",
            },
        },
        "definition_choices": {
            ("review-record", "finding-count-consistency"): {
                "consistent",
                "inconsistent",
            },
            ("review-record", "review-mode"): {
                "remediation-eligible",
                "confirmation-only",
            },
        },
        "routes": {
            "decide-verification": {"failed": "verify"},
            "decide-review-ci": {
                "passed": "confirm-review-completion",
                "failed": "decide-task-rework-authority",
            },
            "confirm-review-completion": {
                "complete": "decide-review",
                "unmet": "decide-task-rework-authority",
                "unverified": "review",
            },
            "decide-review": {
                "clean": "assess-goal",
                "blocking": "decide-task-rework-authority",
                "low-disposition": "record-low-disposition",
                "inconsistent": "review",
            },
            "decide-task-rework-authority": {
                "remediation": "decide-implementation-owner",
                "user-direction": "await-user-direction",
            },
            "decide-implementation-owner": {
                "required": "implement",
                "clear": "decide-verification-owner",
            },
            "decide-verification-owner": {
                "required": "verify",
                "clear": "decide-documentation-owner",
            },
            "decide-documentation-owner": {
                "required": "document",
                "clear": "review",
            },
            "decide-low-result": {"passed": "decide-low-completion"},
            "decide-low-completion": {"completed": "assess-goal"},
            "choose-user-direction": {
                "fix-and-review": "decide-implementation-owner",
                "stop": "assess-goal",
            },
        },
        "evidence": {
            "implement": {
                ("record-plan", "plan-summary"),
                ("prepare-implementation", "implementation-entry-summary"),
            },
            "document": {
                ("implement", "implementation-summary"),
                ("implement", "source-revision"),
                ("refine", "refinement-summary"),
                ("verify", "verification-result"),
                ("verify", "verification-observations"),
                ("decide-verification", None),
            },
            "await-user-direction": {
                ("review", "completion-assessment-summary"),
                ("review", "completion-unmet-criteria"),
                ("review", "completion-unverified-criteria"),
            },
            "assess-goal": {
                ("review", "completion-assessment-summary"),
                ("review", "completion-unmet-criteria"),
                ("review", "completion-unverified-criteria"),
                ("review", "finding-count-consistency"),
                ("await-user-direction", "direction-classification"),
                ("await-user-direction", "direction-summary"),
            },
        },
    },
    "aquarium-goal-v2.yaml": {
        "nodes": {
            "decide-review-basis",
            "decide-operational-evidence",
            "confirm-finding-validity",
            "confirm-completion-assessment",
            "decide-evidence",
            "decide-goal-rework-authority",
            "record-hardening-deferral",
            "decide-low-handling",
            "await-user-direction",
            "choose-user-direction",
            "record-low-disposition",
            "decide-low-result",
            "decide-low-completion",
        },
        "definition_items": {
            "evidence-record": {
                "finding-count-consistency",
                "goal-kind",
                "review-evidence-kind",
                "goal-verification-result",
                "goal-review-readiness-result",
                "confirmation-needed-findings",
                "completion-assessment-summary",
                "completion-unmet-criteria",
                "completion-unverified-criteria",
            },
            "low-disposition-record": {
                "source-review-basis",
                "completion-assessment-summary",
                "completion-unmet-criteria",
                "completion-unverified-criteria",
                "pending-low-dispositions",
                "current-blocking-findings",
                "before-target",
                "after-target",
                "coverage-relationship",
                "low-disposition-verification",
            },
        },
        "definition_choices": {
            ("evidence-record", "finding-count-consistency"): {
                "consistent",
                "inconsistent",
            },
            ("evidence-record", "goal-kind"): {
                "member-task",
                "pre-validation-remediation",
                "epic-closeout",
            },
            ("evidence-record", "review-evidence-kind"): {
                "native-review",
                "validated-closeout",
            },
            ("evidence-record", "review-mode"): {
                "remediation-eligible",
                "hardening-deferral-eligible",
                "closeout-not-required",
            },
        },
        "routes": {
            "decide-review-basis": {
                "native-review": "decide-operational-evidence",
                "final-closeout": "record-closeout-substitute",
                "invalid-substitute": "record-evidence",
            },
            "decide-operational-evidence": {
                "passed": "confirm-finding-validity",
                "verification-incomplete": "complete-work",
                "review-incomplete": "record-evidence",
            },
            "confirm-finding-validity": {
                "resolved": "confirm-completion-assessment",
                "unresolved": "record-evidence",
            },
            "confirm-completion-assessment": {
                "complete": "decide-evidence",
                "unmet": "decide-goal-rework-authority",
                "unverified": "record-evidence",
            },
            "decide-evidence": {
                "clean": "assess-goal",
                "blocking": "decide-goal-rework-authority",
                "low-only": "record-hardening-deferral",
                "inconsistent": "record-evidence",
            },
            "decide-goal-rework-authority": {
                "remediation": "complete-work",
                "user-direction": "await-user-direction",
            },
            "decide-low-handling": {
                "settle": "record-low-disposition",
                "defer": "record-hardening-handoff",
            },
            "decide-low-result": {"passed": "decide-low-completion"},
            "decide-low-completion": {"completed": "assess-goal"},
            "choose-user-direction": {
                "fix-and-review": "complete-work",
                "stop": "assess-goal",
            },
        },
        "evidence": {
            "await-user-direction": {
                ("record-evidence", "completion-assessment-summary"),
                ("record-evidence", "completion-unmet-criteria"),
                ("record-evidence", "completion-unverified-criteria"),
                ("record-low-disposition", "source-review-basis"),
                ("record-low-disposition", "low-disposition-summary"),
                ("record-low-disposition", "current-blocking-findings"),
                ("record-low-disposition", "after-target"),
            },
            "assess-goal": {
                ("record-evidence", "completion-assessment-summary"),
                ("record-evidence", "completion-unmet-criteria"),
                ("record-evidence", "completion-unverified-criteria"),
                ("record-evidence", "finding-count-consistency"),
                ("await-user-direction", "direction-classification"),
                ("await-user-direction", "direction-summary"),
            },
        },
    },
    "aquarium-validation-v2.yaml": {
        "nodes": {
            "record-audit-low-basis",
            "remediate",
            "re-audit",
            "decide-final-review-operation",
            "confirm-final-review-findings",
            "confirm-completion-assessment",
            "decide-required-evidence",
            "decide-current-blockers",
            "decide-validation-rework-authority",
            "decide-final-review",
            "await-user-direction",
            "choose-user-direction",
            "record-stopped",
            "record-low-disposition",
            "decide-low-result",
            "decide-low-completion",
        },
        "definition_items": {
            "audit-record": {
                "blocking-gap-count",
                "eligible-low-gap-count",
                "confirmation-needed-gap-count",
                "blocking-rework-authority",
            },
            "audit-low-basis-record": {
                "audit-basis-target",
                "audit-basis-status",
                "audit-low-finding-count",
                "audit-low-finding-identities",
                "audit-low-basis-summary",
            },
            "final-review-record": {
                "applicable-obligation-summary",
                "completion-assessment-summary",
                "completion-unmet-criteria",
                "completion-unverified-criteria",
                "pending-applicable-low-dispositions",
                "current-applicable-blockers",
                "required-evidence-gaps",
            },
            "low-disposition-record": {
                "source-review-basis",
                "completion-assessment-summary",
                "completion-unmet-criteria",
                "completion-unverified-criteria",
                "pending-low-dispositions",
                "current-blocking-findings",
                "before-target",
                "after-target",
                "coverage-relationship",
                "low-disposition-verification",
            },
        },
        "definition_choices": {
            ("final-review-record", "review-mode"): {
                "remediation-eligible",
                "confirmation-only",
            },
        },
        "routes": {
            "decide-gaps": {
                "blocking-gaps": "remediate",
                "low-only": "record-audit-low-basis",
                "user-direction": "await-user-direction",
            },
            "decide-re-audit": {
                "blocking-gaps": "remediate",
                "low-only": "record-audit-low-basis",
                "user-direction": "await-user-direction",
            },
            "decide-final-review-operation": {
                "passed": "confirm-final-review-findings",
                "incomplete": "record-review-operation-incomplete",
            },
            "confirm-final-review-findings": {
                "resolved": "confirm-completion-assessment",
                "unresolved": "record-incomplete",
            },
            "confirm-completion-assessment": {
                "complete": "decide-required-evidence",
                "unmet": "decide-validation-rework-authority",
                "unverified": "record-incomplete",
            },
            "decide-required-evidence": {
                "complete": "decide-current-blockers",
                "incomplete": "record-incomplete",
            },
            "decide-current-blockers": {
                "clear": "decide-final-review",
                "blocking": "decide-validation-rework-authority",
            },
            "decide-validation-rework-authority": {
                "remediation": "audit",
                "user-direction": "await-user-direction",
            },
            "choose-user-direction": {
                "fix-and-review": "audit",
                "stop": "record-stopped",
            },
            "decide-final-review": {
                "low-disposition": "record-low-disposition",
                "validated": "assess-goal",
            },
            "decide-low-result": {"passed": "decide-low-completion"},
            "decide-low-completion": {"completed": "assess-goal"},
        },
        "evidence": {
            "await-user-direction": {
                ("final-review", "completion-assessment-summary"),
                ("final-review", "completion-unmet-criteria"),
                ("final-review", "completion-unverified-criteria"),
                ("record-low-disposition", "source-review-basis"),
                ("record-low-disposition", "low-disposition-summary"),
                ("record-low-disposition", "current-blocking-findings"),
                ("record-low-disposition", "after-target"),
            },
            "assess-goal": {
                ("final-review", "completion-assessment-summary"),
                ("final-review", "completion-unmet-criteria"),
                ("final-review", "completion-unverified-criteria"),
                ("await-user-direction", "direction-classification"),
                ("await-user-direction", "direction-summary"),
            },
        },
    },
    "aquarium-design-v2.yaml": {},
    "aquarium-war-room-v2.yaml": {},
}
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
    rf"ouroboros-ai\[mcp\](?:==({CANONICAL_NUMERIC_COMPONENT}\.{CANONICAL_NUMERIC_COMPONENT}\.{CANONICAL_NUMERIC_COMPONENT}))?"
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
    input_text: str | None = None,
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
            input=input_text,
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
    return bool(match and int(match.group(1)) >= 9)


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


def podway_handler_structure(value: Any) -> Any:
    prose_keys = {
        "criteria",
        "description",
        "evidence_guidance",
        "help",
        "instructions",
        "intent",
        "label",
        "name",
        "objective",
        "prompt",
        "purpose",
        "title",
    }
    if isinstance(value, dict):
        return {
            key: podway_handler_structure(item)
            for key, item in value.items()
            if key not in prose_keys
        }
    if isinstance(value, list):
        return [podway_handler_structure(item) for item in value]
    return value


def podway_handler_shape_reasons(
    definitions: dict[Any, Any], raw_nodes: list[Any]
) -> list[str]:
    """Return bounded diagnostics for nested containers consumed below."""
    reasons: list[str] = []
    for definition_id, definition in definitions.items():
        if not isinstance(definition_id, str) or not isinstance(definition, dict):
            reasons.append(f"malformed_definition:{definition_id}")
            continue
        if "items" in definition:
            items = definition["items"]
            if not isinstance(items, list):
                reasons.append(f"malformed_items:{definition_id}")
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    reasons.append(f"malformed_item:{definition_id}:{index}")
                    continue
                if "choices" in item:
                    choices = item["choices"]
                    if not (
                        isinstance(choices, list)
                        and choices
                        and all(
                            isinstance(choice, str) and choice.strip()
                            for choice in choices
                        )
                    ):
                        item_id = item.get("id")
                        reasons.append(
                            f"malformed_choices:{definition_id}:{item_id or index}"
                        )

    for index, node in enumerate(raw_nodes):
        if not isinstance(node, dict):
            reasons.append(f"malformed_graph_node:{index}")
            continue
        node_id = node.get("id")
        node_label = node_id if isinstance(node_id, str) else str(index)
        if "evidence_from" not in node:
            continue
        evidence_from = node["evidence_from"]
        if not isinstance(evidence_from, list):
            reasons.append(f"malformed_evidence_from:{node_label}")
            continue
        for evidence_index, entry in enumerate(evidence_from):
            if not isinstance(entry, dict) or not isinstance(entry.get("node"), str):
                reasons.append(
                    f"malformed_evidence_source:{node_label}:{evidence_index}"
                )
                continue
            if "items" not in entry:
                continue
            selected_items = entry["items"]
            if not (
                isinstance(selected_items, list)
                and selected_items
                and all(
                    isinstance(item_id, str) and item_id.strip()
                    for item_id in selected_items
                )
            ):
                reasons.append(
                    f"malformed_evidence_items:{node_label}:{evidence_index}"
                )
    return reasons


def inspect_podway_handler_contract(
    name: str, content: bytes | None, canonical_content: bytes | None
) -> tuple[str, list[str]]:
    """Check only the structural Procedure surface consumed by Aquarium handlers."""
    if content is None:
        return "not_checked", ["procedure_bytes_unavailable"]
    if yaml is None:
        return "not_checked", ["pyyaml_unavailable"]
    try:
        document = yaml.safe_load(content)
    except (UnicodeDecodeError, yaml.YAMLError):
        return "not_checked", ["procedure_yaml_unreadable"]
    if not isinstance(document, dict):
        return "incompatible", ["procedure_document_invalid"]

    definitions = document.get("node_definitions")
    graph = document.get("graph")
    raw_nodes = graph.get("nodes") if isinstance(graph, dict) else None
    if not isinstance(definitions, dict) or not isinstance(raw_nodes, list):
        return "incompatible", ["procedure_structure_missing"]

    shape_reasons = podway_handler_shape_reasons(definitions, raw_nodes)
    if shape_reasons:
        return "incompatible", sorted(set(shape_reasons))

    nodes = {
        node.get("id"): node
        for node in raw_nodes
        if isinstance(node, dict) and isinstance(node.get("id"), str)
    }
    contract = PODWAY_HANDLER_CONTRACTS[name]
    reasons: list[str] = []
    missing_nodes = sorted(contract.get("nodes", set()) - nodes.keys())
    if missing_nodes:
        reasons.append("missing_required_nodes:" + ",".join(missing_nodes))

    for definition_id, required_items in contract.get("definition_items", {}).items():
        definition = definitions.get(definition_id)
        items = definition.get("items") if isinstance(definition, dict) else None
        present_items = {
            item.get("id")
            for item in items or []
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        missing_items = sorted(required_items - present_items)
        if missing_items:
            reasons.append(
                f"missing_required_items:{definition_id}:" + ",".join(missing_items)
            )

    for (definition_id, item_id), required_choices in contract.get(
        "definition_choices", {}
    ).items():
        definition = definitions.get(definition_id)
        items = definition.get("items") if isinstance(definition, dict) else None
        item = next(
            (
                candidate
                for candidate in items or []
                if isinstance(candidate, dict) and candidate.get("id") == item_id
            ),
            None,
        )
        observed_choices = (
            set(item.get("choices", [])) if isinstance(item, dict) else set()
        )
        if not required_choices.issubset(observed_choices):
            reasons.append(f"missing_required_choices:{definition_id}:{item_id}")

    for node_id, required_routes in contract.get("routes", {}).items():
        node = nodes.get(node_id)
        routes = node.get("routes") if isinstance(node, dict) else None
        for option, destination in required_routes.items():
            route = routes.get(option) if isinstance(routes, dict) else None
            if not isinstance(route, dict) or route.get("to") != destination:
                reasons.append(f"incompatible_route:{node_id}:{option}")

    for node_id, required_evidence in contract.get("evidence", {}).items():
        node = nodes.get(node_id)
        evidence_from = node.get("evidence_from") if isinstance(node, dict) else None
        observed_evidence = {
            (entry.get("node"), item)
            for entry in evidence_from or []
            if isinstance(entry, dict) and isinstance(entry.get("node"), str)
            for item in (entry.get("items") or [None])
        }
        missing_evidence = sorted(
            required_evidence - observed_evidence,
            key=lambda item: (item[0], item[1] or ""),
        )
        if missing_evidence:
            reasons.append(
                f"missing_required_evidence:{node_id}:"
                + ",".join(
                    f"{source}:{item or '*'}" for source, item in missing_evidence
                )
            )

    used_definitions = {
        node.get("use")
        for node in raw_nodes
        if isinstance(node, dict) and isinstance(node.get("use"), str)
    }
    missing_instructions = sorted(
        definition_id
        for definition_id in used_definitions
        if isinstance(definitions.get(definition_id), dict)
        and definitions[definition_id].get("type") == "action"
        and not (
            isinstance(definitions[definition_id].get("instructions"), list)
            and definitions[definition_id]["instructions"]
            and all(
                isinstance(instruction, str) and instruction.strip()
                for instruction in definitions[definition_id]["instructions"]
            )
        )
    )
    if missing_instructions:
        reasons.append("missing_action_instructions:" + ",".join(missing_instructions))

    if reasons:
        return "incompatible", reasons
    if canonical_content is None:
        return "not_checked", ["canonical_procedure_unavailable"]
    try:
        canonical = yaml.safe_load(canonical_content)
    except (UnicodeDecodeError, yaml.YAMLError):
        return "not_checked", ["canonical_procedure_unreadable"]
    if podway_handler_structure(document) != podway_handler_structure(canonical):
        return "unqualified", ["unrecognized_semantic_customization"]
    return "compatible", []


def supported_sanho_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.2\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 7)


def supported_dolgorae_version(version: str | None) -> bool:
    return bool(
        dolgorae_release
        and dolgorae_release.canonical_supported_tag(version) is not None
    )


def supported_gaori_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.1\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 16)


def supported_mulgae_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.1\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 21)


def supported_sorage_version(version: str | None) -> bool:
    if not version:
        return False
    match = re.fullmatch(rf"v?0\.1\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and int(match.group(1)) >= 1)


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
    match = re.fullmatch(rf"v?0\.(51|52|53)\.({CANONICAL_NUMERIC_COMPONENT})", version)
    return bool(match and (int(match.group(1)) > 51 or int(match.group(2)) >= 1))


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


def ignored_by_root_gitignore(
    repository: Path, relative_path: str, timeout_seconds: float
) -> bool:
    probe = run_command(
        ["git", "check-ignore", "--verbose", "--no-index", "-z", "--stdin"],
        repository,
        timeout_seconds,
        input_text=f"{relative_path}\0",
    )
    if not probe["ok"]:
        return False
    fields = probe["stdout"].split("\0")
    if len(fields) != 5 or fields[-1] or not fields[1].isdigit():
        return False
    source_text, _, pattern, pathname, _ = fields
    if pathname != relative_path or pattern.startswith("!"):
        return False
    source = Path(source_text)
    if not source.is_absolute():
        source = repository / source
    return os.path.normpath(source) == os.path.normpath(repository / ".gitignore")


def tracked_by_git(
    repository: Path, relative_path: str, timeout_seconds: float
) -> bool:
    probe = run_command(
        ["git", "ls-files", "--error-unmatch", "--", relative_path],
        repository,
        timeout_seconds,
    )
    return probe["exit_code"] == 0


def tracked_under_git(
    repository: Path, relative_path: str, timeout_seconds: float
) -> bool:
    probe = run_command(
        ["git", "ls-files", "--", relative_path], repository, timeout_seconds
    )
    return bool(probe["ok"] and probe.get("stdout", "").strip())


def untracked_under_git(
    repository: Path, relative_path: str, timeout_seconds: float
) -> bool:
    probe = run_command(
        ["git", "ls-files", "--others", "--exclude-standard", "--", relative_path],
        repository,
        timeout_seconds,
    )
    return bool(probe["ok"] and probe.get("stdout", "").strip())


def configuration_entry(
    repository: Path,
    relative_path: str,
    timeout_seconds: float,
    ignore_probe_path: str | None = None,
    ignored: bool | None = None,
) -> dict[str, Any]:
    path = repository.joinpath(relative_path)
    present, symlinked = safe_managed_file_state(path, repository)
    if relative_path.endswith("/") and not symlinked:
        present = path.is_dir()
    return {
        "path": relative_path,
        "present": present,
        "symlinked": symlinked,
        "ignored": (
            ignored
            if ignored is not None
            else ignored_by_git(
                repository, ignore_probe_path or relative_path, timeout_seconds
            )
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
    try:
        candidate = Path(command).expanduser()
        if candidate.is_absolute():
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate.resolve()
            return None
        discovered = shutil.which(command)
        return Path(discovered).resolve() if discovered else None
    except (OSError, ValueError, RuntimeError):
        return None


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
    if set(env) - (OUROBOROS_RUNTIME_SELECTOR_KEYS | {"CODEX_HOME"}):
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


def sorage_envelope_data(
    probe: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    normalized = normalized_probe(probe)
    envelope = probe.get("result")
    if not isinstance(envelope, dict) or not isinstance(envelope.get("ok"), bool):
        normalized["contract_valid"] = False
        return normalized, None
    if envelope["ok"] is False:
        error = envelope.get("error")
        code = error.get("code") if isinstance(error, dict) else None
        valid_code = isinstance(code, str) and bool(SORAGE_ERROR_CODE.fullmatch(code))
        normalized["contract_valid"] = valid_code
        normalized["error_code"] = code if valid_code else "invalid_error"
        return normalized, None
    data = envelope.get("data")
    normalized["contract_valid"] = isinstance(data, dict)
    return normalized, data if isinstance(data, dict) else None


def normalize_sorage_version(probe: dict[str, Any]) -> dict[str, Any]:
    normalized = normalized_probe(probe)
    result = probe.get("result")
    version = result.get("version") if isinstance(result, dict) else None
    normalized["contract_valid"] = bool(
        probe.get("ok")
        and isinstance(result, dict)
        and result.get("name") == "sorage"
        and isinstance(version, str)
        and CANONICAL_SEMVER.fullmatch(version)
    )
    if normalized["contract_valid"]:
        normalized["result"] = {"name": "sorage", "version": version}
    return normalized


def normalize_sorage_doctor(
    probe: dict[str, Any],
) -> tuple[dict[str, Any], bool | None, int | None]:
    normalized, data = sorage_envelope_data(probe)
    if data is None:
        return normalized, None, None
    checks = data.get("checks")
    if not isinstance(checks, list) or len(checks) != len(SORAGE_DOCTOR_CATALOG):
        normalized["contract_valid"] = False
        return normalized, None, None
    counts = {"ok": 0, "warning": 0, "blocking": 0}
    for expected_id, check in zip(SORAGE_DOCTOR_CATALOG, checks, strict=False):
        if not isinstance(check, dict):
            normalized["contract_valid"] = False
            return normalized, None, None
        check_id = check.get("id")
        severity = check.get("severity")
        message = check.get("message")
        recovery = check.get("recovery")
        if (
            check_id != expected_id
            or not isinstance(severity, str)
            or severity not in counts
            or not isinstance(message, str)
            or not message
            or (
                recovery is not None
                and (
                    not isinstance(recovery, dict)
                    or not isinstance(recovery.get("suggestedCommand"), str)
                    or not recovery["suggestedCommand"]
                )
            )
        ):
            normalized["contract_valid"] = False
            return normalized, None, None
        counts[severity] += 1
    not_initialized = all(
        check["severity"] == "blocking"
        and isinstance(check.get("recovery"), dict)
        and check["recovery"].get("suggestedCommand") == "sorage init"
        for check in checks
    )
    expected_exit_code = 1 if counts["blocking"] else 0
    if probe.get("timed_out") or probe.get("exit_code") != expected_exit_code:
        normalized["contract_valid"] = False
        return normalized, None, None
    normalized["contract_valid"] = True
    normalized["result"] = {
        "check_count": len(checks),
        "ok_count": counts["ok"],
        "warning_count": counts["warning"],
        "blocking_count": counts["blocking"],
    }
    return normalized, not not_initialized, counts["blocking"]


def valid_sorage_project_slug(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and value
        and value == value.lower()
        and not value.startswith("-")
        and not value.endswith("-")
        and all(character == "-" or character.isalnum() for character in value)
    )


def normalize_sorage_project_resolution(
    probe: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    normalized, data = sorage_envelope_data(probe)
    if data is None or not probe.get("ok"):
        if data is not None:
            normalized["contract_valid"] = False
        return normalized, None
    kind = data.get("kind")
    if kind == "unregistered_workspace":
        normalized["contract_valid"] = True
        normalized["result"] = {"kind": kind}
        return normalized, normalized["result"]
    if kind != "registered_project":
        normalized["contract_valid"] = False
        return normalized, None
    project = data.get("project")
    binding = data.get("binding")
    if not isinstance(project, dict) or not isinstance(binding, dict):
        normalized["contract_valid"] = False
        return normalized, None
    slug = project.get("slug")
    project_status = project.get("status")
    binding_kind = binding.get("bindingKind")
    if (
        not valid_sorage_project_slug(slug)
        or not isinstance(project_status, str)
        or project_status not in {"active", "archived"}
        or not isinstance(binding_kind, str)
        or binding_kind not in {"git_repository", "directory"}
    ):
        normalized["contract_valid"] = False
        return normalized, None
    result = {
        "kind": kind,
        "project_slug": slug,
        "project_status": project_status,
        "binding_kind": binding_kind,
    }
    normalized["contract_valid"] = True
    normalized["result"] = result
    return normalized, result


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


def agent_skill_ready(agent_skill: dict[str, Any]) -> bool:
    if agent_skill.get("verification_scope") == "presence_only":
        return agent_skill.get("present") is True
    return agent_skill.get("status") == "configured"


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


def normalize_podway_daemon_probe(
    daemon_probe: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized, payload = normalize_podway_envelope(
        daemon_probe,
        "daemon.wait-ready",
        ("podway.daemon-status-result/v3",),
    )
    daemon: dict[str, Any] = {
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
    }
    if not isinstance(payload, dict):
        return normalized, daemon

    observed_version = payload.get("daemon_version")
    if isinstance(observed_version, str) and re.fullmatch(
        r"v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", observed_version
    ):
        daemon["version"] = observed_version
    observed_target = payload.get("target")
    if observed_target in {"aarch64-apple-darwin", "x86_64-apple-darwin"}:
        daemon["target"] = observed_target
    daemon.update(
        {
            "installed": payload.get("installed") is True,
            "loaded": payload.get("loaded") is True,
            "reachable": payload.get("reachable") is True,
            "running": payload.get("status") == "running",
        }
    )

    observed_mode = payload.get("mode")
    daemon["mode"] = (
        observed_mode
        if isinstance(observed_mode, str)
        and len(observed_mode.encode("utf-8")) <= 64
        and re.fullmatch(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9]))*", observed_mode)
        else None
    )
    observed_state = payload.get("readiness_state")
    if observed_state in {
        "not_running",
        "unreachable",
        "starting",
        "recovering",
        "ready",
        "failed",
    }:
        daemon["readiness_state"] = observed_state
    observed_stage = payload.get("readiness_stage")
    if observed_stage in {
        "endpoint",
        "registry",
        "workspaces",
        "jobs",
        "ready",
        "failed",
    }:
        daemon["readiness_stage"] = observed_stage
    observed_elapsed = payload.get("readiness_elapsed_ms")
    if (
        isinstance(observed_elapsed, int)
        and not isinstance(observed_elapsed, bool)
        and observed_elapsed >= 0
    ):
        daemon["readiness_elapsed_ms"] = observed_elapsed
    observed_recovery = payload.get("worktree_recovery")
    if isinstance(observed_recovery, dict):
        recovery = {
            key: observed_recovery.get(key) for key in ("total", "completed", "failed")
        }
        if all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 10_000
            for value in recovery.values()
        ):
            daemon["worktree_recovery"] = recovery

    observed_clients = payload.get("in_flight_client_count")
    observed_maintenance = payload.get("maintenance_operation_count")
    activity_valid = bool(
        (
            observed_clients is None
            or isinstance(observed_clients, int)
            and not isinstance(observed_clients, bool)
            and 0 <= observed_clients <= 1024
        )
        and (
            observed_maintenance is None
            or isinstance(observed_maintenance, int)
            and not isinstance(observed_maintenance, bool)
            and 0 <= observed_maintenance <= 10_000
        )
    )
    if daemon["readiness_state"] in {"not_running", "unreachable"}:
        contract_valid = bool(
            daemon["mode"] == "prod"
            and observed_stage is None
            and observed_elapsed is None
            and observed_recovery is None
            and observed_clients is None
            and observed_maintenance is None
        )
    else:
        contract_valid = bool(
            daemon["mode"] == "prod"
            and daemon["readiness_state"] is not None
            and daemon["readiness_stage"] is not None
            and daemon["readiness_elapsed_ms"] is not None
            and daemon["worktree_recovery"] is not None
            and activity_valid
        )
    if not contract_valid:
        normalized["ok"] = False
        normalized["error_code"] = (
            "unsupported_daemon_mode"
            if daemon["mode"] is not None and daemon["mode"] != "prod"
            else "invalid_daemon_readiness"
        )
    recovery = daemon["worktree_recovery"]
    daemon["ready"] = bool(
        contract_valid
        and daemon["reachable"]
        and daemon["running"]
        and daemon["readiness_state"] == "ready"
        and daemon["readiness_stage"] == "ready"
        and isinstance(recovery, dict)
        and recovery["completed"] == recovery["total"]
    )
    normalized["result"] = {
        **daemon,
        "version_valid": daemon["version"] is not None,
        "target_supported": daemon["target"] is not None,
    }
    return normalized, daemon


def inspect_sanho(
    repository: Path,
    timeout_seconds: float,
    agent_skill: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tool = base_tool("sanho")
    tool["version_supported"] = False
    tool["agent_skill"] = (
        agent_skill if agent_skill is not None else inspect_sanho_skill()
    )
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


def valid_dolgorae_envelope(
    probe: dict[str, Any], raw_probe: dict[str, Any], command: str
) -> bool:
    envelope = probe.get("result")
    return bool(
        probe["ok"]
        and not raw_probe["stderr"]
        and isinstance(envelope, dict)
        and set(envelope)
        == {"schema_version", "ok", "command", "invocation_id", "data"}
        and type(envelope.get("schema_version")) is int
        and envelope["schema_version"] == 2
        and envelope.get("ok") is True
        and envelope.get("command") == command
        and isinstance(envelope.get("invocation_id"), str)
        and DOLGORAE_INVOCATION_ID_RE.fullmatch(envelope["invocation_id"])
    )


def dolgorae_capabilities_compatible(data: Any, version: str) -> bool:
    if not isinstance(data, dict):
        return False
    protocol_fields = (
        "machine_protocol_version",
        "event_protocol_version",
        "rpc_protocol_version",
        "timeline_protocol_version",
        "event_projection_version",
        "grpc_error_detail_version",
    )
    credential = data.get("controller_credential")
    bounds = data.get("artifact_bounds")
    lanes = data.get("lane_capabilities")
    shared = lanes.get("shared_readonly") if isinstance(lanes, dict) else None
    features = data.get("features")
    interactions = data.get("interactions")
    required_features = (
        "controller_binding",
        "operator_capability",
        "operator_controller_reset",
        "profile_diagnostics",
        "profile_membership_repair",
        "profile_server_migration",
        "worker_controller_revalidation",
    )
    return bool(
        data.get("dolgorae_version") == version
        and all(
            type(data.get(field)) is int and data[field] == 1
            for field in protocol_fields
        )
        and type(data.get("minimum_rpc_client_version")) is int
        and data.get("minimum_rpc_client_version") == 1
        and isinstance(data.get("maximum_rpc_client_version"), int)
        and not isinstance(data["maximum_rpc_client_version"], bool)
        and data["maximum_rpc_client_version"] >= 1
        and isinstance(data.get("rpc_descriptor_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", data["rpc_descriptor_sha256"])
        and data.get("controller_carrier_root") == "home/.dolgorae/controller-carriers"
        and isinstance(data.get("supported_transports"), list)
        and "machine_cli" in data["supported_transports"]
        and data.get("profile_launch_mode") == "dolgorae_owned_direct_executable"
        and isinstance(data.get("control_modes"), list)
        and "managed_agent" in data["control_modes"]
        and isinstance(data.get("execution_lanes"), list)
        and "shared_readonly" in data["execution_lanes"]
        and isinstance(shared, dict)
        and shared.get("writer_support") is False
        and shared.get("codex_mode") == "plan"
        and shared.get("command_execution") == "bounded_best_effort"
        and isinstance(credential, dict)
        and credential.get("schema_id")
        == "https://dolgorae.local/schema/controller-credential/v1"
        and type(credential.get("schema_version")) is int
        and credential.get("schema_version") == 1
        and isinstance(credential.get("schema_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", credential["schema_sha256"])
        and type(credential.get("capability_byte_length")) is int
        and credential.get("capability_byte_length") == 32
        and credential.get("capability_encoding") == "base64url_no_padding"
        and credential.get("same_uid") is True
        and credential.get("regular_file") is True
        and credential.get("symlinks") == "forbidden"
        and credential.get("create_exclusive") is True
        and type(credential.get("maximum_file_bytes")) is int
        and credential.get("maximum_file_bytes") == 4096
        and credential.get("client_descendant_pattern") == "<client>/<installation-id>/"
        and credential.get("normalized_principal")
        == "kind+subject_id_else_kind+instance_id"
        and type(credential.get("initial_generation")) is int
        and credential.get("initial_generation") == 1
        and isinstance(credential.get("accepted_kinds"), list)
        and "workflow_orchestrator" in credential["accepted_kinds"]
        and isinstance(bounds, dict)
        and bounds.get("digest") == "sha256"
        and bounds.get("exact_byte_length") is True
        and all(
            isinstance(bounds.get(field), int)
            and not isinstance(bounds[field], bool)
            and bounds[field] > 0
            for field in (
                "maximum_artifact_bytes",
                "maximum_chunk_bytes",
                "maximum_inline_response_bytes",
            )
        )
        and isinstance(bounds.get("visibility_classes"), list)
        and {"observer", "controller_only"}.issubset(bounds["visibility_classes"])
        and isinstance(features, dict)
        and all(features.get(field) is True for field in required_features)
        and isinstance(interactions, dict)
        and all(
            isinstance(interactions.get(field), int)
            and not isinstance(interactions[field], bool)
            and interactions[field] > 0
            for field in ("maximum_response_bytes", "maximum_safe_payload_bytes")
        )
    )


def is_arm64_macho(path: Path) -> bool:
    try:
        with path.open("rb") as executable:
            header = executable.read(16)
            return bool(
                header[:8] == b"\xcf\xfa\xed\xfe\x0c\x00\x00\x01"
                and header[12:16] == b"\x02\x00\x00\x00"
            )
    except OSError:
        return False


def inspect_dolgorae(
    repository: Path,
    timeout_seconds: float,
    verify_official_release: bool = False,
) -> dict[str, Any]:
    if dolgorae_release is None:
        raise RuntimeError("global Dolgorae release verifier is unavailable")
    discovered = shutil.which("dolgorae")
    tool = base_tool("dolgorae")
    tool["version_supported"] = False
    tool["platform"] = {
        "system": platform.system(),
        "machine": platform.machine(),
        "supported": platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"},
    }
    tool["symlinked"] = bool(discovered and Path(discovered).is_symlink())
    tool["regular_file"] = False
    tool["safe_location"] = False
    tool["arm64_macho"] = False
    tool["executable_sha256"] = None
    tool["official_executable"] = False
    tool["file_identity"] = None
    tool["identity_stable"] = False
    tool["capability_sha256"] = None
    tool["capabilities_compatible"] = False
    tool["release_verification"] = {
        "schema_version": dolgorae_release.SCHEMA_VERSION,
        "status": "not_requested",
    }

    def verify_release(version: str | None) -> dict[str, Any]:
        try:
            return dolgorae_release.verify_release(version, timeout_seconds)
        except dolgorae_release.ReleaseVerificationError as error:
            return dolgorae_release.failure_result(error)

    if not discovered:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        tool["probes"]["capabilities"] = skipped_probe("executable_missing")
        if verify_official_release:
            tool["release_verification"] = verify_release(None)
        return tool

    executable = Path(discovered)
    try:
        executable_stat = executable.stat()
        tool["regular_file"] = stat.S_ISREG(executable_stat.st_mode)
        resolved_executable = executable.resolve()
        home = Path.home().resolve()
        tool["safe_location"] = bool(
            executable.is_absolute()
            and not resolved_executable.is_relative_to(home / ".aquarium")
            and not resolved_executable.is_relative_to(home / ".aquarium-dev")
        )
        if (
            not tool["symlinked"]
            and tool["regular_file"]
            and tool["safe_location"]
            and os.access(executable, os.X_OK)
        ):
            digest = hashlib.sha256(executable.read_bytes()).hexdigest()
            tool["executable_sha256"] = digest
            tool["arm64_macho"] = is_arm64_macho(executable)
            tool["file_identity"] = {
                "device": executable_stat.st_dev,
                "inode": executable_stat.st_ino,
            }
    except OSError:
        pass

    if (
        tool["symlinked"]
        or not tool["regular_file"]
        or not tool["safe_location"]
        or not os.access(executable, os.X_OK)
    ):
        tool["probes"]["version"] = skipped_probe("executable_unsafe")
        tool["probes"]["capabilities"] = skipped_probe("executable_unsafe")
        if verify_official_release:
            tool["release_verification"] = verify_release(None)
        tool["status"] = "degraded"
        return tool

    raw_version_probe = run_command(
        [str(executable.resolve()), "version", "--json"], repository, timeout_seconds
    )
    version_probe = parse_json_probe(raw_version_probe)
    normalized_probe_result = normalized_probe(version_probe)
    version_result = version_probe.get("result")
    valid_envelope = bool(
        version_probe["ok"]
        and not raw_version_probe["stderr"]
        and isinstance(version_result, dict)
        and set(version_result) == {"name", "version"}
        and version_result.get("name") == "dolgorae"
        and isinstance(version_result.get("version"), str)
        and re.fullmatch(
            rf"v{CANONICAL_NUMERIC_COMPONENT}\.{CANONICAL_NUMERIC_COMPONENT}"
            rf"\.{CANONICAL_NUMERIC_COMPONENT}(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
            r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?",
            version_result["version"],
        )
    )
    if valid_envelope:
        tool["version"] = version_result["version"].removeprefix("v")
    if not valid_envelope:
        normalized_probe_result["ok"] = False
        if "error_code" not in normalized_probe_result:
            normalized_probe_result["error_code"] = "unexpected_version_envelope"
    tool["probes"]["version"] = normalized_probe_result
    tool["version_supported"] = supported_dolgorae_version(tool["version"])

    release = None
    if verify_official_release and tool["version_supported"]:
        tool["release_verification"] = verify_release(tool["version"])
        if tool["release_verification"]["status"] == "verified":
            release = tool["release_verification"]["release"]
            tool["official_executable"] = (
                tool["executable_sha256"] == release["executable_sha256"]
            )
    elif verify_official_release:
        version_unknown = tool["version"] is None
        tool["release_verification"] = dolgorae_release.failure_result(
            dolgorae_release.ReleaseVerificationError(
                "version_unknown" if version_unknown else "unsupported_version",
                (
                    "Dolgorae version could not be determined"
                    if version_unknown
                    else dolgorae_release.UNSUPPORTED_VERSION_MESSAGE
                ),
            )
        )

    raw_capabilities_probe = run_command(
        [str(executable.resolve()), "runtime", "capabilities"],
        repository,
        timeout_seconds,
    )
    capabilities_probe = parse_json_probe(raw_capabilities_probe)
    normalized_capabilities = normalized_probe(capabilities_probe)
    capability_envelope = capabilities_probe.get("result")
    capability_data = (
        capability_envelope.get("data")
        if isinstance(capability_envelope, dict)
        else None
    )
    valid_capabilities_envelope = valid_dolgorae_envelope(
        capabilities_probe, raw_capabilities_probe, "runtime.capabilities"
    )
    valid_capabilities = bool(
        tool["version"]
        and valid_capabilities_envelope
        and dolgorae_capabilities_compatible(capability_data, tool["version"])
    )
    if valid_capabilities:
        canonical = (
            json.dumps(capability_data, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
            + b"\n"
        )
        tool["capability_sha256"] = hashlib.sha256(canonical).hexdigest()
        tool["capabilities_compatible"] = True
    else:
        normalized_capabilities["ok"] = False
        if "error_code" not in normalized_capabilities:
            if not valid_capabilities_envelope:
                normalized_capabilities["error_code"] = (
                    "unexpected_capabilities_envelope"
                )
            elif not tool["version"]:
                normalized_capabilities["error_code"] = "version_unknown"
            else:
                normalized_capabilities["error_code"] = "incompatible_capabilities"
    tool["probes"]["capabilities"] = normalized_capabilities
    try:
        final_stat = executable.stat()
        initial_identity = tool["file_identity"]
        tool["identity_stable"] = bool(
            isinstance(initial_identity, dict)
            and final_stat.st_dev == initial_identity["device"]
            and final_stat.st_ino == initial_identity["inode"]
            and hashlib.sha256(executable.read_bytes()).hexdigest()
            == tool["executable_sha256"]
        )
    except OSError:
        tool["identity_stable"] = False
    if not tool["identity_stable"]:
        tool["official_executable"] = False
    tool["status"] = (
        "installed"
        if valid_envelope
        and tool["version_supported"]
        and tool["platform"]["supported"]
        and tool["arm64_macho"]
        and tool["official_executable"]
        and tool["identity_stable"]
        and valid_capabilities
        and release is not None
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
    repository: Path,
    timeout_seconds: float,
    environment_overrides: dict[str, str] | None = None,
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
        environment_overrides,
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
    return "continue_with_dev_setup_global"


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
    repository: Path,
    timeout_seconds: float,
    require_mcp: bool = False,
    agent_skill: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tool = base_tool("mulgae")
    tool["version_supported"] = False
    tool["platform"] = {
        "system": platform.system(),
        "machine": platform.machine(),
        "supported": platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"},
    }
    tool["agent_skill"] = (
        agent_skill
        if agent_skill is not None
        else inspect_agent_skill("use-mulgae", MULGAE_SKILL_FILES)
    )
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


def inspect_sorage(
    repository: Path,
    timeout_seconds: float,
    include_readiness: bool = False,
    agent_skill: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tool = base_tool("sorage")
    tool["version_supported"] = False
    tool["platform"] = {
        "system": platform.system(),
        "machine": platform.machine(),
        "supported": platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"},
    }
    tool["agent_skill"] = (
        agent_skill
        if agent_skill is not None
        else inspect_agent_skill("use-sorage", SORAGE_SKILL_FILES)
    )
    configuration = configuration_entry(
        repository,
        ".sorage/",
        timeout_seconds,
        ignored=ignored_by_root_gitignore(repository, ".sorage/", timeout_seconds),
    )
    configuration["tracked"] = tracked_under_git(repository, ".sorage", timeout_seconds)
    configuration["unignored"] = untracked_under_git(
        repository, ".sorage", timeout_seconds
    )
    configuration["tree_symlinked"] = managed_directory_tree_symlinked(
        repository / ".sorage", repository
    )
    tool["configuration"] = [configuration]
    tool["initialization_status"] = "not_applicable"
    tool["project_registration"] = {
        "status": "not_applicable",
        "project_slug": None,
        "project_status": None,
        "binding_kind": None,
    }
    tool["readiness_status"] = "not_applicable"
    if not tool["installed"]:
        tool["probes"]["version"] = skipped_probe("executable_missing")
        tool["probes"]["doctor"] = skipped_probe("executable_missing")
        tool["probes"]["project_resolve"] = skipped_probe("executable_missing")
        return tool

    version_probe = json_probe(
        [tool["executable"], "version", "--json"], repository, timeout_seconds
    )
    tool["probes"]["version"] = normalize_sorage_version(version_probe)
    version_result = version_probe.get("result")
    tool["version"] = (
        version_from_probe(version_probe)
        if isinstance(version_result, dict) and version_result.get("name") == "sorage"
        else None
    )
    tool["version_supported"] = supported_sorage_version(tool["version"])
    compatible = bool(
        version_probe["ok"]
        and tool["probes"]["version"]["contract_valid"]
        and tool["version_supported"]
        and tool["platform"]["supported"]
    )
    if not compatible:
        tool["probes"]["doctor"] = skipped_probe("unsupported_runtime")
        tool["probes"]["project_resolve"] = skipped_probe("unsupported_runtime")
        tool["status"] = "degraded"
        tool["readiness_status"] = "degraded"
        return tool

    if not include_readiness:
        tool["probes"]["doctor"] = skipped_probe("not_requested")
        tool["probes"]["project_resolve"] = skipped_probe("not_requested")
        tool["initialization_status"] = "not_inspected"
        tool["project_registration"]["status"] = "not_inspected"
        tool["readiness_status"] = "not_inspected"
        return tool

    doctor_probe = json_probe(
        [tool["executable"], "doctor", "--json"], repository, timeout_seconds
    )
    normalized_doctor, initialized, blocking_count = normalize_sorage_doctor(
        doctor_probe
    )
    tool["probes"]["doctor"] = normalized_doctor
    if initialized is False:
        tool["initialization_status"] = "not_initialized"
        tool["probes"]["project_resolve"] = skipped_probe("not_initialized")
        tool["project_registration"]["status"] = "not_inspected"
        tool["status"] = "installed"
        tool["readiness_status"] = "initialization_required"
        return tool
    if initialized is not True or blocking_count is None:
        tool["initialization_status"] = "unverifiable"
        tool["probes"]["project_resolve"] = skipped_probe("initialization_unverifiable")
        tool["project_registration"]["status"] = "not_inspected"
        tool["status"] = "degraded"
        tool["readiness_status"] = "degraded"
        return tool

    tool["initialization_status"] = "initialized"
    if blocking_count:
        tool["probes"]["project_resolve"] = skipped_probe("doctor_blocking")
        tool["project_registration"]["status"] = "not_inspected"
        tool["status"] = "degraded"
        tool["readiness_status"] = "degraded"
        return tool

    resolution_probe = json_probe(
        [
            tool["executable"],
            "project",
            "resolve",
            "--path",
            str(repository),
            "--json",
        ],
        repository,
        timeout_seconds,
    )
    normalized_resolution, resolution = normalize_sorage_project_resolution(
        resolution_probe
    )
    tool["probes"]["project_resolve"] = normalized_resolution
    if resolution is None:
        tool["project_registration"]["status"] = "unverifiable"
        if normalized_resolution.get("contract_valid"):
            tool["status"] = "installed"
            tool["readiness_status"] = "resolution_error"
        else:
            tool["status"] = "degraded"
            tool["readiness_status"] = "degraded"
        return tool
    if resolution["kind"] == "unregistered_workspace":
        tool["project_registration"]["status"] = "unregistered"
        tool["status"] = "installed"
        tool["readiness_status"] = "registration_required"
        return tool

    tool["project_registration"] = {
        "status": "registered",
        "project_slug": resolution["project_slug"],
        "project_status": resolution["project_status"],
        "binding_kind": resolution["binding_kind"],
    }
    ready = bool(
        resolution["project_status"] == "active"
        and resolution["binding_kind"] == "git_repository"
        and agent_skill_ready(tool["agent_skill"])
        and configuration["ignored"]
        and not configuration["tracked"]
        and not configuration["unignored"]
        and not configuration["symlinked"]
        and not configuration["tree_symlinked"]
    )
    tool["status"] = "configured" if ready else "installed"
    tool["readiness_status"] = "ready" if ready else "degraded"
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


def inspect_gaori(
    repository: Path,
    timeout_seconds: float,
    agent_skill: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tool = base_tool("gaori")
    tool["version_supported"] = False
    tool["agent_skill"] = (
        agent_skill
        if agent_skill is not None
        else inspect_agent_skill("use-gaori", GAORI_SKILL_FILES)
    )
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
        try:
            candidates.append(Path(codex_home).expanduser().joinpath("skills"))
        except (OSError, ValueError, RuntimeError):
            pass
    candidates.extend(
        [Path.home().joinpath(".codex/skills"), Path.home().joinpath(".agents/skills")]
    )
    roots: list[Path] = []
    for candidate in candidates:
        lexical = candidate if candidate.is_absolute() else Path.cwd() / candidate
        if lexical not in roots:
            roots.append(lexical)
    return roots


def effective_codex_skill_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    root = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return (root if root.is_absolute() else Path.cwd() / root) / "skills"


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


def frontmatter_version(skill_path: Path) -> str | None:
    try:
        content = skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", content, re.DOTALL)
    if not match:
        return None
    version_match = re.search(
        r"^(?:  )?version:\s*[\"']?([^\"'#\n]+?)[\"']?\s*$",
        match.group(1),
        re.MULTILINE,
    )
    return version_match.group(1).strip() if version_match else None


def unexpected_skill_entries(
    directory: Path, expected_files: tuple[str, ...]
) -> list[str]:
    expected_file_set = set(expected_files)
    expected_directories = {
        str(parent)
        for relative_path in expected_files
        for parent in Path(relative_path).parents
        if str(parent) != "."
    }
    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    unsafe_entries: set[str] = set()
    if directory.is_symlink() or not directory.is_dir():
        return ["<unsafe-or-unreadable>"]
    try:
        for root, directories, files in os.walk(directory, followlinks=False):
            root_path = Path(root)
            retained_directories = []
            for name in directories:
                path = root_path / name
                relative = str(path.relative_to(directory))
                if path.is_symlink():
                    unsafe_entries.add(relative)
                else:
                    actual_directories.add(relative)
                    retained_directories.append(name)
            directories[:] = retained_directories
            for name in files:
                path = root_path / name
                relative = str(path.relative_to(directory))
                if path.is_symlink():
                    unsafe_entries.add(relative)
                else:
                    actual_files.add(relative)
    except OSError:
        return ["<unsafe-or-unreadable>"]
    return sorted(
        unsafe_entries
        | (actual_files - expected_file_set)
        | (actual_directories - expected_directories)
    )


def inspect_writing_skill(
    *,
    skill_name: str,
    expected_files: tuple[str, ...],
    expected_target: Path | None,
    supported_release: str,
    require_version: bool,
) -> dict[str, Any]:
    agent_skill = inspect_agent_skill(skill_name, expected_files)
    for installation in agent_skill["installations"]:
        installation["unexpected_entries"] = (
            ["<unsafe-or-unreadable>"]
            if installation["symlinked"]
            else unexpected_skill_entries(Path(installation["path"]), expected_files)
        )
    structurally_ready = bool(
        agent_skill["status"] == "configured"
        and len(agent_skill["installations"]) == 1
        and Path(agent_skill["installations"][0]["path"]) == expected_target
        and all(
            not installation["unexpected_entries"]
            for installation in agent_skill["installations"]
        )
    )
    version = None
    if (
        len(agent_skill["installations"]) == 1
        and not agent_skill["installations"][0]["symlinked"]
    ):
        installation = agent_skill["installations"][0]
        skill_entry = next(
            entry for entry in installation["files"] if entry["path"] == "SKILL.md"
        )
        if skill_entry["present"] and not skill_entry["symlinked"]:
            version = frontmatter_version(Path(installation["path"]) / "SKILL.md")
    version_supported = (
        version == supported_release.removeprefix("v") if require_version else None
    )
    ready = structurally_ready and (version_supported is not False)
    return {
        "catalog_status": "active",
        "setup_supported": True,
        "installed": ready,
        "complete_tree_verified": False,
        "verification_scope": "structure_only",
        "expected_target": str(expected_target)
        if expected_target is not None
        else None,
        "supported_release": supported_release,
        "executable": None,
        "version": version,
        "version_supported": version_supported,
        "status": (
            "unverifiable"
            if ready or expected_target is None
            else ("missing" if agent_skill["status"] == "missing" else "degraded")
        ),
        "agent_skill": agent_skill,
        "configuration": [],
        "probes": {},
    }


def inspect_humanizer() -> dict[str, Any]:
    return inspect_writing_skill(
        skill_name="humanizer",
        expected_files=HUMANIZER_SKILL_FILES,
        expected_target=Path.home() / ".agents/skills/humanizer",
        supported_release=HUMANIZER_SUPPORTED_RELEASE,
        require_version=True,
    )


def inspect_im_not_ai() -> dict[str, Any]:
    try:
        target = Path.home() / ".agents/skills/humanize-korean"
    except (OSError, ValueError, RuntimeError):
        target = None
    result = inspect_writing_skill(
        skill_name="humanize-korean",
        expected_files=HUMANIZE_KOREAN_SKILL_FILES,
        expected_target=target,
        supported_release=IM_NOT_AI_SUPPORTED_RELEASE,
        require_version=False,
    )
    if target is None:
        result["reason"] = "home_resolution_failed"
    return result


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
        and skills[name]["installations"][0]["location"]
        == str(Path.home() / ".agents/skills" / name)
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
    expected_entries = {"SKILL.md", "LICENSE"}
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
                    "unexpected_entries": [],
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
        try:
            unexpected_entries = sorted(
                entry.name
                for entry in skill_directory.iterdir()
                if entry.name not in expected_entries
            )
        except OSError:
            unexpected_entries = ["<unreadable>"]
        installations.append(
            {
                "location": str(skill_directory),
                "skill_file_present": skill_file_present,
                "license_file_present": license_file_present,
                "frontmatter_valid": skill_file_present
                and frontmatter_name(skill_path) == name,
                "symlinked": symlinked,
                "unexpected_entries": unexpected_entries,
            }
        )

    ready = (
        len(installations) == 1
        and installations[0]["location"] == str(Path.home() / ".agents/skills/deslop")
        and installations[0]["skill_file_present"]
        and installations[0]["license_file_present"]
        and installations[0]["frontmatter_valid"]
        and not installations[0]["symlinked"]
        and not installations[0]["unexpected_entries"]
    )
    return {
        "catalog_status": "active",
        "setup_supported": True,
        "installed": ready,
        "complete_tree_verified": False,
        "verification_scope": "structure_only",
        "executable": None,
        "version": None,
        "status": "unverifiable"
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


def inspect_ouroboros_cli(repository: Path, timeout_seconds: float) -> dict[str, Any]:
    tool = base_tool("ooo")
    tool["version_supported"] = False
    tool["probes"]["version"] = skipped_probe("executable_missing")
    if tool["installed"]:
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
            key: version_raw[key]
            for key in ("attempted", "ok", "exit_code", "timed_out")
        }
    return tool


def inspect_ouroboros(
    repository: Path,
    timeout_seconds: float,
    *,
    codex_home: Path | None = None,
    cli_observation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tool = (
        dict(cli_observation)
        if cli_observation is not None
        else inspect_ouroboros_cli(repository, timeout_seconds)
    )
    tool["supported_range"] = ">=0.51.1,<0.54.0"
    environment = {"CODEX_HOME": str(codex_home)} if codex_home else None
    tool["home_binding"] = {
        "status": "unverifiable",
        "reason": "registration_unavailable",
    }
    tool["runtime_package"] = {"status": "unverifiable", "version": None}
    if codex_home is not None and codex_home.exists() and not codex_home.is_dir():
        reason = "home_not_a_directory"
        tool["status"] = "degraded"
        for key in ("codex_integration", "mcp_registration", "mcp_runtime"):
            tool[key] = {"status": "unverifiable", "probe": skipped_probe(reason)}
        tool["home_binding"] = {"status": "unverifiable", "reason": reason}
        tool["runtime_package"] = {
            "status": "unverifiable",
            "version": None,
            "reason": reason,
        }
        return tool
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
            environment_overrides=environment,
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
        if isinstance(registration_transport, dict):
            registered_env = registration_transport.get("env", {})
            registered_home = (
                registered_env.get("CODEX_HOME")
                if isinstance(registered_env, dict)
                else None
            )
            if codex_home is not None:
                if registered_home is None:
                    tool["home_binding"] = {
                        "status": "unverifiable",
                        "reason": "home_not_explicit",
                    }
                elif (
                    isinstance(registered_home, str)
                    and Path(registered_home).is_absolute()
                ):
                    try:
                        matches = (
                            Path(registered_home).resolve() == codex_home.resolve()
                        )
                        if not matches:
                            try:
                                matches = Path(registered_home).samefile(codex_home)
                            except FileNotFoundError:
                                matches = False
                        tool["home_binding"] = {
                            "status": "configured" if matches else "degraded",
                            "reason": "home_matches" if matches else "home_mismatch",
                        }
                    except (OSError, ValueError, RuntimeError):
                        tool["home_binding"] = {
                            "status": "degraded",
                            "reason": "home_invalid",
                        }
                else:
                    tool["home_binding"] = {
                        "status": "degraded",
                        "reason": "home_invalid",
                    }
            args = registration_transport.get("args", [])
            if isinstance(args, list) and len(args) > 4 and isinstance(args[4], str):
                package = OUROBOROS_MCP_PACKAGE.fullmatch(args[4])
                if package:
                    tool["runtime_package"] = {
                        "status": "pinned" if package.group(1) else "unverifiable",
                        "version": package.group(1),
                    }
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
        elif codex:
            registration_reason = (
                tool["mcp_registration"].get("probe", {}).get("reason")
            )
            runtime_reason = (
                "registration_not_supported_launcher"
                if registration_reason in {None, "registration_mismatch"}
                else registration_reason
            )
            tool["mcp_runtime"] = {
                "status": "unverifiable",
                "probe": skipped_probe(runtime_reason),
            }
        else:
            tool["mcp_runtime"] = {
                "status": "missing",
                "probe": skipped_probe("executable_missing"),
            }
        return tool

    codex_doctor = run_command(
        [tool["executable"], "codex", "doctor"],
        repository,
        timeout_seconds,
        environment_overrides=environment,
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
            environment_overrides=environment,
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

    if direct_runtime_configured:
        tool["runtime_package"] = {"status": "selected_cli", "version": tool["version"]}
    if (
        tool["runtime_package"]["status"] == "pinned"
        and tool["runtime_package"]["version"] != tool["version"]
    ):
        tool["runtime_package"]["status"] = "different"
    components_ready = (
        tool["version_supported"]
        and (codex_home is None or tool["home_binding"]["status"] == "configured")
        and tool["codex_integration"]["status"] == "configured"
        and tool["mcp_runtime"]["status"] == "configured"
        and tool["mcp_registration"]["status"] == "configured"
    )
    tool["status"] = "configured" if components_ready else "degraded"
    return tool


def inspect_podway(
    repository: Path,
    timeout_seconds: float,
    agent_skill: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tool = base_tool("podway")
    tool["agent_skill"] = (
        agent_skill
        if agent_skill is not None
        else inspect_agent_skill("use-podway", PODWAY_SKILL_FILES)
    )
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
            update_explanation = "unsafe"
        elif not present:
            source_state = "missing"
            update_explanation = "missing"
        elif not source_present:
            source_state = "unsafe"
            update_explanation = "unsafe"
        elif matching:
            source_state = "canonical"
            update_explanation = "current_canonical"
        elif target_digest in PODWAY_PRIOR_CANONICAL_SHA256[name]:
            source_state = "pending_validation"
            update_explanation = "prior_canonical"
        elif workaround is not None and target_bytes == workaround:
            source_state = "pending_validation"
            update_explanation = "podway_v0.2.5_workaround"
        else:
            source_state = "pending_validation"
            update_explanation = "local_customization"
        tracked = present and tracked_by_git(repository, relative_path, timeout_seconds)
        handler_contract_status, handler_contract_reasons = (
            inspect_podway_handler_contract(name, target_bytes, source_bytes)
        )
        present_count += int(present or symlinked)
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
                "update_explanation": update_explanation,
                "expected_procedure_id": Path(name).stem,
                "handler_contract_status": handler_contract_status,
                "handler_contract_reasons": handler_contract_reasons,
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
        for entry in managed:
            if entry["source_state"] in {"canonical", "pending_validation"}:
                entry["source_state"] = "unverifiable"
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
            f"{PODWAY_DAEMON_WAIT_SECONDS:g}s",
        ],
        repository,
        max(timeout_seconds, PODWAY_DAEMON_CALLER_TIMEOUT_SECONDS),
    )
    normalized_daemon, daemon = normalize_podway_daemon_probe(daemon_probe)
    daemon_version = daemon["version"]
    daemon_ready = daemon["ready"]
    daemon_target = daemon["target"]
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
                in {"prepared", "running", "completed", "cancelled", "discarded"}
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
                in {"prepared", "running", "completed", "cancelled", "discarded"}
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

    valid_managed_count = 0
    for entry in managed:
        if entry["source_state"] not in {"canonical", "pending_validation"}:
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
        check_valid = (
            normalized_check["ok"]
            and isinstance(payload, dict)
            and payload.get("valid") is True
        )
        preview_payload = None
        preview_valid = False
        if check_valid:
            preview = json_probe(
                [
                    tool["executable"],
                    "--json",
                    "procedure",
                    "preview",
                    entry["path"],
                ],
                repository,
                timeout_seconds,
            )
            normalized_preview, preview_payload = normalize_podway_envelope(
                preview,
                "procedure.preview",
                ("podway.procedure-preview-result/v1",),
            )
            entry["preview"] = normalized_preview
            if isinstance(preview_payload, dict):
                entry["preview"]["admissible"] = (
                    preview_payload.get("admissible") is True
                )
                procedure_id = preview_payload.get("procedure_id")
                entry["preview"]["procedure_id"] = (
                    procedure_id if isinstance(procedure_id, str) else None
                )
            preview_valid = (
                normalized_preview["ok"]
                and isinstance(preview_payload, dict)
                and preview_payload.get("admissible") is True
                and preview_payload.get("procedure_id")
                == entry["expected_procedure_id"]
            )
        check_rejected = isinstance(payload, dict) and payload.get("valid") is False
        preview_rejected = isinstance(preview_payload, dict) and (
            preview_payload.get("admissible") is False
            or isinstance(preview_payload.get("procedure_id"), str)
            and preview_payload["procedure_id"] != entry["expected_procedure_id"]
        )
        procedure_valid = check_valid and preview_valid
        if procedure_valid:
            entry["source_state"] = (
                "canonical" if entry["matches_source"] else "valid_customization"
            )
            if entry["handler_contract_status"] == "compatible":
                valid_managed_count += 1
        elif check_rejected or preview_rejected:
            entry["source_state"] = "invalid"
        else:
            entry["source_state"] = "unverifiable"

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
        valid_managed_count == len(PODWAY_PROCEDURES)
        and tracked_count == len(PODWAY_PROCEDURES)
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
    include_sorage: bool = False,
    require_mulgae_mcp: bool = False,
) -> dict[str, Any]:
    repository = resolve_repository(requested_path, timeout_seconds)
    trusted_global_skills = {
        name: {
            "canonical_path": str(path),
            "present": path.exists(),
            "verification_scope": "presence_only",
        }
        for name, path in {
            "use-sanho": Path.home() / ".agents/skills/use-sanho",
            "use-dolgorae": Path.home() / ".agents/skills/use-dolgorae",
            "use-mulgae": Path.home() / ".agents/skills/use-mulgae",
            "use-gaori": Path.home() / ".agents/skills/use-gaori",
            "use-gaori-status": Path.home() / ".agents/skills/use-gaori-status",
            "use-sorage": Path.home() / ".agents/skills/use-sorage",
            "use-podway": Path.home() / ".agents/skills/use-podway",
            "lore-commits": Path.home() / ".agents/skills/lore-commits",
            "lore-query": Path.home() / ".agents/skills/lore-query",
            "deslop": Path.home() / ".agents/skills/deslop",
            "humanizer": Path.home() / ".agents/skills/humanizer",
            "humanize-korean": Path.home() / ".agents/skills/humanize-korean",
        }.items()
    }
    tools = {
        "sanho": inspect_sanho(
            repository,
            timeout_seconds,
            agent_skill=trusted_global_skills.get("use-sanho"),
        ),
        "mulgae": inspect_mulgae(
            repository,
            timeout_seconds,
            require_mcp=require_mulgae_mcp,
            agent_skill=trusted_global_skills.get("use-mulgae"),
        ),
        "gaori": inspect_gaori(
            repository,
            timeout_seconds,
            agent_skill=trusted_global_skills.get("use-gaori"),
        ),
        "sorage": inspect_sorage(
            repository,
            timeout_seconds,
            include_readiness=include_sorage,
            agent_skill=trusted_global_skills.get("use-sorage"),
        ),
    }
    if include_podway:
        tools["podway"] = inspect_podway(
            repository,
            timeout_seconds,
            agent_skill=trusted_global_skills["use-podway"],
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": repository_inventory(repository, timeout_seconds),
        "trusted_global_skills": trusted_global_skills,
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
        "--include-sorage",
        action="store_true",
        help="Include explicitly selected Sorage readiness diagnostics",
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
                include_sorage=arguments.include_sorage,
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
