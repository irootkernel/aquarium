from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[1]
PROFILES_ROOT = REPOSITORY / "tests/vm/profiles"
VALIDATOR_PATH = PROFILES_ROOT / "validate_profiles.py"
STABLE_PROFILE = PROFILES_ROOT / "proposed-stable-haepari-0.1.0-aquarium-0.1.21.json"
CANDIDATE_PROFILE = (
    PROFILES_ROOT / "proposed-candidate-haepari-0.1.0-aquarium-0.1.22.json"
)
INVENTORY_BEFORE = PROFILES_ROOT / "fixtures/inventory-before.json"
INVENTORY_CANDIDATE = PROFILES_ROOT / "fixtures/inventory-candidate.json"
INVENTORY_POST_CLEANUP = PROFILES_ROOT / "fixtures/inventory-post-cleanup.json"


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "vm_profile_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class ProfileValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()
        self.base = load_json(STABLE_PROFILE)

    def test_committed_proposed_profiles_are_valid(self) -> None:
        for path in (STABLE_PROFILE, CANDIDATE_PROFILE):
            self.assertEqual(self.validator.validate_profile(load_json(path)), [])

    def test_committed_profiles_have_distinct_immutable_identities(self) -> None:
        stable = load_json(STABLE_PROFILE)
        candidate = load_json(CANDIDATE_PROFILE)
        self.assertNotEqual(stable["profile_id"], candidate["profile_id"])
        raw_stable = STABLE_PROFILE.read_bytes()
        raw_candidate = CANDIDATE_PROFILE.read_bytes()
        self.assertNotEqual(raw_stable, raw_candidate)
        self.assertEqual(
            self.validator.digest_bytes(raw_stable),
            hashlib.sha256(raw_stable).hexdigest(),
        )

    def test_profile_with_unknown_top_level_key_is_rejected(self) -> None:
        profile = copy.deepcopy(self.base)
        profile["vm_provisioned"] = True
        self.assertNotEqual(self.validator.validate_profile(profile), [])

    def test_machine_local_bindings_are_rejected(self) -> None:
        for field, value in (
            ("vm_uuid", "12345678-90AB-CDEF-1234-567890ABCDEF"),
            ("mac_address", "02:00:00:00:00:01"),
            ("installation_id", "local-0123456789abcdef"),
            ("registered_resource_id", "sample-vm"),
            ("identity_file", "ssh key material"),
        ):
            profile = copy.deepcopy(self.base)
            profile[field] = value
            errors = self.validator.validate_profile(profile)
            self.assertTrue(errors, f"{field} was accepted")

    def test_absolute_and_home_paths_are_rejected(self) -> None:
        profile = copy.deepcopy(self.base)
        profile["components"][0]["installation_scope"] = "/Users/operator/tools"
        errors = self.validator.validate_profile(profile)
        self.assertTrue(any("path" in error for error in errors))

    def test_profile_claiming_qualification_outcomes_is_rejected(self) -> None:
        for field, value in (
            ("vm_provisioned", True),
            ("migration_passed", True),
        ):
            profile = copy.deepcopy(self.base)
            profile[field] = value
            self.assertNotEqual(self.validator.validate_profile(profile), [])

    def test_component_without_identity_axis_is_rejected(self) -> None:
        profile = copy.deepcopy(self.base)
        profile["components"].append(
            {"name": "unpinned", "role": "guest", "installation_scope": "guest-path"}
        )
        errors = self.validator.validate_profile(profile)
        self.assertTrue(any("identity axis" in error for error in errors))

    def test_malformed_identity_pins_are_rejected(self) -> None:
        profile = copy.deepcopy(self.base)
        profile["components"][0]["archive_sha256"] = "ABCD" * 16
        profile["components"][0]["executable_sha256"] = "sha256:not-a-digest"
        profile["components"][1]["version"] = "0.1"
        errors = self.validator.validate_profile(profile)
        joined = "\n".join(errors)
        self.assertIn("archive_sha256", joined)
        self.assertIn("executable_sha256", joined)
        self.assertIn("version", joined)

    def test_duplicate_and_conflicting_components_are_rejected(self) -> None:
        profile = copy.deepcopy(self.base)
        profile["components"].append(copy.deepcopy(profile["components"][0]))
        errors = self.validator.validate_profile(profile)
        self.assertTrue(any("duplicates" in error for error in errors))
        conflicting = copy.deepcopy(self.base)
        conflicting["absent_components"].append(
            {"name": conflicting["components"][0]["name"], "reason": "absent"}
        )
        errors = self.validator.validate_profile(conflicting)
        self.assertTrue(any("also declared present" in error for error in errors))

    def test_resource_must_stay_abstract_and_capacity_one(self) -> None:
        profile = copy.deepcopy(self.base)
        profile["resource"] = {"kind": "local", "capacity": 1}
        self.assertNotEqual(self.validator.validate_profile(profile), [])
        profile["resource"] = {"kind": "utm-macos", "capacity": 2}
        self.assertNotEqual(self.validator.validate_profile(profile), [])
        profile["resource"] = {"kind": "utm-macos", "capacity": 1, "uuid": "abc"}
        self.assertNotEqual(self.validator.validate_profile(profile), [])

    def test_starting_states_and_upgrade_edges(self) -> None:
        profile = copy.deepcopy(self.base)
        profile["starting_states"] = []
        self.assertNotEqual(self.validator.validate_profile(profile), [])
        profile["starting_states"] = [{"kind": "prior_version"}]
        self.assertNotEqual(self.validator.validate_profile(profile), [])
        profile["starting_states"] = [{"kind": "product_absent", "aquarium": "0.1.20"}]
        self.assertNotEqual(self.validator.validate_profile(profile), [])
        profile["starting_states"] = [
            {"kind": "product_absent"},
            {"kind": "prior_version", "aquarium": "0.1.21"},
        ]
        self.assertEqual(self.validator.validate_profile(profile), [])

    def test_service_plan_identity_is_validated(self) -> None:
        profile = copy.deepcopy(self.base)
        service = profile["components"][0]["controller_service"]
        service["plan"]["schema"] = "haepari.development-service-plan/v1"
        service["plan"]["host_macos_guest_limit"] = 3
        errors = self.validator.validate_profile(profile)
        joined = "\n".join(errors)
        self.assertIn("release-service-plan", joined)
        self.assertIn("host_macos_guest_limit", joined)

    def test_effective_limits_must_match_controller_plan(self) -> None:
        profile = copy.deepcopy(self.base)
        profile["effective_configuration"]["service_limits"]["global_limit"] = 1
        errors = self.validator.validate_profile(profile)
        self.assertTrue(any("service_limits must match" in error for error in errors))


class InventoryContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()
        self.before = load_json(INVENTORY_BEFORE)
        self.candidate = load_json(INVENTORY_CANDIDATE)
        self.post_cleanup = load_json(INVENTORY_POST_CLEANUP)

    def test_committed_inventory_fixtures_are_valid(self) -> None:
        for document in (self.before, self.candidate, self.post_cleanup):
            self.assertEqual(self.validator.validate_inventory(document), [])

    def test_invalid_inventory_entries_are_rejected(self) -> None:
        invalid = copy.deepcopy(self.before)
        invalid["entries"][0]["relative_path"] = "/absolute/haepari"
        self.assertNotEqual(self.validator.validate_inventory(invalid), [])
        invalid = copy.deepcopy(self.before)
        invalid["entries"][1]["relative_path"] = "../outside/SKILL.md"
        self.assertNotEqual(self.validator.validate_inventory(invalid), [])
        invalid = copy.deepcopy(self.before)
        invalid["entries"][2]["sha256"] = "short"
        self.assertNotEqual(self.validator.validate_inventory(invalid), [])
        invalid = copy.deepcopy(self.before)
        invalid["entries"][3]["executable"] = "yes"
        self.assertNotEqual(self.validator.validate_inventory(invalid), [])
        invalid = copy.deepcopy(self.before)
        invalid["entries"].append(copy.deepcopy(invalid["entries"][0]))
        self.assertNotEqual(self.validator.validate_inventory(invalid), [])
        invalid = copy.deepcopy(self.before)
        invalid["phase"] = "during"
        self.assertNotEqual(self.validator.validate_inventory(invalid), [])
        invalid = copy.deepcopy(self.before)
        invalid["run_root"] = "/private/tmp/run"
        self.assertNotEqual(self.validator.validate_inventory(invalid), [])

    def test_candidate_comparison_reports_every_tree_difference(self) -> None:
        differences = self.validator.compare_inventories(self.before, self.candidate)
        self.assertEqual(differences["missing"], ["guest-path:legacy/old-runner.txt"])
        self.assertEqual(
            differences["added"],
            [
                (
                    "codex-plugin-cache:plugin/aquarium/skills/task-handler"
                    "/references/new-feature.md"
                )
            ],
        )
        self.assertEqual(
            differences["changed"],
            ["codex-plugin-cache:plugin/aquarium/.codex-plugin/plugin.json"],
        )
        self.assertEqual(
            differences["executable_bit_changed"],
            ["project-discovery:scripts/run-checks.sh"],
        )

    def test_inventory_identity_includes_the_installation_scope(self) -> None:
        shadowed = copy.deepcopy(self.before)
        shadowed["entries"].append(
            {
                "relative_path": "bin/haepari",
                "executable": True,
                "sha256": "e1a4c0a0" + "0" * 56,
                "installation_scope": "codex-home-skills",
            }
        )
        self.assertEqual(self.validator.validate_inventory(shadowed), [])
        duplicate = copy.deepcopy(shadowed)
        duplicate["entries"].append(copy.deepcopy(shadowed["entries"][-1]))
        errors = self.validator.validate_inventory(duplicate)
        self.assertTrue(
            any("duplicates the codex-home-skills entry" in e for e in errors)
        )

    def test_moving_a_file_between_scopes_is_missing_and_added(self) -> None:
        moved = copy.deepcopy(self.before)
        moved["entries"][0] = dict(moved["entries"][0])
        moved["entries"][0]["installation_scope"] = "codex-home-skills"
        differences = self.validator.compare_inventories(self.before, moved)
        self.assertEqual(differences["missing"], ["user-global:bin/haepari"])
        self.assertEqual(differences["added"], ["codex-home-skills:bin/haepari"])
        self.assertEqual(differences["changed"], [])

    def test_verified_cleanup_restores_the_before_tree(self) -> None:
        differences = self.validator.compare_inventories(self.before, self.post_cleanup)
        self.assertEqual(
            differences,
            {"missing": [], "added": [], "changed": [], "executable_bit_changed": []},
        )


class OverrideSemanticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()
        self.base = load_json(STABLE_PROFILE)

    def test_whole_unit_override_replaces_only_the_declared_component(self) -> None:
        override = copy.deepcopy(self.base)
        override["profile_id"] = "proposed-candidate-whole-unit-override"
        override["profile_revision"] = 2
        override["components"] = [
            {
                "name": "aquarium-plugin",
                "role": "guest",
                "installation_scope": "codex-plugin-cache",
                "version": "0.1.22",
                "provenance": {
                    "release_tag": "v0.1.22",
                    "tag_commit": "0" * 40,
                },
            }
        ]
        merged, errors = self.validator.apply_override(self.base, override)
        self.assertEqual(errors, [])
        assert merged is not None
        self.assertEqual(merged["profile_id"], "proposed-candidate-whole-unit-override")
        self.assertEqual(merged["profile_revision"], 2)
        plugin = next(
            component
            for component in merged["components"]
            if component["name"] == "aquarium-plugin"
        )
        self.assertEqual(plugin["version"], "0.1.22")
        self.assertEqual(plugin["provenance"]["tag_commit"], "0" * 40)
        haepari = next(
            component
            for component in merged["components"]
            if component["name"] == "haepari"
        )
        self.assertEqual(
            haepari["executable_sha256"],
            self.base["components"][0]["executable_sha256"],
        )

    def test_skill_only_override_retains_the_binary_and_other_pins(self) -> None:
        override = copy.deepcopy(self.base)
        override["profile_id"] = "proposed-candidate-skill-only-override"
        haepari = copy.deepcopy(self.base["components"][0])
        haepari["skill_tree"]["sha256"] = "9" * 64
        override["components"] = [haepari]
        self.assertEqual(
            self.validator.skill_only_override_errors(self.base, override, "haepari"),
            [],
        )
        merged, errors = self.validator.apply_override(self.base, override)
        self.assertEqual(errors, [])
        assert merged is not None
        podway = next(
            component
            for component in merged["components"]
            if component["name"] == "use-podway"
        )
        self.assertEqual(
            podway["pin"]["commit"], "fa29dba929777b020377bc9803cb0a3954d219b1"
        )

    def test_skill_only_override_that_changes_binary_pins_is_rejected(self) -> None:
        override = copy.deepcopy(self.base)
        override["profile_id"] = "proposed-candidate-fake-skill-override"
        haepari = copy.deepcopy(self.base["components"][0])
        haepari["skill_tree"]["sha256"] = "9" * 64
        haepari["executable_sha256"] = "sha256:" + "a" * 64
        override["components"] = [haepari]
        errors = self.validator.skill_only_override_errors(
            self.base, override, "haepari"
        )
        self.assertTrue(any("executable_sha256" in error for error in errors))

    def test_invalid_override_is_rejected(self) -> None:
        override = copy.deepcopy(self.base)
        override["profile_id"] = "invalid-override"
        override["components"][0]["executable_sha256"] = "sha256:oops"
        merged, errors = self.validator.apply_override(self.base, override)
        self.assertIsNone(merged)
        self.assertNotEqual(errors, [])


class IdentityDriftTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()
        self.recorded = {
            "installation_id": "local-0123456789abcdef",
            "resource_id": "sample-vm",
            "resource_revision": 1,
            "known_resource_ids": ["sample-vm"],
            "service_plan": {
                "schema": "haepari.release-service-plan/v1",
                "instance": "release",
                "global_limit": 2,
                "host_macos_guest_limit": 1,
            },
            "effective_settings": {"controller_selection": "explicit_haepari_home"},
        }

    def test_matching_identity_reports_no_drift(self) -> None:
        self.assertEqual(
            self.validator.check_identity(self.recorded, copy.deepcopy(self.recorded)),
            [],
        )

    def test_wrong_installation_is_flagged(self) -> None:
        observed = copy.deepcopy(self.recorded)
        observed["installation_id"] = "local-fedcba9876543210"
        errors = self.validator.check_identity(self.recorded, observed)
        self.assertTrue(any("installation_id_mismatch" in error for error in errors))

    def test_unobserved_installation_id_is_a_gap(self) -> None:
        observed = copy.deepcopy(self.recorded)
        observed["installation_id"] = None
        errors = self.validator.check_identity(self.recorded, observed)
        self.assertTrue(any("installation_id_unobserved" in error for error in errors))

    def test_unknown_resource_is_flagged(self) -> None:
        observed = copy.deepcopy(self.recorded)
        observed["known_resource_ids"] = ["other-vm"]
        errors = self.validator.check_identity(self.recorded, observed)
        self.assertTrue(any("resource_unknown" in error for error in errors))

    def test_changed_resource_revision_is_flagged(self) -> None:
        observed = copy.deepcopy(self.recorded)
        observed["resource_revision"] = 2
        errors = self.validator.check_identity(self.recorded, observed)
        self.assertTrue(any("resource_revision_changed" in error for error in errors))

    def test_effective_settings_drift_is_flagged(self) -> None:
        observed = copy.deepcopy(self.recorded)
        observed["service_plan"]["global_limit"] = 1
        errors = self.validator.check_identity(self.recorded, observed)
        self.assertTrue(any("effective_settings_drift" in error for error in errors))
        observed = copy.deepcopy(self.recorded)
        observed["effective_settings"]["controller_selection"] = "default-root"
        errors = self.validator.check_identity(self.recorded, observed)
        self.assertTrue(any("settings_drift" in error for error in errors))


class TreeDigestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()

    def _write_tree(self, root: Path) -> None:
        (root / "use-haepari").mkdir(parents=True)
        (root / "use-haepari" / "SKILL.md").write_text(
            "---\nname: use-haepari\n---\n# Use Haepari\n", encoding="utf-8"
        )

    def test_pinned_digest_matches_the_algorithm_over_the_packaged_tree(self) -> None:
        pinned = load_json(STABLE_PROFILE)["components"][0]["skill_tree"]
        self.assertEqual(pinned["digest_algorithm"], "aquarium-skill-tree-sha256/v1")
        self.assertEqual(
            pinned["sha256"],
            self.validator.tree_digest(
                [
                    {
                        "relative_path": "SKILL.md",
                        "executable": False,
                        "sha256": (
                            "00295fa08965a45e15b91b77b5e6e8188d3bb824"
                            "1c1821651993df5a2e9da4c0"
                        ),
                    }
                ]
            ),
        )
        candidate = load_json(CANDIDATE_PROFILE)["components"][0]["skill_tree"]
        self.assertEqual(candidate["sha256"], pinned["sha256"])

    def test_directory_digest_matches_entry_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tree = Path(temporary) / "use-haepari"
            self._write_tree(tree.parent)
            self.assertEqual(
                self.validator.tree_digest_from_directory(tree),
                self.validator.tree_digest(
                    [
                        {
                            "relative_path": "SKILL.md",
                            "executable": False,
                            "sha256": hashlib.sha256(
                                (tree / "SKILL.md").read_bytes()
                            ).hexdigest(),
                        }
                    ]
                ),
            )

    def test_every_tree_difference_changes_the_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_tree(root)
            baseline = self.validator.tree_digest_from_directory(root)

            (root / "use-haepari" / "references").mkdir()
            (root / "use-haepari" / "references" / "guide.md").write_text(
                "guide\n", encoding="utf-8"
            )
            self.assertNotEqual(
                self.validator.tree_digest_from_directory(root), baseline
            )
            (root / "use-haepari" / "references" / "guide.md").unlink()
            (root / "use-haepari" / "references").rmdir()
            self.assertEqual(self.validator.tree_digest_from_directory(root), baseline)

            (root / "use-haepari" / "SKILL.md").write_text(
                "---\nname: use-haepari\n---\n# Changed\n", encoding="utf-8"
            )
            changed = self.validator.tree_digest_from_directory(root)
            self.assertNotEqual(changed, baseline)
            (root / "use-haepari" / "SKILL.md").write_text(
                "---\nname: use-haepari\n---\n# Use Haepari\n", encoding="utf-8"
            )
            self.assertEqual(self.validator.tree_digest_from_directory(root), baseline)

            (root / "use-haepari" / "SKILL.md").chmod(0o755)
            self.assertNotEqual(
                self.validator.tree_digest_from_directory(root), baseline
            )
            (root / "use-haepari" / "SKILL.md").chmod(0o644)
            self.assertEqual(self.validator.tree_digest_from_directory(root), baseline)

            removed = root / "use-haepari" / "SKILL.md"
            removed.unlink()
            self.assertNotEqual(
                self.validator.tree_digest_from_directory(root), baseline
            )

    def test_symlink_in_a_skill_tree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_tree(root)
            os.symlink(
                root / "use-haepari" / "SKILL.md",
                root / "use-haepari" / "alias.md",
            )
            with self.assertRaises(ValueError):
                self.validator.tree_digest_from_directory(root)

    def test_special_file_in_a_skill_tree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_tree(root)
            os.mkfifo(root / "use-haepari" / "channel")
            with self.assertRaises(ValueError):
                self.validator.tree_digest_from_directory(root)

    def test_skill_tree_requires_the_named_algorithm(self) -> None:
        profile = load_json(STABLE_PROFILE)
        broken = copy.deepcopy(profile)
        del broken["components"][0]["skill_tree"]["digest_algorithm"]
        errors = self.validator.validate_profile(broken)
        self.assertTrue(any("digest_algorithm" in error for error in errors))
        broken = copy.deepcopy(profile)
        broken["components"][0]["skill_tree"]["digest_algorithm"] = "sha256"
        errors = self.validator.validate_profile(broken)
        self.assertTrue(any("digest_algorithm" in error for error in errors))


