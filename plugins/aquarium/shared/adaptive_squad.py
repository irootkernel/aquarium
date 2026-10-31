"""Squad assignment scopes and consumption of original collaboration evidence."""

import copy
import json
from pathlib import Path

from adaptive_bundles import BundleError, sha256
from adaptive_preparation import member_scope, requirements

ASSESSMENT_PHASES = {
    "assess-task-plan": "task-plan",
    "assess-epic-plan": "epic-plan",
    "assess-candidate": "task-result",
    "assess-integration": "integration",
    "assess-affected": "affected-result",
}


def resolve_profiles(profiles):
    """Resolve supplied role configuration without inspecting or launching a CLI."""
    profiles = object_value(profiles, "Squad profiles")
    keys = {
        "Evaluator",
        "Epic Evaluator",
        "Task Evaluator",
        "Task Operator",
        "Task Operators",
        "Support Operators",
    }
    if set(profiles) - keys:
        raise BundleError("invalid-input", "Unknown Squad profile role")
    if "Evaluator" in profiles and any(
        key in profiles for key in ("Epic Evaluator", "Task Evaluator")
    ):
        raise BundleError(
            "invalid-input", "Common and scoped Evaluator profiles conflict"
        )
    if "Task Operator" in profiles and "Task Operators" in profiles:
        raise BundleError(
            "invalid-input", "Singular and plural Task Operator profiles conflict"
        )

    def explicit(value):
        value = object_value(value, "Explicit Squad profile")
        if set(value) - {"cli", "model", "effort"} or any(
            not isinstance(value.get(key), str) or not value[key].strip()
            for key in ("cli", "model")
        ):
            raise BundleError("invalid-input", "Explicit profiles need CLI and model")
        if "effort" in value and (
            not isinstance(value["effort"], str) or not value["effort"].strip()
        ):
            raise BundleError("invalid-input", "Explicit effort must be nonempty text")
        return {
            "route": "herdr",
            **copy.deepcopy(value),
            "effort": value.get("effort", "high"),
        }

    def native():
        return {"route": "native", "configuration": "current-coordinator"}

    def pool(key):
        values = profiles[key]
        if not isinstance(values, list) or (key == "Task Operators" and not values):
            raise BundleError(
                "invalid-input", "A Task Operator pool needs at least one profile"
            )
        return [explicit(value) for value in values]

    roles = {}
    for role in ("Epic Evaluator", "Task Evaluator"):
        key = "Evaluator" if "Evaluator" in profiles else role
        roles[role] = explicit(profiles[key]) if key in profiles else native()
    roles["Task Operators"] = (
        pool("Task Operators")
        if "Task Operators" in profiles
        else [explicit(profiles["Task Operator"])]
        if "Task Operator" in profiles
        else [native()]
    )
    roles["Support Operators"] = (
        pool("Support Operators") if "Support Operators" in profiles else []
    )
    return {"requested": copy.deepcopy(profiles), "roles": roles}


def execution_profile(assignment, display_role, scope, instance=0):
    """Bind requested configuration to one direct assignment, without a launch."""
    squad = object_value(assignment["target"].get("squad"), "target.squad")
    profiles = squad.get("profiles", {})
    resolved = resolve_profiles(profiles)["roles"]
    result = {"display_role": display_role, "scope": scope, "instance": instance}
    if display_role in {"Epic Evaluator", "Task Evaluator"}:
        key = "Evaluator" if "Evaluator" in profiles else display_role
        return {
            **result,
            **resolved[display_role],
            "requested": copy.deepcopy(profiles.get(key)),
        }
    if display_role not in {"Task Operator", "Support Operator"}:
        raise BundleError("invalid-input", "Unknown Squad assignment role")
    pool = resolved[display_role + "s"]
    if not pool:
        # An omitted/empty support pool permits an optional native factual helper.
        return {
            **result,
            "route": "native",
            "configuration": "current-coordinator",
            "requested": None,
        }
    selections = object_value(
        squad.get("profile_selections", {}), "Squad profile selections"
    )
    scopes = object_value(selections.get(display_role, {}), "Operator profile scopes")
    chosen = scopes.get(scope)
    if chosen is None and len(pool) == 1:
        index = 0
    elif not isinstance(chosen, list) or instance >= len(chosen):
        raise BundleError(
            "not-established",
            "The Coordinator must select an approved Operator profile for each assignment instance",
        )
    else:
        index = chosen[instance]
    if type(index) is not int or index < 0 or index >= len(pool):
        raise BundleError(
            "invalid-input", "Operator selection is outside its approved profile pool"
        )
    key = display_role + "s"
    requested = profiles.get(key)
    if display_role == "Task Operator" and "Task Operator" in profiles:
        requested = [profiles["Task Operator"]]
    return {
        **result,
        **copy.deepcopy(pool[index]),
        "profile_index": index if requested is not None else None,
        "requested": copy.deepcopy(requested[index]) if requested is not None else None,
    }


def assessment_execution(repository, assignment, report, reference, phase):
    """Bind mixed evidence to its original assignment and declared observations."""
    profiles = assignment["target"]["squad"].get("profiles", {})
    if not any(
        value["route"] == "herdr"
        for role in resolve_profiles(profiles)["roles"].values()
        for value in (role if isinstance(role, list) else [role])
    ):
        return None
    original = object_value(report.get("assignment"), "Original mixed assignment")
    if original.get("schema") != "aquarium.assignment/v3":
        original = artifact(repository, original)
    work = object_value(original.get("work"), "Original assignment work")
    target = object_value(original.get("target"), "Original assignment target")
    original_squad = object_value(target.get("squad"), "Original Squad assignment")
    requested = object_value(
        target.get("role_execution"), "Original role configuration"
    )
    original_authority = object_value(
        original.get("authority"), "Original assignment authority"
    )
    report_work = object_value(report.get("work"), "Original report work")
    report_target = object_value(report.get("target"), "Original report target")
    target_field = "plan" if phase.endswith("plan") else "candidate"
    if (
        original.get("schema") != "aquarium.assignment/v3"
        or object_value(target.get("procedure_plan"), "Original assignment owner").get(
            "entrypoint"
        )
        != "epic-squad"
        or original.get("role")
        != ("executor" if reference["role"] == "Task Operator" else "evaluator")
        or work.get("display_role") != reference["role"]
        or work.get("assignment_scope") != reference["scope"]
        or any(
            work.get(key) != report_work.get(key)
            for key in ("repository", "roadmap", "epic", "task")
        )
        or work.get("repository") != assignment["work"].get("repository")
        or work.get("epic") != assignment["work"].get("epic")
        or original_squad.get(target_field) != report_target.get(target_field)
        or original_squad.get("profiles", {}) != profiles
        or original_authority.get("effects") != []
        or type(requested.get("instance")) is not int
        or requested["instance"] < 0
        or requested
        != execution_profile(
            original, reference["role"], reference["scope"], requested["instance"]
        )
        or report_target.get("role_execution") != requested
    ):
        raise BundleError(
            "not-established",
            "Mixed assessment configuration differs from its original scoped assignment",
        )
    observed = object_value(
        report["native"].get("execution"), "Original execution observations"
    )
    if (
        observed.get("route") != requested["route"]
        or observed.get("requested") != requested
        or not isinstance(observed.get("profile_status"), str)
        or observed.get("profile_status") not in {"matched", "unconfirmed"}
        or observed.get("required_control_gaps") != []
        or not isinstance(observed.get("basis"), str)
        or not observed["basis"].strip()
    ):
        raise BundleError(
            "not-established",
            "Mixed assessment route, profile or required controls are unresolved",
        )
    return copy.deepcopy(observed)


