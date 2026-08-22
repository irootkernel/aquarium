from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/aquarium/skills/test-setup/scripts/inspect_testing.py"

sys.path.insert(0, str(SCRIPT.parent))

import inspect_testing


class InspectTestingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary_directory.name) / "repository"
        self.repository.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative_path: str, content: str) -> None:
        path = self.repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content), encoding="utf-8")

    def enroll(self, profile: str) -> None:
        self.write(
            "TESTING.md",
            f"""\
            # Testing

            ## Contract

            Contract: aquarium-test-contract/v1
            Profile: {profile}

            ## Canonical Commands

            Fixture commands.

            ## Stage Mapping

            Fixture stages.

            ## Test Frameworks

            Fixture frameworks.

            ## Gaori Mapping

            Not configured.

            ## E2E Environment

            Disposable fixture.

            ## Language Diagnostics

            Not applicable.

            ## Legacy Waivers

            None.
            """,
        )

    def write_make_contract(self) -> None:
        self.write(
            "Makefile",
            """\
            .PHONY: test test-prepare test-unit test-int test-e2e

            test:
            \t$(MAKE) test-prepare
            \t$(MAKE) test-unit
            \t$(MAKE) test-int
            \t$(MAKE) test-e2e

            test-prepare:
            \t@true

            test-unit:
            \t@true

            test-int:
            \t@true

            test-e2e:
            \t@true
            """,
        )

    def write_bun_adapter(self) -> None:
        self.write(
            "Makefile",
            """\
            .PHONY: test test-prepare test-unit test-int test-e2e

            test:
            \tbun run test

            test-prepare:
            \tbun run test:prepare

            test-unit:
            \tbun run test:unit

            test-int:
            \tbun run test:int

            test-e2e:
            \tbun run test:e2e
            """,
        )

    def write_ginkgo_make_contract(self) -> None:
        self.write(
            "Makefile",
            """\
            .PHONY: test test-prepare test-unit test-int test-e2e
            test:
            \t$(MAKE) test-prepare
            \t$(MAKE) test-unit
            \t$(MAKE) test-int
            \t$(MAKE) test-e2e
            test-prepare:
            \t@true
            test-unit:
            \tginkgo -race ./...
            test-int:
            \tginkgo -race ./...
            test-e2e:
            \t@true
            """,
        )

    def write_ginkgo_evidence(self) -> None:
        self.write(
            "go.mod",
            """\
            module example.com/fixture

            go 1.26

            require (
                github.com/onsi/ginkgo/v2 v2.27.2
                github.com/onsi/gomega v1.38.2
            )
            """,
        )
        self.write(
            "go.sum",
            """\
            github.com/onsi/ginkgo/v2 v2.27.2 h1:fixture
            github.com/onsi/gomega v1.38.2 h1:fixture
            """,
        )
        self.write(
            "fixture_test.go",
            """\
            package fixture_test

            import (
                . "github.com/onsi/ginkgo/v2"
                . "github.com/onsi/gomega"
            )
            """,
        )

    def write_bun_package(self, test_command: str | None = None) -> None:
        package = {
            "name": "fixture",
            "private": True,
            "packageManager": "bun@1.3.14",
            "devDependencies": {"typescript": "1.0.0", "vitest": "4.0.0"},
            "scripts": {
                "test": test_command
                or "bun run test:prepare && bun run test:unit && bun run test:int && bun run test:e2e",
                "test:prepare": "bun run format && bun run lint && bun run typecheck",
                "test:unit": "bun run vitest run tests/unit",
                "test:int": "bun run vitest run tests/integration",
                "test:e2e": "python3 -m unittest discover tests/e2e",
            },
        }
        self.write("package.json", json.dumps(package))
        self.write("bun.lock", "")

    @staticmethod
    def framework(result: dict[str, object], language: str) -> dict[str, object]:
        frameworks = result["frameworks"]
        assert isinstance(frameworks, dict)
        entries = frameworks["entries"]
        assert isinstance(entries, list)
        return next(entry for entry in entries if entry["language"] == language)

    def test_conforming_make_profile(self) -> None:
        self.write_make_contract()
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["selected_profile"], "make")
        self.assertEqual(result["structural_status"], "conforming")
        self.assertEqual(result["make"]["aggregate_mode"], "recursive_recipe")
        self.assertEqual(
            result["make"]["aggregate_recursive_calls"],
            list(inspect_testing.MAKE_STAGES),
        )

    def test_symlinked_root_makefile_is_not_read(self) -> None:
        external = Path(self.temporary_directory.name) / "credentials.make"
        external.write_text("credential-marker: secret\n", encoding="utf-8")
        (self.repository / "Makefile").symlink_to(external)
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertFalse(result["make"]["present"])
        self.assertNotIn("credential-marker", json.dumps(result))

    def test_prerequisite_aggregate_is_parallel_unsafe(self) -> None:
        self.write(
            "Makefile",
            """\
            .PHONY: test test-prepare test-unit test-int test-e2e
            test: test-prepare test-unit test-int test-e2e
            test-prepare test-unit test-int test-e2e:
            \t@true
            """,
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(result["make"]["aggregate_mode"], "prerequisites")
        self.assertIn(
            "make_aggregate_parallel_unsafe",
            {item["code"] for item in result["findings"]},
        )

    def test_quoted_recursive_make_text_is_not_an_executable_stage(self) -> None:
        self.write(
            "Makefile",
            """\
            .PHONY: test test-prepare test-unit test-int test-e2e
            test:
            \t@echo '$(MAKE) test-prepare'
            \t@echo '$(MAKE) test-unit'
            \t@echo '$(MAKE) test-int'
            \t@echo '$(MAKE) test-e2e'
            test-prepare test-unit test-int test-e2e:
            \t@true
            """,
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(result["make"]["aggregate_mode"], "unverifiable")
        self.assertEqual(result["make"]["aggregate_recursive_calls"], [])

    def test_error_ignoring_recursive_make_calls_are_not_fail_fast(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        makefile.write_text(
            makefile.read_text(encoding="utf-8").replace("\t$(MAKE)", "\t-$(MAKE)"),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(result["make"]["aggregate_mode"], "unverifiable")
        self.assertEqual(result["make"]["aggregate_recursive_calls"], [])

    def test_extra_make_aggregate_command_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        makefile.write_text(
            makefile.read_text(encoding="utf-8").replace(
                "\t$(MAKE) test-unit", "\tfalse\n\t$(MAKE) test-unit"
            ),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(result["make"]["aggregate_mode"], "unverifiable")

    def test_oneshell_make_aggregate_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        makefile.write_text(
            ".ONESHELL:\n" + makefile.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertTrue(result["make"]["global_shell_semantics"])
        self.assertIn(
            "make_authority_unverifiable",
            {item["code"] for item in result["findings"]},
        )

    def test_custom_make_shell_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            "SHELL := /bin/true\n" + makefile.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertTrue(result["make"]["global_shell_semantics"])

    def test_makeflags_error_ignoring_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            "MAKEFLAGS += -i\n" + makefile.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertTrue(result["make"]["global_shell_semantics"])

    def test_included_make_authority_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            "include ignored.mk\n" + makefile.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.write("ignored.mk", ".IGNORE:\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertTrue(result["make"]["authority_includes_unresolved"])

    def test_conforming_typescript_bun_profile_and_make_adapter(self) -> None:
        self.write_bun_package()
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["detected_languages"], ["typescript"])
        self.assertEqual(result["selected_profile"], "typescript-bun")
        self.assertEqual(result["structural_status"], "conforming")
        self.assertTrue(result["bun"]["aggregate_serial"])
        self.assertEqual(result["make"]["aggregate_mode"], "bun_adapter")
        self.assertEqual(self.framework(result, "typescript")["status"], "canonical")
        self.assertEqual(
            result["frameworks"]["gaori"]["stage_parser_defaults"]["test-unit"],
            "vitest",
        )

    def test_bun_reverse_make_edge_and_unpinned_runtime_fail(self) -> None:
        self.write_bun_package(test_command="make test")
        package = json.loads(
            (self.repository / "package.json").read_text(encoding="utf-8")
        )
        package.pop("packageManager")
        (self.repository / "package.json").write_text(
            json.dumps(package), encoding="utf-8"
        )
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)
        codes = {item["code"] for item in result["findings"]}

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertIn("bun_aggregate_invalid", codes)
        self.assertIn("bun_make_cycle", codes)
        self.assertIn("bun_version_unpinned", codes)

    def test_polyglot_root_keeps_make_authority(self) -> None:
        self.write_ginkgo_make_contract()
        self.write_bun_package()
        self.write_ginkgo_evidence()
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["detected_languages"], ["go", "typescript"])
        self.assertEqual(result["selected_profile"], "polyglot-make")
        self.assertEqual(result["structural_status"], "conforming")
        self.assertEqual(result["make"]["aggregate_mode"], "recursive_recipe")
        self.assertEqual(
            result["frameworks"]["gaori"]["stage_parser_defaults"]["test-unit"],
            "generic",
        )

    def test_go_ginkgo_and_gomega_are_canonical(self) -> None:
        self.write_ginkgo_make_contract()
        self.write_ginkgo_evidence()
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "go")

        self.assertEqual(result["structural_status"], "conforming")
        self.assertEqual(framework["status"], "canonical")
        self.assertEqual(framework["unit_int_parser"], "ginkgo")

    def test_go_standard_testing_requires_legacy_waiver_review(self) -> None:
        self.write_make_contract()
        self.write("go.mod", "module example.com/fixture\n\ngo 1.26\n")
        self.write("thing_test.go", 'package fixture\n\nimport "testing"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "go")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertTrue(framework["waiver_required"])
        self.assertIn(
            "framework_waiver_required", {item["code"] for item in result["findings"]}
        )

    def test_stale_go_dependencies_do_not_select_ginkgo_parser(self) -> None:
        self.write_make_contract()
        self.write_ginkgo_evidence()
        self.repository.joinpath("go.sum").unlink()
        self.write("fixture_test.go", 'package fixture\n\nimport "testing"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "go")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["unit_int_parser"], "generic")
        self.assertTrue(framework["waiver_required"])

    def test_dependency_only_python_does_not_select_pytest_parser(self) -> None:
        self.write_make_contract()
        self.write(
            "pyproject.toml", '[project.optional-dependencies]\ntest = ["pytest>=8"]\n'
        )
        self.write("Cargo.toml", '[package]\nname = "fixture"\nversion = "0.1.0"\n')
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "generic")
        self.assertEqual(self.framework(result, "rust")["unit_int_parser"], "generic")
        self.assertEqual(
            result["frameworks"]["gaori"]["stage_parser_defaults"]["test-int"],
            "generic",
        )

    def test_python_mixed_frameworks_require_waiver_and_map_stage_parsers(self) -> None:
        self.write(
            "Makefile",
            """\
            .PHONY: test test-prepare test-unit test-int test-e2e

            test:
            \t$(MAKE) test-prepare
            \t$(MAKE) test-unit
            \t$(MAKE) test-int
            \t$(MAKE) test-e2e

            test-prepare:
            \t@true

            test-unit:
            \tpython3 -m pytest tests/unit

            test-int:
            \tpython3 -m unittest tests/test_integration.py

            test-e2e:
            \tpython3 -m pytest tests/e2e
            """,
        )
        self.write("pyproject.toml", "[tool.pytest.ini_options]\n")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "python")
        parsers = result["frameworks"]["gaori"]["stage_parser_defaults"]

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["detected"], ["pytest", "unittest"])
        self.assertTrue(framework["waiver_required"])
        self.assertEqual(parsers["test-unit"], "pytest")
        self.assertEqual(parsers["test-int"], "generic")

    def test_requirements_only_python_root_detects_mixed_frameworks(self) -> None:
        self.write(
            "Makefile",
            """\
            .PHONY: test test-prepare test-unit test-int test-e2e
            test:
            \t$(MAKE) test-prepare
            \t$(MAKE) test-unit
            \t$(MAKE) test-int
            \t$(MAKE) test-e2e
            test-prepare:
            \t@true
            test-unit:
            \tpython3 -m pytest tests/unit
            test-int:
            \tpython3 -m unittest tests/test_integration.py
            test-e2e:
            \tpython3 -m pytest tests/e2e
            """,
        )
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["detected_languages"], ["python"])
        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(
            self.framework(result, "python")["detected"], ["pytest", "unittest"]
        )

    def test_python_dependency_and_opaque_wrapper_are_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace("\t@true\n\ntest-int:", "\t./run-unit\n\ntest-int:")
            .replace("\t@true\n\ntest-e2e:", "\t./run-int\n\ntest-e2e:"),
            encoding="utf-8",
        )
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.write("tests/test_legacy.py", "import unittest\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "python")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["detected"], ["pytest", "unittest"])
        self.assertEqual(framework["unit_int_parser"], "generic")

    def test_invalid_root_package_manifest_is_nonconforming(self) -> None:
        self.write_make_contract()
        self.write("package.json", "{")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertIn(
            "package_json_invalid", {item["code"] for item in result["findings"]}
        )

    def test_testing_document_profile_must_match_executable_authority(self) -> None:
        self.write_make_contract()
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertIn(
            "testing_profile_mismatch", {item["code"] for item in result["findings"]}
        )

    def test_testing_document_requires_every_contract_section(self) -> None:
        self.write_make_contract()
        self.write("TESTING.md", "Contract: aquarium-test-contract/v1\n")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertIn(
            "testing_sections_missing", {item["code"] for item in result["findings"]}
        )

    def test_testing_document_requires_nonempty_contract_sections(self) -> None:
        self.write_make_contract()
        headings = "\n\n".join(
            f"## {heading}" for heading in inspect_testing.TESTING_HEADINGS
        )
        self.write(
            "TESTING.md",
            f"# Testing\n\n{headings}\n\nContract: aquarium-test-contract/v1\nProfile: make\n",
        )

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertFalse(result["testing_document"]["sections"]["Canonical Commands"])
        self.assertIn(
            "testing_sections_missing", {item["code"] for item in result["findings"]}
        )

    def test_contract_marker_outside_contract_section_does_not_enroll(self) -> None:
        self.write_make_contract()
        self.enroll("make")
        document = self.repository.joinpath("TESTING.md")
        content = document.read_text(encoding="utf-8")
        content = content.replace(
            "Contract: aquarium-test-contract/v1\nProfile: make",
            "This repository is not enrolled.\nProfile: make",
        ).replace("None.\n", "Rejected contract: aquarium-test-contract/v1\n")
        document.write_text(content, encoding="utf-8")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertFalse(result["testing_document"]["contract_registered"])
        self.assertIn(
            "testing_contract_unregistered",
            {item["code"] for item in result["findings"]},
        )

    def test_bun_test_requires_typescript_framework_waiver(self) -> None:
        self.write_bun_package()
        package = json.loads(
            (self.repository / "package.json").read_text(encoding="utf-8")
        )
        package["devDependencies"].pop("vitest")
        package["scripts"]["test:unit"] = "bun test tests/unit"
        package["scripts"]["test:int"] = "bun test tests/integration"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "typescript")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["detected"], ["bun-test"])
        self.assertTrue(framework["waiver_required"])

    def test_vitest_dependency_without_vitest_runners_is_not_canonical(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] = "echo unit"
        package["scripts"]["test:int"] = "echo integration"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "typescript")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["unit_int_parser"], "generic")
        self.assertTrue(framework["waiver_required"])

    def test_bun_script_command_make_reverse_edge_is_rejected(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += " && command make auxiliary"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(result["bun"]["make_cycles"], ["test:unit"])
        self.assertIn("bun_make_cycle", {item["code"] for item in result["findings"]})

    def test_bun_script_env_make_reverse_edge_is_rejected(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += " && env MODE=test make auxiliary"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(result["bun"]["make_cycles"], ["test:unit"])

    def test_bun_script_absolute_make_reverse_edge_is_rejected(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += " && /usr/bin/make auxiliary"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(result["bun"]["make_cycles"], ["test:unit"])

    def test_bun_script_wrapped_make_reverse_edge_is_rejected(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += " && time make test-unit"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(result["bun"]["make_cycles"], ["test:unit"])

    def test_bun_script_quoted_make_reverse_edge_is_rejected(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += " && sh -c 'make test-unit'"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(result["bun"]["make_cycles"], ["test:unit"])

    def test_bun_script_make_alias_reverse_edge_is_rejected(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += (
            " && MAKE_CMD=make sh -c '$MAKE_CMD test-unit'"
        )
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(result["bun"]["make_cycles"], ["test:unit"])

    def test_vitest_runner_that_swallows_failure_is_not_canonical(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += " || true"
        package["scripts"]["test:int"] += " || true"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "typescript")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["unit_int_parser"], "generic")
        self.assertTrue(framework["waiver_required"])

    def test_python_pipeline_runner_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit | tee unit.log"
        )
        content = content.replace(
            "test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int | tee int.log"
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "generic")

    def test_unresolved_python_make_variable_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = "PYTHON := echo\n" + makefile.read_text(encoding="utf-8")
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\t$(PYTHON) -m pytest unit"
        )
        content = content.replace(
            "test-int:\n\t@true", "test-int:\n\t$(PYTHON) -m pytest int"
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "generic")

    def test_override_python_make_variable_is_resolved(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = "PYTHON := python3\noverride PYTHON := echo\n" + makefile.read_text(
            encoding="utf-8"
        )
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\t$(PYTHON) -m pytest unit"
        ).replace("test-int:\n\t@true", "test-int:\n\t$(PYTHON) -m pytest int")
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "generic")

    def test_sensitive_python_file_is_not_read_for_framework_detection(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = "PYTHON := python3\n" + makefile.read_text(encoding="utf-8")
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\t$(PYTHON) -m pytest unit"
        )
        content = content.replace(
            "test-int:\n\t@true", "test-int:\n\t$(PYTHON) -m pytest int"
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.write(".env.test.py", "import unittest\ncredential = 'must-not-read'\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "conforming")
        self.assertEqual(self.framework(result, "python")["detected"], ["pytest"])

    def test_plural_sensitive_python_file_is_not_read(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = "PYTHON := python3\n" + makefile.read_text(encoding="utf-8")
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\t$(PYTHON) -m pytest unit"
        ).replace("test-int:\n\t@true", "test-int:\n\t$(PYTHON) -m pytest int")
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.write("credentials.py", "import unittest\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "conforming")
        self.assertEqual(self.framework(result, "python")["detected"], ["pytest"])

    def test_pytest_information_only_command_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest --help")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest --help")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "generic")

    def test_pytest_collection_alias_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest --co")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest --co")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "generic")

    def test_pytest_fixtures_command_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest --fixtures"
        ).replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest --fixtures")
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "generic")

    def test_pytest_addopts_collect_only_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = "export PYTEST_ADDOPTS := --collect-only\n" + makefile.read_text(
            encoding="utf-8"
        ).replace(
            "test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest tests"
        ).replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest tests")
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")

    def test_pytest_ini_collect_only_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest tests")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest tests")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.write("pytest.ini", "[pytest]\naddopts = --collect-only\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")

    def test_background_pytest_command_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit &")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int &")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "generic")

    def test_make_runner_with_error_ignore_prefix_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        content = makefile.read_text(encoding="utf-8")
        content = content.replace("test-unit:\n\t@true", "test-unit:\n\t-pytest unit")
        content = content.replace(
            "test-int:\n\t@true", "test-int:\n\t-pytest integration"
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "python")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["unit_int_parser"], "generic")

    def test_rust_without_cargo_test_runner_is_not_canonical(self) -> None:
        self.write_make_contract()
        self.write("Cargo.toml", '[package]\nname = "fixture"\nversion = "0.1.0"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "rust")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["unit_int_parser"], "generic")
        self.assertTrue(framework["waiver_required"])

    def test_rust_with_cargo_test_runners_is_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        content = makefile.read_text(encoding="utf-8")
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\tcargo test --lib"
        )
        content = content.replace(
            "test-int:\n\t@true", "test-int:\n\tcargo test --test integration"
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("Cargo.toml", '[package]\nname = "fixture"\nversion = "0.1.0"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "rust")

        self.assertEqual(result["structural_status"], "conforming")
        self.assertEqual(framework["unit_int_parser"], "cargo-test")
        self.assertFalse(framework["waiver_required"])

    def test_rust_runner_variable_must_resolve_to_cargo(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = "CARGO := echo\n" + makefile.read_text(encoding="utf-8")
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\t$(CARGO) test --lib"
        ).replace("test-int:\n\t@true", "test-int:\n\t$(CARGO) test --test integration")
        makefile.write_text(content, encoding="utf-8")
        self.write("Cargo.toml", '[package]\nname = "fixture"\nversion = "0.1.0"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(self.framework(result, "rust")["unit_int_parser"], "generic")

    def test_bun_adapter_variable_must_resolve_to_bun(self) -> None:
        self.write_bun_package()
        self.write_bun_adapter()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            "BUN := echo\n"
            + makefile.read_text(encoding="utf-8").replace("bun run", "$(BUN) run"),
            encoding="utf-8",
        )
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(result["make"]["aggregate_mode"], "invalid_bun_adapter")

    def test_legacy_bun_lock_requires_waiver_even_with_bun_lock(self) -> None:
        self.write_bun_package()
        self.write_bun_adapter()
        self.write("bun.lockb", "legacy")
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertIn(
            "bun_legacy_lock_waiver_required",
            {item["code"] for item in result["findings"]},
        )

    def test_dart_and_flutter_pending_gaori_parsers_are_explicit(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        content = makefile.read_text(encoding="utf-8")
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\tdart test test/unit"
        )
        content = content.replace(
            "test-int:\n\t@true", "test-int:\n\tdart test test/integration"
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("pubspec.yaml", "dev_dependencies:\n  test: ^1.25.0\n")
        self.enroll("make")

        dart_result = inspect_testing.inspect_repository(self.repository)
        dart = self.framework(dart_result, "dart")

        self.assertEqual(dart["status"], "canonical")
        self.assertEqual(dart["unit_int_parser"], "generic")
        self.assertEqual(dart["parser_support"], "pending-dart-test")

        self.write(
            "pubspec.yaml",
            """\
            dependencies:
              flutter:
                sdk: flutter
            dev_dependencies:
              flutter_test:
                sdk: flutter
              patrol: ^4.0.0
            """,
        )
        content = makefile.read_text(encoding="utf-8").replace(
            "dart test", "flutter test"
        )
        makefile.write_text(content, encoding="utf-8")

        flutter_result = inspect_testing.inspect_repository(self.repository)
        flutter = self.framework(flutter_result, "flutter")

        self.assertEqual(flutter["status"], "canonical")
        self.assertEqual(flutter["unit_int_parser"], "flutter-test")
        self.assertEqual(flutter["e2e_parser"], "generic")
        self.assertEqual(flutter["e2e_parser_support"], "pending-patrol")

    def test_dart_dependency_without_runner_is_not_canonical(self) -> None:
        self.write_make_contract()
        self.write("pubspec.yaml", "dev_dependencies:\n  test: ^1.25.0\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "dart")

        self.assertEqual(result["structural_status"], "unverifiable")
        self.assertEqual(framework["status"], "waiver_required")

    def test_included_targets_are_unverifiable_not_assumed_missing(self) -> None:
        self.write("Makefile", "include tests.mk\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        target_finding = next(
            item
            for item in result["findings"]
            if item["code"] == "make_targets_missing"
        )

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertEqual(target_finding["severity"], "unverifiable")

    def test_missing_testing_document_does_not_enroll_repository(self) -> None:
        self.write_make_contract()

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(result["structural_status"], "nonconforming")
        self.assertFalse(result["testing_document"]["contract_registered"])
        self.assertIn(
            "testing_document_missing", {item["code"] for item in result["findings"]}
        )

    def test_cli_returns_structured_error_for_missing_repository(self) -> None:
        missing = self.repository / "missing"

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--repository", str(missing)],
            check=False,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(
            payload["schema_version"], "aquarium-test-setup-inspection-error.v1"
        )
        self.assertEqual(payload["error"]["code"], "repository_not_found")


if __name__ == "__main__":
    unittest.main()
