"""Minimum-version admission for Python distributions and standalone Ruff."""

import importlib.util
from pathlib import Path

import pytest
from packaging.version import Version

SCRIPT = Path(__file__).parents[1] / "check_test_requirements.py"
SPEC = importlib.util.spec_from_file_location("check_test_requirements", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


@pytest.mark.parametrize("installed", ["9.1.1", "9.2.0", "10.0.0", "10.0.0rc1"])
def test_equal_and_higher_dependency_versions_are_admitted(installed: str) -> None:
    assert (
        checker.dependency_errors({"pytest": Version("9.1.1")}, {"pytest": installed})
        == []
    )


@pytest.mark.parametrize("installed", ["9.1.0", "9.1.1rc1"])
def test_lower_dependency_versions_are_rejected(installed: str) -> None:
    assert checker.dependency_errors(
        {"pytest": Version("9.1.1")}, {"pytest": installed}
    )


def test_missing_distribution_remains_a_prerequisite_failure() -> None:
    assert checker.dependency_errors({"pytest": Version("9.1.1")}, {})


@pytest.mark.parametrize("installed", ["0.16.2", "0.16.8", "0.16.10", "0.17.0"])
def test_standalone_ruff_equal_or_above_minimum_is_admitted(installed: str) -> None:
    assert checker.dependency_errors({"ruff": Version("0.16.2")}, {}) == []
    assert checker.ruff_error(f"ruff {installed}\n", 0, Version("0.16.2")) is None


@pytest.mark.parametrize(
    ("output", "exit_code"), [("ruff 0.16.1", 0), ("unavailable", 1)]
)
def test_old_or_failed_ruff_is_rejected(output: str, exit_code: int) -> None:
    assert checker.ruff_error(output, exit_code, Version("0.16.2"))


def test_minimum_declarations_normalize_names_and_preserve_bounds(
    tmp_path: Path,
) -> None:
    path = tmp_path / "requirements.txt"
    path.write_text("# Development minimums\nPyYAML >= 6.0.3\nruff>=0.16.2\n")
    assert checker.read_minimums(path) == {
        "pyyaml": Version("6.0.3"),
        "ruff": Version("0.16.2"),
    }


@pytest.mark.parametrize(
    "content", ["pytest==9.1.1", "pytest>=9.1.1,<10", "pytest>=9.1.1\nPyTest>=9.2.0"]
)
def test_fixed_upper_bounded_or_duplicate_declarations_are_rejected(
    tmp_path: Path, content: str
) -> None:
    path = tmp_path / "requirements.txt"
    path.write_text(content)
    with pytest.raises(ValueError):
        checker.read_minimums(path)
