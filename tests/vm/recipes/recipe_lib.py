"""Shared guest-side helpers for Aquarium's Haepari VM recipes.

Recipes own guest installation, fixtures, inventories and consumer cleanup.
Haepari owns transport, Job collection and its own cleanup. The guest
identity check runs before any write, and every destructive operation is
bounded by this run's ownership ledger.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tree_digest import (
    TreeDigestError,
    inventory_tree_sha256_from_directory,
    tree_sha256_from_directory,
)

RESULT_SCHEMA = "aquarium.vm-suite-result/v1"
INVENTORY_SCHEMA = "aquarium.vm-inventory/v1"
INPUTS_SCHEMA = "aquarium.vm-host-inputs/v1"
LEDGER_SCHEMA = "aquarium.vm-run-ledger/v1"
RUNTIME_ERROR_SCHEMA = "aquarium-status-runtime-error/v1"
OWNERSHIP_MARKER = "AQUARIUM-VM-OWNED"
OUTCOME_EXITS = {"pass": 0, "fail": 1, "incomplete": 2}
EVIDENCE_ARCHIVE_SCHEMA = "aquarium.vm-evidence-archive/v1"
SKILL_TREE_DIGEST_ALGORITHM = "aquarium-skill-tree-sha256/v1"


class RecipeError(RuntimeError):
    def __init__(self, message: str, outcome: str = "fail"):
        super().__init__(message)
        self.outcome = outcome if outcome in OUTCOME_EXITS else "incomplete"


class IdentityError(RecipeError):
    """A guest identity rejection: the caller must not write anything."""

    def __init__(self, message: str):
        super().__init__(message, outcome="incomplete")
        self.nowrite = True


def job_root() -> Path:
    root = Path.cwd()
    if root.name != "harness":
        raise RecipeError("recipes must run from the sealed harness directory")
    return root.parent


def load_inputs() -> dict[str, Any]:
    document = json.loads((Path.cwd() / "inputs.json").read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("schema") != INPUTS_SCHEMA:
        raise RecipeError("sealed harness inputs are missing or invalid")
    return document


def context_value(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RecipeError(f"guest context variable {name} is required")
    return value


def job_identity() -> dict[str, str]:
    """The managed runner's Job identity, exported by the guest entrypoint."""
    job_id = os.environ.get("AQUARIUM_VM_JOB_ID", "")
    lease = os.environ.get("AQUARIUM_VM_LEASE_GENERATION", "")
    if not job_id or not lease:
        raise RecipeError("the managed runner Job identity is required")
    return {"job_id": job_id, "lease_generation": lease}


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 1800,
    input_text: str | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(part) for part in argv],
        cwd=None if cwd is None else str(cwd),
        env=env,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def read_platform_identity() -> dict[str, Any]:
    """Read the non-mutating platform identity without touching any file."""
    flag = subprocess.run(
        ["/usr/sbin/sysctl", "-n", "kern.hv_vmm_present"],
        capture_output=True,
        text=True,
        check=False,
    )
    identity = subprocess.run(
        ["/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
        capture_output=True,
        text=True,
        check=False,
    )
    match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', identity.stdout or "")
    return {
        "platform": platform.system(),
        "hypervisor_present": flag.stdout.strip() if flag.returncode == 0 else None,
        "hardware_uuid": match[1] if match else None,
    }


def verify_guest_identity(
    expected_uuid: str | None = None, identity: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Reject a physical host or a foreign guest before any write."""
    expected = expected_uuid or context_value("AQUARIUM_EXPECTED_GUEST_UUID")
    observed = identity or read_platform_identity()
    if observed.get("platform") != "Darwin":
        raise IdentityError("a dedicated macOS guest is required")
    if observed.get("hypervisor_present") != "1":
        raise IdentityError("physical-host execution is rejected")
    if not expected or not re.fullmatch(
        r"[0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12}",
        expected,
    ):
        raise RecipeError("expected guest UUID is required")
    if (observed.get("hardware_uuid") or "").casefold() != expected.casefold():
        raise IdentityError(
            f"dedicated guest identity mismatch: expected {expected}, observed "
            f"{observed.get('hardware_uuid')}"
        )
    return observed


def ensure_checkout(root: Path) -> Path:
    """Clone the sealed candidate history; callers verify identity first."""
    checkout = root / "checkout"
    if not checkout.exists():
        bundle = root / "checkout.bundle"
        if bundle.is_symlink() or not bundle.is_file():
            raise RecipeError("sealed candidate history is unavailable")
        result = run(
            ["git", "clone", "--quiet", str(bundle), str(checkout)], timeout=600
        )
        if result.returncode != 0:
            raise RecipeError(f"candidate clone failed: {result.stderr[:400]}")
    driver_root = checkout / "tests/vm"
    if not (driver_root / "run_acceptance.py").is_file():
        raise RecipeError("cloned candidate lacks the guest driver")
    if driver_root.resolve() not in [Path(item).resolve() for item in sys.path]:
        sys.path.insert(0, str(driver_root))
    return checkout


def guard(root: Path, expected_uuid: str | None = None) -> dict[str, Any]:
    """Identity check first, then the committed driver's own guard contract."""
    identity = verify_guest_identity(expected_uuid)
    checkout = ensure_checkout(root)
    if (
        run(["git", "rev-parse", "HEAD"], cwd=checkout).stdout.strip()
        != load_inputs()["candidate"]["git_sha"]
    ):
        raise RecipeError("cloned candidate does not match the sealed identity")
    return identity


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sealed_inputs(root: Path) -> dict[str, Any]:
    """Compare consumed bundle bytes with the spec-bound subtree digests."""
    inputs = load_inputs()
    verified: dict[str, Any] = {}
    for name, directory, expected in (
        (
            "artifact_tree_sha256",
            root / "artifact",
            inputs["candidate"]["artifact_tree_sha256"],
        ),
        (
            "prior_artifact_tree_sha256",
            root / "prior-artifact",
            inputs["prior"]["artifact_tree_sha256"],
        ),
        (
            "harness_tree_sha256",
            root / "harness/tests/vm/recipes",
            inputs["harness_tree_sha256"],
        ),
    ):
        try:
            actual = tree_sha256_from_directory(directory)
        except TreeDigestError as error:
            raise RecipeError(
                f"sealed {name} is unsafe: {error}", "incomplete"
            ) from error
        if actual != expected:
            raise RecipeError(f"consumed bundle bytes differ from the admitted {name}")
        verified[name] = actual
    return verified


def write_inventory(
    path: Path,
    phase: str,
    entries: list[dict[str, Any]],
    profile_digest: str,
    recipe_digest: str,
) -> dict[str, Any]:
    document = {
        "schema": INVENTORY_SCHEMA,
        "phase": phase,
        "profile_digest": profile_digest,
        "recipe_digest": recipe_digest,
        "entries": entries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    return document


def _entry_map(
    entries: list[dict[str, Any]], label: str
) -> dict[tuple[str, str], dict[str, Any]]:
    mapping: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        key = (entry.get("installation_scope"), entry.get("relative_path"))
        if key in mapping:
            raise RecipeError(f"duplicate inventory identity in {label}: {key}")
        mapping[key] = entry
    return mapping


def postcondition_violations(
    target: list[dict[str, Any]],
    actual: list[dict[str, Any]],
    allowed: Callable[[str, str], bool],
) -> list[str]:
    wanted = _entry_map(target, "declared end state")
    observed = _entry_map(actual, "observed end state")
    violations: list[str] = []
    for key in sorted(set(wanted) - set(observed)):
        if not allowed(*key):
            violations.append(f"missing from declared end state: {key[0]}:{key[1]}")
    for key in sorted(set(observed) - set(wanted)):
        if not allowed(*key):
            violations.append(f"leftover outside declared end state: {key[0]}:{key[1]}")
    for key in sorted(set(wanted) & set(observed)):
        if wanted[key]["sha256"] != observed[key]["sha256"] and not allowed(*key):
            violations.append(f"changed outside declared end state: {key[0]}:{key[1]}")
        elif wanted[key].get("executable") != observed[key].get(
            "executable"
        ) and not allowed(*key):
            violations.append(
                f"executable bit changed outside declared end state: {key[0]}:{key[1]}"
            )
    return violations


class RunLedger:
    """This run's own guest effects; only ledger-owned effects are deleted."""

    def __init__(self, path: Path):
        self.path = path
        if path.is_file():
            self.document = json.loads(path.read_text(encoding="utf-8"))
        else:
            self.document = {
                "schema": LEDGER_SCHEMA,
                "generations": [],
                "staging": [],
                "marketplaces": [],
            }
        if self.document.get("schema") != LEDGER_SCHEMA:
            raise RecipeError("run ledger has an unsupported shape")

    def _record(self, kind: str, value: str) -> None:
        if value not in self.document[kind]:
            self.document[kind].append(value)

    def record_generation(self, name: str) -> None:
        self._record("generations", name)

    def record_staging(self, name: str) -> None:
        self._record("staging", name)

    def record_marketplace(self, kind: str) -> None:
        self._record("marketplaces", kind)

    def owns(self, kind: str, value: str) -> bool:
        return value in self.document.get(kind, [])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.document, indent=2, ensure_ascii=False) + "\n"
        )


def runtime_locations(home: Path) -> tuple[Path, Path]:
    return home / ".aquarium/status-runtime", home / ".local/bin/aquarium-status"


def installer_command(python: str, source: Path, *, approve: bool) -> list[str]:
    argv = [
        python,
        "-B",
        str(source / "install.py"),
        "install",
        "--source",
        str(source),
    ]
    if approve:
        argv += ["--approve-install", "--approve-launcher"]
    return argv


def run_installer(
    python: str, source: Path, *, approve: bool = True, timeout: int = 900
) -> tuple[int, dict[str, Any]]:
    result = run(installer_command(python, source, approve=approve), timeout=timeout)
    payload: dict[str, Any] = {"exit": result.returncode}
    for stream, name in ((result.stdout, "stdout"), (result.stderr, "stderr")):
        try:
            payload[name] = json.loads(stream)
        except ValueError:
            payload[name] = stream[-800:]
    return result.returncode, payload


def diagnose_runtime(python: str, source: Path) -> dict[str, Any]:
    result = run(
        [python, "-B", str(source / "install.py"), "diagnose", "--source", str(source)],
        timeout=300,
    )
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {
            "exit": result.returncode,
            "error": result.stderr[-800:],
            "status": "unavailable",
        }


def read_current_generation(home: Path) -> tuple[str, dict[str, Any]]:
    runtime_root, _launcher = runtime_locations(home)
    current = runtime_root / "current"
    if current.is_symlink() or not current.is_file():
        raise RecipeError("status runtime has no current selection", "incomplete")
    try:
        name = current.read_text(encoding="utf-8").strip().removeprefix("versions/")
    except (OSError, ValueError) as error:
        raise RecipeError(
            f"status runtime current selection is unreadable: {error}",
            "incomplete",
        ) from error
    receipt_path = runtime_root / "versions" / name / "runtime.json"
    if not receipt_path.is_file():
        raise RecipeError("selected runtime generation has no receipt", "incomplete")
    try:
        raw = receipt_path.read_text(encoding="utf-8")
        receipt = json.loads(raw)
    except (OSError, ValueError) as error:
        raise RecipeError(
            f"selected runtime generation has a malformed receipt: {error}",
            "incomplete",
        ) from error
    if not isinstance(receipt, dict):
        raise RecipeError(
            "selected runtime generation receipt is not a JSON object",
            "incomplete",
        )
    return name, receipt


def generation_receipts(home: Path) -> dict[str, dict[str, Any]]:
    runtime_root, _launcher = runtime_locations(home)
    receipts: dict[str, dict[str, Any]] = {}
    versions = runtime_root / "versions"
    if not versions.is_dir():
        return receipts
    for generation in sorted(versions.iterdir()):
        receipt = generation / "runtime.json"
        if generation.is_dir() and receipt.is_file():
            try:
                document = json.loads(receipt.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise RecipeError(
                    f"runtime generation {generation.name} has an unreadable "
                    f"receipt: {error}",
                    "incomplete",
                ) from error
            if not isinstance(document, dict):
                raise RecipeError(
                    f"runtime generation {generation.name} receipt is not a "
                    "JSON object",
                    "incomplete",
                )
            receipts[generation.name] = document
    return receipts


def _version_names(home: Path) -> set[str]:
    runtime_root, _launcher = runtime_locations(home)
    versions = runtime_root / "versions"
    if not versions.is_dir():
        return set()
    return {entry.name for entry in versions.iterdir() if entry.is_dir()}


def observe_install(
    python: str, source: Path, home: Path, ledger: RunLedger
) -> dict[str, Any]:
    """Run the supported installer and observe creation versus reuse.

    A generation is created-and-owned only when it was absent before the
    invocation and present after it; a reused generation is recorded as
    reused and never owned.
    """
    before = _version_names(home)
    exit_code, payload = run_installer(python, source)
    observation_payload = payload.get("stdout")
    if exit_code != 0:
        raise RecipeError("status runtime installation failed")
    after = _version_names(home)
    created = sorted(after - before)
    name, receipt = read_current_generation(home)
    observation: dict[str, Any] = {
        "exit": exit_code,
        "selected": name,
        "created": created,
        "reused": name not in created,
        "receipt": receipt,
        "installer_result": observation_payload,
    }
    for generation in created:
        ledger.record_generation(generation)
    ledger.save()
    return observation


def assert_runtime_identity(
    receipt: dict[str, Any],
    *,
    source_sha256: str | None = None,
    plugin_version: str | None = None,
    python_sha256: str | None = None,
) -> list[str]:
    """Receipt identity fields are bare lowercase hex, never prefixed."""
    violations: list[str] = []
    if source_sha256 and receipt.get("source_sha256") != source_sha256.removeprefix(
        "sha256:"
    ):
        violations.append("runtime content identity differs from the sealed source")
    if plugin_version and receipt.get("plugin_version") != plugin_version:
        violations.append(f"runtime plugin version is {receipt.get('plugin_version')}")
    if python_sha256 and receipt.get("python_executable_sha256") != (
        python_sha256.removeprefix("sha256:")
    ):
        violations.append(
            "runtime interpreter identity differs from the pinned guest interpreter"
        )
    return violations


def remove_runtime(home: Path, ledger: RunLedger) -> dict[str, Any]:
    """Product-absent for the status runtime: remove `current`, the launcher
    and only generations this Job created. Pre-existing generations,
    `install.lock`, `status.yaml`, `status.lock` and the EPIC-024 backups are
    preserved."""
    runtime_root, launcher = runtime_locations(home)
    removed: list[str] = []
    for path in (runtime_root / "current", launcher):
        if path.is_symlink():
            raise RecipeError(f"unsafe runtime path refuses removal: {path}")
        if path.is_file():
            path.unlink()
            removed.append(str(path))
    versions = runtime_root / "versions"
    for name in sorted(ledger.document.get("generations", [])):
        generation = versions / name
        if generation.is_dir():
            shutil.rmtree(generation)
            removed.append(str(generation))
    preserved = {
        "pre_existing_generations": sorted(
            set(_version_names(home)) - set(ledger.document.get("generations", []))
        ),
        "install_lock": (runtime_root / "install.lock").exists(),
    }
    return {"removed": removed, "preserved": preserved}


def remove_owned_generation(home: Path, name: str, ledger: RunLedger) -> bool:
    """Delete only a generation this run created; preserve foreign state."""
    if not ledger.owns("generations", name):
        return False
    runtime_root, _launcher = runtime_locations(home)
    generation = runtime_root / "versions" / name
    if generation.is_dir():
        shutil.rmtree(generation)
    return True


def _staging_dirs(home: Path) -> list[str]:
    runtime_root, _launcher = runtime_locations(home)
    versions = runtime_root / "versions"
    if not versions.is_dir():
        return []
    return [
        entry.name
        for entry in versions.iterdir()
        if entry.name.startswith(".generation.")
    ]


def interrupted_update(
    python: str,
    source: Path,
    home: Path,
    ledger: RunLedger,
    *,
    deadline_seconds: int = 600,
) -> dict[str, Any]:
    """Run the supported installer and kill its process group at staging.

    Foreign staging directories are preserved and reported; only a staging
    directory created by an installer this run started, whose process group
    has ceased, is recorded and later removable.
    """
    foreign = sorted(set(_staging_dirs(home)))
    argv = installer_command(python, source, approve=True)
    process = subprocess.Popen(
        argv,
        cwd=str(source),
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + deadline_seconds
    staging: str | None = None
    while time.monotonic() < deadline:
        candidates = [name for name in _staging_dirs(home) if name not in foreign]
        if candidates:
            staging = min(candidates)
            break
        if process.poll() is not None:
            break
        time.sleep(0.2)
    if staging is None:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=60)
        return {
            "interrupted": False,
            "foreign_staging_preserved": foreign,
            "reason": "interruption checkpoint missed; the installer published "
            "before the staging directory was observed",
        }
    os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=60)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.2)
    else:
        raise RecipeError(
            "interrupted installer process group did not exit; refusing assertions"
        )
    ledger.record_staging(staging)
    return {
        "interrupted": True,
        "staging_directory": staging,
        "foreign_staging_preserved": foreign,
        "cessation": "process-group exit confirmed through kill(pgid, 0) ESRCH",
    }


