from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aquarium/skills/release-qa/scripts/manage_release_qa.py"
SPEC = importlib.util.spec_from_file_location("manage_release_qa", SCRIPT)
assert SPEC and SPEC.loader
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


@pytest.fixture
def release_case(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "QA")
    git(repo, "config", "user.email", "qa@example.invalid")
    (repo / "surface.txt").write_text("baseline\n", encoding="utf-8")
    git(repo, "add", "surface.txt")
    git(repo, "commit", "-m", "baseline")
    git(repo, "tag", "v1.0.0")
    (repo / "surface.txt").write_text("candidate\n", encoding="utf-8")
    git(repo, "commit", "-am", "candidate")
    candidate = git(repo, "rev-parse", "HEAD")
    evidence = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    yield repo, candidate, evidence
    shutil.rmtree(evidence, ignore_errors=True)


def write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def cluster(evidence: Path, candidate: str, *, outcome: str = "finding") -> Path:
    proof = evidence / "scenario.txt"
    proof.write_text("bounded observation\n", encoding="utf-8")
    findings = (
        [{"id": "F-1", "scenario_id": "S-1", "severity": "Medium"}]
        if outcome == "finding"
        else []
    )
    return write_json(
        evidence / "cluster.json",
        {
            "schema": qa.CLUSTER_SCHEMA,
            "cluster_id": "C-1",
            "candidate_sha": candidate,
            "source_status": {"before": "clean", "after": "clean"},
            "scenarios": [
                {
                    "id": "S-1",
                    "sources": ["release-delta:surface.txt"],
                    "procedure": "inspect the bounded fixture",
                    "controlled_environment": {"HOME": "/tmp/isolated"},
                    "expected": "candidate contract",
                    "observed": "bounded observation",
                    "outcome": outcome,
                    "evidence": [str(proof)],
                }
            ],
            "verified_findings": findings,
        },
    )


def full_spec(repo: Path, candidate: str, evidence: Path, result: Path) -> dict:
    baseline = git(repo, "rev-parse", "v1.0.0")
    commit = git(repo, "rev-list", "--reverse", f"{baseline}..{candidate}")
    return {
        "schema": qa.FULL_INPUT_SCHEMA,
        "repository": str(repo),
        "version": "v1.0.1",
        "previous_release": "v1.0.0",
        "candidate_sha": candidate,
        "evidence_root": str(evidence),
        "design_gate_state": "not_enrolled",
        "cluster_results": [str(result)],
        "commit_matrix": [{"commit": commit, "scenarios": ["S-1"]}],
        "surface_matrix": [{"path": "surface.txt", "scenarios": ["S-1"]}],
    }


def freeze(repo: Path, candidate: str, evidence: Path, outcome: str = "finding"):
    result = cluster(evidence, candidate, outcome=outcome)
    record_path = evidence / "full-record.json"
    receipt = qa.freeze_full(
        full_spec(repo, candidate, evidence, result), str(record_path)
    )
    return record_path, receipt


def remediate(repo: Path) -> str:
    (repo / "surface.txt").write_text("remediated\n", encoding="utf-8")
    git(repo, "commit", "-am", "remediate")
    return git(repo, "rev-parse", "HEAD")


def prepare(repo: Path, candidate: str, evidence: Path, record: Path) -> Path:
    manifest = evidence / "manifest.json"
    qa.prepare_confirmation(
        {
            "schema": qa.PREPARE_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "candidate_sha": candidate,
            "changed_surface_mappings": [{"path": "surface.txt", "scenarios": ["S-1"]}],
            "finding_reproductions": [{"finding_id": "F-1", "scenario_id": "S-1"}],
        },
        str(manifest),
    )
    return manifest


def test_full_findings_round_trip_to_confirmation_pass(release_case):
    repo, candidate, evidence = release_case
    record, receipt = freeze(repo, candidate, evidence)
    assert receipt["verdict"] == "FINDINGS"
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        begin = qa.begin_confirmation(
            {
                "schema": qa.BEGIN_SCHEMA,
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
                "confirmation_root": str(confirmation),
            }
        )
        confirmation_cluster = cluster(confirmation, remediated, outcome="pass")
        result_path = confirmation / "result.json"
        result = qa.finish_confirmation(
            {
                "schema": qa.FINISH_SCHEMA,
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
                "claim": begin["path"],
                "confirmation_root": str(confirmation),
                "cluster_results": [str(confirmation_cluster)],
            },
            str(result_path),
        )
        assert result["verdict"] == "PASS"
        assert result_path.stat().st_mode & 0o777 == 0o600
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize("outcome", ["pass", "gap"])
def test_only_complete_findings_can_prepare_confirmation(release_case, outcome):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence, outcome=outcome)
    remediated = remediate(repo)
    with pytest.raises(qa.EvidenceError, match="only a complete FINDINGS"):
        prepare(repo, remediated, evidence, record)


def test_freeze_rejects_missing_surface_and_duplicate_scenario(release_case):
    repo, candidate, evidence = release_case
    result = cluster(evidence, candidate)
    spec = full_spec(repo, candidate, evidence, result)
    spec["surface_matrix"] = []
    with pytest.raises(qa.EvidenceError):
        qa.freeze_full(spec, str(evidence / "record.json"))
    payload = json.loads(result.read_text())
    payload["scenarios"].append(payload["scenarios"][0])
    write_json(result, payload)
    spec = full_spec(repo, candidate, evidence, result)
    with pytest.raises(qa.EvidenceError, match="scenario IDs"):
        qa.freeze_full(spec, str(evidence / "record.json"))


