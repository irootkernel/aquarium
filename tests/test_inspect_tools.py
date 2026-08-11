from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/root-kernel/skills/dev-setup/scripts/inspect_tools.py"


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

    def inspect(
        self, repository: Path | None = None, timeout_seconds: float = 3.0
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repository",
                str(repository or self.repository),
                "--timeout-seconds",
                str(timeout_seconds),
            ],
            env=self.environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def install_fake_tools(
        self,
        malformed_sanho: bool = False,
        slow_gaori: bool = False,
        failing_mulgae_providers: bool = False,
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
                        time.sleep(2)
                    print(json.dumps({{"name": "gaori", "version": "0.4.5"}}))
                    raise SystemExit(0)
                print("generic-v1")
                raise SystemExit(0)
            if name == "podway":
                print(json.dumps({{"name": "podway", "version": "v0.6.7"}}))
                raise SystemExit(0)
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
        self.assertEqual(payload["tools"]["podway"]["status"], "planned")
        self.assertFalse(payload["tools"]["podway"]["setup_supported"])

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
        self.assertEqual(tools["podway"]["version"], "v0.6.7")
        self.assertEqual(tools["podway"]["status"], "planned")

    def test_malformed_json_and_timeout_degrade_only_the_affected_probes(self) -> None:
        self.install_fake_tools(
            malformed_sanho=True, slow_gaori=True, failing_mulgae_providers=True
        )
        completed = self.inspect(timeout_seconds=0.5)
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


if __name__ == "__main__":
    unittest.main()
