#!/usr/bin/env python3
"""Classify one release publication state without mutation."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

REQUEST_SCHEMA_VERSION = "aquarium-release-publication-observation/v1"
RESULT_SCHEMA_VERSION = "aquarium-release-publication-state/v1"
ERROR_SCHEMA_VERSION = "aquarium-release-publication-state-error/v1"
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


def ref_status(observed: str, expected: str, allowed_previous: str | None) -> str:
    if observed == expected:
        return "matching"
    if allowed_previous is not None and observed == allowed_previous:
        return "missing"
    return "conflict"


def inspect(payload: object) -> dict[str, object]:
    request = exact_mapping(
        payload,
        {
            "schema_version",
            "version",
            "qa_candidate_sha",
            "release_commit",
            "qa_evidence_candidate_sha",
            "gate_evidence_release_commit_sha",
            "local_main_sha",
            "remote_main_sha",
            "tag",
            "hosted_release",
        },
        "observation",
    )
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ObservationError(
            "schema_unsupported", "observation schema is unsupported"
        )
    version = request["version"]
    if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
        raise ObservationError("observation_invalid", "version is invalid")
    qa_candidate = object_id(request["qa_candidate_sha"], "qa candidate")
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
    gate_evidence = optional_object_id(
        request["gate_evidence_release_commit_sha"], "gate evidence release commit"
    )
    local_main = object_id(request["local_main_sha"], "local main")
    remote_main = object_id(request["remote_main_sha"], "remote main")
    tag = exact_mapping(request["tag"], {"state", "annotated", "peeled_sha"}, "tag")
    hosted = exact_mapping(
        request["hosted_release"], {"state", "tag", "target_sha"}, "hosted release"
    )
    if tag["state"] not in {"absent", "present"} or not isinstance(
        tag["annotated"], bool
    ):
        raise ObservationError("observation_invalid", "tag observation is invalid")
    tag_peeled = optional_object_id(tag["peeled_sha"], "peeled tag")
    if tag["state"] == "absent" and (tag["annotated"] or tag_peeled is not None):
        raise ObservationError("observation_invalid", "absent tag has object data")
    if hosted["state"] not in {"absent", "present"}:
        raise ObservationError(
            "observation_invalid", "hosted release observation is invalid"
        )
    hosted_tag = hosted["tag"]
    if hosted_tag is not None and not isinstance(hosted_tag, str):
        raise ObservationError("observation_invalid", "hosted release tag is invalid")
    hosted_target = optional_object_id(hosted["target_sha"], "hosted release target")
    if hosted["state"] == "absent" and (
        hosted_tag is not None or hosted_target is not None
    ):
        raise ObservationError(
            "observation_invalid", "absent hosted release has object data"
        )

    evidence_status = (
        "matching"
        if release_parent == qa_candidate
        and release_title == f"[REL] Release {version}"
        and qa_evidence == qa_candidate
        and gate_evidence == release_sha
        else "unproven"
    )
    local_main_status = ref_status(local_main, release_sha, None)
    remote_main_status = ref_status(remote_main, release_sha, qa_candidate)
    if tag["state"] == "absent":
        tag_status = "missing"
    elif tag["annotated"] and tag_peeled == release_sha:
        tag_status = "matching"
    else:
        tag_status = "conflict"
    if hosted["state"] == "absent":
        hosted_status = "missing"
    elif hosted_tag == version and hosted_target == release_sha:
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
        "qa_candidate_sha": qa_candidate,
        "release_commit_sha": release_sha,
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
