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
from adaptive_squad import assignments, commit_handoff, composition, composition_record

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


@pytest.mark.parametrize("member", [False, True])
def test_mapped_groups_preserve_machine_roles_and_no_implicit_writer(
    basis, monkeypatch, member
):
    if member:
        whole_member_case(basis)
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
    if member:
        assert all(
            row["target"]["member_scope"]
            == assignment["target"]["procedure_plan"]["member_scope"]
            for row in result["dispatches"]
        )
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


@pytest.mark.parametrize(
    "assignment_form", ["absent", "text", "inline", "no-bytes", "unavailable"]
)
def test_conditional_closeout_grant_requires_actual_user_acceptance(
    basis, assignment_form
):
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
    current["assessments"].append(
        {**copy.deepcopy(ee), "id": "closeout-ee", "scope": "affected-epic"}
    )
    closeout = current["assessments"][-1]
    report = json.loads(Path(closeout["path"]).read_bytes())
    ordinary_closeout_assignment(tmp_path, assignment, report, assignment_form)
    closeout.update(write_artifact(tmp_path, "ordinary-commit-closeout", report))
    value["grant"].update(kind="conditional-closeout", id="closeout-1")
    assignment["authority"]["commit_grants"] = [copy.deepcopy(value["grant"])]
    with pytest.raises(BundleError):
        commit_handoff(tmp_path, value)
    value["acceptance"]["source"] = "user"
    result = commit_handoff(tmp_path, value)
    assert result["acceptance"]["source"] == "user"
    assert result["grant"]["kind"] == "conditional-closeout"
    report.update(verdict="rework", criteria=report_rows("unmet"))
    closeout.update(
        write_artifact(tmp_path, "ordinary-negative-commit-closeout", report)
    )
    with pytest.raises(BundleError):
        commit_handoff(tmp_path, value)


@pytest.mark.parametrize("member", [False, True])
def test_pure_commit_consumer_executes_no_native_or_commit_effect(basis, member):
    value = whole_member_case(basis) if member else commit_input(basis)
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
    failed = consume()
    assert "composition" not in failed
    assert failed["composition_error"]["code"] == "not-established"
    assert (
        failed["composition_error"]["native_values"]["composition-evidence"]
        == "unavailable"
    )


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


@pytest.mark.parametrize(
    "fault", ["missing-check", "failed-check", "coverage", "drift"]
)
def test_native_negative_record_keeps_strict_failure_without_counts(basis, fault):
    tmp_path, assignment, current = basis
    handoff = commit_input(basis)
    assert (
        composition_record(tmp_path, assignment, current)["composition"]["status"]
        == "ready"
    )
    if fault == "missing-check":
        current["checks"] = []
    elif fault == "failed-check":
        current["checks"] = [
            {
                **write_artifact(
                    tmp_path,
                    "negative-run",
                    {
                        "target": current["target"],
                        "command": ["existing-test", "behavior"],
                        "outcome": "fail",
                    },
                ),
                "id": "behavior",
            }
        ]
    elif fault == "coverage":
        current["assessments"].pop()
    else:
        Path(current["assessments"][0]["path"]).write_text("changed")
    with pytest.raises(BundleError) as original:
        composition(tmp_path, assignment, current)
    result = composition_record(tmp_path, assignment, current)
    assert "composition" not in result
    error = result["composition_error"]
    assert error["code"] == original.value.code
    assert error["message"] == str(original.value)
    assert error["details"] == original.value.details
    assert error["target"] == "candidate1"
    assert error["basis"] == current
    assert error["criterion_counts"] is None
    assert error["native_values"] == {
        "composition-evidence": "unavailable",
        "composition-current": {"outcome": "inconclusive"},
        "composition-goal-outcome": "not-achieved",
        "composition-scope": "task-result",
    }
    with pytest.raises(BundleError):
        commit_handoff(tmp_path, handoff)
    # Re-reading the same unavailable basis cannot promote its outcome on resume.
    assert composition_record(tmp_path, assignment, current) == result


@pytest.mark.parametrize("family", ["goal", "validation"])
def test_unavailable_native_evidence_completes_only_negative_route(family):
    document, binding = reusable(family)
    assert proof(document, binding)["status"] == "compatible"
    for definition in document["node_definitions"].values():
        items = {row["id"]: row for row in definition.get("items", [])}
        if "composition-current" not in items:
            continue
        for name in (
            "composition-unmet",
            "composition-unverified",
            "pending-local",
            "pending-low",
            "current-blockers",
            "pending-judgment",
        ):
            assert items[name]["required"] is False
            assert items[name]["required_when"] == [
                {"item": "composition-evidence", "equals": "established"}
            ]
    # A positive check cannot replace the original real zero-count guard.
    for definition in document["node_definitions"].values():
        for option in definition.get("options", []):
            option["guards"] = [
                row
                for row in option.get("guards", [])
                if row["evidence"]["item"] != "composition-unverified"
            ]
    assert proof(document, binding)["status"] != "compatible"


def test_validation_group_commit_is_intermediate_and_closeout_is_user_only():
    document, binding = reusable("validation")
    nodes = {row["id"]: row for row in document["graph"]["nodes"]}
    assess = document["node_definitions"]["assess-goal"]
    assert assess["assessment"]["outcomes"]["group-ready"] == "not_achieved"
    assert nodes["assess-goal"]["routes"]["group-ready"]["to"] == "record-acceptance"
    for name in ("group-commit", "delegated-closeout"):
        assert not nodes[name].get("terminal", False)
        assert nodes[name]["next"] == "resume-integration"
    assert nodes["resume-integration"]["routes"]["continue"] == {
        "to": "current-composition",
        "effect": "rework",
    }
    assert (
        nodes["approve-closeout"]["routes"]["delegated"]["to"] == "delegated-closeout"
    )
    delegated = next(
        row
        for row in document["node_definitions"]["approve-closeout"]["options"]
        if row["id"] == "delegated"
    )
    assert {
        "evidence": {"node": "current-composition", "item": "composition-scope"},
        "equals": "correction-group",
    } in delegated["guards"]
    assert "integration-complete" not in {row["node"] for row in binding["closeout"]}


def test_retained_old_composition_keeps_its_original_record_contract(basis):
    tmp_path, assignment, current = basis
    assert (
        "composition-evidence"
        not in composition_record(tmp_path, assignment, current, availability=False)[
            "composition"
        ]["native_values"]
    )
    current["checks"] = []
    with pytest.raises(BundleError):
        composition_record(tmp_path, assignment, current, availability=False)


@pytest.mark.parametrize(
    "fault",
    [
        "reference",
        "criterion",
        "part",
        "work",
        "native",
        "target",
        "closure",
        "phase-shape",
        "criterion-shape",
        "parts-shape",
        "closure-shape",
        "findings-shape",
        "confirmation-shape",
        "correction-identity-shape",
        "check-policy-shape",
    ],
)
def test_malformed_composition_has_structured_unavailable_record(basis, fault):
    repo, _assignment, current = basis
    assert composition(*basis)["status"] == "ready"
    if fault in {"confirmation-shape", "correction-identity-shape"}:
        _roles, proof = affected_case(basis, "task-result", "primary-only")
        if fault == "confirmation-shape":
            proof["assessments"] = [None, {}]
        else:
            proof["correction"]["original_assessments"][0]["id"] = ["invalid"]
        verification = write_artifact(repo, "malformed-closure-proof", proof)
        current["closures"][0]["verification"] = verification
    elif fault == "check-policy-shape":
        basis[1]["target"]["squad"]["required_checks"] = [
            {"id": "behavior", "execution": {}}
        ]
    elif fault == "phase-shape":
        current["phase"] = {"unknown": True}
    elif fault == "criterion-shape":
        current["criteria"][0]["state"] = []
    elif fault == "parts-shape":
        current["criteria"][0]["parts"] = {"unknown": True}
    elif fault == "closure-shape":
        current["closures"] = [{"assessment": ["not-an-id"]}]
    elif fault == "findings-shape":
        ref = current["assessments"][0]
        report = json.loads(Path(ref["path"]).read_bytes())
        report["findings"] = [{"id": "invalid", "state": {}}]
        ref.update(write_artifact(repo, "malformed-finding-state", report))
    elif fault == "reference":
        current["assessments"][0].pop("sha256")
    elif fault == "criterion":
        current["criteria"][0].pop("id")
    elif fault == "part":
        current["criteria"][0]["parts"][0].pop("id")
    elif fault == "closure":
        affected_case(basis, "task-result", "primary-only")
        current["closures"][0].pop("verification")
    else:
        ref = current["assessments"][0]
        report = json.loads(Path(ref["path"]).read_text())
        report[fault] = None
        ref.update(write_artifact(repo, "malformed-" + fault, report))
    with pytest.raises(BundleError) as original:
        composition(*basis)
    result = composition_record(*basis)["composition_error"]
    assert result["code"] == original.value.code
    assert result["message"] == str(original.value)
    assert result["basis"] == current
    assert result["criterion_counts"] is None
    assert result["native_values"]["composition-current"]["outcome"] == "inconclusive"
    with pytest.raises(BundleError):
        composition_record(*basis, availability=False)


