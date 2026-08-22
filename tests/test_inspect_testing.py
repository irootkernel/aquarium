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

            Contract: aquarium-test-contract/v1
            Profile: {profile}
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
        self.write_make_contract()
        self.write_bun_package()
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
        self.write_make_contract()
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

    def test_python_pytest_and_rust_use_supported_parsers(self) -> None:
        self.write_make_contract()
        self.write(
            "pyproject.toml", '[project.optional-dependencies]\ntest = ["pytest>=8"]\n'
        )
        self.write("Cargo.toml", '[package]\nname = "fixture"\nversion = "0.1.0"\n')
        self.enroll("polyglot-make")

        result = inspect_testing.inspect_repository(self.repository)

        self.assertEqual(self.framework(result, "python")["unit_int_parser"], "pytest")
        self.assertEqual(
            self.framework(result, "rust")["unit_int_parser"], "cargo-test"
        )
        self.assertEqual(
            result["frameworks"]["gaori"]["stage_parser_defaults"]["test-int"],
            "generic",
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

    def test_dart_and_flutter_pending_gaori_parsers_are_explicit(self) -> None:
        self.write_make_contract()
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

        flutter_result = inspect_testing.inspect_repository(self.repository)
        flutter = self.framework(flutter_result, "flutter")

        self.assertEqual(flutter["status"], "canonical")
        self.assertEqual(flutter["unit_int_parser"], "flutter-test")
        self.assertEqual(flutter["e2e_parser"], "generic")
        self.assertEqual(flutter["e2e_parser_support"], "pending-patrol")

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
