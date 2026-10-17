"""Mapped native consumers; fixture reports never attest actual independent agents."""

import copy
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))
import adaptive_execution as execution
from adaptive_bundles import BundleError, sha256
from adaptive_suitability import qualify_prepared
from test_adaptive_suitability_unit import Oracle, prepared, report_for


@pytest.fixture
def admitted(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    value = prepared(tmp_path)
    client = Oracle(tmp_path)
    request = qualify_prepared(tmp_path, value, client=client)
    report = report_for(request["target"])
    retained = qualify_prepared(
        tmp_path, value, client=client, assessment=report, retain=True
    )
    qualification = {"assignment": value, "assessment": report}
    observation = {
        "status": {
            "procedure": retained["binding"]["procedure"],
            "session": {"id": str(uuid.uuid4()), "lifecycle": "running", "revision": 5},
            "current": {
                "node": {"graph_node_id": "deliver"},
                "attempt": {"attempt_id": "a"},
            },
            "goal_revision": 1,
        },
        "guidance": {"node": {"graph_node_id": "deliver"}, "readback": []},
        "active_items": [],
        "mutation_templates": [],
    }
    client.health = lambda: copy.deepcopy(observation)
    return tmp_path, qualification, client, observation, retained


def consume(admitted, **kwargs):
    repository, qualification, client, _, _ = admitted
    return execution.execution_context(
        repository,
        roots=["definitions"],
        entrypoint="task-handler",
        qualification=qualification,
        client=client,
        **kwargs,
    )


def test_current_worker_mapping_preserves_original_authority_and_sources(admitted):
    result = consume(admitted)
    assert result["status"] == "dispatch-ready"
    dispatch = result["dispatch"]
    assert dispatch["schema"] == "aquarium.assignment/v2"
    assert dispatch["role"] == "worker"
    assert dispatch["procedure"]["node"] == "deliver"
    assert dispatch["work"] == admitted[1]["assignment"]["work"]
    assert dispatch["authority"] == admitted[1]["assignment"]["authority"]
    assert dispatch["native"]["public_handle"] == "unknown"
    assert dispatch["target"]["active_operation"]["items"][0]["id"] == "documentation"
    assert result["phase_skills"] == []
    assert dispatch["procedure"]["phase_skills"] == result["phase_skills"]


@pytest.mark.parametrize(
    "state,status",
    [
        ("prepared", "prepared-resolved"),
        ("completed", "terminal-resolved"),
        ("cancelled", "terminal-resolved"),
    ],
)
def test_lifecycle_only_never_claims_achievement_or_dispatches(admitted, state, status):
    observation = admitted[3]
    observation["status"]["session"]["lifecycle"] = state
    observation["guidance"] = None
    observation["status"]["current"] = None
    result = consume(admitted)
    assert result["status"] == status
    assert result["dispatch"] is None
    assert "achieved" not in result


def test_running_nonbootstrap_judge_uses_actual_mapping_and_report_only_scope(admitted):
    observation = admitted[3]
    observation["guidance"]["node"]["graph_node_id"] = "assess"
    result = consume(admitted)
    assert result["role"] == "judge"
    assert result["dispatch"]["role"] == "judge"
    assert result["dispatch"]["authority"]["effects"] == []
    assert {row["node"] for row in result["selected_evidence"]} == {"deliver"}
    assert set(admitted[1]["assignment"]["authority"]["excluded"]).issubset(
        result["dispatch"]["authority"]["excluded"]
    )


@pytest.mark.parametrize(
    "node", ["outcome", "accept", "collect-review", "check-review", "closeout"]
)
def test_native_decisions_review_and_finalization_remain_primary_owned(admitted, node):
    admitted[3]["guidance"]["node"]["graph_node_id"] = node
    result = consume(admitted)
    assert result["status"] == "primary-owned"
    assert result["dispatch"] is None
    assert result["authority"]["review"]["route"] == "herdr"


@pytest.mark.parametrize("lifecycle", ["running", "completed"])
def test_verified_commit_survives_finalization_recovery_without_new_dispatch(
    admitted, lifecycle
):
    qualification, observation = admitted[1], admitted[3]
    qualification["pending_operations"] = [
        {"kind": "verified-commit", "commit": "a" * 40, "remaining": "finalization"}
    ]
    observation["status"]["session"]["lifecycle"] = lifecycle
    observation["guidance"]["node"]["graph_node_id"] = "closeout"
    expected = copy.deepcopy(qualification["pending_operations"])
    recovered = consume(admitted)
    assert recovered["dispatch"] is None
    assert recovered["pending_operations"] == expected
    assert recovered["procedure"]["session"] == observation["status"]["session"]
    recovered["pending_operations"][0]["commit"] = "b" * 40
    assert qualification["pending_operations"] == expected
    assert consume(admitted)["pending_operations"] == expected


@pytest.mark.parametrize(
    "change,code",
    [
        ("session", "session-conflict"),
        ("node", "missing-topology"),
        ("missing", "missing-session"),
        ("binding", "corrupt"),
    ],
)
def test_recovery_stops_without_guessed_work_or_replacement(admitted, change, code):
    if change == "session":
        kwargs = {"session": str(uuid.uuid4())}
    else:
        kwargs = {}
    if change == "node":
        admitted[3]["guidance"]["node"]["graph_node_id"] = "missing-node"
    if change == "missing":
        admitted[2].health = lambda: None
    if change == "binding":
        (Path(admitted[4]["retention"]["path"]) / "binding.json").unlink()
    with pytest.raises(BundleError) as error:
        consume(admitted, **kwargs)
    assert error.value.code == code


def test_unchanged_running_basis_retrieves_same_current_assessment_without_new_assignment(
    admitted,
):
    result = consume(admitted)
    assert result["qualification"]["status"] == "qualified"
    admitted[1].pop("assessment")
    with pytest.raises(BundleError) as error:
        consume(admitted)
    assert error.value.code == "reassessment-required"
    assert "assignment" not in error.value.details


@pytest.mark.parametrize(
    "entrypoint", ["new-feature", "new-project", "refactor", "war-room"]
)
def test_other_family_activation_is_not_implied(admitted, entrypoint):
    with pytest.raises(BundleError) as error:
        execution.execution_context(
            admitted[0],
            roots=["definitions"],
            entrypoint=entrypoint,
            qualification=admitted[1],
            client=admitted[2],
        )
    assert error.value.code == "not-established"


def test_approved_due_phase_owners_can_combine_documentation_and_verification():
    document = {
        "graph": {"nodes": [{"id": "write-doc", "use": "writer"}]},
        "node_definitions": {"writer": {}},
    }
    binding = {"family": "task", "nodes": {"write-doc": {}}}
    assignment = {
        "target": {
            "procedure_plan": {
                "phase_skills": {"write-doc": ["task-document", "task-verify"]}
            }
        }
    }
    assert execution.phase_skills(document, binding, assignment, "write-doc") == [
        "task-document",
        "task-verify",
    ]
    assert (
        execution.phase_skills(document, {"family": "goal"}, assignment, "write-doc")
        == []
    )
    assignment["target"]["procedure_plan"]["phase_skills"]["write-doc"] = [
        "invented-skill"
    ]
    with pytest.raises(BundleError) as error:
        execution.phase_skills(document, binding, assignment, "write-doc")
    assert error.value.code == "invalid-input"


def handoff(tmp_path):
    session = str(uuid.uuid4())
    path = Path(".podway/runtime/handoffs") / session / "plan.md"
    (tmp_path / path).parent.mkdir(parents=True)
    (tmp_path / path).write_text("# Exact approved plan\n")
    artifact = {
        "location": str(path),
        "location_type": "path",
        "media_type": "text/markdown",
        "sha256_digest": sha256((tmp_path / path).read_bytes()),
        "size_bytes": (tmp_path / path).stat().st_size,
    }
    from adaptive_definitions import canonical_json
    from test_adaptive_qualification_unit import adaptive, bound

    document, mapping, context = adaptive()
    attachment = {
        "type": "action",
        "title": "Record the approved plan",
        "intent": "Record exact approved execution context only",
        "items": [
            {
                "id": "plan-link",
                "type": "artifact",
                "prompt": "Attach approved plan",
                "required": False,
                "allowed_media_types": ["text/markdown"],
            }
        ],
    }
    document["node_definitions"]["record"] = attachment
    document["graph"]["nodes"].insert(
        0, {"id": "approved-input", "use": "record", "next": document["graph"]["entry"]}
    )
    document["graph"]["entry"] = "approved-input"
    next(
        row for row in document["graph"]["nodes"] if row["id"] == "deliver"
    ).setdefault("evidence_from", []).append(
        {"node": "approved-input", "required": False, "items": ["plan-link"]}
    )
    mapping["nodes"]["approved-input"] = {
        "role": "orchestrator",
        "kind": "action",
        "effects": [],
        "capabilities": [],
    }
    context["operation_contracts"][sha256(canonical_json(attachment))] = {
        "roles": ["orchestrator"],
        "effect": "control",
        "basis": "Exact approved context recording without product work",
    }
    binding = bound(document, mapping)
    assignment = {
        "target": {
            "procedure_plan": {
                "plan_handoff": {
                    "attachment": {"node": "approved-input", "item": "plan-link"},
                    "first_work": ["deliver"],
                }
            },
            "plan_handoff_runtime": {
                "initial_session_id": session,
                "mode": "plan-handoff",
            },
        }
    }
    assignment["authority"] = {"review": {"route": "herdr"}}
    assignment["target"]["qualification_context"] = context
    observation = {
        "status": {
            "session": {"id": session},
            "current": {
                "attempt": {"attempt_id": "native-plan-attempt", "attempt_number": 1}
            },
            "counters": [{"graph_node_id": "approved-input", "attempt_count": 1}],
        },
        "guidance": {"node": {"graph_node_id": "approved-input"}},
        "active_items": [{"item_id": "plan-link", "value": artifact}],
    }
    return document, binding, assignment, observation, artifact, path


def test_mapped_handoff_attachment_binds_exact_local_bytes(tmp_path):
    doc, binding, assignment, observation, artifact, path = handoff(tmp_path)
    result = execution.handoff_context(
        tmp_path, doc, binding, assignment, observation, None
    )
    assert result["verified"] is True
    assert result["artifact"] == artifact
    (tmp_path / path).write_text("changed")
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "source-drift"


def test_mapped_handoff_requires_attachment_and_selected_work_connection(tmp_path):
    doc, binding, assignment, observation, _, _ = handoff(tmp_path)
    observation["active_items"][0]["value"] = None
    assert (
        execution.handoff_context(
            tmp_path, doc, binding, assignment, observation, None
        )["status"]
        == "attachment-required"
    )
    observation["guidance"]["node"]["graph_node_id"] = "deliver"
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "missing-topology"


def test_handoff_rejects_a_later_worker_before_the_actual_work_frontier(tmp_path):
    from adaptive_definitions import canonical_json

    doc, binding, assignment, observation, _, _ = handoff(tmp_path)
    body = copy.deepcopy(doc["node_definitions"]["deliver"])
    doc["node_definitions"]["later"] = body
    doc["graph"]["nodes"].append(
        {"id": "later", "use": "later", "next": "collect-review"}
    )
    next(row for row in doc["graph"]["nodes"] if row["id"] == "deliver")["next"] = (
        "later"
    )
    binding["nodes"]["later"] = copy.deepcopy(binding["nodes"]["deliver"])
    assignment["target"]["procedure_plan"]["plan_handoff"]["first_work"] = ["later"]
    # Both scopes remain covered by the same due final assessment.
    binding["obligations"]["original-goal"]["producers"].append(
        {"node": "later", "item": "documentation"}
    )
    next(row for row in doc["graph"]["nodes"] if row["id"] == "assess")[
        "evidence_from"
    ].append({"node": "later", "required": True, "items": ["documentation"]})
    binding["procedure"]["source_sha256"] = sha256(canonical_json(doc))
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "incompatible"
    assert error.value.details["first_work"] == ["deliver"]


def test_handoff_first_work_stop_and_resume_verify_selected_exact_artifact(tmp_path):
    from unittest.mock import Mock

    doc, binding, assignment, observation, artifact, _ = handoff(tmp_path)
    observation.update(
        status=observation["status"],
        mutation_templates=[{"preconditions": {"workspace_uuid": str(uuid.uuid4())}}],
    )
    observation["guidance"] = {
        "node": {"graph_node_id": "deliver"},
        "readback": [
            {
                "source_graph_node_id": "approved-input",
                "source_attempt_id": "native-plan-attempt",
                "source_attempt_number": 1,
                "state": "resolved",
                "items": [
                    {"item_id": "plan-link", "value_digest": "exact-native-digest"}
                ],
            }
        ],
    }
    client = Mock()
    client.read.return_value = {
        "truncated": False,
        "next_page_token": None,
        "value_digest": "exact-native-digest",
        "page": {"data": artifact},
    }
    stopped = execution.handoff_context(
        tmp_path, doc, binding, assignment, observation, client
    )
    assert stopped["status"] == "stop-before-work"
    assert stopped["verified"] is True
    assignment["target"]["plan_handoff_runtime"]["mode"] = "resume"
    resumed = execution.handoff_context(
        tmp_path, doc, binding, assignment, observation, client
    )
    assert resumed["status"] == "verified"
    client.read.return_value["value_digest"] = "stale-native-digest"
    with pytest.raises(BundleError) as error:
        execution.handoff_context(
            tmp_path, doc, binding, assignment, observation, client
        )
    assert error.value.code == "not-established"


def test_guarded_alternative_first_work_frontiers_remain_supported(tmp_path):
    from adaptive_definitions import canonical_json

    doc, binding, assignment, observation, _, _ = handoff(tmp_path)
    doc["node_definitions"]["choose"] = {
        "type": "decision",
        "title": "Choose actual delivery",
        "objective": "Use the approved work variant",
        "prompt": "Which actual variant is due?",
        "options": [
            {
                "id": "primary",
                "label": "Primary",
                "criteria": "Primary original variant applies",
            },
            {
                "id": "alternative",
                "label": "Alternative",
                "criteria": "Alternative original variant applies",
            },
        ],
        "reason": {
            "required": True,
            "prompt": "Reference approved actual applicability",
        },
    }
    doc["node_definitions"]["alternative"] = copy.deepcopy(
        doc["node_definitions"]["deliver"]
    )
    next(row for row in doc["graph"]["nodes"] if row["id"] == "approved-input")[
        "next"
    ] = "choose"
    doc["graph"]["nodes"].extend(
        [
            {
                "id": "choose",
                "use": "choose",
                "routes": {
                    "primary": {"to": "deliver", "effect": "advance"},
                    "alternative": {"to": "alternative", "effect": "advance"},
                },
            },
            {"id": "alternative", "use": "alternative", "next": "collect-review"},
        ]
    )
    binding["nodes"]["choose"] = {
        "kind": "decision",
        "role": "orchestrator",
        "effects": [],
        "capabilities": [],
    }
    binding["nodes"]["alternative"] = copy.deepcopy(binding["nodes"]["deliver"])
    binding["nodes"]["alternative"]["role"] = "orchestrator"
    assess = next(row for row in doc["graph"]["nodes"] if row["id"] == "assess")
    assess["evidence_from"][0]["required"] = False
    assess["evidence_from"].append(
        {"node": "alternative", "items": ["documentation"], "required": False}
    )
    binding["obligations"]["original-goal"]["producers"].append(
        {"node": "alternative", "item": "documentation"}
    )
    binding["procedure"]["source_sha256"] = sha256(canonical_json(doc))
    assignment["target"]["procedure_plan"]["plan_handoff"]["first_work"] = [
        "deliver",
        "alternative",
    ]
    result = execution.handoff_context(
        tmp_path, doc, binding, assignment, observation, None
    )
    assert result["verified"] is True


@pytest.mark.parametrize("resume", [False, True])
def test_selected_inspector_forwards_actual_adaptive_binding_context(
    admitted, monkeypatch, resume
):
    import adaptive_admission
    from test_adaptive_bundles_unit import inspector

    repository, qualification, client, observation, retained = admitted
    tool = {
        "executable": "synthetic-oracle",
        "runtime_readiness": {
            "state": "ready",
            "session_procedure": observation["status"]["procedure"] if resume else None,
            "session_lifecycle": "running" if resume else None,
        },
        "managed_procedures": [],
        "readiness_status": "degraded",
    }
    monkeypatch.setattr(inspector, "inspect_podway", lambda *args, **kwargs: tool)
    monkeypatch.setattr(
        adaptive_admission, "NativeClient", lambda *args, **kwargs: client
    )
    path = Path(retained["retention"]["path"])
    result = inspector.inspect_selected_podway(
        repository,
        30,
        source=path / "procedure.yaml",
        binding_path=path / "binding.json",
        roots=["definitions"],
        entrypoint="task-handler",
        route="herdr",
        qualification=qualification,
        resume=resume,
    )
    assert result["selected_procedure"]["status"] == "ready"
    assert (
        result["selected_procedure"]["binding"]["procedure"]
        == retained["binding"]["procedure"]
    )
    assert result["selected_procedure"]["retention_status"] == "resolved"
    result = inspector.inspect_selected_podway(
        repository,
        30,
        source=path / "procedure.yaml",
        binding_path=path / "binding.json",
        roots=["definitions"],
        entrypoint="task-handler",
        route="waived",
        qualification=qualification,
        resume=resume,
    )
    assert result["selected_procedure"]["status"] == "route-unavailable"


def test_public_context_bad_ordinary_shape_is_typed_without_native_work(tmp_path):
    import json

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    path = tmp_path / "context.json"
    path.write_text(json.dumps({"assignment": 5}))
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "plugins/aquarium/shared/manage_adaptive_procedure.py"),
            "context",
            "--repository",
            str(tmp_path),
            "--root",
            "definitions",
            "--entrypoint",
            "task-handler",
            "--qualification",
            str(path),
            "--podway",
            "/missing/native-not-called",
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == b""


