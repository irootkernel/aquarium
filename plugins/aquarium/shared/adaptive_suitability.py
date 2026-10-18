"""Exact pre-start Judge targets and bootstrap import using ordinary v2 evidence."""

import copy
import json
from pathlib import Path

import yaml
from adaptive_admission import known_source, qualify_known, selection_contract
from adaptive_bundles import (
    BundleError,
    contained,
    publish_bundle,
    read_regular,
    roots_for,
    sha256,
)
from adaptive_definitions import (
    canonical_json,
    capability_signatures,
    definition_id,
    native_key,
    parse_definition,
)
from adaptive_preparation import fit, object_value, requirements, source_authority
from adaptive_qualification import guarantee_minima, qualify

BOOTSTRAP_SIGNATURE = "aquarium.shared.suitability-bootstrap/v1"
BOOTSTRAP_OPERATION = "aquarium-adaptive-suitability-applicability"
BOOTSTRAP_MEANING = (
    "For a new or changed definition verify the actual independent pre-start ordinary Judge assessment covers the exact candidate bundle, native tuple, source bytes and complete current original requirement and approved plan basis, with passing due phase criteria. "
    "For adequate unchanged established reuse verify the exact retained qualified definition and its actual prior independent evidence plus current original-source fit; record established-reuse timing and preserve normal first-due checkpoints, without presenting prior evidence as a current assessment. "
    "Material in-session definition or plan changes require affected reassessment. Recording authenticates no agent or authority."
)

BOOTSTRAP_DIGEST = sha256(BOOTSTRAP_MEANING.encode())


def add_bootstrap(document, mapping):
    """Add recording and applicability before work, without embedding invocation values."""
    document, mapping = copy.deepcopy(document), copy.deepcopy(mapping)
    names = {node["id"] for node in document["graph"]["nodes"]} | set(
        document["node_definitions"]
    )
    record, decision = "suitability-bootstrap", "suitability-applicability"
    if names.intersection({record, decision}):
        raise BundleError("incompatible", "Bootstrap placement identity collides")
    fields = {
        "suitability-assessment": {
            "type": "artifact",
            "required": True,
            "allowed_media_types": ["application/json"],
        },
        "suitability-target": {
            "type": "text",
            "required": True,
            "min_length": 1,
            "max_length": 8000,
            "multiline": True,
        },
        "suitability-timing": {
            "type": "choice",
            "required": True,
            "choices": ["pre-start", "established-reuse", "not-established"],
        },
        "suitability-verdict": {
            "type": "choice",
            "required": True,
            "choices": ["pass", "rework", "evidence-needed"],
        },
        "suitability-unmet": {"type": "integer", "required": True, "minimum": 0},
        "suitability-unverified": {"type": "integer", "required": True, "minimum": 0},
        "suitability-current": {
            "type": "check_result",
            "required": True,
            "help": BOOTSTRAP_MEANING,
            "operation_id": BOOTSTRAP_OPERATION,
            "operation_digest": BOOTSTRAP_DIGEST,
            "accepted_outcomes": ["pass", "fail", "inconclusive"],
        },
    }
    document["node_definitions"][record] = {
        "type": "action",
        "title": "Record definition suitability or established reuse",
        "intent": "Retain actual definition evidence and current applicability before original work.",
        "items": [
            {"id": name, "prompt": name.replace("-", " "), **spec}
            for name, spec in fields.items()
        ],
    }
    guards = [
        {
            "evidence": {"node": record, "item": field},
            **({"field": "outcome"} if field == "suitability-current" else {}),
            "equals": value,
        }
        for field, value in [
            ("suitability-verdict", "pass"),
            ("suitability-unmet", 0),
            ("suitability-unverified", 0),
            ("suitability-current", "pass"),
        ]
    ]
    document["node_definitions"][decision] = {
        "type": "decision",
        "title": "Check current suitability applicability",
        "objective": "Check exact definition evidence and current applicability",
        "prompt": "Does actual suitability or established-reuse evidence cover this exact definition and current work?",
        "reason": {
            "required": True,
            "prompt": "Cite actual definition evidence, current target and applicability gaps.",
        },
        "options": [
            {
                "id": "current",
                "label": "Current pass",
                "criteria": "All due suitability facts pass.",
                "guards": guards,
            },
            {
                "id": "reassess",
                "label": "Reassess",
                "criteria": "The target or basis is stale, incomplete or negative.",
            },
        ],
    }
    entry = document["graph"]["entry"]
    document["graph"]["entry"] = record
    document["graph"]["nodes"][0:0] = [
        {"id": record, "use": record, "next": decision},
        {
            "id": decision,
            "use": decision,
            "evidence_from": [
                {"node": record, "required": True, "items": list(fields)}
            ],
            "routes": {
                "current": {"to": entry, "effect": "advance"},
                "reassess": {"to": record, "effect": "rework"},
            },
        },
    ]
    mapping["nodes"][record] = {
        "kind": "action",
        "role": "orchestrator",
        "effects": [],
        "capabilities": [{"signature": BOOTSTRAP_SIGNATURE, "fields": {}}],
    }
    mapping["nodes"][decision] = {
        "kind": "decision",
        "role": "orchestrator",
        "effects": [],
        "capabilities": [],
    }
    return document, mapping


