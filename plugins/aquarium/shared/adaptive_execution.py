"""Map admitted native work to ordinary assignments without executing transitions."""

import copy
import importlib.util
import uuid
from pathlib import Path

import yaml
from adaptive_admission import resume_selected, selection_contract
from adaptive_bundles import BundleError, read_regular, sha256
from adaptive_definitions import (
    canonical_json,
    capability_signatures,
    native_key,
    parse_definition,
)

ACTIVATED = {
    "task-handler": {"task"},
    "epic-handler": {"goal", "validation"},
    "epic-validator": {"validation"},
    "new-feature": {"design"},
    "new-project": {"design"},
    "refactor": {"design"},
    "war-room": {"diagnosis"},
}
TASK_SKILLS = {
    "task-plan",
    "task-implement",
    "task-refine",
    "task-verify",
    "task-document",
    "task-review",
    "task-close",
}
# Exact reference leaf ownership, independent of mutable origin source files.
REFERENCE_OPERATION_PHASES = {
    "sha256:21646cf39875e15c523250a1b4952f8ddb51a3bef5ae4707c36b6498c2b1dbe6": [
        "task-review"
    ],
    "sha256:d43fd605b6f031c14ba26c43122aa1c96c05e03deec33f4746bcd342c8bfe9e3": [
        "task-plan"
    ],
    "sha256:652053b65846fea7e59961be6eefaee7f283edc98f83d7f26c66a62ad6b9dbb2": [
        "task-plan"
    ],
    "sha256:aa00c5804c7bea07b4f9d7fb9ebe03f438ea181334e2bc4e1b5f42519df4dc10": [
        "task-implement"
    ],
    "sha256:b2aaa79f9216a76ce57c9d4ecf37554a38aba0d3c756bd64ce56bb3bd5c2f0d7": [
        "task-refine"
    ],
    "sha256:1c801c722d3b2a553fc85f096e05f07c25b36a19a397fc07172c033b1ccc38d4": [
        "task-verify"
    ],
    "sha256:81e0975adc3169dfa5a6b600579be132136f482b964740e2f960db5280b237a3": [
        "task-document"
    ],
    "sha256:435045d71cd11c7f7f1143f5c5a3918864ebef810dcdac17b9000d2be9dbbb42": [
        "task-review"
    ],
}


