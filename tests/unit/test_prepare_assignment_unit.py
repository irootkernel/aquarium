from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/goal-evaluator/scripts/prepare_assignment.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_assignment", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
preparation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preparation)


@pytest.fixture
def sources(tmp_path: Path) -> Path:
    # macOS can expose the system temporary root through a symlink.
    root = tmp_path.resolve() / "sources"
    root.mkdir()
    (root / "role.md").write_bytes(b"Role\r\n\xff\n")
    (root / "a.md").write_bytes(b"First dependency\r\n")
    (root / "b.md").write_bytes(b"Second dependency")
    (root / "evidence.bin").write_bytes(b"Full evidence\x00\xff\r\n")
    return root


@pytest.fixture
def request_payload() -> dict:
    return {
        "schema": preparation.REQUEST_SCHEMA,
        "role": {"path": "role.md", "dependencies": ["b.md", "a.md"]},
        "node": {
            "objective": "Assess the exact candidate",
            "purpose": "Supply the semantic decision basis",
            "instructions": "Read every applicable criterion.\r\nReturn gaps.",
            "canonical_sources": ["docs/roadmap/README.md#TASK-111"],
            "context": {
                "work_identity": "TASK-111",
                "goal_ref": "goal-111",
                "goal_revision": "revision-3",
                "target": "candidate-sha256:012345",
                "base": "base-sha:abcdef",
                "procedure": "aquarium-goal-v2@package-sha256:fedcba",
                "node": "assessment@session-1/attempt-2",
            },
            "selected_evidence": ["evidence.bin"],
            "permitted_effects": {
                "allowed": ["Read declared original sources"],
                "excluded": ["Source and runtime mutation"],
            },
            "deliverables": ["Complete assessment"],
            "success_criteria": ["Every applicable criterion has evidence or a gap"],
        },
    }


def test_preserves_exact_bytes_and_self_contained_assignment(
    sources: Path, request_payload: dict
) -> None:
    result = preparation.prepare(sources, request_payload)
    snapshot = result["prepared_role_snapshot"]
    assert snapshot["schema"] == preparation.SNAPSHOT_SCHEMA
    assert snapshot["role_path"] == "role.md"
    assert [file["path"] for file in snapshot["files"]] == ["a.md", "b.md", "role.md"]
    for file in snapshot["files"]:
        content = (sources / file["path"]).read_bytes()
        assert base64.b64decode(file["content_base64"]) == content
        assert file["size_bytes"] == len(content)
        assert file["sha256"] == hashlib.sha256(content).hexdigest()
    assert (
        result["local_prepared_role_snapshot_sha256"]
        == hashlib.sha256(preparation.canonical_bytes(snapshot)).hexdigest()
    )
    assignment = result["prepared_assignment"]
    assert assignment["role_snapshot"] == snapshot
    expected_node = copy.deepcopy(request_payload["node"])
    evidence = assignment["node"]["selected_evidence"]
    assert (
        base64.b64decode(evidence[0]["content_base64"])
        == (sources / "evidence.bin").read_bytes()
    )
    expected_node["selected_evidence"] = evidence
    assert assignment["node"] == expected_node
    assert (
        result["local_prepared_assignment_sha256"]
        == hashlib.sha256(preparation.canonical_bytes(assignment)).hexdigest()
    )
    request_payload["node"]["context"]["target"] = "later-candidate"
    assert assignment["node"]["context"]["target"] == "candidate-sha256:012345"


@pytest.mark.parametrize("source", ["role.md", "a.md", "b.md"])
def test_role_and_dependency_changes_change_both_digests(
    sources: Path, request_payload: dict, source: str
) -> None:
    before = preparation.prepare(sources, request_payload)
    (sources / source).write_bytes((sources / source).read_bytes() + b"\r\nchange")
    after = preparation.prepare(sources, request_payload)
    for key in (
        "local_prepared_role_snapshot_sha256",
        "local_prepared_assignment_sha256",
    ):
        assert before[key] != after[key]