def validate_mappings(binding, assignment):
    """Check custom placement scopes before source preparation or dispatch."""
    resolve_profiles(assignment["target"].get("squad", {}).get("profiles", {}))
    configured = assignment["target"]["procedure_plan"].get("squad_phases", {})
    scopes = set(ASSESSMENT_PHASES.values())
    if not isinstance(configured, dict) or any(
        node not in binding["nodes"]
        or binding["nodes"][node]["role"] != "evaluator"
        or not isinstance(scope, str)
        or scope not in scopes
        for node, scope in configured.items()
    ):
        raise BundleError(
            "incompatible",
            "Squad assessment scopes must map actual evaluator placements",
        )
    if any(
        row["role"] == "evaluator"
        and node not in ASSESSMENT_PHASES
        and node not in configured
        for node, row in binding["nodes"].items()
    ):
        raise BundleError(
            "not-established",
            "A custom Squad evaluator placement needs its actual scope mapping",
        )
    support = assignment["target"].get("squad", {}).get("support_assignments", {})
    if not isinstance(support, dict) or any(
        node not in binding["nodes"]
        or binding["nodes"][node]["role"] != "executor"
        or set(binding["nodes"][node]["effects"]) & {"work", "covered-work"}
        or not isinstance(scope, str)
        or not scope.strip()
        for node, scope in support.items()
    ):
        raise BundleError(
            "incompatible", "Support maps only explicit non-writing executor placements"
        )


def object_value(value, name):
    if not isinstance(value, dict):
        raise BundleError("invalid-input", name + " must be an object")
    return value


def artifact(repository, reference):
    reference = object_value(reference, "Squad artifact reference")
    if (
        not isinstance(reference.get("path"), str)
        or not reference["path"]
        or not isinstance(reference.get("sha256"), str)
        or type(reference.get("bytes")) is not int
        or reference["bytes"] < 0
    ):
        raise BundleError(
            "invalid-input", "Squad artifact reference needs path, sha256 and byte size"
        )
    path = Path(reference["path"])
    if not path.is_absolute():
        path = Path(repository) / path
    if path.is_symlink() or not path.is_file():
        raise BundleError(
            "not-established", "Squad evidence is not a readable regular file"
        )
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise BundleError("not-established", "Squad evidence is unreadable") from error
    if sha256(raw) != reference["sha256"] or len(raw) != reference["bytes"]:
        raise BundleError("source-drift", "Squad evidence identity changed")
    try:
        value = json.loads(raw)
    except (UnicodeError, ValueError) as error:
        raise BundleError("not-established", "Squad evidence is unreadable") from error
    return object_value(value, "Squad original artifact")


def correction_roles(classification, repository):
    classification = object_value(classification, "Current correction classification")
    depth = classification.get("depth")
    phase = classification.get("phase")
    if (
        not isinstance(depth, str)
        or depth not in {"primary-only", "bounded", "elevated"}
        or not isinstance(phase, str)
        or phase
        not in {
            "task-plan",
            "epic-plan",
            "task-result",
            "integration",
            "epic-closeout",
            "correction-group",
        }
        or type(classification.get("epic_scope_changed")) is not bool
        or not classification.get("id")
        or not classification.get("basis")
    ):
        raise BundleError(
            "not-established", "Actual correction depth and impact are required"
        )
    epic = phase in {"integration", "epic-closeout", "correction-group", "epic-plan"}
    roles = [
        ("Epic Evaluator", "affected-epic")
        if epic
        else ("Task Evaluator", "affected-result")
    ]
    roles += [("Task Operator", "affected-result")] * {
        "primary-only": 0,
        "bounded": 1,
        "elevated": 2,
    }[depth]
    if not epic and classification["epic_scope_changed"]:
        roles.append(("Epic Evaluator", "affected-epic"))
    originals = classification.get("original_assessments")
    if not isinstance(originals, list) or not originals:
        raise BundleError(
            "not-established",
            "Affected judgment needs its original assessment references",
        )
    identifiers = set()
    for reference in originals:
        reference = object_value(reference, "Original correction assessment")
        role, producer = reference.get("role"), reference.get("producer")
        identifier = reference.get("id")
        if (
            not isinstance(role, str)
            or role not in {"Task Evaluator", "Epic Evaluator", "Task Operator"}
            or not isinstance(producer, str)
            or not producer
            or not isinstance(identifier, str)
            or not identifier
            or identifier in identifiers
        ):
            raise BundleError(
                "not-established", "Original judgment owner is missing or ambiguous"
            )
        identifiers.add(identifier)
        report = artifact(repository, reference)
        native = object_value(
            report.get("native"), "Original assessment native identity"
        )
        if (
            native.get("public_handle") != reference["producer"]
            or object_value(report.get("work"), "Original assessment work").get(
                "display_role"
            )
            != reference["role"]
        ):
            raise BundleError(
                "not-established", "Original judgment owner is not established"
            )
        pair = role, "affected-epic" if role == "Epic Evaluator" else "affected-result"
        if pair not in roles:
            roles.append(pair)
    return roles


def owns_original(current, original, originals):
    """Follow only the supplied same-role reports for this unresolved owner."""
    if current["reference"]["role"] != original["role"]:
        return False
    if current["reference"]["producer"] == original["producer"]:
        return True
    visited, covered = set(), False
    while True:
        replacement = current["native"].get("replaces")
        if replacement is None:
            return covered
        if not isinstance(replacement, dict):
            return covered
        assessment = replacement.get("assessment")
        if not isinstance(assessment, str) or not assessment:
            raise BundleError(
                "invalid-input", "Replacement assessment must name its original report"
            )
        previous = originals.get(assessment)
        if (
            previous is None
            or previous["reference"]["role"] != original["role"]
            or replacement.get("public_handle") != previous["reference"]["producer"]
            or not isinstance(replacement.get("basis"), str)
            or not replacement["basis"].strip()
        ):
            return covered
        identifier = previous["reference"]["id"]
        if identifier in visited:
            return False
        visited.add(identifier)
        covered |= identifier == original["id"]
        current = previous


def finding_states(report, reference):
    findings = report.get("findings", [])
    if not isinstance(findings, list):
        raise BundleError(
            "not-established", "Original finding rows must remain readable"
        )
    result = {}
    future = reference.get("future_findings", [])
    if not isinstance(future, list) or any(
        not isinstance(identifier, str) for identifier in future
    ):
        raise BundleError(
            "not-established", "Future findings need original identifiers"
        )
    for finding in findings:
        finding = object_value(finding, "Original assessment finding")
        identifier = finding.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in result:
            raise BundleError(
                "not-established", "Original findings need unique identifiers"
            )
        status = finding.get("state", finding.get("disposition"))
        if status is not None and not isinstance(status, str):
            raise BundleError(
                "invalid-input", "Original finding state must be a string"
            )
        if identifier in future:
            applicability = finding.get("applicability")
            if not (
                isinstance(applicability, str)
                and applicability.strip()
                or finding.get("scope") == "future"
                and (finding.get("basis") or finding.get("reason"))
            ):
                raise BundleError(
                    "not-established", "Future findings need original applicability"
                )
            result[identifier] = "future"
        elif (
            (
                finding.get("blocking") is False
                or finding.get("priority") == "optional"
                or status in {"optional", "nonblocking"}
            )
            and finding.get("required") is not True
            and finding.get("blocking") is not True
        ):
            result[identifier] = "informational"
        elif status in {"met", "resolved", "rejected", "not-applicable"}:
            if not (finding.get("basis") or finding.get("reason")):
                raise BundleError(
                    "not-established", "Finding settlement needs its original basis"
                )
            result[identifier] = "met"
        else:
            result[identifier] = "unmet"
    if not set(future) <= set(result):
        raise BundleError(
            "not-established", "Future finding attribution lacks original IDs"
        )
    return result


