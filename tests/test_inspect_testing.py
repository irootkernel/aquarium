from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/aquarium/skills/test-setup/scripts/inspect_testing.py"

sys.path.insert(0, str(SCRIPT.parent))

import inspect_testing


@contextmanager
def case(**labels: object):
    try:
        yield
    except AssertionError as error:
        raise AssertionError(f"case {labels}: {error}") from error


class TestInspectTesting:
    @pytest.fixture(autouse=True)
    def repository_fixture(self, tmp_path: Path) -> None:
        self.repository = tmp_path / "repository"
        self.repository.mkdir()

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
                "test:e2e": "bun run vitest run tests/e2e",
            },
        }
        self.write("package.json", json.dumps(package))
        self.write("bun.lock", 'vitest = "4.0.0"\n')

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

        assert result["selected_profile"] == "make"
        assert result["structural_status"] == "conforming"
        assert result["make"]["aggregate_mode"] == "recursive_recipe"
        assert result["make"]["aggregate_recursive_calls"] == list(
            inspect_testing.MAKE_STAGES
        )

    def test_symlinked_root_makefile_is_not_read(self) -> None:
        external = self.repository.parent / "credentials.make"
        external.write_text("credential-marker: secret\n", encoding="utf-8")
        (self.repository / "Makefile").symlink_to(external)
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert not result["make"]["present"]
        assert "credential-marker" not in json.dumps(result)

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

        assert result["structural_status"] == "nonconforming"
        assert result["make"]["aggregate_mode"] == "prerequisites"
        assert "make_aggregate_parallel_unsafe" in {
            item["code"] for item in result["findings"]
        }

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

        assert result["structural_status"] == "unverifiable"
        assert result["make"]["aggregate_mode"] == "unverifiable"
        assert result["make"]["aggregate_recursive_calls"] == []

    def test_error_ignoring_recursive_make_calls_are_not_fail_fast(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        makefile.write_text(
            makefile.read_text(encoding="utf-8").replace("\t$(MAKE)", "\t-$(MAKE)"),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert result["make"]["aggregate_mode"] == "unverifiable"
        assert result["make"]["aggregate_recursive_calls"] == []

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

        assert result["structural_status"] == "unverifiable"
        assert result["make"]["aggregate_mode"] == "unverifiable"

    def test_oneshell_make_aggregate_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository.joinpath("Makefile")
        makefile.write_text(
            ".ONESHELL:\n" + makefile.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert result["make"]["global_shell_semantics"]
        assert "make_authority_unverifiable" in {
            item["code"] for item in result["findings"]
        }

    def test_custom_make_shell_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            "SHELL := /bin/true\n" + makefile.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert result["make"]["global_shell_semantics"]

    def test_makeflags_error_ignoring_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            "MAKEFLAGS += -i\n" + makefile.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert result["make"]["global_shell_semantics"]

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

        assert result["structural_status"] == "unverifiable"
        assert result["make"]["authority_includes_unresolved"]

    def test_conforming_typescript_bun_profile_and_make_adapter(self) -> None:
        self.write_bun_package()
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["typescript"]
        assert result["selected_profile"] == "typescript-bun"
        assert result["structural_status"] == "conforming"
        assert result["bun"]["aggregate_serial"]
        assert result["make"]["aggregate_mode"] == "bun_adapter"
        assert self.framework(result, "typescript")["status"] == "canonical"
        assert (
            result["frameworks"]["gaori"]["stage_parser_defaults"]["test-unit"]
            == "vitest"
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

        assert result["structural_status"] == "nonconforming"
        assert "bun_aggregate_invalid" in codes
        assert "bun_make_cycle" in codes
        assert "bun_version_unpinned" in codes

    def test_polyglot_root_keeps_make_authority(self) -> None:
        self.write_ginkgo_make_contract()
        self.write_bun_package()
        self.write_ginkgo_evidence()
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["go", "typescript"]
        assert result["selected_profile"] == "polyglot-make"
        assert result["structural_status"] == "conforming"
        assert result["make"]["aggregate_mode"] == "recursive_recipe"
        assert (
            result["frameworks"]["gaori"]["stage_parser_defaults"]["test-unit"]
            == "generic"
        )

    def test_go_ginkgo_and_gomega_are_canonical(self) -> None:
        self.write_ginkgo_make_contract()
        self.write_ginkgo_evidence()
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "go")

        assert result["structural_status"] == "conforming"
        assert framework["status"] == "canonical"
        assert framework["unit_int_parser"] == "ginkgo"

    def test_ginkgo_information_commands_are_not_canonical(self) -> None:
        for subcommand in (
            "--dry-run ./...",
            "--dry-run=true ./...",
            "--dryRun ./...",
            "build ./...",
            "help",
            "labels",
            "outline",
            "version",
        ):
            with case(subcommand=subcommand):
                self.write_ginkgo_make_contract()
                makefile = self.repository / "Makefile"
                makefile.write_text(
                    makefile.read_text(encoding="utf-8").replace(
                        "ginkgo -race ./...", f"ginkgo {subcommand}"
                    ),
                    encoding="utf-8",
                )
                self.write_ginkgo_evidence()
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "unverifiable"

    def test_ginkgo_explicit_false_dry_run_executes_tests(self) -> None:
        self.write_ginkgo_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8").replace(
                "ginkgo -race ./...", "ginkgo --dry-run=false -race ./..."
            ),
            encoding="utf-8",
        )
        self.write_ginkgo_evidence()
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "conforming"
        assert self.framework(result, "go")["status"] == "canonical"

    def test_go_standard_testing_requires_legacy_waiver_review(self) -> None:
        self.write_make_contract()
        self.write("go.mod", "module example.com/fixture\n\ngo 1.26\n")
        self.write("thing_test.go", 'package fixture\n\nimport "testing"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "go")

        assert result["structural_status"] == "unverifiable"
        assert framework["waiver_required"]
        assert "framework_waiver_required" in {
            item["code"] for item in result["findings"]
        }

    def test_stale_go_dependencies_do_not_select_ginkgo_parser(self) -> None:
        self.write_make_contract()
        self.write_ginkgo_evidence()
        self.repository.joinpath("go.sum").unlink()
        self.write("fixture_test.go", 'package fixture\n\nimport "testing"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "go")

        assert result["structural_status"] == "unverifiable"
        assert framework["unit_int_parser"] == "generic"
        assert framework["waiver_required"]

    def test_dependency_only_python_does_not_select_pytest_parser(self) -> None:
        self.write_make_contract()
        self.write(
            "pyproject.toml", '[project.optional-dependencies]\ntest = ["pytest>=8"]\n'
        )
        self.write("Cargo.toml", '[package]\nname = "fixture"\nversion = "0.1.0"\n')
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        assert self.framework(result, "python")["unit_int_parser"] == "generic"
        assert self.framework(result, "rust")["unit_int_parser"] == "generic"
        assert (
            result["frameworks"]["gaori"]["stage_parser_defaults"]["test-int"]
            == "generic"
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

        assert result["structural_status"] == "unverifiable"
        assert framework["detected"] == ["pytest", "unittest"]
        assert framework["waiver_required"]
        assert parsers["test-unit"] == "pytest"
        assert parsers["test-int"] == "generic"

    @pytest.mark.parametrize(
        "runner",
        [
            "python3 -m nose",
            "python3 -m nose2",
            "python3 -m nosetests",
            ".venv/bin/nose2",
        ],
    )
    def test_pytest_and_legacy_nose_mixture_requires_waiver(self, runner: str) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace(
                "test-unit:\n\t@true",
                f"test-unit:\n\tpython3 -m pytest tests/unit\n\t{runner} tests.legacy",
            )
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest tests/int"),
            encoding="utf-8",
        )
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "python")

        assert result["structural_status"] == "unverifiable"
        assert framework["detected"] == ["pytest", "legacy-python-runner"]
        assert framework["unit_int_parser"] == "generic"

    def test_pytest_requirement_with_extras_is_valid_authority(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int"),
            encoding="utf-8",
        )
        self.write("requirements.txt", "pytest[testing]==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "conforming"
        assert self.framework(result, "python")["status"] == "canonical"

    def test_pytest_plugin_pin_is_not_malformed_core_authority(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int"),
            encoding="utf-8",
        )
        self.write("requirements.txt", "pytest==9.1.1\npytest-cov==7.0.0\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "conforming"

    def test_pytest_configuration_is_not_dependency_authority(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int"),
            encoding="utf-8",
        )
        self.write(
            "pyproject.toml",
            "[project]\nname = 'pytest'\n[tool.pytest.ini_options]\naddopts = '-ra'\n",
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["status"] == "waiver_required"

    def test_python_unittest_e2e_requires_waiver(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int")
            .replace(
                "test-e2e:\n\t@true",
                "test-e2e:\n\tpython3 -m unittest discover tests/e2e",
            ),
            encoding="utf-8",
        )
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["status"] == "waiver_required"

    def test_empty_bun_lock_is_not_dependency_evidence(self) -> None:
        self.write_bun_package()
        self.write("bun.lock", "")
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert "bun_lock_missing" in {item["code"] for item in result["findings"]}

    @pytest.mark.parametrize("e2e_path", ["tests/e2e", "e2e"])
    def test_typescript_profile_allows_python_pytest_e2e_handler(
        self, e2e_path: str
    ) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = f"python3 -m pytest {e2e_path}"
        self.write("package.json", json.dumps(package))
        self.write(f"{e2e_path}/test_cli.py", "def test_cli():\n    assert True\n")
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["typescript"]
        assert result["selected_profile"] == "typescript-bun"
        assert result["structural_status"] == "conforming"

    def test_pytest_option_value_is_not_a_typescript_owned_e2e_root(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "python3 -m pytest --rootdir src e2e"
        self.write("package.json", json.dumps(package))
        self.write("e2e/test_cli.py", "def test_cli():\n    assert True\n")
        self.write("src/service.py", "def run():\n    return True\n")
        self.write_bun_adapter()
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["python", "typescript"]
        assert result["selected_profile"] == "polyglot-make"

    def test_pytest_node_selector_is_a_typescript_owned_e2e_source(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "python3 -m pytest e2e/test_cli.py::test_cli"
        self.write("package.json", json.dumps(package))
        self.write("e2e/test_cli.py", "def test_cli():\n    assert True\n")
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["typescript"]
        assert result["selected_profile"] == "typescript-bun"

    def test_pytest_ignore_value_is_not_a_typescript_owned_e2e_root(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "python3 -m pytest --ignore src e2e"
        self.write("package.json", json.dumps(package))
        self.write("e2e/test_cli.py", "def test_cli():\n    assert True\n")
        self.write("src/service.py", "def run():\n    return True\n")
        self.write_bun_adapter()
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["python", "typescript"]
        assert result["selected_profile"] == "polyglot-make"

    def test_unknown_pytest_option_fails_closed_for_e2e_ownership(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "python3 -m pytest --plugin-path e2e"
        self.write("package.json", json.dumps(package))
        self.write("e2e/test_cli.py", "def test_cli():\n    assert True\n")
        self.write_bun_adapter()
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["python", "typescript"]
        assert result["selected_profile"] == "polyglot-make"

    def test_unknown_equals_pytest_option_fails_closed_for_e2e_ownership(
        self,
    ) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "python3 -m pytest --plugin-path=e2e e2e"
        self.write("package.json", json.dumps(package))
        self.write("e2e/test_cli.py", "def test_cli():\n    assert True\n")
        self.write_bun_adapter()
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["python", "typescript"]

    def test_pytest_option_terminator_preserves_e2e_roots(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "python3 -m pytest -- e2e src"
        self.write("package.json", json.dumps(package))
        self.write("e2e/test_cli.py", "def test_cli():\n    assert True\n")
        self.write("src/test_service.py", "def test_service():\n    assert True\n")
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["typescript"]

    def test_pytest_assert_value_is_not_an_e2e_root(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "python3 -m pytest --assert plain e2e"
        self.write("package.json", json.dumps(package))
        self.write("e2e/test_cli.py", "def test_cli():\n    assert True\n")
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["typescript"]

    def test_node_modules_python_is_not_product_source(self) -> None:
        self.write_bun_package()
        self.write(
            "node_modules/example/tool.py", "def dependency():\n    return True\n"
        )
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["typescript"]

    def test_tox_python_is_not_product_or_framework_source(self) -> None:
        self.write_bun_package()
        self.write(
            ".tox/lib/python3.13/site-packages/example/test_helpers.py",
            "import unittest\n",
        )
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["typescript"]
        assert result["frameworks"]["entries"] == [
            entry
            for entry in result["frameworks"]["entries"]
            if entry["language"] == "typescript"
        ]

    def test_typescript_profile_requires_waiver_for_python_unittest_e2e(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "python3 -m unittest discover tests/e2e"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "typescript")["status"] == "waiver_required"

    def test_typescript_and_manifestless_python_unit_layers_are_polyglot(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        for name in ("test:unit", "test:int"):
            package["scripts"][name] += " && python3 -m unittest tests.legacy"
        package["scripts"]["test:e2e"] = "python3 -m pytest tests/e2e"
        self.write("package.json", json.dumps(package))
        self.write("src/service.py", "def run():\n    return True\n")
        self.write_bun_adapter()
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["python", "typescript"]
        assert result["selected_profile"] == "polyglot-make"
        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["status"] == "waiver_required"
        assert self.framework(result, "typescript")["status"] == "waiver_required"

    @pytest.mark.parametrize(
        ("name", "content"),
        [
            ("requirements.txt", "# pytest\n"),
            ("setup.py", "# pytest\nfrom setuptools import setup\nsetup()\n"),
            ("setup.py", "from setuptools import setup\nsetup(name='pytest')\n"),
            (
                "setup.py",
                "from setuptools import setup\nsetup(extras_require={'pytest': ['requests==2.0.0']})\n",
            ),
            ("setup.cfg", "[metadata]\nname = pytest\n"),
        ],
    )
    def test_pytest_comments_are_not_dependency_authority(
        self, name: str, content: str
    ) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int"),
            encoding="utf-8",
        )
        self.write(name, content)
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["status"] == "waiver_required"

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

        assert result["detected_languages"] == ["python"]
        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["detected"] == ["pytest", "unittest"]

    def test_manifestless_python_runner_and_source_require_framework_review(
        self,
    ) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace(
                "test-unit:\n\t@true",
                "test-unit:\n\tpython3 -m unittest tests.test_unit",
            )
            .replace(
                "test-int:\n\t@true",
                "test-int:\n\tpython3 -m unittest tests.test_integration",
            )
            .replace(
                "test-e2e:\n\t@true",
                "test-e2e:\n\tpython3 -m unittest tests.test_e2e",
            ),
            encoding="utf-8",
        )
        self.write("tests/test_unit.py", "import unittest\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["detected_languages"] == ["python"]
        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["status"] == "waiver_required"

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

        assert result["structural_status"] == "unverifiable"
        assert framework["detected"] == ["pytest", "unittest"]
        assert framework["unit_int_parser"] == "generic"

    def test_invalid_root_package_manifest_is_nonconforming(self) -> None:
        for content in ("{", '{"value":1e309}', '{"name":"a","name":"b"}'):
            with case(content=content):
                self.write_make_contract()
                self.write("package.json", content)
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "nonconforming"
                assert "package_json_invalid" in {
                    item["code"] for item in result["findings"]
                }

    def test_invalid_pyproject_cannot_prove_pytest(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int"),
            encoding="utf-8",
        )
        self.write("pyproject.toml", '[project\nname = "pytest-fixture"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert "pyproject_invalid" in {item["code"] for item in result["findings"]}

    def test_invalid_python_config_cannot_prove_pytest(self) -> None:
        for name, config in (
            ("pytest.ini", "[pytest\naddopts = -ra\n"),
            ("requirements.txt", "pytest==\n"),
            ("setup.cfg", "[tool:pytest\naddopts = -ra\n"),
            ("setup.py", "pytest setup(\n"),
        ):
            with case(name=name):
                self.write_make_contract()
                makefile = self.repository / "Makefile"
                makefile.write_text(
                    makefile.read_text(encoding="utf-8")
                    .replace(
                        "test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit"
                    )
                    .replace(
                        "test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int"
                    ),
                    encoding="utf-8",
                )
                if name != "requirements.txt":
                    self.write("requirements.txt", "pytest==9.1.1\n")
                self.write(name, config)
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "nonconforming"
                assert "python_config_invalid" in {
                    item["code"] for item in result["findings"]
                }

    def test_testing_document_profile_must_match_executable_authority(self) -> None:
        self.write_make_contract()
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert "testing_profile_mismatch" in {
            item["code"] for item in result["findings"]
        }

    def test_testing_document_requires_every_contract_section(self) -> None:
        self.write_make_contract()
        self.write("TESTING.md", "Contract: aquarium-test-contract/v1\n")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert "testing_sections_missing" in {
            item["code"] for item in result["findings"]
        }

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

        assert result["structural_status"] == "nonconforming"
        assert not result["testing_document"]["sections"]["Canonical Commands"]
        assert "testing_sections_missing" in {
            item["code"] for item in result["findings"]
        }

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

        assert result["structural_status"] == "nonconforming"
        assert not result["testing_document"]["contract_registered"]
        assert "testing_contract_unregistered" in {
            item["code"] for item in result["findings"]
        }

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

        assert result["structural_status"] == "unverifiable"
        assert framework["detected"] == ["bun-test"]
        assert framework["waiver_required"]

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

        assert result["structural_status"] == "unverifiable"
        assert framework["unit_int_parser"] == "generic"
        assert framework["waiver_required"]

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

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]
        assert "bun_make_cycle" in {item["code"] for item in result["findings"]}

    def test_bun_script_command_substitution_is_fail_closed(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:e2e"] = "$(printf make) test-e2e"
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:e2e"]

    def test_bun_script_opaque_shell_expansions_are_fail_closed(self) -> None:
        commands = (
            "`printf make` test-e2e",
            '"$MAKE" test-e2e',
            '"$RUNNER" test-e2e',
            "${RUNNER-make} test-e2e",
            "${RUNNER:=make} test-e2e",
            "${RUNNER%foo} test-e2e",
            "${RUNNER#prefix} test-e2e",
            'set -- m a k e; IFS=; "$*" test-e2e',
            'set -- make; "$@" test-e2e',
            'RUNNER=make; "$0" test-e2e',
        )
        for command in commands:
            with case(command=command):
                self.write_bun_package()
                package = json.loads(
                    self.repository.joinpath("package.json").read_text(encoding="utf-8")
                )
                package["scripts"]["test:e2e"] = command
                self.write("package.json", json.dumps(package))
                self.write_bun_adapter()
                self.enroll("typescript-bun")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "nonconforming"
                assert result["bun"]["make_cycles"] == ["test:e2e"]

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

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]

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

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]

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

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]

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

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]

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

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]

    def test_bun_script_quote_joined_make_alias_is_rejected(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += (
            " && MAKE_CMD=m'ak'e sh -c '$MAKE_CMD test-unit'"
        )
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]

    def test_bun_script_empty_quote_joined_make_is_rejected(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += ' && ma""ke auxiliary'
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]

    def test_bun_script_semicolon_alias_and_backslash_make_are_rejected(self) -> None:
        for command in ("M=make; sh -c '$M test-unit'", r"m\ake test-unit"):
            with case(command=command):
                self.write_bun_package()
                package = json.loads(
                    self.repository.joinpath("package.json").read_text(encoding="utf-8")
                )
                package["scripts"]["test:unit"] += f" && {command}"
                self.write("package.json", json.dumps(package))
                self.write_bun_adapter()
                self.enroll("typescript-bun")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "nonconforming"
                assert result["bun"]["make_cycles"] == ["test:unit"]

    def test_bun_script_extended_make_assignments_are_rejected(self) -> None:
        for command in (
            "M=make>/dev/null && $M test-unit",
            r"M=make\  && $M test-unit",
            "M=${TOOL:-make} && $M test-unit",
        ):
            with case(command=command):
                self.write_bun_package()
                package = json.loads(
                    self.repository.joinpath("package.json").read_text(encoding="utf-8")
                )
                package["scripts"]["test:unit"] += f" && {command}"
                self.write("package.json", json.dumps(package))
                self.write_bun_adapter()
                self.enroll("typescript-bun")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "nonconforming"
                assert result["bun"]["make_cycles"] == ["test:unit"]

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

        assert result["structural_status"] == "unverifiable"
        assert framework["unit_int_parser"] == "generic"
        assert framework["waiver_required"]

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

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

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

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

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

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

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

        assert result["structural_status"] == "conforming"
        assert self.framework(result, "python")["detected"] == ["pytest"]

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

        assert result["structural_status"] == "conforming"
        assert self.framework(result, "python")["detected"] == ["pytest"]

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

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

    def test_pytest_funcargs_alias_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace(
                "test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest --funcargs"
            )
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest --funcargs")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

    def test_inspection_output_redacts_make_recipes_and_bun_commands(self) -> None:
        secret = "AQUARIUM_QA_SYNTHETIC_PROOF"
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += f" --token={secret}"
        package["packageManager"] = secret
        package["engines"] = {"bun": secret}
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace(".PHONY:", f"include config.mk?token={secret}\n\n.PHONY:")
            .replace(
                "test-e2e:\n\tbun run test:e2e",
                f"test-e2e: prerequisite-{secret}\n\tAPI_TOKEN={secret} bun run test:e2e",
            ),
            encoding="utf-8",
        )
        self.enroll("typescript-bun")

        serialized = json.dumps(inspect_testing.inspect_repository(self.repository))

        assert secret not in serialized
        assert "recipe" not in serialized.replace("recipe_command_count", "")

    def test_symlinked_pytest_configuration_is_rejected(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest int")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        external = self.repository.parent / "external-pytest.ini"
        external.write_text("[pytest]\naddopts = --funcargs\n", encoding="utf-8")
        self.repository.joinpath("pytest.ini").symlink_to(external)
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert "root_authority_symlinked" in {
            item["code"] for item in result["findings"]
        }

    def test_pytest_prefixed_module_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest-fake unit")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest.fake int")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

    def test_opaque_pytest_shell_expansion_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            "PYTEST_ADDOPTS := $(shell printf --collect-only)\n"
            + makefile.read_text(encoding="utf-8")
        )
        content = content.replace(
            "test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest unit"
        ).replace(
            "test-int:\n\t@true",
            "test-int:\n\tpython3 -m pytest $$(printf --collect$${EMPTY}-only)",
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

    def test_pytest_collection_alias_is_not_canonical(self) -> None:
        for option in ("--co", "--collectonly", "-V"):
            with case(option=option):
                self.write_make_contract()
                makefile = self.repository / "Makefile"
                content = (
                    makefile.read_text(encoding="utf-8")
                    .replace(
                        "test-unit:\n\t@true",
                        f"test-unit:\n\tpython3 -m pytest {option}",
                    )
                    .replace(
                        "test-int:\n\t@true",
                        f"test-int:\n\tpython3 -m pytest {option}",
                    )
                )
                makefile.write_text(content, encoding="utf-8")
                self.write("requirements.txt", "pytest==9.1.1\n")
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "unverifiable"
                assert self.framework(result, "python")["unit_int_parser"] == "generic"

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

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

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

        assert result["structural_status"] == "unverifiable"

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

        assert result["structural_status"] == "unverifiable"

    def test_quoted_pyproject_collect_only_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest tests")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest tests")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.write(
            "pyproject.toml",
            '[tool.pytest.ini_options]\naddopts = "--collect-only"\n',
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"

    def test_multiline_pyproject_collect_only_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest tests")
            .replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest tests")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.write(
            "pyproject.toml",
            '[tool.pytest.ini_options]\naddopts = [\n  "--collect-only",\n]\n',
        )
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"

    def test_quote_joined_pytest_control_option_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace(
                "test-unit:\n\t@true",
                'test-unit:\n\tpython3 -m pytest --collect"-only"',
            )
            .replace(
                "test-int:\n\t@true", 'test-int:\n\tpython3 -m pytest --collect"-only"'
            )
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"

    def test_quote_joined_static_pytest_controls_are_not_canonical(self) -> None:
        for authority, content in (
            ("Makefile", 'export PYTEST_ADDOPTS := --collect""-only\n'),
            (
                "pyproject.toml",
                '[tool.pytest.ini_options]\naddopts = "--collect\\"\\"-only"\n',
            ),
        ):
            with case(authority=authority):
                self.write_make_contract()
                makefile = self.repository / "Makefile"
                make_content = (
                    makefile.read_text(encoding="utf-8")
                    .replace(
                        "test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest tests"
                    )
                    .replace(
                        "test-int:\n\t@true", "test-int:\n\tpython3 -m pytest tests"
                    )
                )
                if authority == "Makefile":
                    make_content = content + make_content
                else:
                    self.write(authority, content)
                makefile.write_text(make_content, encoding="utf-8")
                self.write("requirements.txt", "pytest==9.1.1\n")
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "unverifiable"

    def test_additive_pytest_addopts_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = "PYTEST_ADDOPTS += --collect-only\n" + makefile.read_text(
            encoding="utf-8"
        ).replace(
            "test-unit:\n\t@true", "test-unit:\n\tpython3 -m pytest tests"
        ).replace("test-int:\n\t@true", "test-int:\n\tpython3 -m pytest tests")
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"

    def test_pytest_cache_and_setup_only_commands_are_not_canonical(self) -> None:
        for option in ("--cache-show", "--setup-plan", "--setup-only"):
            with case(option=option):
                self.write_make_contract()
                makefile = self.repository / "Makefile"
                content = (
                    makefile.read_text(encoding="utf-8")
                    .replace(
                        "test-unit:\n\t@true",
                        f"test-unit:\n\tpython3 -m pytest {option}",
                    )
                    .replace(
                        "test-int:\n\t@true", f"test-int:\n\tpython3 -m pytest {option}"
                    )
                )
                makefile.write_text(content, encoding="utf-8")
                self.write("requirements.txt", "pytest==9.1.1\n")
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "unverifiable"

    def test_pytest_control_option_before_shell_operator_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace(
                "test-unit:\n\t@true",
                "test-unit:\n\tpython3 -m pytest --collect-only&& true",
            )
            .replace(
                "test-int:\n\t@true", "test-int:\n\tpython3 -m pytest --collect-only"
            )
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"

    def test_pytest_redirection_is_not_execution_proof(self) -> None:
        for command in (
            "python3 -m pytest tests >/dev/null",
            "python3 -m pytest --collect-only>/dev/null",
        ):
            with case(command=command):
                self.write_make_contract()
                makefile = self.repository / "Makefile"
                content = (
                    makefile.read_text(encoding="utf-8")
                    .replace("test-unit:\n\t@true", f"test-unit:\n\t{command}")
                    .replace("test-int:\n\t@true", f"test-int:\n\t{command}")
                )
                makefile.write_text(content, encoding="utf-8")
                self.write("requirements.txt", "pytest==9.1.1\n")
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "unverifiable"

    def test_pytest_parameter_default_is_not_execution_proof(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        command = "python3 -m pytest ${OPTS:---collect-only} tests"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", f"test-unit:\n\t{command}")
            .replace("test-int:\n\t@true", f"test-int:\n\t{command}")
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"

    def test_bun_parameter_default_script_is_fail_closed(self) -> None:
        self.write_bun_package()
        package = json.loads(
            self.repository.joinpath("package.json").read_text(encoding="utf-8")
        )
        package["scripts"]["test:unit"] += (
            " && MAKE_CMD=m${X:-a}ke sh -c '$MAKE_CMD test-unit'"
        )
        self.write("package.json", json.dumps(package))
        self.write_bun_adapter()
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert result["bun"]["make_cycles"] == ["test:unit"]

    def test_make_recipe_continuation_is_unverifiable(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = makefile.read_text(encoding="utf-8").replace(
            "test-unit:\n\t@true",
            "test-unit:\n\tpython3 -m pytest --collect-\\\n\t  only",
        )
        makefile.write_text(content, encoding="utf-8")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert result["make"]["global_shell_semantics"]

    def test_dynamic_make_authorities_are_unverifiable(self) -> None:
        additions = (
            ".RECIPEPREFIX := >\n",
            "test-%: BUN = true\n",
            "$(eval test-unit: ; @true)\n",
            "DYNAMIC := $(eval test-unit: ; @true)\n",
            "ifeq ($(MODE),fast)\ntest-unit: ; @true\nendif\n",
            "define MAKEFLAGS\n-i\nendef\n",
            "MAKE := true\n",
            "export PYTEST_ADDOPTS\n",
            "undefine MAKE\n",
            "test-unit:\n\t$(eval DYNAMIC := true)\n",
            "PYTHON ?= python3\n",
            "CARGO ?= cargo\n",
            "BUN ?= bun\n",
        )
        for addition in additions:
            with case(addition=addition):
                self.write_make_contract()
                makefile = self.repository / "Makefile"
                makefile.write_text(
                    addition + makefile.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "unverifiable"
                assert result["make"]["global_shell_semantics"]

    def test_symlinked_legacy_lock_authority_is_rejected(self) -> None:
        self.write_bun_package()
        self.write_bun_adapter()
        self.write("bun.lock", "lockfileVersion = 1\n")
        external = self.repository.parent / "external-pnpm-lock.yaml"
        external.write_text("lockfileVersion: 9\n", encoding="utf-8")
        self.repository.joinpath("pnpm-lock.yaml").symlink_to(external)
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert "root_authority_symlinked" in {
            item["code"] for item in result["findings"]
        }

    def test_ansi_quoted_pytest_option_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        content = (
            makefile.read_text(encoding="utf-8")
            .replace(
                "test-unit:\n\t@true",
                "test-unit:\n\tpython3 -m pytest $'--collect\\x2donly'",
            )
            .replace(
                "test-int:\n\t@true",
                'test-int:\n\tpython3 -m pytest $"--collect-only"',
            )
        )
        makefile.write_text(content, encoding="utf-8")
        self.write("requirements.txt", "pytest==9.1.1\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

    def test_unresolved_pytest_addopts_expansion_is_not_canonical(self) -> None:
        for value in ("--collect$()-only", "--collect$(UNDEFINED)-only"):
            with case(value=value):
                self.write_make_contract()
                makefile = self.repository / "Makefile"
                makefile.write_text(
                    f"export PYTEST_ADDOPTS := {value}\n"
                    + makefile.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                self.write("requirements.txt", "pytest==9.1.1\n")
                self.enroll("make")

                result = inspect_testing.inspect_repository(self.repository)

                assert result["structural_status"] == "unverifiable"

    def test_symlinked_requirements_authority_is_reported(self) -> None:
        self.write_make_contract()
        external = self.repository.parent / "requirements.txt"
        external.write_text("pytest==9.1.1\n", encoding="utf-8")
        self.repository.joinpath("requirements.txt").symlink_to(external)
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert "root_authority_symlinked" in {
            item["code"] for item in result["findings"]
        }

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

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "python")["unit_int_parser"] == "generic"

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

        assert result["structural_status"] == "unverifiable"
        assert framework["unit_int_parser"] == "generic"

    def test_rust_without_cargo_test_runner_is_not_canonical(self) -> None:
        self.write_make_contract()
        self.write("Cargo.toml", '[package]\nname = "fixture"\nversion = "0.1.0"\n')
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "rust")

        assert result["structural_status"] == "unverifiable"
        assert framework["unit_int_parser"] == "generic"
        assert framework["waiver_required"]

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

        assert result["structural_status"] == "conforming"
        assert framework["unit_int_parser"] == "cargo-test"
        assert not framework["waiver_required"]

    def test_cargo_no_run_is_not_canonical(self) -> None:
        self.write_make_contract()
        makefile = self.repository / "Makefile"
        makefile.write_text(
            makefile.read_text(encoding="utf-8")
            .replace("test-unit:\n\t@true", "test-unit:\n\tcargo test --no-run")
            .replace("test-int:\n\t@true", "test-int:\n\tcargo test --no-run"),
            encoding="utf-8",
        )
        self.write("Cargo.toml", '[package]\nname = "fixture"\nversion = "0.1.0"\n')
        self.write("Cargo.lock", "# fixture\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"

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

        assert result["structural_status"] == "unverifiable"
        assert self.framework(result, "rust")["unit_int_parser"] == "generic"

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

        assert result["structural_status"] == "nonconforming"
        assert result["make"]["aggregate_mode"] == "invalid_bun_adapter"

    def test_legacy_bun_lock_requires_waiver_even_with_bun_lock(self) -> None:
        self.write_bun_package()
        self.write_bun_adapter()
        self.write("bun.lockb", "legacy")
        self.enroll("typescript-bun")

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "unverifiable"
        assert "bun_legacy_lock_waiver_required" in {
            item["code"] for item in result["findings"]
        }

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

        assert dart["status"] == "canonical"
        assert dart["unit_int_parser"] == "generic"
        assert dart["parser_support"] == "pending-dart-test"

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

        assert flutter["status"] == "canonical"
        assert flutter["unit_int_parser"] == "flutter-test"
        assert flutter["e2e_parser"] == "generic"
        assert flutter["e2e_parser_support"] == "pending-patrol"

    def test_dart_dependency_without_runner_is_not_canonical(self) -> None:
        self.write_make_contract()
        self.write("pubspec.yaml", "dev_dependencies:\n  test: ^1.25.0\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        framework = self.framework(result, "dart")

        assert result["structural_status"] == "unverifiable"
        assert framework["status"] == "waiver_required"

    def test_included_targets_are_unverifiable_not_assumed_missing(self) -> None:
        self.write("Makefile", "include tests.mk\n")
        self.enroll("make")

        result = inspect_testing.inspect_repository(self.repository)
        target_finding = next(
            item
            for item in result["findings"]
            if item["code"] == "make_targets_missing"
        )

        assert result["structural_status"] == "nonconforming"
        assert target_finding["severity"] == "unverifiable"

    def test_missing_testing_document_does_not_enroll_repository(self) -> None:
        self.write_make_contract()

        result = inspect_testing.inspect_repository(self.repository)

        assert result["structural_status"] == "nonconforming"
        assert not result["testing_document"]["contract_registered"]
        assert "testing_document_missing" in {
            item["code"] for item in result["findings"]
        }

    def test_cli_returns_structured_error_for_missing_repository(self) -> None:
        missing = self.repository.resolve() / "missing"

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--repository", str(missing)],
            check=False,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)

        assert completed.returncode == 2
        assert payload["schema_version"] == "aquarium-test-setup-inspection-error.v1"
        assert payload["error"]["code"] == "repository_not_found"

    def test_cli_does_not_reflect_unknown_argument_values(self) -> None:
        secret = "QA20_SYNTHETIC_SECRET"

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--repository", ".", f"--api-token={secret}"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 2
        assert secret not in completed.stdout