def test_closeout_requires_actual_exact_candidate_ee_in_addition_to_first_panel(basis):
    repo, _assignment, current = basis
    integration_basis(repo, current)
    assert composition(*basis)["status"] == "ready"
    current["phase"] = "epic-closeout"
    with pytest.raises(BundleError):
        composition(*basis)
    ref = next(ref for ref in current["assessments"] if ref["role"] == "Epic Evaluator")
    closeout = copy.deepcopy(ref)
    closeout.update(id="closeout-ee", scope="affected-epic")
    current["assessments"].append(closeout)
    assert composition(*basis)["status"] == "ready"
    current["assessments"].remove(ref)
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("aliased", [False, True])
@pytest.mark.parametrize(
    "fault",
    [
        "reference",
        "work",
        "criterion",
        "closure",
        "replacement-list",
        "replacement-object",
        "negative-closeout",
        "noncloseout-purpose",
        "contrary-closeout-provenance",
        "dispatch-integration",
        "coarse-unknown-first",
        "member-positive",
        "member-current-negative",
        "member-no-plan",
        *[
            f"ordinary-{form}-{result}"
            for form in ("text", "inline", "no-bytes", "unavailable")
            for result in ("pass", "negative")
        ],
    ],
)
def test_context_cli_consumes_malformed_basis_without_traceback(
    basis, monkeypatch, capsys, aliased, fault
):
    import adaptive_admission
    import adaptive_entrypoint
    import manage_adaptive_procedure as cli

    repo, assignment, current = basis
    document, binding = reusable(
        "validation" if fault == "dispatch-integration" else "goal"
    )
    if fault == "dispatch-integration":
        assignment["target"]["procedure_plan"]["family"] = "validation"
    if aliased:
        capability = binding["nodes"]["current-composition"]["capabilities"][0]
        capability["fields"]["composition-evidence"] = "availability"
        for item in document["node_definitions"]["current-composition"]["items"]:
            if item["id"] == "composition-evidence":
                item["id"] = "availability"
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
        "guidance": {"node": {"graph_node_id": "current-composition"}},
        "active_items": [],
        "mutation_templates": [],
    }
    monkeypatch.setattr(
        adaptive_admission,
        "NativeClient",
        lambda *args: SimpleNamespace(health=lambda: observation),
    )
    monkeypatch.setattr(adaptive_entrypoint, "branch", lambda *args, **kwargs: None)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    qualification = repo / "invocation.json"
    assignment["target"]["squad"]["compositions"] = {"current-composition": current}

    def consume():
        qualification.write_text(json.dumps({"assignment": assignment}))
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "context",
                "context",
                "--repository",
                str(repo),
                "--root",
                "definitions",
                "--entrypoint",
                "epic-squad",
                "--qualification",
                str(qualification),
                "--podway",
                "not-executed",
            ],
        )
        code = cli.main()
        result = json.loads(capsys.readouterr().out)
        assert code == 0, result
        return result

    assert consume()["composition"]["status"] == "ready"
    if fault.startswith("replacement-"):
        _proof, _recovered, delta = owner_recovery_case(basis)
        assert consume()["composition"]["status"] == "ready"
        report = json.loads(Path(delta["path"]).read_bytes())
        report["native"]["replaces"]["assessment"] = (
            [] if fault.endswith("list") else {}
        )
        delta.update(write_artifact(repo, "bad-cli-replacement", report))
    elif fault.startswith("ordinary-"):
        ref = closeout_case(basis)
        assert consume()["composition"]["status"] == "ready"
        report = json.loads(Path(ref["path"]).read_bytes())
        form, outcome = fault.removeprefix("ordinary-").rsplit("-", 1)
        ordinary_closeout_assignment(repo, assignment, report, form)
        if outcome == "negative":
            report.update(verdict="rework", criteria=report_rows("unmet"))
            current["criteria"] = report_rows("unmet")
        ref.update(write_artifact(repo, "cli-ordinary-closeout", report))
        result = consume()["composition"]
        assert result["status"] == ("unresolved" if outcome == "negative" else "ready")
        assert result["native_values"]["composition-unmet"] == int(
            outcome == "negative"
        )
        return
    elif fault.startswith("member-"):
        whole_member_case(basis)
        assignment["target"]["squad"]["compositions"]["current-composition"] = current
        assert consume()["composition"]["status"] == "ready"
        if fault == "member-positive":
            result = consume()["composition"]
            assert result["native_values"]["composition-unverified"] == 0
            assert set(result["original_verdicts"].values()) == {"evidence-needed"}
            assert (
                result["member_scope"]
                == assignment["target"]["procedure_plan"]["member_scope"]
            )
            return
        if fault == "member-no-plan":
            assignment["target"]["squad"]["compositions"].pop("epic-plan")
        else:
            ref = current["assessments"][0]
            report = json.loads(Path(ref["path"]).read_bytes())
            checkpoint = report["checkpoint_assessment"]
            checkpoint["criteria"][0]["state"] = checkpoint["criteria"][0]["parts"][0][
                "state"
            ] = "unverified"
            checkpoint.update(state="unverified", due_unverified=1)
            report["checkpoint_result"] = "inconclusive"
            current["criteria"][0]["state"] = current["criteria"][0]["parts"][0][
                "state"
            ] = "unverified"
            ref.update(write_artifact(repo, "cli-member-current-negative", report))
            result = consume()["composition"]
            assert result["status"] == "unresolved"
            assert result["native_values"]["composition-goal-outcome"] == "not-achieved"
            return
    elif fault == "coarse-unknown-first":
        ref = closeout_case(basis)
        report = json.loads(Path(ref["path"]).read_bytes())
        ordinary_closeout_assignment(repo, assignment, report, "text")
        ref.update(write_artifact(repo, "cli-coarse-purpose-original", report))
        assert consume()["composition"]["status"] == "ready"
        moved_candidate(basis)
        preserve_closeout_report(basis, ref)
        assert consume()["composition"]["status"] == "ready"
        report["work"].pop("assignment_scope")
        ref.update(write_artifact(repo, "cli-coarse-purpose-unknown", report))
        preserve_closeout_report(basis, ref)
    elif fault == "dispatch-integration":
        ref = closeout_case(basis, form="assignment")
        report = json.loads(Path(ref["path"]).read_bytes())
        assignment["target"]["squad"]["work_unit_kind"] = "epic-closeout"
        observation["guidance"]["node"]["graph_node_id"] = "assess-integration"
        original = consume()["dispatches"][0]
        assert original["work"]["assignment_scope"] == "integration"
        assert original["target"]["squad"]["work_unit_kind"] == "epic-closeout"
        assert "correction" not in original["target"]["squad"]
        observation["guidance"]["node"]["graph_node_id"] = "current-composition"
        report["assignment"] = write_artifact(
            repo, "cli-dispatched-integration", original
        )
        ref.update(write_artifact(repo, "cli-original-integration", report))
        assert consume()["composition"]["status"] == "ready"
        moved_candidate(basis)
        preserve_closeout_report(basis, ref)
    elif fault in {"noncloseout-purpose", "contrary-closeout-provenance"}:
        ref = closeout_case(basis, form="checkpoint")
        assert consume()["composition"]["status"] == "ready"
        report = json.loads(Path(ref["path"]).read_bytes())
        original = copy.deepcopy(assignment)
        original["role"] = "evaluator"
        original["authority"]["effects"] = []
        original["target"]["procedure_plan"]["family"] = "validation"
        original["checkpoint"] = "assess-affected"
        original["target"]["squad"]["work_unit_kind"] = "validation-remediation"
        original["target"]["squad"]["correction"] = {"phase": "integration"}
        report["assignment"] = write_artifact(
            repo, "cli-original-noncloseout-purpose", original
        )
        if fault == "noncloseout-purpose":
            report["target"].pop("squad", None)
            current["phase"] = "integration"
        ref.update(write_artifact(repo, "cli-affected-report-provenance", report))
        if fault == "noncloseout-purpose":
            assert consume()["composition"]["status"] == "ready"
            current["phase"] = "epic-closeout"
        moved_candidate(basis)
        preserve_closeout_report(basis, ref)
    elif fault == "negative-closeout":
        ref = closeout_case(basis)
        assert consume()["composition"]["status"] == "ready"
        report = json.loads(Path(ref["path"]).read_bytes())
        report.update(verdict="rework", criteria=report_rows("unmet"))
        current["criteria"] = report_rows("unmet")
        ref.update(write_artifact(repo, "actual-cli-negative-closeout", report))
        result = consume()["composition"]
        assert result["status"] == "unresolved"
        assert result["native_values"]["composition-unmet"] == 1
        assert (
            result["native_values"][
                "availability" if aliased else "composition-evidence"
            ]
            == "established"
        )
        return
    elif fault == "reference":
        current["assessments"][0].pop("bytes")
    elif fault == "criterion":
        current["criteria"][0].pop("id")
    elif fault == "closure":
        affected_case(basis, "task-result", "primary-only")
        current["closures"][0].pop("verification")
    else:
        ref = current["assessments"][0]
        report = json.loads(Path(ref["path"]).read_bytes())
        report["work"] = None
        ref.update(write_artifact(repo, "malformed-cli-work", report))
    result = consume()
    assert "composition" not in result
    assert result["composition_error"]["criterion_counts"] is None
    native = result["composition_error"]["native_values"]
    assert (
        native["availability" if aliased else "composition-evidence"] == "unavailable"
    )


def test_scoped_validation_original_producers_reach_strict_composition():
    document, binding = reusable("validation")
    assert proof(document, binding)["status"] == "compatible"
    nodes = {r["id"]: r for r in document["graph"]["nodes"]}
    assert nodes["assess-integration"]["next"] == "restore-closeout-basis"
    assert (
        nodes["prepare-final-closeout"]["routes"]["ready"]["to"]
        == "restore-closeout-basis"
    )
    assert nodes["decide-corrections"]["routes"]["closeout"]["to"] == "assess-affected"
    for obligation in binding["obligations"].values():
        assert {
            "node": "restore-closeout-basis",
            "item": "integration-basis",
        } in obligation["producers"]
        assert {"node": "baseline", "item": "context-brief"} not in obligation[
            "producers"
        ]
    nodes["current-composition"]["evidence_from"] = [
        r
        for r in nodes["current-composition"]["evidence_from"]
        if r["node"] != "restore-closeout-basis"
    ]
    assert proof(document, binding)["status"] != "compatible"


@pytest.mark.parametrize("fault", ["missing-producer", "unconsumed-producer"])
def test_restored_integration_obligation_cannot_lose_its_native_endpoint(fault):
    document, binding = reusable("validation")
    assert proof(document, binding)["status"] == "compatible"
    if fault == "missing-producer":
        document["node_definitions"]["restore-closeout-basis"]["items"] = []
    else:
        for row in document["graph"]["nodes"]:
            if row["id"] in {"current-composition", "classify-corrections"}:
                row["evidence_from"] = [
                    ref
                    for ref in row["evidence_from"]
                    if ref["node"] != "restore-closeout-basis"
                ]
    assert proof(document, binding)["status"] != "compatible"


def test_preserved_old_ee_target_cannot_replace_exact_final_closeout_assessment(basis):
    repo, _assignment, current = basis
    integration_basis(repo, current)
    current["phase"] = "epic-closeout"
    ee = next(ref for ref in current["assessments"] if ref["role"] == "Epic Evaluator")
    current["assessments"].append(
        {**copy.deepcopy(ee), "id": "exact-closeout-ee", "scope": "affected-epic"}
    )
    assert composition(*basis)["status"] == "ready"
    moved_candidate(basis)
    with pytest.raises(BundleError):
        composition(*basis)
    ref = current["assessments"][-1]
    report = json.loads(Path(ref["path"]).read_bytes())
    report["target"]["candidate"] = "candidate2"
    ref.update(
        write_artifact(repo, "actual-final-closeout-ee", report),
        target="candidate2",
        applicability="current",
    )
    assert composition(*basis)["status"] == "ready"


def test_record_only_closeout_dispatch_keeps_unchanged_to_panel_as_evidence(basis):
    repo, assignment, current = basis
    integration_basis(repo, current)
    ee = next(ref for ref in current["assessments"] if ref["role"] == "Epic Evaluator")
    assignment["target"]["squad"]["correction"] = {
        "id": "final-records",
        "phase": "epic-closeout",
        "depth": "primary-only",
        "epic_scope_changed": False,
        "basis": "Exact final record-only candidate, original first panel preserved",
        "original_assessments": [copy.deepcopy(ee)],
    }
    assert assignments(assignment, "assess-affected", "evaluator") == [
        ("Epic Evaluator", "affected-epic")
    ]


def test_validation_delegation_uses_only_existing_correction_grant_kind():
    document, _binding = reusable("validation")
    option = next(
        row
        for row in document["node_definitions"]["approve-closeout"]["options"]
        if row["id"] == "delegated"
    )
    assert {
        "evidence": {"node": "record-acceptance", "item": "grant-kind"},
        "equals": "correction",
    } in option["guards"]


def closeout_case(basis, producer="ee", form="work"):
    repo, _assignment, current = basis
    integration_basis(repo, current)
    current["phase"] = "epic-closeout"
    report = {
        "schema": "aquarium.evaluator-assessment/v3",
        "work": {"display_role": "Epic Evaluator"},
        "native": {"public_handle": producer},
        "target": {"candidate": current["target"]},
        "verdict": "pass",
        "criteria": report_rows(),
    }
    if form == "work":
        report["work"]["assignment_scope"] = "affected-epic"
        report["target"]["squad"] = {
            "work_unit_kind": "epic-closeout",
            "candidate": current["target"],
        }
    elif form == "checkpoint":
        report["target"]["squad"] = {
            "correction": {"phase": "epic-closeout"},
            "candidate": current["target"],
        }
        report["checkpoint_assessment"] = {
            "phase": "affected-epic",
            "state": "met",
            "basis": "Actual final lifecycle record review",
            "criteria": report_rows(),
        }
        report["checkpoint_result"] = "pass"
    elif form in {"assignment", "assignment-plain"}:
        assigned = copy.deepcopy(basis[1])
        assigned["role"] = "evaluator"
        assigned["work"]["display_role"] = "Epic Evaluator"
        assigned["work"]["assignment_scope"] = "affected-epic"
        assigned["target"]["squad"]["work_unit_kind"] = "epic-closeout"
        report["assignment"] = write_artifact(
            repo, "actual-closeout-assignment", assigned
        )
        if form == "assignment-plain":
            report["assignment"]["sha256"] = report["assignment"][
                "sha256"
            ].removeprefix("sha256:")
    ref = {
        **write_artifact(repo, "closeout-first-report", report),
        "id": "closeout-first",
        "role": "Epic Evaluator",
        "producer": producer,
        "scope": "affected-epic",
        "target": current["target"],
        "applicability": "current",
        "basis": "Actual first substantive final-record judgment",
    }
    current["assessments"].append(ref)
    return ref