def criterion_rows(rows):
    if not isinstance(rows, list) or not rows:
        raise BundleError("not-established", "Original criterion rows are required")
    result = {}
    for row in rows:
        row = object_value(row, "Squad criterion")
        if not isinstance(row.get("id"), str) or not row["id"]:
            raise BundleError("invalid-input", "Squad criterion needs its original ID")
        if row.get("parts") is not None and not isinstance(row["parts"], list):
            raise BundleError("invalid-input", "Squad criterion parts must be a list")
        parts = row.get("parts") or [
            {"id": "whole", "state": row.get("state"), "basis": row.get("basis")}
        ]
        parts = [object_value(part, "Squad criterion part") for part in parts]
        if (row.get("state") is not None and not isinstance(row["state"], str)) or any(
            not isinstance(part.get("state"), str) for part in parts
        ):
            raise BundleError("invalid-input", "Squad criterion states must be strings")
        if row.get("state") in {"unmet", "unverified"} and all(
            part.get("state") in {"met", "not-applicable"} for part in parts
        ):
            raise BundleError(
                "not-established",
                "Compound criterion summary conflicts with its part states",
            )
        for part in parts:
            if (
                not isinstance(part.get("id"), str)
                or not part["id"]
                or not isinstance(part.get("state"), str)
            ):
                raise BundleError(
                    "invalid-input", "Squad criterion part needs ID and state"
                )
            key = (row["id"], part["id"])
            if key in result or part.get("state") not in {
                "met",
                "unmet",
                "unverified",
                "not-applicable",
            }:
                raise BundleError(
                    "not-established", "Criterion state is missing or ambiguous"
                )
            if part["state"] == "not-applicable" and not any(
                isinstance(reason, str) and reason.strip()
                for reason in (
                    part.get("basis"),
                    part.get("reason"),
                    row.get("basis"),
                    row.get("reason"),
                )
            ):
                raise BundleError(
                    "not-established",
                    "Not-applicable parts need their original applicability reason",
                )
            result[key] = part["state"]
    return result


def assessment_rows(report, scope, expected, *, member=None):
    """Retain global states while consuming an actual scoped per-part judgment."""
    original = criterion_rows(report.get("criteria"))
    rows = {key: state for key, state in original.items() if key in expected}
    checkpoint = report.get("checkpoint_assessment")
    if checkpoint is None:
        if member is not None:
            raise BundleError(
                "not-established",
                "Member assessment needs its actual current checkpoint",
            )
        return original, rows
    checkpoint = object_value(checkpoint, "Original scoped checkpoint assessment")
    if (
        scope
        not in {
            "task-plan",
            "epic-plan",
            "epic-contribution",
            "affected-result",
            "affected-epic",
            "task-result",
            "integration",
        }
        or checkpoint.get("phase") != scope
        or not isinstance(checkpoint.get("basis"), str)
        or not checkpoint["basis"].strip()
        or not isinstance(checkpoint.get("state"), str)
        or checkpoint.get("state") not in {"met", "unmet", "unverified"}
        or not isinstance(report.get("checkpoint_result"), str)
        or report.get("checkpoint_result") not in {"pass", "fail", "inconclusive"}
    ):
        raise BundleError(
            "not-established", "Scoped assessment lacks its actual phase and judgment"
        )
    checkpoint_rows = criterion_rows(checkpoint.get("criteria"))
    if set(checkpoint_rows) != expected or not expected <= set(original):
        raise BundleError(
            "not-established", "Scoped assessment omits original due criterion parts"
        )
    if scope in {"task-result", "integration"} or (
        member is not None and scope == "epic-contribution"
    ):
        counts = {
            "due_unmet": sum(state == "unmet" for state in checkpoint_rows.values()),
            "due_unverified": sum(
                state == "unverified" for state in checkpoint_rows.values()
            ),
        }
        negative_states = {
            state
            for state in checkpoint_rows.values()
            if state in {"unmet", "unverified"}
        }
        if (
            (report["checkpoint_result"] == "pass") != (not negative_states)
            or (checkpoint["state"] == "met") != (not negative_states)
            or (negative_states and checkpoint["state"] not in negative_states)
            or (
                report["checkpoint_result"] == "inconclusive"
                and "unverified" not in negative_states
            )
            or any(
                status in {"unmet", "unverified"} and rows[key] != status
                for key, status in checkpoint_rows.items()
            )
            or any(
                field in checkpoint
                and (type(checkpoint[field]) is not int or checkpoint[field] != count)
                for field, count in counts.items()
            )
        ):
            raise BundleError(
                "not-established",
                "Checkpoint gaps are contradictory or absent from original obligations",
            )
        if member is None or scope == "integration":
            return original, rows
        applicable = {
            (row["criterion"], row["part"]): bool(row["later"] or row["gates"])
            for row in member["criteria"]
        }
        reasons = {
            (row["id"], part["id"]): part.get("applicability") or part.get("reason")
            for row in report["criteria"]
            for part in row.get("parts") or [{**row, "id": "whole"}]
        }
        for key, status in rows.items():
            if status == "unverified" and checkpoint_rows[key] in {
                "met",
                "not-applicable",
            }:
                if (
                    not applicable[key]
                    or not isinstance(reasons.get(key), str)
                    or not reasons[key].strip()
                ):
                    raise BundleError(
                        "not-established",
                        "Member passage lacks original future applicability",
                    )
                rows[key] = checkpoint_rows[key]
        return original, rows
    rows = checkpoint_rows
    applicability = {
        (row["id"], part["id"]): part.get("applicability") or part.get("reason")
        for row in report["criteria"]
        for part in row.get("parts") or [{**row, "id": "whole"}]
    }
    if any(
        original[key] in {"unmet", "unverified"}
        and state in {"met", "not-applicable"}
        and not (isinstance(applicability.get(key), str) and applicability[key].strip())
        for key, state in rows.items()
    ):
        raise BundleError(
            "not-established",
            "Future global parts lack their original scoped applicability",
        )
    if (
        report["checkpoint_result"] != "pass"
        or checkpoint.get("state") in {"unmet", "unverified"}
        or any(
            checkpoint.get(field, 0) != 0 for field in ("due_unmet", "due_unverified")
        )
    ) and all(state in {"met", "not-applicable"} for state in rows.values()):
        raise BundleError(
            "not-established", "Scoped checkpoint judgment remains unresolved"
        )
    return original, rows


def closeout_scope(repository, report, *, moved=False):
    """Resolve original purpose; generic affected-Epic metadata is not closeout."""
    target = object_value(report.get("target"), "Original assessment target")
    contexts = []
    if "squad" in target:
        contexts.append(target["squad"])
    assigned = report.get("assignment")
    if (
        isinstance(assigned, dict)
        and assigned.get("schema") != "aquarium.assignment/v3"
    ):
        reference = assigned
        assigned = None
        if isinstance(reference.get("path"), str) and isinstance(
            reference.get("sha256"), str
        ):
            path = Path(reference["path"])
            if not path.is_absolute():
                path = Path(repository) / path
            # This optional ordinary provenance is not a required Squad artifact.
            # If available, its declared identity must still agree with its bytes.
            if path.is_symlink():
                raise BundleError(
                    "not-established", "Original assignment is not a regular file"
                )
            if path.is_file():
                try:
                    raw = path.read_bytes()
                except OSError:
                    raw = None
                if raw is not None:
                    digest = reference["sha256"]
                    if not digest.startswith("sha256:"):
                        digest = "sha256:" + digest
                    if sha256(raw) != digest or (
                        "bytes" in reference and reference["bytes"] != len(raw)
                    ):
                        raise BundleError(
                            "source-drift", "Original assignment identity changed"
                        )
                    try:
                        assigned = json.loads(raw)
                    except (UnicodeError, ValueError) as error:
                        raise BundleError(
                            "not-established", "Original assignment is unreadable"
                        ) from error
                    assigned = object_value(assigned, "Original ordinary assignment")
    if (
        isinstance(assigned, dict)
        and assigned.get("schema") == "aquarium.assignment/v3"
    ):
        original_target = object_value(
            assigned.get("target"), "Original closeout assignment target"
        )
        if "squad" in original_target:
            contexts.append(original_target["squad"])
    # Dispatch supplies semantic scope even when its copied work-unit metadata is
    # coarser. It cannot establish first closeout coverage across a later delta.
    work_contexts = (
        report.get("work"),
        assigned.get("work") if isinstance(assigned, dict) else None,
    )
    if moved and any(
        isinstance(work, dict)
        and work.get("assignment_scope")
        in {
            "integration",
            "epic-plan",
            "task-plan",
            "task-result",
            "epic-contribution",
            "affected-result",
        }
        for work in work_contexts
    ):
        return False
    purposes = []
    closeout_phase = False
    for context in contexts:
        if not isinstance(context, dict):
            return False
        if "candidate" in context and context["candidate"] != target.get("candidate"):
            return False
        if context.get("work_unit_kind") is not None:
            purposes.append(context["work_unit_kind"] == "epic-closeout")
        correction = context.get("correction")
        if correction is not None:
            if not isinstance(correction, dict):
                return False
            if correction.get("phase") is not None:
                purposes.append(correction["phase"] == "epic-closeout")
                closeout_phase = correction["phase"] == "epic-closeout"
    # Read all original provenance before accepting an affirmative report context.
    if False in purposes:
        return False
    if (
        moved
        and not closeout_phase
        and not any(
            isinstance(work, dict) and work.get("assignment_scope") == "affected-epic"
            for work in work_contexts
        )
    ):
        return None
    return True if purposes else None