def unsafe_launcher_refusal(python: str, source: Path, home: Path) -> dict[str, Any]:
    """Prove the installer's explicit safe failure without substituting effects."""
    _runtime, launcher = runtime_locations(home)
    backup = (
        home
        / ".aquarium"
        / f"status-runtime-launcher-backup-{job_identity()['job_id']}"
    )
    if backup.exists():
        raise RecipeError(
            "an unsafe-launcher probe backup already exists for this Job",
            "incomplete",
        )
    if launcher.exists() or launcher.is_symlink():
        shutil.move(str(launcher), str(backup))
    try:
        launcher.parent.mkdir(parents=True, exist_ok=True)
        launcher.symlink_to("/nonexistent/aquarium-status")
        exit_code, payload = run_installer(python, source, approve=True, timeout=300)
    finally:
        if launcher.is_symlink():
            launcher.unlink()
        if backup.exists():
            shutil.move(str(backup), str(launcher))

    def _schema_error(stream: Any) -> bool:
        return isinstance(stream, dict) and stream.get("schema") == RUNTIME_ERROR_SCHEMA

    refused = exit_code != 0 and (
        _schema_error(payload.get("stderr")) or _schema_error(payload.get("stdout"))
    )
    return {"refused": bool(refused), "payload": payload}


def codex_plugin_list(codex: str, marketplace: str) -> dict[str, Any]:
    result = run(
        [codex, "plugin", "list", "--marketplace", marketplace, "--json"], timeout=300
    )
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {"exit": result.returncode, "error": result.stderr[-800:]}


