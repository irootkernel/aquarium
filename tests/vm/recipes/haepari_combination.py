"""Bounded manual combination observations inside one managed VM Job."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
from pathlib import Path
from typing import Any

import recipe_lib as lib
from release_orchestration import publish_archive_pair, recover_archive_pair

SUITE = "haepari-combination"
PROFILE = "combination-candidate"
# Each tuple is (required variant, installed/native evidence required).
CASES = {
    "identity": (("released-baseline", True), ("target-identities", True)),
    "clean-install": (("product-absent", True), ("install-discovery", True)),
    "upgrade": (
        ("meaningful-released-state", True),
        ("channel-disable-binding", True),
        ("interim-no-launch", True),
        ("released-skills-status", True),
        ("dependency-order", True),
        ("original-writer-refusal", True),
        ("fresh-generation2", True),
        ("candidate-startup", True),
    ),
    "tools": tuple(
        (name, True)
        for name in (
            "haepari",
            "podway",
            "mulgae",
            "gaori",
            "sorage",
            "sanho",
            "seongge",
            "gaebokchi",
            "task-epic-startup",
            "release-plan-readiness",
            "fresh-skills",
            "inter-tool",
        )
    )
    + (("dolgorae-gul-functional-exclusion", False),),
    "busy": tuple(
        (name, False)
        for name in (
            "podway-writer",
            "haepari-job",
            "mulgae-grant",
            "gaori-invocation",
            "same-operation-settlement",
            "history-preserved",
        )
    ),
    "locks": tuple(
        (name, name in {"cli-mcp", "role-concurrency"})
        for name in (
            "cli-mcp",
            "role-concurrency",
            "fifo-serialization",
            "renew-release",
            "queued-cancel",
            "raced-grant-release",
            "borrower-validation",
            "loss-drain",
            "expiry-no-termination",
            "partial-role-termination",
            "interrupted-start-await",
            "fresh-full-review",
            "receipt-bound-provider-free-reconciliation",
        )
    ),
    "assessments": tuple(
        (name, False)
        for name in (
            "plan",
            "qa-ready",
            "publication-ready",
            "publication-complete",
            "missing-cleanup",
            "stale-identity",
            "timeout-unknown",
            "executor-replacement",
        )
    ),
    "resource-p": (("q-queued-while-p-held", True), ("p-only-occupancy", True)),
    "cleanup": (
        ("consumers-settled", True),
        ("target-retained", True),
        ("history-preserved", True),
        ("clean-home-removed", True),
    ),
}
PHASE_CASES = {
    "baseline": "identity",
    "clean-install": "clean-install",
    "transition-upgrade": "upgrade",
    "tool-cases": "tools",
    "busy-cases": "busy",
    "lock-cases": "locks",
    "assessment-cases": "assessments",
    "resource-p": "resource-p",
}
PHASE_OUTPUTS = {
    "transition-upgrade": "transition-upgrade",
    "tool-cases": "tools",
    "busy-cases": "busy",
    "lock-cases": "locks",
    "assessment-cases": "assessments",
}


def regular_member(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise lib.RecipeError("evidence member must be a relative file", "incomplete")
    path = root / relative
    if ".." in Path(relative).parts or path.resolve() != path.absolute():
        raise lib.RecipeError("unsafe evidence member", "incomplete")
    if path.exists() and not path.is_file():
        raise lib.RecipeError("evidence member must be a regular file", "incomplete")
    return path


def binding(context: Any) -> dict:
    return {
        "candidate_sha": context.inputs["candidate"]["git_sha"],
        "profile_digest": context.profile_digest(PROFILE),
        "job": context.job,
    }


def write_once(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(document, indent=2) + "\n")


def case_index(context: Any, results: Path) -> dict:
    index = lib.read_json_safe(results / "case-index.json")
    if not isinstance(index, dict) or any(
        index.get(k) != v for k, v in binding(context).items()
    ):
        raise lib.RecipeError(
            "original Job/candidate/profile case index required", "incomplete"
        )
    if not isinstance(index.get("cases"), dict) or set(index["cases"]) != set(CASES):
        raise lib.RecipeError("complete fixed case index required", "incomplete")
    return index


def case_complete(context: Any, name: str, entry: Any) -> bool:
    if not isinstance(entry, dict) or not isinstance(entry.get("observations"), list):
        return False
    observations = entry["observations"]
    if not all(isinstance(row, dict) for row in observations):
        return False
    rows = {row.get("variant"): row for row in observations}
    if len(rows) != len(observations) or set(rows) != {v for v, _ in CASES[name]}:
        return False
    for variant, native in CASES[name]:
        row = rows[variant]
        evidence = row.get("evidence_class")
        allowed = {"native-installed", "reused-with-applicability"}
        if not native:
            allowed.add("fixture-helper")
        if (
            row.get("status") != "pass"
            or not row.get("decision_reference")
            or evidence not in allowed
            or not row.get("required")
            or not isinstance(row["required"], list)
            or (
                evidence == "reused-with-applicability" and not row.get("applicability")
            )
        ):
            return False
        for relative in row["required"]:
            path = regular_member(context.root, relative)
            if not path.is_file() or not path.stat().st_size:
                return False
    return True


def verify_payload(context: Any) -> None:
    data = context.inputs.get("combination")
    if not isinstance(data, dict) or not data.get("files"):
        raise lib.RecipeError("sealed combination input required", "incomplete")
    root = context.root / data["payload_root"]
    members = list(root.rglob("*"))
    if (
        root.is_symlink()
        or any(
            path.is_symlink() or not (path.is_dir() or path.is_file())
            for path in members
        )
        or {path.relative_to(root).as_posix() for path in members if path.is_file()}
        != set(data["files"])
    ):
        raise lib.RecipeError("combination input membership differs", "incomplete")
    if context.profile_digest(PROFILE) != data["candidate_profile_sha256"]:
        raise lib.RecipeError("derived combination profile differs", "incomplete")
    for relative, expected in data["files"].items():
        path = regular_member(root, relative)
        if not path.is_file() or lib.sha256_file(path) != expected:
            raise lib.RecipeError("combination bytes differ: " + relative, "incomplete")
    original = context.root / "profile/combination-original.json"
    if lib.sha256_file(original) != data["profile_sha256"]:
        raise lib.RecipeError("original combination profile differs", "incomplete")


def extract_executable(archive: Path, target: Path, row: dict, *, whole: bool) -> dict:
    """Extract only the pinned regular executable; never follow archive links."""
    if archive.is_symlink() or lib.sha256_file(archive) != row["archive_sha256"]:
        raise lib.RecipeError("archive identity differs", "incomplete")
    with tarfile.open(archive, "r:gz") as handle:
        selected = None
        seen = set()
        for member in handle:
            parts = Path(member.name).parts
            if (
                not parts
                or Path(member.name).is_absolute()
                or ".." in parts
                or member.name in seen
                or not (member.isfile() or member.isdir())
            ):
                raise lib.RecipeError("unsafe archive member", "incomplete")
            seen.add(member.name)
            if whole and (
                not member.isfile() or member.name != row["member"] or len(seen) != 1
            ):
                raise lib.RecipeError(
                    "whole archive must contain one exact executable", "incomplete"
                )
            if member.name == row["member"]:
                if not member.isfile() or member.size != row["binary_bytes"]:
                    raise lib.RecipeError(
                        "archive executable size differs", "incomplete"
                    )
                selected = member
        if selected is None:
            raise lib.RecipeError("archive executable missing", "incomplete")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.parent.resolve() != target.parent or target.is_symlink():
            raise lib.RecipeError("unsafe extraction destination", "incomplete")
        with handle.extractfile(selected) as source, target.open("xb") as output:
            shutil.copyfileobj(source, output)
    if lib.sha256_file(target) != row["binary_sha256"]:
        raise lib.RecipeError("extracted executable identity differs", "incomplete")
    target.chmod(0o755)
    return {
        "path": str(target),
        "sha256": lib.sha256_file(target),
        "archive_sha256": row["archive_sha256"],
        "member": row["member"],
    }


def custody_document(path: Path) -> dict:
    try:
        document = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise lib.RecipeError(
            f"unreadable custody JSON: {path.name}", "incomplete"
        ) from error
    if not isinstance(document, dict):
        raise lib.RecipeError(
            f"custody JSON object required: {path.name}", "incomplete"
        )
    return document


def custody_parent() -> dict:
    try:
        chain = json.loads(os.environ.get("HAEPARI_PARENT_CONTEXT", ""))
    except ValueError as error:
        raise lib.RecipeError(
            "native custody parent context required", "incomplete"
        ) from error
    if not isinstance(chain, list) or not chain or not isinstance(chain[0], dict):
        raise lib.RecipeError("native custody parent context required", "incomplete")
    parent = chain[0]
    if (
        not all(
            isinstance(parent.get(k), str) and parent[k]
            for k in ("installation_id", "job_id")
        )
        or not isinstance(parent.get("lease_generation"), int)
        or isinstance(parent["lease_generation"], bool)
        or parent["lease_generation"] <= 0
        or not isinstance(parent.get("nonce"), str)
        or len(parent["nonce"]) != 64
        or any(c not in "0123456789abcdef" for c in parent["nonce"])
    ):
        raise lib.RecipeError(
            "native custody parent identity is malformed", "incomplete"
        )
    return {
        key: parent[key] for key in ("installation_id", "job_id", "lease_generation")
    }


def prepare_artifact_custody(manifest_path: Path, payload: Path, home: Path) -> dict:
    """Retain six whole unpublished executables without installing any tool."""
    manifest = custody_document(manifest_path)
    tools = manifest.get("tools")
    expected_names = {
        "mulgae",
        "gaori",
        "sanho",
        "seongge",
        "schema-decode",
        "gaebokchi",
    }
    if (
        not isinstance(tools, dict)
        or set(tools) != expected_names
        or not isinstance(manifest.get("custody_root"), str)
        or not isinstance(manifest.get("expected_guest_uuid"), str)
        or not manifest["expected_guest_uuid"]
    ):
        raise lib.RecipeError("custody manifest shape differs", "incomplete")
    required = {
        "archive",
        "archive_sha256",
        "member",
        "binary_bytes",
        "binary_sha256",
        "source_commit",
    }
    archives = {}
    for name, row in tools.items():
        if (
            not isinstance(row, dict)
            or set(row) != required
            or not isinstance(row.get("archive"), str)
            or not row["archive"]
            or row.get("member") != name
            or not isinstance(row.get("binary_bytes"), int)
            or isinstance(row["binary_bytes"], bool)
            or row["binary_bytes"] <= 0
            or any(
                not isinstance(row.get(k), str)
                or len(row[k]) != size
                or any(c not in "0123456789abcdef" for c in row[k])
                for k, size in (
                    ("archive_sha256", 64),
                    ("binary_sha256", 64),
                    ("source_commit", 40),
                )
            )
        ):
            raise lib.RecipeError(f"custody manifest row differs: {name}", "incomplete")
        archives[name] = regular_member(payload, row["archive"])
        if not archives[name].is_file():
            raise lib.RecipeError(f"custody archive missing: {name}", "incomplete")
    root = Path(manifest["custody_root"])
    marker = root.with_name(root.name + ".owner.json")
    if (
        not root.is_absolute()
        or root.parent != home / "haepari-artifact-custody"
        or not root.name.startswith("task100-")
        or root.resolve() != root
        or root.exists()
        or marker.exists()
        or marker.is_symlink()
    ):
        raise lib.RecipeError(
            "custody scope is not a fresh disclosed root", "incomplete"
        )
    parent = custody_parent()
    lib.verify_guest_identity(manifest["expected_guest_uuid"])
    ownership = {
        "custody_root": str(root),
        "native_job": parent,
        "input_manifest_sha256": lib.sha256_file(manifest_path),
        "declared_selected_input_digest": os.environ.get(
            "AQUARIUM_CUSTODY_INPUT_DIGEST"
        ),
        "retained_for": ["P", "Q", "TASK-102"],
        "current_last_consumer": "TASK-102",
        "cleanup_owner": "CO after verified last-consumer settlement",
        "cleanup_state": "intentionally retained; not removed",
        "parent_directory_created": not root.parent.exists(),
    }
    root.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    write_once(marker, ownership)
    root.mkdir(mode=0o700)
    records = {}
    try:
        for name, row in tools.items():
            records[name] = extract_executable(
                archives[name], root / "bin" / name, row, whole=True
            )
    except (lib.RecipeError, OSError, tarfile.TarError, EOFError) as error:
        write_once(
            root / "custody-failure.json",
            {
                "ownership_marker": str(marker),
                "ownership_sha256": lib.sha256_file(marker),
                "native_job": parent,
                "input_manifest_sha256": ownership["input_manifest_sha256"],
                "complete": False,
                "completed_tools": records,
                "error_type": type(error).__name__,
                "error": str(error),
                "retention": ownership,
            },
        )
        raise lib.RecipeError(
            "custody preparation failed; tracked partial root retained", "incomplete"
        ) from error
    receipt = {
        "custody_root": str(root),
        "manifest_sha256": ownership["input_manifest_sha256"],
        "native_job": parent,
        "tools": records,
        "complete": True,
        "installed_tools": False,
        "ownership_marker": str(marker),
        "ownership_sha256": lib.sha256_file(marker),
        "retention": ownership,
    }
    write_once(root / "custody-receipt.json", receipt)
    return receipt


def custody_binary(context: Any, name: str, row: dict) -> Path:
    if not isinstance(row, dict) or not isinstance(row.get("custody_root"), str):
        raise lib.RecipeError("custody delivery row is malformed", "incomplete")
    root = Path(row["custody_root"])
    if (
        root.parent != context.home / "haepari-artifact-custody"
        or root.resolve() != root
    ):
        raise lib.RecipeError(
            "custody root differs from selected guest home", "incomplete"
        )
    receipt = custody_document(root / "custody-receipt.json")
    marker = root.with_name(root.name + ".owner.json")
    ownership = custody_document(marker)
    parent = custody_parent()
    native_job = receipt.get("native_job")
    tools = receipt.get("tools")
    selected = tools.get(name) if isinstance(tools, dict) else None
    if (
        receipt.get("complete") is not True
        or receipt.get("custody_root") != str(root)
        or receipt.get("manifest_sha256") != row.get("manifest_sha256")
        or not isinstance(native_job, dict)
        or native_job.get("installation_id") != parent["installation_id"]
        or native_job.get("job_id") == context.job["job_id"]
        or not isinstance(selected, dict)
        or selected.get("sha256") != row.get("binary_sha256")
        or receipt.get("ownership_marker") != str(marker)
        or receipt.get("ownership_sha256") != lib.sha256_file(marker)
        or ownership.get("native_job") != native_job
        or ownership.get("input_manifest_sha256") != row.get("manifest_sha256")
        or ownership.get("custody_root") != str(root)
        or ownership.get("current_last_consumer") != "TASK-102"
    ):
        raise lib.RecipeError("custody receipt/pin/ownership differs", "incomplete")
    binary = regular_member(root, "bin/" + name)
    if (
        not binary.is_file()
        or binary.stat().st_size != row.get("binary_bytes")
        or lib.sha256_file(binary) != row.get("binary_sha256")
    ):
        raise lib.RecipeError("custody executable differs", "incomplete")
    return binary


def retained_custody(context: Any) -> list[dict]:
    retained = {}
    for name, row in context.inputs.get("combination", {}).get("delivery", {}).items():
        if row["mode"] != "guest-custody":
            continue
        binary = custody_binary(context, name, row)
        root = Path(row["custody_root"])
        marker = root.with_name(root.name + ".owner.json")
        if str(root) not in retained:
            retained[str(root)] = {
                **custody_document(marker),
                "ownership_marker": str(marker),
                "ownership_sha256": lib.sha256_file(marker),
                "receipt": str(root / "custody-receipt.json"),
                "receipt_sha256": lib.sha256_file(root / "custody-receipt.json"),
                "binaries": {},
            }
        retained[str(root)]["binaries"][name] = {
            "path": str(binary),
            "sha256": lib.sha256_file(binary),
        }
    return list(retained.values())


def materialize(context: Any, results: Path) -> int:
    """Acquire only the declared artifacts, with receipts separate from input digest."""
    data = context.inputs["combination"]
    root = context.root / data["payload_root"]
    delivery = data.get("delivery")
    if (
        not isinstance(delivery, dict)
        or not delivery
        or custody_document(root / "delivery.json") != delivery
    ):
        raise lib.RecipeError(
            "sealed finite delivery declaration required", "incomplete"
        )
    baseline = lib.read_json_safe(results / "baseline.json")
    if not isinstance(baseline, dict) or any(
        baseline.get(k) != v for k, v in binding(context).items()
    ):
        raise lib.RecipeError(
            "observe baseline before target artifact acquisition", "incomplete"
        )
    destination = context.root / "combination-materialized"
    if destination.exists():
        raise lib.RecipeError(
            "retain original materialization; reconcile, never redownload", "incomplete"
        )
    destination.mkdir()
    originals = results / "originals/identity/delivery"
    originals.mkdir(parents=True, exist_ok=True)
    binaries = {}
    for name, row in delivery.items():
        target = destination / name
        if row["mode"] == "guest-custody":
            binary = custody_binary(context, name, row)
            write_once(
                originals / (name + ".custody-receipt.json"),
                custody_document(Path(row["custody_root"]) / "custody-receipt.json"),
            )
            binaries[name] = {
                "path": str(binary),
                "sha256": lib.sha256_file(binary),
                "source": "verified guest custody; not native selected-input bytes",
            }
        elif row["mode"] == "whole-archive":
            binaries[name] = extract_executable(
                regular_member(root, row["archive"]), target, row, whole=True
            )
        else:
            archive = destination / (name + ".download")
            checksum = destination / (name + ".sha256")
            request = {
                "name": name,
                "url": row["url"],
                "checksum_url": row["checksum_url"],
                "expected_sha256": row["download_sha256"],
                "source_commit": row["source_commit"],
            }
            write_once(originals / (name + ".request.json"), request)
            observations = []
            requests = [(row["url"], archive), (row["checksum_url"], checksum)]
            if name == "sorage":
                requests.append(
                    (
                        row["url"] + ".manifest.json",
                        destination / "sorage.manifest.json",
                    )
                )
            for url, path in requests:
                completed = lib.run(
                    [
                        "/usr/bin/curl",
                        "--disable",
                        "--fail",
                        "--location",
                        "--silent",
                        "--show-error",
                        "--proto",
                        "=https",
                        "--output",
                        str(path),
                        url,
                    ],
                    timeout=1800,
                )
                observations.append(
                    {
                        "url": url,
                        "exit_code": completed.returncode,
                        "stderr": completed.stderr,
                        "path": str(path),
                    }
                )
                if completed.returncode:
                    write_once(
                        originals / (name + ".download-receipt.json"),
                        {"requests": observations},
                    )
                    raise lib.RecipeError(
                        "official download failed; original retained", "incomplete"
                    )
            actual = lib.sha256_file(archive)
            receipt = {
                "requests": observations,
                "sha256": actual,
                "source_commit": row["source_commit"],
            }
            write_once(originals / (name + ".download-receipt.json"), receipt)
            shutil.copyfile(checksum, originals / (name + ".sha256"))
            tokens = checksum.read_text().split()
            if actual != row["download_sha256"] or not tokens or tokens[0] != actual:
                raise lib.RecipeError(
                    "official download/checksum differs", "incomplete"
                )
            if name == "sorage":
                manifest_path = destination / "sorage.manifest.json"
                shutil.copyfile(manifest_path, originals / "sorage.manifest.json")
                manifest = json.loads(manifest_path.read_text())
                expected_manifest = {
                    "version": "0.1.4",
                    "revision": row["source_commit"],
                    "target": "darwin-arm64",
                    "binary": "sorage-v0.1.4-darwin-arm64",
                    "sha256": actual,
                    "signature": "ad-hoc",
                }
                if not isinstance(manifest, dict) or any(
                    manifest.get(k) != v for k, v in expected_manifest.items()
                ):
                    raise lib.RecipeError(
                        "official Sorage manifest differs", "incomplete"
                    )
            if row["member"] is not None:
                binaries[name] = extract_executable(
                    archive,
                    target,
                    {**row, "archive_sha256": row["download_sha256"]},
                    whole=False,
                )
                prefix = "haepari-0.1.0-darwin-arm64/skill/use-haepari/"
                with tarfile.open(archive, "r:gz") as handle:
                    archived_skill = {
                        member.name.removeprefix(prefix): (
                            hashlib.sha256(
                                handle.extractfile(member).read()
                            ).hexdigest(),
                            bool(member.mode & 0o111),
                        )
                        for member in handle
                        if member.isfile() and member.name.startswith(prefix)
                    }
                skill = root / "skills/use-haepari"
                sealed_skill = {
                    path.relative_to(skill).as_posix(): (
                        lib.sha256_file(path),
                        bool(path.stat().st_mode & 0o111),
                    )
                    for path in skill.rglob("*")
                    if path.is_file()
                }
                if archived_skill != sealed_skill:
                    raise lib.RecipeError(
                        "official Haepari complete skill differs", "incomplete"
                    )
                binaries[name]["archive_skill_matches_sealed"] = True
            else:
                if (
                    archive.stat().st_size != row["binary_bytes"]
                    or actual != row["binary_sha256"]
                ):
                    raise lib.RecipeError("official executable differs", "incomplete")
                archive.rename(target)
                target.chmod(0o755)
                binaries[name] = {"path": str(target), "sha256": actual}
            if name == "sorage":
                signature = lib.run(
                    [
                        "/usr/bin/codesign",
                        "--verify",
                        "--strict",
                        "--verbose=2",
                        str(target),
                    ],
                    timeout=60,
                )
                write_once(
                    originals / "sorage-signature.json",
                    {
                        "exit_code": signature.returncode,
                        "stdout": signature.stdout,
                        "stderr": signature.stderr,
                        "scope": "actual signature observation, not qualification",
                    },
                )
                if signature.returncode:
                    raise lib.RecipeError(
                        "official Sorage signature verification failed; retain original",
                        "incomplete",
                    )
    write_once(
        results / "materialization.json",
        {
            **binding(context),
            "delivery_sha256": lib.sha256_file(root / "delivery.json"),
            "binaries": binaries,
            "external_artifacts": "verified separately; not covered by native input digest",
        },
    )
    return 0


def fresh_home(context: Any) -> Path:
    """Create only an empty run-owned home; native installation stays manual."""
    home = context.root / "workspaces/haepari-combination-clean-home"
    owner = home.parent / "haepari-combination-clean-home.owner.json"
    expected = binding(context)
    if owner.exists():
        if (
            lib.read_json_safe(owner) != expected
            or home.is_symlink()
            or not home.is_dir()
        ):
            raise lib.RecipeError("preserve foreign/invalid clean home", "incomplete")
        return home
    if home.exists() or home.is_symlink():
        raise lib.RecipeError(
            "clean install requires an absent owned home", "incomplete"
        )
    home.mkdir(parents=True, mode=0o700)
    write_once(owner, expected)
    return home


def observe_tools(context: Any, home: Path, profile_name: str) -> dict:
    """Read installed bytes and complete skills; never start a tool daemon."""
    profile = context.profile(profile_name)
    tools = {}
    for component in profile["components"]:
        name = component["name"]
        if component.get("role") == "host":
            continue
        row = {}
        if "executable_sha256" in component:
            if name == "codex":
                binary = Path(context.codex)
            elif name == "guest-python":
                binary = Path(context.python)
            else:
                local = home / ".local/bin" / name
                binary = local
                if home == context.home and not local.exists():
                    binary = Path(shutil.which(name) or "/nonexistent")
            if home != context.home and binary.is_symlink():
                raise lib.RecipeError(
                    "clean-home executable must be owned bytes: " + name, "incomplete"
                )
            if not binary.is_file():
                raise lib.RecipeError(
                    "installed executable missing: " + name, "incomplete"
                )
            digest = lib.sha256_file(binary.resolve(strict=True))
            if digest != component["executable_sha256"].removeprefix("sha256:"):
                raise lib.RecipeError(
                    "installed executable differs: " + name, "incomplete"
                )
            row["binary_sha256"] = digest
            row["path"] = str(binary)
        if name in {"codex", "guest-python"} and "version" in component:
            binary = context.codex if name == "codex" else context.python
            output = lib.run([binary, "--version"], timeout=30)
            version = output.stdout.strip().split()[-1] if output.stdout.strip() else ""
            if output.returncode or version != component["version"].removeprefix("v"):
                raise lib.RecipeError(
                    "installed version differs: " + name, "incomplete"
                )
            row["version"] = version
        skill = component.get("skill_tree")
        if skill and name != "aquarium-plugin":
            tree = home / ".agents/skills" / skill["name"]
            digest = lib.skill_tree_digest(context.checkout, tree)
            if digest != skill["sha256"]:
                raise lib.RecipeError(
                    "installed complete skill differs: " + name, "incomplete"
                )
            row["skill_tree_sha256"] = digest
        if row:
            tools[name] = row
    plugin = next(
        row for row in profile["components"] if row["name"] == "aquarium-plugin"
    )
    cache = (
        home
        / ".codex/plugins/cache"
        / context.marketplace
        / "aquarium"
        / plugin["version"].removeprefix("v")
    )
    metadata = lib.read_json_safe(cache / ".codex-plugin/plugin.json")
    if not isinstance(metadata, dict) or metadata.get("version", "").removeprefix(
        "v"
    ) != plugin["version"].removeprefix("v"):
        raise lib.RecipeError("installed Aquarium metadata differs", "incomplete")
    if (
        lib.skill_tree_digest(context.checkout, cache / "skills")
        != plugin["skill_tree"]["sha256"]
    ):
        raise lib.RecipeError("installed Aquarium complete skills differ", "incomplete")
    tools["aquarium-plugin"] = {"skill_tree_sha256": plugin["skill_tree"]["sha256"]}
    # Haepari is the host controller in the profile; its guest copy is used
    # only for the isolated lock cases, never for recursive VM admission.
    if profile_name == PROFILE:
        expected = next(
            row for row in profile["components"] if row["name"] == "haepari"
        )
        binary = home / ".local/bin/haepari"
        tree = home / ".agents/skills/use-haepari"
        if (
            not binary.is_file()
            or lib.sha256_file(binary)
            != expected["executable_sha256"].removeprefix("sha256:")
            or lib.skill_tree_digest(context.checkout, tree)
            != expected["skill_tree"]["sha256"]
        ):
            raise lib.RecipeError(
                "isolated guest Haepari binary/skill differs", "incomplete"
            )
        tools["isolated-guest-haepari"] = {"binary_sha256": lib.sha256_file(binary)}
    return tools


def stage(context: Any, results: Path) -> int:
    index = case_index(context, results)
    attempts = results / "staging-attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    ok = True
    manifests = {}
    for name in CASES:
        entry = index["cases"][name]
        rows = entry.get("observations", []) if isinstance(entry, dict) else []
        required = [
            f"results/{SUITE}/{output}.json"
            for output in {
                "identity": ("baseline", "target"),
                "clean-install": ("clean-home-ready", "clean-install"),
                "upgrade": ("transition-upgrade",),
                "tools": ("tools",),
                "busy": ("busy",),
                "locks": ("locks",),
                "assessments": ("assessments",),
                "resource-p": ("resource-p",),
                "cleanup": ("consumer-cleanup", "inventory-post-cleanup"),
            }[name]
        ]
        if name == "identity" and context.inputs.get("combination", {}).get("delivery"):
            required.append(f"results/{SUITE}/materialization.json")
        for row in rows:
            if not isinstance(row, dict) or not isinstance(
                row.get("required", []), list
            ):
                raise lib.RecipeError("invalid original evidence list", "incomplete")
            required.extend(row.get("required", []))
        for member in required:
            regular_member(context.root, member)
        originals = context.root / f"results/{SUITE}/originals/{name}"
        members = list(required)
        if originals.is_symlink():
            raise lib.RecipeError("unsafe original evidence directory", "incomplete")
        if originals.exists():
            for path in originals.rglob("*"):
                relative = path.relative_to(context.root).as_posix()
                if path.is_symlink():
                    raise lib.RecipeError(
                        "unsafe original evidence member", "incomplete"
                    )
                if path.is_file():
                    regular_member(context.root, relative)
                    members.append(relative)
        # Include the exact decisions and phase snapshots as well as transcripts.
        members.append(f"results/{SUITE}/case-index.json")
        archive = results / f"evidence/{name}.tar"
        recover_archive_pair(archive)
        pending = archive.with_name(archive.name + ".partial")
        manifest = lib.stage_evidence_archive(pending, context.root, members, required)
        manifest["case_complete"] = case_complete(context, name, entry)
        manifest["case_index_sha256"] = lib.sha256_file(results / "case-index.json")
        pending_manifest = archive.with_suffix(".manifest.json.partial")
        lib.write_document(pending_manifest, manifest)
        publish_archive_pair(archive, pending, pending_manifest)
        manifests[name] = lib.sha256_file(archive.with_suffix(".manifest.json"))
        ok = ok and manifest["case_complete"] and not manifest["missing_required"]
    document = {
        **binding(context),
        "ok": ok,
        "manifests": manifests,
        "case_index_sha256": lib.sha256_file(results / "case-index.json"),
    }
    sequence = len(list(attempts.glob("*.json")))
    write_once(attempts / f"{sequence:04d}.json", document)
    lib.write_document(results / "stage-evidence.json", document)
    cleanup = lib.read_json_safe(results / "consumer-cleanup.json") or {}
    verified_cleanup = cleanup.get("consumer_cleanup") == "verified" and all(
        cleanup.get(k) == v for k, v in binding(context).items()
    )
    return lib.finish(
        SUITE,
        "pass" if ok else "incomplete",
        {"scope": "evidence transport only", "evidence_staging": ok},
        consumer_cleanup="verified" if verified_cleanup else "unverified",
        inputs=context.inputs,
        preserve_invalid_inventory=True,
    )


def complete_template(context: Any, results: Path) -> int:
    index = case_index(context, results)
    staged = lib.read_json_safe(results / "stage-evidence.json") or {}
    cleanup = lib.read_json_safe(results / "consumer-cleanup.json") or {}
    current = (
        staged.get("ok") is True
        and staged.get("case_index_sha256")
        == lib.sha256_file(results / "case-index.json")
        and cleanup.get("consumer_cleanup") == "verified"
        and all(cleanup.get(k) == v for k, v in binding(context).items())
    )
    for name in CASES:
        archive = results / f"evidence/{name}.tar"
        manifest = archive.with_suffix(".manifest.json")
        saved = lib.read_json_safe(manifest) or {}
        current = (
            current
            and archive.is_file()
            and manifest.is_file()
            and staged.get("manifests", {}).get(name) == lib.sha256_file(manifest)
            and saved.get("sha256") == lib.sha256_file(archive)
        )
        for member in saved.get("members", []):
            original = regular_member(context.root, member["path"])
            current = (
                current
                and original.is_file()
                and lib.sha256_file(original) == member["sha256"]
            )
    if not current:
        raise lib.RecipeError(
            "current complete staging and verified consumer cleanup required",
            "incomplete",
        )
    rows = [
        {
            "id": name,
            "status": "pass"
            if case_complete(context, name, index["cases"][name])
            else "unobserved",
            "evidence_references": [
                f"results/{SUITE}/evidence/{name}.tar",
                f"results/{SUITE}/evidence/{name}.manifest.json",
            ],
        }
        for name in CASES
    ]
    lib.write_document(
        results / "manual-complete-template.json",
        {
            "schema": "haepari.manual-result/v1",
            "job_id": context.job["job_id"],
            "installation_id": "<actual installation>",
            "profile_id": context.profile(PROFILE)["profile_id"],
            "profile_digest": context.profile_digest(PROFILE),
            "expected_revision": "<current native revision>",
            "observer": "<authorized operator>",
            "scenarios": rows,
        },
    )
    return 0


def run(context: Any, phase: str) -> int:
    lib.verify_guest_identity()
    lib.verify_sealed_inputs(context.root)
    lib.guard(context.root)
    verify_payload(context)
    results = lib.results_directory(SUITE)
    if phase == "ready":
        if (results / "case-index.json").exists():
            raise lib.RecipeError("preserve original manual preparation", "incomplete")
        write_once(
            results / "case-index.json",
            {
                **binding(context),
                "cases": {
                    name: {
                        "observations": [
                            {
                                "variant": variant,
                                "status": "unobserved",
                                "evidence_class": None,
                                "decision_reference": None,
                                "required": [],
                            }
                            for variant, _native in variants
                        ]
                    }
                    for name, variants in CASES.items()
                },
            },
        )
        write_once(
            results / "target.json",
            {
                **binding(context),
                "profile": context.profile(PROFILE),
                "inputs": context.inputs["combination"],
                "functional_cases": "unverified",
            },
        )
        lib.finish(
            SUITE,
            "incomplete",
            {"state": "awaiting manual cases"},
            consumer_cleanup="unverified",
            inputs=context.inputs,
            preserve_invalid_inventory=True,
        )
        return 0
    if phase == "materialize":
        return materialize(context, results)
    if phase == "stage-evidence":
        return stage(context, results)
    if phase == "complete-template":
        return complete_template(context, results)
    if phase == "consumer-cleanup":
        if (results / "consumer-cleanup.json").exists() or (
            results / "inventory-post-cleanup.json"
        ).exists():
            raise lib.RecipeError("preserve original cleanup observation", "incomplete")
        index = case_index(context, results)
        if not case_complete(context, "cleanup", index["cases"]["cleanup"]):
            raise lib.RecipeError(
                "original consumer settlement/cleanup observations required",
                "incomplete",
            )
        home = context.root / "workspaces/haepari-combination-clean-home"
        owner = home.parent / "haepari-combination-clean-home.owner.json"
        if (
            home.exists()
            or home.is_symlink()
            or lib.read_json_safe(owner) != binding(context)
        ):
            raise lib.RecipeError(
                "owned clean home removal must be observed first", "incomplete"
            )
        tools = observe_tools(context, context.home, PROFILE)
        custody = retained_custody(context)
        inventory = context.snapshot(
            SUITE, "post_cleanup", profile=PROFILE, capture="post-cleanup"
        )
        document = {
            **binding(context),
            "tools": tools,
            "inventory": inventory,
            "intentionally_retained_custody": custody,
            "custody_cleanup": "pending CO verified last-consumer TASK-102 settlement"
            if custody
            else "not_applicable",
            "consumer_cleanup": "verified",
            "declared_final_state": "target-retained",
        }
        write_once(results / "consumer-cleanup.json", document)
        return lib.finish(
            SUITE,
            "pass",
            {"scope": "consumer cleanup only"},
            consumer_cleanup="verified",
            inputs=context.inputs,
            preserve_invalid_inventory=True,
        )
    if phase not in PHASE_CASES:
        raise lib.RecipeError("unknown combination phase: " + phase, "incomplete")
    output = results / f"{PHASE_OUTPUTS.get(phase, phase)}.json"
    if output.exists():
        raise lib.RecipeError("preserve original phase observation", "incomplete")
    if phase == "clean-install":
        home = fresh_home(context)
        write_path = results / "clean-home-ready.json"
        if not write_path.exists():
            if any(home.iterdir()):
                raise lib.RecipeError(
                    "preserve uncaptured clean-home starting state", "incomplete"
                )
            write_once(
                write_path,
                {
                    **binding(context),
                    "home": str(home),
                    "product_absent": not any(home.iterdir()),
                    "process_environment": {
                        "HOME": str(home),
                        "CODEX_HOME": str(home / ".codex"),
                    },
                    "next": "perform native installation in this empty home, then repeat clean-install",
                },
            )
            return 0
        tools = observe_tools(context, home, PROFILE)
        document = {**binding(context), "home": str(home), "tools": tools}
    elif phase == "baseline":
        tools = observe_tools(context, context.home, "stable")
        document = {
            **binding(context),
            "profile": context.profile("stable"),
            "tools": tools,
            "inventory": context.snapshot(SUITE, "before", profile="stable"),
        }
    else:
        baseline = lib.read_json_safe(results / "baseline.json")
        if (
            not isinstance(baseline, dict)
            or baseline.get("candidate_sha") != binding(context)["candidate_sha"]
        ):
            raise lib.RecipeError(
                "meaningful original baseline required before replacement", "incomplete"
            )
        index = case_index(context, results)
        name = PHASE_CASES[phase]
        document = {
            **binding(context),
            "observations": index["cases"][name],
            "functional_cases": "native manual completion owns the verdict",
        }
        if phase in {"transition-upgrade", "tool-cases"}:
            document["tools"] = observe_tools(context, context.home, PROFILE)
        document["inventory"] = context.snapshot(
            SUITE, "candidate", profile=PROFILE, capture=phase
        )
    write_once(output, document)
    return 0