def original_reference(reference):
    return {
        key: value
        for key, value in reference.items()
        if key not in {"applicability", "applicability_evidence"}
    }


def composition(
    repository, assignment, value, *, plan_compositions=None, source_reader=None
):
    """Verify a current basis; never turn a source rework verdict into a new pass."""
    value = object_value(value, "Squad composition")
    if assignment["target"]["procedure_plan"][
        "entrypoint"
    ] != "epic-squad" or assignment["authority"]["review"].get("route") not in {
        "not-required",
        "herdr",
        "mulgae",
        "subagent-review",
        "waived",
    }:
        raise BundleError(
            "incompatible",
            "Current composition belongs only to the real Squad owner and selected route",
        )
    squad = object_value(assignment["target"].get("squad"), "target.squad")
    phase = value.get("phase")
    if not isinstance(phase, str) or phase not in {
        "task-plan",
        "epic-plan",
        "task-result",
        "integration",
        "epic-closeout",
        "correction-group",
    }:
        raise BundleError("invalid-input", "Unknown Squad composition scope")
    target = squad.get("plan") if phase.endswith("plan") else squad.get("candidate")
    if not isinstance(target, str) or not target or value.get("target") != target:
        raise BundleError("source-drift", "Squad composition target is not current")
    risk = squad.get("risk")
    if not isinstance(risk, str) or risk not in {"standard", "elevated"}:
        raise BundleError(
            "not-established", "The Task risk and its assessment scope are required"
        )
    prepared = (
        assignment["target"]
        .get("prepared_definition", {})
        .get("coverage_plan", {})
        .get("criteria")
    )
    original = requirements(
        repository,
        assignment,
        verify_sources=prepared is None and source_reader is None,
        source_reader=source_reader,
    )
    if prepared is not None and original != prepared:
        raise BundleError(
            "source-drift", "Original requirement meaning changed after qualification"
        )
    scoped = member_scope(assignment, original)
    if prepared is not None and (
        assignment["target"]["prepared_definition"]["coverage_plan"].get("member_scope")
        != scoped
    ):
        raise BundleError(
            "source-drift", "Assessed member scope changed after preparation"
        )
    member = (
        scoped
        if squad.get("work_unit_kind") in {"member-task", "pre-validation-remediation"}
        and assignment["target"]["procedure_plan"]["family"] == "goal"
        and phase in {"task-plan", "epic-plan", "task-result"}
        else None
    )
    if member is not None:
        if value.get("member_scope") != member:
            raise BundleError(
                "not-established", "Composition lacks its actual member basis"
            )
        if phase == "task-result":
            plans = (
                plan_compositions
                if plan_compositions is not None
                else squad.get("compositions", {})
            )
            plans = object_value(plans, "Actual independent member plan bases")
            for due in ("task-plan", "epic-plan"):
                matches = [
                    row
                    for row in plans.values()
                    if isinstance(row, dict) and row.get("phase") == due
                ]
                if (
                    len(matches) != 1
                    or composition(
                        repository, assignment, matches[0], source_reader=source_reader
                    )["status"]
                    != "ready"
                ):
                    raise BundleError(
                        "not-established",
                        "Both actual independent member plans must be ready",
                    )
    expected = {
        (key, part["id"]) for key, row in original.items() for part in row["parts"]
    }
    current = criterion_rows(value.get("criteria"))
    if set(current) != expected:
        raise BundleError(
            "not-established", "Current composition omits original criterion parts"
        )
    refs = value.get("assessments")
    if not isinstance(refs, list) or not refs:
        raise BundleError(
            "not-established", "Actual independent first assessments are required"
        )
    author_rows = squad.get("authors", [])
    if not isinstance(author_rows, list) or any(
        not isinstance(author, str) for author in author_rows
    ):
        raise BundleError("invalid-input", "Original authors must be a list of handles")
    authors = set(author_rows)
    if not authors:
        raise BundleError(
            "not-established", "Original plan and implementation authors are required"
        )
    sources, producers, gaps = {}, {}, []
    execution_records = {}
    for ref in refs:
        ref = object_value(ref, "Squad assessment")
        identity = ref.get("id")
        if not isinstance(identity, str) or not identity or identity in sources:
            raise BundleError(
                "invalid-input", "Assessment references need unique original IDs"
            )
        report = artifact(repository, ref)
        role = ref.get("role")
        producer = ref.get("producer")
        if (
            not isinstance(role, str)
            or role not in {"Task Evaluator", "Epic Evaluator", "Task Operator"}
            or not isinstance(producer, str)
            or not producer
            or producer in authors
            or object_value(report.get("work"), "Original assessment work").get(
                "display_role"
            )
            != role
            or object_value(
                report.get("native"), "Original assessment native identity"
            ).get("public_handle")
            != producer
            or report.get("schema")
            != (
                "aquarium.executor-handoff/v3"
                if role == "Task Operator"
                else "aquarium.evaluator-assessment/v3"
            )
        ):
            raise BundleError(
                "not-established",
                "Independent original producer and role are not established",
            )
        scope = ref.get("scope")
        if (
            not isinstance(scope, str)
            or not isinstance(ref.get("target"), str)
            or not isinstance(ref.get("applicability"), str)
        ):
            raise BundleError(
                "invalid-input",
                "Assessment needs scope, target and applicability strings",
            )
        execution = assessment_execution(repository, assignment, report, ref, phase)
        if execution is not None:
            execution_records[identity] = execution
        source_target = object_value(
            report.get("target"), "Original assessment target"
        ).get("plan" if phase.endswith("plan") else "candidate")
        if (
            source_target != ref.get("target")
            or ref.get("applicability") not in {"current", "preserved"}
            or not ref.get("basis")
        ):
            raise BundleError(
                "not-established",
                "Assessment target or current applicability is missing",
            )
        verdict = report.get("verdict")
        if not isinstance(verdict, str) or verdict not in {
            "pass",
            "rework",
            "evidence-needed",
        }:
            raise BundleError(
                "not-established", "Original assessment verdict is unavailable"
            )
        if (
            member is not None
            and object_value(report.get("target"), "Assessment target").get(
                "member_scope"
            )
            != member
        ):
            raise BundleError(
                "source-drift", "Assessment does not cover the current member basis"
            )
        all_rows, rows = assessment_rows(report, scope, expected, member=member)
        future_rows = ref.get("future_criteria", [])
        if not isinstance(future_rows, list) or any(
            not isinstance(identifier, str) for identifier in future_rows
        ):
            raise BundleError(
                "invalid-input", "Future criteria must retain their original IDs"
            )
        future = set(future_rows)
        if any(key[0] not in future for key in set(all_rows) - expected):
            raise BundleError(
                "incompatible",
                "Unassigned criterion rows need explicit future-scope attribution",
            )
        negative = [
            key for key, state in rows.items() if state in {"unmet", "unverified"}
        ]
        findings = finding_states(report, ref)
        due_findings = {key for key, state in findings.items() if state == "unmet"}
        scoped_future = (
            any(
                state in {"unmet", "unverified"}
                and (key not in expected or rows.get(key) in {"met", "not-applicable"})
                for key, state in all_rows.items()
            )
            or "future" in findings.values()
        )
        if (
            verdict != "pass"
            and not negative
            and not due_findings
            and not (
                scoped_future
                and report.get("checkpoint_result") == "pass"
                and (
                    member is None
                    or verdict != "rework"
                    or "future" in findings.values()
                )
            )
        ):
            gaps.append(
                {"assessment": identity, "reason": "unresolved-negative-verdict"}
            )
        if source_target != target and ref["applicability"] != "preserved":
            raise BundleError(
                "source-drift",
                "Changed assessment target lacks preserved-scope evidence",
            )
        if source_target != target:
            applicability = artifact(repository, ref.get("applicability_evidence"))
            if (
                applicability.get("before") != source_target
                or applicability.get("after") != target
                or applicability.get("outcome") != "pass"
                or applicability.get("preserved_scope") != scope
                or not applicability.get("checks")
                or applicability.get("unknown_impact") is not False
            ):
                raise BundleError(
                    "not-established",
                    "Changed assessment basis lacks current preserved-scope proof",
                )
        closeout_applicable = source_target == target
        if (
            phase == "epic-closeout"
            and role == "Epic Evaluator"
            and scope == "affected-epic"
        ):
            original_scope = closeout_scope(
                repository, report, moved=source_target != target
            )
            if original_scope is False:
                closeout_applicable = False
            elif source_target != target:
                closeout_applicable = (
                    original_scope is True
                    and applicability.get("source_assessment")
                    == original_reference(ref)
                    and applicability.get("local_eligible") is True
                    and applicability.get("record_only") is True
                    and applicability.get("meaning_preserved") is True
                    and applicability.get("unresolved_judgment") is False
                    and bool(applicability.get("delta"))
                    and bool(applicability.get("basis"))
                )
        sources[identity] = {
            "reference": ref,
            "closeout_applicable": closeout_applicable,
            "verdict": verdict,
            "rows": rows,
            "original_criteria": copy.deepcopy(report["criteria"]),
            "original_findings": copy.deepcopy(report.get("findings", [])),
            "findings": findings,
            "native": copy.deepcopy(report["native"]),
            "scoped_pass": report.get("checkpoint_result") == "pass"
            if report.get("checkpoint_assessment") is not None
            else verdict == "pass",
        }
        producers.setdefault((role, scope), set()).add(producer)
        gaps += [
            {"assessment": identity, "criterion": key[0], "part": key[1]}
            for key in negative
        ]
        gaps += [{"assessment": identity, "finding": key} for key in due_findings]
    reviewers = 2 if risk == "elevated" or phase == "integration" else 1
    required = {
        "task-plan": [
            ("Task Evaluator", "task-plan", 1),
            ("Task Operator", "task-plan", reviewers),
        ],
        "epic-plan": [("Epic Evaluator", "epic-plan", 1)],
        "task-result": [
            ("Task Evaluator", "task-result", 1),
            ("Task Operator", "task-result", reviewers),
            ("Epic Evaluator", "epic-contribution", 1),
        ],
        "integration": [
            ("Epic Evaluator", "integration", 1),
            ("Task Operator", "integration", 2),
        ],
        "epic-closeout": [
            ("Epic Evaluator", "integration", 1),
            ("Task Operator", "integration", 2),
            ("Epic Evaluator", "affected-epic", 1),
        ],
        "correction-group": [("Epic Evaluator", "integration", 1)],
    }[phase]
    if phase == "correction-group" and not any(
        source["reference"]["role"] == "Epic Evaluator"
        and source["reference"]["scope"] == "integration"
        and (
            any(state in {"unmet", "unverified"} for state in source["rows"].values())
            or "unmet" in source["findings"].values()
        )
        for source in sources.values()
    ):
        raise BundleError(
            "not-established",
            "Correction groups retain their original integration audit obligations",
        )
    required_producers = []
    for role, scope, count in required:
        handles = producers.get((role, scope), set())
        covered = set().union(
            *(
                set(source["rows"])
                for source in sources.values()
                if (source["reference"]["role"], source["reference"]["scope"])
                == (role, scope)
            )
        )
        if len(handles) < count or covered != expected:
            raise BundleError(
                "not-established",
                "Required independent Squad assessment scope is missing",
            )
        if phase == "epic-closeout" and scope == "affected-epic":
            if not any(
                source["reference"]["role"] == role
                and source["reference"]["scope"] == scope
                and source["closeout_applicable"]
                and set(source["rows"]) == expected
                for source in sources.values()
            ):
                raise BundleError(
                    "not-established",
                    "Final closeout needs an actual applicable Epic assessment",
                )
            # Only the same logical EE lane may coincide with the integration EE.
            # Fresh independent EEs remain distinct from all integration TOs.
            required_producers.extend(
                handles - producers.get(("Epic Evaluator", "integration"), set())
            )
        else:
            required_producers.extend(handles)
    if len(set(required_producers)) != len(required_producers):
        raise BundleError(
            "incompatible",
            "One report producer cannot fill distinct independent role instances",
        )
    closures = value.get("closures", [])
    if not isinstance(closures, list):
        raise BundleError("invalid-input", "Squad closures must be a list")
    settled = set()
    for closure in closures:
        closure = object_value(closure, "Squad closure")
        if any(
            closure.get(field) is not None and not isinstance(closure[field], str)
            for field in ("assessment", "criterion", "part", "finding", "disposition")
        ):
            raise BundleError(
                "invalid-input", "Closure obligation identifiers must be strings"
            )
        key = (
            closure.get("assessment"),
            closure.get("criterion"),
            closure.get("part"),
            closure.get("finding"),
        )
        source = sources.get(key[0])
        named = key[3] is not None
        obligation = source is not None and (
            source["findings"].get(key[3]) == "unmet" and key[1:3] == (None, None)
            if named
            else source["rows"].get(key[1:3]) in {"unmet", "unverified"}
        )
        if (
            key in settled
            or source is None
            or not obligation
            or closure.get("before") != source["reference"]["target"]
            or not isinstance(closure.get("after"), str)
            or closure.get("disposition")
            not in {"local-verified-fix", "affected-assessment"}
            or not closure.get("basis")
            or not closure.get("owner")
        ):
            raise BundleError(
                "not-established",
                "Closure lacks an exact original obligation and eligible delta",
            )
        proof = artifact(repository, closure.get("verification"))
        if (
            proof.get("outcome") != "pass"
            or proof.get("before") != closure["before"]
            or proof.get("after") != closure["after"]
            or proof.get("unresolved_judgment") is not False
            or not proof.get("delta")
            or not proof.get("checks")
        ):
            raise BundleError(
                "not-established", "Current finite local verification is incomplete"
            )
        carry = None
        if closure["after"] != target:
            carry = artifact(repository, closure.get("applicability_evidence"))
            original_closure = original_reference(closure)
            contextual = "before_context" in carry or "after_context" in carry
            before_context = carry.get("before_context")
            preserved_context = (
                isinstance(before_context, dict)
                and set(before_context)
                == {"inputs", "coverage", "dependencies", "environment", "judgment"}
                and all(
                    item and (not isinstance(item, str) or item.strip())
                    for item in before_context.values()
                )
                and before_context == carry.get("after_context")
                and isinstance(carry.get("checks"), list)
                and isinstance(value.get("checks"), list)
                and all(
                    isinstance(check, str)
                    and any(
                        isinstance(row, dict) and row.get("id") == check
                        for row in value["checks"]
                    )
                    for check in carry["checks"]
                )
            )
            preserved_delta = (
                preserved_context
                if contextual
                else (
                    carry.get("local_eligible") is True
                    and carry.get("record_only") is True
                )
            )
            if (
                closure.get("applicability") != "preserved"
                or carry.get("source_closure") != original_closure
                or carry.get("before") != closure["after"]
                or carry.get("after") != target
                or carry.get("current_scope") != phase
                or carry.get("outcome") != "pass"
                or carry.get("unknown_impact") is not False
                or not preserved_delta
                or carry.get("meaning_preserved") is not True
                or carry.get("unresolved_judgment") is not False
                or not carry.get("delta")
                or not carry.get("checks")
                or not carry.get("basis")
            ):
                raise BundleError(
                    "not-established",
                    "Settled closure lacks exact current applicability",
                )
        if closure["disposition"] == "local-verified-fix":
            if proof.get("local_eligible") is not True:
                raise BundleError(
                    "not-established",
                    "Local closure cannot bypass required independent judgment",
                )
        else:
            classification = object_value(
                proof.get("correction"), "Original correction classification"
            )
            due = correction_roles(classification, repository)
            identity_fields = (
                "id",
                "role",
                "producer",
                "scope",
                "target",
                "path",
                "sha256",
                "bytes",
            )
            originals = {}
            for reference in classification["original_assessments"]:
                original = sources.get(reference["id"])
                if original is None or any(
                    reference.get(field) != original["reference"].get(field)
                    for field in identity_fields
                ):
                    raise BundleError(
                        "not-established",
                        "Affected classification lacks its exact original reports",
                    )
                originals[reference["id"]] = original
            if source["reference"]["id"] not in originals:
                raise BundleError(
                    "not-established",
                    "Affected classification does not identify the original obligation",
                )
            if classification["phase"] != phase and (
                classification["phase"],
                phase,
            ) not in {
                ("correction-group", "integration"),
                ("correction-group", "epic-closeout"),
                ("integration", "epic-closeout"),
            }:
                raise BundleError(
                    "not-established",
                    "Affected correction scope differs from the current composition",
                )
            assessment_ids = proof.get("assessments")
            if not isinstance(assessment_ids, list) or any(
                not isinstance(identifier, str) for identifier in assessment_ids
            ):
                raise BundleError(
                    "invalid-input",
                    "Affected confirmation must identify its original reports",
                )
            confirmation = [sources.get(identifier) for identifier in assessment_ids]
            if not confirmation or any(source is None for source in confirmation):
                raise BundleError(
                    "not-established",
                    "Affected closure lacks original independent delta reports",
                )
            if carry is not None and (
                carry.get("preserved_scope") != classification["phase"]
                or carry.get("confirmations")
                != [original_reference(source["reference"]) for source in confirmation]
            ):
                raise BundleError(
                    "not-established",
                    "Closure applicability lacks its exact original confirmation scope and reports",
                )
            covered = {}
            for current_source in confirmation:
                ref = current_source["reference"]
                if (
                    ref["target"] != closure["after"]
                    or not current_source["scoped_pass"]
                    or (
                        current_source["findings"].get(key[3]) != "met"
                        if named
                        else current_source["rows"].get(key[1:3])
                        not in {"met", "not-applicable"}
                    )
                ):
                    raise BundleError(
                        "not-established",
                        "Affected judgment does not cover the exact corrected obligation",
                    )
                covered.setdefault((ref["role"], ref["scope"]), set()).add(
                    ref["producer"]
                )
            if any(
                len(covered.get(pair, set())) < due.count(pair) for pair in set(due)
            ):
                raise BundleError(
                    "not-established",
                    "The required affected panel or EE scope is missing",
                )
            handles = [covered[pair] for pair in set(due)]
            if len(set().union(*handles)) != sum(len(group) for group in handles):
                raise BundleError(
                    "incompatible",
                    "Affected roles require distinct independent instances",
                )
            original = source["reference"]
            owner_scope = (
                "affected-epic"
                if original["role"] == "Epic Evaluator"
                else "affected-result"
            )
            owner_present = any(
                current_source["reference"]["scope"] == owner_scope
                and owns_original(current_source, original, originals)
                for current_source in confirmation
            )
            if not owner_present:
                raise BundleError(
                    "not-established",
                    "The unresolved original assessor or supported replacement is missing",
                )
        settled.add(key)
    gaps = [
        gap
        for gap in gaps
        if (
            gap.get("assessment"),
            gap.get("criterion"),
            gap.get("part"),
            gap.get("finding"),
        )
        not in settled
    ]
    required_checks = squad.get("required_checks")
    if isinstance(required_checks, dict):
        required_checks = required_checks.get(phase)
    checks = value.get("checks")
    if not isinstance(required_checks, list) or not isinstance(checks, list):
        raise BundleError(
            "not-established",
            "The due check inventory and actual receipts are required",
        )
    policies = {}
    for entry in required_checks:
        if isinstance(entry, str):
            identifier, policy = entry, {"execution": "current-target"}
        else:
            policy = object_value(entry, "Due check policy")
            identifier = policy.get("id")
            if (
                not isinstance(policy.get("execution"), str)
                or policy.get("execution")
                not in {
                    "current-target",
                    "reusable",
                }
                or not policy.get("basis")
            ):
                raise BundleError(
                    "not-established", "Due check reuse policy is unknown"
                )
        if not isinstance(identifier, str) or not identifier or identifier in policies:
            raise BundleError("not-established", "Due check identities are ambiguous")
        policies[identifier] = policy
    observed = set()
    for ref in checks:
        ref = object_value(ref, "Squad check reference")
        if not isinstance(ref.get("id"), str) or not ref["id"]:
            raise BundleError("invalid-input", "Squad check needs its original ID")
        check = artifact(repository, ref)
        if (
            not check.get("target")
            or not check.get("command")
            or check.get("outcome") != "pass"
        ):
            raise BundleError(
                "not-established", "A due check is stale, missing or negative"
            )
        if check["target"] != target:
            proof = artifact(repository, ref.get("applicability_evidence"))
            before_context = object_value(
                proof.get("before_context"), "Original check execution context"
            )
            after_context = object_value(
                proof.get("after_context"), "Current comparable check context"
            )
            original_ref = {
                key: value
                for key, value in ref.items()
                if key not in {"applicability", "applicability_evidence"}
            }
            if (
                policies.get(ref.get("id"), {}).get("execution") != "reusable"
                or ref.get("applicability") != "preserved"
                or proof.get("before") != check["target"]
                or proof.get("after") != target
                or proof.get("outcome") != "pass"
                or proof.get("unknown_impact") is not False
                or proof.get("check_id") != ref.get("id")
                or proof.get("preserved_scope") != phase
                or proof.get("source_check") != original_ref
                or not proof.get("basis")
                or set(before_context)
                != {"command", "coverage", "inputs", "dependencies", "environment"}
                or before_context != after_context
                or before_context["command"] != check["command"]
                or any(
                    value is None or isinstance(value, str) and not value.strip()
                    for value in before_context.values()
                )
            ):
                raise BundleError(
                    "not-established",
                    "Prior check lacks exact current applicability or needs current execution",
                )
        observed.add(ref.get("id"))
    if not set(policies) <= observed:
        raise BundleError("not-established", "A mandatory check has not executed")
    pending = object_value(value.get("pending"), "Squad pending obligations")
    if set(pending) != {"local", "low", "blocking", "judgment"} or any(
        type(count) is not int or count < 0 for count in pending.values()
    ):
        raise BundleError(
            "not-established", "Outstanding obligation counts are incomplete"
        )
    gaps += [
        {"criterion": key[0], "part": key[1]}
        for key, state in current.items()
        if state in {"unmet", "unverified"}
    ]
    ready = not gaps and not any(pending.values())
    return {
        "status": "ready" if ready else "unresolved",
        "phase": phase,
        "target": target,
        **({"member_scope": copy.deepcopy(member)} if member is not None else {}),
        "original_verdicts": {
            key: source["verdict"] for key, source in sources.items()
        },
        "original_criteria": {
            key: source["original_criteria"] for key, source in sources.items()
        },
        "original_findings": {
            key: source["original_findings"] for key, source in sources.items()
        },
        "whole_epic_confirmation": "pending" if phase == "correction-group" else None,
        "assessments": copy.deepcopy(refs),
        "closures": copy.deepcopy(closures),
        "checks": copy.deepcopy(checks),
        "current_criteria": copy.deepcopy(value["criteria"]),
        "pending": copy.deepcopy(pending),
        "gaps": gaps,
        "new_evaluator_verdict": None,
        "additional_review": assignment["authority"]["review"]["route"],
        "role_execution": execution_records,
        "native_values": {
            "composition-scope": phase,
            "composition-goal-outcome": "achieved"
            if ready and not phase.endswith("plan") and phase != "correction-group"
            else "not-achieved",
            "composition-unmet": sum(state == "unmet" for state in current.values()),
            "composition-unverified": sum(
                state == "unverified" for state in current.values()
            ),
            "pending-local": pending["local"],
            "pending-low": pending["low"],
            "current-blockers": pending["blocking"] + len(gaps),
            "pending-judgment": pending["judgment"],
            "composition-current": {"outcome": "pass" if ready else "fail"},
        },
    }