def marketplace_register(codex: str, directory: Path) -> subprocess.CompletedProcess:
    return run([codex, "plugin", "marketplace", "add", str(directory)], timeout=300)


def marketplace_unregister(codex: str, name: str) -> subprocess.CompletedProcess:
    return run([codex, "plugin", "marketplace", "remove", name], timeout=300)


def plugin_remove(
    codex: str, plugin: str, marketplace: str
) -> subprocess.CompletedProcess:
    return run(
        [codex, "plugin", "remove", plugin, "--marketplace", marketplace], timeout=300
    )


def plugin_add(
    codex: str, plugin: str, marketplace: str
) -> subprocess.CompletedProcess:
    return run([codex, "plugin", "add", f"{plugin}@{marketplace}"], timeout=600)


def installed_aquarium(codex: str, marketplace: str) -> dict[str, Any] | None:
    listing = codex_plugin_list(codex, marketplace)
    for row in listing.get("installed", []) if isinstance(listing, dict) else []:
        if isinstance(row, dict) and row.get("name") == "aquarium":
            return row
    return None


OWNERSHIP_SCHEMA = "aquarium.vm-marketplace-owner/v1"


def marketplace_dir(home: Path, kind: str) -> Path:
    """Single source of truth for each sealed artifact's guest-local path."""
    if kind not in {"artifact", "prior-artifact"}:
        raise RecipeError(f"unknown sealed artifact kind: {kind}")
    return home / ".aquarium-vm-marketplaces" / kind