def test_namespaced_reference_phase_preserves_its_original_leaf_owner():
    from adaptive_composition import expand
    from test_adaptive_qualification_unit import known

    document, binding = known("task")
    expanded, mapping, _, _ = expand(document, binding, "member", {})
    actual = next(
        row["id"]
        for row in expanded["graph"]["nodes"]
        if row["use"] == "member-implementation-record"
    )
    assert execution.phase_skills(
        expanded, mapping, {"target": {"procedure_plan": {}}}, actual
    ) == ["task-implement"]


@pytest.mark.parametrize(
    "placement,skill",
    [
        ("record-plan", "task-plan"),
        ("implement", "task-implement"),
        ("refine", "task-refine"),
        ("verify", "task-verify"),
        ("document", "task-document"),
        ("review", "task-review"),
    ],
)
def test_typed_item_alias_retains_known_task_phase_owner(placement, skill):
    from adaptive_composition import expand
    from adaptive_qualification import qualify
    from test_adaptive_qualification_unit import bound, known

    document, binding = known("task")
    use = next(
        row["use"] for row in document["graph"]["nodes"] if row["id"] == placement
    )
    item = document["node_definitions"][use]["items"][0]["id"]
    aliases = {
        row["id"]: {item: "current-" + item}
        for row in document["graph"]["nodes"]
        if row["use"] == use
    }
    expanded, mapping, _, _ = expand(
        document,
        {key: value for key, value in binding.items() if key != "procedure"},
        "member",
        aliases,
    )
    expanded["id"] = "aquarium-adapt-task-phase-alias"
    expanded["version"] = "1"
    mapping = bound(expanded, mapping)
    if placement == "record-plan":
        assert qualify(expanded, mapping)["status"] == "compatible"
    assert execution.phase_skills(
        expanded, mapping, {"target": {"procedure_plan": {}}}, "member-" + placement
    ) == [skill]


