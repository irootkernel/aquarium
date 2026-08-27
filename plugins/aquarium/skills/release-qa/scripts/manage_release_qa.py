#!/usr/bin/env python3
"""Freeze and validate release-QA evidence and confirmation admission."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn

ERROR_SCHEMA = "aquarium-release-qa-error/v1"
CLUSTER_SCHEMA = "aquarium-release-qa-cluster-result/v1"
FULL_INPUT_SCHEMA = "aquarium-release-qa-full-pass/v1"
RECORD_SCHEMA = "aquarium-release-qa-confirmation-record/v1"
PREPARE_SCHEMA = "aquarium-release-qa-confirmation-prepare/v1"
MANIFEST_SCHEMA = "aquarium-release-qa-confirmation-manifest/v1"
BEGIN_SCHEMA = "aquarium-release-qa-confirmation-begin/v1"
CLAIM_SCHEMA = "aquarium-release-qa-confirmation-claim/v1"
FINISH_SCHEMA = "aquarium-release-qa-confirmation-finish/v1"
RESULT_SCHEMA = "aquarium-release-qa-confirmation-result/v1"
MAX_JSON_BYTES = 4 * 1024 * 1024
OUTCOMES = {"pass", "finding", "gap"}


class EvidenceError(ValueError):
    """One bounded release-QA evidence contract violation."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def fail(code: str, message: str) -> NoReturn:
    raise EvidenceError(code, message)


