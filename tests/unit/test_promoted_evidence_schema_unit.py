"""Validate the public v2 manifest shape, independently of skill decisions."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "plugins/aquarium/assets/schemas/promoted-evidence-v2.schema.json"


@pytest.fixture
def validator():
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def manifest(scope="stage"):
    return {
        "schema": "aquarium.promoted-evidence/v2",
        "work_unit": {"kind": "task", "id": "TASK-124"},
        "purpose": "hardening-deferral",
        "target": {
            "identity": {
                "schema_version": "mulgae-live-source.v1",
                "scope": scope,
                "operand": (
                    "a..b" if scope == "diff" else "HEAD~1" if scope == "commit" else ""
                ),
                "base_oid": "a" * 40 if scope in {"stage", "commit", "diff"} else "",
                "head_oid": "b" * 40 if scope in {"head", "commit", "diff"} else "",
                "empty_base": False,
            },
            "source_identity_sha256": "sha256:" + "c" * 64,
            "consistency": (
                "caller_maintained"
                if scope in {"workspace", "stage"}
                else "resolved_git_objects"
            ),
        },
        "source": {"tool": "mulgae"},
        "payloads": [
            {
                "path": "findings.json",
                "media_type": "application/json",
                "sha256": "sha256:" + "d" * 64,
            }
        ],
    }


@pytest.mark.parametrize("scope", ["workspace", "stage", "head", "commit", "diff"])
def test_native_source_scopes_and_consistency(validator, scope):
    value = manifest(scope)
    validator.validate(value)
    value["target"]["consistency"] = (
        "resolved_git_objects"
        if scope in {"workspace", "stage"}
        else "caller_maintained"
    )
    assert not validator.is_valid(value)


@pytest.mark.parametrize("scope", ["stage", "commit"])
def test_native_empty_base_is_supported(validator, scope):
    value = manifest(scope)
    value["target"]["identity"].update(base_oid="", empty_base=True)
    validator.validate(value)


@pytest.mark.parametrize(
    "scope,updates",
    [
        ("workspace", {"operand": "x"}),
        ("workspace", {"base_oid": "a" * 40}),
        ("workspace", {"head_oid": "b" * 40}),
        ("workspace", {"empty_base": True}),
        ("head", {"operand": "x"}),
        ("head", {"base_oid": "a" * 40}),
        ("head", {"head_oid": ""}),
        ("head", {"empty_base": True}),
        ("stage", {"operand": "x"}),
        ("stage", {"head_oid": "b" * 40}),
        ("stage", {"base_oid": ""}),
        ("stage", {"empty_base": True}),
        ("commit", {"operand": ""}),
        ("commit", {"head_oid": ""}),
        ("commit", {"base_oid": ""}),
        ("commit", {"empty_base": True}),
        ("diff", {"operand": ""}),
        ("diff", {"base_oid": ""}),
        ("diff", {"head_oid": ""}),
        ("diff", {"empty_base": True}),
    ],
)
def test_native_impossible_identity_combinations_are_rejected(
    validator, scope, updates
):
    value = manifest(scope)
    value["target"]["identity"].update(updates)
    assert not validator.is_valid(value)


@pytest.mark.parametrize(
    "path",
    [
        ("target", "source_identity_sha256"),
        ("target", "identity", "head_oid"),
        ("target", "consistency"),
        ("payloads",),
    ],
)
def test_missing_binding_or_payload_is_rejected(validator, path):
    value = manifest()
    parent = value
    for key in path[:-1]:
        parent = parent[key]
    del parent[path[-1]]
    assert not validator.is_valid(value)


@pytest.mark.parametrize(
    "path",
    [
        "../findings.json",
        "/findings.json",
        "sub/findings.json",
        "manifest.json",
        "findings.json\n",
    ],
)
def test_payload_paths_are_package_basenames(validator, path):
    value = manifest()
    value["payloads"][0]["path"] = path
    assert not validator.is_valid(value)


def test_capture_claims_private_identity_and_invalid_metadata_are_rejected(validator):
    for owner, key, data in [
        ("target", "content_sha256", "sha256:" + "e" * 64),
        ("source", "run_id", "private-run"),
        ("source", "provider", "private-provider"),
        ("target", "source_identity_sha256", "sha256:invalid"),
    ]:
        value = manifest()
        value[owner][key] = data
        assert not validator.is_valid(value)
    value = manifest()
    value["target"]["identity"]["scope"] = "dirty"
    assert not validator.is_valid(value)
    value = manifest()
    value["work_unit"] = {"kind": "epic", "id": ""}
    assert not validator.is_valid(value)


def test_epic_and_multiple_structured_payloads_are_supported(validator):
    value = manifest("head")
    value["work_unit"] = {"kind": "epic", "id": "EPIC-023"}
    other = copy.deepcopy(value["payloads"][0])
    other["path"] = "assessment.json"
    value["payloads"].append(other)
    validator.validate(value)


def test_native_work_unit_scope_and_suffix_are_preserved(validator):
    value = manifest()
    value["work_unit"]["id"] = "backend:TASK-124a"
    validator.validate(value)
