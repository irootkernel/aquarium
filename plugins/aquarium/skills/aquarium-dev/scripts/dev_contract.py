#!/usr/bin/env python3
"""Strict shared JSON contract for the Aquarium development channel."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

PROJECT_IDS = frozenset({"aquarium", "podway", "mulgae", "gaori", "sanho", "dolgorae"})
ARTIFACT_KINDS = frozenset({"codex-plugin", "executable"})
OPERATIONS = frozenset(
    {
        "diagnose",
        "enroll",
        "rebuild",
        "publish",
        "repair",
        "install-launcher",
    }
)
RESULT_STATUSES = frozenset({"success", "no-change", "diagnosed"})
ERROR_CODES = frozenset(
    {
        "unsupported_host",
        "not_git_root",
        "symlink_git_root",
        "unsupported_project",
        "producer_contract_missing",
        "producer_description_invalid",
        "producer_build_failed",
        "producer_build_timeout",
        "producer_manifest_invalid",
        "not_local_main",
        "dirty_worktree",
        "sha_mismatch",
        "output_escape",
        "checksum_mismatch",
        "enrollment_missing",
        "enrollment_conflict",
        "enrollment_broken",
        "hook_conflict",
        "artifact_missing",
        "artifact_invalid",
        "lease_unavailable",
        "publication_failed",
        "approval_required",
        "invalid_arguments",
        "worker_failed",
    }
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
DEV_VERSION_RE = re.compile(
    r"^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)-dev\.([0-9a-f]{12})$"
)
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class ContractError(ValueError):
    """Raised when an object does not satisfy the frozen v1 contract."""


def _exact_object(value: Any, fields: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{name} must be an object")
    actual = set(value)
    if actual != fields:
        raise ContractError(
            f"{name} fields must be exactly {sorted(fields)}; got {sorted(actual)}"
        )
    return value


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{name} must be a non-empty string")
    return value


def _project_id(value: Any) -> str:
    project_id = _string(value, "project_id")
    if project_id not in PROJECT_IDS:
        raise ContractError(f"unsupported project_id: {project_id}")
    return project_id


def _artifact_path(value: Any) -> str:
    path = _string(value, "artifact_path")
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or str(pure) != path
        or any(part in {".", ".."} for part in pure.parts)
    ):
        raise ContractError(
            "artifact_path must be a normalized contained relative path"
        )
    return path


def _artifact_contract(project_id: str, artifact_kind: Any, artifact_path: Any) -> None:
    path = _artifact_path(artifact_path)
    if project_id == "aquarium":
        if artifact_kind != "codex-plugin":
            raise ContractError("aquarium must produce one codex-plugin artifact")
        return
    if artifact_kind != "executable" or path != f"bin/{project_id}":
        raise ContractError(
            "tool producers must emit one executable at bin/<project_id>"
        )


def validate_description(value: Any) -> dict[str, Any]:
    document = _exact_object(
        value,
        {"schema", "project_id", "next_version", "artifact_kind", "artifact_path"},
        "description",
    )
    if document["schema"] != "aquarium-dev-producer-description/v1":
        raise ContractError("unsupported description schema")
    project_id = _project_id(document["project_id"])
    if not isinstance(document["next_version"], str) or not VERSION_RE.fullmatch(
        document["next_version"]
    ):
        raise ContractError("next_version must be a stable v-prefixed semantic version")
    if document["artifact_kind"] not in ARTIFACT_KINDS:
        raise ContractError("unsupported artifact_kind")
    _artifact_contract(project_id, document["artifact_kind"], document["artifact_path"])
    return document


def validate_manifest(value: Any) -> dict[str, Any]:
    document = _exact_object(
        value,
        {
            "schema",
            "project_id",
            "git_sha",
            "development_version",
            "artifact_kind",
            "artifact_path",
            "sha256",
        },
        "manifest",
    )
    if document["schema"] != "aquarium-dev-artifact-manifest/v1":
        raise ContractError("unsupported manifest schema")
    project_id = _project_id(document["project_id"])
    git_sha = document["git_sha"]
    if not isinstance(git_sha, str) or not SHA_RE.fullmatch(git_sha):
        raise ContractError("git_sha must be 40 lowercase hexadecimal characters")
    version = document["development_version"]
    match = DEV_VERSION_RE.fullmatch(version) if isinstance(version, str) else None
    if match is None or match.group(1) != git_sha[:12]:
        raise ContractError(
            "development_version must contain the first 12 git_sha characters"
        )
    if document["artifact_kind"] not in ARTIFACT_KINDS:
        raise ContractError("unsupported artifact_kind")
    _artifact_contract(project_id, document["artifact_kind"], document["artifact_path"])
    if not isinstance(document["sha256"], str) or not DIGEST_RE.fullmatch(
        document["sha256"]
    ):
        raise ContractError("sha256 must be a lowercase prefixed digest")
    return document


def validate_result(value: Any) -> dict[str, Any]:
    document = _exact_object(
        value,
        {"schema", "operation", "status", "project_id", "message", "details"},
        "manager result",
    )
    if document["schema"] != "aquarium-dev-manager-result/v1":
        raise ContractError("unsupported manager result schema")
    if document["operation"] not in OPERATIONS:
        raise ContractError("unsupported operation")
    if document["status"] not in RESULT_STATUSES:
        raise ContractError("unsupported result status")
    if document["project_id"] is not None:
        _project_id(document["project_id"])
    _string(document["message"], "message")
    if not isinstance(document["details"], dict):
        raise ContractError("details must be an object")
    return document


def validate_error(value: Any) -> dict[str, Any]:
    document = _exact_object(value, {"schema", "error"}, "error document")
    if document["schema"] != "aquarium-dev-error/v1":
        raise ContractError("unsupported error schema")
    error = _exact_object(
        document["error"],
        {"code", "message", "action", "stage", "project_id", "git_sha"},
        "error",
    )
    if error["code"] not in ERROR_CODES:
        raise ContractError("unsupported error code")
    for field in ("message", "action", "stage"):
        _string(error[field], field)
    if error["project_id"] is not None:
        _project_id(error["project_id"])
    if error["git_sha"] is not None and (
        not isinstance(error["git_sha"], str) or not SHA_RE.fullmatch(error["git_sha"])
    ):
        raise ContractError("git_sha must be null or a full lowercase commit ID")
    return document