class ValidatorCliTest(unittest.TestCase):
    def test_cli_accepts_committed_documents(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(VALIDATOR_PATH),
                str(STABLE_PROFILE),
                str(CANDIDATE_PROFILE),
                str(INVENTORY_BEFORE),
                str(INVENTORY_CANDIDATE),
                str(INVENTORY_POST_CLEANUP),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["schema_version"], "aquarium.vm-profile-validation/v1")
        self.assertEqual(
            [document["errors"] for document in report["documents"]],
            [[] for _ in report["documents"]],
        )

    def test_cli_rejects_an_invalid_document(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "invalid-profile.json"
            document = load_json(STABLE_PROFILE)
            document["vm_uuid"] = "12345678-90AB-CDEF-1234-567890ABCDEF"
            invalid.write_text(json.dumps(document), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR_PATH), str(invalid)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            report = json.loads(completed.stdout)
            self.assertTrue(report["documents"][0]["errors"])


class DerivedSealedArtifactProfileTest(unittest.TestCase):
    DERIVED_STABLE = (
        PROFILES_ROOT
        / "proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0.json"
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def sealed_plugin_component(self) -> Any:
        return {
            "name": "aquarium-plugin",
            "role": "guest",
            "installation_scope": "codex-plugin-cache",
            "version": "0.1.21-dev.63bbcf7e4db8",
            "sealed_artifact": {
                "tree_sha256": "a" * 64,
                "development_version": "v0.1.21-dev.63bbcf7e4db8",
            },
        }

    def test_derived_stable_profile_is_valid_and_pins_aligned_codex(self) -> None:
        document = load_json(self.DERIVED_STABLE)
        self.assertEqual(self.validator.validate_profile(document), [])
        codex = next(
            component
            for component in document["components"]
            if component["name"] == "codex"
        )
        self.assertEqual(codex["version"], "0.164.0")
        self.assertNotEqual(
            document["profile_id"], load_json(STABLE_PROFILE)["profile_id"]
        )

    def test_sealed_artifact_is_an_optional_closed_identity_axis(self) -> None:
        document = load_json(self.DERIVED_STABLE)
        document["components"] = [
            self.sealed_plugin_component()
            if component.get("name") == "aquarium-plugin"
            else component
            for component in document["components"]
        ]
        self.assertEqual(self.validator.validate_profile(document), [])
        for mutation in (
            {"tree_sha256": "A" * 64},
            {"tree_sha256": "short"},
            {"tree_sha256": "a" * 64, "development_version": "0.1.21"},
            {"tree_sha256": "a" * 64, "development_version": "v0.1.21", "extra": 1},
        ):
            broken = json.loads(json.dumps(document))
            for component in broken["components"]:
                if component.get("name") == "aquarium-plugin":
                    component["sealed_artifact"] = mutation
            self.assertTrue(self.validator.validate_profile(broken), mutation)

    def test_skill_only_override_retains_the_sealed_artifact_binding(self) -> None:
        base = load_json(self.DERIVED_STABLE)
        for component in base["components"]:
            if component.get("name") == "haepari":
                component["sealed_artifact"] = {
                    "tree_sha256": "d" * 64,
                    "development_version": "v0.1.21-dev.63bbcf7e4db8",
                }
        override = json.loads(json.dumps(base))
        override["profile_id"] = "override-with-skill-tree"
        for component in override["components"]:
            if component.get("name") == "haepari":
                component["skill_tree"] = {
                    **component["skill_tree"],
                    "sha256": "b" * 64,
                }
        self.assertEqual(self.validator.validate_profile(override), [])
        self.assertEqual(
            self.validator.skill_only_override_errors(base, override, "haepari"), []
        )
        dropped = json.loads(json.dumps(override))
        for component in dropped["components"]:
            if component.get("name") == "haepari":
                del component["sealed_artifact"]
        self.assertTrue(
            self.validator.skill_only_override_errors(base, dropped, "haepari")
        )

    def test_candidate_profile_generator_binds_sealed_bytes(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "vm_host_bundle_profiles", REPOSITORY / "tests/vm/host_bundle.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        stable = load_json(FullCombinationProfilePairTest.STABLE)
        generated = module.derive_candidate_profile(
            stable, "c" * 64, "v0.1.21-dev.63bbcf7e4db8", "d" * 64
        )
        self.assertEqual(self.validator.validate_profile(generated), [])
        plugin = next(
            component
            for component in generated["components"]
            if component["name"] == "aquarium-plugin"
        )
        self.assertEqual(plugin["sealed_artifact"]["tree_sha256"], "c" * 64)
        self.assertNotIn("provenance", plugin)
        # The skill pin is the candidate's own tree, never the stable pin.
        self.assertEqual(plugin["skill_tree"]["sha256"], "d" * 64)

    def test_derived_candidate_upgrades_from_the_stable_plugin_release(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "vm_host_bundle_edge", REPOSITORY / "tests/vm/host_bundle.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        stable = load_json(FullCombinationProfilePairTest.STABLE)
        generated = module.derive_candidate_profile(
            stable, "c" * 64, "v0.1.21-dev.63bbcf7e4db8", "d" * 64
        )
        stable_plugin = next(
            component
            for component in stable["components"]
            if component["name"] == "aquarium-plugin"
        )
        prior = next(
            state
            for state in generated["starting_states"]
            if state["kind"] == "prior_version"
        )
        self.assertEqual(prior["aquarium"], stable_plugin["version"])
        self.assertEqual(self.validator.validate_profile(generated), [])

    def test_a_stable_without_a_skill_pin_refuses_derivation(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "vm_host_bundle_nopin", REPOSITORY / "tests/vm/host_bundle.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        stable = load_json(self.DERIVED_STABLE)
        with self.assertRaises(module.BundleError):
            module.derive_candidate_profile(
                stable, "c" * 64, "v0.1.21-dev.63bbcf7e4db8", "d" * 64
            )


class CommittedCandidateProfileTest(unittest.TestCase):
    """The committed candidate profile is the sealed copy's bytes."""

    COMMITTED_CANDIDATE = (
        PROFILES_ROOT / "proposed-candidate-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0"
        "-podway-0.2.14-dev-db132845624c.json"
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_committed_candidate_profile_is_valid(self) -> None:
        document = load_json(self.COMMITTED_CANDIDATE)
        self.assertEqual(self.validator.validate_profile(document), [])

    def test_committed_candidate_pins_the_tested_artifact(self) -> None:
        document = load_json(self.COMMITTED_CANDIDATE)
        plugin = next(
            component
            for component in document["components"]
            if component.get("sealed_artifact")
        )
        self.assertEqual(
            plugin["sealed_artifact"]["development_version"],
            "v0.1.21-dev.db132845624c",
        )
        self.assertNotIn("provenance", plugin)

    def test_committed_candidate_equals_fresh_derivation_bytes(self) -> None:
        # The committed candidate must be byte-for-byte what a fresh bundle
        # derivation from the committed stable profile seals, so a stale
        # file (for example an old upgrade edge) fails here.
        spec = importlib.util.spec_from_file_location(
            "vm_host_bundle_committed", REPOSITORY / "tests/vm/host_bundle.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        committed = load_json(self.COMMITTED_CANDIDATE)
        plugin = next(
            component
            for component in committed["components"]
            if component.get("sealed_artifact")
        )
        derived = module.derive_candidate_profile(
            load_json(FullCombinationProfilePairTest.STABLE),
            plugin["sealed_artifact"]["tree_sha256"],
            plugin["sealed_artifact"]["development_version"],
            plugin["skill_tree"]["sha256"],
        )
        expected = json.dumps(derived, indent=2, ensure_ascii=False) + "\n"
        self.assertEqual(self.COMMITTED_CANDIDATE.read_text(), expected)


class FullCombinationProfilePairTest(unittest.TestCase):
    """TASK-089's full-combination stable and candidate pair."""

    STABLE = (
        PROFILES_ROOT / "proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0"
        "-podway-0.2.14.json"
    )
    CANDIDATE = (
        PROFILES_ROOT / "proposed-candidate-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0"
        "-podway-0.2.14-dev-db132845624c.json"
    )
    TESTED_SHA12 = "db132845624c"

    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator()

    def component(self, document, name):
        return next(
            component
            for component in document["components"]
            if component["name"] == name
        )

    def test_both_files_validate_offline(self):
        for path in (self.STABLE, self.CANDIDATE):
            self.assertEqual(self.validator.validate_profile(load_json(path)), [])

    def test_stable_pins_the_complete_intended_combination(self):
        stable = load_json(self.STABLE)
        versions = {
            component["name"]: component.get("version")
            for component in stable["components"]
            if component.get("version") is not None
        }
        self.assertEqual(
            versions,
            {
                "haepari": "0.1.0",
                "aquarium-plugin": "0.1.21",
                "codex": "0.164.0",
                "podway": "v0.2.14",
                "guest-python": "3.14.8",
            },
        )
        self.assertIsNotNone(self.component(stable, "use-podway").get("pin"))
        self.assertEqual(
            self.component(stable, "podway")["executable_sha256"],
            "sha256:f48adfed9aa04c3fc8c0936c9da172136d8dd8d750eb79c62d876c31bc7677bb",
        )
        skill_tree = self.component(stable, "aquarium-plugin")["skill_tree"]
        self.assertEqual(
            skill_tree["digest_algorithm"], "aquarium-skill-tree-sha256/v1"
        )
        self.assertEqual(skill_tree["installation_scope"], "codex-plugin-cache")

    def test_candidate_id_derives_from_the_stable_id_and_binds_the_tested_sha(self):
        stable = load_json(self.STABLE)
        candidate = load_json(self.CANDIDATE)
        self.assertEqual(
            candidate["profile_id"],
            "proposed-candidate-"
            + stable["profile_id"].removeprefix("proposed-stable-")
            + f"-dev-{self.TESTED_SHA12}",
        )
        plugin = self.component(candidate, "aquarium-plugin")
        self.assertEqual(plugin["version"], f"0.1.21-dev.{self.TESTED_SHA12}")
        self.assertEqual(
            plugin["sealed_artifact"]["development_version"],
            f"v0.1.21-dev.{self.TESTED_SHA12}",
        )
        # The candidate skill pin is its own tree, never the stable pin.
        self.assertNotEqual(
            plugin["skill_tree"]["sha256"],
            self.component(stable, "aquarium-plugin")["skill_tree"]["sha256"],
        )
        self.assertEqual(
            plugin["skill_tree"]["sha256"],
            "e3c96ffef369010dc5407deba3f3cc2774e7a7907832b12d79a698fda92ddfa1",
        )
        prior = [
            state
            for state in candidate["starting_states"]
            if state["kind"] == "prior_version"
        ]
        self.assertEqual(prior, [{"kind": "prior_version", "aquarium": "0.1.21"}])

    def test_cli_accepts_every_committed_profile(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(VALIDATOR_PATH),
                *sorted(str(path) for path in PROFILES_ROOT.glob("proposed-*.json")),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
