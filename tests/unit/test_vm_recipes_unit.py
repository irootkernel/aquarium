from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[2]
RECIPES_ROOT = REPOSITORY / "tests/vm/recipes"
if str(RECIPES_ROOT) not in sys.path:
    sys.path.insert(0, str(RECIPES_ROOT))
ENTRY_PATH = RECIPES_ROOT / "guest_entry.sh"
MAIN_PATH = RECIPES_ROOT / "guest_main.py"
TREE_DIGEST_PATH = RECIPES_ROOT / "tree_digest.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FAKE_INSTALLER_STAGE = """#!/usr/bin/env python3
import os
import sys
import time

home = os.environ["FAKE_HOME"]
versions = os.path.join(home, ".aquarium/status-runtime/versions")
os.makedirs(versions, exist_ok=True)
if os.environ.get("FAKE_INSTALLER_MODE") == "miss":
    raise SystemExit(0)
os.makedirs(os.path.join(versions, ".generation.staging"), exist_ok=True)
time.sleep(120)
"""

FAKE_INSTALLER_REFUSE = """#!/usr/bin/env python3
import json
import sys

print(json.dumps({
    "schema": "aquarium-status-runtime-error/v1",
    "error": {"code": "runtime_install_failed"},
}), file=sys.stderr)
raise SystemExit(1)
"""


class TreeDigestVectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-tree-"))
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        (cls.work / "source").mkdir()
        (cls.work / "source/input.txt").write_bytes(b"t086 fixture input\n")

    def test_native_admission_vector(self):
        module = load_module("vm_tree_digest_vector", TREE_DIGEST_PATH)
        self.assertEqual(
            module.tree_sha256(self.work, ["source/input.txt"]),
            "9bd639f14f7dd2e712eba85b40dc9ccb0924b98b65d17c8a55312ee626a7ba3c",
        )

    def test_executable_bit_changes_the_digest(self):
        module = load_module("vm_tree_digest_bit", TREE_DIGEST_PATH)
        base = module.tree_sha256(self.work, ["source/input.txt"])
        target = self.work / "source/input.txt"
        target.chmod(0o755)
        try:
            self.assertNotEqual(
                module.tree_sha256(self.work, ["source/input.txt"]), base
            )
        finally:
            target.chmod(0o644)


class InventoryWalkTest(unittest.TestCase):
    """The symlink-aware walk used for guest-state inventories."""

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-walk-"))
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        cls.digest = load_module("vm_tree_digest_walk", TREE_DIGEST_PATH)
        cls.lib = load_module("vm_recipe_lib_walk", RECIPES_ROOT / "recipe_lib.py")

    def _scoped(self, tree: Path):
        return self.digest.inventory_entries(tree, "user-global", "scope")

    def test_c14_symlink_entry_encoding_and_sealed_walker_stays_strict(self):
        tree = self.work / "encoding"
        (tree / "bin").mkdir(parents=True)
        (tree / "bin/tool").write_text("#!/bin/sh\n")
        (tree / "bin/tool").chmod(0o755)
        (tree / "codex").symlink_to("bin/tool")
        entries = {entry["relative_path"]: entry for entry in self._scoped(tree)}
        self.assertEqual(set(entries), {"scope/bin/tool", "scope/codex"})
        self.assertTrue(entries["scope/bin/tool"]["executable"])
        self.assertEqual(
            entries["scope/codex"],
            {
                "installation_scope": "user-global",
                "relative_path": "scope/codex",
                "executable": False,
                "sha256": hashlib.sha256(
                    b"aquarium-symlink/v1\x00" + b"bin/tool"
                ).hexdigest(),
            },
        )
        with self.assertRaises(self.digest.TreeDigestError):
            self.digest.directory_files(tree)
        with self.assertRaises(self.digest.TreeDigestError):
            self.digest.tree_sha256_from_directory(tree)

    def test_c14_walk_never_descends_into_symlinked_directory(self):
        tree = self.work / "nodescend"
        (tree / "real").mkdir(parents=True)
        (tree / "real/inner.txt").write_text("inner\n")
        (tree / "alias").symlink_to("real")
        paths = {entry["relative_path"] for entry in self._scoped(tree)}
        self.assertEqual(paths, {"scope/real/inner.txt", "scope/alias"})

    def test_c14_symlink_retarget_detected_as_change(self):
        tree = self.work / "retarget"
        tree.mkdir()
        (tree / "one.txt").write_text("one\n")
        (tree / "two.txt").write_text("two\n")
        (tree / "link").symlink_to("one.txt")
        before = self._scoped(tree)
        (tree / "link").unlink()
        (tree / "link").symlink_to("two.txt")
        after = self._scoped(tree)
        violations = self.lib.postcondition_violations(
            before, after, lambda _scope, _path: False
        )
        self.assertEqual(
            violations,
            ["changed outside declared end state: user-global:scope/link"],
        )

    def test_c14_file_replaced_by_symlink_detected(self):
        tree = self.work / "swap"
        tree.mkdir()
        (tree / "target.txt").write_text("target\n")
        (tree / "entry").write_text("was a file\n")
        before = self._scoped(tree)
        (tree / "entry").unlink()
        (tree / "entry").symlink_to("target.txt")
        after = self._scoped(tree)
        violations = self.lib.postcondition_violations(
            before, after, lambda _scope, _path: False
        )
        self.assertTrue(
            any("changed outside declared end state" in item for item in violations),
            violations,
        )

    def test_c14_special_file_in_scope_raises(self):
        tree = self.work / "special"
        tree.mkdir()
        fifo = tree / "pipe"
        os.mkfifo(fifo)
        try:
            with self.assertRaises(self.digest.TreeDigestError) as raised:
                self._scoped(tree)
            self.assertIn("special file inside inventory scope", str(raised.exception))
        finally:
            fifo.unlink()

    def test_c14_component_digest_uses_the_walk(self):
        tree = self.work / "component"
        (tree / "bin").mkdir(parents=True)
        (tree / "bin/codex").write_text("#!/bin/sh\n")
        (tree / "codex").symlink_to("bin/codex")
        base = self.digest.inventory_tree_sha256_from_directory(tree)
        self.assertEqual(len(base), 64)
        (tree / "codex").unlink()
        (tree / "codex").symlink_to("bin/other")
        self.assertNotEqual(
            self.digest.inventory_tree_sha256_from_directory(tree), base
        )

    def test_c15_walk_digest_order_matches_the_strict_digest(self):
        # `a-c` sorts before `a/b` by UTF-8 bytes but after it in a plain
        # depth-first walk, so a symlink-free tree with such a name pair
        # proves the walk's entry order matches the strict digest's order.
        tree = self.work / "order"
        (tree / "a").mkdir(parents=True)
        (tree / "a/b").write_text("nested\n")
        (tree / "a-c").write_text("flat\n")
        self.assertEqual(
            self.digest.inventory_tree_sha256_from_directory(tree),
            self.digest.tree_sha256_from_directory(tree),
        )

    def test_c16_streamed_walk_matches_whole_content_hashing(self):
        # Independent in-test framing: the streamed, bounded-chunk walk must
        # produce exactly the digest and entry values that hashing whole
        # contents here produces, including a file larger than one chunk.
        tree = self.work / "streaming"
        (tree / "bin").mkdir(parents=True)
        (tree / "bin/tool").write_text("#!/bin/sh\n")
        (tree / "bin/tool").chmod(0o755)
        (tree / "nested").mkdir()
        big = bytes(range(256)) * 6144  # 1.5 MiB, spans two 1 MiB chunks
        (tree / "nested/big.bin").write_bytes(big)
        (tree / "codex").symlink_to("bin/tool")
        expected = hashlib.sha256(b"haepari-tree-sha256/v1\x00")
        for relative, executable, content in (
            ("bin/tool", True, b"#!/bin/sh\n"),
            ("codex", False, b"aquarium-symlink/v1\x00bin/tool"),
            ("nested/big.bin", False, big),
        ):
            name = relative.encode("utf-8")
            expected.update(
                len(name).to_bytes(8, "big")
                + name
                + (b"\x01" if executable else b"\x00")
                + len(content).to_bytes(8, "big")
            )
            expected.update(hashlib.sha256(content).digest())
        self.assertEqual(
            self.digest.inventory_tree_sha256_from_directory(tree),
            expected.hexdigest(),
        )
        entries = {entry["relative_path"]: entry for entry in self._scoped(tree)}
        self.assertEqual(
            entries["scope/codex"]["sha256"],
            hashlib.sha256(b"aquarium-symlink/v1\x00bin/tool").hexdigest(),
        )
        self.assertEqual(
            entries["scope/nested/big.bin"]["sha256"],
            hashlib.sha256(big).hexdigest(),
        )
        self.assertTrue(entries["scope/bin/tool"]["executable"])


class RecipeLibTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-recipes-")).resolve()
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        cls.lib = load_module("vm_recipe_lib_unit", RECIPES_ROOT / "recipe_lib.py")
        cls.home = cls.work / "home"
        (cls.home / ".aquarium/status-runtime/versions").mkdir(parents=True)
        harness = cls.work / "harness"
        harness.mkdir(exist_ok=True)

    def setUp(self):
        harness = self.work / "harness"
        self._previous_cwd = os.getcwd()
        os.chdir(harness)

    def tearDown(self):
        os.chdir(self._previous_cwd)

    def fake_installer(self, body: str) -> Path:
        source = Path(tempfile.mkdtemp(prefix="source-", dir=str(self.work)))
        source.joinpath("install.py").write_text(body)
        return source

    def ledger(self, name: str = "suite"):
        ledger = self.lib.run_ledger(name)
        return ledger

    def test_identity_check_rejects_wrong_uuid_before_writes(self):
        identity = {
            "platform": "Darwin",
            "hypervisor_present": "1",
            "hardware_uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        }
        with self.assertRaises(self.lib.RecipeError):
            self.lib.verify_guest_identity(
                "11111111-2222-3333-4444-555555555555", identity
            )
        marker = self.work / "identity-probe-marker"
        try:
            self.lib.verify_guest_identity(
                "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", identity
            )
        finally:
            self.assertFalse(marker.exists())

    def test_identity_check_rejects_physical_host(self):
        with self.assertRaises(self.lib.RecipeError):
            self.lib.verify_guest_identity(
                "11111111-2222-3333-4444-555555555555",
                {"platform": "Darwin", "hypervisor_present": "0", "hardware_uuid": "x"},
            )

    def test_postcondition_compares_bits_and_rejects_duplicates(self):
        target = [
            {
                "installation_scope": "user-global",
                "relative_path": "a",
                "executable": False,
                "sha256": "0" * 64,
            }
        ]
        actual = json.loads(json.dumps(target))
        actual[0]["executable"] = True
        violations = self.lib.postcondition_violations(
            target, actual, lambda scope, path: False
        )
        self.assertTrue(
            any("executable bit changed" in v for v in violations), violations
        )
        duplicate = target + json.loads(json.dumps(target))
        with self.assertRaises(self.lib.RecipeError):
            self.lib.postcondition_violations(
                duplicate, actual, lambda scope, path: False
            )

    def test_interrupted_update_records_owned_staging_and_preserves_foreign(self):
        source = self.fake_installer(FAKE_INSTALLER_STAGE)
        versions = self.home / ".aquarium/status-runtime/versions"
        (versions / ".generation.foreign").mkdir(exist_ok=True)
        ledger = self.lib.run_ledger("interrupt-suite")
        os.environ["FAKE_HOME"] = str(self.home)
        os.environ.pop("FAKE_INSTALLER_MODE", None)
        try:
            observation = self.lib.interrupted_update(
                sys.executable, source, self.home, ledger, deadline_seconds=30
            )
        finally:
            os.environ.pop("FAKE_HOME", None)
        self.assertTrue(observation["interrupted"])
        self.assertNotEqual(observation["staging_directory"], ".generation.foreign")
        self.assertIn(".generation.foreign", observation["foreign_staging_preserved"])
        self.assertTrue((versions / ".generation.foreign").is_dir())
        self.assertTrue(ledger.owns("staging", observation["staging_directory"]))

    def test_interrupted_update_reports_missed_checkpoint(self):
        source = self.fake_installer(FAKE_INSTALLER_STAGE)
        ledger = self.lib.run_ledger("miss-suite")
        os.environ["FAKE_HOME"] = str(self.home)
        os.environ["FAKE_INSTALLER_MODE"] = "miss"
        try:
            observation = self.lib.interrupted_update(
                sys.executable, source, self.home, ledger, deadline_seconds=30
            )
        finally:
            os.environ.pop("FAKE_HOME", None)
            os.environ.pop("FAKE_INSTALLER_MODE", None)
        self.assertFalse(observation["interrupted"])
        self.assertIn("interruption checkpoint missed", observation["reason"])

    def test_owned_generation_removal_preserves_foreign_state(self):
        ledger = self.lib.run_ledger("generation-suite")
        versions = self.home / ".aquarium/status-runtime/versions"
        foreign = versions / "aaa-py3.14"
        foreign.mkdir(parents=True, exist_ok=True)
        (foreign / "runtime.json").write_text("{}")
        self.assertFalse(
            self.lib.remove_owned_generation(self.home, "aaa-py3.14", ledger)
        )
        self.assertTrue(foreign.is_dir())
        ledger.record_generation("bbb-py3.14")
        owned = versions / "bbb-py3.14"
        owned.mkdir(parents=True, exist_ok=True)
        (owned / "runtime.json").write_text("{}")
        self.assertTrue(
            self.lib.remove_owned_generation(self.home, "bbb-py3.14", ledger)
        )
        self.assertFalse(owned.exists())

    def write_fake_codex(self) -> Path:
        fake_codex = self.work / "fake-codex"
        fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "state = json.load(open(os.environ['FAKE_CODEX_STATE']))\n"
            "arguments = sys.argv[1:]\n"
            "if arguments[:3] == ['plugin', 'marketplace', 'list']:\n"
            "    print(json.dumps({'marketplaces': state['marketplaces']}))\n"
            "    raise SystemExit(0)\n"
            "if arguments[:3] == ['plugin', 'marketplace', 'add']:\n"
            "    directory = arguments[3]\n"
            "    name = json.load(open(os.path.join(directory,\n"
            "        '.agents/plugins/marketplace.json')))['name']\n"
            "    for row in state['marketplaces']:\n"
            "        if row['name'] == name and row['root'] != directory:\n"
            "            print('already added from a different source',\n"
            "                  file=sys.stderr)\n"
            "            raise SystemExit(1)\n"
            "    if not any(row['name'] == name for row in state['marketplaces']):\n"
            "        state['marketplaces'].append({'name': name, 'root': directory,\n"
            "            'marketplaceSource': {'sourceType': 'local',\n"
            "                                  'source': directory}})\n"
            "    json.dump(state, open(os.environ['FAKE_CODEX_STATE'], 'w'))\n"
            "    print(json.dumps({'marketplaceName': name,\n"
            "                      'alreadyAdded': True}))\n"
            "    raise SystemExit(0)\n"
            "if arguments[:3] == ['plugin', 'marketplace', 'remove']:\n"
            "    state['marketplaces'] = [row for row in state['marketplaces']\n"
            "                             if row['name'] != arguments[3]]\n"
            "    json.dump(state, open(os.environ['FAKE_CODEX_STATE'], 'w'))\n"
            "    raise SystemExit(0)\n"
            "print('unsupported', file=sys.stderr)\n"
            "raise SystemExit(2)\n"
        )
        fake_codex.chmod(0o755)
        return fake_codex

    def test_marketplace_ownership_boundary(self):
        fake_codex = self.write_fake_codex()
        codex_state = self.work / "codex-state.json"
        codex_state.write_text(json.dumps({"marketplaces": [], "installed": []}))
        sealed = self.work / "sealed-artifact"
        marketplace_json = sealed / ".agents/plugins"
        marketplace_json.mkdir(parents=True, exist_ok=True)
        (marketplace_json / "marketplace.json").write_text(
            json.dumps({"name": "synthetic-market"})
        )
        plugin = sealed / "plugins/aquarium/.codex-plugin"
        plugin.mkdir(parents=True, exist_ok=True)
        (plugin / "plugin.json").write_text(json.dumps({"version": "0.1.21"}))
        marketplace = self.work / "harness" / ".agents" / "plugins"
        marketplace.mkdir(parents=True, exist_ok=True)
        (marketplace / "marketplace.json").write_text(
            json.dumps({"name": "synthetic-market"})
        )
        ledger = self.lib.run_ledger("marketplace-suite")
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-marketplace"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(codex_state)
        self.addCleanup(os.environ.pop, "FAKE_CODEX_STATE", None)
        self.addCleanup(os.environ.pop, "AQUARIUM_VM_JOB_ID", None)
        self.addCleanup(os.environ.pop, "AQUARIUM_VM_LEASE_GENERATION", None)
        target = self.lib.marketplace_dir(self.home, "artifact")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir()
        (target / "FOREIGN.txt").write_text("foreign\n")
        with self.assertRaises(self.lib.RecipeError):
            self.lib.establish_marketplace(
                str(fake_codex),
                self.home,
                sealed,
                "artifact",
                ledger,
                "synthetic-market",
            )
        self.assertTrue((target / "FOREIGN.txt").is_file())
        shutil.rmtree(target)
        established = self.lib.establish_marketplace(
            str(fake_codex),
            self.home,
            sealed,
            "artifact",
            ledger,
            "synthetic-market",
        )
        self.assertEqual(established, target)
        sidecar = self.lib.read_owner_sidecar(self.home, "artifact")
        self.assertIsNotNone(sidecar)
        self.assertIn("job_id", sidecar)
        with self.assertRaises(self.lib.RecipeError):
            self.lib.marketplace_dir(self.home, "unknown-kind")
        # Removal unregisters only while the registration points at the kind.
        removal = self.lib.remove_owned_marketplace(
            str(fake_codex), self.home, "artifact", ledger, "synthetic-market"
        )
        self.assertTrue(removal["removed"])
        self.assertTrue(removal.get("unregistered"))
        self.assertFalse(target.exists())

    def test_c5_f1_target_replacement_frees_predecessor_first(self):
        """Reproduce the real swap: candidate predecessor registered first,
        then the prior target must free the name through the fully-owned
        predecessor before the target directory is replaced."""
        fake_codex = self.write_fake_codex()
        codex_state = self.work / "codex-state-f1.json"
        codex_state.write_text(json.dumps({"marketplaces": [], "installed": []}))
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-f1"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(codex_state)
        self.addCleanup(os.environ.pop, "AQUARIUM_VM_JOB_ID", None)
        self.addCleanup(os.environ.pop, "AQUARIUM_VM_LEASE_GENERATION", None)
        self.addCleanup(os.environ.pop, "FAKE_CODEX_STATE", None)

        def sealed(name: str, version: str) -> Path:
            tree = self.work / f"sealed-f1-{name}"
            if tree.exists():
                shutil.rmtree(tree)
            market = tree / ".agents/plugins"
            market.mkdir(parents=True)
            (market / "marketplace.json").write_text(
                json.dumps({"name": "synthetic-market"})
            )
            plugin = tree / "plugins/aquarium/.codex-plugin"
            plugin.mkdir(parents=True)
            (plugin / "plugin.json").write_text(json.dumps({"version": version}))
            return tree

        marketplaces = self.home / ".aquarium-vm-marketplaces"
        self.addCleanup(shutil.rmtree, marketplaces, True)
        candidate_sealed = sealed("candidate", "0.1.22")
        prior_sealed = sealed("prior", "0.1.21")
        # 1. Establish and register the candidate predecessor.
        self.lib.establish_marketplace(
            str(fake_codex),
            self.home,
            candidate_sealed,
            "artifact",
            self.lib.run_ledger("f1-candidate"),
            "synthetic-market",
        )
        registrations = self.lib.marketplace_registrations(str(fake_codex))
        self.assertTrue(registrations["synthetic-market"].endswith("/artifact"))
        # 2. Establish the prior target: the name must be freed through the
        # fully-owned candidate predecessor before prior replaces it.
        restored = self.lib.establish_marketplace(
            str(fake_codex),
            self.home,
            prior_sealed,
            "prior-artifact",
            self.lib.run_ledger("f1-restore"),
            "synthetic-market",
            declared_predecessors=("artifact",),
        )
        self.assertTrue(restored.is_dir())
        self.assertEqual(
            self.lib.marketplace_registrations(str(fake_codex)).get("synthetic-market"),
            str(restored),
        )

    def test_c8_f4_ineffective_unregister_preserves_target(self):
        """Failure path: `marketplace remove` reports success but the
        registration persists. The real preservation behavior is asserted:
        the prior-artifact target directory and its sidecar stay absent,
        the candidate predecessor directory and its sidecar are unchanged,
        and the final registration still points at the predecessor."""
        fake_codex = self.write_fake_codex()
        sticky = self.work / "fake-codex-sticky"
        sticky.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "state = json.load(open(os.environ['FAKE_CODEX_STATE']))\n"
            "arguments = sys.argv[1:]\n"
            "if arguments[:3] == ['plugin', 'marketplace', 'list']:\n"
            "    print(json.dumps({'marketplaces': state['marketplaces']}))\n"
            "    raise SystemExit(0)\n"
            "if arguments[:3] == ['plugin', 'marketplace', 'add']:\n"
            "    directory = arguments[3]\n"
            "    name = json.load(open(os.path.join(directory,\n"
            "        '.agents/plugins/marketplace.json')))['name']\n"
            "    existing = next((row for row in state['marketplaces']\n"
            "                     if row['name'] == name), None)\n"
            "    if existing is not None and existing['root'] != directory:\n"
            "        # Native duplicate-name rejection (facts §B).\n"
            "        message = ('Error: marketplace ' + name +\n"
            "                   ' is already added from a different source')\n"
            "        print(message, file=sys.stderr)\n"
            "        raise SystemExit(1)\n"
            "    if existing is None:\n"
            "        state['marketplaces'].append({\n"
            "            'name': name, 'root': directory,\n"
            "            'marketplaceSource': {'sourceType': 'local',\n"
            "                                  'source': directory}})\n"
            "    json.dump(state, open(os.environ['FAKE_CODEX_STATE'], 'w'))\n"
            "    print(json.dumps({'marketplaceName': name,\n"
            "                      'alreadyAdded': existing is not None}))\n"
            "    raise SystemExit(0)\n"
            "if arguments[:3] == ['plugin', 'marketplace', 'remove']:\n"
            "    # Reports success but silently keeps the registration.\n"
            "    print(json.dumps({'removed': arguments[3]}))\n"
            "    raise SystemExit(0)\n"
            "print('unsupported', file=sys.stderr)\n"
            "raise SystemExit(2)\n"
        )
        sticky.chmod(0o755)
        codex_state = self.work / "codex-state-f4.json"
        codex_state.write_text(json.dumps({"marketplaces": [], "installed": []}))
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-f4"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(codex_state)
        self.addCleanup(os.environ.pop, "AQUARIUM_VM_JOB_ID", None)
        self.addCleanup(os.environ.pop, "AQUARIUM_VM_LEASE_GENERATION", None)
        self.addCleanup(os.environ.pop, "FAKE_CODEX_STATE", None)

        def sealed(name: str, version: str) -> Path:
            tree = self.work / f"sealed-f4-{name}"
            if tree.exists():
                shutil.rmtree(tree)
            market = tree / ".agents/plugins"
            market.mkdir(parents=True)
            (market / "marketplace.json").write_text(
                json.dumps({"name": "synthetic-market"})
            )
            plugin = tree / "plugins/aquarium/.codex-plugin"
            plugin.mkdir(parents=True)
            (plugin / "plugin.json").write_text(json.dumps({"version": version}))
            return tree

        marketplaces = self.home / ".aquarium-vm-marketplaces"
        self.addCleanup(shutil.rmtree, marketplaces, True)
        candidate = sealed("candidate", "0.1.22")
        prior = sealed("prior", "0.1.21")
        self.lib.establish_marketplace(
            str(fake_codex),
            self.home,
            candidate,
            "artifact",
            self.lib.run_ledger("f4-candidate"),
            "synthetic-market",
        )
        predecessor_dir = self.lib.marketplace_dir(self.home, "artifact")
        predecessor_digest = self.lib.tree_sha256_from_directory(predecessor_dir)
        predecessor_sidecar = self.lib.read_owner_sidecar(self.home, "artifact")
        target = self.lib.marketplace_dir(self.home, "prior-artifact")
        with self.assertRaises(self.lib.RecipeError):
            self.lib.establish_marketplace(
                str(sticky),
                self.home,
                prior,
                "prior-artifact",
                self.lib.run_ledger("f4-restore"),
                "synthetic-market",
                declared_predecessors=("artifact",),
            )
        # The prior target directory and its sidecar stay absent.
        self.assertFalse(target.exists())
        self.assertIsNone(self.lib.read_owner_sidecar(self.home, "prior-artifact"))
        # The predecessor directory and its sidecar are unchanged.
        self.assertTrue(predecessor_dir.is_dir())
        self.assertEqual(
            self.lib.tree_sha256_from_directory(predecessor_dir),
            predecessor_digest,
        )
        self.assertEqual(
            self.lib.read_owner_sidecar(self.home, "artifact"),
            predecessor_sidecar,
        )
        # The final registration still points at the predecessor.
        self.assertEqual(
            self.lib.marketplace_registrations(str(sticky)).get("synthetic-market"),
            str(predecessor_dir),
        )

    def test_mutated_predecessor_registration_is_refused(self):
        fake_codex = self.work / "fake-codex"
        codex_state = self.work / "codex-state-mutated.json"
        # Register the prior-artifact directory as an owned predecessor.
        target = self.lib.marketplace_dir(self.home, "prior-artifact")
        if target.exists():
            shutil.rmtree(target)
        sealed_prior = self.work / "sealed-prior"
        marketplace_json = sealed_prior / ".agents/plugins"
        marketplace_json.mkdir(parents=True, exist_ok=True)
        (marketplace_json / "marketplace.json").write_text(
            json.dumps({"name": "synthetic-market"})
        )
        plugin = sealed_prior / "plugins/aquarium/.codex-plugin"
        plugin.mkdir(parents=True, exist_ok=True)
        (plugin / "plugin.json").write_text(json.dumps({"version": "0.1.21"}))
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-mutated"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(codex_state)
        self.addCleanup(os.environ.pop, "AQUARIUM_VM_JOB_ID", None)
        self.addCleanup(os.environ.pop, "AQUARIUM_VM_LEASE_GENERATION", None)
        self.addCleanup(os.environ.pop, "FAKE_CODEX_STATE", None)
        ledger = self.lib.run_ledger("mutated-suite")
        codex_state.write_text(json.dumps({"marketplaces": [], "installed": []}))
        self.lib.establish_marketplace(
            str(fake_codex),
            self.home,
            sealed_prior,
            "prior-artifact",
            ledger,
            "synthetic-market",
        )
        # Mutate the predecessor payload after the sidecar was written.
        (target / "MUTATED.txt").write_text("drift\n")
        sealed_candidate = self.work / "sealed-candidate"
        shutil.copytree(sealed_prior, sealed_candidate, dirs_exist_ok=True)
        (sealed_candidate / "plugins/aquarium/.codex-plugin/plugin.json").write_text(
            json.dumps({"version": "0.1.22"})
        )
        candidate_ledger = self.lib.run_ledger("mutated-candidate")
        with self.assertRaises(self.lib.RecipeError):
            self.lib.establish_marketplace(
                str(fake_codex),
                self.home,
                sealed_candidate,
                "artifact",
                candidate_ledger,
                "synthetic-market",
                declared_predecessors=("prior-artifact",),
            )
        self.assertTrue((target / "MUTATED.txt").is_file())

    def test_runtime_receipt_identity_uses_bare_hex(self):
        receipt = {
            "source_sha256": "a" * 64,
            "plugin_version": "0.1.21",
            "python_executable_sha256": "b" * 64,
        }
        self.assertEqual(
            self.lib.assert_runtime_identity(
                receipt,
                source_sha256="sha256:" + "a" * 64,
                plugin_version="0.1.21",
                python_sha256="sha256:" + "b" * 64,
            ),
            [],
        )
        self.assertTrue(
            self.lib.assert_runtime_identity(
                receipt, source_sha256="sha256:" + "c" * 64
            )
        )

    def test_unsafe_launcher_refusal_is_explicit_safe_failure(self):
        source = self.fake_installer(FAKE_INSTALLER_REFUSE)
        launcher = self.home / ".local/bin/aquarium-status"
        launcher.parent.mkdir(parents=True, exist_ok=True)
        launcher.write_text("#!/bin/sh\n")
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-refusal"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        observation = self.lib.unsafe_launcher_refusal(
            sys.executable, source, self.home
        )
        os.environ.pop("AQUARIUM_VM_JOB_ID", None)
        os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)
        self.assertTrue(observation["refused"])
        self.assertTrue(launcher.is_file())
        self.assertFalse(launcher.is_symlink())

    def test_pip_install_uses_require_hashes_and_no_deps(self):
        venv_python = self.work / "fake-venv-python"
        captured = self.work / "pip-argv.json"
        venv_python.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            f"open({str(captured)!r}, 'w').write(json.dumps(sys.argv[1:]))\n"
        )
        venv_python.chmod(0o755)
        lock = self.work / "requirements.lock"
        lock.write_text("pytest==8.3.5 --hash=sha256:" + "a" * 64 + "\n")
        result = self.lib.pip_install_locked(venv_python, lock)
        self.assertEqual(result["exit"], 0)
        argv = json.loads(captured.read_text())
        self.assertIn("--require-hashes", argv)
        self.assertIn("--no-deps", argv)
        self.assertIn("-r", argv)

    def test_verify_sealed_inputs_detects_mutation(self):
        root = self.work / "sealed-root"
        recipes = root / "harness/tests/vm/recipes"
        (root / "artifact/plugins").mkdir(parents=True)
        (root / "prior-artifact/plugins").mkdir(parents=True)
        recipes.mkdir(parents=True)
        (recipes / "guest_main.py").write_text("body\n")
        (root / "artifact/plugins/plugin.json").write_text("candidate\n")
        (root / "prior-artifact/plugins/plugin.json").write_text("prior\n")
        module = load_module("vm_tree_digest_sealed", TREE_DIGEST_PATH)

        def subtree(directory: Path) -> str:
            return module.tree_sha256_from_directory(directory)

        inputs = {
            "schema": "aquarium.vm-host-inputs/v1",
            "candidate": {
                "git_sha": "0" * 40,
                "development_version": "v0.1.21-dev.000000000000",
                "artifact_tree_sha256": subtree(root / "artifact"),
            },
            "prior": {
                "version": "0.1.21",
                "tag": "v0.1.21",
                "tag_commit": "1" * 40,
                "artifact_tree_sha256": subtree(root / "prior-artifact"),
            },
            "harness_tree_sha256": subtree(recipes),
        }
        (recipes.parent / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
        original = self.lib.load_inputs
        self.lib.load_inputs = lambda: inputs
        try:
            verified = self.lib.verify_sealed_inputs(root)
            self.assertEqual(len(verified), 3)
            (root / "artifact/plugins/plugin.json").write_text("mutated\n")
            with self.assertRaises(self.lib.RecipeError):
                self.lib.verify_sealed_inputs(root)
        finally:
            self.lib.load_inputs = original

    def test_c19_finish_requires_consumer_cleanup_claim(self):
        # finish has no default consumer_cleanup; every suite must
        # state its claim, so a missing one fails loudly at call time.
        with self.assertRaises(TypeError):
            self.lib.finish("suite", "pass", {})

    def test_c36_read_current_generation_requires_object_receipt(self):
        # Malformed JSON and non-object receipts raise the same
        # incomplete RecipeError as the existing guards; a valid object
        # receipt still returns (name, receipt).
        home = self.work / "c36-receipt-home"
        runtime_root, _launcher = self.lib.runtime_locations(home)
        versions = runtime_root / "versions"
        generation = versions / "c36-generation"
        generation.mkdir(parents=True)
        (runtime_root / "current").write_text("versions/c36-generation\n")
        valid = {"schema": "aquarium-status-runtime/v1", "plugin_version": "v0.1.21"}
        receipt_path = generation / "runtime.json"
        for raw, needle in (
            ("null", "not a JSON object"),
            ("[1, 2]", "not a JSON object"),
            ("{not json", "malformed receipt"),
        ):
            receipt_path.write_text(raw)
            with self.assertRaises(self.lib.RecipeError) as raised:
                self.lib.read_current_generation(home)
            self.assertEqual(raised.exception.outcome, "incomplete")
            self.assertIn(needle, str(raised.exception))
        receipt_path.write_text(json.dumps(valid))
        name, receipt = self.lib.read_current_generation(home)
        self.assertEqual(name, "c36-generation")
        self.assertEqual(receipt, valid)

    def test_c38_read_current_generation_undecodable_bytes(self):
        # The current marker and the receipt are read inside the error
        # boundary, so undecodable bytes become the structured incomplete
        # RecipeError instead of a UnicodeDecodeError traceback.
        home = self.work / "c38-current-home"
        runtime_root, _launcher = self.lib.runtime_locations(home)
        versions = runtime_root / "versions"
        generation = versions / "c38-generation"
        generation.mkdir(parents=True)
        (runtime_root / "current").write_text("versions/c38-generation\n")
        receipt_path = generation / "runtime.json"
        receipt_path.write_text('{"plugin_version": "v0.1.21"}')
        current = runtime_root / "current"
        original = current.read_bytes()
        try:
            current.write_bytes(b"versions/\xffgeneration\n")
            with self.assertRaises(self.lib.RecipeError) as raised:
                self.lib.read_current_generation(home)
            self.assertEqual(raised.exception.outcome, "incomplete")
            self.assertIn("unreadable", str(raised.exception))
        finally:
            current.write_bytes(original)
        receipt_path.write_bytes(b'{"plugin_version": "\xff"}')
        with self.assertRaises(self.lib.RecipeError) as raised:
            self.lib.read_current_generation(home)
        self.assertEqual(raised.exception.outcome, "incomplete")
        self.assertIn("malformed receipt", str(raised.exception))

    def test_c38_generation_receipts_unreadable_receipts_refused(self):
        # A malformed, undecodable or non-object receipt names its
        # generation in an incomplete RecipeError; a bad receipt is never
        # skipped, and a valid set still returns every receipt.
        home = self.work / "c38-receipts-home"
        runtime_root, _launcher = self.lib.runtime_locations(home)
        versions = runtime_root / "versions"
        good = versions / "aaaa-good"
        good.mkdir(parents=True)
        (good / "runtime.json").write_text('{"plugin_version": "v0.1.20"}')
        valid = {"aaaa-good": {"plugin_version": "v0.1.20"}}
        self.assertEqual(self.lib.generation_receipts(home), valid)
        for name, raw, needle in (
            ("bbbb-malformed", "{not json", "unreadable"),
            ("cccc-nonobject", "null", "not a"),
        ):
            bad = versions / name
            bad.mkdir()
            (bad / "runtime.json").write_text(raw)
            with self.assertRaises(self.lib.RecipeError) as raised:
                self.lib.generation_receipts(home)
            self.assertEqual(raised.exception.outcome, "incomplete")
            self.assertIn(name, str(raised.exception))
            self.assertIn(needle, str(raised.exception))
            shutil.rmtree(bad)
        undecodable = versions / "dddd-raw"
        undecodable.mkdir()
        (undecodable / "runtime.json").write_bytes(b'{"x": "\xff"}')
        with self.assertRaises(self.lib.RecipeError) as raised:
            self.lib.generation_receipts(home)
        self.assertEqual(raised.exception.outcome, "incomplete")
        self.assertIn("dddd-raw", str(raised.exception))
        shutil.rmtree(undecodable)
        self.assertEqual(self.lib.generation_receipts(home), valid)

    def test_c38_read_owner_sidecar_unparsable_returns_none(self):
        # An unreadable, undecodable, malformed or non-object sidecar
        # returns None under the existing "missing or unparsable"
        # contract, so ownership fails closed as not owned.
        home = self.work / "c38-sidecar-home"
        home.mkdir()
        path = self.lib.owner_sidecar_path(home, "prior-artifact")
        path.parent.mkdir(parents=True, exist_ok=True)
        valid = {
            "schema": self.lib.OWNERSHIP_SCHEMA,
            "kind": "prior-artifact",
            "artifact_tree_sha256": "a" * 64,
            "job_id": "job-c38",
        }
        for raw in ("{not json", "[1]", "null", '"x"'):
            path.write_text(raw)
            self.assertIsNone(self.lib.read_owner_sidecar(home, "prior-artifact"))
        path.write_bytes(b'{"kind": "\xff"}')
        self.assertIsNone(self.lib.read_owner_sidecar(home, "prior-artifact"))
        path.write_text(json.dumps(valid))
        self.assertEqual(self.lib.read_owner_sidecar(home, "prior-artifact"), valid)

    def test_c17_owned_directory_with_unsafe_object_is_not_owned(self):
        # A strict-digest failure means "cannot be byte-identical to a
        # sealed artifact", so ownership fails closed as not owned instead
        # of crashing the caller.
        home = self.work / "c17-owned-home"
        marketplace = self.lib.marketplace_dir(home, "artifact")
        (marketplace / "plugins").mkdir(parents=True)
        (marketplace / "plugins/payload.txt").write_text("payload\n")
        sidecar = {
            "schema": self.lib.OWNERSHIP_SCHEMA,
            "kind": "artifact",
            "artifact_tree_sha256": self.lib.tree_sha256_from_directory(marketplace),
            "job_id": "job-c17-owned",
        }
        self.lib.owner_sidecar_path(home, "artifact").write_text(json.dumps(sidecar))
        self.assertTrue(self.lib._harness_directory_owned(home, "artifact"))
        fifo = marketplace / "stuck-pipe"
        os.mkfifo(fifo)
        try:
            self.assertFalse(self.lib._harness_directory_owned(home, "artifact"))
        finally:
            fifo.unlink()
        link = marketplace / "plugins/link"
        link.symlink_to("payload.txt")
        try:
            self.assertFalse(self.lib._harness_directory_owned(home, "artifact"))
        finally:
            link.unlink()
        self.assertTrue(self.lib._harness_directory_owned(home, "artifact"))


class GuestEntryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-entry-"))
        cls.addClassCleanup(shutil.rmtree, cls.work, True)

    def invoke(self, environment: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["/bin/sh", str(ENTRY_PATH), "--suite", "probe"],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin", **environment},
            timeout=60,
            check=False,
        )

    def context(self, job="job-1", lease="1", nonce=None):
        nonce = nonce or "ab" * 32
        return json.dumps([{"job_id": job, "lease_generation": lease, "nonce": nonce}])

    def test_entry_requires_managed_context(self):
        result = self.invoke({})
        self.assertEqual(result.returncode, 2)
        self.assertIn("Job/lease context", result.stderr)

    def test_entry_rejects_malformed_context(self):
        for bad in (
            {"HAEPARI_PARENT_CONTEXT": self.context(nonce="xyz")},
            {"HAEPARI_PARENT_CONTEXT": self.context(lease="0")},
            {"HAEPARI_PARENT_CONTEXT": "not-a-plist"},
        ):
            result = self.invoke(bad)
            self.assertEqual(result.returncode, 2, bad)

    def test_entry_requires_guest_interpreter_selection(self):
        result = self.invoke(
            {"HAEPARI_PARENT_CONTEXT": self.context(), "AQUARIUM_GUEST_PYTHON": ""}
        )
        self.assertEqual(result.returncode, 2)


class GuestMainTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-guest-main-"))
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        if str(RECIPES_ROOT) not in sys.path:
            sys.path.insert(0, str(RECIPES_ROOT))
        import guest_main

        cls.guest_main = guest_main

    def test_main_requires_managed_context(self):
        result = subprocess.run(
            [sys.executable, "-B", str(MAIN_PATH), "--suite", "immutability-probe"],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin"},
            timeout=60,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("managed runner context", result.stderr)

    def _safety_run(self, error: Exception) -> tuple[int, dict]:
        # job_root() accepts a cwd named exactly "harness".
        harness = self.work / f"case-{type(error).__name__}" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        (harness / "inputs.json").write_text(
            json.dumps(
                {
                    "schema": "aquarium.vm-host-inputs/v1",
                    "candidate": {"development_version": "v0.1.21-dev.test"},
                }
            )
        )

        class StubContext:
            root = harness

        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            with (
                mock.patch.object(self.guest_main, "Context", StubContext),
                mock.patch.object(self.guest_main.lib, "guard", lambda _root: {}),
                mock.patch.object(self.guest_main, "run_baseline", side_effect=error),
                mock.patch.dict(os.environ, {"HAEPARI_PARENT_CONTEXT": "[{}]"}),
                mock.patch.object(
                    sys, "argv", ["guest_main.py", "--suite", "baseline"]
                ),
            ):
                exit_code = self.guest_main.main()
            # job_root() is the harness directory's parent, so results are
            # written beside the harness, not inside it.
            result = json.loads(
                (harness.parent / "results/baseline/result.json").read_text()
            )
        finally:
            os.chdir(previous_cwd)
        return exit_code, result

    def test_c17_safety_net_converts_tree_digest_error(self):
        # A strict-validation error escaping a runner still writes a
        # structured incomplete result instead of a traceback.
        exit_code, result = self._safety_run(
            self.guest_main.lib.TreeDigestError(
                "special file inside inventory scope: /synthetic/pipe"
            )
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["outcome"], "incomplete")
        self.assertEqual(
            result["problem"],
            "TreeDigestError: special file inside inventory scope: /synthetic/pipe",
        )
        self.assertEqual(result["consumer_cleanup"], "unverified")

    def test_c17_safety_net_converts_os_error(self):
        exit_code, result = self._safety_run(OSError("disk gone"))
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["outcome"], "incomplete")
        self.assertEqual(result["problem"], "OSError: disk gone")
        self.assertEqual(result["consumer_cleanup"], "unverified")

    def test_c38_safety_net_converts_value_error(self):
        # Decoding failures outside the structured readers produce the
        # same structured incomplete result as OSError and TreeDigestError.
        exit_code, result = self._safety_run(ValueError("'utf-8' codec can't decode"))
        self.assertEqual(exit_code, 2)
        self.assertEqual(result["outcome"], "incomplete")
        self.assertEqual(result["problem"], "ValueError: 'utf-8' codec can't decode")
        self.assertEqual(result["consumer_cleanup"], "unverified")

    def test_c20_generation_replaced_by_regular_file_is_residue(self):
        # A ledger generation replaced by a regular file is residue only a
        # type-independent absence check can see. The codex observations
        # are stubbed so the unit exercises the absence checks directly;
        # run_install turns any problem into consumer_cleanup failed, which
        # the c18 and c20 simulation tests cover end-to-end.
        module = self.guest_main
        home = self.work / "c20-file-generation-home"
        versions = home / ".aquarium/status-runtime/versions"
        versions.mkdir(parents=True)
        name = f"{'b' * 64}-py3.14"
        (versions / name).write_text("not a generation directory\n")

        class StubContext:
            def __init__(self, home):
                self.home = home
                self.codex = "/synthetic/codex"
                self.marketplace = "root-kernel"

            def marketplace_path(self, kind):
                return self.home / ".aquarium-vm-marketplaces" / kind

        ledger = module.lib.RunLedger(self.work / "c20-ledger.json")
        ledger.record_generation(name)
        with (
            mock.patch.object(
                module.lib, "installed_aquarium", lambda codex, marketplace: None
            ),
            mock.patch.object(
                module.lib, "assert_registration", lambda codex, marketplace, x: None
            ),
        ):
            problems = module.install_cleanup_problems(
                StubContext(home),
                ledger,
                {"marketplace": {"kind": "artifact", "removed": False}},
            )
        self.assertEqual(problems, [f"run-owned generation remains: {name}"])


if __name__ == "__main__":
    unittest.main()
