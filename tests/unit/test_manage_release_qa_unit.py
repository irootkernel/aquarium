from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
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
    path.write_bytes(qa.canonical_bytes(value))
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


def full_spec(
    repo: Path, candidate: str, evidence: Path, result: Path, *, first_release=False
) -> dict:
    baseline = git(repo, "rev-parse", "v1.0.0")
    commits = git(
        repo,
        "rev-list",
        "--reverse",
        candidate if first_release else f"{baseline}..{candidate}",
    ).splitlines()
    paths = (
        git(repo, "ls-tree", "-r", "--name-only", candidate).splitlines()
        if first_release
        else ["surface.txt"]
    )
    return {
        "schema": qa.FULL_INPUT_SCHEMA,
        "repository": str(repo),
        "version": "v1.0.1",
        "baseline_mode": "first_release" if first_release else "previous_release",
        "previous_release": None if first_release else "v1.0.0",
        "candidate_sha": candidate,
        "evidence_root": str(evidence),
        "design_gate_state": "not_enrolled",
        "active_design_gates": [],
        "design_gate_matrix": [],
        "cluster_results": [str(result)],
        "commit_matrix": [
            {"commit": commit, "scenarios": ["S-1"]} for commit in commits
        ],
        "surface_matrix": [{"path": path, "scenarios": ["S-1"]} for path in paths],
    }


def add_gate_scenarios(path: Path, *, outcome="pass") -> None:
    result = json.loads(path.read_text())
    for kind in ("positive", "failure"):
        scenario = dict(result["scenarios"][0])
        scenario.update(
            id=f"GATE-1-{kind}", sources=["design-gate:GATE-1"], outcome=outcome
        )
        result["scenarios"].append(scenario)
    write_json(path, result)


def gate_enrollment(spec: dict) -> None:
    spec.update(
        design_gate_state="enrolled",
        active_design_gates=["GATE-1"],
        design_gate_matrix=[
            {
                "gate": "GATE-1",
                "positive_scenarios": ["GATE-1-positive"],
                "failure_scenarios": ["GATE-1-failure"],
            }
        ],
    )


def freeze(
    repo: Path,
    candidate: str,
    evidence: Path,
    outcome: str = "finding",
    *,
    first_release=False,
    active_gate=False,
):
    result = cluster(evidence, candidate, outcome=outcome)
    spec = full_spec(repo, candidate, evidence, result, first_release=first_release)
    if active_gate:
        add_gate_scenarios(result)
        gate_enrollment(spec)
    record_path = evidence / "full-record.json"
    receipt = qa.freeze_full(spec, str(record_path))
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


