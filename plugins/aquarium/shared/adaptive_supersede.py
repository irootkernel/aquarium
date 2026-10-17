"""Consented native atomic preserve-start and same-request recovery, without begin."""

import copy
from pathlib import Path

from adaptive_admission import resume_selected
from adaptive_bundles import BundleError, resolve_bundle
from adaptive_definitions import native_key
from adaptive_suitability import qualify_prepared


def required_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise BundleError("invalid-input", name + " must be nonempty text")
    return value


def observed(client):
    observation = client.health()
    if observation is None:
        raise BundleError("missing-session", "There is no predecessor to preserve")
    status = observation["status"]
    identities = {
        row.get("preconditions", {}).get("workspace_uuid")
        for row in observation.get("mutation_templates", [])
        if isinstance(row, dict)
    } - {None}
    if len(identities) != 1:
        raise BundleError(
            "unsupported-runtime", "Observation lacks one native workspace fence"
        )
    return observation, {
        "workspace_uuid": identities.pop(),
        "session": copy.deepcopy(status["session"]),
        "procedure": copy.deepcopy(status["procedure"]),
    }


def successor_bundle(repository, roots, qualification, client):
    if not isinstance(qualification, dict) or not isinstance(
        qualification.get("assignment"), dict
    ):
        raise BundleError(
            "invalid-input", "Successor needs its exact ordinary qualification context"
        )
    result = qualify_prepared(
        repository,
        qualification["assignment"],
        client=client,
        assessment=qualification.get("assessment"),
        combined_task_plan=qualification.get("combined_task_plan", False),
    )
    if result["status"] not in {"qualified", "qualified-known", "qualified-reuse"}:
        raise BundleError(
            "not-established", "Successor suitability remains due", result
        )
    binding = result["binding"]
    bundle = resolve_bundle(
        repository, roots, native_key(binding), native_identity=client.identity
    )
    if bundle["status"] != "resolved":
        raise BundleError(
            bundle["status"],
            "Retain the complete qualified successor before replacement",
            bundle,
        )
    if bundle["binding"] != binding:
        raise BundleError(
            "ambiguous", "Retained successor differs from the assessed mapping"
        )
    return bundle


def request_for(checkpoint):
    disclosure = checkpoint["disclosure"]
    old = disclosure["predecessor"]
    try:
        source = (
            Path(checkpoint["source_path"])
            .relative_to(Path(checkpoint["repository"]))
            .as_posix()
        )
    except ValueError as error:
        raise BundleError(
            "invalid-input", "Retained successor source is outside the worktree"
        ) from error
    return [
        "start",
        "--procedure=" + source,
        "--expect-procedure-digest",
        disclosure["successor"]["procedure"]["digest"],
        "--task",
        disclosure["title"],
        "--on-existing",
        "preserve",
        "--supersede-reason",
        disclosure["reason"],
        "--if-workspace-uuid",
        old["workspace_uuid"],
        "--if-session-id",
        old["session"]["id"],
        "--if-session-revision",
        str(old["session"]["revision"]),
        "--idempotency-key",
        checkpoint["idempotency_key"],
    ]


def prepare_transition(
    repository,
    *,
    roots,
    qualification,
    client,
    title,
    reason,
    missing_topology,
    pending_operations,
    remaining_authority,
    effects_reconciled,
    idempotency_key,
):
    """Retained successor preparation precedes the actual user's replacement decision."""
    repository = Path(repository).expanduser().resolve()
    if client.repository != repository:
        raise BundleError("invalid-input", "Client and transition worktree differ")
    for name, value in {
        "title": title,
        "reason": reason,
        "missing_topology": missing_topology,
        "idempotency_key": idempotency_key,
    }.items():
        required_text(value, name)
    if not isinstance(pending_operations, list) or not isinstance(
        remaining_authority, dict
    ):
        raise BundleError(
            "invalid-input",
            "Restore pending work and remaining authority from ordinary records",
        )
    if effects_reconciled is not True:
        raise BundleError(
            "not-established",
            "Reconcile uncertain effects and relevant descendants before replacement",
        )
    bundle = successor_bundle(repository, roots, qualification, client)
    observation, predecessor = observed(client)
    if predecessor["session"]["lifecycle"] != "running":
        raise BundleError(
            "incompatible",
            "Unexpected atomic supersede applies only to a running session",
        )
    old = resolve_bundle(
        repository,
        roots,
        tuple(predecessor["procedure"][k] for k in ("id", "version", "digest")),
        native_identity=client.identity,
    )
    if old["status"] != "resolved":
        raise BundleError(
            old["status"],
            "Resolve the original adopted binding before replacement",
            old,
        )
    disclosure = {
        "predecessor": predecessor,
        "successor": {
            "procedure": bundle["binding"]["procedure"],
            "bundle_id": bundle["bundle_id"],
            "family": bundle["binding"]["family"],
            "state": "prepared",
            "revision": 0,
        },
        "title": title,
        "reason": reason,
        "missing_topology": missing_topology,
        "current": observation["status"].get("current"),
        "pending_operations": copy.deepcopy(pending_operations),
        "remaining_authority": copy.deepcopy(remaining_authority),
        "effects_reconciled": True,
        "effect": "Atomically cancel and archive the running predecessor with superseded lineage; retain its history/results and create the prepared successor. No begin, goal achievement or authority renewal.",
    }
    checkpoint = {
        "repository": str(repository),
        "roots": list(roots),
        "disclosure": disclosure,
        "source_path": str(Path(bundle["path"]) / "procedure.yaml"),
        "idempotency_key": idempotency_key,
    }
    checkpoint["request"] = request_for(checkpoint)
    return {
        "status": "replacement-consent-required",
        "checkpoint": checkpoint,
        "dispatch": None,
    }


