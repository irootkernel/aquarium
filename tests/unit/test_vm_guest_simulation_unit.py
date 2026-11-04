from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

REPOSITORY = Path(__file__).resolve().parents[2]
RECIPES_ROOT = REPOSITORY / "tests/vm/recipes"
STABLE_PROFILE = (
    REPOSITORY
    / "tests/vm/profiles"
    / "proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0-podway-0.2.14.json"
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


def skill_tree_digest_of(root: Path) -> str:
    """`aquarium-skill-tree-sha256/v1` over a stub skills tree, computed the
    same way the profile validator computes it."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sim_profile_validator",
        REPOSITORY / "tests/vm/profiles/validate_profiles.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.tree_digest_from_directory(root)


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
        # The cloned checkout must carry the profile validator the skill
        # identity phase imports by exact file path.
        (stub / "tests/vm/profiles").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            REPOSITORY / "tests/vm/profiles/validate_profiles.py",
            stub / "tests/vm/profiles/validate_profiles.py",
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
            for procedure in (
                "task",
                "goal",
                "validation",
                "design",
                "war-room",
            ):
                (assets / f"aquarium-{procedure}-v2.yaml").write_text(
                    f"procedure: {procedure} stub\n"
                )
            # The skills trees are byte-identical between prior and candidate
            # so the profile pins can be rebound per stub tree.
            for skill in ("dev-setup", "task-handler", "epic-handler"):
                tree = plugin / "skills" / skill
                tree.mkdir(parents=True)
                (tree / "SKILL.md").write_text(f"# aquarium:{skill}\n")
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
        (stub / "Makefile").write_text(
            "test-vm:\n\tpython3 -B tests/vm/run_acceptance.py run\n"
        )
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
        cls.checkout_bundle = cls.work / "checkout.bundle"
        subprocess.run(
            [
                "git",
                "-C",
                str(stub),
                "bundle",
                "create",
                str(cls.checkout_bundle),
                "--all",
            ],
            check=True,
            capture_output=True,
        )

    def setUp(self):
        self.test_work = Path(
            tempfile.mkdtemp(prefix="test-", dir=str(self.work))
        ).resolve()
        self.addCleanup(shutil.rmtree, self.test_work, True)
        self.home = self.test_work / "home"
        self.codex_state = self.test_work / "codex-state.json"
        self.podway_state = self.test_work / "podway-state.json"
        self._released_threads = {}
        self._seed_persistent_home()

    def _seed_persistent_home(self):
        home = self.home
        home.mkdir(parents=True, exist_ok=True)
        foreign_root = self.test_work / "foreign-marketplace-root"
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
        self.codex_state.write_text(
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
        for name in ("deslop", "use-gaori"):
            skill = home / ".agents/skills" / name
            skill.mkdir(parents=True, exist_ok=True)
            (skill / "SKILL.md").write_text(f"# {name}\n")
        # The profile pins this synthetic guest tree, independent of host installs.
        synthetic_skill = home / ".agents/skills/use-podway"
        synthetic_skill.mkdir(parents=True)
        (synthetic_skill / "SKILL.md").write_text("# synthetic use-podway\n")
        # Per-home skills shaped like the guest: system skills plus foreign
        # trees, all inventoried by the codex-home-skills scope, and per-home
        # rules preserved as starting state with content identity.
        for name in (".system", "imagegen", "humanize-korean", "ouroboros-orca"):
            skill = home / ".codex/skills" / name
            skill.mkdir(parents=True, exist_ok=True)
            (skill / "SKILL.md").write_text(f"# {name}\n")
        rules = home / ".codex/rules"
        rules.mkdir(parents=True, exist_ok=True)
        (rules / "ouroboros.md").write_text("# ouroboros rules\n")
        self.podway_state.write_text("{}")
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
        job = self.test_work / f"job-{name}"
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
        shutil.copyfile(self.checkout_bundle, job / "checkout.bundle")
        profiles = job / "profile"
        profiles.mkdir()
        stable = json.loads(STABLE_PROFILE.read_text())
        # Rebind the plugin skill pin to the stub trees exactly as the host
        # derivation binds it to the sealed artifact's own skills.
        prior_digest = skill_tree_digest_of(self.prior / "plugins/aquarium/skills")
        candidate_digest = skill_tree_digest_of(
            self.candidate / "plugins/aquarium/skills"
        )
        candidate_profile = {
            **json.loads(json.dumps(stable)),
            "profile_id": f"sim-candidate-{self.git_sha[:12]}",
        }
        # Test-only setup: the simulated bundle's profiles carry the fake
        # Podway executable's digest instead of the real installation pin,
        # so production code reads its profile pin unchanged.
        fake_podway_digest = (
            "sha256:"
            + hashlib.sha256((FIXTURES / "fake_podway.py").read_bytes()).hexdigest()
        )
        for document, pin, version in (
            (stable, prior_digest, "0.1.21"),
            (candidate_profile, candidate_digest, f"0.1.21-dev.{self.git_sha[:12]}"),
        ):
            for component in document["components"]:
                if component.get("name") == "aquarium-plugin":
                    component["skill_tree"]["sha256"] = pin
                    component["version"] = version
                if component.get("name") == "podway":
                    component["executable_sha256"] = fake_podway_digest
                if component.get("name") == "use-podway":
                    component["skill_tree"]["sha256"] = skill_tree_digest_of(
                        self.home / ".agents/skills/use-podway"
                    )
        (profiles / "stable.json").write_text(
            json.dumps(stable, indent=2, ensure_ascii=False) + "\n"
        )
        (profiles / "candidate.json").write_text(
            json.dumps(candidate_profile, indent=2, ensure_ascii=False) + "\n"
        )
        upgraded = json.loads(json.dumps(candidate_profile))
        upgraded["profile_id"] += "-podway-16"
        for component in upgraded["components"]:
            if component.get("name") == "podway":
                component["version"] = "v0.2.16"
        (profiles / "podway-candidate.json").write_text(json.dumps(upgraded))
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
        # Every operator phase runs through guest_entry.sh with only the
        # documented environment. The wrapper keeps the simulation's guest
        # premise: guest_main invocations go through the launcher (platform
        # identity + in-process driver guard), everything else through the
        # fake guest python.
        wrapper = job / "bin/guest-python"
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(
            "#!/bin/sh\n"
            'case "$2" in\n'
            "*guest_main.py)\n"
            "    shift 2\n"
            f"    exec {json.dumps(sys.executable)} -B {json.dumps(str(LAUNCHER))} "
            f"{json.dumps(str(self.identity))} {json.dumps(str(job / 'harness'))} "
            '"$@";;\n'
            "*)\n"
            f"    exec {json.dumps(sys.executable)} -B "
            f'{json.dumps(str(FIXTURES / "fake_python.py"))} "$@";;\n'
            "esac\n"
        )
        wrapper.chmod(0o755)
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
                    "podway_upgrade": {
                        "source_commit": "sim-podway-16",
                        "contract_manifest_digest": "sim-manifest-16",
                        "contract_generation": 2,
                    },
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
            "TMPDIR": str(self.test_work.resolve()),
            "AQUARIUM_GUEST_HOME": str(self.home),
            "AQUARIUM_GUEST_PYTHON": str(FIXTURES / "fake_python.py"),
            "AQUARIUM_DRIVER_PYTHON": sys.executable,
            "AQUARIUM_GUEST_CODEX": str(FIXTURES / "fake_codex.py"),
            "AQUARIUM_GUEST_PODWAY": str(FIXTURES / "fake_podway.py"),
            "AQUARIUM_EXPECTED_GUEST_UUID": SIMULATED_UUID,
            "AQUARIUM_MARKETPLACE_NAME": "root-kernel",
            "FAKE_CODEX_STATE": str(self.codex_state),
            "FAKE_PODWAY_STATE": str(self.podway_state),
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
        self._c10_establish_prior_for_hold("reply-window-hold")
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

    # ------------------------------------------------------------------
    # TASK-089 release-acceptance (J-RA)

    _released_threads: ClassVar[dict[str, str]] = {}

    def _jra_run(self, job: Path, phase: str, fixture: str | None = None, **env):
        """Every J-RA phase runs the documented entry point with only the
        documented environment: the saved spec's workload.environment plus
        the managed context. The entry point derives the Job identity; the
        test never injects AQUARIUM_VM_JOB_ID or the lease generation."""
        extra = ["--phase", phase]
        if fixture:
            extra += ["--fixture", fixture]
        environment = self.base_env()
        environment["AQUARIUM_GUEST_PYTHON"] = str(job / "bin/guest-python")
        environment.update({key: str(value) for key, value in env.items()})
        environment["HAEPARI_PARENT_CONTEXT"] = json.dumps(
            [
                {
                    "job_id": f"sim-jra-{job.name}",
                    "lease_generation": 1,
                    "nonce": "ab" * 32,
                }
            ]
        )
        result = subprocess.run(
            [
                "/bin/sh",
                str(job / "harness/tests/vm/recipes/guest_entry.sh"),
                "--suite",
                "release-acceptance",
                *extra,
            ],
            cwd=job / "harness",
            env=environment,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        SEQUENCE_LOG.append(
            {
                "suite": "release-acceptance",
                "extra": list(extra),
                "exit": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-500:],
            }
        )
        return result.returncode

    def _released_setup(self, job: Path, fixture: str) -> None:
        run_root = job / "acceptance-run"
        environment = self.base_env()
        prompt = (
            f"Invoke the normally discovered installed $aquarium:dev-setup for "
            f"{run_root / fixture}, scoped only to Podway managed configuration "
            "and sources. Use the current installed source and normal concrete "
            "proposal/approval boundary. The authorized fixture operator is "
            "coordinator-fixture-operator; existing scope authority is "
            "epic-019-vm-test-authority. Preserve custom sources, original "
            "admitted sessions, Git work and reports. Settle native agents and "
            "return the actual result. Do not commit or publish."
        )
        result = subprocess.run(
            [
                environment["AQUARIUM_GUEST_CODEX"],
                "exec",
                "--json",
                "--add-dir",
                str(run_root),
                "-C",
                str(run_root / fixture),
                "--output-last-message",
                str(run_root / f"released-{fixture}.last"),
                "-",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            env=environment,
            timeout=300,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        (run_root / f"released-{fixture}.jsonl").write_text(result.stdout)
        thread = None
        for line in result.stdout.splitlines():
            event = json.loads(line)
            if event.get("type") == "thread.started":
                thread = event["thread_id"]
        self.assertIsNotNone(thread, result.stdout)
        self._released_threads[fixture] = thread

    def _preservation_prerequisites(self, job: Path) -> None:
        run_root = job / "acceptance-run"
        environment = self.base_env()
        check = subprocess.run(
            [
                environment["AQUARIUM_GUEST_PODWAY"],
                "--json",
                "procedure",
                "check",
                "--warnings-as-errors",
                ".podway/procedures/aquarium-task-v2.yaml",
            ],
            cwd=run_root / "preservation",
            capture_output=True,
            text=True,
            env=environment,
            timeout=120,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)
        (run_root / "podway-procedure-check.json").write_text(check.stdout)
        start = subprocess.run(
            [
                environment["AQUARIUM_GUEST_PODWAY"],
                "--worktree",
                str(run_root / "preservation"),
                "start",
                "--preset",
                "sw-dev-v2",
                "--task",
                "admitted baseline session",
                "--idempotency-key",
                "aquarium-vm-release-acceptance",
            ],
            capture_output=True,
            text=True,
            env=environment,
            timeout=120,
            check=False,
        )
        self.assertEqual(start.returncode, 0, start.stderr)
        observe = subprocess.run(
            [
                environment["AQUARIUM_GUEST_PODWAY"],
                "--worktree",
                str(run_root / "preservation"),
                "--json",
                "observe",
            ],
            capture_output=True,
            text=True,
            env=environment,
            timeout=120,
            check=False,
        )
        self.assertEqual(observe.returncode, 0, observe.stderr)
        (run_root / "podway-observe.json").write_text(observe.stdout)

    def _reset_fake_guest_for_jra(self) -> None:
        """Fresh fake-guest state for each J-RA test.

        The shared persistent home made J-RA tests order-dependent: an
        earlier test's own dev-stamped generation changed the next test's
        abort preimage. Each J-RA test now starts from a freshly seeded
        home, Codex state and Podway state, so any subset passes in any
        order.
        """
        shutil.rmtree(self.home, ignore_errors=True)
        self._seed_persistent_home()
        state = {
            "marketplaces": [],
            "installed": [],
            "sessions": {},
        }
        self.codex_state.write_text(json.dumps(state))
        self.podway_state.write_text("{}")
        # Reset the recorded fake-thread handles per test.
        self._released_threads.clear()

    def _reset_marketplaces_for_jra(self) -> None:
        """Deterministic J-RA starting state over the persistent home.

        Earlier fault tests can leave the candidate marketplace unowned or
        registered; a fresh Job must not depend on their residue, so the
        harness marketplaces, the root-kernel registration and its cache
        rows are cleared before the prefix re-establishes prior stable.
        """
        marketplaces = self.home / ".aquarium-vm-marketplaces"
        for kind in ("artifact", "prior-artifact"):
            directory = marketplaces / kind
            if directory.exists() or directory.is_symlink():
                shutil.rmtree(directory, ignore_errors=True)
            sidecar = marketplaces / f"{kind}.owner.json"
            if sidecar.exists() or sidecar.is_symlink():
                sidecar.unlink()
        state = json.loads(self.codex_state.read_text())
        state["marketplaces"] = [
            row for row in state["marketplaces"] if row["name"] != "root-kernel"
        ]
        state["installed"] = [
            row for row in state["installed"] if row["marketplaceName"] != "root-kernel"
        ]
        self.codex_state.write_text(json.dumps(state))
        cache = self.home / ".codex/plugins/cache/root-kernel"
        if cache.exists():
            shutil.rmtree(cache)

    def _upgrade_jra_dependency(self, job):
        if not (job / "results/release-acceptance/capture.json").exists():
            for fixture in ("task", "epic", "preservation"):
                self._released_setup(job, fixture)
                self.assertEqual(
                    self._jra_run(
                        job,
                        "record-setup",
                        fixture,
                        AQUARIUM_VM_THREAD=self._released_threads[fixture],
                    ),
                    0,
                    SEQUENCE_LOG[-1],
                )
            self._preservation_prerequisites(job)
            self.assertEqual(self._jra_run(job, "capture"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "podway-upgrade"), 0, SEQUENCE_LOG[-1])

    def _run_jra_through_managed_updates(self, job: Path) -> Path:
        """The operator prefix every J-RA run shares, up to step g."""
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        for fixture in ("task", "epic", "preservation"):
            self._released_setup(job, fixture)
            self.assertEqual(
                self._jra_run(
                    job,
                    "record-setup",
                    fixture,
                    AQUARIUM_VM_THREAD=self._released_threads[fixture],
                ),
                0,
                SEQUENCE_LOG[-1],
            )
        self._preservation_prerequisites(job)
        capture_exit = self._jra_run(job, "capture")
        capture_path = job / "results/release-acceptance/capture.json"
        self.assertEqual(
            capture_exit,
            0,
            capture_path.read_text() if capture_path.is_file() else SEQUENCE_LOG[-1],
        )
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "skill-identity"), 0, SEQUENCE_LOG[-1])
        request_before_runtime = (job / "acceptance/request.json").read_bytes()
        self.assertEqual(self._jra_run(job, "runtime-update"), 0, SEQUENCE_LOG[-1])
        reply = job / "runtime-reply.txt"
        reply.write_text("Approve the proposed runtime update.\n")
        reply_exit = self._jra_run(
            job, "runtime-reply", AQUARIUM_VM_REPLY_FILE=str(reply)
        )
        runtime_path = job / "results/release-acceptance/runtime-update.json"
        self.assertEqual(
            reply_exit,
            0,
            runtime_path.read_text() if runtime_path.is_file() else SEQUENCE_LOG[-1],
        )
        self.assertEqual(
            (job / "acceptance/request.json").read_bytes(), request_before_runtime
        )
        for fixture in ("task", "epic", "preservation"):
            self.assertEqual(
                self._jra_run(job, "managed-updates", fixture),
                0,
                SEQUENCE_LOG[-1],
            )
            record = json.loads(
                (
                    job
                    / "results/release-acceptance"
                    / f"managed-update-{fixture}.json"
                ).read_text()
            )
            self.assertEqual(record["exit"], 0)
            self.assertEqual(record["driver_outcome"], "managed-update-observed")
        return job / "results/release-acceptance"

    def test_podway_transition_without_baseline_refuses_before_copy(self):
        job = self.job_root("jra-upgrade-no-baseline")
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-upgrade-no-baseline")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "podway-upgrade"), 2, SEQUENCE_LOG[-1])
        self.assertFalse((job / "acceptance-run/candidate-fixtures").exists())
        self.assertFalse(
            (job / "results/release-acceptance/podway-upgrade.json").exists()
        )

    def test_jra_offline_sequence_through_the_smoke_boundary(self):
        job = self.job_root("jra-sequence")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        prepare = json.loads((results / "machine-prepare.json").read_text())
        self.assertEqual(prepare["codex_identity"]["version"], "codex-cli 0.164.0")
        self.assertEqual(prepare["codex_identity"]["login_status"]["mode"], "chatgpt")
        self.assertIn("ChatGPT", prepare["codex_identity"]["login_status"]["line"])
        self.assertEqual(prepare["abort_normalization"]["runtime_generations"], [])
        request = json.loads((job / "acceptance/request.json").read_text())
        self.assertEqual(
            request["baseline_combination"],
            {"aquarium": "0.1.21", "codex": "0.164.0", "podway": "v0.2.14"},
        )
        prior_identity = json.loads((results / "skill-identity.json").read_text())
        self.assertTrue(
            prior_identity["skill_trees"]["installed-plugin-skills"]["match"]
        )
        self.assertTrue(prior_identity["comparisons"]["all_passed"])
        rules = next(
            scope
            for scope in prior_identity["scopes"]
            if scope["root"] == "~/.codex/rules"
        )
        self.assertEqual(rules["scope"], "codex-rules")
        self.assertIsNotNone(rules["entries"])
        self.assertTrue(
            all("sha256" in entry for entry in rules["entries"]), rules["entries"]
        )
        inventory = json.loads((results / "inventory-prior-baseline.json").read_text())
        scopes = {entry["installation_scope"] for entry in inventory["entries"]}
        self.assertIn("codex-home-skills", scopes)
        self.assertEqual(json.loads((results / "capture.json").read_text())["exit"], 0)
        self.assertTrue((run_root / "baseline.json").is_file())
        identity = json.loads((results / "skill-identity.json").read_text())
        self.assertEqual(identity["stage"], "candidate")
        self.assertTrue(identity["skill_trees"]["installed-plugin-skills"]["match"])
        self.assertTrue(identity["comparisons"]["all_passed"])
        self.assertEqual(identity["duplicates"], [])
        self.assertIsNotNone(identity["prior_stage"])
        runtime = json.loads((results / "runtime-update.json").read_text())
        network_override = "sandbox_workspace_write.network_access=true"
        self.assertNotIn(network_override, request["codex_args"])
        for case in (
            "runtime-update",
            "task-setup",
            "epic-setup",
            "preservation-setup",
        ):
            receipts = sorted(
                (run_root / "operations" / case).glob("*.invocation.json")
            )
            self.assertTrue(receipts, case)
            if case == "runtime-update":
                self.assertEqual(len(receipts), 2)
            for path in receipts:
                argv = json.loads(path.read_text())["argv"]
                self.assertEqual(
                    argv.count(network_override), int(case == "runtime-update"), path
                )
                if case == "runtime-update":
                    self.assertEqual(argv[argv.index(network_override) - 1], "-c")
        self.assertIs(runtime["approval_completed"], True, runtime)
        self.assertEqual(runtime["workflow_exit"], 0)
        self.assertIs(runtime["recipe_ran_installer"], False, runtime)
        self.assertEqual(runtime["dev_stamped_outside_windows"], [])
        self.assertTrue(runtime["generations_created_in_reply_window"])
        self.assertTrue(runtime["same_thread"])
        # The append-only reply history keeps the initial evidence.
        self.assertTrue(runtime["versions_before_initial"])
        self.assertEqual(len(runtime["replies"]), 1)
        self.assertEqual(
            runtime["replies"][0]["versions_after_reply"],
            sorted(
                set(runtime["versions_before_initial"])
                | set(runtime["generations_created_in_reply_window"])
            ),
        )
        # The smoke gate runs as a subprocess without the launcher's guest
        # patch. The driver must refuse before producing an installed result.
        smoke_exit = self._jra_run(job, "startup-smokes")
        smoke_path = results / "startup-smokes.json"
        self.assertEqual(
            smoke_exit,
            2,
            smoke_path.read_text() if smoke_path.is_file() else SEQUENCE_LOG[-1],
        )
        smokes = json.loads(smoke_path.read_text())
        self.assertEqual(smokes["outcome"], "unobserved")
        self.assertNotEqual(smokes["exit"], 0)
        self.assertFalse((run_root / "result.json").exists())
        self.assertEqual(
            set(smokes["unobserved_cases"]),
            {"VM-UPGRADE-01", "VM-TASK-START-01", "VM-EPIC-START-01"},
        )
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        stale = json.loads((results / "stale-skill.json").read_text())
        self.assertEqual(stale["observation"]["outcome"], "duplication")
        self.assertTrue(stale["observation"]["planted_rows"])
        self.assertTrue(stale["restoration"]["verified"])
        self.assertFalse((self.home / ".codex/skills/task-handler").exists())
        self.assertEqual(self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1])
        staged = json.loads((results / "stage-evidence.json").read_text())
        self.assertIs(staged["ok"], False)
        joined = "\n".join(staged["problems"])
        self.assertIn("result.json", joined)
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 1, SEQUENCE_LOG[-1])
        document = self.result_of(job, "release-acceptance")
        self.assertEqual(document["outcome"], "fail")
        self.assertEqual(document["consumer_cleanup"], "unverified")
        self.assertIn("startup-smokes.json", document["problem"])
        self.assertEqual(self._jra_run(job, "complete-template"), 0, SEQUENCE_LOG[-1])
        template = json.loads((results / "manual-complete-template.json").read_text())
        statuses = {row["id"]: row["status"] for row in template["scenarios"]}
        for passed in (
            "released-baseline",
            "runtime-approval",
            "skill-identity",
            "stale-skill-failure",
            "stale-skill-restoration",
        ):
            self.assertEqual(statuses[passed], "pass", statuses)
        for unobserved in (
            "candidate-upgrade",
            "task-startup",
            "epic-startup",
            "release-startup",
            "evidence-staging",
            "consumer-cleanup",
        ):
            self.assertEqual(statuses[unobserved], "unobserved", statuses)

    def _seed_release_startup(self, run_root: Path) -> None:
        """Synthetic startup originals for archive/cleanup scenarios only."""
        release_case = run_root / "originals/release-startup/release-startup"
        release_case.mkdir(parents=True)
        evidence = {}
        for key in (
            "executor_assignment",
            "evaluator_assignment",
            "executor_result",
            "evaluator_assessment",
        ):
            path = release_case / (key + ".json")
            path.write_text(json.dumps({"explicitly": "synthetic"}))
            evidence[key] = str(path)
        (release_case / "startup-evidence.json").write_text(json.dumps(evidence))
        for name in (
            "operations/000.request.json",
            "operations/000.input",
            "operations/000.jsonl",
            "operations/000.stderr",
            "operations/000.invocation.json",
            "native-000.json",
            "capture-000.json",
        ):
            path = release_case / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}")
        (
            run_root.parent / "results/release-acceptance/release-startup.json"
        ).write_text(
            json.dumps({"candidate_sha": self.git_sha, "exit": 0, "outcome": "pass"})
        )

    def _seed_upgrade_observation(self, run_root: Path) -> None:
        # run_gate retains verify_managed_update's setup capture bindings.
        setup = {}
        for fixture in ("task", "epic", "preservation"):
            window = max(
                (run_root / "operations" / f"{fixture}-setup").glob(
                    "*.setup-after.json"
                )
            )
            setup[fixture] = {"setup": json.loads(window.read_text())["setup"]}
        (run_root / "upgrade-observation.json").write_text(
            json.dumps({"setup": setup}) + "\n"
        )

    def _seed_startup_case(self, run_root: Path, case: str) -> None:
        """Real-shape smoke artifacts following the driver's writers.

        The case directory holds startup-evidence.json plus the child
        assignment and report files it references; the native observation
        and checks use the driver's own names; the operation window holds
        the invocation receipts.
        """
        name = case.removesuffix("-startup")
        case_dir = run_root / case
        case_dir.mkdir(parents=True, exist_ok=True)
        greet = run_root / name / "greet.py"
        greet_sha = hashlib.sha256(greet.read_bytes()).hexdigest()
        criteria = {
            "uppercase-default": "--uppercase prints HELLO, WORLD! plus a newline.",
            "uppercase-name": "--uppercase Ada prints HELLO, ADA! plus a newline.",
            "existing-behavior": "Default and named greetings keep their bytes.",
        }
        paths = {}
        for role in ("executor", "evaluator"):
            path = case_dir / f"{role}-assignment.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "aquarium.assignment/v3",
                        "role": role,
                        "work": {"repository": str(run_root / name)},
                        "success_criteria": criteria,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            paths[f"{role}_assignment"] = path
        handoff = case_dir / "executor-result.json"
        handoff.write_text(
            json.dumps(
                {
                    "schema": "aquarium.executor-handoff/v3",
                    "changed_artifacts": [{"path": "greet.py", "sha256": greet_sha}],
                    "results": [{"check": "greeting oracle", "exit": 0}],
                    "target": {"greet_sha256": greet_sha},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        assessment = case_dir / "evaluator-assessment.json"
        assessment.write_text(
            json.dumps(
                {
                    "schema": "aquarium.evaluator-assessment/v3",
                    "criteria": [
                        {
                            "id": key,
                            "source": "greeting fixture oracle",
                            "evidence": f"oracle row for {key}",
                            "state": "met",
                        }
                        for key in criteria
                    ],
                    "checkpoint_result": "pass",
                    "target": {"greet_sha256": greet_sha},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (case_dir / "startup-evidence.json").write_text(
            json.dumps(
                {
                    "executor_agent": f"thread-{name}-executor",
                    "evaluator_agent": f"thread-{name}-evaluator",
                    "executor_assignment": str(paths["executor_assignment"]),
                    "evaluator_assignment": str(paths["evaluator_assignment"]),
                    "executor_result": str(handoff),
                    "evaluator_assessment": str(assessment),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (run_root / f"{name}-native-observation.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium.vm-native-observation/v1",
                    "root": {
                        "metadata": {"id": f"thread-{name}-root", "cwd": str(run_root)},
                        "items": [],
                        "turns": [{"id": "turn-0", "status": "completed"}],
                    },
                    "descendants": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (run_root / f"{name}-checks.json").write_text(
            json.dumps(
                {
                    "exit": 0,
                    "stdout": "ok\n",
                    "stderr": "",
                    "oracle": [{"arguments": [], "exit": 0}],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        window = run_root / "operations" / case
        window.mkdir(parents=True, exist_ok=True)
        (window / "000.input").write_text(f"invoke the {name} smoke\n")
        (window / "000.jsonl").write_text(
            json.dumps({"type": "thread.started", "thread_id": f"thread-{name}"})
            + "\n",
            encoding="utf-8",
        )
        (window / "000.stderr").write_text("", encoding="utf-8")
        (window / "000.last").write_text(f"{name} smoke complete\n", encoding="utf-8")
        (window / "000.invocation.json").write_text(
            json.dumps(
                {
                    "argv": ["codex", "exec", "--json"],
                    "exit": 0,
                    "input_sha256": "sha256:" + "a" * 64,
                    "thread_id": f"thread-{name}",
                    "handle_source": "cli-event",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def test_jra_completion_after_seeded_smokes(self):
        job = self.job_root("jra-completion")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        cases = [
            {"id": "VM-UPGRADE-01", "outcome": "pass"},
            {"id": "VM-TASK-START-01", "outcome": "pass"},
            {"id": "VM-EPIC-START-01", "outcome": "pass"},
        ]
        (results / "startup-smokes.json").write_text(
            json.dumps(
                {
                    "exit": 0,
                    "outcome": "pass",
                    "interpreter": "/usr/bin/python3",
                    "cases": cases,
                },
                indent=2,
            )
            + "\n"
        )
        (run_root / "result.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium.vm-acceptance-result/v1",
                    "outcome": "pass",
                    "cases": cases,
                },
                indent=2,
            )
            + "\n"
        )
        self._seed_release_startup(run_root)
        self._seed_upgrade_observation(run_root)
        for case in ("task-startup", "epic-startup"):
            self._seed_startup_case(run_root, case)
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])
        staged = json.loads((results / "stage-evidence.json").read_text())
        self.assertIs(staged["ok"], True)
        self.assertEqual(len(staged["archives"]), 10)
        for row in staged["archives"]:
            self.assertTrue((results / f"evidence/{row['case']}.tar").is_file(), row)
            manifest = json.loads(
                (results / f"evidence/{row['case']}.manifest.json").read_text()
            )
            for record in manifest["members"]:
                self.assertTrue(record["sha256"])
                self.assertGreaterEqual(record["size"], 0)
        versions = self.home / ".aquarium/status-runtime/versions"
        dev_generations = [
            entry.name
            for entry in versions.iterdir()
            if entry.is_dir()
            and (entry / "runtime.json").is_file()
            and json.loads((entry / "runtime.json").read_text()).get("plugin_version")
            == f"v0.1.21-dev.{self.git_sha[:12]}"
        ]
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 0, SEQUENCE_LOG[-1])
        # Every per-capture inventory file survives the phase processes,
        # and the aggregate carries all six captures.
        for capture in (
            "prior-baseline",
            "post-install",
            "stale-pre",
            "stale-post",
            "cleanup-before",
            "post-cleanup",
        ):
            self.assertTrue((results / f"inventory-{capture}.json").is_file(), capture)
        aggregate = json.loads((results / "inventories.json").read_text())
        self.assertEqual(
            sorted(aggregate["inventories"]),
            [
                "cleanup-before",
                "post-cleanup",
                "post-install",
                "prior-baseline",
                "stale-post",
                "stale-pre",
            ],
        )
        document = self.result_of(job, "release-acceptance")
        self.assertEqual(document["outcome"], "pass")
        self.assertEqual(document["consumer_cleanup"], "verified")
        cleanup = json.loads((results / "consumer-cleanup.json").read_text())
        self.assertEqual(cleanup["violations"], [])
        selected = cleanup["runtime_end_state"]["selected_generation"]
        self.assertIn(selected, dev_generations)
        self.assertTrue((versions / selected).exists())
        self.assertEqual(cleanup["tools"]["identity"]["result"]["version"], "v0.2.16")
        self.assertEqual(self._jra_run(job, "complete-template"), 0, SEQUENCE_LOG[-1])
        template = json.loads((results / "manual-complete-template.json").read_text())
        self.assertEqual({row["status"] for row in template["scenarios"]}, {"pass"})
        self.assertEqual(len(template["scenarios"]), 11)

    def test_shadowing_outcome_is_observed(self):
        job = self.job_root("jra-shadow")
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-shadow-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(
            self._jra_run(job, "stale-skill", FAKE_CODEX_SHADOW="1"),
            0,
            SEQUENCE_LOG[-1],
        )
        stale = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertEqual(stale["observation"]["outcome"], "shadowing")
        self.assertTrue(stale["observation"]["shadowed_rows"])
        self.assertTrue(stale["restoration"]["verified"])
        self.assertFalse((self.home / ".codex/skills/task-handler").exists())

    def _jra_stale_drift(self, name: str, flag: str) -> None:
        job = self.job_root(name)
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold(f"{name}-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        drifted = self.home / ".codex/skills/ouroboros-orca/SKILL.md"
        original = drifted.read_bytes()
        mode = drifted.stat().st_mode
        try:
            self.assertEqual(
                self._jra_run(job, "stale-skill", **{flag: "1"}),
                2,
                SEQUENCE_LOG[-1],
            )
        finally:
            drifted.write_bytes(original)
            drifted.chmod(mode & 0o7777)
        stale = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertTrue(
            any(
                "changed outside declared end state" in problem
                for problem in stale["restoration"]["problems"]
            ),
            stale["restoration"]["problems"],
        )
        self.assertIs(stale["restoration"]["verified"], False)

    def test_content_drift_at_the_same_path_fails_restoration(self):
        # The planted tree is removed; a native read changed an existing
        # skill file's bytes at the same path, which a path-set comparison
        # would miss.
        self._jra_stale_drift("jra-drift", "FAKE_CODEX_DRIFT_SKILLS")

    def test_executable_bit_drift_fails_restoration(self):
        self._jra_stale_drift("jra-chmod", "FAKE_CODEX_CHMOD_SKILLS")

    def test_stale_passing_result_cannot_satisfy_a_failing_gate(self):
        job = self.job_root("jra-stale-result")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        cases = [
            {"id": "VM-UPGRADE-01", "outcome": "pass"},
            {"id": "VM-TASK-START-01", "outcome": "pass"},
            {"id": "VM-EPIC-START-01", "outcome": "pass"},
        ]
        (run_root / "result.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium.vm-acceptance-result/v1",
                    "outcome": "pass",
                    "cases": cases,
                },
                indent=2,
            )
            + "\n"
        )
        # The gate subprocess still refuses the physical host; the stale
        # pass moves aside and cannot satisfy this invocation.
        self.assertEqual(self._jra_run(job, "startup-smokes"), 2, SEQUENCE_LOG[-1])
        smokes = json.loads((results / "startup-smokes.json").read_text())
        self.assertNotEqual(smokes["outcome"], "pass")
        self.assertNotEqual(smokes["exit"], 0)
        self.assertTrue((run_root / "result.stale.json").is_file())
        self.assertFalse((run_root / "result.json").exists())

    def test_case_row_without_outcome_stays_unobserved(self):
        job = self.job_root("jra-no-outcome")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        self._seed_startup_case(run_root, "task-startup")
        self._seed_startup_case(run_root, "epic-startup")
        (run_root / "result.json").write_text("{}\n")
        self._seed_release_startup(run_root)
        self._seed_upgrade_observation(run_root)
        # A row without an explicit outcome never becomes a pass.
        (results / "startup-smokes.json").write_text(
            json.dumps(
                {
                    "exit": 0,
                    "outcome": "pass",
                    "cases": [
                        {"id": "VM-UPGRADE-01", "outcome": "pass"},
                        {"id": "VM-TASK-START-01"},
                    ],
                },
                indent=2,
            )
            + "\n"
        )
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "complete-template"), 0, SEQUENCE_LOG[-1])
        template = json.loads((results / "manual-complete-template.json").read_text())
        statuses = {row["id"]: row["status"] for row in template["scenarios"]}
        self.assertEqual(statuses["task-startup"], "unobserved")
        self.assertEqual(statuses["epic-startup"], "unobserved")
        self.assertEqual(statuses["candidate-upgrade"], "pass")

    def test_step_g_sequence_merges_attempts_without_cycles(self):
        # The documented step g sequence for a fixture whose setup asks for
        # a decision: managed-updates, reply, managed-updates again. The
        # declared record stays valid JSON, holds the settled outcome at the
        # top level, and keeps each earlier attempt.
        job = self.job_root("jra-attempt-history")
        results = self._run_jra_through_managed_updates(job)
        record_path = results / "managed-update-task.json"
        # Replay step g for the task fixture with the decision boundary
        # armed, starting from a fresh record so the sequence performs all
        # three writes itself.
        record_path.unlink()
        # Reset the task setup windows so the sequence dispatches a fresh
        # setup that asks for the decision.
        shutil.rmtree(job / "acceptance-run/operations/task-setup")
        flag = str(job / "acceptance-run/candidate-fixtures/task")
        exit_one = self._jra_run(
            job, "managed-updates", "task", FAKE_CODEX_SETUP_DECISION=flag
        )
        self.assertEqual(exit_one, 2, SEQUENCE_LOG[-1])
        reply = job / "task-reply.txt"
        reply.write_text("Approve the proposed managed update.\n")
        exit_reply = self._jra_run(
            job,
            "reply",
            AQUARIUM_VM_CASE="task-setup",
            AQUARIUM_VM_REPLY_FILE=str(reply),
            FAKE_CODEX_SETUP_DECISION=flag,
        )
        self.assertEqual(exit_reply, 0, SEQUENCE_LOG[-1])
        exit_settled = self._jra_run(
            job, "managed-updates", "task", FAKE_CODEX_SETUP_DECISION=flag
        )
        self.assertEqual(exit_settled, 0, SEQUENCE_LOG[-1])
        document = json.loads(record_path.read_text())
        self.assertEqual(document["exit"], 0)
        self.assertEqual(document["driver_outcome"], "managed-update-observed")
        self.assertGreaterEqual(len(document["attempts"]), 2)
        for attempt in document["attempts"]:
            self.assertNotIn("attempts", attempt)
        # The whole suite result still round-trips: no cycle anywhere.
        json.loads(record_path.read_text())

    def test_unreadable_selection_after_reply_fails_structurally(self):
        job = self.job_root("jra-unreadable-selection")
        results = job / "results/release-acceptance"
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-unreadable-selection-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "runtime-update"), 0, SEQUENCE_LOG[-1])
        current = self.home / ".aquarium/status-runtime/current"
        original = current.read_bytes()
        current.write_bytes(b"versions/\xffgeneration\n")
        reply = job / "runtime-reply.txt"
        reply.write_text("Approve the proposed runtime update.\n")
        try:
            self.assertEqual(
                self._jra_run(
                    job,
                    "runtime-reply",
                    AQUARIUM_VM_REPLY_FILE=str(reply),
                    FAKE_CODEX_RUNTIME_NO_INSTALL="1",
                ),
                2,
                SEQUENCE_LOG[-1],
            )
        finally:
            current.write_bytes(original)
        runtime = json.loads((results / "runtime-update.json").read_text())
        self.assertIs(runtime["approval_completed"], False)
        self.assertIn("unreadable", runtime["problem"])
        # The initial-invocation evidence survives the structured failure.
        self.assertTrue(runtime["initial_thread"])
        self.assertTrue(runtime["versions_before_initial"])
        # The attempted reply enters the append-only history with its
        # snapshots, input binding and known effects.
        self.assertEqual(len(runtime["replies"]), 1)
        attempted = runtime["replies"][0]
        self.assertIs(attempted["approval_completed"], False)
        self.assertIn("unreadable", attempted["problem"])
        self.assertTrue(attempted["versions_before_reply"])
        self.assertTrue(attempted["versions_after_reply"])
        self.assertEqual(
            attempted["reply_sha256"],
            __import__("hashlib").sha256(reply.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            attempted["generations_created_in_reply_window"],
            runtime["generations_created_in_reply_window"],
        )

    def test_machine_prepare_normalizes_a_selected_dev_generation(self):
        # The abort checkpoint leaves the approved-update generation
        # selected; the successor's machine-prepare restores the prior
        # selection first and removes it under its preimage.
        first = self.job_root("jra-selected-generation-first")
        self._run_jra_through_managed_updates(first)
        successor = self.job_root("jra-selected-generation-second")
        self.assertEqual(
            self._jra_run(successor, "machine-prepare"), 0, SEQUENCE_LOG[-1]
        )
        prepare = json.loads(
            (successor / "results/release-acceptance/machine-prepare.json").read_text()
        )
        # The abort preimage is a declared output and is always written.
        declared = successor / "results/release-acceptance/abort-normalization.json"
        self.assertTrue(declared.is_file())
        normalization = prepare["abort_normalization"]
        self.assertTrue(normalization["runtime_generations"])
        self.assertTrue(normalization["runtime_generations"][0]["selected_at_preimage"])
        self.assertTrue(normalization["runtime_generations_removed"])
        self.assertTrue(normalization["residue_disposition_verified"])
        self.assertEqual(normalization["dev_stamped_generations_remaining"], [])
        for name in normalization["runtime_generations_removed"]:
            self.assertFalse(
                (self.home / ".aquarium/status-runtime/versions" / name).exists()
            )

    def test_gate_shim_row_without_outcome_keeps_phase_failing(self):
        job = self.job_root("jra-missing-outcome")
        results = self._run_jra_through_managed_updates(job)
        # A make shim on the Job PATH exits 0 and writes a result whose
        # task row lacks an outcome.
        shim_dir = job / "bin-shim"
        shim_dir.mkdir()
        shim = shim_dir / "make"
        shim.write_text(
            "#!/bin/sh\n"
            'if [ "$1" != "test-vm" ]; then exec /usr/bin/make "$@"; fi\n'
            "python3 - <<'PY'\n"
            "import json, os\n"
            "request = json.load(open(os.environ['AQUARIUM_VM_REQUEST']))\n"
            "run_root = request['run_root']\n"
            "document = {\n"
            "    'schema': 'aquarium.vm-acceptance-result/v1',\n"
            "    'outcome': 'pass',\n"
            "    'cases': [\n"
            "        {'id': 'VM-UPGRADE-01', 'outcome': 'pass'},\n"
            "        {'id': 'VM-TASK-START-01'},\n"
            "        {'id': 'VM-EPIC-START-01', 'outcome': 'pass'},\n"
            "    ],\n"
            "}\n"
            "open(os.path.join(run_root, 'result.json'), 'w').write(\n"
            "    json.dumps(document, indent=2) + '\\n')\n"
            "PY\n"
            "exit 0\n"
        )
        shim.chmod(0o755)
        environment = self.base_env()
        environment["AQUARIUM_GUEST_PYTHON"] = str(job / "bin/guest-python")
        environment["HAEPARI_PARENT_CONTEXT"] = json.dumps(
            [
                {
                    "job_id": "sim-jra-missing-outcome",
                    "lease_generation": 1,
                    "nonce": "ab" * 32,
                }
            ]
        )
        environment["PATH"] = f"{shim_dir}:" + environment["PATH"]
        result = subprocess.run(
            [
                "/bin/sh",
                str(job / "harness/tests/vm/recipes/guest_entry.sh"),
                "--suite",
                "release-acceptance",
                "--phase",
                "startup-smokes",
            ],
            cwd=job / "harness",
            env=environment,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        smokes = json.loads((results / "startup-smokes.json").read_text())
        self.assertEqual(smokes["outcome"], "unobserved")
        self.assertIn("VM-TASK-START-01", smokes["unobserved_cases"])
        rows = {case["id"]: case["outcome"] for case in smokes["cases"]}
        self.assertEqual(rows["VM-TASK-START-01"], "unobserved")

    def test_runtime_update_rerun_refuses_and_preserves_history(self):
        job = self.job_root("jra-runtime-create-once")
        results = self._run_jra_through_managed_updates(job)
        runtime_path = results / "runtime-update.json"
        before = json.loads(runtime_path.read_text())
        self.assertEqual(self._jra_run(job, "runtime-update"), 2, SEQUENCE_LOG[-1])
        after = json.loads(runtime_path.read_text())
        self.assertEqual(after, before)
        self.assertTrue(after["replies"])

    def test_partial_run_stages_every_case_with_recorded_gaps(self):
        job = self.job_root("jra-partial-evidence")
        results = self._run_jra_through_managed_updates(job)
        # No smoke artifacts exist: the run stops after managed updates.
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1])
        staged = json.loads((results / "stage-evidence.json").read_text())
        self.assertIs(staged["ok"], False)
        self.assertEqual(len(staged["archives"]), 10)
        for row in staged["archives"]:
            self.assertTrue((results / f"evidence/{row['case']}.tar").is_file(), row)
        startup = json.loads(
            (results / "evidence/task-startup.manifest.json").read_text()
        )
        self.assertTrue(startup["missing_required"])
        release_startup = json.loads(
            (results / "evidence/release-startup.manifest.json").read_text()
        )
        self.assertTrue(release_startup["missing_required"])
        self.assertTrue(
            any("operation window" in name for name in startup["missing_required"])
        )
        # Existing originals still travel: the setup window is archived.
        setup = json.loads((results / "evidence/task-setup.manifest.json").read_text())
        self.assertEqual(setup["missing_required"], [])
        self.assertTrue(setup["members"])

    def _completed_job_for_cleanup(self, name: str):
        job = self.job_root(name)
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        self._seed_startup_case(run_root, "task-startup")
        self._seed_startup_case(run_root, "epic-startup")
        cases = [
            {"id": "VM-UPGRADE-01", "outcome": "pass"},
            {"id": "VM-TASK-START-01", "outcome": "pass"},
            {"id": "VM-EPIC-START-01", "outcome": "pass"},
        ]
        (results / "startup-smokes.json").write_text(
            json.dumps({"exit": 0, "outcome": "pass", "cases": cases}, indent=2) + "\n"
        )
        (run_root / "result.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium.vm-acceptance-result/v1",
                    "outcome": "pass",
                    "cases": cases,
                },
                indent=2,
            )
            + "\n"
        )
        self._seed_release_startup(run_root)
        self._seed_upgrade_observation(run_root)
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])
        return job, results

    def test_setup_observations_and_window_originals_survive_staging(self):
        job, results = self._completed_job_for_cleanup("setup-transport")
        run_root = job / "acceptance-run"
        captures = sorted((run_root / "setup-observations").rglob("*.json"))
        expected = {
            (phase, fixture)
            for phase in ("baseline", "update")
            for fixture in ("task", "epic", "preservation")
        }
        self.assertTrue(
            expected
            <= {tuple(path.relative_to(run_root).parts[1:3]) for path in captures}
        )
        archived = {}
        for archive in (results / "evidence").glob("*.tar"):
            with tarfile.open(archive) as handle:
                for member in handle.getmembers():
                    if member.name.startswith("setup-observations/"):
                        archived[member.name] = handle.extractfile(member).read()
        for capture in captures:
            payload = archived[capture.relative_to(run_root).as_posix()]
            self.assertEqual(payload, capture.read_bytes())
            self.assertEqual(hashlib.sha256(payload).hexdigest(), capture.stem)
        capture = captures[-1]
        original = capture.read_bytes()
        capture.unlink()
        self.assertEqual(self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1])
        staged = json.loads((results / "stage-evidence.json").read_text())
        self.assertIs(staged["ok"], False)
        self.assertEqual(len(staged["archives"]), 10)
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 1, SEQUENCE_LOG[-1])
        self.assertEqual(
            self.result_of(job, "release-acceptance")["consumer_cleanup"], "unverified"
        )
        capture.write_bytes(b"changed original")
        self.assertEqual(self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1])
        capture.write_bytes(original)
        receipt = max((run_root / "operations/task-setup").glob("*.invocation.json"))
        prefix = receipt.name.removesuffix(".invocation.json")
        for suffix in ("jsonl", "stderr", "setup-before.json", "setup-after.json"):
            with self.subTest(original=suffix):
                path = receipt.with_name(f"{prefix}.{suffix}")
                content = path.read_bytes()
                path.unlink()
                try:
                    self.assertEqual(
                        self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1]
                    )
                    manifest = json.loads(
                        (results / "evidence/task-setup.manifest.json").read_text()
                    )
                    self.assertIn(
                        path.relative_to(run_root).as_posix(),
                        manifest["missing_required"],
                    )
                finally:
                    path.write_bytes(content)
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 0, SEQUENCE_LOG[-1])

    def test_interrupted_operation_windows_keep_originals_and_block_cleanup(self):
        job, results = self._completed_job_for_cleanup("interrupted-windows")
        run_root = job / "acceptance-run"
        for case in ("task-setup", "runtime-update", "task-startup"):
            with self.subTest(case=case):
                directory = run_root / "operations" / case
                receipt = max(directory.glob("*.invocation.json"))
                original = receipt.read_bytes()
                prefix = receipt.name.removesuffix(".invocation.json")
                companions = {
                    path.relative_to(run_root).as_posix(): path.read_bytes()
                    for path in directory.glob(f"{prefix}.*")
                    if path != receipt
                }
                receipt.unlink()
                try:
                    self.assertEqual(
                        self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1]
                    )
                    manifest = json.loads(
                        (results / f"evidence/{case}.manifest.json").read_text()
                    )
                    self.assertIn(
                        receipt.relative_to(run_root).as_posix(),
                        manifest["missing_required"],
                    )
                    with tarfile.open(results / f"evidence/{case}.tar") as archive:
                        for name, payload in companions.items():
                            self.assertEqual(archive.extractfile(name).read(), payload)
                    self.assertEqual(
                        self._jra_run(job, "consumer-cleanup"), 1, SEQUENCE_LOG[-1]
                    )
                finally:
                    receipt.write_bytes(original)
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 0, SEQUENCE_LOG[-1])

    def test_failed_skill_identity_blocks_cleanup(self):
        job, results = self._completed_job_for_cleanup("jra-cleanup-gate-skill")
        document = json.loads((results / "skill-identity.json").read_text())
        document["comparisons"]["all_passed"] = False
        (results / "skill-identity.json").write_text(
            json.dumps(document, indent=2) + "\n"
        )
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 1, SEQUENCE_LOG[-1])
        result = self.result_of(job, "release-acceptance")
        self.assertEqual(result["outcome"], "fail")
        self.assertEqual(result["consumer_cleanup"], "unverified")
        self.assertIn("skill-identity.json", result["problem"])

    def test_failed_managed_update_blocks_cleanup(self):
        job, results = self._completed_job_for_cleanup("jra-cleanup-gate-managed")
        document = json.loads((results / "managed-update-task.json").read_text())
        document["exit"] = 2
        document.pop("driver_outcome", None)
        (results / "managed-update-task.json").write_text(
            json.dumps(document, indent=2) + "\n"
        )
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 1, SEQUENCE_LOG[-1])
        result = self.result_of(job, "release-acceptance")
        self.assertEqual(result["outcome"], "fail")
        self.assertEqual(result["consumer_cleanup"], "unverified")
        self.assertIn("managed-update-task.json", result["problem"])

    def _config_with_features(self, home) -> None:
        config = home / ".codex/config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            'notify = ["noop"]\n\n'
            "[features]\n"
            "shell = true\n\n"
            '[plugins."aquarium@root-kernel"]\n'
            "enabled = true\n",
            encoding="utf-8",
        )

    def test_rule_content_drift_fails_restoration(self):
        job = self.job_root("jra-settings-drift-rule")
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-settings-drift-rule-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        rules = self.home / ".codex/rules/ouroboros.md"
        original = rules.read_bytes()
        # The drift happens during the native read, like the skills drift.
        self.assertEqual(
            self._jra_run(job, "stale-skill", FAKE_CODEX_DRIFT_RULES="1"),
            2,
            SEQUENCE_LOG[-1],
        )
        rules.write_bytes(original)
        stale = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertIs(stale["restoration"]["verified"], False)
        self.assertTrue(
            any(
                "rule content identities changed" in problem
                for problem in stale["restoration"]["problems"]
            ),
            stale["restoration"]["problems"],
        )

    def test_plugin_enabled_flip_fails_restoration(self):
        job = self.job_root("jra-settings-drift-config")
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-settings-drift-config-prefix")
        self._config_with_features(self.home)
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        config = self.home / ".codex/config.toml"
        original = config.read_bytes()
        self.assertEqual(
            self._jra_run(job, "stale-skill", FAKE_CODEX_FLIP_PLUGIN="1"),
            2,
            SEQUENCE_LOG[-1],
        )
        config.write_bytes(original)
        stale = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertIs(stale["restoration"]["verified"], False)
        self.assertTrue(
            any(
                "effective configuration 'enabled_plugins' changed" in problem
                for problem in stale["restoration"]["problems"]
            ),
            stale["restoration"]["problems"],
        )

    def test_no_setup_windows_stages_every_later_case(self):
        job = self.job_root("jra-no-setup-windows")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        # Simulate an abort before any setup window existed: remove all
        # setup operations but keep the later originals.
        for case in ("task-setup", "epic-setup", "preservation-setup"):
            shutil.rmtree(run_root / "operations" / case)
        self._seed_startup_case(run_root, "task-startup")
        self._seed_startup_case(run_root, "epic-startup")
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1])
        staged = json.loads((results / "stage-evidence.json").read_text())
        self.assertIs(staged["ok"], False)
        by_case = {row["case"]: row for row in staged["archives"]}
        self.assertEqual(len(staged["archives"]), 10)
        # The later cases still stage with their originals.
        for case in ("runtime-update", "task-startup", "epic-startup", "stale-skill"):
            self.assertIn(case, by_case)
            self.assertTrue((results / f"evidence/{case}.tar").is_file(), case)
        self.assertGreater(by_case["task-startup"]["members"], 0)
        self.assertGreater(by_case["stale-skill"]["members"], 0)
        # The runtime-update case keeps its own existing window; the setup
        # cases that lost theirs stage empty archives with named gaps.
        self.assertGreater(by_case["runtime-update"]["members"], 0)
        # Each setup case names its missing window class.
        for case in ("task-setup", "epic-setup", "preservation-setup"):
            manifest = json.loads(
                (results / f"evidence/{case}.manifest.json").read_text()
            )
            self.assertIn(
                f"operations/{case}/ operation window",
                manifest["missing_required"],
            )

    def test_malformed_startup_evidence_still_archives_originals(self):
        job = self.job_root("jra-malformed-originals")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        self._seed_startup_case(run_root, "task-startup")
        self._seed_startup_case(run_root, "epic-startup")
        (run_root / "task-startup/startup-evidence.json").write_text("{not json")
        (run_root / "result.json").write_text("{}\n")
        self._seed_release_startup(run_root)
        self._seed_upgrade_observation(run_root)
        (results / "startup-smokes.json").write_text(
            json.dumps({"exit": 0, "outcome": "pass", "cases": []}, indent=2) + "\n"
        )
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1])
        staged = json.loads((results / "stage-evidence.json").read_text())
        self.assertIs(staged["ok"], False)
        joined = "\n".join(staged["problems"])
        self.assertIn("cannot be validated", joined)
        manifest = json.loads(
            (results / "evidence/task-startup.manifest.json").read_text()
        )
        member_names = [record["path"] for record in manifest["members"]]
        # The native observation, checks and window still travel.
        self.assertIn("task-native-observation.json", member_names)
        self.assertIn("task-checks.json", member_names)
        self.assertIn("operations/task-startup/000.invocation.json", member_names)

    def test_malformed_startup_evidence_fails_staging(self):
        job = self.job_root("jra-malformed-evidence-malformed")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        self._seed_startup_case(run_root, "task-startup")
        self._seed_startup_case(run_root, "epic-startup")
        evidence = run_root / "task-startup/startup-evidence.json"
        for child in (
            "executor-assignment.json",
            "evaluator-assignment.json",
            "executor-result.json",
            "evaluator-assessment.json",
        ):
            (run_root / "task-startup" / child).unlink()
        (run_root / "result.json").write_text("{}\n")
        self._seed_release_startup(run_root)
        self._seed_upgrade_observation(run_root)
        (results / "startup-smokes.json").write_text(
            json.dumps({"exit": 0, "outcome": "pass", "cases": []}, indent=2) + "\n"
        )
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        for label, raw in (
            ("malformed", "{not json"),
            ("array", "[]"),
            ("null", "null"),
        ):
            with self.subTest(evidence=label):
                evidence.write_text(raw)
                self.assertEqual(
                    self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1]
                )
                staged = json.loads((results / "stage-evidence.json").read_text())
                self.assertIs(staged["ok"], False)
                joined = "\n".join(staged["problems"])
                self.assertIn("cannot be validated", joined)

    def test_staging_fails_for_each_missing_required_record(self):
        # Negative coverage on real-shape artifacts: a missing native
        # observation, a missing child report and a missing operation
        # window each fail staging with the named record.
        job = self.job_root("jra-missing-original")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        for case in ("task-startup", "epic-startup"):
            self._seed_startup_case(run_root, case)
        (run_root / "result.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium.vm-acceptance-result/v1",
                    "outcome": "pass",
                    "cases": [
                        {"id": "VM-UPGRADE-01", "outcome": "pass"},
                        {"id": "VM-TASK-START-01", "outcome": "pass"},
                        {"id": "VM-EPIC-START-01", "outcome": "pass"},
                    ],
                }
            )
            + "\n"
        )
        self._seed_release_startup(run_root)
        self._seed_upgrade_observation(run_root)
        (results / "startup-smokes.json").write_text(
            json.dumps({"exit": 0, "outcome": "pass", "cases": []}, indent=2) + "\n"
        )
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])
        removals = (
            ("task-native-observation.json", run_root, "task-native-observation.json"),
            (
                "evaluator-assessment.json",
                run_root / "task-startup",
                "evaluator-assessment.json",
            ),
            (
                "000.invocation.json",
                run_root / "operations/task-startup",
                "operations/task-startup/000.invocation.json",
            ),
        )
        for relative, root, needle in removals:
            with self.subTest(missing=relative):
                target = root / relative
                original = target.read_bytes()
                target.unlink()
                try:
                    self.assertEqual(
                        self._jra_run(job, "stage-evidence"),
                        2,
                        SEQUENCE_LOG[-1],
                    )
                    staged = json.loads((results / "stage-evidence.json").read_text())
                    self.assertIs(staged["ok"], False)
                    joined = "\n".join(staged["problems"])
                    self.assertIn(needle, joined)
                    manifest = json.loads(
                        (results / "evidence/task-startup.manifest.json").read_text()
                    )
                    self.assertTrue(
                        any(needle in name for name in manifest["missing_required"]),
                        manifest["missing_required"],
                    )
                finally:
                    target.write_bytes(original)
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])

    def test_generation_created_before_the_reply_fails_approval(self):
        # A generation created before the reply cannot establish approval.
        job = self.job_root("jra-reply-window")
        results = job / "results/release-acceptance"
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-reply-window-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "runtime-update"), 0, SEQUENCE_LOG[-1])
        # Install the candidate runtime BEFORE the reply, as a self-updating
        # or pre-approved installation would.
        source = job / "artifact/plugins/aquarium/tools/aquarium-status"
        environment = self.base_env()
        install = subprocess.run(
            [
                environment["AQUARIUM_GUEST_PYTHON"],
                "-B",
                str(source / "install.py"),
                "install",
                "--source",
                str(source),
                "--approve-install",
                "--approve-launcher",
            ],
            capture_output=True,
            text=True,
            env=environment,
            timeout=300,
            check=False,
        )
        self.assertEqual(install.returncode, 0, install.stderr)
        reply = job / "runtime-reply.txt"
        reply.write_text("Approve the proposed runtime update.\n")
        self.assertEqual(
            self._jra_run(job, "runtime-reply", AQUARIUM_VM_REPLY_FILE=str(reply)),
            2,
            SEQUENCE_LOG[-1],
        )
        runtime = json.loads((results / "runtime-update.json").read_text())
        self.assertIs(runtime["approval_completed"], False)
        self.assertEqual(runtime["generations_created_in_reply_window"], [])
        self.assertEqual(runtime["reply_exit"], 0)
        self.assertTrue(runtime["same_thread"])

    def test_runtime_record_without_workflow_exit_fails_cleanup(self):
        # A missing workflow exit must prevent cleanup from claiming success.
        job = self.job_root("jra-workflow-exit")
        results = self._run_jra_through_managed_updates(job)
        document = json.loads((results / "runtime-update.json").read_text())
        del document["workflow_exit"]
        (results / "runtime-update.json").write_text(
            json.dumps(document, indent=2) + "\n"
        )
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 1, SEQUENCE_LOG[-1])
        result = self.result_of(job, "release-acceptance")
        self.assertIn("runtime-update.json", result["problem"])

    def test_ignored_scope_outcome_is_a_reported_gap(self):
        job = self.job_root("jra-ignored")
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-ignored-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(
            self._jra_run(job, "stale-skill", FAKE_CODEX_IGNORE_SCOPE="1"),
            2,
            SEQUENCE_LOG[-1],
        )
        stale = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertEqual(stale["observation"]["outcome"], "ignored-scope")
        self.assertIn("reported gap", stale["observation"]["decision"])
        # The planted tree is still removed and restoration verified; the
        # outcome itself, never a pass, keeps the scenario unobserved.
        self.assertTrue(stale["restoration"]["verified"])
        self.assertFalse((self.home / ".codex/skills/task-handler").exists())

    def test_stage_evidence_enforces_aggregate_bound_and_removes_stale_archive(self):
        job, results = self._completed_job_for_cleanup("jra-archive-bounds-bounds")
        run_root = job / "acceptance-run"
        # Initial stage-evidence in _completed_job_for_cleanup published all 9
        # archives with archive_present=True.
        for case in ("task-setup", "epic-startup", "stale-skill"):
            self.assertTrue((results / f"evidence/{case}.tar").is_file())
            manifest = json.loads(
                (results / f"evidence/{case}.manifest.json").read_text()
            )
            self.assertIs(manifest["archive_present"], True)
        # Pass 1 (aggregate bound): write 30 MiB payloads (each under the
        # 32 MiB per-archive bound) into all 9 cases (9 * 30 MiB = 270 MiB >
        # 256 MiB total bound) so the first 8 archives fit (240 MiB) and the
        # 9th archive (stale-skill) exceeds the 256 MiB aggregate bound before
        # exposure and unlinks its pre-existing .tar.
        thirty_mib = b"x" * (30 * 1024 * 1024)
        for target_rel in (
            "released-task.last",
            "upgrade-observation.json",
            "operations/task-setup/000.stderr",
            "operations/epic-setup/000.stderr",
            "operations/preservation-setup/000.stderr",
            "operations/runtime-update/000.stderr",
            "operations/task-startup/000.stderr",
            "operations/epic-startup/000.stderr",
            "stale-skill-originals/extra.bin",
        ):
            target_file = run_root / target_rel
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_bytes(thirty_mib)
        self.assertEqual(self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1])
        staged = json.loads((results / "stage-evidence.json").read_text())
        self.assertIs(staged["ok"], False)
        self.assertLessEqual(staged["total_size"], 256 * 1024 * 1024)
        self.assertTrue((results / "evidence/task-setup.tar").is_file())
        self.assertTrue((results / "evidence/epic-startup.tar").is_file())
        self.assertFalse((results / "evidence/stale-skill.tar").exists())
        stale_manifest = json.loads(
            (results / "evidence/stale-skill.manifest.json").read_text()
        )
        self.assertIs(stale_manifest["archive_present"], False)
        self.assertIsNone(stale_manifest["sha256"])
        self.assertEqual(stale_manifest["members"], [])
        self.assertTrue(
            any("total bound" in item for item in stale_manifest["missing_required"]),
            stale_manifest["missing_required"],
        )
        self.assertTrue(
            any("total bound" in item for item in stale_manifest["gaps"]),
            stale_manifest["gaps"],
        )
        # Pass 2 (per-archive bound): write 33 MiB (> 32 MiB per-archive bound)
        # into epic-startup and rerun stage-evidence; epic-startup.tar from
        # Pass 1 is unlinked and its manifest rewritten with archive_present=False.
        (run_root / "operations/epic-startup/000.stderr").write_bytes(
            b"y" * (33 * 1024 * 1024)
        )
        self.assertEqual(self._jra_run(job, "stage-evidence"), 2, SEQUENCE_LOG[-1])
        self.assertFalse((results / "evidence/epic-startup.tar").exists())
        epic_manifest = json.loads(
            (results / "evidence/epic-startup.manifest.json").read_text()
        )
        self.assertIs(epic_manifest["archive_present"], False)
        self.assertIsNone(epic_manifest["sha256"])
        self.assertEqual(epic_manifest["members"], [])
        self.assertTrue(
            any(
                "exceeds the 33554432-byte bound" in item
                for item in epic_manifest["missing_required"]
            ),
            epic_manifest["missing_required"],
        )
        self.assertTrue(
            any(
                "exceeds the 33554432-byte bound" in item
                for item in epic_manifest["gaps"]
            ),
            epic_manifest["gaps"],
        )

    def test_stale_skill_accepts_reordered_plugin_tables_and_fails_corrupt_toml(
        self,
    ):
        job = self.job_root("jra-config-normalization-config")
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-config-normalization-config-prefix")
        config = self.home / ".codex/config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            'notify = ["noop"]\n\n'
            "[features]\n"
            "shell = true\n\n"
            '[plugins."aquarium@root-kernel"]\n'
            "enabled = true\n\n"
            '[plugins."formatter@openai-bundled"]\n'
            "enabled = false\n",
            encoding="utf-8",
        )
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(
            self._jra_run(
                job, "stale-skill", FAKE_CODEX_REORDER_PLUGINS_AND_COMMENT="1"
            ),
            0,
            SEQUENCE_LOG[-1],
        )
        stale = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertIs(stale["restoration"]["verified"], True, stale["restoration"])
        # Corrupt TOML during native read fails restoration explicitly.
        self.assertEqual(
            self._jra_run(job, "stale-skill", FAKE_CODEX_CORRUPT_CONFIG="1"),
            2,
            SEQUENCE_LOG[-1],
        )
        corrupt = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertIs(corrupt["restoration"]["verified"], False)
        self.assertTrue(
            any(
                "config.toml failed to parse" in problem
                for problem in corrupt["restoration"]["problems"]
            ),
            corrupt["restoration"]["problems"],
        )

    def test_failed_runtime_reply_records_attempt_and_blocks_cleanup(self):
        job = self.job_root("jra-failed-reply-reply")
        results = self._run_jra_through_managed_updates(job)
        run_root = job / "acceptance-run"
        for case in ("task-startup", "epic-startup"):
            self._seed_startup_case(run_root, case)
        cases = [
            {"id": "VM-UPGRADE-01", "outcome": "pass"},
            {"id": "VM-TASK-START-01", "outcome": "pass"},
            {"id": "VM-EPIC-START-01", "outcome": "pass"},
        ]
        (results / "startup-smokes.json").write_text(
            json.dumps({"exit": 0, "outcome": "pass", "cases": cases}, indent=2) + "\n"
        )
        (run_root / "result.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium.vm-acceptance-result/v1",
                    "outcome": "pass",
                    "cases": cases,
                },
                indent=2,
            )
            + "\n"
        )
        self._seed_release_startup(run_root)
        self._seed_upgrade_observation(run_root)
        # Remove the generation created in the first passing reply so the
        # second (failing) reply creates a fresh generation in its own window
        # before exiting nonzero.
        first_runtime = json.loads((results / "runtime-update.json").read_text())
        self.assertIs(first_runtime["approval_completed"], True)
        for gen in first_runtime["generations_created_in_reply_window"]:
            shutil.rmtree(
                self.home / ".aquarium/status-runtime/versions" / gen,
                ignore_errors=True,
            )
        (self.home / ".aquarium/status-runtime/current").write_text(
            f"versions/{'a' * 64}-py3.14\n"
        )
        reply = job / "runtime-reply-fail.txt"
        reply.write_text("Approve the proposed runtime update again.\n")
        self.assertEqual(
            self._jra_run(
                job,
                "runtime-reply",
                AQUARIUM_VM_REPLY_FILE=str(reply),
                FAKE_CODEX_FAIL_RUNTIME_REPLY="1",
            ),
            2,
            SEQUENCE_LOG[-1],
        )
        updated = json.loads((results / "runtime-update.json").read_text())
        self.assertIs(updated["approval_completed"], False)
        self.assertNotEqual(updated["workflow_exit"], 0)
        self.assertEqual(len(updated["replies"]), 2)
        failed_attempt = updated["replies"][1]
        self.assertIs(failed_attempt["approval_completed"], False)
        self.assertNotEqual(failed_attempt["reply_exit"], 0)
        self.assertTrue(failed_attempt["generations_created_in_reply_window"])
        ledger = json.loads((results / "run-ledger.json").read_text())
        for gen in failed_attempt["generations_created_in_reply_window"]:
            self.assertIn(gen, ledger["generations"])
        self.assertEqual(self._jra_run(job, "stale-skill"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "consumer-cleanup"), 1, SEQUENCE_LOG[-1])
        result = self.result_of(job, "release-acceptance")
        self.assertEqual(result["outcome"], "fail")
        self.assertEqual(result["consumer_cleanup"], "unverified")
        self.assertIn("runtime-update.json", result["problem"])

    def test_runtime_update_rerun_refuses_before_reply_and_on_malformed_record(self):
        job = self.job_root("jra-initial-record-guard")
        results = job / "results/release-acceptance"
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-initial-record-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(self._jra_run(job, "runtime-update"), 0, SEQUENCE_LOG[-1])
        runtime_path = results / "runtime-update.json"
        pre_reply_bytes = runtime_path.read_bytes()
        pre_reply_doc = json.loads(pre_reply_bytes.decode("utf-8"))
        self.assertEqual(pre_reply_doc["replies"], [])
        # Rerun before any reply is refused and preserves exact bytes.
        self.assertEqual(self._jra_run(job, "runtime-update"), 2, SEQUENCE_LOG[-1])
        self.assertEqual(runtime_path.read_bytes(), pre_reply_bytes)
        # Malformed or non-dict records are also refused without overwriting.
        reply = job / "runtime-reply.txt"
        reply.write_text("Approve the proposed runtime update.\n")
        for label, payload in (("malformed", b"{not-json"), ("list", b"[]\n")):
            with self.subTest(record=label):
                runtime_path.write_bytes(payload)
                self.assertEqual(
                    self._jra_run(job, "runtime-update"), 2, SEQUENCE_LOG[-1]
                )
                self.assertEqual(runtime_path.read_bytes(), payload)
                self.assertEqual(
                    self._jra_run(
                        job, "runtime-reply", AQUARIUM_VM_REPLY_FILE=str(reply)
                    ),
                    1,
                    SEQUENCE_LOG[-1],
                )
                self.assertEqual(runtime_path.read_bytes(), payload)

    def test_stale_result_travels_in_upgrade_archive_when_present(self):
        job, results = self._completed_job_for_cleanup("jra-stale-result-stale-result")
        run_root = job / "acceptance-run"
        (run_root / "result.stale.json").write_text('{"stale": true}\n')
        self.assertEqual(self._jra_run(job, "stage-evidence"), 0, SEQUENCE_LOG[-1])
        manifest = json.loads((results / "evidence/upgrade.manifest.json").read_text())
        member_paths = [row["path"] for row in manifest["members"]]
        self.assertIn("result.stale.json", member_paths)
        self.assertEqual(manifest["missing_required"], [])

    def test_stale_skill_records_non_root_kernel_cache_observations_and_fails_root_kernel_drift(
        self,
    ):
        job = self.job_root("jra-cache-observation-cache")
        self._reset_fake_guest_for_jra()
        self._c10_establish_prior_for_hold("jra-cache-observation-prefix")
        self.assertEqual(self._jra_run(job, "machine-prepare"), 0, SEQUENCE_LOG[-1])
        self._upgrade_jra_dependency(job)
        self.assertEqual(self._jra_run(job, "candidate-install"), 0, SEQUENCE_LOG[-1])
        self.assertEqual(
            self._jra_run(job, "stale-skill", FAKE_CODEX_DRIFT_BUNDLED_CACHE="1"),
            0,
            SEQUENCE_LOG[-1],
        )
        stale = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertIs(stale["restoration"]["verified"], True)
        self.assertEqual(stale["restoration"]["problems"], [])
        self.assertTrue(
            any(
                ".codex/plugins/cache/openai-bundled/plugin.txt" in item
                for item in stale["restoration"]["codex_owned_cache_observations"]
            ),
            stale["restoration"]["codex_owned_cache_observations"],
        )
        # Drift under .codex/plugins/cache/root-kernel/ still fails restoration.
        self.assertEqual(
            self._jra_run(job, "stale-skill", FAKE_CODEX_DRIFT_ROOT_KERNEL_CACHE="1"),
            2,
            SEQUENCE_LOG[-1],
        )
        rk_stale = json.loads(
            (job / "results/release-acceptance/stale-skill.json").read_text()
        )
        self.assertIs(rk_stale["restoration"]["verified"], False)
        self.assertTrue(
            any(
                "codex-plugin-cache" in problem
                for problem in rk_stale["restoration"]["problems"]
            ),
            rk_stale["restoration"]["problems"],
        )


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
