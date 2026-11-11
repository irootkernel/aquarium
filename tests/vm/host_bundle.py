#!/usr/bin/env python3
"""Seal the Aquarium VM host bundle and build its Haepari job specs.

The candidate plugin artifact always comes from a clean committed checkout,
never from the dirty working tree. The TASK-088 harness rides along as a
labelled development snapshot whose tree digest is recorded with every suite.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

REPOSITORY = Path(__file__).resolve().parents[2]
PROFILES_ROOT = REPOSITORY / "tests/vm/profiles"
STABLE_PROFILE_NAME = (
    "proposed-stable-haepari-0.1.0-aquarium-0.1.21-codex-0.164.0-podway-0.2.14.json"
)
PODWAY_RELEASE_COMMIT = "31cbd110573271ea3376cb07eb961f3dc257a05d"
PODWAY_RELEASE_FILES = {
    "archive.tar.gz": "4ca62ec943aa21e59c3173201c1f2e80cf274bb459dbb2ff3af0f01e34926546",
    "archive.tar.gz.sha256": "ee9dd6295032d0e9d9ad67a11b532a0a62ad2c56a34a213434d78fd01c7f8cd0",
    "bin/podway": "c9923c6c1fee8c31e595c8163863051ebc5d62ae651c3a947b8662cd3aa927a7",
    "provenance.json": "703d6baf3957d95634f6d0680d95293ae8e2ef9471b37970b6ebc3c021c6b975",
    "skills/use-podway/SKILL.md": "6949e7513cc699ef2bd445cbaf834b726ea7e25ed39141813c547b7b1f650871",
    "skills/use-podway/references/delegation.md": "1ccc52365a6f83091a42e38fab6bb4398a78e881df1254401b20522cd2401272",
    "skills/use-podway/references/goal.md": "dbd4f7a5188d507526bf9da216839eb22b3114a8f4d32f17edfef70027ff8846",
    "skills/use-podway/references/lifecycle.md": "b5460fd4eb5f101cc3f63412dc2e1d52be33902f835baa1df029412e0e81d83b",
    "skills/use-podway/references/recovery.md": "1153c6b60ddb1831b7a726ea0f1f63ca3e29962514183e0e85d3a4fe7262b83a",
}
PODWAY_PREVIOUS_RELEASE_FILES = {
    "archive.tar.gz": "cc91c083790da53977e193b09742836a7cec68aa18864df93989fed2df645835",
    "archive.tar.gz.sha256": "4eb8b039a022c1d3c6773e71f1284002c99bc48f95b22ec843cfbd81b865bab4",
    "bin/podway": "249685e65402049ecad83f1ecef8efee361f6ac979bde686a9ebabd10c685cf2",
    "provenance.json": "63a7b1385fa766e6b23edb5eed0d0f63cf68f1008c04a4de8e4aceacb591553e",
    "skills/use-podway/SKILL.md": "e1b067e8e64dc1d297c295ad6f17d0db202c4763fb496dce0d98e13513710200",
    "skills/use-podway/references/delegation.md": "ea314acd2179ede83c19e92df6cb4db20a2b55b7c7e8a1ded907dd9617be232d",
    "skills/use-podway/references/goal.md": "facf835661b08da9432d3d063df8be0c064d6899e132256b55ab6155a6bf41d9",
    "skills/use-podway/references/lifecycle.md": "736998ddb12262da2a3fca6fc90c84001207623928c9e876908fa9b9e502f4f3",
    "skills/use-podway/references/recovery.md": "ac839571e629ef05c7e4cbb5dec2e6683dfa5fde11d91fe0d77a84557d8e465c",
}
HARNESS_ROOT = REPOSITORY / "tests/vm/recipes"
SUITES_PATH = REPOSITORY / "tests/vm/host_suites.json"
INPUTS_SCHEMA = "aquarium.vm-host-inputs/v1"
SUITES_SCHEMA = "aquarium.vm-host-suites/v1"
GUEST_CONTEXT_SCHEMA = "aquarium.vm-guest-context/v1"
JOB_SCHEMA = "haepari.job/v2"
TRACKED_ROOTS = (".agents/plugins/marketplace.json", "plugins/aquarium")
TREE_ALGORITHM = "haepari-tree-sha256/v1"
SPEC_SCHEMA_KEYS = frozenset(
    {
        "schema",
        "execution_mode",
        "resource_id",
        "mode",
        "suite",
        "input",
        "environment",
        "workload",
        "setup",
        "manual",
        "deadlines",
        "effects",
        "provenance",
    }
)
DEADLINE_KEYS = {
    "queue_seconds",
    "prepare_seconds",
    "run_seconds",
    "manual_seconds",
    "collect_seconds",
    "cleanup_seconds",
}
GUEST_CONTEXT_REQUIRED = (
    "expected_guest_uuid",
    "guest_home",
    "guest_path",
    "guest_python",
    "guest_codex",
    "guest_podway",
    "guest_marketplace_name",
)
CONTEXT_TOKENS = frozenset(GUEST_CONTEXT_REQUIRED) | {"driver_python"}
UUID_RE = re.compile(
    r"^[0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12}$"
)
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
LOCK_PIN_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*=="
    r"[A-Za-z0-9.!+_-]+(?: --hash=sha256:[0-9a-f]{64})+$"
)


class BundleError(RuntimeError):
    pass


def _git(repository: Path, *arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise BundleError(
            f"git {' '.join(arguments)} failed: {result.stderr.strip()[:400]}"
        )
    return result.stdout


def _copy_tree(source: Path, target: Path, refuse_links: bool = True) -> list[str]:
    copied: list[str] = []
    for path in sorted(source.rglob("*")):
        if "__pycache__" in path.relative_to(source).parts:
            continue
        if refuse_links and path.is_symlink():
            raise BundleError(f"symlink in sealed input source: {path}")
        relative = path.relative_to(source).as_posix()
        if path.is_dir():
            continue
        if not path.is_file():
            raise BundleError(f"nonregular sealed input: {path}")
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        mode = stat.S_IMODE(path.stat().st_mode)
        destination.chmod(0o755 if mode & 0o111 else 0o644)
        copied.append(relative)
    return copied


def _copy_git_visible(repository: Path, source: Path, target: Path) -> list[str]:
    """Seal exactly the git-visible files under the harness root.

    The listing is `git ls-files --cached --others --exclude-standard`, so
    tracked files and untracked-but-not-ignored candidate files are sealed
    while ignored local state (`__pycache__/`, `.omc/`, ...) never is. A
    listed path missing on disk — an unstaged deletion — is refused
    explicitly, never silently skipped. Every listed path is walked
    component by component with os.lstat: each ancestor must be a real
    directory, the leaf a regular file, any symlink at any level is
    refused, and the resolved leaf must stay inside the source root."""
    try:
        relative_root = source.resolve().relative_to(repository.resolve())
    except ValueError as error:
        raise BundleError(
            f"sealed input source is outside the repository: {source}"
        ) from error
    listing = _git(
        repository,
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
        "--",
        relative_root.as_posix(),
    )
    copied: list[str] = []
    for entry in listing.split("\0"):
        if not entry:
            continue
        try:
            relative = Path(entry).relative_to(relative_root).as_posix()
        except ValueError as error:
            raise BundleError(
                f"listed sealed input outside the root: {entry}"
            ) from error
        path = source / relative
        parts = Path(relative).parts
        current = source
        for part in parts[:-1]:
            current = current / part
            try:
                info = os.lstat(current)
            except OSError as error:
                raise BundleError(
                    f"listed sealed input is missing on disk: {path}"
                ) from error
            if stat.S_ISLNK(info.st_mode):
                raise BundleError(f"symlink in sealed input source: {path}")
            if not stat.S_ISDIR(info.st_mode):
                raise BundleError(f"nonregular sealed input: {path}")
        try:
            info = os.lstat(current / parts[-1])
        except OSError as error:
            raise BundleError(
                f"listed sealed input is missing on disk: {path}"
            ) from error
        if stat.S_ISLNK(info.st_mode):
            raise BundleError(f"symlink in sealed input source: {path}")
        if not stat.S_ISREG(info.st_mode):
            raise BundleError(f"nonregular sealed input: {path}")
        if not (current / parts[-1]).resolve().is_relative_to(source.resolve()):
            raise BundleError(f"sealed input escapes the source root: {path}")
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        mode = stat.S_IMODE(path.stat().st_mode)
        destination.chmod(0o755 if mode & 0o111 else 0o644)
        copied.append(relative)
    if not copied:
        raise BundleError(f"no git-visible sealed inputs under {relative_root}")
    return copied


def _load_tree_digest() -> Any:
    spec = importlib.util.spec_from_file_location(
        "aquarium_vm_tree_digest", REPOSITORY / "tests/vm/recipes/tree_digest.py"
    )
    if spec is None or spec.loader is None:
        raise BundleError("the shared tree digest module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_profile_validator() -> Any:
    """The single implementation of `aquarium-skill-tree-sha256/v1`."""
    spec = importlib.util.spec_from_file_location(
        "aquarium_vm_profile_validator_bundle",
        REPOSITORY / "tests/vm/profiles/validate_profiles.py",
    )
    if spec is None or spec.loader is None:
        raise BundleError("the profile validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_TREE_DIGEST = _load_tree_digest()
tree_sha256 = _TREE_DIGEST.tree_sha256
_PROFILE_VALIDATOR = _load_profile_validator()
skill_tree_digest_from_directory = _PROFILE_VALIDATOR.tree_digest_from_directory


def load_guest_context(path: Path) -> dict[str, str]:
    try:
        context = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BundleError(f"guest context is unreadable: {error}") from error
    if not isinstance(context, dict) or context.get("schema") != GUEST_CONTEXT_SCHEMA:
        raise BundleError(f"guest context schema must be {GUEST_CONTEXT_SCHEMA}")
    for field in GUEST_CONTEXT_REQUIRED:
        value = context.get(field)
        if not isinstance(value, str) or not value:
            raise BundleError(f"guest context field {field} is required")
    if not UUID_RE.fullmatch(context["expected_guest_uuid"]):
        raise BundleError("guest context expected_guest_uuid must be a UUID")
    for field in ("guest_home", "guest_python", "guest_codex", "guest_podway"):
        if not context[field].startswith("/"):
            raise BundleError(f"guest context {field} must be absolute")
    if "driver_python" not in context:
        context["driver_python"] = context["guest_python"]
    elif not context["driver_python"].startswith("/"):
        raise BundleError("guest context driver_python must be absolute")
    return context


def load_suites(path: Path = SUITES_PATH) -> dict[str, Any]:
    try:
        declarations = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BundleError(f"host suite declarations are unreadable: {error}") from error
    if (
        not isinstance(declarations, dict)
        or declarations.get("schema") != SUITES_SCHEMA
    ):
        raise BundleError(f"host suite schema must be {SUITES_SCHEMA}")
    if not isinstance(declarations.get("common_env"), dict):
        raise BundleError("host suite common_env must be an object")
    suites = declarations.get("suites")
    if not isinstance(suites, dict) or not suites:
        raise BundleError("host suites must be a non-empty object")
    return declarations


def validate_suite(name: str, suite: Any, selected_files: set[str]) -> None:
    label = f"suite {name}"
    if not isinstance(suite, dict):
        raise BundleError(f"{label} must be an object")
    allowed = {
        "modes",
        "environment_profile",
        "argv",
        "setup_argv",
        "cwd",
        "required_outputs",
        "manual",
        "effects_mode",
        "authorization_reference",
        "deadlines",
    }
    unknown = sorted(set(suite) - allowed)
    if unknown:
        raise BundleError(f"{label} has unknown keys: {', '.join(unknown)}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise BundleError(f"{label} name is not a suite identity")
    modes = suite.get("modes")
    if not isinstance(modes, list) or not modes or set(modes) - {"auto", "manual"}:
        raise BundleError(f"{label} modes must be auto/manual entries")
    if suite.get("environment_profile") not in {
        "stable",
        "candidate",
        "podway-candidate",
    }:
        raise BundleError(
            f"{label} environment_profile must select a declared stable, candidate or podway-candidate profile"
        )
    argv = suite.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(item, str) for item in argv)
    ):
        raise BundleError(f"{label} argv must be a non-empty string list")
    if suite.get("cwd") != "harness":
        raise BundleError(f"{label} cwd must stay inside the sealed harness")
    outputs = suite.get("required_outputs")
    if not isinstance(outputs, list) or not outputs:
        raise BundleError(f"{label} required_outputs must be non-empty")
    for output in outputs:
        if (
            not isinstance(output, str)
            or not output.startswith("results/")
            or output.endswith("/")
            or ".." in output
        ):
            raise BundleError(f"{label} required output is unsafe: {output}")
    if suite.get("effects_mode") not in {"offline", "live"}:
        raise BundleError(f"{label} effects_mode must be offline or live")
    if (
        not isinstance(suite.get("authorization_reference"), str)
        or not suite["authorization_reference"]
    ):
        raise BundleError(f"{label} authorization_reference is required")
    deadlines = suite.get("deadlines")
    if not isinstance(deadlines, dict) or not deadlines:
        raise BundleError(f"{label} deadlines are required")
    manual = "manual" in modes
    for key, value in deadlines.items():
        if key not in DEADLINE_KEYS:
            raise BundleError(f"{label} deadline {key} is unknown")
        pinned_zero = manual and key == "run_seconds" and value == 0
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or (value < 1 and not pinned_zero)
        ):
            raise BundleError(f"{label} deadline {key} must be positive")
    if manual:
        if "manual_seconds" not in deadlines:
            raise BundleError(f"{label} manual deadline is required")
        if deadlines.get("run_seconds", 0) != 0:
            raise BundleError(f"{label} manual Jobs pin run_seconds to zero")
    elif "run_seconds" not in deadlines or "manual_seconds" in deadlines:
        raise BundleError(f"{label} run/manual deadline does not match its mode")
    if manual:
        block = suite.get("manual")
        if not isinstance(block, dict):
            raise BundleError(f"{label} manual block is required")
        document = block.get("scenario_document")
        scenarios = block.get("required_scenarios")
        if not isinstance(document, str) or document not in selected_files:
            raise BundleError(f"{label} scenario document must be a sealed input")
        if (
            not isinstance(scenarios, list)
            or not scenarios
            or any(
                not isinstance(item, str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", item)
                for item in scenarios
            )
        ):
            raise BundleError(f"{label} required_scenarios must be suite identities")
    else:
        if "manual" in suite:
            raise BundleError(f"{label} manual block belongs to manual mode only")


def resolve_tokens(value: str, context: dict[str, str]) -> str:
    token = re.fullmatch(r"\{([a-z_]+)\}", value)
    if token is None:
        return value
    field = token[1]
    if field not in CONTEXT_TOKENS:
        raise BundleError(f"unknown guest context token: {value}")
    return context[field]


def _materialize_tree_at(repository: Path, revision: str, target: Path) -> list[str]:
    listing = _git(repository, "ls-tree", "-r", "-z", revision, "--", *TRACKED_ROOTS)
    written: list[str] = []
    for record in listing.split("\0"):
        if not record:
            continue
        metadata, raw_path = record.split("\t", 1)
        mode, kind, _object = metadata.split(" ", 2)
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise BundleError(f"unsupported Git entry at {revision}: {raw_path}")
        blob = subprocess.run(
            ["git", "-C", str(repository), "show", f"{revision}:{raw_path}"],
            capture_output=True,
            check=False,
        )
        if blob.returncode != 0:
            raise BundleError(f"cannot read {revision}:{raw_path}")
        destination = target / raw_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(blob.stdout)
        destination.chmod(0o755 if mode == "100755" else 0o644)
        written.append(raw_path)
    if not written:
        raise BundleError(f"revision {revision} carries no plugin snapshot")
    return written


def build_candidate_artifact(
    repository: Path, git_sha: str, scratch: Path, output: Path
) -> dict[str, Any]:
    subprocess.run(
        ["git", "clone", "--no-hardlinks", "--quiet", str(repository), str(scratch)],
        capture_output=True,
        check=True,
    )
    _git(scratch, "checkout", "--quiet", "-B", "main", git_sha)
    status = _git(scratch, "status", "--porcelain=v1")
    if status.strip():
        raise BundleError("scratch clone at the candidate is not clean")
    make = subprocess.run(
        [
            "make",
            "aquarium-dev-build",
        ],
        cwd=scratch,
        env={**os.environ, "AQUARIUM_DEV_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        check=False,
    )
    if make.returncode != 0:
        raise BundleError(
            f"candidate artifact build failed: {make.stderr.strip()[:400]}"
        )
    try:
        manifest = json.loads(make.stdout)
    except ValueError as error:
        raise BundleError(f"candidate artifact manifest is invalid: {error}") from error
    if (
        manifest.get("schema") != "aquarium-dev-artifact-manifest/v1"
        or manifest.get("git_sha") != git_sha
    ):
        raise BundleError("candidate artifact manifest does not bind the candidate")
    return manifest


def derive_candidate_profile(
    stable: dict[str, Any],
    tree_digest: str,
    development_version: str,
    candidate_skill_tree_digest: str,
) -> dict[str, Any]:
    """Derive the candidate profile from the stable bytes and sealed inputs.

    Every overridden Aquarium identity comes from the sealed candidate unit:
    the version, provenance, sealed artifact and the plugin's own skill-tree
    pin computed from the sealed artifact's skills tree. Unchanged
    dependency pins stay verbatim, and the candidate id derives from the
    stable id rather than a hard-coded prefix.
    """
    stable_id = stable.get("profile_id")
    stable_prefix = "proposed-stable-"
    if not isinstance(stable_id, str) or not stable_id.startswith(stable_prefix):
        raise BundleError("the stable profile id does not follow the stable prefix")
    sha12 = development_version.rsplit(".", 1)[-1]
    profile = json.loads(json.dumps(stable))
    profile["profile_id"] = (
        f"proposed-candidate-{stable_id[len(stable_prefix) :]}-dev-{sha12}"
    )
    stable_plugin_version = None
    for component in stable.get("components", []):
        if (
            isinstance(component, dict)
            and component.get("name") == "aquarium-plugin"
            and isinstance(component.get("version"), str)
        ):
            stable_plugin_version = component["version"]
    plugin_seen = False
    for component in profile.get("components", []):
        if isinstance(component, dict) and component.get("name") == "aquarium-plugin":
            plugin_seen = True
            component["version"] = development_version.removeprefix("v")
            component.pop("provenance", None)
            component["sealed_artifact"] = {
                "tree_sha256": tree_digest,
                "development_version": development_version,
            }
            skill_tree = component.get("skill_tree")
            if not isinstance(skill_tree, dict):
                raise BundleError(
                    "the stable plugin component carries no skill-tree pin to "
                    "rebind to the candidate's own skills"
                )
            skill_tree["sha256"] = candidate_skill_tree_digest
    if not plugin_seen:
        raise BundleError("the stable profile has no aquarium-plugin component")
    # The candidate upgrades from the stable profile's own plugin release,
    # not from the earlier release the stable profile upgrades from.
    for state in profile.get("starting_states", []):
        if state.get("kind") == "prior_version" and stable_plugin_version:
            state["aquarium"] = stable_plugin_version
    return profile


def seal_release_files(
    source: Path, bundle: Path, prefix: str, inventory: dict[str, str]
) -> list[str]:
    """Copy only an exact pinned release inventory, checking both sides."""
    if not source.is_absolute() or source.resolve() != source or not source.is_dir():
        raise BundleError("Podway release input must be a physical absolute directory")
    members = list(source.rglob("*"))
    if any(
        path.is_symlink() or not (path.is_file() or path.is_dir()) for path in members
    ):
        raise BundleError("Podway release input contains unsafe members")
    files = {path.relative_to(source).as_posix() for path in members if path.is_file()}
    if files != set(inventory):
        raise BundleError(
            "Podway release input must contain the exact archive, provenance, binary and complete skill tree"
        )
    for relative, expected in inventory.items():
        if hashlib.sha256((source / relative).read_bytes()).hexdigest() != expected:
            raise BundleError(f"Podway release input digest differs: {relative}")
    copied = _copy_tree(source, bundle / prefix)
    if set(copied) != set(inventory) or any(
        hashlib.sha256((bundle / prefix / relative).read_bytes()).hexdigest()
        != expected
        for relative, expected in inventory.items()
    ):
        raise BundleError("Podway release input changed while sealing")
    return [f"{prefix}/{name}" for name in copied]


def seal_podway_release(
    source: Path, bundle: Path, profile: dict[str, Any]
) -> tuple[list[str], dict[str, Any]]:
    """Seal one qualified release without changing the historical baseline."""
    prefix = "dependencies/podway-0.2.17"
    copied = seal_release_files(source, bundle, prefix, PODWAY_RELEASE_FILES)
    skill_digest = skill_tree_digest_from_directory(
        bundle / prefix / "skills/use-podway"
    )
    components = {row["name"]: row for row in profile["components"]}
    if not {"podway", "use-podway"} <= set(components):
        raise BundleError("candidate profile lacks Podway and its paired skill")
    components["podway"].update(
        version="v0.2.17",
        executable_sha256="sha256:" + PODWAY_RELEASE_FILES["bin/podway"],
        archive_sha256=PODWAY_RELEASE_FILES["archive.tar.gz"],
        provenance={"release_tag": "v0.2.17", "tag_commit": PODWAY_RELEASE_COMMIT},
    )
    components["use-podway"]["pin"] = {"commit": PODWAY_RELEASE_COMMIT}
    components["use-podway"]["skill_tree"]["sha256"] = skill_digest
    profile["profile_id"] = profile["profile_id"].replace(
        "-podway-0.2.14-", "-podway-0.2.17-"
    )
    return copied, {
        "payload_root": prefix,
        "version": "v0.2.17",
        "source_commit": PODWAY_RELEASE_COMMIT,
        "contract_generation": 2,
        "contract_manifest_digest": "sha256:f5e56e344a79022766fb69af7991c60d57e7793495b2599c1c3d3ef296309100",
        "binary_sha256": PODWAY_RELEASE_FILES["bin/podway"],
        "skill_tree_sha256": skill_digest,
    }


def _check_fixture_lock(path: Path) -> None:
    """Accept pip's standard hash-locked requirements, continuations included."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise BundleError(
            f"fixture requirements lock is unreadable: {error}"
        ) from error
    pins: list[str] = []
    pending = ""
    for line in raw.splitlines():
        if line.lstrip().startswith("#"):
            continue
        if line.rstrip().endswith("\\"):
            pending += line.rstrip()[:-1].strip() + " "
            continue
        pending += line.strip()
        if pending.strip():
            pins.append(" ".join(pending.split()))
        pending = ""
    if pending.strip():
        pins.append(" ".join(pending.split()))
    if not pins:
        raise BundleError("fixture requirements lock is empty")
    for pin in pins:
        if not LOCK_PIN_RE.fullmatch(pin):
            raise BundleError(
                "fixture requirements lock must be pip exact pins with sha256 hashes"
            )