def current_basis(repository, assignment, *, in_session=False, source_reader=None):
    """Original sources and current ordinary plan remain the requirements authority."""
    if source_reader is not None and not in_session:
        raise BundleError("invalid-input", "Source recovery is in-session only")
    criteria = requirements(
        repository,
        assignment,
        verify_sources=not in_session,
        source_reader=source_reader,
    )
    if in_session:
        approved = assignment["target"]["prepared_definition"]["coverage_plan"][
            "criteria"
        ]
        if criteria != approved:
            raise BundleError(
                "reassessment-required",
                "Current extracted original requirements differ from the approved basis",
            )
    if not in_session:
        prepared = assignment["target"]["prepared_definition"]
        if (
            source_authority(repository, assignment)
            != prepared["coverage_plan"]["source_authority"]
        ):
            raise BundleError(
                "reassessment-required",
                "Managed source authority changed after preparation",
            )
    plan = assignment["target"]["procedure_plan"]
    qualification = object_value(
        assignment["target"].get("qualification_context", {}), "qualification_context"
    )
    review = object_value(assignment["authority"].get("review", {}), "authority.review")
    live = {
        "consumed",
        "remaining",
        "assessment_ordinal",
        "review_ordinal",
        "pending_operation",
        "session",
        "native",
        "consumed_review_authority",
        "remaining_review_authority",
        "last_operation",
    }
    static_authority = {
        key: copy.deepcopy(assignment["authority"][key])
        for key in ("allowed", "excluded", "effects")
        if key in assignment["authority"]
    }
    static_authority["review"] = {
        key: copy.deepcopy(value) for key, value in review.items() if key not in live
    }
    return {
        "work": copy.deepcopy(assignment["work"]),
        "criteria": criteria,
        "success_criteria": copy.deepcopy(assignment["success_criteria"]),
        "plan": copy.deepcopy(plan),
        "authority": static_authority,
        "base": copy.deepcopy(assignment["target"].get("base")),
        "qualification_context": {
            key: copy.deepcopy(value)
            for key, value in qualification.items()
            if key
            in {
                "operation_contracts",
                "signatures",
                "goal_kind",
                "workflow_owner",
                "due_capabilities",
                "required_endpoints",
                "criterion_capacity",
                "review_required",
                "expected_outcome",
            }
        },
    }


def suitability_target(binding, basis, *, combined_task_plan=False, coverage_plan=None):
    return {
        "candidate": {
            "bundle_id": definition_id(binding),
            "procedure": copy.deepcopy(binding["procedure"]),
        },
        "basis": basis,
        "coverage_plan": copy.deepcopy(coverage_plan),
        "timing": "pre-start",
        "scopes": [
            "procedure-suitability",
            *(["task-plan"] if combined_task_plan else []),
        ],
    }


def judge_assignment(assignment, target, assessment_requirements=None):
    result = copy.deepcopy(assignment)
    result.update(
        role="judge",
        purpose="Assess exact Procedure suitability before native start",
        checkpoint="pre-start-procedure-suitability",
        instructions="Report only. Reconcile complete original sources and compound criteria with the exact candidate and selected reviews/effects. Assess the execution definition, not future product completion. Preserve independent role and authority. Return aquarium.judge-assessment/v2 with this exact target; unknown evidence cannot pass. If a new discriminator or planning-output semantic contract needs establishment, include applicability.operation_contracts keyed by its exact operation-definition digest, with the exact retained contract and readable supporting evidence. This is part of the same due assessment, never proof that an agent executed.",
        deliverables=["Exact current independent suitability assessment"],
    )
    result["target"]["preparation_native_context"] = copy.deepcopy(result["native"])
    result["native"] = {
        "harness": result["native"].get("harness", "unknown"),
        "assigned_agent": "unknown",
        "lifecycle": "not-dispatched",
    }
    result["target"]["procedure_suitability"] = target
    result["target"]["assessment_requirements"] = copy.deepcopy(
        assessment_requirements or {}
    )
    result["authority"]["allowed"] = [
        "Read approved original sources and exact execution-definition bytes",
        "Return independent report-only suitability assessment",
    ]
    result["authority"]["excluded"] = list(
        dict.fromkeys(
            result["authority"].get("excluded", [])
            + ["Mutation", "Native start or advance", "Authority changes"]
        )
    )
    # Keep available pre-session context truthful; do not invent a future node,
    # attempt, actor identity or successful execution.
    result["evidence"] = list(result.get("evidence", [])) + [copy.deepcopy(target)]
    return result


