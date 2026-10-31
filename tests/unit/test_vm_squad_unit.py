"""Synthetic adapter controls, never installed/native-agent acceptance."""

import json
import sys
from pathlib import Path

import pytest
import test_podway_upgrade_unit as podway_tests

environment = podway_tests.environment
upgrade = podway_tests.upgrade

VM = Path(__file__).resolve().parents[1] / "vm"
sys.path.insert(0, str(VM))
import native_observation
import run_acceptance


def test_squad_uses_original_observation_and_restoration_recipe(
    environment, monkeypatch
):
    context, _state, binary, results, _run, skills = environment
    monkeypatch.setattr(upgrade.lib, "finish", podway_tests.finish)
    monkeypatch.setattr(upgrade.lib, "RECORDED_INVENTORIES", {})
    assert upgrade.run(context, "prepare", skills, suite="epic-squad") == 0
    binary.write_bytes(b"candidate")
    assert upgrade.run(context, "candidate", skills, suite="epic-squad") == 0
    binary.write_bytes(b"prior")
    assert upgrade.run(context, "consumer-cleanup", skills, suite="epic-squad") == 0
    assert (
        json.loads((results / "consumer-cleanup.json").read_text())["consumer_cleanup"]
        == "verified"
    )
    assert (
        json.loads((results / "consumer-result.json").read_bytes())["consumer_cleanup"]
        == "verified"
    )


def test_suite_requires_every_original_group_without_synthetic_functional_pass():
    suites = json.loads((VM / "host_suites.json").read_text())["suites"]
    inventory = json.loads((VM / "fixtures/squad/cases.json").read_text())
    suite = suites["epic-squad"]
    assert suite["modes"] == ["manual"]
    assert suite["environment_profile"] == "podway-candidate"
    assert set(suite["manual"]["required_scenarios"]) == set(inventory["cases"])
    assert all(
        row["case"] in inventory["cases"] and row["observed"] is False
        for row in inventory["original_scenarios"]
    )
    assert "results/epic-squad/case-evidence.json" in suite["required_outputs"]
    assert (
        "results/podway-upgrade/result.json"
        in suites["podway-upgrade"]["required_outputs"]
    )


def test_existing_handle_capture_uses_public_reader_and_preserves_original(
    tmp_path, monkeypatch
):
    repository = tmp_path / "fixture"
    repository.mkdir()
    (repository / "product.txt").write_text("original product")
    output = tmp_path / "capture.json"
    calls = []
    monkeypatch.setattr(
        run_acceptance, "guest_guard", lambda uuid: calls.append(("guard", uuid))
    )
    observation = {
        "schema": "aquarium.vm-native-observation/v1",
        "root": {"id": "existing"},
        "descendants": [],
    }
    monkeypatch.setattr(
        native_observation,
        "collect",
        lambda codex, cwd, handle: (
            calls.append((codex, cwd, handle)) or dict(observation)
        ),
    )
    argv = [
        "--codex",
        "codex",
        "--cwd",
        str(repository),
        "--thread-id",
        "existing",
        "--expected-guest-uuid",
        "guest",
        "--candidate",
        "a" * 40,
        "--case",
        "operation-recovery",
        "--output",
        str(output),
    ]
    assert native_observation.main(argv) == 0
    captured = json.loads(output.read_text())
    assert captured["root"] == observation["root"]
    assert captured["candidate"] == "a" * 40
    assert set(captured["product_image"]) == {"product.txt"}
    assert calls == [("guard", "guest"), ("codex", repository, "existing")]
    original = output.read_bytes()
    with pytest.raises(run_acceptance.GateError):
        native_observation.main(argv)
    assert output.read_bytes() == original
    assert (
        len(calls) == 3
    )  # Second call verifies guest identity, but never reads another operation.