@pytest.mark.parametrize("first_release", [False, True])
@pytest.mark.parametrize("active_gate", [False, True])
def test_full_findings_round_trip_to_confirmation_pass(
    release_case, first_release, active_gate
):
    repo, candidate, evidence = release_case
    record, receipt = freeze(
        repo, candidate, evidence, first_release=first_release, active_gate=active_gate
    )
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
        if active_gate:
            add_gate_scenarios(confirmation_cluster)
        result_path = confirmation / "result.json"
        result = qa.finish_confirmation(
            {
                "schema": qa.FINISH_SCHEMA,
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
                "claim": begin["path"],
                "claim_digest": begin["digest"],
                "confirmation_root": str(confirmation),
                "cluster_results": [str(confirmation_cluster)],
            },
            str(result_path),
        )
        assert result["verdict"] == "PASS"
        assert result_path.stat().st_mode & 0o777 == 0o600
        terminal = json.loads(result_path.read_text())
        admission_path = confirmation / (
            "settlement-admission-" + begin["digest"].removeprefix("sha256:") + ".json"
        )
        admission = json.loads(admission_path.read_text())
        assert admission["schema"] == qa.ADMISSION_SCHEMA
        assert terminal["schema"] == qa.RESULT_SCHEMA
        assert terminal["claim_digest"] == begin["digest"]
        assert terminal["admission_digest"] == qa.digest(admission)
        assert terminal["diagnostic"] is None
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "old_root",
        "old_sha",
        "escape",
        "sibling",
        "different_suffix",
        "language",
        "network",
        "baseline_sha",
        "nested",
        "missing",
        "extra",
        "sources",
        "procedure",
        "expected",
        "frozen_escape",
        "frozen_unnormalized",
    ],
)
def test_confirmation_rebinds_only_fixture_paths_and_source_sha(release_case, damage):
    repo, candidate, evidence = release_case
    original = cluster(evidence, candidate)
    full_cluster = json.loads(original.read_text())
    full_cluster["scenarios"][0]["controlled_environment"] = {
        "HOME": str(evidence / "S-1/home"),
        "fixture": str(evidence),
        "source_sha": candidate,
        "baseline_sha": candidate,
        "nested": {"outputs": [str(evidence / "S-1/output"), "/dev/null"]},
        "external": str(evidence) + "-sibling/home",
        "LC_ALL": "C",
        "network": "offline",
    }
    if damage == "frozen_escape":
        full_cluster["scenarios"][0]["controlled_environment"]["HOME"] = (
            str(evidence) + "/../outside/home"
        )
    elif damage == "frozen_unnormalized":
        full_cluster["scenarios"][0]["controlled_environment"]["HOME"] = (
            str(evidence) + "/S-1/./home"
        )
    write_json(original, full_cluster)
    record = evidence / "full-record.json"
    qa.freeze_full(full_spec(repo, candidate, evidence, original), str(record))
    record_bytes = record.read_bytes()
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    manifest_bytes = manifest.read_bytes()
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
        result = json.loads(result_file.read_text())
        scenario = result["scenarios"][0]
        environment = dict(full_cluster["scenarios"][0]["controlled_environment"])
        environment.update(
            HOME=str(confirmation / "S-1/home"),
            fixture=str(confirmation),
            source_sha=remediated,
            nested={"outputs": [str(confirmation / "S-1/output"), "/dev/null"]},
        )
        scenario["controlled_environment"] = environment
        if damage == "old_root":
            environment["HOME"] = str(evidence / "S-1/home")
        elif damage == "old_sha":
            environment["source_sha"] = candidate
        elif damage == "escape":
            environment["HOME"] = str(confirmation) + "/../outside/home"
        elif damage == "sibling":
            environment["HOME"] = str(confirmation) + "-sibling/S-1/home"
        elif damage == "different_suffix":
            environment["HOME"] = str(confirmation / "S-2/home")
        elif damage == "language":
            environment["LC_ALL"] = "en_US.UTF-8"
        elif damage == "network":
            environment["network"] = "online"
        elif damage == "baseline_sha":
            environment["baseline_sha"] = remediated
        elif damage == "nested":
            environment["nested"]["outputs"][0] = str(confirmation / "other/output")
        elif damage == "missing":
            environment.pop("network")
        elif damage == "extra":
            environment["new_condition"] = "allowed"
        elif damage in {"sources", "procedure", "expected"}:
            scenario[damage] = (
                ["different source"] if damage == "sources" else "changed"
            )
        write_json(result_file, result)
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        output = str(confirmation / "result.json")
        if damage is None:
            assert qa.finish_confirmation(request, output)["verdict"] == "PASS"
            assert qa.finish_confirmation(request, output)["verdict"] == "PASS"
        else:
            with pytest.raises(qa.EvidenceError) as rejected:
                qa.finish_confirmation(request, output)
            assert rejected.value.code == "confirmation_inventory_mismatch"
            assert json.loads(Path(output).read_text())["verdict"] == "REJECTED"
        assert record.read_bytes() == record_bytes
        assert manifest.read_bytes() == manifest_bytes
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "stale",
        "swapped",
        "arbitrary_root",
        "unlisted_path",
        "escaped_child",
        "different_child",
        "network",
        "removed_declaration",
        "missing_root",
        "public_root",
        "symlink_root",
    ],
)
def test_confirmation_rebinds_declared_native_roots(release_case, damage):
    repo, candidate, evidence = release_case
    native_roots = [
        Path(tempfile.mkdtemp(prefix="release-qa.native-full.", dir="/tmp")).resolve(),
        Path(
            tempfile.mkdtemp(prefix="release-qa.native-confirm.", dir="/tmp")
        ).resolve(),
    ]
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    fresh_roots = [
        confirmation.parent
        / ("release-qa.native-" + qa.digest([str(confirmation), str(root)])[7:])
        for root in native_roots
    ]
    for root in fresh_roots:
        root.mkdir(mode=0o700)
    try:
        original = cluster(evidence, candidate)
        full_cluster = json.loads(original.read_text())
        full_cluster["scenarios"][0]["controlled_environment"] = {
            "HOME": str(evidence / "home"),
            "source_sha": candidate,
            "native_helper_roots": [str(root) for root in native_roots],
            "input": str(native_roots[0] / "case/input.json"),
            "nested": {"outputs": [str(native_roots[1] / "case/result.json")]},
            "unlisted_path": str(native_roots[0]) + "-other/input.json",
            "network": "offline",
        }
        write_json(original, full_cluster)
        record = evidence / "record.json"
        qa.freeze_full(full_spec(repo, candidate, evidence, original), str(record))
        record_bytes = record.read_bytes()
        native_before = {root: list(root.iterdir()) for root in native_roots}
        remediated = remediate(repo)
        manifest = prepare(repo, remediated, evidence, record)
        manifest_bytes = manifest.read_bytes()
        begin_request = {
            "schema": qa.BEGIN_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "confirmation_root": str(confirmation),
        }
        begin = qa.begin_confirmation(begin_request)
        assert qa.begin_confirmation(begin_request) == begin
        result_file = cluster(confirmation, remediated, outcome="pass")
        result = json.loads(result_file.read_text())
        environment = dict(full_cluster["scenarios"][0]["controlled_environment"])
        environment.update(
            HOME=str(confirmation / "home"),
            source_sha=remediated,
            native_helper_roots=[str(root) for root in fresh_roots],
            input=str(fresh_roots[0] / "case/input.json"),
            nested={"outputs": [str(fresh_roots[1] / "case/result.json")]},
        )
        result["scenarios"][0]["controlled_environment"] = environment
        if damage == "stale":
            environment["native_helper_roots"] = [str(root) for root in native_roots]
        elif damage == "swapped":
            environment["native_helper_roots"].reverse()
        elif damage == "arbitrary_root":
            environment["native_helper_roots"][0] = str(confirmation)
        elif damage == "unlisted_path":
            environment["unlisted_path"] = str(confirmation / "other/input.json")
        elif damage == "escaped_child":
            environment["input"] = str(fresh_roots[0]) + "/../input.json"
        elif damage == "different_child":
            environment["input"] = str(fresh_roots[0] / "other/input.json")
        elif damage == "network":
            environment["network"] = "online"
        elif damage == "removed_declaration":
            environment.pop("native_helper_roots")
        elif damage == "missing_root":
            fresh_roots[0].rmdir()
        elif damage == "public_root":
            fresh_roots[0].chmod(0o755)
        elif damage == "symlink_root":
            fresh_roots[0].rmdir()
            fresh_roots[0].symlink_to(native_roots[0], target_is_directory=True)
        write_json(result_file, result)
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        output = str(confirmation / "result.json")
        if damage is None:
            assert qa.finish_confirmation(request, output)["verdict"] == "PASS"
            assert qa.finish_confirmation(request, output)["verdict"] == "PASS"
            settled = json.loads(Path(output).read_text())
            assert settled["clusters"][0]["scenarios"][0]["controlled_environment"] == (
                environment
            )
        else:
            with pytest.raises(qa.EvidenceError) as rejected:
                qa.finish_confirmation(request, output)
            assert rejected.value.code == (
                "evidence_root_invalid"
                if damage in {"missing_root", "public_root", "symlink_root"}
                else "confirmation_inventory_mismatch"
            )
            assert json.loads(Path(output).read_text())["verdict"] == "REJECTED"
        assert record.read_bytes() == record_bytes
        assert manifest.read_bytes() == manifest_bytes
        assert {root: list(root.iterdir()) for root in native_roots} == native_before
        assert git(repo, "status", "--porcelain") == ""
    finally:
        for root in fresh_roots:
            if root.is_symlink():
                root.unlink()
            else:
                shutil.rmtree(root, ignore_errors=True)
        for root in [confirmation, *native_roots]:
            shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "public",
        "symlink",
        "escape",
        "outside_tmp",
        "duplicate",
        "reuse_retained",
    ],
)
def test_native_root_prerequisites_fail_before_confirmation_claim(release_case, damage):
    repo, candidate, evidence = release_case
    native = Path(tempfile.mkdtemp(prefix="release-qa.native.", dir="/tmp")).resolve()
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    fresh = confirmation.parent / (
        "release-qa.native-" + qa.digest([str(confirmation), str(native)])[7:]
    )
    fresh.mkdir(mode=0o700)
    try:
        original = cluster(evidence, candidate)
        value = json.loads(original.read_text())
        roots = [str(native)]
        if damage == "escape":
            roots[0] += "/../release-qa.elsewhere"
        elif damage == "outside_tmp":
            roots[0] = str(repo / "release-qa.native")
        elif damage == "duplicate":
            roots.append(roots[0])
        elif damage == "reuse_retained":
            roots.append(str(fresh))
        value["scenarios"][0]["controlled_environment"]["native_helper_roots"] = roots
        write_json(original, value)
        record = evidence / "record.json"
        qa.freeze_full(full_spec(repo, candidate, evidence, original), str(record))
        remediated = remediate(repo)
        manifest = prepare(repo, remediated, evidence, record)
        if damage == "missing":
            fresh.rmdir()
        elif damage == "public":
            fresh.chmod(0o755)
        elif damage == "symlink":
            fresh.rmdir()
            fresh.symlink_to(native, target_is_directory=True)
        with pytest.raises(qa.EvidenceError) as rejected:
            qa.begin_confirmation(
                {
                    "schema": qa.BEGIN_SCHEMA,
                    "repository": str(repo),
                    "full_record": str(record),
                    "manifest": str(manifest),
                    "confirmation_root": str(confirmation),
                }
            )
        assert rejected.value.code == (
            "duplicate_identity" if damage == "duplicate" else "evidence_root_invalid"
        )
        assert not list(evidence.glob("confirmation-attempt-*.json"))
    finally:
        if fresh.is_symlink():
            fresh.unlink()
        else:
            shutil.rmtree(fresh, ignore_errors=True)
        for root in [native, confirmation]:
            shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("root_only", [False, True])
def test_first_release_includes_root_and_complete_current_tree(release_case, root_only):
    repo, candidate, evidence = release_case
    if root_only:
        git(repo, "reset", "--hard", "HEAD^")
    else:
        (repo / "unchanged.txt").write_text("public root surface\n")
        git(repo, "add", "unchanged.txt")
        git(repo, "commit", "-m", "add public surface")
        remediate(repo)
    candidate = git(repo, "rev-parse", "HEAD")
    record, receipt = freeze(repo, candidate, evidence, "pass", first_release=True)
    value, _, _ = qa.validate_record(repo, str(record))
    assert receipt["verdict"] == "PASS"
    assert value["baseline_mode"] == "first_release"
    assert value["previous_release"] is None and value["baseline_sha"] is None
    assert [row["commit"] for row in value["commit_matrix"]] == git(
        repo, "rev-list", "--reverse", "HEAD"
    ).splitlines()
    assert {row["path"] for row in value["surface_matrix"]} == set(
        git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    )