def assess_current(report, target):
    if (
        not isinstance(report, dict)
        or report.get("schema") != "aquarium.judge-assessment/v2"
    ):
        raise BundleError(
            "not-established",
            "Actual ordinary independent Judge assessment is required",
        )
    report_target = object_value(report.get("target"), "Judge target")
    if report_target.get("procedure_suitability") != target:
        raise BundleError(
            "reassessment-required", "Suitability target or original basis changed"
        )
    phase_pass = report.get("checkpoint_result") == "pass"
    if report.get("checkpoint_result") not in (None, "pass") or (
        not phase_pass and report.get("verdict") != "pass"
    ):
        raise BundleError(
            "not-established", "Due suitability checkpoint has not passed"
        )
    gaps = report.get("gaps")
    if not isinstance(gaps, list):
        raise BundleError("invalid-input", "Ordinary Judge gaps must be a list")
    if any(
        isinstance(gap, dict) and gap.get("scope") in target["scopes"] for gap in gaps
    ):
        raise BundleError("not-established", "Due suitability gaps remain")
    # Ordinary applicability may be prose or structured evidence. Exact target
    # equality and current source reconciliation establish its mechanical basis;
    # no private report dialect or completed product is required at this phase.
    applicability = report.get("applicability")
    if not isinstance(applicability, (dict, str, list)) or not applicability:
        raise BundleError(
            "not-established", "Current assessment applicability is unestablished"
        )
    if isinstance(applicability, dict) and applicability.get("status", "pass") not in (
        "pass",
        "current",
        "applicable",
    ):
        raise BundleError(
            "not-established", "Assessment explicitly lacks current applicability"
        )
    rows = report.get("criteria")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise BundleError(
            "invalid-input", "Judge criteria must be ordinary criterion rows"
        )

    def indexed(values):
        result = {}
        for row in values:
            identifier = row.get("id", row.get("criterion"))
            if not isinstance(identifier, str) or identifier in result:
                raise BundleError(
                    "invalid-input", "Criterion identities must be unambiguous"
                )
            if "state" in row and "status" in row and row["state"] != row["status"]:
                raise BundleError(
                    "invalid-input", "Criterion state renderings contradict"
                )
            result[identifier] = row
        return result

    def established(row, *, global_row=True):
        if not row:
            return False
        evidence = isinstance(row.get("evidence"), (str, list, dict)) and bool(
            row["evidence"]
        )
        state = row.get("state", row.get("status"))
        if state == "met":
            return evidence
        if state == "not-applicable":
            return (
                evidence
                and isinstance(row.get("reason"), str)
                and bool(row["reason"].strip())
            )
        # A nonfinal scoped pass preserves truthful global future gaps. The
        # Judge's phase result covers definition/plan fit, not product delivery.
        return (
            global_row
            and phase_pass
            and state in ("unmet", "unverified")
            and bool(evidence or row.get("reason") or row.get("gap"))
        )

    by_id = indexed(rows)
    if "checkpoint_criteria" in report:
        checkpoint_rows = report["checkpoint_criteria"]
        if not isinstance(checkpoint_rows, list) or any(
            not isinstance(row, dict) for row in checkpoint_rows
        ):
            raise BundleError(
                "invalid-input", "Scoped checkpoint criteria must be ordinary rows"
            )
        for row in indexed(checkpoint_rows).values():
            if not established(row, global_row=False):
                raise BundleError(
                    "not-established", "A due checkpoint criterion lacks passage"
                )
    for identifier, criterion in target["basis"]["criteria"].items():
        row = by_id.get(identifier)
        if not established(row):
            raise BundleError(
                "not-established",
                "An original suitability criterion lacks current evidence",
                {"criterion": identifier},
            )
        parts = row.get("parts", [])
        if not isinstance(parts, list) or any(
            not isinstance(part, dict) for part in parts
        ):
            raise BundleError("invalid-input", "Compound Judge criteria must be rows")
        supplied = indexed(parts)
        for part in criterion["parts"]:
            actual = supplied.get(part["id"])
            if (
                actual is None
                and len(criterion["parts"]) == 1
                and part["id"] == "whole"
            ):
                actual = row
            if not established(actual):
                raise BundleError(
                    "not-established",
                    "A compound suitability obligation lacks evidence",
                    {"criterion": identifier, "part": part["id"]},
                )
    return report