@pytest.fixture
def staging(tmp_path, monkeypatch):
    from types import SimpleNamespace

    cases = json.loads((VM / "fixtures/squad/cases.json").read_text())["cases"]
    results = tmp_path / "results/epic-squad"
    results.mkdir(parents=True)
    candidate = "a" * 40
    index = {"candidate_sha": candidate, "cases": {}}
    for case in cases:
        directory = results / "originals" / case
        directory.mkdir(parents=True)
        (directory / "report.json").write_text(
            json.dumps({"case": case, "original": True})
        )
        (directory / "native.jsonl").write_bytes(b'{"actual":"public capture"}\n')
        index["cases"][case] = {"required": ["report.json", "native.jsonl"]}
    for name, document in {
        "prepared.json": {"candidate_sha": candidate},
        "candidate.json": {"candidate_sha": candidate},
        "consumer-cleanup.json": {
            "candidate_sha": candidate,
            "consumer_cleanup": "verified",
        },
        "inventories.json": {
            "schema": "aquarium.vm-suite-inventories/v1",
            "inventories": {"actual-restoration": {"original": True}},
        },
        "consumer-result.json": {
            "scope": "consumer restoration only",
            "outcome": "pass",
            "consumer_cleanup": "verified",
            "candidate": {"git_sha": candidate},
        },
        "case-evidence.json": index,
    }.items():
        upgrade.lib.write_document(results / name, document)
    monkeypatch.setattr(upgrade.lib, "results_directory", lambda suite: results)
    monkeypatch.setattr(upgrade.lib, "RECORDED_INVENTORIES", {})
    context = SimpleNamespace(
        checkout=VM.parents[1],
        root=tmp_path,
        inputs={
            "candidate": {"git_sha": candidate},
            "podway_upgrade": {"contract_generation": 2},
        },
    )
    return context, results, index


def test_staging_collects_complete_originals_and_actual_restoration_receipt(staging):
    import hashlib
    import tarfile

    context, results, _index = staging
    original_cleanup = (results / "consumer-cleanup.json").read_bytes()
    original_result = (results / "consumer-result.json").read_bytes()
    original_inventory = (results / "inventories.json").read_bytes()
    assert upgrade.stage_squad_evidence(context, results) == 0
    summary = json.loads((results / "stage-evidence.json").read_bytes())
    assert summary["ok"] is True
    assert len(summary["archives"]) == len(
        json.loads((VM / "fixtures/squad/cases.json").read_text())["cases"]
    )
    for case in summary["archives"]:
        archive = results / "evidence" / case["archive"]
        assert case["sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
        with tarfile.open(archive) as reader:
            assert (
                reader.extractfile(f"originals/{case['case']}/report.json").read()
                == (results / f"originals/{case['case']}/report.json").read_bytes()
            )
            for record in case["members"]:
                assert (
                    hashlib.sha256(
                        reader.extractfile(record["path"]).read()
                    ).hexdigest()
                    == record["sha256"]
                )
    with tarfile.open(results / "evidence/consumer-restoration.tar") as reader:
        assert reader.extractfile("consumer-cleanup.json").read() == original_cleanup
        assert reader.extractfile("consumer-result.json").read() == original_result
        assert reader.extractfile("inventories.json").read() == original_inventory
    assert (results / "consumer-cleanup.json").read_bytes() == original_cleanup
    assert (results / "consumer-result.json").read_bytes() == original_result
    assert (
        json.loads((results / "result.json").read_bytes())["evidence_staging"] is True
    )


def test_staging_preserves_large_originals_for_native_collection(staging, monkeypatch):
    import hashlib
    import tarfile

    context, results, index = staging
    case = "native-multitask"
    original = results / f"originals/{case}/large-original.bin"
    with original.open("wb") as stream:
        stream.truncate(33 * 1024 * 1024)
    index["cases"][case]["required"].append(original.name)
    upgrade.lib.write_document(results / "case-evidence.json", index)
    # Release-acceptance limits do not own Squad's native collection budget.
    monkeypatch.setattr(upgrade.lib, "EVIDENCE_TOTAL_BYTES_BOUND", 32 * 1024 * 1024)
    assert upgrade.stage_squad_evidence(context, results) == 0
    summary = json.loads((results / "stage-evidence.json").read_bytes())
    assert summary["ok"] is True
    assert len(summary["archives"]) == len(
        json.loads((VM / "fixtures/squad/cases.json").read_text())["cases"]
    )
    with tarfile.open(results / f"evidence/{case}.tar") as reader:
        member = reader.getmember(f"originals/{case}/{original.name}")
        assert member.size == original.stat().st_size
        digest = hashlib.file_digest(reader.extractfile(member), "sha256").hexdigest()
        assert digest == upgrade.lib.sha256_file(original)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "inventory",
        "traversal",
        "symlink",
        "cleanup",
        "candidate",
        "receipt",
        "wrong-receipt",
    ],
)
def test_staging_failure_preserves_every_other_case_and_never_claims_pass(
    staging, fault
):
    context, results, index = staging
    case = "native-multitask"
    report = results / f"originals/{case}/report.json"
    if fault == "missing":
        report.unlink()
    elif fault == "inventory":
        index["cases"][case].pop("required")
    elif fault == "traversal":
        index["cases"][case]["required"] = ["../outside.json"]
    elif fault == "symlink":
        report.unlink()
        report.symlink_to(results / f"originals/{case}/native.jsonl")
    elif fault == "cleanup":
        (results / "consumer-cleanup.json").unlink()
    elif fault == "candidate":
        index["candidate_sha"] = "b" * 40
    elif fault == "receipt":
        (results / "consumer-result.json").unlink()
    elif fault == "wrong-receipt":
        upgrade.lib.write_document(
            results / "consumer-result.json",
            {
                "outcome": "pass",
                "consumer_cleanup": "verified",
                "candidate": {"git_sha": "b" * 40},
            },
        )
    upgrade.lib.write_document(results / "case-evidence.json", index)
    assert upgrade.stage_squad_evidence(context, results) == 2
    summary = json.loads((results / "stage-evidence.json").read_bytes())
    assert summary["ok"] is False
    assert len(summary["archives"]) == len(
        json.loads((VM / "fixtures/squad/cases.json").read_text())["cases"]
    )
    assert json.loads((results / "result.json").read_bytes())["outcome"] == "incomplete"
    assert all(row["archive_present"] is True for row in summary["archives"])
    assert all(
        (results / "evidence" / row["archive"]).is_file() for row in summary["archives"]
    )
    assert (
        results / f"originals/{case}/native.jsonl"
    ).read_bytes() == b'{"actual":"public capture"}\n'