@pytest.mark.parametrize("change", ["evidence", "target", "instructions"])
def test_node_changes_do_not_change_role_digest(
    sources: Path, request_payload: dict, change: str
) -> None:
    before = preparation.prepare(sources, request_payload)
    if change == "evidence":
        (sources / "evidence.bin").write_bytes(b"changed evidence")
    elif change == "target":
        request_payload["node"]["context"]["target"] = "different candidate"
    else:
        request_payload["node"]["instructions"] += "\r\nAnother instruction."
    after = preparation.prepare(sources, request_payload)
    assert (
        before["local_prepared_role_snapshot_sha256"]
        == after["local_prepared_role_snapshot_sha256"]
    )
    assert (
        before["local_prepared_assignment_sha256"]
        != after["local_prepared_assignment_sha256"]
    )


def test_ordering_is_deterministic_and_undeclared_links_are_not_inferred(
    sources: Path, request_payload: dict
) -> None:
    (sources / "role.md").write_bytes(b"Read [missing dependency](missing.md).\r\n")
    (sources / "another.bin").write_bytes(b"another evidence item")
    request_payload["node"]["selected_evidence"].append("another.bin")
    before = preparation.prepare(sources, request_payload)
    request_payload["role"]["dependencies"].reverse()
    request_payload["node"]["selected_evidence"].reverse()
    reordered = dict(reversed(list(request_payload.items())))
    after = preparation.prepare(sources, reordered)
    assert preparation.canonical_bytes(before) == preparation.canonical_bytes(after)


@pytest.mark.parametrize(
    "path",
    [
        "../role.md",
        "/role.md",
        "./role.md",
        "a/../role.md",
        "a//role.md",
        "a/",
        "a\x00",
    ],
)
@pytest.mark.parametrize("location", ["role", "dependencies", "evidence"])
def test_rejects_noncanonical_or_escaping_paths(
    sources: Path, request_payload: dict, path: str, location: str
) -> None:
    if location == "role":
        request_payload["role"]["path"] = path
    elif location == "dependencies":
        request_payload["role"]["dependencies"] = [path]
    else:
        request_payload["node"]["selected_evidence"] = [path]
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


@pytest.mark.parametrize("location", ["dependencies", "role-as-dependency", "evidence"])
def test_rejects_duplicate_paths(
    sources: Path, request_payload: dict, location: str
) -> None:
    if location == "dependencies":
        request_payload["role"]["dependencies"] = ["a.md", "a.md"]
    elif location == "role-as-dependency":
        request_payload["role"]["dependencies"] = ["role.md"]
    else:
        request_payload["node"]["selected_evidence"] = ["evidence.bin", "evidence.bin"]
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


@pytest.mark.parametrize("location", ["role", "dependency", "evidence"])
def test_rejects_missing_files(
    sources: Path, request_payload: dict, location: str
) -> None:
    path = {"role": "role.md", "dependency": "a.md", "evidence": "evidence.bin"}[
        location
    ]
    (sources / path).unlink()
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


@pytest.mark.parametrize("location", ["root", "root-parent", "file", "parent"])
def test_rejects_symlinks_even_to_sources_within_the_root(
    sources: Path, request_payload: dict, location: str
) -> None:
    if location == "root":
        link = sources.parent / "root-link"
        link.symlink_to(sources, target_is_directory=True)
        sources = link
    elif location == "root-parent":
        link = sources.parent / "parent-link"
        link.symlink_to(sources.parent, target_is_directory=True)
        sources = link / "sources"
    elif location == "file":
        (sources / "role.md").unlink()
        (sources / "role.md").symlink_to(sources / "a.md")
    else:
        (sources / "nested").mkdir()
        (sources / "nested" / "dependency.md").write_bytes(b"dependency")
        (sources / "link").symlink_to(sources / "nested", target_is_directory=True)
        request_payload["role"]["dependencies"] = ["link/dependency.md"]
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