def consented(checkpoint, consent):
    if not isinstance(checkpoint, dict) or not isinstance(
        checkpoint.get("disclosure"), dict
    ):
        raise BundleError(
            "invalid-input", "Restore the complete ordinary transition checkpoint"
        )
    disclosure = checkpoint["disclosure"]
    for name in ("predecessor", "successor", "remaining_authority"):
        if not isinstance(disclosure.get(name), dict):
            raise BundleError("invalid-input", "Transition disclosure lacks " + name)
    predecessor = disclosure["predecessor"]
    if (
        not isinstance(predecessor.get("session"), dict)
        or not isinstance(predecessor.get("procedure"), dict)
        or not isinstance(disclosure["successor"].get("procedure"), dict)
    ):
        raise BundleError(
            "invalid-input", "Restore the exact old/new native identities"
        )
    for name in ("repository", "source_path", "idempotency_key"):
        required_text(checkpoint.get(name), name)
    if (
        not isinstance(checkpoint.get("roots"), list)
        or not checkpoint["roots"]
        or any(
            not isinstance(root, str) or not root.strip()
            for root in checkpoint["roots"]
        )
    ):
        raise BundleError("invalid-input", "Restore every approved searched root")
    for name in ("title", "reason", "missing_topology"):
        required_text(disclosure.get(name), name)
    required_text(predecessor.get("workspace_uuid"), "workspace_uuid")
    required_text(predecessor["session"].get("id"), "predecessor session ID")
    required_text(predecessor["session"].get("lifecycle"), "predecessor lifecycle")
    revision = predecessor["session"].get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise BundleError("invalid-input", "Restore the native predecessor revision")
    for procedure in (predecessor["procedure"], disclosure["successor"]["procedure"]):
        for name in ("id", "version", "digest"):
            required_text(procedure.get(name), "procedure " + name)
    required_text(disclosure["successor"].get("bundle_id"), "successor bundle ID")
    if not isinstance(disclosure.get("pending_operations"), list):
        raise BundleError("invalid-input", "Restore the pending operation records")
    if (
        not isinstance(consent, dict)
        or consent.get("source") != "user"
        or consent.get("decision") != "approved"
        or consent.get("disclosure") != checkpoint["disclosure"]
    ):
        raise BundleError(
            "replacement-consent-required",
            "Actual explicit consent must cover the complete current disclosure",
        )
    if checkpoint.get("request") != request_for(checkpoint):
        raise BundleError(
            "invalid-input",
            "Retained request differs from its disclosed atomic transition",
        )


def verify_result(repository, checkpoint, result, *, client, qualification):
    old = checkpoint["disclosure"]["predecessor"]
    if (
        result.get("schema") != "podway.session-start-result/v4"
        or result.get("session_state") != "prepared"
        or result.get("revision") != 0
        or result.get("active_attempt") is not None
        or result.get("goal_defined") is not False
        or result.get("procedure_digest")
        != checkpoint["disclosure"]["successor"]["procedure"]["digest"]
        or result.get("existing_session")
        != {
            "action": "supersede_archive",
            "lifecycle": "running",
            "session_id": old["session"]["id"],
            "session_revision": old["session"]["revision"],
        }
    ):
        raise BundleError(
            "not-established",
            "Native result does not establish the disclosed atomic transition",
            result,
        )
    archive = client.read(
        ["archive", "show", "--session-id", old["session"]["id"]],
        "session.archive_show",
        {"podway.session-archive-show-result/v3"},
    )
    disposition = archive.get("terminal_disposition", {})
    if (
        archive.get("activity") != "inactive"
        or archive.get("state", {}).get("procedure") != old["procedure"]
        or archive.get("state", {}).get("session")
        != {
            "id": old["session"]["id"],
            "lifecycle": "cancelled",
            "revision": old["session"]["revision"] + 1,
        }
        or disposition.get("kind") != "superseded"
        or disposition.get("successor_session_id") != result.get("session_id")
        or disposition.get("reason") != checkpoint["disclosure"]["reason"]
    ):
        raise BundleError(
            "not-established", "Archived predecessor/successor lineage differs", archive
        )
    current = client.health()
    if (
        current is None
        or current["status"]["session"]
        != {"id": result["session_id"], "lifecycle": "prepared", "revision": 0}
        or current["status"].get("current") is not None
        or current["status"].get("goal_defined") is not False
    ):
        raise BundleError(
            "not-established",
            "Reconcile current successor state before separately authorized begin",
            current,
        )
    expected = checkpoint["disclosure"]["successor"]["procedure"]
    if any(
        current["status"]["procedure"].get(key) != expected[key]
        for key in ("id", "version", "digest")
    ):
        raise BundleError(
            "corrupt", "Successor native tuple differs from the retained target"
        )
    resolved = resume_selected(
        repository,
        checkpoint["roots"],
        current["status"]["procedure"],
        client=client,
        qualification=qualification,
    )
    return {
        "status": "superseded-prepared-resolved",
        "session": current["status"]["session"],
        "bundle_id": resolved["bundle_id"],
        "predecessor": old,
        "native_result": result,
        "remaining_authority": copy.deepcopy(
            checkpoint["disclosure"]["remaining_authority"]
        ),
        "pending_operations": copy.deepcopy(
            checkpoint["disclosure"]["pending_operations"]
        ),
        "next_owner": "Primary separately authorized begin",
        "dispatch": None,
    }