def test_missing_original_recovery_retains_previous_failure_and_cleanup(staging):
    context, results, _index = staging
    target = results / "originals/operation-recovery/report.json"
    original = target.read_bytes()
    cleanup = (results / "consumer-cleanup.json").read_bytes()
    target.unlink()
    assert upgrade.stage_squad_evidence(context, results) == 2
    first = json.loads((results / "stage-evidence.json").read_bytes())["attempts"][0]
    receipt = (results / "consumer-result.json").read_bytes()
    target.write_bytes(original)
    assert upgrade.stage_squad_evidence(context, results) == 0
    current = json.loads((results / "stage-evidence.json").read_bytes())
    assert current["attempts"][0] == first
    assert current["attempts"][0]["ok"] is False
    assert current["ok"] is True
    assert (results / "consumer-cleanup.json").read_bytes() == cleanup
    assert (results / "consumer-result.json").read_bytes() == receipt


def test_managed_stage_phase_reads_checkout_and_never_runs_an_installed_writer(
    staging, monkeypatch
):
    context, results, _index = staging
    observed = []
    monkeypatch.setattr(
        upgrade.lib, "verify_guest_identity", lambda: observed.append("identity")
    )
    monkeypatch.setattr(
        upgrade.lib, "verify_sealed_inputs", lambda root: observed.append("sealed")
    )
    monkeypatch.setattr(upgrade.lib, "guard", lambda root: observed.append("guard"))

    def unexpected(*_args, **_kwargs):
        pytest.fail("staging must not execute the restored or candidate writer")

    monkeypatch.setattr(upgrade, "observe_tools", unexpected)
    assert upgrade.run(context, "stage-evidence", unexpected, suite="epic-squad") == 0
    assert observed == ["identity", "sealed", "guard"]
    assert json.loads((results / "stage-evidence.json").read_bytes())["ok"] is True


def test_staging_persists_interrupted_attempt_and_keeps_last_complete_archive(
    staging, monkeypatch
):
    context, results, _index = staging
    assert upgrade.stage_squad_evidence(context, results) == 0
    archive = results / "evidence/native-multitask.tar"
    before = archive.read_bytes()
    original = upgrade.lib.stage_evidence_archive

    def interrupt(path, *args):
        if path.name == "native-multitask.tar.partial":
            path.write_bytes(b"partial attempt")
            raise OSError("injected staging write failure")
        return original(path, *args)

    monkeypatch.setattr(upgrade.lib, "stage_evidence_archive", interrupt)
    with pytest.raises(OSError):
        upgrade.stage_squad_evidence(context, results)
    assert archive.read_bytes() == before
    failed = json.loads((results / "stage-evidence.json").read_bytes())
    assert len(failed["attempts"]) == 2
    assert failed["attempts"][-1]["ok"] is False
    assert failed["attempts"][-1]["archives"]
    assert "injected staging write failure" in str(failed["attempts"][-1]["problems"])
    monkeypatch.setattr(upgrade.lib, "stage_evidence_archive", original)
    assert upgrade.stage_squad_evidence(context, results) == 0
    recovered = json.loads((results / "stage-evidence.json").read_bytes())
    assert recovered["attempts"][:2] == failed["attempts"]