def preserve_closeout_report(basis, ref):
    repo, _assignment, current = basis
    proof = {
        "before": ref["target"],
        "after": current["target"],
        "outcome": "pass",
        "preserved_scope": "affected-epic",
        "checks": ["record readback and integrity"],
        "unknown_impact": False,
        "local_eligible": True,
        "record_only": True,
        "meaning_preserved": True,
        "unresolved_judgment": False,
        "delta": "Finite meaning-preserving final record edit",
        "basis": "Original first closeout judgment still applies",
        "source_assessment": {
            k: v
            for k, v in ref.items()
            if k not in {"applicability", "applicability_evidence"}
        },
    }
    ref["applicability"] = "preserved"
    ref["applicability_evidence"] = write_artifact(
        repo, "preserved-closeout-judgment", proof
    )
    return proof


def test_complete_negative_closeout_ee_remains_established(basis):
    repo, _assignment, current = basis
    ref = closeout_case(basis)
    assert composition(*basis)["status"] == "ready"
    report = json.loads(Path(ref["path"]).read_bytes())
    report.update(verdict="rework", criteria=report_rows("unmet"))
    ref.update(write_artifact(repo, "negative-closeout", report))
    current["criteria"] = report_rows("unmet")
    result = composition_record(*basis)
    assert result["composition"]["status"] == "unresolved"
    assert result["composition"]["native_values"]["composition-unmet"] == 1
    assert (
        result["composition"]["native_values"]["composition-evidence"] == "established"
    )
    assert result["composition"]["original_verdicts"][ref["id"]] == "rework"


@pytest.mark.parametrize(
    "form", ["work", "checkpoint", "assignment", "assignment-plain"]
)
def test_real_closeout_first_assessment_allows_verified_local_record_delta(basis, form):
    ref = closeout_case(basis, form=form)
    assert composition(*basis)["status"] == "ready"
    moved_candidate(basis)
    preserve_closeout_report(basis, ref)
    assert composition(*basis)["status"] == "ready"


def test_integration_to_cannot_supply_final_ee_instance(basis):
    ref = closeout_case(basis)
    assert composition(*basis)["status"] == "ready"
    report = json.loads(Path(ref["path"]).read_bytes())
    report["native"]["public_handle"] = "reviewer"
    ref.update(
        write_artifact(basis[0], "to-disguised-as-ee", report), producer="reviewer"
    )
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("bad", [[], {}])
def test_malformed_replacement_identity_is_structured_after_valid_recovery(basis, bad):
    _proof, _recovered, delta = owner_recovery_case(basis)
    assert composition(*basis)["status"] == "ready"
    report = json.loads(Path(delta["path"]).read_bytes())
    report["native"]["replaces"]["assessment"] = bad
    delta.update(write_artifact(basis[0], "malformed-replacement-identity", report))
    with pytest.raises(BundleError):
        composition(*basis)
    assert composition_record(*basis)["composition_error"]["code"] == "invalid-input"
    with pytest.raises(BundleError):
        composition_record(*basis, availability=False)


def test_affected_group_closure_survives_integration_phase_without_relabel(basis):
    _roles, proof = affected_case(basis, "correction-group", "primary-only")
    assert composition(*basis)["status"] == "ready"
    basis[2]["phase"] = "integration"
    assert composition(*basis)["status"] == "ready"
    assert proof["correction"]["phase"] == "correction-group"


def carried_group_case(basis, owner="Epic Evaluator"):
    repo, _assignment, current = basis
    _roles, proof = affected_case(basis, "correction-group", "bounded")
    if owner == "Task Operator":
        original = next(
            r
            for r in current["assessments"]
            if r["role"] == "Task Operator" and r["scope"] == "integration"
        )
        report = json.loads(Path(original["path"]).read_bytes())
        report["verdict"] = "rework"
        report["findings"] = [
            {
                "id": "TO-1",
                "state": "unmet",
                "basis": "Required original reviewer finding",
            }
        ]
        original.update(write_artifact(repo, "original-to-objection", report))
        proof["correction"]["original_assessments"].append(copy.deepcopy(original))
        delta = next(
            r
            for r in current["assessments"]
            if r["role"] == "Task Operator" and r["scope"] == "affected-result"
        )
        report = json.loads(Path(delta["path"]).read_bytes())
        report["native"]["public_handle"] = original["producer"]
        report["findings"] = [
            {
                "id": "TO-1",
                "state": "met",
                "basis": "Exact independently assessed repair",
            }
        ]
        delta.update(
            write_artifact(repo, "actual-to-confirmation", report),
            producer=original["producer"],
        )
        current["closures"].append(
            {
                **copy.deepcopy(current["closures"][0]),
                "assessment": original["id"],
                "finding": "TO-1",
            }
        )
        current["closures"][-1].pop("criterion")
        current["closures"][-1].pop("part")
        ee_delta = next(
            r
            for r in current["assessments"]
            if r["role"] == "Epic Evaluator" and r["id"] in proof["assessments"]
        )
        report = json.loads(Path(ee_delta["path"]).read_bytes())
        report["findings"] = [
            {
                "id": "TO-1",
                "state": "met",
                "basis": "EE confirms the same original reviewer correction",
            }
        ]
        ee_delta.update(write_artifact(repo, "ee-confirms-to-obligation", report))
        verification = write_artifact(repo, "ee-to-group-closure-proof", proof)
        for closure in current["closures"]:
            closure["verification"] = verification
    assert composition(*basis)["status"] == "ready"
    current["phase"] = "integration"
    assert composition(*basis)["status"] == "ready"
    current["phase"] = "epic-closeout"
    report = {
        "schema": "aquarium.evaluator-assessment/v3",
        "work": {"display_role": "Epic Evaluator", "assignment_scope": "affected-epic"},
        "native": {"public_handle": "ee"},
        "target": {"candidate": current["target"]},
        "criteria": report_rows(),
        "verdict": "pass",
    }
    first = {
        **write_artifact(repo, "first-substantive-closeout", report),
        "id": "final-first",
        "role": "Epic Evaluator",
        "producer": "ee",
        "scope": "affected-epic",
        "target": current["target"],
        "applicability": "current",
        "basis": "Actual first final record review",
    }
    report["target"]["squad"] = {
        "work_unit_kind": "epic-closeout",
        "candidate": current["target"],
    }
    first.update(write_artifact(repo, "first-substantive-closeout", report))
    current["assessments"].append(first)
    assert composition(*basis)["status"] == "ready"
    current["target"] = basis[1]["target"]["squad"]["candidate"] = "candidate3"
    for ref in current["assessments"]:
        ref["applicability"] = "preserved"
        ref["applicability_evidence"] = write_artifact(
            repo,
            ref["id"] + "-record-applicability",
            {
                "before": ref["target"],
                "after": "candidate3",
                "outcome": "pass",
                "preserved_scope": ref["scope"],
                "unknown_impact": False,
                "checks": ["record readback"],
            },
        )
    preserve_closeout_report(basis, first)
    # Existing affected EE confirmations are not the final-first intake. Keep their
    # ordinary scope applicability and bind them in the original closure carry.
    current["checks"] = [
        {
            **write_artifact(
                repo,
                "current-record-check",
                {
                    "target": "candidate3",
                    "command": ["existing-test", "behavior"],
                    "outcome": "pass",
                },
            ),
            "id": "behavior",
        }
    ]
    for closure in current["closures"]:
        original = copy.deepcopy(closure)
        carry = {
            "before": closure["after"],
            "after": "candidate3",
            "current_scope": "epic-closeout",
            "preserved_scope": "correction-group",
            "outcome": "pass",
            "unknown_impact": False,
            "local_eligible": True,
            "record_only": True,
            "meaning_preserved": True,
            "unresolved_judgment": False,
            "delta": "Record-only meaning-preserving change",
            "basis": "Original independent repair remains applicable",
            "checks": ["record integrity"],
            "source_closure": original,
            "confirmations": [
                {
                    k: v
                    for k, v in ref.items()
                    if k not in {"applicability", "applicability_evidence"}
                }
                for identifier in proof["assessments"]
                for ref in current["assessments"]
                if ref["id"] == identifier
            ],
        }
        closure["applicability"] = "preserved"
        closure["applicability_evidence"] = write_artifact(
            repo, closure["assessment"] + "-closure-carry", carry
        )
    return proof, first


@pytest.mark.parametrize("owner", ["Epic Evaluator", "Task Operator"])
def test_original_affected_group_judgments_carry_to_record_closeout(basis, owner):
    proof, _first = carried_group_case(basis, owner)
    assert composition(*basis)["status"] == "ready"
    assert proof["correction"]["phase"] == "correction-group"


@pytest.mark.parametrize(
    "fault",
    [
        "source-closure",
        "confirmations",
        "unknown",
        "meaning",
        "scope",
        "prior-scope",
        "missing-confirmation",
        "lost-original",
        "missing-owner",
        "failed-confirmation",
    ],
)
def test_carried_affected_closure_refuses_unestablished_current_basis(basis, fault):
    proof, _first = carried_group_case(basis, "Task Operator")
    assert composition(*basis)["status"] == "ready"
    closure = basis[2]["closures"][-1]
    carry = json.loads(Path(closure["applicability_evidence"]["path"]).read_bytes())
    if fault == "source-closure":
        carry["source_closure"]["owner"] = "unrelated owner"
    elif fault == "confirmations":
        carry["confirmations"][0]["sha256"] = "sha256:" + "0" * 64
    elif fault == "unknown":
        carry["unknown_impact"] = True
    elif fault == "meaning":
        carry["meaning_preserved"] = False
    elif fault == "scope":
        carry["current_scope"] = "task-result"
    elif fault == "prior-scope":
        carry["preserved_scope"] = "integration"
    elif fault == "missing-confirmation":
        basis[2]["assessments"] = [
            r for r in basis[2]["assessments"] if r["id"] != proof["assessments"][-1]
        ]
    elif fault == "lost-original":
        Path(proof["correction"]["original_assessments"][-1]["path"]).unlink()
    elif fault == "missing-owner":
        ref = next(
            r for r in basis[2]["assessments"] if r["id"] == proof["assessments"][-1]
        )
        report = json.loads(Path(ref["path"]).read_bytes())
        report["native"]["public_handle"] = "unrelated"
        ref.update(
            write_artifact(basis[0], "wrong-carried-owner", report),
            producer="unrelated",
        )
    else:
        ref = next(
            r for r in basis[2]["assessments"] if r["id"] == proof["assessments"][-1]
        )
        report = json.loads(Path(ref["path"]).read_bytes())
        report["verdict"] = "rework"
        ref.update(write_artifact(basis[0], "negative-old-confirmation", report))
    closure["applicability_evidence"] = write_artifact(
        basis[0], "invalid-carry-" + fault, carry
    )
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize(
    "fault",
    [
        "unknown",
        "meaning",
        "record-kind",
        "source-report",
        "first-scope",
        "missing-first",
        "material-judgment",
    ],
)
def test_preserved_closeout_ee_needs_real_first_coverage_and_local_fit(basis, fault):
    ref = closeout_case(basis, form="assignment")
    assert composition(*basis)["status"] == "ready"
    moved_candidate(basis)
    proof = preserve_closeout_report(basis, ref)
    assert composition(*basis)["status"] == "ready"
    if fault == "unknown":
        proof["unknown_impact"] = True
    elif fault == "meaning":
        proof["meaning_preserved"] = False
    elif fault == "record-kind":
        proof["record_only"] = False
    elif fault == "source-report":
        proof["source_assessment"]["bytes"] += 1
    elif fault == "first-scope":
        report = json.loads(Path(ref["path"]).read_bytes())
        report.pop("assignment")
        report["work"]["assignment_scope"] = "integration"
        ref.update(write_artifact(basis[0], "old-integration-not-closeout", report))
        proof["source_assessment"] = {
            k: v
            for k, v in ref.items()
            if k not in {"applicability", "applicability_evidence"}
        }
    elif fault == "missing-first":
        basis[2]["assessments"].remove(ref)
    else:
        proof["unresolved_judgment"] = True
    ref["applicability_evidence"] = write_artifact(
        basis[0], "invalid-local-closeout-" + fault, proof
    )
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("kind", ["same-ee", "fresh-ee", "replacement-ee"])
def test_final_ee_continuity_preserves_distinct_role_instances(basis, kind):
    producer = "ee" if kind == "same-ee" else "fresh-final-ee"
    ref = closeout_case(basis, producer=producer)
    if kind == "replacement-ee":
        original = next(
            r
            for r in basis[2]["assessments"]
            if r["role"] == "Epic Evaluator" and r["scope"] == "integration"
        )
        report = json.loads(Path(ref["path"]).read_bytes())
        report["native"]["replaces"] = {
            "assessment": original["id"],
            "public_handle": original["producer"],
            "basis": "Supported same-role EE continuity",
        }
        ref.update(write_artifact(basis[0], "supported-final-ee-replacement", report))
    assert composition(*basis)["status"] == "ready"


