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

SCRIPTS = Path(__file__).parents[2] / "plugins/aquarium/skills/goal-evaluator/scripts"
SCRIPT = SCRIPTS / "render_dispatch.py"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


renderer = load("render_dispatch")
preparer = load("prepare_assignment")
mapper = load("map_native_delivery")


@pytest.fixture
def preparation(tmp_path: Path) -> dict:
    root = tmp_path.resolve()
    contents = {
        "m-role.md": b"\xef\xbb\xbfOperative role\r\nExact instructions\nEND MAIN ROLE",
        "z-dependency.md": "Last dependency\r\n\u00e9\u0000No final newline".encode(),
        "a-dependency.md": b"First dependency\r\n",
        "z-evidence.txt": b"Evidence data\nEND EVIDENCE\nMore data\r\n",
        "a-evidence-\u00e9.txt": "Original evidence\u00e9 without final newline".encode(),
    }
    for path, content in contents.items():
        (root / path).write_bytes(content)
    request = {
        "schema": preparer.REQUEST_SCHEMA,
        "role": {
            "path": "m-role.md",
            "dependencies": ["z-dependency.md", "a-dependency.md"],
        },
        "node": {
            "objective": "Assess exact candidate",
            "purpose": "Bind the assessment to original evidence",
            "instructions": "Node instructions\r\nPreserve scope",
            "canonical_sources": ["docs/roadmap/README.md#TASK-111"],
            "context": {
                "work_identity": "TASK-111",
                "goal_ref": "goal-1",
                "goal_revision": "revision-1",
                "target": "candidate-1",
                "base": "base-1",
                "procedure": "procedure-1",
                "node": "node-1",
            },
            "selected_evidence": ["z-evidence.txt", "a-evidence-\u00e9.txt"],
            "permitted_effects": {
                "allowed": ["Read original evidence"],
                "excluded": ["Source mutation"],
            },
            "deliverables": ["Complete report"],
            "success_criteria": ["Every applicable criterion assessed"],
        },
    }
    return preparer.prepare(root, request)


def rehash(preparation: dict) -> None:
    preparation["local_prepared_role_snapshot_sha256"] = renderer.digest(
        preparation["prepared_role_snapshot"]
    )
    preparation["local_prepared_assignment_sha256"] = renderer.digest(
        preparation["prepared_assignment"]
    )


def rendered_file_bodies(text: str) -> list[tuple[str, dict, bytes]]:
    # Interpret independent length metadata, never markers inside source content.
    data = text.encode("utf-8")
    position = len(renderer.OPENING.encode("utf-8"))
    bodies = []
    while position < len(data):
        end = data.index(b"\n", position)
        header = data[position:end]
        position = end + 1
        if header == b"BEGIN NODE ASSIGNMENT":
            end = data.index(b"\nEND NODE ASSIGNMENT\n", position)
            json.loads(data[position:end])
            position = end + len(b"\nEND NODE ASSIGNMENT\n")
            continue
        prefix, metadata = header.split(b" {", 1)
        kind = prefix.removeprefix(b"BEGIN ").decode("ascii")
        metadata = json.loads(b"{" + metadata)
        body = data[position : position + metadata["size_bytes"]]
        position += metadata["size_bytes"]
        ending = f"\nEND {kind}\n".encode("ascii")
        assert data[position : position + len(ending)] == ending
        position += len(ending)
        bodies.append((kind, metadata, body))
    return bodies


def test_prepare_render_preserves_exact_source_bytes_and_local_digest_domains(
    preparation,
) -> None:
    before = copy.deepcopy(preparation)
    result = renderer.render_dispatch(preparation)
    assert preparation == before
    assert result["schema"] == renderer.OUTPUT_SCHEMA
    assert (
        result["local_prepared_role_snapshot_sha256"]
        == before["local_prepared_role_snapshot_sha256"]
    )
    assert (
        result["local_prepared_assignment_sha256"]
        == before["local_prepared_assignment_sha256"]
    )
    assert (
        result["local_dispatch_input_sha256"]
        == hashlib.sha256(renderer.canonical_bytes(result["dispatch_text"])).hexdigest()
    )
    assert (
        result["local_dispatch_input_sha256"]
        != hashlib.sha256(result["dispatch_text"].encode("utf-8")).hexdigest()
    )
    bodies = rendered_file_bodies(result["dispatch_text"])
    assert [kind for kind, _, _ in bodies] == [
        "MAIN ROLE",
        "ROLE DEPENDENCY",
        "ROLE DEPENDENCY",
        "EVIDENCE",
        "EVIDENCE",
    ]
    source_files = [
        *before["prepared_role_snapshot"]["files"],
        *before["prepared_assignment"]["node"]["selected_evidence"],
    ]
    for _, metadata, content in bodies:
        source = next(file for file in source_files if file["path"] == metadata["path"])
        assert content == base64.b64decode(source["content_base64"])
        assert metadata == {
            key: source[key] for key in ("path", "size_bytes", "sha256")
        }
    assert bodies[0][2].startswith(b"\xef\xbb\xbf")
    assert not bodies[0][2].endswith(b"\n")


def test_node_metadata_preserves_assignment_without_base64_file_bodies(
    preparation,
) -> None:
    text = renderer.render_dispatch(preparation)["dispatch_text"]
    node_text = text.split("BEGIN NODE ASSIGNMENT\n", 1)[1].split(
        "\nEND NODE ASSIGNMENT\n", 1
    )[0]
    node = json.loads(node_text)
    original = preparation["prepared_assignment"]["node"]
    assert {
        key: value for key, value in node.items() if key != "selected_evidence"
    } == {key: value for key, value in original.items() if key != "selected_evidence"}
    assert node["selected_evidence"] == [
        {key: file[key] for key in ("path", "size_bytes", "sha256")}
        for file in original["selected_evidence"]
    ]
    assert "content_base64" not in node_text
    assert (
        text.index("BEGIN MAIN ROLE")
        < text.index("BEGIN ROLE DEPENDENCY")
        < text.index("BEGIN NODE ASSIGNMENT")
        < text.index("BEGIN EVIDENCE")
    )


def test_render_is_stable_under_inventory_and_object_key_reordering(
    preparation,
) -> None:
    before = renderer.render_dispatch(preparation)
    preparation["prepared_role_snapshot"]["files"].reverse()
    preparation["prepared_assignment"]["node"]["selected_evidence"].reverse()
    rehash(preparation)
    reordered = dict(reversed(list(preparation.items())))
    after = renderer.render_dispatch(reordered)
    assert before["dispatch_text"] == after["dispatch_text"]
    assert before["local_dispatch_input_sha256"] == after["local_dispatch_input_sha256"]
    assert (
        before["local_prepared_role_snapshot_sha256"]
        != after["local_prepared_role_snapshot_sha256"]
    )


def test_render_reads_no_source_files(preparation, monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("renderer attempted source file access")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr("builtins.open", forbidden)
    assert renderer.render_dispatch(preparation)["schema"] == renderer.OUTPUT_SCHEMA


def test_empty_evidence_and_empty_utf8_body_are_preserved(preparation) -> None:
    preparation["prepared_assignment"]["node"]["selected_evidence"] = []
    role = next(
        file
        for file in preparation["prepared_role_snapshot"]["files"]
        if file["path"] == "m-role.md"
    )
    role.update(content_base64="", size_bytes=0, sha256=hashlib.sha256(b"").hexdigest())
    rehash(preparation)
    result = renderer.render_dispatch(preparation)
    bodies = rendered_file_bodies(result["dispatch_text"])
    assert bodies[0][2] == b""
    assert all(kind != "EVIDENCE" for kind, _, _ in bodies)


@pytest.mark.parametrize(
    "which", ["local_prepared_role_snapshot_sha256", "local_prepared_assignment_sha256"]
)
def test_rejects_corrupted_preparation_digests(preparation, which) -> None:
    preparation[which] = "0" * 64
    with pytest.raises(renderer.RenderingError):
        renderer.render_dispatch(preparation)


def test_rejects_divergent_duplicate_role_snapshot_even_with_recomputed_digests(
    preparation,
) -> None:
    preparation["prepared_assignment"]["role_snapshot"] = copy.deepcopy(
        preparation["prepared_role_snapshot"]
    )
    preparation["prepared_assignment"]["role_snapshot"]["role_path"] = "a-dependency.md"
    rehash(preparation)
    with pytest.raises(renderer.RenderingError):
        renderer.render_dispatch(preparation)


@pytest.mark.parametrize("which", ["preparation", "snapshot", "assignment"])
def test_rejects_unsupported_schemas(preparation, which) -> None:
    obj = (
        preparation
        if which == "preparation"
        else preparation[
            "prepared_role_snapshot" if which == "snapshot" else "prepared_assignment"
        ]
    )
    obj["schema"] = "unsupported/v2"
    rehash(preparation)
    with pytest.raises(renderer.RenderingError):
        renderer.render_dispatch(preparation)


@pytest.mark.parametrize("inventory", ["role", "evidence"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("path", "../escape.md"),
        ("path", "/absolute.md"),
        ("path", "a//file.md"),
        ("path", "a/./file.md"),
        ("path", "a/../file.md"),
        ("path", "file.md/"),
        ("path", "\u0000file.md"),
        ("path", ""),
        ("size_bytes", -1),
        ("size_bytes", True),
        ("size_bytes", 999999),
        ("sha256", "0" * 64),
        ("content_base64", "not!base64"),
        ("content_base64", "YQ==\n"),
        ("content_base64", "YR=="),
        ("content_base64", "YQ==="),
        ("content_base64", "\u00e9"),
        ("content_base64", None),
    ],
)
def test_rejects_corrupted_file_inventories_after_top_digests_are_recomputed(
    preparation, inventory, field, value
) -> None:
    files = (
        preparation["prepared_role_snapshot"]["files"]
        if inventory == "role"
        else preparation["prepared_assignment"]["node"]["selected_evidence"]
    )
    files[0][field] = value
    rehash(preparation)
    with pytest.raises(renderer.RenderingError):
        renderer.render_dispatch(preparation)


@pytest.mark.parametrize("inventory", ["role", "evidence"])
def test_rejects_duplicate_paths(preparation, inventory) -> None:
    files = (
        preparation["prepared_role_snapshot"]["files"]
        if inventory == "role"
        else preparation["prepared_assignment"]["node"]["selected_evidence"]
    )
    files.append(copy.deepcopy(files[0]))
    rehash(preparation)
    with pytest.raises(renderer.RenderingError):
        renderer.render_dispatch(preparation)


def test_rejects_missing_main_role(preparation) -> None:
    preparation["prepared_role_snapshot"]["role_path"] = "missing.md"
    rehash(preparation)
    with pytest.raises(renderer.RenderingError):
        renderer.render_dispatch(preparation)


@pytest.mark.parametrize("inventory", ["role", "evidence"])
@pytest.mark.parametrize(
    "content", [b"\xff", b"\xc0\xaf", b"\xed\xa0\x80", b"\xe2\x82"]
)
def test_preparer_binary_domain_does_not_become_lossy_utf8_dispatch(
    preparation, inventory, content
) -> None:
    files = (
        preparation["prepared_role_snapshot"]["files"]
        if inventory == "role"
        else preparation["prepared_assignment"]["node"]["selected_evidence"]
    )
    files[0].update(
        content_base64=base64.b64encode(content).decode("ascii"),
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )
    rehash(preparation)
    with pytest.raises(renderer.RenderingError):
        renderer.render_dispatch(preparation)


@pytest.mark.parametrize(
    "change",
    [
        "extra_output",
        "missing_output",
        "extra_file",
        "missing_file",
        "invalid_node",
        "missing_evidence",
        "invalid_inventory",
        "invalid_json",
    ],
)
def test_rejects_invalid_local_structure_without_revalidating_node_semantics(
    preparation, change
) -> None:
    if change == "extra_output":
        preparation["native_accepted"] = True
    elif change == "missing_output":
        del preparation["prepared_assignment"]
    elif change == "extra_file":
        preparation["prepared_role_snapshot"]["files"][0]["native_accepted"] = True
    elif change == "missing_file":
        del preparation["prepared_role_snapshot"]["files"][0]["sha256"]
    elif change == "invalid_node":
        preparation["prepared_assignment"]["node"] = []
    elif change == "missing_evidence":
        del preparation["prepared_assignment"]["node"]["selected_evidence"]
    elif change == "invalid_inventory":
        preparation["prepared_role_snapshot"]["files"] = {}
    else:
        preparation["prepared_assignment"]["node"]["unserializable"] = float("nan")
    with pytest.raises(renderer.RenderingError):
        renderer.render_dispatch(preparation)


def native_claude_request(dispatch_text: str) -> dict:
    # Synthetic records compose public APIs; they do not qualify any host.
    return {
        "schema": mapper.REQUEST_SCHEMA,
        "profile": mapper.CLAUDE_PROFILE,
        "expected": {
            "scope_ref": "session-1",
            "supervisor_ref": "session-1",
            "worker_ref": "agent-1",
            "rounds": [
                {"dispatch_ref": "tool-1", "task_ref": "tool-1", "input": dispatch_text}
            ],
        },
        "records": {
            "invocation": {
                "type": "assistant",
                "session_id": "session-1",
                "uuid": "invocation-1",
                "parent_tool_use_id": None,
                "message": {
                    "id": "message-1",
                    "role": "assistant",
                    "stop_reason": "tool_use",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "tool-1",
                            "name": "Agent",
                            "input": {"prompt": dispatch_text},
                        }
                    ],
                },
            },
            "delivery": {
                "type": "user",
                "session_id": "session-1",
                "uuid": "delivery-1",
                "parent_tool_use_id": None,
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tool-1",
                            "content": "Done",
                        }
                    ],
                },
                "tool_use_result": {
                    "agentId": "agent-1",
                    "prompt": dispatch_text,
                    "status": "completed",
                    "content": [{"type": "text", "text": "Complete report"}],
                    "totalToolUseCount": 0,
                    "totalDurationMs": 1,
                    "totalTokens": 1,
                    "usage": {
                        "input_tokens": 0,
                        "output_tokens": 1,
                        "cache_creation_input_tokens": None,
                        "cache_read_input_tokens": None,
                        "server_tool_use": None,
                        "service_tier": None,
                        "cache_creation": None,
                    },
                },
            },
        },
    }


