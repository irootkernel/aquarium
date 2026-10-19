"""Design consumers and current ordinary evidence; synthetic agents are not execution proof."""

import copy
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))

from adaptive_admission import reference_mapping
from adaptive_bundles import BundleError, sha256
from adaptive_definitions import ASSETS, canonical_json
from adaptive_design import application, quality
from adaptive_execution import execution_context, phase_skills
from adaptive_preparation import prepare
from adaptive_suitability import qualify_prepared
from test_adaptive_preparation_unit import Oracle, assignment


@pytest.fixture
def design(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    value = assignment(tmp_path, mode="prepare")
    plan = value["target"]["procedure_plan"]
    plan.update(family="design", entrypoint="new-feature")
    raw = (ASSETS / "podway/procedures/aquarium-design-v2.yaml").read_bytes()
    source = tmp_path / "definitions/design with spaces.yaml"
    source.parent.mkdir()
    source.write_bytes(raw)
    mapping = reference_mapping(raw)
    effects = sorted(
        {effect for row in mapping["nodes"].values() for effect in row["effects"]}
    )
    plan["effects"] = effects
    value["authority"]["effects"] = effects[:]
    coverage = [
        {**row, "obligation": next(iter(mapping["obligations"]))}
        for row in plan["drafts"][0]["coverage"]
    ]
    plan["candidates"] = [
        {
            "path": "definitions/design with spaces.yaml",
            "sha256": sha256(raw),
            "coverage": coverage,
            "reason": "The unchanged Design contract covers the requested documents.",
        }
    ]
    client = Oracle(tmp_path)
    value = prepare(tmp_path, value, client=client)["assignment"]
    retained = qualify_prepared(tmp_path, value, client=client, retain=True)
    observation = {
        "status": {
            "procedure": retained["binding"]["procedure"],
            "session": {"id": str(uuid.uuid4()), "lifecycle": "running", "revision": 1},
            "current": {"node": {"graph_node_id": "discover"}},
        },
        "guidance": {"node": {"graph_node_id": "discover"}, "readback": []},
        "active_items": [],
        "mutation_templates": [],
    }
    client.health = lambda: copy.deepcopy(observation)
    return tmp_path, {"assignment": value}, client, observation, retained


def consume(design, entrypoint="new-feature", **kwargs):
    design[1]["assignment"]["target"]["procedure_plan"]["entrypoint"] = entrypoint
    return execution_context(
        design[0],
        roots=["definitions"],
        entrypoint=entrypoint,
        qualification=design[1],
        client=design[2],
        **kwargs,
    )


@pytest.mark.parametrize("entrypoint", ["new-feature", "new-project", "refactor"])
def test_adequate_known_design_reuses_first_due_checkpoint_without_suitability_report(
    design, entrypoint
):
    result = consume(design, entrypoint)
    assert result["status"] == "dispatch-ready"
    assert result["qualification"]["status"] == "qualified-known"
    assert result["dispatch"]["role"] == "executor"
    assert result["phase_skills"] == ["interview"]
    assert result["dispatch"]["work"] == design[1]["assignment"]["work"]
    assert (
        result["dispatch"]["target"]["design_context"]["product_implementation"]
        is False
    )
    assert set(design[1]["assignment"]["authority"]["excluded"]).issubset(
        result["dispatch"]["authority"]["excluded"]
    )
    assert (
        result["dispatch"]["authority"]["review"]
        == design[1]["assignment"]["authority"]["review"]
    )


@pytest.mark.parametrize(
    "node,role",
    [
        ("evaluator-discovery", "evaluator"),
        ("quality", "executor"),
        ("decide-quality", "coordinator"),
        ("approve-diff", "coordinator"),
        ("closeout", "coordinator"),
    ],
)
def test_nonselecting_recovery_preserves_actual_role_and_primary_decisions(
    design, node, role
):
    design[3]["guidance"]["node"]["graph_node_id"] = node
    result = consume(design)
    assert result["role"] == role
    assert result["status"] == (
        "coordinator-owned" if role == "coordinator" else "dispatch-ready"
    )
    if role == "evaluator":
        assert result["dispatch"]["authority"]["effects"] == []
    if node == "quality":
        assert result["phase_skills"] == ["qa"]


@pytest.mark.parametrize(
    "state,expected",
    [
        ("prepared", "prepared-resolved"),
        ("completed", "terminal-resolved"),
        ("cancelled", "terminal-resolved"),
    ],
)
def test_design_prepared_and_terminal_tuple_recovery_does_not_claim_success(
    design, state, expected
):
    design[3]["status"]["session"]["lifecycle"] = state
    design[3]["guidance"] = None
    result = consume(design)
    assert result["status"] == expected
    assert result["dispatch"] is None
    assert "achieved" not in result


def test_same_definition_successor_uses_actual_new_session_and_retained_pending_commit(
    design,
):
    old = design[3]["status"]["session"]["id"]
    design[3]["status"]["session"]["id"] = str(uuid.uuid4())
    design[1]["pending_operations"] = [{"kind": "verified-commit", "commit": "a" * 40}]
    result = consume(design)
    assert result["procedure"]["session"]["id"] != old
    assert result["pending_operations"] == design[1]["pending_operations"]
    with pytest.raises(BundleError) as error:
        consume(design, session=old)
    assert error.value.code == "session-conflict"


@pytest.mark.parametrize("entrypoint", ["new-feature", "new-project", "refactor"])
def test_explicit_optout_precedes_health_and_invalid_qualification(
    tmp_path, entrypoint
):
    class NoNative:
        def health(self):
            pytest.fail("Opt-out inspected Podway")

    result = execution_context(
        tmp_path,
        roots=[],
        entrypoint=entrypoint,
        qualification=None,
        client=NoNative(),
        opt_out=True,
    )
    assert result["status"] == "podway-inapplicable"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("optout", [False, True])
def test_public_non_git_branch_needs_no_native_binary_roots_or_definitions(
    tmp_path, optout
):
    cli = ROOT / "plugins/aquarium/shared/manage_adaptive_procedure.py"
    argv = [
        sys.executable,
        "-S",
        str(cli),
        "context",
        "--repository",
        str(tmp_path),
        "--entrypoint",
        "new-project",
        "--podway",
        str(tmp_path / "must-not-run"),
        "--qualification",
        str(tmp_path / "must-not-read"),
    ]
    if optout:
        argv.append("--podway-opt-out")
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "podway-inapplicable"
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("raw", ["PASS", "REVISE", "FAIL"])
@pytest.mark.parametrize("owner", ["discovery", "draft", None])
def test_adjudicable_raw_qa_keeps_operation_pass_and_original_owner(raw, owner):
    findings = (
        []
        if owner is None
        else [
            {
                "id": "M1",
                "owner": owner,
                "disposition": "unresolved",
                "basis": "Original artifact contradicts the requested contract.",
            }
        ]
    )
    result = quality(
        {
            "operation_outcome": "pass",
            "raw_verdict": raw,
            "draft_sha256": sha256(b"draft"),
            "findings": findings,
        }
    )
    assert result["operation_outcome"] == "pass"
    assert result["raw_verdict"] == raw
    assert result["owner"] == (owner or "approval")
    assert result["findings"] == findings


@pytest.mark.parametrize("outcome", ["fail", "inconclusive"])
def test_missing_or_failed_qa_returns_operation_recovery_not_content_owner(outcome):
    assert quality({"operation_outcome": outcome})["owner"] == "quality"


@pytest.mark.parametrize(
    "row,code",
    [
        ({"id": "M1", "disposition": "rejected"}, "not-established"),
        (
            {
                "id": "M1",
                "owner": "quality",
                "disposition": "unresolved",
                "basis": "Actual content issue",
            },
            "incompatible",
        ),
    ],
)
def test_qa_does_not_erase_findings_or_assign_content_to_invocation_retry(row, code):
    with pytest.raises(BundleError) as error:
        quality(
            {
                "operation_outcome": "pass",
                "raw_verdict": "FAIL",
                "draft_sha256": sha256(b"draft"),
                "findings": [row],
            }
        )
    assert error.value.code == code


def proposal(tmp_path):
    (tmp_path / "README.md").write_text("Original\n")
    value = {
        "diff": "Complete displayed documentation diff",
        "targets": {
            "README.md": {
                "before": sha256(b"Original\n"),
                "after": sha256(b"Approved\n"),
            }
        },
    }
    approval = {
        "source": "user",
        "decision": "approved",
        "proposal": copy.deepcopy(value),
    }
    return value, approval


def test_application_verifies_exact_approval_before_writes_and_applied_bytes(tmp_path):
    value, approval = proposal(tmp_path)
    assert application(tmp_path, value, approval)["status"] == "approved-current"
    assert (tmp_path / "README.md").read_text() == "Original\n"
    (tmp_path / "README.md").write_text("Approved\n")
    assert (
        application(tmp_path, value, approval, applied=True)["status"]
        == "verified-applied"
    )
    assert application(tmp_path, value, approval)["status"] == "reapproval-required"


@pytest.mark.parametrize("change", ["diff", "target", "before", "after", "authority"])
def test_changed_proposal_or_target_requires_actual_reapproval(tmp_path, change):
    value, approval = proposal(tmp_path)
    if change == "diff":
        value["diff"] += " changed"
    elif change == "target":
        (tmp_path / "README.md").write_text("Concurrent change\n")
    elif change in {"before", "after"}:
        value["targets"]["README.md"][change] = sha256(b"different")
    else:
        approval["source"] = "evaluator"
    assert application(tmp_path, value, approval)["status"] in {
        "reapproval-required",
        "approval-required",
    }


def test_application_executor_waits_for_actual_exact_diff_authority(design):
    design[3]["guidance"]["node"]["graph_node_id"] = "apply-documents"
    assert consume(design)["status"] == "approval-required"
    value, approval = proposal(design[0])
    design[1]["assignment"]["target"]["design"] = {"proposal": value}
    design[1]["assignment"]["authority"]["document_approval"] = approval
    # Approval is current ordinary evidence, not part of the pre-start immutable basis.
    result = consume(design)
    assert result["status"] == "dispatch-ready"
    assert (
        result["dispatch"]["target"]["design_context"]["application"]["status"]
        == "approved-current"
    )
    assert (
        result["dispatch"]["target"]["design_context"]["delivery_commit"]
        == "separate-authority"
    )
    (design[0] / "README.md").write_text("Changed after approval\n")
    result = consume(design)
    assert result["status"] == "reapproval-required"
    assert result["dispatch"] is None
    (design[0] / "README.md").write_text("Approved\n")
    design[1]["assignment"]["target"]["design"]["applied"] = True
    recovered = consume(design)
    assert recovered["design"]["application"]["status"] == "verified-applied"
    assert recovered["dispatch"]["authority"]["effects"] == []
    assert (
        recovered["dispatch"]["target"]["design_context"]["application"]["status"]
        == "verified-applied"
    )


def test_approved_upstream_leaf_mapping_preserves_entrypoint_specific_pm_or_seed(
    design,
):
    value = design[1]["assignment"]
    value["target"]["procedure_plan"]["phase_skills"] = {
        "discover": ["interview", "pm"],
        "draft": ["seed"],
    }
    assert consume(design)["phase_skills"] == ["interview", "pm"]
    design[3]["guidance"]["node"]["graph_node_id"] = "draft"
    assert consume(design)["phase_skills"] == ["seed"]
    value["target"]["procedure_plan"]["phase_skills"]["draft"] = ["auto"]
    with pytest.raises(BundleError) as error:
        consume(design)
    assert error.value.code == "invalid-input"


def test_namespaced_design_owner_survives_native_reference_rewriting():
    from adaptive_composition import expand
    from test_adaptive_qualification_unit import known

    document, binding = known("design")
    expanded, mapping, _, _ = expand(
        document,
        {key: value for key, value in binding.items() if key != "procedure"},
        "shaped",
        {},
    )
    value = {"target": {"procedure_plan": {}}}
    assert phase_skills(expanded, mapping, value, "shaped-quality") == ["qa"]
    assert phase_skills(expanded, mapping, value, "shaped-discover") == ["interview"]


def adaptive_design(*, conditional=False):
    """Consolidate context/discovery, with optional original-source research."""
    from test_adaptive_qualification_unit import known

    document, mapping = known("design")
    mapping.pop("procedure")
    document["id"] = "aquarium-adapt-design-" + (
        "research" if conditional else "grouped"
    )
    document["version"] = "1"
    definitions = document["node_definitions"]
    discover = definitions["discovery-record"]
    discover["items"].insert(
        0, copy.deepcopy(definitions["context-record"]["items"][0])
    )
    discover["intent"] = (
        "Reconcile original repository authority and requirements together."
    )
    definitions.pop("context-record")
    document["graph"]["entry"] = "discover"
    document["graph"]["nodes"] = [
        row for row in document["graph"]["nodes"] if row["id"] != "capture-context"
    ]
    mapping["nodes"].pop("capture-context")
    for row in document["graph"]["nodes"]:
        for selector in row.get("evidence_from", []):
            if selector["node"] == "capture-context":
                selector["node"] = "discover"
        for route in row.get("routes", {}).values():
            if route["to"] == "capture-context":
                route["to"] = "discover"
    for row in document["graph"]["nodes"]:
        if row["id"] == "discover":
            row.pop("evidence_from", None)
    for row in document["graph"]["nodes"]:
        if row["id"] == "confirm-discovery-evidence-needed-authority":
            row["routes"].pop("capture-context")
            definitions[row["use"]]["options"] = [
                option
                for option in definitions[row["use"]]["options"]
                if option["id"] != "capture-context"
            ]
    for obligation in mapping["obligations"].values():
        for producer in obligation["producers"]:
            if producer["node"] == "capture-context":
                producer["node"] = "discover"
    if "manual_rework" in document:
        document["manual_rework"]["allowed_targets"] = list(
            dict.fromkeys(
                "discover" if node == "capture-context" else node
                for node in document["manual_rework"]["allowed_targets"]
            )
        )
    if conditional:
        discover["items"].append(
            {
                "id": "depth",
                "type": "choice",
                "prompt": "Which actual requirements need original-source research?",
                "required": True,
                "choices": ["bounded", "research"],
            }
        )
        definitions["scope-choice"] = {
            "type": "decision",
            "title": "Resolve requirements depth",
            "objective": "Route current source uncertainty",
            "prompt": "Is further source research due?",
            "reason": {"required": True, "prompt": "Cite original source uncertainty."},
            "options": [
                {
                    "id": value,
                    "label": value,
                    "criteria": "Current original source uncertainty requires further research."
                    if value == "research"
                    else "Original authority and requirements are bounded without further research.",
                    "guards": [
                        {
                            "evidence": {"node": "discover", "item": "depth"},
                            "equals": value,
                        }
                    ],
                }
                for value in ["bounded", "research"]
            ],
        }
        definitions["research-work"] = {
            "type": "action",
            "title": "Research source ambiguity",
            "intent": "Read the approved original source and deliver resolved constraints.",
            "items": [
                {
                    "id": "constraints",
                    "type": "text",
                    "prompt": "Record original source and resolved constraints.",
                    "required": True,
                    "min_length": 1,
                    "max_length": 3000,
                    "multiline": True,
                }
            ],
        }
        for row in document["graph"]["nodes"]:
            if row["id"] == "discover":
                row["next"] = "scope-choice"
            if row["id"] in {"evaluator-discovery", "prepare-design-assessment"}:
                row["evidence_from"].append(
                    {
                        "node": "research-work",
                        "required": False,
                        "items": ["constraints"],
                    }
                )
        document["graph"]["nodes"] += [
            {
                "id": "scope-choice",
                "use": "scope-choice",
                "evidence_from": [
                    {"node": "discover", "required": True, "items": ["depth"]}
                ],
                "routes": {
                    "bounded": {"to": "evaluator-discovery", "effect": "advance"},
                    "research": {"to": "research-work", "effect": "advance"},
                },
            },
            {
                "id": "research-work",
                "use": "research-work",
                "next": "evaluator-discovery",
            },
        ]
        mapping["nodes"]["scope-choice"] = {
            "kind": "decision",
            "role": "coordinator",
            "effects": [],
            "capabilities": [],
        }
        mapping["nodes"]["research-work"] = {
            "kind": "action",
            "role": "executor",
            "effects": ["work"],
            "capabilities": [],
        }
        mapping["obligations"]["evaluator-discovery"]["producers"].append(
            {"node": "research-work", "item": "constraints"}
        )
        mapping.setdefault("semantic_contracts", {})[
            sha256(canonical_json(definitions["research-work"]))
        ] = {
            "roles": ["executor"],
            "effect": "work",
            "basis": "Read scoped original sources and deliver independently assessed constraints.",
            "delivery_items": ["constraints"],
        }
    mapping.setdefault("semantic_contracts", {})[sha256(canonical_json(discover))] = {
        "roles": ["executor"],
        "effect": "work",
        "basis": "Reconcile original authority and discovery in one independently assessed work unit.",
        "delivery_items": [item["id"] for item in discover["items"]],
    }
    return document, mapping


@pytest.mark.parametrize("conditional", [False, True])
def test_real_grouped_and_conditional_design_changes_preserve_obligations(conditional):
    from adaptive_qualification import qualify
    from test_adaptive_qualification_unit import bound

    document, mapping = adaptive_design(conditional=conditional)
    result = qualify(document, bound(document, mapping))
    assert result["status"] == "compatible", result["issues"]
    assert document["graph"]["entry"] == "discover"
    assert "capture-context" not in mapping["nodes"]
    assert {
        row["node"]
        for row in mapping["obligations"]["evaluator-discovery"]["producers"]
    } == ({"discover", "research-work"} if conditional else {"discover"})
    if conditional:
        routes = next(
            row["routes"]
            for row in document["graph"]["nodes"]
            if row["id"] == "scope-choice"
        )
        assert {route["to"] for route in routes.values()} == {
            "research-work",
            "evaluator-discovery",
        }


def test_conditional_research_requires_actual_selected_producer_evidence():
    from adaptive_qualification import qualify
    from test_adaptive_qualification_unit import bound

    document, mapping = adaptive_design(conditional=True)
    evaluator = next(
        row for row in document["graph"]["nodes"] if row["id"] == "evaluator-discovery"
    )
    evaluator["evidence_from"] = [
        row for row in evaluator["evidence_from"] if row["node"] != "research-work"
    ]
    assert qualify(document, bound(document, mapping))["status"] == "incompatible"


@pytest.mark.parametrize(
    "conditional,review", [(False, False), (True, False), (False, True)]
)
def test_adaptive_design_prepare_qualify_retain_and_running_consumer(
    tmp_path, conditional, review
):
    from test_adaptive_suitability_unit import Oracle as SuitabilityOracle
    from test_adaptive_suitability_unit import report_for

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    value = assignment(tmp_path, mode="prepare")
    document, mapping = adaptive_design(conditional=conditional)
    if review:
        document, mapping, context = review_design()
        value["target"]["qualification_context"] = context
    plan = value["target"]["procedure_plan"]
    plan.update(family="design", entrypoint="refactor")
    if review:
        plan["review"]["route"] = "herdr"
        value["authority"]["review"]["route"] = "herdr"
    effects = sorted(
        {effect for row in mapping["nodes"].values() for effect in row["effects"]}
    )
    plan["effects"] = effects
    value["authority"]["effects"] = effects[:]
    draft = plan["drafts"][0]
    draft.update(document=document, mapping=mapping)
    draft["reason"] = (
        "Combine original authority and discovery with bounded conditional research instead of separate context work."
    )
    draft["coverage"] = [
        {**row, "obligation": "evaluator-discovery"} for row in draft["coverage"]
    ]
    plan["source_dispositions"] = {"aquarium-design-v2.yaml": draft["reason"]}
    plan["design_phases"] = {
        "discover": "discovery",
        **({"research-work": "discovery"} if conditional else {}),
    }
    client = SuitabilityOracle(tmp_path)
    value = prepare(tmp_path, value, client=client, bootstrap=True)["assignment"]
    pending = qualify_prepared(tmp_path, value, client=client)
    assert pending["status"] == "assessment-required"
    report = report_for(pending["target"])
    retained = qualify_prepared(
        tmp_path, value, client=client, assessment=report, retain=True
    )
    assert retained["activation"] == "activated-family-consumer-available"
    observation = {
        "status": {
            "procedure": retained["binding"]["procedure"],
            "session": {"id": str(uuid.uuid4()), "lifecycle": "running", "revision": 1},
            "current": {"node": {"graph_node_id": "discover"}},
        },
        "guidance": {
            "node": {"graph_node_id": "research-work" if conditional else "discover"},
            "readback": [],
        },
        "active_items": [],
        "mutation_templates": [],
    }
    client.health = lambda: copy.deepcopy(observation)
    result = execution_context(
        tmp_path,
        roots=["definitions"],
        entrypoint="refactor",
        qualification={"assignment": value, "assessment": report},
        client=client,
    )
    assert result["status"] == "dispatch-ready"
    assert result["phase_skills"] == ["interview"]
    assert result["dispatch"]["procedure"]["node"] == (
        "research-work" if conditional else "discover"
    )


def test_semantic_application_capability_cannot_be_hidden_by_phase_map(design):
    value = design[1]["assignment"]
    value["target"]["procedure_plan"]["design_phases"] = {
        "apply-documents": "discovery"
    }
    design[3]["guidance"]["node"]["graph_node_id"] = "apply-documents"
    with pytest.raises(BundleError) as error:
        consume(design)
    assert error.value.code == "incompatible"


def test_explicit_selected_technical_route_is_preserved_and_mismatch_stops(design):
    value = design[1]["assignment"]
    value["authority"]["review"]["route"] = "herdr"
    value["target"]["procedure_plan"]["review"]["route"] = "herdr"
    with pytest.raises(BundleError) as missing:
        consume(design, route="herdr")
    assert missing.value.code == "incompatible"
    assert any(
        row["property"] == "selected-review-control"
        for row in missing.value.details["issues"]
    )
    with pytest.raises(BundleError) as error:
        consume(design, route="waived")
    assert error.value.code == "route-unavailable"


def review_design():
    from test_adaptive_qualification_unit import with_review

    document, mapping = adaptive_design()
    body = {
        "type": "action",
        "title": "Retain selected review handoff",
        "intent": "Index complete selected review results without changing product or documents.",
        "items": [
            {
                "id": "review-summary",
                "type": "text",
                "prompt": "Reference complete selected review and retained original findings.",
                "required": True,
                "min_length": 1,
                "max_length": 3000,
                "multiline": True,
            }
        ],
    }
    document["node_definitions"]["assess"] = body
    for row in document["graph"]["nodes"]:
        if row.get("next") == "evaluator-design":
            row["next"] = "assess"
    document["graph"]["nodes"].append(
        {"id": "assess", "use": "assess", "next": "evaluator-design"}
    )
    mapping["nodes"]["assess"] = {
        "kind": "action",
        "role": "coordinator",
        "effects": [],
        "capabilities": [],
    }
    contracts = {
        sha256(canonical_json(body)): {
            "roles": ["coordinator"],
            "effect": "evidence",
            "basis": "Bounded selected-review index; no product mutation or authority is granted.",
            "delivery_items": ["review-summary"],
        }
    }
    document, mapping, context = with_review(
        document, mapping, {"operation_contracts": contracts}
    )
    mapping.setdefault("semantic_contracts", {}).update(
        context.pop("operation_contracts")
    )
    context["review_required"] = True
    return document, mapping, context


def test_genuinely_review_capable_design_preserves_route_result_and_recovery():
    from adaptive_qualification import qualify
    from test_adaptive_qualification_unit import bound

    document, mapping, context = review_design()
    binding = bound(document, mapping)
    assert qualify(document, binding, context=context)["status"] == "compatible"
    selected = next(
        row for row in document["graph"]["nodes"] if row["id"] == "check-review"
    )
    selected["evidence_from"][0]["items"].remove("route-binding-result")
    assert (
        qualify(document, bound(document, mapping), context=context)["status"]
        == "incompatible"
    )


def test_git_backed_project_subdirectory_does_not_silently_opt_out(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    child = tmp_path / "project"
    child.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(ROOT / "plugins/aquarium/shared/manage_adaptive_procedure.py"),
            "context",
            "--repository",
            str(child),
            "--root",
            "definitions",
            "--entrypoint",
            "new-project",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "missing-prerequisite"
    assert list(child.iterdir()) == []


@pytest.mark.parametrize(
    "entrypoint,optout",
    [
        ("new-project", False),
        ("new-project", True),
        ("new-feature", True),
        ("refactor", True),
    ],
)
@pytest.mark.parametrize("mode", ["plan-only", "prepare"])
def test_preparation_api_and_public_cli_branch_before_source_selection(
    tmp_path, monkeypatch, entrypoint, optout, mode
):
    import adaptive_preparation

    value = assignment(tmp_path, mode=mode)
    value["target"]["procedure_plan"].update(family="design", entrypoint=entrypoint)
    snapshot = {
        str(path.relative_to(tmp_path)): path.read_bytes() if path.is_file() else None
        for path in tmp_path.rglob("*")
    }

    def no_selection(*args, **kwargs):
        pytest.fail("Inapplicable Design reached source selection/rendering")

    monkeypatch.setattr(adaptive_preparation, "select", no_selection)
    result = prepare(tmp_path, value, client=object(), bootstrap=True, opt_out=optout)
    assert result["status"] == "podway-inapplicable"
    argv = [
        sys.executable,
        "-S",
        str(ROOT / "plugins/aquarium/shared/prepare_adaptive_procedure.py"),
        "--repository",
        str(tmp_path),
        "--assignment",
        "-",
        "--bootstrap",
        "--podway",
        str(tmp_path / "must-not-run"),
    ]
    if optout:
        argv.append("--podway-opt-out")
    public = subprocess.run(
        argv, input=json.dumps(value), capture_output=True, text=True, check=False
    )
    assert public.returncode == 0, public.stderr
    assert json.loads(public.stdout)["status"] == "podway-inapplicable"
    assert public.stderr == ""
    assert snapshot == {
        str(path.relative_to(tmp_path)): path.read_bytes() if path.is_file() else None
        for path in tmp_path.rglob("*")
    }


@pytest.mark.parametrize(
    "case",
    ["relative-git", "relative-nongit", "linked-git", "linked-nongit", "home-git"],
)
def test_repository_applicability_normalizes_actual_scope_before_any_native_or_source_work(
    tmp_path, monkeypatch, case
):
    import adaptive_preparation

    git_root, nongit = tmp_path / "git", tmp_path / "nongit"
    subprocess.run(["git", "init", "-q", str(git_root)], check=True)
    child = git_root / "nested"
    child.mkdir()
    nongit.mkdir()
    value = assignment(git_root)
    value["target"]["procedure_plan"].update(family="design", entrypoint="new-project")
    git_backed = case in {"relative-git", "linked-git", "home-git"}
    cwd = child if case == "relative-git" else git_root
    if case == "relative-git":
        scope = "."
    elif case == "relative-nongit":
        scope = "../nongit"
    elif case == "home-git":
        scope = "~/" + os.path.relpath(child, Path.home())
    else:
        link = tmp_path / "linked" if git_backed else git_root / "linked"
        link.symlink_to(child if git_backed else nongit, target_is_directory=True)
        scope = str(link)
    snapshot = {
        str(path.relative_to(tmp_path)): path.read_bytes() if path.is_file() else None
        for path in tmp_path.rglob("*")
    }
    for script in ["manage_adaptive_procedure.py", "prepare_adaptive_procedure.py"]:
        argv = [sys.executable, "-S", str(ROOT / "plugins/aquarium/shared" / script)]
        if script.startswith("manage"):
            argv += [
                "context",
                "--repository",
                scope,
                "--root",
                "definitions",
                "--entrypoint",
                "new-project",
            ]
        else:
            argv += ["--repository", scope, "--assignment", "-"]
        result = subprocess.run(
            argv,
            cwd=cwd,
            input=json.dumps(value),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == (2 if git_backed else 0), result.stderr
        assert json.loads(result.stdout)["status"] == (
            "missing-prerequisite" if git_backed else "podway-inapplicable"
        )
        assert result.stderr == ""

    class BoundaryReached(Exception):
        pass

    def selected(*args, **kwargs):
        raise BoundaryReached

    class Native:
        def health(self):
            raise BoundaryReached

    monkeypatch.setattr(adaptive_preparation, "select", selected)
    monkeypatch.chdir(cwd)
    if git_backed:
        with pytest.raises(BoundaryReached):
            prepare(scope, value)
        with pytest.raises(BoundaryReached):
            execution_context(
                scope,
                roots=[],
                entrypoint="new-project",
                qualification={"assignment": value},
                client=Native(),
            )
    else:
        assert prepare(scope, value)["status"] == "podway-inapplicable"
        assert (
            execution_context(
                scope,
                roots=[],
                entrypoint="new-project",
                qualification={"assignment": value},
                client=Native(),
            )["status"]
            == "podway-inapplicable"
        )
    assert snapshot == {
        str(path.relative_to(tmp_path)): path.read_bytes() if path.is_file() else None
        for path in tmp_path.rglob("*")
    }


@pytest.mark.parametrize(
    "entrypoint", [None, "task-handler", "war-room", "unsupported"]
)
def test_design_only_optout_rejects_invalid_or_missing_entrypoints_before_calls(
    tmp_path, monkeypatch, entrypoint
):
    import adaptive_preparation

    value = assignment(tmp_path)
    plan = value["target"]["procedure_plan"]
    if entrypoint is None:
        plan.pop("entrypoint")
    else:
        plan["entrypoint"] = entrypoint

    def no_source(*args, **kwargs):
        pytest.fail("Invalid Design opt-out reached source selection")

    class NoNative:
        def health(self):
            pytest.fail("Invalid Design opt-out reached native health")

    monkeypatch.setattr(adaptive_preparation, "select", no_source)
    with pytest.raises(BundleError) as preparation:
        prepare(tmp_path, value, client=NoNative(), opt_out=True)
    assert preparation.value.code == "invalid-arguments"
    with pytest.raises(BundleError) as execution:
        execution_context(
            tmp_path,
            roots=[],
            entrypoint=entrypoint,
            qualification=None,
            client=NoNative(),
            opt_out=True,
        )
    assert execution.value.code == "invalid-arguments"
    for script in ["manage_adaptive_procedure.py", "prepare_adaptive_procedure.py"]:
        argv = [sys.executable, "-S", str(ROOT / "plugins/aquarium/shared" / script)]
        if script.startswith("manage"):
            argv += ["context", "--repository", str(tmp_path)]
            if entrypoint is not None:
                argv += ["--entrypoint", entrypoint]
        else:
            argv += ["--repository", str(tmp_path), "--assignment", "-"]
        argv += ["--podway-opt-out"]
        result = subprocess.run(
            argv, input=json.dumps(value), capture_output=True, text=True, check=False
        )
        assert result.returncode == 2
        assert json.loads(result.stdout)["status"] == "invalid-arguments"
        assert result.stderr == ""


@pytest.mark.parametrize("applied", [False, True])
@pytest.mark.parametrize("symlink", [False, True])
def test_absent_approved_targets_validate_existing_parent_chain_without_creating_directories(
    tmp_path, applied, symlink
):
    repo, outside = tmp_path / "repo", tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    if symlink:
        (repo / "docs").symlink_to(outside, target_is_directory=True)
    target = {
        "before": sha256(b"old") if applied else None,
        "after": None if applied else sha256(b"new"),
    }
    proposed = {
        "diff": "Complete approved document change",
        "targets": {"docs/plans/new.md": target},
    }
    approval = {
        "source": "user",
        "decision": "approved",
        "proposal": copy.deepcopy(proposed),
    }
    if symlink:
        with pytest.raises(BundleError) as error:
            application(repo, proposed, approval, applied=applied)
        assert error.value.code == "unsafe"
    else:
        assert application(repo, proposed, approval, applied=applied)["status"] == (
            "verified-applied" if applied else "approved-current"
        )
        assert not (repo / "docs").exists()
    assert list(outside.iterdir()) == []


def test_tilde_plan_only_reads_actual_requirement_and_source_bytes_in_api_and_cli(
    design,
):
    repository, qualification, _, _, _ = design
    value = copy.deepcopy(qualification["assignment"])
    value["target"]["procedure_plan"]["mode"] = "plan-only"
    scope = "~/" + os.path.relpath(repository, Path.home())
    snapshot = {
        str(path.relative_to(repository)): path.read_bytes() if path.is_file() else None
        for path in repository.rglob("*")
    }
    direct = prepare(scope, value)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "plugins/aquarium/shared/prepare_adaptive_procedure.py"),
            "--repository",
            scope,
            "--assignment",
            "-",
        ],
        input=json.dumps(value),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    actual = json.loads(result.stdout)
    for observed in [direct, actual]:
        assert observed["status"] == "planned"
        assert observed["selection"]["kind"] == "reuse"
        assert set(observed["selection"]["plan"]["criteria"]) == {
            "original:delivery",
            "original:omitted",
        }
        assert observed["writes"] == []
    assert snapshot == {
        str(path.relative_to(repository)): path.read_bytes() if path.is_file() else None
        for path in repository.rglob("*")
    }


def test_tilde_prepared_api_uses_the_actual_source_scope_and_matching_client(design):
    repository, qualification, client, _, _ = design
    scope = "~/" + os.path.relpath(repository, Path.home())
    result = prepare(scope, copy.deepcopy(qualification["assignment"]), client=client)
    assert result["status"] == "prepared"
    target = result["assignment"]["target"]["prepared_definition"]
    assert Path(target["source_path"]).is_relative_to(repository)
    assert (
        Path(target["source_path"]).read_bytes()
        == (repository / "definitions/design with spaces.yaml").read_bytes()
    )
    assert target["procedure"]["id"] == "aquarium-design-v2"


@pytest.mark.parametrize("lifecycle", ["prepared", "running"])
def test_tilde_execution_resolves_the_actual_retained_bundle_beyond_health(
    design, lifecycle
):
    repository, qualification, client, observation, retained = design
    scope = "~/" + os.path.relpath(repository, Path.home())
    observation["status"]["session"]["lifecycle"] = lifecycle
    result = execution_context(
        scope,
        roots=["definitions"],
        entrypoint="new-feature",
        qualification=qualification,
        client=client,
    )
    assert result["status"] == (
        "prepared-resolved" if lifecycle == "prepared" else "dispatch-ready"
    )
    assert (
        Path(result["source_path"])
        == Path(retained["retention"]["path"]) / "procedure.yaml"
    )
    assert result["bundle_id"] == retained["retention"]["bundle_id"]
    assert (
        result["procedure"]["session"]["id"] == observation["status"]["session"]["id"]
    )


def test_preparation_cli_constructs_client_with_expanded_target_before_actual_preparation(
    design, monkeypatch, capsys
):
    import io

    import adaptive_admission
    import prepare_adaptive_procedure

    repository, qualification, client, _, _ = design
    scope = "~/" + os.path.relpath(repository, Path.home())
    constructed = []

    def factory(actual_repository, executable):
        constructed.append((actual_repository, executable))
        assert Path(actual_repository) == repository
        return client

    monkeypatch.setattr(adaptive_admission, "NativeClient", factory)
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps(qualification["assignment"]))
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prepare_adaptive_procedure.py",
            "--repository",
            scope,
            "--assignment",
            "-",
            "--podway",
            "synthetic-source-only-client",
        ],
    )
    assert prepare_adaptive_procedure.main() == 0
    actual = json.loads(capsys.readouterr().out)
    assert constructed == [(str(repository), "synthetic-source-only-client")]
    assert actual["status"] == "prepared"
    assert Path(
        actual["assignment"]["target"]["prepared_definition"]["source_path"]
    ).is_relative_to(repository)


@pytest.mark.parametrize("source", ["epic-delegation", None, "unknown"])
@pytest.mark.parametrize("applied", [False, True])
def test_design_default_application_preserves_user_only_approval(
    tmp_path, source, applied
):
    value, approval = proposal(tmp_path)
    if applied:
        (tmp_path / "README.md").write_text("Approved\n")
    if source is None:
        approval.pop("source")
    else:
        approval["source"] = source
    assert (
        application(tmp_path, value, approval, applied=applied)["status"]
        == "approval-required"
    )