def bootstrap_import(document, binding, target, report):
    assess_current(report, target)
    records = []
    for node, declaration in binding["nodes"].items():
        for cap in declaration["capabilities"]:
            if cap["signature"] == BOOTSTRAP_SIGNATURE:
                records.append((node, cap["fields"]))
    if len(records) != 1 or records[0][0] != document["graph"]["entry"]:
        raise BundleError(
            "not-established",
            "New definition lacks its initial suitability recording capability",
        )
    node, aliases = records[0]
    values = {
        "suitability-target": json.dumps(
            {
                "bundle_id": target["candidate"]["bundle_id"],
                "target_sha256": sha256(canonical_json(target)),
            },
            sort_keys=True,
        ),
        "suitability-timing": "pre-start",
        "suitability-verdict": "pass",
        "suitability-unmet": 0,
        "suitability-unverified": 0,
        "suitability-current": {
            "outcome": "pass",
            "operation_id": BOOTSTRAP_OPERATION,
            "operation_digest": BOOTSTRAP_DIGEST,
        },
    }
    return {
        "node": node,
        "artifact_evidence": {
            aliases.get("suitability-assessment", "suitability-assessment"): report
        },
        "native_attachment": "Use the actual ordinary delivery or its authorized projection through native item.attach; this output asserts no ArtifactValue or location.",
        "items": {aliases.get(key, key): value for key, value in values.items()},
        "limits": "Actual ordinary report import only; no agent execution or approval is attested by this helper.",
    }


def operation_proofs(report, document, binding):
    """Consume optional semantic evidence only after exact ordinary assessment."""
    applicability = report.get("applicability", {})
    proofs = (
        applicability.get("operation_contracts", {})
        if isinstance(applicability, dict)
        else {}
    )
    proofs = object_value(proofs, "Assessment operation contracts")
    definitions = {
        sha256(canonical_json(value)) for value in document["node_definitions"].values()
    }
    verified = {}
    for digest, row in proofs.items():
        contract = binding.get("semantic_contracts", {}).get(digest)
        evidence = row.get("evidence") if isinstance(row, dict) else None
        pending = [evidence]
        readable = False
        while pending:
            value = pending.pop()
            if isinstance(value, str) and value.strip():
                readable = True
                break
            if isinstance(value, list):
                pending.extend(value)
            elif isinstance(value, dict):
                pending.extend(value.values())
        if (
            digest not in definitions
            or contract is None
            or not isinstance(row, dict)
            or row.get("contract") != contract
            or not readable
        ):
            raise BundleError(
                "not-established",
                "Operation semantics lack exact retained contract and supporting evidence",
                {"operation": digest},
            )
        verified[digest] = copy.deepcopy(contract)
    return verified


