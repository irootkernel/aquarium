from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
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


class ReleaseAcceptanceUnitTest(unittest.TestCase):
    """Offline unit coverage for the J-RA recipe helpers and phases."""

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-jra-unit-")).resolve()
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        if str(RECIPES_ROOT) not in sys.path:
            sys.path.insert(0, str(RECIPES_ROOT))
        import guest_main

        cls.guest_main = guest_main
        cls.home = cls.work / "home"
        (cls.home / ".codex/skills").mkdir(parents=True)
        (cls.home / ".codex/skills/system-skill").mkdir()
        (cls.home / ".codex/skills/system-skill/SKILL.md").write_text("system\n")
        cls.codex_state = cls.work / "residue-codex-state.json"
        cls.codex_state.write_text(json.dumps({"marketplaces": [], "installed": []}))
        cls._fake_codex = cls.work / "residue-fake-codex"
        cls._fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "arguments = sys.argv[1:]\n"
            "if arguments[:3] == ['plugin', 'marketplace', 'list']:\n"
            "    print(json.dumps({'marketplaces': json.load(\n"
            "        open(os.environ['FAKE_CODEX_STATE']))['marketplaces']}))\n"
            "    raise SystemExit(0)\n"
            "print('unsupported', file=sys.stderr)\n"
            "raise SystemExit(2)\n"
        )
        cls._fake_codex.chmod(0o755)

    def context_stub(self):
        class Stub:
            root = self.work / "job"
            home = self.home

        return Stub()

    def test_retained_upgrade_cleanup_checks_unrelated_inventory(self):
        import copy

        import podway_upgrade

        module = self.guest_main
        context = mock.MagicMock()
        context.dev_version = "0.1.21-dev.fixture"
        context.inputs = {"candidate": {"git_sha": "a" * 40}}
        records = {
            "machine-prepare.json": {},
            "record-setup-task.json": {},
            "record-setup-epic.json": {},
            "record-setup-preservation.json": {},
            "capture.json": {"exit": 0},
            "podway-upgrade.json": {"identity": {"result": {"version": "v0.2.16"}}},
            "candidate-install.json": {},
            "skill-identity.json": {
                "comparisons": {"all_passed": True},
                "prior_stage": {"comparisons": {"all_passed": True}},
            },
            "runtime-update.json": {
                "approval_completed": True,
                "workflow_exit": 0,
                "receipt_plugin_version": "v0.1.21-dev.fixture",
            },
            "managed-update-task.json": {"exit": 0},
            "managed-update-epic.json": {"exit": 0},
            "managed-update-preservation.json": {"exit": 0},
            "startup-smokes.json": {"outcome": "pass", "exit": 0},
            "release-startup.json": {
                "outcome": "pass",
                "exit": 0,
                "candidate_sha": "a" * 40,
            },
            "stale-skill.json": {
                "observation": {"outcome": "shadowing"},
                "restoration": {"verified": True},
            },
            "stage-evidence.json": {"ok": True},
        }
        before = [
            {
                "installation_scope": scope,
                "relative_path": path,
                "sha256": "a" * 64,
                "executable": False,
            }
            for scope, path in (
                ("user-global", ".aquarium/user-settings.json"),
                ("user-global", ".aquarium/status-runtime/current"),
                ("shared-agents-skills", ".agents/skills/use-podway/SKILL.md"),
                ("user-global", ".aquarium/status.yaml"),
            )
        ]
        retained = copy.deepcopy(before)
        for entry in retained[1:]:
            entry["sha256"] = "b" * 64
        retained.append(
            {
                "installation_scope": "user-global",
                "relative_path": ".aquarium/status.lock",
                "sha256": hashlib.sha256(b"").hexdigest(),
                "executable": False,
            }
        )
        variants = {"retained-upgrade": retained}
        for name in ("content", "missing", "extra", "executable"):
            entries = copy.deepcopy(retained)
            if name == "content":
                entries[0]["sha256"] = "c" * 64
            elif name == "missing":
                entries.pop(0)
            elif name == "extra":
                entries.append(
                    {**before[0], "relative_path": ".aquarium/unowned-leftover.txt"}
                )
            else:
                entries[0]["executable"] = True
            variants[name] = entries

        with (
            tempfile.TemporaryDirectory(dir="/tmp") as directory,
            mock.patch.object(module.lib, "guard"),
            mock.patch.object(module, "acceptance_request"),
            mock.patch.object(
                module.lib, "results_directory", return_value=Path(directory)
            ),
            mock.patch.object(podway_upgrade, "observe_tools", return_value={}),
            mock.patch.object(
                module,
                "skill_identity_document",
                return_value={"comparisons": {"all_passed": True}},
            ),
            mock.patch.object(
                module.lib,
                "read_current_generation",
                return_value=(
                    "candidate-generation",
                    {"plugin_version": "v0.1.21-dev.fixture"},
                ),
            ),
            mock.patch.object(module.lib, "assert_registration"),
            mock.patch.object(
                module.lib,
                "finish",
                side_effect=lambda _suite, outcome, _detail, **_kwargs: (
                    0 if outcome == "pass" else 1
                ),
            ) as finish,
        ):
            root = Path(directory)
            for name, record in records.items():
                (root / name).write_text(json.dumps(record))
            baseline = root / "inventory-prior-baseline.json"
            baseline.write_text(
                json.dumps({"schema": module.lib.INVENTORY_SCHEMA, "entries": before})
            )
            for name, entries in variants.items():
                with self.subTest(variant=name):
                    context.snapshot.return_value = entries
                    expected = "verified" if name == "retained-upgrade" else "failed"
                    code = module.run_release_acceptance(
                        context, "consumer-cleanup", "task"
                    )
                    self.assertEqual(code, 0 if expected == "verified" else 1)
                    self.assertEqual(
                        finish.call_args.kwargs["consumer_cleanup"], expected
                    )
                    observed = json.loads((root / "consumer-cleanup.json").read_text())
                    self.assertEqual(bool(observed["violations"]), expected == "failed")
            baseline.unlink()
            with self.assertRaises(module.lib.RecipeError) as error:
                module.run_release_acceptance(context, "consumer-cleanup", "task")
            self.assertEqual(error.exception.outcome, "incomplete")

    def test_codex_identity_records_only_login_mode_from_either_stream(self):
        context = self.context_stub()
        context.codex = "/fixture/codex"
        for stream in ("stdout", "stderr"):
            with self.subTest(stream=stream):
                output = {"stdout": "", "stderr": ""}
                output[stream] = "private account detail\nLogged in using ChatGPT\n"
                with mock.patch.object(
                    self.guest_main.lib,
                    "run",
                    side_effect=[
                        subprocess.CompletedProcess([], 0, "codex-cli 0.164.0\n", ""),
                        subprocess.CompletedProcess([], 0, **output),
                    ],
                ):
                    identity = self.guest_main.codex_identity_record(context)
                self.assertEqual(
                    identity["login_status"],
                    {"exit": 0, "mode": "chatgpt", "line": "Logged in using ChatGPT"},
                )
                self.assertNotIn("private account detail", json.dumps(identity))

    def test_codex_identity_refuses_unverified_or_failed_login(self):
        context = self.context_stub()
        context.codex = "/fixture/codex"
        for exit_code, stdout, stderr in (
            (0, "", ""),
            (0, "opaque account detail", ""),
            (0, "", "Logged in using an API key - private fixture value"),
            (1, "", "Logged in using ChatGPT"),
        ):
            with self.subTest(exit_code=exit_code, stdout=stdout, stderr=stderr):
                with (
                    mock.patch.object(
                        self.guest_main.lib,
                        "run",
                        side_effect=[
                            subprocess.CompletedProcess(
                                [], 0, "codex-cli 0.164.0\n", ""
                            ),
                            subprocess.CompletedProcess([], exit_code, stdout, stderr),
                        ],
                    ),
                    self.assertRaises(self.guest_main.lib.RecipeError) as error,
                ):
                    self.guest_main.codex_identity_record(context)
                self.assertEqual(error.exception.outcome, "incomplete")

    def test_numeric_startup_reports_are_preserved_without_becoming_windows(self):
        root = Path(tempfile.mkdtemp(prefix="startup-reports-", dir=self.work))
        self.addCleanup(shutil.rmtree, root, True)
        for case in ("task-startup", "epic-startup"):
            with self.subTest(case=case):
                directory = root / case
                directory.mkdir()
                fields = (
                    "executor_assignment",
                    "evaluator_assignment",
                    "executor_result",
                    "evaluator_assessment",
                )
                reports = {}
                for field, suffix in zip(fields, ("input", "jsonl", "stderr", "last")):
                    path = directory / f"001.{suffix}"
                    path.write_text(f"original {field}\n")
                    reports[field] = path.relative_to(root).as_posix()
                (directory / "startup-evidence.json").write_text(json.dumps(reports))
                name = case.removesuffix("-startup")
                for suffix in ("native-observation", "checks"):
                    (root / f"{name}-{suffix}.json").write_text("{}")
                operations = root / "operations" / case
                operations.mkdir(parents=True)
                for suffix in ("invocation.json", "input", "jsonl", "stderr", "last"):
                    (operations / f"000.{suffix}").write_text("original window\n")
                members, required, gaps = self.guest_main.evidence_members(root, case)
                manifest = self.guest_main.lib.stage_evidence_archive(
                    root / f"{case}.tar",
                    root,
                    members,
                    required,
                )
                self.assertEqual(gaps, [])
                self.assertEqual(manifest["missing_required"], [])
                with tarfile.open(root / f"{case}.tar") as archive:
                    for relative in reports.values():
                        self.assertEqual(
                            archive.extractfile(relative).read(),
                            (root / relative).read_bytes(),
                        )
                (operations / "001.input").write_text("interrupted invocation\n")
                members, required, _ = self.guest_main.evidence_members(root, case)
                self.assertIn(f"operations/{case}/001.invocation.json", required)
                self.assertIn(f"operations/{case}/001.input", members)

    def test_restage_bounds_every_publication_and_invalidates_interrupted_attempt(self):
        root = Path(tempfile.mkdtemp(prefix="publication-", dir=self.work)).resolve()
        self.addCleanup(shutil.rmtree, root, True)
        run_root = root / "acceptance-run"
        run_root.mkdir()
        results = root / "results/release-acceptance"
        evidence = results / "evidence"
        evidence.mkdir(parents=True)
        cases = ["baseline", "upgrade", "task-setup"]
        for case, size in zip(cases, (100, 12000, 12000), strict=True):
            (run_root / f"{case}.bin").write_bytes(b"x" * size)
        foreign = evidence / "unrelated.tar"
        foreign.write_bytes(b"preserve this unrelated output")
        context = self.context_stub()
        context.root = root

        def stage():
            with (
                mock.patch.object(self.guest_main.lib, "guard"),
                mock.patch.object(
                    self.guest_main.lib, "results_directory", return_value=results
                ),
                mock.patch.object(
                    self.guest_main,
                    "acceptance_request",
                    return_value=root / "unused.json",
                ),
                mock.patch.object(self.guest_main, "EVIDENCE_CASES", cases),
                mock.patch.object(
                    self.guest_main,
                    "evidence_members",
                    side_effect=lambda _root, case: ([f"{case}.bin"], [], []),
                ),
                mock.patch.object(self.guest_main, "ARCHIVE_BYTES_BOUND", 30720),
                mock.patch.object(self.guest_main, "ARCHIVE_TOTAL_BYTES_BOUND", 51200),
            ):
                return self.guest_main.run_release_acceptance(
                    context, "stage-evidence", ""
                )

        def exposed():
            return sum(
                (evidence / f"{case}.tar").stat().st_size
                for case in cases
                if (evidence / f"{case}.tar").is_file()
            )

        self.assertEqual(stage(), 0)
        self.assertEqual(exposed(), 51200)
        (run_root / "baseline.bin").write_bytes(b"y" * 12000)
        replace = Path.replace
        publications = []

        def observe(path, target):
            result = replace(path, target)
            if path.name.endswith(".tar.partial"):
                publications.append(exposed())
            return result

        with mock.patch.object(Path, "replace", observe):
            self.assertEqual(stage(), 2)
        self.assertTrue(publications)
        self.assertTrue(all(size <= 51200 for size in publications), publications)
        for case in cases:
            manifest = json.loads((evidence / f"{case}.manifest.json").read_text())
            self.assertEqual(
                manifest["archive_present"], (evidence / f"{case}.tar").is_file()
            )
        (run_root / "baseline.bin").write_bytes(b"x" * 100)
        self.assertEqual(stage(), 0)
        (run_root / "baseline.bin").write_bytes(b"y" * 12000)

        def interrupt(path, target):
            observe(path, target)
            if path.name.endswith(".tar.partial"):
                raise KeyboardInterrupt

        with (
            mock.patch.object(Path, "replace", interrupt),
            self.assertRaises(KeyboardInterrupt),
        ):
            stage()
        self.assertLessEqual(exposed(), 51200)
        self.assertIs(
            json.loads((results / "stage-evidence.json").read_text())["ok"], False
        )
        self.assertEqual(foreign.read_bytes(), b"preserve this unrelated output")

    def test_setup_capture_transport_binds_baseline_update_and_recovery_originals(self):
        root = Path(tempfile.mkdtemp(prefix="capture-", dir=self.work)).resolve()
        self.addCleanup(shutil.rmtree, root, True)
        driver = load_module(
            "setup_capture_producer", REPOSITORY / "tests/vm/run_acceptance.py"
        )
        baseline = {"setup": {}}
        for fixture in ("task", "epic", "preservation"):
            baseline["setup"][fixture] = driver.save_setup_observation(
                root, fixture, "baseline", {"fixture": fixture, "phase": "baseline"}
            )
            for suffix in ("last", "jsonl"):
                (root / f"released-{fixture}.{suffix}").write_text("original\n")
        (root / "baseline.json").write_text(json.dumps(baseline))
        update = driver.save_setup_observation(
            root, "task", "update", {"phase": "update"}
        )
        recovery = driver.save_setup_observation(
            root, "task", "recovery", {"phase": "recovery"}
        )
        upgrades = {"task": {"setup": update}}
        for fixture in ("epic", "preservation"):
            upgrades[fixture] = {
                "setup": driver.save_setup_observation(
                    root, fixture, "update", {"fixture": fixture, "phase": "update"}
                )
            }
        upgrade = root / "upgrade-observation.json"
        upgrade.write_text(json.dumps({"setup": upgrades}))
        (root / "result.json").write_text("{}\n")
        self.assertEqual(self.guest_main.evidence_members(root, "upgrade")[2], [])
        upgrades["task"]["setup"] = {
            **update,
            "observation_sha256": "sha256:" + "0" * 64,
        }
        upgrade.write_text(json.dumps({"setup": upgrades}))
        self.assertTrue(self.guest_main.evidence_members(root, "upgrade")[2])
        upgrades["task"]["setup"] = update
        upgrade.write_text(json.dumps({"setup": upgrades}))
        window = root / "operations/task-setup"
        window.mkdir(parents=True)
        for suffix in ("input", "jsonl", "stderr", "last"):
            (window / f"000.{suffix}").write_text("original\n")
        (window / "000.invocation.json").write_text('{"exit": 0}')
        (window / "000.setup-before.json").write_text(
            json.dumps({"basis": baseline["setup"]["task"]})
        )
        after = window / "000.setup-after.json"
        after.write_text(json.dumps({"setup": update}))
        (window / "000.reconciled-000.json").write_text(
            json.dumps({"setup": update, "settlement": recovery})
        )
        for case in ("baseline", "task-setup"):
            members, required, gaps = self.guest_main.evidence_members(root, case)
            self.assertEqual(gaps, [])
            archive = root / f"{case}.tar"
            manifest = self.guest_main.lib.stage_evidence_archive(
                archive, root, members, required
            )
            self.assertEqual(manifest["missing_required"], [])
            expected = (
                list(baseline["setup"].values())
                if case == "baseline"
                else [update, recovery]
            )
            with tarfile.open(archive) as handle:
                for record in expected:
                    relative = (
                        Path(record["public_observation"]).relative_to(root).as_posix()
                    )
                    stream = handle.extractfile(relative)
                    self.assertIsNotNone(stream)
                    self.assertEqual(
                        "sha256:" + hashlib.sha256(stream.read()).hexdigest(),
                        record["observation_sha256"],
                    )
        capture = Path(update["public_observation"])
        original = capture.read_bytes()
        capture.unlink()
        members, required, gaps = self.guest_main.evidence_members(root, "task-setup")
        self.assertIn(capture.relative_to(root).as_posix(), required)
        self.assertTrue(gaps)
        self.assertIn("operations/task-setup/000.jsonl", members)
        capture.write_bytes(b"changed capture")
        self.assertTrue(self.guest_main.evidence_members(root, "task-setup")[2])
        capture.write_bytes(original)
        (window / "000.stderr").unlink()
        members, required, gaps = self.guest_main.evidence_members(root, "task-setup")
        self.assertNotIn("operations/task-setup/000.stderr", members)
        self.assertIn("operations/task-setup/000.stderr", required)
        outside = root.parent / "outside-observation.json"
        outside.write_text("never read this outside the run root")
        self.addCleanup(outside.unlink)
        after.write_text(
            json.dumps({"setup": {**update, "public_observation": str(outside)}})
        )
        digest = self.guest_main.lib.sha256_file

        def bounded_digest(path):
            self.assertNotEqual(Path(path), outside)
            return digest(path)

        with mock.patch.object(
            self.guest_main.lib, "sha256_file", side_effect=bounded_digest
        ):
            self.assertTrue(self.guest_main.evidence_members(root, "task-setup")[2])

    def test_scope_roots_cover_the_active_codex_home_skills(self):
        scopes = self.guest_main.Context.scope_roots(self.context_stub())
        names = [scope[0] for scope in scopes]
        self.assertIn("codex-home-skills", names)
        self.assertIn("shared-agents-skills", names)
        codex_home = next(scope for scope in scopes if scope[0] == "codex-home-skills")
        self.assertEqual(codex_home[1], self.home / ".codex/skills")

    def test_baseline_combination_uses_the_driver_reported_shapes(self):
        stable = {
            "components": [
                {"name": "aquarium-plugin", "version": "0.1.21"},
                {"name": "codex", "version": "0.164.0"},
                {"name": "podway", "version": "0.2.14"},
            ]
        }
        self.assertEqual(
            self.guest_main.baseline_combination_from_profile(stable),
            {"aquarium": "0.1.21", "codex": "0.164.0", "podway": "v0.2.14"},
        )
        broken = {"components": [{"name": "podway", "version": "0.2.14"}]}
        with self.assertRaises(self.guest_main.lib.RecipeError):
            self.guest_main.baseline_combination_from_profile(broken)

    def test_acceptance_request_retains_sealed_original_generation(self):
        from types import SimpleNamespace

        driver = load_module(
            "request_generation_driver", REPOSITORY / "tests/vm/run_acceptance.py"
        )
        for name, version, digest, generation in (
            ("legacy", "v0.2.14", "b" * 64, 1),
            ("current", "v0.2.16", "a" * 64, 2),
        ):
            stable = {
                "components": [
                    {"name": "aquarium-plugin", "version": "0.1.22"},
                    {"name": "codex", "version": "0.164.0"},
                    {
                        "name": "podway",
                        "version": version,
                        "executable_sha256": "sha256:" + digest,
                    },
                ]
            }
            context = SimpleNamespace(
                root=self.work / name,
                home=self.home,
                marketplace="fixture",
                python=sys.executable,
                codex="synthetic-codex",
                inputs={
                    "prior": {"version": "0.1.22"},
                    "podway_upgrade": {
                        "version": "v0.2.16",
                        "binary_sha256": "a" * 64,
                        "contract_generation": 2,
                    },
                },
                profile=lambda _, stable=stable: stable,
                marketplace_path=lambda _: self.work / "prior-marketplace",
            )
            with (
                mock.patch.object(
                    self.guest_main.lib, "context_value", return_value="synthetic"
                ),
                mock.patch.dict(sys.modules, {"run_acceptance": driver}),
            ):
                path = self.guest_main.acceptance_request(context)
            original = path.read_bytes()
            request = json.loads(original)
            self.assertEqual(request["podway_contract_generation"], generation)
            self.assertEqual(request["baseline_combination"]["podway"], version)
            self.assertEqual(
                request["released_plugin_root"],
                str(self.home / ".codex/plugins/cache/fixture/aquarium/0.1.22"),
            )
            context.profile = lambda _: self.fail(
                "must retain existing request on reconnect"
            )
            context.inputs["podway_upgrade"]["contract_generation"] = 1
            self.assertEqual(self.guest_main.acceptance_request(context), path)
            self.assertEqual(path.read_bytes(), original)

    def test_current_baseline_without_matching_sealed_generation_refuses(self):
        from types import SimpleNamespace

        driver = load_module(
            "current_baseline_generation_driver",
            REPOSITORY / "tests/vm/run_acceptance.py",
        )

        stable = {
            "components": [
                {"name": "aquarium-plugin", "version": "0.1.22"},
                {"name": "codex", "version": "0.164.0"},
                {
                    "name": "podway",
                    "version": "v0.2.16",
                    "executable_sha256": "sha256:" + "a" * 64,
                },
            ]
        }
        for name, binary, generation in (
            ("wrong-bytes", "b" * 64, 2),
            ("invalid-generation", "a" * 64, True),
        ):
            context = SimpleNamespace(
                root=self.work / name,
                profile=lambda _: stable,
                inputs={
                    "podway_upgrade": {
                        "version": "v0.2.16",
                        "binary_sha256": binary,
                        "contract_generation": generation,
                    }
                },
            )
            with (
                mock.patch.dict(sys.modules, {"run_acceptance": driver}),
                self.assertRaises((self.guest_main.lib.RecipeError, driver.GateError)),
            ):
                self.guest_main.acceptance_request(context)
            self.assertFalse(context.root.exists())

    def test_skill_tree_digest_uses_the_profile_algorithm(self):
        # The digest comes from the candidate checkout's validator, so a
        # changed file, an added file or a flipped bit changes the value —
        # aquarium-skill-tree-sha256/v1, not haepari-tree-sha256/v1.
        tree = self.work / "skills" / "task-handler"
        tree.mkdir(parents=True)
        (tree / "SKILL.md").write_text("# task-handler\n")
        base = self.guest_main.lib.skill_tree_digest(REPOSITORY, tree)
        (tree / "SKILL.md").write_text("# task-handler changed\n")
        self.assertNotEqual(
            self.guest_main.lib.skill_tree_digest(REPOSITORY, tree), base
        )
        (tree / "SKILL.md").write_text("# task-handler\n")
        self.assertEqual(self.guest_main.lib.skill_tree_digest(REPOSITORY, tree), base)
        (tree / "SKILL.md").chmod(0o755)
        try:
            self.assertNotEqual(
                self.guest_main.lib.skill_tree_digest(REPOSITORY, tree), base
            )
        finally:
            (tree / "SKILL.md").chmod(0o644)

    def test_archive_is_deterministic_and_manifest_binds_members(self):
        source = self.work / "originals"
        source.mkdir()
        (source / "a.json").write_text('{"a": 1}\n')
        (source / "b.jsonl").write_text('{"b": 2}\n')
        archive = self.work / "evidence" / "case.tar"
        first = self.guest_main.lib.stage_evidence_archive(
            archive, source, ["a.json", "b.jsonl"], ["a.json"]
        )
        self.assertEqual(first["required"], ["a.json"])
        self.assertEqual(
            [record["path"] for record in first["members"]], ["a.json", "b.jsonl"]
        )
        self.assertEqual(
            first["sha256"],
            hashlib.sha256(archive.read_bytes()).hexdigest(),
        )
        second = self.guest_main.lib.stage_evidence_archive(
            archive, source, ["a.json", "b.jsonl"], ["a.json"]
        )
        self.assertEqual(first, second)

    def test_missing_required_record_archives_with_named_gap(self):
        # Partial staging: the existing original still travels in the
        # archive, the manifest names the missing required record, and the
        # caller keeps `ok` false while the gap remains.
        source = self.work / "originals-missing"
        source.mkdir()
        (source / "a.json").write_text("{}\n")
        archive = self.work / "evidence" / "missing.tar"
        document = self.guest_main.lib.stage_evidence_archive(
            archive, source, ["a.json"], ["b.json"]
        )
        self.assertTrue(archive.is_file())
        self.assertEqual(document["missing_required"], ["b.json"])
        self.assertEqual([record["path"] for record in document["members"]], ["a.json"])

    def test_evidence_members_pin_the_required_originals(self):
        run_root = self.work / "run-root"
        run_root.mkdir()
        for fixture in ("task", "epic", "preservation"):
            (run_root / f"released-{fixture}.last").write_text("last\n")
        (run_root / "operations/runtime-update").mkdir(parents=True)
        (run_root / "operations/runtime-update/000.invocation.json").write_text("{}")
        (run_root / "operations/runtime-update/000.input").write_text("prompt\n")
        (run_root / "operations/runtime-update/000.last").write_text("proposal\n")
        _members, required, _excluded = self.guest_main.evidence_members(
            run_root, "baseline"
        )
        self.assertEqual(
            required,
            [
                "released-task.last",
                "released-epic.last",
                "released-preservation.last",
                "released-task.jsonl",
                "released-epic.jsonl",
                "released-preservation.jsonl",
            ],
        )
        _members, required, _excluded = self.guest_main.evidence_members(
            run_root, "runtime-update"
        )
        self.assertIn("operations/runtime-update/000.invocation.json", required)
        self.assertIn("operations/runtime-update/000.input", required)
        self.assertIn("operations/runtime-update/000.last", required)
        # A setup case without a complete operation window names its
        # missing window class as a gap; the required class is defined by
        # the producer, not by discovery.
        (run_root / "operations/task-setup").mkdir(parents=True)
        _members, required, gaps = self.guest_main.evidence_members(
            run_root, "task-setup"
        )
        self.assertIn("operations/task-setup/ operation window", required)
        self.assertEqual(gaps, [])

    def _residue_home(self, selected: str, dev_names: tuple[str, ...]) -> Path:
        home = self.work / f"residue-{selected[:8]}-{len(dev_names)}"
        versions = home / ".aquarium/status-runtime/versions"
        versions.mkdir(parents=True, exist_ok=True)
        (home / ".aquarium/status-runtime/current").write_text(
            f"versions/{selected}\n", encoding="utf-8"
        )
        stable = versions / "stable-gen"
        stable.mkdir(exist_ok=True)
        (stable / "runtime.json").write_text(json.dumps({"plugin_version": "v0.1.21"}))
        for name in dev_names:
            dev = versions / name
            dev.mkdir(exist_ok=True)
            (dev / "runtime.json").write_text(
                json.dumps({"plugin_version": "v0.1.21-dev.db132845624c"})
            )
        (home / ".codex/skills").mkdir(parents=True, exist_ok=True)
        return home

    def _residue_stub(self, home: Path):
        stub_home = home
        fake_codex = self._fake_codex

        class Stub:
            root = self.work / "residue-job"
            home = stub_home
            codex = fake_codex
            marketplace = "root-kernel"
            dev_version = "v0.1.21-dev.db132845624c"

            def marketplace_path(self, kind):
                return self.home / ".aquarium-vm-marketplaces" / kind

        return Stub()

    def test_selected_dev_generation_is_preimaged_and_normalized(self):
        # The approved-update generation left SELECTED by the abort
        # checkpoint is recorded in the preimage and, after prior selection
        # is restored, removed with the disposition verified.
        home = self._residue_home(f"{'c' * 64}-py3.14", (f"{'c' * 64}-py3.14",))
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-residue"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        harness = self.work / "residue-job" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            record = self.guest_main.abort_preimage(self._residue_stub(home))
            self.assertEqual(len(record["runtime_generations"]), 1)
            self.assertTrue(record["runtime_generations"][0]["selected_at_preimage"])
            preimage_path = (
                harness.parent / "results/release-acceptance/abort-normalization.json"
            )
            persisted = json.loads(preimage_path.read_text())
            self.assertEqual(
                persisted["runtime_generations"][0]["generation"],
                f"{'c' * 64}-py3.14",
            )
            # ensure_prior_stable has restored the prior selection.
            (home / ".aquarium/status-runtime/current").write_text(
                "versions/stable-gen\n", encoding="utf-8"
            )
            finished = self.guest_main.finish_abort_normalization(
                self._residue_stub(home), record
            )
            self.assertEqual(
                finished["runtime_generations_removed"], [f"{'c' * 64}-py3.14"]
            )
            self.assertTrue(finished["residue_disposition_verified"])
            self.assertFalse(
                (
                    home / ".aquarium/status-runtime/versions" / f"{'c' * 64}-py3.14"
                ).exists()
            )
        finally:
            os.chdir(previous_cwd)
            os.environ.pop("AQUARIUM_VM_JOB_ID", None)
            os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)

    def test_unreadable_selection_refuses_without_mutation(self):
        home = self._residue_home("stable-gen", (f"{'c' * 64}-py3.14",))
        current = home / ".aquarium/status-runtime/current"
        current.write_bytes(b"versions/\xffgeneration\n")
        with self.assertRaises(self.guest_main.lib.RecipeError) as raised:
            self.guest_main.abort_preimage(self._residue_stub(home))
        self.assertIn("unreadable", str(raised.exception))
        # No mutation: the dev-stamped generation survives.
        self.assertTrue(
            (home / ".aquarium/status-runtime/versions" / f"{'c' * 64}-py3.14").is_dir()
        )

    def test_preimage_persists_before_each_deletion(self):
        home = self._residue_home(
            "stable-gen", (f"{'c' * 64}-py3.14", f"{'d' * 64}-py3.14")
        )
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-residue-loop"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        harness = self.work / "residue-job-loop" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            record = self.guest_main.abort_preimage(self._residue_stub(home))
            calls = {"count": 0}

            def flaky_rmtree(path, *args, **kwargs):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("injected mid-loop failure")
                return shutil.rmtree(path, *args, **kwargs)

            with (
                mock.patch.object(
                    self.guest_main.shutil, "rmtree", side_effect=flaky_rmtree
                ),
                self.assertRaises(OSError),
            ):
                self.guest_main.finish_abort_normalization(
                    self._residue_stub(home), record
                )
            persisted = json.loads(
                (
                    harness.parent
                    / "results/release-acceptance/abort-normalization.json"
                ).read_text()
            )
            # The preimage naming both generations was durable before the
            # first deletion ran.
            self.assertEqual(len(persisted["runtime_generations"]), 2)
        finally:
            os.chdir(previous_cwd)
            os.environ.pop("AQUARIUM_VM_JOB_ID", None)
            os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)

    def _identity_context(self, home: Path, checkout: Path):
        """A stub context for skill-identity document tests."""
        stub_home = home
        stub_checkout = checkout
        stub_root = self.work / "identity-job"
        stub_fake = self._fake_codex

        class Stub:
            root = stub_root
            home = stub_home
            checkout = stub_checkout
            codex = stub_fake
            python = "/synthetic/python"
            marketplace = "root-kernel"
            dev_version = "v0.1.21-dev.db132845624c"

            def __init__(self):
                (self.root / "profile").mkdir(parents=True, exist_ok=True)
                self.inputs = {
                    "candidate": {"development_version": "v0.1.21-dev.db132845624c"}
                }

            def profile(self, name):
                return json.loads((self.root / "profile" / f"{name}.json").read_text())

            def profile_digest(self, name):
                return "0" * 64

            def established_plugin_version(self):
                cache = self.home / ".codex/plugins/cache/root-kernel/aquarium"
                if not cache.is_dir():
                    return None
                for entry in sorted(cache.iterdir(), reverse=True):
                    if entry.is_dir():
                        return entry.name
                return None

        return Stub()

    def _identity_fixture(self, with_plugin: bool, use_podway: str | None):
        """home with an installed plugin skills tree and a use-podway tree;
        use_podway is None (absent), 'match' or 'mismatch'."""
        base = Path(tempfile.mkdtemp(prefix="vm-identity-", dir=str(self.work)))
        self.addCleanup(shutil.rmtree, base, True)
        home = base / "home"
        checkout = base / "checkout"
        (checkout / "tests/vm/profiles").mkdir(parents=True)
        shutil.copyfile(
            REPOSITORY / "tests/vm/profiles/validate_profiles.py",
            checkout / "tests/vm/profiles/validate_profiles.py",
        )
        if with_plugin:
            skills = home / ".codex/plugins/cache/root-kernel/aquarium/0.1.21/skills"
            skills.mkdir(parents=True)
            (skills / "task-handler").mkdir()
            (skills / "task-handler/SKILL.md").write_text("# task-handler\n")
        if use_podway is not None:
            tree = home / ".agents/skills/use-podway"
            tree.mkdir(parents=True)
            if use_podway == "match":
                (tree / "SKILL.md").write_text("# synthetic use-podway\n")
            else:
                (tree / "SKILL.md").write_text("# drifted\n")
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        self.addCleanup(os.environ.pop, "FAKE_CODEX_STATE", None)
        context = self._identity_context(home, checkout)
        context.codex = str(self._fake_codex)
        return context, home

    def _stable_profile_for(self, context) -> None:
        stable = json.loads(
            (
                REPOSITORY
                / "tests/vm/profiles"
                / "proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0"
                "-podway-0.2.14.json"
            ).read_text()
        )
        # Point the plugin pin at the fixture's own tree so the plugin
        # comparison is meaningful in isolation.
        plugin_skills = (
            context.home / ".codex/plugins/cache/root-kernel/aquarium/0.1.21/skills"
        )
        if plugin_skills.is_dir():
            stable_plugin_pin = self.guest_main.lib.skill_tree_digest(
                context.checkout, plugin_skills
            )
            for component in stable["components"]:
                if component["name"] == "aquarium-plugin":
                    component["skill_tree"]["sha256"] = stable_plugin_pin
        reference = self.work / "synthetic-podway-reference"
        reference.mkdir(exist_ok=True)
        (reference / "SKILL.md").write_text("# synthetic use-podway\n")
        for component in stable["components"]:
            if component["name"] == "use-podway":
                component["skill_tree"]["sha256"] = (
                    self.guest_main.lib.skill_tree_digest(context.checkout, reference)
                )
        (context.root / "profile/stable.json").write_text(
            json.dumps(stable, indent=2) + "\n"
        )
        candidate = json.loads(json.dumps(stable))
        candidate["profile_id"] = "sim-candidate"
        (context.root / "profile/candidate.json").write_text(
            json.dumps(candidate, indent=2) + "\n"
        )

    def test_missing_plugin_skills_at_prior_stage_fails(self):
        context, _home = self._identity_fixture(with_plugin=False, use_podway="match")
        self._stable_profile_for(context)
        document = self.guest_main.skill_identity_document(context, "prior")
        self.assertIs(document["comparisons"]["all_passed"], False)
        self.assertTrue(
            any(
                "tree not found" in problem
                for problem in document["comparisons"]["problems"]
            )
        )

    def test_missing_plugin_skills_at_candidate_stage_fails(self):
        context, _home = self._identity_fixture(with_plugin=False, use_podway="match")
        self._stable_profile_for(context)
        document = self.guest_main.skill_identity_document(context, "candidate")
        self.assertIs(document["comparisons"]["all_passed"], False)

    def test_missing_use_podway_fails(self):
        context, _home = self._identity_fixture(with_plugin=True, use_podway=None)
        self._stable_profile_for(context)
        document = self.guest_main.skill_identity_document(context, "candidate")
        self.assertIs(document["comparisons"]["all_passed"], False)
        self.assertTrue(
            any(
                "use-podway" in problem
                for problem in document["comparisons"]["problems"]
            )
        )

    def test_mismatched_use_podway_fails(self):
        context, _home = self._identity_fixture(with_plugin=True, use_podway="mismatch")
        self._stable_profile_for(context)
        document = self.guest_main.skill_identity_document(context, "candidate")
        self.assertIs(document["comparisons"]["all_passed"], False)
        self.assertTrue(
            any(
                "differs from the pin" in problem
                for problem in document["comparisons"]["problems"]
            )
        )

    def test_matching_trees_pass_and_host_pin_stays_out(self):
        context, _home = self._identity_fixture(with_plugin=True, use_podway="match")
        # The host use-haepari tree is absent from the guest home; the
        # predicate must still pass because host pins are excluded.
        self._stable_profile_for(context)
        document = self.guest_main.skill_identity_document(context, "candidate")
        self.assertIs(document["comparisons"]["all_passed"], True)
        self.assertNotIn("use-haepari", document["comparisons"]["required"])
        podway = document["skill_trees"]["use-podway"]
        self.assertTrue(podway["found"])
        self.assertIs(podway["match"], True)

    def test_plugin_skill_declared_name_matches_renamed_copy(self):
        context, _home = self._identity_fixture(with_plugin=True, use_podway="match")
        plugin_skills = (
            context.home / ".codex/plugins/cache/root-kernel/aquarium/0.1.21/skills"
        )
        shutil.rmtree(plugin_skills / "task-handler")
        renamed_plugin_dir = plugin_skills / "plugin-dir-renamed"
        renamed_plugin_dir.mkdir(parents=True)
        (renamed_plugin_dir / "SKILL.md").write_text(
            "---\nname: task-handler\n---\n# plugin skill with distinct dir name\n"
        )
        self._stable_profile_for(context)
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        clean_document = self.guest_main.skill_identity_document(context, "candidate")
        self.assertIs(clean_document["comparisons"]["all_passed"], True)
        self.assertEqual(clean_document["duplicates"], [])
        # A planted per-home copy whose directory name also differs from
        # both the plugin directory name and the declared front-matter name.
        planted = context.home / ".codex/skills/renamed-handler"
        planted.mkdir(parents=True)
        (planted / "SKILL.md").write_text(
            "---\nname: task-handler\n---\n# renamed copy\n"
        )
        self.addCleanup(shutil.rmtree, planted)
        document = self.guest_main.skill_identity_document(context, "candidate")
        self.assertIs(document["comparisons"]["all_passed"], False)
        self.assertTrue(
            any(
                "task-handler" in duplicate and "shadows" in duplicate
                for duplicate in document["duplicates"]
            ),
            document["duplicates"],
        )

    def test_effective_configuration_records_the_measured_shape(self):
        context, home = self._identity_fixture(with_plugin=True, use_podway="match")
        config = home / ".codex/config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            "\n"
            'notify = ["terminal-command"]\n'
            "\n"
            "[desktop]\n"
            'frame = "none"\n'
            "\n"
            "[hooks.session-start]\n"
            'trusted_hash = "<redacted-example>"\n'
            "\n"
            '[marketplaces."root-kernel"]\n'
            'source_type = "local"\n'
            'source = "/Users/synthetic/marketplace"\n'
            "\n"
            '[plugins."aquarium@root-kernel"]\n'
            "enabled = true\n"
            "\n"
            '[plugins."formatter@openai-bundled"]\n'
            "enabled = false\n"
            "\n"
            "[features]\n"
            "shell = true\n"
            "\n"
            "[mcp_servers.example]\n"
            'command = "/usr/bin/example"\n'
            "\n"
            '[projects."/Users/synthetic/project"]\n'
            'trust_level = "trusted"\n'
            "\n"
            'api_key = "should-not-be-recorded"\n',
            encoding="utf-8",
        )
        document = self.guest_main.effective_configuration_record(context)
        self.assertIn("config_sha256", document)
        self.assertEqual(document["settings"], {"notify": ["terminal-command"]})
        self.assertEqual(
            document["enabled_plugins"],
            {
                "aquarium@root-kernel": True,
                "formatter@openai-bundled": False,
            },
        )
        self.assertEqual(document["features"], {"shell": True})
        self.assertIn("api_key", " ".join(document["redacted_key_names"]))
        self.assertNotIn("should-not-be-recorded", json.dumps(document))
        # The config names no skills: recorded explicitly.
        self.assertEqual(
            document.get("skill_settings_note"),
            "no key or table names skills",
        )

    def test_explicit_absence_of_features_and_skill_settings(self):
        context, home = self._identity_fixture(with_plugin=True, use_podway="match")
        config = home / ".codex/config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text('notify = ["noop"]\n', encoding="utf-8")
        document = self.guest_main.effective_configuration_record(context)
        self.assertEqual(document["features_note"], "no [features] table in the config")
        self.assertEqual(
            document["skill_settings_note"], "no key or table names skills"
        )

    def test_merge_keeps_attempts_detached(self):
        results = self.work / "merge-results"
        results.mkdir(exist_ok=True)
        self.guest_main._merge_phase_record(
            results, "managed-update-task.json", {"exit": 2, "problem": "first"}
        )
        self.guest_main._merge_phase_record(
            results, "managed-update-task.json", {"exit": 0, "driver_outcome": "ok"}
        )
        document = json.loads((results / "managed-update-task.json").read_text())
        self.assertEqual(document["exit"], 0)
        self.assertEqual(len(document["attempts"]), 1)
        self.assertEqual(document["attempts"][0]["exit"], 2)
        self.assertNotIn("attempts", document["attempts"][0])

    def test_absent_generation_recorded_separately(self):
        home = self._residue_home("stable-gen", (f"{'c' * 64}-py3.14",))
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-absent-generation"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        harness = self.work / "absent-generation-job" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            record = self.guest_main.abort_preimage(self._residue_stub(home))
            # The generation directory disappears before normalization.
            shutil.rmtree(
                home / ".aquarium/status-runtime/versions" / f"{'c' * 64}-py3.14"
            )
            finished = self.guest_main.finish_abort_normalization(
                self._residue_stub(home), record
            )
            self.assertEqual(finished["runtime_generations_removed"], [])
            self.assertEqual(
                finished["runtime_generations_already_absent"],
                [f"{'c' * 64}-py3.14"],
            )
            self.assertTrue(finished["residue_disposition_verified"])
        finally:
            os.chdir(previous_cwd)
            os.environ.pop("AQUARIUM_VM_JOB_ID", None)
            os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)

    def test_malformed_startup_evidence_records_its_gap(self):
        work = Path(
            tempfile.mkdtemp(prefix="vm-malformed-evidence-", dir=str(self.work))
        )
        self.addCleanup(shutil.rmtree, work, True)
        run_root = work / "run-root"
        case = run_root / "task-startup"
        case.mkdir(parents=True)
        window = run_root / "operations/task-startup"
        window.mkdir(parents=True)
        (window / "000.invocation.json").write_text("{}")
        (window / "000.input").write_text("prompt\n")
        (window / "000.last").write_text("done\n")
        for label, raw in (
            ("malformed", "{not json"),
            ("array", "[]"),
            ("null", "null"),
        ):
            with self.subTest(evidence=label):
                (case / "startup-evidence.json").write_text(raw)
                _members, _required, gaps = self.guest_main.evidence_members(
                    run_root, "task-startup"
                )
                self.assertTrue(any("cannot be validated" in gap for gap in gaps), gaps)

    def test_podway_digest_mismatch_refuses(self):
        context, _home = self._identity_fixture(with_plugin=True, use_podway="match")
        self._stable_profile_for(context)
        fake = self.work / "podway-executable"
        fake.write_text("#!/bin/sh\n")
        fake.chmod(0o755)
        os.environ["AQUARIUM_GUEST_PODWAY"] = str(fake)
        self.addCleanup(os.environ.pop, "AQUARIUM_GUEST_PODWAY", None)
        # A marker proves the mismatched binary is never executed.
        marker = self.work / "podway-executed-marker"
        marker.unlink(missing_ok=True)
        fake.write_text(f"#!/bin/sh\ntouch {json.dumps(str(marker))}\n")
        fake.chmod(0o755)
        with self.assertRaises(self.guest_main.lib.RecipeError) as raised:
            self.guest_main.podway_identity_record(context)
        self.assertIn(
            "the unverified executable is never executed", str(raised.exception)
        )
        self.assertFalse(marker.exists())
        # A same-path executable whose digest matches the pin passes.
        import hashlib as _hashlib

        matching_digest = "sha256:" + _hashlib.sha256(fake.read_bytes()).hexdigest()
        profile_path = context.root / "profile/stable.json"
        profile = json.loads(profile_path.read_text())
        for component in profile["components"]:
            if component.get("name") == "podway":
                component["executable_sha256"] = matching_digest
        profile_path.write_text(json.dumps(profile, indent=2) + "\n")
        record = self.guest_main.podway_identity_record(context)
        self.assertIs(record["match"], True)

    def test_project_local_duplicate_fails_the_predicate(self):
        context, _home = self._identity_fixture(with_plugin=True, use_podway="match")
        self._stable_profile_for(context)
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        # Plant a fixture-local duplicate directly through the documented
        # fixture path root.
        fixture_skills = (
            context.root / "acceptance-run/task/.agents/skills/task-handler"
        )
        fixture_skills.mkdir(parents=True)
        (fixture_skills / "SKILL.md").write_text(
            "---\nname: task-handler\n---\n# local copy\n"
        )
        self.addCleanup(shutil.rmtree, fixture_skills)
        document = self.guest_main.skill_identity_document(context, "candidate")
        self.assertIs(document["comparisons"]["all_passed"], False)
        self.assertTrue(
            any("task-handler" in duplicate for duplicate in document["duplicates"]),
            document["duplicates"],
        )

    def test_foreign_dev_selection_after_restoration_refuses(self):
        home = self._residue_home("stable-gen", ())
        versions = home / ".aquarium/status-runtime/versions"
        foreign = versions / f"{'e' * 64}-py3.14"
        foreign.mkdir()
        (foreign / "runtime.json").write_text(
            json.dumps({"plugin_version": "v0.1.20-dev.aaaaaaaaaaaa"})
        )
        # The foreign dev generation is SELECTED after restoration.
        (home / ".aquarium/status-runtime/current").write_text(
            f"versions/{'e' * 64}-py3.14\n", encoding="utf-8"
        )
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-dev-selection"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        harness = self.work / "dev-selection-job" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            record = self.guest_main.abort_preimage(self._residue_stub(home))
            with self.assertRaises(self.guest_main.lib.RecipeError) as raised:
                self.guest_main.finish_abort_normalization(
                    self._residue_stub(home), record
                )
            self.assertIn("selection is dev-stamped", str(raised.exception))
            persisted = json.loads(
                (
                    harness.parent
                    / "results/release-acceptance/abort-normalization.json"
                ).read_text()
            )
            self.assertIs(persisted["residue_disposition_verified"], False)
            self.assertEqual(
                persisted["runtime_selection_plugin_version"],
                "v0.1.20-dev.aaaaaaaaaaaa",
            )
            # The foreign generation survives untouched.
            self.assertTrue(foreign.is_dir())
        finally:
            os.chdir(previous_cwd)
            os.environ.pop("AQUARIUM_VM_JOB_ID", None)
            os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)

    def test_absent_selection_refuses(self):
        home = self._residue_home("stable-gen", ())
        (home / ".aquarium/status-runtime/current").unlink()
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-absent-selection"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        with self.assertRaises(self.guest_main.lib.RecipeError) as raised:
            self.guest_main.abort_preimage(self._residue_stub(home))
        self.assertIn("no current selection", str(raised.exception))

    def test_foreign_dev_generation_preserved_and_listed(self):
        home = self._residue_home("stable-gen", (f"{'c' * 64}-py3.14",))
        versions = home / ".aquarium/status-runtime/versions"
        foreign = versions / f"{'e' * 64}-py3.14"
        foreign.mkdir()
        (foreign / "runtime.json").write_text(
            json.dumps({"plugin_version": "v0.1.19-dev.aaaaaaaaaaaa"})
        )
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-generation-ownership"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        harness = self.work / "generation-ownership-job" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            record = self.guest_main.abort_preimage(self._residue_stub(home))
            foreign_listed = record["foreign_dev_generations_preserved"]
            self.assertEqual(
                [entry["generation"] for entry in foreign_listed],
                [f"{'e' * 64}-py3.14"],
            )
            self.assertTrue(foreign.is_dir())
            finished = self.guest_main.finish_abort_normalization(
                self._residue_stub(home), record
            )
            self.assertTrue(foreign.is_dir())
            self.assertEqual(
                finished["runtime_generations_removed"], [f"{'c' * 64}-py3.14"]
            )
            self.assertTrue(finished["residue_disposition_verified"])
        finally:
            os.chdir(previous_cwd)
            os.environ.pop("AQUARIUM_VM_JOB_ID", None)
            os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)

    def test_remaining_own_generation_refuses(self):
        home = self._residue_home(
            "stable-gen",
            (f"{'c' * 64}-py3.14", f"{'d' * 64}-py3.14"),
        )
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-owned-generation"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        harness = self.work / "owned-generation-job" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            record = self.guest_main.abort_preimage(self._residue_stub(home))

            real_rmtree = shutil.rmtree

            def selective_rmtree(path, *args, **kwargs):
                # The first own generation silently fails to delete, so it
                # remains after normalization.
                if str(path).endswith(f"{'c' * 64}-py3.14"):
                    return None
                return real_rmtree(path, *args, **kwargs)

            with (
                mock.patch.object(
                    self.guest_main.shutil, "rmtree", side_effect=selective_rmtree
                ),
                self.assertRaises(self.guest_main.lib.RecipeError) as raised,
            ):
                self.guest_main.finish_abort_normalization(
                    self._residue_stub(home), record
                )
            self.assertIn("refuses to continue", str(raised.exception))
            persisted = json.loads(
                (
                    harness.parent
                    / "results/release-acceptance/abort-normalization.json"
                ).read_text()
            )
            self.assertIs(persisted["residue_disposition_verified"], False)
            self.assertEqual(
                persisted["dev_stamped_generations_remaining"],
                [f"{'c' * 64}-py3.14"],
            )
        finally:
            os.chdir(previous_cwd)
            os.environ.pop("AQUARIUM_VM_JOB_ID", None)
            os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)

    def test_preimage_file_present_after_midloop_failure(self):
        home = self._residue_home(
            "stable-gen", (f"{'c' * 64}-py3.14", f"{'d' * 64}-py3.14")
        )
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-abort-preimage"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        harness = self.work / "abort-preimage-job" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            record = self.guest_main.abort_preimage(self._residue_stub(home))
            declared = (
                harness.parent / "results/release-acceptance/abort-normalization.json"
            )
            self.assertTrue(declared.is_file())
            with (
                mock.patch.object(
                    self.guest_main.shutil,
                    "rmtree",
                    side_effect=OSError("injected mid-loop failure"),
                ),
                self.assertRaises(OSError),
            ):
                self.guest_main.finish_abort_normalization(
                    self._residue_stub(home), record
                )
            # The declared file survives the mid-loop failure.
            self.assertTrue(declared.is_file())
            persisted = json.loads(declared.read_text())
            self.assertEqual(len(persisted["runtime_generations"]), 2)
        finally:
            os.chdir(previous_cwd)
            os.environ.pop("AQUARIUM_VM_JOB_ID", None)
            os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)

    def test_foreign_residue_refuses_without_mutation(self):
        home = self._residue_home("stable-gen", ())
        planted = home / ".codex/skills/task-handler"
        planted.mkdir(parents=True)
        (planted / "SKILL.md").write_text("# stale planted skill\n")
        try:
            with self.assertRaises(self.guest_main.lib.RecipeError) as raised:
                self.guest_main.abort_preimage(self._residue_stub(home))
            self.assertIn("refuses to start", str(raised.exception))
            self.assertTrue(planted.is_dir())
        finally:
            shutil.rmtree(planted)

    def test_effective_configuration_normalizes_reordered_tables_and_ignores_non_plugin_sections(
        self,
    ):
        context, home = self._identity_fixture(with_plugin=True, use_podway="match")
        config = home / ".codex/config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            'notify = ["noop"]\n'
            '[plugins."aquarium@root-kernel"]\n'
            "enabled = true\n"
            '[plugins."formatter@openai-bundled"]\n'
            "enabled = false\n"
            "[features]\n"
            "shell = true\n",
            encoding="utf-8",
        )
        first = self.guest_main.effective_configuration_record(context)
        config.write_text(
            "# comment line\n"
            'notify = [ "noop" ] # formatting and inline comment\n\n'
            '[plugins."formatter@openai-bundled"]\n'
            "enabled = false\n\n"
            '[plugins."aquarium@root-kernel"]\n'
            "enabled = true\n\n"
            "[features]\n"
            "shell = true\n\n"
            '[projects."/Users/synthetic/plugins/repo"]\n'
            'trust_level = "trusted"\n\n'
            "[mcp_servers.plugin_helper]\n"
            "enabled = true\n",
            encoding="utf-8",
        )
        second = self.guest_main.effective_configuration_record(context)
        for field in ("enabled_plugins", "features", "skill_settings", "settings"):
            self.assertEqual(first[field], second[field], field)
        # Explicit skill table is recorded when present.
        config.write_text(
            '[skills]\ndefault_scope = "home"\n',
            encoding="utf-8",
        )
        with_skills = self.guest_main.effective_configuration_record(context)
        self.assertEqual(
            with_skills["skill_settings"], {"skills": {"default_scope": "home"}}
        )
        # Invalid TOML records parse_error and does not crash.
        config.write_text("[broken\nenabled = true\n", encoding="utf-8")
        broken = self.guest_main.effective_configuration_record(context)
        self.assertIn("parse_error", broken)
        self.assertTrue(broken["parse_error"])

    def test_evidence_members_includes_stale_result_only_when_present(self):
        work = Path(tempfile.mkdtemp(prefix="vm-stale-result-", dir=str(self.work)))
        self.addCleanup(shutil.rmtree, work, True)
        run_root = work / "run-root"
        run_root.mkdir(parents=True)
        (run_root / "result.json").write_text("{}\n")
        driver = load_module(
            "stale_result_capture_producer", REPOSITORY / "tests/vm/run_acceptance.py"
        )
        setup = {
            fixture: {
                "setup": driver.save_setup_observation(
                    run_root, fixture, "update", {"fixture": fixture}
                )
            }
            for fixture in ("task", "epic", "preservation")
        }
        (run_root / "upgrade-observation.json").write_text(json.dumps({"setup": setup}))
        members_absent, required_absent, gaps_absent = self.guest_main.evidence_members(
            run_root, "upgrade"
        )
        self.assertEqual(
            members_absent,
            ["baseline.json", "upgrade-observation.json", "result.json"],
        )
        self.assertEqual(
            required_absent,
            ["baseline.json", "upgrade-observation.json", "result.json"],
        )
        self.assertEqual(gaps_absent, [])
        (run_root / "result.stale.json").write_text('{"stale": true}\n')
        members_present, required_present, gaps_present = (
            self.guest_main.evidence_members(run_root, "upgrade")
        )
        self.assertEqual(
            members_present,
            [
                "baseline.json",
                "upgrade-observation.json",
                "result.json",
                "result.stale.json",
            ],
        )
        self.assertEqual(
            required_present,
            ["baseline.json", "upgrade-observation.json", "result.json"],
        )
        self.assertEqual(gaps_present, [])

    def test_null_and_non_string_plugin_version_guarded_in_abort_normalization(
        self,
    ):
        home = self._residue_home("stable-gen", (f"{'c' * 64}-py3.14",))
        versions = home / ".aquarium/status-runtime/versions"
        null_gen = versions / f"{'1' * 64}-py3.14"
        null_gen.mkdir()
        (null_gen / "runtime.json").write_text(json.dumps({"plugin_version": None}))
        int_gen = versions / f"{'2' * 64}-py3.14"
        int_gen.mkdir()
        (int_gen / "runtime.json").write_text(json.dumps({"plugin_version": 123}))
        # Also set the stable selected generation's plugin_version to null to
        # verify the post-restoration selection check does not raise TypeError.
        (versions / "stable-gen/runtime.json").write_text(
            json.dumps({"plugin_version": None})
        )
        os.environ["AQUARIUM_VM_JOB_ID"] = "sim-job-version-types"
        os.environ["AQUARIUM_VM_LEASE_GENERATION"] = "1"
        os.environ["FAKE_CODEX_STATE"] = str(self.codex_state)
        harness = self.work / "version-types-job" / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(harness)
        try:
            record = self.guest_main.abort_preimage(self._residue_stub(home))
            self.assertEqual(
                [row["generation"] for row in record["runtime_generations"]],
                [f"{'c' * 64}-py3.14"],
            )
            finished = self.guest_main.finish_abort_normalization(
                self._residue_stub(home), record
            )
            self.assertEqual(
                finished["runtime_generations_removed"], [f"{'c' * 64}-py3.14"]
            )
            self.assertIsNone(finished["runtime_selection_plugin_version"])
            self.assertTrue(finished["residue_disposition_verified"])
            # Neither non-string generation was deleted as own residue.
            self.assertTrue(null_gen.is_dir())
            self.assertTrue(int_gen.is_dir())
        finally:
            os.chdir(previous_cwd)
            os.environ.pop("AQUARIUM_VM_JOB_ID", None)
            os.environ.pop("AQUARIUM_VM_LEASE_GENERATION", None)