def composition_record(
    repository, assignment, value, *, availability=True, source_reader=None
):
    """Expose failed consumption for native recording without inventing counts."""
    try:
        current = composition(
            repository, assignment, value, source_reader=source_reader
        )
        if availability:
            current["native_values"]["composition-evidence"] = "established"
        return {"composition": current}
    except BundleError as error:
        if not availability:
            raise
        phase = value.get("phase") if isinstance(value, dict) else None
        native = {
            "composition-evidence": "unavailable",
            "composition-current": {"outcome": "inconclusive"},
            "composition-goal-outcome": "not-achieved",
        }
        if isinstance(phase, str) and phase in {
            "task-plan",
            "epic-plan",
            "task-result",
            "integration",
            "correction-group",
            "epic-closeout",
        }:
            native["composition-scope"] = phase
        return {
            "composition_error": {
                "code": error.code,
                "message": str(error),
                "details": copy.deepcopy(error.details),
                "phase": phase,
                "target": value.get("target") if isinstance(value, dict) else None,
                "basis": copy.deepcopy(value),
                "criterion_counts": None,
                "native_values": native,
            }
        }


def assignments(assignment, node, role, effects=(), *, reentry=False):
    """Return direct assignment scopes; the Coordinator launches and joins them."""
    squad = object_value(assignment["target"].get("squad"), "target.squad")
    resolved = resolve_profiles(squad.get("profiles", {}))
    if any(
        profile["route"] == "herdr"
        for value in resolved["roles"].values()
        for profile in (value if isinstance(value, list) else [value])
    ):
        raise BundleError(
            "not-established",
            "Explicit Squad profiles require the pending Herdr execution, commit and recovery integration; preserve the request and obtain user direction for any alternative",
        )
    support = squad.get("support_assignments", {})
    if node in support:
        if (
            role != "executor"
            or set(effects) & {"work", "covered-work"}
            or not isinstance(support[node], str)
            or not support[node].strip()
        ):
            raise BundleError(
                "incompatible",
                "Support assignment must be an explicit factual execution scope without product writes",
            )
        return [("Support Operator", support[node])]
    phases = {
        **ASSESSMENT_PHASES,
        **assignment["target"]["procedure_plan"].get("squad_phases", {}),
    }
    scope = phases.get(node)
    correction = squad.get("correction")
    if (
        reentry
        and scope in {"task-plan", "epic-plan"}
        and isinstance(correction, dict)
        and correction.get("phase") == scope
    ):
        return correction_roles(correction, assignment["work"]["repository"])
    if scope == "epic-plan":
        return [("Epic Evaluator", scope)]
    if scope == "affected-result":
        return correction_roles(
            squad.get("correction"), assignment["work"]["repository"]
        )
    if scope is None:
        if role == "evaluator":
            raise BundleError(
                "not-established", "The Squad evaluator's actual scope is not mapped"
            )
        return [("Task Operator", node)]
    if squad.get("risk") not in {"standard", "elevated"}:
        raise BundleError(
            "not-established", "Current Task risk is required before panel dispatch"
        )
    roles = [("Epic Evaluator" if scope == "integration" else "Task Evaluator", scope)]
    roles += [("Task Operator", scope)] * (
        2 if squad["risk"] == "elevated" or scope == "integration" else 1
    )
    if scope == "task-result":
        roles.append(("Epic Evaluator", "epic-contribution"))
    return roles