def test_selected_inspector_lazy_qualification_works_in_a_fresh_interpreter(admitted):
    import json

    repository, qualification, _, _, retained = admitted
    path = repository / "ordinary-context.json"
    path.write_text(json.dumps(qualification))
    program = r"""
import importlib.util,json,sys
from pathlib import Path
shared,inspector_path,repository,context_path,source,binding=sys.argv[1:]
sys.path.insert(0,shared)
import adaptive_admission
from adaptive_bundles import read_regular,sha256
from adaptive_definitions import canonical_json
import yaml
class Oracle:
 def preview(self,path):
  doc=yaml.safe_load(Path(path).read_bytes())
  return {"procedure_id":doc["id"],"procedure_version":doc["version"],"procedure_digest":sha256(canonical_json(doc))}
 def identity(self,path):
  value=self.preview(path)
  return tuple(value[key] for key in ("procedure_id","procedure_version","procedure_digest"))
client=Oracle()
adaptive_admission.NativeClient=lambda *args,**kwargs:client
sys.path.remove(shared)
spec=importlib.util.spec_from_file_location("standalone_inspector",inspector_path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.inspect_podway=lambda *args,**kwargs:{"executable":"synthetic","runtime_readiness":{"state":"ready","session_procedure":None,"session_lifecycle":None},"managed_procedures":[],"readiness_status":"degraded"}
value=module.inspect_selected_podway(Path(repository),30,source=source,binding_path=binding,roots=["definitions"],entrypoint="task-handler",route="herdr",qualification=json.loads(Path(context_path).read_text()))
print(json.dumps(value))
"""
    bundle = Path(retained["retention"]["path"])
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            program,
            str(ROOT / "plugins/aquarium/shared"),
            str(ROOT / "plugins/aquarium/skills/dev-setup/scripts/inspect_tools.py"),
            str(repository),
            str(path),
            str(bundle / "procedure.yaml"),
            str(bundle / "binding.json"),
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["selected_procedure"]["status"] == "ready"
    assert result.stderr == b""