def execute_transition(repository, *, checkpoint, consent, qualification, client):
    consented(checkpoint, consent)
    if str(Path(repository).expanduser().resolve()) != checkpoint[
        "repository"
    ] or client.repository != Path(checkpoint["repository"]):
        raise BundleError(
            "invalid-input", "Transition worktree differs from its retained request"
        )
    bundle = successor_bundle(repository, checkpoint["roots"], qualification, client)
    if (
        bundle["bundle_id"] != checkpoint["disclosure"]["successor"]["bundle_id"]
        or Path(checkpoint["source_path"]).name != "procedure.yaml"
        or str(Path(checkpoint["source_path"]).parent) not in bundle["aliases"]
    ):
        raise BundleError(
            "source-drift", "Current qualified successor changed after consent"
        )
    _, current = observed(client)
    if current != checkpoint["disclosure"]["predecessor"]:
        raise BundleError(
            "stale-consent",
            "Predecessor changed; reconcile current effects before a new transition",
        )
    try:
        result = client.read(
            checkpoint["request"],
            "session.start_replace",
            {"podway.session-start-result/v4"},
        )
    except BundleError as error:
        if error.code in {"MUTATION_OUTCOME_UNKNOWN", "runtime-failure"}:
            raise BundleError(
                "outcome-unknown",
                "Retain the exact request/key and recover before any replay",
                {"checkpoint": checkpoint, "native_code": error.code},
            ) from error
        raise
    return verify_result(
        repository, checkpoint, result, client=client, qualification=qualification
    )


def recover_transition(
    repository, *, checkpoint, consent, qualification, client, replay=False
):
    """Look up the original operation before an optional exact same-key replay."""
    consented(checkpoint, consent)
    if str(Path(repository).expanduser().resolve()) != checkpoint[
        "repository"
    ] or client.repository != Path(checkpoint["repository"]):
        raise BundleError(
            "invalid-input", "Recovery worktree differs from retained request"
        )
    lookup = client.read(
        ["outcome", "lookup", "--idempotency-key", checkpoint["idempotency_key"]],
        "outcome.lookup",
        {"podway.outcome-lookup-result/v1"},
    )
    if lookup.get("idempotency_key") != checkpoint["idempotency_key"]:
        raise BundleError(
            "unsupported-runtime", "Outcome lookup does not bind the original key"
        )
    if lookup.get("found") is True:
        envelope = lookup.get("outcome", {}).get("response", {})
        if (
            envelope.get("schema") != "podway.output/v4"
            or envelope.get("command") != "session.start_replace"
            or envelope.get("workspace", {}).get("uuid")
            != checkpoint["disclosure"]["predecessor"]["workspace_uuid"]
        ):
            raise BundleError(
                "not-established",
                "Retained outcome is not the original atomic transition",
                lookup,
            )
        return verify_result(
            repository,
            checkpoint,
            envelope.get("result", {}),
            client=client,
            qualification=qualification,
        )
    if lookup.get("found") is not False:
        raise BundleError(
            "unsupported-runtime", "Outcome lookup lacks typed found state"
        )
    _, current = observed(client)
    if current != checkpoint["disclosure"]["predecessor"]:
        raise BundleError(
            "outcome-unknown",
            "Lookup miss does not disprove a historical effect; reconcile native state",
            current,
        )
    if replay:
        return execute_transition(
            repository,
            checkpoint=checkpoint,
            consent=consent,
            qualification=qualification,
            client=client,
        )
    return {
        "status": "same-request-replay-available",
        "checkpoint": checkpoint,
        "dispatch": None,
    }