def commit_handoff(repository, value):
    """Consume exact acceptance and an existing grant without executing a commit."""
    value = object_value(value, "Squad commit input")
    from adaptive_execution import ordinary

    assignment = ordinary(object_value(value.get("assignment"), "Squad invocation"))
    if assignment["target"]["procedure_plan"]["entrypoint"] != "epic-squad":
        raise BundleError(
            "incompatible", "Squad commit consumption requires its real owner"
        )
    recovery = assignment["target"].get("applied_source_context")
    source_reader = None
    if recovery is not None:
        from adaptive_finalization import approved_original_sources

        def recover():
            return approved_original_sources(
                Path(repository).resolve(), assignment, recovery
            )

        source_reader, source_context = recover()
    current = composition(
        repository,
        assignment,
        value.get("composition"),
        plan_compositions=value.get("plan_compositions"),
        source_reader=source_reader,
    )
    if current["status"] != "ready" or current["phase"].endswith("plan"):
        raise BundleError(
            "not-established", "Exact current completion composition is not ready"
        )
    work_kind = assignment["target"]["squad"].get("work_unit_kind")
    due_phase = {
        "member-task": "task-result",
        "pre-validation-remediation": "task-result",
        "validation-remediation": "correction-group",
        "epic-closeout": "epic-closeout",
    }.get(work_kind)
    if due_phase is None or current["phase"] != due_phase:
        raise BundleError(
            "not-established", "Completion scope does not match the current work unit"
        )
    acceptance = object_value(value.get("acceptance"), "Squad exact acceptance")
    grant = object_value(value.get("grant"), "Squad commit grant")
    grants = assignment["authority"].get("commit_grants", [])
    kind = {
        "member-task": "member",
        "pre-validation-remediation": "correction",
        "validation-remediation": "correction",
        "epic-closeout": "conditional-closeout",
    }.get(assignment["target"]["squad"].get("work_unit_kind"))
    if (
        acceptance.get("decision") != "approved"
        or acceptance.get("source") not in {"user", "epic-delegation"}
        or not acceptance.get("authority")
        or acceptance.get("target") != current["target"]
        or not isinstance(grants, list)
        or sum(row == grant for row in grants) != 1
        or grant.get("consumed") is not False
        or grant.get("owner") != "aquarium:epic-squad"
        or grant.get("epic") != assignment["work"].get("epic")
        or grant.get("task") != assignment["work"].get("task")
        or kind is None
        or grant.get("kind") != kind
        or not grant.get("id")
    ):
        raise BundleError(
            "authority-required",
            "Exact acceptance and distinct unconsumed scoped grant are required",
        )
    if assignment["target"]["squad"]["work_unit_kind"] in {
        "member-task",
        "pre-validation-remediation",
    }:
        plans = object_value(
            value.get("plan_compositions"), "Current independent plan bases"
        )
        for scope in ("task-plan", "epic-plan"):
            plan = composition(
                repository, assignment, plans.get(scope), source_reader=source_reader
            )
            if plan["phase"] != scope or plan["status"] != "ready":
                raise BundleError(
                    "not-established",
                    "Both actual independent plan scopes remain due before commit",
                )
    if grant["kind"] == "conditional-closeout" and (
        acceptance["source"] != "user" or current["phase"] != "epic-closeout"
    ):
        raise BundleError(
            "authority-required", "Final Epic closeout needs actual user acceptance"
        )
    if current["phase"] == "epic-closeout" and grant["kind"] != "conditional-closeout":
        raise BundleError(
            "authority-required",
            "A member/correction grant cannot settle final Epic closeout",
        )
    review = artifact(repository, acceptance.get("product_review"))
    if (
        review.get("target") != current["target"]
        or review.get("actor") != "Coordinator"
        or review.get("verdict") != "pass"
        or not review.get("basis")
    ):
        raise BundleError(
            "not-established", "Current Coordinator product review is required"
        )
    for field in ("lifecycle_decision", "record_decision", "release_note_decision"):
        if not acceptance.get(field):
            raise BundleError(
                "not-established", "Exact closeout decisions must accompany acceptance"
            )
    route = current["additional_review"]
    review_due = True
    source_review = None
    if current["phase"] == "correction-group" and route != "not-required":
        boundary = artifact(repository, value.get("review_boundary"))
        if (
            boundary.get("target") != current["target"]
            or boundary.get("phase") != "correction-group"
            or boundary.get("route") != route
            or type(boundary.get("due")) is not bool
            or not boundary.get("authority")
            or not boundary.get("basis")
            or boundary.get("whole_epic_confirmation") != "pending"
        ):
            raise BundleError(
                "not-established",
                "The actual correction-group review boundary is unknown",
            )
        review_due = boundary["due"]
        if not review_due:
            if any(
                value.get(field) is not None
                for field in (
                    "technical_review",
                    "assessment_ordinal",
                    "assessment_kind",
                    "provider_operation",
                )
            ):
                raise BundleError(
                    "incompatible",
                    "A pending whole-Epic review has no current group operation",
                )
            source_review = value.get("source_review")
            if source_review is not None:
                source_review = object_value(source_review, "Original source review")
                if (
                    source_review.get("route") != route
                    or source_review.get("operation") not in {"complete", "waived"}
                    or type(source_review.get("ordinal")) is not int
                    or source_review["ordinal"] < 1
                    or not source_review.get("target")
                    or not source_review.get("original_verdict")
                    or not source_review.get("authority")
                ):
                    raise BundleError(
                        "not-established",
                        "Source review history lacks its original operation",
                    )
                artifact(repository, source_review.get("evidence"))
    if route == "not-required":
        if (
            value.get("assessment_ordinal") is not None
            or value.get("provider_operation") is not None
            or value.get("technical_review") is not None
        ):
            raise BundleError(
                "incompatible",
                "No additional technical review has no provider operation or ordinal",
            )
    elif review_due:
        technical = object_value(
            value.get("technical_review"), "Selected technical review"
        )
        ordinal = value.get("assessment_ordinal")
        if (
            technical.get("route") != route
            or not isinstance(technical.get("target"), str)
            or not technical["target"]
            or not technical.get("original_verdict")
            or value.get("provider_operation")
            != ("waived" if route == "waived" else "complete")
            or type(ordinal) is not int
            or ordinal < 1
            or value.get("assessment_kind")
            != ("work-unit" if ordinal <= 3 else "remediation-confirmation")
            or not technical.get("authority")
        ):
            raise BundleError(
                "not-established",
                "Selected technical review must retain its actual operation, target and ordinal",
            )
        artifact(repository, technical.get("evidence"))
        completion = object_value(
            technical.get("completion"), "Selected technical review current completion"
        )
        if set(completion) != {
            "unmet",
            "unverified",
            "blocking",
            "local",
            "low",
        } or any(type(count) is not int or count != 0 for count in completion.values()):
            raise BundleError(
                "not-established",
                "Selected technical review has unresolved current obligations",
            )
        if technical["target"] != current["target"]:
            bridge = artifact(repository, technical.get("local_settlement"))
            if (
                bridge.get("before_target") != technical["target"]
                or bridge.get("after_target") != current["target"]
                or bridge.get("coverage_relationship")
                != "review-predates-local-correction"
                or bridge.get("source_review") != technical["evidence"]
                or bridge.get("source_verdict") != technical["original_verdict"]
                or bridge.get("all_blocking_obligations_local") is not True
                or bridge.get("completion") != completion
                or not bridge.get("permitted_delta")
            ):
                raise BundleError(
                    "not-established",
                    "Older technical review lacks an exact eligible current settlement bridge",
                )
            verification = artifact(repository, bridge.get("verification"))
            if (
                verification.get("before") != technical["target"]
                or verification.get("after") != current["target"]
                or verification.get("outcome") != "pass"
                or not verification.get("checks")
            ):
                raise BundleError(
                    "not-established",
                    "Technical settlement verification is stale, missing or negative",
                )
    if recovery is not None and recover()[1] != source_context:
        raise BundleError(
            "source-drift",
            "Approved original source context changed during commit consumption",
        )
    return {
        **(
            {"applied_source_context": copy.deepcopy(source_context)}
            if recovery is not None
            else {}
        ),
        "workflow_owner": "aquarium:epic-squad",
        "work": copy.deepcopy(assignment["work"]),
        "accepted_target": current["target"],
        "acceptance": copy.deepcopy(acceptance),
        "grant": copy.deepcopy(grant),
        "current_composition": current,
        "role_profiles": copy.deepcopy(
            assignment["target"]["squad"].get("profiles", {})
        ),
        "role_execution": copy.deepcopy(current["role_execution"]),
        "review_route": assignment["authority"]["review"]["route"],
        "assessment_ordinal": None
        if route == "not-required" or not review_due
        else value.get("assessment_ordinal"),
        "provider_operation": "not-required"
        if route == "not-required"
        else value.get("provider_operation")
        if review_due
        else "not-due",
        "assessment_kind": value.get("assessment_kind")
        if route != "not-required" and review_due
        else None,
        "review_boundary": copy.deepcopy(value.get("review_boundary")),
        "source_review": copy.deepcopy(source_review),
        "technical_review": copy.deepcopy(value.get("technical_review")),
        "effects": [],
        "next_owner": "Coordinator task-commit",
    }