def test_no_follow_read_rejects_file_replaced_with_symlink_before_open(
    sources: Path, request_payload: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_open = os.open

    def replace_then_open(path, flags, *args, **kwargs):
        if path == "role.md":
            (sources / "role.md").unlink()
            (sources / "role.md").symlink_to(sources / "a.md")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", replace_then_open)
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


def test_rejects_source_changed_during_read(
    sources: Path, request_payload: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_read = os.read
    changed = False

    def read_then_change(descriptor, count):
        nonlocal changed
        content = original_read(descriptor, count)
        if content and not changed:
            changed = True
            (sources / "a.md").write_bytes(b"concurrently replaced bytes")
        return content

    monkeypatch.setattr(os, "read", read_then_change)
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


@pytest.mark.parametrize("root", ["relative-root", "/nonexistent/aquarium-fixture"])
def test_rejects_relative_or_missing_source_root(
    root: str, request_payload: dict
) -> None:
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(Path(root), request_payload)


@pytest.mark.parametrize("field", ["schema", "role", "node"])
def test_rejects_incomplete_request(
    sources: Path, request_payload: dict, field: str
) -> None:
    del request_payload[field]
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


@pytest.mark.parametrize("kind", ["directory", "fifo"])
def test_rejects_nonregular_sources(
    sources: Path, request_payload: dict, kind: str
) -> None:
    (sources / "role.md").unlink()
    if kind == "directory":
        (sources / "role.md").mkdir()
    else:
        os.mkfifo(sources / "role.md")
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


@pytest.mark.parametrize(
    "field",
    [
        "objective",
        "purpose",
        "instructions",
        "canonical_sources",
        "context",
        "selected_evidence",
        "permitted_effects",
        "deliverables",
        "success_criteria",
    ],
)
def test_rejects_incomplete_node(
    sources: Path, request_payload: dict, field: str
) -> None:
    del request_payload["node"][field]
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


@pytest.mark.parametrize(
    "field",
    [
        "work_identity",
        "goal_ref",
        "goal_revision",
        "target",
        "base",
        "procedure",
        "node",
    ],
)
def test_rejects_incomplete_context(
    sources: Path, request_payload: dict, field: str
) -> None:
    del request_payload["node"]["context"][field]
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("objective", "  "),
        ("purpose", None),
        ("instructions", 3),
        ("canonical_sources", []),
        ("deliverables", []),
        ("success_criteria", [""]),
        ("permitted_effects", {"allowed": []}),
        ("selected_evidence", None),
    ],
)
def test_rejects_empty_or_malformed_required_inputs(
    sources: Path, request_payload: dict, field: str, value
) -> None:
    request_payload["node"][field] = value
    with pytest.raises(preparation.PreparationError):
        preparation.prepare(sources, request_payload)


def test_explicit_empty_evidence_dependencies_and_effects_are_valid(
    sources: Path, request_payload: dict
) -> None:
    request_payload["role"]["dependencies"] = []
    request_payload["node"]["selected_evidence"] = []
    request_payload["node"]["permitted_effects"] = {"allowed": [], "excluded": []}
    result = preparation.prepare(sources, request_payload)
    assert len(result["prepared_role_snapshot"]["files"]) == 1
    assert result["prepared_assignment"]["node"]["selected_evidence"] == []


def run_cli(sources: Path, payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--source-root", str(sources), "--input", "-"],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_cli_stdin_and_file_produce_same_deterministic_json(
    sources: Path, request_payload: dict, tmp_path: Path
) -> None:
    payload = json.dumps(request_payload)
    request_file = tmp_path / "request.json"
    request_file.write_text(payload, encoding="utf-8")
    stdin = run_cli(sources, payload)
    file = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source-root",
            str(sources),
            "--input",
            str(request_file),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert stdin.returncode == file.returncode == 0
    assert stdin.stderr == file.stderr == ""
    assert stdin.stdout == file.stdout
    assert stdin.stdout.encode("ascii") == (
        preparation.canonical_bytes(preparation.prepare(sources, request_payload))
        + b"\n"
    )


@pytest.mark.parametrize(
    "payload", ["{", "null", '{"schema":"a","schema":"b"}', '{"schema":NaN}', "{}"]
)
def test_cli_rejects_bad_json_without_partial_output(
    sources: Path, payload: str
) -> None:
    result = run_cli(sources, payload)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr


def test_cli_rejects_unreadable_evidence_without_partial_output(
    sources: Path, request_payload: dict
) -> None:
    (sources / "evidence.bin").unlink()
    result = run_cli(sources, json.dumps(request_payload))
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr
