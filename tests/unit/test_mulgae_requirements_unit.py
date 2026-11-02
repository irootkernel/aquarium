from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/mulgae-review/scripts/prepare_requirements.py"
)
SPEC = importlib.util.spec_from_file_location("requirements_input", SCRIPT)
assert SPEC and SPEC.loader
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def request():
    return {
        "roles": ["logic"],
        "criteria": [
            {
                "id": "한글 기준",
                "source": "docs/spec.md#goal",
                "text": "Preserve 한글",
                "acceptance_criteria": ["Index bytes match"],
                "owner_role": "logic",
            }
        ],
    }


def test_prepare_roundtrip_and_cleanup(tmp_path):
    prepared = helper.prepare(tmp_path, request())
    path = tmp_path / prepared["requirements_path"]
    native = json.loads(path.read_text())
    assert path.stat().st_mode & 0o777 == 0o600
    assert native["schema_version"] == "mulgae-requirements-input.v1"
    assert native["requirements"][0]["id"] == prepared["mapping"][0]["id"]
    assert prepared["mapping"][0]["original_id"] == "한글 기준"
    assert (
        native["requirements"][0]["text"]
        == "Preserve 한글\nAuthority: docs/spec.md#goal"
    )
    helper.cleanup(tmp_path, prepared)
    assert not path.exists()


@pytest.mark.parametrize(
    "mutation", ["owner", "empty", "duplicate", "too_many", "too_many_criteria", "nul"]
)
def test_invalid_inputs_do_not_create_files(tmp_path, mutation):
    data = request()
    row = data["criteria"][0]
    if mutation == "owner":
        row["owner_role"] = "security"
    elif mutation == "empty":
        data["criteria"] = []
    elif mutation == "duplicate":
        data["criteria"] *= 2
    elif mutation == "too_many":
        data["criteria"] = [dict(row, id=f"R{i}") for i in range(101)]
    elif mutation == "too_many_criteria":
        row["acceptance_criteria"] *= 33
    else:
        row["text"] = "invalid\0"
    with pytest.raises(ValueError):
        helper.prepare(tmp_path, data)
    assert list(tmp_path.iterdir()) == []


def test_mapping_reserves_native_ids_and_boundaries():
    data = request()
    row = data["criteria"][0]
    data["criteria"] = [row, dict(row, id="Aquarium1")]
    native, mapping = helper.build(data)
    assert [item["id"] for item in native["requirements"]] == [
        "Aquarium1_1",
        "Aquarium1",
    ]
    data["criteria"] = [
        dict(row, id=f"R{i}", acceptance_criteria=["criterion"] * 32)
        for i in range(100)
    ]
    native, mapping = helper.build(data)
    assert len(native["requirements"]) == len(mapping) == 100


@pytest.mark.parametrize("mutation", ["changed", "replaced", "symlink"])
def test_cleanup_preserves_changed_or_replaced_file(tmp_path, mutation):
    prepared = helper.prepare(tmp_path, request())
    path = tmp_path / prepared["requirements_path"]
    if mutation == "changed":
        path.write_text("user edit")
    else:
        other = tmp_path / "other"
        other.write_bytes(path.read_bytes())
        path.unlink()
        if mutation == "symlink":
            path.symlink_to(other)
        else:
            other.rename(path)
    with pytest.raises((ValueError, OSError)):
        helper.cleanup(tmp_path, prepared)
    assert path.exists()


def test_exclusive_creation_preserves_existing_file(tmp_path, monkeypatch):
    class Fixed:
        hex = "a" * 32

    monkeypatch.setattr(helper.uuid, "uuid4", lambda: Fixed())
    first = helper.prepare(tmp_path, request())
    with pytest.raises(FileExistsError):
        helper.prepare(tmp_path, request())
    helper.cleanup(tmp_path, first)


def test_write_failure_preserves_a_replacement(tmp_path, monkeypatch):
    real_fdopen = helper.os.fdopen

    class FailingWriter:
        def __init__(self, fd):
            self.stream = real_fdopen(fd, "wb")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.stream.close()

        def write(self, _raw):
            path = next(tmp_path.glob("aquarium-review-input-*.json"))
            path.unlink()
            path.write_text("replacement owned by user")
            raise OSError("write interrupted")

    monkeypatch.setattr(helper.os, "fdopen", lambda fd, _mode: FailingWriter(fd))
    with pytest.raises(OSError):
        helper.prepare(tmp_path, request())
    assert [path.read_text() for path in tmp_path.iterdir()] == [
        "replacement owned by user"
    ]
