from __future__ import annotations

import hashlib
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


@pytest.mark.parametrize(
    "case", ["timeout", "failed", "invalid_json", "unavailable", "broken"]
)
def test_aquarium_runtime_probe_preserves_failure_reason(tmp_path, monkeypatch, case):
    diagnostic = {
        "schema": "aquarium-dev-runtime-error/v1",
        "error": {"code": "runtime_install_failed"},
    }

    def probe(command, **kwargs):
        assert kwargs["timeout"] == 3.5
        if case == "timeout":
            raise subprocess.TimeoutExpired(command, 3.5)
        if case == "unavailable":
            raise OSError("interpreter unavailable")
        if case == "failed":
            return subprocess.CompletedProcess(command, 1, "", json.dumps(diagnostic))
        if case == "invalid_json":
            return subprocess.CompletedProcess(command, 0, "{", "")
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"status": "broken", "problem": "receipt missing"}),
            "",
        )

    monkeypatch.setattr(inspect_global_tools.subprocess, "run", probe)
    payload = inspect_global_tools.inspect_global(
        str(tmp_path), 3.5, components=("aquarium-dev",)
    )["tools"]["aquarium-dev"]
    if case == "broken":
        assert payload == {"status": "broken", "problem": "receipt missing"}
    else:
        assert payload["status"] == "unverifiable"
        assert payload["problem"]
        assert (
            payload["reason"]
            == {
                "timeout": "probe_timeout",
                "failed": "probe_failed",
                "invalid_json": "invalid_json",
                "unavailable": "probe_failed",
            }[case]
        )
        if case == "failed":
            assert payload["exit_code"] == 1
            assert payload["diagnostic"] == diagnostic
        elif case == "timeout":
            assert payload["timeout_seconds"] == 3.5


@pytest.mark.parametrize(
    ("status", "installed", "launcher_state", "action"),
    [
        (
            "current",
            {
                "plugin_version": "0.1.17",
                "source_sha256": "installed-source",
                "python_version": "3.13.7",
            },
            "managed_current",
            None,
        ),
        ("missing", None, "missing", "install"),
        (
            "outdated",
            {
                "plugin_version": "0.1.16",
                "source_sha256": "old-source",
                "python_version": "3.13.7",
            },
            "managed_outdated",
            "update",
        ),
        ("broken", None, "managed_outdated", "repair"),
        ("unsafe", None, "unknown", None),
    ],
)
def test_aquarium_status_diagnosis_is_passed_through(
    monkeypatch, status, installed, launcher_state, action
):
    diagnosis = {
        "schema": "aquarium-status-runtime-inspection/v1",
        "status": status,
        "bundled": {
            "plugin_version": "0.1.17",
            "source_sha256": "bundled-source",
        },
        "installed": installed,
        "launcher": {
            "path": "/isolated/home/.local/bin/aquarium-status",
            "state": launcher_state,
        },
        "runtime_root": "/isolated/home/.local/share/aquarium-status",
        "action": action,
    }
    diagnose = mock.Mock(return_value=diagnosis)
    module = mock.Mock(diagnose=diagnose)
    spec = mock.Mock(loader=mock.Mock())
    monkeypatch.setattr(
        inspect_global_tools.importlib.util,
        "spec_from_file_location",
        lambda *args, **kwargs: spec,
    )
    monkeypatch.setattr(
        inspect_global_tools.importlib.util,
        "module_from_spec",
        lambda requested_spec: module,
    )

    result = inspect_global_tools.inspect_aquarium_status()

    assert result is diagnosis
    diagnose.assert_called_once()
    assert diagnose.call_args.args[0].name == "aquarium-status"


def test_aquarium_status_component_scope_is_isolated(tmp_path, monkeypatch):
    inspector = mock.Mock()
    diagnosis = {
        "schema": "aquarium-status-runtime-inspection/v1",
        "status": "missing",
        "bundled": {
            "plugin_version": "0.1.17",
            "source_sha256": "bundled-source",
        },
        "installed": None,
        "launcher": {
            "path": "/isolated/home/.local/bin/aquarium-status",
            "state": "missing",
        },
        "runtime_root": "/isolated/home/.local/share/aquarium-status",
        "action": "install",
    }
    status_inspector = mock.Mock(return_value=diagnosis)
    monkeypatch.setattr(inspect_global_tools, "load_inspector", lambda: inspector)
    monkeypatch.setattr(
        inspect_global_tools, "inspect_aquarium_status", status_inspector
    )

    payload = inspect_global_tools.inspect_global(
        str(tmp_path), 1.0, components=("aquarium-status",)
    )

    assert payload["tools"] == {"aquarium-status": diagnosis}
    status_inspector.assert_called_once_with()
    assert inspector.method_calls == []


