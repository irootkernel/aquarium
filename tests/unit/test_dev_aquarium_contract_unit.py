import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "plugins/aquarium/skills/dev-aquarium/scripts/dev_contract.py"
SPEC = importlib.util.spec_from_file_location("dev_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
dev_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dev_contract)
FIXTURES = ROOT / "tests/fixtures/dev_aquarium"


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
