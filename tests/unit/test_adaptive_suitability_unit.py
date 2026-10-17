"""Exact ordinary suitability evidence and source-only preparation boundaries."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugins/aquarium/shared"))
from adaptive_admission import resume_selected, selected_source
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


def prepared(repository, performance=False):
    value = assignment(repository, mode="prepare", performance=performance)
    document, binding, context = adaptive(performance=performance)
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


def existing_adaptive(repository):
    original = prepared(repository)
    client = Oracle(repository)
    request = qualify_prepared(repository, original, client=client)
    prior = report_for(request["target"])
    qualified = qualify_prepared(
        repository, original, client=client, assessment=prior, retain=True
    )
    value = assignment(repository, mode="prepare")
    value["target"]["qualification_context"] = original["target"][
        "qualification_context"
    ]
    plan = value["target"]["procedure_plan"]
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
