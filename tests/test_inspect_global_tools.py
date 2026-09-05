from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_SCRIPT = (
    ROOT / "plugins/aquarium/skills/dev-setup-global/scripts/inspect_global_tools.py"
)
PROJECT_SCRIPT = ROOT / "plugins/aquarium/skills/dev-setup/scripts/inspect_tools.py"

sys.path.insert(0, str(GLOBAL_SCRIPT.parent))

import inspect_global_tools


class TestInspectGlobalTools:
    def setup_method(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.repository = self.base / "repository"
        self.home = self.base / "home"
        self.codex_home = self.base / "codex"
        self.bin_directory = self.base / "bin"
        for path in (self.repository, self.home, self.codex_home, self.bin_directory):
            path.mkdir()
        self.environment = os.environ.copy()
        self.environment.update(
            {
                "HOME": str(self.home),
                "CODEX_HOME": str(self.codex_home),
                "PATH": f"{self.bin_directory}:/usr/bin:/bin",
            }
        )
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=self.repository,
            env=self.environment,
            check=True,
        )

    def teardown_method(self) -> None:
        self.temporary_directory.cleanup()

    def run_inspector(
        self, script: Path, *, include_repository: bool = True
    ) -> dict[str, object]:
        arguments = [
            sys.executable,
            str(script),
            "--timeout-seconds",
            "1",
        ]
        if include_repository:
            arguments.extend(("--repository", str(self.repository)))
        completed = subprocess.run(
            arguments,
            cwd=self.repository,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout)

    def test_global_inventory_has_only_user_global_scope(self) -> None:
        payload = self.run_inspector(GLOBAL_SCRIPT)

        assert payload["schema_version"] == "aquarium-dev-setup-global-inspection.v1"
        assert payload["inspection_scope"] == "user_global"
        assert "repository" not in payload
        for name in ("sanho", "mulgae", "gaori", "sorage", "podway"):
            assert "status" in payload["tools"][name]["cli"]
        assert payload["tools"]["sorage"]["cli"]["status"] == "missing"
        assert "status" in payload["tools"]["dolgorae"]
        assert "installation_prerequisites" in payload["tools"]["mulgae"]
        for name in ("lora", "deslop", "humanizer", "im-not-ai", "ouroboros"):
            assert "status" in payload["tools"][name]
            assert "cli" not in payload["tools"][name]
        assert set(payload["tools"]) == {
            "sanho",
            "dolgorae",
            "mulgae",
            "gaori",
            "sorage",
            "podway",
            "lora",
            "deslop",
            "humanizer",
            "im-not-ai",
            "ouroboros",
        }
        assert list(payload["tools"]) == list(inspect_global_tools.GLOBAL_COMPONENTS)

    def test_missing_podway_daemon_preserves_documented_shape(self) -> None:
        payload = self.run_inspector(GLOBAL_SCRIPT)
        daemon = payload["tools"]["podway"]["daemon"]

        assert daemon == {
            "installed": False,
            "loaded": False,
            "reachable": False,
            "running": False,
            "version": None,
            "target": None,
            "ready": False,
            "mode": None,
            "readiness_state": None,
            "readiness_stage": None,
            "readiness_elapsed_ms": None,
            "worktree_recovery": None,
            "status": "missing",
            "versions_match": False,
            "probe": {
                "attempted": False,
                "ok": False,
                "exit_code": None,
                "timed_out": False,
                "reason": "executable_missing",
            },
        }

    def test_global_paired_skill_uses_only_agents_canonical_root(self) -> None:
        codex_skill = self.codex_home / "skills/use-sorage"
        codex_skill.mkdir(parents=True)
        codex_skill.joinpath("SKILL.md").write_text(
            "---\nname: use-sorage\ndescription: test\n---\n", encoding="utf-8"
        )

        payload = self.run_inspector(GLOBAL_SCRIPT)
        paired_skill = payload["tools"]["sorage"]["paired_skill"]
        assert paired_skill["status"] == "degraded"
        assert paired_skill["canonical_present"] is False

        agents_skill = self.home / ".agents/skills/use-sorage"
        agents_skill.mkdir(parents=True)
        agents_skill.joinpath("SKILL.md").write_text(
            "---\nname: use-sorage\ndescription: test\n---\n", encoding="utf-8"
        )

        payload = self.run_inspector(GLOBAL_SCRIPT)
        paired_skill = payload["tools"]["sorage"]["paired_skill"]
        assert paired_skill["status"] == "degraded"
        assert paired_skill["canonical_present"] is True

        codex_skill.joinpath("SKILL.md").unlink()
        codex_skill.rmdir()
        payload = self.run_inspector(GLOBAL_SCRIPT)
        paired_skill = payload["tools"]["sorage"]["paired_skill"]
        assert paired_skill["status"] == "configured"
        assert paired_skill["installations"][0]["path"] == str(agents_skill)

    def test_global_ouroboros_probe_uses_neutral_working_directory(self) -> None:
        inspector = mock.MagicMock()
        inspector.SANHO_SKILL_FILES = ()
        inspector.MULGAE_SKILL_FILES = ()
        inspector.GAORI_SKILL_FILES = ()
        inspector.SORAGE_SKILL_FILES = ()
        inspector.inspect_dolgorae.return_value = {
            "status": "missing",
            "installed": False,
            "executable": None,
            "probes": {},
        }
        inspector.inspect_agent_skill.return_value = {"status": "missing"}
        inspector.inspect_mulgae_installation_prerequisites.return_value = {}
        for component in (
            inspector.inspect_lora,
            inspector.inspect_deslop,
            inspector.inspect_humanizer,
            inspector.inspect_im_not_ai,
            inspector.inspect_ouroboros,
        ):
            component.return_value = {"status": "missing"}
        cli = {
            "status": "missing",
            "installed": False,
            "executable": None,
            "probes": {},
        }
        sorage = {**cli, "probes": {"doctor": {"attempted": False}}}
        podway = {**cli, "daemon": {"status": "missing"}}

        with (
            mock.patch.object(
                inspect_global_tools, "load_inspector", return_value=inspector
            ),
            mock.patch.object(
                inspect_global_tools,
                "inspect_versioned_cli",
                return_value=cli,
            ) as inspect_versioned,
            mock.patch.object(
                inspect_global_tools,
                "inspect_global_sorage",
                return_value=sorage,
            ),
            mock.patch.object(
                inspect_global_tools,
                "inspect_global_podway",
                return_value=podway,
            ),
            mock.patch.object(
                inspect_global_tools,
                "inspect_global_mcp",
                return_value={"status": "unavailable"},
            ),
        ):
            inspect_global_tools.inspect_global(str(self.repository), 3.5, True)

        inspector.inspect_ouroboros.assert_called_once_with(
            Path(self.repository.anchor), 3.5
        )
        inspector.inspect_dolgorae.assert_called_once_with(
            Path(self.repository.anchor),
            3.5,
            verify_official_release=True,
        )
        assert len(inspect_versioned.mock_calls) == 3
        assert all(
            call.args[2] == Path(self.repository.anchor)
            for call in inspect_versioned.mock_calls
        )
        inspector.inspect_mulgae_installation_prerequisites.assert_called_once_with(
            Path(self.repository.anchor),
            3.5,
            environment_overrides={"GOTOOLCHAIN": "local"},
        )

    def test_dolgorae_scope_skips_unselected_component_probes(self) -> None:
        inspector = mock.MagicMock()
        inspector.SANHO_SKILL_FILES = ()
        inspector.MULGAE_SKILL_FILES = ()
        inspector.GAORI_SKILL_FILES = ()
        inspector.SORAGE_SKILL_FILES = ()
        inspector.inspect_dolgorae.return_value = {
            "status": "configured",
            "installed": True,
            "executable": "/usr/local/bin/dolgorae",
            "probes": {},
        }

        with (
            mock.patch.object(
                inspect_global_tools, "load_inspector", return_value=inspector
            ),
            mock.patch.object(
                inspect_global_tools, "inspect_versioned_cli"
            ) as inspect_versioned,
            mock.patch.object(
                inspect_global_tools, "inspect_global_sorage"
            ) as inspect_sorage,
            mock.patch.object(
                inspect_global_tools, "inspect_global_podway"
            ) as inspect_podway,
            mock.patch.object(
                inspect_global_tools, "inspect_global_mcp"
            ) as inspect_mcp,
        ):
            payload = inspect_global_tools.inspect_global(
                str(self.repository),
                3.5,
                True,
                components=("dolgorae",),
            )

        assert list(payload["tools"]) == ["dolgorae"]
        inspector.inspect_dolgorae.assert_called_once_with(
            Path(self.repository.anchor),
            3.5,
            verify_official_release=True,
        )
        inspect_versioned.assert_not_called()
        inspect_sorage.assert_not_called()
        inspect_podway.assert_not_called()
        inspect_mcp.assert_not_called()
        inspector.inspect_agent_skill.assert_not_called()
        inspector.inspect_mulgae_installation_prerequisites.assert_not_called()
        inspector.inspect_ouroboros.assert_not_called()

    def test_global_podway_wait_ready_uses_native_timeout_with_headroom(self) -> None:
        inspector = mock.MagicMock()
        inspector.PODWAY_SKILL_FILES = ()
        inspector.PODWAY_DAEMON_WAIT_SECONDS = 120.0
        inspector.PODWAY_DAEMON_CALLER_TIMEOUT_SECONDS = 125.0
        inspector.inspect_agent_skill.return_value = {"status": "configured"}
        inspector.json_probe.return_value = {"ok": True}
        inspector.normalize_podway_daemon_probe.return_value = (
            {"ok": True},
            {
                "installed": True,
                "loaded": True,
                "reachable": True,
                "running": True,
                "version": "v0.2.8",
                "target": "aarch64-apple-darwin",
                "ready": True,
                "mode": "prod",
                "readiness_state": "ready",
                "readiness_stage": "ready",
                "readiness_elapsed_ms": 1,
                "worktree_recovery": {"total": 1, "completed": 1, "failed": 0},
            },
        )
        inspector.normalized_version.side_effect = lambda version: version.removeprefix(
            "v"
        )
        tool = {
            "status": "installed",
            "installed": True,
            "executable": "/usr/local/bin/podway",
            "version": "v0.2.8",
            "probes": {},
        }

        with mock.patch.object(
            inspect_global_tools, "inspect_versioned_cli", return_value=tool
        ):
            result = inspect_global_tools.inspect_global_podway(
                inspector, self.repository, 3.5
            )

        inspector.json_probe.assert_called_once_with(
            [
                "/usr/local/bin/podway",
                "--json",
                "daemon",
                "wait-ready",
                "--timeout",
                "120s",
            ],
            Path(self.repository.anchor),
            125.0,
        )
        assert result["daemon"]["status"] == "configured"
        assert result["daemon"]["versions_match"] is True

    @pytest.mark.parametrize(
        ("override", "normalized", "expected_field"),
        (
            (
                {"mode": "dev"},
                {"ok": False, "error_code": "unsupported_daemon_mode"},
                ("mode", "dev"),
            ),
            ({"ready": False}, {"ok": True}, ("ready", False)),
            ({"version": "v0.2.9"}, {"ok": True}, ("versions_match", False)),
            (
                {"target": "x86_64-apple-darwin"},
                {"ok": True},
                ("target", "x86_64-apple-darwin"),
            ),
            (
                {
                    "ready": False,
                    "worktree_recovery": {"total": 2, "completed": 1, "failed": 0},
                },
                {"ok": True},
                (
                    "worktree_recovery",
                    {"total": 2, "completed": 1, "failed": 0},
                ),
            ),
        ),
    )
    def test_global_podway_rejects_unhealthy_daemon_state(
        self,
        override: dict[str, object],
        normalized: dict[str, object],
        expected_field: tuple[str, object],
    ) -> None:
        inspector = mock.MagicMock()
        inspector.PODWAY_SKILL_FILES = ()
        inspector.PODWAY_DAEMON_WAIT_SECONDS = 120.0
        inspector.PODWAY_DAEMON_CALLER_TIMEOUT_SECONDS = 125.0
        inspector.inspect_agent_skill.return_value = {"status": "configured"}
        inspector.json_probe.return_value = {"ok": True}
        daemon = {
            "installed": True,
            "loaded": True,
            "reachable": True,
            "running": True,
            "version": "v0.2.8",
            "target": "aarch64-apple-darwin",
            "ready": True,
            "mode": "prod",
            "readiness_state": "ready",
            "readiness_stage": "ready",
            "readiness_elapsed_ms": 1,
            "worktree_recovery": {"total": 1, "completed": 1, "failed": 0},
        }
        daemon.update(override)
        inspector.normalize_podway_daemon_probe.return_value = (normalized, daemon)
        inspector.normalized_version.side_effect = lambda version: version.removeprefix(
            "v"
        )
        tool = {
            "status": "installed",
            "installed": True,
            "executable": "/usr/local/bin/podway",
            "version": "v0.2.8",
            "probes": {},
        }

        with mock.patch.object(
            inspect_global_tools, "inspect_versioned_cli", return_value=tool
        ):
            result = inspect_global_tools.inspect_global_podway(
                inspector, self.repository, 3.5
            )

        assert result["daemon"]["status"] == "degraded"
        assert result["daemon"][expected_field[0]] == expected_field[1]

    def test_non_sorage_version_probe_does_not_require_a_matching_name(self) -> None:
        inspector = mock.MagicMock()
        inspector.base_tool.return_value = {
            "status": "missing",
            "installed": True,
            "executable": "/usr/local/bin/example",
            "probes": {},
        }
        inspector.json_probe.return_value = {
            "ok": True,
            "result": {"name": "unexpected", "version": "v1.2.3"},
        }
        inspector.normalized_probe.side_effect = lambda probe: probe
        inspector.version_from_probe.return_value = "v1.2.3"

        tool = inspect_global_tools.inspect_versioned_cli(
            inspector,
            "example",
            self.repository,
            1.0,
            ["version", "--json"],
            lambda version: version == "v1.2.3",
        )

        assert tool["version"] == "v1.2.3"
        assert tool["status"] == "installed"
        inspector.json_probe.assert_called_once_with(
            ["/usr/local/bin/example", "version", "--json"],
            Path(self.repository.anchor),
            1.0,
        )

    def test_cli_component_preserves_dolgorae_capabilities_probe(self) -> None:
        capabilities = {"attempted": True, "ok": True, "exit_code": 0}

        component = inspect_global_tools.cli_component(
            {
                "status": "configured",
                "probes": {"capabilities": capabilities},
            }
        )

        assert component["capabilities_probe"] == capabilities

    def test_global_mcp_probe_uses_neutral_working_directory(self) -> None:
        inspector = mock.MagicMock()
        inspector.shutil.which.return_value = "/usr/local/bin/codex"
        inspector.mcp_registration_probe.return_value = ({}, {"ok": False})
        inspector.classify_gaori_mcp_scope.return_value = {"status": "unavailable"}

        inspect_global_tools.inspect_global_mcp(
            inspector, "gaori", "/usr/local/bin/gaori", self.repository, 2.0
        )

        inspector.mcp_registration_probe.assert_called_once_with(
            "/usr/local/bin/codex", "gaori", Path(self.repository.anchor), 2.0
        )

    @pytest.mark.parametrize(
        ("initialized", "blocking_count", "expected", "degraded"),
        (
            (False, 0, "not_initialized", False),
            (True, 0, "initialized", False),
            (None, 0, "unverifiable", True),
            (True, 1, "unverifiable", True),
        ),
    )
    def test_sorage_initialization_outcomes(
        self,
        initialized: bool | None,
        blocking_count: int,
        expected: str,
        degraded: bool,
    ) -> None:
        inspector = mock.MagicMock()
        inspector.json_probe.return_value = {"ok": True}
        inspector.normalize_sorage_doctor.return_value = (
            {"ok": True},
            initialized,
            blocking_count,
        )
        tool = {
            "status": "installed",
            "installed": True,
            "executable": "/usr/local/bin/sorage",
            "probes": {"version": {"contract_valid": True}},
        }

        with mock.patch.object(
            inspect_global_tools, "inspect_versioned_cli", return_value=tool
        ):
            result = inspect_global_tools.inspect_global_sorage(
                inspector, self.repository, 1.0, True
            )

        assert result["initialization_status"] == expected
        assert (result["status"] == "degraded") is degraded
        inspector.json_probe.assert_called_once_with(
            ["/usr/local/bin/sorage", "doctor", "--json"],
            Path(self.repository.anchor),
            1.0,
        )

    @pytest.mark.parametrize("timeout", ("0", "-1", "nan", "inf", "86401"))
    def test_invalid_timeouts_return_json_error(self, timeout: str) -> None:
        completed = subprocess.run(
            [sys.executable, str(GLOBAL_SCRIPT), "--timeout-seconds", timeout],
            cwd=self.repository,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 2
        assert json.loads(completed.stdout)["error"]["code"] == "invalid_arguments"

    @pytest.mark.parametrize("kind", ("missing", "file"))
    def test_invalid_working_directories_return_json_error(self, kind: str) -> None:
        requested = self.base / kind
        if kind == "file":
            requested.write_text("not a directory\n", encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(GLOBAL_SCRIPT), "--repository", str(requested)],
            cwd=self.repository,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 2
        assert (
            json.loads(completed.stdout)["error"]["code"] == "invalid_working_directory"
        )

    def test_missing_project_inspector_has_specific_error(self) -> None:
        with (
            mock.patch.object(
                inspect_global_tools, "PROJECT_INSPECTOR", self.base / "missing.py"
            ),
            pytest.raises(inspect_global_tools.InspectionError) as caught,
        ):
            inspect_global_tools.load_inspector()

        assert caught.value.code == "inspector_unavailable"

    def test_failed_project_inspector_import_is_not_cached(self) -> None:
        broken = self.base / "broken_inspector.py"
        broken.write_text("raise RuntimeError('broken')\n", encoding="utf-8")
        module_name = "aquarium_project_tool_inspector"
        with (
            mock.patch.object(inspect_global_tools, "PROJECT_INSPECTOR", broken),
            pytest.raises(RuntimeError, match="broken"),
        ):
            inspect_global_tools.load_inspector()

        assert module_name not in sys.modules

    def test_project_inventory_excludes_global_components_and_trusts_presence(
        self,
    ) -> None:
        deslop = self.home / ".agents/skills/deslop"
        deslop.mkdir(parents=True)
        (deslop / "unexpected.txt").write_text("not upstream\n", encoding="utf-8")

        payload = self.run_inspector(PROJECT_SCRIPT)

        assert payload["schema_version"] == "aquarium-dev-setup-inspection.v16"
        assert "deslop" not in payload["tools"]
        assert "ouroboros" not in payload["tools"]
        assert payload["trusted_global_skills"]["deslop"] == {
            "canonical_path": str(deslop),
            "present": True,
            "verification_scope": "presence_only",
        }

        global_payload = self.run_inspector(GLOBAL_SCRIPT)
        assert global_payload["tools"]["deslop"]["status"] == "degraded"
        assert not global_payload["tools"]["deslop"]["installed"]

    def test_global_lora_and_deslop_reject_alternate_root_only(self) -> None:
        for name in ("lore-commits", "lore-query", "deslop"):
            skill = self.codex_home / "skills" / name
            skill.mkdir(parents=True)
            skill.joinpath("SKILL.md").write_text(
                f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8"
            )
        (self.codex_home / "skills/deslop/LICENSE").write_text(
            "test\n", encoding="utf-8"
        )

        payload = self.run_inspector(GLOBAL_SCRIPT)

        assert payload["tools"]["lora"]["status"] == "degraded"
        assert payload["tools"]["lora"]["installed"] is False
        assert payload["tools"]["deslop"]["status"] == "degraded"
        assert payload["tools"]["deslop"]["installed"] is False

    def test_global_lora_and_deslop_accept_agents_canonical_root(self) -> None:
        for name in ("lore-commits", "lore-query", "deslop"):
            skill = self.home / ".agents/skills" / name
            skill.mkdir(parents=True)
            skill.joinpath("SKILL.md").write_text(
                f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8"
            )
        (self.home / ".agents/skills/deslop/LICENSE").write_text(
            "test\n", encoding="utf-8"
        )

        payload = self.run_inspector(GLOBAL_SCRIPT)

        assert payload["tools"]["lora"]["status"] == "unverifiable"
        assert payload["tools"]["lora"]["installed"] is True
        assert payload["tools"]["deslop"]["status"] == "unverifiable"
        assert payload["tools"]["deslop"]["installed"] is True

    def test_project_inspector_starts_without_global_verifier_module(self) -> None:
        isolated_script = self.base / "isolated/dev-setup/scripts/inspect_tools.py"
        isolated_script.parent.mkdir(parents=True)
        isolated_script.write_bytes(PROJECT_SCRIPT.read_bytes())

        payload = self.run_inspector(isolated_script)

        assert payload["schema_version"] == "aquarium-dev-setup-inspection.v16"
        assert "error" not in payload

    def test_global_inventory_runs_outside_a_git_worktree_without_repository(
        self,
    ) -> None:
        working_directory = self.base / "not-a-repository"
        working_directory.mkdir()
        completed = subprocess.run(
            [
                sys.executable,
                str(GLOBAL_SCRIPT),
                "--timeout-seconds",
                "1",
            ],
            cwd=working_directory,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 0, completed.stderr
        assert json.loads(completed.stdout)["inspection_scope"] == "user_global"

    def test_invalid_sorage_version_contract_never_runs_doctor(self) -> None:
        doctor_marker = self.base / "doctor-ran"
        sorage = self.bin_directory / "sorage"
        sorage.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "version" ]; then\n'
            "  printf '%s\\n' '{\"version\":\"v0.1.5\"}'\n"
            "  exit 0\n"
            "fi\n"
            f"touch {doctor_marker}\n"
            "exit 0\n",
            encoding="utf-8",
        )
        sorage.chmod(0o755)

        completed = subprocess.run(
            [
                sys.executable,
                str(GLOBAL_SCRIPT),
                "--repository",
                str(self.repository),
                "--include-sorage-initialization",
                "--timeout-seconds",
                "1",
            ],
            cwd=self.repository,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)["tools"]["sorage"]
        assert payload["cli"]["status"] == "degraded"
        assert payload["cli"]["version"] is None
        assert payload["cli"]["version_supported"] is False
        assert not payload["cli"]["version_probe"]["contract_valid"]
        assert payload["initialization_probe"]["reason"] == "unsupported_runtime"
        assert not doctor_marker.exists()

    def test_cli_routes_optional_sorage_initialization_diagnosis(self) -> None:
        output = io.StringIO()
        result = {"schema_version": inspect_global_tools.SCHEMA_VERSION}
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    "inspect_global_tools.py",
                    "--repository",
                    str(self.repository),
                    "--include-sorage-initialization",
                ],
            ),
            mock.patch.object(
                inspect_global_tools, "inspect_global", return_value=result
            ) as inspect,
            mock.patch.object(sys, "stdout", output),
        ):
            exit_code = inspect_global_tools.main()

        assert exit_code == 0
        inspect.assert_called_once_with(
            str(self.repository),
            10.0,
            False,
            True,
            inspect_global_tools.GLOBAL_COMPONENTS,
        )
        assert json.loads(output.getvalue()) == result

    def test_cli_normalizes_repeated_component_scope_in_catalog_order(self) -> None:
        output = io.StringIO()
        result = {"schema_version": inspect_global_tools.SCHEMA_VERSION}
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    "inspect_global_tools.py",
                    "--repository",
                    str(self.repository),
                    "--component",
                    "podway",
                    "--component",
                    "dolgorae",
                    "--component",
                    "podway",
                    "--verify-dolgorae-release",
                ],
            ),
            mock.patch.object(
                inspect_global_tools, "inspect_global", return_value=result
            ) as inspect,
            mock.patch.object(sys, "stdout", output),
        ):
            exit_code = inspect_global_tools.main()

        assert exit_code == 0
        inspect.assert_called_once_with(
            str(self.repository),
            10.0,
            True,
            False,
            ("dolgorae", "podway"),
        )
        assert json.loads(output.getvalue()) == result

    @pytest.mark.parametrize(
        "arguments",
        (
            ("--component", "sorage", "--verify-dolgorae-release"),
            ("--component", "dolgorae", "--include-sorage-initialization"),
            ("--component", "unknown"),
        ),
    )
    def test_invalid_component_scope_returns_json_error(
        self, arguments: tuple[str, ...]
    ) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GLOBAL_SCRIPT),
                "--repository",
                str(self.repository),
                *arguments,
            ],
            cwd=self.repository,
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 2
        assert json.loads(completed.stdout)["error"]["code"] == "invalid_arguments"