def test_other_component_scope_skips_aquarium_status(tmp_path, monkeypatch):
    inspector = mock.Mock()
    inspector.inspect_lora.return_value = {"status": "configured"}
    status_inspector = mock.Mock()
    monkeypatch.setattr(inspect_global_tools, "load_inspector", lambda: inspector)
    monkeypatch.setattr(
        inspect_global_tools, "inspect_aquarium_status", status_inspector
    )

    payload = inspect_global_tools.inspect_global(
        str(tmp_path), 1.0, components=("lora",)
    )

    assert payload["tools"] == {"lora": {"status": "configured"}}
    status_inspector.assert_not_called()
    inspector.inspect_lora.assert_called_once_with()


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

        assert payload["schema_version"] == "aquarium-dev-setup-global-inspection.v5"
        assert payload["inspection_scope"] == "user_global"
        assert "repository" not in payload
        for name in ("sanho", "mulgae", "gaori", "sorage", "podway"):
            assert "status" in payload["tools"][name]["cli"]
        assert payload["tools"]["sorage"]["cli"]["status"] == "missing"
        assert "status" in payload["tools"]["dolgorae"]
        assert "installation_prerequisites" in payload["tools"]["mulgae"]
        for name in ("lora", "deslop", "humanizer", "im-not-ai"):
            assert "status" in payload["tools"][name]
            assert "cli" not in payload["tools"][name]
        assert "homes" in payload["tools"]["ouroboros"]
        assert "cli" in payload["tools"]["ouroboros"]
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
            "aquarium-dev",
            "aquarium-status",
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

    @pytest.mark.parametrize(
        "case",
        ["valid", "missing", "partial", "invalid", "duplicate", "alternate", "symlink"],
    )
    def test_gaori_status_skill_is_independent(self, case: str) -> None:
        inspector = inspect_global_tools.load_inspector()
        execution = self.home / ".agents/skills/use-gaori"
        for name in inspector.GAORI_SKILL_FILES:
            path = execution / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("---\nname: use-gaori\n---\n", encoding="utf-8")
        canonical = self.home / ".agents/skills/use-gaori-status"
        alternate = self.codex_home / "skills/use-gaori-status"
        if case != "missing":
            target = alternate if case == "alternate" else canonical
            target.mkdir(parents=True)
            if case != "partial":
                name = "wrong-name" if case == "invalid" else "use-gaori-status"
                target.joinpath("SKILL.md").write_text(
                    f"---\nname: {name}\n---\n", encoding="utf-8"
                )
            if case == "duplicate":
                alternate.mkdir(parents=True)
                alternate.joinpath("SKILL.md").write_bytes(
                    canonical.joinpath("SKILL.md").read_bytes()
                )
            if case == "symlink":
                external = self.base / "external.md"
                canonical.joinpath("SKILL.md").rename(external)
                canonical.joinpath("SKILL.md").symlink_to(external)

        with mock.patch.dict(os.environ, self.environment, clear=True):
            payload = inspect_global_tools.inspect_global(
                str(self.repository), 1.0, components=("gaori",)
            )
        assert set(payload["tools"]) == {"gaori"}
        gaori = payload["tools"]["gaori"]
        assert gaori["paired_skill"]["status"] == "configured"
        assert gaori["cli"]["status"] == "missing"
        status_skill = gaori["status_skill"]
        expected = (
            "configured"
            if case == "valid"
            else "missing"
            if case == "missing"
            else "degraded"
        )
        assert status_skill["status"] == expected
        assert status_skill["duplicate"] is (case == "duplicate")
        assert status_skill["canonical_path"] == str(canonical)
        if case == "valid":
            files = status_skill["installations"][0]["files"]
            assert len(files) == 1
            assert files[0]["path"] == "SKILL.md"
            assert files[0]["sha256"]

    def test_project_gaori_status_skill_trusts_only_presence(self) -> None:
        canonical = self.home / ".agents/skills/use-gaori-status"
        canonical.mkdir(parents=True)
        canonical.joinpath("SKILL.md").write_text("invalid content", encoding="utf-8")
        payload = self.run_inspector(PROJECT_SCRIPT)
        assert payload["trusted_global_skills"]["use-gaori-status"] == {
            "canonical_path": str(canonical),
            "present": True,
            "verification_scope": "presence_only",
        }

    def test_global_ouroboros_probe_uses_neutral_working_directory(self) -> None:
        inspector = mock.MagicMock()
        inspector.SANHO_SKILL_FILES = ()
        inspector.DOLGORAE_SKILL_FILES = ()
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
                inspect_global_tools, "inspect_ouroboros", return_value={}
            ) as inspect_ouroboros_global,
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
            inspect_global_tools.inspect_global(str(self.repository), 3.5)

        inspect_ouroboros_global.assert_called_once_with(
            inspector, Path(self.repository.anchor), 3.5, (), False
        )
        inspector.inspect_dolgorae.assert_called_once_with(
            Path(self.repository.anchor), 3.5
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
        inspector.DOLGORAE_SKILL_FILES = ()
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
                components=("dolgorae",),
            )

        assert list(payload["tools"]) == ["dolgorae"]
        inspector.inspect_dolgorae.assert_called_once_with(
            Path(self.repository.anchor), 3.5
        )
        inspect_versioned.assert_not_called()
        inspect_sorage.assert_not_called()
        inspect_podway.assert_not_called()
        inspect_mcp.assert_not_called()
        inspector.inspect_agent_skill.assert_called_once_with("use-dolgorae", ())
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
                "version": "v0.2.10",
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
            "version": "v0.2.10",
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
            ({"version": "v0.2.11"}, {"ok": True}, ("versions_match", False)),
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
            "version": "v0.2.10",
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
            "version": "v0.2.10",
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
        inspector.inspect_global_mcp_scope.return_value = {"status": "unavailable"}

        inspect_global_tools.inspect_global_mcp(
            inspector, "gaori", "/usr/local/bin/gaori", self.repository, 2.0
        )

        inspector.inspect_global_mcp_scope.assert_called_once_with(
            "gaori", "/usr/local/bin/gaori", self.repository, 2.0
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

        assert payload["schema_version"] == "aquarium-dev-setup-inspection.v21"
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

        assert payload["schema_version"] == "aquarium-dev-setup-inspection.v21"
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
            True,
            inspect_global_tools.GLOBAL_COMPONENTS,
            (),
            False,
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
            ("dolgorae", "podway"),
            (),
            False,
        )
        assert json.loads(output.getvalue()) == result

    @pytest.mark.parametrize(
        "arguments",
        (
            ("--verify-dolgorae-release",),
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


@pytest.fixture
def ouroboros_homes(tmp_path, monkeypatch):
    import hashlib

    import inspect_ouroboros

    home = tmp_path / "user"
    current = home / ".codex-hsy"
    default = home / ".codex"
    bin_dir = tmp_path / "bin"
    for path in (current, default, bin_dir):
        path.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(current))
    monkeypatch.setenv("PATH", str(bin_dir) + ":/usr/bin:/bin")
    log = tmp_path / "commands.jsonl"
    monkeypatch.setenv("PROBE_LOG", str(log))
    source = {
        "rules/ouroboros.md": b"rules from the package\n",
        "skills/ouroboros-auto/SKILL.md": b"---\nname: auto\n---\nupstream\n",
    }
    expected = {
        path: hashlib.sha256(content).hexdigest() for path, content in source.items()
    }
    monkeypatch.setattr(inspect_ouroboros, "packaged_assets", lambda *args: expected)
    program = """
import json, os, sys, tomllib
from pathlib import Path
name = Path(sys.argv[0]).name
home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
with open(os.environ["PROBE_LOG"], "a") as stream:
    stream.write(json.dumps({"name": name, "args": sys.argv[1:], "home": str(home), "cwd": os.getcwd()}) + "\\n")
if name == "ooo":
    if sys.argv[1:] == ["--version"]:
        print("Ouroboros version 0.53.0")
    elif sys.argv[1:] == ["codex", "doctor"]:
        sys.exit(1 if (home / "doctor-failed").exists() else 0)
    elif sys.argv[1:] == ["mcp", "doctor", "--json"]:
        print("[]")
    else:
        sys.exit(2)
elif name == "codex":
    configured = (home / "config.toml").exists()
    if sys.argv[1:] == ["mcp", "list", "--json"]:
        print(json.dumps([{"name": "ouroboros"}] if configured else []))
        sys.exit(0)
    if not configured:
        print("No MCP server named 'ouroboros' found.", file=sys.stderr)
        sys.exit(1)
    entry = tomllib.loads((home / "config.toml").read_text())["mcp_servers"]["ouroboros"]
    print(json.dumps({"name": "ouroboros", "enabled": True, "transport": {"type": "stdio", **entry}}))
"""
    for name in ("ooo", "codex", "uvx"):
        path = bin_dir / name
        path.write_text(f"#!{sys.executable}\n" + program)
        path.chmod(0o755)

    def install(target, binding=None, pin="0.53.0"):
        target.mkdir(parents=True, exist_ok=True)
        for relative, contents in source.items():
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        env = {"OUROBOROS_AGENT_RUNTIME": "codex", "OUROBOROS_LLM_BACKEND": "codex"}
        if binding != "absent":
            env["CODEX_HOME"] = str(binding or target)
        args = [
            "--isolated",
            "--python",
            ">=3.12",
            "--from",
            "ouroboros-ai[mcp]" + (f"=={pin}" if pin else ""),
            "ouroboros",
            "mcp",
            "serve",
        ]
        (target / "config.toml").write_text(
            "[mcp_servers.ouroboros]\ncommand = "
            + json.dumps(str(bin_dir / "uvx"))
            + "\nargs = "
            + json.dumps(args)
            + "\n[mcp_servers.ouroboros.env]\n"
            + "".join(f"{key} = {json.dumps(value)}\n" for key, value in env.items())
        )

    install(current)
    install(default)
    return inspect_ouroboros, home, current, default, log, install, source


def inspect_home_fixture(fixture):
    module = fixture[0]
    return module.inspect_ouroboros(inspect_global_tools.load_inspector(), Path("/"), 5)


def test_ouroboros_reads_each_home_and_probes_cli_once(ouroboros_homes):
    _, _, current, default, log, _, _ = ouroboros_homes
    result = inspect_home_fixture(ouroboros_homes)
    assert result["current_home"] == str(current)
    assert result["all_discovered_homes_readiness"] == "configured"
    assert {row["home"] for row in result["homes"]} == {str(current), str(default)}
    assert all(
        row["live_runtime"]["status"] == "not_observed" for row in result["homes"]
    )
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert sum(call["args"] == ["--version"] for call in calls) == 1
    assert all(call["cwd"] == "/" for call in calls)
    assert {call["home"] for call in calls if call["name"] == "codex"} == {
        str(current),
        str(default),
    }
    assert not any(call["args"] == ["mcp", "doctor", "--json"] for call in calls)


def test_ouroboros_other_home_failure_does_not_block_current(ouroboros_homes):
    _, _, current, default, _, _, _ = ouroboros_homes
    (default / "skills/ouroboros-auto/SKILL.md").unlink()
    result = inspect_home_fixture(ouroboros_homes)
    assert result["status"] == result["current_home_readiness"] == "configured"
    assert result["all_discovered_homes_readiness"] == "degraded"
    assert result["homes"][1]["rules"]["status"] == "configured"
    assert result["homes"][1]["skills"]["status"] == "missing"
    (current / "rules/ouroboros.md").write_text("outdated")
    result = inspect_home_fixture(ouroboros_homes)
    assert result["homes"][0]["rules"]["status"] == "different"
    assert result["homes"][0]["skills"]["status"] == "configured"


@pytest.mark.parametrize(
    "binding,reason",
    [
        ("other", "home_mismatch"),
        ("absent", "home_not_explicit"),
        ("relative", "home_invalid"),
    ],
)
def test_ouroboros_successful_doctor_cannot_hide_home_mismatch(
    ouroboros_homes, binding, reason
):
    _, _, current, default, _, install, _ = ouroboros_homes
    install(current, default if binding == "other" else binding)
    result = inspect_home_fixture(ouroboros_homes)
    row = result["homes"][0]
    assert row["codex_integration"]["status"] == "configured"
    assert row["mcp_registration"]["status"] == "configured"
    assert row["home_binding"]["reason"] == reason
    assert row["status"] == "degraded"
    # An auto setup which preserves this entry changes no evidence. An explicit
    # replacement binds to the current home and permits configuration readiness.
    assert inspect_home_fixture(ouroboros_homes)["status"] == "degraded"
    install(current)
    assert inspect_home_fixture(ouroboros_homes)["status"] == "configured"


@pytest.mark.parametrize(
    "pin,status", [(None, "unverifiable"), ("0.51.17", "different")]
)
def test_ouroboros_runtime_package_is_independent(ouroboros_homes, pin, status):
    _, _, current, _, _, install, _ = ouroboros_homes
    install(current, pin=pin)
    result = inspect_home_fixture(ouroboros_homes)
    assert result["cli"]["version"] == "0.53.0"
    assert result["homes"][0]["runtime_package"]["status"] == status
    assert result["status"] == "degraded"


def test_ouroboros_discovers_only_home_candidates_and_merges_aliases(
    ouroboros_homes, monkeypatch
):
    module, home, current, default, _, install, _ = ouroboros_homes
    for name in (".codex-tools", ".codexbar"):
        (home / name).mkdir()
    (home / ".codex-tools" / "config.toml").mkdir()
    other = home / ".codex-work"
    install(other)
    alias = home / ".codex-alias"
    alias.symlink_to(other, target_is_directory=True)
    custom = home / "custom"
    active, homes, failures = module.discover_homes((str(custom),))
    assert not failures
    assert active == current
    assert set(homes) == {current, default, other, custom}
    monkeypatch.delenv("CODEX_HOME")
    assert module.discover_homes()[0] == default
    monkeypatch.chdir(home)
    monkeypatch.setenv("CODEX_HOME", "custom")
    assert module.discover_homes()[0] == custom
    invalid = home / "file"
    invalid.touch()
    with pytest.raises(ValueError):
        module.discover_homes((str(invalid),))


def test_ouroboros_shared_skills_are_migration_evidence_only(ouroboros_homes):
    _, home, current, _, _, _, source = ouroboros_homes
    shared = home / ".agents/skills/ouroboros-auto"
    shared.mkdir(parents=True)
    shared.joinpath("SKILL.md").write_bytes(source["skills/ouroboros-auto/SKILL.md"])
    current.joinpath("skills/ouroboros-auto/SKILL.md").unlink()
    before = shared.joinpath("SKILL.md").read_bytes()
    result = inspect_home_fixture(ouroboros_homes)
    assert result["legacy_shared_skills"] == [str(shared)]
    assert result["homes"][0]["skills"]["status"] == "missing"
    assert shared.joinpath("SKILL.md").read_bytes() == before


def test_ouroboros_shared_skill_blocks_ready_home(ouroboros_homes):
    _, home, _, _, _, _, source = ouroboros_homes
    shared = home / ".agents/skills/ouroboros-auto"
    shared.mkdir(parents=True)
    shared.joinpath("SKILL.md").write_bytes(source["skills/ouroboros-auto/SKILL.md"])

    result = inspect_home_fixture(ouroboros_homes)

    assert result["legacy_shared_skills"] == [str(shared)]
    assert result["homes"][0]["skills"]["status"] == "configured"
    assert result["homes"][0]["status"] == "degraded"
    assert result["homes"][0]["reason"] == "legacy_shared_skills_present"
    assert result["current_home_readiness"] == "degraded"


def test_ouroboros_unrelated_prefixed_shared_skill_does_not_block_home(
    ouroboros_homes,
):
    _, home, _, _, _, _, _ = ouroboros_homes
    unrelated = home / ".agents/skills/ouroboros-notes"
    unrelated.mkdir(parents=True)

    result = inspect_home_fixture(ouroboros_homes)

    assert result["legacy_shared_skills"] == []
    assert result["shared_skill_conflicts"] == []
    assert result["current_home_readiness"] == "configured"


def test_ouroboros_old_unprefixed_shared_skill_blocks_ready_home(ouroboros_homes):
    _, home, _, _, _, _, _ = ouroboros_homes
    shared = home / ".agents/skills/auto"
    shared.mkdir(parents=True)
    shared.joinpath("SKILL.md").write_text("---\nname: auto\n---\nold upstream\n")

    result = inspect_home_fixture(ouroboros_homes)

    assert result["legacy_shared_skills"] == []
    assert result["shared_skill_conflicts"] == [str(shared)]
    assert result["homes"][0]["skills"]["status"] == "configured"
    assert result["homes"][0]["status"] == "degraded"
    assert result["homes"][0]["reason"] == "shared_skill_conflict"

    shared.joinpath("SKILL.md").write_text("---\nname: unrelated\n---\nuser skill\n")
    result = inspect_home_fixture(ouroboros_homes)
    assert result["shared_skill_conflicts"] == []
    assert result["current_home_readiness"] == "configured"


def test_ouroboros_case_alias_merges_by_identity_and_matches_binding(
    ouroboros_homes, monkeypatch
):
    module, home, current, default, _, install, _ = ouroboros_homes
    alias = home / ".Codex-HSY"
    original = Path.stat

    def case_insensitive_stat(path, *args, **kwargs):
        return original(current if path == alias else path, *args, **kwargs)

    # Model the same-directory identity supplied by a case-insensitive filesystem.
    # This exercises both discovery and MCP binding on case-sensitive CI hosts too.
    monkeypatch.setattr(Path, "stat", case_insensitive_stat)
    monkeypatch.setenv("CODEX_HOME", str(alias))
    active, homes, failures = module.discover_homes((str(current),))
    assert active == alias
    assert homes == [alias, default]
    assert not failures
    monkeypatch.setenv("CODEX_HOME", str(current))
    install(current, binding=alias)
    active, homes, failures = module.discover_homes((str(alias),))
    assert active == current
    assert homes == [current, default]
    assert not failures
    result = inspect_home_fixture(ouroboros_homes)
    assert len(result["homes"]) == 2
    assert result["homes"][0]["home_binding"]["reason"] == "home_matches"
    assert result["all_discovered_homes_readiness"] == "configured"


@pytest.mark.parametrize("relative", ["rules", "skills", "skills/ouroboros-auto"])
def test_ouroboros_unreadable_artifact_directory_is_not_missing(
    ouroboros_homes, monkeypatch, relative
):
    _, _, current, default, _, _, _ = ouroboros_homes
    original = os.scandir

    def scandir(path):
        if Path(path) == current / relative:
            raise PermissionError("private directory failure")
        return original(path)

    monkeypatch.setattr(os, "scandir", scandir)
    result = inspect_home_fixture(ouroboros_homes)
    row = result["homes"][0]
    affected = relative.split("/")[0]
    healthy = "rules" if affected == "skills" else "skills"
    assert row[affected] == {"status": "unverifiable", "reason": "artifact_read_failed"}
    assert row[healthy]["status"] == "configured"
    assert row["mcp_registration"]["status"] == "configured"
    assert (
        next(row for row in result["homes"] if row["home"] == str(default))["status"]
        == "configured"
    )
    assert result["current_home_readiness"] == "degraded"


def test_ouroboros_unreadable_discovery_artifacts_keep_home_failure(
    ouroboros_homes, monkeypatch
):
    module, home, _, _, _, _, _ = ouroboros_homes
    candidate = home / ".codex-work"
    (candidate / "rules").mkdir(parents=True)
    original = os.scandir

    def scandir(path):
        if Path(path) == candidate / "rules":
            raise PermissionError("private directory failure")
        return original(path)

    monkeypatch.setattr(os, "scandir", scandir)
    _, homes, failures = module.discover_homes()
    assert candidate in homes
    assert failures == {candidate: "home_inspection_failed"}


def test_ouroboros_symlinked_artifacts_and_extra_files_are_gaps(ouroboros_homes):
    _, _, current, _, _, _, _ = ouroboros_homes
    extra = current / "skills/ouroboros-auto/extra.txt"
    extra.write_text("extra")
    assert inspect_home_fixture(ouroboros_homes)["homes"][0]["skills"]["extra"] == [
        "skills/ouroboros-auto/extra.txt"
    ]
    extra.unlink()
    extra.symlink_to(current / "rules/ouroboros.md")
    assert (
        inspect_home_fixture(ouroboros_homes)["homes"][0]["skills"]["status"]
        == "unsafe"
    )


def test_ouroboros_artifacts_do_not_inherit_aggregate_doctor_failure(ouroboros_homes):
    _, _, current, _, _, _, _ = ouroboros_homes
    (current / "doctor-failed").touch()
    row = inspect_home_fixture(ouroboros_homes)["homes"][0]
    assert row["codex_integration"]["status"] == "degraded"
    assert row["rules"]["status"] == row["skills"]["status"] == "configured"


@pytest.mark.parametrize(
    "installed,latest,status",
    [
        ("0.51.15", "0.53.0", "update_available"),
        ("0.53.0", "0.54.4", "update_available"),
        ("0.54.4", "0.54.4", "current"),
        (None, "0.53.0", "missing"),
    ],
)
def test_ouroboros_freshness_distinguishes_supported_and_latest(
    monkeypatch, installed, latest, status
):
    import inspect_ouroboros

    releases = {
        name: [{"yanked": False}] for name in ("0.51.17", "0.53.0", latest, "0.55.0rc1")
    }
    releases["0.55.0"] = [{"yanked": True}]
    payload = {"info": {"name": "ouroboros-ai"}, "releases": releases}
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.geturl.return_value = inspect_ouroboros.PYPI_URL
    response.read.return_value = json.dumps(payload).encode()
    monkeypatch.setattr(
        inspect_ouroboros.urllib.request, "urlopen", lambda *args, **kwargs: response
    )
    result = inspect_ouroboros.release_freshness(
        inspect_global_tools.load_inspector(), ouroboros_cli_observation(installed), 1
    )
    assert result["status"] == status
    assert result["latest_supported"] == latest
    assert result["latest_stable"] == latest
    assert "compatibility_review_required" not in result


def test_ouroboros_freshness_reports_no_supported_release(monkeypatch):
    import inspect_ouroboros

    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.geturl.return_value = inspect_ouroboros.PYPI_URL
    response.read.return_value = json.dumps(
        {
            "info": {"name": "ouroboros-ai"},
            "releases": {"0.51.0": [{"yanked": False}]},
        }
    ).encode()
    monkeypatch.setattr(
        inspect_ouroboros.urllib.request, "urlopen", lambda *args, **kwargs: response
    )

    result = inspect_ouroboros.release_freshness(
        inspect_global_tools.load_inspector(), ouroboros_cli_observation(None), 1
    )

    assert result["status"] == "missing"
    assert result["latest_stable"] == "0.51.0"
    assert result["latest_supported"] is None


def test_ouroboros_freshness_failure_and_opt_in(ouroboros_homes, monkeypatch):
    module = ouroboros_homes[0]
    fetch = mock.Mock(side_effect=OSError("network secret"))
    monkeypatch.setattr(module.urllib.request, "urlopen", fetch)
    assert inspect_home_fixture(ouroboros_homes)["freshness"]["status"] == "not_checked"
    fetch.assert_not_called()
    result = module.release_freshness(
        inspect_global_tools.load_inspector(), ouroboros_cli_observation("0.53.0"), 1
    )
    assert result["status"] == "freshness_unverifiable"
    assert "secret" not in json.dumps(result)


@pytest.mark.parametrize(
    "option", [["--codex-home", "/tmp/home"], ["--verify-ouroboros-release"]]
)
def test_ouroboros_flags_require_selected_component(option):
    completed = subprocess.run(
        [sys.executable, str(GLOBAL_SCRIPT), "--component", "lora", *option],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["error"]["code"] == "invalid_arguments"


@pytest.mark.parametrize(
    "failure", ["version", "path", "digest", "incomplete", "unavailable"]
)
def test_ouroboros_package_asset_probe_fails_closed(tmp_path, failure):
    import inspect_ouroboros

    (tmp_path / "python").touch()
    cli = {
        "installed": True,
        "version_supported": True,
        "executable": str(tmp_path / "ooo"),
        "version": "0.53.0",
    }
    result = {
        "version": "0.53.0",
        "artifacts": {
            "rules/ouroboros.md": "a" * 64,
            "skills/ouroboros-auto/SKILL.md": "b" * 64,
        },
    }
    if failure == "version":
        result["version"] = "0.51.17"
    elif failure == "path":
        result["artifacts"]["skills/../../outside"] = "a" * 64
    elif failure == "digest":
        result["artifacts"]["rules/ouroboros.md"] = "invalid"
    elif failure == "incomplete":
        result["artifacts"].pop("rules/ouroboros.md")
    inspector = mock.Mock()
    inspector.json_probe.return_value = {
        "ok": failure != "unavailable",
        "result": result,
    }
    assert inspect_ouroboros.packaged_assets(inspector, cli, Path("/"), 1) is None
    assert (
        inspect_ouroboros.inspect_artifacts(tmp_path, "rules", None)["status"]
        == "unverifiable"
    )


def test_ouroboros_public_cli_accepts_extra_home_and_keeps_v3_shape(
    ouroboros_homes, tmp_path
):
    _, _, current, default, _, install, _ = ouroboros_homes
    custom = tmp_path / "custom-home"
    install(custom)
    completed = subprocess.run(
        [
            sys.executable,
            str(GLOBAL_SCRIPT),
            "--component",
            "ouroboros",
            "--codex-home",
            str(custom),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "aquarium-dev-setup-global-inspection.v5"
    result = payload["tools"]["ouroboros"]
    assert {row["home"] for row in result["homes"]} == {
        str(current),
        str(default),
        str(custom),
    }
    assert result["freshness"]["status"] == "not_checked"
    # This fixture intentionally lacks the uv-tool package interpreter. CLI
    # success must not turn unavailable package comparison into healthy skills.
    assert all(row["skills"]["status"] == "unverifiable" for row in result["homes"])


def test_ouroboros_asset_manifest_uses_native_rendered_rules(
    tmp_path, monkeypatch, capsys
):
    import hashlib
    import importlib.metadata
    import runpy
    from types import ModuleType, SimpleNamespace

    import inspect_ouroboros

    rule = tmp_path / "ouroboros.md"
    rule.write_text("unrendered source")
    skill = tmp_path / "auto"
    skill.mkdir()
    (skill / "SKILL.md").write_text("upstream skill")
    assets = SimpleNamespace(
        rules_path=rule,
        managed_artifacts=[
            SimpleNamespace(
                source_path=rule, relative_install_path=Path("rules/ouroboros.md")
            ),
            SimpleNamespace(
                source_path=skill, relative_install_path=Path("skills/ouroboros-auto")
            ),
        ],
    )
    context = mock.MagicMock()
    context.__enter__.return_value = assets
    module = ModuleType("ouroboros.codex.artifacts")
    module.resolve_packaged_codex_assets = lambda: context
    module.load_packaged_codex_rules = lambda: (
        "rendered rules with native runtime guidance"
    )
    monkeypatch.setitem(sys.modules, "ouroboros.codex.artifacts", module)
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.53.0")
    script = tmp_path / "asset_probe.py"
    script.write_text(inspect_ouroboros.ASSET_PROBE)
    runpy.run_path(str(script))
    result = json.loads(capsys.readouterr().out)
    assert (
        result["artifacts"]["rules/ouroboros.md"]
        == hashlib.sha256(module.load_packaged_codex_rules().encode()).hexdigest()
    )
    assert (
        result["artifacts"]["skills/ouroboros-auto/SKILL.md"]
        == hashlib.sha256(b"upstream skill").hexdigest()
    )


def ouroboros_cli_observation(version, *, installed=True, ok=True):
    return {
        "installed": installed and version is not None,
        "version": version,
        "probes": {"version": {"ok": ok}},
    }


@pytest.mark.parametrize("phase", ["connect", "read"])
def test_ouroboros_http_failure_preserves_global_results(
    ouroboros_homes, monkeypatch, phase
):
    import http.client

    module = ouroboros_homes[0]
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.geturl.return_value = module.PYPI_URL
    if phase == "connect":
        fetch = mock.Mock(side_effect=http.client.BadStatusLine("private proxy data"))
    else:
        response.read.side_effect = http.client.IncompleteRead(b"private response data")
        fetch = mock.Mock(return_value=response)
    monkeypatch.setattr(module.urllib.request, "urlopen", fetch)
    output = io.StringIO()
    with (
        mock.patch.object(
            sys,
            "argv",
            [
                "inspect_global_tools.py",
                "--component",
                "ouroboros",
                "--component",
                "deslop",
                "--verify-ouroboros-release",
            ],
        ),
        mock.patch.object(sys, "stdout", output),
    ):
        assert inspect_global_tools.main() == 0
    payload = json.loads(output.getvalue())
    assert "deslop" in payload["tools"]
    result = payload["tools"]["ouroboros"]
    assert result["all_discovered_homes_readiness"] == "configured"
    assert result["freshness"]["status"] == "freshness_unverifiable"
    assert result["freshness"]["reason"] == "release_metadata_unverifiable"
    assert "private proxy data" not in output.getvalue()
    assert "private response data" not in output.getvalue()


@pytest.mark.parametrize("default_active", [False, True])
def test_ouroboros_invalid_active_home_preserves_other_results(
    ouroboros_homes, monkeypatch, default_active
):
    _, home, _, default, log, _, _ = ouroboros_homes
    if default_active:
        import shutil

        shutil.rmtree(default)
        invalid = default
        monkeypatch.delenv("CODEX_HOME")
    else:
        invalid = home / "invalid-home"
        monkeypatch.setenv("CODEX_HOME", str(invalid))
    invalid.write_text("not a directory")
    # The CLI entrypoint exercises the real home/leaf wiring without a package fixture.
    completed = subprocess.run(
        [
            sys.executable,
            str(GLOBAL_SCRIPT),
            "--component",
            "ouroboros",
            "--component",
            "deslop",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
    payload = json.loads(completed.stdout)
    assert "deslop" in payload["tools"]
    result = payload["tools"]["ouroboros"]
    assert result["current_home_readiness"] == "degraded"
    assert result["homes"][0]["reason"] == "home_not_a_directory"
    assert all(
        result["homes"][0][key]["status"] == "unverifiable"
        for key in (
            "rules",
            "skills",
            "codex_integration",
            "mcp_registration",
            "mcp_runtime",
            "home_binding",
            "runtime_package",
        )
    )
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert sum(call["args"] == ["--version"] for call in calls) == 1
    assert not any(
        call["home"] == str(invalid) and call["args"] != ["--version"] for call in calls
    )
    assert any(
        call["name"] == "codex" and call["home"] != str(invalid) for call in calls
    )
    # Package assets are available in the in-process fixture: the independent home stays ready.
    result = inspect_home_fixture(ouroboros_homes)
    assert any(row["status"] == "configured" for row in result["homes"][1:])
    assert result["all_discovered_homes_readiness"] == "degraded"
    assert invalid.read_text() == "not a directory"


@pytest.mark.parametrize("value", ["", " ", "\t\n"])
def test_ouroboros_blank_home_rejected_before_probes(ouroboros_homes, value):
    module, _, _, _, log, _, _ = ouroboros_homes
    completed = subprocess.run(
        [
            sys.executable,
            str(GLOBAL_SCRIPT),
            "--component",
            "ouroboros",
            "--codex-home",
            value,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["error"]["code"] == "invalid_arguments"
    assert not log.exists()
    with pytest.raises(ValueError, match="blank"):
        module.discover_homes((value,))


def test_ouroboros_explicit_file_home_remains_input_error(ouroboros_homes):
    _, home, _, _, log, _, _ = ouroboros_homes
    invalid = home / "file"
    invalid.touch()
    completed = subprocess.run(
        [
            sys.executable,
            str(GLOBAL_SCRIPT),
            "--component",
            "ouroboros",
            "--codex-home",
            str(invalid),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["error"]["code"] == "invalid_codex_home"
    assert not log.exists()


def test_ouroboros_relative_home_preserves_spaces_and_missing_target(
    ouroboros_homes, monkeypatch
):
    _, home, _, _, _, _, _ = ouroboros_homes
    monkeypatch.chdir(home)
    requested = " custom home "
    completed = subprocess.run(
        [
            sys.executable,
            str(GLOBAL_SCRIPT),
            "--component",
            "ouroboros",
            "--codex-home",
            requested,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    rows = json.loads(completed.stdout)["tools"]["ouroboros"]["homes"]
    assert any(
        row["home"] == str(home / requested) and row["status"] == "degraded"
        for row in rows
    )
    assert not (home / requested).exists()


@pytest.mark.parametrize(
    "failure",
    ["nonzero", "timeout", "unparseable", "missing", "current", "older", "unsupported"],
)
def test_ouroboros_freshness_uses_cli_probe_evidence(
    ouroboros_homes, monkeypatch, failure
):
    module, _, _, _, _, _, _ = ouroboros_homes
    inspector = inspect_global_tools.load_inspector()
    real_run = inspector.run_command
    version = {"older": "0.51.17", "unsupported": "0.51.0"}.get(failure, "0.53.0")

    def run(command, *args, **kwargs):
        if command[1:] == ["--version"]:
            return {
                "attempted": True,
                "ok": failure not in {"nonzero", "timeout"},
                "exit_code": None
                if failure == "timeout"
                else 1
                if failure == "nonzero"
                else 0,
                "timed_out": failure == "timeout",
                "stdout": "unknown"
                if failure == "unparseable"
                else f"Ouroboros version {version}",
                "stderr": "",
            }
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(inspector, "run_command", run)
    if failure == "missing":
        real_which = inspector.shutil.which
        monkeypatch.setattr(
            inspector.shutil,
            "which",
            lambda name: None if name == "ooo" else real_which(name),
        )
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.geturl.return_value = module.PYPI_URL
    response.read.return_value = json.dumps(
        {"info": {"name": "ouroboros-ai"}, "releases": {"0.53.0": [{"yanked": False}]}}
    ).encode()
    monkeypatch.setattr(
        module.urllib.request, "urlopen", mock.Mock(return_value=response)
    )
    result = module.inspect_ouroboros(inspector, Path("/"), 5, verify_release=True)
    freshness = result["freshness"]
    assert freshness["latest_supported"] == "0.53.0"
    expected = {
        "missing": "missing",
        "current": "current",
        "older": "update_available",
        "unsupported": "incompatible",
    }.get(failure, "freshness_unverifiable")
    assert freshness["status"] == expected
    if failure in {"nonzero", "timeout", "unparseable"}:
        assert freshness["reason"] == "cli_version_unverifiable"
        assert result["current_home_readiness"] == "degraded"


@pytest.mark.parametrize("explicit", [False, True])
def test_ouroboros_unresolvable_home_isolated_or_rejected(
    ouroboros_homes, monkeypatch, explicit
):
    _, _, _, default, log, _, _ = ouroboros_homes
    # This user name cannot be resolved by expanduser; no user-global path is touched.
    invalid = "~aquarium-test-nonexistent-user-827415/home"
    arguments = [
        sys.executable,
        str(GLOBAL_SCRIPT),
        "--component",
        "ouroboros",
        "--component",
        "deslop",
        "--component",
        "im-not-ai",
    ]
    if explicit:
        arguments += ["--codex-home", invalid]
    else:
        monkeypatch.setenv("CODEX_HOME", invalid)
    completed = subprocess.run(arguments, capture_output=True, text=True, check=False)
    payload = json.loads(completed.stdout)
    if explicit:
        assert completed.returncode == 2
        assert payload["error"]["code"] == "invalid_codex_home"
        assert not log.exists()
        return
    assert completed.returncode == 0, completed.stdout
    assert "deslop" in payload["tools"]
    assert payload["tools"]["im-not-ai"]["status"] == "unverifiable"
    assert payload["tools"]["im-not-ai"]["expected_target"] is None
    result = payload["tools"]["ouroboros"]
    assert result["current_home"] == invalid
    assert result["homes"][0]["reason"] == "home_resolution_failed"
    assert result["current_home_readiness"] == "degraded"
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert sum(call["args"] == ["--version"] for call in calls) == 1
    assert not any(
        call["home"] == invalid and call["args"] != ["--version"] for call in calls
    )
    result = inspect_home_fixture(ouroboros_homes)
    assert (
        next(row for row in result["homes"] if row["home"] == str(default))["status"]
        == "configured"
    )


def test_ouroboros_unresolvable_launcher_keeps_independent_components(ouroboros_homes):
    _, _, current, default, _, _, _ = ouroboros_homes
    config = current / "config.toml"
    original = config.read_text()
    command_line = next(
        line for line in original.splitlines() if line.startswith("command =")
    )
    config.write_text(
        original.replace(
            command_line, 'command = "~aquarium-test-nonexistent-user-827415/uvx"'
        )
    )
    result = inspect_home_fixture(ouroboros_homes)
    row = result["homes"][0]
    assert row["status"] == "degraded"
    assert row["mcp_registration"]["status"] != "configured"
    assert row["rules"]["status"] == row["skills"]["status"] == "configured"
    assert (
        next(row for row in result["homes"] if row["home"] == str(default))["status"]
        == "configured"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(GLOBAL_SCRIPT),
            "--component",
            "ouroboros",
            "--component",
            "deslop",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
    assert "deslop" in json.loads(completed.stdout)["tools"]


@pytest.mark.parametrize("phase", ["discovery", "artifact", "leaf"])
def test_ouroboros_home_permission_failure_preserves_global_payload(
    ouroboros_homes, monkeypatch, phase
):
    _, _, current, default, log, _, _ = ouroboros_homes
    if phase == "discovery":
        original = Path.stat

        def stat(path, *args, **kwargs):
            if path == current / "config.toml":
                raise PermissionError("private filesystem failure")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "stat", stat)
    elif phase == "artifact":
        original = Path.is_symlink

        def is_symlink(path):
            if path == current / "rules":
                raise PermissionError("private filesystem failure")
            return original(path)

        monkeypatch.setattr(Path, "is_symlink", is_symlink)
    else:
        inspector = inspect_global_tools.load_inspector()
        original = inspector.inspect_ouroboros

        def inspect(repository, timeout_seconds, **kwargs):
            if kwargs["codex_home"] == current:
                raise PermissionError("private filesystem failure")
            return original(repository, timeout_seconds, **kwargs)

        monkeypatch.setattr(inspector, "inspect_ouroboros", inspect)
        monkeypatch.setattr(inspect_global_tools, "load_inspector", lambda: inspector)
    output = io.StringIO()
    with (
        mock.patch.object(
            sys,
            "argv",
            [
                "inspect_global_tools.py",
                "--component",
                "ouroboros",
                "--component",
                "deslop",
            ],
        ),
        mock.patch.object(sys, "stdout", output),
    ):
        assert inspect_global_tools.main() == 0
    payload = json.loads(output.getvalue())
    assert "deslop" in payload["tools"]
    assert "private filesystem failure" not in output.getvalue()
    result = payload["tools"]["ouroboros"]
    assert result["cli"]["version"] == "0.53.0"
    assert (
        result["current_home_readiness"]
        == result["all_discovered_homes_readiness"]
        == "degraded"
    )
    assert (
        next(row for row in result["homes"] if row["home"] == str(default))["status"]
        == "configured"
    )
    row = result["homes"][0]
    if phase == "artifact":
        assert row["rules"]["reason"] == "artifact_read_failed"
        assert (
            row["skills"]["status"] == row["mcp_registration"]["status"] == "configured"
        )
    else:
        assert row["reason"] == "home_inspection_failed"
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert sum(call["args"] == ["--version"] for call in calls) == 1
    if phase == "discovery":
        assert not any(
            call["home"] == str(current) and call["args"] != ["--version"]
            for call in calls
        )


@pytest.mark.parametrize(
    "case", ["missing", "complete", "incomplete", "changed", "duplicate"]
)
def test_dolgorae_paired_skill_is_independent_and_exposes_freshness_evidence(
    tmp_path, monkeypatch, case
):
    home = tmp_path / "home"
    codex_home = tmp_path / "codex"
    home.mkdir()
    codex_home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    inspector = inspect_global_tools.load_inspector()
    canonical = home / ".agents/skills/use-dolgorae"
    expected = {
        "SKILL.md": "---\nname: use-dolgorae\n---\n# Dolgorae\n",
        "references/configuration.md": "Profile configuration\n",
        "references/lifecycle.md": "Lifecycle\n",
        "references/recovery.md": "Recovery\n",
    }
    if case != "missing":
        for relative, content in expected.items():
            if case == "incomplete" and relative == "references/recovery.md":
                continue
            target = canonical / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content + ("Local edit\n" if case == "changed" else ""))
    if case == "duplicate":
        for relative, content in expected.items():
            target = codex_home / "skills/use-dolgorae" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    monkeypatch.setattr(inspect_global_tools, "load_inspector", lambda: inspector)
    monkeypatch.setattr(
        inspector,
        "inspect_dolgorae",
        lambda *args, **kwargs: {
            "status": "installed",
            "installed": True,
            "version": "0.1.2",
            "probes": {},
        },
    )
    payload = inspect_global_tools.inspect_global(
        str(tmp_path), 1.0, components=("dolgorae",)
    )
    assert list(payload["tools"]) == ["dolgorae"]
    tool = payload["tools"]["dolgorae"]
    assert tool["cli"]["status"] == tool["status"] == "installed"
    skill = tool["paired_skill"]
    assert (
        skill["status"]
        == {
            "missing": "missing",
            "complete": "configured",
            "incomplete": "degraded",
            "changed": "configured",
            "duplicate": "degraded",
        }[case]
    )
    assert skill["duplicate"] is (case == "duplicate")
    if case in {"complete", "changed"}:
        hashes = {
            entry["path"]: entry["sha256"]
            for entry in skill["installations"][0]["files"]
        }
        assert set(hashes) == set(expected)
        for relative, content in expected.items():
            assert (
                hashes[relative] == hashlib.sha256(content.encode()).hexdigest()
            ) is (case == "complete")