@pytest.mark.parametrize("missing", ["root", "surface"])
def test_first_release_rejects_incomplete_scope(release_case, missing):
    repo, candidate, evidence = release_case
    spec = full_spec(
        repo, candidate, evidence, cluster(evidence, candidate), first_release=True
    )
    if missing == "root":
        spec["commit_matrix"].pop(0)
    else:
        spec["surface_matrix"] = [{"path": "wrong.txt", "scenarios": ["S-1"]}]
    with pytest.raises(qa.EvidenceError):
        qa.freeze_full(spec, str(evidence / "record.json"))


@pytest.mark.parametrize(
    "mode,previous",
    [(None, None), ("first_release", "v1.0.0"), ("previous_release", None)],
)
def test_full_pass_rejects_ambiguous_baseline(release_case, mode, previous):
    repo, candidate, evidence = release_case
    spec = full_spec(repo, candidate, evidence, cluster(evidence, candidate))
    spec.update(baseline_mode=mode, previous_release=previous)
    with pytest.raises(qa.EvidenceError):
        qa.freeze_full(spec, str(evidence / "record.json"))


def test_record_rejects_retargeted_previous_release(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    git(repo, "tag", "-f", "v1.0.0", candidate)
    with pytest.raises(qa.EvidenceError, match="baseline"):
        qa.validate_record(repo, str(record))


def test_previous_release_must_be_an_ancestor(release_case):
    repo, candidate, evidence = release_case
    spec = full_spec(repo, candidate, evidence, cluster(evidence, candidate))
    git(repo, "checkout", "-b", "other-release", "v1.0.0")
    (repo / "surface.txt").write_text("different release line\n")
    git(repo, "commit", "-am", "other release")
    git(repo, "tag", "v2.0.0")
    git(repo, "checkout", "main")
    spec["previous_release"] = "v2.0.0"
    with pytest.raises(qa.EvidenceError) as rejected:
        qa.freeze_full(spec, str(evidence / "record.json"))
    assert rejected.value.code == "git_invalid"


def test_enrolled_registry_can_have_no_active_gates(release_case):
    repo, candidate, evidence = release_case
    spec = full_spec(
        repo, candidate, evidence, cluster(evidence, candidate, outcome="pass")
    )
    spec["design_gate_state"] = "enrolled"
    assert qa.freeze_full(spec, str(evidence / "record.json"))["verdict"] == "PASS"


@pytest.mark.parametrize(
    "field,value",
    [
        ("previous_release", "v1.0.0"),
        ("baseline_sha", "a" * 40),
        ("baseline_mode", None),
    ],
)
def test_first_release_record_rejects_conflicting_identity(release_case, field, value):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence, first_release=True)
    raw = json.loads(record.read_text())
    raw[field] = value
    write_json(record, raw)
    with pytest.raises(qa.EvidenceError):
        qa.load_record(str(record))


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "unknown",
        "shared_delta",
        "unenrolled",
        "duplicate",
        "empty_positive",
        "empty_failure",
    ],
)
def test_active_gate_matrix_requires_independent_complete_evidence(
    release_case, damage
):
    repo, candidate, evidence = release_case
    result = cluster(evidence, candidate)
    add_gate_scenarios(result)
    spec = full_spec(repo, candidate, evidence, result)
    gate_enrollment(spec)
    if damage == "missing":
        spec["design_gate_matrix"] = []
    elif damage == "unknown":
        spec["design_gate_matrix"][0]["failure_scenarios"] = ["unknown"]
    elif damage == "shared_delta":
        spec["design_gate_matrix"][0]["positive_scenarios"] = ["S-1"]
    elif damage == "duplicate":
        spec["design_gate_matrix"].append(dict(spec["design_gate_matrix"][0]))
    elif damage.startswith("empty_"):
        kind = damage.removeprefix("empty_")
        spec["design_gate_matrix"][0][f"{kind}_scenarios"] = []
    else:
        spec["design_gate_state"] = "not_enrolled"
    with pytest.raises(qa.EvidenceError):
        qa.freeze_full(spec, str(evidence / "record.json"))


def test_active_gate_gap_prevents_full_pass(release_case):
    repo, candidate, evidence = release_case
    result = cluster(evidence, candidate, outcome="pass")
    add_gate_scenarios(result, outcome="gap")
    spec = full_spec(repo, candidate, evidence, result)
    gate_enrollment(spec)
    assert (
        qa.freeze_full(spec, str(evidence / "record.json"))["verdict"] == "INCOMPLETE"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("baseline_mode", "previous_release"),
        ("previous_release", "v1.0.0"),
        ("baseline_sha", "a" * 40),
        ("active_design_gates", []),
        ("design_gate_matrix", []),
        ("design_gate_state", "not_enrolled"),
    ],
)
def test_confirmation_preserves_first_release_and_active_gate_identity(
    release_case, field, value
):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence, first_release=True, active_gate=True)
    manifest = prepare(repo, remediate(repo), evidence, record)
    raw = json.loads(manifest.read_text())
    raw[field] = value
    write_json(manifest, raw)
    with pytest.raises(qa.EvidenceError, match="release identity"):
        qa.load_confirmation(
            {
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
            }
        )


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
    with pytest.raises(qa.EvidenceError, match="frozen finding-to-scenario"):
        qa.prepare_confirmation(base, str(evidence / "manifest.json"))


def test_begin_is_idempotent_and_rejects_conflicting_claim(release_case):
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
        first = qa.begin_confirmation(request)
        assert qa.begin_confirmation(request) == first
        request["confirmation_root"] = str(second)
        with pytest.raises(qa.EvidenceError) as mismatched:
            qa.begin_confirmation(request)
        assert mismatched.value.code == "claim_invalid"
        value = json.loads(record.read_text())
        value["version"] = "tampered"
        write_json(record, value)
        with pytest.raises(qa.EvidenceError, match="digest"):
            qa.begin_confirmation(request)
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)
        shutil.rmtree(second, ignore_errors=True)


def test_concurrent_identical_begin_returns_one_claim(release_case, monkeypatch):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        request = {
            "schema": qa.BEGIN_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "confirmation_root": str(confirmation),
        }
        barrier = threading.Barrier(2)
        original_create = qa.create_once_write

        def synchronized_create(path, value):
            if Path(path).name.startswith("confirmation-attempt-"):
                barrier.wait(timeout=5)
            return original_create(path, value)

        monkeypatch.setattr(qa, "create_once_write", synchronized_create)
        with ThreadPoolExecutor(max_workers=2) as executor:
            receipts = list(
                executor.map(lambda _: qa.begin_confirmation(request), range(2))
            )

        assert receipts[0] == receipts[1]
        assert len(list(evidence.glob("confirmation-attempt-*.json"))) == 1
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


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


