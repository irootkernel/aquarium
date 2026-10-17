"""Exact ordinary suitability evidence and source-only preparation boundaries."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugins/aquarium/shared"))
from adaptive_admission import resume_selected, retain_selected, selected_source
from adaptive_bundles import BundleError
from adaptive_preparation import prepare
from adaptive_qualification import qualify
from adaptive_suitability import (
    add_bootstrap,
    assess_current,
    qualify_prepared,
)
from test_adaptive_preparation_unit import Oracle as PreparationOracle
from test_adaptive_preparation_unit import assignment as preparation_assignment
from test_adaptive_preparation_unit import known_candidate
from test_adaptive_qualification_unit import adaptive, bound


def assignment(repository, **options):
    value = preparation_assignment(repository, **options)
    for owner in (value["authority"], value["target"]["procedure_plan"]):
        owner["review"]["route"] = "herdr"
    return value


class Oracle(PreparationOracle):
    """Synthetic validation identity, never actual released-native evidence."""

    def _read(self, argv, command, schemas):
        result = super()._read(argv, command, schemas)
        if command == "procedure.validate":
            result["digest"] = self.preview(self.repository / argv[-1])[
                "procedure_digest"
            ]
        return result


@pytest.fixture
def repository(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def prepared(
    repository,
    performance=False,
    *,
    customization_disposition=None,
    privileged=False,
    criterion_maximum=None,
):
    value = assignment(repository, mode="prepare", performance=performance)
    if customization_disposition is not None:
        value["target"]["procedure_plan"]["customization_disposition"] = (
            customization_disposition
        )
    document, binding, context = adaptive(performance=performance)
    if criterion_maximum is not None:
        for item in document["node_definitions"]["assess"]["items"]:
            if item["id"] in {"judge-unmet-criteria", "judge-unverified-criteria"}:
                item["maximum"] = criterion_maximum
    if privileged:
        document["node_definitions"]["sketch-plan"] = {
            "type": "action",
            "title": "Sketch the actual document plan",
            "intent": "Produce planning material only, before approved product work.",
            "items": [
                {
                    "id": "plan-summary",
                    "type": "text",
                    "prompt": "Explain the proposed document plan",
                    "required": True,
                    "min_length": 1,
                    "max_length": 2000,
                },
                {
                    "id": "plan-artifact",
                    "type": "artifact",
                    "prompt": "Attach the approved plan",
                    "required": True,
                    "allowed_media_types": ["text/markdown"],
                },
            ],
        }
        document["graph"]["nodes"].insert(
            0,
            {
                "id": "sketch-plan",
                "use": "sketch-plan",
                "next": document["graph"]["entry"],
            },
        )
        document["graph"]["entry"] = "sketch-plan"
        next(node for node in document["graph"]["nodes"] if node["id"] == "deliver")[
            "evidence_from"
        ] = [
            {
                "node": "sketch-plan",
                "required": True,
                "items": ["plan-summary", "plan-artifact"],
            }
        ]
        next(node for node in document["graph"]["nodes"] if node["id"] == "assess")[
            "evidence_from"
        ].append(
            {
                "node": "sketch-plan",
                "required": True,
                "items": ["plan-summary", "plan-artifact"],
            }
        )
        binding["obligations"]["preparation-plan"] = copy.deepcopy(
            binding["obligations"]["original-goal"]
        )
        binding["obligations"]["preparation-plan"]["producers"] = [
            {"node": "sketch-plan", "item": "plan-summary"}
        ]
        binding["nodes"]["sketch-plan"] = {
            "kind": "action",
            "role": "worker",
            "effects": ["work"],
            "capabilities": [],
        }
        from adaptive_bundles import sha256
        from adaptive_definitions import canonical_json

        binding.setdefault("semantic_contracts", {})[
            sha256(canonical_json(document["node_definitions"]["sketch-plan"]))
        ] = {
            "roles": ["worker"],
            "effect": "work",
            "basis": "Work-specific planning-only output, independently assessed with exact original scope.",
            "output_scopes": {"plan-summary": "task-plan"},
        }
        value["target"]["procedure_plan"]["plan_handoff"] = {
            "attachment": {"node": "sketch-plan", "item": "plan-artifact"},
            "first_work": ["deliver"],
        }
    for owner in (value["authority"], value["target"]["procedure_plan"]):
        owner["review"]["route"] = "herdr"
    mapping = {key: val for key, val in binding.items() if key != "procedure"}
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft.update(document=document, mapping=mapping)
    for row in draft["coverage"]:
        row["obligation"] = "original-goal"
    value["target"]["qualification_context"] = context
    result = prepare(repository, value, client=Oracle(repository), bootstrap=True)
    return result["assignment"]


def report_for(target):
    return {
        "schema": "aquarium.judge-assessment/v2",
        "work": target["basis"]["work"],
        "target": {"procedure_suitability": copy.deepcopy(target)},
        "authority": {"allowed": ["Independent report only"], "excluded": ["Mutation"]},
        "procedure": None,
        "native": {"harness": "Codex", "public_handle": "synthetic-judge"},
        "assignment": "synthetic ordinary Judge assignment",
        "checkpoint": "pre-start-procedure-suitability",
        "evidence": ["synthetic original-source observation"],
        "gaps": [],
        "applicability": {
            "status": "pass",
            "basis": "Exact current candidate and original sources",
        },
        "criteria": [
            {
                "id": identifier,
                "status": "met",
                "evidence": [criterion["source"]],
                "parts": [
                    {
                        "id": part["id"],
                        "status": "met",
                        "evidence": [criterion["source"]],
                    }
                    for part in criterion["parts"]
                ],
            }
            for identifier, criterion in target["basis"]["criteria"].items()
        ],
        "verdict": "pass",
    }


def prove_operations(report, binding):
    report["applicability"]["operation_contracts"] = {
        digest: {
            "contract": copy.deepcopy(contract),
            "evidence": [
                "Synthetic exact-operation semantic assessment; no actual agent execution claim."
            ],
        }
        for digest, contract in binding.get("semantic_contracts", {}).items()
        if contract.get("discriminators") or contract.get("output_scopes")
    }
    return report


@pytest.mark.parametrize("worker", [False, True])
def test_new_goal_discriminator_uses_exact_ordinary_report_and_original_scope(
    repository,
    worker,
):
    from adaptive_bundles import sha256
    from test_adaptive_qualification_unit import compact_goal

    value = assignment(repository, mode="prepare")
    path = repository / "requirements.json"
    original = json.loads(path.read_text())
    original["criteria"][1]["text"] = (
        "Capture the actual approved member-task scope as selected original evidence."
    )
    path.write_text(json.dumps(original))
    value["work"]["requirement_sources"][0]["sha256"] = sha256(path.read_bytes())
    document, binding, digest, contract = compact_goal(worker=worker)
    plan = value["target"]["procedure_plan"]
    plan.update(
        family="goal",
        entrypoint="epic-handler",
        source_dispositions={
            "aquarium-goal-v2.yaml": "The actual original scope requires a separate compact context producer and selected independent evidence."
        },
    )
    draft = plan["drafts"][0]
    draft.update(
        document=document,
        mapping={key: val for key, val in binding.items() if key != "procedure"},
    )
    for row in draft["coverage"]:
        row["obligation"] = (
            "current-work-scope"
            if row["criterion"] == "original:omitted"
            else "judge-work"
        )
    value["target"]["qualification_context"] = {"goal_kind": "member-task"}
    client = Oracle(repository)
    current = prepare(repository, value, client=client, bootstrap=True)["assignment"]
    requested = qualify_prepared(repository, current, client=client)
    assert requested["status"] == "assessment-required"
    assert requested["structural"]["status"] == "not-established"
    report = prove_operations(report_for(requested["target"]), binding)
    retained = qualify_prepared(
        repository, current, client=client, assessment=report, retain=True
    )
    assert retained["status"] == "qualified"
    assert (
        report["applicability"]["operation_contracts"][digest]["contract"] == contract
    )
    resumed = resume_selected(
        repository,
        ["definitions"],
        retained["binding"]["procedure"],
        client=client,
        qualification={"assignment": current, "assessment": report},
    )
    assert resumed["qualification"]["status"] == "qualified"


@pytest.mark.parametrize("change", ["gate", "unknown-effect"])
def test_pending_semantics_do_not_relax_an_independent_structural_violation(
    repository, change
):
    from adaptive_bundles import sha256
    from adaptive_definitions import canonical_json, definition_id

    value = prepared(repository, privileged=True)
    exact = value["target"]["prepared_definition"]
    source = Path(exact["source_path"])
    binding_path = Path(exact["binding_path"])
    document = yaml.safe_load(source.read_bytes())
    binding = json.loads(binding_path.read_text())
    if change == "gate":
        document["node_definitions"]["goal-route"]["options"][0]["guards"] = []
        document["node_definitions"]["outcome"]["options"][0]["guards"] = [
            row
            for row in document["node_definitions"]["outcome"]["options"][0]["guards"]
            if row["evidence"]["item"] != "judge-goal-outcome"
        ]
    else:
        from test_adaptive_qualification_unit import insert_action

        insert_action(
            document, binding, "goal-route", "unresolved-change", declared=False
        )
    source.write_text(yaml.safe_dump(document, sort_keys=False, width=float("inf")))
    preview = Oracle(repository).preview(source)
    binding["procedure"]["digest"] = preview["procedure_digest"]
    binding["procedure"]["source_sha256"] = sha256(source.read_bytes())
    binding_path.write_bytes(canonical_json(binding))
    exact.update(bundle_id=definition_id(binding), procedure=binding["procedure"])
    with pytest.raises(BundleError) as error:
        qualify_prepared(repository, value, client=Oracle(repository))
    assert error.value.code == (
        "incompatible" if change == "gate" else "not-established"
    )
    assert any(
        row["property"] == "current-final-assessment-and-forward-effects"
        for row in error.value.details["issues"]
    )


def test_one_assessment_covers_pending_semantics_and_exact_capacity(repository):
    value = prepared(repository, privileged=True, criterion_maximum=3)
    client = Oracle(repository)
    requested = qualify_prepared(repository, value, client=client)
    assert requested["status"] == "assessment-required"
    assert requested["capacity_proof_due"] is True
    assert requested["structural"]["operation_proof_pending"] is True
    binding = json.loads(
        Path(value["target"]["prepared_definition"]["binding_path"]).read_text()
    )
    report = prove_operations(report_for(requested["target"]), binding)
    report["applicability"]["criterion_capacity"] = {
        "value": 3,
        "basis": requested["target"]["basis"]["criteria"],
        "evidence": [
            "Synthetic independent capacity observation for every original compound part."
        ],
    }
    result = qualify_prepared(repository, value, client=client, assessment=report)
    assert result["status"] == "qualified"


def test_new_compact_plan_operation_uses_same_exact_suitability_and_handoff(repository):
    import uuid

    from adaptive_execution import execution_context

    value = prepared(repository, privileged=True)
    client = Oracle(repository)
    requested = qualify_prepared(repository, value, client=client)
    assert requested["status"] == "assessment-required"
    assert requested["structural"]["status"] == "not-established"
    assert "execution" not in requested["structural"]
    binding = json.loads(
        Path(value["target"]["prepared_definition"]["binding_path"]).read_text()
    )
    report = prove_operations(report_for(requested["target"]), binding)
    retained = qualify_prepared(
        repository, value, client=client, assessment=report, retain=True
    )
    assert retained["status"] == "qualified"
    assert retained["structural"]["execution"]["first_work"] == ["deliver"]
    session = str(uuid.uuid4())
    value["target"]["plan_handoff_runtime"] = {
        "mode": "plan-handoff",
        "initial_session_id": session,
    }
    client.health = lambda: {
        "status": {
            "procedure": binding["procedure"],
            "session": {"id": session, "lifecycle": "running", "revision": 5},
            "current": {
                "node": {"graph_node_id": "sketch-plan"},
                "attempt": {"attempt_id": "a"},
            },
            "goal_revision": 1,
        },
        "guidance": {"node": {"graph_node_id": "sketch-plan"}, "readback": []},
        "active_items": [],
        "mutation_templates": [],
    }
    context = execution_context(
        repository,
        roots=["definitions"],
        entrypoint="task-handler",
        qualification={"assignment": value, "assessment": report},
        client=client,
    )
    assert context["status"] == "attachment-required"
    assert context["dispatch"] is None
    assert context["handoff"]["first_work"] == ["deliver"]


@pytest.mark.parametrize(
    "damage",
    ["missing", "digest", "contract", "evidence", "target", "independent-violation"],
)
def test_operation_labels_and_noncurrent_proofs_cannot_authorize_adoption(
    repository, damage
):
    value = prepared(repository, privileged=True)
    client = Oracle(repository)
    requested = qualify_prepared(repository, value, client=client)
    binding = json.loads(
        Path(value["target"]["prepared_definition"]["binding_path"]).read_text()
    )
    report = prove_operations(report_for(requested["target"]), binding)
    proofs = report["applicability"]["operation_contracts"]
    digest = next(iter(proofs))
    if damage == "missing":
        proofs.clear()
    elif damage == "digest":
        proofs["sha256:" + "0" * 64] = proofs.pop(digest)
    elif damage == "contract":
        proofs[digest]["contract"]["basis"] = "A different operation"
    elif damage == "evidence":
        proofs[digest]["evidence"] = [" ", {}]
    elif damage == "target":
        report["target"]["procedure_suitability"]["candidate"]["bundle_id"] = "0" * 64
    else:
        value["authority"]["review"]["route"] = "waived"
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository, value, client=client, assessment=report, retain=True
        )
    assert error.value.code == (
        "reassessment-required"
        if damage == "target"
        else "authority-required"
        if damage == "independent-violation"
        else "not-established"
    )
    assert not (repository / "definitions/.local").exists()


@pytest.mark.parametrize("performance", [False, True])
def test_qualification_cli_reports_success_after_initial_and_repeated_retention(
    repository, performance, monkeypatch, capsys
):
    import adaptive_admission
    import qualify_adaptive_procedure

    value = prepared(repository, performance)
    requested = qualify_prepared(repository, value, client=Oracle(repository))
    assignment_path = repository / "assignment.json"
    assessment_path = repository / "assessment.json"
    assignment_path.write_text(json.dumps(value))
    assessment_path.write_text(json.dumps(report_for(requested["target"])))
    monkeypatch.setattr(
        adaptive_admission, "NativeClient", lambda root, binary: Oracle(root)
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualify_adaptive_procedure.py",
            "--repository",
            str(repository),
            "--assignment",
            str(assignment_path),
            "--assessment",
            str(assessment_path),
            "--podway",
            "synthetic-native-oracle",
            "--retain",
        ],
    )
    results = []
    for _ in range(2):
        assert qualify_adaptive_procedure.main() == 0
        result = json.loads(capsys.readouterr().out)
        assert result["status"] == "qualified"
        retained = result["retention"]
        source = (Path(retained["path"]) / "procedure.yaml").read_bytes()
        assert retained["source"] == {
            "sha256": result["binding"]["procedure"]["source_sha256"],
            "byte_size": len(source),
        }
        assert yaml.safe_load(source)["schema"] == "podway.procedure/v2"
        results.append(retained)
    assert results[0] == results[1]


@pytest.mark.parametrize("performance", [False, True])
def test_public_preparation_to_exact_suitability_import_and_retained_recovery(
    repository, performance
):
    value = prepared(repository, performance)
    client = Oracle(repository)
    requested = qualify_prepared(repository, value, client=client)
    assert requested["status"] == "assessment-required"
    assert requested["assignment"]["role"] == "judge"
    assert requested["assignment"]["procedure"] is None
    assert (
        requested["target"]["candidate"]["procedure"]["digest"]
        != value["target"]["prepared_definition"]["procedure"]["source_sha256"]
    )
    assessment = report_for(requested["target"])
    result = qualify_prepared(
        repository, value, client=client, assessment=assessment, retain=True
    )
    assert result["status"] == "qualified"
    assert result["bootstrap"]["items"]["suitability-timing"] == "pre-start"
    qualification = {"assignment": value, "assessment": assessment}
    selected = selected_source(
        repository,
        Path(result["retention"]["path"]) / "procedure.yaml",
        binding_path=Path(result["retention"]["path"]) / "binding.json",
        roots=["definitions"],
        entrypoint="task-handler",
        route="herdr",
        runtime_ready=True,
        client=client,
        qualification=qualification,
    )
    assert selected["status"] == "ready"
    # Retained bytes, not the preparation source or mutable library, own recovery.
    original = Path(value["target"]["prepared_definition"]["source_path"])
    original.unlink()
    resumed = resume_selected(
        repository,
        ["definitions"],
        result["binding"]["procedure"],
        client=client,
        qualification=qualification,
    )
    assert resumed["qualification"]["status"] == "qualified"
    client.health.assert_not_called()


@pytest.mark.parametrize(
    "change",
    [
        "candidate",
        "basis",
        "timing",
        "criteria",
        "compound",
        "applicability",
        "verdict",
    ],
)
def test_stale_or_incomplete_suitability_never_imports(repository, change):
    value = prepared(repository)
    request = qualify_prepared(repository, value, client=Oracle(repository))
    target = request["target"]
    assessment = report_for(target)
    if change == "candidate":
        assessment["target"]["procedure_suitability"]["candidate"]["bundle_id"] = (
            "0" * 64
        )
    elif change == "basis":
        assessment["target"]["procedure_suitability"]["basis"]["authority"][
            "effects"
        ] = []
    elif change == "timing":
        assessment["target"]["procedure_suitability"]["timing"] = "in-session"
    elif change == "criteria":
        assessment["criteria"].pop()
    elif change == "compound":
        assessment["criteria"][0]["parts"].pop()
    elif change == "applicability":
        assessment["applicability"]["status"] = "unknown"
    else:
        assessment["verdict"] = "evidence-needed"
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository,
            value,
            client=Oracle(repository),
            assessment=assessment,
            retain=True,
        )
    assert error.value.code in {"reassessment-required", "not-established"}
    assert not (repository / "definitions/.local").exists()


def test_changed_original_source_and_plan_basis_need_reassessment(repository):
    value = prepared(repository)
    request = qualify_prepared(repository, value, client=Oracle(repository))
    assessment = report_for(request["target"])
    value["authority"]["allowed"].append("Another current permitted execution effect")
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository, value, client=Oracle(repository), assessment=assessment
        )
    assert error.value.code == "reassessment-required"
    path = repository / "requirements.json"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository, value, client=Oracle(repository), assessment=assessment
        )
    assert error.value.code == "source-drift"


def test_compatible_due_task_plan_shares_one_exact_judge_scope(repository):
    value = prepared(repository)
    request = qualify_prepared(
        repository, value, client=Oracle(repository), combined_task_plan=True
    )
    assert request["target"]["scopes"] == ["procedure-suitability", "task-plan"]
    report = report_for(request["target"])
    result = qualify_prepared(
        repository,
        value,
        client=Oracle(repository),
        assessment=report,
        combined_task_plan=True,
    )
    assert result["status"] == "qualified"
    with pytest.raises(BundleError):
        qualify_prepared(
            repository, value, client=Oracle(repository), assessment=report
        )


def test_known_unchanged_reuse_preserves_original_bytes_and_checkpoint(repository):
    value = assignment(repository, mode="prepare")
    known_candidate(repository, value)
    result = prepare(repository, value, client=Oracle(repository), bootstrap=True)
    exact = result["assignment"]["target"]["prepared_definition"]
    document = yaml.safe_load(Path(exact["source_path"]).read_bytes())
    assert document["graph"]["entry"] != "suitability-bootstrap"
    qualified = qualify_prepared(
        repository, result["assignment"], client=Oracle(repository)
    )
    assert qualified["status"] == "qualified-known"
    assert qualified["bootstrap"] is None


@pytest.mark.parametrize("known_reuse", [False, True])
@pytest.mark.parametrize("during_publication", [False, True])
def test_managed_authority_changes_require_reassessment_before_adoption(
    repository, monkeypatch, known_reuse, during_publication
):
    import adaptive_suitability
    from test_adaptive_preparation_unit import managed_custom

    managed = managed_custom(repository)
    disposition = "Preserve the actual managed API guarantee in the original work."
    if known_reuse:
        value = assignment(repository, mode="prepare")
        value["target"]["procedure_plan"]["customization_disposition"] = disposition
        known_candidate(repository, value)
        value = prepare(repository, value, client=Oracle(repository))["assignment"]
        assessment = None
    else:
        value = prepared(repository, customization_disposition=disposition)
        request = qualify_prepared(repository, value, client=Oracle(repository))
        assessment = report_for(request["target"])

    def change_authority():
        managed.write_bytes(managed.read_bytes() + b"\n# New adopted requirement\n")

    if during_publication:
        publisher = adaptive_suitability.publish_bundle

        def publish(*args, **kwargs):
            change_authority()
            return publisher(*args, **kwargs)

        monkeypatch.setattr(adaptive_suitability, "publish_bundle", publish)
    else:
        change_authority()
    before = {path.relative_to(repository) for path in repository.rglob("*")}
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository,
            value,
            client=Oracle(repository),
            assessment=assessment,
            retain=True,
        )
    assert error.value.code == "reassessment-required"
    assert {path.relative_to(repository) for path in repository.rglob("*")} == before


def test_intact_admitted_definition_does_not_depend_on_changed_managed_origin(
    repository,
):
    from test_adaptive_preparation_unit import managed_custom

    managed = managed_custom(repository)
    value = prepared(
        repository,
        customization_disposition="Preserve the adopted API guarantee in original work.",
    )
    client = Oracle(repository)
    request = qualify_prepared(repository, value, client=client)
    report = report_for(request["target"])
    result = qualify_prepared(
        repository, value, client=client, assessment=report, retain=True
    )
    managed.unlink()
    resumed = resume_selected(
        repository,
        ["definitions"],
        result["binding"]["procedure"],
        client=client,
        qualification={"assignment": value, "assessment": report},
    )
    assert resumed["status"] == "resolved"
    assert resumed["qualification"]["status"] == "qualified"


@pytest.mark.parametrize("action", ["inspect", "retain", "resume"])
def test_qualification_cannot_hide_conflicting_bundle_by_narrowing_disclosed_roots(
    repository, action
):
    from adaptive_definitions import canonical_json, definition_id

    value = prepared(repository)
    value["authority"]["preparation"]["roots"].append("other flows 한글")
    client = Oracle(repository)
    request = qualify_prepared(repository, value, client=client)
    report = report_for(request["target"])
    admitted = qualify_prepared(
        repository, value, client=client, assessment=report, retain=True
    )
    changed = copy.deepcopy(admitted["binding"])
    changed["parameters"]["extra"] = {
        "type": "text",
        "required": False,
        "description": "Conflicting exact-key mapping",
    }
    other = repository / "other flows 한글/.local" / definition_id(changed)
    other.mkdir(parents=True)
    (other.parent / ".gitignore").write_text("*\n")
    (other / "procedure.yaml").write_bytes(admitted["retention"]["source"])
    (other / "binding.json").write_bytes(canonical_json(changed))
    qualification = {"assignment": value, "assessment": report}
    retained = Path(admitted["retention"]["path"])
    before = {
        path: path.read_bytes() for path in repository.rglob("*") if path.is_file()
    }
    with pytest.raises(BundleError) as omitted:
        if action == "resume":
            resume_selected(
                repository,
                ["definitions"],
                admitted["binding"]["procedure"],
                client=client,
                qualification=qualification,
            )
        else:
            options = {"write_root": "definitions"} if action == "retain" else {}
            (retain_selected if action == "retain" else selected_source)(
                repository,
                retained / "procedure.yaml",
                roots=["definitions"],
                entrypoint="task-handler",
                route="herdr",
                client=client,
                runtime_ready=True,
                binding_path=retained / "binding.json",
                qualification=qualification,
                **options,
            )
    assert omitted.value.code == "not-established"
    with pytest.raises(BundleError) as conflict:
        resume_selected(
            repository,
            value["authority"]["preparation"]["roots"],
            admitted["binding"]["procedure"],
            client=client,
            qualification=qualification,
        )
    assert conflict.value.code == "ambiguous"
    assert {
        path: path.read_bytes() for path in repository.rglob("*") if path.is_file()
    } == before


def test_full_disclosed_custom_domain_resumes_without_write_authority(repository):
    value = prepared(repository)
    roots = ["definitions", "-custom flows 한글"]
    value["authority"]["preparation"]["roots"] = roots
    client = Oracle(repository)
    request = qualify_prepared(repository, value, client=client)
    report = report_for(request["target"])
    admitted = qualify_prepared(
        repository, value, client=client, assessment=report, retain=True
    )
    retained = Path(admitted["retention"]["path"])
    alias = repository / roots[1] / ".local" / retained.name
    alias.mkdir(parents=True)
    (alias.parent / ".gitignore").write_text("*\n")
    for name in ("procedure.yaml", "binding.json"):
        (alias / name).write_bytes((retained / name).read_bytes())
    value["authority"]["preparation"]["native_authoring"] = False
    value["authority"]["preparation"].pop("write_root")
    resumed = resume_selected(
        repository,
        [*roots, "-custom flows 한글/./"],
        admitted["binding"]["procedure"],
        client=client,
        qualification={"assignment": value, "assessment": report},
    )
    assert resumed["status"] == "resolved"
    assert len(resumed["aliases"]) == 2
    assert resumed["qualification"]["status"] == "qualified"


def test_bootstrap_requires_actual_current_pass_and_dominates_work():
    document, binding, context = adaptive()
    mapping = {key: value for key, value in binding.items() if key != "procedure"}
    document, mapping = add_bootstrap(document, mapping)
    binding = bound(document, mapping)
    assert qualify(document, binding, context=context)["status"] == "compatible"
    decision = document["node_definitions"]["suitability-applicability"]
    decision["options"][0]["guards"] = []
    assert qualify(document, binding, context=context)["status"] == "incompatible"


def test_unqualified_new_preparation_remains_non_admissible(repository):
    value = prepared(repository)
    with pytest.raises(BundleError) as error:
        selected_source(
            repository,
            Path(value["target"]["prepared_definition"]["source_path"]),
            roots=["definitions"],
            entrypoint="task-handler",
            runtime_ready=True,
            client=Oracle(repository),
        )
    assert error.value.code == "not-established"


def test_plan_only_with_bootstrap_never_writes_or_runs_native(repository):
    value = assignment(repository)
    before = sorted(
        (
            str(path.relative_to(repository)),
            path.read_bytes() if path.is_file() else None,
        )
        for path in repository.rglob("*")
    )
    client = Oracle(repository)
    result = prepare(repository, value, client=client, bootstrap=True)
    after = sorted(
        (
            str(path.relative_to(repository)),
            path.read_bytes() if path.is_file() else None,
        )
        for path in repository.rglob("*")
    )
    assert result["status"] == "planned"
    assert before == after
    client.read.assert_not_called()


@pytest.mark.parametrize(
    "rendering", ["state", "not-applicable", "future-product-gaps"]
)
def test_actual_ordinary_renderings_and_phase_scope_are_preserved(
    repository, rendering
):
    value = prepared(repository)
    request = qualify_prepared(repository, value, client=Oracle(repository))
    report = report_for(request["target"])
    if rendering == "future-product-gaps":
        report["gaps"] = [
            {
                "scope": "product-delivery",
                "reason": "Actual product work has not started",
            }
        ]
    else:
        for row in report["criteria"]:
            row["state"] = row.pop("status")
            for part in row["parts"]:
                part["state"] = part.pop("status")
        if rendering == "not-applicable":
            row = report["criteria"][-1]
            row["state"] = "not-applicable"
            row["reason"] = (
                "The exact scope preserves this existing behavior without executing an optional phase"
            )
            for part in row["parts"]:
                part["state"] = "not-applicable"
                part["reason"] = row["reason"]
    assert (
        qualify_prepared(
            repository, value, client=Oracle(repository), assessment=report
        )["status"]
        == "qualified"
    )


@pytest.mark.parametrize(
    "damage", ["duplicate", "contradiction", "unjustified-na", "fake-evidence"]
)
def test_ordinary_criterion_ambiguity_or_missing_due_evidence_cannot_pass(
    repository, damage
):
    value = prepared(repository)
    request = qualify_prepared(repository, value, client=Oracle(repository))
    report = report_for(request["target"])
    row = report["criteria"][0]
    if damage == "duplicate":
        report["criteria"].append(copy.deepcopy(row))
    elif damage == "contradiction":
        row["state"] = "unverified"
    elif damage == "unjustified-na":
        row["status"] = "not-applicable"
    else:
        row["evidence"] = True
    with pytest.raises(BundleError) as error:
        assess_current(report, request["target"])
    assert error.value.code in {"invalid-input", "not-established"}


def test_same_operation_live_progress_does_not_change_static_suitability_target(
    repository,
):
    value = prepared(repository)
    request = qualify_prepared(repository, value, client=Oracle(repository))
    report = report_for(request["target"])
    value["authority"]["consumed_review_authority"] = 2
    value["authority"]["remaining_review_authority"] = 1
    value["native"]["available_handle"] = "reconnected-public-handle"
    value["procedure"] = {"lifecycle": "running", "attempt": 3}
    assert (
        qualify_prepared(
            repository, value, client=Oracle(repository), assessment=report
        )["status"]
        == "qualified"
    )


def test_missing_or_stale_running_assessment_never_produces_new_pre_start_dispatch(
    repository,
):
    value = prepared(repository)
    client = Oracle(repository)
    request = qualify_prepared(repository, value, client=client)
    report = report_for(request["target"])
    with pytest.raises(BundleError) as missing:
        qualify_prepared(repository, value, client=client, in_session=True)
    assert missing.value.code == "reassessment-required"
    assert missing.value.details["status"] == "missing-topology"
    assert "assignment" not in missing.value.details
    value["target"]["base"] = "materially-new-approved-plan-basis"
    with pytest.raises(BundleError) as stale:
        qualify_prepared(
            repository, value, client=client, assessment=report, in_session=True
        )
    assert stale.value.code == "reassessment-required"
    assert stale.value.details["status"] == "missing-topology"
    assert "assignment" not in stale.value.details


def test_actual_selected_route_cannot_differ_from_qualified_authority(repository):
    value = prepared(repository)
    client = Oracle(repository)
    request = qualify_prepared(repository, value, client=client)
    qualification = {"assignment": value, "assessment": report_for(request["target"])}
    with pytest.raises(BundleError) as error:
        selected_source(
            repository,
            Path(value["target"]["prepared_definition"]["source_path"]),
            binding_path=Path(value["target"]["prepared_definition"]["binding_path"]),
            roots=["definitions"],
            entrypoint="task-handler",
            route="mulgae",
            runtime_ready=True,
            client=client,
            qualification=qualification,
        )
    assert error.value.code == "route-unavailable"


@pytest.mark.parametrize(
    "value", [[], {"target": []}, {"target": {"prepared_definition": []}}]
)
def test_public_qualifier_returns_typed_invalid_input_without_native_work(
    repository, value
):
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(
                Path(__file__).resolve().parents[2]
                / "plugins/aquarium/shared/qualify_adaptive_procedure.py"
            ),
            "--repository",
            str(repository),
            "--assignment",
            "-",
            "--podway",
            "/absent-native-must-not-run",
        ],
        input=json.dumps(value),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == ""


def test_existing_actual_task_planning_judge_is_a_reassessment_route():
    from adaptive_suitability import reassessment_route
    from test_adaptive_qualification_unit import known

    document, binding = known("task")
    result = reassessment_route(document, binding)
    assert result["status"] == "existing-planning-judge"
    assert result["nodes"] == ["judge-plan"]
    document, binding = known("goal")
    assert reassessment_route(document, binding)["status"] == "missing-topology"


def test_combined_phase_pass_keeps_global_future_product_gaps(repository):
    value = prepared(repository)
    request = qualify_prepared(
        repository, value, client=Oracle(repository), combined_task_plan=True
    )
    report = report_for(request["target"])
    report["verdict"] = "evidence-needed"
    report["checkpoint_result"] = "pass"
    report["gaps"] = [
        {"scope": "product-delivery", "reason": "Actual approved work has not started"}
    ]
    for row in report["criteria"]:
        row["state"] = row.pop("status")
        row["state"] = "unverified"
        row["reason"] = (
            "Future product delivery remains unverified; current definition/plan coverage is assessed at this checkpoint"
        )
        for part in row["parts"]:
            part["state"] = "unverified"
            part.pop("status")
            part["reason"] = row["reason"]
    result = qualify_prepared(
        repository,
        value,
        client=Oracle(repository),
        assessment=report,
        combined_task_plan=True,
    )
    assert result["status"] == "qualified"
    assert result["bootstrap"]["items"]["suitability-verdict"] == "pass"
    report["checkpoint_criteria"] = [
        {
            "id": "actual-plan-suitability",
            "state": "unmet",
            "evidence": ["Missing required original-source coverage"],
        }
    ]
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository,
            value,
            client=Oracle(repository),
            assessment=report,
            combined_task_plan=True,
        )
    assert error.value.code == "not-established"


@pytest.mark.parametrize("damage", ["missing", "revoked", "write-root", "client"])
def test_retention_requires_current_disclosed_preparation_authority(repository, damage):
    value = prepared(repository)
    client = Oracle(repository)
    request = qualify_prepared(repository, value, client=client)
    report = report_for(request["target"])
    if damage == "missing":
        value["authority"].pop("preparation")
    elif damage == "revoked":
        value["authority"]["preparation"]["native_authoring"] = False
    elif damage == "write-root":
        value["authority"]["preparation"]["write_root"] = "another-root"
    else:
        client.repository = repository / "another-worktree"
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository, value, client=client, assessment=report, retain=True
        )
    assert error.value.code in {"authority-required", "unsafe"}
    assert not (repository / "definitions/.local").exists()
    assert not (repository / "another-root").exists()


@pytest.mark.parametrize("maximum", [0, 3])
def test_bounded_gap_capacity_requires_exact_independent_original_basis(
    repository, maximum
):
    value = assignment(repository, mode="prepare")
    document, binding, context = adaptive()
    for item in document["node_definitions"]["assess"]["items"]:
        if item["id"] in {"judge-unmet-criteria", "judge-unverified-criteria"}:
            item["maximum"] = maximum
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft.update(
        document=document,
        mapping={key: val for key, val in binding.items() if key != "procedure"},
    )
    for row in draft["coverage"]:
        row["obligation"] = "original-goal"
    value["target"]["qualification_context"] = context
    value["target"]["qualification_context"]["criterion_capacity"] = 0
    ready = prepare(repository, value, client=Oracle(repository), bootstrap=True)[
        "assignment"
    ]
    request = qualify_prepared(repository, ready, client=Oracle(repository))
    assert request["status"] == "assessment-required"
    assert request["capacity_proof_due"] is True
    assert request["structural"]["status"] == "not-established"
    report = report_for(request["target"])
    report["applicability"]["criterion_capacity"] = {
        "value": 3,
        "basis": request["target"]["basis"]["criteria"],
        "evidence": ["Independent exact original three-part criterion-capacity proof"],
    }
    if maximum == 0:
        with pytest.raises(BundleError) as error:
            qualify_prepared(
                repository, ready, client=Oracle(repository), assessment=report
            )
        assert error.value.code == "incompatible"
    else:
        retained = qualify_prepared(
            repository, ready, client=Oracle(repository), assessment=report, retain=True
        )
        assert retained["status"] == "qualified"
        from adaptive_suitability import established_reuse

        actual_source = Path(retained["retention"]["path"]) / "procedure.yaml"
        exact_criteria = request["target"]["basis"]["criteria"]
        reuse = {
            "client": Oracle(repository),
            "roots": ["definitions"],
            "prior": report,
            "context": {
                **value["target"]["qualification_context"],
                "criterion_capacity": 0,
            },
            "criteria": exact_criteria,
        }
        assert (
            established_reuse(
                repository, actual_source.read_bytes(), retained["binding"], **reuse
            )["status"]
            == "resolved"
        )
        # Current fit cannot reuse a capacity proof for a different criterion basis.
        reuse["criteria"] = {**exact_criteria, "another": {"parts": [{"id": "whole"}]}}
        reuse["context"]["criterion_capacity"] = 100
        with pytest.raises(BundleError) as error:
            established_reuse(
                repository, actual_source.read_bytes(), retained["binding"], **reuse
            )
        assert error.value.code == "not-established"
        report["applicability"]["criterion_capacity"]["basis"] = {}
        with pytest.raises(BundleError) as error:
            qualify_prepared(
                repository, ready, client=Oracle(repository), assessment=report
            )
        assert error.value.code == "not-established"


@pytest.mark.parametrize("semantic_change", [False, True])
def test_formatter_contract_materialization_requires_native_semantic_identity(
    repository, semantic_change
):
    value = assignment(repository, mode="prepare")
    document, binding, context = adaptive()
    closeout = document["node_definitions"]["closeout"]
    closeout["items"][0].pop("multiline", None)
    from adaptive_bundles import sha256
    from adaptive_definitions import canonical_json

    context["operation_contracts"] = {
        **{
            key: value
            for key, value in context["operation_contracts"].items()
            if value["effect"] != "finalization"
        },
        sha256(canonical_json(closeout)): {
            "roles": ["orchestrator"],
            "effect": "finalization",
            "basis": "Explicit static fixture result delivery",
        },
    }
    value["target"]["qualification_context"] = context
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft.update(
        document=document,
        mapping={key: val for key, val in binding.items() if key != "procedure"},
    )
    for row in draft["coverage"]:
        row["obligation"] = "original-goal"

    class Formatter(Oracle):
        def preview(self, path):
            result = super().preview(path)
            result["procedure_digest"] = "sha256:" + "a" * 64
            return result

        def _read(self, argv, command, schemas):
            result = super()._read(argv, command, schemas)
            if command == "procedure.validate" and semantic_change:
                result["digest"] = "sha256:" + "b" * 64
            if command == "procedure.format" and "--check" not in argv:
                parsed = yaml.safe_load(result["document"])
                parsed["node_definitions"]["closeout"]["items"][0]["multiline"] = True
                result["document"] = yaml.safe_dump(parsed)
            return result

    client = Formatter(repository)
    if semantic_change:
        with pytest.raises(BundleError) as error:
            prepare(repository, value, client=client, bootstrap=True)
        assert error.value.code == "source-drift"
        assert (
            list((repository / "definitions/.candidates").glob("*/binding.json")) == []
        )
    else:
        result = prepare(repository, value, client=client, bootstrap=True)
        actual = yaml.safe_load(
            Path(
                result["assignment"]["target"]["prepared_definition"]["source_path"]
            ).read_bytes()
        )
        formatted = actual["node_definitions"]["closeout"]
        assert (
            sha256(canonical_json(formatted)) in result["binding"]["semantic_contracts"]
        )
        assert (
            qualify_prepared(repository, result["assignment"], client=client)["status"]
            == "assessment-required"
        )


def existing_adaptive(repository, *, privileged=False):
    original = prepared(repository, privileged=privileged)
    client = Oracle(repository)
    request = qualify_prepared(repository, original, client=client)
    prior = report_for(request["target"])
    if privileged:
        original_binding = json.loads(
            Path(original["target"]["prepared_definition"]["binding_path"]).read_text()
        )
        prove_operations(prior, original_binding)
    qualified = qualify_prepared(
        repository, original, client=client, assessment=prior, retain=True
    )
    value = assignment(repository, mode="prepare")
    value["target"]["qualification_context"] = original["target"][
        "qualification_context"
    ]
    plan = value["target"]["procedure_plan"]
    if privileged:
        plan["plan_handoff"] = copy.deepcopy(
            original["target"]["procedure_plan"]["plan_handoff"]
        )
    coverage = [
        {**row, "obligation": "original-goal"} for row in plan["drafts"][0]["coverage"]
    ]
    plan["drafts"] = []
    path = Path(qualified["retention"]["path"])
    from adaptive_bundles import sha256

    plan["candidates"] = [
        {
            "path": str((path / "procedure.yaml").relative_to(repository)),
            "sha256": sha256((path / "procedure.yaml").read_bytes()),
            "binding": {
                "path": str((path / "binding.json").relative_to(repository)),
                "sha256": sha256((path / "binding.json").read_bytes()),
            },
            "coverage": coverage,
            "prior_suitability": prior,
            "reason": "The previously qualified documentation structure meets the current original work without changes.",
        }
    ]
    import shutil

    shutil.rmtree(Path(original["target"]["prepared_definition"]["source_path"]).parent)
    return value, prior, qualified


def test_equivalent_privileged_operation_reuse_keeps_prior_proof_and_first_due_boundary(
    repository,
):
    value, prior, original = existing_adaptive(repository, privileged=True)
    client = Oracle(repository)
    result = prepare(repository, value, client=client, bootstrap=True)
    assert result["assignment"]["target"]["prepared_definition"]["kind"] == "reuse"
    qualified = qualify_prepared(
        repository, result["assignment"], client=client, retain=True
    )
    assert qualified["status"] == "qualified-known"
    assert "assignment" not in qualified
    assert qualified["structural"]["execution"]["first_work"] == ["deliver"]
    imported = qualified["bootstrap"]["artifact_evidence"]["suitability-assessment"]
    assert imported["prior_definition_assessment"] == prior
    assert qualified["binding"] == original["binding"]
    resumed = resume_selected(
        repository,
        ["definitions"],
        qualified["binding"]["procedure"],
        client=client,
        qualification={"assignment": result["assignment"]},
    )
    assert resumed["qualification"]["status"] == "qualified-known"
    assert resumed["qualification"]["structural"]["execution"]["first_work"] == [
        "deliver"
    ]


def test_exact_retained_adaptive_reuse_preserves_first_due_assessment(repository):
    value, prior, original = existing_adaptive(repository)
    # A new invocation has a different approved basis; old evidence is definition evidence.
    value["instructions"] += " Preserve current recovery and verification obligations."
    result = prepare(repository, value, client=Oracle(repository), bootstrap=True)
    current = result["assignment"]
    assert current["target"]["prepared_definition"]["kind"] == "reuse"
    assert result["binding"] == original["binding"]
    qualified = qualify_prepared(
        repository, current, client=Oracle(repository), retain=True
    )
    assert qualified["status"] == "qualified-known"
    assert "assignment" not in qualified
    imported = qualified["bootstrap"]
    assert imported["items"]["suitability-timing"] == "established-reuse"
    checkpoint = imported["artifact_evidence"]["suitability-assessment"]
    assert checkpoint["prior_definition_assessment"] == prior
    assert checkpoint["schema"] == "aquarium.orchestration-checkpoint/v2"
    resumed = resume_selected(
        repository,
        ["definitions"],
        result["binding"]["procedure"],
        client=Oracle(repository),
        qualification={"assignment": current},
    )
    assert resumed["qualification"]["status"] == "qualified-known"
    current["target"]["procedure_plan"]["effects"].append("evidence")
    current["authority"]["effects"].append("evidence")
    with pytest.raises(BundleError) as caught:
        resume_selected(
            repository,
            ["definitions"],
            result["binding"]["procedure"],
            client=Oracle(repository),
            qualification={"assignment": current},
        )
    assert caught.value.code == "reassessment-required"
    assert "assignment" not in caught.value.details


@pytest.mark.parametrize("mode", ["plan-only", "no-native-authority", "wrong-client"])
def test_existing_adaptive_reuse_obeys_read_only_and_current_native_scope(
    repository, tmp_path, mode
):
    value, _, _ = existing_adaptive(repository)
    plan = value["target"]["procedure_plan"]
    client = Oracle(repository)
    expected = "not-established"
    if mode == "plan-only":
        plan["mode"] = "plan-only"
    elif mode == "no-native-authority":
        value["authority"]["preparation"]["native_authoring"] = False
        expected = "authority-required"
    else:
        client.repository = repository / "elsewhere"
        expected = "unsafe"
    before = {
        str(path.relative_to(repository)): path.read_bytes() if path.is_file() else None
        for path in repository.rglob("*")
    }
    with pytest.raises(BundleError) as caught:
        prepare(repository, value, client=client, bootstrap=True)
    assert caught.value.code == expected
    assert before == {
        str(path.relative_to(repository)): path.read_bytes() if path.is_file() else None
        for path in repository.rglob("*")
    }
    client.read.assert_not_called()


def test_pre_start_judge_assignment_does_not_impersonate_preparing_worker(repository):
    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parents[2]
            / "plugins/aquarium/skills/goal-judge/scripts"
        ),
    )
    from ordinary_assignment import render_dispatch

    value = prepared(repository)
    value["native"] = {
        "harness": "Codex",
        "available_handle": "preparing-worker",
        "observed_lifecycle": "working",
    }
    result = qualify_prepared(repository, value, client=Oracle(repository))
    judged = result["assignment"]
    assert judged["native"] == {
        "harness": "Codex",
        "assigned_agent": "unknown",
        "lifecycle": "not-dispatched",
    }
    assert judged["target"]["preparation_native_context"] == value["native"]
    rendered = render_dispatch(judged)
    actual = json.loads(
        rendered["dispatch_text"][rendered["dispatch_text"].index("{") :]
    )
    assert actual["native"] == judged["native"]
    assert actual["target"]["preparation_native_context"] == value["native"]


def test_valid_exact_semantic_proof_does_not_waive_assessed_structural_violation(
    repository, monkeypatch
):
    import adaptive_suitability
    from adaptive_bundles import sha256
    from adaptive_definitions import canonical_json, definition_id

    value = prepared(repository, privileged=True)
    exact = value["target"]["prepared_definition"]
    source = Path(exact["source_path"])
    binding_path = Path(exact["binding_path"])
    document = yaml.safe_load(source.read_bytes())
    binding = json.loads(binding_path.read_text())
    document["node_definitions"]["goal-route"]["options"][0]["guards"] = []
    document["node_definitions"]["outcome"]["options"][0]["guards"] = [
        row
        for row in document["node_definitions"]["outcome"]["options"][0]["guards"]
        if row["evidence"]["item"] != "judge-goal-outcome"
    ]
    source.write_text(yaml.safe_dump(document, sort_keys=False, width=float("inf")))
    client = Oracle(repository)
    binding["procedure"].update(
        digest=client.preview(source)["procedure_digest"],
        source_sha256=sha256(source.read_bytes()),
    )
    binding_path.write_bytes(canonical_json(binding))
    exact.update(bundle_id=definition_id(binding), procedure=binding["procedure"])
    target = adaptive_suitability.suitability_target(
        binding,
        adaptive_suitability.current_basis(repository, value),
        combined_task_plan=False,
        coverage_plan=exact["coverage_plan"],
    )
    report = prove_operations(report_for(target), binding)
    accepted = []
    prove = adaptive_suitability.operation_proofs

    def observed_proofs(*args):
        result = prove(*args)
        accepted.append(result)
        return result

    monkeypatch.setattr(adaptive_suitability, "operation_proofs", observed_proofs)
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository, value, client=client, assessment=report, retain=True
        )
    assert accepted == [
        {
            digest: row["contract"]
            for digest, row in report["applicability"]["operation_contracts"].items()
        }
    ]
    assert error.value.code == "incompatible"
    assert any(
        row["property"] == "current-final-assessment-and-forward-effects"
        for row in error.value.details["issues"]
    )
    assert not (repository / "definitions/.local").exists()


def test_same_due_in_session_assessment_receives_exact_semantic_and_capacity_inputs(
    repository,
):
    value = prepared(repository, privileged=True, criterion_maximum=3)
    client = Oracle(repository)
    request = qualify_prepared(repository, value, client=client)
    binding = json.loads(
        Path(value["target"]["prepared_definition"]["binding_path"]).read_text()
    )
    demands = request["assignment"]["target"]["assessment_requirements"]
    assert demands["operation_contracts"] == {
        key: contract
        for key, contract in binding["semantic_contracts"].items()
        if contract.get("discriminators") or contract.get("output_scopes")
    }
    assert {row["item"] for row in demands["criterion_capacity"]["bounded_fields"]} == {
        "judge-unmet-criteria",
        "judge-unverified-criteria",
    }
    assert {
        row["maximum"] for row in demands["criterion_capacity"]["bounded_fields"]
    } == {3}
    report = prove_operations(report_for(request["target"]), binding)
    value["target"]["procedure_plan"]["source_dispositions"][
        "aquarium-task-v2.yaml"
    ] += " Preserve the approved revised plan."
    with pytest.raises(BundleError) as error:
        qualify_prepared(
            repository, value, client=client, assessment=report, in_session=True
        )
    assert error.value.code == "reassessment-required"
    assert error.value.details["assessment_requirements"] == demands
    assert error.value.details["next_owner"] == "Orchestrator"
    assert "assignment" not in error.value.details
    assert "bootstrap" not in error.value.details


def test_existing_mapped_planning_judge_gets_current_equivalent_operation_inputs():
    from adaptive_bundles import sha256
    from adaptive_definitions import ASSETS, canonical_json
    from adaptive_suitability import reassessment_route
    from test_adaptive_qualification_unit import known

    document, binding = known("task")
    definition = document["node_definitions"]["plan-record"]
    operations = json.loads(
        (ASSETS / "adaptive/operation-contracts-v1.json").read_text()
    )
    contract = operations[sha256(canonical_json(definition))]
    definition["title"] = "Record the actual revised documentation plan"
    digest = sha256(canonical_json(definition))
    binding.setdefault("semantic_contracts", {})[digest] = contract
    judge = next(row for row in document["graph"]["nodes"] if row["id"] == "judge-plan")
    judge_definition = document["node_definitions"][judge["use"]]
    judge_contract = operations[sha256(canonical_json(judge_definition))]
    for item in document["node_definitions"][judge["use"]]["items"]:
        if item["id"] in {"judge-unmet-criteria", "judge-unverified-criteria"}:
            item["maximum"] = 3
    binding["semantic_contracts"][sha256(canonical_json(judge_definition))] = (
        judge_contract
    )
    route = reassessment_route(document, binding)
    assert route["status"] == "existing-planning-judge"
    assert route["nodes"] == ["judge-plan"]
    requirements = route["assessment_requirements"]
    assert requirements["operation_contracts"][digest] == contract
    planning_counts = [
        row
        for row in requirements["criterion_capacity"]["bounded_fields"]
        if row["node"] == "judge-plan"
    ]
    assert {row["item"] for row in planning_counts} == {
        "judge-unmet-criteria",
        "judge-unverified-criteria",
    }
    assert {row["maximum"] for row in planning_counts} == {3}
    assert "assignment" not in route
    assert "bootstrap" not in route


def test_current_in_session_report_covers_semantics_and_capacity_without_new_cycle(
    repository,
):
    from adaptive_suitability import current_basis, suitability_target

    value = prepared(repository, privileged=True, criterion_maximum=3)
    client = Oracle(repository)
    request = qualify_prepared(repository, value, client=client)
    exact = value["target"]["prepared_definition"]
    binding = json.loads(Path(exact["binding_path"]).read_text())

    def current_report(target):
        report = prove_operations(report_for(target), binding)
        report["applicability"]["criterion_capacity"] = {
            "value": 3,
            "basis": target["basis"]["criteria"],
            "evidence": ["Synthetic current compound-criterion capacity evidence."],
        }
        return report

    initial_report = current_report(request["target"])
    retained = qualify_prepared(
        repository, value, client=client, assessment=initial_report, retain=True
    )
    path = Path(retained["retention"]["path"])
    value["target"]["procedure_plan"]["source_dispositions"][
        "aquarium-task-v2.yaml"
    ] += " Preserve the approved revised plan."
    target = suitability_target(
        binding,
        current_basis(repository, value, in_session=True),
        combined_task_plan=False,
        coverage_plan=exact["coverage_plan"],
    )
    report = current_report(target)
    options = {
        "client": client,
        "in_session": True,
        "source_path": path / "procedure.yaml",
        "binding_path": path / "binding.json",
    }
    before = {p: p.read_bytes() for p in repository.rglob("*") if p.is_file()}
    client.read.reset_mock()
    with pytest.raises(BundleError) as stale:
        qualify_prepared(repository, value, assessment=initial_report, **options)
    assert stale.value.code == "reassessment-required"
    for missing in ("operation_contracts", "criterion_capacity"):
        incomplete = copy.deepcopy(report)
        incomplete["applicability"].pop(missing)
        with pytest.raises(BundleError) as error:
            qualify_prepared(repository, value, assessment=incomplete, **options)
        assert error.value.code == "not-established"
    result = qualify_prepared(repository, value, assessment=report, **options)
    assert result["status"] == "qualified"
    assert result["binding"] == binding
    assert result["target"] == target
    assert result["bootstrap"]["node"] == retained["bootstrap"]["node"]
    assert result["retention"] is None
    assert "assignment" not in result and "dispatch" not in result
    assert not {call.args[1] for call in client.read.call_args_list}.intersection(
        {
            "session.start",
            "session.start_replace",
            "session.begin",
            "session.work",
            "session.decide",
        }
    )
    assert {p: p.read_bytes() for p in repository.rglob("*") if p.is_file()} == before
