from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
RECIPES_ROOT = REPOSITORY / "tests/vm/recipes"
STABLE_PROFILE = (
    REPOSITORY
    / "tests/vm/profiles"
    / "proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0.json"
)
LAUNCHER = REPOSITORY / "tests/unit/vm_guest_simulation_launcher.py"
FIXTURES = REPOSITORY / "tests/unit/fixtures/vm_simulation"
SIMULATED_UUID = "11111111-2222-3333-4444-555555555555"
SEQUENCE_LOG: list[dict] = []


def driver_artifact_digest(root: Path) -> str:
    """The unchanged driver's artifact_digest algorithm."""
    payload = hashlib.sha256()
    for name, value in sorted(_driver_files(root).items()):
        payload.update(name.encode("utf-8") + b"\0")
        payload.update(bytes.fromhex(value.removeprefix("sha256:")) + b"\n")
    return "sha256:" + payload.hexdigest()


def _driver_files(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        digest_value = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        if path.parent.name == "__pycache__":
            continue
        result[relative] = digest_value
    return result


def digest(root: Path) -> str:
    payload = hashlib.sha256(b"haepari-tree-sha256/v1\x00")
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix().encode()
        content = path.read_bytes()
        payload.update(len(relative).to_bytes(8, "big"))
        payload.update(relative)
        payload.update(b"\x01" if path.stat().st_mode & 0o111 else b"\x00")
        payload.update(len(content).to_bytes(8, "big"))
        payload.update(hashlib.sha256(content).digest())
    return payload.hexdigest()


class SequenceSimulationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-seq-sim-")).resolve()
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        cls.home = cls.work / "home"
        cls.codex_state = cls.work / "codex-state.json"
        cls.identity = cls.work / "identity.json"
        cls.identity.write_text(
            json.dumps(
                {
                    "platform": "Darwin",
                    "hypervisor_present": "1",
                    "hardware_uuid": SIMULATED_UUID,
                }
            )
        )
        stub = cls.work / "stub-repo"
        greeting = stub / "tests/vm/fixtures/greeting"
        shutil.copytree(REPOSITORY / "tests/vm/fixtures/greeting", greeting)
        (greeting / "tests/unit/__init__.py").write_text("")
        (greeting / "tests/__init__.py").write_text("")
        (stub / "tests/vm").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            REPOSITORY / "tests/vm/run_acceptance.py",
            stub / "tests/vm/run_acceptance.py",
        )
        shutil.copyfile(
            REPOSITORY / "tests/vm/native_observation.py",
            stub / "tests/vm/native_observation.py",
        )
        for argv in (
            ["init", "-q"],
            ["config", "user.name", "T"],
            ["config", "user.email", "t@example.invalid"],
            ["add", "."],
            ["commit", "-qm", "stub"],
        ):
            subprocess.run(["git", "-C", str(stub), *argv], check=True)
        cls.git_sha = subprocess.run(
            ["git", "-C", str(stub), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        def plugin_tree(target: Path, version: str) -> Path:
            (target / ".agents/plugins").mkdir(parents=True)
            (target / ".agents/plugins/marketplace.json").write_text(
                json.dumps({"name": "root-kernel"})
            )
            plugin = target / "plugins/aquarium"
            (plugin / ".codex-plugin").mkdir(parents=True)
            (plugin / ".codex-plugin/plugin.json").write_text(
                json.dumps({"version": version})
            )
            status = plugin / "tools/aquarium-status"
            status.mkdir(parents=True)
            shutil.copyfile(FIXTURES / "fake_installer.py", status / "install.py")
            (status / "plugin.json").write_text(json.dumps({"version": version}))
            (status / "requirements.txt").write_text("")
            assets = plugin / "assets/podway/procedures"
            assets.mkdir(parents=True)
            (assets / "aquarium-task-v2.yaml").write_text("procedure: stub\n")
            return target

        cls.prior = plugin_tree(cls.work / "prior", "0.1.21")
        cls.candidate = plugin_tree(cls.work / "cand", f"0.1.21-dev.{cls.git_sha[:12]}")
        # Committed plugin payload so the unchanged verify_candidate passes.
        # Like the real producer, the stub commits the base version and the
        # sealed candidate stamps the dev version over the committed bytes.
        shutil.copytree(cls.candidate / ".agents", stub / ".agents")
        shutil.copytree(cls.candidate / "plugins", stub / "plugins")
        stub_plugin = stub / "plugins/aquarium/.codex-plugin/plugin.json"
        stub_plugin.write_text(json.dumps({"version": "0.1.21"}, indent=2) + "\n")
        for argv in (["add", "."], ["commit", "-qm", "plugin payload"]):
            subprocess.run(["git", "-C", str(stub), *argv], check=True)
        cls.git_sha = subprocess.run(
            ["git", "-C", str(stub), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        cls.candidate = cls.work / "cand-final"
        shutil.copytree(stub / ".agents", cls.candidate / ".agents")
        shutil.copytree(stub / "plugins", cls.candidate / "plugins")
        final_plugin = cls.candidate / "plugins/aquarium/.codex-plugin/plugin.json"
        final_plugin.write_text(
            json.dumps({"version": f"0.1.21-dev.{cls.git_sha[:12]}"}, indent=2) + "\n"
        )
        cls._seed_persistent_home()

    @classmethod
    def _seed_persistent_home(cls):
        home = cls.home
        home.mkdir(parents=True, exist_ok=True)
        foreign_root = cls.work / "foreign-marketplace-root"
        plugin = foreign_root / "plugins/aquarium/.codex-plugin"
        plugin.mkdir(parents=True, exist_ok=True)
        (plugin / "plugin.json").write_text(
            json.dumps({"version": "0.1.20-dev.63bbcf7e4db8"})
        )
        registrations = [
            {
                "name": "root-kernel",
                "root": str(foreign_root),
                "marketplaceSource": {
                    "sourceType": "local",
                    "source": str(foreign_root),
                },
            },
            {"name": "openai-bundled", "root": "/synthetic/bundled"},
            {"name": "openai-curated", "root": "/synthetic/curated"},
        ]
        installed = [
            {
                "pluginId": "aquarium@root-kernel",
                "name": "aquarium",
                "marketplaceName": "root-kernel",
                "version": "0.1.20-dev.63bbcf7e4db8",
                "installed": True,
                "enabled": True,
                "source": {
                    "source": "local",
                    "path": str(foreign_root / "plugins/aquarium"),
                },
                "marketplaceSource": {
                    "sourceType": "local",
                    "source": str(foreign_root),
                },
                "installPolicy": "AVAILABLE",
                "authPolicy": "ON_INSTALL",
            }
        ]
        cls.codex_state.write_text(
            json.dumps({"marketplaces": registrations, "installed": installed})
        )
        cache = home / ".codex/plugins/cache"
        for name in (
            "created-by-me-remote",
            "openai-bundled",
            "openai-curated-remote",
            "openai-primary-runtime",
        ):
            (cache / name).mkdir(parents=True, exist_ok=True)
            (cache / name / "plugin.txt").write_text(name)
        # Section F live layout: the standalone release carries a
        # `codex -> bin/codex` symlink, the bundled cache carries a
        # `chrome/latest` symlink, and Codex keeps mutable internal state
        # beside the cache under `.codex/plugins/.plugin-appserver`.
        release = (
            home / ".codex/packages/standalone/releases/0.164.0-aarch64-apple-darwin"
        )
        (release / "bin").mkdir(parents=True)
        (release / "bin/codex").write_text(
            "#!/bin/sh\n# fake standalone codex binary\n"
        )
        (release / "manifest.json").write_text("{}\n")
        (release / "codex").symlink_to("bin/codex")
        (home / ".codex/packages/standalone/current").symlink_to(
            "releases/0.164.0-aarch64-apple-darwin"
        )
        chrome = cache / "openai-bundled/chrome"
        (chrome / "0.164.0").mkdir(parents=True)
        (chrome / "0.164.0/chrome.bin").write_text("chrome\n")
        (chrome / "latest").symlink_to("0.164.0")
        appserver = home / ".codex/plugins/.plugin-appserver/codex-cli"
        appserver.mkdir(parents=True, exist_ok=True)
        (appserver / "state.json").write_text("{}\n")
        for name in ("deslop", "use-gaori", "use-podway"):
            skill = home / ".agents/skills" / name
            skill.mkdir(parents=True, exist_ok=True)
            (skill / "SKILL.md").write_text(f"# {name}\n")
        runtime = home / ".aquarium/status-runtime"
        versions = runtime / "versions"
        versions.mkdir(parents=True, exist_ok=True)
        (runtime / "install.lock").write_text("")
        (home / ".aquarium/status.yaml").write_text("status: synthetic\n")
        (home / ".aquarium/status.lock").write_text("")
        for backup in (
            "status-backup-epic024-31ba3114d3d8",
            "status-backup-epic024-v017",
        ):
            directory = home / ".aquarium" / backup
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "backup.json").write_text("{}")
        for index in range(3):
            name = f"{'a' * 64}-py3.14" + (f"-r{'b' * 32}" if index else "")
            generation = versions / name
            generation.mkdir(parents=True, exist_ok=True)
            (generation / "runtime.json").write_text(
                json.dumps(
                    {
                        "schema": "aquarium-status-runtime/v1",
                        "source_sha256": "c" * 64,
                        "plugin_version": f"v0.1.1{7 - index}",
                        "python_version": "3.14.8",
                        "python_executable": "/synthetic/python",
                        "python_executable_sha256": "d" * 64,
                        "requirements_sha256": "0" * 64,
                        "files": {},
                        "dependency_files": {},
                    }
                )
            )
        (runtime / "current").write_text(f"versions/{'a' * 64}-py3.14\n")
        launcher = home / ".local/bin/aquarium-status"
        launcher.parent.mkdir(parents=True, exist_ok=True)
        launcher.write_text("#!/bin/sh\n# aquarium-status managed launcher v1\n")
        launcher.chmod(0o755)

    def job_root(self, name: str) -> Path:
        job = self.work / f"job-{name}"
        if job.exists():
            shutil.rmtree(job)
        harness = job / "harness/tests/vm/recipes"
        harness.mkdir(parents=True)
        for source in sorted(RECIPES_ROOT.rglob("*")):
            if source.is_file() and "__pycache__" not in source.parts:
                target = harness / source.relative_to(RECIPES_ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        shutil.copytree(self.prior, job / "prior-artifact")
        shutil.copytree(self.candidate, job / "artifact")
        subprocess.run(
            [
                "git",
                "-C",
                str(self.work / "stub-repo"),
                "bundle",
                "create",
                str(job / "checkout.bundle"),
                "--all",
            ],
            check=True,
            capture_output=True,
        )
        profiles = job / "profile"
        profiles.mkdir()
        shutil.copyfile(STABLE_PROFILE, profiles / "stable.json")
        (profiles / "candidate.json").write_text(
            json.dumps(
                {
                    **json.loads(STABLE_PROFILE.read_text()),
                    "profile_id": f"sim-candidate-{self.git_sha[:12]}",
                }
            )
        )
        lock = job / "requirements/fixture-requirements.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("pytest==9.1.1 --hash=sha256:" + "a" * 64 + "\n")
        (job / "artifact-manifest.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium-dev-artifact-manifest/v1",
                    "git_sha": self.git_sha,
                    "development_version": f"v0.1.21-dev.{self.git_sha[:12]}",
                    "artifact_path": "artifact",
                    "sha256": driver_artifact_digest(self.candidate),
                },
                indent=2,
            )
            + "\n"
        )
        (job / "harness/inputs.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium.vm-host-inputs/v1",
                    "candidate": {
                        "git_sha": self.git_sha,
                        "base_commit": self.git_sha,
                        "dirty_harness_snapshot": False,
                        "development_version": f"v0.1.21-dev.{self.git_sha[:12]}",
                        "artifact_tree_sha256": digest(self.candidate),
                    },
                    "prior": {
                        "version": "0.1.21",
                        "tag": "v0.1.21",
                        "tag_commit": "1" * 40,
                        "artifact_tree_sha256": digest(self.prior),
                    },
                    "harness_tree_sha256": digest(harness),
                    "fixture_requirements": "requirements/fixture-requirements.lock",
                },
                indent=2,
            )
            + "\n"
        )
        return job

    def base_env(self) -> dict:
        return {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.home),
            "AQUARIUM_GUEST_HOME": str(self.home),
            "AQUARIUM_GUEST_PYTHON": str(FIXTURES / "fake_python.py"),
            "AQUARIUM_DRIVER_PYTHON": sys.executable,
            "AQUARIUM_GUEST_CODEX": str(FIXTURES / "fake_codex.py"),
            "AQUARIUM_GUEST_PODWAY": "/usr/bin/true",
            "AQUARIUM_EXPECTED_GUEST_UUID": SIMULATED_UUID,
            "AQUARIUM_MARKETPLACE_NAME": "root-kernel",
            "FAKE_CODEX_STATE": str(self.codex_state),
            "FAKE_PYTHON_REAL": sys.executable,
            "FAKE_PYTHON_BINDING": str(FIXTURES / "fake_python.py"),
        }

    def run_suite(
        self, job: Path, suite: str, *extra: str, stage: int = 0, **extra_env: str
    ) -> int:
        environment = self.base_env()
        environment.update({key: str(value) for key, value in extra_env.items()})
        environment.update(
            {
                "HAEPARI_PARENT_CONTEXT": json.dumps(
                    [
                        {
                            "job_id": f"sim-{suite}",
                            "lease_generation": 1,
                            "nonce": "ab" * 32,
                        }
                    ]
                ),
                "AQUARIUM_VM_JOB_ID": f"sim-{suite}",
                "AQUARIUM_VM_LEASE_GENERATION": "1",
                "FAKE_INSTALLER_STAGE_SECONDS": str(stage),
            }
        )
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(LAUNCHER),
                str(self.identity),
                str(job / "harness"),
                "--suite",
                suite,
                *extra,
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        SEQUENCE_LOG.append(
            {
                "suite": suite,
                "extra": list(extra),
                "exit": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-500:],
            }
        )
        return result.returncode

    def result_of(self, job: Path, suite: str) -> dict:
        return json.loads((job / "results" / suite / "result.json").read_text())

    def test_approved_sequence_over_one_persistent_home(self):
        state = json.loads(self.codex_state.read_text())
        self.assertEqual(state["installed"][0]["pluginId"], "aquarium@root-kernel")
        base = self.job_root("base")
        self.assertEqual(self.run_suite(base, "baseline"), 0, SEQUENCE_LOG[-1])
        document = self.result_of(base, "baseline")
        self.assertEqual(document["outcome"], "pass")
        self.assertEqual(document["consumer_cleanup"], "verified")
        self.assertEqual(
            document["normalization"]["installed_row"]["version"],
            "0.1.20-dev.63bbcf7e4db8",
        )
        install = self.job_root("install")
        self.assertEqual(self.run_suite(install, "install"), 0, SEQUENCE_LOG[-1])
        installed = self.result_of(install, "install")
        self.assertEqual(installed["outcome"], "pass")
        self.assertEqual(installed["consumer_cleanup"], "verified")
        self.assertEqual(installed["cleanup_problems"], [])
        self.assertTrue(installed["cleanup"]["marketplace"]["removed"])
        upgrade = self.job_root("upgrade")
        self.assertEqual(self.run_suite(upgrade, "upgrade"), 0, SEQUENCE_LOG[-1])
        upgraded = self.result_of(upgrade, "upgrade")
        self.assertEqual(upgraded["outcome"], "pass")
        self.assertEqual(upgraded["consumer_cleanup"], "verified")
        self.assertFalse(upgraded["runtime_observation"]["reused"])
        migration = self.job_root("migration")
        self.assertEqual(
            self.run_suite(migration, "migration-failure", stage=10),
            0,
            SEQUENCE_LOG[-1],
        )
        migrated = self.result_of(migration, "migration-failure")
        self.assertEqual(migrated["outcome"], "pass")
        self.assertEqual(migrated["consumer_cleanup"], "verified")
        probe = self.job_root("probe")
        self.assertEqual(
            self.run_suite(probe, "immutability-probe"), 0, SEQUENCE_LOG[-1]
        )
        guard = self.job_root("guard")
        self.assertEqual(
            self.run_suite(guard, "guard-failure-probe"), 1, SEQUENCE_LOG[-1]
        )
        guard_result = self.result_of(guard, "guard-failure-probe")
        self.assertEqual(guard_result["consumer_cleanup"], "failed")
        self.assertTrue(guard_result["guard_rejected"])
        self.assertTrue((self.home / ".aquarium-vm-probe-leftover").is_file())
        hold = self.job_root("hold")
        self.assertEqual(
            self.run_suite(hold, "manual-hold", "--phase", "smoke"), 0, SEQUENCE_LOG[-1]
        )
        smoke = json.loads((hold / "results/manual-hold/smoke.json").read_text())
        self.assertTrue(smoke["successor_repair"]["removed"])
        self.assertFalse((self.home / ".aquarium-vm-probe-leftover").exists())
        self.assertEqual(
            self.run_suite(hold, "manual-hold", "--phase", "consumer-cleanup"),
            0,
            SEQUENCE_LOG[-1],
        )
        final = json.loads(self.codex_state.read_text())
        registered = {
            row["name"]: row.get("marketplaceSource", {}).get("source", "")
            for row in final["marketplaces"]
        }
        # Final state: J-M's cleanup restored prior-stable, J-H touched
        # no product state, and unrelated guest state is preserved.
        self.assertTrue(registered["root-kernel"].endswith("/prior-artifact"))
        self.assertTrue(
            (self.home / ".aquarium-vm-marketplaces/prior-artifact").is_dir()
        )
        self.assertIn("openai-bundled", registered)
        self.assertTrue((self.home / ".aquarium/status.yaml").is_file())
        self.assertTrue((self.home / ".aquarium/status-backup-epic024-v017").is_dir())
        self.assertIn("use-podway", sorted(os.listdir(self.home / ".agents/skills")))
        self.assertIn(
            "openai-bundled", sorted(os.listdir(self.home / ".codex/plugins/cache"))
        )

    def test_c14_codex_internal_state_stays_out_of_scope(self):
        job = self.job_root("appserver")
        self.assertEqual(self.run_suite(job, "baseline"), 0, SEQUENCE_LOG[-1])
        result = self.result_of(job, "baseline")
        self.assertEqual(result["outcome"], "pass")
        # The symlinked standalone release must feed the component digest
        # (the c13 crash) instead of failing the suite.
        self.assertEqual(
            result["identities"]["codex"]["current_target"],
            "releases/0.164.0-aarch64-apple-darwin",
        )
        self.assertIsNotNone(result["identities"]["codex"]["release_digest"])
        # The fake plugin add mutated `.plugin-appserver` — Codex-internal
        # state beside the cache — and the baseline still passes because no
        # inventory scope covers it.
        marker = (
            self.home / ".codex/plugins/.plugin-appserver/codex-cli/last-install.json"
        )
        self.assertTrue(marker.is_file())
        for phase in ("before", "candidate"):
            document = json.loads(
                (job / "results/baseline" / f"inventory-{phase}.json").read_text()
            )
            for entry in document["entries"]:
                self.assertNotIn(".plugin-appserver", entry["relative_path"])

    def test_c14_fifo_in_scope_gives_non_pass_result(self):
        fifo = self.home / ".agents/skills/stuck-pipe"
        os.mkfifo(fifo)
        try:
            job = self.job_root("fifo")
            exit_code = self.run_suite(job, "baseline")
            document = self.result_of(job, "baseline")
            self.assertEqual(document["outcome"], "fail")
            self.assertIn("unsafe inventoried scope", document["problem"])
            self.assertIn("special file inside inventory scope", document["problem"])
            self.assertEqual(exit_code, 1)
        finally:
            fifo.unlink()

    def test_c17_fifo_in_prior_marketplace_fails_hold_before_beginning(self):
        # The Evaluator's regression: a special file inside the owned prior
        # marketplace must give J-H a structured fail result with the
        # retained problem, never a traceback, and the hold must not begin.
        self._c10_establish_prior_for_hold("c17-prior")
        fifo = self.home / ".aquarium-vm-marketplaces/prior-artifact/stuck-pipe"
        os.mkfifo(fifo)
        try:
            hold = self.job_root("c17-prior-hold")
            exit_code = self.run_suite(hold, "manual-hold", "--phase", "smoke")
            document = self.result_of(hold, "manual-hold")
            self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
            self.assertEqual(document["outcome"], "fail")
            self.assertTrue(
                any(
                    "prior marketplace tree digest failed" in problem
                    for problem in document["retained_problems"]
                ),
                document["retained_problems"],
            )
            self.assertIn("the hold did not begin", document["note"])
            self.assertFalse((hold / "results/manual-hold/smoke.json").is_file())
            # Fail closed: the unsafe directory is preserved, not deleted.
            self.assertTrue(fifo.exists() or fifo.is_symlink())
        finally:
            fifo.unlink()

    def test_c17_fifo_in_owned_marketplace_preserved_and_reported(self):
        # A special file inside an owned harness marketplace before J-M:
        # the ownership check fails closed as not owned, the suite writes a
        # structured non-pass result, and the directory survives untouched.
        self._c10_establish_prior_for_hold("c17-owned")
        fifo = self.home / ".aquarium-vm-marketplaces/prior-artifact/stuck-pipe"
        os.mkfifo(fifo)
        try:
            job = self.job_root("c17-owned-migration")
            exit_code = self.run_suite(job, "migration-failure")
            document = self.result_of(job, "migration-failure")
            self.assertEqual(exit_code, 2, SEQUENCE_LOG[-1])
            self.assertEqual(document["outcome"], "incomplete")
            self.assertIn("foreign harness marketplace preserved", document["problem"])
            prior = self.home / ".aquarium-vm-marketplaces/prior-artifact"
            self.assertTrue(prior.is_dir())
            self.assertTrue(fifo.exists() or fifo.is_symlink())
            self.assertTrue((prior / "plugins/aquarium").is_dir())
        finally:
            fifo.unlink()

    def test_c18_preserved_candidate_cleanup_fails_install(self):
        # A foreign symlink inside the installed candidate marketplace
        # (outside plugins/aquarium, planted by the fake codex's plugin add)
        # makes the final cleanup preserve the directory; J-A must then
        # report fail with consumer_cleanup failed, naming the preserved
        # directory and the still-installed plugin and registration — never
        # pass with verified over leftover product.
        self._c10_establish_prior_for_hold("c18-base")
        job = self.job_root("c18-symlink")
        exit_code = self.run_suite(job, "install", FAKE_CODEX_PLANT_SYMLINK="1")
        document = self.result_of(job, "install")
        self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
        self.assertEqual(document["outcome"], "fail")
        self.assertEqual(document["consumer_cleanup"], "failed")
        problems = document["cleanup_problems"]
        candidate = self.home / ".aquarium-vm-marketplaces/artifact"
        self.assertTrue(
            any(str(candidate) in problem for problem in problems), problems
        )
        self.assertTrue(
            any("still installed" in problem for problem in problems), problems
        )
        self.assertTrue(
            any("still registered" in problem for problem in problems), problems
        )
        self.assertTrue(document["cleanup"]["marketplace"].get("preserved"))
        # The preserved directory and its symlink are untouched.
        self.assertTrue((candidate / "planted-link").is_symlink())
        self.assertTrue((candidate / "plugins/aquarium").is_dir())
        # Test-owned fault cleanup: remove only the planted symlink this
        # test created, so later suites see sane ownership again.
        (candidate / "planted-link").unlink()

    def test_c20_dangling_sidecar_symlink_is_residue(self):
        # A dangling owner-sidecar symlink is residue only a
        # type-independent absence check can see: J-A must name it, report
        # consumer_cleanup failed, and preserve the corrupted state.
        self._c10_establish_prior_for_hold("c20-base")
        job = self.job_root("c20-dangling")
        exit_code = self.run_suite(job, "install", FAKE_CODEX_DANGLING_SIDECAR="1")
        document = self.result_of(job, "install")
        self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
        self.assertEqual(document["outcome"], "fail")
        self.assertEqual(document["consumer_cleanup"], "failed")
        sidecar = self.home / ".aquarium-vm-marketplaces/artifact.owner.json"
        self.assertTrue(
            any(str(sidecar) in problem for problem in document["cleanup_problems"]),
            document["cleanup_problems"],
        )
        # Nothing was deleted: the dangling link and the directory survive.
        self.assertTrue(sidecar.is_symlink())
        self.assertFalse(sidecar.exists())
        self.assertTrue(
            (self.home / ".aquarium-vm-marketplaces/artifact/plugins/aquarium").is_dir()
        )
        # Test-owned fault cleanup: remove only the dangling symlink.
        sidecar.unlink()

    _C36_LEFTOVER_BYTES = b"declared leftover bytes\n"

    def _seed_probe_leftover(self) -> None:
        # Seed J-F's declared leftover with known bytes BEFORE the smoke
        # run, so a rejected hold can be checked for leaving it untouched.
        (self.home / ".aquarium-vm-probe-leftover").write_bytes(
            self._C36_LEFTOVER_BYTES
        )

    def _assert_hold_not_begun(self, job: Path, needle: str) -> None:
        # The caller seeded the leftover before the smoke run; a rejected
        # hold must leave it untouched, create no fixture, write no
        # smoke.json and report the repair as not run.
        leftover = self.home / ".aquarium-vm-probe-leftover"
        document = self.result_of(job, "manual-hold")
        self.assertEqual(document["outcome"], "fail")
        self.assertEqual(document["consumer_cleanup"], "unverified")
        self.assertIn("the hold did not begin", document["note"])
        self.assertTrue(
            any(needle in problem for problem in document["retained_problems"]),
            document["retained_problems"],
        )
        self.assertFalse((job / "results/manual-hold/smoke.json").is_file())
        self.assertFalse((job / "manual-hold-fixture").exists())
        self.assertEqual(leftover.read_bytes(), self._C36_LEFTOVER_BYTES)
        repair = document["successor_repair"]
        self.assertFalse(repair["removed"])
        self.assertTrue(repair["probe_leftover_present"])
        leftover.unlink()

    def test_c35_prior_plugin_absent_at_smoke_fails_hold(self):
        self._c10_establish_prior_for_hold("c35-absent")
        self._seed_probe_leftover()
        original = self.codex_state.read_text()
        state = json.loads(original)
        state["installed"] = []
        self.codex_state.write_text(json.dumps(state))
        try:
            job = self.job_root("c35-absent-hold")
            exit_code = self.run_suite(job, "manual-hold", "--phase", "smoke")
            self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
            self._assert_hold_not_begun(job, "prior plugin is not installed")
        finally:
            self.codex_state.write_text(original)

    def test_c35_prior_plugin_wrong_version_at_smoke_fails_hold(self):
        self._c10_establish_prior_for_hold("c35-wrongver")
        self._seed_probe_leftover()
        original = self.codex_state.read_text()
        state = json.loads(original)
        state["installed"][0]["version"] = "0.1.30-other"
        self.codex_state.write_text(json.dumps(state))
        try:
            job = self.job_root("c35-wrongver-hold")
            exit_code = self.run_suite(job, "manual-hold", "--phase", "smoke")
            self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
            self._assert_hold_not_begun(job, "prior plugin version is 0.1.30-other")
        finally:
            self.codex_state.write_text(original)

    def test_c35_registration_elsewhere_at_smoke_fails_hold(self):
        self._c10_establish_prior_for_hold("c35-elsewhere")
        self._seed_probe_leftover()
        original = self.codex_state.read_text()
        state = json.loads(original)
        for row in state["marketplaces"]:
            if row["name"] == "root-kernel":
                row["root"] = "/synthetic/elsewhere"
                row["marketplaceSource"]["source"] = "/synthetic/elsewhere"
        self.codex_state.write_text(json.dumps(state))
        try:
            job = self.job_root("c35-elsewhere-hold")
            exit_code = self.run_suite(job, "manual-hold", "--phase", "smoke")
            self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
            self._assert_hold_not_begun(job, "expected the prior harness marketplace")
        finally:
            self.codex_state.write_text(original)

    def test_c35_runtime_not_prior_at_smoke_fails_hold(self):
        self._c10_establish_prior_for_hold("c35-runtime")
        self._seed_probe_leftover()
        current = self.home / ".aquarium/status-runtime/current"
        original = current.read_bytes()
        current.write_text(f"versions/{'a' * 64}-py3.14\n")
        try:
            job = self.job_root("c35-runtime-hold")
            exit_code = self.run_suite(job, "manual-hold", "--phase", "smoke")
            self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
            self._assert_hold_not_begun(job, "runtime generation binds")
        finally:
            current.write_bytes(original)

    def test_c35_prior_state_drift_between_phases_fails_cleanup(self):
        self._c10_establish_prior_for_hold("c35-drift")
        hold = self.job_root("c35-drift-hold")
        self.assertEqual(
            self.run_suite(hold, "manual-hold", "--phase", "smoke"),
            0,
            SEQUENCE_LOG[-1],
        )
        original = self.codex_state.read_text()
        state = json.loads(original)
        state["installed"][0]["version"] = "0.1.30-other"
        self.codex_state.write_text(json.dumps(state))
        try:
            exit_code = self.run_suite(
                hold, "manual-hold", "--phase", "consumer-cleanup"
            )
            document = self.result_of(hold, "manual-hold")
            self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
            self.assertEqual(document["outcome"], "fail")
            self.assertEqual(document["consumer_cleanup"], "failed")
            problems = document["cleanup"]["problems"]
            self.assertTrue(
                any("prior plugin version changed" in problem for problem in problems),
                problems,
            )
            self.assertTrue(
                any(
                    "differs from the smoke baseline" in problem for problem in problems
                ),
                problems,
            )
        finally:
            self.codex_state.write_text(original)
            self.run_suite(hold, "manual-hold", "--phase", "consumer-cleanup")

    def _selected_generation_receipt(self) -> Path:
        current = self.home / ".aquarium/status-runtime/current"
        name = current.read_text().strip().removeprefix("versions/")
        return self.home / ".aquarium/status-runtime/versions" / name / "runtime.json"

    def test_c36_receipt_shape_at_smoke_fails_hold(self):
        # A null, array, malformed-JSON or undecodable receipt at smoke
        # gives the structured hold rejection, never a crash.
        shapes = {
            "null": b"null",
            "array": b"[1, 2]",
            "malformed": b"{not json",
            "undecodable": b'{"x": "\xff"}',
        }
        for label, raw in shapes.items():
            with self.subTest(receipt=label):
                self._c10_establish_prior_for_hold(f"c36-shape-{label}")
                self._seed_probe_leftover()
                receipt_path = self._selected_generation_receipt()
                original = receipt_path.read_bytes()
                receipt_path.write_bytes(raw)
                try:
                    job = self.job_root(f"c36-shape-{label}-hold")
                    exit_code = self.run_suite(job, "manual-hold", "--phase", "smoke")
                    self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
                    self._assert_hold_not_begun(job, "generation unreadable")
                finally:
                    receipt_path.write_bytes(original)

    def test_c38_undecodable_current_marker_at_smoke_fails_hold(self):
        # A 0xff byte in the current marker is a decoding failure inside
        # the structured boundary, not a traceback.
        self._c10_establish_prior_for_hold("c38-current")
        self._seed_probe_leftover()
        current = self.home / ".aquarium/status-runtime/current"
        original = current.read_bytes()
        current.write_bytes(b"versions/\xffgeneration\n")
        try:
            job = self.job_root("c38-current-hold")
            exit_code = self.run_suite(job, "manual-hold", "--phase", "smoke")
            self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
            self._assert_hold_not_begun(job, "unreadable")
        finally:
            current.write_bytes(original)

    def test_c36_receipt_drift_after_smoke_fails_cleanup(self):
        shapes = {
            "null": b"null",
            "array": b"[1, 2]",
            "malformed": b"{not json",
            "undecodable": b'{"x": "\xff"}',
        }
        for label, raw in shapes.items():
            with self.subTest(receipt=label):
                self._c10_establish_prior_for_hold(f"c36-drift-{label}")
                hold = self.job_root(f"c36-drift-{label}-hold")
                self.assertEqual(
                    self.run_suite(hold, "manual-hold", "--phase", "smoke"),
                    0,
                    SEQUENCE_LOG[-1],
                )
                receipt_path = self._selected_generation_receipt()
                original = receipt_path.read_bytes()
                receipt_path.write_bytes(raw)
                try:
                    exit_code = self.run_suite(
                        hold, "manual-hold", "--phase", "consumer-cleanup"
                    )
                    document = self.result_of(hold, "manual-hold")
                    self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
                    self.assertEqual(document["outcome"], "fail")
                    self.assertEqual(document["consumer_cleanup"], "failed")
                    problems = document["cleanup"]["problems"]
                    self.assertTrue(
                        any("generation unreadable" in problem for problem in problems),
                        problems,
                    )
                finally:
                    receipt_path.write_bytes(original)
                    self.run_suite(hold, "manual-hold", "--phase", "consumer-cleanup")

    def test_c38_unparsable_prior_sidecar_at_smoke_fails_hold(self):
        # A malformed or undecodable prior sidecar reaches the existing
        # "missing or unparsable" problem; the hold does not begin and the
        # leftover is preserved.
        for label, raw in (
            ("malformed", b"{not json"),
            ("undecodable", b'{"kind": "\xff"}'),
        ):
            with self.subTest(sidecar=label):
                self._c10_establish_prior_for_hold(f"c38-sidecar-{label}")
                self._seed_probe_leftover()
                sidecar = (
                    self.home / ".aquarium-vm-marketplaces/prior-artifact.owner.json"
                )
                original = sidecar.read_bytes()
                sidecar.write_bytes(raw)
                try:
                    job = self.job_root(f"c38-sidecar-{label}-hold")
                    exit_code = self.run_suite(job, "manual-hold", "--phase", "smoke")
                    self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
                    self._assert_hold_not_begun(
                        job, "prior marketplace sidecar missing or unparsable"
                    )
                finally:
                    sidecar.write_bytes(original)

    def test_c36_non_object_smoke_json_fails_cleanup(self):
        # Truthy non-object documents reach the isinstance guards: a
        # non-empty array smoke.json, a non-object retained_state_baseline
        # and a non-object prior_state each give the missing-baseline
        # problem with fail/failed, never a crash.
        self._c10_establish_prior_for_hold("c36-badbaseline")
        hold = self.job_root("c36-badbaseline-hold")
        self.assertEqual(
            self.run_suite(hold, "manual-hold", "--phase", "smoke"),
            0,
            SEQUENCE_LOG[-1],
        )
        smoke = hold / "results/manual-hold/smoke.json"
        original = smoke.read_bytes()
        valid = json.loads(original)

        def plant(label: str, needle: str) -> None:
            with self.subTest(case=label):
                try:
                    if label == "array document":
                        smoke.write_text("[1]")
                    elif label == "array baseline":
                        mutated = dict(valid)
                        mutated["retained_state_baseline"] = [1]
                        smoke.write_text(json.dumps(mutated))
                    else:
                        baseline = dict(valid["retained_state_baseline"])
                        baseline["prior_state"] = "x"
                        mutated = dict(valid)
                        mutated["retained_state_baseline"] = baseline
                        smoke.write_text(json.dumps(mutated))
                    exit_code = self.run_suite(
                        hold, "manual-hold", "--phase", "consumer-cleanup"
                    )
                    document = self.result_of(hold, "manual-hold")
                    self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
                    self.assertEqual(document["outcome"], "fail")
                    self.assertEqual(document["consumer_cleanup"], "failed")
                    problems = document["cleanup"]["problems"]
                    self.assertTrue(
                        any(needle in problem for problem in problems), problems
                    )
                finally:
                    smoke.write_bytes(original)
                    self.run_suite(hold, "manual-hold", "--phase", "consumer-cleanup")

        plant("array document", "smoke retained-state baseline is missing")
        plant("array baseline", "smoke retained-state baseline is missing")
        plant(
            "non-object prior_state",
            "smoke prior-state baseline is missing",
        )

    def test_c19_migration_early_exit_reports_unverified(self):
        # A foreign candidate generation makes J-M exit before any
        # end-state check; the suite must report unverified cleanup, and
        # the foreign generation is preserved.
        self._c10_establish_prior_for_hold("c19-mig")
        dev = f"v0.1.21-dev.{self.git_sha[:12]}"
        versions = self.home / ".aquarium/status-runtime/versions"
        foreign = versions / f"{'e' * 64}-py3.14"
        foreign.mkdir()
        (foreign / "runtime.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium-status-runtime/v1",
                    "source_sha256": "f" * 64,
                    "plugin_version": dev,
                    "python_version": "3.14.8",
                    "python_executable": "/synthetic/python",
                    "python_executable_sha256": "d" * 64,
                    "requirements_sha256": "0" * 64,
                    "files": {},
                    "dependency_files": {},
                }
            )
        )
        try:
            job = self.job_root("c19-mig-foreign")
            exit_code = self.run_suite(job, "migration-failure")
            document = self.result_of(job, "migration-failure")
            self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
            self.assertEqual(document["outcome"], "fail")
            self.assertEqual(document["consumer_cleanup"], "unverified")
            self.assertTrue(document["foreign_generations"])
            self.assertTrue(foreign.is_dir())
        finally:
            shutil.rmtree(foreign, ignore_errors=True)

    def test_c19_functional_upgrade_failure_keeps_verified_cleanup(self):
        # A wrong receipt binding digest is a functional failure only: the
        # upgrade ends with a clean end state, so the suite reports fail
        # with verified consumer cleanup.
        self._c10_establish_prior_for_hold("c19-func")
        job = self.job_root("c19-upgrade-func")
        exit_code = self.run_suite(job, "upgrade", FAKE_INSTALLER_MISMATCH_RECEIPT="1")
        document = self.result_of(job, "upgrade")
        self.assertEqual(exit_code, 1, SEQUENCE_LOG[-1])
        self.assertEqual(document["outcome"], "fail")
        self.assertEqual(document["consumer_cleanup"], "verified")
        self.assertTrue(document["functional_violations"], document)
        self.assertEqual(document["postcondition_violations"], [])

    def test_c5_f2_post_normalization_failure_references_preimage(self):
        job = self.job_root("f2")
        result = self.run_suite(
            job,
            "baseline",
            stage=0,
            FAKE_INSTALLER_FAIL_VERSION="v0.1.21",
        )
        self.assertEqual(result, 1, SEQUENCE_LOG[-1])
        document = self.result_of(job, "baseline")
        self.assertEqual(document["outcome"], "fail")
        self.assertEqual(document["consumer_cleanup"], "unverified")
        self.assertIn("pre-normalization.json", document["problem"])
        self.assertTrue((job / "results/baseline/pre-normalization.json").is_file())

    def test_c6_f6_post_snapshot_failure_after_normalization_references_preimage(self):
        job = self.job_root("f6")
        # The installer leaves a special file inside the inventoried scope
        # (in-scope symlinks became normal entries), so the
        # post-install snapshot fails after normalization succeeded; the
        # whole post-normalization body must reference the persisted
        # preimage (c6 finding 6).
        evil = self.home / ".aquarium/status-runtime/versions/.evil-fifo"
        try:
            result = self.run_suite(job, "baseline", FAKE_INSTALLER_LEAVE_FIFO="1")
            self.assertEqual(result, 1, SEQUENCE_LOG[-1])
            document = self.result_of(job, "baseline")
            self.assertEqual(document["outcome"], "fail")
            self.assertEqual(document["consumer_cleanup"], "unverified")
            self.assertIn("pre-normalization.json", document["problem"])
            self.assertIn("special file inside inventory scope", document["problem"])
            self.assertTrue((job / "results/baseline/pre-normalization.json").is_file())
        finally:
            # Clean the injected special file so later suites see a sane
            # scope, even when an assertion above failed.
            if evil.exists() or evil.is_symlink():
                evil.unlink()

    def test_c8_f2_manual_hold_failed_postcondition_not_pass(self):
        job = self.job_root("f2-hold")
        self.run_suite(job, "manual-hold", "--phase", "smoke")
        # Recreate the declared leftover after the repair so the cleanup
        # postcondition (probe_leftover_absent) fails.
        (self.home / ".aquarium-vm-probe-leftover").write_text("foreign\n")
        result = self.run_suite(job, "manual-hold", "--phase", "consumer-cleanup")
        self.assertEqual(result, 1, SEQUENCE_LOG[-1])
        document = self.result_of(job, "manual-hold")
        self.assertEqual(document["outcome"], "fail")
        self.assertEqual(document["consumer_cleanup"], "failed")
        self.assertFalse(document["cleanup"]["probe_leftover_absent"])
        inventory = json.loads(
            (job / "results/manual-hold/post-cleanup-inventory.json").read_text()
        )
        self.assertFalse(inventory["postcondition_ok"])
        (self.home / ".aquarium-vm-probe-leftover").unlink(missing_ok=True)

    def _c10_establish_prior_for_hold(self, job_name: str) -> Path:
        """Explicitly establish the prior marketplace before a J-H hold."""
        base = self.job_root(f"{job_name}-base")
        self.assertEqual(self.run_suite(base, "baseline"), 0, SEQUENCE_LOG[-1])
        return base

    def test_c10_f1_sidecar_changed_during_hold_fails(self):
        self._c10_establish_prior_for_hold("sidecar")
        hold = self.job_root("f10-sidecar")
        self.assertEqual(
            self.run_suite(hold, "manual-hold", "--phase", "smoke"),
            0,
            SEQUENCE_LOG[-1],
        )
        sidecar = self.home / ".aquarium-vm-marketplaces" / "prior-artifact.owner.json"
        original = sidecar.read_bytes()
        self.addCleanup(sidecar.write_bytes, original)
        document = json.loads(sidecar.read_text())
        document["job_id"] = "someone-else"
        sidecar.write_text(json.dumps(document, indent=2) + "\n")
        result = self.run_suite(hold, "manual-hold", "--phase", "consumer-cleanup")
        self.assertEqual(result, 1, SEQUENCE_LOG[-1])
        cleanup = self.result_of(hold, "manual-hold")
        self.assertEqual(cleanup["consumer_cleanup"], "failed")
        self.assertIn(
            "prior marketplace sidecar changed", cleanup["cleanup"]["problems"]
        )

    def test_c10_f1_executable_bit_flipped_during_hold_fails(self):
        self._c10_establish_prior_for_hold("execbit")
        hold = self.job_root("f10-execbit")
        self.assertEqual(
            self.run_suite(hold, "manual-hold", "--phase", "smoke"),
            0,
            SEQUENCE_LOG[-1],
        )
        script = next(
            (
                self.home
                / ".aquarium-vm-marketplaces"
                / "prior-artifact"
                / "plugins/aquarium/tools/aquarium-status"
            ).rglob("install.py")
        )
        # The sealed installer lands non-executable; make it executable so
        # the recorded baseline has a flippable bit, and restore the
        # established mode afterwards so later suites see the sealed bytes.
        script.chmod(0o755)
        self.addCleanup(script.chmod, 0o644)
        result = self.run_suite(hold, "manual-hold", "--phase", "consumer-cleanup")
        self.assertEqual(result, 1, SEQUENCE_LOG[-1])
        cleanup = self.result_of(hold, "manual-hold")
        self.assertEqual(cleanup["consumer_cleanup"], "failed")
        self.assertTrue(
            any(
                "executable bit changed" in problem
                for problem in cleanup["cleanup"]["problems"]
            )
        )

    def test_c10_f1_prior_directory_missing_at_preparation_fails(self):
        self._c10_establish_prior_for_hold("missing")
        prior_dir = self.home / ".aquarium-vm-marketplaces/prior-artifact"
        saved = None
        if prior_dir.exists():
            backup_root = Path(tempfile.mkdtemp(dir=str(self.work)))
            self.addCleanup(shutil.rmtree, backup_root, True)
            saved = backup_root / "prior-artifact"
            shutil.move(str(prior_dir), str(saved))
            self.addCleanup(shutil.move, str(saved), str(prior_dir))
        hold = self.job_root("f10-missing")
        result = self.run_suite(hold, "manual-hold", "--phase", "smoke")
        self.assertEqual(result, 1, SEQUENCE_LOG[-1])
        document = self.result_of(hold, "manual-hold")
        self.assertEqual(document["outcome"], "fail")
        self.assertIn(
            "prior marketplace directory missing",
            document["retained_problems"],
        )

    def test_c9_f2_prior_plugin_changed_during_hold_fails(self):
        self._c10_establish_prior_for_hold("changed")
        hold = self.job_root("f2-changed")
        self.assertEqual(
            self.run_suite(hold, "manual-hold", "--phase", "smoke"),
            0,
            SEQUENCE_LOG[-1],
        )
        marker = (
            self.home
            / ".aquarium-vm-marketplaces/prior-artifact"
            / ".agents/plugins/marketplace.json"
        )
        original = marker.read_bytes()
        self.addCleanup(marker.write_bytes, original)
        marker.write_text(json.dumps({"name": "root-kernel", "changed": True}))
        result = self.run_suite(hold, "manual-hold", "--phase", "consumer-cleanup")
        self.assertEqual(result, 1, SEQUENCE_LOG[-1])
        cleanup = self.result_of(hold, "manual-hold")
        self.assertEqual(cleanup["consumer_cleanup"], "failed")
        self.assertTrue(
            any("changed" in problem for problem in cleanup["cleanup"]["problems"])
        )

    def test_c9_f2_fixture_replaced_by_regular_file_fails(self):
        self._c10_establish_prior_for_hold("fixture-file")
        hold = self.job_root("f2-fixture-file")
        self.assertEqual(
            self.run_suite(hold, "manual-hold", "--phase", "smoke"),
            0,
            SEQUENCE_LOG[-1],
        )
        fixture = hold / "manual-hold-fixture"
        shutil.rmtree(fixture)
        fixture.write_text("replaced\n")
        result = self.run_suite(hold, "manual-hold", "--phase", "consumer-cleanup")
        self.assertEqual(result, 0, SEQUENCE_LOG[-1])
        # Filesystem effect first: the fixture no longer exists.
        self.assertFalse(fixture.exists())
        self.assertFalse(fixture.is_symlink())
        document = self.result_of(hold, "manual-hold")
        self.assertEqual(document["outcome"], "pass")
        self.assertTrue(document["cleanup"]["fixture_absent"])

    def test_c8_f5_baseline_preservation_fail_references_preimage(self):
        job = self.job_root("f5-base")
        # An unexpected change to unrelated inventoried state (skills)
        # happens during the run — the installer drifts a skills file — so
        # the preservation comparison fails after a successful install.
        marker = self.home / ".agents/skills/deslop/UNEXPECTED.md"
        self.addCleanup(marker.unlink, None)
        result = self.run_suite(job, "baseline", FAKE_INSTALLER_TOUCH_SKILLS="1")
        self.assertEqual(result, 1, SEQUENCE_LOG[-1])
        document = self.result_of(job, "baseline")
        self.assertEqual(document["outcome"], "fail")
        self.assertEqual(document["consumer_cleanup"], "failed")
        self.assertIn("pre-normalization.json", document["problem"])
        self.assertTrue(document["violations"])

    def test_wrong_identity_performs_no_write(self):
        job = self.job_root("wrong")
        wrong = self.work / "wrong-identity.json"
        wrong.write_text(
            json.dumps(
                {
                    "platform": "Darwin",
                    "hypervisor_present": "1",
                    "hardware_uuid": "99999999-9999-9999-9999-999999999999",
                }
            )
        )
        environment = self.base_env()
        environment["HAEPARI_PARENT_CONTEXT"] = json.dumps(
            [{"job_id": "sim-wrong", "lease_generation": 1, "nonce": "ab" * 32}]
        )
        environment["AQUARIUM_VM_JOB_ID"] = "sim-wrong"
        environment["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(LAUNCHER),
                str(wrong),
                str(job / "harness"),
                "--suite",
                "immutability-probe",
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((job / "checkout").exists())
        results = job / "results"
        if results.exists():
            self.assertEqual(list(results.rglob("*")), [], "identity rejection wrote")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["writes"], "none")