@pytest.mark.parametrize("form", ["work", "checkpoint"])
@pytest.mark.parametrize(
    "original_phase", ["integration", "correction-group", "epic-plan"]
)
def test_generic_affected_epic_purpose_cannot_create_first_closeout(
    basis, form, original_phase
):
    repo, assignment, current = basis
    ref = closeout_case(basis, form=form)
    report = json.loads(Path(ref["path"]).read_bytes())
    report["target"].pop("squad", None)
    original = copy.deepcopy(assignment)
    original["role"] = "evaluator"
    original["work"].update(
        display_role="Epic Evaluator", assignment_scope="affected-epic"
    )
    original["target"]["squad"]["work_unit_kind"] = (
        "member-task" if original_phase == "epic-plan" else "validation-remediation"
    )
    original["target"]["procedure_plan"]["family"] = (
        "goal" if original_phase == "epic-plan" else "validation"
    )
    original["checkpoint"] = "assess-affected"
    original["target"]["squad"]["correction"] = {
        "id": "original-non-closeout",
        "phase": original_phase,
        "depth": "primary-only",
        "epic_scope_changed": False,
        "basis": "Actual non-closeout affected Epic assessment",
        "original_assessments": [copy.deepcopy(current["assessments"][1])],
    }
    report["assignment"] = write_artifact(
        repo, "non-closeout-original-assignment", original
    )
    ref.update(write_artifact(repo, "genuine-non-closeout-affected-report", report))
    current["phase"] = "integration"
    assert composition(*basis)["status"] == "ready"
    current["phase"] = "epic-closeout"
    moved_candidate(basis)
    preserve_closeout_report(basis, ref)
    with pytest.raises(BundleError):
        composition(*basis)


def test_generic_affected_metadata_without_original_purpose_stays_unknown(basis):
    ref = closeout_case(basis)
    report = json.loads(Path(ref["path"]).read_bytes())
    report["target"].pop("squad", None)
    ref.update(write_artifact(basis[0], "generic-affected-without-purpose", report))
    # Existing exact-candidate ordinary compatibility is retained.
    assert composition(*basis)["status"] == "ready"
    moved_candidate(basis)
    preserve_closeout_report(basis, ref)
    with pytest.raises(BundleError):
        composition(*basis)


def test_original_assignment_contradiction_cannot_be_hidden_by_closeout_report_context(
    basis,
):
    repo, assignment, _current = basis
    ref = closeout_case(basis)
    assert composition(*basis)["status"] == "ready"
    report = json.loads(Path(ref["path"]).read_bytes())
    report["target"]["squad"] = {
        "work_unit_kind": "epic-closeout",
        "candidate": ref["target"],
    }
    original = copy.deepcopy(assignment)
    original["target"]["squad"]["work_unit_kind"] = "validation-remediation"
    original["target"]["procedure_plan"]["family"] = "validation"
    original["checkpoint"] = "assess-affected"
    original["target"]["squad"]["correction"] = {"phase": "integration"}
    report["assignment"] = write_artifact(repo, "contrary-original-purpose", original)
    ref.update(write_artifact(repo, "closeout-label-with-contrary-provenance", report))
    moved_candidate(basis)
    preserve_closeout_report(basis, ref)
    with pytest.raises(BundleError):
        composition(*basis)


def ordinary_closeout_assignment(repo, assignment, report, form):
    original = copy.deepcopy(assignment)
    original["role"] = "evaluator"
    original["work"]["display_role"] = "Epic Evaluator"
    original["work"]["assignment_scope"] = "affected-epic"
    original["target"]["squad"]["work_unit_kind"] = "epic-closeout"
    if form == "text":
        report["assignment"] = "Ordinary assignment delivered as supported text"
    elif form == "inline":
        report["assignment"] = original
    elif form in {"no-bytes", "unavailable"}:
        reference = write_artifact(repo, "ordinary-final-assignment", original)
        if form == "no-bytes":
            reference.pop("bytes")
        else:
            Path(reference["path"]).unlink()
        report["assignment"] = reference


@pytest.mark.parametrize(
    "form", ["absent", "text", "inline", "no-bytes", "unavailable"]
)
@pytest.mark.parametrize("negative", [False, True])
def test_ordinary_exact_closeout_forms_preserve_actual_result(basis, form, negative):
    repo, assignment, current = basis
    ref = closeout_case(basis)
    assert composition(*basis)["status"] == "ready"
    report = json.loads(Path(ref["path"]).read_bytes())
    ordinary_closeout_assignment(repo, assignment, report, form)
    if negative:
        report.update(verdict="rework", criteria=report_rows("unmet"))
        current["criteria"] = report_rows("unmet")
    ref.update(write_artifact(repo, "ordinary-final-report", report))
    result = composition(*basis)
    assert result["status"] == ("unresolved" if negative else "ready")
    assert result["native_values"]["composition-unmet"] == int(negative)


@pytest.mark.parametrize("inline", [False, True])
@pytest.mark.parametrize("moved", [False, True])
def test_dispatch_scope_discriminates_first_closeout_from_integration(
    basis, inline, moved
):
    repo, _assignment, _current = basis
    ref = closeout_case(basis, form="assignment")
    assert composition(*basis)["status"] == "ready"
    report = json.loads(Path(ref["path"]).read_bytes())
    original = json.loads(Path(report["assignment"]["path"]).read_bytes())
    # Actual dispatch retains coarse work-unit kind, but supplies semantic scope.
    assert original["target"]["squad"]["work_unit_kind"] == "epic-closeout"
    original["work"]["assignment_scope"] = "integration"
    original["checkpoint"] = "arbitrary-supported-placement"
    report["assignment"] = (
        original
        if inline
        else write_artifact(repo, "dispatched-integration-assignment", original)
    )
    ref.update(write_artifact(repo, "original-integration-assessment", report))
    assert composition(*basis)["status"] == "ready"
    if moved:
        moved_candidate(basis)
        preserve_closeout_report(basis, ref)
        with pytest.raises(BundleError):
            composition(*basis)


@pytest.mark.parametrize("stage", ["correction-group", "integration", "epic-closeout"])
@pytest.mark.parametrize(
    "fault",
    [
        None,
        "inputs",
        "coverage",
        "dependencies",
        "environment",
        "judgment",
        "unknown",
        "checks",
        "missing-context",
        "empty-context",
        "contrary-record",
        "failed-current-check",
    ],
)
def test_settled_obligation_survives_known_independent_behavioral_delta(
    basis, stage, fault
):
    original_proof, first = carried_group_case(basis)
    assert composition(*basis)["status"] == "ready"
    current = basis[2]
    current["phase"] = stage
    if stage == "epic-closeout":
        report = json.loads(Path(first["path"]).read_bytes())
        report["target"]["candidate"] = current["target"]
        report["target"]["squad"]["candidate"] = current["target"]
        first.update(
            write_artifact(basis[0], "current-behavioral-first-closeout", report),
            target=current["target"],
            applicability="current",
            basis="Actual first closeout judgment after the behavioral change",
        )
        first.pop("applicability_evidence")
        assert first["target"] == report["target"]["candidate"] == "candidate3"
        assert first["applicability"] == "current"
        assert "applicability_evidence" not in first
    else:
        current["assessments"].remove(first)
    assert current["closures"][0]["after"] == "candidate2"
    assert current["closures"][0]["owner"] == "Epic Evaluator"
    assert original_proof["correction"]["phase"] == "correction-group"
    for identifier in original_proof["assessments"]:
        confirmation = next(r for r in current["assessments"] if r["id"] == identifier)
        actual = json.loads(Path(confirmation["path"]).read_bytes())
        assert confirmation["target"] == actual["target"]["candidate"] == "candidate2"
    closure = current["closures"][0]
    carry = json.loads(Path(closure["applicability_evidence"]["path"]).read_bytes())
    carry.update(
        current_scope=stage,
        record_only=False,
        local_eligible=False,
        delta="Independent behavioral correction after the settled repair",
        checks=[current["checks"][0]["id"]],
    )
    context = {
        "inputs": ["settled repair input digest"],
        "coverage": ["original C1/whole"],
        "dependencies": ["unchanged repair dependencies"],
        "environment": "same supported runtime",
        "judgment": "Original owners' confirmed repair meaning",
    }
    carry["before_context"] = copy.deepcopy(context)
    carry["after_context"] = copy.deepcopy(context)
    closure["applicability_evidence"] = write_artifact(
        basis[0], "behavioral-closure-carry", carry
    )
    assert composition(*basis)["status"] == "ready"
    if fault is None:
        return
    if fault in {"inputs", "coverage", "dependencies", "environment", "judgment"}:
        carry["after_context"][fault] = "Changed settled obligation"
    elif fault == "unknown":
        carry["unknown_impact"] = True
    elif fault == "checks":
        carry["checks"] = ["not-a-current-passed-check"]
    elif fault == "empty-context":
        carry["before_context"]["judgment"] = carry["after_context"]["judgment"] = " "
    elif fault == "contrary-record":
        carry.update(record_only=True, local_eligible=True)
        carry["after_context"]["judgment"] = "Contrary known judgment"
    elif fault == "failed-current-check":
        reference = current["checks"][0]
        check = json.loads(Path(reference["path"]).read_bytes())
        check["outcome"] = "fail"
        reference.update(
            write_artifact(basis[0], "failed-current-closure-check", check)
        )
    else:
        carry.pop("before_context")
    closure["applicability_evidence"] = write_artifact(
        basis[0], "invalid-behavioral-carry", carry
    )
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("form", ["text", "inline", "no-bytes", "unavailable"])
def test_moved_closeout_ordinary_forms_still_need_substantive_purpose(basis, form):
    repo, assignment, _current = basis
    ref = closeout_case(basis)
    report = json.loads(Path(ref["path"]).read_bytes())
    ordinary_closeout_assignment(repo, assignment, report, form)
    ref.update(write_artifact(repo, "ordinary-preserved-first-closeout", report))
    moved_candidate(basis)
    proof = preserve_closeout_report(basis, ref)
    assert composition(*basis)["status"] == "ready"
    report["target"].pop("squad")
    ref.update(write_artifact(repo, "ordinary-without-report-purpose", report))
    proof["source_assessment"] = {
        k: v
        for k, v in ref.items()
        if k not in {"applicability", "applicability_evidence"}
    }
    ref["applicability_evidence"] = write_artifact(
        repo, "ordinary-purpose-proof", proof
    )
    if form in {"inline", "no-bytes"}:
        assert composition(*basis)["status"] == "ready"
    else:
        with pytest.raises(BundleError):
            composition(*basis)


