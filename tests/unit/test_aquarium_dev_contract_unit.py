import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "plugins/aquarium/skills/aquarium-dev/scripts/dev_contract.py"
SPEC = importlib.util.spec_from_file_location("dev_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
dev_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dev_contract)
FIXTURES = ROOT / "tests/fixtures/aquarium_dev"


@pytest.mark.parametrize(
    ("name", "validator"),
    [
        ("description", dev_contract.validate_description),
        ("manifest", dev_contract.validate_manifest),
        ("result", dev_contract.validate_result),
        ("error", dev_contract.validate_error),
    ],
)
def test_positive_contract_fixtures(name, validator):
    document = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    assert validator(document) == document


def test_dolgorae_is_a_supported_executable_producer():
    description = json.loads(
        (FIXTURES / "description.json").read_text(encoding="utf-8")
    )
    description.update(
        project_id="dolgorae", artifact_kind="executable", artifact_path="bin/dolgorae"
    )

    assert dev_contract.validate_description(description) == description


@pytest.mark.parametrize(
    ("project_id", "artifact_kind", "artifact_path"),
    (
        ("aquarium", "executable", "bin/aquarium"),
        ("podway", "executable", "bin/other"),
        ("mulgae", "codex-plugin", "plugin"),
    ),
)
def test_project_artifact_contract_is_exact(project_id, artifact_kind, artifact_path):
    description = json.loads(
        (FIXTURES / "description.json").read_text(encoding="utf-8")
    )
    description.update(
        project_id=project_id,
        artifact_kind=artifact_kind,
        artifact_path=artifact_path,
    )

    with pytest.raises(dev_contract.ContractError):
        dev_contract.validate_description(description)


def test_manifest_rejects_noncanonical_tool_executable_path():
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    manifest.update(
        project_id="podway",
        artifact_kind="executable",
        artifact_path="tools/podway",
    )

    with pytest.raises(dev_contract.ContractError):
        dev_contract.validate_manifest(manifest)


def test_managed_service_v2_is_generic_and_strict():
    description = {
        "schema": "aquarium-dev-producer-description/v2",
        "project_id": "gaori",
        "next_version": "v0.2.0",
        "artifact_kind": "managed-service",
        "artifact_path": "bundle",
        "command_path": "bin/gaori",
        "controller_path": "libexec/aquarium-dev-service",
    }
    manifest = {
        "schema": "aquarium-dev-artifact-manifest/v2",
        "project_id": "gaori",
        "git_sha": "a" * 40,
        "development_version": "v0.2.0-dev.aaaaaaaaaaaa",
        "artifact_kind": "managed-service",
        "artifact_path": "bundle",
        "command_path": "bin/gaori",
        "controller_path": "libexec/aquarium-dev-service",
        "sha256": "sha256:" + "b" * 64,
    }

    assert dev_contract.validate_description(description) == description
    assert dev_contract.validate_manifest(manifest) == manifest
    description["controller_path"] = "bin/gaorid"
    with pytest.raises(dev_contract.ContractError):
        dev_contract.validate_description(description)


def test_podway_v1_executable_is_rejected():
    description = {
        "schema": "aquarium-dev-producer-description/v1",
        "project_id": "podway",
        "next_version": "v0.2.8",
        "artifact_kind": "executable",
        "artifact_path": "bin/podway",
    }

    with pytest.raises(dev_contract.ContractError, match="managed-service v2"):
        dev_contract.validate_description(description)


def test_service_protocol_contracts_bind_state_and_generation():
    status = {
        "schema": "aquarium-dev-service-status/v1",
        "project_id": "gaori",
        "state": "busy",
        "active_git_sha": "a" * 40,
        "busy": True,
        "recovery_required": False,
    }
    plan = {
        "schema": "aquarium-dev-service-plan/v1",
        "project_id": "gaori",
        "target_git_sha": "b" * 40,
        "action": "defer",
        "active_git_sha": "a" * 40,
        "busy": True,
        "plan_token": None,
    }
    result = {
        "schema": "aquarium-dev-service-result/v1",
        "project_id": "gaori",
        "status": "activated",
        "active_git_sha": "b" * 40,
        "recovery_required": False,
    }

    assert dev_contract.validate_service_status(status) == status
    assert dev_contract.validate_service_plan(plan) == plan
    assert dev_contract.validate_service_result(result) == result
    plan.update(action="activate", busy=False)
    with pytest.raises(dev_contract.ContractError, match="digest token"):
        dev_contract.validate_service_plan(plan)


@pytest.mark.parametrize(
    ("fixture", "validator", "mutation"),
    [
        (
            "description",
            dev_contract.validate_description,
            lambda value: value.update(extra=True),
        ),
        (
            "description",
            dev_contract.validate_description,
            lambda value: value.update(artifact_path="../plugin"),
        ),
        (
            "description",
            dev_contract.validate_description,
            lambda value: value.update(next_version="0.1.14"),
        ),
        (
            "manifest",
            dev_contract.validate_manifest,
            lambda value: value.update(git_sha="ABC"),
        ),
        (
            "manifest",
            dev_contract.validate_manifest,
            lambda value: value.update(development_version="v0.1.14-dev.ffffffffffff"),
        ),
        (
            "manifest",
            dev_contract.validate_manifest,
            lambda value: value.update(sha256="aaa"),
        ),
        (
            "result",
            dev_contract.validate_result,
            lambda value: value.update(operation="install"),
        ),
        (
            "result",
            dev_contract.validate_result,
            lambda value: value.update(details=[]),
        ),
        (
            "error",
            dev_contract.validate_error,
            lambda value: value["error"].update(code="unknown"),
        ),
        (
            "error",
            dev_contract.validate_error,
            lambda value: value["error"].update(git_sha="main"),
        ),
    ],
)
def test_negative_contract_cases(fixture, validator, mutation):
    document = json.loads((FIXTURES / f"{fixture}.json").read_text(encoding="utf-8"))
    mutation(document)
    with pytest.raises(dev_contract.ContractError):
        validator(document)