@pytest.mark.parametrize("suffix", ["/.", "/..", "/"])
def test_output_normalization_rejects_non_file_basename(suffix):
    root = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    child = root / "child"
    child.mkdir()
    try:
        with pytest.raises(qa.EvidenceError) as invalid:
            qa.output_under(root, str(child) + suffix, "output")
        assert invalid.value.code == "output_invalid"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_output_normalization_bounds_basename_bytes():
    root = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        accepted = root / ("a" * qa.MAX_OUTPUT_BASENAME_BYTES)
        assert qa.output_under(root, str(accepted), "output") == accepted

        oversized = root / ("a" * (qa.MAX_OUTPUT_BASENAME_BYTES + 1))
        with pytest.raises(qa.EvidenceError) as invalid:
            qa.output_under(root, str(oversized), "output")
        assert invalid.value.code == "output_invalid"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_finish_rejects_long_output_before_admission(release_case):
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
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(cluster(confirmation, remediated, outcome="pass"))],
        }
        output = confirmation / ("a" * (qa.MAX_OUTPUT_BASENAME_BYTES + 1))
        with pytest.raises(qa.EvidenceError) as invalid:
            qa.finish_confirmation(request, str(output))
        assert invalid.value.code == "output_invalid"
        assert not list(confirmation.glob("settlement-admission-*.json"))
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_finish_rejects_output_alias_of_admission_before_consuming_claim(release_case):
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
        alias_parent = confirmation / "alias"
        alias_parent.mkdir()
        admission_name = (
            "settlement-admission-" + begin["digest"].removeprefix("sha256:") + ".json"
        )
        aliased_output = alias_parent / ".." / admission_name
        with pytest.raises(qa.EvidenceError) as invalid:
            qa.finish_confirmation(
                {
                    "schema": qa.FINISH_SCHEMA,
                    "repository": str(repo),
                    "full_record": str(record),
                    "manifest": str(manifest),
                    "claim": begin["path"],
                    "claim_digest": begin["digest"],
                    "confirmation_root": str(confirmation),
                    "cluster_results": [str(result_file)],
                },
                str(aliased_output),
            )
        assert invalid.value.code == "output_invalid"
        assert not (confirmation / admission_name).exists()

        with pytest.raises(qa.EvidenceError) as case_variant:
            qa.finish_confirmation(
                {
                    "schema": qa.FINISH_SCHEMA,
                    "repository": str(repo),
                    "full_record": str(record),
                    "manifest": str(manifest),
                    "claim": begin["path"],
                    "claim_digest": begin["digest"],
                    "confirmation_root": str(confirmation),
                    "cluster_results": [str(result_file)],
                },
                str(confirmation / admission_name.upper()),
            )
        assert case_variant.value.code == "output_invalid"
        assert not (confirmation / admission_name).exists()
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_finish_rejection_consumes_claim_and_changed_retry_is_replay(release_case):
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
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [],
        }
        result_path = confirmation / "result.json"
        with pytest.raises(qa.EvidenceError) as rejected:
            qa.finish_confirmation(request, str(confirmation / "result.json"))
        assert rejected.value.code == "field_invalid"
        terminal = json.loads(result_path.read_text())
        assert terminal["verdict"] == "REJECTED"
        assert terminal["clusters"] == []
        assert terminal["diagnostic"]["code"] == "field_invalid"
        (repo / "dirty.txt").write_text("dirty", encoding="utf-8")
        request["cluster_results"] = [
            str(cluster(confirmation, remediated, outcome="pass"))
        ]
        with pytest.raises(qa.EvidenceError) as replay:
            qa.finish_confirmation(request, str(confirmation / "result.json"))
        assert replay.value.code == "settlement_replay"
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
                    "claim_digest": begin["digest"],
                    "confirmation_root": str(confirmation),
                    "cluster_results": [str(result_file)],
                },
                str(confirmation / "result.json"),
            )
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_finish_matches_scenarios_by_identity_not_position(release_case):
    repo, candidate, evidence = release_case
    frozen_cluster = cluster(evidence, candidate)
    frozen = json.loads(frozen_cluster.read_text())
    second = dict(frozen["scenarios"][0])
    second["id"] = "S-2"
    second["outcome"] = "pass"
    frozen["scenarios"].append(second)
    write_json(frozen_cluster, frozen)
    record_path = evidence / "full-record.json"
    qa.freeze_full(
        full_spec(repo, candidate, evidence, frozen_cluster), str(record_path)
    )
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record_path)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        begin = qa.begin_confirmation(
            {
                "schema": qa.BEGIN_SCHEMA,
                "repository": str(repo),
                "full_record": str(record_path),
                "manifest": str(manifest),
                "confirmation_root": str(confirmation),
            }
        )
        fresh_cluster = cluster(confirmation, remediated, outcome="pass")
        fresh = json.loads(fresh_cluster.read_text())
        second = dict(fresh["scenarios"][0])
        second["id"] = "S-2"
        fresh["scenarios"] = [second, fresh["scenarios"][0]]
        write_json(fresh_cluster, fresh)
        receipt = qa.finish_confirmation(
            {
                "schema": qa.FINISH_SCHEMA,
                "repository": str(repo),
                "full_record": str(record_path),
                "manifest": str(manifest),
                "claim": begin["path"],
                "claim_digest": begin["digest"],
                "confirmation_root": str(confirmation),
                "cluster_results": [str(fresh_cluster)],
            },
            str(confirmation / "result.json"),
        )
        assert receipt["verdict"] == "PASS"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_authority_outputs_are_create_once_and_claim_is_exact(release_case):
    repo, candidate, evidence = release_case
    result = cluster(evidence, candidate)
    record = evidence / "record.json"
    spec = full_spec(repo, candidate, evidence, result)
    qa.freeze_full(spec, str(record))
    assert record.stat().st_mode & 0o777 == 0o600
    original = record.read_bytes()
    with pytest.raises(qa.EvidenceError) as frozen:
        qa.freeze_full(spec, str(record))
    assert frozen.value.code == "output_exists"
    assert record.read_bytes() == original

    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    assert manifest.stat().st_mode & 0o777 == 0o600
    manifest_bytes = manifest.read_bytes()
    with pytest.raises(qa.EvidenceError) as prepared:
        prepare(repo, remediated, evidence, record)
    assert prepared.value.code == "output_exists"
    assert manifest.read_bytes() == manifest_bytes

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
        claim = json.loads(Path(begin["path"]).read_text())
        assert begin["digest"] == qa.digest(claim)
        assert claim == {
            "schema": qa.CLAIM_SCHEMA,
            "full_record": str(record),
            "full_record_digest": qa.digest(json.loads(record.read_text())),
            "manifest": str(manifest),
            "manifest_digest": qa.digest(json.loads(manifest.read_text())),
            "full_candidate_sha": candidate,
            "candidate_sha": remediated,
            "full_evidence_root": str(evidence),
            "confirmation_root": str(confirmation),
            "confirmation_attempt": 1,
        }
        assert Path(begin["path"]).stat().st_mode & 0o777 == 0o600
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_prepare_requires_exact_finding_scenario_pairs(release_case):
    repo, candidate, evidence = release_case
    result = cluster(evidence, candidate)
    payload = json.loads(result.read_text())
    second = dict(payload["scenarios"][0])
    second["id"] = "S-2"
    payload["scenarios"].append(second)
    payload["verified_findings"].append(
        {"id": "F-2", "scenario_id": "S-2", "severity": "Low"}
    )
    write_json(result, payload)
    record = evidence / "record.json"
    qa.freeze_full(full_spec(repo, candidate, evidence, result), str(record))
    remediated = remediate(repo)
    request = {
        "schema": qa.PREPARE_SCHEMA,
        "repository": str(repo),
        "full_record": str(record),
        "candidate_sha": remediated,
        "changed_surface_mappings": [{"path": "surface.txt", "scenarios": ["S-1"]}],
        "finding_reproductions": [
            {"finding_id": "F-1", "scenario_id": "S-2"},
            {"finding_id": "F-2", "scenario_id": "S-1"},
        ],
    }
    with pytest.raises(qa.EvidenceError) as mismatch:
        qa.prepare_confirmation(request, str(evidence / "manifest.json"))
    assert mismatch.value.code == "finding_reproduction_mismatch"