def test_cleanup_seals_receipt_before_refused_phase_generic_handler(
    environment, monkeypatch
):
    import guest_main

    context, _state, binary, results, _run, skills = environment
    monkeypatch.setattr(upgrade.lib, "finish", podway_tests.finish)
    monkeypatch.setattr(upgrade.lib, "load_inputs", lambda: context.inputs)
    monkeypatch.setattr(upgrade.lib, "RECORDED_INVENTORIES", {})
    assert upgrade.run(context, "prepare", skills, suite="epic-squad") == 0
    binary.write_bytes(b"candidate")
    assert upgrade.run(context, "candidate", skills, suite="epic-squad") == 0
    binary.write_bytes(b"prior")
    assert upgrade.run(context, "consumer-cleanup", skills, suite="epic-squad") == 0
    receipt = (results / "consumer-result.json").read_bytes()
    monkeypatch.setenv("HAEPARI_PARENT_CONTEXT", "fixture")
    monkeypatch.setattr(guest_main, "Context", lambda: context)
    monkeypatch.setattr(
        sys, "argv", ["guest_main.py", "--suite", "epic-squad", "--phase", "mistyped"]
    )
    assert guest_main.main() != 0
    assert json.loads((results / "result.json").read_bytes())["outcome"] != "pass"
    assert (results / "consumer-result.json").read_bytes() == receipt
    context.checkout = VM.parents[1]
    cases = json.loads((VM / "fixtures/squad/cases.json").read_bytes())["cases"]
    index = {"candidate_sha": context.inputs["candidate"]["git_sha"], "cases": {}}
    for case in cases:
        original = results / "originals" / case / "observed.json"
        upgrade.lib.write_document(original, {"case": case})
        index["cases"][case] = {"required": ["observed.json"]}
    upgrade.lib.write_document(results / "case-evidence.json", index)
    assert upgrade.stage_squad_evidence(context, results) == 0
    assert (results / "consumer-result.json").read_bytes() == receipt


def test_incremental_checkpoint_stages_originals_before_cleanup_without_pass(staging):
    import tarfile

    context, results, _index = staging
    cleanup = (results / "consumer-cleanup.json").read_bytes()
    receipt = (results / "consumer-result.json").read_bytes()
    (results / "consumer-cleanup.json").unlink()
    (results / "consumer-result.json").unlink()
    assert upgrade.stage_squad_evidence(context, results) == 2
    checkpoint = json.loads((results / "stage-evidence.json").read_bytes())
    assert checkpoint["ok"] is False
    assert len(checkpoint["archives"]) == len(
        json.loads((VM / "fixtures/squad/cases.json").read_text())["cases"]
    )
    with tarfile.open(results / "evidence/native-multitask.tar") as archive:
        assert (
            archive.extractfile("originals/native-multitask/report.json").read()
            == (results / "originals/native-multitask/report.json").read_bytes()
        )
    (results / "consumer-cleanup.json").write_bytes(cleanup)
    (results / "consumer-result.json").write_bytes(receipt)
    assert upgrade.stage_squad_evidence(context, results) == 0
    assert (
        json.loads((results / "stage-evidence.json").read_bytes())["attempts"][0]
        == checkpoint["attempts"][0]
    )


def test_manifest_failure_keeps_prior_archive_until_complete_replacement(
    staging, monkeypatch
):
    context, results, _index = staging
    assert upgrade.stage_squad_evidence(context, results) == 0
    archive = results / "evidence/native-multitask.tar"
    before = archive.read_bytes()
    (results / "originals/native-multitask/report.json").write_text(
        "changed public observation"
    )
    original = upgrade.lib.write_document

    def fail_manifest(path, document):
        if path.name == "native-multitask.manifest.json.partial":
            raise OSError("injected manifest write failure")
        return original(path, document)

    monkeypatch.setattr(upgrade.lib, "write_document", fail_manifest)
    with pytest.raises(OSError):
        upgrade.stage_squad_evidence(context, results)
    assert archive.read_bytes() == before
    history = json.loads((results / "stage-evidence.json").read_bytes())
    assert "injected manifest write failure" in str(history["attempts"][-1]["problems"])
    monkeypatch.setattr(upgrade.lib, "write_document", original)
    assert upgrade.stage_squad_evidence(context, results) == 0
    assert archive.read_bytes() != before


@pytest.mark.parametrize("invalid", [b'{"inventories":', b'{"inventories":[]}'])
def test_staging_preserves_invalid_restoration_inventory_across_retry(staging, invalid):
    import tarfile

    context, results, _index = staging
    assert upgrade.stage_squad_evidence(context, results) == 0
    (results / "inventories.json").write_bytes(invalid)
    assert upgrade.stage_squad_evidence(context, results) == 2
    assert (results / "inventories.json").read_bytes() == invalid
    with tarfile.open(results / "evidence/consumer-restoration.tar") as archive:
        assert archive.extractfile("inventories.json").read() == invalid
    assert upgrade.stage_squad_evidence(context, results) == 2
    assert (results / "inventories.json").read_bytes() == invalid


