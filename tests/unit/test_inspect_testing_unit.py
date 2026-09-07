from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIRECTORY = ROOT / "plugins/aquarium/skills/test-setup/scripts"
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import inspect_testing


def test_selected_profile_distinguishes_supported_root_shapes() -> None:
    assert inspect_testing.selected_profile(["python"]) == "make"
    assert inspect_testing.selected_profile(["typescript"]) == "typescript-bun"
    assert inspect_testing.selected_profile(["python", "typescript"]) == "polyglot-make"


@pytest.mark.parametrize(
    ("command", "parser"),
    [
        ("'pytest' tests -k 'left or right'", "pytest"),
        ("pytest tests -k 'left;right'", "pytest"),
        ("pytest unit&&pytest integration", "pytest"),
        ("pytest unit && other-runner integration", "generic"),
        ("pytest tests || true", "generic"),
        ("pytest tests\nother-runner integration", "generic"),
    ],
)
def test_parser_follows_commands_and_preserves_quoted_arguments(
    command: str, parser: str
) -> None:
    assert inspect_testing.stage_output_parser([command], {}) == parser


def test_package_dependencies_uses_only_mapping_sections() -> None:
    dependencies = inspect_testing.package_dependencies(
        {
            "dependencies": {"runtime": "1.0.0"},
            "devDependencies": {"pytest": "9.1.1"},
            "peerDependencies": ["ignored"],
        }
    )

    assert dependencies == {"runtime", "pytest"}
