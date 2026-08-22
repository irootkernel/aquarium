from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIRECTORY = ROOT / "plugins/aquarium/skills/test-setup/scripts"
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import inspect_testing


def test_selected_profile_distinguishes_supported_root_shapes() -> None:
    assert inspect_testing.selected_profile(["python"]) == "make"
    assert inspect_testing.selected_profile(["typescript"]) == "typescript-bun"
    assert inspect_testing.selected_profile(["python", "typescript"]) == "polyglot-make"


def test_parse_makefile_preserves_serial_recursive_stage_order() -> None:
    targets, phony, includes = inspect_testing.parse_makefile(
        """\
.PHONY: test test-prepare test-unit test-int test-e2e
test:
\t$(MAKE) test-prepare
\t$(MAKE) test-unit
\t$(MAKE) test-int
\t$(MAKE) test-e2e
"""
    )

    recipe = targets["test"][0]["recipe"]
    calls = [
        inspect_testing.RECURSIVE_MAKE_PATTERN.search(line).group(1) for line in recipe
    ]

    assert calls == list(inspect_testing.MAKE_STAGES)
    assert phony == set(inspect_testing.MAKE_TARGETS)
    assert includes == []


def test_package_dependencies_uses_only_mapping_sections() -> None:
    dependencies = inspect_testing.package_dependencies(
        {
            "dependencies": {"runtime": "1.0.0"},
            "devDependencies": {"pytest": "9.1.1"},
            "peerDependencies": ["ignored"],
        }
    )

    assert dependencies == {"runtime", "pytest"}