def test_freeze_verdict_precedence_prefers_incomplete(release_case):
    repo, candidate, evidence = release_case
    result = cluster(evidence, candidate, outcome="gap")
    payload = json.loads(result.read_text())
    finding_scenario = dict(payload["scenarios"][0])
    finding_scenario["id"] = "S-2"
    finding_scenario["outcome"] = "finding"
    payload["scenarios"].append(finding_scenario)
    payload["verified_findings"] = [
        {"id": "F-1", "scenario_id": "S-2", "severity": "Medium"}
    ]
    write_json(result, payload)
    receipt = qa.freeze_full(
        full_spec(repo, candidate, evidence, result), str(evidence / "record.json")
    )
    assert receipt["verdict"] == "INCOMPLETE"


def test_prepare_rejects_unmapped_surface_and_missing_finding(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    base = {
        "schema": qa.PREPARE_SCHEMA,
        "repository": str(repo),
        "full_record": str(record),
        "candidate_sha": remediated,
        "changed_surface_mappings": [],
        "finding_reproductions": [],
    }
    with pytest.raises(qa.EvidenceError, match="mappings"):
        qa.prepare_confirmation(base, str(evidence / "manifest.json"))
    base["changed_surface_mappings"] = [{"path": "surface.txt", "scenarios": ["S-1"]}]
    with pytest.raises(qa.EvidenceError, match="verified finding"):
        qa.prepare_confirmation(base, str(evidence / "manifest.json"))


def test_begin_rejects_tampering_and_allows_only_one_claim(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    second = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        request = {
            "schema": qa.BEGIN_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "confirmation_root": str(confirmation),
        }
        qa.begin_confirmation(request)
        request["confirmation_root"] = str(second)
        with pytest.raises(qa.EvidenceError, match="already claimed"):
            qa.begin_confirmation(request)
        value = json.loads(record.read_text())
        value["version"] = "tampered"
        write_json(record, value)
        with pytest.raises(qa.EvidenceError, match="digest"):
            qa.begin_confirmation(request)
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)
        shutil.rmtree(second, ignore_errors=True)


def test_prepare_revalidates_frozen_verdict_and_evidence(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    value = json.loads(record.read_text())
    value["verdict"] = "PASS"
    write_json(record, value)
    with pytest.raises(qa.EvidenceError, match="verdict"):
        prepare(repo, remediated, evidence, record)


def test_prepare_rejects_non_descendant_candidate(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    git(repo, "checkout", "-b", "other", "v1.0.0")
    (repo / "other.txt").write_text("other\n", encoding="utf-8")
    git(repo, "add", "other.txt")
    git(repo, "commit", "-m", "other")
    unrelated = git(repo, "rev-parse", "HEAD")
    with pytest.raises(qa.EvidenceError):
        prepare(repo, unrelated, evidence, record)


def test_evidence_rejects_symlink_and_out_of_root(release_case, tmp_path):
    repo, candidate, evidence = release_case
    result = cluster(evidence, candidate)
    payload = json.loads(result.read_text())
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    payload["scenarios"][0]["evidence"] = [str(outside)]
    write_json(result, payload)
    with pytest.raises(qa.EvidenceError, match="outside"):
        qa.freeze_full(
            full_spec(repo, candidate, evidence, result), str(evidence / "record.json")
        )
    link = evidence / "linked.txt"
    link.symlink_to(outside)
    payload["scenarios"][0]["evidence"] = [str(link)]
    write_json(result, payload)
    with pytest.raises(qa.EvidenceError, match="non-symlink"):
        qa.freeze_full(
            full_spec(repo, candidate, evidence, result), str(evidence / "record.json")
        )


def test_finish_rejects_missing_inventory_and_source_mutation(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        begin = qa.begin_confirmation(
            {
                "schema": qa.BEGIN_SCHEMA,
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
                "confirmation_root": str(confirmation),
            }
        )
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "confirmation_root": str(confirmation),
            "cluster_results": [],
        }
        with pytest.raises(qa.EvidenceError):
            qa.finish_confirmation(request, str(confirmation / "result.json"))
        (repo / "dirty.txt").write_text("dirty", encoding="utf-8")
        request["cluster_results"] = [
            str(cluster(confirmation, remediated, outcome="pass"))
        ]
        with pytest.raises(qa.EvidenceError, match="not clean"):
            qa.finish_confirmation(request, str(confirmation / "result.json"))
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_finish_rejects_extra_or_reassigned_scenario(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        begin = qa.begin_confirmation(
            {
                "schema": qa.BEGIN_SCHEMA,
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
                "confirmation_root": str(confirmation),
            }
        )
        result_file = cluster(confirmation, remediated, outcome="pass")
        payload = json.loads(result_file.read_text())
        payload["scenarios"][0]["id"] = "S-extra"
        write_json(result_file, payload)
        with pytest.raises(qa.EvidenceError, match="inventory"):
            qa.finish_confirmation(
                {
                    "schema": qa.FINISH_SCHEMA,
                    "repository": str(repo),
                    "full_record": str(record),
                    "manifest": str(manifest),
                    "claim": begin["path"],
                    "confirmation_root": str(confirmation),
                    "cluster_results": [str(result_file)],
                },
                str(confirmation / "result.json"),
            )
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)