class FailClosedPathRootsTest(unittest.TestCase):
    """Empty or relative path roots must abort before any filesystem effect."""

    def invoke_fake(self, fixture: str, home_value: str) -> subprocess.CompletedProcess:
        descriptor, state_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(descriptor, "w") as stream:
            stream.write(json.dumps({"marketplaces": [], "installed": []}))
        self.addCleanup(os.unlink, state_path)
        environment = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/private/tmp",
            "AQUARIUM_GUEST_HOME": home_value,
            "FAKE_CODEX_STATE": state_path,
            "FAKE_PYTHON_REAL": sys.executable,
            "FAKE_PYTHON_BINDING": str(FIXTURES / "fake_python.py"),
        }
        return subprocess.run(
            [
                sys.executable,
                str(FIXTURES / fixture),
                "diagnose",
                "--source",
                "/private/tmp",
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def test_empty_home_is_rejected(self):
        for fixture in ("fake_codex.py", "fake_installer.py"):
            result = self.invoke_fake(fixture, "")
            self.assertNotEqual(result.returncode, 0, fixture)
            self.assertIn("non-empty absolute", result.stderr + result.stdout)

    def test_relative_home_is_rejected(self):
        for fixture in ("fake_codex.py", "fake_installer.py"):
            result = self.invoke_fake(fixture, "relative/home")
            self.assertNotEqual(result.returncode, 0, fixture)
            self.assertIn("non-empty absolute", result.stderr + result.stdout)

    def test_launcher_rejects_relative_paths(self):
        for value in ("", "relative/path", "."):
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(LAUNCHER),
                    value,
                    value,
                    "--suite",
                    "immutability-probe",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0, value)
            self.assertIn("absolute", result.stderr + result.stdout)

    def test_fake_python_rejects_non_absolute_real(self):
        result = subprocess.run(
            [sys.executable, str(FIXTURES / "fake_python.py"), "-c", "pass"],
            env={"PATH": "/usr/bin:/bin", "FAKE_PYTHON_REAL": "relative/python"},
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-empty absolute", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
