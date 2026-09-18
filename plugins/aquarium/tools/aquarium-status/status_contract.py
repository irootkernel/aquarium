"""Closed validation and canonicalization for aquarium-status."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

LEDGER_SCHEMA = "aquarium-production-status/v1"
RECORD_SCHEMA = "aquarium-production-status-record/v1"
RECORD_RECEIPT_SCHEMA = "aquarium-production-status-record-receipt/v1"
REPORT_SCHEMA = "aquarium-production-status-report/v1"
FORGET_RECEIPT_SCHEMA = "aquarium-production-status-forget-receipt/v1"
ERROR_SCHEMA = "aquarium-production-status-error/v1"
VERSION_RE = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMPONENTS = frozenset(
    {
        "sanho",
        "dolgorae",
        "mulgae",
        "gaori",
        "sorage",
        "podway",
        "ouroboros",
        "lora",
        "deslop",
        "humanizer",
        "im-not-ai",
        "aquarium-dev",
        "agents-guidance",
    }
)
RECORDABLE_COMPONENTS = frozenset({"sanho", "aquarium_dev"})
VERSION_SOURCES = frozenset(
    {
        "bundled_plugin_manifest",
        "installed_runtime_receipt",
        "recorded_attempt",
        "official_github_release",
        "source_root_manifest",
        "source_root_changelog",
        "not_requested",
        "unavailable",
    }
)
OUTCOMES = frozenset({"ready", "partial", "failed", "declined"})
COMPONENT_OUTCOMES = OUTCOMES | {"unknown"}
RECORD_KEYS = frozenset(
    {
        "schema",
        "attempt_id",
        "expected_row_revision",
        "git_root",
        "project",
        "started_at",
        "completed_at",
        "outcome",
        "scope",
        "components",
    }
)


class ContractError(ValueError):
    """One closed public contract was not satisfied."""

    def __init__(self, code: str, message: str, exit_code: int = 2):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def exact_object(
    value: Any, keys: set[str] | frozenset[str], label: str
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ContractError("invalid_input", f"{label} has an invalid shape")
    return value


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            normalize_strings(value),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def normalize_strings(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize_strings(item) for item in value]
    if isinstance(value, dict):
        return {
            normalize_strings(key): normalize_strings(item)
            for key, item in value.items()
        }
    return value


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def validate_uuid4(value: Any) -> str:
    if not isinstance(value, str):
        raise ContractError("invalid_input", "attempt_id must be a UUIDv4 string")
    try:
        parsed = uuid.UUID(value)
    except ValueError as error:
        raise ContractError(
            "invalid_input", "attempt_id must be a UUIDv4 string"
        ) from error
    if parsed.version != 4 or str(parsed) != value:
        raise ContractError(
            "invalid_input", "attempt_id must be a canonical lowercase UUIDv4"
        )
    return value


def parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractError(
            "invalid_input", f"{label} must be a UTC RFC 3339 timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ContractError(
            "invalid_input", f"{label} must be a UTC RFC 3339 timestamp"
        ) from error
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ContractError("invalid_input", f"{label} must be UTC")
    return parsed


def validate_version(value: Any, label: str = "version") -> dict[str, Any]:
    result = exact_object(value, {"value", "source", "status"}, label)
    status = result["status"]
    source = result["source"]
    if (
        not isinstance(status, str)
        or status not in {"observed", "unknown", "not_checked"}
        or not isinstance(source, str)
        or source not in VERSION_SOURCES
    ):
        raise ContractError("invalid_input", f"{label} has an invalid status or source")
    if status == "observed":
        if (
            not isinstance(result["value"], str)
            or VERSION_RE.fullmatch(result["value"]) is None
        ):
            raise ContractError(
                "invalid_input", f"{label}.value must be a stable version"
            )
        if source in {"not_requested", "unavailable"}:
            raise ContractError(
                "invalid_input", f"{label} has an invalid observed source"
            )
    elif result["value"] is not None:
        raise ContractError("invalid_input", f"{label}.value must be null")
    if status == "not_checked" and source != "not_requested":
        raise ContractError(
            "invalid_input", f"{label} not_checked requires not_requested"
        )
    return dict(result)


def validate_scope(value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("kind"), str)
        or value.get("kind") not in {"full", "scoped"}
    ):
        raise ContractError("invalid_input", "scope is invalid")
    if value["kind"] == "full":
        exact_object(value, {"kind"}, "scope")
        return {"kind": "full"}
    exact_object(value, {"kind", "components"}, "scope")
    components = value["components"]
    if (
        not isinstance(components, list)
        or not components
        or any(
            not isinstance(item, str) or item not in COMPONENTS for item in components
        )
        or components != sorted(set(components))
    ):
        raise ContractError(
            "invalid_input", "scope.components must be sorted, unique, and supported"
        )
    return {"kind": "scoped", "components": list(components)}


def validate_record(value: Any, canonical_root: str) -> dict[str, Any]:
    record = exact_object(value, RECORD_KEYS, "record")
    if record["schema"] != RECORD_SCHEMA:
        raise ContractError("unsupported_schema", "record schema is unsupported")
    attempt_id = validate_uuid4(record["attempt_id"])
    revision = record["expected_row_revision"]
    if type(revision) is not int or revision < 0:
        raise ContractError(
            "invalid_input", "expected_row_revision must be a non-negative integer"
        )
    if (
        not isinstance(record["git_root"], str)
        or unicodedata.normalize("NFC", record["git_root"]) != canonical_root
    ):
        raise ContractError(
            "invalid_git_root", "git_root must be the canonical Git root"
        )
    if not isinstance(record["project"], str):
        raise ContractError("invalid_input", "project must be a non-empty string")
    project = unicodedata.normalize("NFC", record["project"])
    if not project:
        raise ContractError("invalid_input", "project must be a non-empty string")
    started = parse_time(record["started_at"], "started_at")
    completed = parse_time(record["completed_at"], "completed_at")
    if (
        completed < started
        or not isinstance(record["outcome"], str)
        or record["outcome"] not in OUTCOMES
    ):
        raise ContractError(
            "invalid_input", "record outcome or completion time is invalid"
        )
    scope = validate_scope(record["scope"])
    components = record["components"]
    if not isinstance(components, dict) or any(
        key not in RECORDABLE_COMPONENTS for key in components
    ):
        raise ContractError(
            "invalid_input", "components contains an unsupported observation"
        )
    if scope["kind"] == "scoped" and any(
        key.replace("_", "-") not in scope["components"] for key in components
    ):
        raise ContractError(
            "invalid_input", "component observation is outside the declared scope"
        )
    normalized_components: dict[str, Any] = {}
    for name, observation in components.items():
        item = exact_object(observation, {"outcome", "version"}, f"components.{name}")
        if (
            not isinstance(item["outcome"], str)
            or item["outcome"] not in COMPONENT_OUTCOMES
        ):
            raise ContractError(
                "invalid_input", f"components.{name}.outcome is invalid"
            )
        normalized_components[name] = {
            "outcome": item["outcome"],
            "version": validate_version(item["version"], f"components.{name}.version"),
        }
    return {
        "schema": RECORD_SCHEMA,
        "attempt_id": attempt_id,
        "expected_row_revision": revision,
        "git_root": canonical_root,
        "project": project,
        "started_at": record["started_at"],
        "completed_at": record["completed_at"],
        "outcome": record["outcome"],
        "scope": scope,
        "components": normalized_components,
    }


def version_tuple(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value)
    if match is None:
        raise ContractError("invalid_input", "version is not stable")
    return tuple(int(item) for item in match.groups())


def safe_absent_path(value: str) -> str:
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ContractError("invalid_git_root", "git_root must be absolute")
    normalized = unicodedata.normalize("NFC", value)
    raw_parts = normalized.split(os.sep)
    if (
        normalized != value
        or os.path.normpath(normalized) != normalized
        or any(part in {".", ".."} for part in raw_parts)
    ):
        raise ContractError("invalid_git_root", "absent git_root is not canonical")
    return normalized