def design_return(assignment, design, application):
    """Carry a bounded new-feature caller back to its original collaboration owner."""
    caller = object_value(design.get("caller"), "Design collaboration caller")
    if caller.get("workflow_owner") not in {
        "aquarium:epic-handler",
        "aquarium:epic-squad",
    }:
        raise BundleError(
            "incompatible", "Unknown collaboration owner in Design return"
        )
    work = assignment["work"]
    if any(
        caller.get(key) != work.get(key) for key in ("repository", "roadmap", "epic")
    ):
        raise BundleError(
            "incompatible",
            "Design return changed its original repository, roadmap or Epic",
        )
    if caller.get("mode") not in {"execute", "plan-only", "plan-handoff", "resume"}:
        raise BundleError("invalid-input", "Original collaboration mode is required")
    if not isinstance(caller.get("profiles", {}), dict):
        raise BundleError(
            "invalid-input",
            "Preserve supplied profile fields and omissions as an object",
        )
    if caller["workflow_owner"] == "aquarium:epic-squad":
        resolve_profiles(caller.get("profiles", {}))
    if application.get("status") != "verified-applied":
        state = "design-delivery-pending"
    elif type(design.get("commit_required")) is not bool:
        state = "delivery-input-commit-policy-required"
    elif design["commit_required"] and not design.get("delivery_commit"):
        state = "delivery-input-commit-required"
    else:
        state = "new-conversation-required"
    request = f"${caller['workflow_owner']} repository={caller['repository']} roadmap={caller['roadmap']} epic={caller['epic']} mode={caller['mode']}"
    if caller.get("profiles"):
        request += " profiles=" + json.dumps(
            caller["profiles"], ensure_ascii=False, sort_keys=True
        )
    return {
        "status": state,
        "caller": copy.deepcopy(caller),
        "profiles": copy.deepcopy(caller.get("profiles", {})),
        "delivery_commit": design.get("delivery_commit"),
        "request": request,
        "automatic_delivery": False,
        "delivery_input_commit_authority": "separate",
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify an ordinary Squad commit composition without native discovery or mutation."
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--handoff", required=True)
    args = parser.parse_args()
    try:
        value = json.loads(Path(args.handoff).read_text())
        result = commit_handoff(args.repository, value)
    except (
        BundleError,
        OSError,
        UnicodeError,
        ValueError,
        KeyError,
        TypeError,
    ) as error:
        print(
            json.dumps(
                {
                    "status": getattr(error, "code", "invalid-input"),
                    "message": str(error),
                }
            )
        )
        return 2
    print(json.dumps({"status": "verified", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