def qualify_prepared(
    repository,
    assignment,
    *,
    client,
    assessment=None,
    retain=False,
    combined_task_plan=False,
    source_path=None,
    binding_path=None,
    in_session=False,
    source_reader=None,
):
    repository = Path(repository).resolve()
    object_value(assignment, "Ordinary assignment")
    if retain:
        retention_scope(repository, assignment, client)
    prepared = object_value(
        assignment["target"]["prepared_definition"], "prepared_definition"
    )
    source_path = Path(source_path or prepared["source_path"])
    binding_path = Path(binding_path or prepared["binding_path"])
    if (
        combined_task_plan
        and assignment["target"]["procedure_plan"]["family"] != "task"
    ):
        raise BundleError(
            "incompatible",
            "Only a compatible due Task plan assessment can share this scope",
        )
    source = read_regular(repository, source_path)
    binding_bytes = read_regular(repository, binding_path)
    binding = parse_definition(binding_bytes)
    if (
        definition_id(binding) != prepared["bundle_id"]
        or binding["procedure"] != prepared["procedure"]
        or sha256(source) != binding["procedure"]["source_sha256"]
    ):
        raise BundleError("source-drift", "Prepared exact target changed")
    preview = client.preview(source_path)
    if tuple(
        preview[key]
        for key in ("procedure_id", "procedure_version", "procedure_digest")
    ) != native_key(binding):
        raise BundleError(
            "source-drift", "Native prepared tuple differs from exact target"
        )
    document = yaml.safe_load(source)
    selection_contract(
        source,
        binding,
        assignment["target"]["procedure_plan"]["entrypoint"],
        assignment["authority"]["review"].get("route"),
        {"assignment": assignment},
        document=document,
    )
    try:
        basis = current_basis(
            repository, assignment, in_session=in_session, source_reader=source_reader
        )
    except BundleError as error:
        if in_session and error.code == "reassessment-required":
            raise BundleError(
                error.code, str(error), reassessment_route(document, binding)
            ) from error
        raise
    mapping = {key: value for key, value in binding.items() if key != "procedure"}
    coverage = prepared["coverage_plan"]["coverage"]
    fit(assignment, basis["criteria"], document, mapping, coverage)

    def recheck_target(raw, actual):
        if (
            raw != source
            or actual != binding
            or current_basis(
                repository,
                assignment,
                in_session=in_session,
                source_reader=source_reader,
            )
            != basis
        ):
            raise BundleError(
                "reassessment-required",
                "Exact suitability target changed before adoption",
            )

    design_review = (
        binding["family"] in {"design", "diagnosis"}
        and assignment["authority"]["review"].get("route") != "not-applicable"
    )
    try:
        known_source(source)
    except BundleError as error:
        if error.code != "not-established":
            raise
        unchanged = False
    else:
        qualify_known(source, binding, preview)
        unchanged = prepared["kind"] == "reuse"
    prior = prepared.get("prior_suitability")
    reuse = False
    if not unchanged and prepared.get("kind") == "reuse" and prior is not None:
        if in_session and prepared.get("reuse_basis") != basis:
            raise BundleError(
                "reassessment-required",
                "Established reuse basis changed during the session",
                reassessment_route(document, binding),
            )
        grant = assignment["authority"].get("preparation", {})
        reused = established_reuse(
            repository,
            source,
            binding,
            client=client,
            roots=grant.get(
                "roots", assignment["target"]["procedure_plan"]["discovery_roots"]
            ),
            prior=prior,
            criteria=basis["criteria"],
            context={
                **assignment["target"].get("qualification_context", {}),
                "review": assignment["authority"]["review"],
                "required_obligations": sorted({row["obligation"] for row in coverage}),
            },
            execution_info=bool(
                assignment["target"]["procedure_plan"].get("plan_handoff")
            ),
        )
        reuse = True
    if unchanged or reuse:
        if design_review:
            reviewed = qualify(
                document,
                binding,
                context={
                    **assignment["target"].get("qualification_context", {}),
                    "review": assignment["authority"]["review"],
                    "review_required": True,
                },
                verified_operation_contracts=reused["verified_operation_contracts"]
                if reuse
                else None,
            )
            if reviewed["status"] != "compatible":
                raise BundleError(
                    reviewed["status"],
                    "The selected technical review lacks established source continuity",
                    reviewed,
                )
        retained = None
        if retain:
            grant = assignment["authority"]["preparation"]

            def recheck_reuse(raw, actual):
                recheck_target(raw, actual)
                if not reuse:
                    return qualify_known(raw, actual, preview)
                return established_reuse(
                    repository,
                    raw,
                    actual,
                    client=client,
                    roots=grant["roots"],
                    prior=prior,
                    criteria=basis["criteria"],
                    context={
                        **assignment["target"].get("qualification_context", {}),
                        "review": assignment["authority"]["review"],
                        "required_obligations": sorted(
                            {row["obligation"] for row in coverage}
                        ),
                    },
                )

            retained = publish_bundle(
                repository,
                grant["roots"],
                grant["write_root"],
                source,
                binding,
                qualify=recheck_reuse,
                native_identity=client.identity,
            )
        return {
            "status": "qualified-known",
            "retention": retained,
            "binding": binding,
            "structural": reused["structural"] if reuse else None,
            "assessment": "existing-first-due-checkpoint-preserved",
            "bootstrap": reuse_import(document, binding, assignment, basis, prior)
            if reuse
            else None,
            "limits": [
                "Known reuse preserves original first-due assessments, including Goal without a plan Judge."
            ],
        }
    if not any(
        cap["signature"] == BOOTSTRAP_SIGNATURE
        for node in binding["nodes"].values()
        for cap in node["capabilities"]
    ):
        raise BundleError(
            "not-established",
            "New definition needs initial suitability recording topology before assessment",
        )
    context = copy.deepcopy(assignment["target"].get("qualification_context", {}))
    context["review"] = copy.deepcopy(assignment["authority"].get("review", {}))
    if design_review:
        context["review_required"] = True
    context["required_obligations"] = sorted({row["obligation"] for row in coverage})
    for invocation, retained in [
        ("operation_contracts", "semantic_contracts"),
        ("signatures", "capability_definitions"),
    ]:
        supplied = context.get(invocation, {})
        if any(
            binding.get(retained, {}).get(key) != value
            for key, value in supplied.items()
        ):
            raise BundleError(
                "not-established",
                "Custom semantic definitions must be retained in the exact binding",
            )
    target = suitability_target(
        binding,
        basis,
        combined_task_plan=combined_task_plan,
        coverage_plan=prepared["coverage_plan"],
    )
    report = None
    verified = {}
    if assessment is not None:
        try:
            report = assess_current(assessment, target)
        except BundleError as error:
            if in_session and error.code == "reassessment-required":
                raise BundleError(
                    error.code, str(error), reassessment_route(document, binding)
                ) from error
            raise
        verified = operation_proofs(report, document, binding)
    # A bare caller number is not exact-basis capacity evidence. A bounded
    # assessment can use its independent ordinary report's explicit proof.
    context.pop("criterion_capacity", None)
    capacity = None
    if report is not None and isinstance(report.get("applicability"), dict):
        capacity = report["applicability"].get("criterion_capacity")
    if capacity is not None:
        if (
            not isinstance(capacity, dict)
            or type(capacity.get("value")) is not int
            or capacity["value"]
            < sum(len(row["parts"]) for row in basis["criteria"].values())
            or capacity.get("basis") != basis["criteria"]
            or not capacity.get("evidence")
        ):
            raise BundleError(
                "not-established",
                "Bounded assessment lacks exact original criterion-capacity proof",
            )
        context["criterion_capacity"] = capacity["value"]
    structural = qualify(
        document,
        binding,
        context=context,
        signatures=context.get("signatures"),
        verified_operation_contracts=verified,
        execution_info=bool(assignment["target"]["procedure_plan"].get("plan_handoff")),
    )
    semantic_pending = any(
        row["property"] in {"operation-discriminators", "operation-output-scopes"}
        and row["status"] == "not-established"
        for row in structural["issues"]
    )
    conditional_capacity = False
    if semantic_pending:
        semantic_issues = [
            row
            for row in structural["issues"]
            if row["property"]
            in {"operation-discriminators", "operation-output-scopes"}
            and row["status"] == "not-established"
        ]
        proposed = {
            digest: contract
            for digest, contract in binding.get("semantic_contracts", {}).items()
            if contract.get("discriminators") or contract.get("output_scopes")
        }
        conditional = qualify(
            document,
            binding,
            context=context,
            signatures=context.get("signatures"),
            verified_operation_contracts={**proposed, **verified},
        )
        unresolved_capacity = conditional["status"] == "not-established" and all(
            row["property"] in {"capability", "guarantee-minimum"}
            and row.get("unknown_properties") == ["criterion-capacity"]
            for row in conditional["issues"]
        )
        structural = {
            **conditional,
            "status": "incompatible"
            if conditional["status"] == "incompatible"
            else "not-established",
            "issues": semantic_issues + conditional["issues"],
        }
        if conditional["status"] == "compatible" or unresolved_capacity:
            conditional_capacity = unresolved_capacity
            structural["operation_proof_pending"] = True
        else:
            semantic_pending = False
    capacity_pending = conditional_capacity or (
        structural["status"] == "not-established"
        and all(
            row["property"] in {"capability", "guarantee-minimum"}
            and row.get("unknown_properties") == ["criterion-capacity"]
            for row in structural["issues"]
        )
    )
    if structural["status"] != "compatible" and not (
        assessment is None
        and (
            capacity_pending
            or (semantic_pending and structural.get("operation_proof_pending"))
        )
    ):
        raise BundleError(
            structural["status"], "Execution obligations are not qualified", structural
        )
    if assessment is None:
        if in_session:
            raise BundleError(
                "reassessment-required",
                "Retrieve the actual existing assessment or use an affected in-session planning/Judge capability; a new call cannot be pre-start",
                reassessment_route(document, binding),
            )
        return {
            "status": "assessment-required",
            "structural": structural,
            "assignment": judge_assignment(
                assignment, target, assessment_requirements(document, binding)
            ),
            "target": target,
            "capacity_proof_due": capacity_pending,
        }
    bootstrap = bootstrap_import(document, binding, target, report)
    # Reconcile sources and target again before any retention effect.
    if (
        current_basis(
            repository, assignment, in_session=in_session, source_reader=source_reader
        )
        != basis
        or read_regular(repository, source_path) != source
        or read_regular(repository, binding_path) != binding_bytes
    ):
        raise BundleError(
            "reassessment-required", "Suitability basis changed during qualification"
        )
    retained = None
    if retain:
        grant = assignment["authority"].get("preparation", {})

        def recheck(raw, actual):
            recheck_target(raw, actual)
            assess_current(report, target)

        retained = publish_bundle(
            repository,
            grant["roots"],
            grant["write_root"],
            source,
            binding,
            qualify=recheck,
            native_identity=client.identity,
        )
    return {
        "status": "qualified",
        "structural": structural,
        "binding": binding,
        "target": target,
        "bootstrap": bootstrap,
        "retention": retained,
        "activation": "activated-family-consumer-available"
        if binding["family"] in {"task", "goal", "validation", "design", "diagnosis"}
        else "family-activation-remains-required",
    }


