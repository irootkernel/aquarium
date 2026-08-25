from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "verify_podway_compatibility.py"
SPEC = importlib.util.spec_from_file_location("verify_podway_compatibility", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verify_podway_compatibility = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_podway_compatibility)


def test_replace_once_applies_one_exact_declaration_change() -> None:
    assert (
        verify_podway_compatibility.replace_once(
            b"before limit: 100 after",
            b"limit: 100",
            b"limit: 101",
            "limit",
        )
        == b"before limit: 101 after"
    )


@pytest.mark.parametrize("source", [b"missing", b"limit limit"])
def test_replace_once_rejects_fixture_drift(source: bytes) -> None:
    with pytest.raises(
        verify_podway_compatibility.CompatibilityError,
        match="canonical fixture drifted",
    ):
        verify_podway_compatibility.replace_once(source, b"limit", b"new", "limit")


def test_procedure_result_accepts_only_the_expected_contract() -> None:
    result = {"schema": "podway.procedure-diagnostics-result/v1", "valid": True}
    assert (
        verify_podway_compatibility.procedure_result(
            {
                "schema": "podway.output/v3",
                "command": "procedure.check",
                "result": result,
            }
        )
        is result
    )


def test_procedure_result_rejects_an_unexpected_envelope() -> None:
    with pytest.raises(
        verify_podway_compatibility.CompatibilityError,
        match="output envelope is incompatible",
    ):
        verify_podway_compatibility.procedure_result(
            {"schema": "podway.output/v4", "command": "procedure.check"}
        )


def test_exact_binary_requires_an_absolute_path() -> None:
    with pytest.raises(
        verify_podway_compatibility.CompatibilityError,
        match="absolute path",
    ):
        verify_podway_compatibility.exact_binary("podway")
