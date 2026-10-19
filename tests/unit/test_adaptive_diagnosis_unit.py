"""Diagnostic activation and honest evidence; all oracle roles/results are synthetic."""

import copy
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))
from adaptive_admission import reference_mapping
from adaptive_bundles import BundleError, sha256
from adaptive_definitions import ASSETS
from adaptive_diagnosis import conclusion, context, diagnostic_quality
from adaptive_execution import execution_context
from adaptive_preparation import prepare
from adaptive_suitability import qualify_prepared
from test_adaptive_preparation_unit import Oracle, assignment


@pytest.fixture
def diagnosis(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    value = assignment(tmp_path, mode="prepare")
    raw = (ASSETS / "podway/procedures/aquarium-war-room-v2.yaml").read_bytes()
    source = tmp_path / "definitions/diagnosis.yml"
    source.parent.mkdir()
    source.write_bytes(raw)
    mapping = reference_mapping(raw)
    plan = value["target"]["procedure_plan"]
    effects = sorted(
        {effect for row in mapping["nodes"].values() for effect in row["effects"]}
    )
    plan.update(family="diagnosis", entrypoint="war-room", effects=effects)
    value["authority"]["effects"] = effects[:]
    coverage = [
        {**row, "obligation": next(iter(mapping["obligations"]))}
        for row in plan["drafts"][0]["coverage"]
    ]
    plan["candidates"] = [
        {
            "path": "definitions/diagnosis.yml",
            "sha256": sha256(raw),
            "coverage": coverage,
            "reason": "The known diagnostic contract fits the original symptom investigation.",
        }
    ]
    client = Oracle(tmp_path)
    value = prepare(tmp_path, value, client=client)["assignment"]
    retained = qualify_prepared(tmp_path, value, client=client, retain=True)
    observation = {
        "status": {
            "procedure": retained["binding"]["procedure"],
            "session": {"id": str(uuid.uuid4()), "lifecycle": "running", "revision": 1},
            "current": None,
        },
        "guidance": {"node": {"graph_node_id": "capture-baseline"}, "readback": []},
        "active_items": [],
        "mutation_templates": [],
    }
    client.health = lambda: copy.deepcopy(observation)
    return tmp_path, {"assignment": value}, client, observation, retained


def consume(fixture):
    return execution_context(
        fixture[0],
        roots=["definitions"],
        entrypoint="war-room",
        qualification=fixture[1],
        client=fixture[2],
    )


@pytest.mark.parametrize(
    "node,role,phase",
    [
        ("capture-baseline", "executor", "baseline"),
        ("investigate", "executor", "investigation"),
        ("draft-incomplete", "executor", "proposal"),
        ("quality", "executor", "quality"),
        ("evaluator-investigation", "evaluator", None),
        ("evaluator-diagnosis", "evaluator", None),
        ("decide-cause", "coordinator", None),
    ],
)
def test_exact_known_diagnosis_current_operation(diagnosis, node, role, phase):
    diagnosis[3]["guidance"]["node"]["graph_node_id"] = node
    result = consume(diagnosis)
    assert result["role"] == role
    assert result["qualification"]["status"] == "qualified-known"
    assert result["diagnosis"]["phase"] == phase
    if role == "coordinator":
        assert result["dispatch"] is None
    else:
        assert result["dispatch"]["role"] == role
        assert (
            result["dispatch"]["authority"]["review"]
            == diagnosis[1]["assignment"]["authority"]["review"]
        )
        assert (
            result["dispatch"]["target"]["diagnosis_context"]["product_implementation"]
            is False
        )
        if role == "evaluator":
            assert result["dispatch"]["authority"]["effects"] == []


@pytest.mark.parametrize(
    "state,status",
    [
        ("prepared", "prepared-resolved"),
        ("completed", "terminal-resolved"),
        ("cancelled", "terminal-resolved"),
    ],
)
def test_prepared_and_terminal_recovery(diagnosis, state, status):
    diagnosis[3]["status"]["session"]["lifecycle"] = state
    diagnosis[3]["guidance"] = None
    result = consume(diagnosis)
    assert result["status"] == status and result["dispatch"] is None


@pytest.mark.parametrize("raw", ["FAIL", "REVISE", "PASS"])
@pytest.mark.parametrize(
    "owner,route",
    [
        ("baseline", "baseline"),
        ("investigation", "investigation"),
        ("proposal", "investigation"),
    ],
)
def test_raw_qa_is_not_operation_failure(raw, owner, route):
    evidence = {
        "operation_outcome": "pass",
        "raw_verdict": raw,
        "draft_sha256": "sha256:" + "a" * 64,
        "findings": [
            {
                "id": "Q1",
                "owner": owner,
                "disposition": "unresolved",
                "basis": "Original source evidence remains unresolved.",
            }
        ],
    }
    result = diagnostic_quality(evidence)
    assert result["operation_outcome"] == "pass" and result["raw_verdict"] == raw
    assert result["owner"] == route
    assert result["findings"] == evidence["findings"]


@pytest.mark.parametrize(
    "cause,scope,expected",
    [
        ("no-work", "no-work", True),
        ("blocked", "incomplete", False),
        ("investigate-more", "incomplete", False),
        ("established", "task", False),
        ("established", "epic", False),
    ],
)
def test_truthful_conclusions(cause, scope, expected):
    value = {
        "cause": cause,
        "scope": scope,
        "expected_behavior_established": expected,
        "causal_mechanism_established": cause == "established",
        "evidence": ["Original isolated fixture and counter-evidence."],
    }
    assert conclusion(value) == value


@pytest.mark.parametrize(
    "value,code",
    [
        ({"cause": "blocked", "scope": "no-work"}, "incompatible"),
        (
            {
                "cause": "no-work",
                "scope": "no-work",
                "expected_behavior_established": False,
            },
            "incompatible",
        ),
        ({"cause": "established", "scope": "task"}, "not-established"),
    ],
)
def test_unreproduced_or_unproved_is_not_fixed_or_no_work(value, code):
    with pytest.raises(BundleError) as error:
        conclusion({**value, "evidence": ["Symptom not reproduced."]})
    assert error.value.code == code


def test_no_change_still_requires_exact_actual_approval_and_final_evaluator(diagnosis):
    value = diagnosis[1]["assignment"]
    proposal = {
        "no_change": True,
        "diff": "",
        "targets": {},
        "reason": "Expected behavior is established and no durable document is owed.",
    }
    value["target"]["diagnosis"] = {"proposal": proposal}
    diagnosis[3]["guidance"]["node"]["graph_node_id"] = "document"
    assert consume(diagnosis)["status"] == "approval-required"
    value["authority"]["document_approval"] = {
        "source": "user",
        "decision": "approved",
        "proposal": copy.deepcopy(proposal),
    }
    result = consume(diagnosis)
    assert result["status"] == "dispatch-ready"
    value["target"]["diagnosis"]["applied"] = True
    assert consume(diagnosis)["dispatch"]["authority"]["effects"] == []
    proposal["reason"] += " Changed."
    assert consume(diagnosis)["status"] == "reapproval-required"
    diagnosis[3]["guidance"]["node"]["graph_node_id"] = "evaluator-diagnosis"
    assert consume(diagnosis)["dispatch"]["role"] == "evaluator"


def test_changed_document_target_returns_to_investigation(tmp_path):
    path = tmp_path / "spec.md"
    path.write_text("before")
    proposal = {
        "diff": "Exact displayed diff",
        "targets": {
            "spec.md": {"before": sha256(b"before"), "after": sha256(b"after")}
        },
    }
    value = {
        "target": {"diagnosis": {"proposal": proposal}},
        "authority": {
            "document_approval": {
                "source": "user",
                "decision": "approved",
                "proposal": copy.deepcopy(proposal),
            }
        },
    }
    assert (
        context(tmp_path, value, "documentation")["application"]["status"]
        == "approved-current"
    )
    path.write_text("concurrent change")
    result = context(tmp_path, value, "documentation")["application"]
    assert (
        result["status"] == "reapproval-required" and result["owner"] == "investigation"
    )


def adaptive_diagnosis():
    """One coherent baseline/hypothesis producer, assessed together without an extra phase."""
    from adaptive_definitions import canonical_json
    from test_adaptive_qualification_unit import known

    document, mapping = known("war-room")
    mapping.pop("procedure")
    document.update(id="aquarium-adapt-diagnosis-grouped", version="1")
    definitions = document["node_definitions"]
    body = definitions["investigation-record"]
    body["items"] = (
        copy.deepcopy(definitions["baseline-record"]["items"][:-1]) + body["items"]
    )
    body["intent"] = (
        "Capture the isolated symptom boundary and competing hypotheses in one coherent investigation."
    )
    definitions.pop("baseline-record")
    document["graph"]["entry"] = "investigate"
    document["graph"]["nodes"] = [
        row for row in document["graph"]["nodes"] if row["id"] != "capture-baseline"
    ]
    mapping["nodes"].pop("capture-baseline")

    def remap(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"node", "to"} and item == "capture-baseline":
                    value[key] = "investigate"
                else:
                    remap(item)
        elif isinstance(value, list):
            for item in value:
                remap(item)

    remap(document)
    for row in document["graph"]["nodes"]:
        if row["id"] == "investigate":
            row.pop("evidence_from", None)
    for obligation in mapping["obligations"].values():
        for endpoint in obligation["producers"]:
            if endpoint["node"] == "capture-baseline":
                endpoint["node"] = "investigate"
    if "manual_rework" in document:
        document["manual_rework"]["allowed_targets"] = list(
            dict.fromkeys(
                "investigate" if item == "capture-baseline" else item
                for item in document["manual_rework"]["allowed_targets"]
            )
        )
    mapping.setdefault("semantic_contracts", {})[sha256(canonical_json(body))] = {
        "roles": ["executor"],
        "effect": "work",
        "basis": "Safe original baseline and hypothesis evidence are grouped under one independent investigation assessment.",
        "delivery_items": [row["id"] for row in body["items"]],
    }
    return document, mapping


def test_grouped_diagnosis_qualifies_with_real_changed_producer_and_evidence():
    from adaptive_qualification import qualify
    from test_adaptive_qualification_unit import bound

    document, mapping = adaptive_diagnosis()
    result = qualify(document, bound(document, mapping))
    assert result["status"] == "compatible", result["issues"]
    assert document["graph"]["entry"] == "investigate"
    assert "capture-baseline" not in mapping["nodes"]
    evaluator = next(
        row
        for row in document["graph"]["nodes"]
        if row["id"] == "evaluator-investigation"
    )
    assert {row["node"] for row in evaluator["evidence_from"]} == {"investigate"}
    evaluator["evidence_from"] = []
    assert qualify(document, bound(document, mapping))["status"] == "incompatible"


def test_grouped_diagnosis_prepare_qualify_retain_current_phase_and_recovery(tmp_path):
    from test_adaptive_suitability_unit import Oracle as SuitabilityOracle
    from test_adaptive_suitability_unit import report_for

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    value = assignment(tmp_path, mode="prepare")
    document, mapping = adaptive_diagnosis()
    plan = value["target"]["procedure_plan"]
    effects = sorted(
        {effect for row in mapping["nodes"].values() for effect in row["effects"]}
    )
    plan.update(
        family="diagnosis",
        entrypoint="war-room",
        effects=effects,
        diagnosis_phases={"investigate": "investigation"},
    )
    value["authority"]["effects"] = effects[:]
    draft = plan["drafts"][0]
    draft.update(
        document=document,
        mapping=mapping,
        reason="The actual isolated incident fits a coherent baseline and hypothesis producer.",
    )
    draft["coverage"] = [
        {**row, "obligation": "evaluator-investigation"} for row in draft["coverage"]
    ]
    plan["source_dispositions"] = {"aquarium-war-room-v2.yaml": draft["reason"]}
    client = SuitabilityOracle(tmp_path)
    value = prepare(tmp_path, value, client=client, bootstrap=True)["assignment"]
    due = qualify_prepared(tmp_path, value, client=client)
    assert due["status"] == "assessment-required"
    report = report_for(due["target"])
    retained = qualify_prepared(
        tmp_path, value, client=client, assessment=report, retain=True
    )
    observation = {
        "status": {
            "procedure": retained["binding"]["procedure"],
            "session": {"id": str(uuid.uuid4()), "lifecycle": "running", "revision": 1},
            "current": None,
        },
        "guidance": {"node": {"graph_node_id": "investigate"}, "readback": []},
        "active_items": [],
        "mutation_templates": [],
    }
    client.health = lambda: copy.deepcopy(observation)
    result = execution_context(
        tmp_path,
        roots=["definitions"],
        entrypoint="war-room",
        qualification={"assignment": value, "assessment": report},
        client=client,
    )
    assert result["status"] == "dispatch-ready"
    assert result["diagnosis"]["phase"] == "investigation"
    assert result["dispatch"]["procedure"]["node"] == "investigate"


def test_approved_optional_interview_leaf_is_preserved(diagnosis):
    value = diagnosis[1]["assignment"]
    value["target"]["procedure_plan"]["phase_skills"] = {
        "capture-baseline": ["interview"],
        "quality": ["qa"],
    }
    assert consume(diagnosis)["phase_skills"] == ["interview"]
    value["target"]["procedure_plan"]["phase_skills"]["capture-baseline"] = ["auto"]
    with pytest.raises(BundleError) as error:
        consume(diagnosis)
    assert error.value.code == "invalid-input"


def conditional_diagnosis():
    """Retain baseline and add a symptom-driven discriminating experiment branch."""
    from adaptive_definitions import canonical_json
    from test_adaptive_qualification_unit import known

    document, mapping = known("war-room")
    mapping.pop("procedure")
    document.update(id="aquarium-adapt-diagnosis-hypothesis", version="1")
    definitions = document["node_definitions"]
    body = definitions["investigation-record"]
    body["items"].append(
        {
            "id": "experiment-due",
            "type": "choice",
            "prompt": "Does the competing hypothesis require another isolated discriminating experiment?",
            "required": True,
            "choices": ["bounded", "experiment"],
        }
    )
    definitions["experiment-choice"] = {
        "type": "decision",
        "title": "Select discriminating investigation",
        "objective": "Use actual hypothesis uncertainty",
        "prompt": "Is an additional isolated experiment due?",
        "reason": {
            "required": True,
            "prompt": "Cite the current evidence and approved safe boundary.",
        },
        "options": [
            {
                "id": key,
                "label": key,
                "criteria": "Existing isolated evidence resolves the competing hypotheses without another experiment."
                if key == "bounded"
                else "Competing hypotheses remain distinguishable through the approved additional isolated experiment.",
                "guards": [
                    {
                        "evidence": {"node": "investigate", "item": "experiment-due"},
                        "equals": key,
                    }
                ],
            }
            for key in ["bounded", "experiment"]
        ],
    }
    definitions["experiment-work"] = {
        "type": "action",
        "title": "Test competing hypothesis in isolated fixture",
        "intent": "Perform only the authorized isolated discriminating experiment, preserving negative evidence.",
        "items": [
            {
                "id": "experiment-evidence",
                "type": "text",
                "prompt": "Record the competing hypotheses, isolated boundary, observation and remaining uncertainty.",
                "required": True,
                "min_length": 1,
                "max_length": 5000,
                "multiline": True,
            }
        ],
    }
    for row in document["graph"]["nodes"]:
        if row["id"] == "investigate":
            row["next"] = "experiment-choice"
        if row["id"] in {"evaluator-investigation", "prepare-diagnostic-assessment"}:
            row["evidence_from"].append(
                {
                    "node": "experiment-work",
                    "required": False,
                    "items": ["experiment-evidence"],
                }
            )
    document["graph"]["nodes"] += [
        {
            "id": "experiment-choice",
            "use": "experiment-choice",
            "evidence_from": [
                {"node": "investigate", "required": True, "items": ["experiment-due"]}
            ],
            "routes": {
                "bounded": {"to": "evaluator-investigation", "effect": "advance"},
                "experiment": {"to": "experiment-work", "effect": "advance"},
            },
        },
        {
            "id": "experiment-work",
            "use": "experiment-work",
            "next": "evaluator-investigation",
        },
    ]
    mapping["nodes"]["experiment-choice"] = {
        "kind": "decision",
        "role": "coordinator",
        "effects": [],
        "capabilities": [],
    }
    mapping["nodes"]["experiment-work"] = {
        "kind": "action",
        "role": "executor",
        "effects": ["work"],
        "capabilities": [],
    }
    mapping["obligations"]["evaluator-investigation"]["producers"].append(
        {"node": "experiment-work", "item": "experiment-evidence"}
    )
    for name in ["investigation-record", "experiment-work"]:
        definition = definitions[name]
        mapping.setdefault("semantic_contracts", {})[
            sha256(canonical_json(definition))
        ] = {
            "roles": ["executor"],
            "effect": "work",
            "basis": "Isolated baseline and competing hypothesis evidence are independently assessed before cause/scope decisions.",
            "delivery_items": [item["id"] for item in definition["items"]],
        }
    return document, mapping


def test_conditional_hypothesis_changes_actual_work_evidence_and_decision():
    from adaptive_qualification import qualify
    from test_adaptive_qualification_unit import bound

    document, mapping = conditional_diagnosis()
    result = qualify(document, bound(document, mapping))
    assert result["status"] == "compatible", result["issues"]
    choice = next(
        row for row in document["graph"]["nodes"] if row["id"] == "experiment-choice"
    )
    assert {row["to"] for row in choice["routes"].values()} == {
        "experiment-work",
        "evaluator-investigation",
    }
    evaluator = next(
        row
        for row in document["graph"]["nodes"]
        if row["id"] == "evaluator-investigation"
    )
    evaluator["evidence_from"] = [
        row for row in evaluator["evidence_from"] if row["node"] != "experiment-work"
    ]
    assert qualify(document, bound(document, mapping))["status"] == "incompatible"


@pytest.mark.parametrize("cause", ["blocked", "investigate-more"])
@pytest.mark.parametrize("scope", ["task", "epic"])
def test_unresolved_cause_cannot_become_implementation_scope(cause, scope):
    with pytest.raises(BundleError) as error:
        conclusion(
            {
                "cause": cause,
                "scope": scope,
                "evidence": ["The isolated investigation remains unresolved."],
            }
        )
    assert error.value.code == "incompatible"


@pytest.mark.parametrize("outcome", ["fail", "inconclusive"])
def test_failed_or_inconclusive_qa_returns_to_quality(outcome):
    result = diagnostic_quality({"operation_outcome": outcome})
    assert result["operation_outcome"] == outcome
    assert result["owner"] == "quality"
    assert result["raw_verdict"] is None


def test_missing_qa_outcome_is_invalid_input():
    with pytest.raises(BundleError) as error:
        diagnostic_quality({})
    assert error.value.code == "invalid-input"


def test_unknown_qa_correction_owner_is_incompatible():
    with pytest.raises(BundleError) as error:
        diagnostic_quality(
            {
                "operation_outcome": "pass",
                "raw_verdict": "FAIL",
                "draft_sha256": "sha256:" + "a" * 64,
                "findings": [
                    {
                        "id": "Q1",
                        "owner": "product-repair",
                        "disposition": "unresolved",
                        "basis": "Original unresolved source issue.",
                    }
                ],
            }
        )
    assert error.value.code == "incompatible"


@pytest.mark.parametrize(
    "source,decision", [("evaluator", "approved"), ("user", "changes-requested")]
)
def test_no_change_rejects_non_user_or_non_approved_authority_without_dispatch(
    diagnosis, source, decision
):
    value = diagnosis[1]["assignment"]
    proposal = {
        "no_change": True,
        "diff": "",
        "targets": {},
        "reason": "Expected behavior is established and no durable document is owed.",
    }
    value["target"]["diagnosis"] = {"proposal": proposal}
    value["authority"]["document_approval"] = {
        "source": source,
        "decision": decision,
        "proposal": copy.deepcopy(proposal),
    }
    diagnosis[3]["guidance"]["node"]["graph_node_id"] = "document"
    result = consume(diagnosis)
    assert result["status"] == "approval-required"
    assert result["dispatch"] is None and result["next_owner"] == "Coordinator"