def assessment_requirements(document, binding):
    """Describe exact proof inputs for the already due ordinary assessment."""
    contracts = binding.get("semantic_contracts", {})
    definitions = document["node_definitions"]
    operations = {
        sha256(canonical_json(definition)) for definition in definitions.values()
    }
    claims = {
        digest: copy.deepcopy(contract)
        for digest, contract in contracts.items()
        if digest in operations
        and (contract.get("discriminators") or contract.get("output_scopes"))
    }
    signatures = {
        **capability_signatures(),
        **binding.get("capability_definitions", {}),
    }
    bounded = []
    for placement in document["graph"]["nodes"]:
        node = placement["id"]
        items = {
            item["id"]: item for item in definitions[placement["use"]].get("items", [])
        }
        fields = set()
        for capability in binding["nodes"][node]["capabilities"]:
            signature = signatures.get(capability["signature"], {})
            for candidate in [signature, *guarantee_minima(signature)]:
                fields.update(
                    capability["fields"].get(item, item)
                    for item in candidate.get("criterion_counts", [])
                )
        for field in sorted(fields):
            if field in items and "maximum" in items[field]:
                bounded.append(
                    {"node": node, "item": field, "maximum": items[field]["maximum"]}
                )
    return {
        "operation_contracts": claims,
        "operation_contracts_report_field": "applicability.operation_contracts",
        "operation_contracts_scope": "Establish any unestablished claims using these exact retained contracts and current readable evidence; established native contracts and supported derivations need no new proof.",
        "criterion_capacity": {
            "bounded_fields": bounded,
            "report_field": "applicability.criterion_capacity",
            "basis": "Exact current original criteria, including all compound parts",
        },
        "evidence_scope": "Include any due proof in this same current affected ordinary report; this description supplies no proof or authority and requests no additional Judge or bootstrap.",
    }