@pytest.mark.parametrize(
    "field,value", [("node", []), ("item", {}), ("boundary", [{}])]
)
def test_mapped_handoff_consumed_endpoint_shapes_are_typed(tmp_path, field, value):
    doc, binding, assignment, observation, _, _ = handoff(tmp_path)
    mapping = assignment["target"]["procedure_plan"]["plan_handoff"]
    if field == "boundary":
        mapping["first_work"] = value
    else:
        mapping["attachment"][field] = value
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "invalid-input"


def test_later_worker_resume_revalidates_existing_plan_metadata(tmp_path):
    from adaptive_definitions import canonical_json

    doc, binding, assignment, observation, artifact, path = handoff(tmp_path)
    doc["node_definitions"]["later"] = copy.deepcopy(doc["node_definitions"]["deliver"])
    doc["graph"]["nodes"].append(
        {"id": "later", "use": "later", "next": "collect-review"}
    )
    next(row for row in doc["graph"]["nodes"] if row["id"] == "deliver")["next"] = (
        "later"
    )
    binding["nodes"]["later"] = copy.deepcopy(binding["nodes"]["deliver"])
    binding["obligations"]["original-goal"]["producers"].append(
        {"node": "later", "item": "documentation"}
    )
    next(row for row in doc["graph"]["nodes"] if row["id"] == "assess")[
        "evidence_from"
    ].append({"node": "later", "required": True, "items": ["documentation"]})
    binding["procedure"]["source_sha256"] = sha256(canonical_json(doc))
    observation["guidance"]["node"]["graph_node_id"] = "later"
    runtime = assignment["target"]["plan_handoff_runtime"]
    runtime["mode"] = "resume"
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "not-established"
    runtime["artifact"] = artifact
    runtime["artifact_reference"] = {
        "session_id": observation["status"]["session"]["id"],
        "node": "approved-input",
        "attempt_id": "native-plan-attempt",
        "attempt_number": 1,
    }
    assert (
        execution.handoff_context(
            tmp_path, doc, binding, assignment, observation, None
        )["verified"]
        is True
    )
    observation["status"]["counters"][0]["attempt_count"] = 2
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "not-established"
    observation["status"]["counters"][0]["attempt_count"] = 1
    (tmp_path / path).write_text("changed plan after handoff")
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "source-drift"