def test_finish_rejects_wrong_claim_digest_before_result(release_case):
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
        result_path = confirmation / "result.json"
        with pytest.raises(qa.EvidenceError) as mismatch:
            qa.finish_confirmation(
                {
                    "schema": qa.FINISH_SCHEMA,
                    "repository": str(repo),
                    "full_record": str(record),
                    "manifest": str(manifest),
                    "claim": begin["path"],
                    "claim_digest": "sha256:" + "0" * 64,
                    "confirmation_root": str(confirmation),
                    "cluster_results": [
                        str(cluster(confirmation, remediated, outcome="pass"))
                    ],
                },
                str(result_path),
            )
        assert mismatch.value.code == "claim_digest_mismatch"
        assert not result_path.exists()
        assert not list(confirmation.glob("settlement-admission-*.json"))
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize("value", [None, 1, [], {}, "", "x" * 4097])
def test_changed_schema_text_fields_reject_invalid_bounds(value):
    with pytest.raises(qa.EvidenceError) as invalid:
        qa.text(value, "changed_schema_field")
    assert invalid.value.code == "field_invalid"


def test_changed_schema_shared_boundaries_are_closed_and_deduplicated():
    assert qa.text("x" * 4096, "changed_schema_field") == "x" * 4096
    with pytest.raises(qa.EvidenceError) as missing:
        qa.require_fields({"schema": "v"}, "changed schema", {"schema", "value"})
    assert missing.value.code == "schema_invalid"
    with pytest.raises(qa.EvidenceError) as additional:
        qa.require_fields(
            {"schema": "v", "value": "x", "extra": True},
            "changed schema",
            {"schema", "value"},
        )
    assert additional.value.code == "schema_invalid"
    with pytest.raises(qa.EvidenceError) as duplicate:
        qa.string_list(["same", "same"], "changed_schema_list")
    assert duplicate.value.code == "duplicate_identity"


@pytest.mark.parametrize(
    ("operation", "schema"),
    [
        (qa.prepare_confirmation, qa.PREPARE_SCHEMA),
        (qa.begin_confirmation, qa.BEGIN_SCHEMA),
    ],
)
def test_changed_command_schemas_reject_missing_and_additional_fields(
    operation, schema, tmp_path
):
    with pytest.raises(qa.EvidenceError) as invalid:
        if operation is qa.prepare_confirmation:
            operation({"schema": schema, "extra": True}, str(tmp_path / "output"))
        else:
            operation({"schema": schema, "extra": True})
    assert invalid.value.code == "schema_invalid"