def owner_sidecar_path(home: Path, kind: str) -> Path:
    return home / ".aquarium-vm-marketplaces" / f"{kind}.owner.json"


def read_owner_sidecar(home: Path, kind: str) -> dict[str, Any] | None:
    path = owner_sidecar_path(home, kind)
    if not path.is_file() or path.is_symlink():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # Unreadable, undecodable or malformed bytes are "unparsable": the
        # caller treats the sidecar as missing and ownership fails closed.
        return None
    if not isinstance(document, dict):
        return None
    if document.get("schema") != OWNERSHIP_SCHEMA or document.get("kind") != kind:
        return None
    return document


def marketplace_registrations(codex: str) -> dict[str, str]:
    """The active native registrations: marketplace name -> source path."""
    result = run([codex, "plugin", "marketplace", "list", "--json"], timeout=300)
    try:
        payload = json.loads(result.stdout)
    except ValueError:
        raise RecipeError(
            f"native marketplace inventory unavailable: {result.stderr[-300:]}"
        )
    registrations: dict[str, str] = {}
    for row in payload.get("marketplaces", []):
        name = row.get("name")
        source = row.get("marketplaceSource", {})
        if isinstance(name, str) and isinstance(source, dict):
            registrations[name] = str(source.get("source", ""))
    return registrations