def ordinary(assignment):
    path = (
        Path(__file__).resolve().parents[1]
        / "skills/goal-judge/scripts/ordinary_assignment.py"
    )
    spec = importlib.util.spec_from_file_location("adaptive_ordinary_assignment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.prepare(assignment)
    except module.AssignmentError as error:
        raise BundleError("invalid-input", str(error)) from error


def invocation_assignment(qualification):
    if not isinstance(qualification, dict) or not isinstance(
        qualification.get("assignment"), dict
    ):
        raise BundleError(
            "invalid-input", "Execution needs its ordinary invocation context"
        )
    assignment = ordinary(qualification["assignment"])
    if not isinstance(assignment["authority"].get("review"), dict):
        raise BundleError(
            "invalid-input", "Execution review authority must be an object"
        )
    return assignment


def phase_skills(document, binding, assignment, node):
    """Use approved work-specific phase ownership; keep original leaf contracts."""
    if binding["family"] not in {"task", "design", "diagnosis"}:
        return []
    from adaptive_design import LEAVES

    allowed = {"task": TASK_SKILLS, "design": LEAVES, "diagnosis": {"interview", "qa"}}[
        binding["family"]
    ]
    plan = assignment["target"]["procedure_plan"]
    configured = plan.get("phase_skills", {})
    if not isinstance(configured, dict):
        raise BundleError(
            "invalid-input", "phase_skills must map placements to due skills"
        )
    if any(key not in binding["nodes"] for key in configured):
        raise BundleError("incompatible", "A phase owner refers to an absent placement")
    for skills in configured.values():
        if not isinstance(skills, list) or any(
            not isinstance(skill, str) or skill not in allowed for skill in skills
        ):
            raise BundleError(
                "invalid-input", "Phase owners must name supported family leaf skills"
            )
    if node in configured:
        return configured[node]
    if binding["family"] == "diagnosis":
        return (
            ["qa"]
            if diagnosis_phase(document, binding, assignment, node) == "quality"
            else []
        )
    if binding["family"] == "design":
        phase = design_phase(document, binding, assignment, node)
        return {"discovery": ["interview"], "quality": ["qa"]}.get(phase, [])
    definition = next(
        row["use"] for row in document["graph"]["nodes"] if row["id"] == node
    )
    body = document["node_definitions"][definition]
    exact = REFERENCE_OPERATION_PHASES.get(sha256(canonical_json(body)))
    if exact is not None:
        return exact
    candidate = binding.get("semantic_contracts", {}).get(
        sha256(canonical_json(body)), {}
    )
    original = candidate.get("derivation", {}).get("definition")
    return REFERENCE_OPERATION_PHASES.get(sha256(canonical_json(original)), [])


def design_phase(document, binding, assignment, node):
    from adaptive_design import OPERATIONS

    configured = assignment["target"]["procedure_plan"].get("design_phases", {})
    if not isinstance(configured, dict) or any(
        key not in binding["nodes"]
        or not isinstance(value, str)
        or value
        not in {"context", "discovery", "draft", "challenge", "quality", "application"}
        for key, value in configured.items()
    ):
        raise BundleError(
            "invalid-input",
            "Design phases must map actual placements to supported work",
        )
    signatures = capability_signatures()
    signatures.update(binding.get("capability_definitions", {}))
    if any(
        signatures.get(cap["signature"], {}).get("guarantee") == "application-approval"
        for cap in binding["nodes"][node]["capabilities"]
    ):
        if node in configured and configured[node] != "application":
            raise BundleError(
                "incompatible",
                "A mapped application cannot be relabeled as another phase",
            )
        return "application"
    if node in configured:
        return configured[node]
    placement = next(row for row in document["graph"]["nodes"] if row["id"] == node)
    body = document["node_definitions"][placement["use"]]
    digest = sha256(canonical_json(body))
    if digest in OPERATIONS:
        return OPERATIONS[digest]
    contract = binding.get("semantic_contracts", {}).get(digest, {})
    original = contract.get("derivation", {}).get("definition")
    return OPERATIONS.get(sha256(canonical_json(original)))


def diagnosis_phase(document, binding, assignment, node):
    from adaptive_diagnosis import OPERATIONS, PHASES

    configured = assignment["target"]["procedure_plan"].get("diagnosis_phases", {})
    if not isinstance(configured, dict) or any(
        key not in binding["nodes"] or not isinstance(value, str) or value not in PHASES
        for key, value in configured.items()
    ):
        raise BundleError(
            "invalid-input",
            "Diagnosis phases must map actual placements to supported work",
        )
    signatures = capability_signatures()
    signatures.update(binding.get("capability_definitions", {}))
    if any(
        signatures.get(cap["signature"], {}).get("guarantee") == "application-approval"
        for cap in binding["nodes"][node]["capabilities"]
    ):
        if node in configured and configured[node] != "documentation":
            raise BundleError(
                "incompatible", "Documentation approval cannot be relabeled"
            )
        return "documentation"
    if node in configured:
        return configured[node]
    placement = next(row for row in document["graph"]["nodes"] if row["id"] == node)
    body = document["node_definitions"][placement["use"]]
    digest = sha256(canonical_json(body))
    if digest in OPERATIONS:
        return OPERATIONS[digest]
    original = (
        binding.get("semantic_contracts", {})
        .get(digest, {})
        .get("derivation", {})
        .get("definition")
    )
    return OPERATIONS.get(sha256(canonical_json(original)))


def validate_phase_mappings(document, binding, assignment):
    """Check every configured placement before admission, including future work."""
    family = binding["family"]
    if family not in {"task", "design", "diagnosis"}:
        return
    checks = [("phase_skills", phase_skills)]
    if family == "design":
        checks.append(("design_phases", design_phase))
    elif family == "diagnosis":
        checks.append(("diagnosis_phases", diagnosis_phase))
    plan = assignment["target"]["procedure_plan"]
    for field, check in checks:
        configured = plan.get(field, {})
        if not isinstance(configured, dict):
            check(document, binding, assignment, None)
        for node in configured:
            check(document, binding, assignment, node)


def execution_context(
    repository,
    *,
    roots,
    entrypoint,
    qualification,
    client,
    session=None,
    bootstrap=None,
    route=None,
    opt_out=False,
):
    """Resolve before begin/work and expose exact current native ownership/evidence."""
    from adaptive_entrypoint import EntryPointError, branch

    try:
        skipped = branch(repository, entrypoint, opt_out=opt_out)
    except EntryPointError as error:
        raise BundleError(error.code, str(error)) from error
    if skipped is not None:
        return skipped
    if entrypoint not in ACTIVATED:
        raise BundleError(
            "not-established",
            "This family has no activated mapped consumer",
        )
    repository = Path(repository).expanduser().resolve()
    assignment = invocation_assignment(qualification)
    review = assignment["authority"]["review"]
    approved_route = review.get("route")
    routes = {"herdr", "mulgae", "subagent-review", "waived"}
    if entrypoint in {"new-feature", "new-project", "refactor", "war-room"}:
        routes.add("not-applicable")
    if approved_route not in routes or (route is not None and route != approved_route):
        raise BundleError(
            "route-unavailable",
            "Current selected review route differs from approved adaptive execution",
        )
    observation = client.health()
    if observation is None:
        raise BundleError(
            "missing-session",
            "Admission and retained source are required before starting",
        )
    status = observation["status"]
    if session is not None and status["session"]["id"] != session:
        raise BundleError(
            "session-conflict",
            "Observed session differs from the requested continuation",
        )
    recovery = qualification.get("finalization_recovery")
    continuation = qualification.get("applied_source_recovery")
    if recovery is not None and continuation is not None:
        raise BundleError(
            "invalid-input",
            "Choose applied continuation or settled finalization recovery",
        )
    source_reader = None
    source_context = None
    if continuation is not None:
        from adaptive_finalization import approved_sources, finalization_observation

        recovery_observation = finalization_observation(client, observation)
        source_reader, source_context = approved_sources(
            repository,
            assignment,
            continuation,
            recovery_observation,
            continuation=True,
        )
    if recovery is not None:
        from adaptive_finalization import finalization_observation, finalization_sources

        recovery_observation = finalization_observation(client, observation)
        source_reader, affected_assessment = finalization_sources(
            repository, assignment, recovery, recovery_observation
        )
    resolved = resume_selected(
        repository,
        roots,
        status["procedure"],
        client=client,
        bootstrap=bootstrap,
        qualification=qualification,
        source_reader=source_reader,
    )
    binding = resolved["binding"]
    if (
        binding["family"] not in ACTIVATED[entrypoint]
        or entrypoint not in binding["entrypoints"]
    ):
        raise BundleError(
            "incompatible", "Admitted family does not belong to this entrypoint"
        )
    plan = assignment["target"]["procedure_plan"]
    if plan["family"] != binding["family"] or plan["entrypoint"] != entrypoint:
        raise BundleError(
            "incompatible",
            "Current invocation differs from the admitted family context",
        )
    if native_key(binding) != tuple(
        status["procedure"][key] for key in ("id", "version", "digest")
    ):
        raise BundleError("corrupt", "Native readback differs from retained definition")
    document = yaml.safe_load(resolved["source"])
    selection_contract(
        resolved["source"],
        binding,
        entrypoint,
        approved_route,
        qualification,
        document=document,
    )
    result = {
        "status": "resolved",
        "bundle_id": resolved["bundle_id"],
        "source_path": str(Path(resolved["path"]) / "procedure.yaml"),
        "binding_path": str(Path(resolved["path"]) / "binding.json"),
        "procedure": copy.deepcopy(status),
        "work": assignment["work"],
        "authority": assignment["authority"],
        "qualification": resolved["qualification"],
        "mutation_templates": observation.get("mutation_templates", []),
        "guidance": observation.get("guidance"),
        "active_items": observation.get("active_items", []),
        "pending_operations": copy.deepcopy(
            qualification.get("pending_operations", [])
        ),
        "dispatch": None,
        "phase_skills": [],
        "next_owner": "Primary",
        "limits": [
            "Caller verifies actual work identity, pending effects and current authority before acting.",
            "Native declarations and records do not establish independent execution or actual approval.",
        ],
    }

    def checked(value):
        if continuation is not None:
            current = finalization_observation(client, observation)
            _, current_sources = approved_sources(
                repository, assignment, continuation, current, continuation=True
            )
            if current_sources != source_context:
                raise BundleError(
                    "source-drift",
                    "Approved source context changed during continuation",
                )
            if (
                read_regular(repository, Path(resolved["path"]) / "procedure.yaml")
                != resolved["source"]
                or parse_definition(
                    read_regular(repository, Path(resolved["path"]) / "binding.json")
                )
                != binding
            ):
                raise BundleError(
                    "source-drift", "Admitted definition changed during continuation"
                )
        return value

    if source_context is not None:
        result["applied_sources"] = copy.deepcopy(source_context)
    if recovery is not None:
        from adaptive_finalization import selected_assessment

        recovery_observation = finalization_observation(client, observation)
        _, affected_assessment = finalization_sources(
            repository, assignment, recovery, recovery_observation
        )
        selected_assessment(binding, recovery, affected_assessment)
        result["status"] = "finalization-resolved"
        result["next_owner"] = "Primary finalization/disposition"
        result["limits"].append(
            "Approved source retirement recovery permits no product dispatch and establishes no achievement."
        )
        return result
    lifecycle = status["session"]["lifecycle"]
    if lifecycle == "prepared":
        result["status"] = "prepared-resolved"
        return checked(result)
    if lifecycle in {"completed", "cancelled"}:
        result["status"] = "terminal-resolved"
        result["next_owner"] = (
            "Primary finalization/disposition or approved normal successor"
        )
        return checked(result)
    guidance = observation.get("guidance")
    if not isinstance(guidance, dict) or not isinstance(guidance.get("node"), dict):
        raise BundleError(
            "unsupported-runtime", "Running observation lacks current placement"
        )
    node = guidance["node"].get("graph_node_id")
    if not isinstance(node, str):
        raise BundleError(
            "unsupported-runtime", "Current native placement lacks its typed identity"
        )
    if node not in binding["nodes"]:
        raise BundleError(
            "missing-topology",
            "Current native placement has no admitted binding; preserve session",
        )
    placement = next(row for row in document["graph"]["nodes"] if row["id"] == node)
    declaration = binding["nodes"][node]
    result.update(
        node=node,
        role=declaration["role"],
        capabilities=declaration["capabilities"],
        selected_evidence=placement.get("evidence_from", []),
        phase_skills=phase_skills(document, binding, assignment, node),
    )
    if binding["family"] == "design":
        from adaptive_design import context as design_context

        result["design"] = design_context(
            repository, assignment, design_phase(document, binding, assignment, node)
        )
        application = result["design"].get("application", {})
        if application.get("status") in {"approval-required", "reapproval-required"}:
            result["status"] = application["status"]
            return checked(result)
    if binding["family"] == "diagnosis":
        from adaptive_diagnosis import context as diagnosis_context

        result["diagnosis"] = diagnosis_context(
            repository, assignment, diagnosis_phase(document, binding, assignment, node)
        )
        application = result["diagnosis"].get("application", {})
        if application.get("status") in {"approval-required", "reapproval-required"}:
            result["status"] = application["status"]
            return checked(result)
    handoff = handoff_context(
        repository,
        document,
        binding,
        assignment,
        observation,
        client,
        structural=resolved["qualification"].get("structural"),
    )
    result["handoff"] = handoff
    if handoff and handoff["status"] in {"attachment-required", "stop-before-work"}:
        result["status"] = handoff["status"]
        return checked(result)
    if declaration["role"] == "orchestrator" or declaration["kind"] == "decision":
        result["status"] = "primary-owned"
        return checked(result)
    dispatched = copy.deepcopy(assignment)
    dispatched.update(
        role=declaration["role"],
        procedure={
            "native": copy.deepcopy(status),
            "binding": binding["procedure"],
            "bundle_id": resolved["bundle_id"],
            "node": node,
            "selected_evidence": placement.get("evidence_from", []),
            "capabilities": declaration["capabilities"],
            "phase_skills": result["phase_skills"],
        },
        native={
            "harness": assignment["native"].get("harness", "unknown"),
            "public_handle": "unknown",
            "status": "not-dispatched",
        },
    )
    definition = document["node_definitions"][placement["use"]]
    dispatched["target"]["active_operation"] = definition
    if source_context is not None:
        dispatched["target"]["applied_source_context"] = copy.deepcopy(source_context)
        dispatched["instructions"] += (
            "\nRead the original pinned requirement bytes through target.applied_source_context capture/Git references. The approved current images are deliverables; preserve every original criterion and all due checks."
        )
    dispatched["checkpoint"] = node
    dispatched["instructions"] += (
        "\nRead the complete selected native evidence and original sources. Follow this exact active operation and load each named installed leaf skill completely. Return actual evidence; do not advance Podway or grant approval."
    )
    if binding["family"] == "design":
        dispatched["target"]["design_context"] = copy.deepcopy(result["design"])
        dispatched["authority"]["excluded"] += [
            "Product implementation",
            "Ouroboros auto/run/ralph/evolve",
            "Unapproved document application",
            "Unapproved clipboard replacement",
        ]
        if result["design"].get("application", {}).get("status") == "verified-applied":
            dispatched["authority"]["effects"] = []
            dispatched["authority"]["excluded"].append("Document application")
            dispatched["instructions"] += (
                "\nVerify the already applied approved bytes and available original checks only. Do not apply documents again."
            )
    if binding["family"] == "diagnosis":
        dispatched["target"]["diagnosis_context"] = copy.deepcopy(result["diagnosis"])
        dispatched["authority"]["excluded"] += [
            "Product repair or implementation",
            "Production or shared-service mutation",
            "Ouroboros auto/run/ralph/evolve",
            "Unapproved diagnostic document application",
            "Publication",
        ]
        if (
            result["diagnosis"].get("application", {}).get("status")
            == "verified-applied"
        ):
            dispatched["authority"]["effects"] = []
            dispatched["authority"]["excluded"].append("Document application")
    if declaration["role"] == "judge":
        dispatched["authority"]["effects"] = []
        dispatched["authority"]["allowed"] = [
            "Independent report-only assessment of the assigned due checkpoint"
        ]
        dispatched["authority"]["excluded"] = [
            *dispatched["authority"]["excluded"],
            "Product mutation",
            "Check execution",
            "Native progression",
            "Acceptance",
            "Commit",
            "Nested dispatch",
        ]
    result.update(
        status="dispatch-ready",
        dispatch=ordinary(dispatched),
        next_owner=declaration["role"],
    )
    return checked(result)


def handoff_context(
    repository, document, binding, assignment, observation, client, *, structural=None
):
    """Verify the approved mapped handoff before its first actual work boundary."""
    plan = assignment["target"]["procedure_plan"]
    mapping = plan.get("plan_handoff")
    runtime = assignment["target"].get("plan_handoff_runtime")
    if mapping is None and runtime is None:
        return None
    if not isinstance(mapping, dict) or not isinstance(runtime, dict):
        raise BundleError(
            "not-established",
            "Restore exact approved handoff mapping and session-bound plan context",
        )
    endpoint = mapping.get("attachment")
    boundaries = mapping.get("first_work")
    if (
        not isinstance(endpoint, dict)
        or not isinstance(endpoint.get("node"), str)
        or not isinstance(endpoint.get("item"), str)
        or not isinstance(boundaries, list)
        or not boundaries
        or any(not isinstance(node, str) for node in boundaries)
    ):
        raise BundleError(
            "invalid-input",
            "Handoff needs an attachment endpoint and actual first-work placements",
        )
    placements = {row["id"]: row for row in document["graph"]["nodes"]}
    if endpoint.get("node") not in placements or any(
        node not in placements for node in boundaries
    ):
        raise BundleError(
            "incompatible", "Handoff endpoint or actual work boundary is absent"
        )
    definition = document["node_definitions"][placements[endpoint["node"]]["use"]]
    item = next(
        (
            item
            for item in definition.get("items", [])
            if item["id"] == endpoint.get("item")
        ),
        None,
    )
    if (
        item is None
        or item["type"] != "artifact"
        or "text/markdown" not in item.get("allowed_media_types", [])
    ):
        raise BundleError(
            "incompatible", "Mapped plan attachment must admit Markdown artifacts"
        )
    from adaptive_qualification import qualify

    context = {
        **assignment["target"].get("qualification_context", {}),
        "review": assignment["authority"]["review"],
    }
    proof = (
        structural
        if structural is not None and "execution" in structural
        else qualify(document, binding, context=context, execution_info=True)
    )
    if proof["status"] != "compatible":
        raise BundleError(
            proof["status"], "Exact handoff work frontier is not established", proof
        )
    frontier = proof["execution"]
    if frontier["unknown_before_work"]:
        raise BundleError(
            "not-established",
            "An effect before the handoff boundary is unproved",
            frontier,
        )
    if set(boundaries) != set(frontier["first_work"]):
        raise BundleError(
            "incompatible",
            "Mapped handoff must stop at every actual feasible first-work placement",
            frontier,
        )

    initial = runtime.get("initial_session_id")
    try:
        if str(uuid.UUID(initial)) != initial:
            raise ValueError
    except (ValueError, AttributeError, TypeError) as error:
        raise BundleError(
            "invalid-input", "Handoff initial session must be its native UUID"
        ) from error
    if runtime.get("mode") not in {"plan-handoff", "resume"}:
        raise BundleError("invalid-input", "Handoff mode must be explicit")
    node = observation["guidance"]["node"]["graph_node_id"]
    result = {"attachment": endpoint, "first_work": boundaries, "verified": False}
    if node == endpoint["node"]:
        values = [
            row.get("value")
            for row in observation["active_items"]
            if row["item_id"] == endpoint["item"]
        ]
        if not values or values[0] is None:
            return {**result, "status": "attachment-required"}
        artifact = values[0]
        attempt = observation["status"]["current"]["attempt"]
        reference = {
            "session_id": observation["status"]["session"]["id"],
            "node": node,
            "attempt_id": attempt["attempt_id"],
            "attempt_number": attempt["attempt_number"],
        }
    elif node in boundaries and any(
        selected.get("node") == endpoint["node"]
        and ("items" not in selected or endpoint["item"] in selected["items"])
        for selected in placements[node].get("evidence_from", [])
    ):
        rows = {
            (
                row.get("source_attempt_id"),
                row.get("source_attempt_number"),
                item.get("value_digest"),
            ): (row, item)
            for row in observation["guidance"].get("readback", [])
            if row.get("source_graph_node_id") == endpoint["node"]
            and row.get("state") == "resolved"
            for item in row.get("items", [])
            if item.get("item_id") == endpoint["item"]
        }
        if len(rows) != 1:
            raise BundleError(
                "missing-topology",
                "Work boundary lacks one current mapped approved plan reference; preserve session",
            )
        selected, metadata = next(iter(rows.values()))
        if not isinstance(metadata.get("value_digest"), str):
            raise BundleError(
                "unsupported-runtime",
                "Selected plan reference lacks its native value identity",
            )
        reference = {
            "session_id": observation["status"]["session"]["id"],
            "node": endpoint["node"],
            "attempt_id": selected["source_attempt_id"],
            "attempt_number": selected["source_attempt_number"],
        }
        status = observation["status"]
        page = client.read(
            [
                "evidence",
                "read",
                "--source",
                endpoint["node"],
                "--item",
                endpoint["item"],
                "--if-workspace-uuid",
                next(
                    template["preconditions"]["workspace_uuid"]
                    for template in observation["mutation_templates"]
                    if "workspace_uuid" in template.get("preconditions", {})
                ),
                "--if-session-id",
                status["session"]["id"],
            ],
            "evidence.read",
            {"podway.evidence-read-result/v1"},
        )
        if (
            page.get("truncated") is not False
            or page.get("next_page_token") is not None
            or page.get("value_digest") != metadata["value_digest"]
        ):
            raise BundleError(
                "not-established",
                "Exact complete current handoff metadata is unavailable",
            )
        artifact = page["page"]["data"]
    elif node in boundaries or (
        node in frontier["after_first_work"]
        and binding["nodes"][node]["role"] in {"worker", "judge"}
    ):
        if runtime["mode"] == "plan-handoff" and node not in boundaries:
            raise BundleError(
                "not-established",
                "The requested no-work handoff boundary has already been passed; preserve session",
            )
        artifact = runtime.get("artifact")
        reference = runtime.get("artifact_reference")
        if not isinstance(artifact, dict) or not isinstance(reference, dict):
            raise BundleError(
                "not-established",
                "Restore the actual previously verified plan metadata from the ordinary checkpoint before work",
            )
    else:
        return {**result, "status": "before-boundary"}
    status = observation["status"]
    counters = [
        row
        for row in status.get("counters", [])
        if row.get("graph_node_id") == endpoint["node"]
    ]
    if (
        reference.get("session_id") != status["session"]["id"]
        or reference.get("node") != endpoint["node"]
        or not isinstance(reference.get("attempt_id"), str)
        or type(reference.get("attempt_number")) is not int
        or len(counters) != 1
        or counters[0].get("attempt_count") != reference["attempt_number"]
    ):
        raise BundleError(
            "not-established",
            "Native rework or session state invalidated the retained plan attachment; restore its actual current reference",
        )
    path = Path(".podway/runtime/handoffs") / initial / "plan.md"
    raw = read_regular(repository, path)
    expected = {
        "location": str(path),
        "location_type": "path",
        "media_type": "text/markdown",
        "sha256_digest": sha256(raw),
        "size_bytes": len(raw),
    }
    if len(raw) > 65536 or artifact != expected:
        raise BundleError(
            "source-drift",
            "Recorded approved plan does not match its exact session-bound bytes",
        )
    return {
        **result,
        "status": "stop-before-work"
        if node in boundaries and runtime["mode"] == "plan-handoff"
        else "verified",
        "verified": True,
        "artifact": artifact,
        "artifact_reference": reference,
    }