def reassessment_route(document, binding):
    """Describe an existing source capability; never dispatch or replace a session."""
    from adaptive_definitions import ASSETS

    operations = json.loads(
        (ASSETS / "adaptive/operation-contracts-v1.json").read_text()
    )
    operations.update(binding.get("semantic_contracts", {}))
    available = []
    placements = {node["id"]: node for node in document["graph"]["nodes"]}
    contracts = {
        node: operations.get(
            sha256(canonical_json(document["node_definitions"][placement["use"]])), {}
        )
        for node, placement in placements.items()
    }
    for node, declaration in binding["nodes"].items():
        if declaration["role"] != "judge" or "task-plan" not in contracts[node].get(
            "checkpoint_scopes", []
        ):
            continue
        selected, other_work = False, False
        for row in placements[node].get("evidence_from", []):
            source = contracts[row["node"]]
            planning = [
                item
                for item, scope in source.get("output_scopes", {}).items()
                if scope == "task-plan" and ("items" not in row or item in row["items"])
            ]
            selected |= bool(planning) and row.get("required", True)
            other_work |= (
                row.get("required", True)
                and source.get("effect") == "work"
                and not planning
            )
        if selected and not other_work:
            available.append(node)
    return {
        "status": "existing-planning-judge" if available else "missing-topology",
        "nodes": available,
        "next_owner": "Orchestrator",
        "required_scope": ["affected-planning", "procedure-suitability"],
        "assessment_requirements": assessment_requirements(document, binding),
        "same_operation_retrieval": "Recover a pending actual result before assigning replacement assessment",
        "replacement": "Not authorized by reassessment; use the shared consented atomic path only for missing topology.",
    }


def resolver_scope(repository, assignment, roots):
    """Keep a disclosed resolver domain complete without requiring write authority."""
    preparation = assignment.get("authority", {}).get("preparation", {})
    if not isinstance(preparation, dict) or "roots" not in preparation:
        return
    declared = roots_for(repository, preparation["roots"])
    searched = roots_for(repository, roots)
    if any(root not in searched for root in declared):
        raise BundleError(
            "not-established", "Resolver search omits a disclosed definition root"
        )


def retention_scope(repository, assignment, client, *, roots=None, write_root=None):
    grant = assignment["authority"].get("preparation")
    if not isinstance(grant, dict) or grant.get("native_authoring") is not True:
        raise BundleError(
            "authority-required",
            "Current envelope does not cover local execution-definition retention",
        )
    if Path(client.repository).resolve() != Path(repository).resolve():
        raise BundleError("unsafe", "Retention native proof uses another worktree")
    approved = roots_for(repository, grant["roots"])
    selected = roots_for(repository, roots if roots is not None else grant["roots"])
    resolver_scope(repository, assignment, selected)
    target = contained(
        repository, Path(write_root if write_root is not None else grant["write_root"])
    )
    if (
        target not in approved
        or target != contained(repository, Path(grant["write_root"]))
        or any(root not in approved for root in selected)
    ):
        raise BundleError(
            "authority-required", "Retention locations differ from the disclosed scope"
        )
    return grant