def test_finish_schema_rejects_shape_errors_before_admission(tmp_path):
    for spec in (
        {"schema": qa.FINISH_SCHEMA},
        {"schema": qa.FINISH_SCHEMA, "extra": True},
        {"schema": "wrong"},
    ):
        with pytest.raises(qa.EvidenceError) as invalid:
            qa.finish_confirmation(spec, str(tmp_path / "result.json"))
        assert invalid.value.code == "schema_invalid"
    assert not list(tmp_path.glob("settlement-admission-*.json"))


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [("pass", "PASS"), ("finding", "FINDINGS"), ("gap", "INCOMPLETE")],
)
def test_finish_persists_every_non_rejected_terminal_outcome(
    release_case, outcome, expected
):
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
        result_file = cluster(confirmation, remediated, outcome=outcome)
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        result_path = confirmation / "result.json"
        first = qa.finish_confirmation(request, str(result_path))
        second = qa.finish_confirmation(request, str(result_path))
        assert first == second
        assert first["verdict"] == expected
        assert json.loads(result_path.read_text())["verdict"] == expected
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize(
    "damage",
    [
        "verdict",
        "outcome_and_verdict",
        "observed",
        "findings",
        "inventory",
        "cluster_changed",
        "evidence_changed",
        "evidence_missing",
    ],
)
def test_terminal_replay_requires_admitted_outcomes(release_case, damage):
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
        result_file = cluster(confirmation, remediated, outcome="gap")
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        output = confirmation / "result.json"
        assert qa.finish_confirmation(request, str(output))["verdict"] == "INCOMPLETE"
        terminal = json.loads(output.read_text())
        scenario = terminal["clusters"][0]["scenarios"][0]
        if damage == "verdict":
            terminal["verdict"] = "PASS"
        elif damage == "outcome_and_verdict":
            scenario["outcome"] = "pass"
            terminal["verdict"] = "PASS"
        elif damage == "observed":
            scenario["observed"] = "different observation"
        elif damage == "findings":
            scenario["outcome"] = "finding"
            terminal["verdict"] = "FINDINGS"
            terminal["clusters"][0]["verified_findings"] = [
                {"id": "F-2", "scenario_id": "S-1", "severity": "High"}
            ]
        elif damage == "inventory":
            scenario["id"] = "different-scenario"
        elif damage == "cluster_changed":
            value = json.loads(result_file.read_text())
            value["scenarios"][0]["observed"] = "changed admitted observation"
            write_json(result_file, value)
        elif damage == "evidence_changed":
            (confirmation / "scenario.txt").write_text("changed evidence\n")
        else:
            (confirmation / "scenario.txt").unlink()
        write_json(output, terminal)
        admission = qa.settlement_admission_path(confirmation, begin["digest"])
        terminal_bytes, admission_bytes = output.read_bytes(), admission.read_bytes()

        with pytest.raises(qa.EvidenceError) as rejected:
            qa.finish_confirmation(request, str(output))

        assert rejected.value.code == "result_invalid"
        assert output.read_bytes() == terminal_bytes
        assert admission.read_bytes() == admission_bytes
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize(
    "boundary",
    ["before_admission", "after_admission", "during_recovery", "after_terminal"],
)
@pytest.mark.parametrize("_repetition", range(2))
def test_finish_interruption_boundaries_are_deterministic(
    release_case, monkeypatch, boundary, _repetition
):
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
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        output = str(confirmation / "result.json")
        original_snapshot = qa.snapshot_submission
        original_validate = qa.validate_settlement
        original_verify = qa.verify_submission_snapshot
        original_receipt = qa.terminal_receipt

        def interrupted(*_args, **_kwargs):
            raise KeyboardInterrupt

        if boundary == "before_admission":
            monkeypatch.setattr(qa, "snapshot_submission", interrupted)
        elif boundary in {"after_admission", "during_recovery"}:
            monkeypatch.setattr(qa, "validate_settlement", interrupted)
        else:
            monkeypatch.setattr(qa, "terminal_receipt", interrupted)
        with pytest.raises(KeyboardInterrupt):
            qa.finish_confirmation(request, output)
        admissions = list(confirmation.glob("settlement-admission-*.json"))
        assert len(admissions) == (0 if boundary == "before_admission" else 1)
        assert Path(output).exists() == (boundary == "after_terminal")

        monkeypatch.setattr(qa, "snapshot_submission", original_snapshot)
        monkeypatch.setattr(qa, "validate_settlement", original_validate)
        monkeypatch.setattr(qa, "terminal_receipt", original_receipt)
        if boundary == "during_recovery":
            monkeypatch.setattr(qa, "verify_submission_snapshot", interrupted)
            with pytest.raises(KeyboardInterrupt):
                qa.finish_confirmation(request, output)
            assert len(list(confirmation.glob("settlement-admission-*.json"))) == 1
            assert not Path(output).exists()
            monkeypatch.setattr(qa, "verify_submission_snapshot", original_verify)

        receipt = qa.finish_confirmation(request, output)
        terminal_bytes = Path(output).read_bytes()
        assert receipt["verdict"] == "PASS"
        assert qa.finish_confirmation(request, output) == receipt
        alias_parent = confirmation / "alias"
        alias_parent.mkdir()
        alias_output = str(alias_parent / ".." / "result.json")
        assert qa.finish_confirmation(request, alias_output) == receipt
        assert Path(output).read_bytes() == terminal_bytes
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize("tampered_field", ["cluster_results", "snapshot_error"])
def test_exact_retry_rejects_admission_evidence_tampering(
    release_case, monkeypatch, tampered_field
):
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
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        output = str(confirmation / "result.json")
        original_validate = qa.validate_settlement
        monkeypatch.setattr(
            qa,
            "validate_settlement",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
        )
        with pytest.raises(KeyboardInterrupt):
            qa.finish_confirmation(request, output)
        monkeypatch.setattr(qa, "validate_settlement", original_validate)

        admission_path = next(confirmation.glob("settlement-admission-*.json"))
        admission = json.loads(admission_path.read_text())
        if tampered_field == "cluster_results":
            alternate = confirmation / "cluster-alternate.json"
            alternate.write_bytes(result_file.read_bytes())
            admission["cluster_results"][0]["path"] = str(alternate)
        else:
            admission["snapshot_error"] = {
                "code": "input_invalid",
                "message": "tampered snapshot error",
            }
        write_json(admission_path, admission)

        with pytest.raises(qa.EvidenceError) as rejected:
            qa.finish_confirmation(request, output)
        assert rejected.value.code == "admission_invalid"
        terminal = json.loads(Path(output).read_text())
        assert terminal["verdict"] == "REJECTED"
        assert terminal["diagnostic"]["code"] == "admission_invalid"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_interrupted_settlement_reports_pending_for_changed_request(
    release_case, monkeypatch
):
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
        first_result = cluster(confirmation, remediated, outcome="pass")
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(first_result)],
        }
        output = str(confirmation / "result.json")
        original = qa.validate_settlement
        monkeypatch.setattr(
            qa,
            "validate_settlement",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
        )
        with pytest.raises(KeyboardInterrupt):
            qa.finish_confirmation(request, output)
        monkeypatch.setattr(qa, "validate_settlement", original)

        second_result = confirmation / "cluster-second.json"
        second_result.write_bytes(first_result.read_bytes())
        changed = {**request, "cluster_results": [str(second_result)]}
        with pytest.raises(qa.EvidenceError) as pending:
            qa.finish_confirmation(changed, output)
        assert pending.value.code == "settlement_pending"
        assert output in str(pending.value)
        assert not Path(output).exists()

        alternate_output = str(confirmation / "alternate-result.json")
        with pytest.raises(qa.EvidenceError) as output_pending:
            qa.finish_confirmation(request, alternate_output)
        assert output_pending.value.code == "settlement_pending"
        assert output in str(output_pending.value)

        assert qa.finish_confirmation(request, output)["verdict"] == "PASS"
        with pytest.raises(qa.EvidenceError) as output_replay:
            qa.finish_confirmation(request, alternate_output)
        assert output_replay.value.code == "settlement_replay"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_transient_settlement_failure_remains_recoverable(release_case, monkeypatch):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        begin_input = {
            "schema": qa.BEGIN_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "confirmation_root": str(confirmation),
        }
        begin = qa.begin_confirmation(begin_input)
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(cluster(confirmation, remediated, outcome="pass"))],
        }
        output = str(confirmation / "result.json")
        original = qa.validate_settlement
        monkeypatch.setattr(
            qa,
            "validate_settlement",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("temporary")),
        )
        with pytest.raises(OSError, match="temporary"):
            qa.finish_confirmation(request, output)
        assert len(list(confirmation.glob("settlement-admission-*.json"))) == 1
        assert not Path(output).exists()
        with pytest.raises(qa.EvidenceError) as pending_begin:
            qa.begin_confirmation(begin_input)
        assert pending_begin.value.code == "confirmation_already_started"

        monkeypatch.setattr(qa, "validate_settlement", original)
        assert qa.finish_confirmation(request, output)["verdict"] == "PASS"
        with pytest.raises(qa.EvidenceError) as settled_begin:
            qa.begin_confirmation(begin_input)
        assert settled_begin.value.code == "confirmation_already_started"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_finish_changed_evidence_after_interruption_is_incomplete(
    release_case, monkeypatch
):
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
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        original = qa.validate_settlement
        monkeypatch.setattr(
            qa,
            "validate_settlement",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
        )
        with pytest.raises(KeyboardInterrupt):
            qa.finish_confirmation(request, str(confirmation / "result.json"))
        monkeypatch.setattr(qa, "validate_settlement", original)
        (confirmation / "scenario.txt").write_text("replacement\n", encoding="utf-8")
        receipt = qa.finish_confirmation(request, str(confirmation / "result.json"))
        assert receipt["verdict"] == "INCOMPLETE"
        terminal = json.loads((confirmation / "result.json").read_text())
        assert terminal["diagnostic"]["code"] == "settlement_evidence_changed"
        (confirmation / "scenario.txt").write_text("bounded observation\n")
        assert (
            qa.finish_confirmation(request, str(confirmation / "result.json"))
            == receipt
        )
        assert json.loads((confirmation / "result.json").read_text()) == terminal
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_finish_verdict_uses_the_verified_cluster_bytes(release_case, monkeypatch):
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
        result_file = cluster(confirmation, remediated, outcome="gap")
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        original_clean = qa.clean_exact_main

        def rewrite_after_verification(repository, candidate_sha):
            original_clean(repository, candidate_sha)
            cluster(confirmation, remediated, outcome="pass")

        monkeypatch.setattr(qa, "clean_exact_main", rewrite_after_verification)
        output = confirmation / "result.json"
        receipt = qa.finish_confirmation(request, str(output))

        assert receipt["verdict"] == "INCOMPLETE"
        assert json.loads(result_file.read_text())["scenarios"][0]["outcome"] == "pass"
        terminal = json.loads(output.read_text())
        assert terminal["clusters"][0]["scenarios"][0]["outcome"] == "gap"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize(
    "malformed_field",
    ["cluster_results_type", "cluster_fields", "evidence_shape", "snapshot_error"],
)
def test_canonical_malformed_admission_settles_rejected(
    release_case, monkeypatch, malformed_field
):
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
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(cluster(confirmation, remediated, outcome="pass"))],
        }
        output = str(confirmation / "result.json")
        original_validate = qa.validate_settlement
        monkeypatch.setattr(
            qa,
            "validate_settlement",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
        )
        with pytest.raises(KeyboardInterrupt):
            qa.finish_confirmation(request, output)
        monkeypatch.setattr(qa, "validate_settlement", original_validate)

        admission_path = next(confirmation.glob("settlement-admission-*.json"))
        admission = json.loads(admission_path.read_text())
        if malformed_field == "cluster_results_type":
            admission["cluster_results"] = {}
        elif malformed_field == "cluster_fields":
            admission["cluster_results"][0].pop("path")
        elif malformed_field == "evidence_shape":
            admission["cluster_results"][0]["evidence"] = ["not-an-object"]
        else:
            admission["snapshot_error"] = {"code": "input_invalid"}
        write_json(admission_path, admission)

        for _ in range(2):
            with pytest.raises(qa.EvidenceError) as rejected:
                qa.finish_confirmation(request, output)
            assert rejected.value.code == "admission_invalid"
        terminal = json.loads(Path(output).read_text())
        assert terminal["verdict"] == "REJECTED"
        assert terminal["diagnostic"]["code"] == "admission_invalid"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize("missing_gate", [False, True])