def assert_registration(
    codex: str, marketplace_name: str, expected: str | None
) -> None:
    """The declared end state of the native registration for the name."""
    active = marketplace_registrations(codex).get(marketplace_name)
    if expected is None:
        if active is not None:
            raise RecipeError(
                f"marketplace {marketplace_name} is still registered at {active}"
            )
    elif active != expected:
        raise RecipeError(
            f"marketplace {marketplace_name} is registered at {active!r}, "
            f"expected {expected!r}"
        )


def _registration_matches(codex: str, marketplace_name: str, directory: Path) -> bool:
    """The active native registration points exactly at this directory."""
    return marketplace_registrations(codex).get(marketplace_name) == str(directory)


def _harness_directory_owned(home: Path, kind: str) -> bool:
    """A harness directory is replaceable only when its sidecar binds its
    exact sealed bytes; nothing is written inside the payload itself."""
    sidecar = read_owner_sidecar(home, kind)
    if sidecar is None:
        return False
    directory = marketplace_dir(home, kind)
    if not directory.is_dir():
        return False
    try:
        actual = tree_sha256_from_directory(directory)
    except TreeDigestError:
        # A symlink or special file can never be byte-identical to a
        # sealed artifact, so the directory is not ours to replace.
        return False
    return actual == sidecar.get("artifact_tree_sha256")


