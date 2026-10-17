"""Recover original work sources through approved finalization changes."""

import json
from pathlib import Path

from adaptive_bundles import BundleError, contained, git, read_regular, sha256
from adaptive_definitions import definition_id
from adaptive_design import application
from adaptive_preparation import object_rows, object_value, read_basis


def identity(value):
    """Ordinary target maps may render the same SHA-256 with or without its prefix."""
    if isinstance(value, str) and len(value) == 64:
        return "sha256:" + value
    return value


def same_work(repository, expected, actual):
    actual = object_value(actual, "Current ordinary work")
    if (
        actual.get("repository") not in (None, "unknown")
        and (
            not isinstance(actual["repository"], str)
            or Path(actual["repository"]).expanduser().resolve() != repository
        )
        or any(
            (None if actual.get(key) == "none" else actual.get(key))
            != (None if expected[key] == "none" else expected[key])
            for key in ("epic", "task")
            if key in expected
        )
    ):
        raise BundleError("reassessment-required", "Finalization work identity differs")


def finalization_observation(client, observation):
    status = client.read(
        ["status", "--verbose"], "session.status", {"podway.status-result/v5"}
    )
    initial = observation["status"]
    if (
        not isinstance(status, dict)
        or not isinstance(status.get("procedure"), dict)
        or not isinstance(status.get("current_trace_history"), dict)
        or not isinstance(status["current_trace_history"].get("entries"), list)
    ):
        raise BundleError(
            "unsupported-runtime", "Native finalization status is unavailable"
        )
    if (
        status.get("session") != initial["session"]
        or status.get("goal_revision") != initial.get("goal_revision")
        or tuple(status["procedure"].get(key) for key in ("id", "version", "digest"))
        != tuple(initial["procedure"].get(key) for key in ("id", "version", "digest"))
    ):
        raise BundleError(
            "reassessment-required", "Native session changed during recovery"
        )
    return {**observation, "status": status}