def test_later_judge_resume_revalidates_existing_plan_metadata(tmp_path):
    doc, binding, assignment, observation, artifact, path = handoff(tmp_path)
    observation["guidance"]["node"]["graph_node_id"] = "assess"
    runtime = assignment["target"]["plan_handoff_runtime"]
    runtime["mode"] = "resume"
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "not-established"
    runtime["artifact"] = artifact
    runtime["artifact_reference"] = {
        "session_id": observation["status"]["session"]["id"],
        "node": "approved-input",
        "attempt_id": "native-plan-attempt",
        "attempt_number": 1,
    }
    assert execution.handoff_context(
        tmp_path, doc, binding, assignment, observation, None
    )["verified"]
    (tmp_path / path).write_text("changed plan before assessment")
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "source-drift"


@pytest.mark.parametrize("node", ["audit", "remediate"])
def test_internal_validation_handoff_verifies_actual_selected_evidence(tmp_path, node):
    from adaptive_qualification import qualify
    from test_adaptive_qualification_unit import known

    _, _, assignment, observation, _artifact, path = handoff(tmp_path)
    doc, binding = known("validation")
    mapping = assignment["target"]["procedure_plan"]["plan_handoff"]
    mapping["attachment"] = {
        "node": "capture-baseline",
        "item": "plan-handoff-artifact",
    }
    mapping["first_work"] = ["audit", "remediate"]
    assignment["target"]["qualification_context"] = {"workflow_owner": "epic-handler"}
    proof = qualify(
        doc,
        binding,
        context={"review": {"route": "herdr"}, "workflow_owner": "epic-handler"},
        execution_info=True,
    )
    assert proof["status"] == "compatible"
    assert set(proof["execution"]["first_work"]) == {"audit", "remediate"}
    observation["status"]["counters"][0]["graph_node_id"] = "capture-baseline"
    observation["guidance"]["node"]["graph_node_id"] = "capture-baseline"
    observation["active_items"][0]["item_id"] = "plan-handoff-artifact"
    baseline = execution.handoff_context(
        tmp_path, doc, binding, assignment, observation, None
    )
    assert baseline["verified"]
    placement = next(row for row in doc["graph"]["nodes"] if row["id"] == node)
    assert all(
        row["node"] != "capture-baseline"
        or "plan-handoff-artifact" not in row.get("items", [])
        for row in placement.get("evidence_from", [])
    )
    observation["guidance"] = {
        "node": {"graph_node_id": node},
        "readback": [
            {
                "source_graph_node_id": row["node"],
                "state": "resolved",
                "items": [{"item_id": item} for item in row["items"]],
            }
            for row in placement.get("evidence_from", [])
        ],
    }
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "not-established"
    runtime = assignment["target"]["plan_handoff_runtime"]
    runtime["artifact"] = baseline["artifact"]
    runtime["artifact_reference"] = baseline["artifact_reference"]
    assert (
        execution.handoff_context(
            tmp_path, doc, binding, assignment, observation, None
        )["status"]
        == "stop-before-work"
    )
    runtime["mode"] = "resume"
    assert execution.handoff_context(
        tmp_path, doc, binding, assignment, observation, None
    )["verified"]
    observation["status"]["counters"][0]["attempt_count"] = 2
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "not-established"
    observation["status"]["counters"][0]["attempt_count"] = 1
    (tmp_path / path).write_text("changed epic plan before validation work")
    with pytest.raises(BundleError) as error:
        execution.handoff_context(tmp_path, doc, binding, assignment, observation, None)
    assert error.value.code == "source-drift"