def test_rejected_evidence_cannot_be_corrected_with_same_request(
    release_case, missing_gate
):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence, active_gate=missing_gate)
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
        if not missing_gate:
            invalid = json.loads(result_file.read_text())
            invalid["scenarios"][0]["id"] = "S-wrong"
            write_json(result_file, invalid)
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        output = str(confirmation / "result.json")
        with pytest.raises(qa.EvidenceError) as rejected:
            qa.finish_confirmation(request, output)
        assert rejected.value.code == "confirmation_inventory_mismatch"
        cluster(confirmation, remediated, outcome="pass")
        if missing_gate:
            add_gate_scenarios(result_file)
        with pytest.raises(qa.EvidenceError) as still_rejected:
            qa.finish_confirmation(request, output)
        assert still_rejected.value.code == "confirmation_inventory_mismatch"
        assert json.loads(Path(output).read_text())["verdict"] == "REJECTED"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_settlement_artifacts_are_create_once_and_detect_tampering(release_case):
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
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(cluster(confirmation, remediated, outcome="pass"))],
        }
        result_path = confirmation / "result.json"
        qa.finish_confirmation(request, str(result_path))
        admission_path = next(confirmation.glob("settlement-admission-*.json"))
        admission_bytes = admission_path.read_bytes()
        result_bytes = result_path.read_bytes()
        assert admission_path.stat().st_mode & 0o777 == 0o600
        assert result_path.stat().st_mode & 0o777 == 0o600
        for path, original in (
            (admission_path, admission_bytes),
            (result_path, result_bytes),
        ):
            with pytest.raises(qa.EvidenceError) as replacement:
                qa.create_once_write(path, {"replacement": True})
            assert replacement.value.code == "output_exists"
            assert path.read_bytes() == original

        tampered_admission = json.loads(admission_bytes)
        tampered_admission["extra"] = True
        write_json(admission_path, tampered_admission)
        with pytest.raises(qa.EvidenceError) as admission_invalid:
            qa.finish_confirmation(request, str(result_path))
        assert admission_invalid.value.code == "schema_invalid"
        assert result_path.read_bytes() == result_bytes
        admission_path.write_bytes(admission_bytes)

        tampered_result = json.loads(result_bytes)
        tampered_result["extra"] = True
        write_json(result_path, tampered_result)
        with pytest.raises(qa.EvidenceError) as result_invalid:
            qa.finish_confirmation(request, str(result_path))
        assert result_invalid.value.code == "schema_invalid"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_every_authority_artifact_rejects_noncanonical_bytes(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        begin_input = {
            "schema": qa.BEGIN_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "confirmation_root": str(confirmation),
        }

        record_bytes = record.read_bytes()
        record.write_text(
            json.dumps(json.loads(record_bytes), indent=2), encoding="utf-8"
        )
        with pytest.raises(qa.EvidenceError) as record_invalid:
            qa.begin_confirmation(begin_input)
        assert record_invalid.value.code == "record_tampered"
        record.write_bytes(record_bytes)

        manifest_bytes = manifest.read_bytes()
        manifest.write_text(
            json.dumps(json.loads(manifest_bytes), indent=2), encoding="utf-8"
        )
        with pytest.raises(qa.EvidenceError) as manifest_invalid:
            qa.begin_confirmation(begin_input)
        assert manifest_invalid.value.code == "manifest_tampered"
        manifest.write_bytes(manifest_bytes)

        begin = qa.begin_confirmation(begin_input)
        claim_path = Path(begin["path"])
        claim_bytes = claim_path.read_bytes()
        claim_path.write_text(
            json.dumps(json.loads(claim_bytes), indent=2), encoding="utf-8"
        )
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(cluster(confirmation, remediated, outcome="pass"))],
        }
        output = str(confirmation / "result.json")
        with pytest.raises(qa.EvidenceError) as claim_invalid:
            qa.finish_confirmation(request, output)
        assert claim_invalid.value.code == "claim_invalid"
        claim_path.write_bytes(claim_bytes)

        qa.finish_confirmation(request, output)
        admission_path = next(confirmation.glob("settlement-admission-*.json"))
        admission_bytes = admission_path.read_bytes()
        result_path = Path(output)
        result_bytes = result_path.read_bytes()

        admission_path.write_text(
            json.dumps(json.loads(admission_bytes), indent=2), encoding="utf-8"
        )
        with pytest.raises(qa.EvidenceError) as admission_invalid:
            qa.finish_confirmation(request, output)
        assert admission_invalid.value.code == "admission_invalid"
        admission_path.write_bytes(admission_bytes)

        result_path.write_text(
            json.dumps(json.loads(result_bytes), indent=2), encoding="utf-8"
        )
        with pytest.raises(qa.EvidenceError) as result_invalid:
            qa.finish_confirmation(request, output)
        assert result_invalid.value.code == "result_invalid"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_manifest_claim_and_terminal_binding_rejections(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    confirmation = Path(tempfile.mkdtemp(prefix="release-qa.", dir="/tmp")).resolve()
    try:
        begin_input = {
            "schema": qa.BEGIN_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "confirmation_root": str(confirmation),
        }
        manifest_bytes = manifest.read_bytes()
        manifest_value = json.loads(manifest_bytes)
        manifest_value["confirmation_attempt"] = 2
        write_json(manifest, manifest_value)
        with pytest.raises(qa.EvidenceError) as attempt_invalid:
            qa.begin_confirmation(begin_input)
        assert attempt_invalid.value.code == "attempt_invalid"
        manifest.write_bytes(manifest_bytes)

        begin = qa.begin_confirmation(begin_input)
        claim_path = Path(begin["path"])
        claim_bytes = claim_path.read_bytes()
        claim_value = json.loads(claim_bytes)
        claim_value["extra"] = True
        write_json(claim_path, claim_value)
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(cluster(confirmation, remediated, outcome="pass"))],
        }
        output = str(confirmation / "result.json")
        with pytest.raises(qa.EvidenceError) as claim_invalid:
            qa.finish_confirmation(request, output)
        assert claim_invalid.value.code == "schema_invalid"
        claim_path.write_bytes(claim_bytes)

        qa.finish_confirmation(request, output)
        result_path = Path(output)
        result_value = json.loads(result_path.read_text())
        result_value["admission_digest"] = "sha256:" + "0" * 64
        write_json(result_path, result_value)
        with pytest.raises(qa.EvidenceError) as result_invalid:
            qa.finish_confirmation(request, output)
        assert result_invalid.value.code == "result_invalid"
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_source_mutation_after_claim_settles_rejected_without_source_write(
    release_case,
):
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
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(cluster(confirmation, remediated, outcome="pass"))],
        }
        dirty = repo / "dirty.txt"
        dirty.write_text("preserve me\n", encoding="utf-8")
        result_path = confirmation / "result.json"
        with pytest.raises(qa.EvidenceError) as rejected:
            qa.finish_confirmation(request, str(result_path))
        assert rejected.value.code == "source_mutated"
        assert dirty.read_text(encoding="utf-8") == "preserve me\n"
        terminal = json.loads(result_path.read_text())
        assert terminal["verdict"] == "REJECTED"
        assert terminal["diagnostic"]["code"] == "source_mutated"
        terminal_bytes = result_path.read_bytes()
        dirty.unlink()
        with pytest.raises(qa.EvidenceError) as retry:
            qa.finish_confirmation(request, str(result_path))
        assert retry.value.code == "source_mutated"
        assert result_path.read_bytes() == terminal_bytes
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_admission_race_loser_rejects_noncanonical_winner(release_case, monkeypatch):
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
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(cluster(confirmation, remediated, outcome="pass"))],
        }
        output = str(confirmation / "result.json")
        original_create = qa.create_once_write

        def lose_admission_race(path, value):
            if Path(path).name.startswith("settlement-admission-"):
                Path(path).write_text(json.dumps(value, indent=2), encoding="utf-8")
                raise qa.EvidenceError("output_exists", "simulated race loss")
            return original_create(path, value)

        monkeypatch.setattr(qa, "create_once_write", lose_admission_race)
        with pytest.raises(qa.EvidenceError) as rejected:
            qa.finish_confirmation(request, output)
        assert rejected.value.code == "admission_invalid"
        admission_path = next(confirmation.glob("settlement-admission-*.json"))
        assert admission_path.read_bytes() != qa.canonical_bytes(
            json.loads(admission_path.read_text())
        )
        assert not Path(output).exists()
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize("winner", [0, 1])
def test_divergent_concurrent_finish_has_one_deterministic_winner(
    release_case, monkeypatch, winner
):
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
        first_result = cluster(confirmation, remediated, outcome="pass")
        second_result = confirmation / "cluster-second.json"
        second_result.write_bytes(first_result.read_bytes())
        base_request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
        }
        requests = [
            {**base_request, "cluster_results": [str(first_result)]},
            {**base_request, "cluster_results": [str(second_result)]},
        ]
        output = str(confirmation / "result.json")
        barrier = threading.Barrier(2)
        winner_admitted = threading.Event()
        loser_observed = threading.Event()
        original_create = qa.create_once_write

        def ordered_create(path, value):
            if Path(path).name.startswith("settlement-admission-"):
                barrier.wait(timeout=5)
                if value["submission_digest"] == qa.digest(requests[winner]):
                    created = original_create(path, value)
                    winner_admitted.set()
                    assert loser_observed.wait(timeout=5)
                    return created
                assert winner_admitted.wait(timeout=5)
            return original_create(path, value)

        monkeypatch.setattr(qa, "create_once_write", ordered_create)

        def invoke(index):
            try:
                return "ok", qa.finish_confirmation(requests[index], output)
            except qa.EvidenceError as error:
                return "error", error.code
            finally:
                if index != winner:
                    loser_observed.set()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(invoke, range(2)))
        assert outcomes[winner][0] == "ok"
        assert outcomes[winner][1]["verdict"] == "PASS"
        assert outcomes[1 - winner] == ("error", "settlement_pending")
        assert len(list(confirmation.glob("settlement-admission-*.json"))) == 1
        terminal = json.loads(Path(output).read_text())
        assert terminal["submission_digest"] == qa.digest(requests[winner])
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


