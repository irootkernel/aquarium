"""Squad source and consumer behavior; synthetic reports do not attest agents."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))

import adaptive_execution as execution
from adaptive_admission import reference_mapping, selection_contract
from adaptive_bundles import BundleError, sha256
from adaptive_definitions import ASSETS, canonical_json, validate_definition
from adaptive_design import context as design_context
from adaptive_preparation import prepare
from adaptive_qualification import qualify
from adaptive_squad import assignments, commit_handoff, composition

LEGACY_MAPPINGS = {
    "goal": "sha256:f885c7f6b0da1086c582dbae3bb683f8e2089ab6d43fdf467d98149adbe4fc16",
    "task": "sha256:21caa0e4402f4b8412335adafca6e95050a276d331a4956066f244d827083e1d",
    "design": "sha256:2a4abe3bf90cbda48b5040a841b3685d04a2689c02cf976795278cf841b2d033",
    "war-room": "sha256:199e1d130352341a1de92d75c401fd5de1abdacb80844ebc8bd2650b64d8322c",
    "validation": "sha256:53f1e9f5478cb8befa5fbefa708032cdeed0dda48270934d2a9c3dc8a9c0d862",
}


@pytest.fixture
def design(tmp_path):
    from test_adaptive_design_unit import design as original

    return original.__wrapped__(tmp_path)


def reusable(family="goal"):
    path = ASSETS / "adaptive/reusable" / ("squad-" + family + ".yaml")
    return yaml.safe_load(path.read_bytes()), json.loads(
        path.with_suffix(".binding.json").read_bytes()
    )


def proof(document, binding, route="not-required"):
    context = {"review": {"route": route}, "workflow_owner": "epic-squad"}
    if binding["family"] == "goal":
        context["goal_kind"] = "member-task"
    return qualify(
        document,
        binding,
        context=context,
        verified_operation_contracts=binding["semantic_contracts"],
    )


@pytest.mark.parametrize("family", LEGACY_MAPPINGS)
def test_released_reference_mapping_bytes_remain_unchanged(family):
    source = (
        ASSETS / "podway/procedures" / ("aquarium-" + family + "-v2.yaml")
    ).read_bytes()
    assert sha256(canonical_json(reference_mapping(source))) == LEGACY_MAPPINGS[family]


@pytest.mark.parametrize("family", ["goal", "validation"])
def test_owner_specific_sources_have_qualified_current_composition(family):
    document, binding = reusable(family)
    validate_definition(binding)
    assert binding["entrypoints"] == ["epic-squad"]
    assert binding["procedure"]["source_sha256"] == sha256(
        (ASSETS / "adaptive/reusable" / ("squad-" + family + ".yaml")).read_bytes()
    )
    result = proof(document, binding)
    assert result["status"] == "compatible", result
    assert all(
        row["role"] == "coordinator"
        for key, row in binding["nodes"].items()
        if row["kind"] == "decision"
    )
    if family == "validation":
        assert "goal-kind" not in {
            item["id"] for item in document["node_definitions"]["baseline"]["items"]
        }
        assert all(
            "goal-kind" not in contract.get("discriminators", {})
            for contract in binding["semantic_contracts"].values()
        )


@pytest.mark.parametrize("node", ["decide-task-plan", "decide-epic-plan"])
def test_implementation_rejects_missing_either_plan_scope(node):
    document, binding = reusable()
    original = document["node_definitions"][node]
    original["options"][0]["guards"] = []
    current = document["graph"]["nodes"]
    for serial in [
        value for value in current if value["id"].startswith(node + "-current-")
    ]:
        document["node_definitions"][serial["use"]]["options"][0]["guards"] = []
    result = proof(document, binding)
    assert result["status"] != "compatible"


@pytest.mark.parametrize(
    "field",
    [
        "composition-unmet",
        "composition-unverified",
        "pending-local",
        "pending-low",
        "current-blockers",
        "pending-judgment",
    ],
)
def test_goal_cannot_pass_without_each_current_obligation_gate(field):
    document, binding = reusable()
    for definition in document["node_definitions"].values():
        for option in definition.get("options", []):
            option["guards"] = [
                guard
                for guard in option.get("guards", [])
                if not (
                    guard["evidence"]["node"] == "current-composition"
                    and guard["evidence"]["item"] == field
                )
            ]
    assert proof(document, binding)["status"] != "compatible"


def test_composition_cannot_be_added_to_old_handler_contract():
    document, binding = reusable()
    binding["entrypoints"] = ["epic-handler"]
    result = proof(document, binding, "herdr")
    assert result["status"] != "compatible"


@pytest.mark.parametrize(
    "entrypoint", ["epic-handler", "epic-validator", "task-handler"]
)
def test_no_additional_review_is_not_a_legacy_waiver(entrypoint):
    document, binding = reusable()
    binding["entrypoints"] = [entrypoint]
    with pytest.raises(BundleError):
        selection_contract(
            b"",
            binding,
            entrypoint,
            "not-required",
            {"assignment": {"authority": {"review": {"route": "not-required"}}}},
            document=document,
        )


@pytest.mark.parametrize(
    "script,args",
    [
        ("manage_adaptive_procedure.py", ["context", "--entrypoint", "epic-squad"]),
        ("prepare_adaptive_procedure.py", []),
    ],
)
def test_explicit_optout_needs_no_native_or_optional_python_dependencies(
    tmp_path, script, args
):
    source = tmp_path / "assignment.json"
    source.write_text(
        json.dumps({"target": {"procedure_plan": {"entrypoint": "epic-squad"}}})
    )
    marker = tmp_path / "native-called"
    native = tmp_path / "podway"
    native.write_text("#!/bin/sh\nprintf called > '" + str(marker) + "'\nexit 90\n")
    native.chmod(0o700)
    cmd = [
        sys.executable,
        "-S",
        str(ROOT / "plugins/aquarium/shared" / script),
        *args,
        "--repository",
        str(tmp_path),
        "--podway",
        str(native),
        "--podway-opt-out",
    ]
    if script.startswith("prepare"):
        cmd += ["--assignment", str(source)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout)["reason"] == "explicit-opt-out"
    assert not marker.exists()
    assert not (tmp_path / ".podway").exists()


def write_artifact(tmp_path, name, value):
    path = tmp_path / (name + ".json")
    raw = json.dumps(value, sort_keys=True).encode()
    path.write_bytes(raw)
    return {"path": str(path), "sha256": sha256(raw), "bytes": len(raw)}


def report_rows(state="met"):
    return [
        {
            "id": "original:behavior",
            "state": state,
            "parts": [
                {"id": "success", "state": state},
                {"id": "failure", "state": "met"},
            ],
        }
    ]


@pytest.fixture
def basis(tmp_path):
    source = {
        "criteria": [
            {
                "id": "behavior",
                "text": "Original behavior and failure result",
                "parts": [
                    {"id": "success", "text": "Successful result"},
                    {"id": "failure", "text": "Failure result"},
                ],
            }
        ]
    }
    original = write_artifact(tmp_path, "original", source)
    value = {
        "schema": "aquarium.assignment/v3",
        "role": "executor",
        "purpose": "Deliver original scope",
        "instructions": "Read original sources and preserve authority",
        "checkpoint": "delivery",
        "procedure": None,
        "native": {"harness": "Codex"},
        "deliverables": ["original behavior"],
        "evidence": [],
        "gaps": [],
        "success_criteria": ["original:behavior"],
        "work": {
            "repository": str(tmp_path),
            "roadmap": "roadmap.md",
            "epic": "EPIC-001",
            "task": "TASK-001",
            "requirement_sources": [
                {
                    "id": "original",
                    "path": "original.json",
                    "sha256": original["sha256"],
                    "format": "json",
                }
            ],
        },
        "target": {
            "procedure_plan": {
                "family": "goal",
                "entrypoint": "epic-squad",
                "review": {"route": "not-required"},
            },
            "squad": {
                "risk": "standard",
                "work_unit_kind": "member-task",
                "plan": "plan1",
                "candidate": "candidate1",
                "authors": ["plan-author", "writer"],
                "required_checks": ["behavior"],
            },
        },
        "authority": {
            "allowed": ["Approved bounded work"],
            "excluded": ["Publication"],
            "effects": ["work"],
            "review": {"route": "not-required"},
        },
    }
    refs = []
    for role, producer, scope in [
        ("Task Evaluator", "te", "task-result"),
        ("Task Operator", "reviewer", "task-result"),
        ("Epic Evaluator", "ee", "epic-contribution"),
    ]:
        report = {
            "schema": "aquarium.executor-handoff/v3"
            if role == "Task Operator"
            else "aquarium.evaluator-assessment/v3",
            "work": {"display_role": role},
            "native": {"public_handle": producer},
            "target": {"candidate": "candidate1"},
            "verdict": "pass",
            "criteria": report_rows(),
        }
        refs.append(
            {
                **write_artifact(tmp_path, producer, report),
                "id": producer,
                "role": role,
                "producer": producer,
                "scope": scope,
                "target": "candidate1",
                "applicability": "current",
                "basis": "Direct source and current check scope",
            }
        )
    current = {
        "phase": "task-result",
        "target": "candidate1",
        "criteria": report_rows(),
        "assessments": refs,
        "closures": [],
        "checks": [
            {
                **write_artifact(
                    tmp_path,
                    "check",
                    {
                        "target": "candidate1",
                        "outcome": "pass",
                        "command": ["existing-test", "behavior"],
                    },
                ),
                "id": "behavior",
            }
        ],
        "pending": {"local": 0, "low": 0, "blocking": 0, "judgment": 0},
    }
    return tmp_path, value, current


def test_first_reports_compose_without_a_new_evaluator_verdict(basis):
    tmp_path, assignment, current = basis
    result = composition(tmp_path, assignment, current)
    assert result["status"] == "ready"
    assert result["new_evaluator_verdict"] is None
    assert result["original_verdicts"] == {
        "te": "pass",
        "reviewer": "pass",
        "ee": "pass",
    }
    assert result["native_values"]["composition-goal-outcome"] == "achieved"


@pytest.mark.parametrize("scope", ["task-result", "integration"])
@pytest.mark.parametrize("checkpoint_state", ["met", "unmet", "unverified"])
def test_negative_first_report_and_verified_local_delta_do_not_require_new_pass(
    basis, scope, checkpoint_state
):
    tmp_path, assignment, current = basis
    if scope == "integration":
        integration_basis(tmp_path, current)
    assignment["target"]["squad"]["candidate"] = current["target"] = "candidate2"
    source = current["assessments"][0 if scope == "task-result" else 1]
    state = "unverified" if checkpoint_state == "unverified" else "unmet"
    verdict = "evidence-needed" if state == "unverified" else "rework"
    report = json.loads(Path(source["path"]).read_text())
    report.update(verdict=verdict, criteria=report_rows(state))
    report.update(current_checkpoint(scope, checkpoint_state))
    source.update(write_artifact(tmp_path, "negative-original", report))
    for ref in current["assessments"]:
        ref["applicability"] = "preserved"
        ref["applicability_evidence"] = write_artifact(
            tmp_path,
            ref["id"] + "-applicability",
            {
                "before": "candidate1",
                "after": "candidate2",
                "outcome": "pass",
                "preserved_scope": ref["scope"],
                "checks": ["finite delta readback"],
                "unknown_impact": False,
            },
        )
    current["checks"][0].update(
        write_artifact(
            tmp_path,
            "check",
            {
                "target": "candidate2",
                "outcome": "pass",
                "command": ["existing-test", "changed-behavior"],
            },
        )
    )
    verification = write_artifact(
        tmp_path,
        "local",
        {
            "before": "candidate1",
            "after": "candidate2",
            "outcome": "pass",
            "local_eligible": True,
            "unresolved_judgment": False,
            "delta": "Exact isolated correction",
            "checks": ["deterministic direct check"],
        },
    )
    current["closures"] = [
        {
            "assessment": source["id"],
            "criterion": "original:behavior",
            "part": "success",
            "before": "candidate1",
            "after": "candidate2",
            "disposition": "local-verified-fix",
            "owner": "Coordinator",
            "basis": "Existing requirement restoration with no new judgment",
            "verification": verification,
        }
    ]
    result = composition(tmp_path, assignment, current)
    assert result["status"] == "ready"
    assert result["original_verdicts"][source["id"]] == verdict
    assert result["original_criteria"][source["id"]][0]["parts"][0]["state"] == state
    assert result["new_evaluator_verdict"] is None
    assert [row["target"] for row in result["assessments"]] == ["candidate1"] * 3
    closures = current["closures"]
    current["closures"] = []
    assert composition(tmp_path, assignment, current)["status"] == "unresolved"
    current["closures"] = closures
    proof = json.loads(Path(verification["path"]).read_text())
    proof["local_eligible"] = False
    closures[0]["verification"] = write_artifact(tmp_path, "ineligible-local", proof)
    with pytest.raises(BundleError):
        composition(tmp_path, assignment, current)


@pytest.mark.parametrize(
    "fault",
    [
        "target",
        "missing-reviewer",
        "changed-report",
        "missing-part",
        "unknown-applicability",
        "author-review",
        "same-producer",
        "missing-check",
        "failed-check",
        "unreadable",
    ],
)
def test_incomplete_or_stale_current_basis_cannot_pass(basis, fault):
    tmp_path, assignment, current = basis
    if fault == "target":
        assignment["target"]["squad"]["candidate"] = "different"
    elif fault == "missing-reviewer":
        current["assessments"].pop(1)
    elif fault == "changed-report":
        Path(current["assessments"][0]["path"]).write_text("changed")
    elif fault == "missing-part":
        current["criteria"][0]["parts"].pop()
    elif fault == "unknown-applicability":
        current["assessments"][0]["applicability"] = "unknown"
    elif fault == "author-review":
        assignment["target"]["squad"]["authors"].append("reviewer")
    elif fault == "same-producer":
        ref = current["assessments"][2]
        report = json.loads(Path(ref["path"]).read_text())
        report["native"]["public_handle"] = "te"
        ref.update(write_artifact(tmp_path, "ee", report))
        ref["producer"] = "te"
    elif fault == "missing-check":
        current["checks"] = []
    elif fault == "failed-check":
        current["checks"][0].update(
            write_artifact(
                tmp_path,
                "check",
                {"target": "candidate1", "outcome": "fail", "command": ["test"]},
            )
        )
    else:
        Path(current["assessments"][0]["path"]).unlink()
    with pytest.raises(BundleError):
        composition(tmp_path, assignment, current)


@pytest.mark.parametrize("obligation", ["local", "low", "blocking", "judgment"])
def test_pending_current_obligation_is_preserved_and_blocks_achievement(
    basis, obligation
):
    tmp_path, assignment, current = basis
    current["pending"][obligation] = 1
    result = composition(tmp_path, assignment, current)
    assert result["status"] == "unresolved"
    assert result["pending"][obligation] == 1
    assert result["native_values"]["composition-goal-outcome"] == "not-achieved"


def commit_input(basis):
    tmp_path, assignment, current = basis
    grant = {
        "id": "member-1",
        "kind": "member",
        "owner": "aquarium:epic-squad",
        "epic": "EPIC-001",
        "task": "TASK-001",
        "consumed": False,
    }
    assignment["authority"]["commit_grants"] = [copy.deepcopy(grant)]
    assignment["target"]["squad"]["required_checks"] = {
        scope: [] if scope.endswith("plan") else ["behavior"]
        for scope in (
            "task-plan",
            "epic-plan",
            "task-result",
            "integration",
            "epic-closeout",
            "correction-group",
        )
    }
    acceptance = {
        "decision": "approved",
        "source": "epic-delegation",
        "authority": "Original approved envelope",
        "target": "candidate1",
        "product_review": write_artifact(
            tmp_path,
            "product-review",
            {
                "target": "candidate1",
                "actor": "Coordinator",
                "verdict": "pass",
                "basis": "Direct original product/source inspection",
            },
        ),
        "lifecycle_decision": "Task Completed",
        "record_decision": "none",
        "release_note_decision": "intentional no-note",
    }
    plans = {}
    for phase, selected in [
        ("task-plan", current["assessments"][:2]),
        ("epic-plan", current["assessments"][2:]),
    ]:
        plan = copy.deepcopy(current)
        plan.update(phase=phase, target="plan1", assessments=[])
        for ref in selected:
            report = json.loads(Path(ref["path"]).read_text())
            report["target"] = {"plan": "plan1"}
            plan["assessments"].append(
                {
                    **ref,
                    **write_artifact(tmp_path, ref["id"] + "-" + phase, report),
                    "target": "plan1",
                    "scope": phase,
                }
            )
        plan["checks"] = []
        plans[phase] = plan
    return {
        "assignment": assignment,
        "composition": current,
        "acceptance": acceptance,
        "grant": grant,
        "plan_compositions": plans,
    }


def test_exact_accepted_composition_reaches_commit_without_provider_identity(basis):
    value = commit_input(basis)
    result = commit_handoff(basis[0], value)
    assert result["workflow_owner"] == "aquarium:epic-squad"
    assert result["accepted_target"] == "candidate1"
    assert result["assessment_ordinal"] is None
    assert result["provider_operation"] == "not-required"
    assert result["effects"] == []
    assert value["grant"]["consumed"] is False


@pytest.mark.parametrize(
    "fault",
    [
        "target",
        "consumed",
        "wrong-task",
        "wrong-owner",
        "missing-grant",
        "reused-member-closeout",
        "product-review",
    ],
)
def test_commit_rejects_stale_acceptance_or_wrong_grant(basis, fault):
    value = commit_input(basis)
    if fault == "target":
        value["acceptance"]["target"] = "different"
    elif fault == "consumed":
        value["grant"]["consumed"] = True
    elif fault == "wrong-task":
        value["grant"]["task"] = "TASK-002"
    elif fault == "wrong-owner":
        value["grant"]["owner"] = "aquarium:epic-handler"
    elif fault == "missing-grant":
        value["assignment"]["authority"]["commit_grants"] = []
    elif fault == "reused-member-closeout":
        value["composition"]["phase"] = "epic-closeout"
    else:
        value["acceptance"]["product_review"] = write_artifact(
            basis[0],
            "product-review",
            {
                "target": "old",
                "actor": "Coordinator",
                "verdict": "pass",
                "basis": "old",
            },
        )
    with pytest.raises(BundleError):
        commit_handoff(basis[0], value)


@pytest.mark.parametrize("risk,count", [("standard", 3), ("elevated", 4)])
def test_native_role_groups_keep_distinct_scopes(basis, risk, count):
    assignment = basis[1]
    assignment["target"]["squad"]["risk"] = risk
    values = assignments(assignment, "assess-candidate", "evaluator")
    assert len(values) == count
    assert values[0] == ("Task Evaluator", "task-result")
    assert values[-1] == ("Epic Evaluator", "epic-contribution")
    assignment["target"]["squad"]["support_assignments"] = {
        "observe": "Read-only check result facts"
    }
    assert assignments(assignment, "observe", "executor") == [
        ("Support Operator", "Read-only check result facts")
    ]
    with pytest.raises(BundleError):
        assignments(assignment, "observe", "executor", ["work"])


def test_mapped_groups_preserve_machine_roles_and_no_implicit_writer(
    basis, monkeypatch
):
    tmp_path, assignment, _ = basis
    document, binding = reusable()
    monkeypatch.setattr(
        execution,
        "resume_selected",
        lambda *args, **kwargs: {
            "binding": binding,
            "source": yaml.safe_dump(document).encode(),
            "bundle_id": "fixture",
            "path": str(tmp_path),
            "qualification": {},
        },
    )
    observation = {
        "status": {
            "procedure": binding["procedure"],
            "session": {"id": "session", "lifecycle": "running", "revision": 1},
            "current": {"attempt": {"attempt_id": "attempt", "attempt_number": 1}},
        },
        "guidance": {"node": {"graph_node_id": "assess-candidate"}},
        "active_items": [],
        "mutation_templates": [],
    }
    result = execution.execution_context(
        tmp_path,
        roots=["definitions"],
        entrypoint="epic-squad",
        qualification={"assignment": assignment},
        client=SimpleNamespace(health=lambda: observation),
    )
    assert result["dispatch"] is None
    assert [row["role"] for row in result["dispatches"]] == [
        "evaluator",
        "executor",
        "evaluator",
    ]
    assert [row["work"]["display_role"] for row in result["dispatches"]] == [
        "Task Evaluator",
        "Task Operator",
        "Epic Evaluator",
    ]
    assert all(row["authority"]["effects"] == [] for row in result["dispatches"])
    observation["status"]["current"]["attempt"] = {
        "attempt_id": "reentry",
        "attempt_number": 2,
    }
    with pytest.raises(BundleError):
        execution.execution_context(
            tmp_path,
            roots=["definitions"],
            entrypoint="epic-squad",
            qualification={"assignment": assignment},
            client=SimpleNamespace(health=lambda: observation),
        )
    assignment["target"]["squad"]["reentry"] = {
        "attempt_id": "reentry",
        "basis": "Originals remain applicable after native invalidation; fresh re-recording only",
        "assessments": [],
        "original_evidence": ["original actual reports"],
    }
    restored = execution.execution_context(
        tmp_path,
        roots=["definitions"],
        entrypoint="epic-squad",
        qualification={"assignment": assignment},
        client=SimpleNamespace(health=lambda: observation),
    )
    assert restored["dispatches"] == []
    assert restored["status"] == "coordinator-owned"


@pytest.mark.parametrize(
    "profiles", [{}, {"Task Evaluator": {"cli": "codex", "model": "opaque/model/name"}}]
)
def test_design_caller_returns_exact_owner_profiles_and_original_identity(
    basis, profiles
):
    assignment = basis[1]
    assignment["target"]["procedure_plan"]["entrypoint"] = "new-feature"
    caller = {
        **{key: assignment["work"][key] for key in ("repository", "roadmap", "epic")},
        "workflow_owner": "aquarium:epic-squad",
        "mode": "execute",
        "profiles": profiles,
    }
    assignment["target"]["design"] = {"caller": caller, "commit_required": True}
    result = design_context(basis[0], assignment, "draft")["collaboration_return"]
    assert result["profiles"] == profiles
    assert result["caller"] == caller
    assert result["request"].startswith("$aquarium:epic-squad ")
    assert ("profiles=" in result["request"]) is bool(profiles)
    assert result["automatic_delivery"] is False
    assert result["status"] == "design-delivery-pending"
    assignment["target"]["design"]["caller"]["epic"] = "EPIC-002"
    with pytest.raises(BundleError):
        design_context(basis[0], assignment, "draft")


@pytest.mark.parametrize("family", ["goal", "validation"])
def test_packaged_template_adapts_and_qualifies_without_managed_squad_copy(
    basis, family
):
    from adaptive_suitability import qualify_prepared
    from test_adaptive_suitability_unit import Oracle, prove_operations, report_for

    tmp_path, assignment, _ = basis
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("definitions/\n")
    template = tmp_path / "definitions/template.yaml"
    template.parent.mkdir()
    document, binding = reusable(family)
    template.write_text(yaml.safe_dump(document))
    mapping = {key: value for key, value in binding.items() if key != "procedure"}
    coverage = [
        {
            "criterion": "original:behavior",
            "part": part,
            "obligation": "deliver-work",
            "reason": "Original behavior and failure criteria retain actual assessment/composition coverage",
        }
        for part in ["success", "failure"]
    ]
    plan = assignment["target"]["procedure_plan"]
    plan.update(
        family=family,
        mode="prepare",
        effects=["work"],
        discovery_roots=["definitions"],
        candidates=[],
        source_dispositions={
            "aquarium-"
            + family
            + "-v2.yaml": "Handler-owned reference lacks the distinct Squad planning and composition contract"
        },
        drafts=[
            {
                "kind": "adapt",
                "base": {
                    "path": "definitions/template.yaml",
                    "sha256": sha256(template.read_bytes()),
                },
                "document": document,
                "mapping": mapping,
                "coverage": coverage,
                "reason": "Reuse the packaged Squad topology with exact work-specific qualification",
            }
        ],
    )
    assignment["authority"]["preparation"] = {
        "native_authoring": True,
        "roots": ["definitions"],
        "write_root": "definitions",
    }
    result = prepare(tmp_path, assignment, client=Oracle(tmp_path), bootstrap=True)
    request = qualify_prepared(tmp_path, result["assignment"], client=Oracle(tmp_path))
    assert request["status"] == "assessment-required"
    report = prove_operations(report_for(request["target"]), result["binding"])
    admitted = qualify_prepared(
        tmp_path,
        result["assignment"],
        client=Oracle(tmp_path),
        assessment=report,
        retain=True,
    )
    assert admitted["status"] == "qualified"
    assert admitted["binding"]["entrypoints"] == ["epic-squad"]
    assert not (tmp_path / ".podway/procedures").exists()


def test_missing_original_report_parts_cannot_be_filled_by_current_summary(basis):
    tmp_path, assignment, current = basis
    ref = current["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    report["criteria"][0]["parts"].pop()
    ref.update(write_artifact(tmp_path, "te", report))
    with pytest.raises(BundleError):
        composition(tmp_path, assignment, current)


def test_scoped_task_pass_keeps_global_future_gaps_without_claiming_epic_pass(basis):
    tmp_path, assignment, current = basis
    ref = current["assessments"][-1]
    report = json.loads(Path(ref["path"]).read_text())
    report.update(verdict="rework", checkpoint_result="pass")
    report["criteria"].append({"id": "epic:future", "state": "unverified"})
    ref.update(write_artifact(tmp_path, "ee", report))
    ref["future_criteria"] = ["epic:future"]
    result = composition(tmp_path, assignment, current)
    assert result["status"] == "ready"
    assert result["original_verdicts"]["ee"] == "rework"
    assert result["new_evaluator_verdict"] is None


def test_affected_delta_reports_close_only_the_original_scoped_obligation(basis):
    tmp_path, assignment, current = basis
    assignment["target"]["squad"].update(
        candidate="candidate2", epic_scope_changed=True
    )
    correction = {
        "id": "bounded-1",
        "phase": "task-result",
        "depth": "bounded",
        "epic_scope_changed": True,
        "basis": "Actual affected contract scope",
    }
    assignment["target"]["squad"]["correction"] = correction
    current["target"] = "candidate2"
    original = current["assessments"][0]
    report = json.loads(Path(original["path"]).read_text())
    report.update(verdict="rework", criteria=report_rows("unmet"))
    original.update(write_artifact(tmp_path, "te", report))
    for ref in current["assessments"]:
        ref["applicability"] = "preserved"
        ref["applicability_evidence"] = write_artifact(
            tmp_path,
            ref["id"] + "-applicability",
            {
                "before": "candidate1",
                "after": "candidate2",
                "outcome": "pass",
                "preserved_scope": ref["scope"],
                "checks": ["Reviewed exact affected obligations"],
                "unknown_impact": False,
            },
        )
    focused = []
    correction["original_assessments"] = [copy.deepcopy(original)]
    for role, producer, scope in [
        ("Task Evaluator", "te", "affected-result"),
        ("Task Operator", "reviewer", "affected-result"),
        ("Epic Evaluator", "ee", "affected-epic"),
    ]:
        result = {
            "schema": "aquarium.executor-handoff/v3"
            if role == "Task Operator"
            else "aquarium.evaluator-assessment/v3",
            "work": {"display_role": role},
            "native": {"public_handle": producer},
            "target": {"candidate": "candidate2"},
            "verdict": "pass",
            "criteria": report_rows(),
        }
        identity = producer + "-delta"
        focused.append(identity)
        current["assessments"].append(
            {
                **write_artifact(tmp_path, identity, result),
                "id": identity,
                "role": role,
                "producer": producer,
                "scope": scope,
                "target": "candidate2",
                "applicability": "current",
                "basis": "Exact affected delta assessment, no whole-candidate reassessment",
            }
        )
    current["checks"][0].update(
        write_artifact(
            tmp_path,
            "check",
            {
                "target": "candidate2",
                "outcome": "pass",
                "command": ["test", "changed-contract"],
            },
        )
    )
    verification = write_artifact(
        tmp_path,
        "affected",
        {
            "before": "candidate1",
            "after": "candidate2",
            "outcome": "pass",
            "local_eligible": False,
            "unresolved_judgment": False,
            "delta": "Bounded contract correction",
            "checks": ["Changed consumer and failure behavior"],
            "assessments": focused,
            "correction": correction,
        },
    )
    current["closures"] = [
        {
            "assessment": "te",
            "criterion": "original:behavior",
            "part": "success",
            "before": "candidate1",
            "after": "candidate2",
            "disposition": "affected-assessment",
            "owner": "Task Evaluator",
            "basis": "Actual independent affected panel and EE judgment",
            "verification": verification,
        }
    ]
    assert composition(tmp_path, assignment, current)["status"] == "ready"
    for scope in ("affected-result", "affected-epic"):
        scoped_phase_reports(tmp_path, current, scope)
    result = composition(tmp_path, assignment, current)
    assert result["status"] == "ready"
    assert result["original_verdicts"]["te"] == "rework"
    assert result["original_verdicts"]["te-delta"] == "evidence-needed"
    current["assessments"].pop()
    with pytest.raises(BundleError):
        composition(tmp_path, assignment, current)


def test_grant_kind_cannot_substitute_member_for_correction(basis):
    value = commit_input(basis)
    value["assignment"]["target"]["squad"]["work_unit_kind"] = (
        "pre-validation-remediation"
    )
    with pytest.raises(BundleError):
        commit_handoff(basis[0], value)
    value["grant"]["kind"] = "correction"
    value["assignment"]["authority"]["commit_grants"] = [copy.deepcopy(value["grant"])]
    assert commit_handoff(basis[0], value)["grant"]["kind"] == "correction"


def test_no_additional_review_rejects_fabricated_provider_ordinal(basis):
    value = commit_input(basis)
    value["assessment_ordinal"] = 1
    with pytest.raises(BundleError):
        commit_handoff(basis[0], value)


def test_selected_technical_route_cannot_use_only_internal_reports(basis):
    value = commit_input(basis)
    value["assignment"]["authority"]["review"]["route"] = "herdr"
    with pytest.raises(BundleError):
        commit_handoff(basis[0], value)


def test_requirement_source_change_invalidates_opted_out_composition(basis):
    path = basis[0] / "original.json"
    source = json.loads(path.read_text())
    source["criteria"][0]["text"] = "Changed required behavior"
    path.write_text(json.dumps(source))
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("scope", ["task-plan", "epic-plan"])
def test_commit_cannot_omit_a_plan_scope_when_native_is_opted_out(basis, scope):
    value = commit_input(basis)
    value["plan_compositions"].pop(scope)
    with pytest.raises(BundleError):
        commit_handoff(basis[0], value)


def test_conditional_closeout_grant_requires_actual_user_acceptance(basis):
    tmp_path, assignment, current = basis
    value = commit_input(basis)
    assignment["target"]["squad"]["work_unit_kind"] = "epic-closeout"
    current["phase"] = "epic-closeout"
    ee = current["assessments"][-1]
    ee["scope"] = "integration"
    first = current["assessments"][1]
    first["scope"] = "integration"
    report = json.loads(Path(first["path"]).read_text())
    report["native"]["public_handle"] = "fresh-reviewer"
    current["assessments"].append(
        {
            **first,
            **write_artifact(tmp_path, "fresh-reviewer", report),
            "id": "fresh-reviewer",
            "producer": "fresh-reviewer",
        }
    )
    value["grant"].update(kind="conditional-closeout", id="closeout-1")
    assignment["authority"]["commit_grants"] = [copy.deepcopy(value["grant"])]
    with pytest.raises(BundleError):
        commit_handoff(tmp_path, value)
    value["acceptance"]["source"] = "user"
    result = commit_handoff(tmp_path, value)
    assert result["acceptance"]["source"] == "user"
    assert result["grant"]["kind"] == "conditional-closeout"


def test_pure_commit_consumer_executes_no_native_or_commit_effect(basis):
    value = commit_input(basis)
    path = basis[0] / "handoff.json"
    path.write_text(json.dumps(value))
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "plugins/aquarium/shared/adaptive_squad.py"),
            "--repository",
            str(basis[0]),
            "--handoff",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    verified = json.loads(result.stdout)
    assert verified["status"] == "verified"
    assert verified["accepted_target"] == "candidate1"
    assert verified["effects"] == []
    assert not (basis[0] / ".git").exists()
    assert not (basis[0] / ".podway").exists()


def integration_basis(tmp_path, current):
    current["phase"] = "integration"
    current["assessments"] = current["assessments"][1:]
    for ref in current["assessments"]:
        ref["scope"] = "integration"
    first = current["assessments"][0]
    report = json.loads(Path(first["path"]).read_text())
    report["native"]["public_handle"] = "fresh-reviewer"
    current["assessments"].append(
        {
            **first,
            **write_artifact(tmp_path, "fresh-reviewer", report),
            "id": "fresh-reviewer",
            "producer": "fresh-reviewer",
        }
    )


@pytest.mark.parametrize(
    "work_kind,grant_kind",
    [
        ("member-task", "member"),
        ("pre-validation-remediation", "correction"),
        ("validation-remediation", "correction"),
    ],
)
def test_integration_cannot_replace_the_work_units_due_commit_scope(
    basis, work_kind, grant_kind
):
    value = commit_input(basis)
    value["assignment"]["target"]["squad"]["work_unit_kind"] = work_kind
    value["grant"]["kind"] = grant_kind
    value["assignment"]["authority"]["commit_grants"] = [copy.deepcopy(value["grant"])]
    integration_basis(basis[0], value["composition"])
    assert (
        composition(basis[0], value["assignment"], value["composition"])["status"]
        == "ready"
    )
    with pytest.raises(BundleError):
        commit_handoff(basis[0], value)


def correction_group_input(basis):
    tmp_path, assignment, current = basis
    value = commit_input(basis)
    assignment["target"]["squad"]["work_unit_kind"] = "validation-remediation"
    value["grant"]["kind"] = "correction"
    assignment["authority"]["commit_grants"] = [copy.deepcopy(value["grant"])]
    current["phase"] = "correction-group"
    current["assessments"] = current["assessments"][-1:]
    ref = current["assessments"][0]
    ref["scope"] = "integration"
    report = json.loads(Path(ref["path"]).read_text())
    report.update(verdict="rework", criteria=report_rows("unmet"))
    ref.update(write_artifact(tmp_path, "ee-original-integration", report))
    current["closures"] = [
        {
            "assessment": "ee",
            "criterion": "original:behavior",
            "part": "success",
            "before": "candidate1",
            "after": "candidate1",
            "disposition": "local-verified-fix",
            "owner": "Coordinator",
            "basis": "Original integration finding, exact scoped local restoration",
            "verification": write_artifact(
                tmp_path,
                "group-check",
                {
                    "before": "candidate1",
                    "after": "candidate1",
                    "outcome": "pass",
                    "local_eligible": True,
                    "unresolved_judgment": False,
                    "delta": "Exact original finding repaired",
                    "checks": ["affected deterministic regression"],
                },
            ),
        }
    ]
    return value


def test_scoped_validation_group_can_commit_before_final_epic_confirmation(basis):
    value = correction_group_input(basis)
    result = commit_handoff(basis[0], value)
    current = result["current_composition"]
    assert current["status"] == "ready"
    assert current["original_verdicts"] == {"ee": "rework"}
    assert current["native_values"]["composition-goal-outcome"] == "not-achieved"
    assert current["whole_epic_confirmation"] == "pending"
    value["composition"]["phase"] = "integration"
    with pytest.raises(BundleError):
        composition(basis[0], value["assignment"], value["composition"])


@pytest.mark.parametrize("due", [False, True])
def test_validation_group_preserves_selected_whole_epic_route_before_first_review(
    basis, due
):
    value = correction_group_input(basis)
    value["assignment"]["authority"]["review"]["route"] = "herdr"
    value["review_boundary"] = write_artifact(
        basis[0],
        "group-review-boundary",
        {
            "target": "candidate1",
            "phase": "correction-group",
            "route": "herdr",
            "due": due,
            "authority": "Original approved useful review boundaries",
            "basis": "Direct-audit correction precedes first selected whole-Epic provider review",
            "whole_epic_confirmation": "pending",
        },
    )
    if due:
        with pytest.raises(BundleError):
            commit_handoff(basis[0], value)
    else:
        result = commit_handoff(basis[0], value)
        assert result["review_route"] == "herdr"
        assert result["provider_operation"] == "not-due"
        assert result["assessment_ordinal"] is None
        assert result["source_review"] is None
        assert result["current_composition"]["whole_epic_confirmation"] == "pending"
        value.pop("review_boundary")
        with pytest.raises(BundleError):
            commit_handoff(basis[0], value)


@pytest.mark.parametrize(
    "fault", [None, "target", "phase", "unknown-due", "missing-evidence"]
)
def test_group_review_boundary_keeps_actual_source_review_history(basis, fault):
    value = correction_group_input(basis)
    value["assignment"]["authority"]["review"]["route"] = "herdr"
    boundary = {
        "target": "candidate1",
        "phase": "correction-group",
        "route": "herdr",
        "due": False,
        "authority": "Approved correction review boundary",
        "basis": "This group repairs the retained prior provider finding; final review remains due",
        "whole_epic_confirmation": "pending",
    }
    source = write_artifact(
        basis[0], "prior-provider", {"target": "prior", "verdict": "REQUEST_CHANGES"}
    )
    value["source_review"] = {
        "route": "herdr",
        "operation": "complete",
        "ordinal": 1,
        "target": "prior",
        "original_verdict": "REQUEST_CHANGES",
        "authority": "Original selected review grant",
        "evidence": source,
    }
    if fault == "target":
        boundary["target"] = "stale"
    elif fault == "phase":
        boundary["phase"] = "integration"
    elif fault == "unknown-due":
        boundary["due"] = None
    elif fault == "missing-evidence":
        Path(source["path"]).unlink()
    value["review_boundary"] = write_artifact(basis[0], "boundary", boundary)
    if fault:
        with pytest.raises(BundleError):
            commit_handoff(basis[0], value)
    else:
        result = commit_handoff(basis[0], value)
        assert result["source_review"] == value["source_review"]
        assert result["provider_operation"] == "not-due"
        assert result["assessment_ordinal"] is None


@pytest.mark.parametrize(
    "fault", ["fresh-pass", "nonlocal", "missing-closure", "task-result"]
)
def test_group_commit_cannot_replace_original_or_affected_obligations(basis, fault):
    value = correction_group_input(basis)
    current = value["composition"]
    if fault == "fresh-pass":
        ref = current["assessments"][0]
        report = json.loads(Path(ref["path"]).read_text())
        report.update(verdict="pass", criteria=report_rows())
        ref.update(write_artifact(basis[0], "generic-ee-pass", report))
        current["closures"] = []
    elif fault == "nonlocal":
        current["closures"][0]["disposition"] = "affected-assessment"
        value["assignment"]["target"]["squad"]["epic_scope_changed"] = True
    elif fault == "missing-closure":
        current["closures"] = []
    else:
        current["phase"] = "task-result"
        current["assessments"] = basis[2]["assessments"]
    with pytest.raises(BundleError):
        commit_handoff(basis[0], value)


def scoped_phase_reports(tmp_path, current, scope):
    for ref in current["assessments"]:
        if ref["scope"] != scope:
            continue
        report = json.loads(Path(ref["path"]).read_text())
        future = report_rows("unverified")
        future[0]["parts"][1]["state"] = "unverified"
        for part in future[0]["parts"]:
            part["applicability"] = (
                "Future global implementation; current plan/contribution assessed separately"
            )
        report.update(
            verdict="evidence-needed",
            criteria=future,
            checkpoint_result="pass",
            checkpoint_assessment={
                "phase": scope,
                "state": "met",
                "due_unmet": 0,
                "due_unverified": 0,
                "basis": "Original parts assessed for this plan/contribution; global implementation remains future",
                "criteria": report_rows(),
            },
        )
        ref.update(write_artifact(tmp_path, ref["id"] + "-scoped", report))


def current_checkpoint(scope, state="met"):
    return {
        "checkpoint_result": {
            "met": "pass",
            "unmet": "fail",
            "unverified": "inconclusive",
        }[state],
        "checkpoint_assessment": {
            "phase": scope,
            "state": state,
            "due_unmet": int(state == "unmet"),
            "due_unverified": int(state == "unverified"),
            "basis": "Matching complete current-scope metadata retained in the original report",
            "criteria": report_rows(state),
        },
    }


@pytest.mark.parametrize("scope", ["task-result", "integration"])
@pytest.mark.parametrize(
    "fault", ["count", "part-state", "summary", "result", "unknown"]
)
def test_original_negative_checkpoint_cannot_add_unrepresented_or_unknown_gaps(
    basis, scope, fault
):
    tmp_path, assignment, current = basis
    if scope == "integration":
        integration_basis(tmp_path, current)
    ref = next(ref for ref in current["assessments"] if ref["scope"] == scope)
    report = json.loads(Path(ref["path"]).read_text())
    report.update(
        verdict="rework",
        criteria=report_rows("unmet"),
        **current_checkpoint(scope, "unmet"),
    )
    checkpoint = report["checkpoint_assessment"]
    if fault == "count":
        checkpoint["due_unmet"] = 2
    elif fault == "part-state":
        checkpoint["criteria"][0]["parts"][0]["state"] = "unverified"
    elif fault == "summary":
        checkpoint["state"] = "unverified"
    elif fault == "result":
        report["checkpoint_result"] = "inconclusive"
    else:
        checkpoint["state"] = "unknown"
    ref.update(write_artifact(tmp_path, "unrepresented-checkpoint", report))
    with pytest.raises(BundleError):
        composition(tmp_path, assignment, current)


@pytest.mark.parametrize("scope", ["task-result", "integration"])
def test_current_global_pass_can_retain_complete_matching_checkpoint_metadata(
    basis, scope
):
    value = commit_input(basis)
    current = value["composition"]
    if scope == "integration":
        integration_basis(basis[0], current)
    for ref in current["assessments"]:
        if ref["scope"] != scope:
            continue
        report = json.loads(Path(ref["path"]).read_text())
        report.update(current_checkpoint(scope))
        ref.update(write_artifact(basis[0], ref["id"] + "-current-checkpoint", report))
    result = composition(basis[0], value["assignment"], current)
    assert result["status"] == "ready"
    assert all(verdict == "pass" for verdict in result["original_verdicts"].values())
    if scope == "task-result":
        assert commit_handoff(basis[0], value)["accepted_target"] == "candidate1"


@pytest.mark.parametrize("scope", ["task-result", "integration"])
@pytest.mark.parametrize(
    "fault", ["failed", "unknown", "negative-part", "missing-part", "wrong-scope"]
)
def test_current_checkpoint_metadata_cannot_contradict_global_pass(basis, scope, fault):
    tmp_path, assignment, current = basis
    if scope == "integration":
        integration_basis(tmp_path, current)
    ref = next(ref for ref in current["assessments"] if ref["scope"] == scope)
    report = json.loads(Path(ref["path"]).read_text())
    report.update(current_checkpoint(scope))
    checkpoint = report["checkpoint_assessment"]
    if fault == "failed":
        report["checkpoint_result"] = "fail"
    elif fault == "unknown":
        checkpoint["state"] = "unknown"
    elif fault == "negative-part":
        checkpoint["criteria"][0]["parts"][0]["state"] = "unmet"
    elif fault == "missing-part":
        checkpoint["criteria"][0]["parts"].pop()
    else:
        checkpoint["phase"] = "task-plan"
    ref.update(write_artifact(tmp_path, ref["id"] + "-contradictory", report))
    with pytest.raises(BundleError):
        composition(tmp_path, assignment, current)


@pytest.mark.parametrize("scope", ["task-plan", "epic-plan", "epic-contribution"])
def test_actual_phase_parts_preserve_same_criterion_global_future_states(basis, scope):
    value = commit_input(basis)
    current = (
        value["composition"]
        if scope == "epic-contribution"
        else value["plan_compositions"][scope]
    )
    scoped_phase_reports(basis[0], current, scope)
    result = composition(basis[0], value["assignment"], current)
    assert result["status"] == "ready"
    for ref in current["assessments"]:
        if ref["scope"] == scope:
            assert result["original_verdicts"][ref["id"]] == "evidence-needed"
            assert all(
                part["state"] == "unverified"
                for part in result["original_criteria"][ref["id"]][0]["parts"]
            )
    assert result["new_evaluator_verdict"] is None
    assert commit_handoff(basis[0], value)["accepted_target"] == "candidate1"


@pytest.mark.parametrize("scope", ["task-result", "integration"])
def test_current_result_defect_cannot_disappear_in_a_met_phase_summary(basis, scope):
    tmp_path, assignment, current = basis
    if scope == "integration":
        integration_basis(tmp_path, current)
    ref = current["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    report.update(
        verdict="rework",
        criteria=report_rows("unmet"),
        **current_checkpoint(scope),
    )
    ref.update(write_artifact(tmp_path, "unresolved-current-result", report))
    result = composition(tmp_path, assignment, current)
    assert result["status"] == "unresolved"
    assert result["original_verdicts"][ref["id"]] == "rework"
    assert result["original_criteria"][ref["id"]][0]["parts"][0]["state"] == "unmet"
    report.pop("checkpoint_assessment")
    ref.update(write_artifact(tmp_path, "unresolved-current-result", report))
    assert composition(tmp_path, assignment, current)["status"] == "unresolved"


def test_plan_scope_can_retain_explicitly_future_global_unmet_parts(basis):
    value = commit_input(basis)
    current = value["plan_compositions"]["task-plan"]
    scoped_phase_reports(basis[0], current, "task-plan")
    ref = current["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    report["verdict"] = "rework"
    report["criteria"][0]["state"] = "unmet"
    report["criteria"][0]["parts"][0]["state"] = "unmet"
    part = report["criteria"][0]["parts"][0]
    part["reason"] = part.pop("applicability")
    ref.update(write_artifact(basis[0], "future-global-unmet", report))
    result = composition(basis[0], value["assignment"], current)
    assert result["status"] == "ready"
    assert result["original_criteria"][ref["id"]][0]["parts"][0]["state"] == "unmet"


@pytest.mark.parametrize(
    "fault",
    [
        "missing-part",
        "negative",
        "unverified",
        "unknown",
        "summary-only",
        "wrong-phase",
        "failed-checkpoint",
        "negative-summary",
        "unknown-summary",
        "missing-global-part",
        "missing-applicability",
    ],
)
def test_phase_summary_cannot_fill_missing_or_negative_due_part_proof(basis, fault):
    value = commit_input(basis)
    current = value["plan_compositions"]["task-plan"]
    scoped_phase_reports(basis[0], current, "task-plan")
    ref = current["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    phase = report["checkpoint_assessment"]
    if fault == "missing-part":
        phase["criteria"][0]["parts"].pop()
    elif fault in {"negative", "unverified", "unknown"}:
        phase["criteria"][0]["parts"][0]["state"] = {
            "negative": "unmet",
            "unverified": "unverified",
            "unknown": "unknown",
        }[fault]
    elif fault == "summary-only":
        phase.pop("criteria")
    elif fault == "wrong-phase":
        phase["phase"] = "task-result"
    elif fault == "failed-checkpoint":
        report["checkpoint_result"] = "fail"
    elif fault == "unknown-summary":
        phase["state"] = "unknown"
    elif fault == "missing-global-part":
        report["criteria"][0]["parts"].pop()
    elif fault == "missing-applicability":
        report["criteria"][0]["parts"][0].pop("applicability")
    else:
        phase["due_unverified"] = 1
    ref.update(write_artifact(basis[0], "bad-phase", report))
    try:
        result = composition(basis[0], value["assignment"], current)
    except BundleError:
        return
    assert result["status"] != "ready"


@pytest.mark.parametrize(
    "fault", [None, "bare", "blank", "missing-part", "negative-source"]
)
def test_conditional_not_applicable_retains_reason_and_original_coverage(basis, fault):
    tmp_path, assignment, current = basis
    source = json.loads((tmp_path / "original.json").read_text())
    source["criteria"][0]["parts"][1]["text"] = (
        "For external transport scopes, verify failure; local-only scopes do not apply"
    )
    original = write_artifact(tmp_path, "original", source)
    assignment["work"]["requirement_sources"][0]["sha256"] = original["sha256"]
    rows = report_rows()
    rows[0]["parts"][1].update(
        state="not-applicable",
        basis="Original transport-failure branch does not apply to this local-only target",
    )
    if fault == "bare":
        rows[0]["parts"][1].pop("basis")
    elif fault == "blank":
        rows[0]["parts"][1]["basis"] = "  "
    elif fault == "missing-part":
        rows[0]["parts"].pop()
    current["criteria"] = copy.deepcopy(rows)
    for ref in current["assessments"]:
        report = json.loads(Path(ref["path"]).read_text())
        report["criteria"] = copy.deepcopy(rows)
        if fault == "negative-source" and ref["id"] == "te":
            report["criteria"][0]["parts"][1]["state"] = "unmet"
        ref.update(write_artifact(tmp_path, ref["id"] + "-na", report))
    if fault in {"bare", "blank", "missing-part"}:
        with pytest.raises(BundleError):
            composition(tmp_path, assignment, current)
    else:
        result = composition(tmp_path, assignment, current)
        assert result["status"] == ("unresolved" if fault else "ready")
        assert result["current_criteria"][0]["parts"][1]["state"] == "not-applicable"
        assert result["native_values"]["composition-unverified"] == 0


def test_custom_evaluator_scope_mapping_is_checked_before_work(basis):
    from adaptive_execution import validate_phase_mappings

    document, binding = reusable()
    binding["nodes"]["custom-panel"] = binding["nodes"].pop("assess-candidate")
    assignment = basis[1]
    with pytest.raises(BundleError):
        validate_phase_mappings(document, binding, assignment)
    assignment["target"]["procedure_plan"]["squad_phases"] = {
        "custom-panel": "task-result"
    }
    validate_phase_mappings(document, binding, assignment)
    assert assignments(assignment, "custom-panel", "evaluator")[0] == (
        "Task Evaluator",
        "task-result",
    )
    assignment["target"]["procedure_plan"]["squad_phases"] = {"absent": "task-result"}
    with pytest.raises(BundleError):
        validate_phase_mappings(document, binding, assignment)


@pytest.mark.parametrize("fault", [None, "nonlocal", "wrong-target", "missing-check"])
def test_selected_provider_target_survives_only_exact_eligible_local_bridge(
    basis, fault
):
    tmp_path = basis[0]
    value = commit_input(basis)
    value["assignment"]["authority"]["review"]["route"] = "herdr"
    value.update(
        assessment_ordinal=1, assessment_kind="work-unit", provider_operation="complete"
    )
    source = write_artifact(
        tmp_path,
        "provider-original",
        {"target": "reviewed-before", "verdict": "REQUEST_CHANGES", "findings": ["F1"]},
    )
    verification = write_artifact(
        tmp_path,
        "provider-delta-check",
        {
            "before": "reviewed-before",
            "after": "candidate1",
            "outcome": "pass",
            "checks": ["Exact permitted delta/current direct verification"],
        },
    )
    completion = {key: 0 for key in ["unmet", "unverified", "blocking", "local", "low"]}
    bridge = {
        "before_target": "reviewed-before",
        "after_target": "candidate1",
        "coverage_relationship": "review-predates-local-correction",
        "source_review": source,
        "source_verdict": "REQUEST_CHANGES",
        "all_blocking_obligations_local": True,
        "completion": completion,
        "permitted_delta": {"paths": ["owned-source"]},
        "verification": verification,
    }
    if fault == "nonlocal":
        bridge["all_blocking_obligations_local"] = False
    elif fault == "wrong-target":
        bridge["after_target"] = "other-candidate"
    elif fault == "missing-check":
        bridge["verification"] = write_artifact(
            tmp_path,
            "provider-delta-check",
            {
                "before": "reviewed-before",
                "after": "candidate1",
                "outcome": "pass",
                "checks": [],
            },
        )
    value["technical_review"] = {
        "route": "herdr",
        "target": "reviewed-before",
        "original_verdict": "REQUEST_CHANGES",
        "authority": "Original provider grant",
        "evidence": source,
        "completion": completion,
        "local_settlement": write_artifact(tmp_path, "provider-settlement", bridge),
    }
    if fault:
        with pytest.raises(BundleError):
            commit_handoff(tmp_path, value)
    else:
        result = commit_handoff(tmp_path, value)
        assert result["technical_review"]["target"] == "reviewed-before"
        assert result["technical_review"]["original_verdict"] == "REQUEST_CHANGES"
        assert result["assessment_ordinal"] == 1
        assert result["accepted_target"] == "candidate1"


def test_selected_review_native_path_keeps_original_negative_and_current_readiness_separate():
    from test_adaptive_qualification_unit import with_review

    document, binding = reusable()
    document, binding, context = with_review(
        document, binding, {"operation_contracts": {}}
    )
    next(
        node for node in document["graph"]["nodes"] if node["id"] == "assess-candidate"
    )["next"] = "collect-review"
    next(node for node in document["graph"]["nodes"] if node["id"] == "check-review")[
        "routes"
    ]["complete"]["to"] = "classify-corrections"
    collector = document["node_definitions"]["collect-review"]
    # These historical native fields can never claim source approval or zero unmet.
    collector["items"] += [
        {
            "id": "original-provider-verdict",
            "type": "choice",
            "required": True,
            "prompt": "Preserve the actual original verdict",
            "choices": ["REQUEST_CHANGES"],
        },
        {
            "id": "original-provider-unmet",
            "type": "integer",
            "required": True,
            "prompt": "Preserve the original unmet count",
            "minimum": 1,
            "maximum": 1,
        },
    ]
    binding["semantic_contracts"].update(context["operation_contracts"])
    binding["semantic_contracts"][sha256(canonical_json(collector))] = {
        "roles": ["coordinator"],
        "effect": "evidence",
        "basis": "Original completed selected-review records before an eligible correction; no fresh provider verdict or operation",
        "review_recovery": ["same-operation-recovery", "review-route-change"],
    }
    result = proof(document, binding, "herdr")
    assert result["status"] == "compatible", result
    current = document["node_definitions"]["current-composition"]
    assert any(item["id"] == "composition-current" for item in current["items"])
    assert collector["items"][-2]["choices"] == ["REQUEST_CHANGES"]
    assert collector["items"][-1]["minimum"] == 1


def moved_candidate(basis, *, retain_check=False):
    tmp_path, assignment, current = basis
    assignment["target"]["squad"]["candidate"] = current["target"] = "candidate2"
    for ref in current["assessments"]:
        ref["applicability"] = "preserved"
        ref["applicability_evidence"] = write_artifact(
            tmp_path,
            ref["id"] + "-preserved",
            {
                "before": "candidate1",
                "after": "candidate2",
                "outcome": "pass",
                "preserved_scope": ref["scope"],
                "checks": ["cumulative delta readback"],
                "unknown_impact": False,
            },
        )
    if not retain_check:
        current["checks"][0].update(
            write_artifact(
                tmp_path,
                "current-check",
                {
                    "target": "candidate2",
                    "command": ["existing-test", "behavior"],
                    "outcome": "pass",
                },
            )
        )


def delta_report(tmp_path, role, producer, scope, *, findings=None):
    report = {
        "schema": "aquarium.executor-handoff/v3"
        if role == "Task Operator"
        else "aquarium.evaluator-assessment/v3",
        "work": {"display_role": role},
        "native": {"public_handle": producer},
        "target": {"candidate": "candidate2"},
        "verdict": "pass",
        "criteria": report_rows(),
    }
    if findings is not None:
        report["findings"] = findings
    return {
        **write_artifact(tmp_path, producer + "-delta", report),
        "id": producer + "-delta",
        "role": role,
        "producer": producer,
        "scope": scope,
        "target": "candidate2",
        "applicability": "current",
        "basis": "Independent exact affected judgment",
    }


def affected_case(basis, phase, depth, *, risk="standard", finding=None):
    tmp_path, assignment, current = basis
    if phase in {"integration", "epic-closeout", "correction-group"}:
        integration_basis(tmp_path, current)
        current["phase"] = phase
        primary = next(
            ref for ref in current["assessments"] if ref["role"] == "Epic Evaluator"
        )
        roles = [("Epic Evaluator", "affected-epic")]
    else:
        primary = current["assessments"][0]
        roles = [("Task Evaluator", "affected-result")]
        if risk == "elevated":
            extra = delta_report(
                tmp_path, "Task Operator", "first-second-reviewer", "task-result"
            )
            report = json.loads(Path(extra["path"]).read_text())
            report["target"]["candidate"] = "candidate1"
            extra.update(
                write_artifact(tmp_path, "first-second-reviewer", report),
                target="candidate1",
            )
            current["assessments"].append(extra)
    assignment["target"]["squad"]["risk"] = risk
    assignment["target"]["squad"]["epic_scope_changed"] = False
    report = json.loads(Path(primary["path"]).read_text())
    report.update(
        verdict="rework", criteria=report_rows() if finding else report_rows("unmet")
    )
    if finding:
        report["findings"] = [
            {
                "id": finding,
                "priority": "Low",
                "basis": "Unjustified addition in original assessment",
            }
        ]
    primary.update(write_artifact(tmp_path, "original-primary", report))
    moved_candidate(basis)
    classification = {
        "id": "correction-1",
        "phase": phase,
        "depth": depth,
        "epic_scope_changed": False,
        "basis": "Actual bounded correction impact classification",
        "original_assessments": [copy.deepcopy(primary)],
    }
    assignment["target"]["squad"]["correction"] = classification
    roles += [("Task Operator", "affected-result")] * {
        "primary-only": 0,
        "bounded": 1,
        "elevated": 2,
    }[depth]
    refs = [
        delta_report(
            tmp_path,
            role,
            primary["producer"] if i == 0 else "delta-" + str(i),
            scope,
            findings=[
                {"id": finding, "state": "met", "basis": "Original addition removed"}
            ]
            if finding
            else None,
        )
        for i, (role, scope) in enumerate(roles)
    ]
    current["assessments"] += refs
    proof = {
        "before": "candidate1",
        "after": "candidate2",
        "outcome": "pass",
        "local_eligible": False,
        "unresolved_judgment": False,
        "delta": "Exact affected repair",
        "checks": ["direct affected checks"],
        "assessments": [ref["id"] for ref in refs],
        "correction": classification,
    }
    closure = {
        "assessment": primary["id"],
        "before": "candidate1",
        "after": "candidate2",
        "disposition": "affected-assessment",
        "owner": roles[0][0],
        "basis": "Original obligation and actual delta judgment",
        "verification": write_artifact(tmp_path, "affected-proof", proof),
    }
    closure.update(
        {"finding": finding}
        if finding
        else {"criterion": "original:behavior", "part": "success"}
    )
    current["closures"] = [closure]
    return roles, proof


@pytest.mark.parametrize(
    "phase", ["task-result", "integration", "epic-closeout", "correction-group"]
)
@pytest.mark.parametrize("depth", ["primary-only", "bounded", "elevated"])
def test_correction_depth_and_primary_are_shared_by_dispatch_and_settlement(
    basis, phase, depth
):
    roles, _ = affected_case(basis, phase, depth)
    assert assignments(basis[1], "assess-affected", "evaluator") == roles
    assert composition(*basis)["status"] == "ready"
    assert basis[1]["target"]["squad"]["risk"] == "standard"
    basis[2]["assessments"].pop()
    with pytest.raises(BundleError):
        composition(*basis)


def test_primary_only_delta_does_not_recreate_elevated_first_panel(basis):
    roles, _ = affected_case(basis, "task-result", "primary-only", risk="elevated")
    assert roles == [("Task Evaluator", "affected-result")]
    assert assignments(basis[1], "assess-affected", "evaluator") == roles
    assert composition(*basis)["status"] == "ready"


@pytest.mark.parametrize("fault", ["missing", "unknown-depth", "unknown-impact"])
def test_affected_judgment_requires_actual_correction_classification(basis, fault):
    affected_case(basis, "task-result", "bounded")
    classification = basis[1]["target"]["squad"]["correction"]
    if fault == "missing":
        basis[1]["target"]["squad"].pop("correction")
    elif fault == "unknown-depth":
        classification["depth"] = "unknown"
    else:
        classification["epic_scope_changed"] = None
    with pytest.raises(BundleError):
        assignments(basis[1], "assess-affected", "evaluator")


def reusable_check(basis, *, execution="reusable"):
    moved_candidate(basis, retain_check=True)
    tmp_path, assignment, current = basis
    ref = current["checks"][0]
    original = json.loads(Path(ref["path"]).read_text())
    context = {
        "command": original["command"],
        "coverage": ["original:behavior"],
        "inputs": "same product inputs",
        "dependencies": "same dependency snapshot",
        "environment": "same verification environment",
    }
    assignment["target"]["squad"]["required_checks"] = [
        {
            "id": "behavior",
            "execution": execution,
            "basis": "Approved existing verification policy",
        }
    ]
    proof = {
        "before": "candidate1",
        "after": "candidate2",
        "outcome": "pass",
        "unknown_impact": False,
        "check_id": "behavior",
        "preserved_scope": "task-result",
        "source_check": copy.deepcopy(ref),
        "before_context": context,
        "after_context": copy.deepcopy(context),
        "basis": "Cumulative delta leaves this original check obligation unchanged",
    }
    ref["applicability"] = "preserved"
    ref["applicability_evidence"] = write_artifact(
        tmp_path, "check-applicability", proof
    )
    return ref, proof


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "exact-final",
        "changed-input",
        "unknown",
        "source-mismatch",
        "failed-original",
        "missing-proof",
    ],
)
def test_prior_check_reuse_keeps_original_receipt_and_requires_current_fit(
    basis, fault
):
    ref, proof = reusable_check(
        basis, execution="current-target" if fault == "exact-final" else "reusable"
    )
    original_bytes = Path(ref["path"]).read_bytes()
    if fault == "changed-input":
        proof["after_context"]["inputs"] = "changed product inputs"
    elif fault == "unknown":
        proof["unknown_impact"] = True
    elif fault == "source-mismatch":
        proof["source_check"]["sha256"] = "sha256:" + "0" * 64
    elif fault == "failed-original":
        receipt = json.loads(original_bytes)
        receipt["outcome"] = "fail"
        ref.update(write_artifact(basis[0], "failed-original", receipt))
    if fault == "missing-proof":
        ref.pop("applicability_evidence")
    else:
        ref["applicability_evidence"] = write_artifact(
            basis[0], "check-applicability", proof
        )
    if fault:
        with pytest.raises(BundleError):
            composition(*basis)
    else:
        result = composition(*basis)
        assert result["status"] == "ready"
        assert Path(ref["path"]).read_bytes() == original_bytes
        assert json.loads(original_bytes)["target"] == "candidate1"
        assert result["checks"][0] == ref


@pytest.mark.parametrize("phase", ["task-plan", "epic-plan", "task-result"])
def test_explicit_empty_due_inventory_does_not_manufacture_checks(basis, phase):
    value = commit_input(basis)
    current = (
        value["composition"]
        if phase == "task-result"
        else value["plan_compositions"][phase]
    )
    value["assignment"]["target"]["squad"]["required_checks"] = {phase: []}
    current["checks"] = []
    assert composition(basis[0], value["assignment"], current)["status"] == "ready"
    value["assignment"]["target"]["squad"]["required_checks"].pop(phase)
    with pytest.raises(BundleError):
        composition(basis[0], value["assignment"], current)


@pytest.mark.parametrize(
    "fault,code",
    [
        ("drift", "source-drift"),
        ("invalid", "not-established"),
        ("missing", "not-established"),
    ],
)
def test_evidence_error_preserves_drift_versus_retrieval_classification(
    tmp_path, fault, code
):
    from adaptive_squad import artifact

    ref = write_artifact(tmp_path, "source", {"original": True})
    if fault == "drift":
        Path(ref["path"]).write_text('{"changed":true}')
    elif fault == "invalid":
        raw = b"not JSON"
        Path(ref["path"]).write_bytes(raw)
        ref.update(sha256=sha256(raw), bytes=len(raw))
    else:
        Path(ref["path"]).unlink()
    with pytest.raises(BundleError) as result:
        artifact(tmp_path, ref)
    assert result.value.code == code


@pytest.mark.parametrize(
    "fault",
    [None, "unidentified", "second-finding", "negative-part", "passing-checkpoint"],
)
def test_original_named_assessment_finding_uses_exact_local_closure(basis, fault):
    tmp_path, _, current = basis
    ref = current["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    report["verdict"] = "rework"
    if fault != "unidentified":
        report["findings"] = [
            {"id": "addition", "priority": "Low", "basis": "Unjustified abstraction"}
        ]
    if fault == "second-finding":
        report["findings"].append(
            {"id": "other", "priority": "Low", "basis": "Separate unresolved addition"}
        )
    if fault == "negative-part":
        report["criteria"] = report_rows("unmet")
    if fault == "passing-checkpoint":
        report.update(current_checkpoint("task-result"))
    ref.update(write_artifact(tmp_path, "te-named-original", report))
    moved_candidate(basis)
    current["closures"] = [
        {
            "assessment": "te",
            "finding": "addition",
            "before": "candidate1",
            "after": "candidate2",
            "disposition": "local-verified-fix",
            "owner": "Coordinator",
            "basis": "Finite removal under original requirement",
            "verification": write_artifact(
                tmp_path,
                "finding-fix",
                {
                    "before": "candidate1",
                    "after": "candidate2",
                    "outcome": "pass",
                    "local_eligible": True,
                    "unresolved_judgment": False,
                    "delta": "Remove original addition",
                    "checks": ["direct regression"],
                },
            ),
        }
    ]
    if fault == "unidentified":
        with pytest.raises(BundleError):
            composition(*basis)
    else:
        result = composition(*basis)
        assert result["status"] == (
            "unresolved" if fault in {"second-finding", "negative-part"} else "ready"
        )
        assert result["original_verdicts"]["te"] == "rework"
        assert result["original_findings"]["te"] == report["findings"]
        current["closures"] = []
        assert composition(*basis)["status"] == "unresolved"


def test_named_finding_affected_judgment_uses_same_correction_scope(basis):
    affected_case(basis, "task-result", "bounded", finding="addition")
    result = composition(*basis)
    assert result["status"] == "ready"
    assert result["original_verdicts"]["te"] == "rework"
    ref = basis[2]["assessments"][-1]
    report = json.loads(Path(ref["path"]).read_text())
    report["findings"][0]["state"] = "unverified"
    ref.update(write_artifact(basis[0], "unresolved-named-delta", report))
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize(
    "commit_policy,commit,state",
    [
        (None, None, "delivery-input-commit-policy-required"),
        (True, None, "delivery-input-commit-required"),
        (True, "delivery-sha", "new-conversation-required"),
        (False, None, "new-conversation-required"),
    ],
)
@pytest.mark.parametrize("owner", ["aquarium:epic-squad", "aquarium:epic-handler"])
def test_actual_design_application_preserves_exact_owner_and_commit_boundary(
    design, commit_policy, commit, state, owner
):
    from test_adaptive_design_unit import consume, proposal

    repo, qualified, _, observation, _ = design
    assignment = qualified["assignment"]
    assignment["work"].update(
        repository=str(repo), roadmap="roadmap.md", epic="EPIC-001"
    )
    caller = {
        **{key: assignment["work"][key] for key in ("repository", "roadmap", "epic")},
        "workflow_owner": owner,
        "mode": "resume",
    }
    if commit_policy is False:
        caller.update(
            mode="plan-handoff",
            profiles={"Task Evaluator": {"cli": "codex", "model": "opaque/model"}},
        )
    proposed, approval = proposal(repo)
    assignment["target"]["design"] = {
        "caller": caller,
        "proposal": proposed,
        "applied": True,
    }
    if commit_policy is not None:
        assignment["target"]["design"]["commit_required"] = commit_policy
    if commit:
        assignment["target"]["design"]["delivery_commit"] = commit
    assignment["authority"]["document_approval"] = approval
    (repo / "README.md").write_text("Approved\n")
    observation["guidance"]["node"]["graph_node_id"] = "apply-documents"
    result = consume(design)
    returned = result["design"]["collaboration_return"]
    assert result["design"]["application"]["status"] == "verified-applied"
    assert returned["status"] == state
    assert returned["caller"] == caller
    assert ("profiles" in returned["caller"]) == (commit_policy is False)
    assert returned["delivery_input_commit_authority"] == "separate"
    assert returned["request"] == "$" + owner + " repository=" + caller[
        "repository"
    ] + " roadmap=" + caller["roadmap"] + " epic=" + caller["epic"] + " mode=" + caller[
        "mode"
    ] + (
        " profiles=" + json.dumps(caller["profiles"], sort_keys=True)
        if "profiles" in caller
        else ""
    )
    assignment["authority"]["document_approval"]["decision"] = "denied"
    assert consume(design)["status"] == "approval-required"
    observation["status"]["session"]["lifecycle"] = "completed"
    assert consume(design)["status"] == "terminal-resolved"


def test_actual_composition_placement_requires_and_consumes_original_evidence(
    basis, monkeypatch
):
    tmp_path, assignment, current = basis
    document, binding = reusable()
    monkeypatch.setattr(
        execution,
        "resume_selected",
        lambda *args, **kwargs: {
            "binding": binding,
            "source": yaml.safe_dump(document).encode(),
            "bundle_id": "fixture",
            "path": str(tmp_path),
            "qualification": {},
        },
    )
    observation = {
        "status": {
            "procedure": binding["procedure"],
            "session": {"id": "session", "lifecycle": "running", "revision": 1},
            "current": {"attempt": {"attempt_id": "attempt", "attempt_number": 1}},
        },
        "guidance": {"node": {"graph_node_id": "current-composition"}},
        "active_items": [],
        "mutation_templates": [],
    }
    consume = lambda: execution.execution_context(
        tmp_path,
        roots=["definitions"],
        entrypoint="epic-squad",
        qualification={"assignment": assignment},
        client=SimpleNamespace(health=lambda: observation),
    )
    assert consume()["status"] == "composition-required"
    assignment["target"]["squad"]["compositions"] = {"current-composition": current}
    result = consume()
    assert result["composition"]["status"] == "ready"
    assert (
        result["composition"]["native_values"]["composition-goal-outcome"] == "achieved"
    )
    current["pending"]["judgment"] = 1
    assert consume()["composition"]["status"] == "unresolved"
    Path(current["assessments"][0]["path"]).unlink()
    with pytest.raises(BundleError):
        consume()


def test_affected_primary_and_reviewer_cannot_share_one_instance(basis):
    affected_case(basis, "task-result", "bounded")
    ref = basis[2]["assessments"][-1]
    report = json.loads(Path(ref["path"]).read_text())
    producer = basis[2]["assessments"][-2]["producer"]
    report["native"]["public_handle"] = producer
    ref.update(
        write_artifact(basis[0], "same-instance-reviewer", report), producer=producer
    )
    with pytest.raises(BundleError):
        composition(*basis)


def test_scoped_future_finding_keeps_original_report_without_current_waiver(basis):
    ref = basis[2]["assessments"][-1]
    report = json.loads(Path(ref["path"]).read_text())
    report.update(
        verdict="rework",
        checkpoint_result="pass",
        findings=[
            {
                "id": "future-seam",
                "priority": "Low",
                "applicability": "Later Task integration, outside this current contribution",
            }
        ],
    )
    ref.update(
        write_artifact(basis[0], "ee-future-finding", report),
        future_findings=["future-seam"],
    )
    result = composition(*basis)
    assert result["status"] == "ready"
    assert result["original_findings"]["ee"] == report["findings"]
    ref.pop("future_findings")
    assert composition(*basis)["status"] == "unresolved"


def test_unidentified_negative_verdict_cannot_hide_in_passing_checkpoint(basis):
    ref = basis[2]["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    report.update(verdict="rework", **current_checkpoint("task-result"))
    ref.update(write_artifact(basis[0], "unidentified-negative", report))
    assert composition(*basis)["status"] == "unresolved"


def test_explicit_current_target_policy_accepts_actual_current_receipt(basis):
    basis[1]["target"]["squad"]["required_checks"] = [
        {
            "id": "behavior",
            "execution": "current-target",
            "basis": "Existing exact-final repository gate",
        }
    ]
    assert composition(*basis)["status"] == "ready"
    basis[1]["target"]["squad"]["required_checks"][0]["execution"] = "reusable"
    assert composition(*basis)["status"] == "ready"


def test_validation_affected_context_dispatches_ee_primary_at_actual_depth(
    basis, monkeypatch
):
    repo, assignment, _ = basis
    affected_case(basis, "integration", "bounded")
    document, binding = reusable("validation")
    assignment["target"]["procedure_plan"]["family"] = "validation"
    monkeypatch.setattr(
        execution,
        "resume_selected",
        lambda *args, **kwargs: {
            "binding": binding,
            "source": yaml.safe_dump(document).encode(),
            "bundle_id": "fixture",
            "path": str(repo),
            "qualification": {},
        },
    )
    observation = {
        "status": {
            "procedure": binding["procedure"],
            "session": {"id": "session", "lifecycle": "running", "revision": 1},
            "current": {"attempt": {"attempt_id": "attempt", "attempt_number": 1}},
        },
        "guidance": {"node": {"graph_node_id": "assess-affected"}},
        "active_items": [],
        "mutation_templates": [],
    }
    result = execution.execution_context(
        repo,
        roots=["definitions"],
        entrypoint="epic-squad",
        qualification={"assignment": assignment},
        client=SimpleNamespace(health=lambda: observation),
    )
    assert [
        (row["work"]["display_role"], row["work"]["assignment_scope"])
        for row in result["dispatches"]
    ] == [("Epic Evaluator", "affected-epic"), ("Task Operator", "affected-result")]
    assert all(row["authority"]["effects"] == [] for row in result["dispatches"])


@pytest.mark.parametrize(
    "scope",
    ["task-plan", "epic-plan", "epic-contribution", "affected-result", "affected-epic"],
)
def test_unidentified_scoped_negative_needs_represented_future_obligation(basis, scope):
    repo, assignment, current = basis
    value = commit_input(basis)
    if scope in {"task-plan", "epic-plan"}:
        current = value["plan_compositions"][scope]
        ref = current["assessments"][0]
    elif scope == "epic-contribution":
        ref = current["assessments"][-1]
    else:
        role = "Task Evaluator" if scope == "affected-result" else "Epic Evaluator"
        ref = delta_report(repo, role, "extra-affected", scope)
        report = json.loads(Path(ref["path"]).read_text())
        report["target"]["candidate"] = "candidate1"
        ref.update(
            write_artifact(repo, "extra-affected-current", report), target="candidate1"
        )
        current["assessments"].append(ref)
    assert composition(repo, assignment, current)["status"] == "ready"
    report = json.loads(Path(ref["path"]).read_text())
    report.update(verdict="rework", **current_checkpoint(scope))
    ref.update(write_artifact(repo, scope + "-unidentified-negative", report))
    result = composition(repo, assignment, current)
    assert result["status"] == "unresolved"
    assert result["original_verdicts"][ref["id"]] == "rework"
    assert result["original_criteria"][ref["id"]] == report["criteria"]
    assert {"assessment": ref["id"], "reason": "unresolved-negative-verdict"} in result[
        "gaps"
    ]


@pytest.mark.parametrize(
    "fault", ["proof-participant", "classification-phase", "named-resolution"]
)
def test_exact_affected_guards_reject_only_the_declared_missing_guarantee(basis, fault):
    _, proof = affected_case(
        basis,
        "task-result",
        "elevated",
        finding="addition" if fault == "named-resolution" else None,
    )
    assert composition(*basis)["status"] == "ready"
    reports = {ref["id"]: ref for ref in basis[2]["assessments"]}
    if fault == "proof-participant":
        proof["assessments"].pop()
    elif fault == "classification-phase":
        proof["correction"]["phase"] = "task-plan"
    else:
        ref = reports[proof["assessments"][-1]]
        report = json.loads(Path(ref["path"]).read_text())
        report["findings"][0]["state"] = "unverified"
        ref.update(write_artifact(basis[0], "unresolved-only-named-delta", report))
    basis[2]["closures"][0]["verification"] = write_artifact(
        basis[0], "one-affected-gap", proof
    )
    assert all(Path(ref["path"]).is_file() for ref in reports.values())
    assert all(identifier in reports for identifier in proof["assessments"])
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("role", ["Task Evaluator", "Task Operator", "Epic Evaluator"])
def test_original_finding_owner_or_supported_replacement_must_judge_delta(basis, role):
    repo, assignment, current = basis
    _, proof = affected_case(basis, "task-result", "bounded")
    original = next(
        ref
        for ref in current["assessments"]
        if ref["role"] == role and ref["scope"] in {"task-result", "epic-contribution"}
    )
    if original["id"] != "te":
        te = next(ref for ref in current["assessments"] if ref["id"] == "te")
        report = json.loads(Path(te["path"]).read_text())
        report.update(verdict="pass", criteria=report_rows())
        te.update(write_artifact(repo, "te-not-the-owner", report))
        report = json.loads(Path(original["path"]).read_text())
        report.update(verdict="rework", criteria=report_rows("unmet"))
        original.update(write_artifact(repo, "actual-original-owner", report))
    classification = assignment["target"]["squad"]["correction"]
    classification["original_assessments"] = [copy.deepcopy(original)]
    proof["correction"] = classification
    current["closures"][0]["assessment"] = original["id"]
    scope = "affected-epic" if role == "Epic Evaluator" else "affected-result"
    same_role = next(
        (
            ref
            for ref in current["assessments"]
            if ref["id"] in proof["assessments"] and ref["role"] == role
        ),
        None,
    )
    if same_role:
        proof["assessments"].remove(same_role["id"])
    owner_delta = delta_report(repo, role, "unrelated-owner", scope)
    current["assessments"].append(owner_delta)
    proof["assessments"].append(owner_delta["id"])
    current["closures"][0]["verification"] = write_artifact(
        repo, "owner-required", proof
    )
    with pytest.raises(BundleError):
        composition(*basis)
    report = json.loads(Path(owner_delta["path"]).read_text())
    report["native"]["public_handle"] = original["producer"]
    owner_delta.update(
        write_artifact(repo, "same-original-owner", report),
        producer=original["producer"],
    )
    assert composition(*basis)["status"] == "ready"
    report["native"].update(
        public_handle="replacement-owner",
        replaces={
            "assessment": original["id"],
            "public_handle": original["producer"],
            "basis": "Supported ordinary recovery supplied all original criteria, gaps and current artifacts",
        },
    )
    owner_delta.update(
        write_artifact(repo, "replacement-owner", report), producer="replacement-owner"
    )
    assert composition(*basis)["status"] == "ready"
    report["native"]["replaces"]["assessment"] = "different-original"
    owner_delta.update(write_artifact(repo, "wrong-owner-replacement", report))
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize(
    "verdict,state,optional",
    [("rework", "unmet", True), ("pass", "met", True), ("rework", "unmet", False)],
)
def test_original_optional_advice_is_nonblocking_without_waiving_required_parts(
    basis, verdict, state, optional
):
    repo, _, current = basis
    ref = current["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    finding = {
        "id": "advice",
        "priority": "optional" if optional else "Low",
        "state": "open",
        "basis": "Original reviewer suggestion or defect",
    }
    report.update(verdict=verdict, criteria=report_rows(state), findings=[finding])
    ref.update(write_artifact(repo, "original-advice", report))
    assert composition(*basis)["status"] == (
        "ready" if verdict == "pass" else "unresolved"
    )
    if verdict != "pass":
        moved_candidate(basis)
        current["closures"] = [
            {
                "assessment": "te",
                "criterion": "original:behavior",
                "part": "success",
                "before": "candidate1",
                "after": "candidate2",
                "owner": "Coordinator",
                "basis": "Finite restoration of the required part",
                "disposition": "local-verified-fix",
                "verification": write_artifact(
                    repo,
                    "required-part-only",
                    {
                        "before": "candidate1",
                        "after": "candidate2",
                        "outcome": "pass",
                        "local_eligible": True,
                        "unresolved_judgment": False,
                        "delta": "Exact required behavior restored",
                        "checks": ["direct regression"],
                    },
                ),
            }
        ]
        result = composition(*basis)
        assert result["status"] == ("ready" if optional else "unresolved")
        assert result["original_findings"]["te"] == [finding]


def test_basis_alone_cannot_reclassify_a_current_finding_as_future(basis):
    repo, _, current = basis
    ref = current["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    report.update(
        verdict="rework",
        **current_checkpoint("task-result"),
        findings=[{"id": "addition", "basis": "Original current unjustified addition"}],
    )
    ref.update(
        write_artifact(repo, "current-not-future", report), future_findings=["addition"]
    )
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("scope", ["task-plan", "epic-plan"])
@pytest.mark.parametrize("depth", ["primary-only", "elevated"])
@pytest.mark.parametrize("named", [False, True])
def test_actual_plan_reentry_settles_preserved_first_report_at_current_depth(
    basis, monkeypatch, scope, depth, named
):
    repo, assignment, _ = basis
    value = commit_input(basis)
    plan = value["plan_compositions"][scope]
    primary = plan["assessments"][0]
    report = json.loads(Path(primary["path"]).read_text())
    report.update(
        verdict="rework", criteria=report_rows() if named else report_rows("unmet")
    )
    if named:
        report["findings"] = [
            {
                "id": "plan-objection",
                "priority": "Low",
                "basis": "Original plan contract objection",
            }
        ]
    primary.update(write_artifact(repo, "first-negative-" + scope, report))
    assignment["target"]["squad"]["plan"] = "plan2"
    for phase, composition_value in value["plan_compositions"].items():
        composition_value["target"] = "plan2"
        for ref in composition_value["assessments"]:
            ref["applicability"] = "preserved"
            ref["applicability_evidence"] = write_artifact(
                repo,
                phase + "-" + ref["id"] + "-preserved",
                {
                    "before": "plan1",
                    "after": "plan2",
                    "outcome": "pass",
                    "preserved_scope": phase,
                    "checks": ["current plan delta applicability"],
                    "unknown_impact": False,
                },
            )
    classification = {
        "id": "plan-repair",
        "phase": scope,
        "depth": depth,
        "epic_scope_changed": False,
        "basis": "Actual affected plan correction",
        "original_assessments": [copy.deepcopy(primary)],
    }
    assignment["target"]["squad"]["correction"] = classification
    document, binding = reusable()
    monkeypatch.setattr(
        execution,
        "resume_selected",
        lambda *args, **kwargs: {
            "binding": binding,
            "source": yaml.safe_dump(document).encode(),
            "bundle_id": "fixture",
            "path": str(repo),
            "qualification": {},
        },
    )
    node = "assess-task-plan" if scope == "task-plan" else "assess-epic-plan"
    observation = {
        "status": {
            "procedure": binding["procedure"],
            "session": {"id": "session", "lifecycle": "running", "revision": 1},
            "current": {"attempt": {"attempt_id": "first", "attempt_number": 1}},
        },
        "guidance": {"node": {"graph_node_id": node}},
        "active_items": [],
        "mutation_templates": [],
    }
    consume = lambda: execution.execution_context(
        repo,
        roots=["definitions"],
        entrypoint="epic-squad",
        qualification={"assignment": assignment},
        client=SimpleNamespace(health=lambda: observation),
    )
    assignment["target"]["squad"]["reentry"] = {
        "attempt_id": "caller-only-reentry",
        "basis": "Caller claim alone cannot downgrade first coverage",
        "assessments": [],
    }
    first = consume()
    first_roles = [
        (row["work"]["display_role"], row["work"]["assignment_scope"])
        for row in first["dispatches"]
    ]
    assert first_roles == (
        [("Task Evaluator", "task-plan"), ("Task Operator", "task-plan")]
        if scope == "task-plan"
        else [("Epic Evaluator", "epic-plan")]
    )
    roles = (
        [("Task Evaluator", "affected-result")]
        if scope == "task-plan"
        else [("Epic Evaluator", "affected-epic")]
    )
    roles += [("Task Operator", "affected-result")] * (2 if depth == "elevated" else 0)
    observation["status"]["current"]["attempt"] = {
        "attempt_id": "plan-reentry",
        "attempt_number": 2,
    }
    assignment["target"]["squad"]["reentry"] = {
        "attempt_id": "plan-reentry",
        "basis": "Actual declared plan rework; originals retained",
        "assessments": [list(role) for role in roles],
        "original_evidence": [ref["path"] for ref in plan["assessments"]],
    }
    result = consume()
    actual = [
        (row["work"]["display_role"], row["work"]["assignment_scope"])
        for row in result["dispatches"]
    ]
    assert actual == roles
    ids = []
    for i, row in enumerate(result["dispatches"]):
        role, assigned_scope = (
            row["work"]["display_role"],
            row["work"]["assignment_scope"],
        )
        producer = primary["producer"] if i == 0 else "plan-reviewer-" + str(i)
        ref = delta_report(
            repo,
            role,
            producer,
            assigned_scope,
            findings=[
                {
                    "id": "plan-objection",
                    "state": "met",
                    "basis": "Exact plan objection resolved",
                }
            ]
            if named
            else None,
        )
        assessed = json.loads(Path(ref["path"]).read_text())
        assessed["target"] = {"plan": "plan2"}
        assessed["work"]["assignment_scope"] = assigned_scope
        ref.update(
            write_artifact(repo, "actual-plan-delta-" + str(i), assessed),
            target="plan2",
        )
        plan["assessments"].append(ref)
        ids.append(ref["id"])
    closure = {
        "assessment": primary["id"],
        "before": "plan1",
        "after": "plan2",
        "owner": roles[0][0],
        "disposition": "affected-assessment",
        "basis": "Actual same owner plan judgment, first reports preserved",
        "verification": write_artifact(
            repo,
            "plan-affected-proof",
            {
                "before": "plan1",
                "after": "plan2",
                "outcome": "pass",
                "unresolved_judgment": False,
                "delta": "Exact scoped plan repair",
                "checks": ["plan contract check"],
                "correction": classification,
                "assessments": ids,
            },
        ),
    }
    closure.update(
        {"finding": "plan-objection"}
        if named
        else {"criterion": "original:behavior", "part": "success"}
    )
    plan["closures"] = [closure]
    current = composition(repo, assignment, plan)
    assert (
        current["status"] == "ready"
        and current["original_verdicts"][primary["id"]] == "rework"
    )
    assert commit_handoff(repo, value)["accepted_target"] == "candidate1"
    plan["assessments"].remove(primary)
    with pytest.raises(BundleError):
        composition(repo, assignment, plan)


def test_explicit_original_future_marker_is_distinct_from_justification(basis):
    ref = basis[2]["assessments"][-1]
    report = json.loads(Path(ref["path"]).read_text())
    report.update(
        verdict="rework",
        checkpoint_result="pass",
        findings=[
            {
                "id": "later",
                "scope": "future",
                "basis": "Original reviewer explicitly assigned this later obligation",
            }
        ],
    )
    ref.update(
        write_artifact(basis[0], "explicit-original-future", report),
        future_findings=["later"],
    )
    result = composition(*basis)
    assert (
        result["status"] == "ready"
        and result["original_findings"]["ee"] == report["findings"]
    )
    ref.pop("future_findings")
    assert composition(*basis)["status"] == "unresolved"


def test_original_nonblocking_marker_preserves_mandatory_evidence(basis):
    ref = basis[2]["assessments"][0]
    report = json.loads(Path(ref["path"]).read_text())
    report["findings"] = [
        {
            "id": "advice",
            "priority": "Low",
            "state": "open",
            "blocking": False,
            "basis": "Original reviewer explicitly nonblocking advice",
        }
    ]
    ref.update(write_artifact(basis[0], "nonblocking-original", report))
    assert composition(*basis)["status"] == "ready"
    basis[2]["criteria"] = report_rows("unmet")
    assert composition(*basis)["status"] == "unresolved"
    basis[2]["criteria"] = report_rows()
    report["findings"][0]["required"] = True
    ref.update(write_artifact(basis[0], "explicit-mandatory-finding", report))
    assert composition(*basis)["status"] == "unresolved"


@pytest.mark.parametrize("fault", ["missing-original", "different-original"])
def test_affected_classification_must_identify_the_closed_source(basis, fault):
    _, proof = affected_case(basis, "task-result", "bounded")
    assert composition(*basis)["status"] == "ready"
    if fault == "missing-original":
        proof["correction"].pop("original_assessments")
    else:
        proof["correction"]["original_assessments"][0]["id"] = "different-source"
    basis[2]["closures"][0]["verification"] = write_artifact(
        basis[0], "wrong-source-classification", proof
    )
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("fault", ["author", "wrong-scope"])
def test_supported_replacement_retains_current_independence_and_scope(basis, fault):
    _, proof = affected_case(basis, "task-result", "bounded")
    ref = next(
        row for row in basis[2]["assessments"] if row["id"] == proof["assessments"][0]
    )
    report = json.loads(Path(ref["path"]).read_text())
    report["native"].update(
        public_handle="new-primary",
        replaces={
            "assessment": "te",
            "public_handle": "te",
            "basis": "Supported current recovery from original report and remaining scope",
        },
    )
    ref.update(
        write_artifact(basis[0], "valid-primary-replacement", report),
        producer="new-primary",
    )
    assert composition(*basis)["status"] == "ready"
    if fault == "author":
        report["native"]["public_handle"] = "writer"
        ref.update(
            write_artifact(basis[0], "author-is-not-independent", report),
            producer="writer",
        )
    else:
        ref["scope"] = "task-result"
    with pytest.raises(BundleError):
        composition(*basis)


def owner_recovery_case(basis, role="Task Evaluator"):
    repo, _, current = basis
    phase = "integration" if role == "Epic Evaluator" else "task-result"
    _, proof = affected_case(basis, phase, "bounded")
    assert composition(*basis)["status"] == "ready"
    original = next(
        ref
        for ref in current["assessments"]
        if ref["role"] == role and ref["id"] not in proof["assessments"]
    )
    if role == "Task Operator":
        primary = current["assessments"][0]
        report = json.loads(Path(primary["path"]).read_text())
        report.update(verdict="pass", criteria=report_rows())
        primary.update(write_artifact(repo, "primary-without-objection", report))
        report = json.loads(Path(original["path"]).read_text())
        report.update(verdict="rework", criteria=report_rows("unmet"))
        original.update(write_artifact(repo, "original-reviewer-objection", report))
        proof["correction"]["original_assessments"] = [copy.deepcopy(original)]
        current["closures"][0]["assessment"] = original["id"]
    successor = "te2" if role == "Task Evaluator" else "recovered-" + original["id"]
    replacement = {
        "assessment": original["id"],
        "public_handle": original["producer"],
        "basis": "Supported same-role recovery retains the original negative judgment",
    }
    report = json.loads(Path(original["path"]).read_text())
    report["native"].update(public_handle=successor, replaces=replacement)
    recovered = {
        **copy.deepcopy(original),
        **write_artifact(repo, "recovered-original", report),
        "id": successor,
        "producer": successor,
    }
    current["assessments"].append(recovered)
    proof["correction"]["original_assessments"].append(copy.deepcopy(recovered))
    delta = next(
        ref
        for ref in current["assessments"]
        if ref["id"] in proof["assessments"] and ref["role"] == role
    )
    report = json.loads(Path(delta["path"]).read_text())
    report["native"].update(public_handle=successor, replaces=replacement)
    delta.update(
        write_artifact(repo, "recovered-current-delta", report), producer=successor
    )
    closure = copy.deepcopy(current["closures"][0])
    closure["assessment"] = recovered["id"]
    current["closures"].append(closure)
    verification = write_artifact(repo, "recovered-owner-proof", proof)
    for closure in current["closures"]:
        closure["verification"] = verification
    return proof, recovered, delta


@pytest.mark.parametrize("boundary", ["dispatch", "settlement"])
def test_supported_original_recovery_shares_dispatch_and_settlement_lane(
    basis, boundary
):
    owner_recovery_case(basis)
    if boundary == "dispatch":
        assert assignments(basis[1], "assess-affected", "evaluator") == [
            ("Task Evaluator", "affected-result"),
            ("Task Operator", "affected-result"),
        ]
        return
    result = composition(*basis)
    assert result["status"] == "ready"
    assert result["original_verdicts"]["te"] == "rework"
    assert result["original_verdicts"]["te2"] == "rework"


def test_unrelated_original_owner_still_requires_current_owner_coverage(basis):
    proof, recovered, delta = owner_recovery_case(basis)
    report = json.loads(Path(recovered["path"]).read_text())
    report["native"]["replaces"]["assessment"] = "unrelated-original"
    recovered.update(write_artifact(basis[0], "unrelated-original-owner", report))
    proof["correction"]["original_assessments"][-1] = copy.deepcopy(recovered)
    verification = write_artifact(basis[0], "unrelated-owner-proof", proof)
    for closure in basis[2]["closures"]:
        closure["verification"] = verification
    report = json.loads(Path(delta["path"]).read_text())
    report["native"].pop("replaces")
    delta.update(write_artifact(basis[0], "no-original-owner-continuity", report))
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("fault", ["unrelated-current", "missing-replacement"])
def test_recovered_lane_still_covers_each_original_owner(basis, fault):
    _, _, delta = owner_recovery_case(basis)
    report = json.loads(Path(delta["path"]).read_text())
    if fault == "unrelated-current":
        report["native"]["public_handle"] = "unrelated-current"
        delta["producer"] = "unrelated-current"
    else:
        report["native"].pop("replaces")
    delta.update(write_artifact(basis[0], "incomplete-current-owner", report))
    with pytest.raises(BundleError):
        composition(*basis)


def recovery_chain_case(basis, role, mode):
    repo, _, current = basis
    proof, recovered, delta = owner_recovery_case(basis, role)
    if mode == "current-only":
        report = json.loads(Path(recovered["path"]).read_text())
        report["native"].pop("replaces")
        recovered.update(
            write_artifact(repo, "older-original-without-recovery", report)
        )
        proof["correction"]["original_assessments"][-1] = copy.deepcopy(recovered)
    else:
        previous = recovered
        for number in range(2, 4 if mode == "four-hop" else 2):
            producer = "successor-" + str(number)
            report = json.loads(Path(previous["path"]).read_text())
            report["native"] = {
                "public_handle": producer,
                "replaces": {
                    "assessment": previous["id"],
                    "public_handle": previous["producer"],
                    "basis": "Supported recovery from the supplied original judgment",
                },
            }
            previous = {
                **copy.deepcopy(previous),
                **write_artifact(repo, producer + "-original", report),
                "id": producer,
                "producer": producer,
            }
            current["assessments"].append(previous)
            proof["correction"]["original_assessments"].append(copy.deepcopy(previous))
            closure = copy.deepcopy(current["closures"][0])
            closure["assessment"] = previous["id"]
            current["closures"].append(closure)
        report = json.loads(Path(delta["path"]).read_text())
        report["native"] = {
            "public_handle": "current-successor",
            "replaces": {
                "assessment": previous["id"],
                "public_handle": previous["producer"],
                "basis": "Current supported recovery covers every retained original obligation",
            },
        }
        delta.update(
            write_artifact(repo, "current-successor-delta", report),
            producer="current-successor",
        )
    verification = write_artifact(repo, "chain-proof", proof)
    for closure in current["closures"]:
        closure["verification"] = verification
    return proof, delta


@pytest.mark.parametrize("role", ["Task Evaluator", "Epic Evaluator", "Task Operator"])
@pytest.mark.parametrize("mode", ["current-only", "two-hop", "four-hop"])
@pytest.mark.parametrize("boundary", ["dispatch", "settlement"])
def test_supported_current_and_multihop_recovery_preserves_originals(
    basis, role, mode, boundary
):
    proof, _ = recovery_chain_case(basis, role, mode)
    originals = proof["correction"]["original_assessments"]
    identities = {ref["id"]: Path(ref["path"]).read_bytes() for ref in originals}
    if boundary == "dispatch":
        primary = "Epic Evaluator" if role == "Epic Evaluator" else "Task Evaluator"
        assert assignments(basis[1], "assess-affected", "evaluator") == [
            (
                primary,
                "affected-epic" if primary == "Epic Evaluator" else "affected-result",
            ),
            ("Task Operator", "affected-result"),
        ]
    else:
        result = composition(*basis)
        assert result["status"] == "ready"
        assert all(
            result["original_verdicts"][ref["id"]] == "rework" for ref in originals
        )
    assert all(
        Path(ref["path"]).read_bytes() == identities[ref["id"]] for ref in originals
    )


@pytest.mark.parametrize(
    "fault",
    [
        "current-id",
        "current-handle",
        "current-basis",
        "current-role",
        "historical-id",
        "historical-handle",
        "historical-basis",
        "historical-role",
        "missing-intermediate",
        "cycle",
        "current-coverage",
        "current-scope",
        "current-author",
    ],
)
def test_recovery_chain_rejects_unsupported_or_uncovered_originals(basis, fault):
    proof, delta = recovery_chain_case(basis, "Task Evaluator", "two-hop")
    assert composition(*basis)["status"] == "ready"
    repo, _, current = basis
    originals = proof["correction"]["original_assessments"]
    reference = (
        next(ref for ref in current["assessments"] if ref["id"] == originals[1]["id"])
        if fault.startswith("historical-")
        else delta
    )
    report = json.loads(Path(reference["path"]).read_text())
    if fault.endswith("-id"):
        report["native"]["replaces"]["assessment"] = "unrelated-original"
    elif fault.endswith("-handle"):
        report["native"]["replaces"]["public_handle"] = "unrelated-owner"
    elif fault.endswith("-basis"):
        report["native"]["replaces"].pop("basis")
    elif fault.endswith("-role"):
        report["schema"] = "aquarium.executor-handoff/v3"
        report["work"]["display_role"] = reference["role"] = "Task Operator"
    elif fault == "missing-intermediate":
        originals.pop()
    elif fault == "cycle":
        reference = current["assessments"][0]
        report = json.loads(Path(reference["path"]).read_text())
        report["native"]["replaces"] = {
            "assessment": originals[1]["id"],
            "public_handle": originals[1]["producer"],
            "basis": "Cyclic declarations cannot establish supported ownership",
        }
    elif fault == "current-coverage":
        report["criteria"] = report_rows("unmet")
    elif fault == "current-scope":
        reference["scope"] = "task-result"
    else:
        report["native"]["public_handle"] = reference["producer"] = "writer"
    reference.update(write_artifact(repo, "unsupported-chain-report", report))
    for number, original in enumerate(originals):
        if original["id"] == reference["id"]:
            originals[number] = copy.deepcopy(reference)
    verification = write_artifact(repo, "unsupported-chain-proof", proof)
    for closure in current["closures"]:
        closure["verification"] = verification
    with pytest.raises(BundleError):
        composition(*basis)


def test_supported_recovery_needs_no_history_before_the_original_obligation(basis):
    proof, _, _ = owner_recovery_case(basis)
    original = basis[2]["assessments"][0]
    report = json.loads(Path(original["path"]).read_text())
    report["native"]["replaces"] = {
        "assessment": "earlier-outside-current-correction",
        "public_handle": "earlier-producer",
        "basis": "Earlier recovery is outside the supplied current obligations",
    }
    original.update(write_artifact(basis[0], "original-with-earlier-history", report))
    proof["correction"]["original_assessments"][0] = copy.deepcopy(original)
    verification = write_artifact(basis[0], "current-obligations-proof", proof)
    for closure in basis[2]["closures"]:
        closure["verification"] = verification
    assert composition(*basis)["status"] == "ready"