class SorageAdoptionRecipeTest(unittest.TestCase):
    @staticmethod
    def candidate_capture(module):
        return {
            "candidate_sha": "a" * 40,
            "capture": "candidate",
            "tools": {
                "version": "v0.1.3",
                "binary_sha256": module.RELEASE_SHA256,
                "skill_tree_sha256": module.RELEASE_SKILL_TREE_SHA256,
            },
            "inventory": [
                {
                    "installation_scope": "shared-agents-skills",
                    "relative_path": ".agents/skills/use-sorage/SKILL.md",
                    "executable": False,
                    "sha256": "b" * 64,
                }
            ],
        }

    def test_cleanup_refuses_malformed_or_stale_candidate_capture(self):
        import copy

        module = load_module(
            "sorage_adoption_test", RECIPES_ROOT / "sorage_adoption.py"
        )
        context = mock.MagicMock()
        context.inputs = {"candidate": {"git_sha": "a" * 40}}
        with (
            tempfile.TemporaryDirectory(dir="/tmp") as directory,
            mock.patch.object(module.lib, "verify_guest_identity"),
            mock.patch.object(module.lib, "verify_sealed_inputs"),
            mock.patch.object(module.lib, "guard"),
            mock.patch.object(
                module.lib, "results_directory", return_value=Path(directory)
            ),
            mock.patch.object(module, "observe") as observe,
            mock.patch.object(module.lib, "finish") as finish,
        ):
            root = Path(directory)
            (root / "prepare.json").write_text(json.dumps({"candidate_sha": "a" * 40}))
            cases = ["{bad", "{}"]
            for key, value in (
                ("candidate_sha", "c" * 40),
                ("capture", "prepare"),
                ("inventory", []),
                ("inventory", None),
                ("tools", {}),
            ):
                document = self.candidate_capture(module)
                document[key] = value
                cases.append(json.dumps(document))
            for key in ("version", "binary_sha256", "skill_tree_sha256"):
                document = copy.deepcopy(self.candidate_capture(module))
                document["tools"][key] = "wrong"
                cases.append(json.dumps(document))
            for body in cases:
                with self.subTest(body=body):
                    (root / "candidate.json").write_text(body)
                    with self.assertRaises(module.lib.RecipeError):
                        module.run(context, "consumer-cleanup")
                    self.assertEqual((root / "candidate.json").read_text(), body)
                    self.assertFalse((root / "consumer-cleanup.json").exists())
            observe.assert_not_called()
            context.snapshot.assert_not_called()
            finish.assert_not_called()

    def test_valid_candidate_capture_allows_verified_restoration(self):
        module = load_module(
            "sorage_adoption_test", RECIPES_ROOT / "sorage_adoption.py"
        )
        context = mock.MagicMock()
        context.inputs = {"candidate": {"git_sha": "a" * 40}}
        context.snapshot.return_value = []
        tools = {"binary_sha256": "original", "skill_tree_sha256": "original"}
        with (
            tempfile.TemporaryDirectory(dir="/tmp") as directory,
            mock.patch.object(module.lib, "verify_guest_identity"),
            mock.patch.object(module.lib, "verify_sealed_inputs"),
            mock.patch.object(module.lib, "guard"),
            mock.patch.object(
                module.lib, "results_directory", return_value=Path(directory)
            ),
            mock.patch.object(module, "observe", return_value=tools),
            mock.patch.object(module.lib, "postcondition_violations", return_value=[]),
            mock.patch.object(module.lib, "finish", return_value=0) as finish,
        ):
            root = Path(directory)
            (root / "prepare.json").write_text(
                json.dumps({"candidate_sha": "a" * 40, "tools": tools, "inventory": []})
            )
            (root / "candidate.json").write_text(
                json.dumps(self.candidate_capture(module))
            )
            self.assertEqual(module.run(context, "consumer-cleanup"), 0)
            self.assertEqual(
                json.loads((root / "consumer-cleanup.json").read_text())[
                    "consumer_cleanup"
                ],
                "verified",
            )
            self.assertEqual(finish.call_args.kwargs["consumer_cleanup"], "verified")

    def test_wrong_candidate_digest_is_not_executed(self):
        module = load_module(
            "sorage_adoption_test", RECIPES_ROOT / "sorage_adoption.py"
        )
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            binary = Path(directory) / "sorage"
            binary.write_text("unqualified candidate")
            with (
                mock.patch.object(module.shutil, "which", return_value=str(binary)),
                mock.patch.object(module.lib, "run") as run,
            ):
                with self.assertRaises(module.lib.RecipeError):
                    module.observe(mock.MagicMock(), candidate=True)
                run.assert_not_called()

    def test_ready_does_not_inspect_storage_or_execute_sorage(self):
        module = load_module(
            "sorage_adoption_test", RECIPES_ROOT / "sorage_adoption.py"
        )
        context = mock.MagicMock()
        context.inputs = {"candidate": {"git_sha": "a" * 40}}
        context.snapshot.return_value = []
        with (
            tempfile.TemporaryDirectory(dir="/tmp") as directory,
            mock.patch.object(module.lib, "verify_guest_identity"),
            mock.patch.object(module.lib, "verify_sealed_inputs"),
            mock.patch.object(module.lib, "guard"),
            mock.patch.object(
                module.lib, "results_directory", return_value=Path(directory)
            ),
            mock.patch.object(module, "observe") as observe,
        ):
            self.assertEqual(module.run(context, "ready"), 0)
            observe.assert_not_called()
            self.assertFalse((Path(directory) / "prepare.json").exists())
            self.assertEqual(
                json.loads((Path(directory) / "ready.json").read_text())[
                    "candidate_sha"
                ],
                "a" * 40,
            )

    def test_storage_inventory_detects_changed_body_without_copying_content(self):
        module = load_module(
            "sorage_adoption_test", RECIPES_ROOT / "sorage_adoption.py"
        )
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            home, vault = root / "home", root / "vault"
            home.mkdir()
            vault.mkdir()
            (home / "config.yaml").write_text("synthetic configuration")
            (vault / "body").write_text("PRIVATE BODY")
            with mock.patch.dict(
                os.environ,
                {"SORAGE_HOME": str(home), "AQUARIUM_VM_SORAGE_VAULT": str(vault)},
            ):
                before = module.storage_inventory()
                self.assertNotIn("PRIVATE BODY", json.dumps(before))
                (vault / "body").write_text("changed body")
                self.assertNotEqual(before, module.storage_inventory())
            with (
                mock.patch.dict(os.environ, {"SORAGE_HOME": "relative"}),
                self.assertRaises(module.lib.RecipeError),
            ):
                module.storage_inventory()

    def test_missing_baseline_cannot_capture_candidate_or_finish(self):
        module = load_module(
            "sorage_adoption_test", RECIPES_ROOT / "sorage_adoption.py"
        )
        context = mock.MagicMock()
        context.inputs = {"candidate": {"git_sha": "a" * 40}}
        context.snapshot.return_value = []
        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(module.lib, "verify_guest_identity"),
            mock.patch.object(module.lib, "verify_sealed_inputs"),
            mock.patch.object(module.lib, "guard"),
            mock.patch.object(
                module.lib, "results_directory", return_value=Path(directory)
            ),
        ):
            for phase in ("candidate", "consumer-cleanup"):
                with (
                    self.subTest(phase=phase),
                    self.assertRaises(module.lib.RecipeError),
                ):
                    module.run(context, phase)
            context.snapshot.assert_not_called()

    def test_changed_binary_cannot_pass_restoration(self):
        module = load_module(
            "sorage_adoption_test", RECIPES_ROOT / "sorage_adoption.py"
        )
        context = mock.MagicMock()
        context.inputs = {"candidate": {"git_sha": "a" * 40}}
        context.snapshot.return_value = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "prepare.json").write_text(
                json.dumps(
                    {
                        "candidate_sha": "a" * 40,
                        "inventory": {},
                        "tools": {"binary_sha256": "before"},
                    }
                )
            )
            (root / "candidate.json").write_text(
                json.dumps(self.candidate_capture(module))
            )
            with (
                mock.patch.object(module.lib, "verify_guest_identity"),
                mock.patch.object(module.lib, "verify_sealed_inputs"),
                mock.patch.object(module.lib, "guard"),
                mock.patch.object(module.lib, "results_directory", return_value=root),
                mock.patch.object(
                    module, "observe", return_value={"binary_sha256": "changed"}
                ),
                mock.patch.object(
                    module.lib, "postcondition_violations", return_value=[]
                ),
                mock.patch.object(module.lib, "finish") as finish,
            ):
                with self.assertRaises(module.lib.RecipeError):
                    module.run(context, "consumer-cleanup")
                finish.assert_not_called()
                self.assertFalse((root / "consumer-cleanup.json").exists())
                failures = list(root.glob("consumer-cleanup-*.json"))
                self.assertEqual(len(failures), 1)
                self.assertTrue(json.loads(failures[0].read_text())["violations"])


if __name__ == "__main__":
    unittest.main()