def test_optional_assignment_file_does_not_ignore_available_identity_drift(basis):
    repo, assignment, _current = basis
    ref = closeout_case(basis)
    report = json.loads(Path(ref["path"]).read_bytes())
    ordinary_closeout_assignment(repo, assignment, report, "no-bytes")
    ref.update(write_artifact(repo, "optional-assignment-identity-control", report))
    assert composition(*basis)["status"] == "ready"
    Path(report["assignment"]["path"]).write_text("{}")
    with pytest.raises(BundleError) as error:
        composition(*basis)
    assert error.value.code == "source-drift"


@pytest.mark.parametrize(
    "transition", ["later-group", "hook-rewrite", "restored-integration"]
)
def test_behavioral_carry_preserves_settled_originals_across_recovery(
    basis, transition
):
    repo, assignment, current = basis
    proof, first = carried_group_case(basis)
    original_closure = copy.deepcopy(current["closures"][0])
    old_refs = {r["id"]: copy.deepcopy(r) for r in current["assessments"]}
    current["phase"] = (
        "correction-group" if transition == "later-group" else "integration"
    )
    current["assessments"].remove(first)
    closure = current["closures"][0]
    carry = json.loads(Path(closure["applicability_evidence"]["path"]).read_bytes())
    context = {
        "inputs": ["original settled repair"],
        "coverage": ["original:behavior/success"],
        "dependencies": ["unchanged original dependencies"],
        "environment": "same fixture runtime",
        "judgment": "Original independent EE/TO confirmations",
    }
    carry.update(
        current_scope=current["phase"],
        record_only=False,
        local_eligible=False,
        before_context=context,
        after_context=copy.deepcopy(context),
        checks=["behavior"],
        delta=transition,
    )
    closure["applicability_evidence"] = write_artifact(repo, "recovery-carry", carry)
    if transition == "later-group":
        report = {
            "schema": "aquarium.evaluator-assessment/v3",
            "work": {"display_role": "Epic Evaluator"},
            "native": {"public_handle": "second-group-ee"},
            "target": {"candidate": "candidate2"},
            "verdict": "rework",
            "criteria": report_rows(),
            "findings": [
                {
                    "id": "new-independent-obligation",
                    "state": "unmet",
                    "basis": "Separate second behavioral group",
                }
            ],
        }
        source = {
            **write_artifact(repo, "second-group-source", report),
            "id": "second-group-source",
            "role": "Epic Evaluator",
            "producer": "second-group-ee",
            "scope": "integration",
            "target": "candidate2",
            "applicability": "preserved",
            "basis": "Original second-group audit",
        }
        source["applicability_evidence"] = write_artifact(
            repo,
            "second-group-source-applicability",
            {
                "before": "candidate2",
                "after": "candidate3",
                "outcome": "pass",
                "preserved_scope": "integration",
                "checks": ["behavior"],
                "unknown_impact": False,
            },
        )
        current["assessments"].append(source)
        classification = {
            "id": "second-group",
            "phase": "correction-group",
            "depth": "bounded",
            "epic_scope_changed": False,
            "basis": "Independent second behavioral correction",
            "original_assessments": [copy.deepcopy(source)],
        }
        assignment["target"]["squad"]["correction"] = classification
        confirmations = []
        for role, producer, scope in [
            ("Epic Evaluator", "second-group-ee", "affected-epic"),
            ("Task Operator", "second-group-to", "affected-result"),
        ]:
            ref = delta_report(
                repo,
                role,
                producer,
                scope,
                findings=[
                    {
                        "id": "new-independent-obligation",
                        "state": "met",
                        "basis": "Actual second-group repair confirmation",
                    }
                ],
            )
            report = json.loads(Path(ref["path"]).read_bytes())
            report["target"]["candidate"] = "candidate3"
            ref.update(
                write_artifact(repo, "second-group-" + producer, report),
                id="second-group-" + producer,
                target="candidate3",
            )
            current["assessments"].append(ref)
            confirmations.append(ref["id"])
        verification = write_artifact(
            repo,
            "second-group-repair",
            {
                "before": "candidate2",
                "after": "candidate3",
                "outcome": "pass",
                "unresolved_judgment": False,
                "delta": "Independent behavior repaired",
                "checks": ["behavior"],
                "correction": classification,
                "assessments": confirmations,
            },
        )
        current["closures"].append(
            {
                "assessment": source["id"],
                "finding": "new-independent-obligation",
                "before": "candidate2",
                "after": "candidate3",
                "owner": "Epic Evaluator",
                "disposition": "affected-assessment",
                "basis": "Independent second group",
                "verification": verification,
            }
        )
    elif transition == "hook-rewrite":
        output = repo / "hook-produced-record.txt"
        output.write_text("same settled meaning\n")
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; p=Path('hook-produced-record.txt'); p.write_text(p.read_text().rstrip()+'\\n\\n')",
            ],
            cwd=repo,
            check=False,
        )
        assert result.returncode == 0
        assert output.read_text() == "same settled meaning\n\n"
    else:
        # A new consumer restores original integration inputs from disk; no native
        # successor session or installed behavior is claimed by this pure control.
        recovered = write_artifact(repo, "restored-integration-basis", current)
        current = json.loads(Path(recovered["path"]).read_bytes())
        assignment = copy.deepcopy(assignment)
    result = composition(repo, assignment, current)
    assert result["status"] == "ready"
    assert proof["correction"]["phase"] == "correction-group"
    for key, value in original_closure.items():
        if key not in {"applicability", "applicability_evidence"}:
            assert current["closures"][0][key] == value
    assert all(
        next(r for r in current["assessments"] if r["id"] == identifier) == reference
        for identifier, reference in old_refs.items()
        if identifier != first["id"]
    )
    if transition == "later-group":
        assert result["whole_epic_confirmation"] == "pending"


@pytest.mark.parametrize(
    "form", ["text", "path-only", "missing", "unreadable", "absent"]
)
def test_moved_coarse_closeout_kind_needs_actual_original_scope(
    basis, monkeypatch, form
):
    repo, assignment, current = basis
    ref = closeout_case(basis)
    report = json.loads(Path(ref["path"]).read_bytes())
    if form == "text":
        ordinary_closeout_assignment(repo, assignment, report, "text")
    elif form == "path-only":
        ordinary_closeout_assignment(repo, assignment, report, "no-bytes")
        report["assignment"] = {"path": report["assignment"]["path"]}
    elif form == "missing":
        ordinary_closeout_assignment(repo, assignment, report, "unavailable")
    elif form == "unreadable":
        ordinary_closeout_assignment(repo, assignment, report, "no-bytes")
        optional_path = Path(report["assignment"]["path"])
        read_bytes = Path.read_bytes

        def read_optional(path):
            if path == optional_path:
                raise OSError("optional original assignment is unreadable")
            return read_bytes(path)

        monkeypatch.setattr(Path, "read_bytes", read_optional)
    actual_scope = report["work"].pop("assignment_scope")
    ref.update(write_artifact(repo, "coarse-purpose-exact", report))
    assert composition(*basis)["status"] == "ready"
    report.update(verdict="rework", criteria=report_rows("unmet"))
    current["criteria"] = report_rows("unmet")
    ref.update(write_artifact(repo, "coarse-purpose-exact-negative", report))
    negative = composition(*basis)
    assert negative["status"] == "unresolved"
    assert negative["native_values"]["composition-unmet"] == 1
    report.update(verdict="pass", criteria=report_rows())
    current["criteria"] = report_rows()
    report["work"]["assignment_scope"] = actual_scope
    ref.update(write_artifact(repo, "coarse-purpose-original", report))
    assert composition(*basis)["status"] == "ready"
    moved_candidate(basis)
    proof = preserve_closeout_report(basis, ref)
    assert composition(*basis)["status"] == "ready"
    report["work"].pop("assignment_scope")
    assert report["target"]["squad"] == {
        "work_unit_kind": "epic-closeout",
        "candidate": ref["target"],
    }
    ref.update(write_artifact(repo, "coarse-purpose-without-actual-scope", report))
    proof["source_assessment"] = {
        k: v
        for k, v in ref.items()
        if k not in {"applicability", "applicability_evidence"}
    }
    ref["applicability_evidence"] = write_artifact(
        repo, "coarse-purpose-local-proof", proof
    )
    result = composition_record(*basis)
    assert "composition" not in result
    error = result["composition_error"]
    assert error["phase"] == "epic-closeout"
    assert error["target"] == current["target"]
    assert error["criterion_counts"] is None
    assert error["native_values"]["composition-evidence"] == "unavailable"
    assert error["native_values"]["composition-goal-outcome"] == "not-achieved"
    with pytest.raises(BundleError):
        composition(*basis)


# Complete pinned inputs of the installed TASK-001 counterexample, kept as data.
MEMBER_ROADMAP = """# Roadmap

Lifecycle: `Planned` means not started; `In Progress` means authorized work is
active; `In Review` means delivery is awaiting required review or acceptance;
`Completed` means the original criteria and required acceptance are settled;
`Blocked` means a concrete prerequisite prevents progress; `Deferred` means
the operator has explicitly postponed the work. Start a dependent Task only
after its predecessor is completed.

## EPIC-001: Add greeting options

**Status:** `Planned`

Add uppercase and repeat options while preserving the original default and
named greetings. Deliver TASK-001 before TASK-002.

**Detailed SOT:** [Greeting options dossier](../todo/TODO-GREETING-OPTIONS.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-001 | Add uppercase greetings | Add --uppercase for default and named greetings without changing existing behavior. | Planned | None |
| TASK-002 | Add repeated greetings | Add --repeat with a positive integer count and support its combination with --uppercase. | Planned | TASK-001 |
"""

MEMBER_DOSSIER = """# Greeting options

The roadmap owns EPIC-001 and its member identities and lifecycle. Implement
TASK-001, then TASK-002 in separate task-owned changes under the operator's
approved execution scope.

TASK-001 adds `--uppercase`. `python3 greet.py --uppercase` prints
`HELLO, WORLD!` followed by one newline. `python3 greet.py --uppercase Ada`
prints `HELLO, ADA!` followed by one newline. Existing default and named
greetings remain byte-identical. Add meaningful tests and update user guidance.

TASK-002 adds `--repeat N`. A positive integer prints exactly N complete greeting
lines. A missing option retains one line. Zero, negative and noninteger counts
fail with a nonzero exit status. Combine `--uppercase` and `--repeat`. Preserve
TASK-001 and original behavior; add tests and user guidance.

Use the installed handlers, native Codex Workers, an independent Codex Judge and
the explicitly selected three-agent Codex Subagent Review route. Run the
complete fixture Make gate. The operator accepts each ready plan or exact
candidate through the normal handler boundary; no document grants acceptance.

Release startup acceptance stops after real first-member delivery, checks,
independent assessment and semantic progression. It does not establish full
Epic delivery, final review, closeout or publication readiness. Full delivery
and recovery are separate development-verification obligations.
"""