def test_foreign_document_alias_does_not_inherit_task_leaf_ownership():
    from adaptive_composition import expand
    from test_adaptive_qualification_unit import known

    document, binding = known("war-room")
    use = next(
        row["use"] for row in document["graph"]["nodes"] if row["id"] == "document"
    )
    item = document["node_definitions"][use]["items"][0]["id"]
    expanded, mapping, _, _ = expand(
        document, binding, "diagnosis", {"document": {item: "current-" + item}}
    )
    mapping["family"] = "task"
    assignment = {"target": {"procedure_plan": {}}}
    assert (
        execution.phase_skills(expanded, mapping, assignment, "diagnosis-document")
        == []
    )
    assignment["target"]["procedure_plan"]["phase_skills"] = {
        "diagnosis-document": ["task-document"]
    }
    assert execution.phase_skills(
        expanded, mapping, assignment, "diagnosis-document"
    ) == ["task-document"]


def test_frontier_resource_limit_reports_its_actual_consumer_location():
    from adaptive_qualification import qualify
    from test_adaptive_qualification_unit import known

    document, binding = known("validation")
    context = {"review": {"route": "herdr"}, "workflow_owner": "epic-validator"}
    baseline = qualify(document, binding, context=context)
    assert baseline["status"] == "compatible"
    result = qualify(
        document,
        binding,
        context=context,
        execution_info=True,
        node_budget=baseline["analysis"]["symbolic_nodes"],
    )
    assert result["status"] == "not-established"
    resource = [
        row for row in result["issues"] if row["property"] == "analysis-resource"
    ]
    assert resource and resource[0]["during"] in {
        "first-work-frontier",
        "after-first-work",
    }
    assert resource[0]["location"] in binding["nodes"]