def test_invalid_inventory_refuses_cleanup_and_staging_without_erasing_history(
    staging, monkeypatch
):
    import tarfile

    context, results, _index = staging
    assert upgrade.stage_squad_evidence(context, results) == 0
    invalid = b'{"inventories": {"original-failed-cleanup":'
    (results / "inventories.json").write_bytes(invalid)
    (results / "consumer-cleanup.json").unlink()
    monkeypatch.setattr(upgrade.lib, "verify_guest_identity", dict)
    monkeypatch.setattr(upgrade.lib, "verify_sealed_inputs", lambda root: {})
    monkeypatch.setattr(upgrade.lib, "guard", lambda root: {})
    assert (
        upgrade.run(
            context,
            "consumer-cleanup",
            lambda _stage: pytest.fail(
                "invalid history must be refused before writer observation"
            ),
            suite="epic-squad",
        )
        == 2
    )
    assert (results / "inventories.json").read_bytes() == invalid
    assert upgrade.stage_squad_evidence(context, results) == 2
    assert (results / "inventories.json").read_bytes() == invalid
    with tarfile.open(results / "evidence/consumer-restoration.tar") as archive:
        assert archive.extractfile("inventories.json").read() == invalid
    assert upgrade.stage_squad_evidence(context, results) == 2
    with tarfile.open(results / "evidence/consumer-restoration.tar") as archive:
        assert archive.extractfile("inventories.json").read() == invalid


@pytest.mark.parametrize(
    "failure", ["first-persist", "archive", "structured", "decode"]
)
@pytest.mark.parametrize(
    "invalid", [b'{"inventories": {"original":', b'{"inventories": []}']
)
def test_driver_staging_failure_preserves_invalid_original_inventory(
    staging, monkeypatch, failure, invalid
):
    import guest_main

    context, results, _index = staging
    monkeypatch.setenv("HAEPARI_PARENT_CONTEXT", "fixture")
    monkeypatch.setattr(guest_main, "Context", lambda: context)
    monkeypatch.setitem(sys.modules, "podway_upgrade", upgrade)
    monkeypatch.setattr(upgrade.lib, "finish", podway_tests.finish)
    monkeypatch.setattr(upgrade.lib, "load_inputs", lambda: context.inputs)
    monkeypatch.setattr(upgrade.lib, "verify_guest_identity", dict)
    monkeypatch.setattr(upgrade.lib, "verify_sealed_inputs", lambda root: {})
    monkeypatch.setattr(upgrade.lib, "guard", lambda root: {})
    monkeypatch.setattr(
        sys,
        "argv",
        ["guest_main.py", "--suite", "epic-squad", "--phase", "stage-evidence"],
    )
    assert guest_main.main() == 0
    (results / "inventories.json").write_bytes(invalid)
    original_write = upgrade.lib.write_document
    original_archive = upgrade.lib.stage_evidence_archive

    def fail_write(path, value):
        if Path(path).name == "stage-evidence.json.partial":
            raise OSError("first staging persist interrupted")
        return original_write(path, value)

    def fail_archive(*args, **kwargs):
        if failure == "structured":
            raise upgrade.lib.RecipeError("structured staging refusal")
        if failure == "decode":
            raise ValueError("staging decode refusal")
        raise OSError("archive interrupted")

    if failure == "first-persist":
        monkeypatch.setattr(upgrade.lib, "write_document", fail_write)
    else:
        monkeypatch.setattr(upgrade.lib, "stage_evidence_archive", fail_archive)
    assert guest_main.main() == 2
    assert (results / "inventories.json").read_bytes() == invalid
    result = json.loads((results / "result.json").read_bytes())
    assert result["outcome"] == "incomplete"
    assert result["consumer_cleanup"] == "unverified"
    monkeypatch.setattr(upgrade.lib, "write_document", original_write)
    monkeypatch.setattr(upgrade.lib, "stage_evidence_archive", original_archive)
    assert guest_main.main() == 2
    assert (results / "inventories.json").read_bytes() == invalid
    assert (
        upgrade.run(
            context,
            "consumer-cleanup",
            lambda stage: pytest.fail("invalid history must refuse observation"),
            suite="epic-squad",
        )
        == 2
    )
    assert (results / "inventories.json").read_bytes() == invalid