def established_reuse(
    repository,
    source,
    binding,
    *,
    client,
    roots,
    prior,
    context=None,
    criteria=None,
    execution_info=False,
):
    """Establish retained definition reuse, not current product/assessment success."""
    from adaptive_bundles import resolve_bundle

    if client is None:
        raise BundleError(
            "not-established",
            "Plan-only cannot run the native proof for retained adaptive reuse",
            {"candidate_reuse_pending": True},
        )
    if Path(client.repository).resolve() != Path(repository).resolve():
        raise BundleError("unsafe", "Reuse native proof uses another worktree")
    resolved = resolve_bundle(
        repository,
        roots,
        native_key(binding),
        native_identity=client.identity,
        bundle_id=definition_id(binding),
    )
    if resolved["status"] != "resolved":
        raise BundleError(
            resolved["status"],
            "Adaptive reuse needs an intact exact already-retained bundle",
            resolved,
        )
    if resolved["source"] != source or resolved["binding"] != binding:
        raise BundleError(
            "source-drift", "Adaptive reuse differs from retained exact bytes"
        )
    target = object_value(
        object_value(prior, "Prior ordinary assessment").get("target"),
        "Prior assessment target",
    ).get("procedure_suitability")
    target = object_value(target, "Prior suitability scope")
    if target.get("candidate") != {
        "bundle_id": definition_id(binding),
        "procedure": binding["procedure"],
    }:
        raise BundleError(
            "not-established",
            "Prior suitability does not establish this exact definition",
        )
    assess_current(prior, target)
    document = yaml.safe_load(source)
    verified = operation_proofs(prior, document, binding)
    context = {} if context is None else copy.deepcopy(context)
    context.pop("criterion_capacity", None)
    capacity = (
        prior.get("applicability", {}).get("criterion_capacity")
        if isinstance(prior.get("applicability"), dict)
        else None
    )
    if capacity is not None and (
        isinstance(capacity, dict)
        and type(capacity.get("value")) is int
        and criteria is not None
        and capacity.get("basis") == criteria
        and capacity["value"] >= sum(len(row["parts"]) for row in criteria.values())
        and capacity.get("evidence")
    ):
        context["criterion_capacity"] = capacity["value"]
    for invocation, retained in [
        ("operation_contracts", "semantic_contracts"),
        ("signatures", "capability_definitions"),
    ]:
        if any(
            binding.get(retained, {}).get(key) != value
            for key, value in context.get(invocation, {}).items()
        ):
            raise BundleError(
                "not-established", "Reuse semantic definitions are not retained"
            )
    result = qualify(
        document,
        binding,
        context=context,
        verified_operation_contracts=verified,
        execution_info=execution_info,
    )
    if result["status"] != "compatible":
        raise BundleError(
            result["status"], "Current reused structure is unqualified", result
        )
    if not any(
        cap["signature"] == BOOTSTRAP_SIGNATURE
        for node in binding["nodes"].values()
        for cap in node["capabilities"]
    ):
        raise BundleError(
            "not-established",
            "This retained source lacks a supported established-reuse bootstrap contract",
        )
    bootstrap = next(
        (node, cap)
        for node, declaration in binding["nodes"].items()
        for cap in declaration["capabilities"]
        if cap["signature"] == BOOTSTRAP_SIGNATURE
    )
    placement, capability = bootstrap
    native_node = next(
        node for node in document["graph"]["nodes"] if node["id"] == placement
    )
    timing_id = capability["fields"].get("suitability-timing", "suitability-timing")
    timing = next(
        item
        for item in document["node_definitions"][native_node["use"]]["items"]
        if item["id"] == timing_id
    )
    if "established-reuse" not in timing.get("choices", []):
        raise BundleError(
            "not-established",
            "This bootstrap cannot record truthful established-reuse timing",
        )
    return {**resolved, "structural": result, "verified_operation_contracts": verified}


def reuse_import(document, binding, assignment, basis, prior):
    record = next(
        node
        for node, declaration in binding["nodes"].items()
        if any(
            cap["signature"] == BOOTSTRAP_SIGNATURE
            for cap in declaration["capabilities"]
        )
    )
    aliases = next(
        cap["fields"]
        for cap in binding["nodes"][record]["capabilities"]
        if cap["signature"] == BOOTSTRAP_SIGNATURE
    )
    checkpoint = {
        key: copy.deepcopy(assignment.get(key))
        for key in (
            "work",
            "target",
            "authority",
            "procedure",
            "native",
            "evidence",
            "gaps",
        )
    }
    checkpoint.update(
        schema="aquarium.orchestration-checkpoint/v2",
        checkpoint="adequate-established-definition-reuse",
        current_basis=basis,
        prior_definition_assessment=prior,
        current_fit=assignment["target"]["prepared_definition"]["coverage_plan"],
        pending_operations=[],
        next_owner="Original first-due workflow checkpoint",
        limits="Prior independent evidence establishes the unchanged definition; this is current selection/fit evidence, not a new Judge or product pass.",
    )
    values = {
        "suitability-target": json.dumps(
            {
                "bundle_id": definition_id(binding),
                "basis_sha256": sha256(canonical_json(basis)),
            },
            sort_keys=True,
        ),
        "suitability-timing": "established-reuse",
        "suitability-verdict": "pass",
        "suitability-unmet": 0,
        "suitability-unverified": 0,
        "suitability-current": {
            "outcome": "pass",
            "operation_id": BOOTSTRAP_OPERATION,
            "operation_digest": BOOTSTRAP_DIGEST,
        },
    }
    return {
        "node": record,
        "artifact_evidence": {
            aliases.get("suitability-assessment", "suitability-assessment"): checkpoint
        },
        "items": {aliases.get(key, key): value for key, value in values.items()},
        "native_attachment": "Attach actual ordinary selection and prior assessment evidence through the supported native artifact contract; no location is asserted.",
    }