def establish_marketplace(
    codex: str,
    home: Path,
    sealed_dir: Path,
    kind: str,
    ledger: RunLedger,
    marketplace_name: str,
    *,
    declared_predecessors: tuple[str, ...] = (),
) -> Path:
    """Publish a sealed artifact under its harness path and register it.

    A foreign registration or directory is preserved and reported unless it
    is a predecessor kind this run's declared starting state names, or the
    suite performs J-BASE's recorded one-time normalization itself.
    """
    target = marketplace_dir(home, kind)
    active = marketplace_registrations(codex).get(marketplace_name)
    # First free the marketplace name only through a fully-owned predecessor
    # (its own sidecar, digest and exact active registration), then verify
    # the unregister took effect. Unregistering a predecessor never by
    # itself authorizes deleting the target.
    if active is not None and active != str(target):
        replaceable = False
        for predecessor in declared_predecessors:
            predecessor_dir = marketplace_dir(home, predecessor)
            if (
                active == str(predecessor_dir)
                and _harness_directory_owned(home, predecessor)
                and _registration_matches(codex, marketplace_name, predecessor_dir)
            ):
                replaceable = True
                break
        if not replaceable:
            raise RecipeError(
                f"marketplace {marketplace_name} is registered from a "
                f"foreign source {active}; it is preserved and reported",
                "incomplete",
            )
        result = marketplace_unregister(codex, marketplace_name)
        if result.returncode != 0:
            raise RecipeError(f"marketplace unregister failed: {result.stderr[-300:]}")
        active = marketplace_registrations(codex).get(marketplace_name)
        if active is not None:
            raise RecipeError(
                f"marketplace unregister did not take effect for "
                f"{marketplace_name}; state preserved and reported",
                "incomplete",
            )
    if target.exists():
        # Replacing THIS directory requires its own full condition set after
        # the name is free: sidecar, digest match, and no other registration.
        if not _harness_directory_owned(home, kind):
            raise RecipeError(
                "foreign harness marketplace preserved "
                "(sidecar missing or digest mismatch): " + str(target),
                "incomplete",
            )
        if active is not None and active != str(target):
            raise RecipeError(
                f"harness directory {target} is not the active registration "
                f"({active}); it is preserved",
                "incomplete",
            )
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sealed_dir, target)
    try:
        copied_digest = tree_sha256_from_directory(target)
    except TreeDigestError as error:
        raise RecipeError(
            f"copied {kind} marketplace is unsafe: {error}", "incomplete"
        ) from error
    sidecar = {
        "schema": OWNERSHIP_SCHEMA,
        "kind": kind,
        "artifact_tree_sha256": copied_digest,
        "job_id": job_identity()["job_id"],
    }
    owner_sidecar_path(home, kind).write_text(
        json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"
    )
    ledger.record_marketplace(kind)
    ledger.save()
    result = marketplace_register(codex, target)
    if result.returncode != 0 and "alreadyAdded" not in result.stdout:
        raise RecipeError(
            f"guest-local marketplace registration failed: {result.stderr[-400:]}"
        )
    assert_registration(codex, marketplace_name, str(target))
    return target


