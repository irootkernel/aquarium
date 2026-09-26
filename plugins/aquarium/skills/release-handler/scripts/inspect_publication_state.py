#!/usr/bin/env python3
"""Classify one release publication state without mutation."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

REQUEST_SCHEMA_VERSION = "aquarium-release-publication-observation/v5"
RESULT_SCHEMA_VERSION = "aquarium-release-publication-state/v5"
ERROR_SCHEMA_VERSION = "aquarium-release-publication-state-error/v5"
MAX_REQUEST_BYTES = 64 * 1024
SEMVER = re.compile(r"^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
OBJECT_ID = re.compile(r"^[0-9a-f]{40,64}$")


class ObservationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def object_id(value: object, field: str) -> str:
    if not isinstance(value, str) or OBJECT_ID.fullmatch(value) is None:
        raise ObservationError("observation_invalid", f"{field} is invalid")
    return value


def optional_object_id(value: object, field: str) -> str | None:
    if value is None:
        return None
    return object_id(value, field)


def exact_mapping(value: object, keys: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ObservationError("observation_invalid", f"{field} is malformed")
    return value


def ref_status(observed: str, expected: str) -> str:
    if observed == expected:
        return "matching"
    return "conflict"


def inspect(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ObservationError("observation_invalid", "observation is malformed")
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str):
        raise ObservationError("observation_invalid", "observation schema is invalid")
    if schema_version != REQUEST_SCHEMA_VERSION:
        raise ObservationError(
            "schema_unsupported", f"observation must use {REQUEST_SCHEMA_VERSION}"
        )
    request = exact_mapping(
        payload,
        {
            "schema_version",
            "version",
            "expected_release_title",
            "release_basis_candidate_sha",
            "release_commit",
            "qa_evidence_candidate_sha",
            "qa_evidence_relation_to_release_basis",
            "qa_binding",
            "qa_reuse_attempt",
            "gate_evidence_release_commit_sha",
            "local_main_sha",
            "remote_main_sha",
            "remote_main_relation_to_release_basis",
            "remote_main_relation_to_release_commit",
            "tag",
            "hosted_release",
        },
        "observation",
    )
    version = request["version"]
    if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
        raise ObservationError("observation_invalid", "version is invalid")
    expected_title = request["expected_release_title"]
    if (
        not isinstance(expected_title, str)
        or not expected_title.strip()
        or len(expected_title) > 4096
        or "\n" in expected_title
        or "\r" in expected_title
    ):
        raise ObservationError(
            "observation_invalid", "expected release title is invalid"
        )
    release_basis = object_id(
        request["release_basis_candidate_sha"], "release-basis candidate"
    )
    release_commit = exact_mapping(
        request["release_commit"], {"sha", "parent_sha", "title"}, "release commit"
    )
    release_sha = object_id(release_commit["sha"], "release commit SHA")
    release_parent = object_id(release_commit["parent_sha"], "release commit parent")
    release_title = release_commit["title"]
    if not isinstance(release_title, str):
        raise ObservationError("observation_invalid", "release commit title is invalid")
    qa_evidence = optional_object_id(
        request["qa_evidence_candidate_sha"], "QA evidence candidate"
    )
    qa_relation = request["qa_evidence_relation_to_release_basis"]
    if not isinstance(qa_relation, str) or qa_relation not in {
        "equal",
        "direct_parent",
    }:
        raise ObservationError(
            "observation_invalid", "QA evidence relationship is invalid"
        )
    qa_binding = request["qa_binding"]
    if not isinstance(qa_binding, str) or qa_binding not in {
        "exact",
        "approved_qa_neutral_descendant",
    }:
        raise ObservationError("observation_invalid", "QA binding is invalid")
    qa_reuse_attempt = request["qa_reuse_attempt"]
    if (
        not isinstance(qa_reuse_attempt, int)
        or isinstance(qa_reuse_attempt, bool)
        or qa_reuse_attempt not in {0, 1}
    ):
        raise ObservationError("observation_invalid", "QA reuse attempt is invalid")
    gate_evidence = optional_object_id(
        request["gate_evidence_release_commit_sha"], "gate evidence release commit"
    )
    local_main = object_id(request["local_main_sha"], "local main")
    remote_main = object_id(request["remote_main_sha"], "remote main")
    remote_relation = request["remote_main_relation_to_release_basis"]
    if not isinstance(remote_relation, str) or remote_relation not in {
        "equal",
        "ancestor",
        "descendant",
        "diverged",
    }:
        raise ObservationError(
            "observation_invalid", "remote main relationship is invalid"
        )
    if (remote_main == release_basis) != (remote_relation == "equal"):
        raise ObservationError(
            "observation_invalid", "remote main relationship contradicts its SHA"
        )
    release_relation = request["remote_main_relation_to_release_commit"]
    if not isinstance(release_relation, str) or release_relation not in {
        "equal",
        "ancestor",
        "descendant",
        "diverged",
    }:
        raise ObservationError(
            "observation_invalid", "remote release relationship is invalid"
        )
    if (remote_main == release_sha) != (release_relation == "equal"):
        raise ObservationError(
            "observation_invalid", "remote release relationship contradicts its SHA"
        )
    if release_parent == release_basis and release_sha != release_basis:
        allowed = {
            "equal": {"ancestor"},
            "ancestor": {"ancestor"},
            "descendant": {"equal", "descendant", "diverged"},
            "diverged": {"diverged"},
        }
        if release_relation not in allowed[remote_relation]:
            raise ObservationError(
                "observation_invalid", "remote ancestry relationships conflict"
            )
    tag = exact_mapping(request["tag"], {"state", "annotated", "peeled_sha"}, "tag")
    hosted = exact_mapping(
        request["hosted_release"],
        {"state", "tag", "target_sha", "draft", "prerelease"},
        "hosted release",
    )
    if (
        not isinstance(tag["state"], str)
        or tag["state"] not in {"absent", "present"}
        or not isinstance(tag["annotated"], bool)
    ):
        raise ObservationError("observation_invalid", "tag observation is invalid")
    tag_peeled = optional_object_id(tag["peeled_sha"], "peeled tag")
    if tag["state"] == "absent" and (tag["annotated"] or tag_peeled is not None):
        raise ObservationError("observation_invalid", "absent tag has object data")
    if not isinstance(hosted["state"], str) or hosted["state"] not in {
        "absent",
        "present",
    }:
        raise ObservationError(
            "observation_invalid", "hosted release observation is invalid"
        )
    hosted_tag = hosted["tag"]
    if hosted_tag is not None and not isinstance(hosted_tag, str):
        raise ObservationError("observation_invalid", "hosted release tag is invalid")
    hosted_target = optional_object_id(hosted["target_sha"], "hosted release target")
    if not isinstance(hosted["draft"], bool) or not isinstance(
        hosted["prerelease"], bool
    ):
        raise ObservationError(
            "observation_invalid", "hosted release publication state is invalid"
        )
    if hosted["state"] == "absent" and (
        hosted_tag is not None
        or hosted_target is not None
        or hosted["draft"]
        or hosted["prerelease"]
    ):
        raise ObservationError(
            "observation_invalid", "absent hosted release has object data"
        )

    exact_qa_binding = (
        qa_binding == "exact"
        and qa_evidence == release_basis
        and qa_relation == "equal"
        and qa_reuse_attempt == 0
    )
    neutral_qa_binding = (
        qa_binding == "approved_qa_neutral_descendant"
        and qa_evidence is not None
        and qa_evidence != release_basis
        and qa_evidence != release_sha
        and qa_relation == "direct_parent"
        and qa_reuse_attempt == 1
    )
    evidence_status = (
        "matching"
        if release_sha != release_basis
        and release_parent == release_basis
        and release_title == expected_title
        and (exact_qa_binding or neutral_qa_binding)
        and gate_evidence == release_sha
        else "unproven"
    )
    local_main_status = ref_status(local_main, release_sha)
    if remote_main == release_sha:
        remote_main_status = (
            "matching" if remote_relation == "descendant" else "conflict"
        )
    elif remote_relation == "descendant" and release_relation == "descendant":
        remote_main_status = "advanced"
    elif remote_relation in {"equal", "ancestor"} and release_relation == "ancestor":
        remote_main_status = "missing"
    else:
        remote_main_status = "conflict"
    if tag["state"] == "absent":
        tag_status = "missing"
    elif tag["annotated"] and tag_peeled == release_sha:
        tag_status = "matching"
    else:
        tag_status = "conflict"
    if hosted["state"] == "absent":
        hosted_status = "missing"
    elif (
        hosted_tag == version
        and hosted_target == release_sha
        and not hosted["draft"]
        and not hosted["prerelease"]
    ):
        hosted_status = "matching"
    else:
        hosted_status = "conflict"

    statuses = {
        "evidence": evidence_status,
        "local_main": local_main_status,
        "remote_main": remote_main_status,
        "tag": tag_status,
        "hosted_release": hosted_status,
    }
    if evidence_status == "unproven":
        classification = "unproven"
        next_action = "stop"
    elif (
        "conflict" in statuses.values()
        or local_main_status != "matching"
        or hosted_status == "matching"
        and tag_status != "matching"
    ):
        classification = "conflict"
        next_action = "stop"
    elif remote_main_status == "missing":
        classification = "partial"
        next_action = "push_main"
    elif tag_status == "missing":
        classification = "partial"
        next_action = "create_and_push_tag"
    elif hosted_status == "missing":
        classification = "partial"
        next_action = "create_hosted_release"
    else:
        classification = "complete"
        next_action = "verify_complete"

    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "version": version,
        "expected_release_title": expected_title,
        "release_basis_candidate_sha": release_basis,
        "qa_evidence_candidate_sha": qa_evidence,
        "qa_evidence_relation_to_release_basis": qa_relation,
        "qa_binding": qa_binding,
        "qa_reuse_attempt": qa_reuse_attempt,
        "release_commit_sha": release_sha,
        "remote_main_sha": remote_main,
        "remote_main_relation_to_release_basis": remote_relation,
        "remote_main_relation_to_release_commit": release_relation,
        "classification": classification,
        "next_action": next_action,
        "statuses": statuses,
    }


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise ObservationError("observation_oversized", "observation is too large")
        try:
            payload = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ObservationError(
                "observation_invalid", "observation is not valid JSON"
            ) from error
        result = inspect(payload)
    except ObservationError as error:
        print(
            json.dumps(
                {
                    "schema_version": ERROR_SCHEMA_VERSION,
                    "error": {"code": error.code, "message": str(error)},
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
