from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "plugins/aquarium/skills/dev-setup-bundle/scripts/normalize_manifest.py"
)


class NormalizeManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.repository_a = self.create_repository("repository-a")
        self.repository_b = self.create_repository("repository-b")
        (self.repository_a / "nested").mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_repository(self, name: str) -> Path:
        repository = self.base / name
        subprocess.run(
            ["git", "init", "--quiet", str(repository)],
            check=True,
            capture_output=True,
            text=True,
        )
        return repository

    def write_manifest(self, name: str, body: str) -> Path:
        path = self.base / name
        path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
        return path

    def run_script(
        self, manifest: Path | None = None, *, environment: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        arguments = [sys.executable, str(SCRIPT)]
        if manifest is not None:
            arguments.extend(["--manifest", str(manifest)])
        return subprocess.run(
            arguments,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def load_normalizer(self) -> types.ModuleType:
        spec = importlib.util.spec_from_file_location("normalize_manifest", SCRIPT)
        if spec is None or spec.loader is None:
            self.fail("could not load normalize_manifest.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def assert_error(
        self, result: subprocess.CompletedProcess[str], code: str
    ) -> dict[str, object]:
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        payload = json.loads(result.stderr)
        self.assertEqual(
            payload["schema_version"], "aquarium-dev-setup-bundle-error.v1"
        )
        self.assertEqual(payload["error"]["code"], code)
        return payload

    def test_normalizes_ready_and_invalid_targets(self) -> None:
        manifest = self.write_manifest(
            "bundle.yaml",
            f"""
            schema: aquarium.dev-setup-bundle/v1
            defaults:
              tools: [mulgae, gaori, podway, ouroboros, lora, deslop]
              project_mcp: [mulgae, gaori]
              agents_guidance: skip
            targets:
              - path: repository-a
                include: [sanho]
                exclude: [ouroboros]
                project_mcp_exclude: [gaori]
                agents_guidance: propose
              - path: {self.repository_b}
              - path: missing-repository
            """,
        )

        result = self.run_script(manifest)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        plan = json.loads(result.stdout)
        self.assertEqual(
            plan["schema_version"], "aquarium-dev-setup-bundle-plan.v1"
        )
        self.assertEqual(plan["manifest"]["path"], str(manifest.resolve()))
        self.assertEqual(
            plan["manifest"]["sha256"],
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            [target["status"] for target in plan["targets"]],
            ["ready", "ready", "invalid"],
        )
        first = plan["targets"][0]
        self.assertEqual(first["repository"], str(self.repository_a.resolve()))
        self.assertIn("sanho", first["tools"])
        self.assertNotIn("ouroboros", first["tools"])
        self.assertEqual(first["project_mcp"], ["mulgae"])
        self.assertEqual(first["agents_guidance"], "propose")
        self.assertEqual(
            plan["targets"][2]["reason_codes"], ["target_not_found"]
        )
        self.assertEqual(
            plan["shared_tools"],
            ["sanho", "mulgae", "gaori", "podway", "ouroboros", "lora", "deslop"],
        )

    def test_manifest_change_changes_digest(self) -> None:
        manifest = self.write_manifest(
            "digest.yaml",
            """
            schema: aquarium.dev-setup-bundle/v1
            defaults:
              tools: [mulgae]
              project_mcp: []
              agents_guidance: skip
            targets:
              - path: repository-a
            """,
        )
        first = json.loads(self.run_script(manifest).stdout)
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace("skip", "propose"),
            encoding="utf-8",
        )
        second = json.loads(self.run_script(manifest).stdout)
        self.assertNotEqual(first["manifest"]["sha256"], second["manifest"]["sha256"])

    def test_duplicate_git_roots_are_all_invalid(self) -> None:
        manifest = self.write_manifest(
            "duplicate-root.yaml",
            """
            schema: aquarium.dev-setup-bundle/v1
            defaults:
              tools: [mulgae]
              project_mcp: []
              agents_guidance: skip
            targets:
              - path: repository-a
              - path: repository-a/nested
            """,
        )
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["shared_tools"], [])
        self.assertTrue(
            all(
                target["status"] == "invalid"
                and target["reason_codes"] == ["duplicate_git_root"]
                for target in plan["targets"]
            )
        )

    def test_linked_worktrees_are_duplicate_git_roots(self) -> None:
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repository_a),
                "-c",
                "user.name=Aquarium Test",
                "-c",
                "user.email=aquarium@example.invalid",
                "commit",
                "--quiet",
                "--allow-empty",
                "-m",
                "initial",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        linked_worktree = self.base / "repository-a-linked"
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repository_a),
                "worktree",
                "add",
                "--quiet",
                "--detach",
                str(linked_worktree),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        manifest = self.write_manifest(
            "linked-worktrees.yaml",
            """
            schema: aquarium.dev-setup-bundle/v1
            defaults:
              tools: [mulgae]
              project_mcp: []
              agents_guidance: skip
            targets:
              - path: repository-a
              - path: repository-a-linked
            """,
        )

        result = self.run_script(manifest)

        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertTrue(
            all(
                target["status"] == "invalid"
                and target["reason_codes"] == ["duplicate_git_root"]
                for target in plan["targets"]
            )
        )

    def test_ignores_repository_scoping_git_environment(self) -> None:
        plain_directory = self.base / "plain-directory"
        plain_directory.mkdir()
        manifest = self.write_manifest(
            "ambient-git.yaml",
            """
            schema: aquarium.dev-setup-bundle/v1
            defaults:
              tools: [mulgae]
              project_mcp: []
              agents_guidance: skip
            targets:
              - path: plain-directory
              - path: repository-a/nested
            """,
        )
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_CEILING_DIRECTORIES": str(self.repository_a),
                "GIT_COMMON_DIR": str(self.repository_b / ".git"),
                "GIT_DIR": str(self.repository_b / ".git"),
                "GIT_WORK_TREE": "/",
            }
        )

        result = self.run_script(manifest, environment=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(
            [target["status"] for target in plan["targets"]],
            ["invalid", "ready"],
        )
        self.assertEqual(
            plan["targets"][0]["reason_codes"], ["target_not_git_repository"]
        )
        self.assertEqual(
            plan["targets"][1]["repository"], str(self.repository_a.resolve())
        )

    def test_selection_errors_do_not_probe_targets(self) -> None:
        git_call_log = self.base / "git-calls.log"
        shim_directory = self.base / "shim"
        shim_directory.mkdir()
        git_shim = shim_directory / "git"
        git_shim.write_text(
            '#!/bin/sh\nprintf called >> "$GIT_CALL_LOG"\nexit 1\n',
            encoding="utf-8",
        )
        git_shim.chmod(0o755)
        manifest = self.write_manifest(
            "late-selection-error.yaml",
            """
            schema: aquarium.dev-setup-bundle/v1
            defaults:
              tools: [mulgae]
              project_mcp: []
              agents_guidance: skip
            targets:
              - path: repository-a
              - path: repository-b
                include: [gaori]
                exclude: [gaori]
            """,
        )
        environment = os.environ.copy()
        environment["GIT_CALL_LOG"] = str(git_call_log)
        environment["PATH"] = f"{shim_directory}{os.pathsep}{environment['PATH']}"

        result = self.run_script(manifest, environment=environment)

        self.assert_error(result, "conflicting_override")
        self.assertFalse(git_call_log.exists())

    def test_rejects_unsafe_or_ambiguous_yaml(self) -> None:
        cases = {
            "alias": (
                """
                schema: aquarium.dev-setup-bundle/v1
                defaults: &defaults
                  tools: [mulgae]
                  project_mcp: []
                  agents_guidance: skip
                targets: *defaults
                """,
                "invalid_yaml",
            ),
            "duplicate-key": (
                """
                schema: aquarium.dev-setup-bundle/v1
                defaults:
                  tools: [mulgae]
                  tools: [gaori]
                  project_mcp: []
                  agents_guidance: skip
                targets:
                  - path: repository-a
                """,
                "invalid_yaml",
            ),
            "merge-key": (
                """
                schema: aquarium.dev-setup-bundle/v1
                defaults:
                  <<: {tools: [mulgae]}
                  project_mcp: []
                  agents_guidance: skip
                targets:
                  - path: repository-a
                """,
                "invalid_yaml",
            ),
            "unknown-key": (
                """
                schema: aquarium.dev-setup-bundle/v1
                defaults:
                  tools: [mulgae]
                  project_mcp: []
                  agents_guidance: skip
                targets:
                  - path: repository-a
                unexpected: true
                """,
                "unknown_key",
            ),
            "conflicting-override": (
                """
                schema: aquarium.dev-setup-bundle/v1
                defaults:
                  tools: [mulgae]
                  project_mcp: []
                  agents_guidance: skip
                targets:
                  - path: repository-a
                    include: [gaori]
                    exclude: [gaori]
                """,
                "conflicting_override",
            ),
            "unsupported-mcp": (
                """
                schema: aquarium.dev-setup-bundle/v1
                defaults:
                  tools: [mulgae]
                  project_mcp: [gaori]
                  agents_guidance: skip
                targets:
                  - path: repository-a
                """,
                "invalid_mcp_selection",
            ),
        }
        for name, (body, expected_code) in cases.items():
            with self.subTest(name=name):
                manifest = self.write_manifest(f"{name}.yaml", body)
                self.assert_error(self.run_script(manifest), expected_code)

    def test_rejects_missing_pyyaml_with_json_error(self) -> None:
        blocker = self.base / "missing-pyyaml"
        blocker.mkdir()
        (blocker / "yaml.py").write_text(
            'raise ModuleNotFoundError("No module named yaml", name="yaml")\n',
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(blocker)
        result = self.run_script(self.base / "unused.yaml", environment=environment)
        self.assert_error(result, "runtime_dependency_missing")

    def test_rejects_unsupported_pyyaml_with_json_error(self) -> None:
        blocker = self.base / "unsupported-pyyaml"
        blocker.mkdir()
        (blocker / "yaml.py").write_text('__version__ = "7.0.0"\n', encoding="utf-8")
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(blocker)
        result = self.run_script(self.base / "unused.yaml", environment=environment)
        payload = self.assert_error(result, "runtime_dependency_unsupported")
        self.assertIn("7.0.0", payload["error"]["message"])

    def test_rejects_unsupported_python(self) -> None:
        normalizer = self.load_normalizer()
        with (
            mock.patch.object(normalizer.sys, "version_info", (3, 9, 6)),
            self.assertRaises(normalizer.ManifestError) as raised,
        ):
            normalizer.require_python()
        self.assertEqual(raised.exception.code, "runtime_dependency_unsupported")
        self.assertIn("3.9.6", str(raised.exception))

    def test_argument_errors_are_json_only(self) -> None:
        self.assert_error(self.run_script(), "invalid_arguments")


if __name__ == "__main__":
    unittest.main()
