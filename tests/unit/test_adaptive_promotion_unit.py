"""Source promotion and authority controls; fixture consent is synthetic."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))
import adaptive_preparation as prep
import adaptive_promotion as promotion
from adaptive_bundles import BundleError, sha256
from adaptive_definitions import canonical_json
from test_adaptive_composition_unit import fragment_plan
from test_adaptive_preparation_unit import Oracle, assignment


@pytest.fixture
def repository(tmp_path):
    path = tmp_path / "work with 한글"
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    return path


def request(repository, *, fragment=False, name="bounded"):
    value = (
        fragment_plan(repository)
        if fragment
        else assignment(repository, mode="prepare")
    )
    client = Oracle(repository)
    prepared = prep.prepare(repository, value, client=client)
    target = prepared["assignment"]["target"]["prepared_definition"]
    source = {
        "path": target["source_path"],
        "sha256": sha256(Path(target["source_path"]).read_bytes()),
    }
    binding = {
        "path": target["binding_path"],
        "sha256": sha256(Path(target["binding_path"]).read_bytes()),
    }
    candidate = {
        "name": name,
        "kind": "fragment" if fragment else "whole",
        "source": source,
        "binding": binding,
        "future_use": "Reuse this bounded documentation delivery and evidence structure for another API.",
        "limits": "One synthetic fixture use; no claim of future product execution.",
        "use": {
            "outcome": "successful",
            "reference": "fixture ordinary closeout",
            "evidence": "fixture original criteria established",
        },
    }
    if fragment:
        draft = value["target"]["procedure_plan"]["drafts"][0]
        candidate.update(
            source=draft["composition"]["components"][0]["source"],
            representative={"source": source, "draft": draft},
        )
    return {
        "origin": {
            "workflow": "aquarium:task-handler",
            "epic": "EPIC-001",
            "task": "TASK-001",
            "reference": "fixture assignment",
        },
        "library_root": "definitions/reusable",
        "candidates": [candidate],
    }, client


def finalization():
    return {
        "accepted": True,
        "reference": "synthetic original acceptance",
        "no_commit": True,
        "native": {
            "required": True,
            "state": "completed",
            "disposition": "not_required",
            "reference": "fixture final native readback",
        },
    }


def consent(proposal, names):
    return {"source": "user", "proposal_id": proposal["id"], "selected": names}


def test_offer_is_readonly_and_decline_preserves_local_bundle(repository):
    value, client = request(repository)
    before = {str(p): p.read_bytes() for p in repository.rglob("*") if p.is_file()}
    offered = promotion.offer(repository, value, client)
    proposal = offered["proposal"]
    assert not (repository / value["library_root"]).exists()
    assert proposal["candidates"][0]["checks"][-1]["procedure_version"] == "1"
    result = promotion.apply(repository, proposal, consent(proposal, []), {}, client)
    assert result["status"] == "preservation-declined"
    assert before == {
        str(p): p.read_bytes() for p in repository.rglob("*") if p.is_file()
    }


def test_yes_applies_after_no_commit_finalization_and_distinct_grant(repository):
    value, client = request(repository)
    proposal = promotion.offer(repository, value, client)["proposal"]
    grant = {
        "purpose": "procedure-library-promotion",
        "proposal_id": proposal["id"],
        "selected": ["bounded"],
        "consumed": False,
        "reference": "synthetic separate one-commit grant",
    }
    result = promotion.apply(
        repository,
        proposal,
        consent(proposal, ["bounded"]),
        finalization(),
        client,
        commit_grant=grant,
    )
    assert result["status"] == "promotion-applied"
    assert result["task_commit_handoff"]["lifecycle_edits"] == []
    assert result["task_commit_handoff"]["origin"] == value["origin"]
    for path, contents in proposal["candidates"][0]["files"].items():
        assert (repository / path).read_bytes() == contents.encode()
    assert (
        subprocess.check_output(["git", "-C", str(repository), "diff", "--cached"])
        == b""
    )


def test_partial_consent_without_commit_authority_leaves_exact_selected_uncommitted(
    repository,
):
    value, client = request(repository)
    other = copy.deepcopy(value["candidates"][0])
    other["name"] = "another"
    value["candidates"].append(other)
    proposal = promotion.offer(repository, value, client)["proposal"]
    result = promotion.apply(
        repository, proposal, consent(proposal, ["another"]), finalization(), client
    )
    assert result["task_commit_handoff"] is None
    assert not (repository / "definitions/reusable/bounded").exists()
    assert (repository / "definitions/reusable/another/procedure.yaml").is_file()


@pytest.mark.parametrize(
    "change", ["acceptance", "native", "consent", "proposal", "symlink", "ignored"]
)
def test_missing_current_authority_or_unsafe_target_stops_before_library_write(
    repository, change
):
    value, client = request(repository)
    proposal = promotion.offer(repository, value, client)["proposal"]
    decision, final = consent(proposal, ["bounded"]), finalization()
    if change == "acceptance":
        final["accepted"] = False
    elif change == "native":
        final["native"]["state"] = "running"
    elif change == "consent":
        decision["source"] = "broad-edit-grant"
    elif change == "proposal":
        proposal["candidates"][0]["future_use"] = "changed"
    elif change == "symlink":
        (repository / "definitions/reusable").symlink_to(repository.parent)
    else:
        (repository / ".gitignore").write_text("definitions/reusable/\n")
    with pytest.raises(BundleError):
        promotion.apply(repository, proposal, decision, final, client)
    assert not (repository / "definitions/reusable/bounded").exists()


def test_duplicate_comparison_uses_binding_not_source_alone(repository):
    value, client = request(repository)
    old = repository / "definitions/reusable/prior"
    old.mkdir(parents=True)
    old.joinpath("procedure.yaml").write_bytes(
        Path(value["candidates"][0]["source"]["path"]).read_bytes()
    )
    old.joinpath("binding.json").write_text("{}")
    assert (
        promotion.offer(repository, value, client)["proposal"]["candidates"][0][
            "duplicates"
        ]
        == []
    )
    old.joinpath("binding.json").write_bytes(
        Path(value["candidates"][0]["binding"]["path"]).read_bytes()
    )
    proposal = promotion.offer(repository, value, client)["proposal"]
    assert proposal["candidates"][0]["duplicates"] == ["prior"]
    with pytest.raises(BundleError) as caught:
        promotion.apply(
            repository, proposal, consent(proposal, ["bounded"]), finalization(), client
        )
    assert caught.value.code == "duplicate"


def test_fragment_preserves_mapping_and_checks_actual_flattened_representative(
    repository,
):
    value, client = request(repository, fragment=True)
    proposal = promotion.offer(repository, value, client)["proposal"]
    files = proposal["candidates"][0]["files"]
    assert {Path(path).name for path in files} == {
        "fragment.json",
        "mapping.json",
        "representative.yaml",
        "representative.binding.json",
    }
    result = promotion.apply(
        repository, proposal, consent(proposal, ["bounded"]), finalization(), client
    )
    assert len(result["paths"]) == 4


def test_actual_use_required_and_source_drift_rejected(repository):
    value, client = request(repository)
    value["candidates"][0]["use"]["outcome"] = "native-valid"
    with pytest.raises(BundleError) as caught:
        promotion.offer(repository, value, client)
    assert caught.value.code == "not-established"
    value["candidates"][0]["use"]["outcome"] = "successful"
    Path(value["candidates"][0]["source"]["path"]).write_text("changed")
    with pytest.raises(BundleError) as caught:
        promotion.offer(repository, value, client)
    assert caught.value.code == "source-drift"


def test_native_text_multiline_default_is_equivalent_but_false_changes_fragment(
    repository,
):
    import yaml

    value, client = request(repository, fragment=True)
    candidate = value["candidates"][0]
    path = Path(candidate["representative"]["source"]["path"])
    native = yaml.safe_load(path.read_text())
    native = promotion.source_defaults(native)
    path.write_text(yaml.safe_dump(native))
    candidate["representative"]["source"]["sha256"] = sha256(path.read_bytes())
    binding_path = Path(candidate["binding"]["path"])
    binding = json.loads(binding_path.read_text())
    preview = client.preview(path)
    binding["procedure"].update(
        source_sha256=sha256(path.read_bytes()), digest=preview["procedure_digest"]
    )
    binding_path.write_bytes(canonical_json(binding))
    candidate["binding"]["sha256"] = sha256(binding_path.read_bytes())
    assert promotion.offer(repository, value, client)["status"] == "preservation-offer"
    native["node_definitions"]["work-deliver"]["items"][0]["multiline"] = False
    path.write_text(yaml.safe_dump(native))
    candidate["representative"]["source"]["sha256"] = sha256(path.read_bytes())
    binding["procedure"].update(
        source_sha256=sha256(path.read_bytes()),
        digest=client.preview(path)["procedure_digest"],
    )
    binding_path.write_bytes(canonical_json(binding))
    candidate["binding"]["sha256"] = sha256(binding_path.read_bytes())
    with pytest.raises(BundleError) as caught:
        promotion.offer(repository, value, client)
    assert caught.value.code == "not-established"


def test_same_exact_promotion_recovery_reuses_published_content(repository):
    value, client = request(repository)
    proposal = promotion.offer(repository, value, client)["proposal"]
    decision = consent(proposal, ["bounded"])
    first = promotion.apply(repository, proposal, decision, finalization(), client)
    original = {path: (repository / path).read_bytes() for path in first["paths"]}
    second = promotion.apply(repository, proposal, decision, finalization(), client)
    assert second["paths"] == first["paths"]
    assert original == {
        path: (repository / path).read_bytes() for path in second["paths"]
    }


def test_concurrent_target_preserved_and_owned_stage_cleaned(repository, monkeypatch):
    value, client = request(repository)
    proposal = promotion.offer(repository, value, client)["proposal"]
    target = repository / "definitions/reusable/bounded"

    def compete(parent, source, name):
        target.mkdir()
        (target / "custom.txt").write_text("preserve foreign publisher")
        raise FileExistsError(name)

    monkeypatch.setattr(promotion, "_rename_exclusive", compete)
    with pytest.raises(BundleError) as caught:
        promotion.apply(
            repository, proposal, consent(proposal, ["bounded"]), finalization(), client
        )
    assert caught.value.code == "publication-conflict"
    assert (target / "custom.txt").read_text() == "preserve foreign publisher"
    assert not list(target.parent.glob(".promotion-*"))


@pytest.mark.parametrize("revision", ["HEAD", "main", "cancelled", "no-disposition"])
def test_original_finalization_rejects_mutable_or_incomplete_basis(
    repository, revision
):
    final = finalization()
    if revision in {"HEAD", "main"}:
        final.pop("no_commit")
        final["commit"] = revision
    elif revision == "cancelled":
        final["native"]["state"] = "cancelled"
    else:
        final["native"].pop("disposition")
    with pytest.raises(BundleError) as caught:
        promotion.finalized(repository, final)
    assert caught.value.code == "not-established"


def test_original_finalization_accepts_actual_commit_and_completed_undisposed_reason(
    repository,
):
    (repository / "original.txt").write_text("original accepted fixture")
    subprocess.run(["git", "-C", str(repository), "add", "original.txt"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "[TEST] Original fixture",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    final = finalization()
    final.pop("no_commit")
    final["commit"] = commit
    final["native"].pop("disposition")
    final["native"]["undisposed_reason"] = (
        "No supported external handoff disposition for this internal boundary"
    )
    promotion.finalized(repository, final)


@pytest.mark.parametrize(
    "field,value",
    [
        ("purpose", "original-task"),
        ("proposal_id", "another"),
        ("selected", ["other"]),
        ("consumed", True),
    ],
)
def test_mismatching_grant_keeps_consent_applied_uncommitted(repository, field, value):
    data, client = request(repository)
    proposal = promotion.offer(repository, data, client)["proposal"]
    grant = {
        "purpose": "procedure-library-promotion",
        "proposal_id": proposal["id"],
        "selected": ["bounded"],
        "consumed": False,
        "reference": "synthetic grant",
    }
    grant[field] = value
    original = copy.deepcopy(grant)
    with pytest.raises(BundleError) as caught:
        promotion.apply(
            repository,
            proposal,
            consent(proposal, ["bounded"]),
            finalization(),
            client,
            commit_grant=grant,
        )
    assert caught.value.code == "commit-authority-required"
    assert caught.value.details["applied"]
    for name in caught.value.details["applied"]:
        assert (repository / name).is_file()
    assert (
        subprocess.check_output(["git", "-C", str(repository), "diff", "--cached"])
        == b""
    )
    assert grant == original
    result = promotion.apply(
        repository, proposal, consent(proposal, ["bounded"]), finalization(), client
    )
    assert result["task_commit_handoff"] is None


@pytest.mark.parametrize("fragment", [False, True])
def test_transformed_sources_receive_exact_native_gates_without_runtime_claim(
    repository, fragment
):
    data, client = request(repository, fragment=fragment)
    data["candidates"][0]["transformed"] = True
    client.read.reset_mock()
    proposal = promotion.offer(repository, data, client)["proposal"]
    calls = client.read.call_args_list
    assert [call.args[1] for call in calls] == [
        "procedure.format",
        "procedure.validate",
        "procedure.vet",
        "procedure.lint",
    ]
    assert calls[0].args[2] == {
        "podway.procedure-source-result/v1",
        "podway.procedure-diagnostics-result/v1",
    }
    assert all(
        call.args[2] == {"podway.procedure-diagnostics-result/v1"} for call in calls[1:]
    )
    assert "--warnings-as-errors" in calls[-1].args[0]
    assert proposal["candidates"][0]["adoption"] == "not-performed"
    assert (
        proposal["candidates"][0]["runtime"]
        == "source-use-only; transformed candidate execution unobserved"
    )


def test_interrupted_staging_is_diagnostic_not_an_equivalent_entry(repository):
    data, client = request(repository)
    stage = repository / "definitions/reusable/.promotion-prior"
    stage.mkdir(parents=True)
    stage.joinpath("procedure.yaml").write_bytes(
        Path(data["candidates"][0]["source"]["path"]).read_bytes()
    )
    stage.joinpath("binding.json").write_bytes(
        Path(data["candidates"][0]["binding"]["path"]).read_bytes()
    )
    before = {p.name: p.read_bytes() for p in stage.iterdir()}
    proposal = promotion.offer(repository, data, client)["proposal"]
    assert proposal["candidates"][0]["duplicates"] == []
    assert proposal["diagnostics"] == [
        {"path": ".promotion-prior", "status": "interrupted-staging"}
    ]
    assert before == {p.name: p.read_bytes() for p in stage.iterdir()}


def test_cleanup_failure_preserves_original_typed_failure(repository, monkeypatch):
    data, client = request(repository)
    proposal = promotion.offer(repository, data, client)["proposal"]
    monkeypatch.setattr(
        promotion,
        "_rename_exclusive",
        lambda *_: (_ for _ in ()).throw(FileExistsError()),
    )
    monkeypatch.setattr(
        promotion.os,
        "rmdir",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("fixture cleanup blocked")
        ),
    )
    with pytest.raises(BundleError) as caught:
        promotion.apply(
            repository, proposal, consent(proposal, ["bounded"]), finalization(), client
        )
    assert caught.value.code == "cleanup-failed"
    assert caught.value.details["original_failure"]["status"] == "publication-conflict"
    assert list((repository / "definitions/reusable").glob(".promotion-*"))


@pytest.mark.parametrize("wrong_schema", [False, True])
def test_native_client_rejects_unknown_success_shaped_authoring_contract(
    repository, monkeypatch, wrong_schema
):
    from types import SimpleNamespace

    import adaptive_admission as admission

    data, oracle = request(repository)
    candidate = data["candidates"][0]
    source = Path(candidate["source"]["path"])
    binding = json.loads(Path(candidate["binding"]["path"]).read_text())
    client = admission.NativeClient(repository, "/synthetic/native")
    client.preview = oracle.preview

    def native(argv, **_kwargs):
        operation = next(
            word for word in argv if word in {"format", "validate", "vet", "lint"}
        )
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "schema": "podway.output/v4",
                    "command": "procedure." + operation,
                    "result": {
                        "schema": "future.unknown/v1"
                        if wrong_schema
                        else "podway.procedure-diagnostics-result/v1",
                        "valid": True,
                    },
                }
            ).encode(),
        )

    monkeypatch.setattr(admission.subprocess, "run", native)
    if wrong_schema:
        with pytest.raises(BundleError) as caught:
            promotion.native_checks(
                repository, client, source, binding, transformed=True
            )
        assert caught.value.code == "unsupported-runtime"
    else:
        assert (
            len(
                promotion.native_checks(
                    repository, client, source, binding, transformed=True
                )
            )
            == 5
        )