def remove_owned_marketplace(
    codex: str, home: Path, kind: str, ledger: RunLedger, marketplace_name: str
) -> dict[str, Any]:
    """Remove a harness marketplace only when this run's chain owns it.

    The native registration is unregistered only while it points at this
    kind's directory, so a restored predecessor registration survives.
    """
    target = marketplace_dir(home, kind)
    report: dict[str, Any] = {"kind": kind, "removed": False}
    if not target.exists():
        return report
    if not _harness_directory_owned(home, kind):
        report["preserved"] = "foreign or mutated harness directory"
        return report
    active = marketplace_registrations(codex).get(marketplace_name)
    if active is not None and active != str(target):
        # Another source is registered for the name: leave the registration
        # and the directory alone; the declared end state governs the swap.
        report["registration_left_alone"] = active
        return report
    if active == str(target):
        result = marketplace_unregister(codex, marketplace_name)
        if result.returncode != 0:
            report["preserved"] = "unregister failed: " + result.stderr[-200:]
            return report
        active = marketplace_registrations(codex).get(marketplace_name)
        report["unregistered"] = active is None
        if active is not None:
            report["preserved"] = (
                f"unregister did not take effect; {marketplace_name} still "
                f"registered at {active}"
            )
            return report
    elif active is None:
        # No active registration: deletion additionally requires a declared
        # end state that says absent, recorded by the caller.
        if not ledger.owns("marketplaces", kind):
            report["preserved"] = (
                "no active registration and no declared-absent end state"
            )
            return report
    shutil.rmtree(target)
    owner_sidecar_path(home, kind).unlink(missing_ok=True)
    report["removed"] = True
    return report


def record_foreign_registration(codex: str, marketplace_name: str) -> dict[str, Any]:
    """Evidence for J-BASE's declared one-time normalization."""
    registration = {
        "name": marketplace_name,
        "source": marketplace_registrations(codex).get(marketplace_name),
        "installed_row": installed_aquarium(codex, marketplace_name),
    }
    return registration


def codex_component_identity(codex: str, home: Path) -> dict[str, Any]:
    """Record Codex as a component identity instead of walking its tree."""
    standalone = home / ".codex/packages/standalone/current"
    current_target = None
    release_digest = None
    if standalone.is_symlink():
        current_target = os.readlink(standalone)
        release = standalone.resolve()
        if release.is_dir():
            # The real standalone release carries symlinks (for example
            # `codex -> bin/codex`), so the digest follows the
            # symlink-aware inventory walk, not the sealed-tree walker.
            try:
                release_digest = inventory_tree_sha256_from_directory(release)
            except TreeDigestError as error:
                raise RecipeError(f"codex release digest failed: {error}") from error
    return {
        "version": run([codex, "--version"]).stdout.strip(),
        "current_target": current_target,
        "release_digest": release_digest,
    }


def create_venv(python: str, destination: Path) -> Path:
    result = run([python, "-m", "venv", str(destination)], timeout=600)
    if result.returncode != 0:
        raise RecipeError(f"Job-owned venv creation failed: {result.stderr[-400:]}")
    return destination / "bin/python"


def pip_install_locked(venv_python: Path, lock_file: Path) -> dict[str, Any]:
    result = run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "--no-deps",
            "--no-cache-dir",
            "-r",
            str(lock_file),
        ],
        timeout=1800,
    )
    return {"exit": result.returncode, "tail": result.stderr[-800:]}


def seed_fixture(checkout: Path, destination: Path) -> dict[str, Any]:
    template = checkout / "tests/vm/fixtures/greeting"
    if destination.exists():
        raise RecipeError(f"fixture already exists; preserve it: {destination}")
    shutil.copytree(template, destination)
    for argv in (
        ["init", "-q"],
        ["config", "user.name", "VM Fixture"],
        ["config", "user.email", "vm-fixture@example.invalid"],
        ["add", "."],
        ["commit", "-qm", "[TEST] Establish greeting fixture"],
    ):
        result = run(["git", "-C", str(destination), *argv], timeout=300)
        if result.returncode != 0:
            raise RecipeError(f"fixture seed failed: {result.stderr[-400:]}")
    return {
        "fixture": str(destination),
        "head": run(["git", "rev-parse", "HEAD"], cwd=destination).stdout.strip(),
    }


