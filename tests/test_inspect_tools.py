from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/root-kernel/skills/dev-setup/scripts/inspect_tools.py"

sys.path.insert(0, str(SCRIPT.parent))

import inspect_tools


class InspectToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.repository = self.base / "repository"
        self.bin_directory = self.base / "bin"
        self.home = self.base / "home"
        self.codex_home = self.base / "codex"
        self.repository.mkdir()
        self.bin_directory.mkdir()
        self.home.mkdir()
        self.codex_home.mkdir()
        self.environment = os.environ.copy()
        self.environment.update(
            {
                "HOME": str(self.home),
                "CODEX_HOME": str(self.codex_home),
                "PATH": f"{self.bin_directory}:/usr/bin:/bin",
            }
        )
        self.git("init", "--quiet")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test User")
        (self.repository / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "--quiet", "-m", "Initial")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def git(
        self, *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repository,
            env=self.environment,
            check=check,
            capture_output=True,
            text=True,
        )

    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def inspect(
        self, repository: Path | None = None, timeout_seconds: float = 3.0
    ) -> subprocess.CompletedProcess[str]:
        return self.run_script(
            "--repository",
            str(repository or self.repository),
            "--timeout-seconds",
            str(timeout_seconds),
        )

    def install_fake_tools(
        self,
        malformed_sanho: bool = False,
        slow_gaori: bool = False,
        failing_mulgae_providers: bool = False,
        podway_version: str = "v0.2.7",
        podway_daemon_version: str = "0.2.7",
        podway_daemon_reachable: bool = True,
        podway_doctor_ok: bool = True,
        podway_active_session: bool = False,
        podway_procedure_ok: bool = True,
    ) -> None:
        source = textwrap.dedent(
            f"""\
            #!{sys.executable}
            import json
            import pathlib
            import sys
            import time

            name = pathlib.Path(sys.argv[0]).name
            arguments = sys.argv[1:]
            if name == "sanho":
                if arguments == ["version", "--json"]:
                    print("not-json" if {malformed_sanho!r} else json.dumps({{"name": "sanho", "version": "v1.2.3"}}))
                    raise SystemExit(0)
                print(json.dumps({{"state": "ready"}}))
                raise SystemExit(0)
            if name == "mulgae":
                if arguments == ["version", "--json"]:
                    print(json.dumps({{"name": "mulgae", "version": "v2.3.4"}}))
                    raise SystemExit(0)
                if arguments[:1] == ["providers"]:
                    print("family=zcode profile=zcode-default support=verified evidence=ready assignment=active")
                    if {failing_mulgae_providers!r}:
                        print("code: readiness_unverified", file=sys.stderr)
                        print("stage: cli.providers", file=sys.stderr)
                        raise SystemExit(4)
                    raise SystemExit(0)
                print(json.dumps({{"result": {{"kind": "configuration", "config_uri": ".mulgae/config.yaml", "config_sha256": "abc"}}}}))
                raise SystemExit(0)
            if name == "gaori":
                if arguments == ["version", "--json"]:
                    if {slow_gaori!r}:
                        time.sleep(4)
                    print(json.dumps({{"name": "gaori", "version": "0.4.5"}}))
                    raise SystemExit(0)
                print("generic-v1")
                raise SystemExit(0)
            if name == "podway":
                if arguments == ["version", "--json"]:
                    print(json.dumps({{"name": "podway", "version": {podway_version!r}}}))
                    raise SystemExit(0)
                if arguments == ["daemon", "status", "--json"]:
                    print(json.dumps({{"schema": "podway.output/v1", "result": {{"installed": True, "loaded": True, "reachable": {podway_daemon_reachable!r}, "status": "running", "daemon_version": {podway_daemon_version!r}, "target": "aarch64-apple-darwin", "contract_manifest_schema": "podway.contract-manifest/v1", "contract_manifest_digest": "sha256:test"}}}}))
                    raise SystemExit(0 if {podway_daemon_reachable!r} else 1)
                if arguments == ["doctor", "--json"]:
                    print(json.dumps(dict(schema="podway.output/v1", result=dict(healthy={podway_doctor_ok!r}))))
                    raise SystemExit(0 if {podway_doctor_ok!r} else 1)
                if arguments == ["--json", "status"]:
                    if {podway_active_session!r}:
                        print(json.dumps(dict(schema="podway.output/v2", result=dict(
                            procedure=dict(schema="podway.procedure/v2", id="root-kernel-task-v2", version="1", digest="sha256:procedure"),
                            session=dict(id="00000000-0000-4000-8000-000000000001", lifecycle="running", revision=7),
                            current=dict(node=dict(graph_node_id="verify")),
                            goal_revision=2,
                            goal=dict(statement="sensitive goal text"),
                            item_values=[dict(value="sensitive evidence")],
                        ))))
                        raise SystemExit(0)
                    print(json.dumps({{"schema": "podway.error/v1", "code": "NO_ACTIVE_SESSION"}}))
                    raise SystemExit(4)
                if arguments[:4] == ["--json", "procedure", "check", "--warnings-as-errors"]:
                    print(json.dumps({{"schema": "podway.output/v2", "result": {{"valid": {podway_procedure_ok!r}, "digest": "sha256:procedure"}}}}))
                    raise SystemExit(0 if {podway_procedure_ok!r} else 1)
                raise SystemExit(2)
            raise SystemExit(2)
            """
        )
        for name in ("sanho", "mulgae", "gaori", "podway"):
            executable = self.bin_directory / name
            executable.write_text(source, encoding="utf-8")
            executable.chmod(0o755)

    def install_lora_skill(self, name: str) -> None:
        skill_directory = self.codex_home / "skills" / name
        skill_directory.mkdir(parents=True)
        skill_directory.joinpath("SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\n---\n", encoding="utf-8"
        )

    def install_managed_podway_procedures(self, tracked: bool = True) -> None:
        source = ROOT / "plugins/root-kernel/assets/podway/procedures"
        target = self.repository / ".podway/procedures"
        target.mkdir(parents=True, exist_ok=True)
        self.repository.joinpath(".podway/config.yaml").write_text(
            "schema: podway.workspace/v1\n", encoding="utf-8"
        )
        self.repository.joinpath(".podway/.gitignore").write_text(
            "runtime/\n", encoding="utf-8"
        )
        for procedure in source.glob("*.yaml"):
            shutil.copyfile(procedure, target / procedure.name)
        if tracked:
            self.git(
                "add",
                ".podway/config.yaml",
                ".podway/.gitignore",
                ".podway/procedures",
            )

    def test_missing_tools_are_a_successful_inventory_and_do_not_mutate_repository(
        self,
    ) -> None:
        before = self.git("status", "--porcelain=v1").stdout
        completed = self.inspect()
        after = self.git("status", "--porcelain=v1").stdout
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(before, after)
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["schema_version"], "root-kernel-dev-setup-inspection.v1"
        )
        self.assertEqual(
            payload["repository"]["worktree"],
            {"conflicted": 0, "staged": 0, "unstaged": 0, "untracked": 0},
        )
        self.assertEqual(payload["tools"]["sanho"]["status"], "missing")
        self.assertEqual(payload["tools"]["lora"]["status"], "missing")
        self.assertEqual(payload["tools"]["podway"]["status"], "missing")
        self.assertTrue(payload["tools"]["podway"]["setup_supported"])
        self.assertEqual(
            payload["tools"]["podway"]["integration_status"], "legacy"
        )

    def test_configured_tools_are_normalized_without_config_contents(self) -> None:
        self.install_fake_tools()
        self.repository.joinpath(".sanho.json").write_text(
            "secret-value\n", encoding="utf-8"
        )
        self.repository.joinpath(".sanho_base.json").write_text(
            "{}\n", encoding="utf-8"
        )
        self.repository.joinpath(".mulgae").mkdir()
        self.repository.joinpath(".mulgae/config.yaml").write_text(
            "credential: hidden\n", encoding="utf-8"
        )
        self.repository.joinpath(".gaori").mkdir()
        self.repository.joinpath(".gaori/tester.yaml").write_text(
            "schema_version: 2\n", encoding="utf-8"
        )
        self.repository.joinpath(".gitignore").write_text(
            ".sanho.json\n.sanho_base.json\n.mulgae/\n.gaori/\n", encoding="utf-8"
        )
        for name in ("lore-commits", "lore-query", "lore-setup"):
            self.install_lora_skill(name)
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("secret-value", completed.stdout)
        self.assertNotIn("credential: hidden", completed.stdout)
        tools = json.loads(completed.stdout)["tools"]
        self.assertEqual(tools["sanho"]["version"], "v1.2.3")
        self.assertEqual(tools["sanho"]["status"], "configured")
        self.assertEqual(tools["mulgae"]["version"], "v2.3.4")
        self.assertEqual(tools["mulgae"]["status"], "configured")
        mulgae_configuration = {
            entry["path"]: entry for entry in tools["mulgae"]["configuration"]
        }
        self.assertTrue(mulgae_configuration[".mulgae/"]["ignored"])
        self.assertEqual(
            tools["mulgae"]["probes"]["providers"]["providers"][0]["family"], "zcode"
        )
        self.assertEqual(tools["gaori"]["version"], "0.4.5")
        self.assertEqual(tools["gaori"]["status"], "configured")
        gaori_configuration = {
            entry["path"]: entry for entry in tools["gaori"]["configuration"]
        }
        self.assertTrue(gaori_configuration[".gaori/"]["ignored"])
        self.assertEqual(tools["lora"]["status"], "configured")
        self.assertTrue(tools["lora"]["lore_setup_present"])
        self.assertEqual(tools["podway"]["version"], "v0.2.7")
        self.assertTrue(tools["podway"]["version_supported"])
        self.assertEqual(tools["podway"]["integration_status"], "legacy")

    def test_matching_managed_procedures_enable_only_healthy_supported_opt_in(
        self,
    ) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        podway = json.loads(completed.stdout)["tools"]["podway"]
        platform_supported = platform.system() == "Darwin" and platform.machine() in {
            "arm64",
            "aarch64",
        }
        self.assertTrue(all(item["matches_source"] for item in podway["managed_procedures"]))
        self.assertEqual(
            podway["integration_status"],
            "opted_in" if platform_supported else "degraded",
        )
        self.assertEqual(
            podway["status"], "configured" if platform_supported else "degraded"
        )

    def test_managed_procedure_checks_report_validity_and_digest(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        managed = json.loads(completed.stdout)["tools"]["podway"]["managed_procedures"]
        self.assertEqual(
            [entry["path"] for entry in managed],
            [
                ".podway/procedures/root-kernel-task-v2.yaml",
                ".podway/procedures/root-kernel-goal-v2.yaml",
                ".podway/procedures/root-kernel-validation-v2.yaml",
            ],
        )
        for entry in managed:
            with self.subTest(path=entry["path"]):
                self.assertEqual(
                    entry["check"],
                    {
                        "attempted": True,
                        "ok": True,
                        "exit_code": 0,
                        "timed_out": False,
                        "valid": True,
                        "digest": "sha256:procedure",
                    },
                )

    def test_partial_or_drifted_managed_procedures_are_degraded(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        managed = self.repository / ".podway/procedures"
        managed.joinpath("root-kernel-task-v2.yaml").write_text(
            "schema: drifted\n", encoding="utf-8"
        )
        managed.joinpath("root-kernel-goal-v2.yaml").unlink()
        completed = self.inspect()
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertEqual(podway["integration_status"], "degraded")
        self.assertEqual(podway["status"], "degraded")

    def test_managed_procedures_without_initialized_workspace_are_degraded(self) -> None:
        self.install_fake_tools()
        source = ROOT / "plugins/root-kernel/assets/podway/procedures"
        target = self.repository / ".podway/procedures"
        target.mkdir(parents=True)
        for procedure in source.glob("*.yaml"):
            shutil.copyfile(procedure, target / procedure.name)
        completed = self.inspect()
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertEqual(podway["integration_status"], "degraded")
        self.assertEqual(podway["status"], "degraded")

    def test_unsupported_or_mixed_podway_versions_are_degraded(self) -> None:
        self.install_fake_tools(
            podway_version="v0.3.0", podway_daemon_version="0.2.7"
        )
        self.install_managed_podway_procedures()
        completed = self.inspect()
        podway = json.loads(completed.stdout)["tools"]["podway"]
        self.assertFalse(podway["version_supported"])
        self.assertFalse(podway["versions_match"])
        self.assertEqual(podway["integration_status"], "degraded")

    def test_unhealthy_daemon_doctor_or_procedure_is_degraded(self) -> None:
        cases = (
            {"podway_daemon_reachable": False},
            {"podway_doctor_ok": False},
            {"podway_procedure_ok": False},
        )
        for options in cases:
            with self.subTest(options=options):
                for executable in self.bin_directory.iterdir():
                    executable.unlink()
                self.install_fake_tools(**options)
                self.install_managed_podway_procedures()
                completed = self.inspect()
                podway = json.loads(completed.stdout)["tools"]["podway"]
                self.assertEqual(podway["integration_status"], "degraded")
                self.assertEqual(podway["status"], "degraded")

    def test_active_session_inventory_exposes_identity_without_evidence(self) -> None:
        self.install_fake_tools(podway_active_session=True)
        self.install_managed_podway_procedures()
        completed = self.inspect()
        podway = json.loads(completed.stdout)["tools"]["podway"]
        session = podway["probes"]["session_status"]["result"]
        self.assertEqual(session["procedure"]["id"], "root-kernel-task-v2")
        self.assertEqual(session["current_graph_node_id"], "verify")
        self.assertEqual(session["goal_revision"], 2)
        self.assertNotIn("sensitive goal text", completed.stdout)
        self.assertNotIn("sensitive evidence", completed.stdout)

    def test_malformed_json_and_timeout_degrade_only_the_affected_probes(self) -> None:
        self.install_fake_tools(
            malformed_sanho=True, slow_gaori=True, failing_mulgae_providers=True
        )
        completed = self.inspect(timeout_seconds=2.5)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        tools = json.loads(completed.stdout)["tools"]
        self.assertEqual(
            tools["sanho"]["probes"]["version"]["error_code"], "invalid_json"
        )
        self.assertIsNone(tools["sanho"]["version"])
        self.assertEqual(tools["sanho"]["status"], "degraded")
        self.assertTrue(tools["gaori"]["probes"]["version"]["timed_out"])
        self.assertIsNone(tools["gaori"]["version"])
        self.assertEqual(tools["gaori"]["status"], "degraded")
        self.assertEqual(tools["mulgae"]["version"], "v2.3.4")
        self.assertFalse(tools["mulgae"]["probes"]["providers"]["ok"])
        self.assertEqual(tools["mulgae"]["probes"]["providers"]["exit_code"], 4)
        self.assertEqual(
            tools["mulgae"]["probes"]["providers"]["diagnostic"]["code"],
            "readiness_unverified",
        )

    def test_worktree_counts_staged_unstaged_and_untracked_files(self) -> None:
        self.repository.joinpath("tracked.txt").write_text("staged\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.repository.joinpath("tracked.txt").write_text(
            "unstaged\n", encoding="utf-8"
        )
        self.repository.joinpath("untracked.txt").write_text("new\n", encoding="utf-8")
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        counts = json.loads(completed.stdout)["repository"]["worktree"]
        self.assertEqual(
            counts, {"conflicted": 0, "staged": 1, "unstaged": 1, "untracked": 1}
        )

    def test_renamed_files_are_counted_once_as_staged(self) -> None:
        self.git("mv", "tracked.txt", "renamed.txt")
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        counts = json.loads(completed.stdout)["repository"]["worktree"]
        self.assertEqual(
            counts, {"conflicted": 0, "staged": 1, "unstaged": 0, "untracked": 0}
        )

    def test_repository_reports_root_branch_and_upstream_state(self) -> None:
        default_branch = self.git("branch", "--show-current").stdout.strip()
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        repository = json.loads(completed.stdout)["repository"]
        self.assertEqual(repository["root"], str(self.repository.resolve()))
        self.assertEqual(repository["branch"], default_branch)
        self.assertIsNone(repository["upstream"])
        self.git("branch", "other")
        self.git("branch", "--set-upstream-to=other", default_branch)
        tracking = json.loads(self.inspect().stdout)["repository"]
        self.assertEqual(tracking["branch"], default_branch)
        self.assertEqual(tracking["upstream"], "other")
        self.git("checkout", "--quiet", "--detach")
        head = self.git("rev-parse", "--short", "HEAD").stdout.strip()
        detached = json.loads(self.inspect().stdout)["repository"]
        self.assertEqual(detached["branch"], head)
        self.assertIsNone(detached["upstream"])

    def test_invalid_lora_frontmatter_is_degraded(self) -> None:
        self.install_lora_skill("lore-commits")
        invalid_directory = self.codex_home / "skills" / "lore-query"
        invalid_directory.mkdir(parents=True)
        invalid_directory.joinpath("SKILL.md").write_text(
            "---\nname: wrong-name\ndescription: Test skill.\n---\n", encoding="utf-8"
        )
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lora = json.loads(completed.stdout)["tools"]["lora"]
        self.assertEqual(lora["status"], "degraded")
        self.assertFalse(lora["installed"])
        self.assertFalse(lora["skills"]["lore-query"]["frontmatter_valid"])

    def test_conflicted_files_are_counted_separately(self) -> None:
        default_branch = self.git("branch", "--show-current").stdout.strip()
        self.git("checkout", "--quiet", "-b", "other")
        self.repository.joinpath("tracked.txt").write_text("other\n", encoding="utf-8")
        self.git("commit", "--quiet", "-am", "Other")
        self.git("checkout", "--quiet", default_branch)
        self.repository.joinpath("tracked.txt").write_text(
            "default\n", encoding="utf-8"
        )
        self.git("commit", "--quiet", "-am", "Default")
        self.git("merge", "other", check=False)
        completed = self.inspect()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        counts = json.loads(completed.stdout)["repository"]["worktree"]
        self.assertEqual(counts["conflicted"], 1)
        self.assertEqual(counts["staged"], 0)
        self.assertEqual(counts["unstaged"], 0)

    def test_invalid_and_non_git_paths_return_structured_errors(self) -> None:
        invalid = self.inspect(self.base / "missing")
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(
            json.loads(invalid.stdout)["error"]["code"], "invalid_repository_path"
        )
        non_git = self.base / "not-git"
        non_git.mkdir()
        outside = self.inspect(non_git)
        self.assertEqual(outside.returncode, 2)
        self.assertEqual(
            json.loads(outside.stdout)["error"]["code"], "not_a_git_repository"
        )

    def test_missing_repository_argument_returns_a_json_error_envelope(self) -> None:
        completed = self.run_script()
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "")
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["schema_version"], "root-kernel-dev-setup-inspection.v1"
        )
        self.assertEqual(payload["error"]["code"], "invalid_arguments")
        self.assertIn("--repository", payload["error"]["message"])

    def test_non_positive_timeout_is_rejected_before_inspection(self) -> None:
        completed = self.inspect(timeout_seconds=0)
        self.assertEqual(completed.returncode, 2)
        error = json.loads(completed.stdout)["error"]
        self.assertEqual(error["code"], "invalid_arguments")
        self.assertIn("greater than zero", error["message"])

    def test_execution_failures_are_reported_without_json_parsing(self) -> None:
        with mock.patch(
            "inspect_tools.subprocess.run", side_effect=OSError("boom")
        ) as patched_run:
            raw_probe = inspect_tools.run_command(["anything"], self.repository, 1.0)
        self.assertEqual(patched_run.call_count, 1)
        self.assertTrue(raw_probe["attempted"])
        self.assertFalse(raw_probe["ok"])
        self.assertIsNone(raw_probe["exit_code"])
        self.assertFalse(raw_probe["timed_out"])
        self.assertEqual(raw_probe["error_code"], "execution_failed")
        self.assertEqual(raw_probe["error_type"], "OSError")
        probe = inspect_tools.parse_json_probe(raw_probe)
        self.assertEqual(probe["error_code"], "execution_failed")
        self.assertNotIn("result", probe)

    def test_normalized_mulgae_config_keeps_identity_fields_and_reason_codes(
        self,
    ) -> None:
        configured = inspect_tools.normalize_mulgae_config(
            {
                "attempted": True,
                "ok": True,
                "exit_code": 0,
                "timed_out": False,
                "result": {
                    "result": {
                        "kind": "configuration",
                        "config_uri": ".mulgae/config.yaml",
                        "config_sha256": "abc",
                        "credential": "hidden",
                    }
                },
            }
        )
        self.assertEqual(
            configured,
            {
                "attempted": True,
                "ok": True,
                "exit_code": 0,
                "timed_out": False,
                "result": {
                    "kind": "configuration",
                    "config_uri": ".mulgae/config.yaml",
                    "config_sha256": "abc",
                },
            },
        )
        rejected = inspect_tools.normalize_mulgae_config(
            {
                "attempted": True,
                "ok": False,
                "exit_code": 3,
                "timed_out": False,
                "result": {
                    "result": {"kind": "configuration", "config_uri": None},
                    "reasons": [
                        {"code": "config_unreadable", "message": "hidden detail"},
                        {"message": "code is missing"},
                        "not-a-mapping",
                    ],
                },
            }
        )
        self.assertEqual(
            rejected,
            {
                "attempted": True,
                "ok": False,
                "exit_code": 3,
                "timed_out": False,
                "result": {"kind": "configuration"},
                "reason_codes": ["config_unreadable"],
            },
        )
        failed = inspect_tools.normalize_mulgae_config(
            {
                "attempted": True,
                "ok": False,
                "exit_code": None,
                "timed_out": False,
                "error_code": "execution_failed",
            }
        )
        self.assertEqual(
            failed,
            {
                "attempted": True,
                "ok": False,
                "exit_code": None,
                "timed_out": False,
                "error_code": "execution_failed",
            },
        )

    def test_supported_platform_opt_in_is_verified_on_any_host(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures()
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(self.repository.resolve(), 3.0)
        self.assertEqual(
            podway["platform"],
            {"system": "Darwin", "machine": "arm64", "supported": True},
        )
        self.assertTrue(podway["version_supported"])
        self.assertTrue(podway["versions_match"])
        self.assertEqual(podway["integration_status"], "opted_in")
        self.assertEqual(podway["status"], "configured")

    def test_untracked_managed_procedures_are_degraded_not_opted_in(self) -> None:
        self.install_fake_tools()
        self.install_managed_podway_procedures(tracked=False)
        with (
            mock.patch.dict(os.environ, self.environment),
            mock.patch("inspect_tools.platform.system", return_value="Darwin"),
            mock.patch("inspect_tools.platform.machine", return_value="arm64"),
        ):
            podway = inspect_tools.inspect_podway(self.repository.resolve(), 3.0)
        for entry in podway["managed_procedures"]:
            self.assertTrue(entry["present"])
            self.assertTrue(entry["matches_source"])
            self.assertFalse(entry["tracked"])
        self.assertEqual(podway["integration_status"], "degraded")
        self.assertEqual(podway["status"], "degraded")


if __name__ == "__main__":
    unittest.main()