def whole_member_case(basis, *, prepared=False, other_source=None):
    from adaptive_preparation import requirements

    repo, assignment, current = basis
    assert composition(*basis)["status"] == "ready"
    value = commit_input(basis)
    assignment["work"]["requirement_sources"] = []
    scope_rows = []
    for identifier, raw, due, later, gate in [
        (
            "roadmap",
            MEMBER_ROADMAP,
            "| TASK-001 | Add uppercase greetings | Add --uppercase for default and named greetings without changing existing behavior. | Planned | None |",
            "| TASK-002 | Add repeated greetings | Add --repeat with a positive integer count and support its combination with --uppercase. | Planned | TASK-001 |",
            "Start a dependent Task only\nafter its predecessor is completed.",
        ),
        (
            "dossier",
            MEMBER_DOSSIER,
            "TASK-001 adds `--uppercase`. `python3 greet.py --uppercase` prints\n`HELLO, WORLD!` followed by one newline. `python3 greet.py --uppercase Ada`\nprints `HELLO, ADA!` followed by one newline. Existing default and named\ngreetings remain byte-identical. Add meaningful tests and update user guidance.",
            "TASK-002 adds `--repeat N`. A positive integer prints exactly N complete greeting\nlines. A missing option retains one line. Zero, negative and noninteger counts\nfail with a nonzero exit status. Combine `--uppercase` and `--repeat`. Preserve\nTASK-001 and original behavior; add tests and user guidance.",
            "The operator accepts each ready plan or exact\ncandidate through the normal handler boundary; no document grants acceptance.",
        ),
    ]:
        criterion = identifier + ":whole"
        source_fields = {}
        if identifier == "dossier" and other_source:
            if other_source == "markdown":
                raw = (
                    "# Selected\n"
                    + raw.replace("# Greeting options", "## Greeting options", 1)
                    + "\n# Notes\nOriginal note.\n"
                )
                source_fields = {"section": "Selected"}
            else:
                raw = json.dumps(
                    {
                        "criteria": [
                            {
                                "id": "whole",
                                "text": raw,
                                "parts": [{"id": "whole", "text": raw}],
                            }
                        ],
                        "notes": "Original note.",
                    }
                )
                source_fields = {"format": "json"}
        path = repo / (identifier + ".md")
        path.write_text(raw)
        assignment["work"]["requirement_sources"].append(
            {
                "id": identifier,
                "path": path.name,
                "sha256": sha256(path.read_bytes()),
                **source_fields,
            }
        )
        scope_rows.append(
            {
                "criterion": criterion,
                "part": "whole",
                "source": path.name,
                "source_sha256": sha256(path.read_bytes()),
                "due": [
                    {
                        "clause": due,
                        "basis": "Current complete TASK-001 product and due parent obligations",
                    }
                ],
                "later": [
                    {
                        "clause": later,
                        "basis": "Future TASK-002 after predecessor finalization",
                    }
                ],
                "gates": [
                    {
                        "clause": gate,
                        "basis": "Actual acceptance, member commit and native finalization remain separate gates",
                    }
                ],
            }
        )
    shared = {
        "clause": "Run the\ncomplete fixture Make gate.",
        "basis": "Complete gate applies to each member, not only the final Epic",
    }
    scope_rows[1]["due"].append(copy.deepcopy(shared))
    scope_rows[1]["later"].append(copy.deepcopy(shared))
    scope = {"task": "TASK-001", "criteria": scope_rows}
    assignment["success_criteria"] = ["roadmap:whole", "dossier:whole"]
    assignment["target"]["procedure_plan"]["member_scope"] = scope
    rows = [
        {
            "id": row["criterion"],
            "state": "met",
            "parts": [{"id": "whole", "state": "met"}],
        }
        for row in scope_rows
    ]
    original = copy.deepcopy(rows)
    for row in original:
        row["state"] = row["parts"][0]["state"] = "unverified"
        row["parts"][0]["reason"] = (
            "The whole original includes later TASK-002/Epic and post-acceptance gates; current member judgment is separate."
        )
    for composition_basis in [current, *value["plan_compositions"].values()]:
        composition_basis.update(
            criteria=copy.deepcopy(rows), member_scope=copy.deepcopy(scope)
        )
        for reference in composition_basis["assessments"]:
            report = json.loads(Path(reference["path"]).read_bytes())
            report["target"]["member_scope"] = copy.deepcopy(scope)
            report.update(
                criteria=copy.deepcopy(original),
                verdict="evidence-needed",
                checkpoint_result="pass",
                checkpoint_assessment={
                    "phase": reference["scope"],
                    "state": "met",
                    "basis": "Actual independent full plan/source and current due-clause judgment",
                    "criteria": copy.deepcopy(rows),
                    "due_unmet": 0,
                    "due_unverified": 0,
                },
            )
            reference.update(
                write_artifact(
                    repo,
                    reference["id"] + "-" + composition_basis["phase"] + "-member",
                    report,
                )
            )
    assignment["target"]["squad"]["compositions"] = copy.deepcopy(
        value["plan_compositions"]
    )
    if prepared:
        assignment["target"]["prepared_definition"] = {
            "coverage_plan": {
                "criteria": requirements(repo, assignment),
                "member_scope": copy.deepcopy(scope),
            }
        }
    return value


@pytest.mark.parametrize("prepared", [False, True])
def test_actual_whole_markdown_member_ready_retains_future_global_unknowns(
    basis, prepared
):
    value = whole_member_case(basis, prepared=prepared)
    result = composition(*basis)
    assert result["status"] == "ready"
    assert result["native_values"]["composition-unmet"] == 0
    assert result["native_values"]["composition-unverified"] == 0
    assert result["native_values"]["composition-goal-outcome"] == "achieved"
    assert set(result["original_verdicts"].values()) == {"evidence-needed"}
    assert all(
        part["state"] == "unverified"
        for rows in result["original_criteria"].values()
        for row in rows
        for part in row["parts"]
    )
    assert commit_handoff(basis[0], value)["accepted_target"] == "candidate1"
    if not prepared:
        assert "prepared_definition" not in basis[1]["target"]
        assert basis[1]["procedure"] is None


@pytest.mark.parametrize(
    "fault",
    [
        "current-unmet",
        "current-unknown",
        "milestone",
        "required-finding",
        "negative-verdict",
        "failed-check",
        "missing-check",
        "missing-part",
        "unsupported-id",
        "wrong-phase",
        "contradictory-count",
        "stale-candidate",
        "scope-drift",
        "missing-plan",
        "missing-panel",
        "author",
        "old-conservative",
        "missing-checkpoint",
        "missing-plan-judgment",
        "report-scope",
        "source-drift",
        "no-future-basis",
    ],
)
def test_member_scope_does_not_erase_actual_current_gaps(basis, fault):
    whole_member_case(basis)
    assert composition(*basis)["status"] == "ready"
    repo, assignment, current = basis
    ref = current["assessments"][0]
    report = json.loads(Path(ref["path"]).read_bytes())
    if fault in {"current-unmet", "current-unknown", "milestone"}:
        state = "unmet" if fault == "current-unmet" else "unverified"
        report["checkpoint_assessment"]["criteria"][0]["parts"][0]["state"] = state
        report["checkpoint_assessment"]["criteria"][0]["state"] = state
        report["checkpoint_assessment"]["basis"] = (
            "Core is present; CLI/help/docs and complete member evidence are still missing"
            if fault == "milestone"
            else "Actual current due clause is not established"
        )
    elif fault == "required-finding":
        report["findings"] = [
            {
                "id": "current-cli",
                "state": "unmet",
                "required": True,
                "basis": "Current CLI is incomplete",
            }
        ]
    elif fault == "negative-verdict":
        report["verdict"] = "rework"
    elif fault == "failed-check":
        check = json.loads(Path(current["checks"][0]["path"]).read_bytes())
        check["outcome"] = "fail"
        current["checks"][0].update(write_artifact(repo, "member-failed-check", check))
    elif fault == "missing-check":
        current["checks"] = []
    elif fault == "missing-part":
        report["criteria"].pop()
    elif fault == "unsupported-id":
        report["checkpoint_assessment"]["criteria"][0]["id"] = "T1-undeclared-detail"
    elif fault == "wrong-phase":
        report["checkpoint_assessment"]["phase"] = "epic-contribution"
    elif fault == "contradictory-count":
        report["checkpoint_assessment"]["due_unverified"] = 2
    elif fault == "stale-candidate":
        report["target"]["candidate"] = "older-candidate"
    elif fault == "scope-drift":
        assignment["target"]["procedure_plan"]["member_scope"]["criteria"][0]["due"][0][
            "basis"
        ] = "Changed unassessed meaning"
    elif fault == "missing-plan":
        assignment["target"]["squad"]["compositions"].pop("epic-plan")
    elif fault == "missing-panel":
        current["assessments"].pop()
    elif fault == "author":
        assignment["target"]["squad"]["authors"].append(ref["producer"])
    elif fault == "missing-checkpoint":
        report.pop("checkpoint_assessment")
    elif fault == "missing-plan-judgment":
        plan = assignment["target"]["squad"]["compositions"]["epic-plan"]
        plan_ref = plan["assessments"][0]
        plan_report = json.loads(Path(plan_ref["path"]).read_bytes())
        plan_report["checkpoint_result"] = "inconclusive"
        plan_ref.update(write_artifact(repo, "unassessed-member-plan", plan_report))
    elif fault == "report-scope":
        report["target"].pop("member_scope")
    elif fault == "source-drift":
        (repo / "dossier.md").write_text("Changed original")
    elif fault == "no-future-basis":
        report["criteria"][0]["parts"][0].pop("reason")
    else:
        for row in current["criteria"]:
            row["state"] = row["parts"][0]["state"] = "unverified"
        for row in report["checkpoint_assessment"]["criteria"]:
            row["state"] = row["parts"][0]["state"] = "unverified"
        report["checkpoint_assessment"].update(state="unverified", due_unverified=2)
        report["checkpoint_result"] = "inconclusive"
    ref.update(write_artifact(repo, "member-negative-" + fault, report))
    try:
        result = composition(*basis)
    except BundleError:
        return
    assert result["status"] == "unresolved"
    assert result["native_values"]["composition-goal-outcome"] == "not-achieved"


@pytest.mark.parametrize("role", ["Task Evaluator", "Task Operator", "Epic Evaluator"])
@pytest.mark.parametrize("state", ["unmet", "unverified"])
def test_member_current_negative_uses_same_due_basis_for_each_role(basis, role, state):
    whole_member_case(basis)
    assert composition(*basis)["status"] == "ready"
    repo, _assignment, current = basis
    ref = next(r for r in current["assessments"] if r["role"] == role)
    report = json.loads(Path(ref["path"]).read_bytes())
    for rows in [
        report["criteria"],
        report["checkpoint_assessment"]["criteria"],
        current["criteria"],
    ]:
        rows[0]["state"] = rows[0]["parts"][0]["state"] = state
    report["checkpoint_result"] = "fail" if state == "unmet" else "inconclusive"
    report["checkpoint_assessment"].update(
        state=state,
        due_unmet=int(state == "unmet"),
        due_unverified=int(state == "unverified"),
    )
    report["verdict"] = "rework" if state == "unmet" else "evidence-needed"
    ref.update(write_artifact(repo, "member-due-" + ref["id"] + state, report))
    result = composition(*basis)
    assert result["status"] == "unresolved"
    assert result["native_values"]["composition-unmet"] == int(state == "unmet")
    assert result["native_values"]["composition-unverified"] == int(
        state == "unverified"
    )
    assert result["native_values"]["composition-goal-outcome"] == "not-achieved"


@pytest.mark.parametrize("fault", ["acceptance", "grant", "product-review", "plan"])
def test_member_scope_commit_retains_every_actual_gate(basis, fault):
    value = whole_member_case(basis)
    assert commit_handoff(basis[0], value)["accepted_target"] == "candidate1"
    if fault == "acceptance":
        value["acceptance"]["target"] = "stale"
    elif fault == "grant":
        value["grant"]["consumed"] = True
    elif fault == "product-review":
        value["acceptance"].pop("product_review")
    else:
        value["plan_compositions"].pop("epic-plan")
    with pytest.raises(BundleError):
        commit_handoff(basis[0], value)