def finalization_sources(repository, assignment, recovery, observation):
    """Keep original extraction intact through approved changes or deletion."""
    recovery = object_value(recovery, "finalization_recovery")
    status = observation["status"]
    if status["session"]["lifecycle"] not in {"running", "completed", "cancelled"}:
        raise BundleError(
            "invalid-input", "Source retirement is not pre-start recovery"
        )
    checkpoint = object_value(recovery.get("checkpoint"), "Finalization checkpoint")
    same_work(repository, assignment["work"], checkpoint.get("work"))
    # Ordinary v2 separates public workflow context from native agent metadata.
    # Older local captures put the public status in native; retain those only
    # when no canonical procedure field was declared.
    context_field = "procedure" if "procedure" in checkpoint else "native"
    native = object_value(checkpoint.get(context_field), "Checkpoint Procedure context")
    if context_field == "procedure" and "native" in native:
        # Existing mapped dispatches wrap the same public status in procedure.native.
        native = object_value(native["native"], "Checkpoint dispatched native context")
    native_procedure = object_value(native.get("procedure"), "Checkpoint procedure")
    if (
        checkpoint.get("schema") != "aquarium.orchestration-checkpoint/v2"
        or native.get("session") != status["session"]
        or type(status.get("goal_revision")) is not int
        or native.get("goal_revision") != status.get("goal_revision")
        or tuple(native_procedure.get(key) for key in ("id", "version", "digest"))
        != tuple(status["procedure"].get(key) for key in ("id", "version", "digest"))
    ):
        raise BundleError(
            "reassessment-required", "Finalization checkpoint is not current"
        )
    proposal = object_value(recovery.get("proposal"), "Finalization proposal")
    applied = application(
        repository,
        proposal,
        recovery.get("approval"),
        applied=True,
        approval_sources=("user", "epic-delegation"),
    )
    if applied["status"] != "verified-applied":
        raise BundleError(
            applied["status"],
            "Approved finalization postimages are not current",
            applied,
        )
    reference = object_value(
        recovery.get("assessment"), "Affected assessment reference"
    )
    if not all(
        isinstance(reference.get(key), str) and reference[key]
        for key in ("path", "sha256")
    ):
        raise BundleError(
            "invalid-input", "Assessment reference needs its path and SHA-256"
        )
    # This is the existing ordinary report, never a replacement pre-start report.
    report = object_value(
        json.loads(read_basis(repository, reference)), "Affected assessment"
    )
    same_work(repository, assignment["work"], report.get("work"))
    target = object_value(report.get("target"), "Affected assessment target")
    files = object_value(target.get("files", {}), "Affected assessment files")
    checkpoint_result = report.get("checkpoint_result")
    if checkpoint_result is None:
        checkpoint_result = report.get("verdict")
    if (
        report.get("schema") != "aquarium.judge-assessment/v2"
        or checkpoint_result != "pass"
        or not report.get("criteria")
        or not report.get("evidence")
    ):
        raise BundleError(
            "not-established", "Current affected ordinary assessment is missing"
        )
    # Only approved affected postimages are mechanically checked here. Other
    # candidate/check-input applicability remains the ordinary Primary/Judge
    # contract; this helper does not introduce another report/freshness engine.
    deleted = object_value(
        target.get("deleted_before", {}), "Assessment deleted targets"
    )
    for path, images in proposal["targets"].items():
        expected = images["after"]
        if expected is None:
            if identity(deleted.get(path)) != images["before"]:
                raise BundleError(
                    "not-established", "Assessment does not cover approved deletion"
                )
        elif identity(files.get(path)) != expected:
            raise BundleError(
                "not-established", "Assessment does not cover approved postimage"
            )
    evidence = object_value(
        recovery.get("selected_evidence"), "Selected native evidence"
    )
    value = object_value(evidence.get("result"), "Selected native evidence result")
    source = object_value(value.get("source"), "Selected native producer")
    consumer = object_value(value.get("consumer"), "Selected native consumer")
    workspace = object_value(evidence.get("workspace"), "Selected evidence workspace")
    procedure = object_value(
        report.get("procedure") or {}, "Affected assessment procedure"
    )
    report_session = object_value(
        procedure.get("session") or {}, "Affected assessment session"
    )
    report_attempt = object_value(
        procedure.get("attempt") or {}, "Affected assessment attempt"
    )
    page = object_value(value.get("page"), "Selected native page")
    data = object_value(page.get("data"), "Selected native artifact")
    item = object_value(value.get("item"), "Selected native item")
    location = data.get("location")
    if not isinstance(location, str) or not location:
        raise BundleError("invalid-input", "Selected artifact needs its existing path")
    if (
        evidence.get("schema") != "podway.output/v4"
        or not isinstance(workspace.get("root"), str)
        or Path(workspace["root"]).resolve() != repository
        or any(
            declared not in (None, "unknown") and declared != actual
            for declared, actual in (
                (report_session.get("id"), status["session"]["id"]),
                (procedure.get("goal_revision"), status["goal_revision"]),
                (procedure.get("node"), source.get("graph_node_id")),
                (report_attempt.get("attempt_id"), source.get("attempt_id")),
                (report_attempt.get("attempt_number"), source.get("attempt_number")),
            )
        )
        or value.get("schema") != "podway.evidence-read-result/v1"
        or item.get("type") != "artifact"
        or value.get("truncated") is not False
        or not isinstance(source.get("attempt_id"), str)
        or not source["attempt_id"]
        or data.get("sha256_digest") != reference.get("sha256")
        or data.get("location_type") != "path"
        or contained(repository, Path(location))
        != contained(repository, Path(reference["path"]))
    ):
        raise BundleError(
            "not-established", "Current selected native assessment is not established"
        )
    history = object_value(status.get("current_trace_history"), "Current native trace")
    entries = object_rows(history.get("entries"), "Current native attempts")
    for endpoint, lifecycles in (
        (source, {"completed"}),
        (consumer, {"running", "completed"}),
    ):
        if not any(
            all(
                entry.get(key) == endpoint.get(key)
                for key in ("graph_node_id", "attempt_id", "attempt_number")
            )
            and entry.get("goal_revision") == status["goal_revision"]
            and entry.get("validity") == "valid"
            and entry.get("lifecycle") in lifecycles
            for entry in entries
        ):
            raise BundleError(
                "not-established", "Selected native attempt is absent or invalidated"
            )
    rows = object_rows(recovery.get("sources"), "Affected original sources")
    references = {row["path"]: row for row in assignment["work"]["requirement_sources"]}
    recovered = {}
    for row in rows:
        path = row.get("path")
        if not isinstance(path, str):
            raise BundleError("invalid-input", "Retired source path must be a string")
        original = references.get(path)
        images = proposal["targets"].get(path)
        if (
            original is None
            or path in recovered
            or images is None
            or images["before"] != original["sha256"]
        ):
            raise BundleError(
                "not-established",
                "Affected source lacks its original approved before-image",
            )
        if row.get("capture") is not None:
            if not isinstance(row["capture"], str) or not row["capture"]:
                raise BundleError(
                    "invalid-input", "Retained capture needs its existing path"
                )
            raw = read_regular(repository, Path(row["capture"]))
        else:
            commit = row.get("commit")
            if (
                not isinstance(commit, str)
                or len(commit) not in {40, 64}
                or any(char not in "0123456789abcdef" for char in commit)
                or Path(path).is_absolute()
                or ".." in Path(path).parts
            ):
                raise BundleError(
                    "invalid-input",
                    "Recovery needs an exact capture or immutable commit",
                )
            verified = git(
                repository,
                "--no-replace-objects",
                "rev-parse",
                "--quiet",
                "--verify",
                commit + "^{commit}",
            )
            if verified.returncode or verified.stdout.decode().strip() != commit:
                raise BundleError(
                    "not-established", "Original immutable commit is unavailable"
                )
            blob = git(
                repository,
                "--no-replace-objects",
                "rev-parse",
                "--quiet",
                "--verify",
                commit + ":" + path,
            )
            if blob.returncode or not blob.stdout.strip():
                raise BundleError(
                    "not-established", "Original immutable source is unavailable"
                )
            blob_id = blob.stdout.decode().strip()
            kind = git(
                repository, "--no-replace-objects", "cat-file", "-t", blob_id
            ).stdout.strip()
            if kind != b"blob":
                raise BundleError(
                    "not-established", "Original immutable source is not a blob"
                )
            raw = git(
                repository, "--no-replace-objects", "cat-file", "blob", blob_id
            ).stdout
        if sha256(raw) != original["sha256"]:
            raise BundleError(
                "source-drift", "Retained original source differs from approved bytes"
            )
        recovered[path] = raw
    if not recovered:
        raise BundleError(
            "invalid-input", "No approved affected original source was supplied"
        )

    def source_reader(reference):
        if reference["path"] in recovered:
            return recovered[reference["path"]]
        return read_regular(repository, Path(reference["path"]))

    return source_reader, report


def selected_assessment(binding, recovery, report):
    """A native record cannot borrow an unrelated producer's Judge role."""
    producer = recovery["selected_evidence"]["result"]["source"]["graph_node_id"]
    if binding["nodes"].get(producer, {}).get("role") != "judge":
        raise BundleError(
            "not-established", "Selected report is not from a mapped Judge"
        )
    procedure = object_value(report.get("procedure") or {}, "Assessment procedure")
    for field, expected in (
        ("source", binding["procedure"]["source_sha256"]),
        ("binding", "sha256:" + definition_id(binding)),
    ):
        declared = object_value(procedure.get(field) or {}, "Assessment " + field).get(
            "sha256"
        )
        if declared not in (None, "unknown") and identity(declared) != expected:
            raise BundleError(
                "not-established", "Affected report definition identity differs"
            )