def test_concurrent_exact_finish_converges_on_one_terminal(release_case, monkeypatch):
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
        request = {
            "schema": qa.FINISH_SCHEMA,
            "repository": str(repo),
            "full_record": str(record),
            "manifest": str(manifest),
            "claim": begin["path"],
            "claim_digest": begin["digest"],
            "confirmation_root": str(confirmation),
            "cluster_results": [str(result_file)],
        }
        output = str(confirmation / "result.json")
        barrier = threading.Barrier(2)
        original_create = qa.create_once_write

        def synchronized_create(path, value):
            if Path(path).name.startswith("settlement-admission-"):
                barrier.wait()
            return original_create(path, value)

        monkeypatch.setattr(qa, "create_once_write", synchronized_create)
        with ThreadPoolExecutor(max_workers=2) as executor:
            receipts = list(
                executor.map(
                    lambda _: qa.finish_confirmation(request, output), range(2)
                )
            )
        assert receipts[0] == receipts[1]
        assert receipts[0]["verdict"] == "PASS"
        assert len(list(confirmation.glob("settlement-admission-*.json"))) == 1
    finally:
        shutil.rmtree(confirmation, ignore_errors=True)


@pytest.mark.parametrize("field", ["design_gate_matrix", "active_design_gates"])
def test_frozen_record_revalidates_gate_coverage(release_case, field):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence, active_gate=True)
    raw = json.loads(record.read_text())
    raw[field] = []
    write_json(record, raw)
    with pytest.raises(qa.EvidenceError) as rejected:
        qa.validate_record(repo, str(record))
    assert rejected.value.code == "gate_matrix_incomplete"


@pytest.mark.parametrize("baseline_sha", ["not-a-sha", "a" * 39, "a" * 65, None])
def test_previous_release_record_requires_exact_baseline_sha(
    release_case, baseline_sha
):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    raw = json.loads(record.read_text())
    raw["baseline_sha"] = baseline_sha
    write_json(record, raw)
    with pytest.raises(qa.EvidenceError) as rejected:
        qa.load_record(str(record))
    assert rejected.value.code == (
        "field_invalid" if baseline_sha is None else "baseline_invalid"
    )


def test_oversized_frozen_record_does_not_consume_output(release_case, monkeypatch):
    repo, candidate, evidence = release_case
    result = cluster(evidence, candidate)
    spec = full_spec(repo, candidate, evidence, result, first_release=True)
    reference = evidence / "reference.json"
    qa.freeze_full(spec, str(reference))
    size = reference.stat().st_size
    assert result.stat().st_size < size
    monkeypatch.setattr(qa, "MAX_JSON_BYTES", size - 1)
    output = evidence / "record.json"
    before = set(evidence.iterdir())
    with pytest.raises(qa.EvidenceError) as rejected:
        qa.freeze_full(spec, str(output))
    assert rejected.value.code == "output_too_large"
    assert set(evidence.iterdir()) == before
    monkeypatch.setattr(qa, "MAX_JSON_BYTES", size)
    receipt = qa.freeze_full(spec, str(output))
    assert qa.load_record(str(output))[1] == receipt["digest"]


def test_previous_record_schema_is_not_admitted(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    raw = json.loads(record.read_text())
    raw["schema"] = "aquarium-release-qa-confirmation-record/v2"
    write_json(record, raw)
    with pytest.raises(qa.EvidenceError) as rejected:
        qa.load_record(str(record))
    assert rejected.value.code == "schema_invalid"


def test_previous_manifest_schema_is_not_admitted(release_case):
    repo, candidate, evidence = release_case
    record, _ = freeze(repo, candidate, evidence)
    remediated = remediate(repo)
    manifest = prepare(repo, remediated, evidence, record)
    raw = json.loads(manifest.read_text())
    raw["schema"] = "aquarium-release-qa-confirmation-manifest/v2"
    write_json(manifest, raw)
    with pytest.raises(qa.EvidenceError) as rejected:
        qa.load_confirmation(
            {
                "repository": str(repo),
                "full_record": str(record),
                "manifest": str(manifest),
            }
        )
    assert rejected.value.code == "schema_invalid"


def test_unknown_gate_enrollment_is_rejected(release_case):
    repo, candidate, evidence = release_case
    spec = full_spec(repo, candidate, evidence, cluster(evidence, candidate))
    spec["design_gate_state"] = "unknown"
    with pytest.raises(qa.EvidenceError) as rejected:
        qa.freeze_full(spec, str(evidence / "record.json"))
    assert rejected.value.code == "field_invalid"