@pytest.mark.parametrize("phase", ["integration", "epic-closeout", "correction-group"])
def test_member_scope_cannot_waive_global_integration_or_closeout(basis, phase):
    whole_member_case(basis)
    assert composition(*basis)["status"] == "ready"
    repo, assignment, current = basis
    integration_basis(repo, current)
    current["phase"] = phase
    for ref in current["assessments"]:
        report = json.loads(Path(ref["path"]).read_bytes())
        report["checkpoint_assessment"]["phase"] = "integration"
        ref.update(write_artifact(repo, "whole-integration-" + ref["id"], report))
    current["criteria"] = copy.deepcopy(report["criteria"])
    if phase == "epic-closeout":
        ee = next(
            ref for ref in current["assessments"] if ref["role"] == "Epic Evaluator"
        )
        report = json.loads(Path(ee["path"]).read_bytes())
        report["work"]["assignment_scope"] = "affected-epic"
        report["checkpoint_result"] = "inconclusive"
        report["checkpoint_assessment"].update(
            phase="affected-epic",
            state="unverified",
            criteria=copy.deepcopy(report["criteria"]),
            due_unverified=2,
        )
        ordinary_closeout_assignment(repo, assignment, report, "inline")
        current["assessments"].append(
            {
                **copy.deepcopy(ee),
                **write_artifact(repo, "whole-first-closeout", report),
                "id": "whole-first-closeout",
                "scope": "affected-epic",
            }
        )
    result = composition(*basis)
    assert result["status"] == "unresolved"
    assert result["native_values"]["composition-unmet"] == 0
    assert result["native_values"]["composition-unverified"] == 2
    assert result["native_values"]["composition-goal-outcome"] == "not-achieved"
    assert set(result["original_verdicts"].values()) == {"evidence-needed"}
    assert all(
        part["state"] == "unverified"
        for rows in result["original_criteria"].values()
        for row in rows
        for part in row["parts"]
    )


def test_member_assessed_preparation_scope_cannot_drift(basis):
    whole_member_case(basis, prepared=True)
    assert composition(*basis)["status"] == "ready"
    basis[1]["target"]["prepared_definition"]["coverage_plan"]["member_scope"][
        "task"
    ] = "TASK-002"
    with pytest.raises(BundleError) as error:
        composition(*basis)
    assert error.value.code == "source-drift"


def member_lifecycle_case(
    basis, *, native=False, other_source=None, other_change=None, recover_other=False
):
    value = whole_member_case(basis, prepared=native, other_source=other_source)
    repo, assignment, current = basis
    assert composition(*basis)["status"] == "ready"
    roadmap = repo / "roadmap.md"
    original = roadmap.read_bytes()
    capture = repo / ".captures/roadmap.md"
    capture.parent.mkdir()
    capture.write_bytes(original)
    roadmap.write_bytes(
        original.replace(b"| Planned | None |", b"| Completed | None |")
    )
    proposal = {
        "diff": "Apply the exact approved TASK-001 Planned to Completed lifecycle output.",
        "targets": {
            "roadmap.md": {
                "before": sha256(original),
                "after": sha256(roadmap.read_bytes()),
            }
        },
    }
    context = {
        "work": copy.deepcopy(assignment["work"]),
        "sources": [{"path": "roadmap.md", "capture": ".captures/roadmap.md"}],
        "proposal": proposal,
        "approval": {
            "source": "epic-delegation",
            "decision": "approved",
            "proposal": copy.deepcopy(proposal),
            "reference": "Actual fixture approval for this exact lifecycle postimage",
        },
    }
    if other_change:
        dossier = repo / "dossier.md"
        other_original = dossier.read_bytes()
        other_current = other_original
        if other_change == "outside":
            other_current = other_current.replace(
                b"Original note.", b"Changed outside original basis."
            )
        elif other_change == "inside":
            other_current = other_current.replace(
                b"TASK-001 adds", b"Changed current Task adds"
            )
        elif other_change == "identity":
            other_current = other_current.replace(
                b"# Selected" if other_source == "markdown" else b'"id": "whole"',
                b"# Renamed" if other_source == "markdown" else b'"id": "renamed"',
            )
        if other_change == "missing":
            dossier.unlink()
        else:
            assert other_current != other_original
            dossier.write_bytes(other_current)
        if recover_other:
            (repo / ".captures/dossier.md").write_bytes(other_original)
            context["sources"].append(
                {"path": "dossier.md", "capture": ".captures/dossier.md"}
            )
            proposal["targets"]["dossier.md"] = {
                "before": sha256(other_original),
                "after": None if other_change == "missing" else sha256(other_current),
            }
            context["approval"]["proposal"] = copy.deepcopy(proposal)
    # Lifecycle output belongs to the current candidate too. Supply new exact
    # current assessments/checks/acceptance rather than exempting stale inputs.
    assignment["target"]["squad"]["candidate"] = current["target"] = "candidate2"
    for reference in current["assessments"]:
        report = json.loads(Path(reference["path"]).read_bytes())
        report["target"]["candidate"] = "candidate2"
        reference.update(
            write_artifact(repo, "lifecycle-current-" + reference["id"], report),
            target="candidate2",
        )
    for reference in current["checks"]:
        check = json.loads(Path(reference["path"]).read_bytes())
        check["target"] = "candidate2"
        reference.update(write_artifact(repo, "lifecycle-current-check", check))
    value["acceptance"]["target"] = "candidate2"
    review = json.loads(
        Path(value["acceptance"]["product_review"]["path"]).read_bytes()
    )
    review["target"] = "candidate2"
    value["acceptance"]["product_review"] = write_artifact(
        repo, "lifecycle-current-product-review", review
    )
    if native:
        _document, binding = reusable()
        status = {
            "procedure": binding["procedure"],
            "session": {"id": "member-source", "revision": 9, "lifecycle": "running"},
            "goal_revision": 1,
            "current": {
                "node": {"graph_node_id": "current-composition"},
                "attempt": {"attempt_id": "member-active", "attempt_number": 1},
            },
            "current_trace_history": {
                "entries": [
                    {
                        "graph_node_id": "current-composition",
                        "attempt_id": "member-active",
                        "attempt_number": 1,
                        "goal_revision": 1,
                        "validity": "valid",
                        "lifecycle": "active",
                    }
                ]
            },
        }
        observation = {
            "status": status,
            "guidance": {"node": {"graph_node_id": "current-composition"}},
            "active_items": [],
            "mutation_templates": [],
        }
        context["checkpoint"] = {
            "schema": "aquarium.orchestration-checkpoint/v3",
            "work": copy.deepcopy(assignment["work"]),
            "procedure": copy.deepcopy(status),
        }
        assignment["procedure"] = {"native": copy.deepcopy(status)}
        value["observation"] = observation
    return value, context


@pytest.mark.parametrize("native", [False, True])
def test_member_lifecycle_commit_revalidates_approved_originals_and_current_candidate(
    basis, native
):
    from adaptive_preparation import requirements

    value, context = member_lifecycle_case(basis, native=native)
    repo, assignment, _current = basis
    with pytest.raises(BundleError):
        requirements(repo, assignment)
    with pytest.raises(BundleError):
        commit_handoff(repo, value)
    if native:
        from adaptive_finalization import approved_sources

        _reader, context = approved_sources(
            repo, assignment, context, value.pop("observation"), continuation=True
        )
        assert "checkpoint" not in context
        assert context["work"] == assignment["work"]
    assignment["target"]["applied_source_context"] = context
    before = {
        str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob("*") if p.is_file()
    }
    result = commit_handoff(repo, value)
    assert result["accepted_target"] == "candidate2"
    assert (
        result["applied_source_context"]["sources"][0]["sha256"]
        == assignment["work"]["requirement_sources"][0]["sha256"]
    )
    assert result["applied_source_context"]["sources"][0]["applied"]["after"] == sha256(
        (repo / "roadmap.md").read_bytes()
    )
    assert {
        str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob("*") if p.is_file()
    } == before


@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize(
    "fault",
    [
        "no-approval",
        "before",
        "postimage",
        "work",
        "capture",
        "unsafe",
        "approval-source",
        "chain",
        "earlier-path",
        "stale-scope",
        "stale-candidate",
        "acceptance",
        "grant",
        "current-negative",
    ],
)
def test_member_lifecycle_context_cannot_bypass_source_or_completion_guards(
    basis, native, fault
):
    value, context = member_lifecycle_case(basis, native=native)
    repo, assignment, current = basis
    assignment["target"]["applied_source_context"] = context
    assert commit_handoff(repo, value)["accepted_target"] == "candidate2"
    if fault == "no-approval":
        context.pop("approval")
    elif fault == "before":
        context["proposal"]["targets"]["roadmap.md"]["before"] = "sha256:" + "0" * 64
        context["approval"]["proposal"] = copy.deepcopy(context["proposal"])
    elif fault == "postimage":
        (repo / "roadmap.md").write_text("Unapproved after image")
    elif fault == "work":
        context["work"]["task"] = "TASK-002"
        if native:
            context["checkpoint"]["work"]["task"] = "TASK-002"
    elif fault == "capture":
        (repo / ".captures/roadmap.md").unlink()
    elif fault == "unsafe":
        capture = repo / ".captures/roadmap.md"
        capture.unlink()
        capture.symlink_to(repo / "roadmap.md")
    elif fault == "approval-source":
        context["approval"]["source"] = "provider"
    elif fault == "chain":
        first = {
            "proposal": copy.deepcopy(context["proposal"]),
            "approval": copy.deepcopy(context["approval"]),
        }
        second = copy.deepcopy(first)
        second["proposal"]["targets"]["roadmap.md"]["before"] = "sha256:" + "1" * 64
        second["approval"]["proposal"] = copy.deepcopy(second["proposal"])
        context["changes"] = [first, second]
        context.pop("proposal")
        context.pop("approval")
    elif fault == "earlier-path":
        dossier = repo / "dossier.md"
        old = dossier.read_bytes()
        dossier.write_bytes(old + b"\nApproved current record.\n")
        context["proposal"]["targets"]["dossier.md"] = {
            "before": sha256(old),
            "after": sha256(dossier.read_bytes()),
        }
        context["approval"]["proposal"] = copy.deepcopy(context["proposal"])
    elif fault == "stale-scope":
        assignment["target"]["procedure_plan"]["member_scope"]["criteria"][0]["due"][0][
            "basis"
        ] = "Unassessed current scope"
    elif fault == "stale-candidate":
        current["target"] = "candidate1"
    elif fault == "acceptance":
        value["acceptance"]["target"] = "candidate1"
    elif fault == "grant":
        value["grant"]["consumed"] = True
    else:
        reference = current["assessments"][0]
        report = json.loads(Path(reference["path"]).read_bytes())
        report["findings"] = [
            {
                "id": "current-negative",
                "state": "unmet",
                "required": True,
                "basis": "Actual current issue",
            }
        ]
        reference.update(write_artifact(repo, "lifecycle-current-negative", report))
    with pytest.raises(BundleError):
        commit_handoff(repo, value)


