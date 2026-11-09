from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[2]
BUNDLE_PATH = REPOSITORY / "tests/vm/host_bundle.py"
PROFILES_ROOT = REPOSITORY / "tests/vm/profiles"
STABLE_PROFILE_NAME = "proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0.json"

GUEST_CONTEXT = {
    "schema": "aquarium.vm-guest-context/v1",
    "expected_guest_uuid": "11111111-2222-3333-4444-555555555555",
    "guest_home": "/Users/synthetic",
    "guest_path": "/Users/synthetic/.local/bin:/usr/bin:/bin",
    "guest_python": "/Users/synthetic/.local/share/uv/python/synthetic/bin/python3.14",
    "guest_codex": "/Users/synthetic/.local/bin/codex",
    "guest_podway": "/Users/synthetic/.local/bin/podway",
    "guest_marketplace_name": "synthetic-market",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_validator():
    return load_module(
        "vm_profile_validator_bundle_unit",
        PROFILES_ROOT / "validate_profiles.py",
    )


class HostBundleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-host-bundle-"))
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        cls.repository = cls.work / "repository"
        cls.repository.mkdir()
        for argv in (
            ["init", "-q"],
            ["config", "user.name", "T"],
            ["config", "user.email", "t@example.invalid"],
        ):
            subprocess.run(["git", "-C", str(cls.repository), *argv], check=True)
        marketplace = cls.repository / ".agents/plugins"
        marketplace.mkdir(parents=True)
        (marketplace / "marketplace.json").write_text('{"name": "synthetic-market"}\n')
        plugin = cls.repository / "plugins/aquarium/.codex-plugin"
        plugin.mkdir(parents=True)
        (plugin / "plugin.json").write_text('{"version": "0.1.21"}\n')
        status = cls.repository / "plugins/aquarium/tools/aquarium-status"
        status.mkdir(parents=True)
        (status / "install.py").write_text("# synthetic installer\n")
        dev = cls.repository / "plugins/aquarium/tools/aquarium-dev"
        dev.mkdir(parents=True)
        source_dev = REPOSITORY / "plugins/aquarium/tools/aquarium-dev"
        for module in sorted(source_dev.glob("*.py")):
            shutil.copyfile(module, dev / module.name)
        (cls.repository / "Makefile").write_text(
            "aquarium-dev-build:\n"
            "\t@python3 plugins/aquarium/tools/aquarium-dev/"
            "build_aquarium_artifact.py build\n"
        )
        # The harness lives inside the fixture repository: tracked files
        # are committed, and candidate-style untracked files appear after
        # the commit, exactly like development reality.
        cls.harness = cls.repository / "tests/vm/recipes"
        (cls.harness / "scenarios").mkdir(parents=True)
        (cls.harness / ".gitignore").write_text(".omc/\n__pycache__/\n")
        (cls.harness / "guest_main.py").write_text("print('synthetic')\n")
        (cls.harness / "recipe_lib.py").write_text("# synthetic library\n")
        (cls.harness / "tracked.md").write_text("tracked harness input\n")
        (cls.harness / "scenarios/probe.md").write_text("scenario\n")
        (cls.harness / "scenarios/manual-hold.md").write_text("hold scenario\n")
        (cls.harness / "scenarios/podway-upgrade.md").write_text(
            "manual Podway upgrade\n"
        )
        (cls.harness / "scenarios/sorage-adoption.md").write_text("Sorage cases\n")
        (cls.harness / "scenarios/mulgae-adoption.md").write_text("Mulgae cases\n")
        (cls.harness / "scenarios/epic-squad.md").write_text("native Squad cases\n")
        (cls.harness / "scenarios/release-orchestration.md").write_text(
            "release role cases\n"
        )
        skills = cls.repository / "plugins/aquarium/skills/dev-setup"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("synthetic released setup\n")
        (cls.harness / "scenarios/release-acceptance.md").write_text(
            "release-acceptance runbook\n"
        )
        subprocess.run(["git", "-C", str(cls.repository), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(cls.repository), "commit", "-qm", "fixture"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(cls.repository), "tag", "-a", "v0.1.21", "-m", "prior"],
            check=True,
        )
        (cls.harness / "guest_entry.sh").write_text("#!/bin/sh\nexit 0\n")
        (cls.harness / "guest_entry.sh").chmod(0o755)
        (cls.harness / "untracked-notes.txt").write_text("untracked but visible\n")
        ignored = cls.harness / ".omc/state/sessions/s1/pre-tool-advisory-throttle.json"
        ignored.parent.mkdir(parents=True)
        ignored.write_text("{}\n")
        pycache = cls.harness / "__pycache__/guest_main.cpython-314.pyc"
        pycache.parent.mkdir(parents=True)
        pycache.write_bytes(b"\x00")
        cls.git_sha = subprocess.run(
            ["git", "-C", str(cls.repository), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        cls.artifact = cls.work / "artifact/marketplace"
        for relative, content in (
            (".agents/plugins/marketplace.json", '{"name": "synthetic-market"}\n'),
            ("plugins/aquarium/.codex-plugin/plugin.json", "{}\n"),
            ("plugins/aquarium/tools/aquarium-status/install.py", "# candidate\n"),
            ("plugins/aquarium/skills/dev-setup/SKILL.md", "# dev-setup\n"),
        ):
            target = cls.artifact / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        sha12 = cls.git_sha[:12]
        (cls.artifact / "plugins/aquarium/.codex-plugin/plugin.json").write_text(
            json.dumps({"version": f"0.1.21-dev.{sha12}"}, indent=2) + "\n"
        )
        cls.manifest = {
            "schema": "aquarium-dev-artifact-manifest/v1",
            "git_sha": cls.git_sha,
            "development_version": f"v0.1.21-dev.{sha12}",
            "artifact_path": "marketplace",
        }
        cls.module = load_module("vm_host_bundle_unit", BUNDLE_PATH)
        cls.module.HARNESS_ROOT = cls.harness
        cls.context_path = cls.work / "guest-context.json"
        cls.context_path.write_text(json.dumps(GUEST_CONTEXT))

    def build(self, suite: str = "install", **overrides):
        run_dir = Path(tempfile.mkdtemp(prefix="vm-run-", dir=str(self.work)))
        run_dir.chmod(0o700)
        parameters = {
            "run_dir": run_dir,
            "context_path": self.context_path,
            "suites_selection": suite,
            "resource_id": "synthetic-resource",
            "mode": "auto",
            "repository": self.repository,
            "candidate_sha": self.git_sha,
            "artifact_dir": self.artifact,
            "artifact_manifest": self.manifest,
        }
        parameters.update(overrides)
        if suite == "all" and "baseline_profile" not in overrides:
            parameters["baseline_profile"] = self.baseline()
        if (
            suite in {"release-acceptance", "release-orchestration"}
            and "podway_release" not in overrides
        ):
            release = (run_dir / "release-input").resolve()
            hashes = {}
            for relative in self.module.PODWAY_RELEASE_FILES:
                path = release / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"synthetic {relative}\n".encode())
                hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            parameters["podway_release"] = release
            with mock.patch.object(self.module, "PODWAY_RELEASE_FILES", hashes):
                record = self.module.build_bundle(**parameters)
        else:
            record = self.module.build_bundle(**parameters)
        return run_dir, record

    def baseline(self):
        document = json.loads(
            (PROFILES_ROOT / self.module.STABLE_PROFILE_NAME).read_text()
        )
        plugin = next(
            row for row in document["components"] if row["name"] == "aquarium-plugin"
        )
        plugin["provenance"]["tag_commit"] = self.git_sha
        plugin["skill_tree"]["sha256"] = self.module.skill_tree_digest_from_directory(
            self.repository / "plugins/aquarium/skills"
        )
        path = Path(tempfile.mkdtemp(dir=self.work)).resolve() / "baseline.json"
        path.write_text(json.dumps(document, indent=2) + "\n")
        return path

    def test_feature_suite_requires_explicit_released_baseline(self):
        with self.assertRaises(self.module.BundleError):
            self.build("release-orchestration", mode="manual")

    def test_feature_and_release_acceptance_seal_exact_optional_profile(self):
        for name in ("release-orchestration", "release-acceptance", "manual-hold"):
            profile = self.baseline()
            run_dir, record = self.build(name, mode="manual", baseline_profile=profile)
            self.assertEqual(
                (run_dir / "bundle/profile/stable.json").read_bytes(),
                profile.read_bytes(),
            )
            spec = json.loads((run_dir / "spec-0.json").read_text())
            self.assertEqual(record["declared_suites"], [name])
            self.assertIn("profile/stable.json", spec["input"]["selected_files"])
            if name == "release-orchestration":
                self.assertEqual(len(spec["workload"]["required_outputs"]), 34)

    def test_optional_profile_refuses_symlink_version_and_source_pin_drift(self):
        for fault in ("symlink", "version", "commit", "tree"):
            profile = self.baseline()
            document = json.loads(profile.read_text())
            plugin = next(
                row
                for row in document["components"]
                if row["name"] == "aquarium-plugin"
            )
            if fault == "symlink":
                link = profile.with_name("link.json")
                link.symlink_to(profile)
                profile = link
            elif fault == "version":
                plugin["version"] = "0.1.22"
            elif fault == "commit":
                plugin["provenance"]["tag_commit"] = "f" * 40
            else:
                plugin["skill_tree"]["sha256"] = "0" * 64
            if fault != "symlink":
                profile.write_text(json.dumps(document))
            with self.assertRaises(self.module.BundleError):
                self.build("manual-hold", mode="manual", baseline_profile=profile)

    def test_release_acceptance_requires_verified_podway_input(self):
        with self.assertRaises(self.module.BundleError):
            self.build(suite="release-acceptance", mode="manual", podway_release=None)

    def test_build_seals_inputs_and_builds_v2_specs(self):
        run_dir, record = self.build()
        spec = json.loads((run_dir / "spec-0.json").read_text())
        self.assertEqual(spec["schema"], "haepari.job/v2")
        self.assertEqual(spec["resource_id"], "synthetic-resource")
        self.assertEqual(spec["effects"]["mode"], "live")
        self.assertEqual(spec["provenance"]["evidence_class"], "development")
        self.assertEqual(
            record["installation_binding"]["development_version"],
            self.manifest["development_version"],
        )
        for name in spec["input"]["selected_files"]:
            self.assertTrue((run_dir / "bundle" / name).is_file(), name)
        self.assertEqual(
            spec["input"]["inventory_digest"],
            record["installation_binding"]["inventory_digest"],
        )
        inputs = json.loads((run_dir / "bundle/harness/inputs.json").read_text())
        self.assertIn("harness/inputs.json", spec["input"]["selected_files"])
        self.assertEqual(
            inputs["candidate"]["artifact_tree_sha256"],
            spec["provenance"]["candidate_digest"],
        )
        self.assertEqual(
            inputs["harness_tree_sha256"], spec["provenance"]["tests_digest"]
        )
        self.assertTrue((run_dir / "bundle/checkout.bundle").is_file())
        sealed_manifest = json.loads(
            (run_dir / "bundle/artifact-manifest.json").read_text()
        )
        self.assertEqual(sealed_manifest["git_sha"], self.git_sha)
        self.assertIn("artifact-manifest.json", spec["input"]["selected_files"])

        self.assertTrue(
            (
                run_dir
                / "bundle/prior-artifact/plugins/aquarium/.codex-plugin/plugin.json"
            ).is_file()
        )
        candidate_profile = (run_dir / "bundle/profile/candidate.json").read_bytes()
        self.assertEqual(
            hashlib.sha256(candidate_profile).hexdigest(),
            spec["environment"]["profile_digest"],
        )

    def test_all_keeps_podway_upgrade_profile_separate(self):
        release = Path(
            tempfile.mkdtemp(prefix="release-input-", dir=self.work)
        ).resolve()
        hashes = {}
        for relative in self.module.PODWAY_RELEASE_FILES:
            path = release / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"synthetic {relative}\n".encode())
            hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        with mock.patch.object(self.module, "PODWAY_RELEASE_FILES", hashes):
            run_dir, record = self.build("all", podway_release=release)
        profiles = {
            name: json.loads((run_dir / f"bundle/profile/{name}.json").read_text())
            for name in ("stable", "candidate", "podway-candidate")
        }
        for name, profile in profiles.items():
            podway = next(
                row for row in profile["components"] if row["name"] == "podway"
            )
            self.assertEqual(
                podway["version"],
                "v0.2.16" if name == "podway-candidate" else "v0.2.14",
            )
        for index, name in enumerate(record["declared_suites"]):
            spec = json.loads((run_dir / f"spec-{index}.json").read_text())
            if name == "epic-squad":
                outputs = spec["workload"]["required_outputs"]
                cases = self.module.load_suites()["suites"][name]["manual"][
                    "required_scenarios"
                ]
                self.assertEqual(len(outputs), 34)
                for case in cases:
                    for suffix in ("tar", "manifest.json"):
                        self.assertIn(
                            f"results/epic-squad/evidence/{case}.{suffix}", outputs
                        )
                self.assertIn("results/epic-squad/consumer-result.json", outputs)
                self.assertIn("results/epic-squad/stage-evidence.json", outputs)
            if name in {
                "podway-upgrade",
                "epic-squad",
                "release-acceptance",
                "release-orchestration",
            }:
                self.assertEqual(spec["mode"], "manual")
                self.assertEqual(
                    spec["environment"]["profile_id"],
                    profiles["podway-candidate"]["profile_id"],
                )
            else:
                self.assertNotEqual(
                    spec["environment"]["profile_id"],
                    profiles["podway-candidate"]["profile_id"],
                )

    def test_candidate_profile_binds_sealed_artifact_bytes(self):
        run_dir, record = self.build()
        candidate = json.loads((run_dir / "bundle/profile/candidate.json").read_text())
        sha12 = self.git_sha[:12]
        stable = json.loads(
            (PROFILES_ROOT / self.module.STABLE_PROFILE_NAME).read_text()
        )
        self.assertEqual(
            candidate["profile_id"],
            (
                "proposed-candidate-haepari-0.1.0-aquarium-0.1.21-"
                f"codex-0.164.0-podway-0.2.14-dev-{sha12}"
            ),
        )
        self.assertTrue(
            candidate["profile_id"].startswith(
                candidate["profile_id"].split("-dev-")[0]
            ),
        )
        plugin = next(
            component
            for component in candidate["components"]
            if component["name"] == "aquarium-plugin"
        )
        self.assertEqual(plugin["version"], f"0.1.21-dev.{sha12}")
        self.assertEqual(
            plugin["sealed_artifact"]["development_version"],
            self.manifest["development_version"],
        )
        self.assertEqual(
            plugin["sealed_artifact"]["tree_sha256"],
            record["installation_binding"]["artifact_tree_sha256"],
        )
        # The candidate's own skill-tree pin comes from the sealed artifact's
        # skills tree, never the stable profile's pin.
        self.assertEqual(
            plugin["skill_tree"]["sha256"],
            self.module.skill_tree_digest_from_directory(
                run_dir / "bundle/artifact/plugins/aquarium/skills"
            ),
        )
        self.assertNotEqual(
            plugin["skill_tree"]["sha256"],
            next(
                component
                for component in stable["components"]
                if component["name"] == "aquarium-plugin"
            )["skill_tree"]["sha256"],
        )
        # Unchanged dependency pins stay verbatim; the plugin component
        # changes only its version, provenance (dropped), sealed artifact
        # (added) and skill pin.
        stable_by_name = {
            component["name"]: component for component in stable["components"]
        }
        for component in candidate["components"]:
            if component["name"] == "aquarium-plugin":
                self.assertEqual(
                    set(component),
                    (set(stable_by_name["aquarium-plugin"]) - {"provenance"})
                    | {"sealed_artifact"},
                )
                continue
            self.assertEqual(component, stable_by_name[component["name"]])
        validator = load_validator()
        self.assertEqual(validator.validate_profile(candidate), [])

    def test_abort_preimage_is_a_declared_output(self):
        run_dir, _record = self.build(suite="release-acceptance", mode="manual")
        spec = json.loads((run_dir / "spec-0.json").read_text())
        self.assertIn(
            "results/release-acceptance/abort-normalization.json",
            spec["workload"]["required_outputs"],
        )

    def test_sealing_is_deterministic_across_builds(self):
        # Two seals of the same committed inputs produce byte-identical
        # profile files, so a committed copy equals every fresh seal.
        first_dir, _first = self.build()
        second_dir, _second = self.build()
        for name in ("profile/stable.json", "profile/candidate.json"):
            self.assertEqual(
                (first_dir / "bundle" / name).read_bytes(),
                (second_dir / "bundle" / name).read_bytes(),
                name,
            )

    def test_release_acceptance_spec_declares_the_fixed_contract(self):
        run_dir, _record = self.build(suite="release-acceptance", mode="manual")
        spec = json.loads((run_dir / "spec-0.json").read_text())
        self.assertEqual(spec["mode"], "manual")
        self.assertEqual(spec["workload"]["argv"][-1], "machine-prepare")
        self.assertEqual(spec["deadlines"]["run_seconds"], 0)
        self.assertEqual(spec["deadlines"]["manual_seconds"], 21600)
        self.assertEqual(spec["deadlines"]["prepare_seconds"], 1800)
        self.assertEqual(
            spec["manual"]["required_scenarios"],
            [
                "released-baseline",
                "candidate-upgrade",
                "runtime-approval",
                "python-runtime-approval",
                "skill-identity",
                "task-startup",
                "epic-startup",
                "release-startup",
                "stale-skill-failure",
                "stale-skill-restoration",
                "evidence-staging",
                "consumer-cleanup",
            ],
        )
        self.assertEqual(
            spec["manual"]["scenario_document"].split("/")[-1],
            "release-acceptance.md",
        )
        outputs = spec["workload"]["required_outputs"]
        for output in outputs:
            self.assertTrue(output.startswith("results/release-acceptance/"), output)
        for case in (
            "baseline",
            "upgrade",
            "task-setup",
            "epic-setup",
            "preservation-setup",
            "runtime-update",
            "python-runtime-update",
            "task-startup",
            "epic-startup",
            "stale-skill",
        ):
            self.assertIn(f"results/release-acceptance/evidence/{case}.tar", outputs)
            self.assertIn(
                f"results/release-acceptance/evidence/{case}.manifest.json", outputs
            )
        self.assertTrue(
            spec["environment"]["profile_id"].startswith("proposed-candidate-")
        )

    def test_inventory_digest_is_deterministic(self):
        _first_dir, first = self.build()
        _second_dir, second = self.build()
        self.assertEqual(
            first["installation_binding"]["inventory_digest"],
            second["installation_binding"]["inventory_digest"],
        )

    def test_mode_must_be_declared_for_suite(self):
        with self.assertRaises(self.module.BundleError):
            self.build(suite="vm-blocked-probe", mode="manual")

    def test_symlink_in_harness_refuses_sealing(self):
        # An untracked symlink is git-visible, so the listing seals it and
        # the existing symlink refusal fires.
        link = self.harness / "link.py"
        link.symlink_to(self.harness / "guest_main.py")
        try:
            with self.assertRaises(self.module.BundleError):
                self.build()
        finally:
            link.unlink()

    def test_c31_ancestor_symlink_directory_refused(self):
        # A tracked directory replaced by a symlink to an external tree
        # holding the same names — hidden from the untracked listing by an
        # ignore rule — must be refused: sealing may never follow a
        # symlinked ancestor.
        original_ignore = (self.harness / ".gitignore").read_bytes()
        originals = {
            path.name: path.read_bytes()
            for path in sorted((self.harness / "scenarios").iterdir())
        }
        external = self.work / "external-scenarios"
        external.mkdir()
        for name, payload in originals.items():
            (external / name).write_bytes(payload)
        shutil.rmtree(self.harness / "scenarios")
        (self.harness / "scenarios").symlink_to(external)
        (self.harness / ".gitignore").write_text(
            original_ignore.decode() + "scenarios\n"
        )
        try:
            with self.assertRaises(self.module.BundleError) as raised:
                self.build()
            self.assertIn("symlink in sealed input source", str(raised.exception))
        finally:
            (self.harness / "scenarios").unlink()
            scenarios = self.harness / "scenarios"
            scenarios.mkdir()
            for name, payload in originals.items():
                (scenarios / name).write_bytes(payload)
            (self.harness / ".gitignore").write_bytes(original_ignore)

    def test_c30_git_visibility_governs_harness_sealing(self):
        run_dir, _record = self.build()
        spec = json.loads((run_dir / "spec-0.json").read_text())
        sealed_root = run_dir / "bundle/harness/tests/vm/recipes"
        listing = subprocess.run(
            [
                "git",
                "-C",
                str(self.repository),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                "tests/vm/recipes",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        visible = sorted(
            Path(entry).relative_to("tests/vm/recipes").as_posix()
            for entry in listing.split("\0")
            if entry
        )
        # A tracked file and untracked non-ignored files are sealed;
        # ignored local tool state never is.
        self.assertIn("tracked.md", visible)
        self.assertIn("guest_entry.sh", visible)
        self.assertIn("untracked-notes.txt", visible)
        self.assertNotIn(
            ".omc/state/sessions/s1/pre-tool-advisory-throttle.json", visible
        )
        self.assertNotIn("__pycache__/guest_main.cpython-314.pyc", visible)
        sealed = sorted(
            path.relative_to(sealed_root).as_posix()
            for path in sealed_root.rglob("*")
            if path.is_file()
        )
        self.assertEqual(sealed, visible)
        # The harness digest covers exactly the git-visible files.
        self.assertEqual(
            spec["provenance"]["tests_digest"],
            self.module.tree_sha256(self.harness, visible),
        )

    def test_c30_missing_listed_input_refused(self):
        # A tracked file deleted on disk without staging stays listed, and
        # the build refuses it explicitly instead of silently skipping it.
        missing = self.harness / "tracked.md"
        original = missing.read_bytes()
        missing.unlink()
        try:
            with self.assertRaises(self.module.BundleError) as raised:
                self.build()
            self.assertIn("missing on disk", str(raised.exception))
        finally:
            missing.write_bytes(original)

    def test_fixture_lock_requires_hash_pins(self):
        lock = self.work / "requirements.lock"
        lock.write_text("pytest>=8.3.5\n")
        with self.assertRaises(self.module.BundleError):
            self.build(fixture_requirements=lock)
        good_lock = (
            "pytest==8.3.5 "
            + chr(92)
            + "\n    --hash=sha256:"
            + "a" * 64
            + " "
            + chr(92)
            + "\n    --hash=sha256:"
            + "c" * 64
            + "\nruff==0.12.0 --hash=sha256:"
            + "b" * 64
            + "\n"
        )
        lock.write_text(good_lock)
        run_dir, _record = self.build(fixture_requirements=lock)
        spec = json.loads((run_dir / "spec-0.json").read_text())
        self.assertIn(
            "requirements/fixture-requirements.lock", spec["input"]["selected_files"]
        )
        inputs = json.loads((run_dir / "bundle/harness/inputs.json").read_text())
        self.assertEqual(
            inputs["fixture_requirements"], "requirements/fixture-requirements.lock"
        )

    def test_guest_context_requires_absolute_machine_values(self):
        context = dict(GUEST_CONTEXT)
        context["guest_python"] = "python3"
        path = self.work / "bad-context.json"
        path.write_text(json.dumps(context))
        with self.assertRaises(self.module.BundleError):
            self.build(context_path=path)

    def test_queue_override_reaches_spec(self):
        run_dir, _record = self.build(queue_override=78300)
        spec = json.loads((run_dir / "spec-0.json").read_text())
        self.assertEqual(spec["deadlines"]["queue_seconds"], 78300)

    def test_tree_sha256_matches_native_admission_vector(self):
        root = Path(tempfile.mkdtemp(prefix="vm-tree-", dir=str(self.work)))
        (root / "source").mkdir()
        (root / "source/input.txt").write_bytes(b"t086 fixture input\n")
        # Digest reproduced from a real TASK-086 controller admission.
        self.assertEqual(
            self.module.tree_sha256(root, ["source/input.txt"]),
            "9bd639f14f7dd2e712eba85b40dc9ccb0924b98b65d17c8a55312ee626a7ba3c",
        )

    def test_real_scratch_build_path_produces_a_dev_artifact(self):
        run_dir = Path(tempfile.mkdtemp(prefix="vm-build-", dir=str(self.work)))
        run_dir.chmod(0o700)
        self.module.build_bundle(
            run_dir=run_dir,
            context_path=self.context_path,
            suites_selection="install",
            resource_id="synthetic-resource",
            mode="auto",
            repository=self.repository,
        )
        manifest = json.loads((run_dir / "bundle/artifact-manifest.json").read_text())
        self.assertEqual(manifest["git_sha"], self.git_sha)
        branch = subprocess.run(
            ["git", "-C", str(run_dir / "scratch"), "symbolic-ref", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(branch.stdout.strip(), "main")
        self.assertIn("0.1.21-dev.", manifest["development_version"])
        plugin = json.loads(
            (
                run_dir / "bundle/artifact/plugins/aquarium/.codex-plugin/plugin.json"
            ).read_text()
        )
        self.assertEqual(plugin["version"], manifest["development_version"][1:])
        self.assertTrue(
            (run_dir / "build-output/marketplace/plugins/aquarium").is_dir()
        )

    def test_manual_spec_uses_the_native_setup_object(self):
        run_dir, _record = self.build(suite="manual-hold", mode="manual")
        spec = json.loads((run_dir / "spec-0.json").read_text())
        # Setup only persists the genuine managed context for the
        # operator; the workload argv itself stays the preparation
        # entrypoint and run_seconds is pinned to zero. The token-free
        # command survives resolve_tokens unchanged.
        self.assertEqual(
            spec["setup"]["argv"],
            [
                "/bin/sh",
                "-c",
                (
                    "umask 077 && printf '%s' \"$HAEPARI_PARENT_CONTEXT\""
                    " > ../operator-parent-context.json"
                ),
            ],
        )
        self.assertIn("--phase", spec["workload"]["argv"])
        self.assertIn("smoke", spec["workload"]["argv"])
        self.assertEqual(spec["deadlines"]["run_seconds"], 0)
        self.assertEqual(
            spec["manual"]["scenario_document"].split("/")[-1], "manual-hold.md"
        )
        for output in spec["workload"]["required_outputs"]:
            self.assertTrue(output.startswith("results/manual-hold/"), output)

    def test_c29_setup_argv_persists_genuine_context(self):
        # Executing the resolved setup argv from the harness cwd, as the
        # managed runner does, persists the context bytes into the Job root
        # with mode 0600.
        run_dir, _record = self.build(suite="manual-hold", mode="manual")
        spec = json.loads((run_dir / "spec-0.json").read_text())
        job = self.work / "c29-operator-job"
        harness = job / "harness"
        harness.mkdir(parents=True)
        context = json.dumps(
            [{"job_id": "job-c29", "lease_generation": 3, "nonce": "ab" * 32}]
        )
        result = subprocess.run(
            spec["setup"]["argv"],
            cwd=harness,
            env={**os.environ, "HAEPARI_PARENT_CONTEXT": context},
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        persisted = job / "operator-parent-context.json"
        self.assertTrue(persisted.is_file())
        self.assertEqual(stat.S_IMODE(persisted.stat().st_mode), 0o600)
        self.assertEqual(persisted.read_bytes(), context.encode())

    def test_c29_auto_suites_carry_no_setup(self):
        run_dir, _record = self.build()
        spec = json.loads((run_dir / "spec-0.json").read_text())
        self.assertNotIn("setup", spec)


if __name__ == "__main__":
    unittest.main()