def build_bundle(
    run_dir: Path,
    context_path: Path,
    suites_selection: str,
    resource_id: str,
    mode: str,
    *,
    repository: Path = REPOSITORY,
    candidate_sha: str | None = None,
    artifact_dir: Path | None = None,
    artifact_manifest: dict[str, Any] | None = None,
    prior_tag: str = "v0.1.21",
    fixture_requirements: Path | None = None,
    queue_override: int | None = None,
    podway_release: Path | None = None,
    podway_previous_release: Path | None = None,
    baseline_profile: Path | None = None,
) -> dict[str, Any]:
    context = load_guest_context(context_path)
    declarations = load_suites()
    suite_map = declarations["suites"]
    names = (
        sorted(suite_map)
        if suites_selection == "all"
        else [suites_selection]
        if suites_selection in suite_map
        else []
    )
    if not names:
        raise BundleError("select a consumer-declared suite or all")
    dependency_suites = {
        "podway-upgrade",
        "epic-squad",
        "release-acceptance",
        "release-orchestration",
    }
    if "release-orchestration" in names and baseline_profile is None:
        raise BundleError(
            "release-orchestration requires an explicit matching released baseline profile"
        )
    if baseline_profile is not None and (
        not baseline_profile.is_absolute()
        or baseline_profile != baseline_profile.resolve()
        or not baseline_profile.is_file()
    ):
        raise BundleError("baseline profile must be a physical absolute regular file")
    stable_bytes = (
        baseline_profile or (PROFILES_ROOT / STABLE_PROFILE_NAME)
    ).read_bytes()
    stable_profile = json.loads(stable_bytes)
    if baseline_profile is not None:
        errors = _PROFILE_VALIDATOR.validate_profile(stable_profile)
        if errors:
            raise BundleError("invalid baseline profile: " + "; ".join(errors))
        plugin = next(
            (
                row
                for row in stable_profile["components"]
                if row["name"] == "aquarium-plugin"
            ),
            None,
        )
        if plugin is None or not isinstance(plugin.get("version"), str):
            raise BundleError("baseline must pin the released Aquarium plugin version")
        provenance = plugin.get("provenance", {})
        prior_tag = provenance.get("release_tag", "")
        if prior_tag != "v" + plugin["version"] or not plugin.get("skill_tree", {}).get(
            "sha256"
        ):
            raise BundleError(
                "baseline requires released tag/version and complete plugin skill-tree provenance"
            )
        if _git(
            repository, "rev-parse", prior_tag + "^{commit}"
        ).strip() != provenance.get("tag_commit"):
            raise BundleError("baseline release tag commit differs from profile")
    if podway_release is not None and not dependency_suites.intersection(names):
        raise BundleError(
            "Podway release inputs require an explicit manual dependency suite"
        )
    if dependency_suites.intersection(names) and podway_release is None:
        raise BundleError("selected suite requires the verified Podway release input")
    if podway_previous_release is not None and "podway-upgrade" not in names:
        raise BundleError("previous Podway release requires the podway-upgrade suite")
    suite_modes: dict[str, str] = {}
    for name in names:
        declared = suite_map[name]["modes"]
        if suites_selection == "all":
            suite_modes[name] = declared[0]
        elif mode in declared:
            suite_modes[name] = mode
        else:
            raise BundleError(f"requested mode is not declared for suite {name}")

    git_sha = candidate_sha or _git(repository, "rev-parse", "HEAD").strip()
    bundle = run_dir / "bundle"
    if bundle.exists():
        raise BundleError("run directory already holds a bundle; reconnect instead")

    harness_files = _copy_git_visible(
        repository, HARNESS_ROOT, bundle / "harness" / "tests/vm/recipes"
    )
    manifest = artifact_manifest
    if artifact_dir is None:
        scratch = run_dir / "scratch"
        output = run_dir / "build-output"
        output.mkdir(parents=True, exist_ok=True)
        manifest = build_candidate_artifact(repository, git_sha, scratch, output)
        artifact_source = output / manifest["artifact_path"]
    else:
        artifact_source = artifact_dir
        if manifest is None:
            raise BundleError("a prebuilt artifact needs its manifest")
        if manifest.get("git_sha") != git_sha:
            raise BundleError("prebuilt artifact manifest does not bind the candidate")
    artifact_files = _copy_tree(artifact_source, bundle / "artifact")
    prior_files = _materialize_tree_at(repository, prior_tag, bundle / "prior-artifact")
    if baseline_profile is not None:
        prior_plugin = bundle / "prior-artifact/plugins/aquarium"
        version = json.loads((prior_plugin / ".codex-plugin/plugin.json").read_text())[
            "version"
        ]
        if (
            version != plugin["version"]
            or skill_tree_digest_from_directory(prior_plugin / "skills")
            != plugin["skill_tree"]["sha256"]
        ):
            raise BundleError("baseline profile differs from the released plugin bytes")
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "bundle",
            "create",
            str(bundle / "checkout.bundle"),
            "--all",
        ],
        capture_output=True,
        check=True,
    )
    (bundle / "profile").mkdir(parents=True, exist_ok=True)
    (bundle / "profile/stable.json").write_bytes(stable_bytes)
    development_version = manifest["development_version"]
    candidate_digest = tree_sha256(bundle / "artifact", artifact_files)
    candidate_skill_digest = skill_tree_digest_from_directory(
        bundle / "artifact/plugins/aquarium/skills"
    )
    candidate_profile = derive_candidate_profile(
        stable_profile, candidate_digest, development_version, candidate_skill_digest
    )
    dependency_files: list[str] = []
    podway_upgrade = None
    if podway_release is not None:
        podway_profile = json.loads(json.dumps(candidate_profile))
        dependency_files, podway_upgrade = seal_podway_release(
            podway_release, bundle, podway_profile
        )
        (bundle / "profile/podway-candidate.json").write_text(
            json.dumps(podway_profile, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        podway_upgrade["archive_sha256"] = PODWAY_RELEASE_FILES["archive.tar.gz"]
        podway_upgrade["extract_binary"] = True
        dependency_files.remove(podway_upgrade["payload_root"] + "/bin/podway")
        dependency_files.append("profile/podway-candidate.json")
    if podway_previous_release is not None:
        dependency_files.extend(
            seal_release_files(
                podway_previous_release,
                bundle,
                "dependencies/podway-0.2.16",
                PODWAY_PREVIOUS_RELEASE_FILES,
            )
        )
    (bundle / "profile/candidate.json").write_text(
        json.dumps(candidate_profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    prior_tag_commit = _git(repository, "rev-parse", f"{prior_tag}^{{commit}}").strip()
    prior_digest = tree_sha256(bundle / "prior-artifact", prior_files)
    (bundle / "artifact-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lock_relative = None
    if fixture_requirements is not None:
        _check_fixture_lock(fixture_requirements)
        (bundle / "requirements").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            fixture_requirements, bundle / "requirements/fixture-requirements.lock"
        )
        lock_relative = "requirements/fixture-requirements.lock"

    harness_tree = tree_sha256(bundle / "harness/tests/vm/recipes", harness_files)
    dirty = bool(_git(repository, "status", "--porcelain=v1").strip())
    selected = [
        *(f"harness/tests/vm/recipes/{name}" for name in harness_files),
        "checkout.bundle",
        "artifact-manifest.json",
        *(f"artifact/{name}" for name in artifact_files),
        *(f"prior-artifact/{name}" for name in prior_files),
        "profile/stable.json",
        "profile/candidate.json",
        *dependency_files,
    ]
    if lock_relative:
        selected.append(lock_relative)
    for name in selected:
        if (bundle / name).is_symlink() or not (bundle / name).is_file():
            raise BundleError(f"sealed input is missing or unsafe: {name}")
    inputs = {
        "schema": INPUTS_SCHEMA,
        "candidate": {
            "git_sha": git_sha,
            "base_commit": git_sha,
            "dirty_harness_snapshot": dirty,
            "development_version": development_version,
            "artifact_tree_sha256": candidate_digest,
        },
        "prior": {
            "version": manifest_stable_version(stable_profile),
            "tag": prior_tag,
            "tag_commit": prior_tag_commit,
            "artifact_tree_sha256": prior_digest,
        },
        "harness_tree_sha256": harness_tree,
        "fixture_requirements": lock_relative,
    }
    if podway_upgrade is not None:
        inputs["podway_upgrade"] = podway_upgrade
        if podway_previous_release is not None:
            inputs["podway_upgrade"]["previous_payload_root"] = (
                "dependencies/podway-0.2.16"
            )
    (bundle / "harness/inputs.json").write_text(
        json.dumps(inputs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    selected = ["harness/inputs.json", *selected]
    for name in selected:
        if (bundle / name).is_symlink() or not (bundle / name).is_file():
            raise BundleError(f"sealed input is missing or unsafe: {name}")
    for name in names:
        validate_suite(name, suite_map[name], set(selected))
    inventory_digest = tree_sha256(bundle, selected)

    common_env = {
        key: resolve_tokens(value, context)
        for key, value in declarations["common_env"].items()
    }
    jobs: list[dict[str, Any]] = []
    run_id = uuid.uuid4().hex
    for index, name in enumerate(names):
        suite = suite_map[name]
        profile_relative = f"profile/{suite['environment_profile']}.json"
        profile_bytes = (bundle / profile_relative).read_bytes()
        profile = json.loads(profile_bytes.decode("utf-8"))
        deadlines = dict(suite["deadlines"])
        if queue_override is not None:
            deadlines["queue_seconds"] = queue_override
        workload_environment = dict(common_env)
        suite_mode = suite_modes[name]
        spec = {
            "schema": JOB_SCHEMA,
            "execution_mode": "managed",
            "resource_id": resource_id,
            "mode": suite_mode,
            "suite": name,
            "input": {
                "root": str(bundle.resolve()),
                "selected_files": selected,
                "inventory_digest": inventory_digest,
            },
            "environment": {
                "profile_id": profile["profile_id"],
                "profile_digest": hashlib.sha256(profile_bytes).hexdigest(),
            },
            "workload": {
                "argv": [resolve_tokens(item, context) for item in suite["argv"]],
                "cwd": suite["cwd"],
                "environment": workload_environment,
                "required_outputs": list(suite["required_outputs"]),
            },
            "deadlines": deadlines,
            "effects": {
                "mode": suite["effects_mode"],
                "authorization_reference": suite["authorization_reference"],
            },
            "provenance": {
                "candidate_digest": candidate_digest,
                "tests_digest": harness_tree,
                "target_profile_digest": hashlib.sha256(profile_bytes).hexdigest(),
                "evidence_class": "development",
            },
        }
        if suite_mode == "manual" and "setup_argv" in suite:
            spec["setup"] = {
                "argv": [resolve_tokens(item, context) for item in suite["setup_argv"]]
            }
        if suite_mode == "manual":
            spec["manual"] = {
                "scenario_document": suite["manual"]["scenario_document"],
                "required_scenarios": list(suite["manual"]["required_scenarios"]),
            }
        unknown = sorted(set(spec) - SPEC_SCHEMA_KEYS)
        if unknown:
            raise BundleError(f"spec for {name} has unknown keys: {unknown}")
        spec_path = run_dir / f"spec-{index}.json"
        encoded = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
        spec_path.write_text(encoded, encoding="utf-8")
        jobs.append(
            {
                "suite": name,
                "mode": suite_mode,
                "request_key": f"aquarium-vm-{run_id}-{index}",
                "spec": spec_path.name,
                "spec_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                "profile_id": profile["profile_id"],
                "submission_started": False,
                "probe": False,
            }
        )
    return {
        "installation_binding": {
            "candidate_git_sha": git_sha,
            "development_version": development_version,
            "artifact_tree_sha256": candidate_digest,
            "prior_artifact_tree_sha256": prior_digest,
            "harness_tree_sha256": harness_tree,
            "inventory_digest": inventory_digest,
            "dirty_harness_snapshot": dirty,
        },
        "declared_suites": names,
        "jobs": jobs,
    }


def manifest_stable_version(stable: dict[str, Any]) -> str:
    for component in stable.get("components", []):
        if isinstance(component, dict) and component.get("name") == "aquarium-plugin":
            version = component.get("version")
            if isinstance(version, str) and VERSION_RE.fullmatch(version):
                return version
    raise BundleError("stable profile does not pin an aquarium version")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--guest-context", required=True)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--resource", required=True)
    parser.add_argument("--mode", choices=("auto", "manual"), required=True)
    parser.add_argument("--candidate-sha")
    parser.add_argument("--artifact-dir")
    parser.add_argument("--fixture-requirements")
    parser.add_argument("--queue-seconds", type=int)
    parser.add_argument("--podway-release")
    parser.add_argument("--podway-previous-release")
    parser.add_argument("--baseline-profile", type=Path)
    arguments = parser.parse_args()
    try:
        record = build_bundle(
            Path(arguments.run_dir),
            Path(arguments.guest_context),
            arguments.suite,
            arguments.resource,
            arguments.mode,
            candidate_sha=arguments.candidate_sha,
            artifact_dir=Path(arguments.artifact_dir)
            if arguments.artifact_dir
            else None,
            fixture_requirements=(
                Path(arguments.fixture_requirements)
                if arguments.fixture_requirements
                else None
            ),
            queue_override=arguments.queue_seconds,
            podway_previous_release=Path(arguments.podway_previous_release)
            if arguments.podway_previous_release
            else None,
            podway_release=Path(arguments.podway_release)
            if arguments.podway_release
            else None,
            baseline_profile=arguments.baseline_profile,
        )
    except (BundleError, OSError, subprocess.SubprocessError) as error:
        print(f"aquarium host bundle: {error}", file=sys.stderr)
        return 2
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