@pytest.mark.parametrize(
    "threaded,fault",
    [(False, None), (True, None)]
    + [
        (True, fault)
        for fault in (
            "trace",
            "goal",
            "session",
            "definition",
            "attempt",
            "final-session",
            "final-postimage",
        )
    ],
)
def test_member_native_composition_uses_approved_original_reader_after_lifecycle(
    basis, monkeypatch, threaded, fault
):
    import adaptive_squad
    from adaptive_preparation import requirements

    value, context = member_lifecycle_case(basis, native=True)
    repo, assignment, current = basis
    document, binding = reusable()
    (repo / "procedure.yaml").write_bytes(yaml.safe_dump(document).encode())
    (repo / "binding.json").write_text(json.dumps(binding))
    assignment["target"]["squad"]["compositions"]["current-composition"] = current
    original = assignment["target"]["prepared_definition"]["coverage_plan"]["criteria"]

    def resume(*args, **kwargs):
        assert (
            requirements(
                repo,
                assignment,
                verify_sources=False,
                source_reader=kwargs["source_reader"],
            )
            == original
        )
        return {
            "binding": binding,
            "source": (repo / "procedure.yaml").read_bytes(),
            "path": str(repo),
            "bundle_id": "fixture",
            "qualification": {},
        }

    monkeypatch.setattr(execution, "resume_selected", resume)
    if not threaded:
        original_record = adaptive_squad.composition_record

        def omit_reader(*args, **kwargs):
            assert callable(kwargs.pop("source_reader"))
            return original_record(*args, **kwargs)

        monkeypatch.setattr(adaptive_squad, "composition_record", omit_reader)
    observation = value["observation"]
    status = observation["status"]
    if fault == "trace":
        status["current_trace_history"]["entries"][0]["validity"] = "invalidated"
    elif fault == "goal":
        status["goal_revision"] += 1
    elif fault == "session":
        status["session"]["revision"] += 1
    elif fault == "definition":
        status["procedure"] = {**status["procedure"], "digest": "sha256:" + "0" * 64}
    elif fault == "attempt":
        status["current"]["attempt"]["attempt_id"] = "different"
    reads = []

    def read(*args):
        reads.append(args)
        current = copy.deepcopy(status)
        if len(reads) == 2:
            if fault == "final-session":
                current["session"]["revision"] += 1
            elif fault == "final-postimage":
                (repo / "roadmap.md").write_text("Unapproved final source drift")
        return current

    client = SimpleNamespace(
        health=lambda: observation,
        read=read,
    )

    def consume():
        return execution.execution_context(
            repo,
            roots=["definitions"],
            entrypoint="epic-squad",
            qualification={
                "assignment": assignment,
                "applied_source_recovery": context,
            },
            client=client,
        )

    if fault:
        with pytest.raises(BundleError):
            consume()
        return
    result = consume()
    if threaded:
        assert result["composition"]["status"] == "ready"
        assert result["composition"]["native_values"]["composition-unverified"] == 0
    else:
        assert (
            result["composition_error"]["native_values"]["composition-evidence"]
            == "unavailable"
        )
        assert (
            result["composition_error"]["native_values"]["composition-goal-outcome"]
            == "not-achieved"
        )


def test_member_scope_cannot_repin_similar_sources_under_an_old_plan(basis):
    whole_member_case(basis)
    assert composition(*basis)["status"] == "ready"
    repo, assignment, _current = basis
    dossier = repo / "dossier.md"
    dossier.write_bytes(
        dossier.read_bytes() + b"\nAdditional changed future source context.\n"
    )
    assignment["work"]["requirement_sources"][1]["sha256"] = sha256(
        dossier.read_bytes()
    )
    with pytest.raises(BundleError) as error:
        composition(*basis)
    assert error.value.code == "source-drift"


def test_member_scope_cannot_label_current_cli_future_without_due_plan_passage(basis):
    whole_member_case(basis)
    assert composition(*basis)["status"] == "ready"
    repo, assignment, current = basis
    scope = assignment["target"]["procedure_plan"]["member_scope"]
    clause = scope["criteria"][1]["due"].pop(0)
    scope["criteria"][1]["later"].append(clause)
    bases = [current, *assignment["target"]["squad"]["compositions"].values()]
    for item in bases:
        item["member_scope"] = copy.deepcopy(scope)
        for ref in item["assessments"]:
            report = json.loads(Path(ref["path"]).read_bytes())
            report["target"]["member_scope"] = copy.deepcopy(scope)
            if item["phase"] == "epic-plan":
                report["checkpoint_assessment"]["basis"] = (
                    "Full original source still requires current uppercase CLI/help/docs; the new later attribution omits current member work."
                )
                report["checkpoint_result"] = "inconclusive"
                report["checkpoint_assessment"]["state"] = "unverified"
            ref.update(
                write_artifact(
                    repo, "incomplete-current-" + item["phase"] + ref["id"], report
                )
            )
    with pytest.raises(BundleError):
        composition(*basis)


@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize("omit_earlier", [False, True])
def test_member_lifecycle_preserves_entire_ordered_original_change_chain(
    basis, native, omit_earlier
):
    value, context = member_lifecycle_case(basis, native=native)
    repo, assignment, _current = basis
    dossier = repo / "dossier.md"
    original = dossier.read_bytes()
    (repo / ".captures/dossier.md").write_bytes(original)
    dossier.write_bytes(original + b"\nApproved current delivery record.\n")
    second = {
        "diff": "Apply the separately approved current dossier record",
        "targets": {
            "dossier.md": {
                "before": sha256(original),
                "after": sha256(dossier.read_bytes()),
            }
        },
    }
    context["changes"] = [
        {"proposal": context.pop("proposal"), "approval": context.pop("approval")},
        {
            "proposal": second,
            "approval": {
                "source": "epic-delegation",
                "decision": "approved",
                "proposal": copy.deepcopy(second),
                "reference": "Exact second approved fixture image",
            },
        },
    ]
    context["sources"].append({"path": "dossier.md", "capture": ".captures/dossier.md"})
    assignment["target"]["applied_source_context"] = context
    result = commit_handoff(repo, value)
    assert result["accepted_target"] == "candidate2"
    assert len(result["applied_source_context"]["changes"]) == 2
    assert {row["path"] for row in result["applied_source_context"]["sources"]} == {
        "roadmap.md",
        "dossier.md",
    }
    if omit_earlier:
        context["sources"].pop(0)
        with pytest.raises(BundleError):
            commit_handoff(repo, value)


@pytest.mark.parametrize("detailed", [False, True])
def test_original_whole_member_rejections_are_not_automatically_upgraded(
    basis, detailed
):
    whole_member_case(basis)
    repo, assignment, current = basis
    assignment["target"]["procedure_plan"].pop("member_scope")
    for row in current["criteria"]:
        row["state"] = row["parts"][0]["state"] = "unverified"
    for ref in current["assessments"]:
        if ref["scope"] != "task-result":
            continue
        report = json.loads(Path(ref["path"]).read_bytes())
        if detailed:
            report["checkpoint_assessment"]["criteria"][0]["id"] = (
                "T1-default-uppercase"
            )
        else:
            for row in report["checkpoint_assessment"]["criteria"]:
                row["state"] = row["parts"][0]["state"] = "unverified"
            report["checkpoint_assessment"].update(state="unverified", due_unverified=2)
            report["checkpoint_result"] = "inconclusive"
        ref.update(write_artifact(repo, "original-whole-negative-" + ref["id"], report))
    result = composition_record(*basis)
    if detailed:
        assert result["composition_error"]["code"] == "not-established"
        assert result["composition_error"]["criterion_counts"] is None
        assert (
            result["composition_error"]["native_values"]["composition-evidence"]
            == "unavailable"
        )
    else:
        current_result = result["composition"]
        assert current_result["status"] == "unresolved"
        assert current_result["native_values"]["composition-unmet"] == 0
        assert current_result["native_values"]["composition-unverified"] == 2
        assert len(current_result["gaps"]) == 6
        assert current_result["new_evaluator_verdict"] is None


@pytest.mark.parametrize("other_source", ["markdown", "json"])
@pytest.mark.parametrize("prepared", [False, True])
@pytest.mark.parametrize(
    "change,recovered",
    [
        ("outside", False),
        ("inside", False),
        ("identity", False),
        ("missing", False),
        ("inside", True),
    ],
)
def test_member_recovery_consumes_retained_other_basis_or_strict_original_pin(
    basis, other_source, prepared, change, recovered
):
    from adaptive_finalization import approved_original_sources

    value, context = member_lifecycle_case(
        basis,
        native=prepared,
        other_source=other_source,
        other_change=change,
        recover_other=recovered,
    )
    repo, assignment, current = basis
    assignment["target"]["applied_source_context"] = context
    if not recovered and (not prepared or change != "outside"):
        with pytest.raises(BundleError):
            commit_handoff(repo, value)
        return
    reader, _context = approved_original_sources(repo, assignment, context)
    assert (
        composition(
            repo,
            assignment,
            current,
            source_reader=reader,
            plan_compositions=value["plan_compositions"],
        )["status"]
        == "ready"
    )
    assert commit_handoff(repo, value)["accepted_target"] == "candidate2"
    if recovered:
        dossier = repo / "dossier.md"
        dossier.write_bytes(dossier.read_bytes() + b" ")
        with pytest.raises(BundleError) as error:
            commit_handoff(repo, value)
        assert error.value.code == "reapproval-required"


@pytest.mark.parametrize("other_source", ["markdown", "json"])
def test_member_recovery_checks_approved_uncaptured_other_postimage(
    basis, other_source
):
    value, context = member_lifecycle_case(
        basis, native=True, other_source=other_source, other_change="outside"
    )
    repo, assignment, _current = basis
    dossier = repo / "dossier.md"
    source = next(
        row
        for row in assignment["work"]["requirement_sources"]
        if row["path"] == dossier.name
    )
    context["proposal"]["targets"][dossier.name] = {
        "before": source["sha256"],
        "after": sha256(dossier.read_bytes()),
    }
    context["approval"]["proposal"] = copy.deepcopy(context["proposal"])
    assignment["target"]["applied_source_context"] = context
    assert commit_handoff(repo, value)["accepted_target"] == "candidate2"
    dossier.write_bytes(dossier.read_bytes() + b" ")
    with pytest.raises(BundleError) as error:
        commit_handoff(repo, value)
    assert error.value.code == "reapproval-required"


@pytest.mark.parametrize("other_source", ["markdown", "json"])
def test_unprepared_member_rechecks_uncaptured_pin_after_product_review(
    basis, monkeypatch, other_source
):
    import adaptive_squad

    value, context = member_lifecycle_case(basis, other_source=other_source)
    repo, assignment, _current = basis
    assignment["target"]["applied_source_context"] = context
    consume = adaptive_squad.artifact
    changed = []

    def late_source_change(repository, reference):
        result = consume(repository, reference)
        if reference == value["acceptance"]["product_review"] and not changed:
            changed.append(True)
            dossier = repo / "dossier.md"
            dossier.write_bytes(
                dossier.read_bytes().replace(
                    b"Original note.", b"Unapproved late note."
                )
            )
        return result

    monkeypatch.setattr(adaptive_squad, "artifact", late_source_change)
    with pytest.raises(BundleError) as error:
        commit_handoff(repo, value)
    assert changed == [True]
    assert error.value.code == "source-drift"


@pytest.mark.parametrize("future_field", ["later", "gates"])
def test_member_reason_requires_actual_assessed_future_applicability(
    basis, future_field
):
    whole_member_case(basis)
    repo, assignment, current = basis
    plans = assignment["target"]["squad"]["compositions"]
    original = copy.deepcopy(assignment["target"]["procedure_plan"]["member_scope"])
    first = current["assessments"][0]
    reason = json.loads(Path(first["path"]).read_bytes())["criteria"][0]["parts"][0][
        "reason"
    ]

    def install(applicable):
        scope = copy.deepcopy(original)
        scope["criteria"][0]["later"] = []
        scope["criteria"][0]["gates"] = []
        if applicable:
            scope["criteria"][0][future_field] = copy.deepcopy(
                original["criteria"][0][future_field]
            )
        assignment["target"]["procedure_plan"]["member_scope"] = copy.deepcopy(scope)
        for basis_value in [current, *plans.values()]:
            basis_value["member_scope"] = copy.deepcopy(scope)
            for ref in basis_value["assessments"]:
                report = json.loads(Path(ref["path"]).read_bytes())
                report["target"]["member_scope"] = copy.deepcopy(scope)
                assert report["criteria"][0]["parts"][0]["reason"] == reason
                ref.update(
                    write_artifact(
                        repo,
                        "future-applicability-"
                        + basis_value["phase"]
                        + "-"
                        + ref["id"],
                        report,
                    )
                )
        for plan in plans.values():
            assert composition(repo, assignment, plan)["status"] == "ready"

    install(True)
    assert composition(*basis)["status"] == "ready"
    install(False)
    with pytest.raises(BundleError) as error:
        composition(*basis)
    assert error.value.code == "not-established"
    install(True)
    assert composition(*basis)["status"] == "ready"
