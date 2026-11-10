"""Capture installed Sorage identities and restoration inside one manual Job."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import recipe_lib as lib
from tree_digest import TreeDigestError, inventory_entries

RELEASE_SHA256 = "838555333dac99483ed58fab5e6a79276d0ce712c69c2cd22ab64b9290c64eb6"

RELEASE_SKILL_TREE_SHA256 = (
    "15594b776f18229209eb3998df3eb209bcedb6776acd595037784596d962d628"
)


def storage_inventory() -> dict[str, Any]:
    """Read the exact approved roots after writers have been stopped."""
    entries = []
    roots = []
    for variable, scope in (
        ("SORAGE_HOME", "sorage-home"),
        ("AQUARIUM_VM_SORAGE_VAULT", "sorage-vault"),
    ):
        raw = os.environ.get(variable, "")
        path = Path(raw)
        if not raw or not path.is_absolute() or path.is_symlink() or not path.is_dir():
            raise lib.RecipeError(
                f"{variable} must name the approved absolute regular directory",
                "incomplete",
            )
        roots.append(str(path.resolve()))
        try:
            entries.extend(inventory_entries(path, scope, scope))
        except TreeDigestError as error:
            raise lib.RecipeError(
                "unsafe Sorage storage inventory", "incomplete"
            ) from error
    return {
        "roots_sha256": hashlib.sha256(json.dumps(roots).encode()).hexdigest(),
        "entries": entries,
    }


def observe(context: Any, candidate: bool = False) -> dict[str, Any]:
    selected = shutil.which("sorage")
    if not selected or Path(selected).is_symlink():
        raise lib.RecipeError(
            "a regular installed Sorage executable is required", "incomplete"
        )
    digest = lib.sha256_file(Path(selected))
    if candidate and digest != RELEASE_SHA256:
        raise lib.RecipeError(
            "candidate Sorage binary identity differs; it was not executed",
            "incomplete",
        )
    result = lib.run([selected, "version", "--json"], timeout=30)
    try:
        version = json.loads(result.stdout)
    except (ValueError, TypeError) as error:
        raise lib.RecipeError(
            "installed Sorage identity is invalid", "incomplete"
        ) from error
    if (
        result.returncode
        or not isinstance(version, dict)
        or version.get("name") != "sorage"
        or not isinstance(version.get("version"), str)
        or not version["version"]
    ):
        raise lib.RecipeError("installed Sorage identity is invalid", "incomplete")
    skill = context.home / ".agents/skills/use-sorage"
    skill_digest = lib.skill_tree_digest(context.checkout, skill)
    if candidate and skill_digest != RELEASE_SKILL_TREE_SHA256:
        raise lib.RecipeError(
            "installed Sorage skill differs from the complete release tree",
            "incomplete",
        )
    return {
        "version": version.get("version"),
        "binary_sha256": digest,
        "skill_tree_sha256": skill_digest,
        "storage_inventory": storage_inventory(),
    }


def run(context: Any, phase: str) -> int:
    lib.verify_guest_identity()
    lib.verify_sealed_inputs(context.root)
    lib.guard(context.root)
    if phase == "ready":
        results = lib.results_directory("sorage-adoption")
        target = results / "ready.json"
        if target.exists():
            raise lib.RecipeError(
                "preserve the original readiness observation", "incomplete"
            )
        lib.write_document(
            target,
            {
                "candidate_sha": context.inputs["candidate"]["git_sha"],
                "state": "awaiting authorized manual preparation",
            },
        )
        return 0
    if phase not in {"prepare", "candidate", "consumer-cleanup"}:
        raise lib.RecipeError("unknown Sorage observation phase")
    results = lib.results_directory("sorage-adoption")
    target = results / f"{phase}.json"
    if target.exists():
        raise lib.RecipeError("preserve the original phase observation", "incomplete")
    baseline = lib.read_json_safe(results / "prepare.json")
    candidate = context.inputs["candidate"]["git_sha"]
    if phase != "prepare" and (
        not isinstance(baseline, dict) or baseline.get("candidate_sha") != candidate
    ):
        raise lib.RecipeError(
            "the original candidate-bound baseline is required", "incomplete"
        )
    if phase == "consumer-cleanup":
        installed = lib.read_json_safe(results / "candidate.json")
        installed_tools = (
            installed.get("tools") if isinstance(installed, dict) else None
        )
        inventory = installed.get("inventory") if isinstance(installed, dict) else None
        if (
            not isinstance(installed_tools, dict)
            or installed.get("candidate_sha") != candidate
            or installed.get("capture") != "candidate"
            or installed_tools.get("version") != "v0.1.4"
            or installed_tools.get("binary_sha256") != RELEASE_SHA256
            or installed_tools.get("skill_tree_sha256") != RELEASE_SKILL_TREE_SHA256
            or not isinstance(inventory, list)
            or not inventory
            or not all(isinstance(row, dict) for row in inventory)
        ):
            raise lib.RecipeError(
                "a valid candidate-bound installed observation is required before restoration",
                "incomplete",
            )
    tools = observe(context, candidate=phase == "candidate")
    if phase == "candidate" and (
        tools["version"] != "v0.1.4" or tools["binary_sha256"] != RELEASE_SHA256
    ):
        raise lib.RecipeError(
            "installed Sorage differs from the official v0.1.4 binary", "incomplete"
        )
    aggregate_path = results / "inventories.json"
    aggregate = lib.read_json_safe(aggregate_path)
    if aggregate_path.exists() and (
        not isinstance(aggregate, dict)
        or aggregate.get("schema") != "aquarium.vm-suite-inventories/v1"
        or not isinstance(aggregate.get("inventories"), dict)
    ):
        raise lib.RecipeError("preserve the invalid inventory history", "incomplete")
    capture = (
        phase if phase != "consumer-cleanup" else f"consumer-cleanup-{uuid.uuid4().hex}"
    )
    inventory = context.snapshot(
        "sorage-adoption",
        phase,
        profile="candidate" if phase == "candidate" else "stable",
        capture=capture,
    )
    document = {
        "candidate_sha": candidate,
        "capture": capture,
        "tools": tools,
        "inventory": inventory,
        "functional_cases": "unverified; native manual completion owns their verdict",
    }
    if phase == "consumer-cleanup":
        problems = lib.postcondition_violations(
            baseline["inventory"], inventory, lambda _scope, _path: False
        )
        if baseline["tools"] != tools:
            problems.append("Sorage binary or skill differs from baseline")
        if problems:
            lib.write_document(
                results / f"{capture}.json", {**document, "violations": problems}
            )
            raise lib.RecipeError(
                "consumer restoration failed: " + "; ".join(problems), "incomplete"
            )
        document["consumer_cleanup"] = "verified"
    lib.write_document(target, document)
    if phase == "consumer-cleanup":
        return lib.finish(
            "sorage-adoption",
            "pass",
            {"scope": "consumer restoration only", "functional_cases": "unverified"},
            consumer_cleanup="verified",
        )
    return 0