def test_performance_work_dispatches_actual_measurement_and_conditional_producers(
    tmp_path,
):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    value = prepared(tmp_path, performance=True)
    client = Oracle(tmp_path)
    request = qualify_prepared(tmp_path, value, client=client)
    assessment = report_for(request["target"])
    retained = qualify_prepared(
        tmp_path, value, client=client, assessment=assessment, retain=True
    )
    observation = {
        "status": {
            "procedure": retained["binding"]["procedure"],
            "session": {"id": str(uuid.uuid4()), "lifecycle": "running"},
            "current": {"attempt": {"attempt_id": "native-measure"}},
        },
        "guidance": {"node": {"graph_node_id": "measure"}},
        "active_items": [],
        "mutation_templates": [],
    }
    client.health = lambda: copy.deepcopy(observation)
    q = {"assignment": value, "assessment": assessment}
    result = execution.execution_context(
        tmp_path,
        roots=["definitions"],
        entrypoint="task-handler",
        qualification=q,
        client=client,
    )
    assert (
        result["role"] == "worker"
        and result["dispatch"]["target"]["active_operation"]["items"][0]["type"]
        == "integer"
    )
    observation["guidance"]["node"]["graph_node_id"] = "classify"
    decision = execution.execution_context(
        tmp_path,
        roots=["definitions"],
        entrypoint="task-handler",
        qualification=q,
        client=client,
    )
    assert decision["status"] == "primary-owned" and decision["dispatch"] is None
    assert {row["node"] for row in decision["selected_evidence"]} == {"measure"}


def test_new_selected_forwarding_rejects_malformed_raw_review_before_native_discovery(
    tmp_path, monkeypatch
):
    from test_adaptive_bundles_unit import inspector
    from test_adaptive_suitability_unit import assignment

    value = assignment(tmp_path)
    value["authority"]["review"] = []

    def unexpected(*args, **kwargs):
        raise AssertionError(
            "Invalid ordinary context must not invoke native discovery"
        )

    monkeypatch.setattr(inspector, "inspect_podway", unexpected)
    result = inspector.inspect_selected_podway(
        tmp_path,
        30,
        source="unused",
        roots=["definitions"],
        entrypoint="task-handler",
        route="herdr",
        qualification={"assignment": value},
    )
    assert result["selected_procedure"]["status"] == "invalid-input"
    assert result["tools"] == {}