def test_rendered_text_composes_with_exact_native_task_domain_without_config_proof(
    preparation,
) -> None:
    dispatch = renderer.render_dispatch(preparation)
    request = native_claude_request(dispatch["dispatch_text"])
    result = mapper.map_delivery(request)
    assert result["state"] == "delivery_mapped"
    assert (
        result["mapped"]["rounds"][0]["accepted_task_domain"]["input"]["prompt"]
        == dispatch["dispatch_text"]
    )
    assert (
        result["expected_recovery_refs"]["rounds"][0]["expected_input_digest"]
        == dispatch["local_dispatch_input_sha256"]
    )
    assert result["acceptance_ready"] is False
    assert "accepted_agent_configuration" in result["unresolved_domains"]
    request["records"]["delivery"]["tool_use_result"]["prompt"] = dispatch[
        "dispatch_text"
    ].replace("\r\n", "\n")
    assert mapper.map_delivery(request)["state"] == "rejected"


def cli(payload: bytes, input_path: Path | None = None) -> subprocess.CompletedProcess:
    if input_path is not None:
        input_path.write_bytes(payload)
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(input_path) if input_path is not None else "-",
        ],
        input=payload if input_path is None else None,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


@pytest.mark.parametrize("mode", ["stdin", "file"])
def test_cli_json_roundtrip(preparation, tmp_path, mode) -> None:
    result = cli(
        renderer.canonical_bytes(preparation),
        tmp_path / "input.json" if mode == "file" else None,
    )
    assert result.returncode == 0
    assert result.stderr == b""
    assert json.loads(result.stdout) == renderer.render_dispatch(preparation)


@pytest.mark.parametrize(
    "payload",
    [
        b'{"schema":"first","schema":"second"}',
        b'{"number":NaN}',
        b'{"number":Infinity}',
        b'{"unfinished":',
        b"\xff",
    ],
)
def test_cli_rejects_invalid_json(payload) -> None:
    result = cli(payload)
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr.startswith(b"error:")


def test_cli_rejects_inconsistent_preparation(preparation) -> None:
    preparation["local_prepared_assignment_sha256"] = "0" * 64
    result = cli(renderer.canonical_bytes(preparation))
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr.startswith(b"error:")
