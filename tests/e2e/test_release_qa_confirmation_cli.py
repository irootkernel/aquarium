from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aquarium/skills/release-qa/scripts/manage_release_qa.py"


def run(*arguments: str, expected: int = 0) -> dict:
    completed = subprocess.run(
        [str(SCRIPT), *arguments], capture_output=True, text=True, check=False
    )
    assert completed.returncode == expected, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def dump(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture
def cli_case(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "QA")
    git(repo, "config", "user.email", "qa@example.invalid")
    (repo / "contract.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "contract.txt")
    git(repo, "commit", "-m", "baseline")
    git(repo, "tag", "v1.0.0")
    (repo / "contract.txt").write_text("two\n", encoding="utf-8")
    git(repo, "commit", "-am", "candidate")
    evidence = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    yield repo, evidence
    shutil.rmtree(evidence, ignore_errors=True)


def cluster(root: Path, candidate: str, outcome: str) -> Path:
    proof = root / "proof.txt"
    proof.write_text("observation\n", encoding="utf-8")
    return dump(
        root / "cluster.json",
        {
            "schema": "aquarium-release-qa-cluster-result/v1",
            "cluster_id": "cluster-contract",
            "candidate_sha": candidate,
            "source_status": {"before": "clean", "after": "clean"},
            "scenarios": [
                {
                    "id": "scenario-contract",
                    "sources": ["release-delta:contract.txt"],
                    "procedure": "inspect isolated contract fixture",
                    "controlled_environment": {"HOME": "/tmp/isolated"},
                    "expected": "contract is usable",
                    "observed": "observation",
                    "outcome": outcome,
                    "evidence": [str(proof)],
                }
            ],
            "verified_findings": (
                [
                    {
                        "id": "finding-contract",
                        "scenario_id": "scenario-contract",
                        "severity": "Medium",
                    }
                ]
                if outcome == "finding"
                else []
            ),
        },
    )


def test_cli_freeze_prepare_begin_finish_and_single_attempt(cli_case):
    repo, evidence = cli_case
    candidate = git(repo, "rev-parse", "HEAD")
    commit = git(repo, "rev-list", "--reverse", "v1.0.0..HEAD")
    full_input = dump(
        evidence / "full-input.json",
        {
            "schema": "aquarium-release-qa-full-pass/v1",
            "repository": str(repo),
            "version": "v1.0.1",
            "previous_release": "v1.0.0",
            "candidate_sha": candidate,
            "evidence_root": str(evidence),
            "design_gate_state": "not_enrolled",
            "cluster_results": [str(cluster(evidence, candidate, "finding"))],
            "commit_matrix": [{"commit": commit, "scenarios": ["scenario-contract"]}],
            "surface_matrix": [
                {"path": "contract.txt", "scenarios": ["scenario-contract"]}
            ],
        },
    )
    record = evidence / "record.json"
    assert (
        run("freeze-full", "--input", str(full_input), "--output", str(record))[
            "verdict"
        ]
        == "FINDINGS"
    )

    (repo / "contract.txt").write_text("three\n", encoding="utf-8")
    git(repo, "commit", "-am", "remediation")
    remediated = git(repo, "rev-parse", "HEAD")
    prepare_input = dump(
        evidence / "prepare-input.json",
        {
            "schema": "aquarium-release-qa-confirmation-prepare/v1",
            "repository": str(repo),
            "full_record": str(record),
            "candidate_sha": remediated,
            "changed_surface_mappings": [
                {"path": "contract.txt", "scenarios": ["scenario-contract"]}
            ],
            "finding_reproductions": [
                {
                    "finding_id": "finding-contract",
                    "scenario_id": "scenario-contract",
                }
            ],
        },
    )
    manifest = evidence / "manifest.json"
    run(
        "prepare-confirmation",
        "--input",
        str(prepare_input),
        "--output",
        str(manifest),
    )
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    second = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        begin_input = dump(
            evidence / "begin-input.json",
            {
                "schema": "aquarium-release-qa-confirmation-begin/v1",
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
                "confirmation_root": str(confirmation),
            },
        )
        claim = run("begin-confirmation", "--input", str(begin_input))["path"]
        second_value = json.loads(begin_input.read_text())
        second_value["confirmation_root"] = str(second)
        dump(begin_input, second_value)
        error = run("begin-confirmation", "--input", str(begin_input), expected=2)
        assert error["schema"] == "aquarium-release-qa-error/v1"
        assert error["error"]["code"] == "confirmation_already_started"

        result_file = cluster(confirmation, remediated, "pass")
        finish_input = dump(
            confirmation / "finish-input.json",
            {
                "schema": "aquarium-release-qa-confirmation-finish/v1",
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
                "claim": claim,
                "confirmation_root": str(confirmation),
                "cluster_results": [str(result_file)],
            },
        )
        result = run(
            "finish-confirmation",
            "--input",
            str(finish_input),
            "--output",
            str(confirmation / "result.json"),
        )
        assert result["verdict"] == "PASS"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)
        shutil.rmtree(second, ignore_errors=True)


def test_cli_returns_structured_error_for_invalid_schema(tmp_path: Path):
    request = dump(tmp_path / "request.json", {"schema": "wrong"})
    response = run(
        "freeze-full",
        "--input",
        str(request),
        "--output",
        str(tmp_path / "output.json"),
        expected=2,
    )
    assert response == {
        "schema": "aquarium-release-qa-error/v1",
        "error": {
            "code": "schema_invalid",
            "message": "freeze input must use aquarium-release-qa-full-pass/v1",
        },
    }