def read_json(path_value: str) -> dict[str, Any]:
    path = Path(path_value)
    if path.is_symlink() or not path.is_file():
        fail("input_invalid", f"JSON input must be a regular non-symlink file: {path}")
    if path.stat().st_size > MAX_JSON_BYTES:
        fail("input_too_large", f"JSON input exceeds {MAX_JSON_BYTES} bytes: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail("input_invalid", f"cannot read JSON input {path}: {type(error).__name__}")
    if not isinstance(value, dict):
        fail("input_invalid", f"JSON input must contain one object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def atomic_write(path_value: str | Path, value: Any) -> Path:
    path = Path(path_value)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as target:
            target.write(canonical_bytes(value))
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
        path.chmod(0o600)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return path


def text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        fail("field_invalid", f"{field} must be a non-empty bounded string")
    return value


def string_list(value: Any, field: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        fail(
            "field_invalid", f"{field} must be a{' non-empty' if nonempty else ''} list"
        )
    result = [text(item, f"{field}[]") for item in value]
    if len(result) != len(set(result)):
        fail("duplicate_identity", f"{field} contains duplicate values")
    return result


def run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode:
        fail("git_invalid", f"git {' '.join(arguments)} failed")
    return completed.stdout.strip()


def run_git_raw(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode:
        fail("git_invalid", f"git {' '.join(arguments)} failed")
    return completed.stdout


def repository(value: Any) -> Path:
    raw = Path(text(value, "repository"))
    if not raw.is_absolute() or raw.is_symlink():
        fail("repository_invalid", "repository must be an absolute non-symlink path")
    resolved = raw.resolve(strict=True)
    if run_git(resolved, "rev-parse", "--show-toplevel") != str(resolved):
        fail("repository_invalid", "repository must identify the exact Git root")
    return resolved


def exact_commit(repo: Path, value: Any, field: str) -> str:
    requested = text(value, field)
    resolved = run_git(repo, "rev-parse", "--verify", f"{requested}^{{commit}}")
    if requested != resolved:
        fail("commit_not_exact", f"{field} must be a full exact commit ID")
    return resolved


def baseline_commit(repo: Path, value: Any) -> str:
    baseline = text(value, "previous_release")
    return run_git(repo, "rev-parse", "--verify", f"{baseline}^{{commit}}")


def release_range(
    repo: Path, baseline: str, candidate: str
) -> tuple[list[str], list[str]]:
    if run_git(repo, "merge-base", "--is-ancestor", baseline, candidate) != "":
        pass
    commits = run_git(
        repo, "rev-list", "--reverse", f"{baseline}..{candidate}"
    ).splitlines()
    paths = run_git_raw(repo, "diff", "--name-only", "-z", baseline, candidate).split(
        "\0"
    )
    return commits, [path for path in paths if path]


def physical_evidence_root(value: Any) -> Path:
    raw = Path(text(value, "evidence_root"))
    if not raw.is_absolute() or raw.is_symlink():
        fail(
            "evidence_root_invalid",
            "evidence_root must be an absolute non-symlink path",
        )
    try:
        resolved = raw.resolve(strict=True)
    except OSError:
        fail("evidence_root_invalid", "evidence_root must already exist")
    if not resolved.is_dir() or not resolved.name.startswith("release-qa."):
        fail(
            "evidence_root_invalid",
            "evidence_root must be a physical /tmp/release-qa.* directory",
        )
    if resolved.parent not in {Path("/tmp").resolve(), Path("/private/tmp").resolve()}:
        fail(
            "evidence_root_invalid",
            "evidence_root must be directly beneath physical /tmp",
        )
    if raw != resolved or resolved.stat().st_mode & 0o077:
        fail(
            "evidence_root_invalid",
            "evidence_root must be a physical private directory",
        )
    return resolved


def evidence_file(root: Path, value: Any, field: str) -> str:
    raw = Path(text(value, field))
    if not raw.is_absolute() or raw.is_symlink() or not raw.is_file():
        fail(
            "evidence_invalid", f"{field} must be an absolute regular non-symlink file"
        )
    resolved = raw.resolve(strict=True)
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        fail("evidence_outside_root", f"{field} is outside the evidence root")
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            fail("evidence_invalid", f"{field} has symlink ancestry")
    return str(resolved)


def output_under(root: Path, value: str, field: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        fail("output_invalid", f"{field} must be an absolute non-symlink path")
    try:
        relative_parent = path.parent.resolve(strict=True).relative_to(root)
    except (OSError, ValueError):
        fail(
            "output_outside_root", f"{field} must be beneath its physical evidence root"
        )
    current = root
    for component in relative_parent.parts:
        current = current / component
        if current.is_symlink():
            fail("output_invalid", f"{field} has symlink ancestry")
    return path


def clean_exact_main(repo: Path, candidate: str) -> None:
    if run_git(repo, "rev-parse", "HEAD") != candidate:
        fail("candidate_changed", "HEAD does not equal the confirmation candidate")
    if run_git(repo, "rev-parse", "main") != candidate:
        fail(
            "candidate_changed", "local main does not equal the confirmation candidate"
        )
    if run_git(repo, "status", "--porcelain", "--untracked-files=all"):
        fail("source_mutated", "source repository is not clean")


def validate_scenario(raw: Any, root: Path) -> dict[str, Any]:
    if not isinstance(raw, dict):
        fail("scenario_invalid", "each scenario must be an object")
    outcome = text(raw.get("outcome"), "scenario.outcome")
    if outcome not in OUTCOMES:
        fail("scenario_invalid", f"unsupported scenario outcome: {outcome}")
    controlled = raw.get("controlled_environment")
    if not isinstance(controlled, dict) or not controlled:
        fail("scenario_invalid", "controlled_environment must be a non-empty object")
    evidence = [
        evidence_file(root, item, "scenario.evidence[]")
        for item in string_list(raw.get("evidence"), "scenario.evidence")
    ]
    return {
        "id": text(raw.get("id"), "scenario.id"),
        "sources": string_list(raw.get("sources"), "scenario.sources"),
        "procedure": text(raw.get("procedure"), "scenario.procedure"),
        "controlled_environment": controlled,
        "expected": text(raw.get("expected"), "scenario.expected"),
        "observed": text(raw.get("observed"), "scenario.observed"),
        "outcome": outcome,
        "evidence": evidence,
    }


def validate_cluster(raw: dict[str, Any], root: Path, candidate: str) -> dict[str, Any]:
    if raw.get("schema") != CLUSTER_SCHEMA:
        fail("schema_invalid", f"cluster result must use {CLUSTER_SCHEMA}")
    if raw.get("candidate_sha") != candidate:
        fail("candidate_mismatch", "cluster result candidate does not match")
    status = raw.get("source_status")
    if status != {"before": "clean", "after": "clean"}:
        fail("source_mutated", "cluster source_status must be clean before and after")
    scenarios_raw = raw.get("scenarios")
    if not isinstance(scenarios_raw, list) or not scenarios_raw:
        fail("cluster_incomplete", "cluster must contain at least one scenario")
    scenarios = [validate_scenario(item, root) for item in scenarios_raw]
    scenario_ids = [item["id"] for item in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        fail("duplicate_identity", "scenario IDs must be unique")
    findings_raw = raw.get("verified_findings", [])
    if not isinstance(findings_raw, list):
        fail("finding_invalid", "verified_findings must be a list")
    findings: list[dict[str, str]] = []
    for item in findings_raw:
        if not isinstance(item, dict):
            fail("finding_invalid", "each finding must be an object")
        scenario_id = text(item.get("scenario_id"), "finding.scenario_id")
        if scenario_id not in scenario_ids:
            fail("finding_invalid", "finding must reference a scenario in its cluster")
        findings.append(
            {
                "id": text(item.get("id"), "finding.id"),
                "scenario_id": scenario_id,
                "severity": text(item.get("severity"), "finding.severity"),
            }
        )
    if len({item["id"] for item in findings}) != len(findings):
        fail("duplicate_identity", "finding IDs must be unique")
    finding_scenarios = {item["scenario_id"] for item in findings}
    for scenario in scenarios:
        if (scenario["outcome"] == "finding") != (scenario["id"] in finding_scenarios):
            fail(
                "finding_invalid",
                "finding outcomes and verified finding references must agree",
            )
    return {
        "id": text(raw.get("cluster_id"), "cluster_id"),
        "scenarios": scenarios,
        "verified_findings": findings,
    }


def matrix(raw: Any, field: str, identity: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        fail("matrix_incomplete", f"{field} must be a non-empty list")
    result: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            fail("matrix_incomplete", f"{field} entries must be objects")
        result.append(
            {
                identity: text(item.get(identity), f"{field}.{identity}"),
                "scenarios": string_list(item.get("scenarios"), f"{field}.scenarios"),
            }
        )
    keys = [item[identity] for item in result]
    if len(keys) != len(set(keys)):
        fail("duplicate_identity", f"{field} contains duplicate {identity} values")
    return result


def changed_surface_mappings(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        fail("surface_mapping_incomplete", "changed_surface_mappings must be non-empty")
    result: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            fail(
                "surface_mapping_incomplete", "changed-surface mappings must be objects"
            )
        scenarios = string_list(
            item.get("scenarios", []),
            "changed_surface_mappings.scenarios",
            nonempty=False,
        )
        reproductions = string_list(
            item.get("finding_reproductions", []),
            "changed_surface_mappings.finding_reproductions",
            nonempty=False,
        )
        if not scenarios and not reproductions:
            fail("surface_mapping_incomplete", "each changed surface needs coverage")
        result.append(
            {
                "path": text(item.get("path"), "changed_surface_mappings.path"),
                "scenarios": scenarios,
                "finding_reproductions": reproductions,
            }
        )
    paths = [item["path"] for item in result]
    if len(paths) != len(set(paths)):
        fail("duplicate_identity", "changed_surface_mappings contains duplicate paths")
    return result


def freeze_full(spec: dict[str, Any], output: str) -> dict[str, Any]:
    if spec.get("schema") != FULL_INPUT_SCHEMA:
        fail("schema_invalid", f"freeze input must use {FULL_INPUT_SCHEMA}")
    repo = repository(spec.get("repository"))
    candidate = exact_commit(repo, spec.get("candidate_sha"), "candidate_sha")
    clean_exact_main(repo, candidate)
    baseline = baseline_commit(repo, spec.get("previous_release"))
    commits, paths = release_range(repo, baseline, candidate)
    if not commits:
        fail("delta_empty", "full release-QA requires a non-empty release delta")
    root = physical_evidence_root(spec.get("evidence_root"))
    if spec.get("design_gate_state") not in {"enrolled", "not_enrolled"}:
        fail("field_invalid", "design_gate_state must be enrolled or not_enrolled")
    result_paths = string_list(spec.get("cluster_results"), "cluster_results")
    clusters = [
        validate_cluster(
            read_json(evidence_file(root, path, "cluster_results[]")), root, candidate
        )
        for path in result_paths
    ]
    cluster_ids = [item["id"] for item in clusters]
    scenario_ids = [
        scenario["id"] for cluster in clusters for scenario in cluster["scenarios"]
    ]
    finding_ids = [
        finding["id"]
        for cluster in clusters
        for finding in cluster["verified_findings"]
    ]
    if len(cluster_ids) != len(set(cluster_ids)) or len(scenario_ids) != len(
        set(scenario_ids)
    ):
        fail("duplicate_identity", "cluster and scenario IDs must be globally unique")
    if len(finding_ids) != len(set(finding_ids)):
        fail("duplicate_identity", "finding IDs must be globally unique")
    commit_matrix = matrix(spec.get("commit_matrix"), "commit_matrix", "commit")
    surface_matrix = matrix(spec.get("surface_matrix"), "surface_matrix", "path")
    if [item["commit"] for item in commit_matrix] != commits:
        fail(
            "commit_matrix_incomplete",
            "commit_matrix must exactly cover the ordered release delta",
        )
    if {item["path"] for item in surface_matrix} != set(paths):
        fail(
            "surface_matrix_incomplete",
            "surface_matrix must exactly cover every changed path",
        )
    known = set(scenario_ids)
    for item in [*commit_matrix, *surface_matrix]:
        if not set(item["scenarios"]).issubset(known):
            fail("matrix_unknown_scenario", "matrix references an unknown scenario")
    outcomes = [
        scenario["outcome"] for cluster in clusters for scenario in cluster["scenarios"]
    ]
    verdict = (
        "INCOMPLETE"
        if "gap" in outcomes
        else "FINDINGS"
        if finding_ids or "finding" in outcomes
        else "PASS"
    )
    record = {
        "schema": RECORD_SCHEMA,
        "version": text(spec.get("version"), "version"),
        "previous_release": text(spec.get("previous_release"), "previous_release"),
        "baseline_sha": baseline,
        "candidate_sha": candidate,
        "candidate_tree": run_git(repo, "rev-parse", f"{candidate}^{{tree}}"),
        "evidence_root": str(root),
        "design_gate_state": text(spec.get("design_gate_state"), "design_gate_state"),
        "clusters": clusters,
        "commit_matrix": commit_matrix,
        "surface_matrix": surface_matrix,
        "verdict": verdict,
    }
    output_path = output_under(root, output, "output")
    atomic_write(output_path, record)
    return {
        "schema": RECORD_SCHEMA,
        "path": str(output_path.resolve()),
        "digest": digest(record),
        "verdict": verdict,
    }


def load_record(path: str) -> tuple[dict[str, Any], str]:
    record = read_json(path)
    if record.get("schema") != RECORD_SCHEMA:
        fail("schema_invalid", f"record must use {RECORD_SCHEMA}")
    return record, digest(record)


def validate_record(repo: Path, path: str) -> tuple[dict[str, Any], str, Path]:
    record, record_digest = load_record(path)
    root = physical_evidence_root(record.get("evidence_root"))
    evidence_file(root, path, "full_record")
    baseline = exact_commit(repo, record.get("baseline_sha"), "record.baseline_sha")
    candidate = exact_commit(repo, record.get("candidate_sha"), "record.candidate_sha")
    if run_git(repo, "rev-parse", f"{candidate}^{{tree}}") != record.get(
        "candidate_tree"
    ):
        fail("record_tampered", "record candidate tree does not match Git")
    commits, paths = release_range(repo, baseline, candidate)
    commit_matrix = matrix(
        record.get("commit_matrix"), "record.commit_matrix", "commit"
    )
    surface_matrix = matrix(
        record.get("surface_matrix"), "record.surface_matrix", "path"
    )
    if [item["commit"] for item in commit_matrix] != commits:
        fail("record_tampered", "record commit matrix no longer matches Git")
    if {item["path"] for item in surface_matrix} != set(paths):
        fail("record_tampered", "record surface matrix no longer matches Git")
    clusters = record.get("clusters")
    if not isinstance(clusters, list) or not clusters:
        fail("record_tampered", "record clusters must be a non-empty list")
    cluster_ids: list[str] = []
    scenario_ids: list[str] = []
    finding_ids: list[str] = []
    outcomes: list[str] = []
    for cluster in clusters:
        if not isinstance(cluster, dict):
            fail("record_tampered", "record cluster must be an object")
        cluster_ids.append(text(cluster.get("id"), "record.cluster.id"))
        scenarios = cluster.get("scenarios")
        findings = cluster.get("verified_findings")
        if (
            not isinstance(scenarios, list)
            or not scenarios
            or not isinstance(findings, list)
        ):
            fail("record_tampered", "record cluster inventory is incomplete")
        local_scenarios: set[str] = set()
        for scenario in scenarios:
            validated = validate_scenario(scenario, root)
            scenario_ids.append(validated["id"])
            local_scenarios.add(validated["id"])
            outcomes.append(validated["outcome"])
        for finding in findings:
            if not isinstance(finding, dict):
                fail("record_tampered", "record finding must be an object")
            finding_ids.append(text(finding.get("id"), "record.finding.id"))
            if (
                text(finding.get("scenario_id"), "record.finding.scenario_id")
                not in local_scenarios
            ):
                fail("record_tampered", "record finding references another cluster")
            text(finding.get("severity"), "record.finding.severity")
    if (
        len(cluster_ids) != len(set(cluster_ids))
        or len(scenario_ids) != len(set(scenario_ids))
        or len(finding_ids) != len(set(finding_ids))
    ):
        fail("record_tampered", "record contains duplicate stable identities")
    known = set(scenario_ids)
    if any(
        not set(item["scenarios"]).issubset(known)
        for item in [*commit_matrix, *surface_matrix]
    ):
        fail("record_tampered", "record matrix references an unknown scenario")
    verdict = (
        "INCOMPLETE"
        if "gap" in outcomes
        else "FINDINGS"
        if finding_ids or "finding" in outcomes
        else "PASS"
    )
    if record.get("verdict") != verdict:
        fail("record_tampered", "record verdict does not match its evidence")
    return record, record_digest, root


def frozen_inventory(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": cluster["id"],
            "scenarios": cluster["scenarios"],
            "verified_findings": cluster["verified_findings"],
        }
        for cluster in record["clusters"]
    ]


def prepare_confirmation(spec: dict[str, Any], output: str) -> dict[str, Any]:
    if spec.get("schema") != PREPARE_SCHEMA:
        fail("schema_invalid", f"prepare input must use {PREPARE_SCHEMA}")
    repo = repository(spec.get("repository"))
    record, record_digest, root = validate_record(
        repo, text(spec.get("full_record"), "full_record")
    )
    if record.get("verdict") != "FINDINGS":
        fail(
            "full_pass_not_confirmable",
            "only a complete FINDINGS full pass may prepare confirmation",
        )
    candidate = exact_commit(repo, spec.get("candidate_sha"), "candidate_sha")
    clean_exact_main(repo, candidate)
    full_candidate = exact_commit(
        repo, record.get("candidate_sha"), "record.candidate_sha"
    )
    commits, paths = release_range(repo, full_candidate, candidate)
    if not commits:
        fail(
            "remediation_empty",
            "confirmation requires a non-empty remediation commit range",
        )
    mappings = changed_surface_mappings(spec.get("changed_surface_mappings"))
    if {item["path"] for item in mappings} != set(paths):
        fail(
            "surface_mapping_incomplete",
            "changed-surface mappings must exactly cover remediation paths",
        )
    known_scenarios = {
        scenario["id"]
        for cluster in record["clusters"]
        for scenario in cluster["scenarios"]
    }
    reproductions_raw = spec.get("finding_reproductions")
    if not isinstance(reproductions_raw, list):
        fail("finding_reproduction_invalid", "finding_reproductions must be a list")
    reproductions: list[dict[str, str]] = []
    for item in reproductions_raw:
        if not isinstance(item, dict):
            fail(
                "finding_reproduction_invalid", "finding reproduction must be an object"
            )
        reproductions.append(
            {
                "finding_id": text(item.get("finding_id"), "finding_id"),
                "scenario_id": text(item.get("scenario_id"), "scenario_id"),
            }
        )
    expected_findings = {
        finding["id"]
        for cluster in record["clusters"]
        for finding in cluster["verified_findings"]
    }
    if {item["finding_id"] for item in reproductions} != expected_findings or len(
        reproductions
    ) != len(expected_findings):
        fail(
            "finding_reproduction_incomplete",
            "every verified finding must have exactly one reproduction",
        )
    if any(item["scenario_id"] not in known_scenarios for item in reproductions):
        fail(
            "finding_reproduction_invalid",
            "finding reproduction must use a retained scenario",
        )
    for item in mappings:
        if not set(item["scenarios"]).issubset(known_scenarios):
            fail(
                "matrix_unknown_scenario",
                "changed surface maps to an unknown retained scenario",
            )
        if not set(item["finding_reproductions"]).issubset(expected_findings):
            fail(
                "finding_reproduction_invalid",
                "changed surface maps to an unknown finding reproduction",
            )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "version": record["version"],
        "previous_release": record["previous_release"],
        "full_candidate_sha": full_candidate,
        "candidate_sha": candidate,
        "remediation_commits": commits,
        "remediation_range": f"{full_candidate}..{candidate}",
        "full_record": str(
            Path(text(spec.get("full_record"), "full_record")).resolve()
        ),
        "full_record_digest": record_digest,
        "evidence_root": str(root),
        "inventory": frozen_inventory(record),
        "changed_surface_mappings": mappings,
        "finding_reproductions": reproductions,
        "confirmation_attempt": 1,
    }
    output_path = output_under(root, output, "output")
    atomic_write(output_path, manifest)
    return {
        "schema": MANIFEST_SCHEMA,
        "path": str(output_path.resolve()),
        "digest": digest(manifest),
    }


def load_confirmation(
    spec: dict[str, Any],
) -> tuple[Path, dict[str, Any], str, dict[str, Any], Path]:
    repo = repository(spec.get("repository"))
    record, record_digest, root = validate_record(
        repo, text(spec.get("full_record"), "full_record")
    )
    manifest = read_json(text(spec.get("manifest"), "manifest"))
    if manifest.get("schema") != MANIFEST_SCHEMA:
        fail("schema_invalid", f"manifest must use {MANIFEST_SCHEMA}")
    if manifest.get("full_record_digest") != record_digest:
        fail("record_tampered", "manifest full-record digest does not match")
    if manifest.get("inventory") != frozen_inventory(record):
        fail("inventory_mismatch", "manifest inventory differs from the frozen record")
    if manifest.get("confirmation_attempt") != 1:
        fail("attempt_invalid", "manifest must request confirmation attempt 1")
    if manifest.get("version") != record.get("version") or manifest.get(
        "previous_release"
    ) != record.get("previous_release"):
        fail("manifest_mismatch", "manifest release identity differs from the record")
    if (
        Path(str(manifest.get("full_record"))).resolve()
        != Path(text(spec.get("full_record"), "full_record")).resolve()
    ):
        fail("manifest_mismatch", "manifest identifies a different full record")
    full_candidate = exact_commit(
        repo, manifest.get("full_candidate_sha"), "full_candidate_sha"
    )
    if full_candidate != record.get("candidate_sha"):
        fail("manifest_mismatch", "manifest full candidate differs from the record")
    candidate = exact_commit(repo, manifest.get("candidate_sha"), "candidate_sha")
    commits, paths = release_range(repo, full_candidate, candidate)
    if not commits:
        fail("remediation_empty", "confirmation requires a non-empty remediation range")
    if commits != manifest.get(
        "remediation_commits"
    ) or f"{full_candidate}..{candidate}" != manifest.get("remediation_range"):
        fail("remediation_mismatch", "manifest remediation ancestry or range changed")
    mappings = changed_surface_mappings(manifest.get("changed_surface_mappings"))
    if {item.get("path") for item in mappings} != set(paths):
        fail(
            "surface_mapping_incomplete", "manifest no longer covers remediation paths"
        )
    known_scenarios = {
        scenario["id"]
        for cluster in record["clusters"]
        for scenario in cluster["scenarios"]
    }
    known_findings = {
        finding["id"]
        for cluster in record["clusters"]
        for finding in cluster["verified_findings"]
    }
    reproductions = manifest.get("finding_reproductions")
    if not isinstance(reproductions, list):
        fail(
            "finding_reproduction_invalid",
            "manifest finding reproductions are invalid",
        )
    reproduction_findings: list[str] = []
    for item in reproductions:
        if not isinstance(item, dict):
            fail(
                "finding_reproduction_invalid",
                "manifest finding reproduction is invalid",
            )
        finding_id = text(item.get("finding_id"), "manifest.finding_id")
        scenario_id = text(item.get("scenario_id"), "manifest.scenario_id")
        if scenario_id not in known_scenarios:
            fail(
                "finding_reproduction_invalid",
                "manifest reproduction uses an unknown scenario",
            )
        reproduction_findings.append(finding_id)
    if set(reproduction_findings) != known_findings or len(
        reproduction_findings
    ) != len(known_findings):
        fail(
            "finding_reproduction_incomplete",
            "manifest does not reproduce every finding exactly once",
        )
    for item in mappings:
        if not set(item["scenarios"]).issubset(known_scenarios) or not set(
            item["finding_reproductions"]
        ).issubset(known_findings):
            fail(
                "surface_mapping_incomplete",
                "manifest changed-surface coverage is invalid",
            )
    if manifest.get("evidence_root") != str(root):
        fail("evidence_root_invalid", "manifest evidence root differs from the record")
    evidence_file(root, text(spec.get("manifest"), "manifest"), "manifest")
    return repo, record, record_digest, manifest, root


def begin_confirmation(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema") != BEGIN_SCHEMA:
        fail("schema_invalid", f"begin input must use {BEGIN_SCHEMA}")
    repo, _, record_digest, manifest, root = load_confirmation(spec)
    candidate = manifest["candidate_sha"]
    clean_exact_main(repo, candidate)
    confirmation_root = physical_evidence_root(spec.get("confirmation_root"))
    if confirmation_root == root:
        fail("evidence_root_invalid", "confirmation requires a fresh evidence root")
    claim = {
        "schema": CLAIM_SCHEMA,
        "full_record_digest": record_digest,
        "manifest_digest": digest(manifest),
        "candidate_sha": candidate,
        "confirmation_root": str(confirmation_root),
        "status": "started",
    }
    claim_path = (
        root / f"confirmation-attempt-{record_digest.removeprefix('sha256:')}.json"
    )
    try:
        descriptor = os.open(claim_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        fail(
            "confirmation_already_started",
            "the sole confirmation attempt was already claimed",
        )
    with os.fdopen(descriptor, "wb") as target:
        target.write(canonical_bytes(claim))
        target.flush()
        os.fsync(target.fileno())
    return {"schema": CLAIM_SCHEMA, "path": str(claim_path), "digest": digest(claim)}


def finish_confirmation(spec: dict[str, Any], output: str) -> dict[str, Any]:
    if spec.get("schema") != FINISH_SCHEMA:
        fail("schema_invalid", f"finish input must use {FINISH_SCHEMA}")
    repo, record, record_digest, manifest, full_root = load_confirmation(spec)
    clean_exact_main(repo, manifest["candidate_sha"])
    confirmation_root = physical_evidence_root(spec.get("confirmation_root"))
    claim_path = Path(text(spec.get("claim"), "claim"))
    expected_claim_path = (
        full_root / f"confirmation-attempt-{record_digest.removeprefix('sha256:')}.json"
    )
    try:
        resolved_claim_path = claim_path.resolve(strict=True)
    except OSError:
        fail("claim_invalid", "confirmation claim is unavailable")
    if resolved_claim_path != expected_claim_path:
        fail("claim_invalid", "claim path is not the sole canonical attempt claim")
    claim = read_json(str(claim_path))
    if (
        claim.get("schema") != CLAIM_SCHEMA
        or claim.get("full_record_digest") != record_digest
    ):
        fail("claim_invalid", "confirmation claim does not bind the full record")
    if claim.get("manifest_digest") != digest(manifest) or claim.get(
        "confirmation_root"
    ) != str(confirmation_root):
        fail(
            "claim_invalid",
            "confirmation claim does not bind this manifest and evidence root",
        )
    results = [
        validate_cluster(
            read_json(evidence_file(confirmation_root, path, "cluster_results[]")),
            confirmation_root,
            manifest["candidate_sha"],
        )
        for path in string_list(spec.get("cluster_results"), "cluster_results")
    ]
    expected_clusters = {cluster["id"]: cluster for cluster in record["clusters"]}
    actual_clusters = {cluster["id"]: cluster for cluster in results}
    if len(actual_clusters) != len(results) or set(actual_clusters) != set(
        expected_clusters
    ):
        fail(
            "confirmation_inventory_mismatch",
            "confirmation must rerun every retained cluster exactly once with no extras",
        )
    outcomes: list[str] = []
    for cluster_id, expected in expected_clusters.items():
        expected_ids = [item["id"] for item in expected["scenarios"]]
        actual_ids = [item["id"] for item in actual_clusters[cluster_id]["scenarios"]]
        if actual_ids != expected_ids or len(actual_ids) != len(set(actual_ids)):
            fail(
                "confirmation_inventory_mismatch",
                "confirmation scenario inventory or order differs from the frozen record",
            )
        for frozen, fresh in zip(
            expected["scenarios"], actual_clusters[cluster_id]["scenarios"], strict=True
        ):
            for field in (
                "sources",
                "procedure",
                "controlled_environment",
                "expected",
            ):
                if fresh[field] != frozen[field]:
                    fail(
                        "confirmation_inventory_mismatch",
                        f"confirmation changed frozen scenario field: {field}",
                    )
        outcomes.extend(
            item["outcome"] for item in actual_clusters[cluster_id]["scenarios"]
        )
    reproduction_ids = [
        item["scenario_id"] for item in manifest["finding_reproductions"]
    ]
    actual_scenarios = {
        item["id"] for cluster in results for item in cluster["scenarios"]
    }
    if not set(reproduction_ids).issubset(actual_scenarios):
        fail(
            "finding_reproduction_incomplete",
            "confirmation omitted a finding reproduction",
        )
    finding_ids = [
        finding["id"] for cluster in results for finding in cluster["verified_findings"]
    ]
    verdict = (
        "INCOMPLETE"
        if "gap" in outcomes
        else "FINDINGS"
        if finding_ids or "finding" in outcomes
        else "PASS"
    )
    result = {
        "schema": RESULT_SCHEMA,
        "full_record_digest": record_digest,
        "manifest_digest": digest(manifest),
        "candidate_sha": manifest["candidate_sha"],
        "confirmation_root": str(confirmation_root),
        "clusters": results,
        "verdict": verdict,
    }
    output_path = output_under(confirmation_root, output, "output")
    atomic_write(output_path, result)
    return {
        "schema": RESULT_SCHEMA,
        "path": str(output_path.resolve()),
        "digest": digest(result),
        "verdict": verdict,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("freeze-full", "prepare-confirmation", "finish-confirmation"):
        command = commands.add_parser(name)
        command.add_argument("--input", required=True)
        command.add_argument("--output", required=True)
    begin = commands.add_parser("begin-confirmation")
    begin.add_argument("--input", required=True)
    return root


def main() -> int:
    arguments = parser().parse_args()
    try:
        spec = read_json(arguments.input)
        if arguments.command == "freeze-full":
            result = freeze_full(spec, arguments.output)
        elif arguments.command == "prepare-confirmation":
            result = prepare_confirmation(spec, arguments.output)
        elif arguments.command == "begin-confirmation":
            result = begin_confirmation(spec)
        else:
            result = finish_confirmation(spec, arguments.output)
    except EvidenceError as error:
        print(
            json.dumps(
                {
                    "schema": ERROR_SCHEMA,
                    "error": {"code": error.code, "message": str(error)},
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