@pytest.mark.parametrize("kind", ["known", "new", "established-reuse"])
def test_runtime_source_metadata_preserves_original_suitability(tmp_path, kind):
    import json

    from adaptive_admission import resume_selected
    from adaptive_preparation import prepare
    from test_adaptive_preparation_unit import known_candidate
    from test_adaptive_suitability_unit import assignment, existing_adaptive

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    client = Oracle(tmp_path)
    if kind == "new":
        value = prepared(tmp_path)
    elif kind == "known":
        value = assignment(tmp_path, mode="prepare")
        known_candidate(tmp_path, value)
        value["target"]["procedure_plan"]["drafts"] = []
        value = prepare(tmp_path, value, client=client, bootstrap=True)["assignment"]
    else:
        value, _, _ = existing_adaptive(tmp_path)
        value = prepare(tmp_path, value, client=client, bootstrap=True)["assignment"]
    request = qualify_prepared(tmp_path, value, client=client)
    assessment = report_for(request["target"]) if kind == "new" else None
    retained = qualify_prepared(
        tmp_path, value, client=client, assessment=assessment, retain=True
    )
    qualification = {"assignment": value, "assessment": assessment}
    original = copy.deepcopy(qualification)
    source = tmp_path / "requirements.json"
    data = json.loads(source.read_text())
    data["lifecycle"] = "In Review"
    source.write_text(json.dumps(data))
    resumed = resume_selected(
        tmp_path,
        ["definitions"],
        retained["binding"]["procedure"],
        client=client,
        qualification=qualification,
    )
    assert resumed["qualification"]["status"] in {"qualified", "qualified-known"}
    assert "assignment" not in resumed["qualification"]
    assert qualification == original
    with pytest.raises(BundleError) as error:
        qualify_prepared(tmp_path, value, client=client, assessment=assessment)
    assert error.value.code == "source-drift"
    data["criteria"][0]["text"] = "A materially different original requirement."
    source.write_text(json.dumps(data))
    with pytest.raises(BundleError) as error:
        resume_selected(
            tmp_path,
            ["definitions"],
            retained["binding"]["procedure"],
            client=client,
            qualification=qualification,
        )
    assert error.value.code == "reassessment-required"


def test_current_consumer_recovers_after_nonaffecting_requirement_edit(admitted):
    import json

    source = admitted[0] / "requirements.json"
    data = json.loads(source.read_text())
    data["lifecycle"] = "In Review"
    source.write_text(json.dumps(data))
    original = copy.deepcopy(admitted[1])
    assert consume(admitted)["status"] == "dispatch-ready"
    assert admitted[1] == original


@pytest.mark.parametrize(
    "change", ["part", "source", "adopted", "authority", "plan", "review"]
)
def test_runtime_currency_does_not_mask_relevant_changes(admitted, change):
    import json

    repository, qualification = admitted[:2]
    value = qualification["assignment"]
    source = repository / "requirements.json"
    if change == "part":
        data = json.loads(source.read_text())
        data["criteria"][0]["parts"][0]["text"] = "Different compound obligation."
        source.write_text(json.dumps(data))
    elif change == "source":
        (repository / "different.json").write_bytes(source.read_bytes())
        value["work"]["requirement_sources"][0]["path"] = "different.json"
    elif change == "adopted":
        value["work"]["requirement_sources"][0]["role"] = "adopted-customization"
    elif change == "authority":
        value["authority"]["allowed"].append("A different granted effect.")
    elif change == "plan":
        value["target"]["procedure_plan"]["customization_disposition"] = (
            "A different adopted customization preservation basis."
        )
    else:
        for owner in (value["authority"], value["target"]["procedure_plan"]):
            owner["review"]["transmission"].append("different approved source")
    with pytest.raises(BundleError) as error:
        consume(admitted)
    assert error.value.code == "reassessment-required"


def test_runtime_markdown_currency_uses_actual_extraction_boundaries(tmp_path):
    from adaptive_preparation import requirements
    from adaptive_suitability import current_basis
    from test_adaptive_suitability_unit import assignment

    value = assignment(tmp_path)
    path = tmp_path / "roadmap.md"
    path.write_text(
        "# Requirements\nPreserve every original obligation.\n# Status\nPlanned\n"
    )
    value["work"]["requirement_sources"] = [
        {
            "id": "original",
            "path": path.name,
            "sha256": sha256(path.read_bytes()),
            "section": "Requirements",
        }
    ]
    value["success_criteria"] = ["original:whole"]
    value["target"]["prepared_definition"] = {
        "coverage_plan": {"criteria": requirements(tmp_path, value)}
    }
    original = current_basis(tmp_path, value)
    path.write_text(path.read_text().replace("Planned", "In Review"))
    assert current_basis(tmp_path, value, in_session=True) == original
    with pytest.raises(BundleError) as error:
        current_basis(tmp_path, value)
    assert error.value.code == "source-drift"
    path.write_text(
        path.read_text().replace("original obligation", "different obligation")
    )
    with pytest.raises(BundleError) as error:
        current_basis(tmp_path, value, in_session=True)
    assert error.value.code == "reassessment-required"