def read_json_safe(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_document(path: Path, document: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return path


_PROFILE_VALIDATOR: dict[str, Any] = {}


def load_profile_validator(checkout: Path) -> Any:
    """Load the candidate checkout's profile validator by exact file path.

    The validator is stdlib-only and carries the one implementation of
    `aquarium-skill-tree-sha256/v1`; loading it from the sealed candidate
    history keeps a single digest implementation across host and guest.
    """
    path = checkout / "tests/vm/profiles/validate_profiles.py"
    if not path.is_file():
        raise RecipeError(
            "the candidate checkout lacks the profile validator", "incomplete"
        )
    module = _PROFILE_VALIDATOR.get(str(path))
    if module is None:
        spec = importlib.util.spec_from_file_location(
            "aquarium_vm_profile_validator", path
        )
        if spec is None or spec.loader is None:
            raise RecipeError("the profile validator cannot be loaded", "incomplete")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _PROFILE_VALIDATOR[str(path)] = module
    return module


def skill_tree_digest(checkout: Path, tree: Path) -> str:
    """`aquarium-skill-tree-sha256/v1` over one installed skill tree."""
    validator = load_profile_validator(checkout)
    try:
        return validator.tree_digest_from_directory(tree)
    except ValueError as error:
        raise RecipeError(f"skill tree is unsafe: {error}", "incomplete") from error


def stage_evidence_archive(
    archive: Path, source_root: Path, members: list[str], required: list[str]
) -> dict[str, Any]:
    """Write one fixed-name evidence archive and its content manifest.

    A `.partial` archive returns its manifest to the caller for publication
    after the final archive name is installed. Every member is a file under
    `source_root`; `required` names records the
    case cannot pass staging without. Members that exist are always
    archived, so a partial run still transports its originals; each missing
    required record is reported in the manifest, and the caller keeps
    `ok: false` while any gap remains. The tar is deterministic (sorted
    members, zeroed ownership and timestamps) so the manifest digests can be
    reproduced from any copy of the originals.
    """
    present = sorted(
        relative
        for relative in set(members)
        if (source_root / relative).is_file()
        and not (source_root / relative).is_symlink()
    )
    missing = sorted(set(required) - set(present))
    records: list[dict[str, Any]] = []
    for relative in present:
        source = source_root / relative
        records.append(
            {
                "path": relative,
                "size": source.stat().st_size,
                "sha256": sha256_file(source),
            }
        )
    # An empty case is still staged: its archive is empty and its manifest
    # lists its missing required classes, so the loop never stops early and
    # a case with only gaps still travels as a declared output.
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "w") as handle:
        for record in records:
            source = source_root / record["path"]
            info = tarfile.TarInfo(record["path"])
            info.size = record["size"]
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mode = 0o755 if source.stat().st_mode & 0o111 else 0o644
            with source.open("rb") as stream:
                handle.addfile(info, stream)
    document = {
        "schema": EVIDENCE_ARCHIVE_SCHEMA,
        "archive": archive.name.removesuffix(".partial"),
        "archive_present": True,
        "sha256": sha256_file(archive),
        "algorithm": "sha256",
        "members": records,
        "required": sorted(set(required)),
        "missing_required": missing,
    }
    manifest_name = document["archive"].replace(".tar", ".manifest.json")
    if not archive.name.endswith(".partial"):
        write_document(archive.with_name(manifest_name), document)
    return document


def results_directory(suite: str) -> Path:
    return job_root() / "results" / suite


def run_ledger(suite: str) -> RunLedger:
    return RunLedger(results_directory(suite) / "run-ledger.json")


RECORDED_INVENTORIES: dict[str, dict[str, Any]] = {}


def record_inventory(suite: str, phase: str, document: dict[str, Any]) -> None:
    RECORDED_INVENTORIES.setdefault(suite, {})[phase] = document


def finish(
    suite: str,
    outcome: str,
    documents: dict[str, Any],
    *,
    consumer_cleanup: str,
    inputs: dict[str, Any] | None = None,
) -> int:
    result = {
        "schema": RESULT_SCHEMA,
        "suite": suite,
        "outcome": outcome,
        "consumer_cleanup": consumer_cleanup,
        "candidate": (inputs or load_inputs())["candidate"],
        **documents,
    }
    aggregate_path = results_directory(suite) / "inventories.json"
    aggregate = read_json_safe(aggregate_path)
    if not isinstance(aggregate, dict) or not isinstance(
        aggregate.get("inventories"), dict
    ):
        aggregate = {
            "schema": "aquarium.vm-suite-inventories/v1",
            "inventories": {},
        }
    # Phase-mode snapshots merge over any capture-mode aggregate an earlier
    # phase process wrote, so cross-process captures survive this finish.
    aggregate["inventories"].update(RECORDED_INVENTORIES.get(suite, {}))
    write_document(aggregate_path, aggregate)
    write_document(results_directory(suite) / "result.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return OUTCOME_EXITS[outcome]


def wrong_uuid() -> str:
    """A synthetic mismatching UUID for the identity-rejection probe."""
    return "00000000-0000-0000-0000-000000000000"
